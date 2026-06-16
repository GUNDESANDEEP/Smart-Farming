import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { farmerAPI } from '../../services/api';
import toast from 'react-hot-toast';
import { FiPlus, FiShoppingCart, FiTrendingUp, FiUsers, FiLogOut } from 'react-icons/fi';

export default function FarmerDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || user.role !== 'farmer') {
      navigate('/login');
      return;
    }
    fetchDashboard();
  }, [user, navigate]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const [dashboardRes, productsRes, ordersRes] = await Promise.all([
        farmerAPI.getDashboard(),
        farmerAPI.getProducts(1, 5),
        farmerAPI.getOrders(1, 5),
      ]);

      setDashboard(dashboardRes.data.data);
      setProducts(productsRes.data.data || []);
      setOrders(ordersRes.data.data || []);
    } catch (error) {
      toast.error('Failed to load dashboard');
      console.error(error);
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
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-green-600">SmartFarmer</h1>
            <p className="text-gray-600 text-sm">Farmer Dashboard</p>
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
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Total Products */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Products</p>
                <p className="text-3xl font-bold text-gray-800">
                  {dashboard?.total_products || 0}
                </p>
              </div>
              <FiShoppingCart className="text-green-600 text-4xl opacity-20" />
            </div>
          </div>

          {/* Total Orders */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Orders</p>
                <p className="text-3xl font-bold text-gray-800">
                  {dashboard?.total_orders || 0}
                </p>
              </div>
              <FiUsers className="text-blue-600 text-4xl opacity-20" />
            </div>
          </div>

          {/* Total Earnings */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Earnings</p>
                <p className="text-3xl font-bold text-green-600">
                  ₹{dashboard?.total_earnings?.toLocaleString('en-IN') || 0}
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
                  {dashboard?.average_rating ? dashboard.average_rating.toFixed(1) : 'N/A'}
                </p>
              </div>
              <span className="text-3xl">⭐</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => navigate('/farmer/products')}
            className="flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-semibold"
          >
            <FiPlus /> Add New Product
          </button>
          <button
            onClick={() => navigate('/farmer/orders')}
            className="flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
          >
            <FiShoppingCart /> View Orders
          </button>
          <button
            onClick={() => navigate('/farmer/earnings')}
            className="flex items-center justify-center gap-2 bg-yellow-600 text-white px-6 py-3 rounded-lg hover:bg-yellow-700 font-semibold"
          >
            <FiTrendingUp /> View Earnings
          </button>
        </div>

        {/* Recent Products */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Products Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-bold text-gray-800">Recent Products</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Price</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Stock</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {products.length > 0 ? (
                    products.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-800">{product.name}</td>
                        <td className="px-6 py-4 text-sm text-gray-800">₹{product.price}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            product.stock > 0
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {product.stock} units
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" className="px-6 py-4 text-center text-gray-600">
                        No products yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Orders */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-bold text-gray-800">Recent Orders</h2>
            </div>
            <div className="divide-y">
              {orders.length > 0 ? (
                orders.map((order) => (
                  <div key={order.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-gray-800">Order #{order.id}</p>
                        <p className="text-sm text-gray-600">₹{order.total_amount}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        order.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : order.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="px-6 py-4 text-center text-gray-600">
                  No orders yet
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
