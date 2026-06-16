import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';

export default function Login() {
  const navigate = useNavigate();
  const { login, loading, error } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [loginMethod, setLoginMethod] = useState('email');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      const response = await login(formData.email, formData.password);
      const userRole = response.data?.role;

      toast.success('Login successful!');
      
      if (userRole === 'farmer') {
        navigate('/farmer/dashboard');
      } else if (userRole === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/buyer/marketplace');
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-12 px-4">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-green-600 mb-2">SmartFarmer</h1>
          <p className="text-gray-600">Welcome back</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Login Method Tabs */}
        <div className="flex gap-2 mb-6 border-b">
          <button
            onClick={() => setLoginMethod('email')}
            className={`pb-2 px-3 font-semibold text-sm transition-colors ${
              loginMethod === 'email'
                ? 'text-green-600 border-b-2 border-green-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Email & Password
          </button>
          <button
            onClick={() => setLoginMethod('otp')}
            className={`pb-2 px-3 font-semibold text-sm transition-colors ${
              loginMethod === 'otp'
                ? 'text-green-600 border-b-2 border-green-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            OTP
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {loginMethod === 'email' ? (
            <>
              {/* Email */}
              <div className="relative">
                <FiMail className="absolute left-3 top-3 text-gray-400" />
                <input
                  type="email"
                  name="email"
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              {/* Password */}
              <div className="relative">
                <FiLock className="absolute left-3 top-3 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>

              {/* Forgot Password */}
              <div className="text-right">
                <Link to="/forgot-password" className="text-green-600 text-sm hover:underline">
                  Forgot password?
                </Link>
              </div>
            </>
          ) : (
            <p className="text-gray-600 text-sm text-center py-4">
              Click below to use OTP login
            </p>
          )}

          {/* Submit Button */}
          <button
            type={loginMethod === 'email' ? 'submit' : 'button'}
            onClick={
              loginMethod === 'otp'
                ? () => navigate('/otp-login')
                : undefined
            }
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Logging in...' : loginMethod === 'email' ? 'Login' : 'Continue with OTP'}
          </button>
        </form>

        {/* Register Link */}
        <p className="text-center text-gray-600 text-sm mt-4">
          Don't have an account?{' '}
          <Link to="/register" className="text-green-600 hover:underline font-semibold">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
