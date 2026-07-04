"""
Complete Authentication Routes - FastAPI version
Supports: Email/Password, Firebase, Google Sign-In, OTP, JWT, Forgot Password
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import os
import threading
from datetime import datetime, timedelta
from models.models import User, Farmer, Buyer, OTP, Notification, BaseModel
from utils.email_service import _build_otp_html, _build_email_html, EmailService
from utils.jwt_utils import create_access_token, create_refresh_token, decode_token, get_current_user
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[SKIP] firebase_admin not installed - Firebase auth disabled")
from dotenv import load_dotenv

load_dotenv()

auth_router = APIRouter(prefix='/api/auth', tags=['Authentication'])

# ============================================================================
# INITIALIZATION
# ============================================================================

if FIREBASE_AVAILABLE:
    try:
        firebase_credentials = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if firebase_credentials and os.path.exists(firebase_credentials):
            if not firebase_admin.get_app():
                cred = credentials.Certificate(firebase_credentials)
                firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization warning: {e}")

# ============================================================================
# OTP RATE LIMITING & DUPLICATE PREVENTION
# ============================================================================

# Track last OTP sent time per email (in-memory, resets on restart)
_otp_last_sent = {}  # email -> timestamp
_otp_send_lock = threading.Lock()  # Prevent concurrent sends
_otp_in_flight = set()  # Emails currently being processed
_otp_attempts = {}  # email -> count of failed verification attempts

OTP_COOLDOWN_SECONDS = 0  # Minimum seconds between OTP sends
OTP_MAX_VERIFY_ATTEMPTS = 5  # Max wrong OTP attempts before lockout
OTP_LOCKOUT_MINUTES = 15  # Lockout duration after max attempts

def _can_send_otp(email: str) -> tuple:
    """Check if OTP can be sent. Returns (allowed, seconds_remaining)."""
    now = datetime.now()
    last_sent = _otp_last_sent.get(email)
    if last_sent:
        elapsed = (now - last_sent).total_seconds()
        if elapsed < OTP_COOLDOWN_SECONDS:
            remaining = int(OTP_COOLDOWN_SECONDS - elapsed)
            return False, remaining
    return True, 0

def _record_otp_sent(email: str):
    """Record that an OTP was sent for rate limiting."""
    _otp_last_sent[email] = datetime.now()

def _check_verify_attempts(email: str) -> tuple:
    """Check if verification attempts are within limits. Returns (allowed, message)."""
    key = email.lower()
    record = _otp_attempts.get(key)
    if record:
        count, lockout_until = record
        if lockout_until and datetime.now() < lockout_until:
            remaining = int((lockout_until - datetime.now()).total_seconds() / 60) + 1
            return False, f'Too many failed attempts. Try again in {remaining} minutes.'
        if lockout_until and datetime.now() >= lockout_until:
            # Lockout expired, reset
            _otp_attempts[key] = (0, None)
    return True, ''

def _record_failed_attempt(email: str):
    """Record a failed OTP verification attempt."""
    key = email.lower()
    record = _otp_attempts.get(key, (0, None))
    count = record[0] + 1
    if count >= OTP_MAX_VERIFY_ATTEMPTS:
        _otp_attempts[key] = (count, datetime.now() + timedelta(minutes=OTP_LOCKOUT_MINUTES))
    else:
        _otp_attempts[key] = (count, None)

def _clear_verify_attempts(email: str):
    """Clear verification attempts after successful verification."""
    _otp_attempts.pop(email.lower(), None)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_email(to_email, subject, message):
    """Send email via SMTP (centralized EmailService)"""
    return EmailService._send_email(to_email, subject, message)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    import re
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def get_role_id(role_name):
    try:
        result = BaseModel.execute_query("SELECT id FROM roles WHERE name = %s", (role_name,), fetch_one=True)
        return result['id'] if result else None
    except Exception as e:
        print(f"Error getting role: {e}")
        return None

# ============================================================================
# REGISTRATION ROUTES
# ============================================================================

@auth_router.post('/register')
async def register(request: Request):
    """Register new user (Farmer or Buyer)"""
    try:
        data = await request.json()
        role = data.get('role', 'buyer')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        location = data.get('location', '')
        
        if not first_name:
            return JSONResponse(status_code=400, content={'error': 'First name is required'})
        if not password or len(password) < 6:
            return JSONResponse(status_code=400, content={'error': 'Password must be at least 6 characters'})
        
        password_hash = generate_password_hash(password)
        
        if role == 'farmer':
            if not email:
                return JSONResponse(status_code=400, content={'error': 'Email required for farmer registration'})
            existing = BaseModel.execute_query("SELECT id FROM farmers WHERE email = %s", (email,), fetch_one=True)
            if existing:
                return JSONResponse(status_code=409, content={'error': 'Email already registered'})
            user_id = BaseModel.execute_insert(
                """INSERT INTO farmers (first_name, last_name, email, phone, password_hash, location) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (first_name, last_name, email, phone, password_hash, location)
            )
            try:
                BaseModel.execute_insert(
                    "INSERT INTO wallet (farmer_id, balance, total_earnings) VALUES (%s, 0, 0)", (user_id,)
                )
            except Exception:
                pass
            
        elif role == 'buyer':
            if not phone:
                return JSONResponse(status_code=400, content={'error': 'Phone required for buyer registration'})
            existing = BaseModel.execute_query("SELECT id FROM buyers WHERE phone = %s", (phone,), fetch_one=True)
            if existing:
                return JSONResponse(status_code=409, content={'error': 'Phone number already registered'})
            user_id = BaseModel.execute_insert(
                """INSERT INTO buyers (first_name, last_name, email, phone, password_hash, location, buyer_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, NULL)""",
                (first_name, last_name, email, phone, password_hash, location)
            )
            BaseModel.execute_query("UPDATE buyers SET buyer_id = %s WHERE id = %s", (user_id, user_id))
        else:
            return JSONResponse(status_code=400, content={'error': 'Invalid role. Use farmer or buyer'})
        
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims={'role': role, 'user_id': user_id}
        )
        refresh_token = create_refresh_token(identity=str(user_id))
        
        return JSONResponse(status_code=201, content={
            'message': 'Registration successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'name': f"{first_name} {last_name}".strip(),
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'role': role,
            }
        })
    
    except Exception as e:
        print(f"Registration error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@auth_router.post('/verify-email')
async def verify_email(request: Request):
    """Verify email with OTP"""
    try:
        data = await request.json()
        if not data.get('email') or not data.get('otp'):
            return JSONResponse(status_code=400, content={'error': 'Email and OTP required'})
        otp_record = OTP.verify(email=data['email'], otp_code=data['otp'])
        if not otp_record:
            return JSONResponse(status_code=400, content={'error': 'Invalid or expired OTP'})
        user = User.get_by_email(data['email'])
        if not user:
            return JSONResponse(status_code=404, content={'error': 'User not found'})
        User.verify_email(user['id'])
        OTP.mark_verified(otp_record['id'])
        return {'message': 'Email verified successfully'}
    except Exception as e:
        print(f"Email verification error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/resend-otp')
async def resend_otp(request: Request):
    """Resend OTP to email"""
    try:
        data = await request.json()
        email = data.get('email')
        if not email:
            return JSONResponse(status_code=400, content={'error': 'Email required'})
        user = User.get_by_email(email)
        if not user:
            return JSONResponse(status_code=404, content={'error': 'User not found'})
        if user['is_verified']:
            return JSONResponse(status_code=400, content={'error': 'Email already verified'})
        otp_code = generate_otp()
        print(f"[OTP] Generated verification OTP for {email}: {otp_code}")
        OTP.create(email=email, otp_code=otp_code, purpose='email_verification')
        email_body = _build_otp_html('Your email verification OTP is:', otp_code)
        email_sent = send_email(email, 'SmartFarm - Email Verification OTP', email_body)
        if not email_sent:
            print(f"[WARN] OTP email failed for {email} (SMTP)")
            return {'message': 'OTP generated but email delivery failed. Please try again.'}
        return {'message': 'OTP sent to email'}
    except Exception as e:
        print(f"Resend OTP error: {e}")
        return JSONResponse(status_code=500, content={'error': 'Failed to resend OTP. Please try again.'})

# ============================================================================
# BUYER LOGIN OTP VERIFICATION
# ============================================================================

@auth_router.post('/send-otp')
async def send_login_otp(request: Request):
    """Send OTP to email — only triggered by explicit user action (Send OTP button).
    Rate limited: 1 OTP per email per 60 seconds.
    Invalidates all previous OTPs for the email before creating a new one."""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        if not email:
            return JSONResponse(status_code=400, content={'success': False, 'error': 'Email is required'})
        if not validate_email(email):
            return JSONResponse(status_code=400, content={'success': False, 'error': 'Invalid email format'})

        # Rate limiting: 1 OTP per 60 seconds
        allowed, remaining = _can_send_otp(email)
        if not allowed:
            return JSONResponse(status_code=429, content={
                'success': False,
                'error': f'Please wait {remaining} seconds before requesting another OTP.',
                'resend_after': remaining,
            })

        # Prevent duplicate concurrent requests
        with _otp_send_lock:
            if email in _otp_in_flight:
                return JSONResponse(status_code=429, content={
                    'success': False,
                    'error': 'OTP request already in progress. Please wait.',
                })
            _otp_in_flight.add(email)

        try:
            # Invalidate ALL previous OTPs for this email
            BaseModel.execute_query("DELETE FROM otps WHERE email = %s", (email,))

            # Generate and store new OTP
            otp_code = generate_otp()
            print(f"[OTP] Generated login/signup OTP for {email}: {otp_code}")
            now = datetime.now()
            expires_at = now + timedelta(minutes=5)
            BaseModel.execute_insert(
                """INSERT INTO otps (email, otp, created_at, expires_at)
                   VALUES (%s, %s, %s, %s)""",
                (email, otp_code, now, expires_at)
            )

            # Send email
            email_body = _build_otp_html('Your login verification OTP is:', otp_code, 'Valid for 5 minutes')
            email_sent = send_email(email, 'SmartFarm - Login OTP', email_body)

            # Record send time for rate limiting
            _record_otp_sent(email)
            # Clear any previous failed attempts
            _clear_verify_attempts(email)

            if not email_sent:
                print(f"[WARN] OTP email failed for {email} (SMTP)")
                return {'success': True, 'message': 'OTP generated but email delivery failed. Check spam or try again.', 'resend_after': OTP_COOLDOWN_SECONDS}

            return {'success': True, 'message': 'OTP sent to your email', 'resend_after': OTP_COOLDOWN_SECONDS}
        finally:
            with _otp_send_lock:
                _otp_in_flight.discard(email)

    except Exception as e:
        print(f"Send OTP error: {e}")
        with _otp_send_lock:
            _otp_in_flight.discard(email if 'email' in dir() else '')
        return JSONResponse(status_code=500, content={'success': False, 'error': 'Failed to send OTP. Please try again.'})


@auth_router.post('/verify-otp')
async def verify_login_otp(request: Request):
    """Verify OTP for buyer login. Max 5 attempts before lockout."""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        if not email or not otp_code:
            return JSONResponse(status_code=400, content={'success': False, 'error': 'Email and OTP are required'})

        # Check attempt limits
        allowed, lockout_msg = _check_verify_attempts(email)
        if not allowed:
            return JSONResponse(status_code=429, content={'success': False, 'error': lockout_msg})

        # Check for expired OTPs first (give specific error)
        expired_check = BaseModel.execute_query(
            "SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at <= NOW() ORDER BY created_at DESC LIMIT 1",
            (email, otp_code), fetch_one=True
        )
        if expired_check:
            _record_failed_attempt(email)
            BaseModel.execute_query("DELETE FROM otps WHERE email = %s AND expires_at <= NOW()", (email,))
            return JSONResponse(status_code=400, content={
                'success': False, 'verified': False,
                'error': 'OTP has expired. Please request a new one (valid for 5 minutes).'
            })

        query = """
        SELECT * FROM otps
        WHERE email = %s AND otp = %s AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        otp_record = BaseModel.execute_query(query, (email, otp_code), fetch_one=True)
        if not otp_record:
            _record_failed_attempt(email)
            return JSONResponse(status_code=400, content={
                'success': False, 'verified': False,
                'error': 'Invalid OTP. Please check and try again.'
            })

        # Success — delete ALL OTPs for this email and clear attempts
        BaseModel.execute_query("DELETE FROM otps WHERE email = %s", (email,))
        _clear_verify_attempts(email)
        return {'success': True, 'verified': True}
    except Exception as e:
        print(f"Verify OTP error: {e}")
        return JSONResponse(status_code=500, content={'success': False, 'error': 'Verification failed. Please try again.'})


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@auth_router.post('/login')
async def login(request: Request):
    """Login with email/phone and password"""
    try:
        data = await request.json()
        password = data.get('password', '')
        
        if not password:
            return JSONResponse(status_code=400, content={'error': 'Password required'})
        
        # Auto-detect role from fields if not explicitly sent
        role = data.get('role', '')
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        # Fallback: if 'email' field contains a phone number (digits only, 10+ chars), treat as phone
        if email and not phone and email.isdigit() and len(email) >= 10:
            phone = email
            email = ''
        
        # Auto-detect role if not provided
        if not role:
            if phone and not email:
                role = 'buyer'
            else:
                role = 'farmer'
        
        print(f"[AUTH] Login attempt: role={role}, email={email}, phone={phone}")
        
        user = None
        
        # Auto-detect if the email belongs to an admin. If so, override role to 'admin'
        # to support logging in using admin credentials even when the admin tab is hidden.
        if email and '@' in email:
            admin_user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE email = %s", (email,), fetch_one=True)
            if admin_user:
                role = 'admin'
                user = admin_user
        
        if role == 'farmer':
            identifier = email or phone
            if not identifier:
                return JSONResponse(status_code=400, content={'error': 'Email or phone required for farmer login'})
            user = BaseModel.execute_query("SELECT * FROM farmers WHERE email = %s", (identifier,), fetch_one=True)
            if not user:
                user = BaseModel.execute_query("SELECT * FROM farmers WHERE phone = %s", (identifier,), fetch_one=True)
        elif role == 'buyer':
            identifier = phone or email
            if not identifier:
                return JSONResponse(status_code=400, content={'error': 'Phone or email required for buyer login'})
            user = BaseModel.execute_query("SELECT * FROM buyers WHERE phone = %s", (identifier,), fetch_one=True)
            if not user:
                user = BaseModel.execute_query("SELECT * FROM buyers WHERE email = %s", (identifier,), fetch_one=True)
        elif role == 'admin':
            if not email:
                return JSONResponse(status_code=400, content={'error': 'Email required for admin login'})
            user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE email = %s", (email,), fetch_one=True)
        else:
            return JSONResponse(status_code=400, content={'error': 'Invalid role'})
        
        if not user:
            if role == 'buyer':
                return JSONResponse(status_code=401, content={'error': 'No account found with this phone number or email. Please register first.'})
            else:
                return JSONResponse(status_code=401, content={'error': 'No account found with this email or phone number. Please register first.'})
        
        if not check_password_hash(user['password_hash'], password):
            return JSONResponse(status_code=401, content={'error': 'Incorrect password. Please try again.'})
        
        user_id = user.get('id') or user.get('admin_id')
        user_email = user.get('email', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        
        # All roles: direct login with tokens (OTP is a separate explicit step)
        identity = str(user_id)
        access_token = create_access_token(
            identity=identity,
            additional_claims={'role': role, 'user_id': user_id}
        )
        refresh_token = create_refresh_token(identity=identity)
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id, 'name': name, 'first_name': first_name,
                'last_name': last_name, 'email': user_email,
                'phone': user.get('phone', ''), 'role': role,
                'location': user.get('location', ''),
            }
        }
    
    except Exception as e:
        import psycopg2 as _pg2
        error_str = str(e).lower()
        is_db_error = (
            isinstance(e, _pg2.OperationalError) or
            isinstance(e, _pg2.InterfaceError) or
            'connection' in error_str or
            'server closed' in error_str or
            'timeout' in error_str or
            'database' in error_str
        )
        if is_db_error:
            print(f"[AUTH] Database error during login: {e}")
            return JSONResponse(status_code=503, content={
                'error': 'Server is warming up. Please try again in a moment.',
                'error_code': 'database_error'
            })
        print(f"[AUTH] Login error: {e}")
        return JSONResponse(status_code=500, content={
            'error': 'Something went wrong. Please try again.',
            'error_code': 'server_error'
        })


@auth_router.post('/complete-login')
async def complete_login_with_otp(request: Request):
    """Verify OTP and return JWT tokens to complete login"""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        role = data.get('role', 'farmer')
        
        if not email or not otp_code:
            return JSONResponse(status_code=400, content={'error': 'Email and OTP are required'})
        
        query = """
        SELECT * FROM otps
        WHERE email = %s AND otp = %s AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        otp_record = BaseModel.execute_query(query, (email, otp_code), fetch_one=True)
        if not otp_record:
            return JSONResponse(status_code=400, content={'error': 'Invalid or expired OTP'})
        
        BaseModel.execute_query("DELETE FROM otps WHERE id = %s", (otp_record['id'],))
        
        user = None
        if role == 'farmer':
            user = BaseModel.execute_query("SELECT * FROM farmers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'buyer':
            user = BaseModel.execute_query("SELECT * FROM buyers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'admin':
            user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE email = %s", (email,), fetch_one=True)
        
        if not user:
            return JSONResponse(status_code=404, content={'error': 'User not found'})
        
        user_id = user.get('id') or user.get('admin_id')
        identity = str(user_id)
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        
        access_token = create_access_token(
            identity=identity,
            additional_claims={'role': role, 'user_id': user_id}
        )
        refresh_token = create_refresh_token(identity=identity)
        
        return {
            'message': 'Login successful',
            'verified': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id, 'name': name, 'first_name': first_name,
                'last_name': last_name, 'email': user.get('email', ''),
                'phone': user.get('phone', ''), 'role': role,
                'location': user.get('location', ''),
            }
        }
    except Exception as e:
        print(f"Complete login error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/otp-login')
async def otp_login(request: Request):
    """Login with OTP"""
    try:
        data = await request.json()
        phone = data.get('phone')
        if not phone or not validate_phone(phone):
            return JSONResponse(status_code=400, content={'error': 'Valid phone number required'})
        user = User.get_by_phone(phone)
        if not user:
            otp_code = generate_otp()
            OTP.create(phone=phone, otp_code=otp_code, purpose='login')
            return {
                'message': 'OTP sent to phone',
                'phone': phone,
                'new_user': True,
                'otp': otp_code
            }
        otp_code = generate_otp()
        OTP.create(phone=phone, otp_code=otp_code, purpose='login')
        return {
            'message': 'OTP sent to phone',
            'phone': phone,
            'otp': otp_code
        }
    except Exception as e:
        print(f"OTP login error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/verify-otp-login')
async def verify_otp_login(request: Request):
    """Verify OTP and login"""
    try:
        data = await request.json()
        phone = data.get('phone')
        otp_code = data.get('otp')
        if not phone or not otp_code:
            return JSONResponse(status_code=400, content={'error': 'Phone and OTP required'})
        otp_record = OTP.verify(phone=phone, otp_code=otp_code)
        if not otp_record:
            return JSONResponse(status_code=400, content={'error': 'Invalid or expired OTP'})
        user = User.get_by_phone(phone)
        if not user:
            role_id = get_role_id('buyer')
            user_id = User.create(
                username=phone, email='', phone=phone,
                password_hash=generate_password_hash(''),
                first_name=data.get('first_name', 'User'),
                last_name='', role_id=role_id
            )
            Buyer.create(user_id, data.get('location', 'Not Specified'))
            user = User.get_by_id(user_id)
        OTP.mark_verified(otp_record['id'])
        User.verify_phone(user['id'])
        User.update(user['id'], last_login=datetime.now())
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'], 'email': user['email'],
                'phone': user['phone'], 'first_name': user['first_name'],
                'last_name': user['last_name'], 'role': user['role_name']
            }
        }
    except Exception as e:
        print(f"OTP verification error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# FIREBASE AUTHENTICATION
# ============================================================================

@auth_router.post('/firebase-login')
async def firebase_login(request: Request):
    """Login/Register with Firebase"""
    try:
        if not FIREBASE_AVAILABLE:
            return JSONResponse(status_code=503, content={'error': 'Firebase authentication not configured'})
        data = await request.json()
        firebase_token = data.get('firebase_token')
        if not firebase_token:
            return JSONResponse(status_code=400, content={'error': 'Firebase token required'})
        try:
            firebase_user = firebase_auth.verify_id_token(firebase_token)
        except Exception:
            return JSONResponse(status_code=401, content={'error': 'Invalid Firebase token'})
        firebase_uid = firebase_user.get('uid')
        email = firebase_user.get('email')
        user = User.get_by_firebase_uid(firebase_uid)
        if user:
            User.update(user['id'], last_login=datetime.now())
        else:
            role_name = data.get('role', 'buyer')
            role_id = get_role_id(role_name)
            user_id = User.create(
                username=email.split('@')[0] if email else f"user_{firebase_uid[:8]}",
                email=email, phone='',
                password_hash=generate_password_hash(''),
                first_name=data.get('first_name', 'User'),
                last_name=data.get('last_name', ''),
                role_id=role_id, firebase_uid=firebase_uid
            )
            location = data.get('location', 'Not Specified')
            if role_name == 'farmer':
                Farmer.create(user_id, location)
            else:
                Buyer.create(user_id, location)
            user = User.get_by_id(user_id)
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        return {
            'message': 'Firebase authentication successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'], 'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role_name']
            }
        }
    except Exception as e:
        print(f"Firebase login error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@auth_router.post('/forgot-password')
async def forgot_password(request: Request):
    """Request password reset - sends OTP to email"""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        if not email:
            return JSONResponse(status_code=400, content={'error': 'Email is required'})
        user = BaseModel.execute_query('SELECT id, email FROM farmers WHERE email = %s', (email,), fetch_one=True)
        role = 'farmer'
        if not user:
            user = BaseModel.execute_query('SELECT id, email FROM buyers WHERE email = %s', (email,), fetch_one=True)
            role = 'buyer'
        if not user:
            return JSONResponse(status_code=404, content={'error': 'Email not found'})
        # Rate limit password reset OTPs too
        allowed, remaining = _can_send_otp(email)
        if not allowed:
            return JSONResponse(status_code=429, content={
                'success': False,
                'error': f'Please wait {remaining} seconds before requesting another OTP.',
                'resend_after': remaining,
            })

        # Invalidate old OTPs for this email
        BaseModel.execute_query("DELETE FROM otps WHERE email = %s", (email,))

        otp_code = str(random.randint(100000, 999999))
        BaseModel.execute_insert(
            "INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, NOW(), NOW() + INTERVAL '10 minutes')",
            (email, otp_code)
        )
        _record_otp_sent(email)

        email_body = _build_otp_html('Your password reset OTP is:', otp_code)
        try:
            email_sent = send_email(email, 'SmartFarm - Password Reset OTP', email_body)
            if not email_sent:
                print(f"[WARN] Password reset OTP email failed for {email}")
                return {'success': True, 'message': 'OTP generated but email delivery failed. Please try again.'}
        except Exception as e:
            print(f'[ERR] Email send error: {e}')
            return {'success': True, 'message': 'OTP generated but email delivery failed. Please try again.'}
        return {'success': True, 'message': 'OTP sent to your email'}
    except Exception as e:
        print(f"Forgot password error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/reset-password')
async def reset_password(request: Request):
    """Reset password with OTP verification"""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        if not all([email, otp, new_password]):
            return JSONResponse(status_code=400, content={'error': 'All fields required'})
        if len(new_password) < 6:
            return JSONResponse(status_code=400, content={'error': 'Password must be at least 6 characters'})
        stored = BaseModel.execute_query(
            'SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
            (email, otp), fetch_one=True
        )
        if not stored:
            return JSONResponse(status_code=400, content={'error': 'Invalid or expired OTP'})
        hashed = generate_password_hash(new_password)
        updated = False
        result = BaseModel.execute_query('SELECT id FROM farmers WHERE email = %s', (email,), fetch_one=True)
        if result:
            BaseModel.execute_query('UPDATE farmers SET password_hash = %s WHERE email = %s', (hashed, email))
            updated = True
        if not updated:
            result = BaseModel.execute_query('SELECT id FROM buyers WHERE email = %s', (email,), fetch_one=True)
            if result:
                BaseModel.execute_query('UPDATE buyers SET password_hash = %s WHERE email = %s', (hashed, email))
                updated = True
        BaseModel.execute_query('DELETE FROM otps WHERE email = %s', (email,))
        return {'success': True, 'message': 'Password reset successfully'}
    except Exception as e:
        print(f"Reset password error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/change-password')
async def change_password(request: Request, user_id: str = Depends(get_current_user)):
    """Change password for logged-in user"""
    try:
        data = await request.json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not old_password or not new_password:
            return JSONResponse(status_code=400, content={'error': 'Old and new password required'})
        if len(new_password) < 8:
            return JSONResponse(status_code=400, content={'error': 'Password must be at least 8 characters'})
        user = User.get_by_id(user_id)
        if not user or not check_password_hash(user['password_hash'], old_password):
            return JSONResponse(status_code=401, content={'error': 'Invalid old password'})
        password_hash = generate_password_hash(new_password)
        User.update(user_id, password_hash=password_hash)
        return {'message': 'Password changed successfully'}
    except Exception as e:
        print(f"Change password error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

@auth_router.post('/refresh-token')
async def refresh_token_header(request: Request, user_id: str = Depends(get_current_user)):
    """Refresh access token (Authorization header method)"""
    try:
        new_access_token = create_access_token(identity=user_id)
        return {'access_token': new_access_token}
    except Exception as e:
        print(f"Token refresh error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/refresh')
async def refresh_access_token(request: Request):
    """Refresh access token using refresh_token from request body."""
    try:
        data = await request.json()
        refresh_token_str = data.get('refresh_token') if data else None
        if not refresh_token_str:
            return JSONResponse(status_code=400, content={'error': 'refresh_token_missing', 'message': 'Refresh token is required'})
        try:
            decoded = decode_token(refresh_token_str)
        except Exception as decode_err:
            print(f"[AUTH] Refresh token decode failed: {decode_err}")
            return JSONResponse(status_code=401, content={'error': 'refresh_token_expired', 'message': 'Refresh token is invalid or expired. Please login again.'})
        user_id = decoded.get('sub')
        if not user_id:
            return JSONResponse(status_code=401, content={'error': 'refresh_token_invalid', 'message': 'Invalid refresh token'})
        additional_claims = {}
        if 'role' in decoded:
            additional_claims['role'] = decoded['role']
        if 'user_id' in decoded:
            additional_claims['user_id'] = decoded['user_id']
        new_access_token = create_access_token(
            identity=str(user_id),
            additional_claims=additional_claims
        )
        print(f"[AUTH] Token refreshed for user {user_id}")
        return {'access_token': new_access_token}
    except Exception as e:
        print(f"[AUTH] Refresh error: {e}")
        return JSONResponse(status_code=500, content={'error': 'server_error', 'message': 'Failed to refresh token'})

@auth_router.get('/session/validate')
async def validate_session(user_id: str = Depends(get_current_user)):
    """Validate current session"""
    try:
        user_info = None
        role = None
        farmer = BaseModel.execute_query(
            'SELECT id, first_name, last_name, email, phone, location FROM farmers WHERE id = %s',
            (user_id,), fetch_one=True
        )
        if farmer:
            user_info = farmer
            role = 'farmer'
        if not user_info:
            buyer = BaseModel.execute_query(
                'SELECT id, first_name, last_name, email, phone, location FROM buyers WHERE id = %s',
                (user_id,), fetch_one=True
            )
            if buyer:
                user_info = buyer
                role = 'buyer'
        if not user_info:
            admin = BaseModel.execute_query(
                'SELECT admin_id as id, first_name, last_name, email FROM admins WHERE admin_id = %s',
                (user_id,), fetch_one=True
            )
            if admin:
                user_info = admin
                role = 'admin'
        if not user_info:
            return JSONResponse(status_code=404, content={'valid': False, 'error': 'User not found'})
        return {
            'valid': True,
            'user': {
                'id': user_info.get('id'),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                'email': user_info.get('email', ''),
                'phone': user_info.get('phone', ''),
                'role': role,
                'location': user_info.get('location', ''),
            }
        }
    except Exception as e:
        print(f"[AUTH] Session validate error: {e}")
        return JSONResponse(status_code=500, content={'valid': False, 'error': 'server_error'})

@auth_router.post('/logout')
async def logout():
    """Logout user"""
    return {'message': 'Logout successful'}

# ============================================================================
# USER PROFILE
# ============================================================================

@auth_router.get('/profile')
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            return JSONResponse(status_code=404, content={'error': 'User not found'})
        profile = None
        if user['role_name'] == 'farmer':
            profile = Farmer.get_by_user_id(user_id)
        elif user['role_name'] == 'buyer':
            profile = Buyer.get_by_user_id(user_id)
        return {'user': user, 'profile': profile}
    except Exception as e:
        print(f"Get profile error: {e}")
        return JSONResponse(status_code=500, content={'error': 'Failed to load profile'})

@auth_router.put('/profile')
async def update_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Update user profile — supports all editable fields for farmers and buyers"""
    try:
        data = await request.json()
        user_fields = {}
        allowed_user_fields = ['first_name', 'last_name', 'phone', 'email', 'profile_image', 'location']
        for field in allowed_user_fields:
            if field in data:
                user_fields[field] = data[field]
        if user_fields:
            User.update(user_id, **user_fields)
        user = User.get_by_id(user_id)
        if user['role_name'] == 'farmer':
            farmer = Farmer.get_by_user_id(user_id)
            farmer_fields = {}
            allowed_farmer_fields = ['location', 'latitude', 'longitude', 'land_area_hectares',
                                   'crops_grown', 'experience_years', 'bank_account', 'bank_ifsc',
                                   'bank_name', 'aadhar_number', 'pan_number', 'phone', 'email']
            for field in allowed_farmer_fields:
                if field in data:
                    farmer_fields[field] = data[field]
            if farmer_fields:
                Farmer.update(farmer['id'], **farmer_fields)
        elif user['role_name'] == 'buyer':
            buyer = Buyer.get_by_user_id(user_id)
            buyer_fields = {}
            allowed_buyer_fields = ['business_name', 'business_type', 'company_registration',
                                   'location', 'latitude', 'longitude', 'delivery_address',
                                   'gst_number', 'phone', 'email', 'city', 'state', 'pincode']
            for field in allowed_buyer_fields:
                if field in data:
                    buyer_fields[field] = data[field]
            if buyer_fields:
                Buyer.update(buyer['id'], **buyer_fields)
        # Return updated user data so frontend can sync
        updated_user = User.get_by_id(user_id)
        return {'message': 'Profile updated successfully', 'user': updated_user}
    except Exception as e:
        print(f"Update profile error: {e}")
        return JSONResponse(status_code=500, content={'error': 'Failed to update profile. Please try again.'})

# ============================================================================
# VERIFICATION STATUS
# ============================================================================

@auth_router.get('/verification-status')
async def verification_status(user_id: str = Depends(get_current_user)):
    """Get user verification status"""
    try:
        user = User.get_by_id(user_id)
        return {
            'email_verified': bool(user['email_verified_at']),
            'phone_verified': bool(user['phone_verified_at']),
            'account_verified': user['is_verified']
        }
    except Exception as e:
        print(f"Verification status error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# USER NOTIFICATIONS
# ============================================================================

@auth_router.get('/notifications')
async def get_notifications(user_id: str = Depends(get_current_user)):
    """Get all notifications for current user"""
    try:
        uid = int(user_id)
        notifications = Notification.get_user_notifications(uid, limit=50) or []
        result = []
        unread_count = 0
        for n in notifications:
            is_read = bool(n.get('is_read', False))
            if not is_read:
                unread_count += 1
            result.append({
                'id': n['id'],
                'user_id': n['user_id'],
                'title': n.get('title', ''),
                'message': n.get('message', ''),
                'type': n.get('type', 'general'),
                'is_read': is_read,
                'created_at': n['created_at'].isoformat() if n.get('created_at') else None,
                'read_at': n['read_at'].isoformat() if n.get('read_at') else None,
            })
        return {
            'success': True,
            'notifications': result,
            'unread_count': unread_count
        }
    except Exception as e:
        print(f"Get notifications error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/notifications/read-all')
async def read_all_notifications(user_id: str = Depends(get_current_user)):
    """Mark all notifications as read"""
    try:
        uid = int(user_id)
        BaseModel.execute_query(
            "UPDATE notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_read = FALSE",
            (uid,)
        )
        return {'success': True, 'message': 'All notifications marked as read'}
    except Exception as e:
        print(f"Read all notifications error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.post('/notifications/{notification_id}/read')
async def read_single_notification(notification_id: int, user_id: str = Depends(get_current_user)):
    """Mark single notification as read"""
    try:
        uid = int(user_id)
        notif = BaseModel.execute_query(
            "SELECT * FROM notifications WHERE id = %s AND user_id = %s", (notification_id, uid), fetch_one=True
        )
        if not notif:
            return JSONResponse(status_code=404, content={'error': 'Notification not found'})
        Notification.mark_as_read(notification_id)
        return {'success': True, 'message': 'Notification marked as read'}
    except Exception as e:
        print(f"Read notification error: {e}")
        return JSONResponse(status_code=500, content={'error': str(e)})

@auth_router.get('/diagnose')
async def diagnose_database():
    """Temporary endpoint to inspect users and their registered roles"""
    try:
        farmers = BaseModel.execute_query("SELECT id, first_name, last_name, email, phone FROM farmers LIMIT 30", fetch_all=True)
        buyers = BaseModel.execute_query("SELECT id, first_name, last_name, email, phone FROM buyers LIMIT 30", fetch_all=True)
        return {
            'farmers': farmers,
            'buyers': buyers
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

