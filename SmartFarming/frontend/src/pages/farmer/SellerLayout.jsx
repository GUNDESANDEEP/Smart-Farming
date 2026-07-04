import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import '../../styles/seller.css';

const NAV_SECTIONS = [
  {
    title: 'Main',
    items: [
      { key: 'dashboard', path: '/farmer/dashboard', icon: '📊', label: 'Dashboard' },
      { key: 'products', path: '/farmer/products', icon: '📦', label: 'Products' },
      { key: 'orders', path: '/farmer/orders', icon: '🛒', label: 'Orders' },
      { key: 'incoming-orders', path: '/farmer/incoming-orders', icon: '🔔', label: 'Incoming Orders' },
    ],
  },
  {
    title: 'Communication',
    items: [
      { key: 'messages', path: '/farmer/messages', icon: '💬', label: 'Messages' },
    ],
  },
  {
    title: 'Business',
    items: [
      { key: 'analytics', path: '/farmer/analytics', icon: '📈', label: 'Analytics' },
      { key: 'earnings', path: '/farmer/earnings', icon: '💰', label: 'Earnings' },
      { key: 'wallet', path: '/farmer/wallet', icon: '🏦', label: 'Wallet' },
      { key: 'direct-payment', path: '/farmer/direct-payment', icon: '💳', label: 'Direct Payment' },
      { key: 'marketing', path: '/farmer/marketing', icon: '📢', label: 'Marketing' },
    ],
  },
  {
    title: 'AI & Smart Tools',
    items: [
      { key: 'ai-tools', path: '/farmer/ai-tools', icon: '🤖', label: 'AI Tools' },
      { key: 'future-ai', path: '/farmer/future-ai', icon: '🔮', label: 'Future AI' },
      { key: 'agribot', path: '/farmer/agribot', icon: '🌱', label: 'AgriBot Chat' },
    ],
  },
];

// Sample notifications for farmers
const SAMPLE_NOTIFICATIONS = [
  { id: 1, type: 'order', icon: '🛒', title: 'New Order Received', text: 'Buyer placed order for 5kg Tomatoes', time: '2 min ago', unread: true },
  { id: 2, type: 'message', icon: '💬', title: 'New Message', text: 'Buyer asked about organic certification', time: '15 min ago', unread: true },
  { id: 3, type: 'payment', icon: '💰', title: 'Payment Received', text: '₹2,450 credited to your wallet', time: '1 hour ago', unread: false },
  { id: 4, type: 'alert', icon: '⚠️', title: 'Low Stock Alert', text: 'Potatoes stock below 10 kg', time: '3 hours ago', unread: false },
  { id: 5, type: 'order', icon: '📦', title: 'Order Delivered', text: 'Order #1042 marked as delivered', time: '5 hours ago', unread: false },
];

