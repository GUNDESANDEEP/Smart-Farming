import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiMail, FiLock, FiPhone, FiArrowRight, FiUser, FiShield, FiEye, FiEyeOff } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { authAPI, tokenUtils } from '../services/api';
import useAuthStore from '../services/authStore';
import '../styles/auth.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [userType, setUserType] = useState('farmer');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', phone: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  // Buyer OTP verification state
  const [otpStep, setOtpStep] = useState(1);
  const [otp, setOtp] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [buyerLoginData, setBuyerLoginData] = useState(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotStep, setForgotStep] = useState(1);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotOtp, setForgotOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const cursorRef = useRef(null);
  const trailsRef = useRef([]);

  // Custom cursor trail effect
  useEffect(() => {
    const cursor = cursorRef.current;
    let trails = [];
    
    const createTrail = (x, y) => {
      const trail = document.createElement('div');
      trail.className = 'cursor-trail';
      trail.style.left = x + 'px';
      trail.style.top = y + 'px';
      document.body.appendChild(trail);
      
      setTimeout(() => {
        trail.style.opacity = '0';
        trail.style.transform = 'scale(0) rotate(180deg)';
      }, 10);
      
      setTimeout(() => {
        if (trail.parentNode) trail.parentNode.removeChild(trail);
      }, 800);
    };

    let lastTime = 0;
    const handleMouseMove = (e) => {
      if (cursor) {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
      }
      
      const now = Date.now();
      if (now - lastTime > 60) {
        createTrail(e.clientX, e.clientY);
        lastTime = now;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.querySelectorAll('.cursor-trail').forEach(t => t.remove());
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Complete login (shared by farmer/admin direct login and buyer post-OTP)
  const completeLogin = (data) => {
    const token = data.access_token || data.token;
    const refreshToken = data.refresh_token;
    const user = data.user;

    if (!token) {
      toast.error('Login failed');
      return;
    }

    if (!user.role) user.role = userType;
    if (!user.name) {
      user.name = user.first_name
        ? `${user.first_name} ${user.last_name || ''}`.trim()
        : user.email || user.phone;
    }

    tokenUtils.setTokens(token, refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
    login(user, token);

    toast.success(`Welcome back, ${user.name}!`, { icon: '🌾' });

    const dashboardRoutes = { farmer: '/farmer', buyer: '/buyer', admin: '/admin' };
    navigate(dashboardRoutes[user.role] || '/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let response;
      if (userType === 'farmer') {
        response = await authAPI.farmerLogin(formData.email, formData.password);
      } else if (userType === 'buyer') {
        response = await authAPI.buyerLogin(formData.phone, formData.password);
      } else {
        response = await authAPI.adminLogin(formData.email, formData.password);
      }

      const data = response.data;

      // All roles: complete login directly
      completeLogin(data);
    } catch (error) {
      const msg = error.response?.data?.error || error.response?.data?.message || 'Login failed. Check your credentials.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // Buyer OTP handlers
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (otp.length !== 6) {
      toast.error('Please enter the 6-digit OTP');
      return;
    }
    setOtpLoading(true);
    try {
      const res = await authAPI.verifyOTP(buyerLoginData.user.email, otp);
      if (res.data.verified) {
        toast.success('OTP verified!', { icon: '✅' });
        completeLogin(buyerLoginData);
      } else {
        toast.error('Invalid OTP. Please try again.');
      }
    } catch (error) {
      const msg = error.response?.data?.error || 'Invalid or expired OTP';
      toast.error(msg);
    } finally {
      setOtpLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (!buyerLoginData?.user?.email) return;
    setOtpLoading(true);
    try {
      await authAPI.sendOTP(buyerLoginData.user.email);
      toast.success('OTP resent!', { icon: '📧' });
      setOtp('');
    } catch (error) {
      toast.error('Failed to resend OTP.');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotEmail) { toast.error('Enter your email'); return; }
    setForgotLoading(true);
    try {
      await authAPI.forgotPassword(forgotEmail);
      toast.success('OTP sent to your email!');
      setForgotStep(2);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send OTP');
    } finally { setForgotLoading(false); }
  };

  const handleResetPassword = async () => {
    if (!forgotOtp || !newPassword) { toast.error('Fill all fields'); return; }
    if (newPassword.length < 6) { toast.error('Password must be 6+ characters'); return; }
    setForgotLoading(true);
    try {
      await authAPI.resetPassword(forgotEmail, forgotOtp, newPassword);
      toast.success('Password reset successful! Please login.');
      setShowForgotPassword(false);
      setForgotStep(1);
      setForgotEmail(''); setForgotOtp(''); setNewPassword('');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to reset password');
    } finally { setForgotLoading(false); }
  };

  return (
    <div className="auth-page">
      {/* Custom Cursor */}
      <div ref={cursorRef} className="custom-cursor"></div>
      
      {/* Animated Background Particles */}
      <div className="auth-particles">
        {[...Array(6)].map((_, i) => (
          <div key={i} className={`particle p${i + 1}`}>🍃</div>
        ))}
      </div>

      <div className="auth-container">
        {/* Glass Card */}
        <div className="auth-glass-card">
          {/* Avatar Circle */}
          <div className="auth-avatar">
            <div className="avatar-circle">
              {userType === 'farmer' ? '👨‍🌾' : userType === 'buyer' ? '🛒' : '🛡️'}
            </div>
          </div>

          {/* Role Tabs */}
          <div className="role-tabs">
            <button
              className={`role-tab ${userType === 'farmer' ? 'active' : ''}`}
              onClick={() => setUserType('farmer')}
              type="button"
            >
              <FiUser size={14} /> Farmer
            </button>
            <button
              className={`role-tab ${userType === 'buyer' ? 'active' : ''}`}
              onClick={() => setUserType('buyer')}
              type="button"
            >
              <FiUser size={14} /> Buyer
            </button>
            <button
              className={`role-tab ${userType === 'admin' ? 'active' : ''}`}
              onClick={() => setUserType('admin')}
              type="button"
            >
              <FiShield size={14} /> Admin
            </button>
          </div>

          {/* Buyer OTP Step */}
          {userType === 'buyer' && otpStep === 2 ? (
            <form onSubmit={handleVerifyOTP} className="auth-form">
              <p style={{ textAlign: 'center', color: '#d1fae5', marginBottom: '8px', fontSize: '14px' }}>
                📧 OTP sent to <strong>{buyerLoginData?.user?.email}</strong>
              </p>
              <div className="glass-input">
                <FiShield className="input-icon" />
                <input
                  type="text"
                  maxLength="6"
                  placeholder="Enter 6-digit OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  style={{ letterSpacing: '6px', textAlign: 'center', fontSize: '20px' }}
                />
              </div>
              <button type="submit" className="login-btn" disabled={otpLoading}>
                {otpLoading ? <span className="btn-loader"></span> : 'VERIFY OTP'}
                {!otpLoading && <FiArrowRight />}
              </button>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => { setOtpStep(1); setOtp(''); setBuyerLoginData(null); }}
                  style={{ background: 'none', border: 'none', color: '#86efac', cursor: 'pointer', fontSize: '13px' }}
                >
                  ← Back to Login
                </button>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={otpLoading}
                  style={{ background: 'none', border: 'none', color: '#86efac', cursor: 'pointer', fontSize: '13px' }}
                >
                  Resend OTP
                </button>
              </div>
            </form>
          ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {userType === 'buyer' ? (
              <div className="glass-input">
                <FiPhone className="input-icon" />
                <input
                  type="tel"
                  name="phone"
                  placeholder="Phone Number"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>
            ) : (
              <div className="glass-input">
                <FiMail className="input-icon" />
                <input
                  type="email"
                  name="email"
                  placeholder="Email ID"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
            )}

            <div className="glass-input">
              <FiLock className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>

            <div className="auth-options">
              <label className="remember-check">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                onClick={() => setShowForgotPassword(true)}
                className="forgot-link"
                style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer', textDecoration: 'underline', fontFamily: 'Poppins', fontSize: '0.9rem', padding: 0 }}
              >
                Forgot Password?
              </button>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? <span className="btn-loader"></span> : 'LOGIN'}
              {!loading && <FiArrowRight />}
            </button>
          </form>
          )}

          {/* Footer */}
          {userType !== 'admin' ? (
            <div className="auth-footer">
              <p>Don't have an account?</p>
              <div className="signup-links">
                <Link to="/signup/farmer">Register as Farmer</Link>
                <span>•</span>
                <Link to="/signup/buyer">Register as Buyer</Link>
              </div>
            </div>
          ) : (
            <div className="auth-footer">
              <p className="admin-note">🔒 Admin access restricted to authorized personnel</p>
            </div>
          )}
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotPassword && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999,
        }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.97), rgba(240,253,244,0.97))',
            borderRadius: '20px', padding: '36px', width: '400px', maxWidth: '90vw',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)', border: '1px solid rgba(34,197,94,0.2)',
            position: 'relative',
          }}>
            <button
              onClick={() => { setShowForgotPassword(false); setForgotStep(1); setForgotEmail(''); setForgotOtp(''); setNewPassword(''); }}
              style={{ position: 'absolute', top: '14px', right: '14px', background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: '#666' }}
            >✕</button>

            <h2 style={{ margin: '0 0 6px', color: '#14532d', fontSize: '1.4rem', fontFamily: 'Poppins' }}>🔐 Reset Password</h2>
            <p style={{ margin: '0 0 20px', color: '#666', fontSize: '0.85rem' }}>
              {forgotStep === 1 && 'Enter your email to receive a reset OTP.'}
              {forgotStep === 2 && 'Enter the OTP sent to your email.'}
              {forgotStep === 3 && 'Set your new password.'}
            </p>

            {forgotStep === 1 && (
              <div>
                <input
                  type="email" placeholder="Enter your email" value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', border: '1px solid rgba(22,163,74,0.2)', fontSize: '0.95rem', fontFamily: 'Poppins', boxSizing: 'border-box', marginBottom: '16px', outline: 'none' }}
                />
                <button onClick={handleForgotPassword} disabled={forgotLoading}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', background: 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none', fontSize: '1rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'Poppins' }}
                >{forgotLoading ? 'Sending...' : 'Send OTP'}</button>
              </div>
            )}

            {forgotStep === 2 && (
              <div>
                <input
                  type="text" placeholder="Enter 6-digit OTP" value={forgotOtp} maxLength="6"
                  onChange={(e) => setForgotOtp(e.target.value.replace(/\D/g, ''))}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', border: '1px solid rgba(22,163,74,0.2)', fontSize: '1.2rem', fontFamily: 'Poppins', boxSizing: 'border-box', marginBottom: '16px', outline: 'none', letterSpacing: '6px', textAlign: 'center' }}
                />
                <button onClick={() => setForgotStep(3)} disabled={forgotOtp.length !== 6}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', background: forgotOtp.length === 6 ? 'linear-gradient(135deg, #166534, #22c55e)' : '#ccc', color: '#fff', border: 'none', fontSize: '1rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'Poppins' }}
                >Verify & Continue</button>
              </div>
            )}

            {forgotStep === 3 && (
              <div>
                <input
                  type="password" placeholder="New password (min 6 chars)" value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', border: '1px solid rgba(22,163,74,0.2)', fontSize: '0.95rem', fontFamily: 'Poppins', boxSizing: 'border-box', marginBottom: '16px', outline: 'none' }}
                />
                <button onClick={handleResetPassword} disabled={forgotLoading}
                  style={{ width: '100%', padding: '14px', borderRadius: '12px', background: 'linear-gradient(135deg, #166534, #22c55e)', color: '#fff', border: 'none', fontSize: '1rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'Poppins' }}
                >{forgotLoading ? 'Resetting...' : 'Reset Password'}</button>
              </div>
            )}

            {forgotStep > 1 && (
              <button onClick={() => setForgotStep(forgotStep - 1)}
                style={{ marginTop: '12px', background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer', fontSize: '0.85rem', fontFamily: 'Poppins' }}
              >← Back</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
