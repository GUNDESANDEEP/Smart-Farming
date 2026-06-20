import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { FiPlus, FiPackage, FiTrendingUp, FiDollarSign, FiEdit2, FiTrash2, FiX, FiSave, FiEye, FiDownload } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { farmerAPI, paymentsAPI } from '../services/api';
import ReceiptViewer from '../components/ReceiptViewer';
import '../styles/dashboard.css';
import { PLACEHOLDER_IMG } from '../utils/productImages';
import SmartProductImage from '../utils/SmartProductImage';
import AgriBot from './AgriBot';
import UltraAIBanner from '../components/UltraAIBanner';

// ─── Constants ───────────────────────────────────────────────────────
const CATEGORIES = ['Vegetables', 'Fruits', 'Grains', 'Dairy', 'Spices', 'Pulses', 'Others'];
const UNITS = ['kg', 'quintal', 'ton', 'dozen', 'piece', 'liter'];

// ─── Auto-category detection map ─────────────────────────────────────
const PRODUCT_CATEGORY_MAP = {
  Vegetables: [
    'tomato', 'potato', 'onion', 'carrot', 'cabbage', 'cauliflower', 'brinjal', 'eggplant',
    'spinach', 'palak', 'methi', 'fenugreek', 'radish', 'mooli', 'beetroot', 'cucumber',
    'capsicum', 'bell pepper', 'peas', 'matar', 'beans', 'french beans', 'lady finger',
    'okra', 'bhindi', 'bottle gourd', 'lauki', 'bitter gourd', 'karela', 'ridge gourd',
    'turai', 'pumpkin', 'kaddu', 'drumstick', 'moringa', 'mushroom', 'corn', 'makka',
    'sweet potato', 'shakarkandi', 'green chilli', 'hari mirch', 'ginger', 'adrak',
    'garlic', 'lehsun', 'coriander', 'dhaniya', 'curry leaves', 'kadi patta', 'mint',
    'pudina', 'lettuce', 'broccoli', 'zucchini', 'asparagus', 'celery', 'turnip',
    'shalgam', 'yam', 'suran', 'colocasia', 'arbi', 'ivy gourd', 'tindora', 'parwal',
    'pointed gourd', 'chow chow', 'chayote', 'snake gourd', 'cluster beans', 'guar',
    'spring onion', 'leek', 'kale', 'artichoke', 'raw banana', 'kacha kela',
    'green peas', 'amaranth', 'chaulai', 'bathua', 'chenopodium', 'saag', 'greens',
    'sabzi', 'vegetable', 'veggie',
  ],
  Fruits: [
    'apple', 'seb', 'banana', 'kela', 'mango', 'aam', 'orange', 'santra', 'mosambi',
    'sweet lime', 'grapes', 'angoor', 'watermelon', 'tarbooz', 'muskmelon', 'kharbooja',
    'papaya', 'guava', 'amrud', 'pomegranate', 'anar', 'pineapple', 'ananas',
    'strawberry', 'blueberry', 'raspberry', 'cherry', 'peach', 'plum', 'aloo bukhara',
    'pear', 'nashpati', 'fig', 'anjeer', 'dates', 'khajoor', 'coconut', 'nariyal',
    'jackfruit', 'kathal', 'lychee', 'litchi', 'custard apple', 'sitaphal', 'sharifa',
    'sapota', 'chiku', 'kiwi', 'dragon fruit', 'avocado', 'passion fruit', 'starfruit',
    'kamrakh', 'jamun', 'java plum', 'amla', 'gooseberry', 'mulberry', 'shahtoot',
    'wood apple', 'bael', 'tamarind', 'imli', 'lemon', 'nimbu', 'lime', 'cranberry',
    'apricot', 'khubani', 'fruit',
  ],
  Grains: [
    'rice', 'chawal', 'wheat', 'gehu', 'atta', 'flour', 'maida', 'basmati', 'sona masoori',
    'brown rice', 'millets', 'bajra', 'jowar', 'sorghum', 'ragi', 'finger millet',
    'foxtail millet', 'kangni', 'barnyard millet', 'sanwa', 'kodo millet', 'little millet',
    'kutki', 'pearl millet', 'barley', 'jau', 'oats', 'maize', 'cornmeal', 'semolina',
    'suji', 'rava', 'sooji', 'poha', 'flattened rice', 'puffed rice', 'murmura',
    'broken wheat', 'dalia', 'bulgur', 'quinoa', 'amaranth grain', 'rajgira',
    'buckwheat', 'kuttu', 'grain', 'cereal',
  ],
  Dairy: [
    'milk', 'doodh', 'curd', 'dahi', 'yogurt', 'butter', 'makhan', 'ghee', 'cheese',
    'paneer', 'cottage cheese', 'cream', 'malai', 'buttermilk', 'chaas', 'lassi',
    'khoya', 'mawa', 'condensed milk', 'skimmed milk', 'toned milk', 'full cream milk',
    'whey', 'ice cream', 'shrikhand', 'dairy',
  ],
  Spices: [
    'turmeric', 'haldi', 'chilli powder', 'lal mirch', 'red chilli', 'coriander powder',
    'dhaniya powder', 'cumin', 'jeera', 'mustard', 'sarson', 'rai', 'black pepper',
    'kali mirch', 'cardamom', 'elaichi', 'clove', 'laung', 'cinnamon', 'dalchini',
    'bay leaf', 'tej patta', 'nutmeg', 'jaiphal', 'mace', 'javitri', 'fennel', 'saunf',
    'fenugreek seeds', 'methi dana', 'carom', 'ajwain', 'asafoetida', 'hing',
    'star anise', 'chakri phool', 'saffron', 'kesar', 'dry ginger', 'sonth',
    'poppy seeds', 'khus khus', 'sesame', 'til', 'nigella', 'kalonji', 'tamarind paste',
    'curry powder', 'garam masala', 'chaat masala', 'sambar powder', 'rasam powder',
    'biryani masala', 'tandoori masala', 'pav bhaji masala', 'kitchen king masala',
    'spice', 'masala', 'powder',
  ],
  Pulses: [
    'dal', 'daal', 'lentil', 'toor dal', 'arhar dal', 'pigeon pea', 'moong dal',
    'green gram', 'urad dal', 'black gram', 'chana dal', 'bengal gram', 'masoor dal',
    'red lentil', 'red dal', 'yellow dal', 'rajma', 'kidney bean', 'chole', 'chana',
    'chickpea', 'kabuli chana', 'black chana', 'kala chana', 'green moong', 'sabut moong',
    'white urad', 'dhuli urad', 'moth dal', 'moth bean', 'kulith', 'horse gram',
    'lobiya', 'black eyed pea', 'cowpea', 'soybean', 'soya', 'groundnut', 'peanut',
    'moongfali', 'almond', 'badam', 'cashew', 'kaju', 'walnut', 'akhrot', 'pistachio',
    'pista', 'raisin', 'kishmish', 'flax seed', 'alsi', 'chia seed', 'sunflower seed',
    'pumpkin seed', 'pulse', 'legume', 'bean', 'lobia',
  ],
};

