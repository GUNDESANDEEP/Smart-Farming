"""
Orders Routes - View, Accept, Reject, Update Order Status
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Order
import json

orders_bp = Blueprint('orders', __name__)

# ==================== GET FARMER ORDERS ====================
@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """
    Get all orders for farmer
    
    Query: ?status=pending&sort=date
    
    Response: {
        "success": true,
        "pending": 2,
        "accepted": 3,
        "orders": [...]
    }
    """
    try:
        farmer_id = get_jwt_identity()
        status_filter = request.args.get('status')
        
        # Get orders
        orders = Order.get_farmer_orders(farmer_id)
        
        # Filter by status if provided
        if status_filter and orders:
            orders = [o for o in orders if o['status'].lower() == status_filter.lower()]
        
        # Count orders by status
        pending_count = 0
        accepted_count = 0
        delivered_count = 0
        
        if orders:
            pending_count = len([o for o in Order.get_farmer_orders(farmer_id) if o['status'] == 'pending'])
            accepted_count = len([o for o in Order.get_farmer_orders(farmer_id) if o['status'] == 'accepted'])
            delivered_count = len([o for o in Order.get_farmer_orders(farmer_id) if o['status'] == 'delivered'])
        
        # Format orders
        formatted_orders = [
            {
                'id': o['id'],
                'product_name': o['product_name'],
                'product_id': o['product_id'],
                'quantity': o['quantity'],
                'unit_price': float(o['unit_price']),
                'total_price': float(o['total_price']),
                'buyer_id': o['buyer_id'],
                'status': o['status'],
                'payment_status': o['payment_status'],
                'delivery_address': o['delivery_address'],
                'delivery_date': o['delivery_date'].isoformat() if o['delivery_date'] else None,
                'notes': o['notes'],
                'created_at': o['created_at'].isoformat()
            }
            for o in orders
        ] if orders else []
        
        return {
            'success': True,
            'stats': {
                'pending': pending_count,
                'accepted': accepted_count,
                'delivered': delivered_count
            },
            'total': len(formatted_orders),
            'orders': formatted_orders
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== ACCEPT ORDER ====================
@orders_bp.route('/<int:order_id>/accept', methods=['POST'])
@jwt_required()
def accept_order(order_id):
    """
    Accept incoming order
    
    Request: {
        "delivery_date": "2026-06-10"
    }
    
    Response: {
        "success": true,
        "message": "Order accepted",
        "order": {...}
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        
        # Update order status
        Order.update_order_status(order_id, 'accepted')
        
        # TODO: Send notification to buyer
        # TODO: Update delivery tracking
        
        return {
            'success': True,
            'message': 'Order accepted successfully',
            'next_step': 'Arrange delivery'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== REJECT ORDER ====================
@orders_bp.route('/<int:order_id>/reject', methods=['POST'])
@jwt_required()
def reject_order(order_id):
    """
    Reject incoming order
    
    Request: {
        "reason": "Out of stock"
    }
    
    Response: {
        "success": true,
        "message": "Order rejected"
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        # Update order status and rejection reason
        Order.update_order_status(order_id, 'rejected')
        # TODO: Store rejection reason
        
        # TODO: Send notification to buyer with reason
        # TODO: Refund payment if already paid
        
        return {
            'success': True,
            'message': 'Order rejected successfully'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== UPDATE ORDER STATUS ====================
@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """
    Update order status (in_transit, delivered, cancelled)
    
    Request: {
        "status": "in_transit",
        "location": {
            "latitude": 17.3850,
            "longitude": 78.4867
        }
    }
    """
    try:
        farmer_id = get_jwt_identity()
        data = request.get_json()
        new_status = data.get('status')
        
        # Allowed status transitions
        allowed_statuses = ['in_transit', 'delivered', 'cancelled']
        
        if new_status not in allowed_statuses:
            return {'success': False, 'message': 'Invalid status'}, 400
        
        # Update status
        Order.update_order_status(order_id, new_status)
        
        # TODO: Send notification to buyer
        # TODO: Update GPS tracking if in_transit
        
        return {
            'success': True,
            'message': f'Order status updated to {new_status}'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== GET ORDER DETAILS ====================
@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """
    Get detailed order information
    """
    try:
        farmer_id = get_jwt_identity()
        # TODO: Fetch order from database
        # Verify farmer owns this order
        
        return {
            'success': True,
            'order': {
                'id': order_id,
                'status': 'accepted',
                'product': 'Tomato',
                'quantity': 10,
                'price': 450
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== TRACK DELIVERY ====================
@orders_bp.route('/<int:order_id>/track', methods=['GET'])
@jwt_required()
def track_delivery(order_id):
    """
    Get real-time delivery tracking
    
    Response: {
        "success": true,
        "status": "in_transit",
        "current_location": {...},
        "estimated_delivery": "2026-06-10T14:30:00",
        "driver": {...}
    }
    """
    try:
        farmer_id = get_jwt_identity()
        
        return {
            'success': True,
            'status': 'in_transit',
            'current_location': {
                'latitude': 17.3850,
                'longitude': 78.4867
            },
            'estimated_delivery': '2026-06-10T14:30:00',
            'driver': {
                'name': 'Mohan',
                'phone': '9876543210',
                'vehicle': 'Auto TS 09 AB 1234'
            }
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
