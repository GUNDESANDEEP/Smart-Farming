import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { FiPlus, FiPackage, FiTrendingUp, FiDollarSign, FiEdit2, FiTrash2, FiX, FiSave, FiEye, FiDownload } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { farmerAPI, paymentsAPI } from '../services/api';
import ReceiptViewer from '../components/ReceiptViewer';
import '../styles/dashboard.css';
import { getProductImage, PLACEHOLDER_IMG } from '../utils/productImages';
import AgriBot from './AgriBot';

// ─── Constants ───────────────────────────────────────────────────────
const CATEGORIES = ['Vegetables', 'Fruits', 'Grains', 'Dairy', 'Spices', 'Pulses', 'Others'];
const UNITS = ['kg', 'quintal', 'ton', 'dozen', 'piece', 'liter'];

const INITIAL_FORM = {
  name: '',
  description: '',
  category: '',
  price: '',
  quantity: '',
  unit: '',
  location: '',
  discount: '',
};

// ─── Inline style objects (green‑glass theme) ────────────────────────
const formStyles = {
  container: {
    background: 'rgba(255,255,255,0.9)',
    borderRadius: '16px',
    padding: '28px',
    border: '1px solid rgba(22,163,74,0.1)',
    boxShadow: '0 8px 32px rgba(22,163,74,0.10)',
    marginBottom: '24px',
  },
  title: {
    margin: '0 0 20px',
    color: '#14532d',
    fontSize: '1.25rem',
    fontWeight: 700,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: window.innerWidth < 600 ? '1fr' : '1fr 1fr',
    gap: '16px',
  },
  fieldFull: {
    gridColumn: '1 / -1',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    color: '#14532d',
    fontWeight: 600,
    fontSize: '0.9rem',
  },
  input: {
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid rgba(22,163,74,0.15)',
    width: '100%',
    fontFamily: 'Poppins, sans-serif',
    fontSize: '0.95rem',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  },
  textarea: {
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid rgba(22,163,74,0.15)',
    width: '100%',
    fontFamily: 'Poppins, sans-serif',
    fontSize: '0.95rem',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
    minHeight: '90px',
    resize: 'vertical',
  },
  btnRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '8px',
    gridColumn: '1 / -1',
  },
  saveBtn: {
    background: 'linear-gradient(135deg, #166534, #22c55e)',
    color: '#fff',
    padding: '14px 28px',
    borderRadius: '12px',
    fontWeight: 700,
    fontSize: '1rem',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontFamily: 'Poppins, sans-serif',
  },
  cancelBtn: {
    background: 'transparent',
    border: '1px solid #166534',
    color: '#166534',
    padding: '14px 28px',
    borderRadius: '12px',
    fontWeight: 700,
    fontSize: '1rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontFamily: 'Poppins, sans-serif',
  },
  editBtn: {
    background: '#166534',
    color: '#fff',
    padding: '6px 14px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '0.85rem',
    fontFamily: 'Poppins, sans-serif',
  },
  deleteBtn: {
    background: '#ef4444',
    color: '#fff',
    padding: '6px 14px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '0.85rem',
    fontFamily: 'Poppins, sans-serif',
  },
};

