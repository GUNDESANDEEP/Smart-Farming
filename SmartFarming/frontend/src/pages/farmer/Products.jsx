import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { farmerAPI, authAPI, getErrorMessage } from '../../services/api';
import toast from 'react-hot-toast';
import SellerLayout from './SellerLayout';
import SmartProductImage from '../../utils/SmartProductImage';

const CATEGORIES = ['Vegetables', 'Fruits', 'Grains', 'Dairy', 'Spices', 'Pulses', 'Others'];
const UNITS = ['kg', 'quintal', 'ton', 'dozen', 'piece', 'liter', 'grams'];

const CATEGORY_MAP = {
  Vegetables: ['tomato','potato','onion','carrot','cabbage','cauliflower','brinjal','spinach','palak','radish','beetroot','cucumber','capsicum','peas','beans','okra','bhindi','mushroom','corn','ginger','garlic','coriander','broccoli','lettuce'],
  Fruits: ['apple','banana','mango','orange','grapes','watermelon','papaya','guava','pomegranate','pineapple','strawberry','cherry','peach','pear','fig','coconut','kiwi','lemon','lime'],
  Grains: ['rice','wheat','bajra','jowar','ragi','maize','oats','barley','quinoa','millet'],
  Dairy: ['milk','curd','butter','ghee','cheese','paneer','cream','yogurt'],
  Spices: ['turmeric','chilli','cumin','mustard','pepper','cardamom','cinnamon','clove','saffron'],
  Pulses: ['dal','lentil','rajma','chana','chickpea','soybean','groundnut','peanut'],
};

const autoDetectCategory = (name) => {
  if (!name || name.trim().length < 2) return '';
  const lower = name.toLowerCase().trim();
  for (const [cat, keywords] of Object.entries(CATEGORY_MAP)) {
    for (const kw of keywords) {
      if (lower.includes(kw) || kw.includes(lower)) return cat;
    }
  }
  return '';
};

const INITIAL_FORM = { name: '', description: '', category: '', price: '', quantity: '', unit: 'kg', location: '', discount: '', is_organic: false };

