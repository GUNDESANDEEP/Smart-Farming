import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { messagingAPI } from '../../services/api';
import SellerLayout from './SellerLayout';

// Shared message storage key — used by both buyer and farmer
const SHARED_MSGS_KEY = 'sf_shared_messages';
const SHARED_CONVS_KEY = 'sf_shared_conversations';
const ACTIVITY_KEY = 'sf_user_activity';
const MSG_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

// Clean expired messages (>24h old)
const cleanExpiredMessages = () => {
  try {
    const now = Date.now();
    const msgs = JSON.parse(localStorage.getItem(SHARED_MSGS_KEY) || '[]');
    const valid = msgs.filter(m => now - new Date(m.created_at).getTime() < MSG_TTL_MS);
    if (valid.length !== msgs.length) {
      localStorage.setItem(SHARED_MSGS_KEY, JSON.stringify(valid));
    }
    const convs = JSON.parse(localStorage.getItem(SHARED_CONVS_KEY) || '[]');
    const activeConvIds = new Set(valid.map(m => m.conv_id));
    const activeConvs = convs.filter(c => activeConvIds.has(c.id) || (now - new Date(c.updated_at).getTime() < MSG_TTL_MS));
    if (activeConvs.length !== convs.length) {
      localStorage.setItem(SHARED_CONVS_KEY, JSON.stringify(activeConvs));
    }
  } catch {}
};

// Helper to get/set shared messages (for demo — works offline)
const getSharedMessages = () => {
  try { return JSON.parse(localStorage.getItem(SHARED_MSGS_KEY) || '[]'); } catch { return []; }
};
const saveSharedMessage = (msg) => {
  const msgs = getSharedMessages();
  msgs.push(msg);
  localStorage.setItem(SHARED_MSGS_KEY, JSON.stringify(msgs));
};

// Track user activity
const updateUserActivity = (userId) => {
  try {
    const activity = JSON.parse(localStorage.getItem(ACTIVITY_KEY) || '{}');
    activity[userId] = Date.now();
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify(activity));
  } catch {}
};
const isUserOnline = (userId) => {
  try {
    const activity = JSON.parse(localStorage.getItem(ACTIVITY_KEY) || '{}');
    return Date.now() - (activity[userId] || 0) < 120000; // 2 min
  } catch { return false; }
};
const getTimeRemaining = (createdAt) => {
  const remaining = MSG_TTL_MS - (Date.now() - new Date(createdAt).getTime());
  if (remaining <= 0) return null;
  const hours = Math.floor(remaining / 3600000);
  if (hours > 0) return `${hours}h`;
  const mins = Math.floor(remaining / 60000);
  return `${mins}m`;
};

const getSharedConversations = () => {
  try { return JSON.parse(localStorage.getItem(SHARED_CONVS_KEY) || '[]'); } catch { return []; }
};

