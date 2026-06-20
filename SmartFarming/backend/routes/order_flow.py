"""
Order Flow - Complete order lifecycle management
Routes for tracking, status updates, reviews, and returns
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import BaseModel
from datetime import datetime
import json

order_flow_bp = Blueprint('order_flow', __name__, url_prefix='/api/orders')

def _build_directions_url(farmer_lat, farmer_lng, farmer_location, delivery_address):
    """Build Google Maps directions URL from farmer to buyer delivery address (for farmer/delivery use)"""
    import urllib.parse
    if not delivery_address:
        return ''
    if farmer_lat and farmer_lng:
        dest = urllib.parse.quote(delivery_address)
        return f"https://www.google.com/maps/dir/{farmer_lat},{farmer_lng}/{dest}"
    elif farmer_location:
        origin = urllib.parse.quote(farmer_location)
        dest = urllib.parse.quote(delivery_address)
        return f"https://www.google.com/maps/dir/{origin}/{dest}"
    return ''

def _build_buyer_to_farmer_url(farmer_lat, farmer_lng, farmer_location):
    """Build Google Maps directions URL from buyer's current location TO the farmer.
    Uses 'My+Location' as origin so Google Maps auto-detects buyer's GPS."""
    import urllib.parse
    if farmer_lat and farmer_lng:
        return f"https://www.google.com/maps/dir/My+Location/{farmer_lat},{farmer_lng}"
    elif farmer_location:
        dest = urllib.parse.quote(farmer_location)
        return f"https://www.google.com/maps/dir/My+Location/{dest}"
    return ''

# ============================================================================
# ORDER DETAIL
# ============================================================================

