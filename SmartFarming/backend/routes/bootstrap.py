"""
Bootstrap routes for initial setup
WARNING: These routes should be disabled in production after setup
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.models import BaseModel
import os

bootstrap_bp = Blueprint('bootstrap', __name__, url_prefix='/api/bootstrap')

# ====================================================================
# Bootstrap: Initialize Database and Create First Admin
# ====================================================================
@bootstrap_bp.route('/init-admin', methods=['POST'])
def init_admin():
    """
    Initialize admin account for first-time setup
    
    Request:
    {
        "email": "gundesandeep2005@gmail.com",
        "password": "Sandy@7982",
        "name": "Sandeep Gunde"
    }
    
    Headers:
    X-Setup-Key: initial-setup-key-change-me (optional, for security)
    """
    try:
        # Optional security check
        setup_key = os.getenv('SETUP_KEY', 'initial-setup-key-change-me')
        provided_key = request.headers.get('X-Setup-Key', '')
        
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        name = data.get('name', 'Admin').strip()
        
        # Validate input
        if not email:
            return {'success': False, 'error': 'Email is required'}, 400
        if not password:
            return {'success': False, 'error': 'Password is required'}, 400
        if len(password) < 6:
            return {'success': False, 'error': 'Password too short'}, 400
        
        try:
            # Check if any admin exists
            result = BaseModel.execute_query(
                "SELECT COUNT(*) as count FROM admins", fetch_one=True
            )
            admin_count = result['count'] if result else 0
            
            if admin_count > 0:
                return {
                    'success': False,
                    'error': 'Admin account already exists'
                }, 409
            
            # Create password hash
            password_hash = generate_password_hash(password)
            
            # Insert admin
            admin_id = BaseModel.execute_insert(
                """INSERT INTO admins (email, password_hash, first_name, role, is_active, created_at)
                   VALUES (%s, %s, %s, %s, TRUE, NOW())""",
                (email, password_hash, name, 'super_admin')
            )
            
            return {
                'success': True,
                'message': 'Admin account created successfully',
                'admin_id': admin_id,
                'email': email
            }, 201
            
        except Exception as db_error:
            raise db_error
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }, 500


@bootstrap_bp.route('/health', methods=['GET'])
def bootstrap_health():
    """Check bootstrap endpoint is available"""
    return {
        'status': 'available',
        'message': 'Bootstrap endpoint ready',
        'available_endpoints': ['/api/bootstrap/init-admin', '/api/bootstrap/health']
    }, 200