/**
 * Auto-detect category from product name.
 * Returns the matching category or '' if no match.
 */
const autoDetectCategory = (productName) => {
  if (!productName || productName.trim().length < 2) return '';
  const lower = productName.toLowerCase().trim();

  for (const [category, keywords] of Object.entries(PRODUCT_CATEGORY_MAP)) {
    for (const keyword of keywords) {
      // Match whole word or if the product name contains the keyword
      if (lower === keyword || lower.includes(keyword) || keyword.includes(lower)) {
        return category;
      }
    }
  }
  return '';
};

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
    const { name, value } = e.target;
    const updated = { ...formData, [name]: value };

    // Auto-detect category when product name changes
    if (name === 'name') {
      const detected = autoDetectCategory(value);
      if (detected && detected !== formData.category) {
        updated.category = detected;
        toast.success(`Category auto-set: ${detected}`, { icon: '🏷️', duration: 2000 });
      }
    }

    setFormData(updated);
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
          products.map((product) => {
            const qty = parseFloat(product.quantity) || 0;
            const isSoldOut = qty <= 0 || product.status === 'sold_out';
            const isLowStock = qty > 0 && qty <= 20;
            return (
            <div key={product._id || product.id} className="product-card" style={{ overflow: 'hidden', position: 'relative', opacity: isSoldOut ? 0.65 : 1 }}>
              {/* SOLD OUT Overlay */}
              {isSoldOut && (
                <div style={{
                  position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 10,
                  background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  borderRadius: '12px', pointerEvents: 'none',
                }}>
                  <span style={{
                    background: '#dc2626', color: '#fff', padding: '10px 28px', borderRadius: '10px',
                    fontSize: '1.2rem', fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase',
                    boxShadow: '0 4px 20px rgba(220,38,38,0.4)', transform: 'rotate(-12deg)',
                  }}>SOLD OUT</span>
                </div>
              )}
              {/* LOW STOCK Badge */}
              {isLowStock && (
                <div style={{
                  position: 'absolute', top: '10px', right: '10px', zIndex: 8,
                  background: 'linear-gradient(135deg, #dc2626, #ef4444)', color: '#fff',
                  padding: '4px 10px', borderRadius: '8px', fontSize: '0.68rem', fontWeight: 700,
                  display: 'flex', alignItems: 'center', gap: '4px',
                  boxShadow: '0 2px 8px rgba(220,38,38,0.35)',
                  animation: 'lowStockPulse 2s infinite',
                }}>
                  🔴 Only {Math.floor(qty)} left!
                </div>
              )}
              {/* Product Image */}
              <div style={{ width: '100%', height: '140px', overflow: 'hidden', borderRadius: '12px 12px 0 0', marginBottom: '10px' }}>
                <SmartProductImage
                  product={product}
                  alt={product.name}
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
                    background: isSoldOut ? 'rgba(220,38,38,0.15)' : product.status === 'approved' ? 'rgba(34,197,94,0.15)' : product.status === 'rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                    color: isSoldOut ? '#dc2626' : product.status === 'approved' ? '#15803d' : product.status === 'rejected' ? '#dc2626' : '#d97706',
                    border: `1px solid ${isSoldOut ? '#ef444433' : product.status === 'approved' ? '#22c55e33' : product.status === 'rejected' ? '#ef444433' : '#f59e0b33'}`,
                  }}>
                    {isSoldOut ? 'sold out' : (product.status || 'pending')}
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
                <p className="stock" style={{ color: isLowStock ? '#dc2626' : isSoldOut ? '#dc2626' : undefined, fontWeight: isLowStock || isSoldOut ? 700 : undefined }}>
                  {isSoldOut ? '❌ Out of Stock' : isLowStock ? `⚠️ Low Stock: ${Math.floor(qty)} ${product.unit}` : `Qty: ${product.quantity} ${product.unit}`}
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
            );
          })
        )}
      </div>
    </div>
  );
};

