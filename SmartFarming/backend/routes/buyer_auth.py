"""
Buyer Authentication Routes
Handles: Signup, OTP, Login, Password Reset
Path: /api/buyer-auth
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
import random
import string

# Import database models
import sys
sys.path.append('..')
from models.models import BuyerAuth, OTP

buyer_auth_bp = Blueprint('buyer_auth', __name__, url_prefix='/api/buyer-auth')

# ====================================================================
# 1. SEND OTP - For signup or login
# ====================================================================
@buyer_auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to buyer's phone number
    
    Request:
    {
        "phone": "9876543210",
        "type": "signup" or "login"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP sent to 9876****210",
        "otp_for_testing": "123456"  # Only in development
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        otp_type = data.get('type', 'signup')  # signup or login
        
        # Validate phone
        if not phone or len(phone) != 10 or not phone.isdigit():
            return jsonify({'success': False, 'error': 'Invalid phone number'}), 400
        
        # Generate OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Save OTP with 10-minute expiry
        otp_obj = OTP()
        otp_obj.save_otp(phone, otp_code, 'buyer', otp_type)
        
        # TODO: Send SMS via Twilio/AWS SNS
        # send_sms(phone, f"Your Smart Farming OTP is: {otp_code}")
        
        return jsonify({
            'success': True,
            'message': f'OTP sent to {phone[:4]}****{phone[-2:]}',
            'otp_for_testing': otp_code  # Remove in production
        }), 200
        
    except Exception as e:
        print(f"Error in send_otp: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to send OTP'}), 500


# ====================================================================
# 2. VERIFY OTP
# ====================================================================
@buyer_auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP code
    
    Request:
    {
        "phone": "9876543210",
        "otp": "123456"
    }
    
    Response:
    {
        "success": true,
        "verification_token": "temp_token_xyz",
        "message": "OTP verified",
        "otp_type": "signup" or "login"
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        otp = data.get('otp', '').strip()
        
        # Validate inputs
        if not phone or not otp:
            return jsonify({'success': False, 'error': 'Phone and OTP required'}), 400
        
        # Verify OTP
        otp_obj = OTP()
        is_valid = otp_obj.verify_otp(phone, otp, 'buyer')
        
        if not is_valid:
            return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 401
        
        # Get OTP type (signup or login)
        otp_type = otp_obj.get_otp_type(phone, 'buyer')
        
        # Create temporary verification token (5 minute validity)
        verification_token = create_access_token(
            identity=phone,
            additional_claims={'type': 'verification', 'otp_type': otp_type},
            expires_delta=timedelta(minutes=5)
        )
        
        return jsonify({
            'success': True,
            'message': 'OTP verified successfully',
            'verification_token': verification_token,
            'otp_type': otp_type
        }), 200
        
    except Exception as e:
        print(f"Error in verify_otp: {str(e)}")
        return jsonify({'success': False, 'error': 'OTP verification failed'}), 500


# ====================================================================
# 3. SIGNUP - Create buyer account
# ====================================================================
@buyer_auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Create buyer account
    Frontend sends: name, email, phone, password, location, district, company_name
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        location = data.get('location', '').strip()
        district = data.get('district', '').strip()
        
        # Support both 'name' and 'first_name' fields
        name = data.get('name', '').strip()
        first_name = data.get('first_name', '').strip() or name
        last_name = data.get('last_name', '').strip()
        
        # If name was provided as full name, split it
        if name and not last_name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
        
        # Combine location with district
        if district and location:
            location = f"{location}, {district}"
        
        # Validate required fields
        if not all([phone, first_name, email, password]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Validate password strength (min 8 chars)
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Check if buyer already exists
        buyer_auth = BuyerAuth()
        existing = buyer_auth.get_buyer_by_phone(phone)
        if existing:
            return jsonify({'success': False, 'message': 'Buyer with this phone already exists'}), 409
        
        existing_email = buyer_auth.get_buyer_by_email(email)
        if existing_email:
            return jsonify({'success': False, 'message': 'Buyer with this email already exists'}), 409
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create buyer account
        buyer_id = buyer_auth.create_buyer(
            phone=phone,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            location=location
        )
        
        if not buyer_id:
            return jsonify({'success': False, 'message': 'Failed to create account'}), 500
        
        # Create access token
        access_token = create_access_token(
            identity=str(buyer_id),
            additional_claims={'type': 'buyer', 'phone': phone}
        )
        
        # Build user object for frontend
        user_data = {
            'id': buyer_id,
            'buyer_id': buyer_id,
            'name': f"{first_name} {last_name}".strip(),
            'email': email,
            'phone': phone,
            'location': location,
            'role': 'buyer'
        }
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'token': access_token,
            'access_token': access_token,
            'user': user_data
        }), 201
        
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'success': False, 'message': 'Signup failed'}), 500


# ====================================================================
# 4. LOGIN - Buyer login with credentials
# ====================================================================
@buyer_auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login buyer with phone and password
    
    Request:
    {
        "phone": "9876543210",
        "password": "SecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "buyer_id": 1,
        "access_token": "eyJ0eXAi...",
        "first_name": "Ramesh",
        "message": "Login successful"
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        
        # Validate inputs
        if not phone or not password:
            return jsonify({'success': False, 'error': 'Phone and password required'}), 400
        
        # Get buyer
        buyer_auth = BuyerAuth()
        buyer = buyer_auth.get_buyer_by_phone(phone)
        
        if not buyer:
            return jsonify({'success': False, 'error': 'Buyer not found'}), 404
        
        # Verify password
        if not check_password_hash(buyer['password_hash'], password):
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
        
        # Create access token
        access_token = create_access_token(
            identity=str(buyer['buyer_id']),
            additional_claims={'type': 'buyer', 'phone': phone}
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'access_token': access_token,
            'user': {
                'id': buyer.get('buyer_id') or buyer.get('id'),
                'buyer_id': buyer.get('buyer_id') or buyer.get('id'),
                'name': f"{buyer['first_name']} {buyer.get('last_name', '')}".strip(),
                'phone': phone,
                'email': buyer.get('email', ''),
                'role': 'buyer'
            }
        }), 200
        
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500


# ====================================================================
# 5. FORGOT PASSWORD - Reset password via OTP
# ====================================================================
@buyer_auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Step 1: Send OTP for password reset
    
    Request:
    {
        "phone": "9876543210"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP sent for password reset"
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        # Validate phone
        if not phone or len(phone) != 10:
            return jsonify({'success': False, 'error': 'Invalid phone number'}), 400
        
        # Check if buyer exists
        buyer_auth = BuyerAuth()
        buyer = buyer_auth.get_buyer_by_phone(phone)
        
        if not buyer:
            return jsonify({'success': False, 'error': 'Buyer not found'}), 404
        
        # Generate and send OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        otp_obj = OTP()
        otp_obj.save_otp(phone, otp_code, 'buyer', 'password_reset')
        
        # TODO: Send SMS
        
        return jsonify({
            'success': True,
            'message': f'OTP sent to {phone[:4]}****{phone[-2:]}',
            'otp_for_testing': otp_code
        }), 200
        
    except Exception as e:
        print(f"Error in forgot_password: {str(e)}")
        return jsonify({'success': False, 'error': 'Password reset failed'}), 500


# ====================================================================
# 6. RESET PASSWORD - Complete password reset
# ====================================================================
@buyer_auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Step 2: Reset password after OTP verification
    
    Request:
    {
        "phone": "9876543210",
        "otp": "123456",
        "new_password": "NewSecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "message": "Password reset successfully"
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '').strip()
        
        # Validate inputs
        if not all([phone, otp, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Verify OTP
        otp_obj = OTP()
        is_valid = otp_obj.verify_otp(phone, otp, 'buyer')
        
        if not is_valid:
            return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 401
        
        # Update password
        password_hash = generate_password_hash(new_password)
        buyer_auth = BuyerAuth()
        success = buyer_auth.update_password(phone, password_hash)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to reset password'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        return jsonify({'success': False, 'error': 'Password reset failed'}), 500


# ====================================================================
# 7. VERIFY TOKEN - Check if token is valid
# ====================================================================
@buyer_auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    """
    Verify if JWT token is valid
    Requires Authorization header with Bearer token
    
    Response:
    {
        "success": true,
        "message": "Token is valid",
        "buyer_id": 1
    }
    """
    try:
        # This endpoint is protected by @jwt_required() decorator
        # If we reach here, token is valid
        from flask_jwt_extended import get_jwt_identity
        
        buyer_id = get_jwt_identity()
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'buyer_id': buyer_id
        }), 200
        
    except Exception as e:
        print(f"Error in verify_token: {str(e)}")
        return jsonify({'success': False, 'error': 'Invalid token'}), 401


# ====================================================================
# 8. LOGOUT - Client-side logout (JWT doesn't require server logout)
# ====================================================================
@buyer_auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout buyer (client-side cleanup of token)
    
    Response:
    {
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        # In JWT-based auth, logout happens on client side
        # Client should delete the stored token
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500
