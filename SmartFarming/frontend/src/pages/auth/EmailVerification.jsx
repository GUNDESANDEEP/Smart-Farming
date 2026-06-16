import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';
import { FiMail } from 'react-icons/fi';

export default function EmailVerification() {
  const navigate = useNavigate();
  const { user, verifyEmail, loading } = useAuthStore();
  const [otp, setOtp] = useState('');
  const [timer, setTimer] = useState(300); // 5 minutes
  const [resendDisabled, setResendDisabled] = useState(false);

  useEffect(() => {
    // Redirect if user is already verified or not registered
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.is_email_verified) {
      navigate(user.role === 'farmer' ? '/farmer/dashboard' : '/buyer/marketplace');
    }
  }, [user, navigate]);

  // Countdown timer
  useEffect(() => {
    if (timer > 0) {
      const interval = setTimeout(() => setTimer(timer - 1), 1000);
      return () => clearTimeout(interval);
    }
  }, [timer]);

  const handleVerify = async (e) => {
    e.preventDefault();

    if (!otp) {
      toast.error('Please enter the OTP');
      return;
    }

    if (otp.length !== 6) {
      toast.error('OTP must be 6 digits');
      return;
    }

    try {
      await verifyEmail(otp);
      toast.success('Email verified successfully!');
      navigate(user.role === 'farmer' ? '/farmer/dashboard' : '/buyer/marketplace');
    } catch (error) {
      toast.error(error.response?.data?.error || 'OTP verification failed');
    }
  };

  const handleResendOTP = async () => {
    setResendDisabled(true);
    try {
      // Call resend OTP endpoint (you may need to add this to the API)
      toast.success('OTP resent to your email');
      setTimer(300);
    } catch (error) {
      toast.error('Failed to resend OTP');
    } finally {
      setResendDisabled(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-12 px-4 flex items-center">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <FiMail className="text-green-600 text-3xl" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Verify Your Email</h1>
          <p className="text-gray-600">
            We sent a verification code to {user?.email}
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-4">
          {/* OTP Display */}
          <div className="bg-green-50 border border-green-200 rounded p-3 text-center mb-4">
            <p className="text-gray-700 font-mono text-lg tracking-widest">
              {otp || '• • • • • •'}
            </p>
          </div>

          {/* OTP Input */}
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
            maxLength="6"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-center text-2xl tracking-widest font-semibold"
          />

          {/* Timer */}
          <div className="text-center text-sm text-gray-600">
            OTP expires in: <span className="font-semibold text-green-600">{formatTime(timer)}</span>
          </div>

          {/* Verify Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>

          {/* Resend Button */}
          <button
            type="button"
            onClick={handleResendOTP}
            disabled={resendDisabled || timer > 0}
            className="w-full border border-gray-300 text-gray-700 py-2 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {resendDisabled ? 'Sending...' : 'Resend OTP'}
          </button>
        </form>

        {/* Additional Info */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-800">
            <strong>Didn't receive the code?</strong> Check your spam folder or wait a moment before requesting a new code.
          </p>
        </div>
      </div>
    </div>
  );
}
