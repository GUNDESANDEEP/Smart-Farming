import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import FarmerDashboard from './pages/FarmerDashboard';
import BuyerDashboard from './pages/BuyerDashboard';
import AdminDashboard from './pages/AdminDashboard';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import GlobalCursor from './components/GlobalCursor';
import './styles/index.css';

function App() {
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
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
