import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiPhone, FiArrowLeft } from 'react-icons/fi';

export default function OTPLogin() {
  const navigate = useNavigate();
  const { otpLogin, verifyOTPLogin, loading } = useAuthStore();
  const [step, setStep] = useState('phone'); // phone or otp
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRequestOTP = async (e) => {
    e.preventDefault();

    if (!phone) {
      toast.error('Please enter your phone number');
      return;
    }

    setIsSubmitting(true);
    try {
      await otpLogin(phone);
      toast.success('OTP sent to your phone');
      setStep('otp');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();

    if (!otp) {
      toast.error('Please enter the OTP');
      return;
    }

    if (otp.length !== 6) {
      toast.error('OTP must be 6 digits');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await verifyOTPLogin(phone, otp);
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
      toast.error(error.response?.data?.error || 'OTP verification failed');
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
          <h1 className="text-3xl font-bold text-green-600 mb-2">OTP Login</h1>
          <p className="text-gray-600">Quick and secure login with OTP</p>
        </div>

        {step === 'phone' ? (
          <form onSubmit={handleRequestOTP} className="space-y-4">
            <p className="text-gray-600 text-sm mb-4">
              Enter your phone number to receive an OTP
            </p>

            <div className="relative">
              <FiPhone className="absolute left-3 top-3 text-gray-400" />
              <input
                type="tel"
                placeholder="Phone number (10 digits)"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                maxLength="10"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Sending OTP...' : 'Send OTP'}
            </button>

            <p className="text-center text-gray-600 text-sm">
              Don't have an account?{' '}
              <Link to="/register" className="text-green-600 hover:underline font-semibold">
                Register here
              </Link>
            </p>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <p className="text-gray-600 text-sm mb-4">
              Enter the 6-digit OTP sent to {phone}
            </p>

            <div className="bg-green-50 border border-green-200 rounded p-3 text-center">
              <p className="text-gray-700 font-mono text-lg tracking-widest">
                {otp || '• • • • • •'}
              </p>
            </div>

            <input
              type="text"
              placeholder="Enter OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              maxLength="6"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-center text-2xl tracking-widest font-semibold"
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              onClick={() => setStep('phone')}
              className="w-full border border-gray-300 text-gray-700 py-2 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
            >
              Change Phone Number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
