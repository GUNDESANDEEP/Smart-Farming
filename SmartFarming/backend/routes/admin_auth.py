"""
Admin Authentication Routes
Handles: Login, Logout, Password change, Token verification
Path: /api/admin-auth
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging

import sys
sys.path.append('..')
from models.models import Admin

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/api/admin-auth')

# ====================================================================
# DEBUG TEST - Simple test endpoint
# ====================================================================
@admin_auth_bp.route('/test', methods=['POST', 'GET'])
def test_endpoint():
    try:
        with open('C:\\Users\\SANDEEP\\OneDrive\\Documents\\Desktop\\Smart Farming\\SmartFarming\\backend\\debug.log', 'a') as f:
            f.write("TEST ENDPOINT HIT\n")
        return jsonify({'success': True, 'message': 'Test successful'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====================================================================
# 1. LOGIN - Admin login with email and password
# ====================================================================
@admin_auth_bp.route('/login', methods=['POST'])
def login():
    """
    Admin login with email and password
    
    Request:
    {
        "email": "admin@smartfarming.com",
        "password": "admin123"
    }
    
    Response:
    {
        "success": true,
        "access_token": "JWT_TOKEN",
        "admin_id": 1,
        "name": "Admin",
        "email": "admin@smartfarming.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Get admin from database
        admin = Admin.get_admin_by_email(email)
        
        if not admin:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Verify password (admin is a dict from DictCursor)
        password_hash = admin['password_hash']
        
        if not check_password_hash(password_hash, password):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Update last login
        admin_id = admin['admin_id']
        Admin.update_last_login(admin_id)
        
        # Create JWT token
        access_token = create_access_token(identity=str(admin_id), expires_delta=timedelta(days=30))
        
        return jsonify({
            'success': True,
            'token': access_token,
            'access_token': access_token,
            'admin_id': admin_id,
            'user': {
                'id': admin_id,
                'admin_id': admin_id,
                'name': admin.get('first_name', 'Admin'),
                'email': email,
                'role': 'admin',
                'admin_role': admin.get('role', 'moderator')
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error in admin login: {error_msg}")
        print(f"Full traceback:\n{traceback_str}")
        return jsonify({'success': False, 'error': f'Login failed: {error_msg}'}), 500



# ====================================================================
# 2. LOGOUT - Admin logout
# ====================================================================
@admin_auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Admin logout (client-side cleanup of token)
    
    Response:
    {
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        
        # Log the logout action
        admin = Admin()
        admin.log_action(admin_id, 'logout', 'auth', None)
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


# ====================================================================
# 3. VERIFY TOKEN - Check if admin token is valid
# ====================================================================
@admin_auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if JWT token is valid
    Requires Authorization header with Bearer token
    
    Response:
    {
        "success": true,
        "message": "Token is valid",
        "admin_id": 1,
        "role": "super_admin"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        
        claims = get_jwt()
        role = claims.get('role', 'moderator')
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'admin_id': admin_id,
            'role': role
        }), 200
        
    except Exception as e:
        print(f"Error in verify_token: {str(e)}")
        return jsonify({'success': False, 'error': 'Invalid token'}), 401


# ====================================================================
# 4. CHANGE PASSWORD
# ====================================================================
@admin_auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    Change admin password
    
    Request:
    {
        "current_password": "OldPass123!",
        "new_password": "NewPass123!"
    }
    
    Response:
    {
        "success": true,
        "message": "Password changed successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        # Validate inputs
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Both passwords required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        if current_password == new_password:
            return jsonify({'success': False, 'error': 'New password must be different from current'}), 400
        
        # Get admin
        admin = Admin()
        admin_data = admin.get_admin_by_id(admin_id)
        
        if not admin_data:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        # Verify current password
        if not check_password_hash(admin_data['password_hash'], current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Hash new password
        new_password_hash = generate_password_hash(new_password)
        
        # Update password
        success = admin.update_password(admin_id, new_password_hash)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to change password'}), 500
        
        # Log action
        admin.log_action(admin_id, 'password_change', 'auth', admin_id)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in change_password: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500


# ====================================================================
# 5. GET ADMIN PROFILE
# ====================================================================
@admin_auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current admin profile
    
    Response:
    {
        "success": true,
        "profile": {
            "admin_id": 1,
            "email": "admin@smartfarming.com",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin",
            "permissions": [...],
            "last_login": "2026-06-03T10:30:00",
            "is_active": true
        }
    }
    """
    try:
        admin_id = get_jwt_identity()
        
        admin = Admin()
        admin_data = admin.get_admin_by_id(admin_id)
        
        if not admin_data:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        # Parse permissions if JSON
        permissions = admin_data.get('permissions', [])
        if isinstance(permissions, str):
            import json
            try:
                permissions = json.loads(permissions)
            except:
                permissions = []
        
        return jsonify({
            'success': True,
            'profile': {
                'admin_id': admin_data['admin_id'],
                'email': admin_data['email'],
                'first_name': admin_data['first_name'],
                'last_name': admin_data.get('last_name', ''),
                'role': admin_data['role'],
                'permissions': permissions,
                'last_login': admin_data['last_login'].isoformat() if admin_data['last_login'] else None,
                'is_active': admin_data['is_active'],
                'created_at': admin_data['created_at'].isoformat() if admin_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch profile'}), 500


# ====================================================================
# 6. CREATE ADMIN - Only super admin can create new admins
# ====================================================================
@admin_auth_bp.route('/create-admin', methods=['POST'])
@jwt_required()
def create_admin():
    """
    Create new admin account (Super Admin only)
    
    Request:
    {
        "email": "moderator@smartfarming.com",
        "first_name": "Moderator",
        "last_name": "User",
        "role": "moderator",
        "password": "TempPass123!"
    }
    
    Response:
    {
        "success": true,
        "admin_id": 2,
        "message": "Admin created successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        role = claims.get('role', 'moderator')
        
        # Check if current admin is super admin
        if role != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can create admins'}), 403
        
        data = request.get_json()
        email = data.get('email', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        new_role = data.get('role', 'moderator')
        password = data.get('password', '').strip()
        
        # Validate inputs
        if not all([email, first_name, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        if new_role not in ['super_admin', 'moderator', 'analyst']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Check if email already exists
        admin = Admin()
        existing = admin.get_admin_by_email(email)
        if existing:
            return jsonify({'success': False, 'error': 'Admin with this email already exists'}), 409
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create admin
        new_admin_id = admin.create_admin(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=new_role
        )
        
        if not new_admin_id:
            return jsonify({'success': False, 'error': 'Failed to create admin'}), 500
        
        # Log action
        admin.log_action(admin_id, 'create_admin', 'admins', new_admin_id)
        
        return jsonify({
            'success': True,
            'admin_id': new_admin_id,
            'message': 'Admin created successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in create_admin: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create admin'}), 500
