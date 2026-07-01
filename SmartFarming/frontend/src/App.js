import React, { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Eagerly loaded (small, always needed on first visit)
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import useAuthStore from './services/authStore';
import { warmupServer } from './services/api';
import GlobalCursor from './components/GlobalCursor';
import './styles/index.css';

// ============================================================================
// Lazy loading with auto-retry for all dashboard bundles
// This keeps the initial bundle small (~100KB) while loading large dashboards
// on demand. Retries chunk loading up to 3 times with increasing delays.
// ============================================================================
function lazyWithRetry(importFn, retries = 3) {
  return lazy(() => {
    const attempt = (retriesLeft) =>
      importFn().catch((err) => {
        if (retriesLeft <= 0) throw err;
        return new Promise((resolve) =>
          setTimeout(() => resolve(attempt(retriesLeft - 1)), 1000)
        );
      });
    return attempt(retries);
  });
}

// Farmer Pages — lazy loaded (~200KB saved)
const FarmerDashboard = lazyWithRetry(() => import('./pages/farmer/Dashboard'));
const FarmerProducts = lazyWithRetry(() => import('./pages/farmer/Products'));
const FarmerOrders = lazyWithRetry(() => import('./pages/farmer/Orders'));
const FarmerEarnings = lazyWithRetry(() => import('./pages/farmer/Earnings'));
const FarmerMessages = lazyWithRetry(() => import('./pages/farmer/Messages'));
const FarmerAnalytics = lazyWithRetry(() => import('./pages/farmer/Analytics'));
const FarmerMarketing = lazyWithRetry(() => import('./pages/farmer/Marketing'));
const FarmerAITools = lazyWithRetry(() => import('./pages/farmer/AITools'));
const FarmerFutureAI = lazyWithRetry(() => import('./pages/farmer/FutureAI'));
const FarmerDirectPayment = lazyWithRetry(() => import('./pages/farmer/DirectPayment'));
const IncomingOrders = lazyWithRetry(() => import('./pages/farmer/IncomingOrders'));
const FarmerWallet = lazyWithRetry(() => import('./pages/farmer/Wallet'));
const AgriBot = lazyWithRetry(() => import('./pages/AgriBot'));

// Buyer Pages — lazy loaded (~150KB saved)
const BuyerDashboard = lazyWithRetry(() => import('./pages/buyer/BuyerDashboard'));
const BuyerMarketplace = lazyWithRetry(() => import('./pages/buyer/Marketplace'));
const BuyerCart = lazyWithRetry(() => import('./pages/buyer/Cart'));
const BuyerCheckout = lazyWithRetry(() => import('./pages/buyer/Checkout'));
const OrderSuccess = lazyWithRetry(() => import('./pages/buyer/OrderSuccess'));
const MyOrders = lazyWithRetry(() => import('./pages/buyer/MyOrders'));
const OrderTracking = lazyWithRetry(() => import('./pages/buyer/OrderTracking'));
const BuyerProfile = lazyWithRetry(() => import('./pages/buyer/BuyerProfile'));
const BuyerSettings = lazyWithRetry(() => import('./pages/buyer/BuyerSettings'));
const BuyerChat = lazyWithRetry(() => import('./pages/buyer/BuyerChat'));
const BuyerAlerts = lazyWithRetry(() => import('./pages/buyer/BuyerAlerts'));
const BuyerEarlyAccess = lazyWithRetry(() => import('./pages/buyer/BuyerEarlyAccess'));
const BuyerRecommendations = lazyWithRetry(() => import('./pages/buyer/BuyerRecommendations'));
const BuyerDeals = lazyWithRetry(() => import('./pages/buyer/BuyerDeals'));
const BuyerVIP = lazyWithRetry(() => import('./pages/buyer/BuyerVIP'));

// Admin & Other — lazy loaded
const AdminDashboard = lazyWithRetry(() => import('./pages/AdminDashboard'));
const PricingPlans = lazyWithRetry(() => import('./pages/PricingPlans'));
const Navigation = lazyWithRetry(() => import('./components/Navigation'));

// Loading fallback — minimal spinner, shows only on first load of a chunk
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
      Loading...
    </p>
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

// Error boundary for chunk load failures — shows reload button instead of crash
class ChunkErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    console.error('[ChunkError]', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '100vh',
          background: 'linear-gradient(135deg, #0a2e1a 0%, #14532d 50%, #1a4731 100%)',
          color: '#fff', fontFamily: 'Poppins, sans-serif',
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <h2 style={{ margin: '0 0 8px', color: '#86efac' }}>Page failed to load</h2>
          <p style={{ color: '#a7f3d0', marginBottom: '20px', fontSize: '14px' }}>
            This can happen on slow connections. Click below to retry.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '12px 32px', background: '#22c55e', color: '#fff',
              border: 'none', borderRadius: '8px', cursor: 'pointer',
              fontSize: '15px', fontWeight: '600',
            }}
          >
            🔄 Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
    warmupServer();
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
      
      <ChunkErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup/:role" element={<SignupPage />} />
            
            {/* Farmer Routes */}
            <Route path="/farmer" element={<Navigate to="/farmer/dashboard" replace />} />
            <Route path="/farmer/dashboard" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerDashboard /></ProtectedRoute>} />
            <Route path="/farmer/products" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerProducts /></ProtectedRoute>} />
            <Route path="/farmer/orders" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerOrders /></ProtectedRoute>} />
            <Route path="/farmer/incoming-orders" element={<ProtectedRoute allowedRoles={['farmer']}><IncomingOrders /></ProtectedRoute>} />
            <Route path="/farmer/wallet" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerWallet /></ProtectedRoute>} />
            <Route path="/farmer/earnings" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerEarnings /></ProtectedRoute>} />
            <Route path="/farmer/messages" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerMessages /></ProtectedRoute>} />
            <Route path="/farmer/analytics" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerAnalytics /></ProtectedRoute>} />
            <Route path="/farmer/marketing" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerMarketing /></ProtectedRoute>} />
            <Route path="/farmer/ai-tools" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerAITools /></ProtectedRoute>} />
            <Route path="/farmer/future-ai" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerFutureAI /></ProtectedRoute>} />
            <Route path="/farmer/direct-payment" element={<ProtectedRoute allowedRoles={['farmer']}><FarmerDirectPayment /></ProtectedRoute>} />
            <Route path="/farmer/agribot" element={<ProtectedRoute allowedRoles={['farmer','buyer']}><AgriBot /></ProtectedRoute>} />
            
            {/* Buyer Routes */}
            <Route path="/buyer" element={<Navigate to="/buyer/dashboard" replace />} />
            <Route path="/buyer/dashboard" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerDashboard /></ProtectedRoute>} />
            <Route path="/buyer/marketplace" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerMarketplace /></ProtectedRoute>} />
            <Route path="/buyer/cart" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerCart /></ProtectedRoute>} />
            <Route path="/buyer/checkout" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerCheckout /></ProtectedRoute>} />
            <Route path="/buyer/order-success" element={<ProtectedRoute allowedRoles={['buyer']}><OrderSuccess /></ProtectedRoute>} />
            <Route path="/buyer/orders" element={<ProtectedRoute allowedRoles={['buyer']}><MyOrders /></ProtectedRoute>} />
            <Route path="/buyer/orders/:id" element={<ProtectedRoute allowedRoles={['buyer']}><OrderTracking /></ProtectedRoute>} />
            <Route path="/buyer/profile" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerProfile /></ProtectedRoute>} />
            <Route path="/buyer/settings" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerSettings /></ProtectedRoute>} />
            <Route path="/buyer/chat" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerChat /></ProtectedRoute>} />
            <Route path="/buyer/alerts" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerAlerts /></ProtectedRoute>} />
            <Route path="/buyer/early-access" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerEarlyAccess /></ProtectedRoute>} />
            <Route path="/buyer/recommendations" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerRecommendations /></ProtectedRoute>} />
            <Route path="/buyer/deals" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerDeals /></ProtectedRoute>} />
            <Route path="/buyer/vip" element={<ProtectedRoute allowedRoles={['buyer']}><BuyerVIP /></ProtectedRoute>} />
            
            {/* Admin Routes */}
            <Route
              path="/admin/*"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <Suspense fallback={<PageLoader />}>
                    <Navigation />
                  </Suspense>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            
            <Route path="/pricing" element={<PricingPlans />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ChunkErrorBoundary>
    </Router>
  );
}

export default App;
