import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { FiShoppingCart, FiSearch, FiPlus, FiMinus, FiTrash2, FiPackage, FiStar, FiMapPin, FiDownload, FiEye, FiRefreshCw, FiSave } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { buyerAPI, paymentsAPI } from '../services/api';
import ReceiptViewer from '../components/ReceiptViewer';
import '../styles/dashboard.css';

import { getProductImage, PLACEHOLDER_IMG } from '../utils/productImages';

const BuyerShop = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [addingToCart, setAddingToCart] = useState({});
  const [notifiedDiscounts, setNotifiedDiscounts] = useState(new Set());
  const navigate = useNavigate();

  // 🔔 Play notification sound using Web Audio API
  const playNotificationSound = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6 - pleasant chime
      notes.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = freq;
        osc.type = 'sine';
        gain.gain.setValueAtTime(0.15, ctx.currentTime + i * 0.15);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.15 + 0.5);
        osc.start(ctx.currentTime + i * 0.15);
        osc.stop(ctx.currentTime + i * 0.15 + 0.5);
      });
    } catch (e) { /* Audio not supported */ }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, []);

  // 🔔 Notify buyers about new discounts
  useEffect(() => {
    if (products.length === 0) return;
    const discounted = products.filter(p => (p.discount || p.discount_percent) > 0);
    const newDiscounts = discounted.filter(p => !notifiedDiscounts.has(p.id));
    if (newDiscounts.length > 0) {
      playNotificationSound();
      if (newDiscounts.length === 1) {
        toast(`🔥 ${newDiscounts[0].name} is ${newDiscounts[0].discount || newDiscounts[0].discount_percent}% OFF!`, {
          icon: '🎉', duration: 5000,
          style: { background: 'linear-gradient(135deg, #fef3c7, #fde68a)', border: '2px solid #f59e0b', fontWeight: 600 },
        });
      } else {
        toast(`🔥 ${newDiscounts.length} products on discount! Check them out!`, {
          icon: '🎉', duration: 5000,
          style: { background: 'linear-gradient(135deg, #fef3c7, #fde68a)', border: '2px solid #f59e0b', fontWeight: 600 },
        });
      }
      setNotifiedDiscounts(prev => {
        const next = new Set(prev);
        newDiscounts.forEach(p => next.add(p.id));
        return next;
      });
    }
  }, [products, notifiedDiscounts, playNotificationSound]);

  const fetchProducts = async (search = '') => {
    setLoading(true);
    try {
      const params = { limit: 40 };
      if (search) params.search = search;
      const response = await buyerAPI.getProducts(1, 40, search ? { search } : {});
      const data = response.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (error) {
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProducts(searchQuery);
  };

  const handleAddToCart = async (product) => {
    setAddingToCart(prev => ({ ...prev, [product.id]: true }));
    try {
      await buyerAPI.addToCart(product.id, 1);
      toast.success(`${product.name} added to cart!`, { icon: '🛒' });
    } catch (error) {
      const msg = error.response?.data?.error || error.response?.data?.message || 'Failed to add to cart';
      if (msg.includes('already')) {
        toast.success(`${product.name} is already in your cart!`, { icon: '✅' });
      } else {
        toast.error(msg);
      }
    } finally {
      setAddingToCart(prev => ({ ...prev, [product.id]: false }));
    }
  };

  const filteredProducts = products.filter(p =>
    p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="dashboard-section">
      <div className="shop-header">
        <h2>🛒 Fresh Products</h2>
        <form onSubmit={handleSearch} className="search-bar">
          <FiSearch />
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading fresh products...</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="empty-state">
          <FiPackage size={48} />
          <p>No products found</p>
        </div>
      ) : (
        <div className="products-grid">
          {filteredProducts.map(product => (
            <div key={product.id} className={`product-card-buyer ${(product.discount || product.discount_percent) > 0 ? 'discount-shimmer' : ''}`}>
              <div className="product-image">
                <img
                  src={getProductImage(product)}
                  alt={product.name}
                  onError={(e) => { e.target.src = PLACEHOLDER_IMG; }}
                />
                {product.organic && <span className="organic-badge">🌿 Organic</span>}
                {(product.discount || product.discount_percent) > 0 && (
                  <div className="discount-banner">
                    <span className="discount-text">🔥 {product.discount || product.discount_percent}% OFF</span>
                  </div>
                )}
              </div>
              <div className="product-details">
                <h3>{product.name}</h3>
                <p className="farmer-name">
                  <FiMapPin size={12} /> {product.farmer_name || product.farmerName || 'Local Farmer'}
                  {product.farmer_location && ` • ${product.farmer_location}`}
                </p>
                <div className="product-meta">
                  <span className="category-tag">{product.category}</span>
                  {product.average_rating > 0 && (
                    <span className="rating"><FiStar size={12} /> {product.average_rating}</span>
                  )}
                </div>
                <div className="product-footer">
                  <div className="price-info">
                    {(product.discount || product.discount_percent) > 0 ? (
                      <>
                        <span className="price-original">₹{product.price}</span>
                        <span className="price">₹{(product.price * (1 - (product.discount || product.discount_percent) / 100)).toFixed(0)}</span>
                      </>
                    ) : (
                      <span className="price">₹{product.price}</span>
                    )}
                    <span className="unit">/{product.unit || 'kg'}</span>
                  </div>
                  <button
                    className={`btn-add-cart ${addingToCart[product.id] ? 'adding' : ''}`}
                    onClick={() => handleAddToCart(product)}
                    disabled={addingToCart[product.id]}
                  >
                    {addingToCart[product.id] ? (
                      <span className="btn-loading">Adding...</span>
                    ) : (
                      <><FiShoppingCart size={14} /> Add</>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const BuyerCart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchCart = useCallback(async () => {
    try {
      const response = await buyerAPI.getCart();
      const data = response.data;
      setCartItems(Array.isArray(data) ? data : data.items || data.cart_items || []);
    } catch (error) {
      setCartItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return handleRemoveItem(itemId);
    try {
      await buyerAPI.updateCartItem(itemId, newQuantity);
      setCartItems(prev => prev.map(item =>
        item.id === itemId ? { ...item, quantity: newQuantity } : item
      ));
    } catch (error) {
      toast.error('Failed to update quantity');
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      await buyerAPI.removeFromCart(itemId);
      setCartItems(prev => prev.filter(item => item.id !== itemId));
      toast.success('Item removed from cart');
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  const handleCheckout = async () => {
    try {
      const amount = Math.round(total * 100); // Convert to paise
      
      // Step 1: Create Razorpay order
      const orderRes = await paymentsAPI.createOrder({
        amount: amount,
        currency: 'INR',
        receipt_id: `cart_${Date.now()}`,
        notes: { items: cartItems.length },
      });
      
      const { order_id, key_id } = orderRes.data;
      
      // Step 2: Open Razorpay checkout
      const options = {
        key: key_id,
        amount: amount,
        currency: 'INR',
        name: 'SmartFarming Market Place',
        description: `Purchase of ${cartItems.length} item(s)`,
        order_id: order_id,
        handler: async (response) => {
          try {
            // Step 3: Verify payment
            const verifyRes = await paymentsAPI.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              order_items: cartItems.map(item => ({
                product_id: item.product_id || item.id,
                product_name: item.name || item.product_name,
                quantity: item.quantity,
                price_per_kg: item.price,
                quality: item.quality || 'Standard',
              })),
              buyer_id: null, // Will be extracted from JWT
              farmer_id: cartItems[0]?.farmer_id || null,
            });
            
            toast.success('Payment successful! Receipt generated.', { icon: '🎉', duration: 4000 });
            setCartItems([]);
            navigate('/buyer/purchase-history');
          } catch (err) {
            toast.error('Payment verification failed');
          }
        },
        prefill: {
          name: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).first_name : '',
          email: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).email : '',
          contact: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).phone : '',
        },
        config: {
          display: {
            blocks: {
              upi: {
                name: 'Pay via UPI',
                instruments: [
                  { method: 'upi', flows: ['qr', 'collect', 'intent'] }
                ],
              },
              other: {
                name: 'Other Methods',
                instruments: [
                  { method: 'card' },
                  { method: 'netbanking' },
                  { method: 'wallet' },
                ],
              },
            },
            sequence: ['block.upi', 'block.other'],
            preferences: { show_default_blocks: true },
          },
        },
        theme: { color: '#166534' },
        notes: {
          order_type: 'online_purchase',
          delivery: 'standard',
        },
      };
      
      // Load Razorpay script if not loaded
      if (!window.Razorpay) {
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = () => { new window.Razorpay(options).open(); };
        document.body.appendChild(script);
      } else {
        new window.Razorpay(options).open();
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Checkout failed');
    }
  };

  const total = cartItems.reduce((sum, item) => sum + ((item.price || 0) * (item.quantity || 1)), 0);

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>🛒 Shopping Cart ({cartItems.length} items)</h2>

      {cartItems.length === 0 ? (
        <div className="empty-state">
          <FiShoppingCart size={48} />
          <h3>Your cart is empty</h3>
          <p>Browse products and add items to your cart</p>
          <button className="btn-primary" onClick={() => navigate('/buyer/shop')}>
            Browse Products
          </button>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {cartItems.map(item => (
              <div key={item.id} className="cart-item">
                <img
                  src={getProductImage(item)}
                  alt={item.name || item.product_name}
                  onError={(e) => { e.target.src = PLACEHOLDER_IMG; }}
                />
                <div className="item-details">
                  <h4>{item.name || item.product_name}</h4>
                  <p className="item-price">₹{item.price} per {item.unit || 'kg'}</p>
                </div>
                <div className="qty-controls">
                  <button onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}>
                    <FiMinus size={14} />
                  </button>
                  <span>{item.quantity}</span>
                  <button onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}>
                    <FiPlus size={14} />
                  </button>
                </div>
                <span className="item-total">₹{(item.price * item.quantity).toFixed(2)}</span>
                <button className="remove-btn" onClick={() => handleRemoveItem(item.id)}>
                  <FiTrash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <div className="summary-row">
              <span>Subtotal</span>
              <span>₹{total.toFixed(2)}</span>
            </div>
            <div className="summary-row total">
              <span>Total</span>
              <span>₹{total.toFixed(2)}</span>
            </div>
            <button className="btn-checkout" onClick={handleCheckout}>
              Proceed to Checkout — ₹{total.toFixed(2)}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

const BuyerOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await buyerAPI.getOrders();
      const data = response.data;
      setOrders(Array.isArray(data) ? data : data.orders || []);
    } catch (error) {
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f59e0b',
      confirmed: '#3b82f6',
      shipped: '#8b5cf6',
      delivered: '#22c55e',
      cancelled: '#ef4444',
    };
    return colors[status] || '#6b7280';
  };

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>📦 My Orders</h2>
      {orders.length === 0 ? (
        <div className="empty-state">
          <FiPackage size={48} />
          <h3>No orders yet</h3>
          <p>Your orders will appear here</p>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map(order => (
            <div key={order.id} className="order-item">
              <div className="order-header">
                <h4>Order #{order.id}</h4>
                <span
                  className="status-badge"
                  style={{ background: getStatusColor(order.status), color: '#fff' }}
                >
                  {order.status}
                </span>
              </div>
              <div className="order-body">
                <p>Total: <strong>₹{order.total_amount || order.total || 0}</strong></p>
                <p className="order-date">
                  {order.created_at ? new Date(order.created_at).toLocaleDateString('en-IN', {
                    day: 'numeric', month: 'short', year: 'numeric'
                  }) : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Purchase History with Receipt Download ─────────────────────────────
const PurchaseHistory = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await paymentsAPI.getPurchaseHistory();
      const data = res.data;
      setReceipts(Array.isArray(data) ? data : data.receipts || []);
    } catch (e) {
      setReceipts([]);
    } finally {
      setLoading(false);
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

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>🧾 Purchase History</h2>
      {receipts.length === 0 ? (
        <div className="empty-state">
          <FiPackage size={48} />
          <h3>No purchases yet</h3>
          <p>Your purchase receipts will appear here</p>
        </div>
      ) : (
        <div className="orders-list">
          {receipts.map(r => (
            <div key={r.id || r.receipt_id} style={{
              background: 'rgba(255,255,255,0.95)', borderRadius: '12px', padding: '16px',
              marginBottom: '10px', border: '1px solid rgba(22,163,74,0.08)',
              boxShadow: '0 2px 8px rgba(22,101,52,0.05)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ margin: 0, color: '#14532d' }}>{r.receipt_id}</h4>
                  <p style={{ margin: '4px 0', fontSize: '0.82rem', color: '#888' }}>
                    {r.created_at ? new Date(r.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : ''}
                  </p>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#555' }}>
                    {r.farmer_name && `From: ${r.farmer_name}`} • {r.payment_type?.toUpperCase()}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#166534' }}>₹{r.grand_total}</p>
                  <span style={{
                    padding: '2px 10px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 600,
                    background: r.payment_status === 'completed' ? '#dcfce7' : '#fef3c7',
                    color: r.payment_status === 'completed' ? '#15803d' : '#d97706',
                  }}>{r.payment_status}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                <button onClick={() => viewReceipt(r.receipt_id)} style={{
                  display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 14px',
                  borderRadius: '8px', border: '1px solid #16a34a', background: '#f0fdf4',
                  color: '#166534', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                }}><FiEye /> View Receipt</button>
                <button onClick={() => viewReceipt(r.receipt_id)} style={{
                  display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 14px',
                  borderRadius: '8px', border: 'none', background: 'linear-gradient(135deg,#166534,#22c55e)',
                  color: '#fff', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                }}><FiDownload /> Download</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedReceipt && (
        <ReceiptViewer receipt={selectedReceipt} onClose={() => setSelectedReceipt(null)} />
      )}
    </div>
  );
};

// ─── BuyerProfile ────────────────────────────────────────────────────
const profileStyles = {
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
    gridTemplateColumns: '1fr 1fr',
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
  btnRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '8px',
    gridColumn: '1 / -1',
  },
};

const BuyerProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    location: '',
    city: '',
    state: '',
    pincode: '',
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await buyerAPI.getProfile();
      const data = res.data?.profile || res.data;
      setProfile(data);
      setFormData({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        phone: data.phone || '',
        email: data.email || '',
        location: data.location || '',
        city: data.city || '',
        state: data.state || '',
        pincode: data.pincode || '',
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
      await buyerAPI.updateProfile(formData);
      toast.success('Profile updated successfully!');
      fetchProfile();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>👤 My Profile</h2>
      <div style={profileStyles.container}>
        <h3 style={profileStyles.title}>Edit Profile Information</h3>
        <div style={profileStyles.grid}>
          <div>
            <label style={profileStyles.label}>First Name</label>
            <input
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="First Name"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>Last Name</label>
            <input
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Last Name"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>Phone</label>
            <input
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="Phone Number"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>Email</label>
            <input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Email Address"
              style={profileStyles.input}
            />
          </div>
          <div style={profileStyles.fieldFull}>
            <label style={profileStyles.label}>Address / Location</label>
            <input
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="Street address or area"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>City</label>
            <input
              name="city"
              value={formData.city}
              onChange={handleChange}
              placeholder="City"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>State</label>
            <input
              name="state"
              value={formData.state}
              onChange={handleChange}
              placeholder="State"
              style={profileStyles.input}
            />
          </div>
          <div>
            <label style={profileStyles.label}>Pincode</label>
            <input
              name="pincode"
              value={formData.pincode}
              onChange={handleChange}
              placeholder="6-digit pincode"
              style={profileStyles.input}
            />
          </div>

          {/* Info badges */}
          <div style={profileStyles.fieldFull}>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
              {profile?.total_orders > 0 && (
                <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600, background: '#dcfce7', color: '#15803d', border: '1px solid #22c55e33' }}>
                  📦 {profile.total_orders} Orders
                </span>
              )}
              {profile?.member_since && (
                <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600, background: '#f0fdf4', color: '#166534', border: '1px solid #16653433' }}>
                  📅 Member since {new Date(profile.member_since).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
                </span>
              )}
            </div>
          </div>

          <div style={profileStyles.btnRow}>
            <button style={profileStyles.saveBtn} onClick={handleSave} disabled={saving}>
              <FiSave /> {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const BuyerDashboard = () => {
  return (
    <div className="dashboard">
      <Routes>
        <Route
          path="/"
          element={
            <div className="dashboard-overview">
              <h1>Welcome to SmartFarm Marketplace</h1>
              <p>Browse and buy fresh products directly from farmers</p>
              <BuyerShop />
            </div>
          }
        />
        <Route path="shop" element={<BuyerShop />} />
        <Route path="cart" element={<BuyerCart />} />
        <Route path="orders" element={<BuyerOrders />} />
        <Route path="purchase-history" element={<PurchaseHistory />} />
        <Route path="profile" element={<BuyerProfile />} />
      </Routes>
    </div>
  );
};

export default BuyerDashboard;
