import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiArrowLeft, FiSend, FiSearch } from 'react-icons/fi';
import BuyerLayout from './BuyerLayout';

const API = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';
const getToken = () => localStorage.getItem('access_token');

export default function BuyerChat() {
  const { user } = useAuthStore();
  const location = useLocation();
  const [farmers, setFarmers] = useState([]);
  const [selectedFarmer, setSelectedFarmer] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMsg, setNewMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [farmersCount, setFarmersCount] = useState(null);
  const chatEndRef = useRef(null);
  const pollRef = useRef(null);
  const isFetchingFarmersRef = useRef(false);
  const isFetchingMsgsRef = useRef(false);

  useEffect(() => { 
    fetchFarmers(); 
    fetchFarmersCount();

    // Send heartbeat to indicate online status
    const sendHeartbeat = async () => {
      try {
        await fetch(`${API}/messages/heartbeat`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${getToken()}` },
        });
      } catch {}
    };
    sendHeartbeat();
    const heartbeatInterval = setInterval(sendHeartbeat, 30000);

    const listInterval = setInterval(() => {
      fetchFarmers();
      fetchFarmersCount();
    }, 3000);
    return () => {
      clearInterval(listInterval);
      clearInterval(heartbeatInterval);
      clearInterval(pollRef.current);
    };
  }, []);

  useEffect(() => {
    if (location.state?.farmer && farmers.length >= 0 && !loading) {
      const targetFarmer = location.state.farmer;
      const found = farmers.find(f => (f.other_user_id || f.id) === targetFarmer.id);
      if (found) {
        setSelectedFarmer(found);
      } else {
        const newConvo = {
          id: targetFarmer.id,
          other_user_id: targetFarmer.id,
          other_user_name: targetFarmer.name,
          last_message: 'Start conversation...',
          is_new: true
        };
        setFarmers(prev => {
          if (prev.some(f => (f.other_user_id || f.id) === targetFarmer.id)) return prev;
          return [newConvo, ...prev];
        });
        setSelectedFarmer(newConvo);
      }
    }
  }, [location.state, farmers, loading]);

  const fetchFarmersCount = async () => {
    try {
      const res = await fetch(`${API}/messages/farmers/count`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await res.json();
      setFarmersCount(data.count);
    } catch (err) {
      console.error('Fetch farmers count error:', err);
    }
  };

  useEffect(() => {
    if (selectedFarmer) {
      const targetId = selectedFarmer.other_user_id || selectedFarmer.id;
      fetchMessages(targetId);
      clearInterval(pollRef.current);
      pollRef.current = setInterval(() => fetchMessages(targetId), 3000);
    }
    return () => clearInterval(pollRef.current);
  }, [selectedFarmer]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchFarmers = async () => {
    if (isFetchingFarmersRef.current) return;
    isFetchingFarmersRef.current = true;
    try {
      const res = await fetch(`${API}/messages/conversations`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await res.json();
      const convos = data.conversations || data.data || [];
      setFarmers(convos);
    } catch (err) {
      console.error('Fetch farmers error:', err);
    } finally {
      setLoading(false);
      isFetchingFarmersRef.current = false;
    }
  };

  const fetchMessages = async (farmerId) => {
    if (isFetchingMsgsRef.current) return;
    isFetchingMsgsRef.current = true;
    try {
      const res = await fetch(`${API}/messages/${farmerId}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await res.json();
      setMessages(data.messages || data.data || []);
    } catch {} finally {
      isFetchingMsgsRef.current = false;
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMsg.trim() || !selectedFarmer) return;
    const msgText = newMsg.trim();
    setNewMsg('');

    const optimisticMsg = {
      id: `temp_${Date.now()}`,
      sender_id: user?.id,
      receiver_id: selectedFarmer.other_user_id || selectedFarmer.id,
      message: msgText,
      created_at: new Date().toISOString(),
      is_read: false
    };

    // Optimistically update the message list
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const receiverId = selectedFarmer.other_user_id || selectedFarmer.id;
      await fetch(`${API}/messages/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ receiver_id: receiverId, content: msgText }),
      });
      fetchMessages(receiverId);
    } catch {
      toast.error('Failed to send message');
      // Rollback optimistic message on failure
      setMessages(prev => prev.filter(m => m.id !== optimisticMsg.id));
    }
  };

  const filtered = farmers.filter(f => {
    const name = f.other_user_name || f.name || '';
    return name.toLowerCase().includes(search.toLowerCase());
  });

  const buyerId = user?.id || user?.user_id;

  return (
    <BuyerLayout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link to="/buyer/dashboard" style={S.backBtn}><FiArrowLeft size={18} /> Back</Link>
          <h2 style={S.pageTitle}>💬 Chat with Farmers</h2>
        </div>
        <span style={{
          background: '#eff6ff',
          color: '#2563eb',
          padding: '6px 12px',
          borderRadius: 20,
          fontSize: '0.78rem',
          fontWeight: 700,
          border: '1px solid #bfdbfe'
        }}>
          👨‍🌾 {farmersCount !== null ? `${farmersCount} Farmers Available` : 'Loading farmers...'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, height: 'calc(100vh - 180px)', minHeight: 400 }}>
        {/* Farmer List */}
        <div className="buyer-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ position: 'relative' }}>
              <FiSearch style={{ position: 'absolute', left: 10, top: 10, color: '#94a3b8' }} size={14} />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search farmers..." style={{ width: '100%', padding: '8px 12px 8px 32px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: '0.8rem', outline: 'none', boxSizing: 'border-box' }} />
            </div>
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loading ? <p style={{ padding: 16, color: '#94a3b8', fontSize: '0.8rem' }}>Loading...</p> :
              filtered.length === 0 ? <p style={{ padding: 16, color: '#94a3b8', fontSize: '0.8rem' }}>No farmers found</p> :
              filtered.map((f, i) => {
                const fId = f.other_user_id || f.id;
                const isSelected = selectedFarmer && (selectedFarmer.other_user_id || selectedFarmer.id) === fId;
                return (
                  <div key={i} onClick={() => setSelectedFarmer(f)} style={{
                    padding: '12px 14px', cursor: 'pointer', borderBottom: '1px solid #f8fafc',
                    background: isSelected ? '#eff6ff' : '#fff', transition: 'background 0.2s',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #16a34a, #22d3ee)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: '0.8rem', flexShrink: 0 }}>
                        {(f.other_user_name || f.name || 'F')[0].toUpperCase()}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600, color: '#1e293b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.other_user_name || f.name || 'Farmer'}</p>
                        <p style={{ margin: 0, fontSize: '0.68rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.last_message || 'Start chatting...'}</p>
                      </div>
                    </div>
                  </div>
                );
              })
            }
          </div>
        </div>

        {/* Chat Area */}
        <div className="buyer-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {!selectedFarmer ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', color: '#94a3b8' }}>
              <span style={{ fontSize: '3rem', opacity: 0.4 }}>💬</span>
              <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>Select a farmer to start chatting</p>
              <p style={{ fontSize: '0.75rem' }}>Messages update in real-time every 3 seconds</p>
            </div>
          ) : (
            <>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', gap: 10, background: '#f8fafc' }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #16a34a, #22d3ee)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: '0.75rem' }}>
                  {(selectedFarmer.other_user_name || selectedFarmer.name || 'F')[0].toUpperCase()}
                </div>
                <div>
                  <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: '#1e293b' }}>{selectedFarmer.other_user_name || selectedFarmer.name}</p>
                  <p style={{ margin: 0, fontSize: '0.65rem', color: '#16a34a' }}>● Online • Real-time</p>
                </div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 8, background: '#fafbfc' }}>
                {messages.length === 0 && <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem', marginTop: 40 }}>No messages yet. Say hello! 👋</p>}
                {messages.map((msg, i) => {
                  const isMine = String(msg.sender_id) === String(buyerId) || msg.is_mine;
                  return (
                    <div key={i} style={{ display: 'flex', justifyContent: isMine ? 'flex-end' : 'flex-start' }}>
                      <div style={{
                        maxWidth: '70%', padding: '10px 14px', borderRadius: isMine ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                        background: isMine ? 'linear-gradient(135deg, #2563eb, #1d4ed8)' : '#fff',
                        color: isMine ? '#fff' : '#1e293b', fontSize: '0.82rem', lineHeight: 1.5,
                        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
                      }}>
                        {msg.content || msg.message}
                        <p style={{ margin: '4px 0 0', fontSize: '0.6rem', opacity: 0.7, textAlign: 'right' }}>
                          {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </p>
                      </div>
                    </div>
                  );
                })}
                <div ref={chatEndRef} />
              </div>

              <form onSubmit={sendMessage} style={{ padding: '10px 14px', borderTop: '1px solid #f1f5f9', display: 'flex', gap: 8 }}>
                <input value={newMsg} onChange={e => setNewMsg(e.target.value)} placeholder="Type a message..." style={{ flex: 1, padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: 10, fontSize: '0.85rem', outline: 'none' }} />
                <button type="submit" style={{ padding: '10px 18px', background: 'linear-gradient(135deg, #2563eb, #1d4ed8)', border: 'none', borderRadius: 10, color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <FiSend size={16} />
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </BuyerLayout>
  );
}

const S = {
  backBtn: { display: 'flex', alignItems: 'center', gap: 6, background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10, padding: '8px 16px', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none', touchAction: 'manipulation' },
  pageTitle: { fontSize: '1.3rem', fontWeight: 800, color: '#1e293b', margin: 0 },
};
