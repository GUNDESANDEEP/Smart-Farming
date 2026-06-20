import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { paymentsAPI } from '../services/api';
import '../styles/landing.css';

/* Tiny QR code generator URL (no external library needed) */
const generateQRCodeURL = (text, size = 250) => {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(text)}&color=166534&bgcolor=f0fdf4`;
};

const LandingPage = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [showFeatures, setShowFeatures] = useState(false);

  // Payment modal state
  const [showPayModal, setShowPayModal] = useState(false);
  const [payStep, setPayStep] = useState(1); // 1=form, 2=QR, 3=OTP, 4=success
  const [payForm, setPayForm] = useState({ phone: '', amount: '', productId: '', upiId: '' });
  const [qrData, setQrData] = useState(null);
  const [otpInput, setOtpInput] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(null);
  const [productInfo, setProductInfo] = useState(null);
  const [loadingProduct, setLoadingProduct] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => { setTimeout(() => setShowFeatures(true), 500); }, []);

  const handleGoogleAuth = () => toast.error('Google authentication coming soon!');
  const handleMobileOTP = () => toast.error('Mobile OTP coming soon!');

  /* Auto-fetch product when product ID is entered */
  const handleProductIdChange = async (value) => {
    setPayForm(prev => ({ ...prev, productId: value }));
    setProductInfo(null);
    if (value && value.length > 0) {
      setLoadingProduct(true);
      try {
        const API = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
        const res = await fetch(`${API}/buyer/products?page=1&limit=100`);
        const data = await res.json();
        const products = data.products || data || [];
        const product = Array.isArray(products) ? products.find(p => String(p.id) === String(value)) : null;
        if (product) {
          setProductInfo(product);
          if (!payForm.amount) setPayForm(prev => ({ ...prev, amount: String(product.price || '') }));
        }
      } catch (err) { /* silent */ }
      finally { setLoadingProduct(false); }
    }
  };

  /* Generate UPI QR */
  const handleGenerateQR = async () => {
    const { phone, amount, upiId } = payForm;
    if (!phone || phone.length < 10) { toast.error('Enter a valid 10-digit phone number'); return; }
    if (!amount || parseFloat(amount) <= 0) { toast.error('Enter a valid amount'); return; }

    const payeeUPI = upiId || `${phone}@upi`;
    const amountVal = parseFloat(amount).toFixed(2);
    const txnNote = payForm.productId ? `SmartFarm-Product-${payForm.productId}` : 'SmartFarm-Payment';
    const upiLink = `upi://pay?pa=${payeeUPI}&pn=SmartFarm&am=${amountVal}&cu=INR&tn=${txnNote}`;

    setQrData({ upiLink, payeeUPI, amount: amountVal, qrImageUrl: generateQRCodeURL(upiLink, 250) });
    setPayStep(2);

    // Also generate OTP for verification (needs login token)
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await paymentsAPI.generatePaymentOTP({
          amount: parseFloat(amount),
          items: productInfo ? [{ product_name: productInfo.name, quantity: 1, price_per_kg: productInfo.price }] : [],
          farmer_id: productInfo?.farmer_id || null,
          buyer_phone: phone, buyer_email: '',
        });
      }
    } catch (err) { /* OTP generation is optional for non-logged-in users */ }
  };

  const handlePaidClick = () => setPayStep(3);

  /* Verify OTP */
  const handleVerifyOTP = async () => {
    if (!otpInput || otpInput.length !== 6) { toast.error('Enter the 6-digit OTP'); return; }
    setOtpLoading(true);
    try {
      const res = await paymentsAPI.verifyPaymentOTP({ otp: otpInput });
      if (res.data?.verified) { setPaymentSuccess(res.data.payment); setPayStep(4); }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Invalid or expired OTP');
    } finally { setOtpLoading(false); }
  };

  const resetPayModal = () => {
    setShowPayModal(false); setPayStep(1); setQrData(null); setOtpInput('');
    setPayForm({ phone: '', amount: '', productId: '', upiId: '' });
    setPaymentSuccess(null); setProductInfo(null);
  };

  /* ──────── INPUT STYLE ──────── */
  const inputStyle = {
    width: '100%', padding: '12px 14px', borderRadius: '10px', fontSize: '0.95rem',
    border: '2px solid #d1d5db', outline: 'none', fontFamily: 'Poppins, sans-serif',
    boxSizing: 'border-box', transition: 'border-color 0.2s',
  };

  return (
    <div className="landing-page">
      {/* Background */}
      <div className="background-gradient">
        <div className="orb orb-1"></div><div className="orb orb-2"></div><div className="orb orb-3"></div>
      </div>

      {/* Header */}
      <header className="landing-header sticky-header">
        <div className="container header-container">
          <div className="logo">SmartFarm</div>
          <nav className="header-nav">
            <a href="#features" className="nav-link">Features</a>
            <a href="#roles" className="nav-link">Get Started</a>
            <a href="#footer" className="nav-link">Contact</a>
            <button className="otp-shine-btn" onClick={() => setShowPayModal(true)}>
              UPI Payment
            </button>
            <button className="btn btn-outline" onClick={() => navigate('/login')}>Login</button>
          </nav>
        </div>
      </header>

      {/* ════════════════ UPI PAYMENT MODAL ════════════════ */}
      {showPayModal && (
        <div className="otp-modal-overlay" onClick={resetPayModal}>
          <div className="otp-modal-box" style={{ maxWidth: '440px', position: 'relative', overflow: 'hidden' }} onClick={e => e.stopPropagation()}>

            {/* ─── STEP 1: Enter Details ─── */}
            {payStep === 1 && (<>
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '4px' }}>💳</div>
                <h2 style={{ margin: '0 0 4px', fontSize: '1.3rem', color: '#14532d' }}>UPI Quick Payment</h2>
                <p style={{ margin: 0, fontSize: '0.82rem', color: '#6b7280' }}>Enter details to generate a UPI QR code</p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Phone */}
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#374151', display: 'block', marginBottom: '4px' }}>Phone Number *</label>
                  <input type="tel" maxLength={10} value={payForm.phone}
                    onChange={e => setPayForm(p => ({ ...p, phone: e.target.value.replace(/\D/g, '') }))}
                    placeholder="Enter 10-digit number" style={inputStyle} />
                </div>
                {/* UPI ID */}
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#374151', display: 'block', marginBottom: '4px' }}>UPI ID (optional)</label>
                  <input type="text" value={payForm.upiId}
                    onChange={e => setPayForm(p => ({ ...p, upiId: e.target.value }))}
                    placeholder="e.g. 9876543210@ybl or name@paytm" style={inputStyle} />
                </div>
                {/* Product ID */}
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#374151', display: 'block', marginBottom: '4px' }}>Product ID (optional - auto fills price)</label>
                  <input type="text" value={payForm.productId}
                    onChange={e => handleProductIdChange(e.target.value)}
                    placeholder="Enter product ID" style={inputStyle} />
                  {loadingProduct && <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>Looking up product...</span>}
                  {productInfo && (
                    <div style={{ marginTop: '6px', padding: '8px 12px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0', fontSize: '0.82rem' }}>
                      <strong style={{ color: '#166534' }}>{productInfo.name}</strong>
                      <span style={{ marginLeft: '8px', color: '#6b7280' }}>Rs.{productInfo.price}/{productInfo.unit || 'kg'}</span>
                    </div>
                  )}
                </div>
                {/* Amount */}
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#374151', display: 'block', marginBottom: '4px' }}>Amount (Rs.) *</label>
                  <input type="number" min="1" value={payForm.amount}
                    onChange={e => setPayForm(p => ({ ...p, amount: e.target.value }))}
                    placeholder="Enter amount" style={{ ...inputStyle, fontSize: '1.1rem', fontWeight: 700 }} />
                </div>
              </div>

              <button className="otp-verify-btn" onClick={handleGenerateQR}
                disabled={!payForm.phone || !payForm.amount} style={{ marginTop: '16px' }}>
                Generate UPI QR Code
              </button>
              <button className="otp-cancel-btn" onClick={resetPayModal}>Cancel</button>
            </>)}

            {/* ─── STEP 2: QR Code ─── */}
            {payStep === 2 && qrData && (<>
              <div style={{ textAlign: 'center' }}>
                <h2 style={{ margin: '0 0 4px', fontSize: '1.2rem', color: '#14532d' }}>Scan to Pay</h2>
                <p style={{ margin: '0 0 16px', fontSize: '0.82rem', color: '#6b7280' }}>Open GPay / PhonePe / Paytm and scan</p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', background: '#f0fdf4', borderRadius: '16px', border: '2px solid #bbf7d0' }}>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#166534', marginBottom: '12px' }}>
                  Rs.{qrData.amount}
                </div>
                <div style={{ background: '#fff', padding: '16px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(22,101,52,0.12)' }}>
                  <img src={qrData.qrImageUrl} alt="UPI QR Code" style={{ width: '220px', height: '220px', display: 'block' }} />
                </div>
                <p style={{ margin: '12px 0 2px', fontSize: '0.75rem', color: '#6b7280' }}>Pay to:</p>
                <p style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#166534', background: '#dcfce7', padding: '5px 14px', borderRadius: '8px', fontFamily: 'monospace' }}>
                  {qrData.payeeUPI}
                </p>
                {productInfo && (
                  <p style={{ margin: '6px 0 0', fontSize: '0.75rem', color: '#6b7280' }}>
                    Product: {productInfo.name} (ID: {payForm.productId})
                  </p>
                )}
              </div>

              {/* Open UPI App button */}
              <div style={{ display: 'flex', justifyContent: 'center', margin: '14px 0 6px' }}>
                <a href={qrData.upiLink} style={{
                  display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '10px 24px',
                  borderRadius: '10px', fontSize: '0.85rem', fontWeight: 700,
                  background: 'linear-gradient(135deg,#166534,#22c55e)', color: '#fff', textDecoration: 'none',
                }}>Open UPI App</a>
              </div>

              <button className="otp-verify-btn" onClick={handlePaidClick}
                style={{ background: 'linear-gradient(135deg,#1d4ed8,#3b82f6)' }}>
                I have Paid - Verify Now
              </button>
              <button className="otp-cancel-btn" onClick={() => setPayStep(1)}>Back</button>
            </>)}

            {/* ─── STEP 3: OTP Verify ─── */}
            {payStep === 3 && (<>
              <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                <div style={{ fontSize: '2.2rem' }}>🔐</div>
                <h2 style={{ margin: '4px 0', fontSize: '1.2rem', color: '#14532d' }}>Verify Payment</h2>
                <p style={{ margin: 0, fontSize: '0.82rem', color: '#6b7280' }}>Enter the 6-digit OTP sent to your email</p>
              </div>

              <div style={{ background: '#f0fdf4', borderRadius: '12px', padding: '10px 16px', margin: '10px 0', border: '1px solid #bbf7d0', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: '#166534' }}>Rs.{qrData?.amount || payForm.amount}</p>
                <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: '#6b7280' }}>to {qrData?.payeeUPI || payForm.upiId || payForm.phone + '@upi'}</p>
              </div>

              <div className="otp-input-wrapper">
                <input type="text" maxLength={6} value={otpInput}
                  onChange={e => setOtpInput(e.target.value.replace(/\D/g, ''))}
                  placeholder="Enter 6-digit OTP" className="otp-input-field" autoFocus />
              </div>

              <button className="otp-verify-btn" onClick={handleVerifyOTP}
                disabled={otpLoading || otpInput.length !== 6}>
                {otpLoading ? <span className="otp-spinner"></span> : 'Verify & Complete Payment'}
              </button>
              <button className="otp-cancel-btn" onClick={() => setPayStep(2)}>Back</button>
            </>)}

            {/* ─── STEP 4: Success + Receipt ─── */}
            {payStep === 4 && paymentSuccess && (<>
              {/* Confetti */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '200px', overflow: 'hidden', pointerEvents: 'none' }}>
                {[...Array(20)].map((_, i) => (
                  <div key={i} style={{
                    position: 'absolute', left: `${Math.random()*100}%`, top: '-20px',
                    width: `${6+Math.random()*8}px`, height: `${6+Math.random()*8}px`,
                    borderRadius: Math.random()>0.5 ? '50%' : '2px',
                    backgroundColor: ['#22c55e','#166534','#facc15','#f97316','#3b82f6','#a855f7'][i%6],
                    animation: `confettiFall ${1.5+Math.random()*2}s ease-out ${Math.random()*0.5}s forwards`,
                  }}></div>
                ))}
              </div>

              <div style={{ textAlign: 'center', position: 'relative' }}>
                <div style={{
                  width: '70px', height: '70px', borderRadius: '50%',
                  background: 'linear-gradient(135deg,#22c55e,#16a34a)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 12px', fontSize: '2rem', color: '#fff',
                  boxShadow: '0 6px 24px rgba(34,197,94,0.4)', animation: 'scaleIn 0.5s ease-out',
                }}>✓</div>
                <h2 style={{ margin: '0 0 4px', color: '#166534', fontSize: '1.3rem' }}>Payment Successful!</h2>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#166534', margin: '6px 0' }}>
                  Rs.{paymentSuccess.amount?.toFixed(2)}
                </div>
                <div style={{ background: '#f1f5f9', padding: '5px 14px', borderRadius: '8px', display: 'inline-block', fontSize: '0.75rem', color: '#475569', fontFamily: 'monospace' }}>
                  TXN: {paymentSuccess.transaction_id}
                </div>
              </div>

              {/* Receipt */}
              <div style={{ margin: '14px 0', background: '#fafafa', borderRadius: '12px', padding: '12px 14px', border: '1px solid #e5e7eb' }}>
                {paymentSuccess.buyer?.name && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', fontSize: '0.82rem', borderBottom: '1px solid #f3f4f6' }}>
                    <span style={{ color: '#6b7280' }}>Buyer</span>
                    <span style={{ fontWeight: 600, color: '#1f2937' }}>{paymentSuccess.buyer.name}</span>
                  </div>
                )}
                {paymentSuccess.farmer?.name && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', fontSize: '0.82rem', borderBottom: '1px solid #f3f4f6' }}>
                    <span style={{ color: '#6b7280' }}>Farmer</span>
                    <span style={{ fontWeight: 600, color: '#1f2937' }}>{paymentSuccess.farmer.name}</span>
                  </div>
                )}
                {paymentSuccess.items?.length > 0 && paymentSuccess.items.map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', fontSize: '0.82rem', borderBottom: '1px solid #f3f4f6' }}>
                    <span style={{ color: '#6b7280' }}>{item.product_name || 'Product'}</span>
                    <span style={{ fontWeight: 600 }}>{item.quantity || 1} x Rs.{item.price_per_kg || item.price}</span>
                  </div>
                ))}
                {paymentSuccess.farmer?.upi_id && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', fontSize: '0.82rem' }}>
                    <span style={{ color: '#6b7280' }}>Paid to UPI</span>
                    <span style={{ fontWeight: 600, color: '#166534', fontFamily: 'monospace' }}>{paymentSuccess.farmer.upi_id}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0 4px', fontSize: '1rem', fontWeight: 700, borderTop: '2px solid #22c55e' }}>
                  <span style={{ color: '#166534' }}>Total Paid</span>
                  <span style={{ color: '#166534' }}>Rs.{paymentSuccess.amount?.toFixed(2)}</span>
                </div>
              </div>

              <button className="otp-verify-btn" onClick={resetPayModal}
                style={{ background: 'linear-gradient(135deg,#22c55e,#16a34a)' }}>
                Done
              </button>
            </>)}
          </div>
        </div>
      )}

      {/* Hero */}
      <section className="hero" style={{ transform: `translateY(${scrollY * 0.5}px)` }}>
        <div className="container hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="gradient-text">Smart Farming</span><br />
              <span className="gradient-text-2">Marketplace Platform</span>
            </h1>
            <p className="hero-subtitle">
              Revolutionizing agriculture by connecting farmers directly with buyers.
              Get fair prices, fresh produce, and real-time market insights powered by AI.
            </p>
            <div className="hero-buttons">
              <button className="btn btn-primary btn-large animate-slide-in" onClick={() => navigate('/login')}>
                Get Started <FiArrowRight size={18} />
              </button>
              <button className="btn btn-outline btn-large animate-slide-in-delay"
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>
                Learn More
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat"><span className="stat-number">50K+</span><span className="stat-label">Farmers</span></div>
              <div className="stat"><span className="stat-number">100K+</span><span className="stat-label">Products</span></div>
              <div className="stat"><span className="stat-number">Rs.500Cr+</span><span className="stat-label">Transactions</span></div>
            </div>
          </div>
          <div className="hero-image">
            <div className="floating-cards-grid">
              <div className="floating-card card-1"><div className="card-icon">🚜</div><p>Farmer Dashboard</p><span className="card-badge">Manage</span></div>
              <div className="floating-card card-2"><div className="card-icon">📊</div><p>Live Analytics</p><span className="card-badge live">Real-time</span></div>
              <div className="floating-card card-3"><div className="card-icon">🛒</div><p>Smart Shopping</p><span className="card-badge">Browse</span></div>
              <div className="floating-card card-4"><div className="card-icon">🤖</div><p>AI Predictions</p><span className="card-badge ai">Smart</span></div>
              <div className="floating-card card-5"><div className="card-icon">🌦️</div><p>Weather Alerts</p><span className="card-badge weather">Live</span></div>
              <div className="floating-card card-6"><div className="card-icon">💳</div><p>Digital Wallet</p><span className="card-badge wallet">Secure</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features-section" id="features">
        <div className="container">
          <h2 className="section-title">Why Choose SmartFarm?</h2>
          <div className={`features-grid ${showFeatures ? 'show' : ''}`}>
            <div className="feature-card"><div className="feature-icon">🤖</div><h3>AI-Powered Insights</h3><p>Get personalized crop recommendations and price predictions using advanced machine learning.</p></div>
            <div className="feature-card"><div className="feature-icon">💰</div><h3>Better Prices</h3><p>Direct connections eliminate middlemen, ensuring fair pricing for all.</p></div>
            <div className="feature-card"><div className="feature-icon">📱</div><h3>Real-Time Updates</h3><p>Get instant notifications about orders, prices, and market opportunities.</p></div>
            <div className="feature-card"><div className="feature-icon">🌍</div><h3>Weather Integration</h3><p>Access accurate weather forecasts and agriculture-specific alerts for your region.</p></div>
            <div className="feature-card"><div className="feature-icon">🔒</div><h3>Secure & Trusted</h3><p>Bank-level security with verified farmer and buyer profiles.</p></div>
            <div className="feature-card"><div className="feature-icon">🚚</div><h3>Easy Logistics</h3><p>Simplified delivery tracking and management for hassle-free transactions.</p></div>
          </div>
        </div>
      </section>

      {/* Roles */}
      <section className="roles-section" id="roles">
        <div className="container">
          <h2 className="section-title">Choose Your Role</h2>
          <p className="section-subtitle">Join as a Farmer or Buyer and start transforming agriculture today</p>
          <div className="roles-grid">
            <div className="role-card farmer-card">
              <div className="role-icon">👨‍🌾</div><h3>I'm a Farmer</h3>
              <p>Sell your produce directly to buyers, get fair prices, and grow your business.</p>
              <ul className="role-features"><li>✓ Manage products & inventory</li><li>✓ Get price recommendations</li><li>✓ Track orders in real-time</li><li>✓ Access weather forecasts</li><li>✓ AI crop suggestions</li></ul>
              <button className="role-btn" onClick={() => navigate('/login')}>Farmer Login</button>
            </div>
            <div className="role-card buyer-card">
              <div className="role-icon">👩‍💼</div><h3>I'm a Buyer</h3>
              <p>Find fresh produce directly from farmers with guaranteed quality and freshness.</p>
              <ul className="role-features"><li>✓ Browse fresh products</li><li>✓ Direct farmer connections</li><li>✓ Secure checkout</li><li>✓ Order tracking</li><li>✓ Reviews & ratings</li></ul>
              <button className="role-btn" onClick={() => navigate('/login')}>Buyer Login</button>
            </div>
            <div className="role-card admin-card">
              <div className="role-icon">👨‍💻</div><h3>I'm an Admin</h3>
              <p>Manage platform, approve users, monitor transactions, and ensure quality standards.</p>
              <ul className="role-features"><li>✓ User management</li><li>✓ Product approval</li><li>✓ Order monitoring</li><li>✓ Analytics dashboard</li><li>✓ Dispute resolution</li></ul>
              <button className="role-btn" onClick={() => navigate('/login')}>Admin Login</button>
            </div>
          </div>
        </div>
      </section>

      {/* Auth Options */}
      <section className="auth-options-section">
        <div className="container">
          <h2 className="section-title">Quick Access</h2>
          <p className="section-subtitle">Choose how you want to get started</p>
          <div className="auth-methods">
            <button className="auth-method-card" onClick={handleGoogleAuth}><div className="method-icon">🔑</div><h4>Continue with Google</h4><p>Fast and secure login</p></button>
            <button className="auth-method-card" onClick={handleMobileOTP}><div className="method-icon">📱</div><h4>Continue with Mobile OTP</h4><p>One-time password verification</p></button>
            <button className="auth-method-card" onClick={() => navigate('/login')}><div className="method-icon">✉️</div><h4>Email & Password</h4><p>Traditional login method</p></button>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <div className="workflow-grid">
            <div className="workflow-item"><div className="workflow-number">1</div><h4>Sign Up</h4><p>Create your account as farmer or buyer in seconds</p></div>
            <div className="workflow-item"><div className="workflow-number">2</div><h4>Verify Profile</h4><p>Verify your identity through email or phone OTP</p></div>
            <div className="workflow-item"><div className="workflow-number">3</div><h4>Start Trading</h4><p>Farmers list products, buyers browse and purchase</p></div>
            <div className="workflow-item"><div className="workflow-number">4</div><h4>Get Paid</h4><p>Receive payments securely through our platform</p></div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Transform Your Agriculture Business?</h2>
            <p>Join thousands of farmers and buyers already using SmartFarm</p>
            <button className="btn btn-large" onClick={() => navigate('/login')}>Get Started Now <FiArrowRight size={20} /></button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer" id="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-section"><h4>SmartFarm</h4><p>Connecting farmers with buyers for better agriculture</p></div>
            <div className="footer-section"><h4>Quick Links</h4><ul><li><a href="#features">Features</a></li><li><a href="#roles">Get Started</a></li><li><a href="#footer">Contact</a></li></ul></div>
            <div className="footer-section"><h4>Support</h4><ul><li><a href="mailto:gundesandeep2005@gmail.com?subject=SmartFarm%20Help%20Request">Help Center</a></li><li><a href="mailto:gundesandeep2005@gmail.com?subject=SmartFarm%20Contact%20Us">Contact Us</a></li><li><a href="#faq">FAQ</a></li></ul></div>
            <div className="footer-section"><h4>Legal</h4><ul><li><a href="#privacy">Privacy Policy</a></li><li><a href="#terms">Terms & Conditions</a></li><li><a href="#cookies">Cookie Policy</a></li></ul></div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2026 SmartFarm. All rights reserved.</p>
            <div className="social-links"><a href="#facebook">f</a><a href="#twitter">X</a><a href="#instagram">IG</a><a href="#linkedin">in</a></div>
          </div>
        </div>
      </footer>

      {/* Animations */}
      <style>{`
        @keyframes confettiFall {
          0%{transform:translateY(-20px) rotate(0deg);opacity:1}
          100%{transform:translateY(200px) rotate(720deg);opacity:0}
        }
        @keyframes scaleIn {
          0%{transform:scale(0)} 60%{transform:scale(1.2)} 100%{transform:scale(1)}
        }
      `}</style>
    </div>
  );
};

export default LandingPage;
