"""
WebSocket/Socket.IO Event Handlers for Real-time Features
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, session
from functools import wraps
from datetime import datetime
import json

# Initialize Socket.IO
socketio = SocketIO(cors_allowed_origins="*")

# Store active connections
active_users = {}  # user_id -> socket_id
user_sockets = {}  # socket_id -> user_id
room_members = {}  # room_id -> [user_ids]

# ============================================================================
# AUTHENTICATION & CONNECTION
# ============================================================================

def authenticated_only(f):
    """Decorator to ensure socket connection is authenticated"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return False
        return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
def handle_connect():
    """Handle new socket connection"""
    print(f"User connected: {request.sid}")

@socketio.on('authenticate')
@authenticated_only
def handle_auth(data):
    """Authenticate socket connection with JWT token"""
    try:
        user_id = data.get('user_id')
        
        if not user_id:
            emit('error', {'message': 'User ID required'})
            return
        
        # Store connection mapping
        active_users[user_id] = request.sid
        user_sockets[request.sid] = user_id
        session['user_id'] = user_id
        
        emit('authenticated', {
            'status': 'success',
            'message': 'Socket authenticated',
            'user_id': user_id
        })
        
        print(f"User {user_id} authenticated on socket {request.sid}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket disconnection"""
    if request.sid in user_sockets:
        user_id = user_sockets[request.sid]
        del user_sockets[request.sid]
        
        if user_id in active_users and active_users[user_id] == request.sid:
            del active_users[user_id]
        
        print(f"User {user_id} disconnected")

# ============================================================================
# MESSAGING - REAL-TIME CONVERSATIONS
# ============================================================================

@socketio.on('join_conversation')
@authenticated_only
def handle_join_conversation(data):
    """Join a conversation room"""
    try:
        user_id = session.get('user_id')
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            emit('error', {'message': 'Conversation ID required'})
            return
        
        # Join room named after conversation ID
        room = f"conversation_{conversation_id}"
        join_room(room)
        
        if room not in room_members:
            room_members[room] = []
        
        if user_id not in room_members[room]:
            room_members[room].append(user_id)
        
        # Notify others in room
        emit('user_joined', {
            'user_id': user_id,
            'room': room,
            'members': room_members[room],
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        print(f"User {user_id} joined conversation {conversation_id}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('leave_conversation')
@authenticated_only
def handle_leave_conversation(data):
    """Leave a conversation room"""
    try:
        user_id = session.get('user_id')
        conversation_id = data.get('conversation_id')
        
        room = f"conversation_{conversation_id}"
        leave_room(room)
        
        if room in room_members and user_id in room_members[room]:
            room_members[room].remove(user_id)
        
        # Notify others in room
        emit('user_left', {
            'user_id': user_id,
            'room': room,
            'members': room_members.get(room, []),
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        print(f"User {user_id} left conversation {conversation_id}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('send_message')
@authenticated_only
def handle_send_message(data):
    """Send message to conversation room"""
    try:
        user_id = session.get('user_id')
        conversation_id = data.get('conversation_id')
        message_text = data.get('message')
        
        if not message_text or not conversation_id:
            emit('error', {'message': 'Message and conversation ID required'})
            return
        
        room = f"conversation_{conversation_id}"
        
        # Broadcast message to all members in room
        message_data = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'message': message_text,
            'timestamp': datetime.now().isoformat()
        }
        
        emit('new_message', message_data, room=room)
        print(f"Message from {user_id} in conversation {conversation_id}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('typing')
@authenticated_only
def handle_typing(data):
    """Notify others that user is typing"""
    try:
        user_id = session.get('user_id')
        conversation_id = data.get('conversation_id')
        
        room = f"conversation_{conversation_id}"
        
        emit('user_typing', {
            'user_id': user_id,
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat()
        }, room=room, skip_sid=request.sid)
        
    except Exception as e:
        emit('error', {'message': str(e)})

# ============================================================================
# ORDER UPDATES - REAL-TIME ORDER STATUS
# ============================================================================

@socketio.on('join_order')
@authenticated_only
def handle_join_order(data):
    """Join order update room"""
    try:
        user_id = session.get('user_id')
        order_id = data.get('order_id')
        
        if not order_id:
            emit('error', {'message': 'Order ID required'})
            return
        
        room = f"order_{order_id}"
        join_room(room)
        
        emit('joined_order_room', {
            'order_id': order_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"User {user_id} joined order {order_id} updates")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('order_status_update')
@authenticated_only
def handle_order_status_update(data):
    """Broadcast order status update"""
    try:
        user_id = session.get('user_id')
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            emit('error', {'message': 'Order ID and status required'})
            return
        
        room = f"order_{order_id}"
        
        # Broadcast to all users watching this order
        emit('order_updated', {
            'order_id': order_id,
            'status': new_status,
            'updated_by': user_id,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        print(f"Order {order_id} status updated to {new_status}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

# ============================================================================
# NOTIFICATIONS - REAL-TIME ALERTS
# ============================================================================

@socketio.on('subscribe_notifications')
@authenticated_only
def handle_subscribe_notifications():
    """Subscribe user to notifications"""
    try:
        user_id = session.get('user_id')
        room = f"user_{user_id}_notifications"
        join_room(room)
        
        emit('subscribed_notifications', {
            'message': 'Subscribed to notifications',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"User {user_id} subscribed to notifications")
        
    except Exception as e:
        emit('error', {'message': str(e)})

def send_notification(user_id, notification_type, data):
    """Send notification to specific user"""
    room = f"user_{user_id}_notifications"
    
    notification = {
        'type': notification_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    socketio.emit('notification', notification, room=room)
    print(f"Notification sent to user {user_id}: {notification_type}")

# ============================================================================
# PRODUCT UPDATES - REAL-TIME INVENTORY
# ============================================================================

@socketio.on('subscribe_product')
@authenticated_only
def handle_subscribe_product(data):
    """Subscribe to product updates"""
    try:
        product_id = data.get('product_id')
        
        if not product_id:
            emit('error', {'message': 'Product ID required'})
            return
        
        room = f"product_{product_id}"
        join_room(room)
        
        emit('subscribed_product', {
            'product_id': product_id,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"User subscribed to product {product_id} updates")
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('product_stock_update')
@authenticated_only
def handle_product_stock_update(data):
    """Broadcast product stock update"""
    try:
        product_id = data.get('product_id')
        new_stock = data.get('stock')
        
        if product_id is None or new_stock is None:
            emit('error', {'message': 'Product ID and stock required'})
            return
        
        room = f"product_{product_id}"
        
        emit('stock_updated', {
            'product_id': product_id,
            'stock': new_stock,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        print(f"Product {product_id} stock updated to {new_stock}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

# ============================================================================
# PRESENCE - ONLINE STATUS
# ============================================================================

@socketio.on('set_presence')
@authenticated_only
def handle_set_presence(data):
    """Set user presence status"""
    try:
        user_id = session.get('user_id')
        status = data.get('status', 'online')  # online, away, offline
        
        presence_room = 'global_presence'
        
        emit('presence_updated', {
            'user_id': user_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }, room=presence_room)
        
        print(f"User {user_id} presence updated: {status}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

# ============================================================================
# DIRECT MESSAGE - REAL-TIME ONE-TO-ONE
# ============================================================================

@socketio.on('send_direct_message')
@authenticated_only
def handle_direct_message(data):
    """Send direct message to another user"""
    try:
        sender_id = session.get('user_id')
        recipient_id = data.get('recipient_id')
        message_text = data.get('message')
        
        if not recipient_id or not message_text:
            emit('error', {'message': 'Recipient ID and message required'})
            return
        
        # Send to recipient if online
        room = f"user_{recipient_id}_direct_messages"
        
        message_data = {
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'message': message_text,
            'timestamp': datetime.now().isoformat()
        }
        
        socketio.emit('direct_message', message_data, room=room)
        
        print(f"Direct message from {sender_id} to {recipient_id}")
        
    except Exception as e:
        emit('error', {'message': str(e)})

# ============================================================================
# ERROR HANDLING
# ============================================================================

@socketio.on_error_default
def default_error_handler(e):
    """Handle socket errors"""
    print(f'Socket error: {str(e)}')
    emit('error', {'message': 'An error occurred', 'details': str(e)})

def register_socketio(app):
    """Register Socket.IO with Flask app"""
    socketio.init_app(app)
    return socketio
