import React, { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Eagerly loaded (small, always needed)
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import PricingPlans from './pages/PricingPlans';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import GlobalCursor from './components/GlobalCursor';
import useAuthStore from './services/authStore';
import './styles/index.css';

// Lazy loaded (large dashboard bundles — only loaded when needed)
const FarmerDashboard = lazy(() => import('./pages/FarmerDashboard'));
const BuyerDashboard = lazy(() => import('./pages/BuyerDashboard'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));

// Loading fallback for lazy-loaded pages
const PageLoader = () => (
  <div style={{
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', minHeight: '100vh',
    background: 'linear-gradient(135deg, #0a2e1a 0%, #14532d 50%, #1a4731 100%)',
  }}>
    <div style={{
      width: '48px', height: '48px', border: '3px solid rgba(34, 197, 94, 0.2)',
      borderTop: '3px solid #22c55e', borderRadius: '50%',
      animation: 'spin 0.8s linear infinite',
    }} />
    <p style={{ color: '#86efac', marginTop: '16px', fontSize: '0.9rem', fontFamily: 'Poppins, sans-serif' }}>
      Loading dashboard...
    </p>
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

function App() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <Router basename={process.env.PUBLIC_URL || ''}>
      <GlobalCursor />
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        toastOptions={{
          duration: 4000,
          style: {
            background: '#14532d',
            color: '#fff',
            borderRadius: '12px',
            border: '1px solid rgba(74, 222, 128, 0.2)',
          },
        }}
      />
      
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup/:role" element={<SignupPage />} />
          
          <Route
            path="/farmer/*"
            element={
              <ProtectedRoute allowedRoles={['farmer']}>
                <Navigation />
                <FarmerDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/buyer/*"
            element={
              <ProtectedRoute allowedRoles={['buyer']}>
                <Navigation />
                <BuyerDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Navigation />
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route path="/pricing" element={<PricingPlans />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
