"""
Buyer Order Management Routes
Handles: Place order, View orders, Cancel, Returns, Tracking
Path: /api/orders (buyer view)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

import sys
sys.path.append('..')
from models.models import Order, Cart, Payment, OrderTracking

buyer_orders_bp = Blueprint('buyer_orders', __name__, url_prefix='/api/orders')

# ====================================================================
# 1. CREATE ORDER - Place order from cart
# ====================================================================
@buyer_orders_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create order from cart items and clear cart
    
    Request:
    {
        "address_id": 1,
        "payment_method": "upi" or "card" or "cod",
        "notes": "Please deliver after 6 PM"
    }
    
    Response:
    {
        "success": true,
        "order_id": 101,
        "message": "Order placed successfully",
        "order": {
            "order_id": 101,
            "status": "pending",
            "total_amount": 314,
            "payment_status": "pending"
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        address_id = data.get('address_id')
        payment_method = data.get('payment_method', 'cod')
        notes = data.get('notes', '')
        
        # Validate address
        if not address_id:
            return jsonify({'success': False, 'error': 'Delivery address required'}), 400
        
        # Validate payment method
        valid_methods = ['upi', 'card', 'cod', 'netbanking']
        if payment_method not in valid_methods:
            return jsonify({'success': False, 'error': 'Invalid payment method'}), 400
        
        # Get cart items
        cart = Cart()
        cart_items = cart.get_cart_items(buyer_id)
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        # Calculate total
        subtotal = sum(item['quantity'] * item['price_at_addition'] for item in cart_items)
        tax = subtotal * 0.05
        delivery_fee = 50
        total_amount = subtotal + tax + delivery_fee
        
        # TODO: Get address details from buyer_addresses table
        delivery_address = f"Address ID: {address_id}"
        
        # Create order
        order_obj = Order()
        order_id = order_obj.create_order(
            buyer_id=buyer_id,
            cart_items=cart_items,
            total_amount=total_amount,
            delivery_address=delivery_address,
            notes=notes,
            payment_method=payment_method
        )
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Failed to create order'}), 500
        
        # Clear cart
        cart.clear_cart(buyer_id)
        
        # Create order tracking record
        tracking = OrderTracking()
        tracking.create_tracking(order_id, 'pending')
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Order placed successfully',
            'order': {
                'order_id': order_id,
                'status': 'pending',
                'total_amount': float(total_amount),
                'payment_status': 'pending',
                'created_at': datetime.now().isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"Error in create_order: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create order'}), 500


# ====================================================================
# 2. GET ALL ORDERS - Buyer's orders with filters
# ====================================================================
@buyer_orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_buyer_orders():
    """
    Get all orders of buyer with optional filters
    
    Query Parameters:
    - status: Filter by status (pending, accepted, in_transit, delivered, cancelled)
    - page: Page number
    - limit: Items per page
    
    Response:
    {
        "success": true,
        "orders": [
            {
                "order_id": 101,
                "farmer_name": "Ravi Kumar",
                "product_name": "Organic Tomatoes",
                "quantity": 2,
                "total_amount": 314,
                "status": "in_transit",
                "created_at": "2026-06-01T10:30:00",
                "estimated_delivery": "2026-06-02T06:00:00"
            }
        ],
        "summary": {
            "pending": 2,
            "accepted": 1,
            "in_transit": 3,
            "delivered": 15,
            "cancelled": 1
        },
        "total": 22
    }
    """
    try:
        buyer_id = get_jwt_identity()
        status = request.args.get('status', '').strip()
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=10)
        
        order_obj = Order()
        filters = {'status': status} if status else {}
        orders = order_obj.get_buyer_orders(buyer_id, filters, page, limit)
        
        # Get status counts
        status_counts = order_obj.get_order_status_counts(buyer_id)
        
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order['order_id'],
                'farmer_id': order['farmer_id'],
                'farmer_name': order['farmer_name'],
                'product_id': order['product_id'],
                'product_name': order['product_name'],
                'quantity': order['quantity'],
                'unit_price': float(order['price']),
                'total_amount': float(order['total_amount']),
                'status': order['status'],
                'payment_status': order['payment_status'],
                'created_at': order['created_at'].isoformat() if order['created_at'] else None,
                'estimated_delivery': order.get('estimated_delivery', '').isoformat() if order.get('estimated_delivery') else None
            })
        
        total = order_obj.count_buyer_orders(buyer_id, filters)
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'orders': formatted_orders,
            'summary': status_counts,
            'total': total,
            'page': page,
            'pages': pages
        }), 200
        
    except Exception as e:
        print(f"Error in get_buyer_orders: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch orders'}), 500


# ====================================================================
# 3. GET ORDER DETAILS
# ====================================================================
@buyer_orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """
    Get complete order details
    
    Response:
    {
        "success": true,
        "order": {
            "order_id": 101,
            "buyer_name": "Ramesh",
            "buyer_phone": "9876543200",
            "farmer_name": "Ravi Kumar",
            "farmer_phone": "9876543210",
            "product_name": "Organic Tomatoes",
            "quantity": 2,
            "unit_price": 40,
            "total_amount": 314,
            "delivery_address": "123 Main St",
            "status": "in_transit",
            "payment_status": "completed",
            "payment_method": "upi",
            "tracking": {
                "status": "in_transit",
                "delivery_boy": "Rajesh",
                "latitude": 17.3850,
                "longitude": 78.4867,
                "estimated_delivery": "2026-06-02T06:00:00"
            },
            "timeline": [
                {"status": "pending", "timestamp": "..."},
                {"status": "accepted", "timestamp": "..."}
            ]
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get tracking info
        tracking_obj = OrderTracking()
        tracking = tracking_obj.get_tracking(order_id)
        
        # Get payment info
        payment_obj = Payment()
        payment = payment_obj.get_payment(order_id)
        
        return jsonify({
            'success': True,
            'order': {
                'order_id': order['order_id'],
                'buyer_name': order.get('buyer_name', ''),
                'buyer_phone': order.get('buyer_phone', '')[:4] + '****' + order.get('buyer_phone', '')[-2:] if order.get('buyer_phone') else '',
                'farmer_name': order.get('farmer_name', ''),
                'farmer_phone': order.get('farmer_phone', '')[:4] + '****' + order.get('farmer_phone', '')[-2:] if order.get('farmer_phone') else '',
                'product_name': order['product_name'],
                'quantity': order['quantity'],
                'unit_price': float(order['price']),
                'total_amount': float(order['total_amount']),
                'delivery_address': order.get('delivery_address', ''),
                'status': order['status'],
                'payment_status': order['payment_status'],
                'payment_method': payment['payment_method'] if payment else 'unknown',
                'created_at': order['created_at'].isoformat() if order['created_at'] else None,
                'tracking': {
                    'status': tracking['status'] if tracking else 'pending',
                    'delivery_boy': tracking.get('delivery_boy_name', '') if tracking else '',
                    'latitude': float(tracking['latitude']) if tracking and tracking['latitude'] else None,
                    'longitude': float(tracking['longitude']) if tracking and tracking['longitude'] else None,
                    'estimated_delivery': tracking.get('estimated_delivery_time', '').isoformat() if tracking and tracking.get('estimated_delivery_time') else None,
                    'actual_delivery': tracking.get('actual_delivery_time', '').isoformat() if tracking and tracking.get('actual_delivery_time') else None
                }
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_order_details: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch order details'}), 500


# ====================================================================
# 4. CANCEL ORDER
# ====================================================================
@buyer_orders_bp.route('/<int:order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    """
    Cancel order (if not yet shipped)
    
    Request:
    {
        "reason": "Changed my mind"
    }
    
    Response:
    {
        "success": true,
        "message": "Order cancelled successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '')
        
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Check if order can be cancelled
        if order['status'] not in ['pending', 'accepted']:
            return jsonify({
                'success': False,
                'error': f'Cannot cancel order with status: {order["status"]}'
            }), 400
        
        # Cancel order
        success = order_obj.cancel_order(order_id, reason)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to cancel order'}), 500
        
        # TODO: Process refund
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in cancel_order: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to cancel order'}), 500


# ====================================================================
# 5. GET ORDER TRACKING - Live tracking
# ====================================================================
@buyer_orders_bp.route('/<int:order_id>/track', methods=['GET'])
@jwt_required()
def get_order_tracking(order_id):
    """
    Get live order tracking information
    
    Response:
    {
        "success": true,
        "tracking": {
            "order_id": 101,
            "status": "in_transit",
            "delivery_boy_name": "Rajesh",
            "delivery_boy_phone": "9876543210",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "estimated_delivery": "2026-06-02T06:00:00",
            "recent_updates": [
                {
                    "status": "in_transit",
                    "latitude": 17.3850,
                    "longitude": 78.4867,
                    "timestamp": "2026-06-02T04:30:00"
                }
            ]
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify order belongs to buyer
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get tracking
        tracking_obj = OrderTracking()
        tracking = tracking_obj.get_tracking(order_id)
        
        if not tracking:
            return jsonify({
                'success': True,
                'tracking': {
                    'order_id': order_id,
                    'status': order['status'],
                    'message': 'Tracking will be available once order is shipped'
                }
            }), 200
        
        return jsonify({
            'success': True,
            'tracking': {
                'order_id': order_id,
                'status': tracking['status'],
                'delivery_boy_name': tracking.get('delivery_boy_name', ''),
                'delivery_boy_phone': tracking.get('delivery_boy_phone', ''),
                'latitude': float(tracking['latitude']) if tracking['latitude'] else None,
                'longitude': float(tracking['longitude']) if tracking['longitude'] else None,
                'estimated_delivery': tracking.get('estimated_delivery_time', '').isoformat() if tracking.get('estimated_delivery_time') else None,
                'actual_delivery': tracking.get('actual_delivery_time', '').isoformat() if tracking.get('actual_delivery_time') else None,
                'notes': tracking.get('notes', ''),
                'updated_at': tracking['updated_at'].isoformat() if tracking['updated_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_order_tracking: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch tracking'}), 500


# ====================================================================
# 6. REQUEST RETURN
# ====================================================================
@buyer_orders_bp.route('/<int:order_id>/return', methods=['POST'])
@jwt_required()
def request_return(order_id):
    """
    Request return/refund for order
    
    Request:
    {
        "reason": "Product quality issue",
        "description": "Tomatoes are rotten"
    }
    
    Response:
    {
        "success": true,
        "return_id": 1,
        "message": "Return request submitted"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        reason = data.get('reason', '').strip()
        description = data.get('description', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'error': 'Reason required'}), 400
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Check if order can be returned (within 7 days and delivered)
        if order['status'] != 'delivered':
            return jsonify({'success': False, 'error': 'Only delivered orders can be returned'}), 400
        
        # Create return request
        from models.models import ReturnRequest
        return_req = ReturnRequest()
        return_id = return_req.create_return_request(
            order_id=order_id,
            buyer_id=buyer_id,
            reason=reason,
            description=description
        )
        
        if not return_id:
            return jsonify({'success': False, 'error': 'Failed to create return request'}), 500
        
        return jsonify({
            'success': True,
            'return_id': return_id,
            'message': 'Return request submitted successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in request_return: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create return request'}), 500


# ====================================================================
# 7. GET RETURN STATUS
# ====================================================================
@buyer_orders_bp.route('/<int:order_id>/return', methods=['GET'])
@jwt_required()
def get_return_status(order_id):
    """
    Get return/refund status for an order
    
    Response:
    {
        "success": true,
        "return_status": {
            "return_id": 1,
            "status": "approved",
            "reason": "Product quality issue",
            "refund_amount": 314,
            "created_at": "2026-06-03T10:00:00",
            "updated_at": "2026-06-04T02:30:00"
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get return request
        from models.models import ReturnRequest
        return_req = ReturnRequest()
        return_data = return_req.get_return_by_order(order_id)
        
        if not return_data:
            return jsonify({
                'success': True,
                'return_status': None,
                'message': 'No return request for this order'
            }), 200
        
        return jsonify({
            'success': True,
            'return_status': {
                'return_id': return_data['return_id'],
                'status': return_data['status'],
                'reason': return_data['reason'],
                'description': return_data.get('description', ''),
                'refund_amount': float(return_data['refund_amount']) if return_data['refund_amount'] else None,
                'created_at': return_data['created_at'].isoformat() if return_data['created_at'] else None,
                'updated_at': return_data['updated_at'].isoformat() if return_data['updated_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_return_status: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch return status'}), 500
