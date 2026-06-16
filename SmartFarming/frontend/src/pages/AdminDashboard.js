import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import { FiUsers, FiPackage, FiTrendingUp, FiCheckCircle } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { adminAPI, buyerAPI } from '../services/api';
import '../styles/dashboard.css';
import { getProductImage, PLACEHOLDER_IMG } from '../utils/productImages';

// ============================================================================
// AdminUsers – User Management with Edit (suspend/activate) & Delete
// ============================================================================
const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loadingId, setLoadingId] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await adminAPI.getUsers({});
      const data = response.data;
      // API may return {farmers:[], buyers:[]} or {users:[]} or a flat array
      const allUsers = Array.isArray(data)
        ? data
        : [
            ...(data.farmers || []).map((f) => ({
              ...f,
              name: `${f.first_name || ''} ${f.last_name || ''}`.trim() || f.name || 'N/A',
              role: 'farmer',
              status: f.status || 'active',
            })),
            ...(data.buyers || []).map((b) => ({
              ...b,
              name: `${b.first_name || ''} ${b.last_name || ''}`.trim() || b.name || 'N/A',
              role: 'buyer',
              status: b.status || 'active',
            })),
            ...(data.users || []),
          ];
      setUsers(allUsers);
    } catch (error) {
      toast.error('Failed to load users');
    }
  };

  const handleToggleStatus = async (user) => {
    const action = user.status === 'suspended' ? 'activate' : 'suspend';
    setLoadingId(user.id);
    try {
      if (action === 'suspend') {
        await adminAPI.suspendUser(user.id, user.role);
        toast.success(`${user.name || 'User'} has been suspended`);
      } else {
        await adminAPI.activateUser(user.id, user.role);
        toast.success(`${user.name || 'User'} has been activated`);
      }
      // Update local state so UI reflects the change immediately
      setUsers((prev) =>
        prev.map((u) =>
          u.id === user.id
            ? { ...u, status: action === 'suspend' ? 'suspended' : 'active' }
            : u
        )
      );
    } catch (error) {
      toast.error(`Failed to ${action} user`);
    } finally {
      setLoadingId(null);
    }
  };

  const handleDelete = async (user) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${user.name || user.email}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setLoadingId(user.id);
    try {
      // Use suspend as a soft-delete
      await adminAPI.suspendUser(user.id, user.role);
      toast.success(`${user.name || 'User'} has been removed`);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
    } catch (error) {
      toast.error('Failed to delete user');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="dashboard-section">
      <h2>User Management</h2>
      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                  No users found
                </td>
              </tr>
            )}
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>
                  <span className={`badge ${user.status}`}>{user.status}</span>
                </td>
                <td>
                  <button
                    className="action-icon"
                    disabled={loadingId === user.id}
                    onClick={() => handleToggleStatus(user)}
                  >
                    {loadingId === user.id
                      ? '...'
                      : user.status === 'suspended'
                      ? 'Activate'
                      : 'Suspend'}
                  </button>
                  <button
                    className="action-icon delete"
                    disabled={loadingId === user.id}
                    onClick={() => handleDelete(user)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// AdminProducts – Shows ALL products (not just pending)
// ============================================================================
const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [loadingId, setLoadingId] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await adminAPI.getAllProducts();
      const data = response.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (error) {
      // Fallback: try pending products
      try {
        const response = await adminAPI.getPendingProducts();
        const data = response.data;
        setProducts(Array.isArray(data) ? data : data.products || []);
      } catch {
        setProducts([]);
      }
    }
  };

  const handleApprove = async (product) => {
    setLoadingId(product.id);
    try {
      await adminAPI.approveProduct(product.id);
      toast.success(`"${product.name}" approved`);
      setProducts((prev) =>
        prev.map((p) => (p.id === product.id ? { ...p, approval_status: 'approved', status: 'approved' } : p))
      );
    } catch (error) {
      toast.error('Failed to approve product');
    } finally {
      setLoadingId(null);
    }
  };

  const handleReject = async (product) => {
    const reason = window.prompt(`Reason for rejecting "${product.name}":`);
    if (reason === null) return; // user cancelled
    setLoadingId(product.id);
    try {
      await adminAPI.rejectProduct(product.id, reason);
      toast.success(`"${product.name}" rejected`);
      setProducts((prev) =>
        prev.map((p) => (p.id === product.id ? { ...p, approval_status: 'rejected', status: 'rejected', rejection_reason: reason } : p))
      );
    } catch (error) {
      toast.error('Failed to reject product');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="dashboard-section">
      <h2>Product Management</h2>
      <div className="products-list">
        {products.length === 0 && (
          <p style={{ textAlign: 'center', color: '#888', padding: '2rem' }}>
            No products found
          </p>
        )}
        {products.map((product) => {
          const pStatus = product.approval_status || product.status || 'pending';
          const imgSrc = getProductImage(product);

          return (
          <div key={product.id} style={{
            background: 'rgba(255,255,255,0.97)',
            borderRadius: '16px',
            border: '1px solid rgba(22,163,74,0.08)',
            padding: '0',
            marginBottom: '16px',
            boxShadow: '0 2px 16px rgba(22,101,52,0.07)',
            overflow: 'hidden',
          }}>
            {/* Product Header with Image */}
            <div style={{ display: 'flex', gap: '16px', padding: '16px 20px', alignItems: 'center' }}>
              <img
                src={imgSrc}
                alt={product.name}
                style={{
                  width: '72px', height: '72px', borderRadius: '14px',
                  objectFit: 'cover', border: '2px solid #dcfce7',
                  boxShadow: '0 2px 8px rgba(22,101,52,0.1)',
                }}
                onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=200&h=200&fit=crop'; }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: 0, color: '#14532d', fontSize: '1.1rem' }}>{product.name}</h4>
                    <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: '#888' }}>
                      by {product.first_name ? `${product.first_name} ${product.last_name || ''}`.trim() : 'Unknown Farmer'}
                      {product.farmer_phone && <span style={{ marginLeft: 8, color: '#aaa' }}>📞 {product.farmer_phone}</span>}
                    </p>
                  </div>
                  <span style={{
                    padding: '4px 14px', borderRadius: '20px', fontSize: '0.72rem',
                    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px',
                    background: pStatus === 'approved' ? 'rgba(34,197,94,0.15)' : pStatus === 'rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                    color: pStatus === 'approved' ? '#15803d' : pStatus === 'rejected' ? '#dc2626' : '#d97706',
                  }}>
                    {pStatus}
                  </span>
                </div>
              </div>
            </div>

            {/* Detail Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1px', background: 'rgba(22,163,74,0.04)', margin: '0 16px', borderRadius: '10px', overflow: 'hidden' }}>
              <div style={{ background: '#fff', padding: '10px', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: '0.68rem', color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Price</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d', fontSize: '1rem' }}>₹{product.price}/{product.unit || 'kg'}</p>
              </div>
              <div style={{ background: '#fff', padding: '10px', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: '0.68rem', color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Quantity</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d', fontSize: '1rem' }}>{product.quantity} {product.unit || 'kg'}</p>
              </div>
              <div style={{ background: '#fff', padding: '10px', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: '0.68rem', color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Category</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d', fontSize: '0.9rem' }}>{product.category || 'N/A'}</p>
              </div>
              <div style={{ background: '#fff', padding: '10px', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: '0.68rem', color: '#999', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Location</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d', fontSize: '0.9rem' }}>{product.location || 'N/A'}</p>
              </div>
            </div>

            {/* Description */}
            {product.description && (
              <p style={{ fontSize: '0.85rem', color: '#555', margin: '12px 16px', lineHeight: '1.5', background: '#fafafa', padding: '10px 12px', borderRadius: '8px', borderLeft: '3px solid #22c55e' }}>
                📋 {product.description}
              </p>
            )}

            {/* Action Buttons */}
            {pStatus === 'pending' && (
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', padding: '12px 16px' }}>
              <button
                className="btn-approve"
                disabled={loadingId === product.id}
                onClick={() => handleApprove(product)}
                style={{ padding: '8px 20px', borderRadius: '8px', fontWeight: 600 }}
              >
                {loadingId === product.id ? '...' : '✅ Approve'}
              </button>
              <button
                className="btn-reject"
                disabled={loadingId === product.id}
                onClick={() => handleReject(product)}
                style={{ padding: '8px 20px', borderRadius: '8px', fontWeight: 600 }}
              >
                ❌ Reject
              </button>
            </div>
            )}
            {pStatus === 'approved' && (
              <div style={{ padding: '10px 16px', textAlign: 'right' }}>
                <span style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600 }}>✅ Product is live on marketplace</span>
              </div>
            )}
            {pStatus === 'rejected' && product.rejection_reason && (
              <div style={{ padding: '10px 16px', background: '#fef2f2', margin: '0 16px 12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: '#dc2626' }}>❌ Rejected: {product.rejection_reason}</span>
              </div>
            )}
          </div>
          );
        })}
      </div>
    </div>
  );
};

