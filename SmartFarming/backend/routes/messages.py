"""
Messaging Module - Real-time Chat Between Farmers and Buyers
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import User, Message, Conversation, Notification, BaseModel
from datetime import datetime

messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

# ============================================================================
# CONVERSATIONS
# ============================================================================

@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get user's conversations"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        query = """
        SELECT c.*, 
               u1.first_name as user1_name, u1.email as user1_email,
               u2.first_name as user2_name, u2.email as user2_email,
               m.message as last_message, m.created_at as last_message_time
        FROM conversations c
        LEFT JOIN users u1 ON c.user1_id = u1.id
        LEFT JOIN users u2 ON c.user2_id = u2.id
        LEFT JOIN messages m ON c.last_message_id = m.id
        WHERE c.user1_id = %s OR c.user2_id = %s
        ORDER BY c.updated_at DESC
        LIMIT %s OFFSET %s
        """
        
        conversations = BaseModel.execute_query(
            query, 
            (user_id, user_id, limit, offset), 
            fetch_all=True
        )
        
        return jsonify({
            'conversations': conversations,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get conversations error: {e}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations/<int:other_user_id>', methods=['GET', 'POST'])
@jwt_required()
def get_or_create_conversation(other_user_id):
    """Get or create conversation with another user"""
    try:
        user_id = get_jwt_identity()
        
        if user_id == other_user_id:
            return jsonify({'error': 'Cannot chat with yourself'}), 400
        
        # Check if both users exist
        user = User.get_by_id(user_id)
        other_user = User.get_by_id(other_user_id)
        
        if not user or not other_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find or create conversation
        query = """
        SELECT * FROM conversations 
        WHERE (user1_id = %s AND user2_id = %s) 
           OR (user1_id = %s AND user2_id = %s)
        LIMIT 1
        """
        
        conversation = BaseModel.execute_query(
            query, 
            (user_id, other_user_id, other_user_id, user_id),
            fetch_one=True
        )
        
        if not conversation:
            # Create new conversation
            conversation_id = BaseModel.execute_insert(
                """INSERT INTO conversations (user1_id, user2_id, created_at, updated_at)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, other_user_id, datetime.now(), datetime.now())
            )
            conversation = {
                'id': conversation_id,
                'user1_id': user_id,
                'user2_id': other_user_id,
                'created_at': datetime.now()
            }
        
        return jsonify({'conversation': conversation}), 200
    
    except Exception as e:
        print(f"Get/create conversation error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MESSAGES
# ============================================================================

@messages_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """Get messages in conversation"""
    try:
        user_id = get_jwt_identity()
        
        # Verify user is part of conversation
        conversation = BaseModel.execute_query(
            "SELECT * FROM conversations WHERE id = %s",
            (conversation_id,),
            fetch_one=True
        )
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user1_id'] != user_id and conversation['user2_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        messages = BaseModel.execute_query(
            """SELECT m.*, u.first_name, u.last_name, u.email
               FROM messages m
               LEFT JOIN users u ON m.sender_id = u.id
               WHERE m.conversation_id = %s
               ORDER BY m.created_at DESC
               LIMIT %s OFFSET %s""",
            (conversation_id, limit, offset),
            fetch_all=True
        )
        
        # Mark messages as read
        BaseModel.execute_query(
            """UPDATE messages SET is_read = TRUE 
               WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE""",
            (conversation_id, user_id)
        )
        
        return jsonify({
            'messages': messages,
            'page': page,
            'limit': limit
        }), 200
    
    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations/<int:conversation_id>/send', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """Send message in conversation"""
    try:
        user_id = get_jwt_identity()
        
        # Verify user is part of conversation
        conversation = BaseModel.execute_query(
            "SELECT * FROM conversations WHERE id = %s",
            (conversation_id,),
            fetch_one=True
        )
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user1_id'] != user_id and conversation['user2_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        message_text = data.get('message', '').strip()
        attachment_url = data.get('attachment_url')
        
        if not message_text and not attachment_url:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Determine receiver
        receiver_id = conversation['user2_id'] if conversation['user1_id'] == user_id else conversation['user1_id']
        
        # Save message
        message_id = BaseModel.execute_insert(
            """INSERT INTO messages (conversation_id, sender_id, receiver_id, message, attachment_url, is_read, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (conversation_id, user_id, receiver_id, message_text, attachment_url, False, datetime.now())
        )
        
        # Update conversation
        BaseModel.execute_query(
            """UPDATE conversations SET last_message_id = %s, updated_at = %s WHERE id = %s""",
            (message_id, datetime.now(), conversation_id)
        )
        
        # Send notification
        sender = User.get_by_id(user_id)
        Notification.create(
            user_id=receiver_id,
            title=f'New Message from {sender["first_name"]}',
            message=message_text[:50] + '...' if len(message_text) > 50 else message_text,
            notification_type='message'
        )
        
        return jsonify({
            'message': 'Message sent successfully',
            'message_id': message_id
        }), 201
    
    except Exception as e:
        print(f"Send message error: {e}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/messages/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete message"""
    try:
        user_id = get_jwt_identity()
        
        message = BaseModel.execute_query(
            "SELECT * FROM messages WHERE id = %s",
            (message_id,),
            fetch_one=True
        )
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        if message['sender_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        BaseModel.execute_query(
            "DELETE FROM messages WHERE id = %s",
            (message_id,)
        )
        
        return jsonify({'message': 'Message deleted successfully'}), 200
    
    except Exception as e:
        print(f"Delete message error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MESSAGE STATUS
# ============================================================================

@messages_bp.route('/messages/<int:message_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(message_id):
    """Mark message as read"""
    try:
        user_id = get_jwt_identity()
        
        message = BaseModel.execute_query(
            "SELECT * FROM messages WHERE id = %s",
            (message_id,),
            fetch_one=True
        )
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        if message['receiver_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        BaseModel.execute_query(
            "UPDATE messages SET is_read = TRUE WHERE id = %s",
            (message_id,)
        )
        
        return jsonify({'message': 'Message marked as read'}), 200
    
    except Exception as e:
        print(f"Mark as read error: {e}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations/<int:conversation_id>/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count(conversation_id):
    """Get unread message count"""
    try:
        user_id = get_jwt_identity()
        
        count = BaseModel.execute_query(
            """SELECT COUNT(*) as unread 
               FROM messages 
               WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE""",
            (conversation_id, user_id),
            fetch_one=True
        )
        
        return jsonify({'unread_count': count['unread']}), 200
    
    except Exception as e:
        print(f"Get unread count error: {e}")
        return jsonify({'error': str(e)}), 500