export default function FarmerProducts() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [products, setProducts] = useState([]);

  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({ ...INITIAL_FORM });
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [farmerLocation, setFarmerLocation] = useState(
    user?.location || localStorage.getItem('sf_farmer_location') || ''
  );
  const [editingLocation, setEditingLocation] = useState(false);
  const [tempLocation, setTempLocation] = useState('');
  const [platformFees, setPlatformFees] = useState({ gstPercent: 0, platformPercent: 0, deliveryFlat: 0 });
  const profileFetched = React.useRef(false);

  useEffect(() => {
    fetchProducts();
    loadAdminFees();
    // Re-fetch fees when user returns to this page
    const handleVisibility = () => { if (document.visibilityState === 'visible') loadAdminFees(); };
    const handleFocus = () => loadAdminFees();
    const handleStorage = (e) => { if (e.key === 'sf_admin_fees') loadAdminFees(); };
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('storage', handleStorage);
    if (!profileFetched.current && !user?.location) {
      profileFetched.current = true;
      authAPI.getProfile()
        .then(res => {
          const data = res.data?.user || res.data;
          if (data?.location) {
            setFarmerLocation(data.location);
            localStorage.setItem('sf_farmer_location', data.location);
            const stored = JSON.parse(localStorage.getItem('user') || '{}');
            stored.location = data.location;
            localStorage.setItem('user', JSON.stringify(stored));
          }
        })
        .catch(() => {});
    }
    return () => {
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const loadAdminFees = () => {
    try {
      const stored = JSON.parse(localStorage.getItem('sf_admin_fees') || '{}');
      if (stored.gstPercent !== undefined) {
        setPlatformFees({
          gstPercent: parseFloat(stored.gstPercent) || 0,
          platformPercent: parseFloat(stored.platformPercent) || 0,
          deliveryFlat: parseFloat(stored.deliveryFlat) || 0,
        });
      }
    } catch {}
  };

  // Local location cache — deployed backend doesn't store location per product
  const getLocationCache = () => {
    try { return JSON.parse(localStorage.getItem('sf_product_locations') || '{}'); } catch { return {}; }
  };
  const saveLocationToCache = (productId, location) => {
    if (!productId || !location) return;
    const cache = getLocationCache();
    cache[productId] = location;
    localStorage.setItem('sf_product_locations', JSON.stringify(cache));
  };

  const fetchProducts = async () => {
    try {
      const res = await farmerAPI.getProducts(1, 100);
      const data = res.data;
      const list = Array.isArray(data) ? data : data.products || data.data || [];
      // Merge cached locations into product data
      const locationCache = getLocationCache();
      const enriched = list.map(p => ({
        ...p,
        location: p.location || locationCache[p._id || p.id] || '',
      }));
      setProducts(enriched);
    } catch { setProducts([]); }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const updated = { ...formData, [name]: type === 'checkbox' ? checked : value };
    if (name === 'name') {
      const detected = autoDetectCategory(value);
      if (detected && detected !== formData.category) {
        updated.category = detected;
        toast.success(`Category auto-set: ${detected}`, { icon: '🏷️', duration: 2000 });
      }
    }
    setFormData(updated);
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const openAddModal = () => {
    setEditingProduct(null);
    setFormData({ ...INITIAL_FORM });
    setImageFile(null);
    setImagePreview(null);
    setShowModal(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name || '',
      description: product.description || '',
      category: product.category || '',
      price: product.price || '',
      quantity: product.stockQuantity || product.quantity || '',
      unit: product.unit || 'kg',
      location: product.location || '',
      discount: product.discount || product.discount_percentage || product.discount_percent || '',
      is_organic: product.is_organic || false,
    });
    setImageFile(null);
    setImagePreview(product.image_url || null);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formData.name || !formData.price || !formData.quantity) {
      toast.error('Please fill in name, price, and quantity'); return;
    }
    setSaving(true);
    try {
      // Build payload matching backend format
      const payload = {
        name: formData.name,
        description: formData.description || formData.name,
        price: parseFloat(formData.price),
        quantity: parseInt(formData.quantity),
        category: formData.category || 'Others',
        unit: formData.unit || 'kg',
        location: formData.location || '',
        discount_percentage: parseFloat(formData.discount) || 0,
        is_organic: formData.is_organic || false,
      };
      if (editingProduct) {
        await farmerAPI.updateProduct(editingProduct._id || editingProduct.id, payload);
        // Cache location locally since deployed backend may not store it
        saveLocationToCache(editingProduct._id || editingProduct.id, formData.location);
        toast.success('Product updated! ✅');
      } else {
        const createRes = await farmerAPI.createProduct(payload);
        // Cache location for the new product
        const newId = createRes?.data?._id || createRes?.data?.id || createRes?.data?.product?._id || createRes?.data?.product?.id;
        if (newId) saveLocationToCache(newId, formData.location);
        toast.success('Product created! 🎉');
      }
      setShowModal(false);
      setEditingProduct(null);
      setFormData({ ...INITIAL_FORM });
      fetchProducts();
    } catch (error) {
      const msg = getErrorMessage(error) || 'Failed to save product';
      toast.error('Save failed: ' + msg);
      console.error('[Products] Save error:', error.response?.data || error.message);
    } finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await farmerAPI.deleteProduct(id);
      toast.success('Product deleted!');
      fetchProducts();
    } catch { toast.error('Failed to delete product'); }
  };

  const handleStockUpdate = async (product, newQty) => {
    try {
      await farmerAPI.updateProduct(product._id || product.id, { quantity: newQty });
      toast.success('Stock updated!');
      fetchProducts();
    } catch { toast.error('Failed to update stock'); }
  };

  const filteredProducts = products.filter(p => {
    const qty = p.stockQuantity ?? p.quantity ?? 0;
    if (filter === 'in_stock') return qty > 0;
    if (filter === 'low_stock') return qty > 0 && qty <= 20;
    if (filter === 'out_of_stock') return qty <= 0;
    if (filter === 'approved') return p.status === 'approved';
    if (filter === 'pending') return p.status === 'pending';
    return true;
  }).filter(p => !searchQuery || p.name?.toLowerCase().includes(searchQuery.toLowerCase()));

  const stockStats = {
    total: products.length,
    inStock: products.filter(p => (p.stockQuantity ?? p.quantity ?? 0) > 0).length,
    lowStock: products.filter(p => { const q = p.stockQuantity ?? p.quantity ?? 0; return q > 0 && q <= 20; }).length,
    outOfStock: products.filter(p => (p.stockQuantity ?? p.quantity ?? 0) <= 0).length,
  };

  return (
    <SellerLayout title="Products" subtitle="Manage your product catalog">
      {/* Stats */}
      <div className="seller-stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
        {[
          { label: 'Total Products', value: stockStats.total, icon: '📦', color: 'green' },
          { label: 'In Stock', value: stockStats.inStock, icon: '✅', color: 'teal' },
          { label: 'Low Stock', value: stockStats.lowStock, icon: '⚠️', color: 'amber' },
          { label: 'Out of Stock', value: stockStats.outOfStock, icon: '❌', color: 'rose' },
        ].map((s, i) => (
          <div key={i} className="seller-stat-card">
            <div className={`seller-stat-icon ${s.color}`}>{s.icon}</div>
            <div className="seller-stat-info">
              <p>{s.label}</p>
              <h3>{s.value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Farm Location Banner */}
      <div style={{ background: farmerLocation ? 'linear-gradient(135deg, #f0fdf4, #dcfce7)' : 'linear-gradient(135deg, #fffbeb, #fef3c7)', border: `1px solid ${farmerLocation ? '#bbf7d0' : '#fde68a'}`, borderRadius: 12, padding: '10px 16px', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        {editingLocation || !farmerLocation ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '1.2rem' }}>📍</span>
              <span style={{ fontSize: '0.82rem', color: farmerLocation ? '#166534' : '#92400e', fontWeight: 600 }}>
                {farmerLocation ? 'Update your farm location:' : 'Set your farm location to show it on all products'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input type="text" placeholder="e.g., Hyderabad, Telangana" value={tempLocation} onChange={e => setTempLocation(e.target.value)}
                className="seller-form-input" style={{ padding: '7px 12px', fontSize: '0.8rem', minWidth: 200 }} />
              <button onClick={() => { if (tempLocation.trim()) { setFarmerLocation(tempLocation.trim()); localStorage.setItem('sf_farmer_location', tempLocation.trim()); setTempLocation(''); setEditingLocation(false); toast.success('Farm location saved! 📍'); } }}
                style={{ padding: '7px 16px', borderRadius: 8, border: 'none', background: '#166534', color: '#fff', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}>Save</button>
              {farmerLocation && <button onClick={() => setEditingLocation(false)} style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff', color: '#6b7280', fontSize: '0.78rem', cursor: 'pointer' }}>Cancel</button>}
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '1rem' }}>📍</span>
              <span style={{ fontSize: '0.82rem', color: '#166534', fontWeight: 600 }}>Farm Location:</span>
              <span style={{ fontSize: '0.85rem', color: '#14532d', fontWeight: 700 }}>{farmerLocation}</span>
            </div>
            <button onClick={() => { setTempLocation(farmerLocation); setEditingLocation(true); }}
              style={{ padding: '5px 14px', borderRadius: 8, border: '1px solid #86efac', background: '#fff', color: '#166534', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}>✏️ Change</button>
          </>
        )}
      </div>

      {/* Toolbar */}
      <div className="seller-card" style={{ marginBottom: 16 }}>
        <div className="seller-card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', flex: 1 }}>
            <input
              type="text"
              placeholder="🔍 Search products..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="seller-form-input"
              style={{ maxWidth: 260, padding: '9px 14px' }}
            />
            <div className="seller-tabs-pill" style={{ marginBottom: 0 }}>
              {[
                { key: 'all', label: 'All' },
                { key: 'in_stock', label: 'In Stock' },
                { key: 'low_stock', label: '⚠️ Low' },
                { key: 'out_of_stock', label: 'Out' },
              ].map(f => (
                <button key={f.key} className={`seller-tab-pill ${filter === f.key ? 'active' : ''}`} onClick={() => setFilter(f.key)}>
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <button className="seller-btn seller-btn-primary" onClick={openAddModal}>
            ➕ Add Product
          </button>
        </div>
      </div>

      {/* Product Grid */}
      {filteredProducts.length === 0 ? (
        <div className="seller-card">
          <div className="seller-empty-state">
            <div className="empty-icon">📦</div>
            <h3>No products found</h3>
            <p>{searchQuery ? 'Try a different search term' : 'Start adding products to your catalog'}</p>
            <button className="seller-btn seller-btn-primary" style={{ marginTop: 16 }} onClick={openAddModal}>Add Your First Product</button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {filteredProducts.map(product => {
            const qty = parseFloat(product.stockQuantity ?? product.quantity) || 0;
            const isSoldOut = qty <= 0;
            const isLowStock = qty > 0 && qty <= 20;
            return (
              <div key={product._id || product.id} className="seller-card" style={{ opacity: isSoldOut ? 0.7 : 1, position: 'relative' }}>
                {/* Status Ribbon */}
                {isSoldOut && (
                  <div style={{ position: 'absolute', top: 12, right: 12, zIndex: 5, background: '#dc2626', color: '#fff', padding: '3px 10px', borderRadius: 6, fontSize: '0.65rem', fontWeight: 800, letterSpacing: 1 }}>
                    SOLD OUT
                  </div>
                )}
                {isLowStock && (
                  <div style={{ position: 'absolute', top: 12, right: 12, zIndex: 5, background: '#f59e0b', color: '#fff', padding: '3px 10px', borderRadius: 6, fontSize: '0.65rem', fontWeight: 700 }}>
                    LOW STOCK
                  </div>
                )}

                {/* Product Image */}
                <div style={{ width: '100%', height: 140, background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                  <SmartProductImage
                    product={product}
                    alt={product.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                </div>

                <div className="seller-card-body" style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                    <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#14532d' }}>{product.name}</h3>
                    <span className={`seller-badge ${product.status === 'approved' ? 'seller-badge-success' : product.status === 'rejected' ? 'seller-badge-danger' : 'seller-badge-warning'}`}>
                      {product.status || 'pending'}
                    </span>
                  </div>

                  <p style={{ fontSize: '1.15rem', fontWeight: 800, color: '#166534', margin: '4px 0' }}>
                    ₹{product.price}/{product.unit || 'kg'}
                  </p>

                  {(product.discount || product.discount_percentage || product.discount_percent) > 0 && (
                    <span style={{ background: 'linear-gradient(135deg, #ef4444, #f97316)', color: '#fff', padding: '2px 10px', borderRadius: 12, fontSize: '0.68rem', fontWeight: 700 }}>
                      🔥 {product.discount || product.discount_percentage || product.discount_percent}% OFF
                    </span>
                  )}

                  <div style={{ margin: '10px 0', display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>📍 {product.location || farmerLocation || user?.location || 'N/A'}</span>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>🏷️ {product.category || 'Others'}</span>
                    {product.is_organic && <span className="seller-badge seller-badge-success">🌿 Organic</span>}
                  </div>

                  {/* Stock Management */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '10px 0', padding: '8px 10px', background: isSoldOut ? '#fef2f2' : isLowStock ? '#fffbeb' : '#f0fdf4', borderRadius: 8 }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: isSoldOut ? '#dc2626' : isLowStock ? '#d97706' : '#15803d' }}>
                      Stock: {qty} {product.unit || 'kg'}
                    </span>
                    <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
                      <button className="seller-btn seller-btn-sm seller-btn-secondary" style={{ padding: '4px 10px', fontSize: '0.72rem' }} onClick={() => handleStockUpdate(product, qty + 10)}>
                        +10
                      </button>
                      <button className="seller-btn seller-btn-sm seller-btn-secondary" style={{ padding: '4px 10px', fontSize: '0.72rem' }} onClick={() => handleStockUpdate(product, qty + 50)}>
                        +50
                      </button>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                    <button className="seller-btn seller-btn-secondary seller-btn-sm" style={{ flex: 1 }} onClick={() => openEditModal(product)}>
                      ✏️ Edit
                    </button>
                    <button className="seller-btn seller-btn-sm" style={{ flex: 1, background: '#fef2f2', color: '#dc2626', border: '1px solid #fca5a533' }} onClick={() => handleDelete(product._id || product.id)}>
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add/Edit Product Modal */}
      {showModal && (
        <div className="seller-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="seller-modal" style={{ maxWidth: 600 }} onClick={e => e.stopPropagation()}>
            <div className="seller-modal-header">
              <h3>{editingProduct ? '✏️ Edit Product' : '➕ Add New Product'}</h3>
              <button className="seller-modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <div className="seller-modal-body">
              {/* Image Upload */}
              <div className="seller-form-group">
                <label className="seller-form-label">Product Image</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ width: 80, height: 80, borderRadius: 12, background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px dashed rgba(22,163,74,0.2)', overflow: 'hidden' }}>
                    {imagePreview ? (
                      <img src={imagePreview} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : formData.name && formData.name.trim().length >= 2 ? (
                      <SmartProductImage
                        product={{ name: formData.name, category: formData.category }}
                        alt="Auto preview"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <span style={{ fontSize: '1.5rem' }}>📷</span>
                    )}
                  </div>
                  <div>
                    <input type="file" accept="image/*" onChange={handleImageChange} style={{ fontSize: '0.82rem' }} />
                    <p style={{ fontSize: '0.68rem', color: '#9ca3af', margin: '4px 0 0' }}>JPG, PNG up to 5MB — or auto-image by product name</p>
                  </div>
                </div>
              </div>

              <div className="seller-form-row">
                <div className="seller-form-group">
                  <label className="seller-form-label">Product Name *</label>
                  <input className="seller-form-input" name="name" value={formData.name} onChange={handleChange} placeholder="e.g. Fresh Tomatoes" />
                </div>
                <div className="seller-form-group">
                  <label className="seller-form-label">Category</label>
                  <select className="seller-form-select" name="category" value={formData.category} onChange={handleChange}>
                    <option value="">Select Category</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>

              <div className="seller-form-group">
                <label className="seller-form-label">Description</label>
                <textarea className="seller-form-textarea" name="description" value={formData.description} onChange={handleChange} placeholder="Describe your product quality, freshness..." />
              </div>

              <div className="seller-form-row">
                <div className="seller-form-group">
                  <label className="seller-form-label">Price (₹) *</label>
                  <input className="seller-form-input" name="price" type="number" value={formData.price} onChange={handleChange} placeholder="0.00" />
                </div>
                <div className="seller-form-group">
                  <label className="seller-form-label">Quantity *</label>
                  <input className="seller-form-input" name="quantity" type="number" value={formData.quantity} onChange={handleChange} placeholder="0" />
                </div>
              </div>

              <div className="seller-form-row">
                <div className="seller-form-group">
                  <label className="seller-form-label">Unit</label>
                  <select className="seller-form-select" name="unit" value={formData.unit} onChange={handleChange}>
                    {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
                  </select>
                </div>
                <div className="seller-form-group">
                  <label className="seller-form-label">Discount (%)</label>
                  <input className="seller-form-input" name="discount" type="number" min="0" max="90" value={formData.discount} onChange={handleChange} placeholder="0" />
                </div>
              </div>

              <div className="seller-form-group">
                <label className="seller-form-label">Location</label>
                <input className="seller-form-input" name="location" value={formData.location} onChange={handleChange} placeholder="e.g. Pune, Maharashtra" />
              </div>

              <div className="seller-form-group" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input type="checkbox" name="is_organic" checked={formData.is_organic} onChange={handleChange} id="organic-check" style={{ width: 18, height: 18, accentColor: '#22c55e' }} />
                <label htmlFor="organic-check" style={{ fontSize: '0.85rem', color: '#14532d', fontWeight: 500, cursor: 'pointer' }}>
                  🌿 Mark as Organic Product
                </label>
              </div>
            </div>
            <div className="seller-modal-footer">
              <button className="seller-btn seller-btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="seller-btn seller-btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? '⏳ Saving...' : editingProduct ? '✅ Update Product' : '➕ Create Product'}
              </button>
            </div>
          </div>
        </div>
      )}
    </SellerLayout>
  );
}
