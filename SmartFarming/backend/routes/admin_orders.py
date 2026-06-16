"""
Admin Order Management Routes
Handles: Order monitoring, dispute resolution, refund approvals
Path: /api/admin/orders
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

import sys
sys.path.append('..')
from models.models import Admin, Order, Dispute, Payment

admin_orders_bp = Blueprint('admin_orders', __name__, url_prefix='/api/admin/orders')

# ====================================================================
# 1. GET ALL ORDERS
# ====================================================================
@admin_orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_orders():
    """
    Get all orders with filtering and search
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - status: Filter by order status (pending, accepted, in_transit, delivered, cancelled)
    - search: Search by order ID, buyer name, farmer name
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    
    Response:
    {
        "success": true,
        "orders": [
            {
                "order_id": 1234,
                "buyer_name": "Asha Patel",
                "farmer_name": "Ravi Kumar",
                "total_amount": 450.99,
                "status": "in_transit",
                "payment_method": "upi",
                "order_date": "2026-06-01T10:00:00",
                "delivery_date": null
            }
        ],
        "pagination": {...}
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        status = request.args.get('status', default=None)
        search = request.args.get('search', default=None)
        date_from = request.args.get('date_from', default=None)
        date_to = request.args.get('date_to', default=None)
        
        order_obj = Order()
        orders, total = order_obj.get_all_orders_paginated(
            page=page,
            limit=limit,
            status=status,
            search=search,
            date_from=date_from,
            date_to=date_to
        )
        
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order['order_id'],
                'buyer_name': order.get('buyer_name', ''),
                'farmer_name': order.get('farmer_name', ''),
                'total_amount': float(order['total_amount']),
                'status': order['order_status'],
                'payment_method': order.get('payment_method', 'unknown'),
                'order_date': order['created_at'].isoformat() if order['created_at'] else None,
                'delivery_date': order['delivered_date'].isoformat() if order.get('delivered_date') else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'orders': formatted_orders,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_all_orders: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch orders'}), 500


# ====================================================================
# 2. GET ORDER DETAILS
# ====================================================================
@admin_orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """
    Get complete order details with transaction history
    
    Response:
    {
        "success": true,
        "order": {
            "order_id": 1234,
            "buyer_id": 56,
            "buyer_name": "Asha Patel",
            "farmer_id": 23,
            "farmer_name": "Ravi Kumar",
            "products": [...],
            "total_amount": 450.99,
            "status": "in_transit",
            "payment_method": "upi",
            "payment_status": "completed",
            "delivery_address": "...",
            "order_date": "2026-06-01T10:00:00",
            "estimated_delivery": "2026-06-05T10:00:00",
            "actual_delivery": null,
            "history": [...]
        }
    }
    """
    try:
        order_obj = Order()
        order_data = order_obj.get_order_by_id(order_id)
        
        if not order_data:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get order items
        items = order_obj.get_order_items(order_id)
        formatted_items = []
        for item in items:
            formatted_items.append({
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'quantity': item['quantity'],
                'price': float(item['price']),
                'total': float(item['quantity'] * item['price'])
            })
        
        # Get order history/tracking
        history = order_obj.get_order_history(order_id)
        formatted_history = []
        for h in history:
            formatted_history.append({
                'status': h['status'],
                'timestamp': h['created_at'].isoformat() if h['created_at'] else None,
                'notes': h.get('notes', '')
            })
        
        return jsonify({
            'success': True,
            'order': {
                'order_id': order_data['order_id'],
                'buyer_id': order_data['buyer_id'],
                'buyer_name': order_data.get('buyer_name', ''),
                'farmer_id': order_data['farmer_id'],
                'farmer_name': order_data.get('farmer_name', ''),
                'products': formatted_items,
                'total_amount': float(order_data['total_amount']),
                'status': order_data['order_status'],
                'payment_method': order_data.get('payment_method', 'unknown'),
                'payment_status': order_data.get('payment_status', 'unknown'),
                'delivery_address': order_data.get('delivery_address', ''),
                'order_date': order_data['created_at'].isoformat() if order_data['created_at'] else None,
                'estimated_delivery': order_data.get('estimated_delivery_date', ''),
                'actual_delivery': order_data['delivered_date'].isoformat() if order_data.get('delivered_date') else None,
                'history': formatted_history
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_order_details: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch order details'}), 500


# ====================================================================
# 3. GET DISPUTES
# ====================================================================
@admin_orders_bp.route('/disputes', methods=['GET'])
@jwt_required()
def get_disputes():
    """
    Get list of all disputes
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - status: Filter by status (open, investigating, resolved, closed)
    
    Response:
    {
        "success": true,
        "disputes": [
            {
                "dispute_id": 1,
                "order_id": 1234,
                "buyer_name": "Asha",
                "farmer_name": "Ravi",
                "complaint_type": "Quality Issue",
                "description": "Product was damaged",
                "status": "open",
                "created_date": "2026-06-02T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        status = request.args.get('status', default=None)
        
        dispute_obj = Dispute()
        disputes, total = dispute_obj.get_all_disputes_paginated(
            page=page,
            limit=limit,
            status=status
        )
        
        formatted_disputes = []
        for dispute in disputes:
            formatted_disputes.append({
                'dispute_id': dispute['dispute_id'],
                'order_id': dispute['order_id'],
                'buyer_name': dispute.get('buyer_name', ''),
                'farmer_name': dispute.get('farmer_name', ''),
                'complaint_type': dispute.get('complaint_type', ''),
                'description': dispute.get('description', ''),
                'status': dispute['status'],
                'created_date': dispute['created_at'].isoformat() if dispute['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'disputes': formatted_disputes,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_disputes: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch disputes'}), 500


# ====================================================================
# 4. GET DISPUTE DETAILS
# ====================================================================
@admin_orders_bp.route('/disputes/<int:dispute_id>', methods=['GET'])
@jwt_required()
def get_dispute_details(dispute_id):
    """
    Get complete dispute details and resolution history
    
    Response:
    {
        "success": true,
        "dispute": {
            "dispute_id": 1,
            "order_id": 1234,
            "buyer_name": "Asha",
            "farmer_name": "Ravi",
            "complaint_type": "Quality Issue",
            "description": "Product was damaged",
            "status": "open",
            "created_date": "2026-06-02T10:00:00",
            "resolution": null,
            "resolved_date": null,
            "resolved_by": null,
            "notes": []
        }
    }
    """
    try:
        dispute_obj = Dispute()
        dispute_data = dispute_obj.get_dispute_by_id(dispute_id)
        
        if not dispute_data:
            return jsonify({'success': False, 'error': 'Dispute not found'}), 404
        
        # Get dispute notes
        notes = dispute_obj.get_dispute_notes(dispute_id)
        formatted_notes = []
        for note in notes:
            formatted_notes.append({
                'note_id': note['note_id'],
                'admin_name': note.get('admin_name', ''),
                'content': note['content'],
                'created_date': note['created_at'].isoformat() if note['created_at'] else None
            })
        
        return jsonify({
            'success': True,
            'dispute': {
                'dispute_id': dispute_data['dispute_id'],
                'order_id': dispute_data['order_id'],
                'buyer_name': dispute_data.get('buyer_name', ''),
                'farmer_name': dispute_data.get('farmer_name', ''),
                'complaint_type': dispute_data.get('complaint_type', ''),
                'description': dispute_data.get('description', ''),
                'status': dispute_data['status'],
                'created_date': dispute_data['created_at'].isoformat() if dispute_data['created_at'] else None,
                'resolution': dispute_data.get('resolution'),
                'resolved_date': dispute_data['resolution_date'].isoformat() if dispute_data.get('resolution_date') else None,
                'resolved_by': dispute_data.get('admin_name'),
                'notes': formatted_notes
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_dispute_details: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch dispute details'}), 500


# ====================================================================
# 5. RESOLVE DISPUTE
# ====================================================================
@admin_orders_bp.route('/disputes/<int:dispute_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_dispute(dispute_id):
    """
    Resolve a dispute with final resolution
    
    Request:
    {
        "resolution": "Full refund approved",
        "refund_amount": 450.99,
        "notes": "Product was damaged in transit"
    }
    
    Response:
    {
        "success": true,
        "message": "Dispute resolved successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        resolution = data.get('resolution', '').strip()
        refund_amount = data.get('refund_amount')
        notes = data.get('notes', '').strip()
        
        if not resolution:
            return jsonify({'success': False, 'error': 'Resolution required'}), 400
        
        dispute_obj = Dispute()
        dispute_data = dispute_obj.get_dispute_by_id(dispute_id)
        
        if not dispute_data:
            return jsonify({'success': False, 'error': 'Dispute not found'}), 404
        
        # Update dispute to resolved
        success = dispute_obj.update_dispute_status(
            dispute_id=dispute_id,
            status='resolved',
            resolution=resolution,
            resolved_by=admin_id
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to resolve dispute'}), 500
        
        # If refund, create refund request
        if refund_amount and refund_amount > 0:
            payment_obj = Payment()
            payment_obj.create_refund_request(
                order_id=dispute_data['order_id'],
                buyer_id=dispute_data['buyer_id'],
                amount=refund_amount,
                reason='Dispute resolution',
                status='approved',
                approved_by=admin_id
            )
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='resolve_dispute',
            module='orders',
            entity_id=dispute_id,
            description=f'Resolved: {resolution}'
        )
        
        # Add note
        dispute_obj.add_dispute_note(dispute_id, admin_id, notes or resolution)
        
        return jsonify({
            'success': True,
            'message': 'Dispute resolved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in resolve_dispute: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to resolve dispute'}), 500


# ====================================================================
# 6. GET REFUND REQUESTS
# ====================================================================
@admin_orders_bp.route('/refunds', methods=['GET'])
@jwt_required()
def get_refund_requests():
    """
    Get list of refund requests
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - status: Filter by status (requested, approved, rejected, processed)
    
    Response:
    {
        "success": true,
        "refunds": [
            {
                "refund_id": 1,
                "order_id": 1234,
                "buyer_name": "Asha",
                "amount": 450.99,
                "reason": "Quality issue",
                "status": "requested",
                "requested_date": "2026-06-02T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        status = request.args.get('status', default=None)
        
        payment_obj = Payment()
        refunds, total = payment_obj.get_all_refund_requests_paginated(
            page=page,
            limit=limit,
            status=status
        )
        
        formatted_refunds = []
        for refund in refunds:
            formatted_refunds.append({
                'refund_id': refund['refund_id'],
                'order_id': refund['order_id'],
                'buyer_name': refund.get('buyer_name', ''),
                'amount': float(refund['amount']),
                'reason': refund.get('reason', ''),
                'status': refund['status'],
                'requested_date': refund['created_at'].isoformat() if refund['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'refunds': formatted_refunds,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_refund_requests: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch refund requests'}), 500


# ====================================================================
# 7. APPROVE REFUND
# ====================================================================
@admin_orders_bp.route('/refunds/<int:refund_id>/approve', methods=['POST'])
@jwt_required()
def approve_refund(refund_id):
    """
    Approve a refund request
    
    Request:
    {
        "notes": "Refund approved due to quality issue"
    }
    
    Response:
    {
        "success": true,
        "message": "Refund approved successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json() or {}
        notes = data.get('notes', '').strip()
        
        payment_obj = Payment()
        refund_data = payment_obj.get_refund_request(refund_id)
        
        if not refund_data:
            return jsonify({'success': False, 'error': 'Refund request not found'}), 404
        
        # Update refund status
        success = payment_obj.update_refund_status(
            refund_id=refund_id,
            status='approved',
            approved_by=admin_id
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to approve refund'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='approve_refund',
            module='orders',
            entity_id=refund_id,
            description=notes or f'Approved refund: ₹{refund_data["amount"]}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Refund approved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in approve_refund: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to approve refund'}), 500


# ====================================================================
# 8. REJECT REFUND
# ====================================================================
@admin_orders_bp.route('/refunds/<int:refund_id>/reject', methods=['POST'])
@jwt_required()
def reject_refund(refund_id):
    """
    Reject a refund request
    
    Request:
    {
        "reason": "Claim not valid"
    }
    
    Response:
    {
        "success": true,
        "message": "Refund rejected successfully"
    }
    """
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'error': 'Rejection reason required'}), 400
        
        payment_obj = Payment()
        refund_data = payment_obj.get_refund_request(refund_id)
        
        if not refund_data:
            return jsonify({'success': False, 'error': 'Refund request not found'}), 404
        
        # Update refund status
        success = payment_obj.update_refund_status(
            refund_id=refund_id,
            status='rejected',
            approved_by=admin_id
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to reject refund'}), 500
        
        # Log action
        admin = Admin()
        admin.log_action(
            admin_id=admin_id,
            action='reject_refund',
            module='orders',
            entity_id=refund_id,
            description=f'Rejected: {reason}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Refund rejected successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in reject_refund: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to reject refund'}), 500
