"""
Complete Authentication Routes
Supports: Email/Password, Firebase, Google Sign-In, OTP, JWT, Forgot Password
"""

# Flask imports — optional (not installed on Render/FastAPI deployments)
try:
    from flask import Blueprint, request, jsonify
    from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, decode_token
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    # Provide stubs so the rest of the file doesn't crash
    class _StubBP:
        def __init__(self, *a, **kw): pass
        def route(self, *a, **kw):
            def decorator(f): return f
            return decorator
    Blueprint = lambda *a, **kw: _StubBP()
    def jwt_required(*a, **kw):
        def decorator(f): return f
        return decorator
    def get_jwt_identity(): return None
    def create_access_token(**kw): return ''
    def create_refresh_token(**kw): return ''
    def decode_token(t): return {}

from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import os
from datetime import datetime, timedelta
from functools import wraps
from models.models import User, Farmer, Buyer, OTP, Notification, BaseModel
from utils.email_service import _build_otp_html, _build_email_html
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[SKIP] firebase_admin not installed - Firebase auth disabled")
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

if FLASK_AVAILABLE:
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
else:
    auth_bp = _StubBP()


# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize Firebase
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
# HELPER FUNCTIONS
# ============================================================================

def send_email(to_email, subject, message):
    """Send email - SMTP authentication is MANDATORY (uses STARTTLS port 587)
    Anti-spam: uses display name, Reply-To, and text/plain fallback."""
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    if not sender_email or not sender_password:
        raise RuntimeError(
            "SMTP Authentication FAILED: EMAIL_SENDER and EMAIL_PASSWORD must be set in .env. "
            "Email sending is mandatory and cannot be skipped."
        )
    
    try:
        from email.utils import formataddr
        msg = MIMEMultipart("alternative")
        # Use display name to reduce spam score
        msg['From'] = formataddr(('SmartFarm', sender_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = sender_email
        
        # Add plain text fallback (reduces spam score)
        import re
        plain_text = re.sub(r'<[^>]+>', '', message).strip()
        plain_text = re.sub(r'\s+', ' ', plain_text)
        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        # Add HTML version
        msg.attach(MIMEText(message, 'html', 'utf-8'))
        
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Use SMTP + STARTTLS (port 587) - secure connection, best for cloud hosts
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[OK] Email sent to {to_email} (STARTTLS port 587)")
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = (
            f"[ERR] SMTP Authentication FAILED for {sender_email}. "
            f"Check EMAIL_SENDER and EMAIL_PASSWORD in .env. Error: {e}"
        )
        print(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        print(f"[ERR] Email error: {e}")
        return False

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indian phone number"""
    import re
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def get_role_id(role_name):
    """Get role ID by role name"""
    try:
        from models.models import BaseModel
        query = "SELECT id FROM roles WHERE name = %s"
        result = BaseModel.execute_query(query, (role_name,), fetch_one=True)
        return result['id'] if result else None
    except Exception as e:
        print(f"Error getting role: {e}")
        return None

# ============================================================================
# REGISTRATION ROUTES
# ============================================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (Farmer or Buyer)"""
    try:
        data = request.get_json()
        role = data.get('role', 'buyer')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        location = data.get('location', '')
        
        # Validation
        if not first_name:
            return jsonify({'error': 'First name is required'}), 400
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        password_hash = generate_password_hash(password)
        
        if role == 'farmer':
            if not email:
                return jsonify({'error': 'Email required for farmer registration'}), 400
            
            # Check if email already exists
            existing = BaseModel.execute_query("SELECT id FROM farmers WHERE email = %s", (email,), fetch_one=True)
            if existing:
                return jsonify({'error': 'Email already registered'}), 409
            
            user_id = BaseModel.execute_insert(
                """INSERT INTO farmers (first_name, last_name, email, phone, password_hash, location) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (first_name, last_name, email, phone, password_hash, location)
            )
            
            # Create wallet
            try:
                BaseModel.execute_insert(
                    "INSERT INTO wallet (farmer_id, balance, total_earnings) VALUES (%s, 0, 0)", (user_id,)
                )
            except Exception:
                pass
            
        elif role == 'buyer':
            if not phone:
                return jsonify({'error': 'Phone required for buyer registration'}), 400
            
            existing = BaseModel.execute_query("SELECT id FROM buyers WHERE phone = %s", (phone,), fetch_one=True)
            if existing:
                return jsonify({'error': 'Phone number already registered'}), 409
            
            user_id = BaseModel.execute_insert(
                """INSERT INTO buyers (first_name, last_name, email, phone, password_hash, location, buyer_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, NULL)""",
                (first_name, last_name, email, phone, password_hash, location)
            )
            
            # Set buyer_id = id
            BaseModel.execute_query("UPDATE buyers SET buyer_id = %s WHERE id = %s", (user_id, user_id))
        else:
            return jsonify({'error': 'Invalid role. Use farmer or buyer'}), 400
        
        # Create token so user can login immediately
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims={'role': role, 'user_id': user_id}
        )
        
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'name': f"{first_name} {last_name}".strip(),
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'role': role,
            }
        }), 201
    
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email with OTP"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('otp'):
            return jsonify({'error': 'Email and OTP required'}), 400
        
        # Verify OTP
        otp_record = OTP.verify(email=data['email'], otp_code=data['otp'])
        
        if not otp_record:
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Get user and mark email as verified
        user = User.get_by_email(data['email'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        User.verify_email(user['id'])
        OTP.mark_verified(otp_record['id'])
        
        return jsonify({'message': 'Email verified successfully'}), 200
    
    except Exception as e:
        print(f"Email verification error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        user = User.get_by_email(email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['is_verified']:
            return jsonify({'error': 'Email already verified'}), 400
        
        otp_code = generate_otp()
        OTP.create(email=email, otp_code=otp_code, purpose='email_verification')
        
        email_body = _build_otp_html('Your email verification OTP is:', otp_code)
        
        send_email(email, 'SmartFarm - Email Verification OTP', email_body)
        
        return jsonify({'message': 'OTP sent to email'}), 200
    
    except Exception as e:
        print(f"Resend OTP error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BUYER LOGIN OTP VERIFICATION
# ============================================================================

@auth_bp.route('/send-otp', methods=['POST'])
def send_login_otp():
    """Send OTP to buyer email for login verification"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400

        otp_code = generate_otp()
        now = datetime.now()
        expires_at = now + timedelta(minutes=5)

        # Store OTP in the otps table
        BaseModel.execute_insert(
            """INSERT INTO otps (email, otp, created_at, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (email, otp_code, now, expires_at)
        )

        # Build branded email
        email_body = _build_otp_html('Your login verification OTP is:', otp_code, 'Valid for 5 minutes')

        email_sent = send_email(email, 'SmartFarm - Login OTP', email_body)

        if not email_sent:
            # SMTP is mandatory - do NOT leak OTP or allow bypass
            print(f"❌ [OTP] SMTP email send failed for {email}. OTP NOT delivered.")
            return jsonify({'success': False, 'error': 'Failed to send OTP email. Please check SMTP configuration.'}), 500

        return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200

    except Exception as e:
        print(f"Send OTP error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_login_otp():
    """Verify OTP for buyer login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()

        if not email or not otp_code:
            return jsonify({'success': False, 'error': 'Email and OTP are required'}), 400

        # Find the latest non-expired OTP for this email
        query = """
        SELECT * FROM otps
        WHERE email = %s AND otp = %s AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        otp_record = BaseModel.execute_query(query, (email, otp_code), fetch_one=True)

        if not otp_record:
            return jsonify({'success': False, 'verified': False, 'error': 'Invalid or expired OTP'}), 400

        # Delete used OTP
        BaseModel.execute_query("DELETE FROM otps WHERE id = %s", (otp_record['id'],))

        return jsonify({'success': True, 'verified': True}), 200

    except Exception as e:
        print(f"Verify OTP error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email/phone and password - sends OTP to email for verification"""
    try:
        data = request.get_json()
        role = data.get('role', 'farmer')
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password required'}), 400
        
        user = None
        
        if role == 'farmer':
            email = data.get('email', '')
            if not email:
                return jsonify({'error': 'Email required for farmer login'}), 400
            query = "SELECT * FROM farmers WHERE email = %s"
            user = BaseModel.execute_query(query, (email,), fetch_one=True)
            
        elif role == 'buyer':
            phone = data.get('phone', '')
            if not phone:
                return jsonify({'error': 'Phone required for buyer login'}), 400
            query = "SELECT * FROM buyers WHERE phone = %s"
            user = BaseModel.execute_query(query, (phone,), fetch_one=True)
            
        elif role == 'admin':
            email = data.get('email', '')
            if not email:
                return jsonify({'error': 'Email required for admin login'}), 400
            query = "SELECT *, admin_id as id FROM admins WHERE email = %s"
            user = BaseModel.execute_query(query, (email,), fetch_one=True)
        else:
            return jsonify({'error': 'Invalid role'}), 400
        
        if not user:
            if role == 'buyer':
                return jsonify({'error': 'No account found with this phone number. Please register first.'}), 401
            else:
                return jsonify({'error': 'No account found with this email. Please register first.'}), 401
        
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Incorrect password. Please try again.'}), 401
        
        # Password verified — build user info
        user_id = user.get('id') or user.get('admin_id')
        user_email = user.get('email', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        
        # Admin and Farmer: direct login (no OTP)
        if role in ('admin', 'farmer'):
            identity = str(user_id)
            access_token = create_access_token(
                identity=identity,
                additional_claims={'role': role, 'user_id': user_id}
            )
            refresh_token = create_refresh_token(identity=identity)
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user_id, 'name': name, 'first_name': first_name,
                    'last_name': last_name, 'email': user_email,
                    'phone': user.get('phone', ''), 'role': role,
                    'location': user.get('location', ''),
                }
            }), 200
        
        # Buyer: OTP verification required
        if not user_email:
            # No email on record — skip OTP, login directly
            identity = str(user_id)
            access_token = create_access_token(
                identity=identity,
                additional_claims={'role': role, 'user_id': user_id}
            )
            refresh_token = create_refresh_token(identity=identity)
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user_id, 'name': name, 'first_name': first_name,
                    'last_name': last_name, 'email': user_email,
                    'phone': user.get('phone', ''), 'role': role,
                    'location': user.get('location', ''),
                }
            }), 200
        
        # Generate and store OTP for buyer
        otp_code = generate_otp()
        now = datetime.now()
        expires_at = now + timedelta(minutes=5)
        
        BaseModel.execute_insert(
            """INSERT INTO otps (email, otp, created_at, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (user_email, otp_code, now, expires_at)
        )
        
        # Send OTP via branded email template
        email_body = _build_otp_html('Your login verification OTP is:', otp_code, 'Valid for 5 minutes')
        
        email_sent = send_email(user_email, 'SmartFarm - Login OTP', email_body)
        
        if not email_sent:
            return jsonify({'error': 'Failed to send OTP email. Please try again.'}), 500
        
        # Return user info + otp_required flag (NO tokens yet)
        return jsonify({
            'message': 'OTP sent to your email',
            'otp_required': True,
            'user': {
                'id': user_id, 'name': name, 'first_name': first_name,
                'last_name': last_name, 'email': user_email,
                'phone': user.get('phone', ''), 'role': role,
                'location': user.get('location', ''),
            }
        }), 200
    
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
            return jsonify({
                'error': 'Server is warming up. Please try again in a moment.',
                'error_code': 'database_error'
            }), 503
        
        print(f"[AUTH] Login error: {e}")
        return jsonify({
            'error': 'Something went wrong. Please try again.',
            'error_code': 'server_error'
        }), 500


@auth_bp.route('/complete-login', methods=['POST'])
def complete_login_with_otp():
    """Verify OTP and return JWT tokens to complete login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        role = data.get('role', 'farmer')
        
        if not email or not otp_code:
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        # Verify OTP
        query = """
        SELECT * FROM otps
        WHERE email = %s AND otp = %s AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        otp_record = BaseModel.execute_query(query, (email, otp_code), fetch_one=True)
        
        if not otp_record:
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Delete used OTP
        BaseModel.execute_query("DELETE FROM otps WHERE id = %s", (otp_record['id'],))
        
        # Find the user and generate tokens
        user = None
        if role == 'farmer':
            user = BaseModel.execute_query("SELECT * FROM farmers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'buyer':
            user = BaseModel.execute_query("SELECT * FROM buyers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'admin':
            user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE email = %s", (email,), fetch_one=True)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
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
        
        return jsonify({
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
        }), 200
    
    except Exception as e:
        print(f"Complete login error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/otp-login', methods=['POST'])
def otp_login():
    """Login with OTP"""
    try:
        data = request.get_json()
        
        phone = data.get('phone')
        if not phone or not validate_phone(phone):
            return jsonify({'error': 'Valid phone number required'}), 400
        
        # Check if user exists
        user = User.get_by_phone(phone)
        
        if not user:
            # Register with phone
            otp_code = generate_otp()
            OTP.create(phone=phone, otp_code=otp_code, purpose='login')
            
            email_body = f"""
            <h2>Smart Farmer Marketplace - OTP</h2>
            <p>Your login OTP is:</p>
            <h1>{otp_code}</h1>
            <p>This OTP will expire in 10 minutes.</p>
            """
            
            # Send via SMS (integration needed)
            # For now, returning OTP in response for testing
            
            return jsonify({
                'message': 'OTP sent to phone',
                'phone': phone,
                'new_user': True,
                'otp': otp_code  # Remove in production
            }), 200
        
        # Existing user
        otp_code = generate_otp()
        OTP.create(phone=phone, otp_code=otp_code, purpose='login')
        
        return jsonify({
            'message': 'OTP sent to phone',
            'phone': phone,
            'otp': otp_code  # Remove in production
        }), 200
    
    except Exception as e:
        print(f"OTP login error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-otp-login', methods=['POST'])
def verify_otp_login():
    """Verify OTP and login"""
    try:
        data = request.get_json()
        
        phone = data.get('phone')
        otp_code = data.get('otp')
        
        if not phone or not otp_code:
            return jsonify({'error': 'Phone and OTP required'}), 400
        
        # Verify OTP
        otp_record = OTP.verify(phone=phone, otp_code=otp_code)
        
        if not otp_record:
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Get or create user
        user = User.get_by_phone(phone)
        
        if not user:
            # Create new user
            role_id = get_role_id('buyer')
            user_id = User.create(
                username=phone,
                email='',
                phone=phone,
                password_hash=generate_password_hash(''),
                first_name=data.get('first_name', 'User'),
                last_name='',
                role_id=role_id
            )
            Buyer.create(user_id, data.get('location', 'Not Specified'))
            user = User.get_by_id(user_id)
        
        OTP.mark_verified(otp_record['id'])
        User.verify_phone(user['id'])
        User.update(user['id'], last_login=datetime.now())
        
        # Create tokens
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'phone': user['phone'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role_name']
            }
        }), 200
    
    except Exception as e:
        print(f"OTP verification error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FIREBASE AUTHENTICATION
# ============================================================================

@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    """Login/Register with Firebase"""
    try:
        if not FIREBASE_AVAILABLE:
            return jsonify({'error': 'Firebase authentication not configured'}), 503
        
        data = request.get_json()
        firebase_token = data.get('firebase_token')
        
        if not firebase_token:
            return jsonify({'error': 'Firebase token required'}), 400
        
        # Verify Firebase token
        try:
            firebase_user = firebase_auth.verify_id_token(firebase_token)
        except Exception as e:
            return jsonify({'error': 'Invalid Firebase token'}), 401
        
        firebase_uid = firebase_user.get('uid')
        email = firebase_user.get('email')
        
        # Check if user exists
        user = User.get_by_firebase_uid(firebase_uid)
        
        if user:
            # Existing user
            User.update(user['id'], last_login=datetime.now())
        else:
            # Create new user
            role_name = data.get('role', 'buyer')
            role_id = get_role_id(role_name)
            
            user_id = User.create(
                username=email.split('@')[0] if email else f"user_{firebase_uid[:8]}",
                email=email,
                phone='',
                password_hash=generate_password_hash(''),
                first_name=data.get('first_name', 'User'),
                last_name=data.get('last_name', ''),
                role_id=role_id,
                firebase_uid=firebase_uid
            )
            
            # Create profile
            location = data.get('location', 'Not Specified')
            if role_name == 'farmer':
                Farmer.create(user_id, location)
            else:
                Buyer.create(user_id, location)
            
            user = User.get_by_id(user_id)
        
        # Create tokens
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        
        return jsonify({
            'message': 'Firebase authentication successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role_name']
            }
        }), 200
    
    except Exception as e:
        print(f"Firebase login error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PASSWORD MANAGEMENT (OTP-based)
# ============================================================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset - sends OTP to email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if email exists in farmers or buyers
        user = BaseModel.execute_query('SELECT id, email FROM farmers WHERE email = %s', (email,), fetch_one=True)
        role = 'farmer'
        if not user:
            user = BaseModel.execute_query('SELECT id, email FROM buyers WHERE email = %s', (email,), fetch_one=True)
            role = 'buyer'
        if not user:
            return jsonify({'error': 'Email not found'}), 404
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store OTP in database
        BaseModel.execute_insert(
            'INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, NOW(), NOW() + INTERVAL \'10 minutes\')',
            (email, otp_code)
        )
        
        # Send branded OTP email using shared send_email (with anti-spam headers)
        email_body = _build_otp_html('Your password reset OTP is:', otp_code)
        
        try:
            email_sent = send_email(email, 'SmartFarm - Password Reset OTP', email_body)
            if not email_sent:
                return jsonify({'error': 'Failed to send OTP email'}), 500
        except Exception as e:
            print(f'[ERR] Email send error: {e}')
            return jsonify({'error': 'Failed to send OTP email'}), 500
        
        return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200
    
    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with OTP verification"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        
        if not all([email, otp, new_password]):
            return jsonify({'error': 'All fields required'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Verify OTP
        stored = BaseModel.execute_query(
            'SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
            (email, otp), fetch_one=True
        )
        if not stored:
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Hash new password
        hashed = generate_password_hash(new_password)
        
        # Update in farmers or buyers
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
        
        # Delete used OTP
        BaseModel.execute_query('DELETE FROM otps WHERE email = %s', (email,))
        
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
    
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password for logged-in user"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new password required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        user = User.get_by_id(user_id)
        
        if not user or not check_password_hash(user['password_hash'], old_password):
            return jsonify({'error': 'Invalid old password'}), 401
        
        password_hash = generate_password_hash(new_password)
        User.update(user_id, password_hash=password_hash)
        
        return jsonify({'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

@auth_bp.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token (Authorization header method)"""
    try:
        user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
    
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_access_token():
    """Refresh access token using refresh_token from request body.
    This is the primary refresh endpoint used by the frontend.
    It decodes the refresh token manually and issues a new access token."""
    try:
        data = request.get_json()
        refresh_token_str = data.get('refresh_token') if data else None
        
        if not refresh_token_str:
            return jsonify({'error': 'refresh_token_missing', 'message': 'Refresh token is required'}), 400
        
        try:
            decoded = decode_token(refresh_token_str)
        except Exception as decode_err:
            print(f"[AUTH] Refresh token decode failed: {decode_err}")
            return jsonify({'error': 'refresh_token_expired', 'message': 'Refresh token is invalid or expired. Please login again.'}), 401
        
        user_id = decoded.get('sub')
        if not user_id:
            return jsonify({'error': 'refresh_token_invalid', 'message': 'Invalid refresh token'}), 401
        
        # Preserve role claims from the original token
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
        return jsonify({'access_token': new_access_token}), 200
    
    except Exception as e:
        print(f"[AUTH] Refresh error: {e}")
        return jsonify({'error': 'server_error', 'message': 'Failed to refresh token'}), 500

@auth_bp.route('/session/validate', methods=['GET'])
@jwt_required()
def validate_session():
    """Validate current session — used by frontend on app startup.
    Returns user info if the access token is still valid."""
    try:
        user_id = get_jwt_identity()
        # Determine user role by checking all tables
        user_info = None
        role = None
        
        # Check farmers
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
            return jsonify({'valid': False, 'error': 'User not found'}), 404
        
        return jsonify({
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
        }), 200
    
    except Exception as e:
        print(f"[AUTH] Session validate error: {e}")
        return jsonify({'valid': False, 'error': 'server_error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user — no JWT required so it works even with expired tokens"""
    return jsonify({'message': 'Logout successful'}), 200

# ============================================================================
# USER PROFILE
# ============================================================================

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific profile
        profile = None
        if user['role_name'] == 'farmer':
            profile = Farmer.get_by_user_id(user_id)
        elif user['role_name'] == 'buyer':
            profile = Buyer.get_by_user_id(user_id)
        
        return jsonify({
            'user': user,
            'profile': profile
        }), 200
    
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Update user fields
        user_fields = {}
        allowed_user_fields = ['first_name', 'last_name', 'profile_image']
        
        for field in allowed_user_fields:
            if field in data:
                user_fields[field] = data[field]
        
        if user_fields:
            User.update(user_id, **user_fields)
        
        # Update role-specific profile
        user = User.get_by_id(user_id)
        
        if user['role_name'] == 'farmer':
            farmer = Farmer.get_by_user_id(user_id)
            farmer_fields = {}
            allowed_farmer_fields = ['location', 'latitude', 'longitude', 'land_area_hectares',
                                   'crops_grown', 'experience_years', 'bank_account', 'bank_ifsc',
                                   'bank_name', 'aadhar_number', 'pan_number']
            
            for field in allowed_farmer_fields:
                if field in data:
                    farmer_fields[field] = data[field]
            
            if farmer_fields:
                Farmer.update(farmer['id'], **farmer_fields)
        
        elif user['role_name'] == 'buyer':
            buyer = Buyer.get_by_user_id(user_id)
            buyer_fields = {}
            allowed_buyer_fields = ['business_name', 'business_type', 'company_registration',
                                   'location', 'latitude', 'longitude', 'delivery_address', 'gst_number']
            
            for field in allowed_buyer_fields:
                if field in data:
                    buyer_fields[field] = data[field]
            
            if buyer_fields:
                Buyer.update(buyer['id'], **buyer_fields)
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# VERIFICATION STATUS
# ============================================================================

@auth_bp.route('/verification-status', methods=['GET'])
@jwt_required()
def verification_status():
    """Get user verification status"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        return jsonify({
            'email_verified': bool(user['email_verified_at']),
            'phone_verified': bool(user['phone_verified_at']),
            'account_verified': user['is_verified']
        }), 200
    
    except Exception as e:
        print(f"Verification status error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# FASTAPI ROUTER — required by main.py (FastAPI entry point on Render)
# Wraps the same business logic as the Flask Blueprint above.
# ============================================================================

from fastapi import APIRouter, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from utils.jwt_utils import (
    create_access_token as fa_create_access_token,
    create_refresh_token as fa_create_refresh_token,
    decode_token as fa_decode_token,
)

auth_router = APIRouter(prefix='/api/auth', tags=['Authentication'])


def _json(data, status_code=200):
    return JSONResponse(content=data, status_code=status_code)


@auth_router.post('/register')
async def fa_register(request: FastAPIRequest):
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
            return _json({'error': 'First name is required'}, 400)
        if not password or len(password) < 6:
            return _json({'error': 'Password must be at least 6 characters'}, 400)
        password_hash = generate_password_hash(password)
        if role == 'farmer':
            if not email:
                return _json({'error': 'Email required for farmer registration'}, 400)
            existing = BaseModel.execute_query("SELECT id FROM farmers WHERE email = %s", (email,), fetch_one=True)
            if existing:
                return _json({'error': 'Email already registered'}, 409)
            user_id = BaseModel.execute_insert(
                "INSERT INTO farmers (first_name, last_name, email, phone, password_hash, location) VALUES (%s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email, phone, password_hash, location))
            try:
                BaseModel.execute_insert("INSERT INTO wallet (farmer_id, balance, total_earnings) VALUES (%s, 0, 0)", (user_id,))
            except Exception:
                pass
        elif role == 'buyer':
            if not phone:
                return _json({'error': 'Phone required for buyer registration'}, 400)
            existing = BaseModel.execute_query("SELECT id FROM buyers WHERE phone = %s", (phone,), fetch_one=True)
            if existing:
                return _json({'error': 'Phone number already registered'}, 409)
            user_id = BaseModel.execute_insert(
                "INSERT INTO buyers (first_name, last_name, email, phone, password_hash, location, buyer_id) VALUES (%s, %s, %s, %s, %s, %s, NULL)",
                (first_name, last_name, email, phone, password_hash, location))
            BaseModel.execute_query("UPDATE buyers SET buyer_id = %s WHERE id = %s", (user_id, user_id))
        else:
            return _json({'error': 'Invalid role. Use farmer or buyer'}, 400)
        access_token = fa_create_access_token(identity=str(user_id), additional_claims={'role': role, 'user_id': user_id})
        return _json({'message': 'Registration successful', 'access_token': access_token,
            'user': {'id': user_id, 'name': f"{first_name} {last_name}".strip(), 'first_name': first_name,
                     'last_name': last_name, 'email': email, 'phone': phone, 'role': role}}, 201)
    except Exception as e:
        print(f"Registration error: {e}")
        return _json({'error': str(e)}, 500)


@auth_router.post('/login')
async def fa_login(request: FastAPIRequest):
    try:
        data = await request.json()
        role = data.get('role', 'farmer')
        password = data.get('password', '')
        if not password:
            return _json({'error': 'Password required'}, 400)
        user = None
        if role == 'farmer':
            email = data.get('email', '')
            if not email:
                return _json({'error': 'Email required for farmer login'}, 400)
            user = BaseModel.execute_query("SELECT * FROM farmers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'buyer':
            # Accept phone OR email — check both fields
            phone_or_email = (data.get('phone', '') or data.get('email', '')).strip()
            if not phone_or_email:
                return _json({'error': 'Phone or Email required for buyer login'}, 400)
            if '@' in phone_or_email:
                # Input looks like an email — check buyers first
                user = BaseModel.execute_query("SELECT * FROM buyers WHERE LOWER(email) = LOWER(%s)", (phone_or_email,), fetch_one=True)
                if not user:
                    # Not a buyer email — check if it's an admin email (admin logging in via Buyer tab)
                    admin_user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE LOWER(email) = LOWER(%s)", (phone_or_email,), fetch_one=True)
                    if admin_user:
                        user = admin_user
                        role = 'admin'  # Elevate to admin role
            else:
                # Input looks like a phone number — query buyers by phone
                user = BaseModel.execute_query("SELECT * FROM buyers WHERE phone = %s", (phone_or_email,), fetch_one=True)
        elif role == 'admin':
            email = data.get('email', '')
            if not email:
                return _json({'error': 'Email required for admin login'}, 400)
            user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE LOWER(email) = LOWER(%s)", (email,), fetch_one=True)
        else:
            return _json({'error': 'Invalid role'}, 400)
        if not user:
            if role == 'buyer':
                msg = 'No account found with this phone or email. Please register first.'
            else:
                msg = 'No account found with this email. Please register first.'
            return _json({'error': msg}, 401)
        if not check_password_hash(user['password_hash'], password):
            return _json({'error': 'Incorrect password. Please try again.'}, 401)
        user_id = user.get('id') or user.get('admin_id')
        user_email = user.get('email', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        if role in ('admin', 'farmer'):
            identity = str(user_id)
            access_token = fa_create_access_token(identity=identity, additional_claims={'role': role, 'user_id': user_id})
            refresh_token = fa_create_refresh_token(identity=identity)
            return _json({'message': 'Login successful', 'access_token': access_token, 'refresh_token': refresh_token,
                'user': {'id': user_id, 'name': name, 'first_name': first_name, 'last_name': last_name,
                         'email': user_email, 'phone': user.get('phone', ''), 'role': role, 'location': user.get('location', '')}})
        if not user_email:
            identity = str(user_id)
            access_token = fa_create_access_token(identity=identity, additional_claims={'role': role, 'user_id': user_id})
            refresh_token = fa_create_refresh_token(identity=identity)
            return _json({'message': 'Login successful', 'access_token': access_token, 'refresh_token': refresh_token,
                'user': {'id': user_id, 'name': name, 'first_name': first_name, 'last_name': last_name,
                         'email': user_email, 'phone': user.get('phone', ''), 'role': role, 'location': user.get('location', '')}})
        otp_code = generate_otp()
        now = datetime.now()
        expires_at = now + timedelta(minutes=5)
        BaseModel.execute_insert("INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, %s, %s)", (user_email, otp_code, now, expires_at))
        email_body = _build_otp_html('Your login verification OTP is:', otp_code, 'Valid for 5 minutes')
        email_sent = send_email(user_email, 'SmartFarm - Login OTP', email_body)
        if not email_sent:
            # OTP email failed — fall back to direct login since password is already verified
            print(f"[AUTH] OTP email failed for {user_email}, falling back to direct login")
            identity = str(user_id)
            access_token = fa_create_access_token(identity=identity, additional_claims={'role': role, 'user_id': user_id})
            refresh_token = fa_create_refresh_token(identity=identity)
            return _json({'message': 'Login successful', 'access_token': access_token, 'refresh_token': refresh_token,
                'user': {'id': user_id, 'name': name, 'first_name': first_name, 'last_name': last_name,
                         'email': user_email, 'phone': user.get('phone', ''), 'role': role, 'location': user.get('location', '')}})
        return _json({'message': 'OTP sent to your email', 'otp_required': True,
            'user': {'id': user_id, 'name': name, 'first_name': first_name, 'last_name': last_name,
                     'email': user_email, 'phone': user.get('phone', ''), 'role': role, 'location': user.get('location', '')}})
    except Exception as e:
        error_str = str(e).lower()
        if 'connection' in error_str or 'server closed' in error_str or 'timeout' in error_str or 'database' in error_str:
            print(f"[AUTH] Database error during login: {e}")
            return _json({'error': 'Server is warming up. Please try again in a moment.', 'error_code': 'database_error'}, 503)
        print(f"[AUTH] Login error: {e}")
        return _json({'error': 'Something went wrong. Please try again.', 'error_code': 'server_error'}, 500)


@auth_router.post('/complete-login')
async def fa_complete_login(request: FastAPIRequest):
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        role = data.get('role', 'farmer')
        if not email or not otp_code:
            return _json({'error': 'Email and OTP are required'}, 400)
        otp_record = BaseModel.execute_query(
            "SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
            (email, otp_code), fetch_one=True)
        if not otp_record:
            return _json({'error': 'Invalid or expired OTP'}, 400)
        BaseModel.execute_query("DELETE FROM otps WHERE id = %s", (otp_record['id'],))
        user = None
        if role == 'farmer':
            user = BaseModel.execute_query("SELECT * FROM farmers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'buyer':
            user = BaseModel.execute_query("SELECT * FROM buyers WHERE email = %s", (email,), fetch_one=True)
        elif role == 'admin':
            user = BaseModel.execute_query("SELECT *, admin_id as id FROM admins WHERE email = %s", (email,), fetch_one=True)
        if not user:
            return _json({'error': 'User not found'}, 404)
        user_id = user.get('id') or user.get('admin_id')
        identity = str(user_id)
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        access_token = fa_create_access_token(identity=identity, additional_claims={'role': role, 'user_id': user_id})
        refresh_token = fa_create_refresh_token(identity=identity)
        return _json({'message': 'Login successful', 'verified': True, 'access_token': access_token, 'refresh_token': refresh_token,
            'user': {'id': user_id, 'name': name, 'first_name': first_name, 'last_name': last_name,
                     'email': user.get('email', ''), 'phone': user.get('phone', ''), 'role': role, 'location': user.get('location', '')}})
    except Exception as e:
        print(f"Complete login error: {e}")
        return _json({'error': str(e)}, 500)


@auth_router.post('/send-otp')
async def fa_send_otp(request: FastAPIRequest):
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        if not email:
            return _json({'success': False, 'error': 'Email is required'}, 400)
        if not validate_email(email):
            return _json({'success': False, 'error': 'Invalid email format'}, 400)
        otp_code = generate_otp()
        now = datetime.now()
        expires_at = now + timedelta(minutes=5)
        BaseModel.execute_insert("INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, %s, %s)", (email, otp_code, now, expires_at))
        email_body = _build_otp_html('Your login verification OTP is:', otp_code, 'Valid for 5 minutes')
        email_sent = send_email(email, 'SmartFarm - Login OTP', email_body)
        if not email_sent:
            return _json({'success': False, 'error': 'Failed to send OTP email.'}, 500)
        return _json({'success': True, 'message': 'OTP sent to your email'})
    except Exception as e:
        print(f"Send OTP error: {e}")
        return _json({'success': False, 'error': str(e)}, 500)


@auth_router.post('/verify-otp')
async def fa_verify_otp(request: FastAPIRequest):
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        if not email or not otp_code:
            return _json({'success': False, 'error': 'Email and OTP are required'}, 400)
        otp_record = BaseModel.execute_query(
            "SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
            (email, otp_code), fetch_one=True)
        if not otp_record:
            return _json({'success': False, 'verified': False, 'error': 'Invalid or expired OTP'}, 400)
        BaseModel.execute_query("DELETE FROM otps WHERE id = %s", (otp_record['id'],))
        return _json({'success': True, 'verified': True})
    except Exception as e:
        print(f"Verify OTP error: {e}")
        return _json({'success': False, 'error': str(e)}, 500)


@auth_router.post('/forgot-password')
async def fa_forgot_password(request: FastAPIRequest):
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        if not email:
            return _json({'error': 'Email is required'}, 400)
        user = BaseModel.execute_query('SELECT id, email FROM farmers WHERE email = %s', (email,), fetch_one=True)
        if not user:
            user = BaseModel.execute_query('SELECT id, email FROM buyers WHERE email = %s', (email,), fetch_one=True)
        if not user:
            return _json({'error': 'Email not found'}, 404)
        otp_code = str(random.randint(100000, 999999))
        BaseModel.execute_insert("INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, NOW(), NOW() + INTERVAL '10 minutes')", (email, otp_code))
        email_body = _build_otp_html('Your password reset OTP is:', otp_code)
        email_sent = send_email(email, 'SmartFarm - Password Reset OTP', email_body)
        if not email_sent:
            return _json({'error': 'Failed to send OTP email'}, 500)
        return _json({'success': True, 'message': 'OTP sent to your email'})
    except Exception as e:
        print(f"Forgot password error: {e}")
        return _json({'error': str(e)}, 500)


@auth_router.post('/reset-password')
async def fa_reset_password(request: FastAPIRequest):
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        if not all([email, otp, new_password]):
            return _json({'error': 'All fields required'}, 400)
        if len(new_password) < 6:
            return _json({'error': 'Password must be at least 6 characters'}, 400)
        stored = BaseModel.execute_query(
            'SELECT * FROM otps WHERE email = %s AND otp = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
            (email, otp), fetch_one=True)
        if not stored:
            return _json({'error': 'Invalid or expired OTP'}, 400)
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
        BaseModel.execute_query('DELETE FROM otps WHERE email = %s', (email,))
        return _json({'success': True, 'message': 'Password reset successfully'})
    except Exception as e:
        print(f"Reset password error: {e}")
        return _json({'error': str(e)}, 500)


@auth_router.post('/refresh')
async def fa_refresh_token(request: FastAPIRequest):
    try:
        data = await request.json()
        refresh_token_str = data.get('refresh_token') if data else None
        if not refresh_token_str:
            return _json({'error': 'refresh_token_missing', 'message': 'Refresh token is required'}, 400)
        try:
            decoded = fa_decode_token(refresh_token_str)
        except Exception:
            return _json({'error': 'refresh_token_expired', 'message': 'Refresh token is invalid or expired.'}, 401)
        user_id = decoded.get('sub')
        if not user_id:
            return _json({'error': 'refresh_token_invalid', 'message': 'Invalid refresh token'}, 401)
        additional_claims = {}
        if 'role' in decoded:
            additional_claims['role'] = decoded['role']
        if 'user_id' in decoded:
            additional_claims['user_id'] = decoded['user_id']
        new_access_token = fa_create_access_token(identity=str(user_id), additional_claims=additional_claims)
        return _json({'access_token': new_access_token})
    except Exception as e:
        print(f"[AUTH] Refresh error: {e}")
        return _json({'error': 'server_error', 'message': 'Failed to refresh token'}, 500)


@auth_router.post('/refresh-token')
async def fa_refresh_token_alt(request: FastAPIRequest):
    return await fa_refresh_token(request)


@auth_router.get('/session/validate')
async def fa_validate_session(request: FastAPIRequest):
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return _json({'valid': False, 'error': 'Token required'}, 401)
        token = auth_header[7:]
        decoded = fa_decode_token(token)
        user_id = decoded.get('sub')
        if not user_id:
            return _json({'valid': False, 'error': 'Invalid token'}, 401)
        user_info = None
        role = None
        farmer = BaseModel.execute_query('SELECT id, first_name, last_name, email, phone, location FROM farmers WHERE id = %s', (user_id,), fetch_one=True)
        if farmer:
            user_info = farmer
            role = 'farmer'
        if not user_info:
            buyer = BaseModel.execute_query('SELECT id, first_name, last_name, email, phone, location FROM buyers WHERE id = %s', (user_id,), fetch_one=True)
            if buyer:
                user_info = buyer
                role = 'buyer'
        if not user_info:
            admin = BaseModel.execute_query('SELECT admin_id as id, first_name, last_name, email FROM admins WHERE admin_id = %s', (user_id,), fetch_one=True)
            if admin:
                user_info = admin
                role = 'admin'
        if not user_info:
            return _json({'valid': False, 'error': 'User not found'}, 404)
        return _json({'valid': True, 'user': {
            'id': user_info.get('id'), 'first_name': user_info.get('first_name', ''),
            'last_name': user_info.get('last_name', ''),
            'name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
            'email': user_info.get('email', ''), 'phone': user_info.get('phone', ''),
            'role': role, 'location': user_info.get('location', '')}})
    except Exception as e:
        print(f"[AUTH] Session validate error: {e}")
        return _json({'valid': False, 'error': 'server_error'}, 500)


@auth_router.post('/logout')
async def fa_logout():
    return _json({'message': 'Logout successful'})
