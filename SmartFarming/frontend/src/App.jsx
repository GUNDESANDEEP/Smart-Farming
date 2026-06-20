import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import ProtectedRoute from './components/ProtectedRoute';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import OTPLogin from './pages/auth/OTPLogin';
import EmailVerification from './pages/auth/EmailVerification';
import ForgotPassword from './pages/auth/ForgotPassword';

// Farmer Pages
import FarmerDashboard from './pages/farmer/Dashboard';
import FarmerEarnings from './pages/farmer/Earnings';
import FarmerProducts from './pages/farmer/Products';
import FarmerOrders from './pages/farmer/Orders';

// Buyer Pages
import BuyerMarketplace from './pages/buyer/Marketplace';

// Pricing Page
import PricingPlans from './pages/PricingPlans';

// Admin Pages
// (to be implemented)

function App() {
  useEffect(() => {
    // Check and initialize auth state from localStorage if needed
    const token = localStorage.getItem('access_token');
    if (token) {
      // Token exists, user is authenticated
    }
  }, []);

  return (
    <Router basename={process.env.PUBLIC_URL || ''}>
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          duration: 4000,
        }}
      />
      
      <Routes>
        {/* Auth Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/otp-login" element={<OTPLogin />} />
        <Route path="/email-verification" element={<EmailVerification />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/pricing" element={<PricingPlans />} />

        {/* Farmer Routes */}
        <Route
          path="/farmer/dashboard"
          element={
            <ProtectedRoute requiredRole="farmer">
              <FarmerDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/farmer/earnings"
          element={
            <ProtectedRoute requiredRole="farmer">
              <FarmerEarnings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/farmer/products"
          element={
            <ProtectedRoute requiredRole="farmer">
              <FarmerProducts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/farmer/orders"
          element={
            <ProtectedRoute requiredRole="farmer">
              <FarmerOrders />
            </ProtectedRoute>
          }
        />

        {/* Buyer Routes */}
        <Route
          path="/buyer/marketplace"
          element={
            <ProtectedRoute requiredRole="buyer">
              <BuyerMarketplace />
            </ProtectedRoute>
          }
        />

        {/* Redirect root to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* 404 */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