@order_flow_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_detail(order_id):
    """Get full order detail with product, farmer, buyer info and tracking"""
    try:
        user_id = get_jwt_identity()
        
        order = BaseModel.execute_query(
            """SELECT o.*,
                      p.name as product_name, p.price as unit_price, p.unit, p.images, p.category,
                      CONCAT(f.first_name, ' ', f.last_name) as farmer_name,
                      f.phone as farmer_phone, f.location as farmer_location,
                      f.latitude as farmer_lat, f.longitude as farmer_lng,
                      CONCAT(b.first_name, ' ', b.last_name) as buyer_name,
                      b.phone as buyer_phone, b.email as buyer_email
               FROM orders o
               LEFT JOIN products p ON o.product_id = p.id
               LEFT JOIN farmers f ON o.farmer_id = f.id
               LEFT JOIN buyers b ON o.buyer_id = b.id
               WHERE o.id = %s""",
            (order_id,), fetch_one=True
        )
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get tracking timeline
        tracking = BaseModel.execute_query(
            """SELECT * FROM order_tracking 
               WHERE order_id = %s 
               ORDER BY created_at ASC""",
            (order_id,), fetch_all=True
        ) or []
        
        # Get review if exists
        review = BaseModel.execute_query(
            "SELECT * FROM buyer_reviews WHERE order_id = %s",
            (order_id,), fetch_one=True
        )
        
        # Get return request if exists
        return_req = BaseModel.execute_query(
            "SELECT * FROM return_requests WHERE order_id = %s",
            (order_id,), fetch_one=True
        )
        
        # Parse images
        images = []
        if order.get('images'):
            try:
                images = json.loads(order['images']) if isinstance(order['images'], str) else order['images']
            except:
                images = []
        
        result = {
            'id': order['id'],
            'order_number': order.get('order_number', ''),
            'status': order['status'],
            'payment_method': order.get('payment_method', 'cod'),
            'payment_status': order.get('payment_status', 'pending'),
            'quantity': order['quantity'],
            'total_amount': float(order['total_amount'] or 0),
            'delivery_address': order.get('delivery_address', ''),
            'notes': order.get('notes', ''),
            'created_at': order['created_at'].isoformat() if order.get('created_at') else '',
            'updated_at': order['updated_at'].isoformat() if order.get('updated_at') else '',
            'product': {
                'id': order.get('product_id'),
                'name': order.get('product_name', ''),
                'price': float(order.get('unit_price', 0)),
                'unit': order.get('unit', 'kg'),
                'category': order.get('category', ''),
                'images': images,
            },
            'farmer': {
                'id': order.get('farmer_id'),
                'name': order.get('farmer_name', ''),
                'phone': order.get('farmer_phone', ''),
                'location': order.get('farmer_location', ''),
                'lat': float(order['farmer_lat']) if order.get('farmer_lat') else None,
                'lng': float(order['farmer_lng']) if order.get('farmer_lng') else None,
                'directions_url': _build_directions_url(
                    order.get('farmer_lat'), order.get('farmer_lng'),
                    order.get('farmer_location', ''), order.get('delivery_address', '')
                ),
                'navigate_to_farmer_url': _build_buyer_to_farmer_url(
                    order.get('farmer_lat'), order.get('farmer_lng'),
                    order.get('farmer_location', '')
                ),
            },
            'buyer': {
                'id': order.get('buyer_id'),
                'name': order.get('buyer_name', ''),
                'phone': order.get('buyer_phone', ''),
                'email': order.get('buyer_email', ''),
            },
            'tracking': [
                {
                    'status': t['status'],
                    'description': t.get('description', ''),
                    'location': t.get('location', ''),
                    'timestamp': t['created_at'].isoformat() if t.get('created_at') else '',
                }
                for t in tracking
            ],
            'review': {
                'product_rating': review.get('product_rating'),
                'product_review': review.get('product_review', ''),
                'farmer_rating': review.get('farmer_rating'),
                'farmer_review': review.get('farmer_review', ''),
            } if review else None,
            'return_request': {
                'reason': return_req.get('reason', ''),
                'status': return_req.get('status', ''),
                'admin_notes': return_req.get('admin_notes', ''),
            } if return_req else None,
        }
        
        return jsonify({'success': True, 'order': result}), 200
    
    except Exception as e:
        print(f"Get order detail error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ORDER TRACKING
# ============================================================================

@order_flow_bp.route('/<int:order_id>/tracking', methods=['GET'])
@jwt_required()
def get_order_tracking(order_id):
    """Get order tracking timeline"""
    try:
        tracking = BaseModel.execute_query(
            """SELECT * FROM order_tracking 
               WHERE order_id = %s 
               ORDER BY created_at ASC""",
            (order_id,), fetch_all=True
        ) or []
        
        order = BaseModel.execute_query(
            "SELECT status, payment_method, created_at FROM orders WHERE id = %s",
            (order_id,), fetch_one=True
        )
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Build full timeline with all possible statuses
        all_statuses = [
            {'key': 'pending', 'label': 'Order Placed', 'icon': '📋'},
            {'key': 'confirmed', 'label': 'Order Confirmed', 'icon': '✅'},
            {'key': 'processing', 'label': 'Processing', 'icon': '⚙️'},
            {'key': 'packed', 'label': 'Packed', 'icon': '📦'},
            {'key': 'dispatched', 'label': 'Dispatched', 'icon': '🚚'},
            {'key': 'in_transit', 'label': 'In Transit', 'icon': '🚛'},
            {'key': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': '🏍️'},
            {'key': 'delivered', 'label': 'Delivered', 'icon': '✅'},
        ]
        
        # Map tracking entries by status
        tracking_map = {}
        for t in tracking:
            tracking_map[t['status']] = t
        
        current_status = order['status']
        status_order = [s['key'] for s in all_statuses]
        current_idx = status_order.index(current_status) if current_status in status_order else -1
        
        timeline = []
        for i, s in enumerate(all_statuses):
            entry = tracking_map.get(s['key'])
            timeline.append({
                'status': s['key'],
                'label': s['label'],
                'icon': s['icon'],
                'completed': i <= current_idx,
                'current': s['key'] == current_status,
                'timestamp': entry['created_at'].isoformat() if entry and entry.get('created_at') else None,
                'description': entry.get('description', '') if entry else '',
                'location': entry.get('location', '') if entry else '',
            })
        
        return jsonify({
            'success': True,
            'current_status': current_status,
            'timeline': timeline,
        }), 200
    
    except Exception as e:
        print(f"Get tracking error: {e}")
        return jsonify({'error': str(e)}), 500


def _update_order_status(order_id, new_status, description, updated_by, location=''):
    """Helper to update order status and add tracking entry"""
    BaseModel.execute_query(
        "UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s",
        (new_status, order_id)
    )
    BaseModel.execute_insert(
        """INSERT INTO order_tracking (order_id, status, description, location, updated_by, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW())""",
        (order_id, new_status, description, location, updated_by)
    )


# ============================================================================
# FARMER ORDER ACTIONS
# ============================================================================

@order_flow_bp.route('/<int:order_id>/accept', methods=['POST'])
@jwt_required()
def accept_order(order_id):
    """Farmer accepts order — notifies buyer with farmer location + directions"""
    try:
        user_id = get_jwt_identity()
        
        # Get order with farmer and buyer details
        order = BaseModel.execute_query(
            """SELECT o.*, 
                      f.first_name as farmer_first, f.last_name as farmer_last,
                      f.phone as farmer_phone, f.location as farmer_location,
                      f.latitude as farmer_lat, f.longitude as farmer_lng,
                      b.first_name as buyer_first, b.last_name as buyer_last,
                      p.name as product_name
               FROM orders o
               LEFT JOIN farmers f ON o.farmer_id = f.id
               LEFT JOIN buyers b ON o.buyer_id = b.id
               LEFT JOIN products p ON o.product_id = p.id
               WHERE o.id = %s AND o.farmer_id = %s""",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order['status'] != 'pending':
            return jsonify({'error': f'Cannot accept order in {order["status"]} status'}), 400
        
        _update_order_status(order_id, 'confirmed', 'Order accepted by farmer', str(user_id))
        
        # Build directions URLs
        farmer_name = f"{order.get('farmer_first', '')} {order.get('farmer_last', '')}".strip() or 'Farmer'
        farmer_lat = order.get('farmer_lat')
        farmer_lng = order.get('farmer_lng')
        farmer_location = order.get('farmer_location', '')
        delivery_address = order.get('delivery_address', '')
        
        # Farmer → Buyer (for delivery)
        directions_url = _build_directions_url(farmer_lat, farmer_lng, farmer_location, delivery_address)
        # Buyer → Farmer (for buyer navigation to farmer - uses buyer's GPS)
        navigate_to_farmer_url = _build_buyer_to_farmer_url(farmer_lat, farmer_lng, farmer_location)
        
        # Notify buyer with farmer details + directions
        try:
            notification_msg = (
                f'Your order #{order.get("order_number", order_id)} for {order.get("product_name", "your product")} '
                f'has been accepted by {farmer_name}! '
                f'Farmer Location: {farmer_location or "Available"}. '
                f'Contact: {order.get("farmer_phone", "N/A")}.'
            )
            
            notification_data = {
                'order_id': order_id,
                'order_number': order.get('order_number', ''),
                'farmer_name': farmer_name,
                'farmer_phone': order.get('farmer_phone', ''),
                'farmer_location': farmer_location,
                'farmer_lat': float(farmer_lat) if farmer_lat else None,
                'farmer_lng': float(farmer_lng) if farmer_lng else None,
                'directions_url': directions_url,
                'navigate_to_farmer_url': navigate_to_farmer_url,
            }
            
            BaseModel.execute_insert(
                """INSERT INTO notifications (user_id, title, message, type, data, created_at)
                   VALUES (%s, %s, %s, %s, %s, NOW())""",
                (order['buyer_id'], 'Order Confirmed!',
                 notification_msg, 'order',
                 json.dumps(notification_data))
            )
        except Exception as notif_err:
            print(f"Accept order notification error: {notif_err}")
        
        return jsonify({
            'success': True, 
            'message': 'Order accepted',
            'farmer_location': {
                'name': farmer_name,
                'location': farmer_location,
                'lat': float(farmer_lat) if farmer_lat else None,
                'lng': float(farmer_lng) if farmer_lng else None,
                'phone': order.get('farmer_phone', ''),
                'directions_url': directions_url,
                'navigate_to_farmer_url': navigate_to_farmer_url,
            }
        }), 200
    
    except Exception as e:
        print(f"Accept order error: {e}")
        return jsonify({'error': str(e)}), 500


@order_flow_bp.route('/<int:order_id>/reject', methods=['POST'])
@jwt_required()
def reject_order(order_id):
    """Farmer rejects order"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        reason = data.get('reason', 'Order rejected by farmer')
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order['status'] not in ('pending', 'confirmed'):
            return jsonify({'error': f'Cannot reject order in {order["status"]} status'}), 400
        
        _update_order_status(order_id, 'cancelled', f'Rejected: {reason}', str(user_id))
        
        # Restore product quantity
        BaseModel.execute_query(
            "UPDATE products SET quantity = quantity + %s WHERE id = %s",
            (order['quantity'], order['product_id'])
        )
        
        # Notify buyer
        try:
            BaseModel.execute_insert(
                """INSERT INTO notifications (user_id, title, message, type, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (order['buyer_id'], 'Order Rejected',
                 f'Your order #{order.get("order_number", order_id)} was rejected: {reason}',
                 'order')
            )
        except:
            pass
        
        return jsonify({'success': True, 'message': 'Order rejected'}), 200
    
    except Exception as e:
        print(f"Reject order error: {e}")
        return jsonify({'error': str(e)}), 500


@order_flow_bp.route('/<int:order_id>/update-status', methods=['POST'])
@jwt_required()
def update_order_status(order_id):
    """Farmer updates order status through the pipeline"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        new_status = data.get('status', '')
        description = data.get('description', '')
        location = data.get('location', '')
        
        valid_transitions = {
            'confirmed': ['processing'],
            'processing': ['packed'],
            'packed': ['dispatched'],
            'dispatched': ['in_transit'],
            'in_transit': ['out_for_delivery'],
            'out_for_delivery': ['delivered'],
        }
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        current = order['status']
        allowed = valid_transitions.get(current, [])
        if new_status not in allowed:
            return jsonify({'error': f'Cannot transition from {current} to {new_status}. Allowed: {allowed}'}), 400
        
        # ── DELIVERY OTP GATE ──
        # For ONLINE payment: farmer CANNOT mark delivered directly.
        # Must go through send-delivery-otp → verify-delivery-otp flow.
        if new_status == 'delivered' and order.get('payment_method') == 'online':
            return jsonify({
                'error': 'Online payment orders require delivery OTP verification. '
                         'Use the "Send OTP" button first, then enter the OTP from buyer.',
                'requires_otp': True,
                'payment_method': 'online',
            }), 400
        
        status_descriptions = {
            'processing': 'Order is being processed',
            'packed': 'Order has been packed and ready for dispatch',
            'dispatched': 'Order has been dispatched',
            'in_transit': 'Order is in transit',
            'out_for_delivery': 'Order is out for delivery',
            'delivered': 'Order delivered — Cash on Delivery confirmed',
        }
        
        if not description:
            description = status_descriptions.get(new_status, f'Status updated to {new_status}')
        
        _update_order_status(order_id, new_status, description, str(user_id), location)
        
        # If delivered via COD, mark payment completed
        if new_status == 'delivered':
            BaseModel.execute_query(
                "UPDATE orders SET payment_status = 'completed' WHERE id = %s",
                (order_id,)
            )
        
        # Notify buyer
        status_messages = {
            'processing': 'Your order is being processed! 🔄',
            'packed': 'Your order has been packed! 📦',
            'dispatched': 'Your order has been dispatched! 🚚',
            'in_transit': 'Your order is on its way! 🚛',
            'out_for_delivery': 'Your order is out for delivery! 🏍️',
            'delivered': 'Your order has been delivered! ✅',
        }
        
        try:
            BaseModel.execute_insert(
                """INSERT INTO notifications (user_id, title, message, type, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (order['buyer_id'], f'Order Update - {new_status.replace("_", " ").title()}',
                 status_messages.get(new_status, f'Order #{order.get("order_number", order_id)} status: {new_status}'),
                 'order')
            )
        except:
            pass
        
        return jsonify({'success': True, 'message': f'Order status updated to {new_status}'}), 200
    
    except Exception as e:
        print(f"Update order status error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DELIVERY OTP — Send to Buyer (for Online Payment orders)
# ============================================================================

@order_flow_bp.route('/<int:order_id>/send-delivery-otp', methods=['POST'])
@jwt_required()
def send_delivery_otp(order_id):
    """
    Farmer triggers delivery OTP for ONLINE payment orders.
    Generates 6-digit OTP → emails buyer → buyer tells farmer → farmer verifies.
    """
    try:
        user_id = get_jwt_identity()
        
        order = BaseModel.execute_query(
            """SELECT o.*, b.email as buyer_email, b.first_name as buyer_first_name,
                      CONCAT(b.first_name, ' ', b.last_name) as buyer_name,
                      p.name as product_name
               FROM orders o
               LEFT JOIN buyers b ON o.buyer_id = b.id
               LEFT JOIN products p ON o.product_id = p.id
               WHERE o.id = %s AND o.farmer_id = %s""",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['status'] != 'out_for_delivery':
            return jsonify({'error': 'Order must be "Out for Delivery" to send OTP'}), 400
        
        if order.get('payment_method') != 'online':
            return jsonify({'error': 'Delivery OTP is only for online payment orders'}), 400
        
        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))
        
        # Store in DB
        BaseModel.execute_query(
            "UPDATE orders SET delivery_otp = %s, delivery_otp_sent_at = NOW() WHERE id = %s",
            (otp, order_id)
        )
        
        # Send OTP email to buyer
        buyer_email = order.get('buyer_email')
        buyer_name = order.get('buyer_name', 'Customer')
        order_number = order.get('order_number', str(order_id))
        product_name = order.get('product_name', 'your product')
        
        if buyer_email:
            try:
                from utils.email_service import EmailService
                subject = f"🔐 Delivery OTP for Order #{order_number}"
                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <div style="background: linear-gradient(135deg, #166534, #22c55e); padding: 20px; border-radius: 12px 12px 0 0; text-align: center;">
                                <h2 style="color: #fff; margin: 0;">🔐 Delivery Verification OTP</h2>
                            </div>
                            <div style="background: #fff; padding: 24px; border: 1px solid #e5e7eb; border-radius: 0 0 12px 12px;">
                                <p>Hi <strong>{buyer_name}</strong>,</p>
                                
                                <p>Your order <strong>#{order_number}</strong> ({product_name}) is being delivered!</p>
                                
                                <p>Please share this OTP with the delivery person to confirm receipt:</p>
                                
                                <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); padding: 24px; text-align: center; margin: 20px 0; border-radius: 12px; border: 2px solid #22c55e;">
                                    <h1 style="color: #166534; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
                                </div>
                                
                                <div style="background: #fffbeb; padding: 12px 16px; border-radius: 8px; border: 1px solid #fbbf24;">
                                    <p style="margin: 0; font-size: 14px; color: #92400e;">
                                        ⚠️ <strong>Important:</strong> Only share this OTP after you receive your product. 
                                        This confirms delivery and releases payment to the farmer.
                                    </p>
                                </div>
                                
                                <p style="font-size: 13px; color: #888; margin-top: 16px;">
                                    This OTP is valid for 30 minutes. If you didn't place this order, please contact support.
                                </p>
                            </div>
                            <p style="font-size: 11px; color: #aaa; text-align: center; margin-top: 12px;">
                                Smart Farmer Marketplace • {datetime.now().strftime('%d %b %Y, %I:%M %p')}
                            </p>
                        </div>
                    </body>
                </html>
                """
                EmailService._send_email(buyer_email, subject, html_body)
            except Exception as email_err:
                print(f"Delivery OTP email error: {email_err}")
        
        return jsonify({
            'success': True,
            'message': f'Delivery OTP sent to buyer\'s email ({buyer_email})',
            'otp_sent': True,
        }), 200
    
    except Exception as e:
        print(f"Send delivery OTP error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DELIVERY OTP — Verify (Farmer enters OTP from buyer)
# ============================================================================

@order_flow_bp.route('/<int:order_id>/verify-delivery-otp', methods=['POST'])
@jwt_required()
def verify_delivery_otp(order_id):
    """
    Farmer enters the OTP that buyer told them.
    If OTP matches → mark delivered + release payment.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        entered_otp = data.get('otp', '').strip()
        
        if not entered_otp or len(entered_otp) != 6:
            return jsonify({'error': 'Please enter a valid 6-digit OTP'}), 400
        
        order = BaseModel.execute_query(
            """SELECT o.*, p.name as product_name,
                      CONCAT(b.first_name, ' ', b.last_name) as buyer_name,
                      b.email as buyer_email
               FROM orders o
               LEFT JOIN products p ON o.product_id = p.id
               LEFT JOIN buyers b ON o.buyer_id = b.id
               WHERE o.id = %s AND o.farmer_id = %s""",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['status'] != 'out_for_delivery':
            return jsonify({'error': 'Order must be out for delivery'}), 400
        
        stored_otp = order.get('delivery_otp', '')
        otp_sent_at = order.get('delivery_otp_sent_at')
        
        if not stored_otp:
            return jsonify({'error': 'No OTP was sent. Please send OTP first.'}), 400
        
        # Check expiry (30 minutes)
        if otp_sent_at:
            from datetime import timedelta
            now = datetime.utcnow()
            if hasattr(otp_sent_at, 'replace'):
                otp_time = otp_sent_at.replace(tzinfo=None) if otp_sent_at.tzinfo else otp_sent_at
            else:
                otp_time = otp_sent_at
            if now - otp_time > timedelta(minutes=30):
                return jsonify({'error': 'OTP expired. Please send a new OTP.'}), 400
        
        if entered_otp != stored_otp:
            return jsonify({'error': 'Invalid OTP. Please check and try again.'}), 400
        
        # ✅ OTP VERIFIED — Mark as delivered + release payment
        _update_order_status(
            order_id, 'delivered',
            'Order delivered — Verified via OTP. Payment released to farmer.',
            str(user_id)
        )
        
        # Mark payment completed
        BaseModel.execute_query(
            "UPDATE orders SET payment_status = 'completed', delivery_otp = NULL WHERE id = %s",
            (order_id,)
        )
        
        # Notify buyer
        try:
            BaseModel.execute_insert(
                """INSERT INTO notifications (user_id, title, message, type, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (order['buyer_id'], 'Order Delivered! ✅',
                 f'Your order #{order.get("order_number", order_id)} has been delivered and payment is confirmed.',
                 'order')
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'OTP verified! Order delivered successfully. Payment released to farmer. 🎉',
            'delivered': True,
        }), 200
    
    except Exception as e:
        print(f"Verify delivery OTP error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# COD CONFIRM — Farmer confirms cash received
# ============================================================================

@order_flow_bp.route('/<int:order_id>/confirm-cod', methods=['POST'])
@jwt_required()
def confirm_cod_delivery(order_id):
    """Farmer confirms cash received and marks order as delivered (COD only)"""
    try:
        user_id = get_jwt_identity()
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND farmer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order['status'] != 'out_for_delivery':
            return jsonify({'error': 'Order must be out for delivery'}), 400
        
        if order.get('payment_method') != 'cod':
            return jsonify({'error': 'This endpoint is for Cash on Delivery orders only'}), 400
        
        _update_order_status(
            order_id, 'delivered',
            'Order delivered — Cash on Delivery confirmed by farmer.',
            str(user_id)
        )
        
        BaseModel.execute_query(
            "UPDATE orders SET payment_status = 'completed' WHERE id = %s",
            (order_id,)
        )
        
        # Notify buyer
        try:
            BaseModel.execute_insert(
                """INSERT INTO notifications (user_id, title, message, type, created_at)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (order['buyer_id'], 'Order Delivered! ✅',
                 f'Your order #{order.get("order_number", order_id)} has been delivered. Thank you!',
                 'order')
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Cash received confirmed! Order delivered successfully. 💰',
            'delivered': True,
        }), 200
    
    except Exception as e:
        print(f"Confirm COD error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BUYER: CANCEL ORDER
# ============================================================================

@order_flow_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """Buyer cancels order"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        reason = data.get('reason', 'Cancelled by buyer')
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order['status'] not in ('pending', 'confirmed'):
            return jsonify({'error': 'Cannot cancel order at this stage'}), 400
        
        _update_order_status(order_id, 'cancelled', f'Cancelled by buyer: {reason}', str(user_id))
        
        # Restore product quantity
        BaseModel.execute_query(
            "UPDATE products SET quantity = quantity + %s WHERE id = %s",
            (order['quantity'], order['product_id'])
        )
        
        return jsonify({'success': True, 'message': 'Order cancelled'}), 200
    
    except Exception as e:
        print(f"Cancel order error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BUYER: REVIEW & RATING
# ============================================================================

@order_flow_bp.route('/<int:order_id>/review', methods=['POST'])
@jwt_required()
def submit_review(order_id):
    """Buyer submits review after delivery"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order['status'] != 'delivered':
            return jsonify({'error': 'Can only review delivered orders'}), 400
        
        # Check if already reviewed
        existing = BaseModel.execute_query(
            "SELECT id FROM buyer_reviews WHERE order_id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if existing:
            return jsonify({'error': 'Already reviewed this order'}), 400
        
        product_rating = data.get('product_rating', 5)
        farmer_rating = data.get('farmer_rating', 5)
        product_review = data.get('product_review', '')
        farmer_review = data.get('farmer_review', '')
        
        # Validate ratings
        product_rating = max(1, min(5, int(product_rating)))
        farmer_rating = max(1, min(5, int(farmer_rating)))
        
        BaseModel.execute_insert(
            """INSERT INTO buyer_reviews 
               (order_id, buyer_id, product_id, farmer_id, product_rating, product_review, farmer_rating, farmer_review, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (order_id, int(user_id), order['product_id'], order['farmer_id'],
             product_rating, product_review, farmer_rating, farmer_review)
        )
        
        # Update product average rating
        avg = BaseModel.execute_query(
            "SELECT AVG(product_rating) as avg_rating, COUNT(*) as total FROM buyer_reviews WHERE product_id = %s",
            (order['product_id'],), fetch_one=True
        )
        if avg:
            BaseModel.execute_query(
                "UPDATE products SET average_rating = %s, total_reviews = %s WHERE id = %s",
                (round(float(avg['avg_rating'] or 0), 1), avg['total'], order['product_id'])
            )
        
        return jsonify({'success': True, 'message': 'Review submitted! Thank you for your feedback.'}), 201
    
    except Exception as e:
        print(f"Submit review error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BUYER: RETURN REQUEST
# ============================================================================

@order_flow_bp.route('/<int:order_id>/return', methods=['POST'])
@jwt_required()
def request_return(order_id):
    """Buyer requests return"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', '')
        
        if not reason:
            return jsonify({'error': 'Return reason is required'}), 400
        
        order = BaseModel.execute_query(
            "SELECT * FROM orders WHERE id = %s AND buyer_id = %s",
            (order_id, int(user_id)), fetch_one=True
        )
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order['status'] != 'delivered':
            return jsonify({'error': 'Can only return delivered orders'}), 400
        
        # Check if already requested
        existing = BaseModel.execute_query(
            "SELECT id FROM return_requests WHERE order_id = %s",
            (order_id,), fetch_one=True
        )
        if existing:
            return jsonify({'error': 'Return already requested for this order'}), 400
        
        BaseModel.execute_insert(
            """INSERT INTO return_requests (order_id, buyer_id, reason, status, created_at)
               VALUES (%s, %s, %s, 'pending', NOW())""",
            (order_id, int(user_id), reason)
        )
        
        _update_order_status(order_id, 'return_requested', f'Return requested: {reason}', str(user_id))
        
        return jsonify({'success': True, 'message': 'Return request submitted'}), 201
    
    except Exception as e:
        print(f"Return request error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BUYER: CHECKOUT
# ============================================================================

@order_flow_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Checkout from cart - creates orders with payment method selection"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        payment_method = data.get('payment_method', 'cod')  # 'cod' or 'online'
        delivery_address = data.get('delivery_address', '')
        notes = data.get('notes', '')
        delivery_fee = float(data.get('delivery_fee', 0))  # Delivery fee from frontend
        
        if not delivery_address:
            return jsonify({'error': 'Delivery address is required'}), 400
        
        # Get buyer
        buyer = BaseModel.execute_query(
            "SELECT * FROM buyers WHERE id = %s", (int(user_id),), fetch_one=True
        )
        if not buyer:
            return jsonify({'error': 'Buyer not found'}), 404
        
        # Get cart items
        cart_items = BaseModel.execute_query(
            """SELECT c.*, p.name as product_name, p.price as product_price, 
                      p.farmer_id, p.quantity as available_qty, p.unit,
                      p.discount_percentage
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.buyer_id = %s AND c.is_active = true""",
            (int(user_id),), fetch_all=True
        ) or []
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Validate stock and create orders
        import uuid
        created_orders = []
        total_amount = 0
        num_items = len(cart_items)
        
        # Split delivery fee equally across orders (so each order's share is recorded)
        delivery_fee_per_order = round(delivery_fee / num_items, 2) if num_items > 0 else 0
        
        for idx, item in enumerate(cart_items):
            qty = float(item['quantity'] or 1)
            avail = float(item['available_qty'] or 0)
            if qty > avail:
                return jsonify({
                    'error': f'Not enough stock for {item["product_name"]}. Available: {int(avail)}'
                }), 400
            
            # Calculate price with discount
            price = float(item['product_price'] or 0)
            discount = float(item.get('discount_percentage', 0) or 0)
            if discount > 0:
                price = price * (1 - discount / 100)
            
            item_total = round(price * qty, 2)
            
            # Add delivery fee share to this order's total
            order_delivery_fee = delivery_fee_per_order
            # Adjust last order to absorb rounding difference
            if idx == num_items - 1:
                order_delivery_fee = round(delivery_fee - delivery_fee_per_order * (num_items - 1), 2)
            
            item_total_with_delivery = round(item_total + order_delivery_fee, 2)
            total_amount += item_total_with_delivery
            
            # ── PAYMENT SPLIT CALCULATION ──
            # GST: 1% of product total → goes to Admin
            # Platform Fee: 2% of product total → goes to Admin (hidden)
            # Delivery Fee: 100% → goes to Admin
            # Farmer Payout: 97% of product total (no share of delivery fee)
            GST_RATE = 1.0    # 1%
            PLATFORM_FEE_RATE = 2.0  # 2%
            
            gst_amount = round(item_total * GST_RATE / 100, 2)
            platform_fee = round(item_total * PLATFORM_FEE_RATE / 100, 2)
            farmer_payout = round(item_total - gst_amount - platform_fee, 2)
            # Admin total = GST + platform fee + delivery fee
            admin_total = round(gst_amount + platform_fee + order_delivery_fee, 2)
            
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            order_id = BaseModel.execute_insert(
                """INSERT INTO orders 
                   (order_number, buyer_id, farmer_id, product_id, quantity, total_amount,
                    gst_amount, platform_fee, farmer_payout,
                    status, payment_method, payment_status, delivery_address, notes, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
                (order_number, int(user_id), item['farmer_id'], item['product_id'],
                 qty, item_total_with_delivery,
                 gst_amount, round(platform_fee + order_delivery_fee, 2), farmer_payout,
                 'pending', payment_method,
                 'cod_pending' if payment_method == 'cod' else 'pending',
                 delivery_address, notes)
            )
            
            # Record in platform_earnings (admin revenue tracking)
            # platform_fee now includes delivery_fee share for this order
            try:
                BaseModel.execute_insert(
                    """INSERT INTO platform_earnings 
                       (order_id, order_number, farmer_id, buyer_id, total_amount,
                        gst_amount, platform_fee, farmer_payout, gst_rate, platform_fee_rate,
                        settlement_status, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())""",
                    (order_id, order_number, item['farmer_id'], int(user_id), item_total_with_delivery,
                     gst_amount, round(platform_fee + order_delivery_fee, 2), farmer_payout, GST_RATE, PLATFORM_FEE_RATE)
                )
            except Exception as pe_err:
                print(f"Platform earnings record error (non-critical): {pe_err}")
            
            # Add tracking entry
            BaseModel.execute_insert(
                """INSERT INTO order_tracking (order_id, status, description, updated_by, created_at)
                   VALUES (%s, 'pending', 'Order placed', %s, NOW())""",
                (order_id, str(user_id))
            )
            
            # Reduce product stock
            BaseModel.execute_query(
                "UPDATE products SET quantity = quantity - %s WHERE id = %s",
                (item['quantity'], item['product_id'])
            )
            
            # Auto mark SOLD OUT if quantity reaches 0
            remaining = BaseModel.execute_query(
                "SELECT quantity FROM products WHERE id = %s",
                (item['product_id'],), fetch_one=True
            )
            if remaining and float(remaining['quantity'] or 0) <= 0:
                BaseModel.execute_query(
                    "UPDATE products SET status = 'sold_out', is_available = false WHERE id = %s",
                    (item['product_id'],)
                )
                try:
                    BaseModel.execute_insert(
                        """INSERT INTO notifications (user_id, title, message, type, created_at)
                           VALUES (%s, %s, %s, %s, NOW())""",
                        (item['farmer_id'], 'Product Sold Out!',
                         f'Your product "{item["product_name"]}" is now SOLD OUT (0 stock remaining). Please restock.',
                         'stock')
                    )
                except:
                    pass
            elif remaining and float(remaining['quantity'] or 0) <= 20:
                try:
                    BaseModel.execute_insert(
                        """INSERT INTO notifications (user_id, title, message, type, created_at)
                           VALUES (%s, %s, %s, %s, NOW())""",
                        (item['farmer_id'], 'Low Stock Alert!',
                         f'Your product "{item["product_name"]}" has only {int(float(remaining["quantity"]))} units left. Consider restocking soon.',
                         'stock')
                    )
                except:
                    pass
            
            # Notify farmer (shows only their payout amount - no mention of fees or delivery)
            try:
                BaseModel.execute_insert(
                    """INSERT INTO notifications (user_id, title, message, type, created_at)
                       VALUES (%s, %s, %s, %s, NOW())""",
                    (item['farmer_id'], 'New Order!',
                     f'You have a new order #{order_number} for {item["product_name"]} (Qty: {int(qty)}) - Earnings: Rs.{farmer_payout}',
                     'order')
                )
            except:
                pass
            
            created_orders.append({
                'order_id': order_id,
                'order_number': order_number,
                'product_name': item['product_name'],
                'quantity': int(qty),
                'total': item_total_with_delivery,
                'delivery_fee': order_delivery_fee,
            })
        
        # Clear cart
        BaseModel.execute_query(
            "UPDATE cart SET is_active = false WHERE buyer_id = %s",
            (int(user_id),)
        )
        
        return jsonify({
            'success': True,
            'message': f'{len(created_orders)} order(s) placed successfully!',
            'orders': created_orders,
            'total_amount': total_amount,
            'delivery_fee': delivery_fee,
            'payment_method': payment_method,
        }), 201
    
    except Exception as e:
        print(f"Checkout error: {e}")
        return jsonify({'error': str(e)}), 500
