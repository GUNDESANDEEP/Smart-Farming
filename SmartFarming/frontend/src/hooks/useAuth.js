import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../services/authStore';

export const useRequireAuth = (allowedRoles = []) => {
  const navigate = useNavigate();
  const { isAuthenticated, role } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
      navigate('/unauthorized');
    }
  }, [isAuthenticated, role, navigate, allowedRoles]);

  return { isAuthenticated, role };
};

export const useUser = () => {
  const { user } = useAuthStore();
  return user;
};

export const useLogout = () => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  return () => {
    logout();
    navigate('/login');
  };
};
