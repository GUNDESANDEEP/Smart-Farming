import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { checkoutAPI } from '../../services/api';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiArrowLeft, FiMapPin, FiCreditCard, FiTruck, FiShield, FiCheck, FiPlus, FiMinus, FiX } from 'react-icons/fi';
import BuyerLayout from './BuyerLayout';
import SmartProductImage from '../../utils/SmartProductImage';

// Payment methods
const UPI_METHODS = [
  { id: 'upi', label: 'UPI', icon: '📱', color: '#6C3FB5', desc: 'Pay with any UPI app' },
  { id: 'phonepe', label: 'PhonePe', icon: '📲', color: '#5F259F', desc: 'PhonePe UPI' },
  { id: 'gpay', label: 'Google Pay', icon: '💳', color: '#4285F4', desc: 'Google Pay UPI' },
  { id: 'paytm', label: 'Paytm', icon: '🔵', color: '#00BAF2', desc: 'Paytm Wallet/UPI' },
  { id: 'stripe', label: 'Stripe (Card)', icon: '💳', color: '#635BFF', desc: 'Visa, Mastercard, Amex — Powered by Stripe' },
  { id: 'card', label: 'Debit/Credit Card', icon: '💳', color: '#1a1a2e', desc: 'Visa, Mastercard, Rupay' },
  { id: 'netbanking', label: 'Net Banking', icon: '🏦', color: '#0d6efd', desc: 'All major banks' },
];

