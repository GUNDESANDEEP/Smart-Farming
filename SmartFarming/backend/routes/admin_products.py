"""
Admin Product Management Routes
Handles: Product approval/rejection, fake product removal, category management
Path: /api/admin/products
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

import sys
sys.path.append('..')
from models.models import Admin, Product, Farmer

admin_products_bp = Blueprint('admin_products', __name__, url_prefix='/api/admin/products')

# ====================================================================
# 0. GET ALL PRODUCTS (ROOT) - For admin dashboard
# ====================================================================
@admin_products_bp.route('/', methods=['GET'])
@jwt_required()
def list_all_products():
    """Get all products for admin - simple working endpoint"""
    try:
        product_obj = Product()
        products = product_obj.get_all_products(limit=100, offset=0, status='approved')
        
        formatted = []
        for p in products:
            formatted.append({
                'id': p.get('id') or p.get('product_id'),
                'name': p.get('name', ''),
                'description': p.get('description', ''),
                'category': p.get('category', ''),
                'price': float(p.get('price', 0)),
                'quantity': float(p.get('quantity', 0)),
                'unit': p.get('unit', 'kg'),
                'status': p.get('status', 'approved'),
                'farmer_id': p.get('farmer_id'),
                'farmer_name': p.get('farmer_name', 'Unknown'),
                'created_at': p['created_at'].isoformat() if p.get('created_at') else None,
            })
        
        return jsonify({
            'success': True,
            'products': formatted,
            'total': len(formatted)
        }), 200
    except Exception as e:
        print(f"Error in list_all_products: {str(e)}")
        return jsonify({'success': True, 'products': [], 'total': 0}), 200


# ====================================================================
# 1. GET PENDING PRODUCTS
# ====================================================================
@admin_products_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_products():
    """
    Get all pending products awaiting approval
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - sort_by: created_at or farmer_name (default: created_at)
    
    Response:
    {
        "success": true,
        "products": [
            {
                "approval_id": 1,
                "product_id": 45,
                "name": "Organic Tomatoes",
                "category": "Vegetables",
                "farmer_id": 12,
                "farmer_name": "Ravi Kumar",
                "price": 45.99,
                "quantity": 100,
                "image_url": "...",
                "submitted_date": "2026-06-01T10:00:00",
                "status": "pending"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        sort_by = request.args.get('sort_by', default='created_at')
        
        product_obj = Product()
        products, total = product_obj.get_pending_approvals_paginated(
            page=page,
            limit=limit,
            sort_by=sort_by
        )
        
        formatted_products = []
        for product in products:
            formatted_products.append({
                'approval_id': product.get('approval_id'),
                'product_id': product['product_id'],
                'name': product['product_name'],
                'category': product.get('category', ''),
                'farmer_id': product['farmer_id'],
                'farmer_name': product.get('farmer_name', ''),
                'price': float(product['price']),
                'quantity': product['quantity'],
                'image_url': product.get('image_url', ''),
                'description': product.get('description', ''),
                'submitted_date': product['created_at'].isoformat() if product['created_at'] else None,
                'status': product.get('status', 'pending')
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'products': formatted_products,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_pending_products: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch pending products'}), 500


# ====================================================================
# 2. APPROVE PRODUCT
# ====================================================================
@admin_products_bp.route('/<int:product_id>/approve', methods=['POST'])
@jwt_required()
def approve_product(product_id):
    """
    Approve a pending product
    
    Request:
    {
        "notes": "Product quality verified"
    }
    
    Response:
    {
        "success": true,
        "message": "Product approved successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json() or {}
        notes = data.get('notes', '').strip()
        
        product_obj = Product()
        product_data = product_obj.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Update product approval status
        success = product_obj.update_approval_status(
            product_id=product_id,
            status='approved',
            reviewed_by=admin_id,
            notes=notes
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to approve product'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='approve_product',
            module='products',
            entity_id=product_id,
            description=notes or f'Approved product: {product_data["product_name"]}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Product approved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in approve_product: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to approve product'}), 500


# ====================================================================
# 3. REJECT PRODUCT
# ====================================================================
@admin_products_bp.route('/<int:product_id>/reject', methods=['POST'])
@jwt_required()
def reject_product(product_id):
    """
    Reject a pending product with reason
    
    Request:
    {
        "reason": "Image quality is poor / Prohibited product"
    }
    
    Response:
    {
        "success": true,
        "message": "Product rejected successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'error': 'Rejection reason required'}), 400
        
        product_obj = Product()
        product_data = product_obj.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Update product approval status
        success = product_obj.update_approval_status(
            product_id=product_id,
            status='rejected',
            reviewed_by=admin_id,
            reason=reason
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to reject product'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='reject_product',
            module='products',
            entity_id=product_id,
            description=f'Rejected: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Product rejected successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in reject_product: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to reject product'}), 500


# ====================================================================
# 4. FLAG PRODUCT FOR REVIEW
# ====================================================================
@admin_products_bp.route('/<int:product_id>/flag', methods=['POST'])
@jwt_required()
def flag_product(product_id):
    """
    Flag a product for further review (suspicious/needs manual check)
    
    Request:
    {
        "reason": "Potentially fake product / Suspicious pricing"
    }
    
    Response:
    {
        "success": true,
        "message": "Product flagged successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'error': 'Flag reason required'}), 400
        
        product_obj = Product()
        product_data = product_obj.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Update product approval status to flagged
        success = product_obj.update_approval_status(
            product_id=product_id,
            status='flagged',
            reviewed_by=admin_id,
            notes=reason
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to flag product'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='flag_product',
            module='products',
            entity_id=product_id,
            description=f'Flagged: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Product flagged successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in flag_product: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to flag product'}), 500


# ====================================================================
# 5. DELETE PRODUCT (Remove fake/spam)
# ====================================================================
@admin_products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Delete/remove a product (for fake or policy-violating products)
    
    Request:
    {
        "reason": "Violates platform policy / Fake product"
    }
    
    Response:
    {
        "success": true,
        "message": "Product removed successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin' and claims.get('role') != 'moderator':
            return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin removal')
        
        product_obj = Product()
        product_data = product_obj.get_product_by_id(product_id)
        
        if not product_data:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Delete product
        success = product_obj.delete_product(product_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete product'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='delete_product',
            module='products',
            entity_id=product_id,
            description=f'Deleted: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Product removed successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_product: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete product'}), 500


# ====================================================================
# 6. GET ALL PRODUCTS
# ====================================================================
@admin_products_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_products():
    """
    Get all products with approval status
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - status: Filter by approval status (pending, approved, rejected, flagged)
    
    Response:
    {
        "success": true,
        "products": [...]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        status = request.args.get('status', default=None)
        
        product_obj = Product()
        products, total = product_obj.get_all_products_paginated(
            page=page,
            limit=limit,
            approval_status=status
        )
        
        formatted_products = []
        for product in products:
            formatted_products.append({
                'product_id': product['product_id'],
                'name': product['product_name'],
                'category': product.get('category', ''),
                'farmer_id': product['farmer_id'],
                'farmer_name': product.get('farmer_name', ''),
                'price': float(product['price']),
                'quantity': product['quantity'],
                'approval_status': product.get('approval_status', 'approved'),
                'created_at': product['created_at'].isoformat() if product['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'products': formatted_products,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_all_products: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch products'}), 500


# ====================================================================
# 7. GET CATEGORIES
# ====================================================================
@admin_products_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    Get all product categories
    
    Response:
    {
        "success": true,
        "categories": [
            {
                "category_id": 1,
                "name": "Vegetables",
                "description": "Fresh vegetables",
                "icon_url": "...",
                "is_active": true,
                "product_count": 145
            }
        ]
    }
    """
    try:
        product_obj = Product()
        categories = product_obj.get_all_categories()
        
        formatted_categories = []
        for cat in categories:
            formatted_categories.append({
                'category_id': cat['category_id'],
                'name': cat['name'],
                'description': cat.get('description', ''),
                'icon_url': cat.get('icon_url', ''),
                'is_active': cat['is_active'],
                'product_count': cat.get('product_count', 0)
            })
        
        return jsonify({
            'success': True,
            'categories': formatted_categories
        }), 200
        
    except Exception as e:
        print(f"Error in get_categories: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch categories'}), 500


# ====================================================================
# 8. CREATE CATEGORY
# ====================================================================
@admin_products_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """
    Create new product category
    
    Request:
    {
        "name": "Organic Fruits",
        "description": "Organic fruits from certified farms",
        "icon_url": "https://...",
        "parent_category_id": null
    }
    
    Response:
    {
        "success": true,
        "category_id": 8,
        "message": "Category created successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can create categories'}), 403
        
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        icon_url = data.get('icon_url', '').strip()
        parent_category_id = data.get('parent_category_id')
        
        if not name:
            return jsonify({'success': False, 'error': 'Category name required'}), 400
        
        product_obj = Product()
        category_id = product_obj.create_category(
            name=name,
            description=description,
            icon_url=icon_url,
            parent_category_id=parent_category_id,
            created_by=admin_id
        )
        
        if not category_id:
            return jsonify({'success': False, 'error': 'Failed to create category'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='create_category',
            module='products',
            entity_id=category_id,
            description=f'Created category: {name}'
        )
        
        return jsonify({
            'success': True,
            'category_id': category_id,
            'message': 'Category created successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in create_category: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create category'}), 500


# ====================================================================
# 9. UPDATE CATEGORY
# ====================================================================
@admin_products_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    """
    Update product category
    
    Request:
    {
        "name": "Updated Category",
        "description": "Updated description",
        "is_active": true
    }
    
    Response:
    {
        "success": true,
        "message": "Category updated successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can update categories'}), 403
        
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        is_active = data.get('is_active')
        
        product_obj = Product()
        success = product_obj.update_category(
            category_id=category_id,
            name=name or None,
            description=description or None,
            is_active=is_active
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update category'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='update_category',
            module='products',
            entity_id=category_id,
            description=f'Updated category'
        )
        
        return jsonify({
            'success': True,
            'message': 'Category updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_category: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update category'}), 500


# ====================================================================
# 10. DELETE CATEGORY
# ====================================================================
@admin_products_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """
    Delete product category
    
    Response:
    {
        "success": true,
        "message": "Category deleted successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        if claims.get('role') != 'super_admin':
            return jsonify({'success': False, 'error': 'Only super admin can delete categories'}), 403
        
        product_obj = Product()
        success = product_obj.delete_category(category_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete category'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='delete_category',
            module='products',
            entity_id=category_id,
            description=f'Deleted category'
        )
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_category: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete category'}), 500
