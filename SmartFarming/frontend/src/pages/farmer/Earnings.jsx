import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { farmerAPI } from '../../services/api';
import toast from 'react-hot-toast';
import { FiArrowLeft, FiTrendingUp, FiLogOut } from 'react-icons/fi';

export default function FarmerEarnings() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || user.role !== 'farmer') {
      navigate('/login');
      return;
    }
    fetchEarnings();
  }, [user, navigate]);

  const fetchEarnings = async () => {
    try {
      setLoading(true);
      const response = await farmerAPI.getEarnings();
      setEarnings(response.data);
    } catch (error) {
      console.error('Earnings error:', error);
      toast.error('Failed to load earnings');
      setEarnings({ success: true, total: 0, thisMonth: 0, pending: 0, rating: 0 });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading earnings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/farmer/dashboard')}
              className="flex items-center gap-2 text-green-600 hover:text-green-700 font-semibold"
            >
              <FiArrowLeft /> Back to Dashboard
            </button>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-green-600">SmartFarmer</h1>
            <p className="text-gray-600 text-sm">Earnings Report</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-semibold text-gray-800">{user?.first_name} {user?.last_name}</p>
              <p className="text-xs text-gray-600">Farmer Account</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              <FiLogOut /> Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Earnings */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Earnings</p>
                <p className="text-3xl font-bold text-green-600">
                  ₹{earnings?.total?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <FiTrendingUp className="text-green-600 text-4xl opacity-20" />
            </div>
          </div>

          {/* This Month Earnings */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">This Month</p>
                <p className="text-3xl font-bold text-blue-600">
                  ₹{earnings?.thisMonth?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <FiTrendingUp className="text-blue-600 text-4xl opacity-20" />
            </div>
          </div>

          {/* Pending Earnings */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Pending</p>
                <p className="text-3xl font-bold text-yellow-600">
                  ₹{earnings?.pending?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <FiTrendingUp className="text-yellow-600 text-4xl opacity-20" />
            </div>
          </div>

          {/* Rating */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Average Rating</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {earnings?.rating ? parseFloat(earnings.rating).toFixed(1) : 'N/A'}
                </p>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </div>
        </div>

        {/* Earnings Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">Earnings Summary</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-4 border-b">
              <span className="text-gray-600">Total Earnings (All Time)</span>
              <span className="text-2xl font-bold text-green-600">
                ₹{earnings?.total?.toLocaleString('en-IN') || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-4 border-b">
              <span className="text-gray-600">Current Month Earnings</span>
              <span className="text-2xl font-bold text-blue-600">
                ₹{earnings?.thisMonth?.toLocaleString('en-IN') || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-4 border-b">
              <span className="text-gray-600">Pending (Undelivered Orders)</span>
              <span className="text-2xl font-bold text-yellow-600">
                ₹{earnings?.pending?.toLocaleString('en-IN') || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Customer Rating</span>
              <span className="text-xl">
                {'⭐'.repeat(Math.floor(earnings?.rating || 0))} 
                <span className="ml-2 text-gray-800 font-semibold">
                  {earnings?.rating ? parseFloat(earnings.rating).toFixed(1) : 'N/A'}/5
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-8 bg-blue-50 border-l-4 border-blue-600 p-6 rounded">
          <h3 className="text-lg font-bold text-blue-800 mb-2">💡 Tips to Increase Earnings</h3>
          <ul className="text-blue-700 space-y-2">
            <li>✓ Add more products to your catalog</li>
            <li>✓ Maintain high quality and provide timely delivery</li>
            <li>✓ Offer competitive prices</li>
            <li>✓ Respond quickly to buyer inquiries</li>
            <li>✓ Request feedback to improve ratings</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
