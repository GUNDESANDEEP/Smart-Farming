import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut, FiArrowLeft } from 'react-icons/fi';
import useAuthStore from '../services/authStore';
import { API_BASE_URL } from '../services/api';
import '../styles/navigation.css';

const Navigation = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const [buyerNotifCount, setBuyerNotifCount] = useState(0);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [buyerNotifs, setBuyerNotifs] = useState([]);
  const notifBellRef = useRef(null);

  // Show back button on all pages after login
  const hiddenPaths = ['/', '/login', '/register'];
  const showBack = !hiddenPaths.includes(location.pathname);

  const API = API_BASE_URL;

  const loadNotifs = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API}/auth/notifications`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await res.json();
      if (data.success) {
        setBuyerNotifCount(data.unread_count);
        setBuyerNotifs(data.notifications.slice(0, 5));
      }
    } catch (err) {
      console.error('Load notifications error:', err);
    }
  };

  const readAllNotifs = async () => {
    try {
      await fetch(`${API}/auth/notifications/read-all`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      loadNotifs();
    } catch (err) {
      console.error('Read all notifications error:', err);
    }
  };

  const dismissBuyerNotif = async (id) => {
    try {
      await fetch(`${API}/auth/notifications/${id}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      loadNotifs();
    } catch (err) {
      console.error('Dismiss notification error:', err);
    }
  };

  useEffect(() => {
    if (!user) return;
    loadNotifs();
    const interval = setInterval(loadNotifs, 10000);
    
    const handleFocus = () => loadNotifs();
    window.addEventListener('focus', handleFocus);
    
    const handleClick = (e) => { 
      if (notifBellRef.current && !notifBellRef.current.contains(e.target)) {
        setShowNotifDropdown(false); 
      }
    };
    document.addEventListener('mousedown', handleClick);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('mousedown', handleClick);
    };
  }, [user]);

  const timeAgo = (ts) => { try { const d = Math.floor((Date.now() - new Date(ts).getTime()) / 60000); return d < 1 ? 'Just now' : d < 60 ? `${d}m ago` : d < 1440 ? `${Math.floor(d/60)}h ago` : `${Math.floor(d/1440)}d ago`; } catch { return ''; } };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = {
    farmer: [
      { name: 'Dashboard', path: '/farmer/dashboard' },
      { name: 'My Products', path: '/farmer/products' },
      { name: 'Orders', path: '/farmer/orders' },
      { name: 'Direct Sale', path: '/farmer/products' },
      { name: 'Earnings', path: '/farmer/earnings' },
      { name: 'Profile', path: '/farmer/dashboard' },
    ],
    buyer: [
      { name: 'Home', path: '/buyer' },
      { name: 'Shop', path: '/buyer/shop' },
      { name: '❤️ Wishlist', path: '/buyer/wishlist' },
      { name: '🛒 Cart', path: '/buyer/cart' },
      { name: '📦 Orders', path: '/buyer/orders' },
      { name: '💬 Chat', path: '/buyer/chat' },
      { name: '🔔 Alerts', path: '/buyer/notifications', hasBadge: true },
      { name: '👑 Premium', path: '/buyer/premium' },
      { name: '👤 Profile', path: '/buyer/profile' },
    ],
    admin: [
      { name: 'Dashboard', path: '/admin' },
      { name: 'SaaS', path: '/admin/saas' },
      { name: 'Users', path: '/admin/users' },
      { name: 'Products', path: '/admin/products' },
      { name: 'Orders', path: '/admin/orders' },
      { name: 'Activity', path: '/admin/activity' },
      { name: 'Receipts', path: '/admin/receipts' },
      { name: 'Revenue', path: '/admin/revenue' },
      { name: '🔔 Notifications', path: '/admin/notifications' },
    ],
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {showBack && (
            <button className="back-btn" onClick={() => navigate(-1)}>
              <FiArrowLeft size={20} />
            </button>
          )}
          <Link to="/" className="navbar-logo">
            🌾 SmartFarm
          </Link>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Buyer Notification Bell */}
          {user?.role === 'buyer' && (
            <div ref={notifBellRef} style={{ position: 'relative' }}>
              <button
                onClick={() => {
                  const nextState = !showNotifDropdown;
                  setShowNotifDropdown(nextState);
                  if (nextState) {
                    readAllNotifs();
                  }
                }}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem',
                  position: 'relative', padding: '6px 8px', borderRadius: 8,
                  color: showNotifDropdown ? '#166534' : '#4b5563',
                }}
              >
                🔔
                {buyerNotifCount > 0 && (
                  <span style={{
                    position: 'absolute', top: 2, right: 2, minWidth: 16, height: 16, borderRadius: 8,
                    background: '#ef4444', color: '#fff', fontSize: '0.55rem', fontWeight: 700,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 3px',
                  }}>{buyerNotifCount}</span>
                )}
              </button>

              {showNotifDropdown && (
                <div style={{
                  position: 'absolute', top: '100%', right: 0, width: 320, maxHeight: 400,
                  background: '#fff', borderRadius: 14, boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
                  border: '1px solid #e5e7eb', zIndex: 1000, overflow: 'hidden',
                }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(135deg, #f0fdf4, #fff)' }}>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#14532d' }}>🔔 Notifications</h4>
                    <button onClick={() => { navigate('/buyer/notifications'); setShowNotifDropdown(false); }}
                      style={{ background: 'none', border: 'none', color: '#22c55e', fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer' }}>View All</button>
                  </div>
                  <div style={{ overflowY: 'auto', maxHeight: 320 }}>
                    {buyerNotifs.length === 0 ? (
                      <div style={{ padding: '30px 20px', textAlign: 'center', color: '#9ca3af' }}>
                        <p style={{ fontSize: '2rem', marginBottom: 4 }}>🔔</p>
                        <p style={{ fontSize: '0.8rem' }}>No notifications yet</p>
                      </div>
                    ) : (
                      buyerNotifs.map(n => (
                        <div key={n.id} style={{
                          display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 16px',
                          borderBottom: '1px solid #f5f5f5', background: '#fffbeb',
                        }}>
                          <span style={{ fontSize: '1.1rem', flexShrink: 0, marginTop: 2 }}>📢</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600, color: '#92400e', lineHeight: 1.3 }}>{n.message}</p>
                            <span style={{ fontSize: '0.65rem', color: '#b45309' }}>Admin · {timeAgo(n.timestamp)}</span>
                          </div>
                          <button onClick={(e) => { e.stopPropagation(); dismissBuyerNotif(n.id); }}
                            style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '0.7rem', padding: 2, flexShrink: 0 }}>✕</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            className="hamburger"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        <div className={`nav-menu ${isOpen ? 'active' : ''}`}>
          <div className="nav-links">
            {navLinks[user?.role]?.map((link) => (
              <Link key={link.path} to={link.path} className="nav-link" style={{ position: 'relative' }}>
                {link.name}
                {link.hasBadge && buyerNotifCount > 0 && (
                  <span style={{
                    marginLeft: 4, minWidth: 16, height: 16, borderRadius: 8,
                    background: '#ef4444', color: '#fff', fontSize: '0.55rem', fontWeight: 700,
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    padding: '0 4px', verticalAlign: 'middle',
                  }}>{buyerNotifCount}</span>
                )}
              </Link>
            ))}
          </div>

          <div className="user-menu">
            <span className="user-name">{user?.name}</span>
            <button className="logout-btn" onClick={handleLogout}>
              <FiLogOut size={18} />
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
