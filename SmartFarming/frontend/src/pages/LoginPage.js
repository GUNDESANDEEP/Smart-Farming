import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiMail, FiLock, FiPhone, FiArrowRight, FiUser, FiShield, FiEye, FiEyeOff } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { authAPI, tokenUtils, getErrorMessage } from '../services/api';
import useAuthStore from '../services/authStore';
import '../styles/auth.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, role } = useAuthStore();
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

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated && role) {
      const dashboardRoutes = { farmer: '/farmer', buyer: '/buyer', admin: '/admin' };
      navigate(dashboardRoutes[role] || '/', { replace: true });
    }
  }, [isAuthenticated, role, navigate]);

  // Cursor trail is handled by GlobalCursor component in App.js

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
    login(user, token, refreshToken);

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
        // Farmer can login with email or phone — send both, backend detects
        const input = (formData.email || '').trim();
        response = await authAPI.farmerLogin(input, formData.password);
      } else if (userType === 'buyer') {
        // Send input to buyerLogin — backend handles email vs phone detection
        // If the email belongs to an admin, backend auto-detects and logs in as admin
        const input = (formData.phone || '').trim();
        response = await authAPI.buyerLogin(input, formData.password);
      }

      const data = response.data;

      // Check if OTP verification is required
      if (data.otp_required) {
        setBuyerLoginData(data);
        setOtpStep(2);
        toast.success(`OTP sent to ${data.user?.email}`, { icon: '📧', duration: 5000 });
      } else {
        // Direct login (no email on account)
        completeLogin(data);
      }
    } catch (error) {
      // Don't show error toast for silent auth redirects
      if (error._silentAuthRedirect) return;

      const msg = getErrorMessage(error);
      if (msg) {
        // Choose icon based on error type
        const icon = error._isNetworkError ? '🔌'
          : error._isTimeoutError ? '⏱️'
          : error.response?.status === 503 ? '🔄'
          : '❌';
        toast.error(msg, { icon, duration: 6000 });
      }
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
      const res = await authAPI.completeLogin(buyerLoginData.user.email, otp, userType);
      if (res.data.verified || res.data.access_token) {
        toast.success('OTP verified! Logging in...', { icon: '✅' });
        completeLogin(res.data);
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
      {/* Animated Background Particles */}
      <div className="auth-particles">
        {[...Array(3)].map((_, i) => (
          <div key={i} className={`particle p${i + 1}`}>🍃</div>
        ))}
      </div>

      <div className="auth-container">
        {/* Glass Card */}
        <div className="auth-glass-card">
          {/* Avatar Circle */}
          <div className="auth-avatar">
            <div className="avatar-circle">
              {userType === 'farmer' ? '👨‍🌾' : '🛒'}
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
          </div>

          {/* Buyer OTP Step */}
          {otpStep === 2 ? (
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
                {formData.phone && formData.phone.includes('@') ? (
                  <FiMail className="input-icon" />
                ) : (
                  <FiPhone className="input-icon" />
                )}
                <input
                  type="text"
                  name="phone"
                  placeholder="Phone Number or Email"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>
            ) : (
              <div className="glass-input">
                {formData.email && /^\d/.test(formData.email) ? (
                  <FiPhone className="input-icon" />
                ) : (
                  <FiMail className="input-icon" />
                )}
                <input
                  type="text"
                  name="email"
                  placeholder="Email or Phone Number"
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
          <div className="auth-footer">
            <p>Don't have an account?</p>
            <div className="signup-links">
              <Link to="/signup/farmer">Register as Farmer</Link>
              <span>•</span>
              <Link to="/signup/buyer">Register as Buyer</Link>
            </div>
          </div>
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
