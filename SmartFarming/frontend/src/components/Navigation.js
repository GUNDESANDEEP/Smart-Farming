import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut, FiArrowLeft } from 'react-icons/fi';
import useAuthStore from '../services/authStore';
import '../styles/navigation.css';

const Navigation = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const location = useLocation();

  // Show back button on all pages after login
  const hiddenPaths = ['/', '/login', '/register'];
  const showBack = !hiddenPaths.includes(location.pathname);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = {
    farmer: [
      { name: 'Dashboard', path: '/farmer' },
      { name: 'My Products', path: '/farmer/products' },
      { name: 'Orders', path: '/farmer/orders' },
      { name: 'Direct Sale', path: '/farmer/direct-sale' },
      { name: 'Earnings', path: '/farmer/earnings' },
      { name: 'Profile', path: '/farmer/profile' },
    ],
    buyer: [
      { name: 'Home', path: '/buyer' },
      { name: 'Shop', path: '/buyer/shop' },
      { name: 'Cart', path: '/buyer/cart' },
      { name: 'Orders', path: '/buyer/orders' },
      { name: 'Receipts', path: '/buyer/purchase-history' },
      { name: 'Profile', path: '/buyer/profile' },
    ],
    admin: [
      { name: 'Dashboard', path: '/admin' },
      { name: 'SaaS', path: '/admin/saas' },
      { name: 'Users', path: '/admin/users' },
      { name: 'Products', path: '/admin/products' },
      { name: 'Orders', path: '/admin/orders' },
      { name: 'Activity', path: '/admin/activity' },
      { name: 'Receipts', path: '/admin/receipts' },
      { name: 'Revenue', path: '/admin/revenue' },
    ],
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {showBack && (
            <button className="back-btn" onClick={() => navigate(-1)}>
              <FiArrowLeft size={20} />
            </button>
          )}
          <Link to="/" className="navbar-logo">
            🌾 SmartFarm
          </Link>
        </div>

        <button
          className="hamburger"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>

        <div className={`nav-menu ${isOpen ? 'active' : ''}`}>
          <div className="nav-links">
            {navLinks[user?.role]?.map((link) => (
              <Link key={link.path} to={link.path} className="nav-link">
                {link.name}
              </Link>
            ))}
          </div>

          <div className="user-menu">
            <span className="user-name">{user?.name}</span>
            <button className="logout-btn" onClick={handleLogout}>
              <FiLogOut size={18} />
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