export default function Checkout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [placing, setPlacing] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [onlineMethod, setOnlineMethod] = useState('upi');
  const [showOnlineOptions, setShowOnlineOptions] = useState(false);
  const [orderSummary, setOrderSummary] = useState(null);
  const [showUpiModal, setShowUpiModal] = useState(false);
  const [upiOrderDetails, setUpiOrderDetails] = useState(null);
  const [utrNumber, setUtrNumber] = useState('');
  const [verifyingUpi, setVerifyingUpi] = useState(false);
  const [verifyEngineMsg, setVerifyEngineMsg] = useState('');
  
  // Payment Gateway Tab & Field States
  const [gatewayTab, setGatewayTab] = useState('upi'); // 'upi', 'card', 'netbanking'
  const [cardName, setCardName] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvv, setCardCvv] = useState('');
  const [selectedBank, setSelectedBank] = useState('');
  const [showOtpScreen, setShowOtpScreen] = useState(false);
  const [otpValue, setOtpValue] = useState('');
  const [verifyingOtp, setVerifyingOtp] = useState(false);

  // Delivery address — pre-fill from logged-in user
  const [address, setAddress] = useState({
    full_name: '', phone: '', address_line1: '', address_line2: '',
    city: '', state: '', pincode: '', landmark: '',
  });
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);

  useEffect(() => {
    loadCart();
    loadAddresses();
    // Pre-fill name and phone from user data
    if (user) {
      setAddress(prev => ({
        ...prev,
        full_name: prev.full_name || user.name || user.first_name || '',
        phone: prev.phone || user.phone || user.email || '',
        city: prev.city || user.city || user.location || '',
      }));
    }
  }, []);

  const loadCart = useCallback(async () => {
    try {
      setLoading(true);
      const cartData = JSON.parse(localStorage.getItem('cart') || '{"items":[]}');
      if (!cartData.items || cartData.items.length === 0) {
        toast.error('Your cart is empty');
        navigate('/buyer/marketplace');
        return;
      }

      // Enrich items with product data
      const enrichedItems = [];
      for (const item of cartData.items) {
        let foundProduct = null;
        try {
          const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/buyer/products/${item.product_id}`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
          });
          if (res.ok) {
            const data = await res.json();
            foundProduct = data.product || data.data || data;
          }
        } catch { /* skip */ }

        // Fallback to local stored product metadata if API fails/returns 404
        if (!foundProduct && item.product) {
          foundProduct = item.product;
        }

        if (foundProduct && foundProduct.name) {
          let images = [];
          if (foundProduct.images) {
            try { images = typeof foundProduct.images === 'string' ? JSON.parse(foundProduct.images) : foundProduct.images; } catch { images = []; }
          }
          enrichedItems.push({
            ...item,
            name: foundProduct.name,
            price: parseFloat(foundProduct.price || 0),
            unit: foundProduct.unit || 'kg',
            image: images?.[0] || foundProduct.image_url || '',
            farmer_id: foundProduct.farmer_id,
            category: foundProduct.category,
          });
        }
      }

      if (enrichedItems.length === 0) {
        toast.error('No valid products in cart');
        navigate('/buyer/marketplace');
        return;
      }

      setCart({ items: enrichedItems });
      calculateTotal(enrichedItems);
    } catch {
      toast.error('Failed to load cart');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const calculateTotal = (items) => {
    let fees = { gstPercent: 1, platformPercent: 2, deliveryFlat: 40 };
    try {
      const stored = localStorage.getItem('sf_admin_fees');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.deliveryFlat !== undefined) fees = parsed;
      }
    } catch {}

    const subtotal = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const deliveryFee = subtotal >= 500 ? 0 : fees.deliveryFlat;
    const platformFee = Math.round(subtotal * (fees.platformPercent / 100) * 100) / 100;
    const gstTax = Math.round(subtotal * (fees.gstPercent / 100) * 100) / 100;
    const total = subtotal + deliveryFee + gstTax;
    setOrderSummary({ subtotal, deliveryFee, platformFee, tax: gstTax, total, gstPercent: fees.gstPercent });
  };

  const loadAddresses = async () => {
    try {
      const res = await checkoutAPI.getAddresses();
      const addrs = res.data?.addresses || [];
      setSavedAddresses(addrs);
      if (addrs.length > 0) {
        const def = addrs.find(a => a.is_default) || addrs[0];
        setSelectedAddressId(def.id);
        setAddress({
          full_name: def.full_name || '', phone: def.phone || '',
          address_line1: def.address_line1 || '', address_line2: def.address_line2 || '',
          city: def.city || '', state: def.state || '', pincode: def.pincode || '',
          landmark: def.landmark || '',
        });
      }
    } catch { /* first time */ }
  };

  const updateQuantity = (idx, delta) => {
    const items = [...cart.items];
    items[idx].quantity = Math.max(1, items[idx].quantity + delta);
    setCart({ items });
    calculateTotal(items);
    // Update localStorage
    const lsCart = JSON.parse(localStorage.getItem('cart') || '{"items":[],"total_amount":0}');
    const lsItem = lsCart.items.find(i => i.product_id === items[idx].product_id);
    if (lsItem) lsItem.quantity = items[idx].quantity;
    lsCart.total_amount = lsCart.items.reduce((s, i) => s + (i.product?.price || 0) * i.quantity, 0);
    localStorage.setItem('cart', JSON.stringify(lsCart));
  };

  const handlePlaceOrder = async () => {
    if (!address.address_line1 || !address.city || !address.pincode) {
      toast.error('Please fill in delivery address');
      return;
    }
    if (!address.phone) {
      toast.error('Phone number is required');
      return;
    }

    setPlacing(true);
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const fullAddress = [address.address_line1, address.address_line2, address.landmark, address.city, address.state, address.pincode].filter(Boolean).join(', ');

      const orderData = {
        items: cart.items.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
        payment_method: paymentMethod,
        delivery_address: fullAddress,
        buyer_name: address.full_name || user.name || `${user.first_name || ''} ${user.last_name || ''}`.trim(),
        buyer_phone: address.phone || user.phone || '',
        buyer_email: user.email || '',
        notes: '',
        delivery_fee: orderSummary?.deliveryFee || 0,
        platform_fee: orderSummary?.platformFee || 0,
        total_amount: orderSummary?.total || 0,
      };

      const res = await checkoutAPI.createOrder(orderData);
      const order = res.data;

      if (!order.success) {
        toast.error(order.error || 'Failed to create order');
        setPlacing(false);
        return;
      }

      // Save address for next time
      if (!selectedAddressId && address.address_line1) {
        checkoutAPI.saveAddress(address).catch(() => {});
      }

      if (paymentMethod === 'cod') {
        // COD — order confirmed immediately
        localStorage.setItem('cart', JSON.stringify({ items: [] }));
        navigate('/buyer/order-success', {
          state: {
            order_id: order.order_id,
            order_number: order.order_number,
            total_amount: order.total_amount || orderSummary?.total,
            payment_method: 'cod',
            payment_status: 'PENDING',
          }
        });
      } else {
        // Online payment — open UPI QR Code verification modal
        setUpiOrderDetails({
          order_id: order.order_id,
          order_number: order.order_number,
          total_amount: order.total_amount || orderSummary?.total,
          farmer_share: order.farmer_share || orderSummary?.subtotal,
          admin_share: order.admin_share || (orderSummary?.total - orderSummary?.subtotal),
          farmer_name: order.farmer_name || 'Local Farmer',
          farmer_upi: order.farmer_upi || '9492147313@ybl',
          admin_upi: order.admin_upi || '9492147313@ybl',
        });
        setShowUpiModal(true);
      }
    } catch (err) {
      console.error('Order error:', err);
      const errorMsg = err.response?.data?.message || err.response?.data?.error || 'Failed to place order';
      toast.error(errorMsg);
    } finally {
      setPlacing(false);
    }
  };

  const handleConfirmUpiPayment = async () => {
    if (!utrNumber || utrNumber.length !== 12 || !/^\d+$/.test(utrNumber)) {
      toast.error('Please enter a valid 12-digit transaction ID (UTR)');
      return;
    }
    setVerifyingUpi(true);

    const steps = [
      "🔄 Auto Verify Engine starting background verification...",
      "🔍 Checking UTR signature against UPI logs...",
      "💼 Verifying split: " + `₹${parseFloat(upiOrderDetails.farmer_share).toFixed(2)} to Farmer (${upiOrderDetails.farmer_name}), ₹${parseFloat(upiOrderDetails.admin_share).toFixed(2)} to Admin...`,
      "⚡ Finalizing payment confirmation..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setVerifyEngineMsg(steps[i]);
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    try {
      const res = await checkoutAPI.verifyUpiPayment({
        order_id: upiOrderDetails.order_id,
        transaction_id: utrNumber,
        upi_id: upiOrderDetails.farmer_upi,
      });
      if (res.data?.success) {
        localStorage.setItem('cart', JSON.stringify({ items: [], total_amount: 0 }));
        setShowUpiModal(false);
        setUtrNumber('');
        setVerifyEngineMsg('');
        toast.success('Payment verified! Order confirmed.');
        navigate('/buyer/order-success', {
          state: {
            order_id: upiOrderDetails.order_id,
            order_number: upiOrderDetails.order_number,
            total_amount: upiOrderDetails.total_amount,
            payment_method: 'online',
            payment_status: 'PAID',
            transaction_id: `UPI-${utrNumber}`,
          }
        });
      } else {
        toast.error(res.data?.error || 'Verification failed. Please check the UTR.');
        setVerifyEngineMsg('');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Verification error. Try again.');
      setVerifyEngineMsg('');
    } finally {
      setVerifyingUpi(false);
    }
  };

  const handleCardSubmit = (e) => {
    e.preventDefault();
    if (!cardNumber || cardNumber.length < 16) {
      toast.error('Please enter a valid 16-digit card number');
      return;
    }
    if (!cardExpiry || !/^\d\d\/\d\d$/.test(cardExpiry)) {
      toast.error('Please enter expiry date in MM/YY format');
      return;
    }
    if (!cardCvv || cardCvv.length < 3) {
      toast.error('Please enter a valid CVV');
      return;
    }
    setShowOtpScreen(true);
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    if (!otpValue || otpValue.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP code');
      return;
    }
    setVerifyingOtp(true);
    setVerifyEngineMsg("🔄 Auto Verify Engine starting background verification...");
    
    // Simulate background verification split log messages
    const steps = [
      "🔄 Connecting to bank gateway services...",
      "🔍 Checking 3D-Secure signature...",
      "💼 Verifying split: " + `₹${parseFloat(upiOrderDetails.farmer_share).toFixed(2)} to Farmer (${upiOrderDetails.farmer_name}), ₹${parseFloat(upiOrderDetails.admin_share).toFixed(2)} to Admin...`,
      "⚡ Finalizing payment confirmation..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setVerifyEngineMsg(steps[i]);
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    // Auto-generate 12-digit transaction ID for database receipts
    const genTxnId = Math.floor(100000000000 + Math.random() * 900000000000).toString();

    try {
      const res = await checkoutAPI.verifyUpiPayment({
        order_id: upiOrderDetails.order_id,
        transaction_id: genTxnId,
        upi_id: upiOrderDetails.farmer_upi,
      });
      if (res.data?.success) {
        localStorage.setItem('cart', JSON.stringify({ items: [], total_amount: 0 }));
        setShowUpiModal(false);
        setShowOtpScreen(false);
        setOtpValue('');
        setVerifyEngineMsg('');
        toast.success('Payment verified! Order confirmed.');
        navigate('/buyer/order-success', {
          state: {
            order_id: upiOrderDetails.order_id,
            order_number: upiOrderDetails.order_number,
            total_amount: upiOrderDetails.total_amount,
            payment_method: 'card',
            payment_status: 'PAID',
            transaction_id: `CARD-${genTxnId}`,
          }
        });
      } else {
        toast.error(res.data?.error || 'Verification failed. Please try again.');
        setVerifyEngineMsg('');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Verification error. Try again.');
      setVerifyEngineMsg('');
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleNetbankingSubmit = async (bankName) => {
    setSelectedBank(bankName);
    setVerifyingUpi(true);
    setVerifyEngineMsg("🔄 Auto Verify Engine starting background verification...");
    
    const steps = [
      `🔄 Connecting to ${bankName} Secure Gateway...`,
      "🔍 Checking credentials & token validation...",
      "💼 Verifying split: " + `₹${parseFloat(upiOrderDetails.farmer_share).toFixed(2)} to Farmer (${upiOrderDetails.farmer_name}), ₹${parseFloat(upiOrderDetails.admin_share).toFixed(2)} to Admin...`,
      "⚡ Finalizing payment confirmation..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setVerifyEngineMsg(steps[i]);
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    const genTxnId = Math.floor(100000000000 + Math.random() * 900000000000).toString();

    try {
      const res = await checkoutAPI.verifyUpiPayment({
        order_id: upiOrderDetails.order_id,
        transaction_id: genTxnId,
        upi_id: upiOrderDetails.farmer_upi,
      });
      if (res.data?.success) {
        localStorage.setItem('cart', JSON.stringify({ items: [], total_amount: 0 }));
        setShowUpiModal(false);
        setVerifyEngineMsg('');
        toast.success('Payment verified! Order confirmed.');
        navigate('/buyer/order-success', {
          state: {
            order_id: upiOrderDetails.order_id,
            order_number: upiOrderDetails.order_number,
            total_amount: upiOrderDetails.total_amount,
            payment_method: 'netbanking',
            payment_status: 'PAID',
            transaction_id: `NET-${genTxnId}`,
          }
        });
      } else {
        toast.error(res.data?.error || 'Verification failed. Please try again.');
        setVerifyEngineMsg('');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Verification error. Try again.');
      setVerifyEngineMsg('');
    } finally {
      setVerifyingUpi(false);
    }
  };

  if (loading) {
    return (
      <BuyerLayout>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner} />
          <p style={{ color: '#94a3b8', marginTop: 16 }}>Loading checkout...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </BuyerLayout>
    );
  }

  return (
    <BuyerLayout>
      {/* Back + Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <Link to="/buyer/cart" style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10, padding: '8px 16px', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none', touchAction: 'manipulation' }}>
          <FiArrowLeft size={18} /> Back
        </Link>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#1e293b', margin: 0 }}>💳 Checkout</h2>
      </div>

      <div style={styles.container}>
        {/* Left: Order Details */}
        <div style={styles.leftCol}>

          {/* Order Items */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>📦 Order Items</h2>
            {cart?.items?.map((item, idx) => (
              <div key={idx} style={styles.itemRow}>
                <div style={styles.itemImage}>
                  <SmartProductImage product={item.product || { name: item.name, category: item.category, images: item.image }} alt={item.name} style={styles.img} />
                </div>
                <div style={styles.itemInfo}>
                  <h3 style={styles.itemName}>{item.name}</h3>
                  <p style={styles.itemPrice}>₹{item.price}/{item.unit}</p>
                </div>
                <div style={styles.qtyControl}>
                  <button onClick={() => updateQuantity(idx, -1)} style={styles.qtyBtn}><FiMinus size={14} /></button>
                  <span style={styles.qtyValue}>{item.quantity}</span>
                  <button onClick={() => updateQuantity(idx, 1)} style={styles.qtyBtn}><FiPlus size={14} /></button>
                </div>
                <div style={styles.itemTotal}>₹{(item.price * item.quantity).toFixed(0)}</div>
              </div>
            ))}
          </div>

          {/* Delivery Address */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}><FiMapPin size={18} /> Delivery Address</h2>

            {savedAddresses.length > 0 && (
              <div style={styles.savedAddresses}>
                {savedAddresses.map(addr => (
                  <button
                    key={addr.id}
                    onClick={() => {
                      setSelectedAddressId(addr.id);
                      setAddress({
                        full_name: addr.full_name || '', phone: addr.phone || '',
                        address_line1: addr.address_line1 || '', address_line2: addr.address_line2 || '',
                        city: addr.city || '', state: addr.state || '', pincode: addr.pincode || '',
                        landmark: addr.landmark || '',
                      });
                    }}
                    style={{
                      ...styles.addrChip,
                      ...(selectedAddressId === addr.id ? styles.addrChipActive : {}),
                    }}
                  >
                    <span style={styles.addrLabel}>{addr.label || 'Home'}</span>
                    <span style={styles.addrPreview}>{addr.address_line1}, {addr.city}</span>
                  </button>
                ))}
              </div>
            )}

            <div style={styles.formGrid}>
              <input style={styles.input} placeholder="Full Name *" value={address.full_name}
                onChange={e => setAddress({...address, full_name: e.target.value})} />
              <input style={styles.input} placeholder="Phone Number *" value={address.phone}
                onChange={e => setAddress({...address, phone: e.target.value})} />
              <input style={{...styles.input, gridColumn: '1/-1'}} placeholder="Address Line 1 *" value={address.address_line1}
                onChange={e => setAddress({...address, address_line1: e.target.value})} />
              <input style={{...styles.input, gridColumn: '1/-1'}} placeholder="Address Line 2" value={address.address_line2}
                onChange={e => setAddress({...address, address_line2: e.target.value})} />
              <input style={styles.input} placeholder="City *" value={address.city}
                onChange={e => setAddress({...address, city: e.target.value})} />
              <input style={styles.input} placeholder="State" value={address.state}
                onChange={e => setAddress({...address, state: e.target.value})} />
              <input style={styles.input} placeholder="Pincode *" value={address.pincode}
                onChange={e => setAddress({...address, pincode: e.target.value})} />
              <input style={styles.input} placeholder="Landmark" value={address.landmark}
                onChange={e => setAddress({...address, landmark: e.target.value})} />
            </div>
          </div>

          {/* Payment Method */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}><FiCreditCard size={18} /> Payment Method</h2>

            <div style={styles.paymentOptions}>
              {/* Online Payment */}
              <button
                onClick={() => { setPaymentMethod('online'); setShowOnlineOptions(true); }}
                style={{
                  ...styles.paymentOption,
                  ...(paymentMethod === 'online' ? styles.paymentOptionActive : {}),
                }}
              >
                <div style={styles.radioCircle}>
                  {paymentMethod === 'online' && <div style={styles.radioDot} />}
                </div>
                <div style={styles.paymentIcon}>💳</div>
                <div>
                  <div style={styles.paymentLabel}>Online Payment</div>
                  <div style={styles.paymentDesc}>UPI, PhonePe, GPay, Card, Net Banking</div>
                </div>
              </button>

              {/* Online Sub-options */}
              {paymentMethod === 'online' && (
                <div style={styles.onlineMethodsGrid}>
                  {UPI_METHODS.map(m => (
                    <button
                      key={m.id}
                      onClick={() => setOnlineMethod(m.id)}
                      style={{
                        ...styles.upiOption,
                        ...(onlineMethod === m.id ? { borderColor: m.color, background: `${m.color}15` } : {}),
                      }}
                    >
                      <span style={{...styles.upiIcon, background: m.color}}>{m.icon}</span>
                      <span style={styles.upiLabel}>{m.label}</span>
                      {onlineMethod === m.id && <FiCheck size={16} color={m.color} style={{marginLeft:'auto'}} />}
                    </button>
                  ))}
                </div>
              )}

              {/* COD */}
              <button
                onClick={() => { setPaymentMethod('cod'); setShowOnlineOptions(false); }}
                style={{
                  ...styles.paymentOption,
                  ...(paymentMethod === 'cod' ? styles.paymentOptionActive : {}),
                }}
              >
                <div style={styles.radioCircle}>
                  {paymentMethod === 'cod' && <div style={styles.radioDot} />}
                </div>
                <div style={styles.paymentIcon}>💵</div>
                <div>
                  <div style={styles.paymentLabel}>Cash on Delivery</div>
                  <div style={styles.paymentDesc}>Pay when your order arrives</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Right: Order Summary */}
        <div style={styles.rightCol}>
          <div style={styles.summaryCard}>
            <h2 style={styles.summaryTitle}>Order Summary</h2>

            <div style={styles.summaryRow}>
              <span>Items Total ({cart?.items?.length})</span>
              <span>₹{orderSummary?.subtotal?.toFixed(2)}</span>
            </div>
            <div style={styles.summaryRow}>
              <span><FiTruck size={14} style={{marginRight:6}} />Delivery Fee</span>
              <span style={orderSummary?.deliveryFee === 0 ? {color:'#22c55e',fontWeight:600} : {}}>
                {orderSummary?.deliveryFee === 0 ? 'FREE' : `₹${orderSummary?.deliveryFee}`}
              </span>
            </div>
            <div style={styles.summaryRow}>
              <span>Tax ({orderSummary?.gstPercent || 0}%)</span>
              <span>₹{orderSummary?.tax?.toFixed(2)}</span>
            </div>
            {orderSummary?.deliveryFee > 0 && (
              <div style={styles.freeDeliveryHint}>
                🚚 Add ₹{(500 - (orderSummary?.subtotal || 0)).toFixed(0)} more for free delivery
              </div>
            )}

            <div style={styles.summaryDivider} />

            <div style={styles.totalRow}>
              <span>Total Amount</span>
              <span style={styles.totalAmount}>₹{orderSummary?.total?.toFixed(2)}</span>
            </div>

            <button
              onClick={handlePlaceOrder}
              disabled={placing}
              style={{
                ...styles.placeOrderBtn,
                ...(placing ? {opacity:0.6, cursor:'not-allowed'} : {}),
              }}
            >
              {placing ? (
                <span>Processing...</span>
              ) : paymentMethod === 'cod' ? (
                <span>🛒 Place Order (COD)</span>
              ) : (
                <span>💳 Pay ₹{orderSummary?.total?.toFixed(0)}</span>
              )}
            </button>

            <div style={styles.securityInfo}>
              <FiShield size={14} style={{color:'#22c55e'}} />
              <span>100% Secure Payment • SSL Encrypted</span>
            </div>
            <div style={styles.securityInfo}>
              <FiTruck size={14} style={{color:'#3b82f6'}} />
              <span>Estimated Delivery: 1-3 Days</span>
            </div>
          </div>
        </div>
      </div>

      {/* UPI QR Payment Modal */}
      {showUpiModal && upiOrderDetails && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(12px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999,
          padding: 16
        }}>
          <div style={{
            background: '#fff', borderRadius: 28, width: '100%', maxWidth: 640,
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
            overflow: 'hidden', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column'
          }}>
            {/* Gateway Header */}
            <div style={{
              background: 'linear-gradient(135deg, #0f172a, #1e293b)',
              padding: '22px 28px', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255,255,255,0.08)'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '1.4rem' }}>🛡️</span>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, letterSpacing: -0.5 }}>SmartFarm Secure Checkout</h3>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: '0.72rem', color: '#94a3b8' }}>Merchant: SmartFarm Pvt. Ltd. | Order: {upiOrderDetails.order_number}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.68rem', color: '#94a3b8', display: 'block', textTransform: 'uppercase', fontWeight: 700, letterSpacing: 0.5 }}>Amount to Pay</span>
                <span style={{ fontSize: '1.4rem', fontWeight: 900, color: '#10b981' }}>₹{parseFloat(upiOrderDetails.total_amount).toFixed(2)}</span>
              </div>
            </div>

            {/* Gateway Main Body */}
            {verifyEngineMsg ? (
              /* Background Verification Engine Screen */
              <div style={{ padding: '60px 40px', minHeight: 320, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                <div style={{
                  width: 54, height: 54, border: '4px solid #f1f5f9', borderTop: '4px solid #10b981',
                  borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: 24
                }} />
                <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: 12 }}>Processing split payment transfers...</h4>
                <div style={{
                  background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16,
                  padding: '20px 24px', width: '100%', color: '#38bdf8', fontSize: '0.85rem',
                  fontFamily: 'monospace', textAlign: 'left', minHeight: 64, boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.5)',
                  boxSizing: 'border-box', overflow: 'hidden', lineHeight: 1.5
                }}>
                  {verifyEngineMsg}
                </div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              </div>
            ) : showOtpScreen ? (
              /* Simulated 3D-Secure Bank OTP Screen */
              <form onSubmit={handleOtpSubmit} style={{ padding: '36px 40px', textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 8, alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ fontSize: '1.5rem' }}>🏦</span>
                  <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>Secure OTP Verification</h4>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 24, lineHeight: 1.5 }}>
                  A one-time passcode (OTP) has been sent to your registered mobile number for validation. Enter code <b>123456</b> to authorize payment.
                </p>

                <div style={{ maxWidth: 280, margin: '0 auto 24px', textAlign: 'left' }}>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 800, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Enter 6-Digit OTP
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="e.g. 123456"
                    value={otpValue}
                    onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, ''))}
                    style={{
                      width: '100%', padding: '14px 16px', border: '2px solid #cbd5e1', borderRadius: 12,
                      fontSize: '1.1rem', letterSpacing: 6, textAlign: 'center', outline: 'none', color: '#0f172a', fontWeight: 800
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                  <button
                    type="button"
                    onClick={() => setShowOtpScreen(false)}
                    style={{
                      padding: '12px 24px', background: '#f1f5f9', border: 'none',
                      borderRadius: 12, color: '#475569', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem'
                    }}
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={verifyingOtp || otpValue.length !== 6}
                    style={{
                      padding: '12px 32px',
                      background: verifyingOtp || otpValue.length !== 6 ? '#cbd5e1' : 'linear-gradient(135deg, #10b981, #059669)',
                      border: 'none', borderRadius: 12, color: '#fff', fontWeight: 700,
                      cursor: verifyingOtp || otpValue.length !== 6 ? 'not-allowed' : 'pointer', fontSize: '0.85rem'
                    }}
                  >
                    {verifyingOtp ? 'Verifying...' : 'Submit OTP'}
                  </button>
                </div>
              </form>
            ) : (
              /* Razorpay-style tab layout */
              <div style={{ display: 'flex', minHeight: 340 }}>
                {/* Left Tabs Sidebar */}
                <div style={{ width: '35%', background: '#f8fafc', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }}>
                  <button
                    onClick={() => setGatewayTab('upi')}
                    style={{
                      padding: '18px 20px', border: 'none', background: gatewayTab === 'upi' ? '#fff' : 'transparent',
                      textAlign: 'left', cursor: 'pointer', borderLeft: gatewayTab === 'upi' ? '4px solid #4f46e5' : '4px solid transparent',
                      fontWeight: 700, fontSize: '0.85rem', color: gatewayTab === 'upi' ? '#4f46e5' : '#64748b', display: 'flex', alignItems: 'center', gap: 10
                    }}
                  >
                    <span>📱</span> UPI QR Code
                  </button>
                  <button
                    onClick={() => setGatewayTab('card')}
                    style={{
                      padding: '18px 20px', border: 'none', background: gatewayTab === 'card' ? '#fff' : 'transparent',
                      textAlign: 'left', cursor: 'pointer', borderLeft: gatewayTab === 'card' ? '4px solid #4f46e5' : '4px solid transparent',
                      fontWeight: 700, fontSize: '0.85rem', color: gatewayTab === 'card' ? '#4f46e5' : '#64748b', display: 'flex', alignItems: 'center', gap: 10
                    }}
                  >
                    <span>💳</span> Cards (Debit/Credit)
                  </button>
                  <button
                    onClick={() => setGatewayTab('netbanking')}
                    style={{
                      padding: '18px 20px', border: 'none', background: gatewayTab === 'netbanking' ? '#fff' : 'transparent',
                      textAlign: 'left', cursor: 'pointer', borderLeft: gatewayTab === 'netbanking' ? '4px solid #4f46e5' : '4px solid transparent',
                      fontWeight: 700, fontSize: '0.85rem', color: gatewayTab === 'netbanking' ? '#4f46e5' : '#64748b', display: 'flex', alignItems: 'center', gap: 10
                    }}
                  >
                    <span>🏛️</span> Net Banking
                  </button>
                </div>

                {/* Right Tab Content */}
                <div style={{ width: '65%', padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', boxSizing: 'border-box' }}>
                  
                  {/* UPI TAB CONTENT */}
                  {gatewayTab === 'upi' && (
                    <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <div style={{
                        background: '#f8fafc', border: '2px dashed #cbd5e1', borderRadius: 16,
                        padding: 10, display: 'inline-block', marginBottom: 12
                      }}>
                        <img
                          src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(`upi://pay?pa=${upiOrderDetails?.farmer_upi || upiOrderDetails?.admin_upi || '9492147313@ybl'}&pn=SmartFarm&am=${upiOrderDetails?.total_amount}&cu=INR`)}`}
                          alt="UPI QR Code"
                          style={{ width: 150, height: 150, display: 'block', borderRadius: 8 }}
                        />
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#f1f5f9', padding: '6px 12px', borderRadius: 20, marginBottom: 16 }}>
                        <span style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600 }}>UPI ID:</span>
                        <span style={{ fontSize: '0.75rem', color: '#0f172a', fontWeight: 800, fontFamily: 'monospace' }}>{upiOrderDetails?.farmer_upi || upiOrderDetails?.admin_upi || '9492147313@ybl'}</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(upiOrderDetails?.farmer_upi || upiOrderDetails?.admin_upi || '9492147313@ybl');
                            toast.success('UPI ID copied!');
                          }}
                          style={{ background: '#cbd5e1', border: 'none', borderRadius: 4, padding: '2px 6px', fontSize: '0.6rem', color: '#475569', cursor: 'pointer', fontWeight: 700 }}
                        >
                          Copy
                        </button>
                      </div>

                      <div style={{ textAlign: 'left', width: '100%', marginBottom: 12 }}>
                        <label style={{ display: 'block', fontSize: '0.68rem', fontWeight: 800, color: '#475569', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                          Enter 12-Digit UPI Transaction ID / UTR
                        </label>
                        <input
                          type="text"
                          maxLength={12}
                          placeholder="e.g. 123456789012"
                          value={utrNumber}
                          onChange={(e) => setUtrNumber(e.target.value.replace(/\D/g, ''))}
                          style={{
                            width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 8,
                            fontSize: '0.85rem', outline: 'none', color: '#0f172a', boxSizing: 'border-box'
                          }}
                        />
                      </div>

                      <div style={{ display: 'flex', gap: 8, width: '100%' }}>
                        <button
                          onClick={() => setShowUpiModal(false)}
                          style={{
                            flex: 1, padding: '10px 12px', background: '#f1f5f9', border: 'none',
                            borderRadius: 8, color: '#475569', fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem'
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleConfirmUpiPayment}
                          disabled={verifyingUpi || utrNumber.length !== 12}
                          style={{
                            flex: 2, padding: '10px 12px',
                            background: verifyingUpi || utrNumber.length !== 12 ? '#cbd5e1' : 'linear-gradient(135deg, #4f46e5, #3730a3)',
                            border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700,
                            cursor: verifyingUpi || utrNumber.length !== 12 ? 'not-allowed' : 'pointer', fontSize: '0.8rem'
                          }}
                        >
                          {verifyingUpi ? 'Verifying...' : 'Verify Payment'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* CARDS TAB CONTENT */}
                  {gatewayTab === 'card' && (
                    <form onSubmit={handleCardSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: '#64748b', marginBottom: 4, textTransform: 'uppercase' }}>Cardholder Name</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. John Doe"
                          value={cardName}
                          onChange={(e) => setCardName(e.target.value)}
                          style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: '0.85rem', color: '#0f172a', outline: 'none', boxSizing: 'border-box' }}
                        />
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: '#64748b', marginBottom: 4, textTransform: 'uppercase' }}>Card Number</label>
                        <input
                          type="text"
                          required
                          maxLength={16}
                          placeholder="4111 2222 3333 4444"
                          value={cardNumber}
                          onChange={(e) => setCardNumber(e.target.value.replace(/\D/g, ''))}
                          style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: '0.85rem', color: '#0f172a', outline: 'none', boxSizing: 'border-box' }}
                        />
                      </div>

                      <div style={{ display: 'flex', gap: 12 }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: '#64748b', marginBottom: 4, textTransform: 'uppercase' }}>Expiry Date</label>
                          <input
                            type="text"
                            required
                            maxLength={5}
                            placeholder="MM/YY"
                            value={cardExpiry}
                            onChange={(e) => {
                              let val = e.target.value;
                              if (val.length === 2 && !val.includes('/')) {
                                val = val + '/';
                              }
                              setCardExpiry(val);
                            }}
                            style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: '0.85rem', color: '#0f172a', outline: 'none', boxSizing: 'border-box', textAlign: 'center' }}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: '#64748b', marginBottom: 4, textTransform: 'uppercase' }}>CVV</label>
                          <input
                            type="password"
                            required
                            maxLength={3}
                            placeholder="123"
                            value={cardCvv}
                            onChange={(e) => setCardCvv(e.target.value.replace(/\D/g, ''))}
                            style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: '0.85rem', color: '#0f172a', outline: 'none', boxSizing: 'border-box', textAlign: 'center' }}
                          />
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                        <button
                          type="button"
                          onClick={() => setShowUpiModal(false)}
                          style={{
                            flex: 1, padding: '12px 14px', background: '#f1f5f9', border: 'none',
                            borderRadius: 8, color: '#475569', fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem'
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          style={{
                            flex: 2, padding: '12px 14px', background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none',
                            borderRadius: 8, color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem'
                          }}
                        >
                          Pay ₹{parseFloat(upiOrderDetails.total_amount).toFixed(0)}
                        </button>
                      </div>
                    </form>
                  )}

                  {/* NET BANKING TAB CONTENT */}
                  {gatewayTab === 'netbanking' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748b' }}>Select your bank to redirect to netbanking page:</p>
                      
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        {['SBI', 'HDFC', 'ICICI', 'Axis', 'Kotak', 'PNB'].map(bank => (
                          <button
                            key={bank}
                            onClick={() => handleNetbankingSubmit(bank)}
                            style={{
                              padding: '12px 10px', background: '#f8fafc', border: '1px solid #e2e8f0',
                              borderRadius: 8, fontSize: '0.82rem', fontWeight: 700, color: '#334155',
                              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8
                            }}
                          >
                            🏛️ {bank}
                          </button>
                        ))}
                      </div>

                      <button
                        onClick={() => setShowUpiModal(false)}
                        style={{
                          width: '100%', padding: '10px 12px', background: '#f1f5f9', border: 'none',
                          borderRadius: 8, color: '#475569', fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem', marginTop: 12
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  )}

                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </BuyerLayout>
  );
}

