import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowRight, FiUsers, FiTrendingUp, FiAward, FiShoppingCart, FiMapPin } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { paymentsAPI } from '../services/api';
import '../styles/landing.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [showFeatures, setShowFeatures] = useState(false);
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [otpInput, setOtpInput] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setTimeout(() => setShowFeatures(true), 500);
  }, []);

  const handleGoogleAuth = () => {
    toast.error('Google authentication coming soon!');
  };

  const handleMobileOTP = () => {
    toast.error('Mobile OTP coming soon!');
  };

  const handleVerifyPaymentOTP = async () => {
    if (!otpInput || otpInput.length !== 6) {
      toast.error('Enter a valid 6-digit OTP');
      return;
    }
    setOtpLoading(true);
    try {
      const res = await paymentsAPI.verifyPaymentOTP({ otp: otpInput });
      if (res.data.verified) {
        setPaymentSuccess(res.data.payment);
        setShowOtpModal(false);
        setOtpInput('');
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Invalid or expired OTP');
    } finally {
      setOtpLoading(false);
    }
  };

  return (
    <div className="landing-page">
      {/* Animated Background */}
      <div className="background-gradient">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      {/* Navigation Header */}
      <header className="landing-header sticky-header">
        <div className="container header-container">
          <div className="logo">🌾 SmartFarm</div>
          <nav className="header-nav">
            <a href="#features" className="nav-link">Features</a>
            <a href="#roles" className="nav-link">Get Started</a>
            <a href="#footer" className="nav-link">Contact</a>
            <button className="otp-shine-btn" onClick={() => setShowOtpModal(true)}>
              🔐 Buyers Payment OTP
            </button>
            <button className="btn btn-outline" onClick={() => navigate('/login')}>
              Login
            </button>
          </nav>
        </div>
      </header>

      {/* OTP Modal */}
      {showOtpModal && (
        <div className="otp-modal-overlay" onClick={() => setShowOtpModal(false)}>
          <div className="otp-modal-box" onClick={e => e.stopPropagation()}>
            <div className="otp-modal-icon">🔐</div>
            <h2 className="otp-modal-title">Payment Verification</h2>
            <p className="otp-modal-desc">Enter the 6-digit OTP sent to your email to confirm payment</p>
            <div className="otp-input-wrapper">
              <input
                type="text"
                maxLength={6}
                value={otpInput}
                onChange={e => setOtpInput(e.target.value.replace(/\D/g, ''))}
                placeholder="● ● ● ● ● ●"
                className="otp-input-field"
                autoFocus
              />
            </div>
            <button
              className="otp-verify-btn"
              onClick={handleVerifyPaymentOTP}
              disabled={otpLoading || otpInput.length !== 6}
            >
              {otpLoading ? (
                <span className="otp-spinner"></span>
              ) : (
                <>✅ Verify & Complete Payment</>
              )}
            </button>
            <button className="otp-cancel-btn" onClick={() => setShowOtpModal(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Animated Payment Success */}
      {paymentSuccess && (
        <div className="payment-success-overlay">
          <div className="confetti-container">
            {[...Array(30)].map((_, i) => (
              <div key={i} className="confetti-piece" style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                backgroundColor: ['#22c55e','#166534','#facc15','#f97316','#3b82f6','#a855f7'][i % 6],
              }}></div>
            ))}
          </div>
          <div className="payment-success-card">
            <div className="success-checkmark">
              <div className="check-icon">✓</div>
            </div>
            <h2 className="success-title">Payment Successful!</h2>
            <div className="success-amount">₹{paymentSuccess.amount?.toFixed(2)}</div>
            <div className="success-txn">TXN: {paymentSuccess.transaction_id}</div>

            <div className="success-details">
              {paymentSuccess.buyer?.name && (
                <div className="success-row">
                  <span>👤 Buyer</span>
                  <span>{paymentSuccess.buyer.name}</span>
                </div>
              )}
              {paymentSuccess.farmer?.name && (
                <div className="success-row">
                  <span>🌾 Farmer</span>
                  <span>{paymentSuccess.farmer.name}</span>
                </div>
              )}
              {paymentSuccess.items?.length > 0 && paymentSuccess.items.map((item, idx) => (
                <div key={idx} className="success-row">
                  <span>📦 {item.product_name || item.name || 'Product'}</span>
                  <span>{item.quantity || item.quantity_kg} kg × ₹{item.price_per_kg}/kg</span>
                </div>
              ))}
              <div className="success-row total-row">
                <span>💰 Total Paid</span>
                <span>₹{paymentSuccess.amount?.toFixed(2)}</span>
              </div>
            </div>

            {paymentSuccess.farmer?.upi_id && (
              <div className="success-upi">
                Paid to UPI: {paymentSuccess.farmer.upi_id}
              </div>
            )}

            <button className="success-done-btn" onClick={() => setPaymentSuccess(null)}>
              Done ✓
            </button>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="hero" style={{ transform: `translateY(${scrollY * 0.5}px)` }}>
        <div className="container hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="gradient-text">🌾 Smart Farming</span>
              <br />
              <span className="gradient-text-2">Marketplace Platform</span>
            </h1>
            <p className="hero-subtitle">
              Revolutionizing agriculture by connecting farmers directly with buyers. Get fair prices, fresh produce, and real-time market insights powered by AI.
            </p>
            
            <div className="hero-buttons">
              <button 
                className="btn btn-primary btn-large animate-slide-in"
                onClick={() => navigate('/login')}
              >
                Get Started <FiArrowRight size={18} />
              </button>
              <button 
                className="btn btn-outline btn-large animate-slide-in-delay"
                onClick={() => {
                  const element = document.getElementById('features');
                  element?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Learn More
              </button>
            </div>

            <div className="hero-stats">
              <div className="stat">
                <span className="stat-number">50K+</span>
                <span className="stat-label">Farmers</span>
              </div>
              <div className="stat">
                <span className="stat-number">100K+</span>
                <span className="stat-label">Products</span>
              </div>
              <div className="stat">
                <span className="stat-number">₹500Cr+</span>
                <span className="stat-label">Transactions</span>
              </div>
            </div>
          </div>

          <div className="hero-image">
            <div className="floating-cards-grid">
              <div className="floating-card card-1">
                <div className="card-icon">🚜</div>
                <p>Farmer Dashboard</p>
                <span className="card-badge">Manage</span>
              </div>
              <div className="floating-card card-2">
                <div className="card-icon">📊</div>
                <p>Live Analytics</p>
                <span className="card-badge live">Real-time</span>
              </div>
              <div className="floating-card card-3">
                <div className="card-icon">🛒</div>
                <p>Smart Shopping</p>
                <span className="card-badge">Browse</span>
              </div>
              <div className="floating-card card-4">
                <div className="card-icon">🤖</div>
                <p>AI Predictions</p>
                <span className="card-badge ai">Smart</span>
              </div>
              <div className="floating-card card-5">
                <div className="card-icon">🌦️</div>
                <p>Weather Alerts</p>
                <span className="card-badge weather">Live</span>
              </div>
              <div className="floating-card card-6">
                <div className="card-icon">💳</div>
                <p>Digital Wallet</p>
                <span className="card-badge wallet">Secure</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" id="features">
        <div className="container">
          <h2 className="section-title">Why Choose SmartFarm?</h2>
          
          <div className={`features-grid ${showFeatures ? 'show' : ''}`}>
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Insights</h3>
              <p>Get personalized crop recommendations and price predictions using advanced machine learning.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">💰</div>
              <h3>Better Prices</h3>
              <p>Direct connections eliminate middlemen, ensuring fair pricing for all.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3>Real-Time Updates</h3>
              <p>Get instant notifications about orders, prices, and market opportunities.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🌍</div>
              <h3>Weather Integration</h3>
              <p>Access accurate weather forecasts and agriculture-specific alerts for your region.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure & Trusted</h3>
              <p>Bank-level security with verified farmer and buyer profiles.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🚚</div>
              <h3>Easy Logistics</h3>
              <p>Simplified delivery tracking and management for hassle-free transactions.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Role Selection Section */}
      <section className="roles-section" id="roles">
        <div className="container">
          <h2 className="section-title">Choose Your Role</h2>
          <p className="section-subtitle">Join as a Farmer or Buyer and start transforming agriculture today</p>

          <div className="roles-grid">
            {/* Farmer Role */}
            <div className="role-card farmer-card">
              <div className="role-icon">👨‍🌾</div>
              <h3>I'm a Farmer</h3>
              <p>Sell your produce directly to buyers, get fair prices, and grow your business.</p>
              <ul className="role-features">
                <li>✓ Manage products & inventory</li>
                <li>✓ Get price recommendations</li>
                <li>✓ Track orders in real-time</li>
                <li>✓ Access weather forecasts</li>
                <li>✓ AI crop suggestions</li>
              </ul>
              <button className="role-btn" onClick={() => navigate('/login')}>
                Farmer Login
              </button>
            </div>

            {/* Buyer Role */}
            <div className="role-card buyer-card">
              <div className="role-icon">👩‍💼</div>
              <h3>I'm a Buyer</h3>
              <p>Find fresh produce directly from farmers with guaranteed quality and freshness.</p>
              <ul className="role-features">
                <li>✓ Browse fresh products</li>
                <li>✓ Direct farmer connections</li>
                <li>✓ Secure checkout</li>
                <li>✓ Order tracking</li>
                <li>✓ Reviews & ratings</li>
              </ul>
              <button className="role-btn" onClick={() => navigate('/login')}>
                Buyer Login
              </button>
            </div>

            {/* Admin Role */}
            <div className="role-card admin-card">
              <div className="role-icon">👨‍💻</div>
              <h3>I'm an Admin</h3>
              <p>Manage platform, approve users, monitor transactions, and ensure quality standards.</p>
              <ul className="role-features">
                <li>✓ User management</li>
                <li>✓ Product approval</li>
                <li>✓ Order monitoring</li>
                <li>✓ Analytics dashboard</li>
                <li>✓ Dispute resolution</li>
              </ul>
              <button className="role-btn" onClick={() => navigate('/login')}>
                Admin Login
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Authentication Options Section */}
      <section className="auth-options-section">
        <div className="container">
          <h2 className="section-title">Quick Access</h2>
          <p className="section-subtitle">Choose how you want to get started</p>

          <div className="auth-methods">
            <button className="auth-method-card" onClick={handleGoogleAuth}>
              <div className="method-icon">🔑</div>
              <h4>Continue with Google</h4>
              <p>Fast and secure login</p>
            </button>

            <button className="auth-method-card" onClick={handleMobileOTP}>
              <div className="method-icon">📱</div>
              <h4>Continue with Mobile OTP</h4>
              <p>One-time password verification</p>
            </button>

            <button 
              className="auth-method-card" 
              onClick={() => navigate('/login')}
            >
              <div className="method-icon">✉️</div>
              <h4>Email & Password</h4>
              <p>Traditional login method</p>
            </button>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          
          <div className="workflow-grid">
            <div className="workflow-item">
              <div className="workflow-number">1</div>
              <h4>Sign Up</h4>
              <p>Create your account as farmer or buyer in seconds</p>
            </div>

            <div className="workflow-item">
              <div className="workflow-number">2</div>
              <h4>Verify Profile</h4>
              <p>Verify your identity through email or phone OTP</p>
            </div>

            <div className="workflow-item">
              <div className="workflow-number">3</div>
              <h4>Start Trading</h4>
              <p>Farmers list products, buyers browse and purchase</p>
            </div>

            <div className="workflow-item">
              <div className="workflow-number">4</div>
              <h4>Get Paid</h4>
              <p>Receive payments securely through our platform</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Transform Your Agriculture Business?</h2>
            <p>Join thousands of farmers and buyers already using SmartFarm</p>
            <button className="btn btn-large" onClick={() => navigate('/login')}>
              Get Started Now <FiArrowRight size={20} />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer" id="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-section">
              <h4>🌾 SmartFarm</h4>
              <p>Connecting farmers with buyers for better agriculture</p>
            </div>

            <div className="footer-section">
              <h4>Quick Links</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#roles">Get Started</a></li>
                <li><a href="#footer">Contact</a></li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Support</h4>
              <ul>
                <li><a href="mailto:gundesandeep2005@gmail.com?subject=SmartFarm%20Help%20Request">Help Center</a></li>
                <li><a href="mailto:gundesandeep2005@gmail.com?subject=SmartFarm%20Contact%20Us">Contact Us</a></li>
                <li><a href="#faq">FAQ</a></li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Legal</h4>
              <ul>
                <li><a href="#privacy">Privacy Policy</a></li>
                <li><a href="#terms">Terms & Conditions</a></li>
                <li><a href="#cookies">Cookie Policy</a></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p>&copy; 2026 SmartFarm. All rights reserved.</p>
            <div className="social-links">
              <a href="#facebook">f</a>
              <a href="#twitter">𝕏</a>
              <a href="#instagram">📷</a>
              <a href="#linkedin">in</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
