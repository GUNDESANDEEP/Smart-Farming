import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { farmerAPI, weatherAPI } from '../../services/api';
import toast from 'react-hot-toast';
import SellerLayout from './SellerLayout';
import PremiumWeatherWidget from '../../components/PremiumWeatherWidget';

// Cache key for localStorage
const CACHE_KEY = 'sf_farmer_dashboard';
const CACHE_TTL = 300000; // 5 minutes

// Load cached data instantly (synchronous, no network)
const loadCachedDashboard = () => {
  try {
    const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
    if (cached && (Date.now() - cached.ts) < CACHE_TTL) {
      return cached;
    }
  } catch {}
  return null;
};

export default function FarmerDashboard() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // Initialize from cache immediately — no loading state needed
  const cached = useRef(loadCachedDashboard());
  const [stats, setStats] = useState(cached.current?.stats || { products: 0, orders: 0, pendingOrders: 0, activeOrders: 0, deliveredOrders: 0, earnings: 0, thisMonth: 0, pending: 0, rating: 0 });
  const [recentOrders, setRecentOrders] = useState(cached.current?.recentOrders || []);
  const [topProducts, setTopProducts] = useState(cached.current?.topProducts || []);
  const [weather, setWeather] = useState(cached.current?.weather || null);
  const [activityFeed, setActivityFeed] = useState(cached.current?.activityFeed || []);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Fetch fresh data in background (non-blocking, UI already has cached data)
    fetchAll();
    loadNotifications();
    const handleFocus = () => loadNotifications();
    const handleVisibility = () => { if (document.visibilityState === 'visible') loadNotifications(); };
    const handleStorage = (e) => { if (e.key === 'sf_notifications_farmers') loadNotifications(); };
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('storage', handleStorage);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadNotifications = () => {
    try {
      const notifs = JSON.parse(localStorage.getItem('sf_notifications_farmers') || '[]');
      setNotifications(notifs.filter(n => !n.dismissed));
    } catch { setNotifications([]); }
  };

  const dismissNotification = (id) => {
    try {
      const notifs = JSON.parse(localStorage.getItem('sf_notifications_farmers') || '[]');
      const updated = notifs.map(n => n.id === id ? { ...n, dismissed: true } : n);
      localStorage.setItem('sf_notifications_farmers', JSON.stringify(updated));
      setNotifications(updated.filter(n => !n.dismissed));
    } catch {}
  };

  const fetchAll = async () => {
    let prods = [], ordersArr = [], earnings = {};

    // Fetch all data in parallel for speed
    const [productsRes, ordersRes, earningsRes] = await Promise.allSettled([
      farmerAPI.getProducts(1, 100),
      farmerAPI.getOrders(1, 100),
      farmerAPI.getEarnings(),
    ]);

    if (productsRes.status === 'fulfilled') {
      const prodData = productsRes.value.data;
      prods = Array.isArray(prodData) ? prodData : (prodData.products || prodData.data || []);
    }
    if (ordersRes.status === 'fulfilled') {
      const ordersList = ordersRes.value.data?.orders || ordersRes.value.data?.data || ordersRes.value.data || [];
      ordersArr = Array.isArray(ordersList) ? ordersList : [];
    }
    if (earningsRes.status === 'fulfilled') {
      earnings = earningsRes.value.data || {};
    }

    const newStats = {
      products: prods.length,
      orders: ordersArr.length,
      pendingOrders: ordersArr.filter(o => o.status === 'pending').length,
      activeOrders: ordersArr.filter(o => ['confirmed','processing','packed','dispatched','in_transit','out_for_delivery'].includes(o.status)).length,
      deliveredOrders: ordersArr.filter(o => o.status === 'delivered').length,
      earnings: earnings.total || 0,
      thisMonth: earnings.thisMonth || 0,
      pending: earnings.pending || 0,
      rating: earnings.rating || 0,
    };
    setStats(newStats);

    const newRecentOrders = ordersArr.slice(0, 5);
    const newTopProducts = prods.slice(0, 5);
    setRecentOrders(newRecentOrders);
    setTopProducts(newTopProducts);

    // Build activity feed from orders
    const activities = ordersArr.slice(0, 6).map(o => ({
      id: o.id || o._id,
      text: o.status === 'pending' ? `New order <strong>#${o.id || o._id}</strong> for ${o.product_name || 'a product'}`
           : o.status === 'delivered' ? `Order <strong>#${o.id || o._id}</strong> delivered successfully`
           : `Order <strong>#${o.id || o._id}</strong> is ${o.status}`,
      time: o.created_at ? new Date(o.created_at).toLocaleDateString() : 'Recently',
      color: o.status === 'pending' ? 'amber' : o.status === 'delivered' ? 'green' : 'blue',
    }));
    if (activities.length === 0) {
      activities.push(
        { id: 'w1', text: 'Welcome to <strong>SmartFarmer</strong>! Start by adding products.', time: 'Just now', color: 'green' },
        { id: 'w2', text: 'Set up your <strong>profile</strong> to attract more buyers.', time: 'Tip', color: 'blue' },
        { id: 'w3', text: 'Use <strong>AI Tools</strong> to optimize your pricing.', time: 'Tip', color: 'purple' },
      );
    }
    setActivityFeed(activities);

    // Weather
    let newWeather = null;
    try {
      const wRes = await weatherAPI.getWeather(user?.location || 'Hyderabad');
      const data = wRes.data;
      if (data && data.weather) {
        newWeather = {
          temperature: data.weather.temp,
          description: data.weather.description,
          humidity: data.weather.humidity,
          icon: data.weather.icon ? `https://openweathermap.org/img/wn/${data.weather.icon}@2x.png` : null
        };
      } else {
        newWeather = data;
      }
      setWeather(newWeather);
    } catch { /* silent */ }

    // Save to localStorage cache for instant load next time
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        ts: Date.now(),
        stats: newStats,
        recentOrders: newRecentOrders,
        topProducts: newTopProducts,
        weather: newWeather,
        activityFeed: activities,
      }));
    } catch {} // localStorage full — ignore
  };

  const statCards = [
    { label: 'Total Products', value: stats.products, icon: '📦', color: 'green', change: '+3 this week', up: true },
    { label: 'New Orders', value: stats.pendingOrders, icon: '🔔', color: 'amber', change: 'Needs action', up: true },
    { label: 'Active Orders', value: stats.activeOrders, icon: '⚙️', color: 'blue', change: 'In progress', up: true },
    { label: 'Delivered', value: stats.deliveredOrders, icon: '✅', color: 'teal', change: 'Completed', up: true },
    { label: 'Total Earnings', value: `₹${Number(stats.earnings).toLocaleString('en-IN')}`, icon: '💰', color: 'green', change: '+12% vs last month', up: true },
    { label: 'This Month', value: `₹${Number(stats.thisMonth).toLocaleString('en-IN')}`, icon: '📅', color: 'purple', change: 'Current period', up: true },
  ];

  const getStatusBadge = (status) => {
    const map = {
      pending: { cls: 'seller-badge-warning', label: '⏳ Pending' },
      confirmed: { cls: 'seller-badge-info', label: '✅ Confirmed' },
      processing: { cls: 'seller-badge-purple', label: '⚙️ Processing' },
      packed: { cls: 'seller-badge-info', label: '📦 Packed' },
      dispatched: { cls: 'seller-badge-info', label: '🚚 Dispatched' },
      delivered: { cls: 'seller-badge-success', label: '🎉 Delivered' },
      cancelled: { cls: 'seller-badge-danger', label: '❌ Cancelled' },
    };
    const info = map[status] || { cls: 'seller-badge-info', label: status };
    return <span className={`seller-badge ${info.cls}`}>{info.label}</span>;
  };

  const displayName = user?.name || user?.first_name || 'Farmer';
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? 'Good Morning' : currentHour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <SellerLayout title="Dashboard" subtitle={`${greeting}, ${displayName}! 👋`}>
      {/* ═══ HERO WELCOME SECTION ═══ */}
      <div className="seller-hero">
        <div className="seller-hero-content">
          <div>
            <h2>🌾 {greeting}, {displayName}!</h2>
            <p>Here's what's happening with your farm today</p>
          </div>
          <div className="seller-hero-stats">
            <div className="seller-hero-stat">
              <h3>{stats.products}</h3>
              <span>Products</span>
            </div>
            <div className="seller-hero-stat">
              <h3>{stats.orders}</h3>
              <span>Total Orders</span>
            </div>
            <div className="seller-hero-stat">
              <h3>₹{Number(stats.earnings).toLocaleString('en-IN')}</h3>
              <span>Revenue</span>
            </div>
            <div className="seller-hero-stat">
              <h3>{stats.rating ? Number(stats.rating).toFixed(1) : '4.5'}</h3>
              <span>Rating ⭐</span>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Notifications Banner */}
      {notifications.length > 0 && (
        <div style={{ marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {notifications.slice(0, 5).map(n => (
            <div key={n.id} style={{
              display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
              background: 'linear-gradient(135deg, #fffbeb, #fef3c7)', borderRadius: 12,
              border: '1px solid #fde68a', animation: 'sellerGlow 3s infinite',
            }}>
              <span style={{ fontSize: '1.3rem', flexShrink: 0 }}>📢</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: '0.88rem', color: '#92400e', fontWeight: 600, lineHeight: 1.4 }}>{n.message}</p>
                <span style={{ fontSize: '0.68rem', color: '#b45309' }}>
                  From Admin · {(() => {
                    try {
                      const diff = Math.floor((Date.now() - new Date(n.timestamp)) / 60000);
                      if (diff < 1) return 'Just now';
                      if (diff < 60) return `${diff}m ago`;
                      if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
                      return new Date(n.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
                    } catch { return 'Recently'; }
                  })()}
                </span>
              </div>
              <button onClick={() => dismissNotification(n.id)}
                style={{ padding: '4px 10px', borderRadius: 6, border: '1px solid #fde68a', background: '#fff', color: '#92400e', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }}>✕ Dismiss</button>
            </div>
          ))}
        </div>
      )}

      {/* Stats Grid */}
      <div className="seller-stats-grid">
        {statCards.map((s, i) => (
          <div key={i} className="seller-stat-card" style={s.label === 'New Orders' && stats.pendingOrders > 0 ? { border: '2px solid #f59e0b', animation: 'sellerGlow 2s infinite' } : {}}>
            <div className={`seller-stat-icon ${s.color}`}>{s.icon}</div>
            <div className="seller-stat-info">
              <p>{s.label}</p>
              <h3>{s.value}</h3>
              <div className={`stat-change ${s.up ? 'up' : 'down'}`}>{s.change}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="seller-card" style={{ marginBottom: 20 }}>
        <div className="seller-card-header">
          <h3>⚡ Quick Actions</h3>
        </div>
        <div className="seller-card-body" style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="seller-btn seller-btn-primary" onClick={() => navigate('/farmer/products')}>📦 Add Product</button>
          <button className="seller-btn seller-btn-primary" onClick={() => navigate('/farmer/direct-payment')} style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7)', boxShadow: '0 4px 14px rgba(124,58,237,0.3)' }}>💳 Direct Payment</button>
          <button className="seller-btn seller-btn-secondary" onClick={() => navigate('/farmer/orders')}>🛒 View Orders</button>
          <button className="seller-btn seller-btn-secondary" onClick={() => navigate('/farmer/analytics')}>📈 Analytics</button>
          <button className="seller-btn seller-btn-secondary" onClick={() => navigate('/farmer/ai-tools')}>🤖 AI Tools</button>
          <button className="seller-btn seller-btn-secondary" onClick={() => navigate('/farmer/messages')}>💬 Messages</button>
          <button className="seller-btn seller-btn-secondary" onClick={() => navigate('/farmer/marketing')}>📢 Marketing</button>
        </div>
      </div>

      {/* Weather + Activity Feed + Revenue */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 20 }}>
        {/* Weather */}
        <PremiumWeatherWidget defaultLocation={user?.location || 'Hyderabad'} />

        {/* Activity Feed */}
        <div className="seller-card">
          <div className="seller-card-header">
            <h3>📋 Recent Activity</h3>
          </div>
          <div className="seller-card-body">
            <div className="seller-activity-feed">
              {activityFeed.map(a => (
                <div key={a.id} className="seller-activity-item">
                  <div className={`seller-activity-dot ${a.color}`} />
                  <div className="seller-activity-info">
                    <p dangerouslySetInnerHTML={{ __html: a.text }} />
                    <span>{a.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Revenue Summary */}
        <div className="seller-card">
          <div className="seller-card-header"><h3>💰 Revenue Summary</h3></div>
          <div className="seller-card-body">
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>Total Earnings</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#166534' }}>₹{Number(stats.earnings).toLocaleString('en-IN')}</span>
              </div>
              <div className="seller-progress-bar">
                <div className="seller-progress-fill green" style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>This Month</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#7c3aed' }}>₹{Number(stats.thisMonth).toLocaleString('en-IN')}</span>
              </div>
              <div className="seller-progress-bar">
                <div className="seller-progress-fill blue" style={{ width: stats.earnings > 0 ? `${Math.min((stats.thisMonth / stats.earnings) * 100, 100)}%` : '0%' }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>Pending Payouts</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#d97706' }}>₹{Number(stats.pending).toLocaleString('en-IN')}</span>
              </div>
              <div className="seller-progress-bar">
                <div className="seller-progress-fill amber" style={{ width: stats.earnings > 0 ? `${Math.min((stats.pending / stats.earnings) * 100, 100)}%` : '0%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Orders + Top Products */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16 }}>
        {/* Recent Orders */}
        <div className="seller-card">
          <div className="seller-card-header">
            <h3>🛒 Recent Orders</h3>
            <button className="seller-btn seller-btn-ghost seller-btn-sm" onClick={() => navigate('/farmer/orders')}>View All →</button>
          </div>
          <div className="seller-card-body" style={{ padding: 0 }}>
            {recentOrders.length > 0 ? (
              <div className="seller-table-wrap">
                <table className="seller-table">
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Product</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentOrders.map(order => (
                      <tr key={order.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/farmer/orders')}>
                        <td style={{ fontWeight: 600 }}>#{order.id}</td>
                        <td>{order.product_name || 'Product'}</td>
                        <td style={{ fontWeight: 700, color: '#166534' }}>₹{order.total_price || order.total || 0}</td>
                        <td>{getStatusBadge(order.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="seller-empty-state">
                <div className="empty-icon">🛒</div>
                <h3>No orders yet</h3>
                <p>Orders will appear here when buyers purchase your products</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Products */}
        <div className="seller-card">
          <div className="seller-card-header">
            <h3>⭐ Top Products</h3>
            <button className="seller-btn seller-btn-ghost seller-btn-sm" onClick={() => navigate('/farmer/products')}>Manage →</button>
          </div>
          <div className="seller-card-body" style={{ padding: 0 }}>
            {topProducts.length > 0 ? (
              <div className="seller-table-wrap">
                <table className="seller-table">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Price</th>
                      <th>Stock</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topProducts.map(prod => (
                      <tr key={prod.id || prod._id}>
                        <td style={{ fontWeight: 600 }}>{prod.name}</td>
                        <td style={{ color: '#166534', fontWeight: 600 }}>₹{prod.price}/{prod.unit || 'kg'}</td>
                        <td>
                          <span style={{ color: (prod.stockQuantity ?? prod.quantity ?? 0) <= 10 ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                            {prod.stockQuantity ?? prod.quantity ?? 0} {prod.unit || 'kg'}
                          </span>
                        </td>
                        <td>
                          <span className={`seller-badge ${prod.status === 'approved' ? 'seller-badge-success' : prod.status === 'rejected' ? 'seller-badge-danger' : 'seller-badge-warning'}`}>
                            {prod.status || 'pending'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="seller-empty-state">
                <div className="empty-icon">📦</div>
                <h3>No products yet</h3>
                <p>Start adding products to your catalog</p>
                <button className="seller-btn seller-btn-primary seller-btn-sm" style={{ marginTop: 12 }} onClick={() => navigate('/farmer/products')}>
                  Add Product
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rating Card */}
      <div className="seller-card" style={{ marginTop: 16 }}>
        <div className="seller-card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ fontSize: '2.2rem' }}>⭐</div>
            <div>
              <p style={{ margin: 0, fontSize: '0.78rem', color: '#6b7280' }}>Your Average Rating</p>
              <h3 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800, color: '#14532d' }}>
                {stats.rating ? Number(stats.rating).toFixed(1) : 'N/A'}/5.0
              </h3>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {'⭐'.repeat(Math.floor(stats.rating || 0)).split('').map((_, i) => (
              <span key={i} style={{ fontSize: '1.4rem' }}>⭐</span>
            ))}
          </div>
          <div style={{ textAlign: 'right' }}>
            <p style={{ margin: 0, fontSize: '0.72rem', color: '#9ca3af' }}>Maintain high ratings for better visibility</p>
            <button className="seller-btn seller-btn-ghost seller-btn-sm" style={{ marginTop: 6 }} onClick={() => navigate('/farmer/marketing')}>
              Boost Visibility →
            </button>
          </div>
        </div>
      </div>
    </SellerLayout>
  );
}
