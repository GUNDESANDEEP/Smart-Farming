import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../services/authStore';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const navigate = useNavigate();
  const { isAuthenticated, role } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else if (allowedRoles && !allowedRoles.includes(role)) {
      navigate('/');
    }
  }, [isAuthenticated, role, navigate, allowedRoles]);

  if (!isAuthenticated) return null;
  if (allowedRoles && !allowedRoles.includes(role)) return null;

  return children;
};

export default ProtectedRoute;
