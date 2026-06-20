"""
Buyer Module - Complete Shopping, Orders and Payments
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    User, Buyer, Product, Order, Payment, Review, Cart, Notification,
    Wallet, Transaction, BaseModel, Message, Conversation
)
from datetime import datetime
import json
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("[SKIP] razorpay not installed - payment features disabled")
import os
from dotenv import load_dotenv

load_dotenv()

buyer_bp = Blueprint('buyer', __name__, url_prefix='/api/buyer')


# ============================================================================
# HELPER: Resolve buyer from JWT (supports farmers shopping as buyers)
# ============================================================================

def get_or_create_buyer(user_id):
    """
    Get buyer by JWT identity. Checks multiple lookup paths:
    1. buyers.id = user_id
    2. buyers.buyer_id = user_id
    3. If user is a farmer, auto-create buyer record
    4. If user is an admin, auto-create buyer record
    Also checks JWT claims for role hints.
    """
    uid = int(user_id)
    
    # Try 1: Direct buyer id lookup
    buyer = BaseModel.execute_query(
        "SELECT * FROM buyers WHERE id = %s", (uid,), fetch_one=True
    )
    if buyer:
        return buyer
    
    # Try 2: buyer_id lookup (used by buyer_auth.py login)
    buyer = BaseModel.execute_query(
        "SELECT * FROM buyers WHERE buyer_id = %s", (uid,), fetch_one=True
    )
    if buyer:
        return buyer
    
    # Try 3: Check if user is a farmer — auto-create buyer record
    farmer = BaseModel.execute_query(
        "SELECT * FROM farmers WHERE id = %s", (uid,), fetch_one=True
    )
    if farmer:
        return _create_buyer_from_record(farmer, uid)
    
    # Try 4: Check if user is an admin — auto-create buyer record
    admin = BaseModel.execute_query(
        "SELECT * FROM admins WHERE admin_id = %s", (uid,), fetch_one=True
    )
    if admin:
        return _create_buyer_from_record(admin, uid)
    
    return None


def _create_buyer_from_record(record, uid):
    """Create a buyer record from a farmer/admin record"""
    try:
        buyer_id = BaseModel.execute_insert(
            """INSERT INTO buyers (first_name, last_name, email, phone, password_hash, location, buyer_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (record.get('first_name', ''), record.get('last_name', ''),
             record.get('email', ''), record.get('phone', ''),
             record.get('password_hash', ''), record.get('location', ''),
             uid)
        )
        return BaseModel.execute_query(
            "SELECT * FROM buyers WHERE id = %s", (buyer_id,), fetch_one=True
        )
    except Exception as e:
        # If insert fails (e.g. duplicate phone/email), find by email/phone
        buyer = BaseModel.execute_query(
            "SELECT * FROM buyers WHERE email = %s OR phone = %s",
            (record.get('email', ''), record.get('phone', '')), fetch_one=True
        )
        return buyer


# Initialize Razorpay
razorpay_client = None
if RAZORPAY_AVAILABLE:
    try:
        razorpay_client = razorpay.Client(
            auth=(os.getenv('RAZORPAY_KEY_ID', ''), os.getenv('RAZORPAY_KEY_SECRET', ''))
        )
    except Exception:
        razorpay_client = None

# ============================================================================
# PRODUCT BROWSING & SEARCH
# ============================================================================