// ─── FarmerOrders ── Full Order Management with Actions ──────────────
const FARMER_ORDER_STEPS = [
  { key: 'pending', label: 'New Order', icon: '🔔', next: null, actionLabel: null },
  { key: 'confirmed', label: 'Accepted', icon: '✅', next: 'processing', actionLabel: '⚙️ Start Processing' },
  { key: 'processing', label: 'Processing', icon: '⚙️', next: 'packed', actionLabel: '📦 Mark Packed' },
  { key: 'packed', label: 'Packed', icon: '📦', next: 'dispatched', actionLabel: '🚚 Dispatch' },
  { key: 'dispatched', label: 'Dispatched', icon: '🚚', next: 'in_transit', actionLabel: '🚛 In Transit' },
  { key: 'in_transit', label: 'In Transit', icon: '🚛', next: 'out_for_delivery', actionLabel: '🏍️ Out for Delivery' },
  { key: 'out_for_delivery', label: 'Out for Delivery', icon: '🏍️', next: null, actionLabel: null },
  { key: 'delivered', label: 'Delivered', icon: '🎉', next: null, actionLabel: null },
];

const FarmerOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [rejectModal, setRejectModal] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  // Delivery OTP states
  const [otpModal, setOtpModal] = useState(null);
  const [otpValue, setOtpValue] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpSending, setOtpSending] = useState(false);
  // COD confirmation
  const [codModal, setCodModal] = useState(null);

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
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (orderId) => {
    setActionLoading(orderId);
    try {
      await farmerAPI.acceptOrder(orderId);
      toast.success('Order accepted! 🎉');
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to accept');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) { toast.error('Please enter a reason'); return; }
    setActionLoading(rejectModal);
    try {
      await farmerAPI.rejectOrder(rejectModal, rejectReason);
      toast.success('Order rejected');
      setRejectModal(null);
      setRejectReason('');
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to reject');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    setActionLoading(orderId);
    try {
      await farmerAPI.updateOrderStatus(orderId, newStatus);
      toast.success(`Status updated to ${newStatus.replace(/_/g, ' ')}!`);
      fetchOrders();
      if (orderDetail && orderDetail.id === orderId) {
        handleViewDetail(orderId);
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to update status');
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewDetail = async (orderId) => {
    try {
      const res = await farmerAPI.getOrderDetail(orderId);
      setOrderDetail(res.data?.order || res.data);
      setSelectedOrder(orderId);
    } catch (error) {
      toast.error('Failed to load order details');
    }
  };

  // ── Delivery OTP handlers ──
  const handleSendOtp = async (orderId) => {
    setOtpSending(true);
    try {
      await farmerAPI.sendDeliveryOtp(orderId);
      toast.success('Delivery OTP sent to buyer\'s email! 📧');
      setOtpSent(true);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    } finally {
      setOtpSending(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpValue || otpValue.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }
    setActionLoading(otpModal);
    try {
      await farmerAPI.verifyDeliveryOtp(otpModal, otpValue);
      toast.success('OTP Verified! Order delivered & payment released! 🎉💰');
      setOtpModal(null);
      setOtpValue('');
      setOtpSent(false);
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'OTP verification failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleConfirmCod = async () => {
    setActionLoading(codModal);
    try {
      await farmerAPI.confirmCodDelivery(codModal);
      toast.success('Cash received confirmed! Order delivered! 💰🎉');
      setCodModal(null);
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to confirm delivery');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f59e0b', confirmed: '#3b82f6', processing: '#8b5cf6',
      packed: '#6366f1', dispatched: '#0ea5e9', in_transit: '#14b8a6',
      out_for_delivery: '#f97316', delivered: '#22c55e', cancelled: '#ef4444',
    };
    return colors[status] || '#6b7280';
  };

  const getStepInfo = (status) => FARMER_ORDER_STEPS.find(s => s.key === status);
  const getStepIndex = (status) => FARMER_ORDER_STEPS.findIndex(s => s.key === status);

  // Filter orders by tab
  const filteredOrders = orders.filter(o => {
    if (activeTab === 'all') return true;
    if (activeTab === 'new') return o.status === 'pending';
    if (activeTab === 'active') return ['confirmed', 'processing', 'packed', 'dispatched', 'in_transit', 'out_for_delivery'].includes(o.status);
    if (activeTab === 'delivered') return o.status === 'delivered';
    if (activeTab === 'cancelled') return o.status === 'cancelled';
    return true;
  });

  // Order stats
  const stats = {
    total: orders.length,
    newOrders: orders.filter(o => o.status === 'pending').length,
    active: orders.filter(o => ['confirmed', 'processing', 'packed', 'dispatched', 'in_transit', 'out_for_delivery'].includes(o.status)).length,
    delivered: orders.filter(o => o.status === 'delivered').length,
    revenue: orders.filter(o => o.status === 'delivered').reduce((sum, o) => sum + (parseFloat(o.total_price || o.total || 0)), 0),
  };

  const tabs = [
    { key: 'all', label: 'All Orders', count: stats.total, color: '#6b7280' },
    { key: 'new', label: '🔔 New', count: stats.newOrders, color: '#f59e0b' },
    { key: 'active', label: '⚙️ Active', count: stats.active, color: '#3b82f6' },
    { key: 'delivered', label: '✅ Delivered', count: stats.delivered, color: '#22c55e' },
    { key: 'cancelled', label: '❌ Cancelled', count: orders.filter(o => o.status === 'cancelled').length, color: '#ef4444' },
  ];

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>📦 Order Management</h2>

      {/* ── Stats Bar ── */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '10px', marginBottom: '20px',
      }}>
        {[
          { label: 'Total Orders', value: stats.total, icon: '📦', bg: '#f0fdf4' },
          { label: 'New Orders', value: stats.newOrders, icon: '🔔', bg: stats.newOrders > 0 ? '#fffbeb' : '#f0fdf4' },
          { label: 'In Progress', value: stats.active, icon: '⚙️', bg: '#eff6ff' },
          { label: 'Delivered', value: stats.delivered, icon: '✅', bg: '#f0fdf4' },
          { label: 'Revenue', value: `₹${stats.revenue.toFixed(0)}`, icon: '💰', bg: '#f0fdf4' },
        ].map((s, i) => (
          <div key={i} style={{
            background: s.bg, borderRadius: '12px', padding: '14px',
            textAlign: 'center', border: '1px solid rgba(22,163,74,0.08)',
          }}>
            <div style={{ fontSize: '1.4rem', marginBottom: '4px' }}>{s.icon}</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#14532d' }}>{s.value}</div>
            <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '2px' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Tab Filters ── */}
      <div style={{
        display: 'flex', gap: '6px', marginBottom: '16px', overflowX: 'auto',
        paddingBottom: '4px',
      }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '8px 16px', borderRadius: '20px', fontSize: '0.8rem',
              fontWeight: 600, fontFamily: 'Poppins, sans-serif', cursor: 'pointer',
              whiteSpace: 'nowrap', border: 'none',
              background: activeTab === tab.key ? tab.color : '#f1f5f9',
              color: activeTab === tab.key ? '#fff' : '#475569',
              transition: 'all 0.2s',
            }}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* ── Order Cards ── */}
      {filteredOrders.length === 0 ? (
        <div className="empty-state">
          <FiPackage size={48} />
          <h3>No orders found</h3>
          <p>Orders matching this filter will appear here</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredOrders.map(order => {
            const stepInfo = getStepInfo(order.status);
            const currentIdx = getStepIndex(order.status);
            const isCancelled = order.status === 'cancelled';
            const isPending = order.status === 'pending';
            const isDelivered = order.status === 'delivered';
            const isLoading = actionLoading === (order.id || order._id);
            const orderId = order.id || order._id;

            return (
              <div key={orderId} style={{
                background: 'rgba(255,255,255,0.97)', borderRadius: '16px',
                border: isPending ? '2px solid #f59e0b40' : '1px solid rgba(22,163,74,0.08)',
                overflow: 'hidden', boxShadow: '0 2px 12px rgba(22,101,52,0.06)',
              }}>
                {/* New Order Alert Banner */}
                {isPending && (
                  <div style={{
                    background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                    padding: '8px 20px', display: 'flex', alignItems: 'center', gap: '8px',
                    color: '#78350f', fontWeight: 700, fontSize: '0.82rem',
                  }}>
                    <span style={{ fontSize: '1.1rem' }}>🔔</span>
                    NEW ORDER — Action Required!
                  </div>
                )}

                {/* Order Header */}
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '14px 20px', borderBottom: '1px solid rgba(22,163,74,0.06)',
                  background: isCancelled ? '#fef2f2' : 'linear-gradient(135deg, #f0fdf4, #fff)',
                }}>
                  <div>
                    <span style={{ fontWeight: 700, color: '#14532d', fontSize: '0.95rem' }}>
                      Order #{order.id}
                    </span>
                    <span style={{ marginLeft: '12px', fontSize: '0.78rem', color: '#888' }}>
                      {order.created_at ? new Date(order.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
                      }) : ''}
                    </span>
                  </div>
                  <span style={{
                    padding: '4px 14px', borderRadius: '20px', fontSize: '0.75rem',
                    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px',
                    background: getStatusColor(order.status) + '20',
                    color: getStatusColor(order.status),
                  }}>
                    {stepInfo?.icon} {(order.status || 'pending').replace(/_/g, ' ')}
                  </span>
                </div>

                {/* Order Body */}
                <div style={{ padding: '16px 20px' }}>
                  {/* Product & Amount Row */}
                  <div style={{
                    display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px',
                    marginBottom: '14px', alignItems: 'center',
                  }}>
                    <div>
                      <p style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#1f2937' }}>
                        {order.product_name || 'Product'}
                      </p>
                      <p style={{ margin: '2px 0', fontSize: '0.82rem', color: '#6b7280' }}>
                        Qty: {order.quantity} • {order.payment_method === 'cod' ? '💰 COD' : '💳 Online'}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: '#166534' }}>
                        ₹{order.total || order.total_price || 0}
                      </p>
                    </div>
                  </div>

                  {/* Buyer Info Card */}
                  <div style={{
                    background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)',
                    borderRadius: '12px', padding: '14px 16px', marginBottom: '14px',
                    border: '1px solid rgba(22,163,74,0.08)',
                  }}>
                    <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#166534', fontSize: '0.85rem' }}>
                      👤 Buyer Details
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <div>
                        <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Name</p>
                        <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.88rem' }}>
                          {order.buyer_name || 'N/A'} {order.buyer_last_name || ''}
                        </p>
                      </div>
                      <div>
                        <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Phone</p>
                        <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.88rem' }}>
                          📞 {order.buyer_phone || 'N/A'}
                        </p>
                      </div>
                      {order.buyer_email && (
                        <div>
                          <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Email</p>
                          <p style={{ margin: '1px 0 0', color: '#14532d', fontSize: '0.82rem' }}>✉️ {order.buyer_email}</p>
                        </div>
                      )}
                      <div style={{ gridColumn: '1/-1' }}>
                        <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Delivery Address</p>
                        <p style={{ margin: '1px 0 0', fontWeight: 600, color: '#14532d', fontSize: '0.85rem' }}>
                          📍 {[order.buyer_address, order.buyer_city, order.buyer_state].filter(Boolean).join(', ') || 'Not provided'}
                          {order.buyer_pincode && (
                            <span style={{ marginLeft: 6, background: '#166534', color: '#fff', padding: '2px 8px', borderRadius: '6px', fontSize: '0.72rem' }}>
                              PIN: {order.buyer_pincode}
                            </span>
                          )}
                        </p>
                        {/* Google Maps link */}
                        {(order.buyer_address || order.buyer_city) && (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                              [order.buyer_address, order.buyer_city, order.buyer_state, order.buyer_pincode].filter(Boolean).join(', ')
                            )}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-flex', alignItems: 'center', gap: '4px',
                              marginTop: '6px', padding: '4px 12px', borderRadius: '6px',
                              background: '#4285F4', color: '#fff', fontSize: '0.72rem',
                              fontWeight: 600, textDecoration: 'none',
                            }}
                          >
                            🗺️ Open in Google Maps
                          </a>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Mini Progress Stepper */}
                  {!isCancelled && (
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '2px',
                      background: '#f8fdf9', borderRadius: '10px', padding: '8px 6px', marginBottom: '14px',
                    }}>
                      {FARMER_ORDER_STEPS.map((step, i) => {
                        const isCompleted = i <= currentIdx;
                        const isCurrent = i === currentIdx;
                        return (
                          <React.Fragment key={step.key}>
                            <div style={{
                              display: 'flex', flexDirection: 'column', alignItems: 'center',
                              flex: 1, minWidth: 0,
                            }}>
                              <div style={{
                                width: '24px', height: '24px', borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '0.7rem',
                                background: isCompleted ? '#22c55e' : '#e5e7eb',
                                color: isCompleted ? '#fff' : '#9ca3af',
                                boxShadow: isCurrent ? '0 0 0 3px #22c55e40' : 'none',
                              }}>
                                {isCompleted ? step.icon : (i + 1)}
                              </div>
                              <span style={{
                                fontSize: '0.5rem', color: isCompleted ? '#166534' : '#9ca3af',
                                marginTop: '2px', fontWeight: isCurrent ? 700 : 500,
                                textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden',
                                textOverflow: 'ellipsis', maxWidth: '48px',
                              }}>
                                {step.label}
                              </span>
                            </div>
                            {i < FARMER_ORDER_STEPS.length - 1 && (
                              <div style={{
                                height: '2px', flex: '0 0 6px',
                                background: i < currentIdx ? '#22c55e' : '#e5e7eb',
                                borderRadius: '1px', marginTop: '-10px',
                              }} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                  )}

                  {/* ── Action Buttons ── */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {/* Pending: Accept / Reject */}
                    {isPending && (
                      <>
                        <button
                          onClick={() => handleAccept(orderId)}
                          disabled={isLoading}
                          style={{
                            flex: 1, padding: '12px 20px', borderRadius: '10px', fontWeight: 700,
                            background: isLoading ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)',
                            color: '#fff', border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                            fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                          }}
                        >
                          {isLoading ? '⏳ ...' : '✅ Accept Order'}
                        </button>
                        <button
                          onClick={() => setRejectModal(orderId)}
                          disabled={isLoading}
                          style={{
                            padding: '12px 20px', borderRadius: '10px', fontWeight: 700,
                            background: '#fef2f2', color: '#dc2626', border: '1px solid #fca5a533',
                            cursor: 'pointer', fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                          }}
                        >
                          ❌ Reject
                        </button>
                      </>
                    )}

                    {/* Active orders: Next status button */}
                    {stepInfo?.next && !isPending && (
                      <button
                        onClick={() => handleUpdateStatus(orderId, stepInfo.next)}
                        disabled={isLoading}
                        style={{
                          flex: 1, padding: '12px 20px', borderRadius: '10px', fontWeight: 700,
                          background: isLoading ? '#9ca3af' : `linear-gradient(135deg, ${getStatusColor(stepInfo.next)}, ${getStatusColor(stepInfo.next)}cc)`,
                          color: '#fff', border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                          fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                        }}
                      >
                        {isLoading ? '⏳ Updating...' : stepInfo.actionLabel}
                      </button>
                    )}

                    {/* ── OUT FOR DELIVERY: Payment-specific delivery buttons ── */}
                    {order.status === 'out_for_delivery' && (
                      <>
                        {/* ONLINE PAYMENT → OTP Flow */}
                        {order.payment_method === 'online' ? (
                          <button
                            onClick={() => { setOtpModal(orderId); setOtpValue(''); setOtpSent(false); }}
                            disabled={isLoading}
                            style={{
                              flex: 1, padding: '12px 20px', borderRadius: '10px', fontWeight: 700,
                              background: isLoading ? '#9ca3af' : 'linear-gradient(135deg, #7c3aed, #a855f7)',
                              color: '#fff', border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                              fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                            }}
                          >
                            🔐 Verify OTP & Deliver
                          </button>
                        ) : (
                          /* COD → Cash Confirmation */
                          <button
                            onClick={() => setCodModal(orderId)}
                            disabled={isLoading}
                            style={{
                              flex: 1, padding: '12px 20px', borderRadius: '10px', fontWeight: 700,
                              background: isLoading ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)',
                              color: '#fff', border: 'none', cursor: isLoading ? 'not-allowed' : 'pointer',
                              fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                            }}
                          >
                            💰 Confirm Cash & Deliver
                          </button>
                        )}
                      </>
                    )}

                    {/* View Details button */}
                    <button
                      onClick={() => handleViewDetail(orderId)}
                      style={{
                        padding: '12px 16px', borderRadius: '10px', fontWeight: 600,
                        background: '#f0fdf4', color: '#166534', border: '1px solid #22c55e33',
                        cursor: 'pointer', fontSize: '0.82rem', fontFamily: 'Poppins, sans-serif',
                      }}
                    >
                      <FiEye size={14} style={{ marginRight: '4px' }} /> Details
                    </button>

                    {/* Delivered badge */}
                    {isDelivered && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: '6px',
                        padding: '8px 16px', borderRadius: '10px',
                        background: '#dcfce7', color: '#15803d', fontWeight: 700, fontSize: '0.85rem',
                      }}>
                        🎉 Order Complete!
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Order Detail Modal ── */}
      {selectedOrder && orderDetail && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => { setSelectedOrder(null); setOrderDetail(null); }}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '550px',
            width: '100%', maxHeight: '85vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#14532d' }}>📋 Order #{orderDetail.order_number || orderDetail.id}</h3>
              <span style={{
                padding: '4px 14px', borderRadius: '20px', fontSize: '0.75rem',
                fontWeight: 700, textTransform: 'uppercase',
                background: getStatusColor(orderDetail.status) + '20',
                color: getStatusColor(orderDetail.status),
              }}>
                {(orderDetail.status || '').replace(/_/g, ' ')}
              </span>
            </div>

            {/* Product Info */}
            <div style={{
              background: '#f0fdf4', borderRadius: '12px', padding: '14px', marginBottom: '14px',
              border: '1px solid #22c55e22',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ margin: 0, fontWeight: 700, color: '#14532d', fontSize: '1rem' }}>
                    {orderDetail.product?.name || 'Product'}
                  </p>
                  <p style={{ margin: '2px 0', fontSize: '0.82rem', color: '#6b7280' }}>
                    {orderDetail.product?.category} • {orderDetail.product?.unit}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: '#6b7280' }}>
                    ₹{orderDetail.product?.price} × {orderDetail.quantity}
                  </p>
                  <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#166534' }}>
                    ₹{orderDetail.total_amount}
                  </p>
                </div>
              </div>
            </div>

            {/* Buyer Info */}
            <div style={{
              background: '#eff6ff', borderRadius: '12px', padding: '14px', marginBottom: '14px',
              border: '1px solid #3b82f622',
            }}>
              <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#1e40af', fontSize: '0.85rem' }}>👤 Buyer</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.85rem' }}>
                <div><span style={{ color: '#888' }}>Name:</span> <strong>{orderDetail.buyer?.name}</strong></div>
                <div><span style={{ color: '#888' }}>Phone:</span> <strong>📞 {orderDetail.buyer?.phone}</strong></div>
                {orderDetail.buyer?.email && (
                  <div style={{ gridColumn: '1/-1' }}><span style={{ color: '#888' }}>Email:</span> ✉️ {orderDetail.buyer?.email}</div>
                )}
              </div>
            </div>

            {/* Delivery Address */}
            <div style={{
              background: '#fef3c7', borderRadius: '12px', padding: '14px', marginBottom: '14px',
              border: '1px solid #f59e0b22',
            }}>
              <p style={{ margin: '0 0 6px', fontWeight: 700, color: '#92400e', fontSize: '0.85rem' }}>📍 Delivery Address</p>
              <p style={{ margin: 0, color: '#78350f', fontSize: '0.88rem' }}>
                {orderDetail.delivery_address || 'Not provided'}
              </p>
              {orderDetail.delivery_address && (
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(orderDetail.delivery_address)}`}
                  target="_blank" rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    marginTop: '8px', padding: '6px 14px', borderRadius: '8px',
                    background: '#4285F4', color: '#fff', fontSize: '0.78rem',
                    fontWeight: 600, textDecoration: 'none',
                  }}
                >
                  🗺️ View on Google Maps
                </a>
              )}
            </div>

            {/* Payment & Notes */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
              <div style={{ background: '#f0fdf4', borderRadius: '10px', padding: '10px 14px' }}>
                <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Payment</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d' }}>
                  {orderDetail.payment_method === 'cod' ? '💰 COD' : '💳 Online'}
                </p>
              </div>
              <div style={{ background: '#f0fdf4', borderRadius: '10px', padding: '10px 14px' }}>
                <p style={{ margin: 0, fontSize: '0.72rem', color: '#888', textTransform: 'uppercase' }}>Payment Status</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, color: '#14532d' }}>
                  {(orderDetail.payment_status || 'pending').replace(/_/g, ' ')}
                </p>
              </div>
            </div>
            {orderDetail.notes && (
              <div style={{ background: '#f8fafc', borderRadius: '10px', padding: '10px 14px', marginBottom: '14px' }}>
                <p style={{ margin: 0, fontSize: '0.72rem', color: '#888' }}>NOTES</p>
                <p style={{ margin: '4px 0 0', color: '#374151', fontSize: '0.88rem' }}>{orderDetail.notes}</p>
              </div>
            )}

            {/* Tracking Timeline */}
            {orderDetail.tracking && orderDetail.tracking.length > 0 && (
              <div style={{ marginBottom: '14px' }}>
                <p style={{ margin: '0 0 10px', fontWeight: 700, color: '#14532d', fontSize: '0.9rem' }}>📍 Tracking Timeline</p>
                {orderDetail.tracking.map((t, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
                    <div style={{
                      width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                      background: '#22c55e', color: '#fff', display: 'flex',
                      alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem',
                    }}>✓</div>
                    <div>
                      <p style={{ margin: 0, fontWeight: 600, color: '#14532d', fontSize: '0.85rem' }}>
                        {(t.status || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                      <p style={{ margin: '1px 0', fontSize: '0.72rem', color: '#888' }}>
                        {t.timestamp ? new Date(t.timestamp).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                        }) : ''}
                        {t.description && ` — ${t.description}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Review */}
            {orderDetail.review && (
              <div style={{
                background: '#fffbeb', borderRadius: '12px', padding: '14px', marginBottom: '14px',
                border: '1px solid #f59e0b22',
              }}>
                <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#92400e', fontSize: '0.85rem' }}>⭐ Buyer Review</p>
                <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem' }}>
                  <div>
                    <span style={{ color: '#888' }}>Product:</span>{' '}
                    {'⭐'.repeat(orderDetail.review.product_rating || 0)}
                    {orderDetail.review.product_review && (
                      <p style={{ margin: '4px 0 0', color: '#374151', fontSize: '0.82rem', fontStyle: 'italic' }}>
                        "{orderDetail.review.product_review}"
                      </p>
                    )}
                  </div>
                  <div>
                    <span style={{ color: '#888' }}>Farmer:</span>{' '}
                    {'⭐'.repeat(orderDetail.review.farmer_rating || 0)}
                    {orderDetail.review.farmer_review && (
                      <p style={{ margin: '4px 0 0', color: '#374151', fontSize: '0.82rem', fontStyle: 'italic' }}>
                        "{orderDetail.review.farmer_review}"
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <button onClick={() => { setSelectedOrder(null); setOrderDetail(null); }} style={{
              width: '100%', padding: '12px', borderRadius: '10px', fontWeight: 600,
              background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
              fontFamily: 'Poppins, sans-serif',
            }}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* ── Reject Reason Modal ── */}
      {rejectModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => setRejectModal(null)}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '400px',
            width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 16px', color: '#dc2626' }}>❌ Reject Order</h3>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason for rejecting this order..."
              rows={3}
              style={{
                width: '100%', padding: '12px', borderRadius: '10px',
                border: '1px solid #fca5a533', fontSize: '0.9rem', outline: 'none',
                fontFamily: 'Poppins, sans-serif', boxSizing: 'border-box', marginBottom: '16px',
              }}
            />
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setRejectModal(null)} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontWeight: 600,
                background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                Cancel
              </button>
              <button onClick={handleReject} disabled={actionLoading === rejectModal} style={{
                flex: 2, padding: '12px', borderRadius: '10px', fontWeight: 700,
                background: actionLoading === rejectModal ? '#9ca3af' : '#dc2626',
                color: '#fff', border: 'none', cursor: actionLoading === rejectModal ? 'not-allowed' : 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                {actionLoading === rejectModal ? 'Rejecting...' : '❌ Confirm Reject'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delivery OTP Modal (Online Payment) ── */}
      {otpModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => { setOtpModal(null); setOtpValue(''); setOtpSent(false); }}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '420px',
            width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
          }} onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div style={{
              background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
              borderRadius: '14px', padding: '20px', marginBottom: '20px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🔐</div>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Delivery OTP Verification</h3>
              <p style={{ margin: '6px 0 0', color: '#e9d5ff', fontSize: '0.82rem' }}>
                Online Payment — Verify before releasing payment
              </p>
            </div>

            {/* Step 1: Send OTP */}
            <div style={{
              background: '#f5f3ff', borderRadius: '12px', padding: '14px', marginBottom: '14px',
              border: '1px solid #7c3aed22',
            }}>
              <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#5b21b6', fontSize: '0.85rem' }}>
                Step 1: Send OTP to Buyer's Email
              </p>
              <p style={{ margin: '0 0 10px', fontSize: '0.78rem', color: '#6b7280' }}>
                An OTP will be sent to the buyer's registered email. The buyer will tell you the OTP.
              </p>
              <button
                onClick={() => handleSendOtp(otpModal)}
                disabled={otpSending || otpSent}
                style={{
                  width: '100%', padding: '12px', borderRadius: '10px', fontWeight: 700,
                  background: otpSent ? '#22c55e' : otpSending ? '#9ca3af' : 'linear-gradient(135deg, #7c3aed, #a855f7)',
                  color: '#fff', border: 'none', cursor: (otpSending || otpSent) ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif',
                }}
              >
                {otpSent ? '✅ OTP Sent to Buyer!' : otpSending ? '📧 Sending...' : '📧 Send OTP to Buyer'}
              </button>
              {otpSent && (
                <p style={{ margin: '6px 0 0', fontSize: '0.72rem', color: '#22c55e', textAlign: 'center' }}>
                  ✅ OTP sent! Ask buyer to check their email.
                </p>
              )}
            </div>

            {/* Step 2: Enter OTP */}
            <div style={{
              background: otpSent ? '#f0fdf4' : '#f9fafb', borderRadius: '12px', padding: '14px', marginBottom: '16px',
              border: otpSent ? '1px solid #22c55e22' : '1px solid #e5e7eb',
              opacity: otpSent ? 1 : 0.6, pointerEvents: otpSent ? 'auto' : 'none',
            }}>
              <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#166534', fontSize: '0.85rem' }}>
                Step 2: Enter OTP from Buyer
              </p>
              <p style={{ margin: '0 0 10px', fontSize: '0.78rem', color: '#6b7280' }}>
                Ask the buyer for the 6-digit OTP they received via email.
              </p>
              <input
                type="text"
                maxLength={6}
                value={otpValue}
                onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="Enter 6-digit OTP"
                style={{
                  width: '100%', padding: '16px', borderRadius: '12px',
                  border: '2px solid #7c3aed33', fontSize: '1.5rem', textAlign: 'center',
                  letterSpacing: '8px', fontWeight: 800, fontFamily: 'monospace',
                  outline: 'none', boxSizing: 'border-box', color: '#14532d',
                }}
              />
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => { setOtpModal(null); setOtpValue(''); setOtpSent(false); }} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontWeight: 600,
                background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                Cancel
              </button>
              <button
                onClick={handleVerifyOtp}
                disabled={!otpSent || otpValue.length !== 6 || actionLoading === otpModal}
                style={{
                  flex: 2, padding: '12px', borderRadius: '10px', fontWeight: 700,
                  background: (!otpSent || otpValue.length !== 6) ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)',
                  color: '#fff', border: 'none',
                  cursor: (!otpSent || otpValue.length !== 6) ? 'not-allowed' : 'pointer',
                  fontFamily: 'Poppins, sans-serif',
                }}
              >
                {actionLoading === otpModal ? '⏳ Verifying...' : '✅ Verify OTP & Deliver'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── COD Cash Confirmation Modal ── */}
      {codModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => setCodModal(null)}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '400px',
            width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
          }} onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div style={{
              background: 'linear-gradient(135deg, #166534, #22c55e)',
              borderRadius: '14px', padding: '20px', marginBottom: '20px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>💰</div>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Cash on Delivery</h3>
              <p style={{ margin: '6px 0 0', color: '#bbf7d0', fontSize: '0.82rem' }}>
                Confirm you received cash payment
              </p>
            </div>

            <div style={{
              background: '#fffbeb', borderRadius: '12px', padding: '14px', marginBottom: '16px',
              border: '1px solid #fbbf2433',
            }}>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#92400e', fontWeight: 600 }}>
                ⚠️ Please confirm:
              </p>
              <ul style={{ margin: '8px 0 0', paddingLeft: '20px', fontSize: '0.82rem', color: '#78350f' }}>
                <li>You have delivered the product to the buyer</li>
                <li>You have collected the cash payment</li>
                <li>The buyer has confirmed receipt of the product</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setCodModal(null)} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontWeight: 600,
                background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                Cancel
              </button>
              <button
                onClick={handleConfirmCod}
                disabled={actionLoading === codModal}
                style={{
                  flex: 2, padding: '12px', borderRadius: '10px', fontWeight: 700,
                  background: actionLoading === codModal ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)',
                  color: '#fff', border: 'none',
                  cursor: actionLoading === codModal ? 'not-allowed' : 'pointer',
                  fontFamily: 'Poppins, sans-serif',
                }}
              >
                {actionLoading === codModal ? '⏳ Confirming...' : '💰 Confirm Cash Received & Deliver'}
              </button>
            </div>
          </div>
        </div>
      )}
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (city && locationLoaded) {
      fetchWeatherByCity(city);
    }
    const interval = setInterval(() => {
      if (city) fetchWeatherByCity(city);
    }, 600000); // Refresh every 10 minutes
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city, locationLoaded]);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  const fetchWeatherByCoords = async (lat, lon) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_URL}/weather?lat=${lat}&lon=${lon}`, {
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
      const res = await fetch(`${API_URL}/weather?city=${c}`, {
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
    pendingOrders: 0,
    activeOrders: 0,
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
      const ordersList = ordersRes.data.orders || ordersRes.data || [];
      const ordersArr = Array.isArray(ordersList) ? ordersList : [];
      setStats({
        products: productsRes.data.total || (productsRes.data.products || []).length || 0,
        orders: ordersArr.length,
        pendingOrders: ordersArr.filter(o => o.status === 'pending').length,
        activeOrders: ordersArr.filter(o => ['confirmed', 'processing', 'packed', 'dispatched', 'in_transit', 'out_for_delivery'].includes(o.status)).length,
        earnings: earningsRes.data.total || earningsRes.data.total_earnings || earningsRes.data.earnings || 0,
        rating: earningsRes.data.rating || 4.5,
      });
    } catch (error) {
      console.error('Failed to load stats', error);
      setStats({ products: 0, orders: 0, pendingOrders: 0, activeOrders: 0, earnings: 0, rating: 0 });
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
              <UltraAIBanner />
              <WeatherWidget />

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="icon"><FiPackage /></div>
                  <div className="stat-content">
                    <p>Products</p>
                    <h3>{stats.products}</h3>
                  </div>
                </div>

                <div className="stat-card" style={stats.pendingOrders > 0 ? { border: '2px solid #f59e0b', animation: 'discountPulse 2s infinite' } : {}}>
                  <div className="icon" style={stats.pendingOrders > 0 ? { background: '#fbbf24', color: '#78350f' } : {}}>🔔</div>
                  <div className="stat-content">
                    <p>New Orders</p>
                    <h3 style={stats.pendingOrders > 0 ? { color: '#d97706' } : {}}>{stats.pendingOrders || 0}</h3>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="icon"><FiTrendingUp /></div>
                  <div className="stat-content">
                    <p>Active Orders</p>
                    <h3>{stats.activeOrders || 0}</h3>
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

