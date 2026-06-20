import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { FiShoppingCart, FiSearch, FiPlus, FiMinus, FiTrash2, FiPackage, FiStar, FiMapPin, FiPhone, FiDownload, FiEye, FiSave, FiCheck, FiChevronRight, FiCreditCard, FiTruck, FiShield, FiClock, FiChevronDown, FiArrowLeft } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { buyerAPI, paymentsAPI } from '../services/api';
import ReceiptViewer from '../components/ReceiptViewer';
import '../styles/dashboard.css';


import { PLACEHOLDER_IMG } from '../utils/productImages';
import SmartProductImage from '../utils/SmartProductImage';

const BuyerShop = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [addingToCart, setAddingToCart] = useState({});
  const [notifiedDiscounts, setNotifiedDiscounts] = useState(new Set());


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

  // Get low-stock and sold-out products for the ticker
  const lowStockProducts = products.filter(p => {
    const qty = parseFloat(p.quantity) || 0;
    return qty > 0 && qty <= 20;
  });

  const soldOutProducts = products.filter(p => {
    const qty = parseFloat(p.quantity) || 0;
    return qty <= 0 || p.status === 'sold_out';
  });

  return (
    <div className="dashboard-section">
      {/* === SCROLLING STOCK TICKER === */}
      {lowStockProducts.length > 0 && (
        <div className="stock-ticker-wrapper">
          <div className="stock-ticker-track">
            {/* Duplicate items for seamless infinite scroll */}
            {[...lowStockProducts, ...lowStockProducts].map((p, i) => (
              <div key={`${p.id}-${i}`} className="stock-ticker-item">
                <span className="ticker-dot" />
                <span>{p.name}</span>
                <span className="ticker-qty">Only {Math.floor(parseFloat(p.quantity))} {p.unit || 'units'} left!</span>
              </div>
            ))}
          </div>
        </div>
      )}

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
          {filteredProducts.map(product => {
            const qty = parseFloat(product.quantity) || 0;
            const isSoldOut = qty <= 0 || product.status === 'sold_out';
            const isLowStock = qty > 0 && qty <= 20;
            return (
            <div key={product.id} className={`product-card-buyer ${(product.discount || product.discount_percent) > 0 ? 'discount-shimmer' : ''}`}
              style={{ opacity: isSoldOut ? 0.7 : 1 }}>
              <div className="product-image" style={{ position: 'relative' }}>
                <SmartProductImage
                  product={product}
                  alt={product.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                {product.organic && <span className="organic-badge">🌿 Organic</span>}
                {(product.discount || product.discount_percent) > 0 && (
                  <div className="discount-banner">
                    <span className="discount-text">🔥 {product.discount || product.discount_percent}% OFF</span>
                  </div>
                )}
                {/* SOLD OUT overlay on image */}
                {isSoldOut && (
                  <div className="sold-out-badge-buyer">
                    <span>SOLD OUT</span>
                  </div>
                )}
                {/* LOW STOCK badge on image */}
                {isLowStock && (
                  <div className="low-stock-indicator-buyer">
                    ⚡ Only {Math.floor(qty)} left!
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
                  {isLowStock && (
                    <span style={{
                      background: 'rgba(239,68,68,0.1)', color: '#dc2626',
                      padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700,
                    }}>
                      Low Stock
                    </span>
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
                  {isSoldOut ? (
                    <button className="btn-add-cart" disabled
                      style={{ background: '#9ca3af', cursor: 'not-allowed', opacity: 0.7 }}>
                      Sold Out
                    </button>
                  ) : (
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
                  )}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const BuyerCart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [checkoutStep, setCheckoutStep] = useState(1);
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [houseNumber, setHouseNumber] = useState('');
  const [street, setStreet] = useState('');
  const [city, setCity] = useState('');
  const [addrState, setAddrState] = useState('');
  const [pincode, setPincode] = useState('');
  const [notes, setNotes] = useState('');
  const [placing, setPlacing] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const navigate = useNavigate();

  const fetchCart = useCallback(async () => {
    try {
      const response = await buyerAPI.getCart();
      const data = response.data;
      const items = Array.isArray(data) ? data : (data.items || data.cart || []);
      setCartItems(items);
      setSelectedItems(new Set(items.map(i => i.id)));
      setLoading(false);
    } catch (error) { setCartItems([]); setLoading(false); }
  }, []);

  useEffect(() => {
    fetchCart();
    (async () => {
      try {
        const res = await buyerAPI.getProfile();
        const p = res.data?.profile || res.data;
        if (p) {
          setUserProfile(p);
          if (p.house_number || p.address) setHouseNumber(p.house_number || p.address || '');
          if (p.location || p.street) setStreet(p.location || p.street || '');
          if (p.city) setCity(p.city);
          if (p.state) setAddrState(p.state);
          if (p.pincode) setPincode(String(p.pincode));
        }
      } catch {}
    })();
  }, [fetchCart]);

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    try {
      await buyerAPI.updateCartItem(itemId, newQuantity);
      setCartItems(prev => prev.map(item =>
        item.id === itemId ? { ...item, quantity: newQuantity } : item
      ));
    } catch (error) { toast.error('Failed to update quantity'); }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      await buyerAPI.removeFromCart(itemId);
      setCartItems(prev => prev.filter(item => item.id !== itemId));
      toast.success('Item removed from cart');
    } catch (error) { toast.error('Failed to remove item'); }
  };

  const handlePlaceOrder = async () => {
    if (!houseNumber.trim()) { toast.error('Please enter house number'); setCheckoutStep(2); return; }
    if (!pincode.trim() || !/^[0-9]{6}$/.test(pincode.trim())) { toast.error('Please enter valid 6-digit pincode'); setCheckoutStep(2); return; }
    setPlacing(true);
    try {
      if (paymentMethod === 'online') {
        const orderRes = await paymentsAPI.createOrder({
          amount: grandTotal, currency: 'INR', delivery_fee: deliveryFee,
          cart_items: cartItems.map(item => ({ product_id: item.product_id || item.id, quantity: Math.floor(item.quantity) || 1, price: item.price })),
          delivery_address: deliveryAddress, notes,
        });
        const { order_id, key_id, amount: amountPaise } = orderRes.data;
        const options = {
          key: key_id, amount: amountPaise, currency: 'INR', name: 'SmartFarm Marketplace',
          description: `${cartItems.length} item(s) - Fresh from Farm`, order_id,
          prefill: { name: localStorage.getItem('user_name') || '', email: localStorage.getItem('user_email') || '', contact: localStorage.getItem('user_phone') || '' },
          theme: { color: '#166534' },
          method: { upi: true, card: true, netbanking: true, wallet: true, paylater: true },
          config: { display: { blocks: { utib: { name: 'Pay using UPI', instruments: [{ method: 'upi', flows: ['qrcode', 'collect', 'intent'] }] } }, sequence: ['block.utib'], preferences: { show_default_blocks: true } } },
          handler: async function (response) {
            try {
              const verifyRes = await paymentsAPI.verifyPayment({
                razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature, delivery_address: deliveryAddress, notes,
                cart_items: cartItems.map(item => ({ product_id: item.product_id || item.id, quantity: Math.floor(item.quantity) || 1, price: item.price })),
              });
              setOrderSuccess(verifyRes.data); setCartItems([]);
              toast.success('Payment successful! Order placed! 🎉', { duration: 5000 });
            } catch (ve) { toast.error(ve.response?.data?.error || 'Payment verification failed.'); }
            finally { setPlacing(false); }
          },
          modal: { ondismiss: () => { setPlacing(false); toast('Payment cancelled', { icon: '⚠️' }); }, confirm_close: true },
        };
        if (typeof window.Razorpay === 'undefined') { toast.error('Payment gateway loading...'); setPlacing(false); return; }
        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', (r) => { setPlacing(false); toast.error(`Payment failed: ${r.error.description || 'Unknown'}`, { duration: 5000 }); });
        rzp.open(); return;
      } else {
        const res = await buyerAPI.checkout({ payment_method: paymentMethod, delivery_address: deliveryAddress, notes, delivery_fee: deliveryFee });
        setOrderSuccess(res.data); setCartItems([]);
        toast.success(`${res.data.orders?.length || 1} order(s) placed!`, { icon: '🎉', duration: 4000 });
      }
    } catch (error) { toast.error(error.response?.data?.error || 'Checkout failed'); }
    finally { setPlacing(false); }
  };

  const selectedCartItems = cartItems.filter(item => selectedItems.has(item.id));
  const total = selectedCartItems.reduce((sum, item) => sum + ((item.price || 0) * (Math.floor(item.quantity) || 1)), 0);
  const deliveryFee = total >= 500 ? 0 : 30;
  const grandTotal = total + deliveryFee;
  const allSelected = cartItems.length > 0 && selectedItems.size === cartItems.length;

  const toggleSelectItem = (id) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };
  const toggleSelectAll = () => {
    if (allSelected) setSelectedItems(new Set());
    else setSelectedItems(new Set(cartItems.map(i => i.id)));
  };
  const deliveryDate = new Date(); deliveryDate.setDate(deliveryDate.getDate() + 4);
  const deliveryDateStr = deliveryDate.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' });
  const userName = userProfile?.first_name || localStorage.getItem('user_name') || 'Customer';
  const userPhone = userProfile?.phone || localStorage.getItem('user_phone') || '';
  const deliveryAddress = [houseNumber, street, city, addrState, pincode].filter(Boolean).join(', ');

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  // ── Order Success ──
  if (orderSuccess) {
    return (
      <div className="dashboard-section">
        <div style={{ textAlign: 'center', padding: '3rem 1rem', background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)', borderRadius: '20px', border: '1px solid #22c55e33' }}>
          <div style={{ fontSize: '4rem', marginBottom: '16px' }}>✅</div>
          <h2 style={{ color: '#14532d', marginBottom: '8px' }}>Order Placed Successfully!</h2>
          <p style={{ color: '#166534', fontSize: '1.1rem', marginBottom: '6px' }}>{orderSuccess.orders?.length || 1} order(s) • Total: ₹{orderSuccess.total_amount?.toFixed(2)}</p>
          <p style={{ color: '#15803d', fontSize: '0.9rem', marginBottom: '24px' }}>Payment: {orderSuccess.payment_method === 'cod' ? '💰 Cash on Delivery' : '💳 Online'}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '400px', margin: '0 auto 24px' }}>
            {(orderSuccess.orders || []).map((o, i) => (
              <div key={i} style={{ background: '#fff', borderRadius: '10px', padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid #22c55e22' }}>
                <span style={{ fontWeight: 600, color: '#14532d' }}>{o.order_number}</span>
                <span style={{ color: '#666' }}>{o.product_name} × {o.quantity}</span>
                <span style={{ fontWeight: 700, color: '#166534' }}>₹{o.total}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button className="btn-primary" onClick={() => navigate('/buyer/orders')} style={{ padding: '12px 24px', borderRadius: '12px', fontWeight: 600 }}>📦 View Orders</button>
            <button onClick={() => navigate('/buyer/shop')} style={{ padding: '12px 24px', borderRadius: '12px', fontWeight: 600, background: '#f0fdf4', color: '#166534', border: '1px solid #22c55e33', cursor: 'pointer' }}>🛒 Continue Shopping</button>
          </div>
        </div>
      </div>
    );
  }

  // ── Step Labels ──
  const stepLabels = ['Cart', 'Address', 'Summary', 'Payment'];

  return (
    <div className="dashboard-section" style={{ paddingBottom: '0' }}>
      
      {/* Back Button */}
      {checkoutStep > 1 && (
        <button onClick={() => setCheckoutStep(checkoutStep - 1)}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', border: 'none', color: '#166534', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer', padding: '4px 0', marginBottom: '8px', fontFamily: 'Poppins, sans-serif' }}>
          <FiArrowLeft size={18} /> Back
        </button>
      )}

      {/* ── STEP PROGRESS BAR ── */}
      {cartItems.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '12px 0 18px', gap: '0' }}>
          {stepLabels.map((label, i) => {
            const sn = i + 1; const isActive = checkoutStep === sn; const isDone = checkoutStep > sn;
            return (
              <React.Fragment key={label}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px', minWidth: '55px' }}>
                  <div style={{
                    width: '30px', height: '30px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.75rem', fontWeight: 700,
                    background: isDone ? '#22c55e' : isActive ? '#166534' : '#e5e7eb',
                    color: isDone || isActive ? '#fff' : '#9ca3af', transition: 'all 0.3s',
                    cursor: isDone ? 'pointer' : 'default',
                  }} onClick={() => isDone && setCheckoutStep(sn)}>
                    {isDone ? <FiCheck size={15} /> : sn}
                  </div>
                  <span style={{ fontSize: '0.62rem', fontWeight: isActive ? 700 : 500, color: isActive ? '#166534' : isDone ? '#22c55e' : '#9ca3af', textAlign: 'center' }}>{label}</span>
                </div>
                {i < stepLabels.length - 1 && (
                  <div style={{ flex: 1, height: '2px', maxWidth: '40px', background: checkoutStep > sn ? '#22c55e' : '#e5e7eb', margin: '0 2px', marginBottom: '20px', transition: 'background 0.3s' }} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}

      {cartItems.length === 0 ? (
        <div className="empty-state">
          <FiShoppingCart size={48} /><h3>Your cart is empty</h3><p>Browse products and add items to your cart</p>
          <button className="btn-primary" onClick={() => navigate('/buyer/shop')}>Browse Products</button>
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 2px 16px rgba(22,101,52,0.06)', overflow: 'hidden' }}>

          {/* === STEP 1: CART === */}
          {checkoutStep === 1 && (<>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0, color: '#14532d', fontSize: '1rem' }}>🛒 Cart ({cartItems.length} {cartItems.length === 1 ? 'item' : 'items'})</h3>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.78rem', color: '#166534', fontWeight: 600, userSelect: 'none' }}>
                <input type="checkbox" checked={allSelected} onChange={toggleSelectAll}
                  style={{ width: '17px', height: '17px', accentColor: '#166534', cursor: 'pointer' }} />
                {allSelected ? 'Deselect All' : 'Select All'}
              </label>
            </div>
            {cartItems.map((item, idx) => {
              const qty = Math.floor(item.quantity) || 1;
              const isSelected = selectedItems.has(item.id);
              return (
                <div key={item.id} style={{ padding: '14px 20px', borderBottom: idx < cartItems.length - 1 ? '1px solid #f5f5f5' : 'none', opacity: isSelected ? 1 : 0.5, transition: 'opacity 0.2s' }}>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <input type="checkbox" checked={isSelected} onChange={() => toggleSelectItem(item.id)}
                      style={{ width: '18px', height: '18px', accentColor: '#166534', cursor: 'pointer', marginTop: '28px', flexShrink: 0 }} />
                    <SmartProductImage product={item} alt={item.name || item.product_name}
                      style={{ width: '75px', height: '75px', borderRadius: '10px', objectFit: 'cover', border: '1px solid #f0f0f0' }} />
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: '0 0 3px', fontSize: '0.92rem', color: '#1f2937', fontWeight: 600 }}>{item.name || item.product_name}</h4>
                      <p style={{ margin: '0 0 3px', fontSize: '0.75rem', color: '#6b7280' }}>{item.farmer_name || 'Local Farmer'}{item.category ? ` • ${item.category}` : ''}</p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                        <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#14532d' }}>₹{(item.price * qty).toFixed(0)}</span>
                        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>₹{item.price}/{item.unit || 'kg'}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.7rem', color: '#22c55e', fontWeight: 500 }}>
                        <FiTruck size={10} style={{ marginRight: '3px', verticalAlign: 'middle' }} />
                        Delivery by {deliveryDateStr}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', paddingTop: '8px', borderTop: '1px dashed #f0f0f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', border: '1.5px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
                      <button onClick={() => handleUpdateQuantity(item.id, qty - 1)} disabled={qty <= 1}
                        style={{ width: '34px', height: '34px', border: 'none', background: qty <= 1 ? '#f9fafb' : '#fff', cursor: qty <= 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: qty <= 1 ? '#d1d5db' : '#166534', fontSize: '1.1rem', fontWeight: 700 }}>−</button>
                      <span style={{ width: '40px', height: '34px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderLeft: '1.5px solid #e5e7eb', borderRight: '1.5px solid #e5e7eb', fontWeight: 700, fontSize: '0.9rem', color: '#14532d', background: '#f0fdf4' }}>{qty}</span>
                      <button onClick={() => handleUpdateQuantity(item.id, qty + 1)}
                        style={{ width: '34px', height: '34px', border: 'none', background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#166534', fontSize: '1.1rem', fontWeight: 700 }}>+</button>
                    </div>
                    <button onClick={() => handleRemoveItem(item.id)}
                      style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'none', border: '1px solid #fecaca', borderRadius: '8px', padding: '7px 12px', color: '#dc2626', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'Poppins, sans-serif' }}>
                      <FiTrash2 size={12} /> Remove
                    </button>
                  </div>
                </div>
              );
            })}
            {total < 500 && (
              <div style={{ padding: '10px 20px', background: '#fffbeb', borderTop: '1px solid #fde68a', fontSize: '0.78rem', color: '#92400e' }}>
                🚚 Add ₹{(500 - total).toFixed(0)} more for <b>FREE delivery</b>
              </div>
            )}
            {/* Sticky Bottom */}
            <div style={{ position: 'sticky', bottom: '0', background: '#fff', borderTop: '1px solid #e5e7eb', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 -4px 20px rgba(0,0,0,0.06)' }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#6b7280', fontWeight: 500 }}>{selectedItems.size} of {cartItems.length} item{cartItems.length !== 1 ? 's' : ''} selected</div>
                {total > 0 && <div style={{ fontSize: '0.65rem', color: '#9ca3af', textDecoration: 'line-through' }}>₹{(total * 1.15).toFixed(0)}</div>}
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#14532d' }}>₹{grandTotal.toFixed(0)}</div>
              </div>
              <button onClick={() => { if (selectedItems.size === 0) { toast.error('Select at least one item'); return; } setCheckoutStep(2); }}
                disabled={selectedItems.size === 0}
                style={{ padding: '12px 32px', borderRadius: '12px', fontWeight: 700, background: selectedItems.size === 0 ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none', fontSize: '0.95rem', cursor: selectedItems.size === 0 ? 'not-allowed' : 'pointer', fontFamily: 'Poppins, sans-serif', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: selectedItems.size === 0 ? 'none' : '0 4px 15px rgba(22,101,52,0.3)' }}>
                Continue <FiChevronRight size={16} />
              </button>
            </div>
          </>)}

          {/* = = =  STEP 2: ADDRESS = = =  */}
          {checkoutStep === 2 && (() => {
            const fullAddress = [houseNumber, street, city, addrState, pincode].filter(Boolean).join(', ');
            const isAddressValid = houseNumber.trim() && pincode.trim() && /^[0-9]{6}$/.test(pincode.trim());
            const inputStyle = { width: '100%', padding: '11px 12px', borderRadius: '10px', border: '1.5px solid rgba(22,163,74,0.2)', fontFamily: 'Poppins, sans-serif', fontSize: '0.88rem', outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s' };
            const labelStyle = { display: 'block', marginBottom: '5px', color: '#14532d', fontWeight: 600, fontSize: '0.8rem' };
            const requiredStar = <span style={{ color: '#dc2626' }}> *</span>;
            return (<>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid #f0f0f0' }}>
              <h3 style={{ margin: 0, color: '#14532d', fontSize: '1rem' }}>📍 Delivery Address</h3>
            </div>
            <div style={{ padding: '18px 20px' }}>
              {/* Deliver To Preview Card */}
              {fullAddress && (
                <div style={{ background: '#f0fdf4', borderRadius: '12px', padding: '12px 14px', border: '1.5px solid #22c55e', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, color: '#14532d', fontSize: '0.9rem' }}>Deliver to:</span>
                    <span style={{ background: '#dcfce7', color: '#166534', fontSize: '0.58rem', fontWeight: 600, padding: '2px 8px', borderRadius: '4px' }}>HOME</span>
                  </div>
                  <p style={{ margin: '0 0 2px', fontWeight: 600, color: '#1f2937', fontSize: '0.88rem' }}>{userName}</p>
                  <p style={{ margin: '0 0 2px', color: '#4b5563', fontSize: '0.8rem', lineHeight: 1.4 }}>{fullAddress}</p>
                  {userPhone && <p style={{ margin: 0, color: '#6b7280', fontSize: '0.8rem' }}>📞 {userPhone}</p>}
                </div>
              )}

              {/* House Number */}
              <div style={{ marginBottom: '12px' }}>
                <label style={labelStyle}>House / Flat / Building No.{requiredStar}</label>
                <input value={houseNumber} onChange={(e) => setHouseNumber(e.target.value)}
                  placeholder="e.g. 28-5-339, Flat 201"
                  style={{ ...inputStyle, borderColor: !houseNumber.trim() && checkoutStep === 2 ? 'rgba(220,38,38,0.4)' : 'rgba(22,163,74,0.2)' }} />
                {!houseNumber.trim() && <p style={{ margin: '3px 0 0', fontSize: '0.7rem', color: '#dc2626' }}>House number is required</p>}
              </div>

              {/* Street / Colony */}
              <div style={{ marginBottom: '12px' }}>
                <label style={labelStyle}>Street / Colony / Area</label>
                <input value={street} onChange={(e) => setStreet(e.target.value)}
                  placeholder="e.g. Reddy Puram bypass road, Vijaya Laxmi Colony"
                  style={inputStyle} />
              </div>

              {/* City + State Row */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>City</label>
                  <input value={city} onChange={(e) => setCity(e.target.value)}
                    placeholder="e.g. Hanamkonda"
                    style={inputStyle} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>State</label>
                  <input value={addrState} onChange={(e) => setAddrState(e.target.value)}
                    placeholder="e.g. Telangana"
                    style={inputStyle} />
                </div>
              </div>

              {/* Pincode */}
              <div style={{ marginBottom: '12px' }}>
                <label style={labelStyle}>Pincode{requiredStar}</label>
                <input value={pincode} onChange={(e) => { const v = e.target.value.replace(/\D/g, '').slice(0, 6); setPincode(v); }}
                  placeholder="6-digit pincode (e.g. 506001)"
                  inputMode="numeric" maxLength={6}
                  style={{ ...inputStyle, width: '180px', letterSpacing: '2px', fontWeight: 600, borderColor: pincode && !/^[0-9]{6}$/.test(pincode) ? 'rgba(220,38,38,0.4)' : 'rgba(22,163,74,0.2)' }} />
                {pincode && !/^[0-9]{6}$/.test(pincode) && <p style={{ margin: '3px 0 0', fontSize: '0.7rem', color: '#dc2626' }}>Enter a valid 6-digit pincode</p>}
                {!pincode && <p style={{ margin: '3px 0 0', fontSize: '0.7rem', color: '#dc2626' }}>Pincode is required</p>}
              </div>

              {/* Notes */}
              <div>
                <label style={labelStyle}>Delivery Notes (optional)</label>
                <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Landmark, special instructions..."
                  style={inputStyle} />
              </div>
            </div>

            {/* Sticky Bottom */}
            <div style={{ position: 'sticky', bottom: '0', background: '#fff', borderTop: '1px solid #e5e7eb', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 -4px 20px rgba(0,0,0,0.06)' }}>
              <div><div style={{ fontSize: '0.7rem', color: '#9ca3af', textDecoration: 'line-through' }}>₹{(total * 1.15).toFixed(0)}</div><div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#14532d' }}>₹{grandTotal.toFixed(0)}</div></div>
              <button onClick={() => {
                  if (!houseNumber.trim()) { toast.error('Please enter house number'); return; }
                  if (!pincode.trim() || !/^[0-9]{6}$/.test(pincode.trim())) { toast.error('Please enter valid 6-digit pincode'); return; }
                  setCheckoutStep(3);
                }}
                disabled={!(houseNumber.trim() && pincode.trim() && /^[0-9]{6}$/.test(pincode.trim()))}
                style={{ padding: '12px 32px', borderRadius: '12px', fontWeight: 700, background: !(houseNumber.trim() && pincode.trim() && /^[0-9]{6}$/.test(pincode.trim())) ? '#9ca3af' : 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none', fontSize: '0.95rem', cursor: !(houseNumber.trim() && pincode.trim() && /^[0-9]{6}$/.test(pincode.trim())) ? 'not-allowed' : 'pointer', fontFamily: 'Poppins, sans-serif', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: !(houseNumber.trim() && pincode.trim() && /^[0-9]{6}$/.test(pincode.trim())) ? 'none' : '0 4px 15px rgba(22,101,52,0.3)' }}>
                Continue <FiChevronRight size={16} />
              </button>
            </div>
          </>); })()}

          {/* = = =  STEP 3: ORDER SUMMARY = = =  */}
          {checkoutStep === 3 && (<>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid #f0f0f0' }}>
              <h3 style={{ margin: 0, color: '#14532d', fontSize: '1rem' }}>📋 Order Summary</h3>
            </div>
            <div style={{ padding: '14px 20px' }}>
              {/* Deliver To Mini */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', borderRadius: '10px', padding: '10px 14px', marginBottom: '14px', border: '1px solid #e2e8f0' }}>
                <div>
                  <p style={{ margin: 0, fontSize: '0.72rem', color: '#64748b' }}>Deliver to</p>
                  <p style={{ margin: '2px 0 0', fontWeight: 600, color: '#1e293b', fontSize: '0.85rem' }}>{userName} — {deliveryAddress.length > 35 ? deliveryAddress.substring(0, 35) + '...' : deliveryAddress}</p>
                </div>
                <button onClick={() => setCheckoutStep(2)} style={{ background: 'none', border: '1px solid #166534', borderRadius: '8px', color: '#166534', padding: '5px 12px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'Poppins, sans-serif' }}>Change</button>
              </div>

              {/* Items */}
              {cartItems.map((item, idx) => {
                const qty = Math.floor(item.quantity) || 1;
                return (
                  <div key={item.id} style={{ display: 'flex', gap: '10px', padding: '10px 0', borderBottom: idx < cartItems.length - 1 ? '1px solid #f5f5f5' : 'none' }}>
                    <SmartProductImage product={item} alt={item.name || item.product_name} style={{ width: '55px', height: '55px', borderRadius: '8px', objectFit: 'cover', border: '1px solid #f0f0f0' }} />
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: '0 0 2px', fontWeight: 600, fontSize: '0.85rem', color: '#1f2937' }}>{item.name || item.product_name}</p>
                      <p style={{ margin: '0 0 3px', fontSize: '0.75rem', color: '#6b7280' }}>Qty: {qty} × ₹{item.price}/{item.unit || 'kg'}</p>
                      <p style={{ margin: 0, fontWeight: 700, color: '#14532d', fontSize: '0.92rem' }}>₹{(item.price * qty).toFixed(0)}</p>
                    </div>
                  </div>
                );
              })}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 0', borderTop: '1px solid #f0f0f0', color: '#166534', fontSize: '0.82rem', fontWeight: 500 }}>
                <FiTruck size={14} /> Delivery by <b>{deliveryDateStr}</b>
                {total >= 500 && <span style={{ color: '#22c55e', fontWeight: 600, marginLeft: '4px' }}>| FREE</span>}
              </div>
            </div>

            {/* Price Details */}
            <div style={{ padding: '14px 20px', borderTop: '6px solid #f5f5f5' }}>
              <h4 style={{ margin: '0 0 12px', color: '#1e293b', fontSize: '0.92rem', fontWeight: 700 }}>Price Details</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#4b5563' }}>
                  <span>Price ({cartItems.length} item{cartItems.length > 1 ? 's' : ''})</span><span>₹{total.toFixed(0)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#4b5563' }}>
                  <span>Delivery Charges</span>
                  <span style={{ color: total >= 500 ? '#22c55e' : '#4b5563', fontWeight: total >= 500 ? 600 : 400 }}>{total >= 500 ? 'FREE' : `₹${deliveryFee}`}</span>
                </div>
                <hr style={{ border: 'none', borderTop: '1px dashed #e5e7eb', margin: '2px 0' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1rem', color: '#14532d' }}>
                  <span>Total Amount</span><span>₹{grandTotal.toFixed(0)}</span>
                </div>
              </div>
              <div style={{ marginTop: '12px', padding: '10px 14px', background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)', borderRadius: '10px', border: '1px solid #bbf7d0', fontSize: '0.82rem', fontWeight: 600, color: '#166534' }}>
                🎉 You'll save <b>₹{deliveryFee === 0 ? '30' : '0'}</b> on delivery{total >= 500 ? '!' : ' when you add more items!'}
              </div>
            </div>

            <div style={{ position: 'sticky', bottom: '0', background: '#fff', borderTop: '1px solid #e5e7eb', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 -4px 20px rgba(0,0,0,0.06)' }}>
              <div><div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#14532d' }}>₹{grandTotal.toFixed(0)}</div></div>
              <button onClick={() => setCheckoutStep(4)}
                style={{ padding: '12px 32px', borderRadius: '12px', fontWeight: 700, background: 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none', fontSize: '0.95rem', cursor: 'pointer', fontFamily: 'Poppins, sans-serif', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 4px 15px rgba(22,101,52,0.3)' }}>
                Continue <FiChevronRight size={16} />
              </button>
            </div>
          </>)}

          {/* === STEP 4: PAYMENT === */}
          {checkoutStep === 4 && (<>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#14532d', fontSize: '1rem' }}>💳 Payment</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#6b7280', fontSize: '0.72rem' }}><FiShield size={12} color="#22c55e" /> 100% Secure</div>
            </div>

            {/* Total Bar */}
            <div style={{ padding: '10px 20px', background: '#f0fdf4', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #dcfce7' }}>
              <span style={{ color: '#166534', fontWeight: 600, fontSize: '0.88rem' }}>Total Amount</span>
              <span style={{ color: '#14532d', fontWeight: 800, fontSize: '1.1rem' }}>₹{grandTotal.toFixed(0)}</span>
            </div>

            <div style={{ padding: '14px 20px' }}>
              {/* Recommended */}
              <div style={{ background: '#fffbeb', borderRadius: '10px', padding: '12px 14px', border: '1px solid #fde68a', marginBottom: '14px' }}>
                <p style={{ margin: '0 0 4px', fontSize: '0.82rem', fontWeight: 700, color: '#92400e' }}>✨ Recommended for You</p>
                <p style={{ margin: 0, fontSize: '0.78rem', color: '#78716c' }}>Cash on Delivery — Pay when your fresh produce arrives!</p>
              </div>

              {/* UPI / Online */}
              <div onClick={() => setPaymentMethod('online')}
                style={{ padding: '14px', cursor: 'pointer', borderBottom: '1px solid #f0f0f0', background: paymentMethod === 'online' ? '#f0fdf4' : '#fff', transition: 'all 0.2s', borderRadius: paymentMethod === 'online' ? '10px' : '0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: paymentMethod === 'online' ? '5px solid #22c55e' : '2px solid #d1d5db', transition: 'all 0.2s' }} />
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: 0, fontWeight: 600, color: '#1f2937', fontSize: '0.9rem' }}>💳 UPI / Card / Net Banking</p>
                    <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: '#22c55e', fontWeight: 500 }}>Pay securely online via Razorpay</p>
                  </div>
                </div>
              </div>

              {/* COD */}
              <div onClick={() => setPaymentMethod('cod')}
                style={{ padding: '14px', cursor: 'pointer', borderBottom: '1px solid #f0f0f0', background: paymentMethod === 'cod' ? '#f0fdf4' : '#fff', transition: 'all 0.2s', borderRadius: paymentMethod === 'cod' ? '10px' : '0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: paymentMethod === 'cod' ? '5px solid #22c55e' : '2px solid #d1d5db', transition: 'all 0.2s' }} />
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: 0, fontWeight: 600, color: '#1f2937', fontSize: '0.9rem' }}>💰 Cash on Delivery</p>
                    <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: '#6b7280' }}>Pay when you receive your order</p>
                  </div>
                </div>
              </div>

              {/* Security Badges */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '18px', padding: '10px 0', borderTop: '1px solid #f0f0f0' }}>
                {[{icon: <FiShield size={18} color="#22c55e" />, t: 'Safe & Secure'}, {icon: <FiTruck size={18} color="#22c55e" />, t: 'Fast Delivery'}, {icon: <FiCheck size={18} color="#22c55e" />, t: 'Farm Fresh'}].map((b,i) => (
                  <div key={i} style={{ textAlign: 'center', fontSize: '0.65rem', color: '#9ca3af' }}>
                    <div style={{ marginBottom: '3px', display: 'flex', justifyContent: 'center' }}>{b.icon}</div>{b.t}
                  </div>
                ))}
              </div>
            </div>

            {/* Place Order */}
            <div style={{ position: 'sticky', bottom: '0', background: '#fff', borderTop: '1px solid #e5e7eb', padding: '14px 20px', boxShadow: '0 -4px 20px rgba(0,0,0,0.06)' }}>
              <button onClick={handlePlaceOrder} disabled={placing}
                style={{ width: '100%', padding: '15px', borderRadius: '12px', fontWeight: 700, background: placing ? '#9ca3af' : 'linear-gradient(135deg, #166534, #15803d, #22c55e)', color: '#fff', border: 'none', fontSize: '1rem', cursor: placing ? 'not-allowed' : 'pointer', fontFamily: 'Poppins, sans-serif', boxShadow: placing ? 'none' : '0 6px 20px rgba(22,101,52,0.35)', transition: 'all 0.3s' }}>
                {placing ? '⏳ Placing Order...' : `Place Order - ₹${grandTotal.toFixed(0)}`}
              </button>
              <p style={{ margin: '8px 0 0', textAlign: 'center', fontSize: '0.65rem', color: '#9ca3af', lineHeight: 1.4 }}>
                By placing this order, you agree to SmartFarm's Terms of Use and Privacy Policy
              </p>
            </div>
          </>)}

        </div>
      )}
    </div>
  );
};

// ============================================================================
// BuyerOrders – Full Order Lifecycle with Tracking, Reviews, Returns
// ============================================================================

const ORDER_STEPS = [
  { key: 'pending', label: 'Placed', icon: '📋' },
  { key: 'confirmed', label: 'Confirmed', icon: '✅' },
  { key: 'processing', label: 'Processing', icon: '⚙️' },
  { key: 'packed', label: 'Packed', icon: '📦' },
  { key: 'dispatched', label: 'Dispatched', icon: '🚚' },
  { key: 'in_transit', label: 'In Transit', icon: '🚛' },
  { key: 'out_for_delivery', label: 'Out for Delivery', icon: '🛵' },
  { key: 'delivered', label: 'Delivered', icon: '🎉' },
];

const BuyerOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [showReview, setShowReview] = useState(null);
  const [showReturn, setShowReturn] = useState(null);
  const [reviewData, setReviewData] = useState({
    product_rating: 5, product_review: '', farmer_rating: 5, farmer_review: '',
  });
  const [returnReason, setReturnReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

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

  const handleTrackOrder = async (orderId) => {
    try {
      const [trackRes, detailRes] = await Promise.all([
        buyerAPI.getOrderTracking(orderId),
        buyerAPI.getOrderDetail(orderId),
      ]);
      const trackData = trackRes.data;
      const detailData = detailRes.data?.order || detailRes.data || {};
      setTracking({ ...trackData, orderDetail: detailData });
      setSelectedOrder(orderId);
    } catch (error) {
      toast.error('Failed to load tracking');
    }
  };

  const handleCancelOrder = async (orderId) => {
    const reason = window.prompt('Reason for cancellation:');
    if (reason === null) return;
    try {
      await buyerAPI.cancelOrder(orderId, reason);
      toast.success('Order cancelled');
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to cancel');
    }
  };

  const handleSubmitReview = async () => {
    setSubmitting(true);
    try {
      await buyerAPI.submitReview(showReview, reviewData);
      toast.success('Review submitted! Thank you!');
      setShowReview(null);
      setReviewData({ product_rating: 5, product_review: '', farmer_rating: 5, farmer_review: '' });
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitReturn = async () => {
    if (!returnReason.trim()) { toast.error('Please enter a reason'); return; }
    setSubmitting(true);
    try {
      await buyerAPI.requestReturn(showReturn, { reason: returnReason });
      toast.success('Return request submitted');
      setShowReturn(null);
      setReturnReason('');
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to submit return');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f59e0b', confirmed: '#3b82f6', processing: '#8b5cf6',
      packed: '#6366f1', dispatched: '#0ea5e9', in_transit: '#14b8a6',
      out_for_delivery: '#f97316', delivered: '#22c55e', cancelled: '#ef4444',
      return_requested: '#dc2626',
    };
    return colors[status] || '#6b7280';
  };

  const getStepIndex = (status) => ORDER_STEPS.findIndex(s => s.key === status);

  if (loading) return <div className="loading-state"><div className="spinner"></div></div>;

  return (
    <div className="dashboard-section">
      <h2>My Orders</h2>
      {orders.length === 0 ? (
        <div className="empty-state">
          <FiPackage size={48} />
          <h3>No orders yet</h3>
          <p>Your orders will appear here</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {orders.map(order => {
            const currentStep = getStepIndex(order.status);
            const isCancelled = order.status === 'cancelled';
            const isDelivered = order.status === 'delivered';
            const isReturned = order.status === 'return_requested';
            const isConfirmed = ['confirmed', 'processing', 'packed', 'dispatched', 'in_transit', 'out_for_delivery'].includes(order.status);
            
            return (
              <div key={order.id} style={{
                background: 'rgba(255,255,255,0.97)', borderRadius: '16px',
                border: '1px solid rgba(22,163,74,0.08)', overflow: 'hidden',
                boxShadow: '0 2px 12px rgba(22,101,52,0.06)',
              }}>
                {/* Order Header */}
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '14px 20px', background: 'linear-gradient(135deg, #f0fdf4, #fff)',
                  borderBottom: '1px solid rgba(22,163,74,0.06)',
                }}>
                  <div>
                    <span style={{ fontWeight: 700, color: '#14532d', fontSize: '0.95rem' }}>
                      Order #{order.order_number || order.id}
                    </span>
                    <span style={{ marginLeft: '12px', fontSize: '0.8rem', color: '#888' }}>
                      {order.created_at ? new Date(order.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric', month: 'short', year: 'numeric'
                      }) : ''}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isConfirmed && (
                      <span style={{
                        padding: '3px 8px', borderRadius: '12px', fontSize: '0.65rem',
                        fontWeight: 700, background: '#dcfce7', color: '#166534',
                        display: 'flex', alignItems: 'center', gap: '4px',
                        animation: 'pulse 2s infinite',
                      }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
                        LIVE
                      </span>
                    )}
                    <span style={{
                      padding: '4px 14px', borderRadius: '20px', fontSize: '0.75rem',
                      fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px',
                      background: getStatusColor(order.status) + '20',
                      color: getStatusColor(order.status),
                    }}>
                      {(order.status || 'pending').replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                {/* Order Body */}
                <div style={{ padding: '16px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div>
                      <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: '#1f2937' }}>
                        {order.product_name || 'Product'}
                      </p>
                      <p style={{ margin: '2px 0', fontSize: '0.82rem', color: '#6b7280' }}>
                        Qty: {order.quantity} {order.farmer_name ? `from ${order.farmer_name}` : ''} {order.payment_method === 'cod' ? 'COD' : 'Online'}
                      </p>
                    </div>
                    <p style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#166534' }}>
                      Rs.{order.total_amount || order.total || 0}
                    </p>
                  </div>

                  {/* Mini Progress Stepper (for active orders) */}
                  {!isCancelled && !isReturned && (
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '2px',
                      background: '#f8fdf9', borderRadius: '10px', padding: '10px 8px', marginBottom: '12px',
                    }}>
                      {ORDER_STEPS.map((step, i) => {
                        const isCompleted = i <= currentStep;
                        const isCurrent = i === currentStep;
                        return (
                          <React.Fragment key={step.key}>
                            <div style={{
                              display: 'flex', flexDirection: 'column', alignItems: 'center',
                              flex: 1, minWidth: 0,
                            }}>
                              <div style={{
                                width: '28px', height: '28px', borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '0.85rem',
                                background: isCompleted ? '#22c55e' : '#e5e7eb',
                                color: isCompleted ? '#fff' : '#9ca3af',
                                boxShadow: isCurrent ? '0 0 0 3px #22c55e40' : 'none',
                                transition: 'all 0.3s',
                              }}>
                                {isCompleted ? step.icon : (i + 1)}
                              </div>
                              <span style={{
                                fontSize: '0.55rem', color: isCompleted ? '#166534' : '#9ca3af',
                                marginTop: '3px', fontWeight: isCurrent ? 700 : 500,
                                textAlign: 'center', lineHeight: 1.1,
                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                maxWidth: '50px',
                              }}>
                                {step.label}
                              </span>
                            </div>
                            {i < ORDER_STEPS.length - 1 && (
                              <div style={{
                                height: '2px', flex: '0 0 8px',
                                background: i < currentStep ? '#22c55e' : '#e5e7eb',
                                borderRadius: '1px', marginTop: '-12px',
                              }} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                  )}

                  {/* Cancelled Banner */}
                  {isCancelled && (
                    <div style={{
                      background: '#fef2f2', borderRadius: '8px', padding: '10px 14px',
                      marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px',
                    }}>
                      <span style={{ color: '#dc2626', fontSize: '0.85rem', fontWeight: 600 }}>
                        This order has been cancelled
                      </span>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {!isCancelled && (
                      <button onClick={() => handleTrackOrder(order.id)} style={{
                        padding: '8px 16px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600,
                        background: '#f0fdf4', color: '#166534', border: '1px solid #22c55e33',
                        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px',
                      }}>
                        Track Order
                      </button>
                    )}
                    
                    {(order.status === 'pending' || order.status === 'confirmed') && (
                      <button onClick={() => handleCancelOrder(order.id)} style={{
                        padding: '8px 16px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600,
                        background: '#fef2f2', color: '#dc2626', border: '1px solid #fca5a533',
                        cursor: 'pointer',
                      }}>
                        Cancel
                      </button>
                    )}
                    
                    {isDelivered && (
                      <>
                        <button onClick={() => setShowReview(order.id)} style={{
                          padding: '8px 16px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600,
                          background: 'linear-gradient(135deg, #f59e0b, #fbbf24)', color: '#fff',
                          border: 'none', cursor: 'pointer',
                        }}>
                          Rate & Review
                        </button>
                        <button onClick={() => setShowReturn(order.id)} style={{
                          padding: '8px 16px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600,
                          background: '#fff7ed', color: '#c2410c', border: '1px solid #fb923c33',
                          cursor: 'pointer',
                        }}>
                          Return
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Tracking Modal ── */}
      {selectedOrder && tracking && (() => {
        const detail = tracking.orderDetail || {};
        const farmer = detail.farmer || {};
        const isActive = ['confirmed', 'processing', 'packed', 'dispatched', 'in_transit', 'out_for_delivery'].includes(detail.status);
        return (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => { setSelectedOrder(null); setTracking(null); }}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '500px',
            width: '100%', maxHeight: '80vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 20px', color: '#14532d', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Order Tracking
              {isActive && (
                <span style={{ padding: '3px 10px', borderRadius: '12px', fontSize: '0.65rem', fontWeight: 700, background: '#dcfce7', color: '#166534', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', display: 'inline-block', animation: 'pulse 2s infinite' }}></span>
                  LIVE
                </span>
              )}
            </h3>

            {/* Farmer Info Card - shows when order is confirmed/active */}
            {farmer.name && isActive && (
              <div style={{
                background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)', borderRadius: '14px',
                padding: '14px 16px', marginBottom: '18px', border: '1px solid #bbf7d0',
              }}>
                <p style={{ margin: '0 0 6px', fontSize: '0.78rem', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Farmer Details</p>
                <p style={{ margin: '0 0 4px', fontSize: '0.92rem', fontWeight: 700, color: '#14532d' }}>{farmer.name}</p>
                {farmer.location && <p style={{ margin: '0 0 4px', fontSize: '0.8rem', color: '#6b7280' }}>Location: {farmer.location}</p>}
                {farmer.phone && <p style={{ margin: '0 0 8px', fontSize: '0.8rem', color: '#6b7280' }}>Phone: {farmer.phone}</p>}
                
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {(farmer.navigate_to_farmer_url || farmer.directions_url) && (
                    <a href={farmer.navigate_to_farmer_url || farmer.directions_url} target="_blank" rel="noopener noreferrer" style={{
                      display: 'inline-flex', alignItems: 'center', gap: '6px',
                      padding: '8px 16px', borderRadius: '10px', fontSize: '0.82rem', fontWeight: 700,
                      background: 'linear-gradient(135deg, #1d4ed8, #3b82f6)', color: '#fff',
                      textDecoration: 'none', boxShadow: '0 2px 8px rgba(29,78,216,0.3)',
                    }}>
                      <FiMapPin size={14} /> Navigate to Farmer
                    </a>
                  )}
                  {farmer.phone && (
                    <a href={`tel:${farmer.phone}`} style={{
                      display: 'inline-flex', alignItems: 'center', gap: '6px',
                      padding: '8px 16px', borderRadius: '10px', fontSize: '0.82rem', fontWeight: 700,
                      background: '#166534', color: '#fff', textDecoration: 'none',
                      boxShadow: '0 2px 8px rgba(22,101,52,0.3)',
                    }}>
                      <FiPhone size={14} /> Call Farmer
                    </a>
                  )}
                </div>
              </div>
            )}
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
              {(tracking.timeline || []).map((step, i) => (
                <div key={step.status} style={{ display: 'flex', gap: '16px' }}>
                  {/* Timeline Line & Dot */}
                  <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', width: '40px',
                  }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1.1rem', flexShrink: 0,
                      background: step.completed ? '#22c55e' : '#f1f5f9',
                      color: step.completed ? '#fff' : '#9ca3af',
                      boxShadow: step.current ? '0 0 0 4px #22c55e40' : 'none',
                    }}>
                      {step.icon}
                    </div>
                    {i < (tracking.timeline || []).length - 1 && (
                      <div style={{
                        width: '2px', height: '36px',
                        background: step.completed ? '#22c55e' : '#e5e7eb',
                      }} />
                    )}
                  </div>
                  
                  {/* Step Content */}
                  <div style={{ paddingBottom: '16px', flex: 1 }}>
                    <p style={{
                      margin: 0, fontWeight: step.current ? 700 : 500,
                      color: step.completed ? '#14532d' : '#9ca3af', fontSize: '0.92rem',
                    }}>
                      {step.label}
                    </p>
                    {step.timestamp && (
                      <p style={{ margin: '2px 0 0', fontSize: '0.75rem', color: '#6b7280' }}>
                        {new Date(step.timestamp).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                        })}
                      </p>
                    )}
                    {step.description && (
                      <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: '#888' }}>
                        {step.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <button onClick={() => { setSelectedOrder(null); setTracking(null); }} style={{
              width: '100%', padding: '12px', borderRadius: '10px', fontWeight: 600,
              background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
              marginTop: '8px', fontFamily: 'Poppins, sans-serif',
            }}>
              Close
            </button>
          </div>
        </div>
        );
      })()}

      {/* ── Review Modal ── */}
      {showReview && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => setShowReview(null)}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '450px',
            width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 20px', color: '#14532d' }}>⭐ Rate & Review</h3>
            
            {/* Product Rating */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                Product Rating
              </label>
              <div style={{ display: 'flex', gap: '6px' }}>
                {[1, 2, 3, 4, 5].map(star => (
                  <button key={star} onClick={() => setReviewData(d => ({ ...d, product_rating: star }))}
                    style={{
                      fontSize: '1.6rem', background: 'none', border: 'none', cursor: 'pointer', padding: '2px',
                      filter: star <= reviewData.product_rating ? 'none' : 'grayscale(1) opacity(0.3)',
                    }}>
                    ⭐
                  </button>
                ))}
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <textarea
                value={reviewData.product_review}
                onChange={(e) => setReviewData(d => ({ ...d, product_review: e.target.value }))}
                placeholder="Write about the product quality..."
                rows={2}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: '1px solid #e5e7eb', fontSize: '0.85rem', outline: 'none',
                  fontFamily: 'Poppins, sans-serif', boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Farmer Rating */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                Farmer Rating
              </label>
              <div style={{ display: 'flex', gap: '6px' }}>
                {[1, 2, 3, 4, 5].map(star => (
                  <button key={star} onClick={() => setReviewData(d => ({ ...d, farmer_rating: star }))}
                    style={{
                      fontSize: '1.6rem', background: 'none', border: 'none', cursor: 'pointer', padding: '2px',
                      filter: star <= reviewData.farmer_rating ? 'none' : 'grayscale(1) opacity(0.3)',
                    }}>
                    ⭐
                  </button>
                ))}
              </div>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <textarea
                value={reviewData.farmer_review}
                onChange={(e) => setReviewData(d => ({ ...d, farmer_review: e.target.value }))}
                placeholder="Write about the farmer service..."
                rows={2}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: '1px solid #e5e7eb', fontSize: '0.85rem', outline: 'none',
                  fontFamily: 'Poppins, sans-serif', boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setShowReview(null)} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontWeight: 600,
                background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                Cancel
              </button>
              <button onClick={handleSubmitReview} disabled={submitting} style={{
                flex: 2, padding: '12px', borderRadius: '10px', fontWeight: 700,
                background: submitting ? '#9ca3af' : 'linear-gradient(135deg, #f59e0b, #fbbf24)',
                color: '#fff', border: 'none', cursor: submitting ? 'not-allowed' : 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                {submitting ? 'Submitting...' : '⭐ Submit Review'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Return Modal ── */}
      {showReturn && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px',
        }} onClick={() => setShowReturn(null)}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '28px', maxWidth: '450px',
            width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 20px', color: '#c2410c' }}>🔄 Request Return</h3>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#14532d', fontSize: '0.9rem' }}>
                Reason for Return *
              </label>
              <select
                value={returnReason.split(':')[0] || ''}
                onChange={(e) => setReturnReason(e.target.value)}
                style={{
                  width: '100%', padding: '12px', borderRadius: '10px',
                  border: '1px solid #e5e7eb', fontSize: '0.9rem', outline: 'none',
                  fontFamily: 'Poppins, sans-serif', boxSizing: 'border-box', marginBottom: '12px',
                }}
              >
                <option value="">Select reason...</option>
                <option value="Damaged product">Damaged product</option>
                <option value="Wrong item received">Wrong item received</option>
                <option value="Quality issue">Quality issue</option>
                <option value="Not as described">Not as described</option>
                <option value="Other">Other</option>
              </select>
              
              <textarea
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                placeholder="Describe the issue in detail..."
                rows={3}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: '1px solid #e5e7eb', fontSize: '0.85rem', outline: 'none',
                  fontFamily: 'Poppins, sans-serif', boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setShowReturn(null)} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontWeight: 600,
                background: '#f1f5f9', color: '#475569', border: 'none', cursor: 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                Cancel
              </button>
              <button onClick={handleSubmitReturn} disabled={submitting} style={{
                flex: 2, padding: '12px', borderRadius: '10px', fontWeight: 700,
                background: submitting ? '#9ca3af' : '#c2410c',
                color: '#fff', border: 'none', cursor: submitting ? 'not-allowed' : 'pointer',
                fontFamily: 'Poppins, sans-serif',
              }}>
                {submitting ? 'Submitting...' : '🔄 Submit Return Request'}
              </button>
            </div>
          </div>
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