// ─── FarmerProducts ──────────────────────────────────────────────────
const FarmerProducts = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({ ...INITIAL_FORM });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await farmerAPI.getProducts();
      const data = response.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (error) {
      toast.error('Failed to load products');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFocus = (e) => {
    e.target.style.borderColor = '#22c55e';
  };

  const handleBlur = (e) => {
    e.target.style.borderColor = 'rgba(22,163,74,0.15)';
  };

  const openAddForm = () => {
    setShowForm(true);
    setEditingProduct(null);
    setFormData({ ...INITIAL_FORM });
  };

  const openEditForm = (product) => {
    setShowForm(true);
    setEditingProduct(product);
    setFormData({
      name: product.name || '',
      description: product.description || '',
      category: product.category || '',
      price: product.price || '',
      quantity: product.quantity || '',
      unit: product.unit || '',
      location: product.location || '',
      discount: product.discount || product.discount_percent || '',
    });
  };

  const handleSave = async () => {
    if (!formData.name || !formData.price || !formData.quantity) {
      toast.error('Please fill in name, price, and quantity');
      return;
    }

    try {
      if (editingProduct) {
        await farmerAPI.updateProduct(editingProduct._id || editingProduct.id, formData);
        toast.success('Product updated successfully!');
      } else {
        await farmerAPI.createProduct(formData);
        toast.success('Product created successfully!');
      }
      setShowForm(false);
      setEditingProduct(null);
      setFormData({ ...INITIAL_FORM });
      fetchProducts();
    } catch (error) {
      toast.error(editingProduct ? 'Failed to update product' : 'Failed to create product');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await farmerAPI.deleteProduct(id);
      toast.success('Product deleted successfully!');
      fetchProducts();
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingProduct(null);
    setFormData({ ...INITIAL_FORM });
  };

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h2>My Products</h2>
        <button className="btn-primary" onClick={openAddForm}>
          <FiPlus /> Add Product
        </button>
      </div>

      {/* ── Add / Edit Form ── */}
      {showForm && (
        <div style={formStyles.container}>
          <h3 style={formStyles.title}>
            {editingProduct ? 'Edit Product' : 'Add New Product'}
          </h3>

          <div style={formStyles.grid}>
            {/* Name */}
            <div>
              <label style={formStyles.label}>Name</label>
              <input
                name="name"
                value={formData.name}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="Product name"
                style={formStyles.input}
              />
            </div>

            {/* Category */}
            <div>
              <label style={formStyles.label}>Category</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                style={formStyles.input}
              >
                <option value="">Select Category</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Description (full width) */}
            <div style={formStyles.fieldFull}>
              <label style={formStyles.label}>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="Describe your product"
                style={formStyles.textarea}
              />
            </div>

            {/* Price */}
            <div>
              <label style={formStyles.label}>Price (₹)</label>
              <input
                name="price"
                type="number"
                value={formData.price}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="0.00"
                style={formStyles.input}
              />
            </div>

            {/* Quantity */}
            <div>
              <label style={formStyles.label}>Quantity</label>
              <input
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="0"
                style={formStyles.input}
              />
            </div>

            {/* Unit */}
            <div>
              <label style={formStyles.label}>Unit</label>
              <select
                name="unit"
                value={formData.unit}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                style={formStyles.input}
              >
                <option value="">Select Unit</option>
                {UNITS.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>

            {/* Location */}
            <div>
              <label style={formStyles.label}>Location</label>
              <input
                name="location"
                value={formData.location}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="e.g. Pune, Maharashtra"
                style={formStyles.input}
              />
            </div>

            {/* Discount */}
            <div>
              <label style={formStyles.label}>Discount (%)</label>
              <input
                name="discount"
                type="number"
                min="0"
                max="90"
                value={formData.discount}
                onChange={handleChange}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="0"
                style={formStyles.input}
              />
            </div>

            {/* Action buttons */}
            <div style={formStyles.btnRow}>
              <button style={formStyles.saveBtn} onClick={handleSave}>
                <FiSave /> Save Product
              </button>
              <button style={formStyles.cancelBtn} onClick={handleCancel}>
                <FiX /> Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Product Cards ── */}
      <div className="products-grid">
        {loading ? (
          <div className="empty-state"><p>Loading products…</p></div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <p>No products yet. Start by adding your first product!</p>
          </div>
        ) : (
          products.map((product) => (
            <div key={product._id || product.id} className="product-card" style={{ overflow: 'hidden' }}>
              {/* Product Image */}
              <div style={{ width: '100%', height: '140px', overflow: 'hidden', borderRadius: '12px 12px 0 0', marginBottom: '10px' }}>
                <img
                  src={getProductImage(product)}
                  alt={product.name}
                  onError={(e) => { e.target.src = PLACEHOLDER_IMG; }}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
              <div className="product-info">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <h3 style={{ margin: 0 }}>{product.name}</h3>
                  <span style={{
                    padding: '3px 10px',
                    borderRadius: '20px',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    background: product.status === 'approved' ? 'rgba(34,197,94,0.15)' : product.status === 'rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                    color: product.status === 'approved' ? '#15803d' : product.status === 'rejected' ? '#dc2626' : '#d97706',
                    border: `1px solid ${product.status === 'approved' ? '#22c55e33' : product.status === 'rejected' ? '#ef444433' : '#f59e0b33'}`,
                  }}>
                    {product.status || 'pending'}
                  </span>
                </div>
                <p className="price">₹{product.price}/{product.unit || 'kg'}</p>
                {(product.discount || product.discount_percent) > 0 && (
                  <p style={{
                    margin: '4px 0', fontSize: '0.85rem', fontWeight: 700,
                    color: '#fff', background: 'linear-gradient(135deg, #ef4444, #f97316)',
                    display: 'inline-block', padding: '3px 12px', borderRadius: '20px',
                    animation: 'discountPulse 2s infinite',
                  }}>
                    🔥 {product.discount || product.discount_percent}% OFF
                  </p>
                )}
                <p className="stock">
                  Qty: {product.quantity} {product.unit}
                </p>
                {product.description && (
                  <p style={{ fontSize: '0.82rem', color: '#666', margin: '4px 0', lineHeight: '1.4' }}>
                    {product.description.substring(0, 60)}{product.description.length > 60 ? '…' : ''}
                  </p>
                )}
                <p style={{ fontSize: '0.82rem', color: '#888', margin: '2px 0' }}>
                  📍 {product.location || 'N/A'} · 🏷️ {product.category}
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                  <button style={formStyles.editBtn} onClick={() => openEditForm(product)}>
                    <FiEdit2 /> Edit
                  </button>
                  <button
                    style={formStyles.deleteBtn}
                    onClick={() => handleDelete(product._id || product.id)}
                  >
                    <FiTrash2 /> Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ─── FarmerOrders ────────────────────────────────────────────────────
const FarmerOrders = () => {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await farmerAPI.getOrders();
      const data = response.data;
      setOrders(Array.isArray(data) ? data : data.orders || []);
    } catch (error) {
      setOrders([]);
    }
  };

  return (
    <div className="dashboard-section">
      <h2>📦 Orders</h2>
      <div className="orders-list">
        {!orders || orders.length === 0 ? (
          <div className="empty-state">
            <p>No orders received yet.</p>
          </div>
        ) : (
          orders.map((order) => (
            <div key={order._id || order.id} style={{
              background: 'rgba(255,255,255,0.95)',
              borderRadius: '16px',
              border: '1px solid rgba(22,163,74,0.1)',
              padding: '20px',
              marginBottom: '16px',
              boxShadow: '0 4px 16px rgba(22,101,52,0.06)',
            }}>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h4 style={{ margin: 0, color: '#14532d' }}>Order #{order._id || order.id}</h4>
                <span className={`status-badge ${order.status}`}>{order.status}</span>
              </div>
              
              {/* Product & Amount */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div style={{ background: '#f0fdf4', padding: '10px 14px', borderRadius: '10px' }}>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: '#888', textTransform: 'uppercase' }}>Product</p>
                  <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d' }}>{order.product_name || 'N/A'}</p>
                </div>
                <div style={{ background: '#f0fdf4', padding: '10px 14px', borderRadius: '10px' }}>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: '#888', textTransform: 'uppercase' }}>Amount</p>
                  <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d' }}>₹{order.total || order.total_price || 0}</p>
                </div>
              </div>

              {/* Shipping Info */}
              <div style={{
                background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
                borderRadius: '12px',
                padding: '14px 16px',
                border: '1px solid rgba(22,163,74,0.1)',
              }}>
                <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#166534', fontSize: '0.85rem' }}>📦 Shipping Details</p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>
                    <p style={{ margin: 0, fontSize: '0.75rem', color: '#888' }}>Buyer Name</p>
                    <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                      {order.buyer_name || 'N/A'} {order.buyer_last_name || ''}
                    </p>
                  </div>
                  <div>
                    <p style={{ margin: 0, fontSize: '0.75rem', color: '#888' }}>Phone</p>
                    <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                      📞 {order.buyer_phone || 'N/A'}
                    </p>
                  </div>
                  <div style={{ gridColumn: '1/-1' }}>
                    <p style={{ margin: 0, fontSize: '0.75rem', color: '#888' }}>Delivery Address</p>
                    <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                      📍 {[order.buyer_address, order.buyer_city, order.buyer_state].filter(Boolean).join(', ') || 'Not provided'}
                      {order.buyer_pincode && <span style={{ marginLeft: 6, background: '#166534', color: '#fff', padding: '2px 8px', borderRadius: '6px', fontSize: '0.75rem' }}>PIN: {order.buyer_pincode}</span>}
                    </p>
                  </div>
                  {order.buyer_email && (
                    <div style={{ gridColumn: '1/-1' }}>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#888' }}>Email</p>
                      <p style={{ margin: '1px 0 0', color: '#14532d', fontSize: '0.85rem' }}>✉️ {order.buyer_email}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ─── FarmerEarnings ──────────────────────────────────────────────────
const FarmerEarnings = () => {
  const [earnings, setEarnings] = useState(null);
  const [recentSales, setRecentSales] = useState([]);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchEarnings();
  }, []);

  const fetchEarnings = async () => {
    try {
      const response = await farmerAPI.getEarnings();
      const data = response.data || {};
      setEarnings({
        total: data.total || data.total_earnings || 0,
        thisMonth: data.thisMonth || 0,
        today: data.today || 0,
        totalSales: data.total_sales || 0,
        pending: data.pending || 0,
      });
      setRecentSales(data.recent_sales || []);
    } catch (error) {
      toast.error('Failed to load earnings');
      setEarnings({ total: 0, thisMonth: 0, today: 0, totalSales: 0, pending: 0 });
    }
  };

  const viewReceipt = async (receiptId) => {
    try {
      const res = await paymentsAPI.getReceipt(receiptId);
      setSelectedReceipt(res.data.receipt || res.data);
    } catch (e) {
      toast.error('Failed to load receipt');
    }
  };

  return (
    <div className="dashboard-section">
      <h2>💰 Earnings Dashboard</h2>
      {earnings && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="icon"><FiDollarSign /></div>
              <div className="stat-content">
                <p>Total Earnings</p>
                <h3>₹{earnings.total}</h3>
              </div>
            </div>
            <div className="stat-card">
              <div className="icon"><FiTrendingUp /></div>
              <div className="stat-content">
                <p>This Month</p>
                <h3>₹{earnings.thisMonth}</h3>
              </div>
            </div>
            <div className="stat-card">
              <div className="icon">📅</div>
              <div className="stat-content">
                <p>Today</p>
                <h3>₹{earnings.today}</h3>
              </div>
            </div>
            <div className="stat-card">
              <div className="icon">🧾</div>
              <div className="stat-content">
                <p>Total Sales</p>
                <h3>{earnings.totalSales}</h3>
              </div>
            </div>
          </div>

          {/* Recent Sales */}
          <div style={{ marginTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, color: '#14532d' }}>Recent Sales</h3>
              <button onClick={() => navigate('/farmer/direct-sale')} style={{
                background: 'linear-gradient(135deg,#166534,#22c55e)', color: '#fff', border: 'none',
                padding: '8px 18px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif', fontSize: '0.85rem',
              }}><FiPlus /> New Sale</button>
            </div>

            {recentSales.length === 0 ? (
              <div style={{
                textAlign: 'center', padding: '30px', background: 'rgba(255,255,255,0.9)',
                borderRadius: '12px', border: '1px solid rgba(22,163,74,0.08)',
              }}>
                <FiDollarSign size={40} color="#ccc" />
                <p style={{ color: '#999', marginTop: '8px' }}>No sales recorded yet</p>
                <button onClick={() => navigate('/farmer/direct-sale')} style={{
                  marginTop: '12px', background: '#166534', color: '#fff', border: 'none',
                  padding: '10px 22px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                }}>Create Direct Sale</button>
              </div>
            ) : (
              <div className="orders-list">
                {recentSales.map((sale, idx) => (
                  <div key={idx} style={{
                    background: 'rgba(255,255,255,0.95)', borderRadius: '12px', padding: '14px 18px',
                    marginBottom: '8px', border: '1px solid rgba(22,163,74,0.08)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    boxShadow: '0 2px 6px rgba(22,101,52,0.04)',
                  }}>
                    <div>
                      <h4 style={{ margin: 0, color: '#14532d', fontSize: '0.95rem' }}>{sale.receipt_id}</h4>
                      <p style={{ margin: '2px 0', fontSize: '0.8rem', color: '#888' }}>
                        {sale.buyer_name || 'Walk-in'} • {sale.payment_type?.toUpperCase()}
                        {sale.created_at && ` • ${new Date(sale.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`}
                      </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 700, color: '#166534', fontSize: '1rem' }}>₹{sale.grand_total}</span>
                      <button onClick={() => viewReceipt(sale.receipt_id)} style={{
                        background: '#f0fdf4', border: '1px solid #16a34a', color: '#166534',
                        borderRadius: '6px', padding: '4px 10px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                      }}><FiEye size={12} /> View</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {selectedReceipt && <ReceiptViewer receipt={selectedReceipt} onClose={() => setSelectedReceipt(null)} />}
    </div>
  );
};

// ─── DirectSale ──────────────────────────────────────────────────────
const PAYMENT_TYPES = ['cash', 'upi', 'card', 'online'];

const DirectSale = () => {
  const [products, setProducts] = useState([]);
  const [items, setItems] = useState([{ product_id: '', product_name: '', quantity: '', price_per_kg: '', quality: 'Standard' }]);
  const [paymentType, setPaymentType] = useState('cash');
  const [buyerInfo, setBuyerInfo] = useState({ buyer_name: '', buyer_phone: '', buyer_email: '' });
  const [discount, setDiscount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState(null);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const res = await farmerAPI.getProducts(1, 100);
      const data = res.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (e) {
      setProducts([]);
    }
  };

  const addItem = () => setItems([...items, { product_id: '', product_name: '', quantity: '', price_per_kg: '', quality: 'Standard' }]);
  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const updateItem = (idx, field, value) => {
    const updated = [...items];
    updated[idx][field] = value;
    if (field === 'product_id') {
      const p = products.find(p => String(p.id) === String(value));
      if (p) { updated[idx].product_name = p.name; updated[idx].price_per_kg = p.price; }
    }
    setItems(updated);
  };

  const subtotal = items.reduce((sum, i) => sum + (parseFloat(i.quantity || 0) * parseFloat(i.price_per_kg || 0)), 0);
  const total = subtotal - parseFloat(discount || 0);

  const handleSubmit = async () => {
    if (!items[0]?.product_name || !items[0]?.quantity) {
      toast.error('Please add at least one item with quantity');
      return;
    }
    setSubmitting(true);
    try {
      const res = await paymentsAPI.directSale({
        items: items.filter(i => i.product_name && i.quantity).map(i => ({
          product_id: parseInt(i.product_id) || 0,
          product_name: i.product_name,
          quantity: parseFloat(i.quantity),
          price_per_kg: parseFloat(i.price_per_kg),
          quality: i.quality,
        })),
        payment_type: paymentType,
        buyer_name: buyerInfo.buyer_name,
        buyer_phone: buyerInfo.buyer_phone,
        buyer_email: buyerInfo.buyer_email,
        discount: parseFloat(discount || 0),
      });
      toast.success('Sale recorded! Receipt generated.', { icon: '✅' });
      setReceipt(res.data.receipt || res.data);
      setItems([{ product_id: '', product_name: '', quantity: '', price_per_kg: '', quality: 'Standard' }]);
      setBuyerInfo({ buyer_name: '', buyer_phone: '', buyer_email: '' });
      setDiscount(0);
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to process sale');
    } finally {
      setSubmitting(false);
    }
  };

  const fStyle = {
    container: { background: 'rgba(255,255,255,0.95)', borderRadius: '14px', padding: '24px', border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 4px 16px rgba(22,101,52,0.06)' },
    label: { display: 'block', marginBottom: '6px', color: '#14532d', fontWeight: 600, fontSize: '0.85rem' },
    input: { padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(22,163,74,0.15)', width: '100%', fontFamily: 'Poppins, sans-serif', fontSize: '0.9rem', boxSizing: 'border-box' },
    select: { padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(22,163,74,0.15)', width: '100%', fontFamily: 'Poppins, sans-serif', fontSize: '0.9rem', background: '#fff', boxSizing: 'border-box' },
    grid: { display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr auto', gap: '10px', alignItems: 'end', marginBottom: '10px' },
    btn: { background: 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', padding: '12px 28px', borderRadius: '10px', fontWeight: 700, border: 'none', cursor: 'pointer', fontSize: '1rem', fontFamily: 'Poppins, sans-serif' },
  };

  return (
    <div className="dashboard-section">
      <h2>🏪 Direct Farm Sale</h2>
      <div style={fStyle.container}>
        {/* Buyer Info */}
        <h3 style={{ color: '#14532d', marginBottom: '14px' }}>Buyer Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
          <div>
            <label style={fStyle.label}>Buyer Name</label>
            <input style={fStyle.input} placeholder="Name" value={buyerInfo.buyer_name} onChange={e => setBuyerInfo(f => ({ ...f, buyer_name: e.target.value }))} />
          </div>
          <div>
            <label style={fStyle.label}>Phone</label>
            <input style={fStyle.input} placeholder="Phone number" value={buyerInfo.buyer_phone} onChange={e => setBuyerInfo(f => ({ ...f, buyer_phone: e.target.value }))} />
          </div>
          <div>
            <label style={fStyle.label}>Email</label>
            <input style={fStyle.input} placeholder="Email (optional)" value={buyerInfo.buyer_email} onChange={e => setBuyerInfo(f => ({ ...f, buyer_email: e.target.value }))} />
          </div>
        </div>

        {/* Items */}
        <h3 style={{ color: '#14532d', marginBottom: '14px' }}>Products</h3>
        {items.map((item, idx) => (
          <div key={idx} style={fStyle.grid}>
            <div>
              <label style={fStyle.label}>Product</label>
              <select style={fStyle.select} value={item.product_id} onChange={e => updateItem(idx, 'product_id', e.target.value)}>
                <option value="">Select product</option>
                {products.map(p => <option key={p.id} value={p.id}>{p.name} (₹{p.price}/{p.unit})</option>)}
              </select>
            </div>
            <div>
              <label style={fStyle.label}>Qty (KG)</label>
              <input style={fStyle.input} type="number" placeholder="0" value={item.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)} />
            </div>
            <div>
              <label style={fStyle.label}>Price/KG</label>
              <input style={fStyle.input} type="number" placeholder="0" value={item.price_per_kg} onChange={e => updateItem(idx, 'price_per_kg', e.target.value)} />
            </div>
            <div>
              <label style={fStyle.label}>Quality</label>
              <select style={fStyle.select} value={item.quality} onChange={e => updateItem(idx, 'quality', e.target.value)}>
                <option value="Standard">Standard</option>
                <option value="Premium">Premium</option>
                <option value="Organic">Organic</option>
              </select>
            </div>
            <button onClick={() => removeItem(idx)} style={{ background: '#fee2e2', color: '#dc2626', border: 'none', borderRadius: '8px', padding: '10px', cursor: 'pointer', marginTop: '18px' }}><FiTrash2 /></button>
          </div>
        ))}
        <button onClick={addItem} style={{ ...fStyle.btn, background: '#f0fdf4', color: '#166534', border: '1px solid #166534', padding: '8px 16px', fontSize: '0.85rem', marginBottom: '20px' }}><FiPlus /> Add Item</button>

        {/* Payment */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
          <div>
            <label style={fStyle.label}>Payment Type</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {PAYMENT_TYPES.map(t => (
                <button key={t} onClick={() => setPaymentType(t)} style={{
                  padding: '8px 16px', borderRadius: '8px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
                  fontFamily: 'Poppins, sans-serif',
                  background: paymentType === t ? 'linear-gradient(135deg,#166534,#22c55e)' : '#f0fdf4',
                  color: paymentType === t ? '#fff' : '#166534',
                  border: paymentType === t ? 'none' : '1px solid #16653466',
                }}>{t.toUpperCase()}</button>
              ))}
            </div>
          </div>
          <div>
            <label style={fStyle.label}>Discount (₹)</label>
            <input style={fStyle.input} type="number" value={discount} onChange={e => setDiscount(e.target.value)} placeholder="0" />
          </div>
        </div>

        {/* Summary */}
        <div style={{ background: '#f0fdf4', borderRadius: '10px', padding: '16px', margin: '20px 0', textAlign: 'right' }}>
          <p style={{ margin: '4px 0', color: '#555' }}>Subtotal: ₹{subtotal.toFixed(2)}</p>
          {discount > 0 && <p style={{ margin: '4px 0', color: '#16a34a' }}>Discount: -₹{parseFloat(discount).toFixed(2)}</p>}
          <p style={{ margin: '4px 0', fontSize: '1.3rem', fontWeight: 700, color: '#166534' }}>Total: ₹{total.toFixed(2)}</p>
        </div>

        <button style={fStyle.btn} onClick={handleSubmit} disabled={submitting}>
          {submitting ? 'Processing...' : '✅ Complete Sale & Generate Receipt'}
        </button>
      </div>

      {receipt && <ReceiptViewer receipt={receipt} onClose={() => {
        setReceipt(null);
        // Navigate to sales history so user can always find receipts
        window.location.href = '/farmer/earnings';
      }} />}
    </div>
  );
};

// ─── SalesHistory ────────────────────────────────────────────────────
const SalesHistory = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState(null);

  useEffect(() => { fetchSales(); }, []);

  const fetchSales = async () => {
    try {
      const res = await paymentsAPI.getSalesHistory();
      const data = res.data;
      setReceipts(Array.isArray(data) ? data : data.sales || data.receipts || []);
    } catch (e) { setReceipts([]); }
    finally { setLoading(false); }
  };

  const viewReceipt = async (receiptId) => {
    try {
      const res = await paymentsAPI.getReceipt(receiptId);
      setSelectedReceipt(res.data.receipt || res.data);
    } catch (e) { toast.error('Failed to load receipt'); }
  };

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>📋 Sales History</h2>
      {receipts.length === 0 ? (
        <div className="empty-state"><FiPackage size={48} /><h3>No sales recorded</h3></div>
      ) : (
        <div className="orders-list">
          {receipts.map(r => (
            <div key={r.id || r.receipt_id} style={{
              background: 'rgba(255,255,255,0.95)', borderRadius: '12px', padding: '16px', marginBottom: '10px',
              border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 2px 8px rgba(22,101,52,0.05)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ margin: 0, color: '#14532d' }}>{r.receipt_id}</h4>
                  <p style={{ margin: '4px 0', fontSize: '0.82rem', color: '#888' }}>
                    {r.created_at ? new Date(r.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''}
                    {' • '}{r.buyer_name || 'Walk-in Customer'} • {r.payment_type?.toUpperCase()}
                  </p>
                </div>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#166534' }}>₹{r.grand_total}</p>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button onClick={() => viewReceipt(r.receipt_id)} style={{
                  display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', borderRadius: '8px',
                  border: '1px solid #16a34a', background: '#f0fdf4', color: '#166534', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                }}><FiEye /> View</button>
                <button onClick={() => viewReceipt(r.receipt_id)} style={{
                  display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', borderRadius: '8px',
                  border: 'none', background: 'linear-gradient(135deg,#166534,#22c55e)', color: '#fff', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                }}><FiDownload /> Download</button>
              </div>
            </div>
          ))}
        </div>
      )}
      {selectedReceipt && <ReceiptViewer receipt={selectedReceipt} onClose={() => setSelectedReceipt(null)} />}
    </div>
  );
};

// ─── FarmerProfile ───────────────────────────────────────────────────
const FarmerProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    location: '',
    upi_id: '',
    bank_name: '',
    bank_account: '',
    experience_years: '',
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await farmerAPI.getProfile();
      const data = res.data?.farmer || res.data;
      setProfile(data);
      setFormData({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        phone: data.phone || '',
        email: data.email || '',
        location: data.location || '',
        upi_id: data.upi_id || '',
        bank_name: data.bank_name || '',
        bank_account: '',
        experience_years: data.experience_years || '',
      });
    } catch (error) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...formData };
      // Don't send empty bank_account (it's masked)
      if (!payload.bank_account) delete payload.bank_account;
      if (payload.experience_years) payload.experience_years = parseInt(payload.experience_years);
      
      await farmerAPI.updateProfile(payload);
      toast.success('Profile updated successfully!');
      fetchProfile();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>👤 My Profile</h2>
      <div style={formStyles.container}>
        <h3 style={formStyles.title}>Edit Profile Information</h3>
        <div style={formStyles.grid}>
          <div>
            <label style={formStyles.label}>First Name</label>
            <input
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="First Name"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Last Name</label>
            <input
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Last Name"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Phone</label>
            <input
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="Phone Number"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Email</label>
            <input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Email Address"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Location</label>
            <input
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g. Hyderabad, Telangana"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Experience (years)</label>
            <input
              name="experience_years"
              type="number"
              value={formData.experience_years}
              onChange={handleChange}
              placeholder="Years of farming"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>UPI ID</label>
            <input
              name="upi_id"
              value={formData.upi_id}
              onChange={handleChange}
              placeholder="yourname@upi"
              style={formStyles.input}
            />
          </div>
          <div>
            <label style={formStyles.label}>Bank Name</label>
            <input
              name="bank_name"
              value={formData.bank_name}
              onChange={handleChange}
              placeholder="e.g. State Bank of India"
              style={formStyles.input}
            />
          </div>
          <div style={formStyles.fieldFull}>
            <label style={formStyles.label}>Bank Account Number</label>
            <input
              name="bank_account"
              value={formData.bank_account}
              onChange={handleChange}
              placeholder={profile?.bank_account ? `Current: ${profile.bank_account}` : 'Enter account number'}
              style={formStyles.input}
            />
          </div>

          {/* Info badges */}
          <div style={formStyles.fieldFull}>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
              {profile?.is_verified && (
                <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600, background: '#dcfce7', color: '#15803d', border: '1px solid #22c55e33' }}>
                  ✅ Verified Farmer
                </span>
              )}
              {profile?.aadhar_verified && (
                <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600, background: '#dbeafe', color: '#1d4ed8', border: '1px solid #3b82f633' }}>
                  🪪 Aadhaar Verified
                </span>
              )}
              {profile?.created_at && (
                <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600, background: '#f0fdf4', color: '#166534', border: '1px solid #16653433' }}>
                  📅 Member since {new Date(profile.created_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
                </span>
              )}
            </div>
          </div>

          <div style={formStyles.btnRow}>
            <button style={formStyles.saveBtn} onClick={handleSave} disabled={saving}>
              <FiSave /> {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── WeatherWidget (with geolocation) ────────────────────────────────
const WeatherWidget = () => {
  const [weather, setWeather] = useState(null);
  const [city, setCity] = useState('');
  const [locationLoaded, setLocationLoaded] = useState(false);

  useEffect(() => {
    // Try browser geolocation first
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          fetchWeatherByCoords(pos.coords.latitude, pos.coords.longitude);
          setLocationLoaded(true);
        },
        () => {
          // Fallback to default city
          setCity('Hyderabad');
          setLocationLoaded(true);
        },
        { timeout: 5000 }
      );
    } else {
      setCity('Hyderabad');
      setLocationLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (city && locationLoaded) {
      fetchWeatherByCity(city);
    }
    const interval = setInterval(() => {
      if (city) fetchWeatherByCity(city);
    }, 600000); // Refresh every 10 minutes
    return () => clearInterval(interval);
  }, [city, locationLoaded]);

  const fetchWeatherByCoords = async (lat, lon) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`http://localhost:8000/api/weather?lat=${lat}&lon=${lon}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.weather) {
        setWeather(data.weather);
        setCity(data.weather.city || '');
      }
    } catch (e) { console.error('Weather fetch failed', e); }
  };

  const fetchWeatherByCity = async (c) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`http://localhost:8000/api/weather?city=${c}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.weather) setWeather(data.weather);
    } catch (e) { console.error('Weather fetch failed', e); }
  };

  const getWeatherEmoji = (main) => {
    const map = { Clear: '☀️', Clouds: '☁️', Rain: '🌧️', Drizzle: '🌦️', Thunderstorm: '⛈️', Snow: '❄️', Mist: '🌫️', Haze: '🌫️', Fog: '🌫️' };
    return map[main] || '🌤️';
  };

  if (!weather) return (
    <div style={{ background: 'linear-gradient(135deg, #166534, #14532d)', borderRadius: '16px', padding: '16px', color: '#fff', marginBottom: '16px', textAlign: 'center', opacity: 0.7, fontSize: '0.9rem' }}>
      📍 Detecting your location for weather...
    </div>
  );

  const isMobileView = window.innerWidth < 600;

  return (
    <div style={{
      background: 'linear-gradient(135deg, #166534, #14532d)',
      borderRadius: '16px', padding: isMobileView ? '14px' : '20px', color: '#fff',
      display: 'flex', flexDirection: isMobileView ? 'column' : 'row',
      alignItems: isMobileView ? 'flex-start' : 'center', gap: isMobileView ? '12px' : '20px',
      boxShadow: '0 8px 32px rgba(22,101,52,0.15)', marginBottom: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%' }}>
        <div style={{ fontSize: isMobileView ? '2rem' : '3rem' }}>{getWeatherEmoji(weather.main)}</div>
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: 0, fontSize: isMobileView ? '0.85rem' : '1.1rem', opacity: 0.9 }}>📍 Weather in {weather.city}</h3>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', margin: '4px 0', flexWrap: 'wrap' }}>
            <span style={{ fontSize: isMobileView ? '1.8rem' : '2.5rem', fontWeight: 800 }}>{weather.temp}°C</span>
            <span style={{ opacity: 0.8, fontSize: isMobileView ? '0.8rem' : '1rem' }}>{weather.description}</span>
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>Feels like {weather.feels_like}°C</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', gap: '4px' }}>
            <input
              value={city}
              onChange={(e) => setCity(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') fetchWeatherByCity(city); }}
              placeholder="City"
              style={{ padding: '6px 10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.15)', color: '#fff', width: isMobileView ? '70px' : '90px', fontSize: '0.8rem' }}
            />
            <button onClick={() => fetchWeatherByCity(city)} style={{
              background: 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)',
              borderRadius: '8px', color: '#fff', padding: '4px 10px', cursor: 'pointer', fontSize: '0.9rem',
              fontWeight: 700,
            }}>↻</button>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: isMobileView ? '10px' : '16px', fontSize: isMobileView ? '0.75rem' : '0.85rem', opacity: 0.85, flexWrap: 'wrap' }}>
        <span>💧 Humidity: {weather.humidity}%</span>
        <span>🌬️ Wind: {weather.wind_speed} km/h</span>
        <span>🌡️ {weather.temp_min}°-{weather.temp_max}°C</span>
      </div>
    </div>
  );
};

// ─── Floating AgriBot Button ─────────────────────────────────────────
const FloatingBotButton = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      title="🤖 Ask AgriBot"
      style={{
        position: 'fixed', bottom: '30px', right: '30px', zIndex: 1000,
        width: '64px', height: '64px', borderRadius: '50%', border: 'none',
        background: 'linear-gradient(135deg, #22c55e, #166534)',
        color: '#fff', fontSize: '1.8rem', cursor: 'pointer',
        boxShadow: '0 8px 32px rgba(34,197,94,0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'agriBotFloat 3s ease-in-out infinite',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.12)';
        e.currentTarget.style.boxShadow = '0 12px 40px rgba(34,197,94,0.5)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = '0 8px 32px rgba(34,197,94,0.35)';
      }}
    >
      🤖
    </button>
  );
};

// ─── Inject floating animation keyframe ──────────────────────────────
const injectFloatKeyframe = () => {
  if (document.getElementById('agribot-float-kf')) return;
  const s = document.createElement('style');
  s.id = 'agribot-float-kf';
  s.textContent = `@keyframes agriBotFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }`;
  document.head.appendChild(s);
};

// ─── FarmerDashboard (main) ──────────────────────────────────────────
const FarmerDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    products: 0,
    orders: 0,
    earnings: 0,
    rating: 0,
  });

  useEffect(() => {
    injectFloatKeyframe();
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [productsRes, ordersRes, earningsRes] = await Promise.all([
        farmerAPI.getProducts(1, 100),
        farmerAPI.getOrders(1, 100),
        farmerAPI.getEarnings(),
      ]);
      setStats({
        products: productsRes.data.total || (productsRes.data.products || []).length || 0,
        orders: ordersRes.data.total || (ordersRes.data.orders || []).length || 0,
        earnings: earningsRes.data.total_earnings || earningsRes.data.earnings || 0,
        rating: earningsRes.data.rating || 4.5,
      });
    } catch (error) {
      console.error('Failed to load stats', error);
      setStats({ products: 0, orders: 0, earnings: 0, rating: 0 });
    }
  };

  return (
    <div className="dashboard">
      <Routes>
        <Route
          path="/"
          element={
            <div className="dashboard-overview">
              <h1 style={{ marginTop: '8px' }}>Farmer Dashboard</h1>
              <WeatherWidget />

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="icon"><FiPackage /></div>
                  <div className="stat-content">
                    <p>Total Products</p>
                    <h3>{stats.products}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon"><FiTrendingUp /></div>
                  <div className="stat-content">
                    <p>Total Orders</p>
                    <h3>{stats.orders}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon"><FiDollarSign /></div>
                  <div className="stat-content">
                    <p>Total Earnings</p>
                    <h3>₹{stats.earnings}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon">⭐</div>
                  <div className="stat-content">
                    <p>Rating</p>
                    <h3>{stats.rating}</h3>
                  </div>
                </div>
              </div>

              <div className="quick-actions">
                <button className="action-btn" onClick={() => navigate('/farmer/products')}><FiPlus /> Add Product</button>
                <button className="action-btn" onClick={() => navigate('/farmer/orders')}><FiPackage /> View Orders</button>
                <button className="action-btn" onClick={() => navigate('/farmer/products')}><FiEdit2 /> Manage Inventory</button>
              </div>
            </div>
          }
        />
        <Route path="products" element={<FarmerProducts />} />
        <Route path="orders" element={<FarmerOrders />} />
        <Route path="direct-sale" element={<DirectSale />} />
        <Route path="sales-history" element={<SalesHistory />} />
        <Route path="earnings" element={<FarmerEarnings />} />
        <Route path="profile" element={<FarmerProfile />} />
        <Route path="agribot" element={<AgriBot />} />
      </Routes>

      {/* Floating Animated AgriBot Button */}
      <FloatingBotButton onClick={() => navigate('/farmer/agribot')} />
    </div>
  );
};

export default FarmerDashboard;