export default function SellerLayout({ children, title, subtitle }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [notifPanelOpen, setNotifPanelOpen] = useState(false);
  const [notifications, setNotifications] = useState(SAMPLE_NOTIFICATIONS);
  const profileRef = useRef(null);
  const notifRef = useRef(null);

  // Load admin notifications from PostgreSQL backend and merge with sample
  const loadAdminNotifs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const API_URL = process.env.REACT_APP_API_URL || 'https://smart-farming-backend.onrender.com/api';
      const res = await fetch(`${API_URL}/auth/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        const dbNotifs = (data.notifications || []).map(n => {
          const diff = Math.floor((Date.now() - new Date(n.created_at || n.timestamp).getTime()) / 60000);
          const timeStr = diff < 1 ? 'Just now' : diff < 60 ? `${diff} min ago` : diff < 1440 ? `${Math.floor(diff/60)}h ago` : `${Math.floor(diff/1440)}d ago`;
          return {
            id: n.id,
            type: n.type || 'admin',
            icon: '📢',
            title: n.title || 'Admin Notification',
            text: n.message,
            time: timeStr,
            unread: !n.is_read,
            isAdmin: true,
          };
        });

        // Load local ones too for backup, if any
        const stored = JSON.parse(localStorage.getItem('sf_notifications_farmers') || '[]');
        const localNotifs = stored.filter(n => !n.dismissed).map(n => {
          const diff = Math.floor((Date.now() - new Date(n.timestamp).getTime()) / 60000);
          const timeStr = diff < 1 ? 'Just now' : diff < 60 ? `${diff} min ago` : diff < 1440 ? `${Math.floor(diff/60)}h ago` : `${Math.floor(diff/1440)}d ago`;
          return {
            id: `local_${n.id}`,
            type: 'admin',
            icon: '📢',
            title: 'Admin Announcement',
            text: n.message,
            time: timeStr,
            unread: !n.read,
            isAdmin: true,
          };
        });

        setNotifications(prev => {
          const systemNotifs = prev.filter(n => !n.isAdmin);
          return [...dbNotifs, ...localNotifs, ...systemNotifs];
        });
      }
    } catch (err) {
      console.error('Error loading admin notifications from API:', err);
    }
  };

  // Close menus on outside click + load admin notifs
  useEffect(() => {
    const handleClick = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifPanelOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);

    // Load admin notifications
    loadAdminNotifs();
    const handleStorage = (e) => { if (e.key === 'sf_notifications_farmers') loadAdminNotifs(); };
    const handleFocus = () => loadAdminNotifs();
    const handleVis = () => { if (document.visibilityState === 'visible') loadAdminNotifs(); };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVis);

    return () => {
      document.removeEventListener('mousedown', handleClick);
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVis);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleNav = (path) => {
    navigate(path);
    setSidebarOpen(false);
    setProfileMenuOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  const displayName = user?.name || user?.first_name || 'Farmer';
  const nameParts = displayName.split(' ');
  const userInitials = `${(nameParts[0] || 'F')[0]}${(nameParts[1] || '')[0] || ''}`.toUpperCase();
  const unreadCount = notifications.filter(n => n.unread).length;

  const markAllRead = async () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      const API_URL = process.env.REACT_APP_API_URL || 'https://smart-farming-backend.onrender.com/api';
      await fetch(`${API_URL}/auth/notifications/read-all`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (err) {
      console.error('Error marking all notifications read:', err);
    }
  };

  const profileMenuItems = [
    { icon: '📊', label: 'Dashboard', path: '/farmer/dashboard' },
    { icon: '📦', label: 'My Products', path: '/farmer/products' },
    { icon: '🛒', label: 'Orders', path: '/farmer/orders' },
    { icon: '💰', label: 'Earnings', path: '/farmer/earnings' },
    { icon: '📈', label: 'Analytics', path: '/farmer/analytics' },
    { icon: '💬', label: 'Messages', path: '/farmer/messages' },
  ];

  return (
    <div className="seller-layout">
      {/* Mobile overlay */}
      <div
        className={`seller-sidebar-overlay ${sidebarOpen ? 'show' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`seller-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="seller-sidebar-brand">
          <div className="brand-icon">🌾</div>
          <div>
            <h2>SmartFarmer</h2>
            <span>Seller Dashboard</span>
          </div>
        </div>

        <div className="seller-sidebar-user">
          <div className="user-avatar">{userInitials}</div>
          <div className="user-info">
            <div className="user-name">{displayName}</div>
            <div className="user-role">Verified Farmer</div>
          </div>
        </div>

        <nav className="seller-nav">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title} className="seller-nav-section">
              <div className="seller-nav-section-title">{section.title}</div>
              {section.items.map((item) => (
                <button
                  key={item.key}
                  className={`seller-nav-item ${isActive(item.path) ? 'active' : ''}`}
                  onClick={() => handleNav(item.path)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                  {item.key === 'orders' && (
                    <span className="nav-badge" style={{ display: 'none' }} id="seller-order-badge" />
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="seller-sidebar-footer">
          <button className="seller-logout-btn" onClick={handleLogout}>
            <span className="nav-icon">🚪</span>
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="seller-main">
        <div className="seller-topbar">
          <div className="seller-topbar-left">
            <button className="seller-menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <div>
              <h1>{title || 'Dashboard'}</h1>
              {subtitle && <p>{subtitle}</p>}
            </div>
          </div>

          {/* ═══ TOP-RIGHT MENU ═══ */}
          <div className="seller-topbar-right">
            {/* Messages Quick Button */}
            <button
              className="seller-topbar-btn"
              onClick={() => navigate('/farmer/messages')}
              title="Messages"
            >
              💬
            </button>

            {/* Notifications Bell */}
            <div ref={notifRef} style={{ position: 'relative' }}>
              <button
                className="seller-topbar-btn"
                onClick={() => { setNotifPanelOpen(!notifPanelOpen); setProfileMenuOpen(false); }}
                title="Notifications"
              >
                🔔
                {unreadCount > 0 && (
                  <span className="badge-count">{unreadCount}</span>
                )}
              </button>

              {/* Notification Panel Dropdown */}
              {notifPanelOpen && (
                <div className="seller-notif-panel">
                  <div className="seller-notif-panel-header">
                    <h3>🔔 Notifications</h3>
                    <button onClick={markAllRead}>Mark all read</button>
                  </div>
                  <div className="seller-notif-list">
                    {notifications.length > 0 ? notifications.map(n => (
                      <div
                        key={n.id}
                        className={`seller-notif-item ${n.unread ? 'unread' : ''}`}
                        onClick={async () => {
                          setNotifications(prev => prev.map(x => x.id === n.id ? { ...x, unread: false } : x));
                          if (n.type === 'order') navigate('/farmer/orders');
                          if (n.type === 'message') navigate('/farmer/messages');
                          if (n.type === 'payment') navigate('/farmer/earnings');
                          if (n.type === 'admin') navigate('/farmer/messages');
                          setNotifPanelOpen(false);

                          // If it is a database-backed notification (represented by numeric id)
                          if (typeof n.id === 'number') {
                            try {
                              const token = localStorage.getItem('access_token');
                              if (token) {
                                const API_URL = process.env.REACT_APP_API_URL || 'https://smart-farming-backend.onrender.com/api';
                                await fetch(`${API_URL}/auth/notifications/${n.id}/read`, {
                                  method: 'POST',
                                  headers: { Authorization: `Bearer ${token}` }
                                });
                              }
                            } catch (e) {
                              console.error('Error marking single notification read:', e);
                            }
                          }
                        }}
                      >
                      <div className={`notif-icon ${n.type}`}>{n.icon}</div>
                        <div className="notif-content">
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <p className="notif-title">{n.title}</p>
                            {n.isAdmin && <span style={{ fontSize: '0.5rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4, background: '#fef3c7', color: '#d97706', border: '1px solid #fde68a', whiteSpace: 'nowrap' }}>ADMIN</span>}
                          </div>
                          <p className="notif-text">{n.text}</p>
                          <span className="notif-time">{n.time}</span>
                        </div>
                      </div>
                    )) : (
                      <div className="seller-notif-empty">
                        <div className="empty-bell">🔔</div>
                        <p>No notifications yet</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Profile Dropdown */}
            <div ref={profileRef} style={{ position: 'relative' }}>
              <button
                className={`seller-profile-trigger ${profileMenuOpen ? 'open' : ''}`}
                onClick={() => { setProfileMenuOpen(!profileMenuOpen); setNotifPanelOpen(false); }}
              >
                <div className="profile-avatar">{userInitials}</div>
                <div className="profile-info">
                  <span className="profile-name">{displayName}</span>
                  <span className="profile-role">Farmer</span>
                </div>
                <span className="profile-chevron">▼</span>
              </button>

              {/* Profile Menu Dropdown */}
              {profileMenuOpen && (
                <div className="seller-dropdown">
                  <div className="seller-dropdown-header">
                    <h4>{displayName}</h4>
                    <p>{user?.email || 'Verified Farmer'}</p>
                  </div>

                  {profileMenuItems.map(item => (
                    <button
                      key={item.path}
                      className="seller-dropdown-item"
                      onClick={() => handleNav(item.path)}
                    >
                      <span className="item-icon">{item.icon}</span>
                      {item.label}
                    </button>
                  ))}

                  <div className="seller-dropdown-divider" />

                  <button className="seller-dropdown-item" onClick={() => handleNav('/farmer/ai-tools')}>
                    <span className="item-icon">🤖</span>
                    AI Tools
                  </button>

                  <button className="seller-dropdown-item" onClick={() => handleNav('/farmer/marketing')}>
                    <span className="item-icon">📢</span>
                    Marketing
                  </button>

                  <div className="seller-dropdown-divider" />

                  <button className="seller-dropdown-item danger" onClick={handleLogout}>
                    <span className="item-icon">🚪</span>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="seller-content">
          {children}
        </div>
      </main>
    </div>
  );
}
