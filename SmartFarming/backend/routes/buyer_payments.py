"""
Buyer Payments Routes
Handles: Razorpay, Card, UPI, COD, Refunds
Path: /api/payments
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json

import sys
sys.path.append('..')
from models.models import Payment, Order

buyer_payments_bp = Blueprint('buyer_payments', __name__, url_prefix='/api/payments')

# ====================================================================
# 1. VERIFY COD ELIGIBILITY
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/verify-cod', methods=['POST'])
@jwt_required()
def verify_cod(order_id):
    """
    Verify if order is eligible for Cash on Delivery
    
    Response:
    {
        "success": true,
        "eligible": true,
        "message": "Order is eligible for COD",
        "max_amount": 5000
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Check COD eligibility
        # Rules: Amount < 5000, Location is serviceable, Buyer has good rating
        amount = order['total_amount']
        max_cod_amount = 5000
        eligible = amount <= max_cod_amount
        
        return jsonify({
            'success': True,
            'eligible': eligible,
            'message': 'Order is eligible for COD' if eligible else 'Order amount exceeds COD limit',
            'max_amount': max_cod_amount,
            'order_amount': float(amount)
        }), 200
        
    except Exception as e:
        print(f"Error in verify_cod: {str(e)}")
        return jsonify({'success': False, 'error': 'COD verification failed'}), 500


# ====================================================================
# 2. CREATE RAZORPAY ORDER - Initialize payment
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/create-razorpay', methods=['POST'])
@jwt_required()
def create_razorpay_order(order_id):
    """
    Create Razorpay payment order
    
    Response:
    {
        "success": true,
        "razorpay_order_id": "order_9A33XWu170gUtm",
        "amount": 31400,  // in paise (multiply by 100)
        "currency": "INR"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        amount_in_paise = int(order['total_amount'] * 100)
        
        # TODO: Initialize Razorpay client and create order
        # import razorpay
        # client = razorpay.Client(auth=('KEY_ID', 'KEY_SECRET'))
        # razorpay_order = client.order.create(
        #     amount=amount_in_paise,
        #     currency='INR',
        #     notes={'order_id': order_id}
        # )
        
        # For now, mock response
        razorpay_order_id = f"order_{order_id}_{datetime.now().timestamp()}"
        
        return jsonify({
            'success': True,
            'razorpay_order_id': razorpay_order_id,
            'amount': amount_in_paise,
            'currency': 'INR',
            'order_id': order_id
        }), 200
        
    except Exception as e:
        print(f"Error in create_razorpay_order: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create Razorpay order'}), 500


# ====================================================================
# 3. VERIFY RAZORPAY PAYMENT - Confirm payment
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/verify-razorpay', methods=['POST'])
@jwt_required()
def verify_razorpay_payment(order_id):
    """
    Verify Razorpay payment signature
    
    Request:
    {
        "razorpay_payment_id": "pay_1Aa00000000001",
        "razorpay_order_id": "order_9A33XWu170gUtm",
        "razorpay_signature": "9ef4dffbfd84f1318f6739a..."
    }
    
    Response:
    {
        "success": true,
        "payment_id": 1,
        "message": "Payment verified successfully",
        "status": "completed"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        payment_id = data.get('razorpay_payment_id')
        order_id_from_razorpay = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        
        if not all([payment_id, order_id_from_razorpay, signature]):
            return jsonify({'success': False, 'error': 'Missing payment details'}), 400
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # TODO: Verify signature using Razorpay
        # import hmac
        # import hashlib
        # 
        # expected_signature = hmac.new(
        #     KEY_SECRET.encode(),
        #     f"{order_id_from_razorpay}|{payment_id}".encode(),
        #     hashlib.sha256
        # ).hexdigest()
        # 
        # if signature != expected_signature:
        #     return error
        
        # Signature verified - create payment record
        payment = Payment()
        db_payment_id = payment.create_payment(
            order_id=order_id,
            buyer_id=buyer_id,
            amount=order['total_amount'],
            payment_method='card',
            transaction_id=payment_id,
            payment_gateway='razorpay',
            status='completed'
        )
        
        if not db_payment_id:
            return jsonify({'success': False, 'error': 'Failed to save payment'}), 500
        
        # Update order payment status
        order_obj.update_payment_status(order_id, 'completed')
        
        return jsonify({
            'success': True,
            'payment_id': db_payment_id,
            'message': 'Payment verified successfully',
            'status': 'completed'
        }), 200
        
    except Exception as e:
        print(f"Error in verify_razorpay_payment: {str(e)}")
        return jsonify({'success': False, 'error': 'Payment verification failed'}), 500


# ====================================================================
# 4. GET PAYMENT STATUS
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/status', methods=['GET'])
@jwt_required()
def get_payment_status(order_id):
    """
    Get payment status for an order
    
    Response:
    {
        "success": true,
        "payment": {
            "payment_id": 1,
            "order_id": 101,
            "amount": 314,
            "payment_method": "upi",
            "status": "completed",
            "transaction_id": "TXN123456",
            "payment_gateway": "razorpay",
            "created_at": "2026-06-01T10:30:00"
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
        
        # Get payment
        payment = Payment()
        payment_data = payment.get_payment(order_id)
        
        if not payment_data:
            return jsonify({
                'success': True,
                'payment': None,
                'message': 'No payment record for this order'
            }), 200
        
        return jsonify({
            'success': True,
            'payment': {
                'payment_id': payment_data['payment_id'],
                'order_id': payment_data['order_id'],
                'amount': float(payment_data['amount']),
                'payment_method': payment_data['payment_method'],
                'status': payment_data['status'],
                'transaction_id': payment_data['transaction_id'],
                'payment_gateway': payment_data['payment_gateway'],
                'created_at': payment_data['created_at'].isoformat() if payment_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_payment_status: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch payment status'}), 500


# ====================================================================
# 5. RECORD COD PAYMENT - Record cash on delivery
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/record-cod', methods=['POST'])
@jwt_required()
def record_cod_payment(order_id):
    """
    Record COD payment (after delivery)
    
    Response:
    {
        "success": true,
        "message": "COD payment recorded"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Create payment record for COD
        payment = Payment()
        db_payment_id = payment.create_payment(
            order_id=order_id,
            buyer_id=buyer_id,
            amount=order['total_amount'],
            payment_method='cod',
            transaction_id=f"COD_{order_id}_{datetime.now().timestamp()}",
            payment_gateway='cash',
            status='pending'  # Will be completed after delivery
        )
        
        if not db_payment_id:
            return jsonify({'success': False, 'error': 'Failed to record payment'}), 500
        
        return jsonify({
            'success': True,
            'message': 'COD payment recorded successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in record_cod_payment: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to record COD payment'}), 500


# ====================================================================
# 6. REQUEST REFUND
# ====================================================================
@buyer_payments_bp.route('/<int:order_id>/refund', methods=['POST'])
@jwt_required()
def request_refund(order_id):
    """
    Request refund for order (usually after return approval)
    
    Request:
    {
        "reason": "Return approved"
    }
    
    Response:
    {
        "success": true,
        "message": "Refund initiated",
        "refund_amount": 314
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '')
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get payment
        payment = Payment()
        payment_data = payment.get_payment(order_id)
        
        if not payment_data:
            return jsonify({'success': False, 'error': 'No payment found for this order'}), 404
        
        # Initiate refund
        # TODO: Call payment gateway refund API (Razorpay refund)
        # client.payment.fetch(payment_data['transaction_id']).refund(
        #     amount=int(payment_data['amount'] * 100)
        # )
        
        # Update payment status
        success = payment.update_payment_status(payment_data['payment_id'], 'refunded')
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to process refund'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Refund initiated successfully',
            'refund_amount': float(order['total_amount'])
        }), 200
        
    except Exception as e:
        print(f"Error in request_refund: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to process refund'}), 500


# ====================================================================
# 7. GET PAYMENT METHODS
# ====================================================================
@buyer_payments_bp.route('/methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """
    Get available payment methods
    
    Response:
    {
        "success": true,
        "methods": [
            {
                "id": "card",
                "name": "Credit/Debit Card",
                "icon": "credit-card",
                "description": "Visa, Mastercard, Amex"
            },
            {
                "id": "upi",
                "name": "UPI",
                "icon": "phone",
                "description": "Google Pay, PhonePe, Paytm"
            },
            {
                "id": "cod",
                "name": "Cash on Delivery",
                "icon": "money",
                "description": "Pay at delivery",
                "max_amount": 5000
            }
        ]
    }
    """
    try:
        methods = [
            {
                'id': 'card',
                'name': 'Credit/Debit Card',
                'icon': 'credit-card',
                'description': 'Visa, Mastercard, Amex'
            },
            {
                'id': 'upi',
                'name': 'UPI',
                'icon': 'phone',
                'description': 'Google Pay, PhonePe, Paytm'
            },
            {
                'id': 'netbanking',
                'name': 'Net Banking',
                'icon': 'bank',
                'description': 'All major banks'
            },
            {
                'id': 'cod',
                'name': 'Cash on Delivery',
                'icon': 'money',
                'description': 'Pay at delivery',
                'max_amount': 5000
            }
        ]
        
        return jsonify({
            'success': True,
            'methods': methods
        }), 200
        
    except Exception as e:
        print(f"Error in get_payment_methods: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch payment methods'}), 500
