import React from 'react';
import { Navigate } from 'react-router-dom';
import { tokenUtils } from './services/api';

export default function ProtectedRoute({ children, requiredRole }) {
  const isAuthenticated = tokenUtils.isAuthenticated();
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    // Redirect to appropriate dashboard based on role
    if (user.role === 'farmer') {
      return <Navigate to="/farmer/dashboard" replace />;
    } else if (user.role === 'admin') {
      return <Navigate to="/admin/dashboard" replace />;
    } else {
      return <Navigate to="/buyer/marketplace" replace />;
    }
  }

  return children;
}
