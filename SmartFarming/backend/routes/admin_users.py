"""
Admin User Management Routes
Handles: Approve farmers, manage buyers, block/unblock users, delete accounts
Path: /api/admin/users
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta

import sys
sys.path.append('..')
from models.models import Admin, Farmer, Buyer

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/api/admin/users')

# ====================================================================
# Helper: Check if admin has permission
# ====================================================================
def check_admin_permission(required_role):
    claims = get_jwt()
    role = claims.get('role', 'moderator')
    return role in ['super_admin'] or (required_role == 'moderator' and role == 'moderator')


# ====================================================================
# 1. GET ALL FARMERS
# ====================================================================
@admin_users_bp.route('/farmers', methods=['GET'])
@jwt_required()
def get_all_farmers():
    """
    Get all farmers with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - status: Filter by status (approved, pending, suspended)
    - search: Search by name/phone/email
    
    Response:
    {
        "success": true,
        "farmers": [
            {
                "farmer_id": 1,
                "name": "Ravi Kumar",
                "phone": "9876543210",
                "email": "ravi@example.com",
                "location": "Mumbai, Maharashtra",
                "status": "approved",
                "products": 15,
                "total_sales": 450000,
                "rating": 4.5,
                "joined_date": "2025-01-15T10:00:00"
            }
        ],
        "pagination": {
            "total": 1250,
            "page": 1,
            "limit": 20,
            "pages": 63
        }
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        status = request.args.get('status', default=None)
        search = request.args.get('search', default=None)
        
        if page < 1 or limit < 1:
            return jsonify({'success': False, 'error': 'Invalid pagination parameters'}), 400
        
        farmer_obj = Farmer()
        farmers, total = farmer_obj.get_all_farmers_paginated(
            page=page,
            limit=limit,
            status=status,
            search=search
        )
        
        formatted_farmers = []
        for farmer in farmers:
            formatted_farmers.append({
                'farmer_id': farmer['farmer_id'],
                'name': farmer['name'],
                'phone': farmer['phone'],
                'email': farmer['email'],
                'location': farmer['location'],
                'status': farmer.get('status', 'approved'),
                'products': farmer.get('product_count', 0),
                'total_sales': float(farmer.get('total_sales', 0)),
                'rating': float(farmer.get('rating', 0)),
                'joined_date': farmer['created_at'].isoformat() if farmer['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'farmers': formatted_farmers,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_all_farmers: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch farmers'}), 500


# ====================================================================
# 2. GET FARMER DETAILS
# ====================================================================
@admin_users_bp.route('/farmers/<int:farmer_id>', methods=['GET'])
@jwt_required()
def get_farmer_details(farmer_id):
    """
    Get detailed farmer information
    
    Response:
    {
        "success": true,
        "farmer": {
            "farmer_id": 1,
            "name": "Ravi Kumar",
            "phone": "9876543210",
            "email": "ravi@example.com",
            "location": "Mumbai, Maharashtra",
            "status": "approved",
            "bio": "Organic vegetable farmer",
            "rating": 4.5,
            "total_products": 15,
            "total_orders": 234,
            "total_sales": 450000,
            "reviews_count": 89,
            "joined_date": "2025-01-15T10:00:00",
            "documents": [...]
        }
    }
    """
    try:
        farmer_obj = Farmer()
        farmer_data = farmer_obj.get_farmer_by_id(farmer_id)
        
        if not farmer_data:
            return jsonify({'success': False, 'error': 'Farmer not found'}), 404
        
        return jsonify({
            'success': True,
            'farmer': {
                'farmer_id': farmer_data['farmer_id'],
                'name': farmer_data['name'],
                'phone': farmer_data['phone'],
                'email': farmer_data['email'],
                'location': farmer_data['location'],
                'status': farmer_data.get('status', 'approved'),
                'bio': farmer_data.get('bio', ''),
                'rating': float(farmer_data.get('rating', 0)),
                'total_products': farmer_data.get('product_count', 0),
                'total_orders': farmer_data.get('order_count', 0),
                'total_sales': float(farmer_data.get('total_sales', 0)),
                'reviews_count': farmer_data.get('reviews_count', 0),
                'joined_date': farmer_data['created_at'].isoformat() if farmer_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_farmer_details: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch farmer details'}), 500


# ====================================================================
# 3. APPROVE FARMER
# ====================================================================
@admin_users_bp.route('/farmers/<int:farmer_id>/approve', methods=['PUT'])
@jwt_required()
def approve_farmer(farmer_id):
    """
    Approve pending farmer for selling
    
    Request:
    {
        "notes": "Documents verified"
    }
    
    Response:
    {
        "success": true,
        "message": "Farmer approved successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json() or {}
        notes = data.get('notes', '').strip()
        
        farmer_obj = Farmer()
        farmer_data = farmer_obj.get_farmer_by_id(farmer_id)
        
        if not farmer_data:
            return jsonify({'success': False, 'error': 'Farmer not found'}), 404
        
        # Update farmer status
        success = farmer_obj.update_status(farmer_id, 'approved')
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to approve farmer'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='approve_farmer',
            module='users',
            entity_id=farmer_id,
            description=notes or f'Approved farmer {farmer_data["name"]}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Farmer approved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in approve_farmer: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to approve farmer'}), 500


# ====================================================================
# 4. DELETE FARMER
# ====================================================================
@admin_users_bp.route('/farmers/<int:farmer_id>', methods=['DELETE'])
@jwt_required()
def delete_farmer(farmer_id):
    """
    Delete farmer account and all associated data
    
    Request:
    {
        "reason": "Fake account / Violating terms"
    }
    
    Response:
    {
        "success": true,
        "message": "Farmer deleted successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can delete farmers'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin deletion')
        
        farmer_obj = Farmer()
        farmer_data = farmer_obj.get_farmer_by_id(farmer_id)
        
        if not farmer_data:
            return jsonify({'success': False, 'error': 'Farmer not found'}), 404
        
        # Delete farmer
        success = farmer_obj.delete_farmer(farmer_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete farmer'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='delete_farmer',
            module='users',
            entity_id=farmer_id,
            description=f'Deleted farmer: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Farmer deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_farmer: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete farmer'}), 500


# ====================================================================
# 5. GET ALL BUYERS
# ====================================================================
@admin_users_bp.route('/buyers', methods=['GET'])
@jwt_required()
def get_all_buyers():
    """
    Get all buyers with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - search: Search by name/phone/email
    
    Response:
    {
        "success": true,
        "buyers": [
            {
                "buyer_id": 1,
                "name": "Asha Patel",
                "phone": "9876543210",
                "email": "asha@example.com",
                "location": "Delhi",
                "total_orders": 45,
                "total_spent": 120000,
                "rating": 4.3,
                "joined_date": "2025-01-20T10:00:00"
            }
        ],
        "pagination": {...}
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        search = request.args.get('search', default=None)
        
        if page < 1 or limit < 1:
            return jsonify({'success': False, 'error': 'Invalid pagination parameters'}), 400
        
        buyer_obj = Buyer()
        buyers, total = buyer_obj.get_all_buyers_paginated(
            page=page,
            limit=limit,
            search=search
        )
        
        formatted_buyers = []
        for buyer in buyers:
            formatted_buyers.append({
                'buyer_id': buyer['buyer_id'],
                'name': buyer['name'],
                'phone': buyer['phone'],
                'email': buyer['email'],
                'location': buyer.get('location', ''),
                'total_orders': buyer.get('order_count', 0),
                'total_spent': float(buyer.get('total_spent', 0)),
                'rating': float(buyer.get('rating', 0)),
                'joined_date': buyer['created_at'].isoformat() if buyer['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'buyers': formatted_buyers,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_all_buyers: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch buyers'}), 500


# ====================================================================
# 6. GET BUYER DETAILS
# ====================================================================
@admin_users_bp.route('/buyers/<int:buyer_id>', methods=['GET'])
@jwt_required()
def get_buyer_details(buyer_id):
    """
    Get detailed buyer information
    
    Response:
    {
        "success": true,
        "buyer": {
            "buyer_id": 1,
            "name": "Asha Patel",
            "phone": "9876543210",
            "email": "asha@example.com",
            "location": "Delhi",
            "total_orders": 45,
            "total_spent": 120000,
            "rating": 4.3,
            "reviews_count": 23,
            "joined_date": "2025-01-20T10:00:00"
        }
    }
    """
    try:
        buyer_obj = Buyer()
        buyer_data = buyer_obj.get_buyer_by_id(buyer_id)
        
        if not buyer_data:
            return jsonify({'success': False, 'error': 'Buyer not found'}), 404
        
        return jsonify({
            'success': True,
            'buyer': {
                'buyer_id': buyer_data['buyer_id'],
                'name': buyer_data['name'],
                'phone': buyer_data['phone'],
                'email': buyer_data['email'],
                'location': buyer_data.get('location', ''),
                'total_orders': buyer_data.get('order_count', 0),
                'total_spent': float(buyer_data.get('total_spent', 0)),
                'rating': float(buyer_data.get('rating', 0)),
                'reviews_count': buyer_data.get('reviews_count', 0),
                'joined_date': buyer_data['created_at'].isoformat() if buyer_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_buyer_details: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch buyer details'}), 500


# ====================================================================
# 7. DELETE BUYER
# ====================================================================
@admin_users_bp.route('/buyers/<int:buyer_id>', methods=['DELETE'])
@jwt_required()
def delete_buyer(buyer_id):
    """
    Delete buyer account
    
    Request:
    {
        "reason": "Spam / Fraud account"
    }
    
    Response:
    {
        "success": true,
        "message": "Buyer deleted successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can delete buyers'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin deletion')
        
        buyer_obj = Buyer()
        buyer_data = buyer_obj.get_buyer_by_id(buyer_id)
        
        if not buyer_data:
            return jsonify({'success': False, 'error': 'Buyer not found'}), 404
        
        # Delete buyer
        success = buyer_obj.delete_buyer(buyer_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete buyer'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='delete_buyer',
            module='users',
            entity_id=buyer_id,
            description=f'Deleted buyer: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Buyer deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_buyer: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete buyer'}), 500


# ====================================================================
# 8. BLOCK USER (Farmer or Buyer)
# ====================================================================
@admin_users_bp.route('/block', methods=['POST'])
@jwt_required()
def block_user():
    """
    Block farmer or buyer account temporarily or permanently
    
    Request:
    {
        "user_type": "farmer" or "buyer",
        "user_id": 123,
        "reason": "Suspicious activity",
        "is_permanent": false,
        "expires_days": 30
    }
    
    Response:
    {
        "success": true,
        "block_id": 1,
        "message": "User blocked successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        user_type = data.get('user_type', '').strip()
        user_id = data.get('user_id')
        reason = data.get('reason', '').strip()
        is_permanent = data.get('is_permanent', False)
        expires_days = data.get('expires_days', 30)
        
        # Validate inputs
        if user_type not in ['farmer', 'buyer']:
            return jsonify({'success': False, 'error': 'Invalid user type'}), 400
        
        if not user_id or not reason:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Create block
        admin = Admin()
        expires_at = None if is_permanent else (datetime.now() + timedelta(days=expires_days))
        
        block_id = admin.create_user_block(
            user_type=user_type,
            user_id=user_id,
            reason=reason,
            blocked_by=admin_id,
            is_permanent=is_permanent,
            expires_at=expires_at
        )
        
        if not block_id:
            return jsonify({'success': False, 'error': 'Failed to block user'}), 500
        
        # Log action
        admin.log_action(
            admin_id=admin_id,
            action='block_user',
            module='users',
            entity_id=user_id,
            description=f'Blocked {user_type}: {reason}'
        )
        
        return jsonify({
            'success': True,
            'block_id': block_id,
            'message': 'User blocked successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in block_user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to block user'}), 500


# ====================================================================
# 9. UNBLOCK USER
# ====================================================================
@admin_users_bp.route('/blocks/<int:block_id>/unblock', methods=['PUT'])
@jwt_required()
def unblock_user(block_id):
    """
    Unblock previously blocked user
    
    Response:
    {
        "success": true,
        "message": "User unblocked successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        
        admin = Admin()
        success = admin.remove_user_block(block_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to unblock user'}), 500
        
        # Log action
        admin.log_action(
            admin_id=admin_id,
            action='unblock_user',
            module='users',
            entity_id=block_id,
            description='Unblocked user'
        )
        
        return jsonify({
            'success': True,
            'message': 'User unblocked successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in unblock_user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to unblock user'}), 500


# ====================================================================
# 10. GET BLOCKED USERS
# ====================================================================
@admin_users_bp.route('/blocks', methods=['GET'])
@jwt_required()
def get_blocked_users():
    """
    Get list of all blocked users
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    
    Response:
    {
        "success": true,
        "blocks": [
            {
                "block_id": 1,
                "user_type": "farmer",
                "user_id": 123,
                "user_name": "Ravi Kumar",
                "reason": "Suspicious activity",
                "blocked_by": "Admin",
                "blocked_date": "2026-05-01T10:00:00",
                "is_permanent": false,
                "expires_at": "2026-05-31T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        
        admin = Admin()
        blocks, total = admin.get_blocked_users(page=page, limit=limit)
        
        formatted_blocks = []
        for block in blocks:
            formatted_blocks.append({
                'block_id': block['block_id'],
                'user_type': 'farmer' if block['farmer_id'] else 'buyer',
                'user_id': block['farmer_id'] or block['buyer_id'],
                'user_name': block.get('user_name', 'Unknown'),
                'reason': block['reason'],
                'blocked_by': block.get('admin_name', 'System'),
                'blocked_date': block['created_at'].isoformat() if block['created_at'] else None,
                'is_permanent': block['is_permanent'],
                'expires_at': block['expires_at'].isoformat() if block['expires_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'blocks': formatted_blocks,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_blocked_users: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch blocked users'}), 500