@buyer_bp.route('/products', methods=['GET'])
def browse_products():
    """Browse available products"""
    try:
        search_term = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        sort_by = request.args.get('sort', 'newest')
        offset = (page - 1) * limit
        
        query = """
            SELECT p.*, 
                   CONCAT(f.first_name, ' ', COALESCE(f.last_name, '')) as farmer_name,
                   f.location as farmer_location
            FROM products p 
            LEFT JOIN farmers f ON p.farmer_id = f.id 
            WHERE (p.is_available = TRUE AND p.status = 'approved')
               OR p.status = 'sold_out'
        """
        params = []
        
        if search_term:
            query += " AND (p.name ILIKE %s OR p.description ILIKE %s OR p.category ILIKE %s)"
            like = f"%{search_term}%"
            params.extend([like, like, like])
        
        if category:
            query += " AND p.category = %s"
            params.append(category)
        
        if sort_by == 'rating':
            query += " ORDER BY p.average_rating DESC"
        elif sort_by == 'price_low':
            query += " ORDER BY p.price ASC"
        elif sort_by == 'price_high':
            query += " ORDER BY p.price DESC"
        else:
            query += " ORDER BY p.created_at DESC"
        
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        products = BaseModel.execute_query(query, params, fetch_all=True) or []
        
        # Serialize
        result = []
        for p in products:
            result.append({
                'id': p['id'],
                'name': p['name'],
                'description': p.get('description', ''),
                'category': p.get('category', ''),
                'price': float(p['price']),
                'quantity': float(p.get('quantity', 0)),
                'unit': p.get('unit', 'kg'),
                'images': json.loads(p['images']) if p.get('images') else [],
                'organic': bool(p.get('organic', False)),
                'average_rating': float(p.get('average_rating', 0)),
                'total_reviews': p.get('total_reviews', 0),
                'farmer_id': p['farmer_id'],
                'farmer_name': p.get('farmer_name', ''),
                'farmer_location': p.get('farmer_location', ''),
                'discount_percent': int(p.get('discount_percent', 0)),
                'status': p.get('status', 'approved'),
                'harvest_date': p['harvest_date'].isoformat() if p.get('harvest_date') else None,
                'created_at': p['created_at'].isoformat() if p.get('created_at') else None,
            })
        
        return jsonify({
            'success': True,
            'products': result,
            'page': page,
            'limit': limit,
            'sort': sort_by
        }), 200
    
    except Exception as e:
        print(f"Browse products error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    """Get product details"""
    try:
        product = Product.get_by_id(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Increment views
        Product.increment_views(product_id)
        
        # Get reviews
        reviews = Review.get_product_reviews(product_id, limit=10)
        
        return jsonify({
            'product': product,
            'reviews': reviews
        }), 200
    
    except Exception as e:
        print(f"Get product details error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/products/search', methods=['GET'])
def search_products():
    """Search products with filters"""
    try:
        search_term = request.args.get('q', '')
        category_id = request.args.get('category_id', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        min_rating = request.args.get('min_rating', type=float)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        if not search_term:
            return jsonify({'error': 'Search term required'}), 400
        
        products = Product.search(search_term, category_id, limit, offset)
        
        # Apply price and rating filters
        filtered_products = []
        for product in products:
            if min_price and product['price'] < min_price:
                continue
            if max_price and product['price'] > max_price:
                continue
            if min_rating and (product['average_rating'] or 0) < min_rating:
                continue
            filtered_products.append(product)
        
        return jsonify({
            'products': filtered_products,
            'page': page,
            'limit': limit,
            'total': len(filtered_products)
        }), 200
    
    except Exception as e:
        print(f"Search products error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SHOPPING CART
# ============================================================================

@buyer_bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """Get shopping cart"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        # Cart uses buyer_id directly
        items = Cart.get_items(buyer['id'])
        
        # Calculate totals
        subtotal = 0
        for item in items:
            subtotal += (item['price'] * item['quantity'])
        
        return jsonify({
            'cart_id': buyer['id'],
            'items': items,
            'subtotal': subtotal,
            'item_count': len(items)
        }), 200
    
    except Exception as e:
        print(f"Get cart error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/cart/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add item to cart"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        data = request.get_json()
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id or quantity <= 0:
            return jsonify({'error': 'Invalid product or quantity'}), 400
        
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if quantity > product['quantity']:
            return jsonify({'error': f'Only {product["quantity"]} available'}), 400
        
        # Cart.add_item uses buyer_id directly (no separate cart table)
        Cart.add_item(buyer['id'], product_id, quantity)
        
        return jsonify({'message': 'Item added to cart'}), 200
    
    except Exception as e:
        print(f"Add to cart error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/cart/items/<int:cart_item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(cart_item_id):
    """Update cart item quantity"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        data = request.get_json()
        quantity = float(data.get('quantity', 1))
        
        if quantity <= 0:
            return jsonify({'error': 'Invalid quantity'}), 400
        
        BaseModel.execute_query(
            "UPDATE cart SET quantity = %s WHERE id = %s",
            (quantity, cart_item_id)
        )
        
        return jsonify({'message': 'Cart item updated'}), 200
    
    except Exception as e:
        import traceback
        print(f"[CART-UPDATE-ERROR] {e}", flush=True)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/cart/items/<int:cart_item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        Cart.remove_item(cart_item_id)
        
        return jsonify({'message': 'Item removed from cart'}), 200
    
    except Exception as e:
        print(f"Remove from cart error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/cart/clear', methods=['POST'])
@jwt_required()
def clear_cart():
    """Clear entire cart"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        # Cart.clear_cart uses buyer_id directly
        Cart.clear_cart(buyer['id'])
        
        return jsonify({'message': 'Cart cleared'}), 200
    
    except Exception as e:
        print(f"Clear cart error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ORDERS
# ============================================================================

@buyer_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Create order from cart"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        data = request.get_json()
        
        # Validation
        if not data.get('product_id') or not data.get('quantity'):
            return jsonify({'error': 'Product and quantity required'}), 400
        
        product = Product.get_by_id(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if data['quantity'] > product['quantity']:
            return jsonify({'error': f'Only {product["quantity"]} available'}), 400
        
        if not data.get('delivery_address'):
            return jsonify({'error': 'Delivery address required'}), 400
        
        # Calculate total
        unit_price = product['price']
        total_price = unit_price * data['quantity']
        final_price = total_price
        
        # Create order
        import uuid
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        order_id = Order.create(
            order_number=order_number,
            farmer_id=product['farmer_id'],
            buyer_id=buyer['id'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            unit_price=unit_price,
            total_price=total_price,
            final_price=final_price,
            delivery_address=data['delivery_address']
        )
        
        # Add notes if provided
        if data.get('notes'):
            BaseModel.execute_query(
                "UPDATE orders SET notes = %s WHERE id = %s",
                (data['notes'], order_id)
            )
        
        # Send notifications
        Notification.create(
            user_id=user_id,
            title='Order Created',
            message=f'Your order #{order_number} has been placed',
            notification_type='order'
        )
        
        Notification.create(
            user_id=str(product['farmer_id']),
            title='New Order',
            message=f'You have received a new order #{order_number}',
            notification_type='order'
        )
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order_id,
            'order_number': order_number
        }), 201
    
    except Exception as e:
        print(f"Create order error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get buyer's orders"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        orders = Order.get_buyer_orders(buyer['id'], status=status, limit=limit, offset=offset)
        
        return jsonify({
            'orders': orders,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get orders error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get order details"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['buyer_id'] != buyer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'order': order}), 200
    
    except Exception as e:
        print(f"Get order error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """Cancel order"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['buyer_id'] != buyer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if order['status'] not in ['pending', 'confirmed']:
            return jsonify({'error': 'Cannot cancel order in current status'}), 400
        
        data = request.get_json()
        reason = data.get('reason', 'User requested cancellation')
        
        Order.update_status(order_id, 'cancelled')
        BaseModel.execute_query(
            "UPDATE orders SET cancellation_reason = %s WHERE id = %s",
            (reason, order_id)
        )
        
        # Notify farmer
        Notification.create(
            user_id=order['farmer_user_id'],
            title='Order Cancelled',
            message=f'Order #{order["order_number"]} has been cancelled',
            notification_type='order'
        )
        
        return jsonify({'message': 'Order cancelled successfully'}), 200
    
    except Exception as e:
        print(f"Cancel order error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PAYMENTS
# ============================================================================

@buyer_bp.route('/payments/create', methods=['POST'])
@jwt_required()
def create_payment():
    """Create Razorpay payment"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        if not razorpay_client:
            return jsonify({'error': 'Payment service not configured'}), 500
        
        data = request.get_json()
        
        order_id = data.get('order_id')
        order = Order.get_by_id(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['buyer_id'] != buyer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create(dict(
            amount=int(order['final_price'] * 100),  # Amount in paise
            currency='INR',
            payment_capture='1'
        ))
        
        # Create payment record
        payment_id = Payment.create(
            order_id=order_id,
            buyer_id=buyer['id'],
            amount=order['final_price'],
            payment_method='razorpay'
        )
        
        # Update payment with Razorpay order ID
        BaseModel.execute_query(
            "UPDATE payments SET razorpay_order_id = %s WHERE id = %s",
            (razorpay_order['id'], payment_id)
        )
        
        return jsonify({
            'payment_id': payment_id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': order['final_price'],
            'key_id': os.getenv('RAZORPAY_KEY_ID')
        }), 200
    
    except Exception as e:
        print(f"Create payment error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/payments/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify Razorpay payment"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        data = request.get_json()
        
        payment_id = data.get('payment_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        payment = Payment.get_by_id(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Verify signature
        import hmac
        import hashlib
        
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            os.getenv('RAZORPAY_KEY_SECRET', '').encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if expected_signature != razorpay_signature:
            Payment.mark_failed(payment_id, 'Invalid signature')
            return jsonify({'error': 'Payment verification failed'}), 400
        
        # Update payment
        Payment.update_with_razorpay(
            payment_id,
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature
        )
        
        # Update order status
        Order.update_payment_status(payment['order_id'], 'paid')
        
        # Update farmer wallet
        order = Order.get_by_id(payment['order_id'])
        farmer_commission = order['final_price'] * 0.95  # 5% platform fee
        Wallet.add_balance(order['farmer_user_id'], farmer_commission)
        
        # Record transaction
        transaction_record_id = BaseModel.execute_insert(
            """INSERT INTO transactions (user_id, type, amount, order_id, payment_id, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (order['farmer_user_id'], 'credit', farmer_commission, order['id'], payment_id, 'completed')
        )
        
        # Send notifications
        Notification.create(
            user_id=order['buyer_user_id'],
            title='Payment Confirmed',
            message=f'Payment for order #{order["order_number"]} has been confirmed',
            notification_type='payment'
        )
        
        Notification.create(
            user_id=order['farmer_user_id'],
            title='Order Paid',
            message=f'Order #{order["order_number"]} has been paid',
            notification_type='payment'
        )
        
        return jsonify({'message': 'Payment verified successfully'}), 200
    
    except Exception as e:
        print(f"Verify payment error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REVIEWS
# ============================================================================

@buyer_bp.route('/orders/<int:order_id>/review', methods=['POST'])
@jwt_required()
def create_review(order_id):
    """Create product review"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        order = Order.get_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['buyer_id'] != buyer['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        review_id = Review.create(
            product_id=order['product_id'],
            buyer_id=buyer['id'],
            rating=rating,
            comment=data.get('comment', ''),
            order_id=order_id
        )
        
        # Update product rating
        query = """
        SELECT AVG(rating) as avg_rating, COUNT(*) as count
        FROM reviews WHERE product_id = %s
        """
        result = BaseModel.execute_query(query, (order['product_id'],), fetch_one=True)
        
        BaseModel.execute_query(
            "UPDATE products SET average_rating = %s, review_count = %s WHERE id = %s",
            (result['avg_rating'], result['count'], order['product_id'])
        )
        
        return jsonify({
            'message': 'Review created successfully',
            'review_id': review_id
        }), 201
    
    except Exception as e:
        print(f"Create review error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROFILE
# ============================================================================

@buyer_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get buyer profile"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        
        return jsonify({'profile': buyer}), 200
    
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500

@buyer_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update buyer profile"""
    try:
        user_id = get_jwt_identity()
        buyer = get_or_create_buyer(user_id)
        if not buyer:
            return jsonify({'error': 'Buyer access required'}), 403
        data = request.get_json()
        
        buyer_fields = {}
        allowed_fields = ['business_name', 'business_type', 'company_registration',
                         'location', 'latitude', 'longitude', 'delivery_address', 'gst_number']
        
        for field in allowed_fields:
            if field in data:
                buyer_fields[field] = data[field]
        
        if buyer_fields:
            Buyer.update(buyer['id'], **buyer_fields)
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500
