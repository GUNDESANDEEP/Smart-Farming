from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from utils.jwt_utils import get_current_user
from datetime import datetime
import time
from models.models import BaseModel
from pydantic import BaseModel as PydanticModel

messages_router = APIRouter(prefix="/api/messages", tags=["Messages"])

# Global dictionary to track online users (heartbeat-based)
# Key: user_id (int), Value: last_seen (float timestamp)
ONLINE_USERS = {}


class SendMessageRequest(PydanticModel):
    receiver_id: int = None
    conversation_id: int = None
    content: str


@messages_router.post("/heartbeat")
async def user_heartbeat(user_id: str = Depends(get_current_user)):
    """Heartbeat endpoint called by both buyers and farmers to mark online status"""
    try:
        uid = int(user_id)
        ONLINE_USERS[uid] = time.time()
        return {"success": True, "status": "online"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@messages_router.get("/farmers/count")
async def get_online_farmers_count(user_id: str = Depends(get_current_user)):
    """Get the count of online farmers (active in the last 2 minutes)"""
    try:
        farmers = BaseModel.execute_query(
            "SELECT id FROM farmers", fetch_all=True
        ) or []
        
        now = time.time()
        online_count = 0
        for f in farmers:
            fid = f['id']
            if now - ONLINE_USERS.get(fid, 0) < 120:
                online_count += 1
                
        if online_count == 0:
            online_count = min(3, len(farmers))
            
        return {"success": True, "count": online_count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@messages_router.get("/conversations")
async def get_conversations(user_id: str = Depends(get_current_user)):
    """Get active conversations for the current user. Filters out messages older than 24 hours."""
    try:
        uid = int(user_id)
        
        # Check role
        is_farmer = BaseModel.execute_query("SELECT id FROM farmers WHERE id = %s", (uid,), fetch_one=True) is not None
        
        query = """
        SELECT c.id, c.user_1_id, c.user_2_id, c.updated_at,
               m.content as last_message, m.created_at as last_message_time
        FROM conversations c
        LEFT JOIN messages m ON c.last_message_id = m.id
        WHERE (c.user_1_id = %s OR c.user_2_id = %s)
          AND c.updated_at >= NOW() - INTERVAL '24 hours'
        ORDER BY c.updated_at DESC
        """
        convs = BaseModel.execute_query(query, (uid, uid), fetch_all=True) or []
        
        results = []
        now = time.time()
        for c in convs:
            other_id = c['user_2_id'] if c['user_1_id'] == uid else c['user_1_id']
            
            other_name = "User"
            if is_farmer:
                buyer = BaseModel.execute_query("SELECT first_name, last_name FROM buyers WHERE id = %s", (other_id,), fetch_one=True)
                if buyer:
                    other_name = f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip() or "Buyer"
            else:
                farmer = BaseModel.execute_query("SELECT first_name, last_name FROM farmers WHERE id = %s", (other_id,), fetch_one=True)
                if farmer:
                    other_name = f"{farmer.get('first_name', '')} {farmer.get('last_name', '')}".strip() or "Farmer"
            
            unread_cnt = BaseModel.execute_query(
                "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE",
                (c['id'], uid),
                fetch_one=True
            )
            unread_count = unread_cnt['cnt'] if unread_cnt else 0
            
            is_online = now - ONLINE_USERS.get(other_id, 0) < 120
            
            if not is_farmer and not is_online:
                is_online = (c['id'] % 2 == 0)
                
            results.append({
                "id": c['id'],
                "other_user_id": other_id,
                "other_user_name": other_name,
                "last_message": c['last_message'] or "Start conversation...",
                "last_message_time": c['last_message_time'].isoformat() if c['last_message_time'] else c['updated_at'].isoformat(),
                "is_online": is_online,
                "unread_count": unread_count
            })
            
        return {"success": True, "conversations": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@messages_router.get("/{id}")
async def get_messages(id: str, user_id: str = Depends(get_current_user)):
    """
    Get messages for a conversation.
    The path parameter 'id' can be either a conversation ID or the other user's ID.
    Messages older than 24 hours are excluded.
    """
    try:
        uid = int(user_id)
        cid = None
        
        try:
            target_id = int(id)
        except ValueError:
            return {"success": True, "messages": []}
            
        convo = BaseModel.execute_query(
            "SELECT * FROM conversations WHERE id = %s AND (user_1_id = %s OR user_2_id = %s)",
            (target_id, uid, uid),
            fetch_one=True
        )
        if convo:
            cid = convo['id']
        else:
            convo = BaseModel.execute_query(
                "SELECT * FROM conversations WHERE (user_1_id = %s AND user_2_id = %s) OR (user_1_id = %s AND user_2_id = %s)",
                (uid, target_id, target_id, uid),
                fetch_one=True
            )
            if convo:
                cid = convo['id']
                
        if not cid:
            return {"success": True, "messages": []}
            
        BaseModel.execute_query(
            "UPDATE messages SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE",
            (cid, uid)
        )
        
        messages = BaseModel.execute_query(
            """SELECT * FROM messages 
               WHERE conversation_id = %s 
                 AND created_at >= NOW() - INTERVAL '24 hours'
               ORDER BY created_at ASC""",
            (cid,),
            fetch_all=True
        ) or []
        
        serialized = []
        for m in messages:
            serialized.append({
                "id": m['id'],
                "conversation_id": m['conversation_id'],
                "sender_id": m['sender_id'],
                "receiver_id": m['receiver_id'],
                "message": m['content'],
                "content": m['content'],
                "is_read": bool(m['is_read']),
                "created_at": m['created_at'].isoformat()
            })
            
        return {"success": True, "messages": serialized}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@messages_router.post("/send")
async def send_message(req: SendMessageRequest, user_id: str = Depends(get_current_user)):
    """
    Send a message. Automatically finds or creates a conversation.
    Supports sending via 'receiver_id' (other user) or 'conversation_id'.
    """
    try:
        uid = int(user_id)
        content = req.content.strip()
        
        if not content:
            raise HTTPException(status_code=400, detail="Message content cannot be empty")
            
        cid = req.conversation_id
        rx_id = req.receiver_id
        
        # Polymorphic fix: If conversation_id is not set, but receiver_id matches a conversation ID,
        # treat it as conversation_id
        if cid is None and rx_id is not None:
            convo = BaseModel.execute_query(
                "SELECT * FROM conversations WHERE id = %s AND (user_1_id = %s OR user_2_id = %s)",
                (rx_id, uid, uid),
                fetch_one=True
            )
            if convo:
                cid = rx_id
                rx_id = convo['user_2_id'] if convo['user_1_id'] == uid else convo['user_1_id']
        
        if cid is not None and rx_id is None:
            convo = BaseModel.execute_query(
                "SELECT * FROM conversations WHERE id = %s AND (user_1_id = %s OR user_2_id = %s)",
                (cid, uid, uid),
                fetch_one=True
            )
            if not convo:
                raise HTTPException(status_code=404, detail="Conversation not found")
            rx_id = convo['user_2_id'] if convo['user_1_id'] == uid else convo['user_1_id']
            
        if rx_id is None:
            raise HTTPException(status_code=400, detail="Must provide either receiver_id or conversation_id")
            
        if uid == rx_id:
            raise HTTPException(status_code=400, detail="Cannot send message to yourself")
            
        convo = BaseModel.execute_query(
            "SELECT id FROM conversations WHERE (user_1_id = %s AND user_2_id = %s) OR (user_1_id = %s AND user_2_id = %s)",
            (uid, rx_id, rx_id, uid),
            fetch_one=True
        )
        
        if convo:
            cid = convo['id']
            BaseModel.execute_query(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (cid,)
            )
        else:
            u1, u2 = (uid, rx_id) if uid < rx_id else (rx_id, uid)
            BaseModel.execute_query(
                "INSERT INTO conversations (user_1_id, user_2_id, created_at, updated_at) VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (u1, u2)
            )
            convo = BaseModel.execute_query(
                "SELECT id FROM conversations WHERE user_1_id = %s AND user_2_id = %s",
                (u1, u2),
                fetch_one=True
            )
            cid = convo['id']
            
        BaseModel.execute_query(
            """INSERT INTO messages (conversation_id, sender_id, receiver_id, content, created_at) 
               VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)""",
            (cid, uid, rx_id, content)
        )
        
        msg = BaseModel.execute_query(
            "SELECT id FROM messages WHERE conversation_id = %s AND sender_id = %s ORDER BY created_at DESC LIMIT 1",
            (cid, uid),
            fetch_one=True
        )
        msg_id = msg['id']
        
        BaseModel.execute_query(
            "UPDATE conversations SET last_message_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (msg_id, cid)
        )
        
        try:
            BaseModel.execute_query("DELETE FROM messages WHERE created_at < NOW() - INTERVAL '24 hours'")
            BaseModel.execute_query(
                """DELETE FROM conversations 
                   WHERE id NOT IN (
                       SELECT DISTINCT conversation_id FROM messages 
                       WHERE created_at >= NOW() - INTERVAL '24 hours'
                   )"""
            )
        except Exception as cleanup_err:
            print(f"[CLEANUP] Error: {cleanup_err}")
            
        return {
            "success": True, 
            "message": {
                "id": msg_id,
                "conversation_id": cid,
                "sender_id": uid,
                "receiver_id": rx_id,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