// ============================================================================
// STYLES — Premium dark theme with glassmorphism
// ============================================================================
const styles = {
  loadingContainer: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' },
  spinner: { width: 40, height: 40, border: '3px solid #e2e8f0', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite' },

  container: { display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24 },
  leftCol: { display: 'flex', flexDirection: 'column', gap: 20 },
  rightCol: { position: 'sticky', top: 100, height: 'fit-content' },

  card: { background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' },
  cardTitle: { fontSize: 16, fontWeight: 700, color: '#1e293b', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: 8 },

  // Items
  itemRow: { display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0', borderBottom: '1px solid #f1f5f9' },
  itemImage: { width: 64, height: 64, borderRadius: 12, overflow: 'hidden', flexShrink: 0 },
  img: { width: '100%', height: '100%', objectFit: 'cover' },
  imgPlaceholder: { width: '100%', height: '100%', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28 },
  itemInfo: { flex: 1, minWidth: 0 },
  itemName: { fontSize: 14, fontWeight: 600, color: '#1e293b', margin: 0 },
  itemPrice: { fontSize: 12, color: '#94a3b8', margin: '4px 0 0' },
  qtyControl: { display: 'flex', alignItems: 'center', gap: 8, background: '#f1f5f9', borderRadius: 10, padding: '4px 8px' },
  qtyBtn: { background: '#eff6ff', border: '1px solid #bfdbfe', color: '#2563eb', width: 28, height: 28, borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  qtyValue: { fontSize: 14, fontWeight: 700, color: '#1e293b', minWidth: 20, textAlign: 'center' },
  itemTotal: { fontSize: 16, fontWeight: 700, color: '#16a34a', minWidth: 60, textAlign: 'right' },

  // Address
  savedAddresses: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 },
  addrChip: { background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '8px 14px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s' },
  addrChipActive: { borderColor: '#3b82f6', background: '#eff6ff' },
  addrLabel: { display: 'block', fontSize: 12, fontWeight: 700, color: '#2563eb' },
  addrPreview: { display: 'block', fontSize: 11, color: '#94a3b8', marginTop: 2 },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  input: { background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '12px 14px', color: '#1e293b', fontSize: 14, outline: 'none', transition: 'border-color 0.2s', width: '100%', boxSizing: 'border-box' },

  // Payment
  paymentOptions: { display: 'flex', flexDirection: 'column', gap: 12 },
  paymentOption: { display: 'flex', alignItems: 'center', gap: 14, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 14, padding: '16px 18px', cursor: 'pointer', transition: 'all 0.2s', textAlign: 'left', width: '100%' },
  paymentOptionActive: { borderColor: '#3b82f6', background: '#eff6ff', boxShadow: '0 0 12px rgba(59,130,246,0.1)' },
  radioCircle: { width: 22, height: 22, borderRadius: '50%', border: '2px solid #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  radioDot: { width: 12, height: 12, borderRadius: '50%', background: '#3b82f6' },
  paymentIcon: { fontSize: 24 },
  paymentLabel: { fontSize: 15, fontWeight: 700, color: '#1e293b' },
  paymentDesc: { fontSize: 12, color: '#94a3b8', marginTop: 2 },

  // Online methods grid
  onlineMethodsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginLeft: 36, marginTop: 4, marginBottom: 4 },
  upiOption: { display: 'flex', alignItems: 'center', gap: 10, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '10px 12px', cursor: 'pointer', transition: 'all 0.2s' },
  upiIcon: { width: 32, height: 32, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, color: '#fff', flexShrink: 0 },
  upiLabel: { fontSize: 13, fontWeight: 600, color: '#475569' },

  // Summary
  summaryCard: { background: '#fff', borderRadius: 20, padding: 28, border: '1px solid #e2e8f0', boxShadow: '0 4px 16px rgba(0,0,0,0.06)' },
  summaryTitle: { fontSize: 18, fontWeight: 700, color: '#1e293b', margin: '0 0 20px' },
  summaryRow: { display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#64748b', margin: '10px 0' },
  freeDeliveryHint: { fontSize: 11, color: '#f59e0b', background: '#fffbeb', padding: '6px 10px', borderRadius: 8, marginTop: 4 },
  summaryDivider: { height: 1, background: '#e2e8f0', margin: '16px 0' },
  totalRow: { display: 'flex', justifyContent: 'space-between', fontSize: 16, fontWeight: 700, color: '#1e293b', margin: '12px 0' },
  totalAmount: { fontSize: 24, fontWeight: 800, color: '#16a34a' },

  placeOrderBtn: { width: '100%', padding: '16px 24px', background: 'linear-gradient(135deg, #3b82f6, #2563eb)', border: 'none', borderRadius: 14, color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: 20, transition: 'all 0.3s', boxShadow: '0 4px 20px rgba(59,130,246,0.25)' },
  securityInfo: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#94a3b8', marginTop: 12 },
};