export default function FarmerMessages() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [conversations, setConversations] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [activeTab, setActiveTab] = useState('chats');
  const messagesEndRef = useRef(null);
  const selectedConvRef = useRef(null);
  const isFetchingConvsRef = useRef(false);
  const isFetchingMsgsRef = useRef(false);

  // Notifications & Announcements
  const [notifications, setNotifications] = useState([
    { id: 1, type: 'order', title: 'New Order Received', body: 'Order #1042 for Fresh Tomatoes from Ravi Kumar', time: '2 min ago', read: false },
    { id: 2, type: 'system', title: 'Product Approved', body: 'Your product "Organic Rice" has been approved by admin', time: '1 hour ago', read: false },
    { id: 3, type: 'payment', title: 'Payment Released', body: '₹2,450 has been credited to your wallet', time: '3 hours ago', read: true },
    { id: 4, type: 'review', title: 'New Review', body: 'Buyer left a 5⭐ review for "Fresh Carrots"', time: '1 day ago', read: true },
  ]);

  const [announcements, setAnnouncements] = useState([
    { id: 1, title: '🎉 New Feature: AI Crop Recommendations', body: 'Get AI-powered crop suggestions based on your location and season. Try it in AI Tools!', date: 'June 20, 2026', type: 'feature' },
    { id: 2, title: '📢 Price Update: Minimum Pricing Changed', body: 'We have updated the minimum pricing guidelines for all categories. Please review your product prices.', date: 'June 18, 2026', type: 'policy' },
    { id: 3, title: '🚚 Improved Delivery Tracking', body: 'Buyers can now track orders in real-time with GPS. Ensure you update order status promptly.', date: 'June 15, 2026', type: 'feature' },
  ]);

  // Helper: time ago string
  const timeAgoStr = (ts) => {
    try {
      const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 60000);
      if (diff < 1) return 'Just now';
      if (diff < 60) return `${diff} min ago`;
      if (diff < 1440) return `${Math.floor(diff / 60)} hour${Math.floor(diff/60) > 1 ? 's' : ''} ago`;
      return `${Math.floor(diff / 1440)} day${Math.floor(diff/1440) > 1 ? 's' : ''} ago`;
    } catch { return 'Recently'; }
  };

  // Load admin notifications from localStorage
  // Load admin notifications from PostgreSQL backend
  const loadAdminNotifications = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const API_URL = process.env.REACT_APP_API_URL || 'https://smart-farming-backend.onrender.com/api';
      const res = await fetch(`${API_URL}/auth/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        const dbNotifs = (data.notifications || []).map(n => ({
          id: n.id,
          type: n.type || 'admin',
          title: '📢 Admin Notification',
          body: n.message,
          time: timeAgoStr(n.created_at || n.timestamp),
          read: n.is_read || false,
          isAdmin: true,
          timestamp: n.created_at || n.timestamp,
        }));

        // Load local ones too for backup, if any
        const stored = JSON.parse(localStorage.getItem('sf_notifications_farmers') || '[]');
        const localNotifs = stored.filter(n => !n.dismissed).map(n => ({
          id: `local_${n.id}`,
          type: 'admin',
          title: '📢 Admin Announcement',
          body: n.message,
          time: timeAgoStr(n.timestamp),
          read: n.read || false,
          isAdmin: true,
          timestamp: n.timestamp,
        }));

        setNotifications(prev => {
          const systemNotifs = prev.filter(n => !n.isAdmin);
          return [...dbNotifs, ...localNotifs, ...systemNotifs];
        });

        // Format Announcements
        const dbAnns = (data.notifications || []).map(n => ({
          id: `ann_${n.id}`,
          title: `📢 ${n.title || 'Admin Announcement'}`,
          body: n.message,
          date: new Date(n.created_at || n.timestamp).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }),
          type: 'admin',
          isAdmin: true,
        }));

        const localAnns = stored.filter(n => !n.dismissed).map(n => ({
          id: `local_ann_${n.id}`,
          title: `📢 ${n.message.substring(0, 50)}${n.message.length > 50 ? '...' : ''}`,
          body: n.message,
          date: new Date(n.timestamp).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }),
          type: 'admin',
          isAdmin: true,
        }));

        setAnnouncements(prev => {
          const systemAnns = prev.filter(a => !a.isAdmin);
          return [...dbAnns, ...localAnns, ...systemAnns];
        });
      }
    } catch (err) {
      console.error('Error loading admin notifications from API:', err);
    }
  };

  useEffect(() => {
    // Clean expired messages on mount
    cleanExpiredMessages();
    // Track farmer activity
    if (user?.id) updateUserActivity(user.id);
    const activityInterval = setInterval(() => { if (user?.id) updateUserActivity(user.id); }, 30000);

    fetchConversations();
    loadAdminNotifications();

    // ★ Fast polling (1.5s) for live feel
    const msgInterval = setInterval(() => {
      pollMessages();
      // Also refresh conversation list to pick up new incoming chats
      fetchConversations();
    }, 1500);

    // Listen for admin notification changes
    const handleStorage = (e) => {
      if (e.key === 'sf_notifications_farmers') loadAdminNotifications();
      // ★ Cross-tab instant sync for messages
      if (e.key === SHARED_MSGS_KEY && selectedConvRef.current) {
        const allMsgs = getSharedMessages().filter(m => m.conv_id === selectedConvRef.current.id);
        setMessages(prev => {
          const ids = new Set(prev.map(m => m.id));
          const newMsgs = allMsgs.filter(m => !ids.has(m.id));
          return newMsgs.length > 0 ? [...prev, ...newMsgs] : prev;
        });
      }
    };
    const handleFocus = () => loadAdminNotifications();
    const handleVis = () => { if (document.visibilityState === 'visible') loadAdminNotifications(); };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVis);
    return () => {
      clearInterval(msgInterval);
      clearInterval(activityInterval);
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVis);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep ref in sync for storage event handler
  useEffect(() => { selectedConvRef.current = selectedConv; }, [selectedConv]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    if (isFetchingConvsRef.current) return;
    isFetchingConvsRef.current = true;
    // First try API for real conversations
    try {
      const res = await messagingAPI.getConversations(1, 50);
      const data = res.data;
      const convs = data.conversations || data.data || [];
      if (convs.length > 0) { setConversations(convs); return; }
    } catch { /* fallback below */ } finally {
      isFetchingConvsRef.current = false;
    }

    // ★ KEY FIX: Match conversations by multiple criteria since buyer may use
    // demo farmer IDs (farmer_1, farmer_2) when adminAPI fails (401).
    // The real farmer's user.id won't match those demo IDs.
    const farmerId = String(user?.id || user?._id || '');
    const farmerName = (user?.name || user?.first_name || '').toLowerCase().trim();
    const now = Date.now();
    const allMsgs = getSharedMessages().filter(m => now - new Date(m.created_at).getTime() < MSG_TTL_MS);
    const sharedConvs = getSharedConversations();

    // Match conversations by: farmer_id, farmer_name, or conv_id pattern
    const farmerConvs = sharedConvs.filter(sc => {
      // Match by ID (exact)
      if (farmerId && String(sc.farmer_id) === farmerId) return true;
      if (farmerId && sc.id?.includes(`conv_${farmerId}_`)) return true;
      // Match by name (case-insensitive) — critical for demo ID fallback
      const scFarmerName = (sc.farmer_name || sc.other_user?.name || '').toLowerCase().trim();
      if (farmerName && scFarmerName && scFarmerName === farmerName) return true;
      return false;
    });

    // Also discover conversations from ALL messages (any conv with messages)
    // In a single-browser demo, just show all conversations that have messages
    const allConvIds = new Set();
    allMsgs.forEach(m => {
      if (m.conv_id && m.conv_id !== 'no_chats_yet') {
        allConvIds.add(m.conv_id);
      }
    });

    // Build conversation list
    const convMap = new Map();

    // From shared conversations that match this farmer
    farmerConvs.forEach(sc => {
      const convMsgs = allMsgs.filter(m => m.conv_id === sc.id);
      const lastMsg = convMsgs.length > 0 ? convMsgs[convMsgs.length - 1] : null;
      if (convMsgs.length > 0) {
        convMap.set(sc.id, {
          id: sc.id,
          other_user: { name: sc.buyer_name || sc.other_user?.name || 'Buyer', id: sc.buyer_id || sc.other_user?.id },
          last_message: lastMsg?.content || sc.last_message || '',
          updated_at: lastMsg?.created_at || sc.updated_at || new Date().toISOString(),
          unread_count: convMsgs.filter(m => m.sender_role === 'buyer' && !m.read).length,
          isReal: true,
        });
      }
    });

    // Also check all message conv_ids against shared convs (catches name-based matches)
    allConvIds.forEach(convId => {
      if (convMap.has(convId)) return;
      // Check if this conv belongs to this farmer via shared convs
      const matchingConv = sharedConvs.find(sc => sc.id === convId);
      if (matchingConv) {
        const scFarmerName = (matchingConv.farmer_name || '').toLowerCase().trim();
        const matchesById = farmerId && String(matchingConv.farmer_id) === farmerId;
        const matchesByName = farmerName && scFarmerName === farmerName;
        if (!matchesById && !matchesByName) return; // Not for this farmer
      } else {
        // No shared conv record — check if conv_id contains farmer's id
        if (!farmerId || !String(convId).includes(`conv_${farmerId}_`)) return;
      }
      const convMsgs = allMsgs.filter(m => m.conv_id === convId);
      if (convMsgs.length === 0) return;
      const lastMsg = convMsgs[convMsgs.length - 1];
      const buyerMsg = convMsgs.find(m => m.sender_role === 'buyer');
      const buyerName = matchingConv?.buyer_name || buyerMsg?.sender_name || 'Buyer';
      const buyerId = matchingConv?.buyer_id || buyerMsg?.sender_id || String(convId).split('_').pop();
      convMap.set(convId, {
        id: convId,
        other_user: { name: buyerName, id: buyerId },
        last_message: lastMsg?.content || '',
        updated_at: lastMsg?.created_at || new Date().toISOString(),
        unread_count: convMsgs.filter(m => m.sender_role === 'buyer' && !m.read).length,
        isReal: true,
      });
    });

    const merged = Array.from(convMap.values());
    // Sort by most recent message
    merged.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

    // If no chats, show empty state
    if (merged.length === 0) {
      merged.push({
        id: 'no_chats_yet',
        other_user: { name: 'No chats yet', id: '' },
        last_message: 'Buyers will appear here when they message you',
        updated_at: new Date().toISOString(),
        unread_count: 0,
        isEmpty: true,
      });
    }

    setConversations(merged);
  };

  const pollMessages = () => {
    if (!selectedConvRef.current) return;
    fetchMessages(selectedConvRef.current.id);
  };

  const fetchMessages = async (convId) => {
    if (isFetchingMsgsRef.current) return;
    isFetchingMsgsRef.current = true;
    // Try API first
    try {
      const res = await messagingAPI.getMessages(convId, 1, 100);
      const data = res.data;
      const apiMsgs = data.messages || data.data || [];
      if (apiMsgs.length > 0) {
        // Reverse array since backend returns DESC order
        const sorted = [...apiMsgs].reverse();
        setMessages(sorted);
        return;
      }
    } catch { /* fallback below */ } finally {
      isFetchingMsgsRef.current = false;
    }

    // Load real messages from shared localStorage (no fake samples)
    const now = Date.now();
    const sharedMsgs = getSharedMessages().filter(m => m.conv_id === convId && (now - new Date(m.created_at).getTime() < MSG_TTL_MS));
    sharedMsgs.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    setMessages(sharedMsgs);
  };

  const handleSelectConv = (conv) => {
    setSelectedConv(conv);
    fetchMessages(conv.id);
    // Mark as read
    setConversations(prev => prev.map(c => c.id === conv.id ? { ...c, unread_count: 0 } : c));
  };

  const handleSend = async () => {
    if (!newMessage.trim() || !selectedConv) return;
    setSending(true);
    const msg = {
      id: `farmer_msg_${Date.now()}`,
      content: newMessage,
      sender_id: user?.id,
      sender_role: 'farmer',
      sender_name: user?.name || 'Farmer',
      created_at: new Date().toISOString(),
      conv_id: selectedConv.id,
    };

    // Save to localStorage for cross-role sync
    saveSharedMessage(msg);

    // Also try API
    try { await messagingAPI.sendMessage(selectedConv.id, newMessage); } catch { /* silent */ }

    setMessages(prev => [...prev, msg]);
    setNewMessage('');

    // Update conversation preview
    setConversations(prev => prev.map(c => c.id === selectedConv.id ? { ...c, last_message: newMessage, updated_at: new Date().toISOString() } : c));
    setSending(false);
  };

  const getInitials = (name) => (name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

  return (
    <SellerLayout title="Messages" subtitle="Chat with buyers & view notifications">
      {/* Tabs */}
      <div className="seller-tabs-pill" style={{ marginBottom: 20 }}>
        {[
          { key: 'chats', label: `💬 Buyer Chats (${conversations.filter(c => !c.isEmpty).length})` },
          { key: 'notifications', label: `🔔 Notifications (${notifications.filter(n => !n.read).length})` },
          { key: 'announcements', label: '📢 Announcements' },
        ].map(t => (
          <button key={t.key} className={`seller-tab-pill ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Chat Tab */}
      {activeTab === 'chats' && (
        <div className="seller-chat-container">
          {/* Conversations list */}
          <div className="seller-chat-list">
            <div className="seller-chat-list-header">💬 Buyer Conversations ({conversations.filter(c => !c.isEmpty).length})</div>
            {conversations.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#9ca3af', fontSize: '0.82rem' }}>No buyers registered yet</div>
            ) : (
              conversations.map(conv => (
                <div
                  key={conv.id}
                  className={`seller-chat-item ${selectedConv?.id === conv.id ? 'active' : ''}`}
                  onClick={() => !conv.isEmpty && handleSelectConv(conv)}
                  style={{ opacity: conv.isEmpty ? 0.5 : 1, cursor: conv.isEmpty ? 'default' : 'pointer' }}
                >
                  <div className="seller-chat-avatar">
                    {getInitials(conv.other_user?.name || conv.other_user?.first_name)}
                  </div>
                  <div className="seller-chat-preview">
                    <h4>{conv.other_user?.name || conv.other_user?.first_name || 'Buyer'}</h4>
                    <p>{conv.last_message || 'No messages yet'}</p>
                  </div>
                  {conv.unread_count > 0 && (
                    <span style={{ background: '#22c55e', color: '#fff', fontSize: '0.6rem', fontWeight: 700, padding: '2px 7px', borderRadius: 10, minWidth: 18, textAlign: 'center' }}>
                      {conv.unread_count}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Chat area */}
          <div className="seller-chat-main">
            {selectedConv ? (
              <>
                <div className="seller-chat-main-header">
                  <div className="seller-chat-avatar" style={{ width: 36, height: 36 }}>
                    {getInitials(selectedConv.other_user?.name || selectedConv.other_user?.first_name)}
                  </div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>
                      {selectedConv.other_user?.name || selectedConv.other_user?.first_name || 'Buyer'}
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.68rem', color: isUserOnline(selectedConv.other_user?.id) ? '#22c55e' : '#9ca3af' }}>
                      {isUserOnline(selectedConv.other_user?.id) ? '● Online' : '○ Offline'}
                    </p>
                  </div>
                </div>

                <div className="seller-messages-area">
                  {messages.map(msg => (
                    <div key={msg.id} className={`seller-message ${String(msg.sender_id) === String(user?.id) || msg.sender_role === 'farmer' ? 'sent' : 'received'}`}>
                      {msg.content}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                        <span className="msg-time">
                          {new Date(msg.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        {getTimeRemaining(msg.created_at) && (
                          <span style={{ fontSize: '0.55rem', color: '#d97706', background: '#fef3c7', padding: '1px 5px', borderRadius: 4 }}>
                            ⏳ {getTimeRemaining(msg.created_at)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                <div className="seller-chat-input">
                  <input
                    value={newMessage}
                    onChange={e => setNewMessage(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSend()}
                    placeholder="Reply to buyer..."
                  />
                  <button className="seller-btn seller-btn-primary" onClick={handleSend} disabled={sending || !newMessage.trim()}>
                    {sending ? '⏳' : '📤'} Send
                  </button>
                </div>
              </>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '3rem', marginBottom: 8 }}>💬</p>
                  <p style={{ fontSize: '0.9rem', fontWeight: 500 }}>Select a conversation to start chatting</p>
                  <p style={{ fontSize: '0.75rem', marginTop: 4 }}>Buyer messages will appear here in real-time</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {notifications.map(notif => (
            <div key={notif.id} className="seller-card" style={{
              opacity: notif.read ? 0.7 : 1,
              borderLeft: notif.isAdmin ? '3px solid #f59e0b' : (notif.read ? 'none' : '3px solid #22c55e'),
              background: notif.isAdmin ? 'linear-gradient(135deg, #fffbeb, #fef9e7)' : undefined,
            }}>
              <div className="seller-card-body" style={{ display: 'flex', alignItems: 'flex-start', gap: 14, padding: '14px 18px' }}>
                <div style={{ fontSize: '1.5rem', flexShrink: 0 }}>
                  {notif.type === 'admin' ? '📢' : notif.type === 'order' ? '🛒' : notif.type === 'payment' ? '💰' : notif.type === 'review' ? '⭐' : '🔔'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <h4 style={{ margin: 0, fontSize: '0.88rem', fontWeight: 700, color: notif.isAdmin ? '#92400e' : '#14532d' }}>{notif.title}</h4>
                    {notif.isAdmin && <span style={{ fontSize: '0.6rem', fontWeight: 700, padding: '1px 6px', borderRadius: 4, background: '#fef3c7', color: '#d97706', border: '1px solid #fde68a' }}>FROM ADMIN</span>}
                  </div>
                  <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#6b7280' }}>{notif.body}</p>
                </div>
                <span style={{ fontSize: '0.68rem', color: '#9ca3af', whiteSpace: 'nowrap' }}>{notif.time}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Announcements Tab */}
      {activeTab === 'announcements' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {announcements.map(ann => (
            <div key={ann.id} className="seller-card">
              <div className="seller-card-body" style={{ padding: '18px 22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#14532d' }}>{ann.title}</h3>
                  <span className={`seller-badge ${ann.type === 'feature' ? 'seller-badge-success' : 'seller-badge-info'}`}>{ann.type}</span>
                </div>
                <p style={{ margin: '0 0 8px', fontSize: '0.85rem', color: '#4b5563', lineHeight: 1.6 }}>{ann.body}</p>
                <p style={{ margin: 0, fontSize: '0.72rem', color: '#9ca3af' }}>📅 {ann.date}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </SellerLayout>
  );
}
