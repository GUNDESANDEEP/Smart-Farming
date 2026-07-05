import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../services/authStore';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const navigate = useNavigate();
  const { isAuthenticated, role, authLoading } = useAuthStore();

  useEffect(() => {
    // Don't redirect while auth is still initializing (token refresh in progress)
    if (authLoading) return;

    if (!isAuthenticated) {
      navigate('/login', { replace: true });
    } else if (allowedRoles && !allowedRoles.includes(role)) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, role, navigate, allowedRoles, authLoading]);

  // Show loading spinner while auth is being recovered
  if (authLoading) {
    return (
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
          Restoring your session...
        </p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated) return null;
  if (allowedRoles && !allowedRoles.includes(role)) return null;

  return children;
};

export default ProtectedRoute;
