import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FiUser, FiMail, FiPhone, FiLock, FiMapPin, FiArrowRight, FiEye, FiEyeOff } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { authAPI, tokenUtils } from '../services/api';
import useAuthStore from '../services/authStore';
import '../styles/auth.css';

const SignupPage = () => {
  const { role } = useParams();
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // Multi-step form
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    location: '',
    district: '',
    farmName: '',
    companyName: '',
    agreeToTerms: false,
  });

  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateStep1 = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.email.includes('@')) newErrors.email = 'Invalid email format';
    if (!formData.phone.trim()) newErrors.phone = 'Phone is required';
    if (formData.phone.length < 10) newErrors.phone = 'Phone must be at least 10 digits';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};
    if (!formData.password) newErrors.password = 'Password is required';
    if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (!formData.confirmPassword) newErrors.confirmPassword = 'Please confirm password';
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    if (!formData.location.trim()) newErrors.location = 'Location is required';
    if (!formData.district.trim()) newErrors.district = 'District is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep3 = () => {
    const newErrors = {};
    if (role === 'farmer' && !formData.farmName.trim()) {
      newErrors.farmName = 'Farm name is required';
    }
    if (role === 'buyer' && !formData.companyName.trim()) {
      newErrors.companyName = 'Company name is required';
    }
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to terms and conditions';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };

  const handlePrev = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateStep3()) return;

    setLoading(true);

    try {
      // Split name into first and last
      const nameParts = formData.name.trim().split(' ');
      const first_name = nameParts[0] || '';
      const last_name = nameParts.slice(1).join(' ') || '';

      const payload = {
        role: role,
        first_name,
        last_name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        location: formData.location,
        district: formData.district,
      };

      // Add role-specific fields
      if (role === 'farmer') {
        payload.farm_name = formData.farmName;
      } else {
        payload.company_name = formData.companyName;
      }

      const response = await authAPI.register(payload);
      const data = response.data;
      const token = data.access_token || data.token;
      const user = data.user;

      if (token && user) {
        tokenUtils.setTokens(token);
        localStorage.setItem('user', JSON.stringify(user));
        login(user, token);
        toast.success(`Welcome, ${user.name || first_name}! Account created successfully. 🌾`);
        const dashboardRoutes = { farmer: '/farmer', buyer: '/buyer' };
        navigate(dashboardRoutes[role] || '/');
      } else {
        toast.success('Account created! Please login.');
        navigate('/login');
      }
    } catch (error) {
      const msg = error.response?.data?.error || error.response?.data?.message || 'Signup failed. Please try again.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const getRoleEmoji = () => {
    return role === 'farmer' ? '👨‍🌾' : '👩‍💼';
  };

  const getRoleLabel = () => {
    return role === 'farmer' ? 'Farmer' : 'Buyer';
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <h1>{getRoleEmoji()} Sign Up</h1>
          <p>Join SmartFarm as a {getRoleLabel()}</p>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar">
          <div className="progress" style={{ width: `${(step / 3) * 100}%` }}></div>
        </div>

        <div className="step-indicator">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>1</div>
          <div className={`step ${step >= 2 ? 'active' : ''}`}>2</div>
          <div className={`step ${step >= 3 ? 'active' : ''}`}>3</div>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          {/* Step 1: Personal Information */}
          {step === 1 && (
            <div className="form-step">
              <h3>Personal Information</h3>

              <div className="form-group-full">
                <label htmlFor="name">Full Name *</label>
                <div className="input-wrapper">
                  <FiUser className="input-icon" />
                  <input
                    id="name"
                    type="text"
                    name="name"
                    placeholder="Enter your full name"
                    value={formData.name}
                    onChange={handleChange}
                  />
                </div>
                {errors.name && <span className="error-message">{errors.name}</span>}
              </div>

              <div className="form-group-full">
                <label htmlFor="email">Email Address *</label>
                <div className="input-wrapper">
                  <FiMail className="input-icon" />
                  <input
                    id="email"
                    type="email"
                    name="email"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>

              <div className="form-group-full">
                <label htmlFor="phone">Phone Number *</label>
                <div className="input-wrapper">
                  <FiPhone className="input-icon" />
                  <input
                    id="phone"
                    type="tel"
                    name="phone"
                    placeholder="10-digit mobile number"
                    value={formData.phone}
                    onChange={handleChange}
                    maxLength="10"
                  />
                </div>
                {errors.phone && <span className="error-message">{errors.phone}</span>}
              </div>

              <button type="button" className="btn-next" onClick={handleNext}>
                Next <FiArrowRight size={16} />
              </button>
            </div>
          )}

          {/* Step 2: Password & Location */}
          {step === 2 && (
            <div className="form-step">
              <h3>Security & Location</h3>

              <div className="form-group-full">
                <label htmlFor="password">Password *</label>
                <div className="input-wrapper">
                  <FiLock className="input-icon" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    placeholder="At least 8 characters"
                    value={formData.password}
                    onChange={handleChange}
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
                {errors.password && <span className="error-message">{errors.password}</span>}
              </div>

              <div className="form-group-full">
                <label htmlFor="confirmPassword">Confirm Password *</label>
                <div className="input-wrapper">
                  <FiLock className="input-icon" />
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    name="confirmPassword"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                  </button>
                </div>
                {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
              </div>

              <div className="form-group-full">
                <label htmlFor="location">City/Town *</label>
                <div className="input-wrapper">
                  <FiMapPin className="input-icon" />
                  <input
                    id="location"
                    type="text"
                    name="location"
                    placeholder="Enter your city"
                    value={formData.location}
                    onChange={handleChange}
                  />
                </div>
                {errors.location && <span className="error-message">{errors.location}</span>}
              </div>

              <div className="form-group-full">
                <label htmlFor="district">District/State *</label>
                <div className="input-wrapper">
                  <FiMapPin className="input-icon" />
                  <input
                    id="district"
                    type="text"
                    name="district"
                    placeholder="Enter your district"
                    value={formData.district}
                    onChange={handleChange}
                  />
                </div>
                {errors.district && <span className="error-message">{errors.district}</span>}
              </div>

              <div className="form-buttons">
                <button type="button" className="btn-back" onClick={handlePrev}>
                  Back
                </button>
                <button type="button" className="btn-next" onClick={handleNext}>
                  Next <FiArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Role-Specific & Agreement */}
          {step === 3 && (
            <div className="form-step">
              <h3>{getRoleLabel()} Details</h3>

              {role === 'farmer' && (
                <div className="form-group-full">
                  <label htmlFor="farmName">Farm Name *</label>
                  <div className="input-wrapper">
                    <FiUser className="input-icon" />
                    <input
                      id="farmName"
                      type="text"
                      name="farmName"
                      placeholder="Enter your farm name"
                      value={formData.farmName}
                      onChange={handleChange}
                    />
                  </div>
                  {errors.farmName && <span className="error-message">{errors.farmName}</span>}
                </div>
              )}

              {role === 'buyer' && (
                <div className="form-group-full">
                  <label htmlFor="companyName">Company/Organization Name *</label>
                  <div className="input-wrapper">
                    <FiUser className="input-icon" />
                    <input
                      id="companyName"
                      type="text"
                      name="companyName"
                      placeholder="Enter your company name"
                      value={formData.companyName}
                      onChange={handleChange}
                    />
                  </div>
                  {errors.companyName && <span className="error-message">{errors.companyName}</span>}
                </div>
              )}

              <div className="form-group-full checkbox">
                <label>
                  <input
                    type="checkbox"
                    name="agreeToTerms"
                    checked={formData.agreeToTerms}
                    onChange={handleChange}
                  />
                  <span>I agree to the <Link to="#terms">Terms & Conditions</Link> and <Link to="#privacy">Privacy Policy</Link> *</span>
                </label>
                {errors.agreeToTerms && <span className="error-message">{errors.agreeToTerms}</span>}
              </div>

              <div className="form-buttons">
                <button type="button" className="btn-back" onClick={handlePrev}>
                  Back
                </button>
                <button type="submit" className="btn-submit-final" disabled={loading}>
                  {loading ? 'Creating Account...' : 'Create Account'}
                </button>
              </div>
            </div>
          )}
        </form>

        <div className="login-link">
          Already have an account? <Link to="/login">Login here</Link>
        </div>
      </div>

      <div className="auth-image">
        <div className="illustration">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
          <div className="shape shape-3"></div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
