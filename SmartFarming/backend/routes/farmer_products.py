"""
Farmer Module - Complete Product and Order Management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    User, Farmer, Product, Order, Review, Notification, Wallet,
    Transaction, BaseModel
)
from datetime import datetime
try:
    from slugify import slugify
except ImportError:
    def slugify(text):
        import re
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
import json
import uuid

farmer_bp = Blueprint('farmer', __name__, url_prefix='/api/farmer')

# ============================================================================
# MIDDLEWARE - Verify User is Farmer
# ============================================================================

def farmer_required(f):
    """Decorator to ensure user is a farmer"""
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        kwargs['farmer'] = farmer
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# ============================================================================
# DASHBOARD
# ============================================================================

@farmer_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard(user=None, farmer=None):
    """Get farmer dashboard statistics"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        farmer_id = farmer['id']
        
        # Product stats
        prod_stats = BaseModel.execute_query(
            "SELECT COUNT(*) as total_products FROM products WHERE farmer_id = %s", 
            (farmer_id,), fetch_one=True
        ) or {'total_products': 0}
        
        # Order stats
        order_stats = BaseModel.execute_query(
            """SELECT COUNT(*) as total_orders, 
                      SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered_orders,
                      COALESCE(SUM(CASE WHEN status='delivered' THEN total_amount ELSE 0 END), 0) as total_earnings
               FROM orders WHERE farmer_id = %s""",
            (farmer_id,), fetch_one=True
        ) or {'total_orders': 0, 'delivered_orders': 0, 'total_earnings': 0}
        
        # Rating stats
        rating_stats = BaseModel.execute_query(
            """SELECT COALESCE(AVG(product_rating), 0) as average_rating, COUNT(*) as total_ratings 
               FROM buyer_reviews WHERE farmer_id = %s""",
            (farmer_id,), fetch_one=True
        ) or {'average_rating': 0, 'total_ratings': 0}
        
        # Recent products
        recent_products = BaseModel.execute_query(
            "SELECT id, name, price, quantity, unit, category, is_available FROM products WHERE farmer_id = %s ORDER BY created_at DESC LIMIT 5",
            (farmer_id,), fetch_all=True
        ) or []
        
        return jsonify({
            'success': True,
            'farmer_id': farmer_id,
            'name': f"{farmer.get('first_name', '')} {farmer.get('last_name', '')}".strip(),
            'location': farmer.get('location', ''),
            'stats': {
                'total_products': prod_stats.get('total_products', 0) or 0,
                'total_orders': order_stats.get('total_orders', 0) or 0,
                'delivered_orders': order_stats.get('delivered_orders', 0) or 0,
                'total_earnings': float(order_stats.get('total_earnings', 0) or 0),
                'average_rating': round(float(rating_stats.get('average_rating', 0) or 0), 1),
                'total_ratings': rating_stats.get('total_ratings', 0) or 0
            },
            'recent_products': recent_products
        }), 200
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PRODUCT MANAGEMENT
# ============================================================================

