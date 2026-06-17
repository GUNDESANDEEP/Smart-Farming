"""
Complete Authentication Routes
Supports: Email/Password, Firebase, Google Sign-In, OTP, JWT, Forgot Password
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import os
from datetime import datetime, timedelta
from functools import wraps
from models.models import User, Farmer, Buyer, OTP, Notification, BaseModel
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

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

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
    """Send email - SMTP authentication is MANDATORY (uses STARTTLS port 587)"""
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    if not sender_email or not sender_password:
        raise RuntimeError(
            "SMTP Authentication FAILED: EMAIL_SENDER and EMAIL_PASSWORD must be set in .env. "
            "Email sending is mandatory and cannot be skipped."
        )
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        
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
        
        print(f"✅ Email sent to {to_email} (STARTTLS port 587)")
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = (
            f"❌ SMTP Authentication FAILED for {sender_email}. "
            f"Check EMAIL_SENDER and EMAIL_PASSWORD in .env. Error: {e}"
        )
        print(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        print(f"❌ Email error: {e}")
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
        
        email_body = f"""
        <h2>Email Verification OTP</h2>
        <p>Your verification OTP is:</p>
        <h1>{otp_code}</h1>
        <p>This OTP will expire in 10 minutes.</p>
        """
        
        send_email(email, 'Verification OTP - Smart Farmer Marketplace', email_body)
        
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

        # Build email
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 30px; background: #f0fdf4; border-radius: 12px;">
            <h2 style="color: #166534;">🌾 Smart Farmer Marketplace</h2>
            <p style="color: #374151;">Your login verification OTP is:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #15803d; background: #dcfce7; padding: 12px 28px; border-radius: 8px;">{otp_code}</span>
            </div>
            <p style="color: #6b7280; font-size: 13px;">This OTP will expire in 5 minutes. Do not share it with anyone.</p>
        </div>
        """

        email_sent = send_email(email, 'Login OTP - Smart Farmer Marketplace', email_body)

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
    """Login with email/phone and password - supports all roles"""
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
            return jsonify({'error': 'Account not found'}), 401
        
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Build identity string
        user_id = user.get('id') or user.get('admin_id')
        identity = str(user_id)
        
        # Get name
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        
        # Create tokens with role in claims
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
                'id': user_id,
                'name': name,
                'first_name': first_name,
                'last_name': last_name,
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'role': role,
                'location': user.get('location', ''),
            }
        }), 200
    
    except Exception as e:
        print(f"Login error: {e}")
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
            'INSERT INTO otps (email, otp, created_at, expires_at) VALUES (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 10 MINUTE))',
            (email, otp_code)
        )
        
        # Send OTP via email using SMTP - MANDATORY
        sender_email = os.getenv('EMAIL_SENDER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            return jsonify({'error': 'SMTP credentials not configured. Email sending is mandatory.'}), 500
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = 'SmartFarm - Password Reset OTP'
            body = f'''<html><body style="font-family:Arial;text-align:center;">
            <div style="max-width:400px;margin:auto;padding:30px;background:#f0fdf4;border-radius:16px;">
            <h2 style="color:#166534;">🌿 SmartFarm</h2>
            <p>Your password reset OTP is:</p>
            <h1 style="color:#22c55e;letter-spacing:8px;">{otp_code}</h1>
            <p style="color:#888;">Valid for 10 minutes</p>
            </div></body></html>'''
            msg.attach(MIMEText(body, 'html'))
            # Use SMTP + STARTTLS (port 587) - secure connection, best for cloud hosts
            server = smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', 587)), timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ Password reset OTP sent to {email} (STARTTLS port 587)")
        except smtplib.SMTPAuthenticationError as e:
            print(f'❌ SMTP Authentication FAILED: {e}')
            return jsonify({'error': 'SMTP authentication failed. Check email credentials.'}), 500
        except Exception as e:
            print(f'❌ Email send error: {e}')
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
    """Refresh access token"""
    try:
        user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
    
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        # Token will be invalidated on client-side by removing from storage
        return jsonify({'message': 'Logout successful'}), 200
    
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'error': str(e)}), 500

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

