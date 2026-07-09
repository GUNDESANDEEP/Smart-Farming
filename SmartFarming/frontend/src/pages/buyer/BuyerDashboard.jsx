import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { buyerAPI, checkoutAPI, weatherAPI } from '../../services/api';
import BuyerLayout from './BuyerLayout';
import PremiumWeatherWidget from '../../components/PremiumWeatherWidget';

// Cache key for localStorage
const CACHE_KEY = 'sf_buyer_dashboard';
const CACHE_TTL = 300000; // 5 minutes

const loadCachedDashboard = () => {
  try {
    const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
    if (cached && (Date.now() - cached.ts) < CACHE_TTL) return cached;
  } catch {}
  return null;
};

const getLocalWishlistCount = () => {
  try {
    const list = JSON.parse(localStorage.getItem('buyer_wishlist') || '[]');
    return Array.isArray(list) ? list.length : 0;
  } catch {
    return 0;
  }
};

export default function BuyerDashboard() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // Initialize from cache instantly
  const cached = useRef(loadCachedDashboard());
  const [stats, setStats] = useState(cached.current?.stats || { totalOrders: 0, activeOrders: 0, delivered: 0, totalSpent: 0, cartItems: 0, wishlist: getLocalWishlistCount() });
  const [recentOrders, setRecentOrders] = useState(cached.current?.recentOrders || []);
  const [weather, setWeather] = useState(cached.current?.weather || null);
  const [activityFeed, setActivityFeed] = useState(cached.current?.activityFeed || []);

  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAll = async () => {
    let ordersArr = [], cartCount = 0;

    // Fetch orders and cart in parallel
    const [ordersRes, cartRes] = await Promise.allSettled([
      checkoutAPI.getOrders(),
      buyerAPI.getCart(),
    ]);

    if (ordersRes.status === 'fulfilled') {
      ordersArr = ordersRes.value.data?.orders || ordersRes.value.data || [];
      if (!Array.isArray(ordersArr)) ordersArr = [];
    }
    if (cartRes.status === 'fulfilled') {
      cartCount = cartRes.value.data?.items?.length || 0;
    }

    const totalSpent = ordersArr.reduce((sum, o) => sum + parseFloat(o.total_amount || 0), 0);

    const newStats = {
      totalOrders: ordersArr.length,
      activeOrders: ordersArr.filter(o => !['DELIVERED', 'CANCELLED', 'delivered', 'cancelled'].includes(o.order_status || o.status)).length,
      delivered: ordersArr.filter(o => ['DELIVERED', 'delivered'].includes(o.order_status || o.status)).length,
      totalSpent,
      cartItems: cartCount,
      wishlist: getLocalWishlistCount(),
    };
    setStats(newStats);

    const newRecentOrders = ordersArr.slice(0, 5);
    setRecentOrders(newRecentOrders);

    // Build activity feed
    const activities = ordersArr.slice(0, 6).map(o => {
      const status = o.order_status || o.status;
      return {
        id: o.id || o.order_number,
        text: status === 'DELIVERED' || status === 'delivered'
          ? `Order <strong>#${o.order_number || o.id}</strong> delivered successfully`
          : status === 'PLACED' || status === 'pending'
          ? `Order <strong>#${o.order_number || o.id}</strong> placed — awaiting confirmation`
          : `Order <strong>#${o.order_number || o.id}</strong> is ${status?.toLowerCase()}`,
        time: o.created_at ? new Date(o.created_at).toLocaleDateString() : 'Recently',
        color: ['DELIVERED','delivered'].includes(status) ? 'green' : ['PLACED','pending'].includes(status) ? 'amber' : 'blue',
      };
    });
    if (activities.length === 0) {
      activities.push(
        { id: 'w1', text: 'Welcome to <strong>SmartFarmer</strong>! Browse our marketplace for fresh produce.', time: 'Just now', color: 'blue' },
        { id: 'w2', text: 'Add items to your <strong>cart</strong> and place your first order!', time: 'Tip', color: 'green' },
        { id: 'w3', text: 'Use <strong>AgriBot</strong> to get farming tips and product recommendations.', time: 'Tip', color: 'purple' },
      );
    }
    setActivityFeed(activities);

    // Weather
    let newWeather = null;
    try {
      const wRes = await weatherAPI.getWeather(user?.location || user?.city || 'Hyderabad');
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

    // Save to cache for instant next load
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        ts: Date.now(), stats: newStats, recentOrders: newRecentOrders,
        weather: newWeather, activityFeed: activities,
      }));
    } catch {}
  };

  const statCards = [
    { label: 'Total Orders', value: stats.totalOrders, icon: '📋', color: 'blue', change: 'All time', up: true },
    { label: 'Active Orders', value: stats.activeOrders, icon: '🚚', color: 'amber', change: 'In progress', up: true },
    { label: 'Delivered', value: stats.delivered, icon: '✅', color: 'green', change: 'Completed', up: true },
    { label: 'Total Spent', value: `₹${Number(stats.totalSpent).toLocaleString('en-IN')}`, icon: '💰', color: 'purple', change: 'Lifetime', up: true },
    { label: 'Cart Items', value: stats.cartItems, icon: '🧺', color: 'teal', change: 'Ready to buy', up: true },
    { label: 'Saved', value: stats.wishlist, icon: '❤️', color: 'red', change: 'Wishlist', up: false },
  ];

  const getStatusBadge = (status) => {
    const map = {
      PLACED: { cls: 'buyer-badge-warning', label: '🔔 Placed' },
      CONFIRMED: { cls: 'buyer-badge-info', label: '✅ Confirmed' },
      PACKING: { cls: 'buyer-badge-purple', label: '📦 Packing' },
      PACKED: { cls: 'buyer-badge-info', label: '📦 Packed' },
      OUT_FOR_DELIVERY: { cls: 'buyer-badge-info', label: '🚚 On the way' },
      DELIVERED: { cls: 'buyer-badge-success', label: '🎉 Delivered' },
      CANCELLED: { cls: 'buyer-badge-danger', label: '❌ Cancelled' },
      pending: { cls: 'buyer-badge-warning', label: '⏳ Pending' },
      confirmed: { cls: 'buyer-badge-info', label: '✅ Confirmed' },
      delivered: { cls: 'buyer-badge-success', label: '🎉 Delivered' },
      cancelled: { cls: 'buyer-badge-danger', label: '❌ Cancelled' },
    };
    const info = map[status] || { cls: 'buyer-badge-info', label: status };
    return <span className={`buyer-badge ${info.cls}`}>{info.label}</span>;
  };

  const displayName = user?.name || user?.first_name || 'Buyer';
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? 'Good Morning' : currentHour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <BuyerLayout>
      {/* ═══ HERO WELCOME SECTION ═══ */}
      <div className="buyer-hero">
        <div className="buyer-hero-content">
          <div>
            <h2>🛍️ {greeting}, {displayName}!</h2>
            <p>Discover fresh products directly from local farmers</p>
          </div>
          <div className="buyer-hero-stats">
            <div className="buyer-hero-stat">
              <h3>{stats.totalOrders}</h3>
              <span>Orders</span>
            </div>
            <div className="buyer-hero-stat">
              <h3>{stats.delivered}</h3>
              <span>Delivered</span>
            </div>
            <div className="buyer-hero-stat">
              <h3>₹{Number(stats.totalSpent).toLocaleString('en-IN')}</h3>
              <span>Spent</span>
            </div>
            <div className="buyer-hero-stat">
              <h3>{stats.cartItems}</h3>
              <span>In Cart</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="buyer-stats-grid">
        {statCards.map((s, i) => (
          <div key={i} className="buyer-stat-card">
            <div className={`buyer-stat-icon ${s.color}`}>{s.icon}</div>
            <div className="buyer-stat-info">
              <p>{s.label}</p>
              <h3>{s.value}</h3>
              <div className={`stat-change ${s.up ? 'up' : 'down'}`}>{s.change}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="buyer-card" style={{ marginBottom: 20 }}>
        <div className="buyer-card-header">
          <h3>⚡ Quick Actions</h3>
        </div>
        <div className="buyer-card-body" style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="buyer-btn buyer-btn-primary" onClick={() => navigate('/buyer/marketplace')}>🛒 Shop Now</button>
          <button className="buyer-btn buyer-btn-primary" onClick={() => navigate('/buyer/cart')} style={{ background: 'linear-gradient(135deg, #0891b2, #06b6d4)', boxShadow: '0 4px 14px rgba(8,145,178,0.3)' }}>🧺 View Cart</button>
          <button className="buyer-btn buyer-btn-secondary" onClick={() => navigate('/buyer/orders')}>📋 My Orders</button>
          <button className="buyer-btn buyer-btn-secondary" onClick={() => navigate('/buyer/checkout')}>💳 Checkout</button>
          <button className="buyer-btn buyer-btn-secondary" onClick={() => navigate('/farmer/agribot')}>🤖 AgriBot</button>
        </div>
      </div>

      {/* Weather + Activity Feed + Spending Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 20 }}>
        {/* Weather */}
        <PremiumWeatherWidget defaultLocation={user?.location || user?.city || 'Hyderabad'} />

        {/* Activity Feed */}
        <div className="buyer-card">
          <div className="buyer-card-header"><h3>📋 Recent Activity</h3></div>
          <div className="buyer-card-body">
            <div className="buyer-activity-feed">
              {activityFeed.map(a => (
                <div key={a.id} className="buyer-activity-item">
                  <div className={`buyer-activity-dot ${a.color}`} />
                  <div className="buyer-activity-info">
                    <p dangerouslySetInnerHTML={{ __html: a.text }} />
                    <span>{a.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Spending Summary */}
        <div className="buyer-card">
          <div className="buyer-card-header"><h3>💳 Spending Summary</h3></div>
          <div className="buyer-card-body">
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>Total Spent</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1e40af' }}>₹{Number(stats.totalSpent).toLocaleString('en-IN')}</span>
              </div>
              <div className="buyer-progress-bar">
                <div className="buyer-progress-fill blue" style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>Active Orders</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#d97706' }}>{stats.activeOrders}</span>
              </div>
              <div className="buyer-progress-bar">
                <div className="buyer-progress-fill amber" style={{ width: stats.totalOrders > 0 ? `${Math.min((stats.activeOrders / stats.totalOrders) * 100, 100)}%` : '0%' }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.82rem', color: '#6b7280' }}>Delivered</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#16a34a' }}>{stats.delivered}</span>
              </div>
              <div className="buyer-progress-bar">
                <div className="buyer-progress-fill green" style={{ width: stats.totalOrders > 0 ? `${Math.min((stats.delivered / stats.totalOrders) * 100, 100)}%` : '0%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="buyer-card">
        <div className="buyer-card-header">
          <h3>🛒 Recent Orders</h3>
          <button className="buyer-btn buyer-btn-ghost buyer-btn-sm" onClick={() => navigate('/buyer/orders')}>View All →</button>
        </div>
        <div className="buyer-card-body" style={{ padding: 0 }}>
          {recentOrders.length > 0 ? (
            <div className="buyer-table-wrap">
              <table className="buyer-table">
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Payment</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentOrders.map(order => (
                    <tr key={order.id || order.order_number} style={{ cursor: 'pointer' }} onClick={() => navigate(`/buyer/orders/${order.id}`)}>
                      <td style={{ fontWeight: 600 }}>{order.order_number || `#${order.id}`}</td>
                      <td>{order.created_at ? new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '--'}</td>
                      <td style={{ fontWeight: 700, color: '#1e40af' }}>₹{parseFloat(order.total_amount || 0).toFixed(0)}</td>
                      <td>
                        <span className={`buyer-badge ${order.payment_method === 'cod' ? 'buyer-badge-warning' : 'buyer-badge-success'}`}>
                          {order.payment_method === 'cod' ? '💵 COD' : '💳 Paid'}
                        </span>
                      </td>
                      <td>{getStatusBadge(order.order_status || order.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="buyer-empty-state">
              <div className="empty-icon">🛒</div>
              <h3>No orders yet</h3>
              <p>Start shopping from our marketplace to see your orders here</p>
              <button className="buyer-btn buyer-btn-primary buyer-btn-sm" style={{ marginTop: 12 }} onClick={() => navigate('/buyer/marketplace')}>
                Shop Now
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Links Card */}
      <div className="buyer-card" style={{ marginTop: 16 }}>
        <div className="buyer-card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ fontSize: '2.2rem' }}>🛍️</div>
            <div>
              <p style={{ margin: 0, fontSize: '0.78rem', color: '#6b7280' }}>Fresh from the Farm</p>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#1e40af' }}>
                SmartFarmer Marketplace
              </h3>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="buyer-btn buyer-btn-primary buyer-btn-sm" onClick={() => navigate('/buyer/marketplace')}>
              🛒 Browse Products
            </button>
            <button className="buyer-btn buyer-btn-secondary buyer-btn-sm" onClick={() => navigate('/buyer/orders')}>
              📋 Track Orders
            </button>
            <button className="buyer-btn buyer-btn-ghost buyer-btn-sm" onClick={() => navigate('/farmer/agribot')}>
              🤖 Ask AgriBot
            </button>
          </div>
        </div>
      </div>
    </BuyerLayout>
  );
}