// ============================================================================
// AdminOrders – Order Monitoring
// ============================================================================
const AdminOrders = () => {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await adminAPI.getOrdersAnalytics();
      const data = response.data;
      setOrders(Array.isArray(data) ? data : data.orders || []);
    } catch (error) {
      setOrders([]);
    }
  };

  return (
    <div className="dashboard-section">
      <h2>Order Monitoring</h2>
      <div className="orders-grid">
        {orders.length === 0 && (
          <p style={{ textAlign: 'center', color: '#888', padding: '2rem' }}>
            No orders found
          </p>
        )}
        {orders.map((order) => (
          <div key={order.id} className="order-card">
            <h4>Order #{order.id}</h4>
            <p>Farmer: {order.farmerName || order.farmer_name || 'N/A'}</p>
            <p>Buyer: {order.buyerName || order.buyer_name || 'N/A'}</p>
            <p>
              Status:{' '}
              <span className={`status-badge ${order.status}`}>{order.status}</span>
            </p>
            <p>Total: ₹{order.total || order.total_amount || 0}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// AdminActivityFeed – Live Activity Feed with Auto-Refresh
// ============================================================================
const AdminActivityFeed = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchActivities = useCallback(async () => {
    try {
      const response = await adminAPI.getActivityFeed();
      const data = response.data;
      setActivities(data.activities || []);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to load activity feed', error);
      if (loading) toast.error('Failed to load activity feed');
    } finally {
      setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchActivities();
    const interval = setInterval(fetchActivities, 30000);
    return () => clearInterval(interval);
  }, [fetchActivities]);

  const getActivityIcon = (type) => {
    switch (type) {
      case 'purchase': return '\uD83D\uDED2';
      case 'product_listed': return '\uD83D\uDCE6';
      case 'order': return '\uD83D\uDCCB';
      default: return '\uD83D\uDD14';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'purchase': return '#22c55e';
      case 'product_listed': return '#3b82f6';
      case 'order': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = Math.floor((now - date) / 1000);
      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="dashboard-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, color: '#14532d' }}>
          \uD83D\uDCE1 Live Activity Feed
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {lastRefresh && (
            <span style={{ fontSize: '0.75rem', color: '#888' }}>
              Last updated: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <div style={{
            width: '10px', height: '10px', borderRadius: '50%',
            background: '#22c55e', boxShadow: '0 0 8px rgba(34,197,94,0.5)',
            animation: 'pulse 2s infinite',
          }} />
          <span style={{ fontSize: '0.8rem', color: '#22c55e', fontWeight: 600 }}>LIVE</span>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
          <div style={{ fontSize: '2rem', marginBottom: '10px' }}>\u23F3</div>
          Loading activity feed...
        </div>
      ) : activities.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
          <div style={{ fontSize: '2rem', marginBottom: '10px' }}>\uD83D\uDCED</div>
          No recent activity found
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {activities.map((activity, index) => (
            <div
              key={index}
              style={{
                background: 'rgba(255,255,255,0.97)',
                borderRadius: '12px',
                padding: '14px 18px',
                borderLeft: `4px solid ${getActivityColor(activity.type)}`,
                boxShadow: '0 1px 8px rgba(22,101,52,0.06)',
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                transition: 'transform 0.15s, box-shadow 0.15s',
                cursor: 'default',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = '0 3px 16px rgba(22,101,52,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = '0 1px 8px rgba(22,101,52,0.06)';
              }}
            >
              <div style={{
                width: '42px', height: '42px', borderRadius: '12px',
                background: `${getActivityColor(activity.type)}15`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.3rem', flexShrink: 0,
              }}>
                {getActivityIcon(activity.type)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: '0.9rem', color: '#1f2937', fontWeight: 500, lineHeight: 1.4 }}>
                  {activity.message}
                </p>
                <span style={{
                  fontSize: '0.72rem', color: '#9ca3af', fontWeight: 500,
                  textTransform: 'uppercase', letterSpacing: '0.3px',
                }}>
                  {activity.type.replace('_', ' ')}
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#6b7280', whiteSpace: 'nowrap', flexShrink: 0 }}>
                {formatTime(activity.timestamp)}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
};

// ============================================================================
// AdminReceipts – All Receipts Table
// ============================================================================
const AdminReceipts = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReceipts();
  }, []);

  const fetchReceipts = async () => {
    try {
      const response = await adminAPI.getAllReceipts();
      const data = response.data;
      setReceipts(data.receipts || []);
    } catch (error) {
      console.error('Failed to load receipts', error);
      toast.error('Failed to load receipts');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="dashboard-section">
      <h2 style={{ color: '#14532d', marginBottom: '20px' }}>🧾 All Receipts</h2>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>Loading receipts...</div>
      ) : receipts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
          <div style={{ fontSize: '2rem', marginBottom: '10px' }}>📭</div>
          No receipts found
        </div>
      ) : (
        <div style={{ overflowX: 'auto', borderRadius: '12px', boxShadow: '0 2px 12px rgba(22,101,52,0.08)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ background: 'linear-gradient(135deg, #166534, #14532d)' }}>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'left', fontWeight: 600 }}>Receipt ID</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'left', fontWeight: 600 }}>Buyer</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'left', fontWeight: 600 }}>Farmer</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'left', fontWeight: 600 }}>Product</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'right', fontWeight: 600 }}>Qty (kg)</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'right', fontWeight: 600 }}>Amount</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'center', fontWeight: 600 }}>Payment</th>
                <th style={{ padding: '12px 16px', color: '#fff', textAlign: 'left', fontWeight: 600 }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((receipt, index) => (
                <tr
                  key={index}
                  style={{
                    background: index % 2 === 0 ? '#fff' : '#f0fdf4',
                    borderBottom: '1px solid #e5e7eb',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#dcfce7'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = index % 2 === 0 ? '#fff' : '#f0fdf4'; }}
                >
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: '#166534' }}>
                    {receipt.receipt_id || receipt.id}
                  </td>
                  <td style={{ padding: '10px 16px', color: '#374151' }}>{receipt.buyer_name || 'N/A'}</td>
                  <td style={{ padding: '10px 16px', color: '#374151' }}>{receipt.farmer_name || 'N/A'}</td>
                  <td style={{ padding: '10px 16px', color: '#374151' }}>{receipt.product_name || 'N/A'}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', color: '#374151' }}>
                    {receipt.quantity_kg || '-'}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: 700, color: '#14532d' }}>
                    ₹{receipt.grand_total || receipt.total_amount || 0}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
                      background: receipt.payment_type === 'cash' ? '#fef3c7' : '#dbeafe',
                      color: receipt.payment_type === 'cash' ? '#92400e' : '#1e40af',
                    }}>
                      {receipt.payment_type || 'N/A'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', color: '#6b7280', fontSize: '0.82rem' }}>
                    {formatDate(receipt.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// AdminDashboard – Main dashboard with stats & nested routes
// ============================================================================
const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalOrders: 0,
    revenue: 0,
    pendingProducts: 0,
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await adminAPI.getDashboard();
      const data = response.data;
      // Handle both snake_case (backend) and camelCase field names
      setStats({
        totalUsers: data.total_users ?? data.totalUsers ?? 0,
        totalOrders: data.total_orders ?? data.totalOrders ?? 0,
        revenue: data.total_revenue ?? data.revenue ?? 0,
        pendingProducts: data.pending_products ?? data.pendingProducts ?? 0,
      });
    } catch (error) {
      console.error('Failed to load stats', error);
      // Fallback: derive counts from individual endpoints
      try {
        const usersRes = await adminAPI.getUsers({});
        const uData = usersRes.data;
        const userCount = Array.isArray(uData)
          ? uData.length
          : (uData.farmers?.length || 0) + (uData.buyers?.length || 0) + (uData.users?.length || 0);
        setStats((prev) => ({ ...prev, totalUsers: userCount }));
      } catch {
        /* ignore */
      }
    }
  };

  // Green gradient for stat icons
  const greenIconStyle = {
    background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    color: '#fff',
    borderRadius: '12px',
    width: 48,
    height: 48,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.4rem',
  };

  return (
    <div className="dashboard">
      <Routes>
        <Route
          path="/"
          element={
            <div className="dashboard-overview">
              <h1>Admin Dashboard</h1>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="icon" style={greenIconStyle}>
                    <FiUsers />
                  </div>
                  <div className="stat-content">
                    <p>Total Users</p>
                    <h3>{stats.totalUsers}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon" style={greenIconStyle}>
                    <FiPackage />
                  </div>
                  <div className="stat-content">
                    <p>Total Orders</p>
                    <h3>{stats.totalOrders}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon" style={greenIconStyle}>
                    <FiTrendingUp />
                  </div>
                  <div className="stat-content">
                    <p>Total Revenue</p>
                    <h3>₹{Number(stats.revenue).toLocaleString('en-IN')}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon" style={greenIconStyle}>
                    <FiCheckCircle />
                  </div>
                  <div className="stat-content">
                    <p>Pending Products</p>
                    <h3>{stats.pendingProducts}</h3>
                  </div>
                </div>
              </div>
            </div>
          }
        />
        <Route path="users" element={<AdminUsers />} />
        <Route path="products" element={<AdminProducts />} />
        <Route path="orders" element={<AdminOrders />} />
        <Route path="activity" element={<AdminActivityFeed />} />
        <Route path="receipts" element={<AdminReceipts />} />
      </Routes>
    </div>
  );
};

export default AdminDashboard;