@farmer_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create new product"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validation
        name = str(data.get('name', '')).strip()
        category = str(data.get('category', 'Others')).strip()
        unit = str(data.get('unit', 'kg')).strip()
        description = str(data.get('description', '')).strip()
        location = str(data.get('location', '')).strip()
        
        # Convert to numbers FIRST
        try:
            price = float(data.get('price', 0))
            quantity = float(data.get('quantity', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Price and quantity must be numbers'}), 400
        
        if not name:
            return jsonify({'error': 'Product name is required'}), 400
        if price <= 0:
            return jsonify({'error': 'Price must be positive'}), 400
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        images = json.dumps(data.get('images', []))
        organic = 1 if data.get('organic') else 0
        harvest_date = data.get('harvest_date')
        
        product_id = BaseModel.execute_insert(
            """INSERT INTO products (farmer_id, name, category, description, price, quantity, unit, 
                                     images, organic, harvest_date, location, is_available, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'pending')""",
            (farmer['id'], name, category, description, price, quantity, unit,
             images, organic, harvest_date, location)
        )
        
        return jsonify({
            'success': True,
            'message': 'Product created! Waiting for admin approval.',
            'product': {
                'id': product_id,
                'name': name,
                'category': category,
                'description': description,
                'price': price,
                'quantity': quantity,
                'unit': unit,
                'location': location,
                'status': 'pending',
            }
        }), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    """Get farmer's products"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        if not farmer:
            return jsonify({'error': 'Farmer profile not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        products = Product.get_by_farmer(farmer['id'], limit=limit, offset=offset)
        
        return jsonify({
            'products': products,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get products error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get product details"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Verify product belongs to farmer
        if product['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'product': product}), 200
    
    except Exception as e:
        print(f"Get product error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update product"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if product['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        update_fields = {}
        
        allowed_fields = ['name', 'description', 'detailed_description', 'quantity',
                         'price', 'min_order_quantity', 'max_order_quantity',
                         'discount_percentage', 'harvest_date', 'expiry_date',
                         'images', 'specifications', 'certifications', 'is_organic',
                         'is_available']
        
        for field in allowed_fields:
            if field in data:
                if field in ['images', 'specifications', 'certifications']:
                    update_fields[field] = json.dumps(data[field])
                else:
                    update_fields[field] = data[field]
        
        Product.update(product_id, **update_fields)
        
        return jsonify({'message': 'Product updated successfully'}), 200
    
    except Exception as e:
        print(f"Update product error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete product"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if product['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        Product.update(product_id, is_available=False)
        
        return jsonify({'message': 'Product deleted successfully'}), 200
    
    except Exception as e:
        print(f"Delete product error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

@farmer_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get farmer's orders"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        if not farmer:
            return jsonify({'error': 'Farmer profile not found'}), 404
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        orders = Order.get_farmer_orders(farmer['id'], status=status, limit=limit, offset=offset)
        
        return jsonify({
            'orders': orders,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get orders error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get order details"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'order': order}), 200
    
    except Exception as e:
        print(f"Get order error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'rejected']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        Order.update_status(order_id, new_status)
        
        # Send notification to buyer
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Status Updated',
            message=f'Your order #{order["order_number"]} status has been updated to {new_status}',
            notification_type='order'
        )
        
        return jsonify({'message': 'Order status updated successfully'}), 200
    
    except Exception as e:
        print(f"Update order status error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/orders/<int:order_id>/accept', methods=['POST'])
@jwt_required()
def accept_order(order_id):
    """Accept order"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if order['status'] != 'pending':
            return jsonify({'error': 'Can only accept pending orders'}), 400
        
        Order.update_status(order_id, 'confirmed')
        
        # Send notification
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Accepted',
            message=f'Your order #{order["order_number"]} has been accepted',
            notification_type='order'
        )
        
        return jsonify({'message': 'Order accepted successfully'}), 200
    
    except Exception as e:
        print(f"Accept order error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@jwt_required()
def reject_order(order_id):
    """Reject order"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['farmer_id'] != farmer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if order['status'] != 'pending':
            return jsonify({'error': 'Can only reject pending orders'}), 400
        
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        Order.update_status(order_id, 'rejected')
        BaseModel.execute_query(
            "UPDATE orders SET rejection_reason = %s WHERE id = %s",
            (reason, order_id)
        )
        
        # Send notification
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Order Rejected',
            message=f'Your order #{order["order_number"]} has been rejected. Reason: {reason}',
            notification_type='order'
        )
        
        return jsonify({'message': 'Order rejected successfully'}), 200
    
    except Exception as e:
        print(f"Reject order error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EARNINGS & WALLET
# ============================================================================

@farmer_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_earnings():
    """Get farmer earnings from orders + receipts"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        farmer_id = farmer['id']
        
        # Total from receipts (direct sales + online)
        receipt_earnings = BaseModel.execute_query(
            """SELECT 
                COALESCE(SUM(grand_total), 0) as total,
                COALESCE(SUM(CASE WHEN MONTH(created_at) = MONTH(NOW()) AND YEAR(created_at) = YEAR(NOW()) THEN grand_total ELSE 0 END), 0) as this_month,
                COALESCE(SUM(CASE WHEN DATE(created_at) = CURDATE() THEN grand_total ELSE 0 END), 0) as today,
                COUNT(*) as total_sales
               FROM receipts WHERE farmer_id = %s AND payment_status = 'completed'""",
            (farmer_id,), fetch_one=True
        ) or {'total': 0, 'this_month': 0, 'today': 0, 'total_sales': 0}
        
        # Also try orders table for backward compatibility
        order_earnings = BaseModel.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE farmer_id = %s AND status = 'delivered'",
            (farmer_id,), fetch_one=True
        ) or {'total': 0}
        
        # Recent sales (last 10)
        recent_sales = BaseModel.execute_query(
            """SELECT receipt_id, buyer_name, grand_total, payment_type, created_at 
               FROM receipts WHERE farmer_id = %s ORDER BY created_at DESC LIMIT 10""",
            (farmer_id,), fetch_all=True
        ) or []
        
        # Serialize dates and decimals
        for sale in recent_sales:
            if sale.get('created_at'):
                sale['created_at'] = sale['created_at'].isoformat() if hasattr(sale['created_at'], 'isoformat') else str(sale['created_at'])
            if sale.get('grand_total') is not None:
                sale['grand_total'] = float(sale['grand_total'])
        
        total = float(receipt_earnings['total']) + float(order_earnings['total'])
        
        return jsonify({
            'success': True,
            'total': total,
            'total_earnings': total,
            'thisMonth': float(receipt_earnings['this_month']),
            'today': float(receipt_earnings['today']),
            'total_sales': int(receipt_earnings['total_sales']),
            'pending': 0,
            'recent_sales': recent_sales,
        }), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get transaction history"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT * FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        transactions = BaseModel.execute_query(query, (user_id, limit, offset), fetch_all=True)
        
        return jsonify({
            'transactions': transactions,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get transactions error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REVIEWS & RATINGS
# ============================================================================

@farmer_bp.route('/reviews', methods=['GET'])
@jwt_required()
def get_reviews():
    """Get reviews for farmer's products"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT r.*, p.name as product_name, u.first_name, u.last_name
        FROM reviews r
        LEFT JOIN products p ON r.product_id = p.id
        LEFT JOIN buyers b ON r.buyer_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE p.farmer_id = %s
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
        """
        
        reviews = BaseModel.execute_query(query, (farmer['id'], limit, offset), fetch_all=True)
        
        return jsonify({
            'reviews': reviews,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get reviews error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/ratings', methods=['GET'])
@jwt_required()
def get_ratings():
    """Get farmer ratings"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT fr.*, u.first_name, u.last_name
        FROM farmer_ratings fr
        LEFT JOIN buyers b ON fr.buyer_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE fr.farmer_id = %s
        ORDER BY fr.created_at DESC
        LIMIT %s OFFSET %s
        """
        
        ratings = BaseModel.execute_query(query, (farmer['id'], limit, offset), fetch_all=True)
        
        return jsonify({
            'ratings': ratings,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get ratings error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

@farmer_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_farmer_profile():
    """Get farmer profile"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        
        return jsonify({'profile': farmer}), 200
    
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_farmer_profile():
    """Update farmer profile"""
    try:
        user_id = get_jwt_identity()
        farmer = BaseModel.execute_query("SELECT * FROM farmers WHERE id = %s", (int(user_id),), fetch_one=True)
        if not farmer:
            return jsonify({'error': 'Farmer access required'}), 403
        data = request.get_json()
        
        farmer_fields = {}
        allowed_fields = ['location', 'latitude', 'longitude', 'land_area_hectares',
                         'crops_grown', 'experience_years', 'bank_account',
                         'bank_ifsc', 'bank_name', 'aadhar_number', 'pan_number']
        
        for field in allowed_fields:
            if field in data:
                farmer_fields[field] = data[field]
        
        if farmer_fields:
            Farmer.update(farmer['id'], **farmer_fields)
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500
