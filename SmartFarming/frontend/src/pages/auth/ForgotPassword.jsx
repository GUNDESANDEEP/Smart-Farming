import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiMail, FiLock, FiEye, FiEyeOff, FiArrowLeft } from 'react-icons/fi';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const { forgotPassword, resetPassword, loading } = useAuthStore();
  const [step, setStep] = useState(token ? 'reset' : 'email'); // email or reset
  const [email, setEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwords, setPasswords] = useState({
    password: '',
    confirmPassword: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRequestReset = async (e) => {
    e.preventDefault();

    if (!email) {
      toast.error('Please enter your email');
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword(email);
      toast.success('Password reset link sent to your email');
      setStep('reset');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send reset link');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();

    if (!passwords.password || !passwords.confirmPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    if (passwords.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (passwords.password !== passwords.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword(token, passwords.password);
      toast.success('Password reset successful! Please login with your new password.');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Password reset failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-12 px-4">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
        <button
          onClick={() => navigate('/login')}
          className="flex items-center text-green-600 hover:text-green-700 mb-6"
        >
          <FiArrowLeft className="mr-2" /> Back to Login
        </button>

        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Reset Password</h1>
          <p className="text-gray-600">
            {step === 'email'
              ? 'Enter your email to receive a reset link'
              : 'Create a new password'}
          </p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleRequestReset} className="space-y-4">
            <div className="relative">
              <FiMail className="absolute left-3 top-3 text-gray-400" />
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || loading}
              className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting || loading ? 'Sending...' : 'Send Reset Link'}
            </button>

            <p className="text-center text-gray-600 text-sm">
              Remember your password?{' '}
              <Link to="/login" className="text-green-600 hover:underline font-semibold">
                Login here
              </Link>
            </p>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className="space-y-4">
            {/* New Password */}
            <div className="relative">
              <FiLock className="absolute left-3 top-3 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="New password"
                value={passwords.password}
                onChange={(e) =>
                  setPasswords({ ...passwords, password: e.target.value })
                }
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

            {/* Confirm Password */}
            <div className="relative">
              <FiLock className="absolute left-3 top-3 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Confirm password"
                value={passwords.confirmPassword}
                onChange={(e) =>
                  setPasswords({ ...passwords, confirmPassword: e.target.value })
                }
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            {/* Password Requirements */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
              <p className="font-semibold mb-2">Password must:</p>
              <ul className="space-y-1 text-xs">
                <li>✓ Be at least 8 characters long</li>
                <li>✓ Contain an uppercase letter</li>
                <li>✓ Contain a lowercase letter</li>
                <li>✓ Contain a number</li>
                <li>✓ Contain a special character</li>
              </ul>
            </div>

            {/* Reset Button */}
            <button
              type="submit"
              disabled={isSubmitting || loading}
              className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting || loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
