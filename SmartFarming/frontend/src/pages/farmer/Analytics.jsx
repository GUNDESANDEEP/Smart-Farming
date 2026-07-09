import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { farmerAPI, checkoutAPI } from '../../services/api';
import toast from 'react-hot-toast';
import SellerLayout from './SellerLayout';

export default function FarmerAnalytics() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [earnings, setEarnings] = useState({ total: 0, thisMonth: 0, pending: 0 });
  const [activeTab, setActiveTab] = useState('sales');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [pRes, oRes, eRes] = await Promise.all([
        farmerAPI.getProducts(1, 100),
        checkoutAPI.getFarmerOrders(),
        farmerAPI.getEarnings(),
      ]);
      const pData = pRes.data; setProducts(Array.isArray(pData) ? pData : (pData.products || pData.data || []));
      const orderList = oRes.data.orders || oRes.data.data || [];
      const ordersArr = Array.isArray(orderList) ? orderList : [];
      setOrders(ordersArr);

      const delivered = ordersArr.filter(o => o.order_status === 'DELIVERED');
      const totalRev = delivered.reduce((s, o) => s + parseFloat(o.subtotal || o.total || 0), 0);

      // Monthly sales calculations
      const currentMonth = new Date().getMonth();
      const currentYear = new Date().getFullYear();
      const thisMonthEarnings = delivered
        .filter(o => {
          if (!o.created_at) return false;
          const d = new Date(o.created_at);
          return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
        })
        .reduce((sum, o) => sum + parseFloat(o.subtotal || o.total || 0), 0);

      setEarnings({
        total: totalRev,
        thisMonth: thisMonthEarnings,
        pending: ordersArr.filter(o => ['PLACED', 'CONFIRMED', 'ACCEPTED', 'PACKED', 'OUT_FOR_DELIVERY'].includes(o.order_status)).reduce((s, o) => s + parseFloat(o.subtotal || o.total || 0), 0)
      });
    } catch { /* silent - page shows empty state */ }
  };

  // Computed analytics
  const deliveredOrders = orders.filter(o => o.order_status === 'DELIVERED');
  const totalRevenue = deliveredOrders.reduce((s, o) => s + parseFloat(o.subtotal || o.total || 0), 0);
  const avgOrderValue = deliveredOrders.length > 0 ? totalRevenue / deliveredOrders.length : 0;

  // Monthly sales data (last 6 months)
  const monthlyData = [];
  for (let i = 5; i >= 0; i--) {
    const d = new Date();
    d.setMonth(d.getMonth() - i);
    const month = d.toLocaleString('en-IN', { month: 'short' });
    const monthOrders = deliveredOrders.filter(o => {
      const od = new Date(o.created_at);
      return od.getMonth() === d.getMonth() && od.getFullYear() === d.getFullYear();
    });
    const revenue = monthOrders.reduce((s, o) => s + parseFloat(o.subtotal || o.total || 0), 0);
    monthlyData.push({ month, orders: monthOrders.length, revenue });
  }
  const maxRevenue = Math.max(...monthlyData.map(m => m.revenue), 1);

  // Product performance
  const productPerformance = products.map(p => {
    const pOrders = orders.filter(o => o.product_name === p.name);
    const pRevenue = pOrders.filter(o => o.order_status === 'DELIVERED').reduce((s, o) => s + parseFloat(o.subtotal || o.total || 0), 0);
    return { ...p, orderCount: pOrders.length, revenue: pRevenue };
  }).sort((a, b) => b.revenue - a.revenue);

  // Customer insights
  const customerMap = {};
  orders.forEach(o => {
    const key = o.buyer_name || o.buyer_phone || 'Unknown';
    if (!customerMap[key]) customerMap[key] = { name: `${o.buyer_name || ''} ${o.buyer_last_name || ''}`.trim() || 'Unknown', orders: 0, spent: 0, city: o.buyer_city || '' };
    customerMap[key].orders++;
    if (o.order_status === 'DELIVERED') customerMap[key].spent += parseFloat(o.subtotal || o.total || 0);
  });
  const topCustomers = Object.values(customerMap).sort((a, b) => b.spent - a.spent).slice(0, 10);

  // Category distribution
  const categoryMap = {};
  products.forEach(p => {
    const cat = p.category || 'Others';
    if (!categoryMap[cat]) categoryMap[cat] = { count: 0, revenue: 0 };
    categoryMap[cat].count++;
  });
  orders.filter(o => o.order_status === 'DELIVERED').forEach(o => {
    const prod = products.find(p => p.name === o.product_name);
    const cat = prod?.category || 'Others';
    if (categoryMap[cat]) categoryMap[cat].revenue += parseFloat(o.subtotal || o.total || 0);
  });

  const catColors = { Vegetables: '#22c55e', Fruits: '#f59e0b', Grains: '#8b5cf6', Dairy: '#3b82f6', Spices: '#ef4444', Pulses: '#14b8a6', Others: '#6b7280' };




  return (
    <SellerLayout title="Analytics" subtitle="Track your business performance">
      {/* Summary Stats */}
      <div className="seller-stats-grid">
        {[
          { label: 'Total Revenue', value: `₹${totalRevenue.toLocaleString('en-IN')}`, icon: '💰', color: 'green' },
          { label: 'This Month', value: `₹${Number(earnings.thisMonth).toLocaleString('en-IN')}`, icon: '📅', color: 'purple' },
          { label: 'Total Orders', value: orders.length, icon: '📦', color: 'blue' },
          { label: 'Avg Order Value', value: `₹${avgOrderValue.toFixed(0)}`, icon: '📊', color: 'teal' },
          { label: 'Products', value: products.length, icon: '🏷️', color: 'amber' },
          { label: 'Conversion Rate', value: `${deliveredOrders.length > 0 ? ((deliveredOrders.length / Math.max(orders.length, 1)) * 100).toFixed(0) : 0}%`, icon: '🎯', color: 'rose' },
        ].map((s, i) => (
          <div key={i} className="seller-stat-card">
            <div className={`seller-stat-icon ${s.color}`}>{s.icon}</div>
            <div className="seller-stat-info"><p>{s.label}</p><h3>{s.value}</h3></div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="seller-tabs-pill" style={{ marginBottom: 20 }}>
        {[
          { key: 'sales', label: '📈 Sales Dashboard' },
          { key: 'products', label: '🏷️ Product Performance' },
          { key: 'customers', label: '👥 Customer Insights' },
          { key: 'reports', label: '📋 Sales Reports' },
          { key: 'profit', label: '💹 Profit Analysis' },
        ].map(t => (
          <button key={t.key} className={`seller-tab-pill ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Sales Dashboard */}
      {activeTab === 'sales' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16 }}>
          {/* Monthly Revenue Chart */}
          <div className="seller-card">
            <div className="seller-card-header"><h3>📊 Monthly Revenue</h3></div>
            <div className="seller-card-body">
              <div className="seller-bar-chart">
                {monthlyData.map((m, i) => (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div className="seller-bar-value">₹{m.revenue > 1000 ? (m.revenue / 1000).toFixed(1) + 'k' : m.revenue}</div>
                    <div className="seller-bar" style={{ height: `${Math.max((m.revenue / maxRevenue) * 100, 5)}%` }} />
                    <div className="seller-bar-label">{m.month}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Revenue by Category */}
          <div className="seller-card">
            <div className="seller-card-header"><h3>🏷️ Revenue by Category</h3></div>
            <div className="seller-card-body">
              {Object.entries(categoryMap).map(([cat, data]) => (
                <div key={cat} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1f2937' }}>{cat}</span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: catColors[cat] || '#6b7280' }}>₹{data.revenue.toLocaleString('en-IN')} ({data.count} products)</span>
                  </div>
                  <div className="seller-progress-bar">
                    <div style={{ height: '100%', borderRadius: 4, background: catColors[cat] || '#6b7280', width: `${Math.max((data.revenue / Math.max(totalRevenue, 1)) * 100, 3)}%`, transition: 'width 0.6s ease' }} />
                  </div>
                </div>
              ))}
              {Object.keys(categoryMap).length === 0 && <div className="seller-empty-state"><p>No category data yet</p></div>}
            </div>
          </div>

          {/* Order Status Distribution */}
          <div className="seller-card">
            <div className="seller-card-header"><h3>📦 Order Status</h3></div>
            <div className="seller-card-body">
              {[
                { label: 'Pending', count: orders.filter(o => o.status === 'pending').length, color: '#f59e0b' },
                { label: 'Active', count: orders.filter(o => ['confirmed','processing','packed','dispatched','in_transit','out_for_delivery'].includes(o.status)).length, color: '#3b82f6' },
                { label: 'Delivered', count: deliveredOrders.length, color: '#22c55e' },
                { label: 'Cancelled', count: orders.filter(o => o.status === 'cancelled').length, color: '#ef4444' },
              ].map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: s.color }} />
                  <span style={{ flex: 1, fontSize: '0.85rem', color: '#374151' }}>{s.label}</span>
                  <span style={{ fontWeight: 700, color: s.color }}>{s.count}</span>
                  <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
                    ({orders.length > 0 ? ((s.count / orders.length) * 100).toFixed(0) : 0}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Revenue Summary */}
          <div className="seller-card">
            <div className="seller-card-header"><h3>💰 Revenue Summary</h3></div>
            <div className="seller-card-body">
              {[
                { label: 'Total Revenue', value: totalRevenue, color: '#166534' },
                { label: 'This Month', value: earnings.thisMonth, color: '#7c3aed' },
                { label: 'Pending Payouts', value: earnings.pending, color: '#d97706' },
                { label: 'Net Profit (est.)', value: totalRevenue * 0.85, color: '#0ea5e9' },
              ].map((r, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < 3 ? '1px solid #f1f5f9' : 'none' }}>
                  <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>{r.label}</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: r.color }}>₹{Number(r.value).toLocaleString('en-IN')}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Product Performance */}
      {activeTab === 'products' && (
        <div className="seller-card">
          <div className="seller-card-header"><h3>🏆 Product Performance Rankings</h3></div>
          <div className="seller-card-body" style={{ padding: 0 }}>
            <div className="seller-table-wrap">
              <table className="seller-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Orders</th>
                    <th>Revenue</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {productPerformance.length > 0 ? productPerformance.map((p, i) => (
                    <tr key={p.id || p._id}>
                      <td style={{ fontWeight: 700, color: i < 3 ? '#166534' : '#6b7280' }}>{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}</td>
                      <td style={{ fontWeight: 600 }}>{p.name}</td>
                      <td><span className="seller-badge seller-badge-info">{p.category || 'Others'}</span></td>
                      <td style={{ color: '#166534', fontWeight: 600 }}>₹{p.price}</td>
                      <td style={{ color: (p.stockQuantity ?? p.quantity ?? 0) <= 10 ? '#dc2626' : '#16a34a', fontWeight: 600 }}>{p.stockQuantity ?? p.quantity ?? 0} {p.unit || 'kg'}</td>
                      <td style={{ fontWeight: 600 }}>{p.orderCount}</td>
                      <td style={{ fontWeight: 800, color: '#166534' }}>₹{p.revenue.toLocaleString('en-IN')}</td>
                      <td><span className={`seller-badge ${p.status === 'approved' ? 'seller-badge-success' : 'seller-badge-warning'}`}>{p.status || 'pending'}</span></td>
                    </tr>
                  )) : (
                    <tr><td colSpan="8" style={{ textAlign: 'center', padding: 24, color: '#9ca3af' }}>No products yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Customer Insights */}
      {activeTab === 'customers' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16 }}>
          <div className="seller-card">
            <div className="seller-card-header"><h3>👥 Top Customers</h3></div>
            <div className="seller-card-body" style={{ padding: 0 }}>
              <div className="seller-table-wrap">
                <table className="seller-table">
                  <thead><tr><th>#</th><th>Customer</th><th>City</th><th>Orders</th><th>Total Spent</th></tr></thead>
                  <tbody>
                    {topCustomers.length > 0 ? topCustomers.map((c, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 700 }}>{i + 1}</td>
                        <td style={{ fontWeight: 600 }}>{c.name}</td>
                        <td>{c.city || 'N/A'}</td>
                        <td>{c.orders}</td>
                        <td style={{ fontWeight: 800, color: '#166534' }}>₹{c.spent.toLocaleString('en-IN')}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan="5" style={{ textAlign: 'center', padding: 24, color: '#9ca3af' }}>No customer data yet</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="seller-card">
            <div className="seller-card-header"><h3>📊 Customer Stats</h3></div>
            <div className="seller-card-body">
              {[
                { label: 'Total Unique Customers', value: Object.keys(customerMap).length, icon: '👥' },
                { label: 'Repeat Customers', value: Object.values(customerMap).filter(c => c.orders > 1).length, icon: '🔄' },
                { label: 'Avg Orders/Customer', value: Object.keys(customerMap).length > 0 ? (orders.length / Object.keys(customerMap).length).toFixed(1) : '0', icon: '📈' },
                { label: 'Top Customer Spend', value: `₹${topCustomers[0]?.spent?.toLocaleString('en-IN') || 0}`, icon: '🏆' },
              ].map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 0', borderBottom: i < 3 ? '1px solid #f1f5f9' : 'none' }}>
                  <span style={{ fontSize: '1.3rem' }}>{s.icon}</span>
                  <span style={{ flex: 1, fontSize: '0.85rem', color: '#374151' }}>{s.label}</span>
                  <span style={{ fontWeight: 800, color: '#14532d', fontSize: '1.1rem' }}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Sales Reports */}
      {activeTab === 'reports' && (
        <div className="seller-card">
          <div className="seller-card-header">
            <h3>📋 Detailed Sales Report</h3>
            <button className="seller-btn seller-btn-secondary seller-btn-sm" onClick={() => toast.success('Report data ready for export')}>📥 Export</button>
          </div>
          <div className="seller-card-body" style={{ padding: 0 }}>
            <div className="seller-table-wrap">
              <table className="seller-table">
                <thead><tr><th>Order ID</th><th>Product</th><th>Customer</th><th>Qty</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>
                  {orders.slice(0, 20).map(o => (
                    <tr key={o.id}>
                      <td style={{ fontWeight: 600 }}>#{o.id}</td>
                      <td>{o.product_name || 'Product'}</td>
                      <td>{o.buyer_name || 'N/A'}</td>
                      <td>{o.quantity}</td>
                      <td style={{ fontWeight: 700, color: '#166534' }}>₹{o.total_price || o.total || 0}</td>
                      <td><span className={`seller-badge ${o.status === 'delivered' ? 'seller-badge-success' : o.status === 'cancelled' ? 'seller-badge-danger' : 'seller-badge-warning'}`}>{o.status}</span></td>
                      <td style={{ fontSize: '0.78rem', color: '#6b7280' }}>{o.created_at ? new Date(o.created_at).toLocaleDateString('en-IN') : 'N/A'}</td>
                    </tr>
                  ))}
                  {orders.length === 0 && <tr><td colSpan="7" style={{ textAlign: 'center', padding: 24, color: '#9ca3af' }}>No sales data</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Profit Analysis */}
      {activeTab === 'profit' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
          <div className="seller-card">
            <div className="seller-card-header"><h3>💹 Profit Breakdown</h3></div>
            <div className="seller-card-body">
              {[
                { label: 'Gross Revenue', value: totalRevenue, color: '#166534', pct: '100%' },
                { label: 'Platform Fee (5%)', value: totalRevenue * 0.05, color: '#dc2626', pct: '5%' },
                { label: 'Delivery Costs (est. 10%)', value: totalRevenue * 0.10, color: '#f59e0b', pct: '10%' },
                { label: 'Net Profit (est. 85%)', value: totalRevenue * 0.85, color: '#22c55e', pct: '85%' },
              ].map((r, i) => (
                <div key={i} style={{ padding: '14px 0', borderBottom: i < 3 ? '1px solid #f1f5f9' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: '0.85rem', color: '#374151' }}>{r.label}</span>
                    <span style={{ fontWeight: 800, color: r.color, fontSize: '1rem' }}>₹{Number(r.value).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="seller-progress-bar" style={{ height: 6 }}>
                    <div style={{ height: '100%', borderRadius: 3, background: r.color, width: r.pct, transition: 'width 0.6s ease' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="seller-card">
            <div className="seller-card-header"><h3>📈 Monthly Profit Trend</h3></div>
            <div className="seller-card-body">
              <div className="seller-bar-chart">
                {monthlyData.map((m, i) => (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div className="seller-bar-value">₹{(m.revenue * 0.85) > 1000 ? ((m.revenue * 0.85) / 1000).toFixed(1) + 'k' : (m.revenue * 0.85).toFixed(0)}</div>
                    <div className="seller-bar" style={{ height: `${Math.max(((m.revenue * 0.85) / maxRevenue) * 100, 5)}%`, background: 'linear-gradient(180deg, #4ade80, #166534)' }} />
                    <div className="seller-bar-label">{m.month}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </SellerLayout>
  );
}
