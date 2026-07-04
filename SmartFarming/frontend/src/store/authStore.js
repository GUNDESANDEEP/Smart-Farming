import { create } from 'zustand';
import axios from 'axios';
import { authAPI, tokenUtils, API_BASE_URL } from '../services/api';

// Decode a JWT token payload without verification
const decodeToken = (token) => {
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

// Check if a JWT token is expired (with 30-second buffer)
const isTokenExpired = (token) => {
  const payload = decodeToken(token);
  if (!payload || !payload.exp) return true;
  return payload.exp * 1000 < Date.now() + 30000;
};

const getInitialState = () => {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  const userStr = localStorage.getItem('user');

  let user = null;
  try {
    user = userStr ? JSON.parse(userStr) : null;
  } catch {
    user = null;
  }

  const isAuth = !!accessToken && !isTokenExpired(accessToken);
  return {
    user,
    token: isAuth ? accessToken : null,
    refreshToken: isAuth ? refreshToken : null,
    isAuthenticated: isAuth,
    role: user?.role || null,
    authLoading: !isAuth && !!refreshToken && !isTokenExpired(refreshToken),
    loading: false,
    error: null
  };
};

export const useAuthStore = create((set, get) => ({
  ...getInitialState(),

  setUser: (user) => {
    set({ user, role: user?.role || null });
    localStorage.setItem('user', JSON.stringify(user));
  },

  setError: (error) => set({ error }),
  
  clearError: () => set({ error: null }),

  register: async (email, password, firstName, lastName, phone, role) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.register({
        name: `${firstName} ${lastName}`.trim(),
        email,
        password,
        phone,
        role,
      });
      
      const d = response.data.data || response.data;
      const token = d.token || d.access_token;
      const user = {
        id: d._id || d.id,
        name: d.name || `${d.first_name || ''} ${d.last_name || ''}`.trim(),
        first_name: d.first_name || (d.name || '').split(' ')[0],
        last_name: d.last_name || (d.name || '').split(' ').slice(1).join(' '),
        email: d.email || email,
        phone: d.phone || phone,
        role: d.role || role,
        location: d.location || '',
      };

      tokenUtils.setTokens(token, d.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, role: user.role, isAuthenticated: true, token, refreshToken: d.refresh_token, loading: false });
      return { data: user };
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Registration failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  apiLogin: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.login({ email, password });
      
      const d = response.data.data || response.data;
      const token = d.token || d.access_token;
      const user = {
        id: d._id || d.id,
        name: d.name || `${d.first_name || ''} ${d.last_name || ''}`.trim(),
        first_name: d.first_name || (d.name || '').split(' ')[0],
        last_name: d.last_name || (d.name || '').split(' ').slice(1).join(' '),
        email: d.email || email,
        phone: d.phone || '',
        role: d.role || 'farmer',
        location: d.location || '',
      };

      tokenUtils.setTokens(token, d.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, role: user.role, isAuthenticated: true, token, refreshToken: d.refresh_token, loading: false });
      return { data: user };
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Login failed. Please check your credentials.';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  login: (userData, accessToken, refreshToken) => {
    tokenUtils.setTokens(accessToken, refreshToken);
    localStorage.setItem('user', JSON.stringify(userData));
    set({
      user: userData,
      token: accessToken,
      refreshToken: refreshToken || get().refreshToken,
      isAuthenticated: true,
      role: userData.role,
      authLoading: false,
    });
  },

  verifyEmail: async (otp) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.verifyEmail(otp);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Email verification failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  otpLogin: async (phone) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.otpLogin(phone);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'OTP request failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  verifyOTPLogin: async (phone, otp) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.verifyOTPLogin(phone, otp);
      const d = response.data.data || response.data;
      const token = d.token || d.access_token;
      const user = {
        id: d._id || d.id,
        name: d.name || `${d.first_name || ''} ${d.last_name || ''}`.trim(),
        email: d.email || '',
        phone: d.phone || phone,
        role: d.role || 'buyer',
        location: d.location || '',
      };

      tokenUtils.setTokens(token, d.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, role: user.role, isAuthenticated: true, token, refreshToken: d.refresh_token, loading: false });
      return { data: user };
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'OTP verification failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  firebaseLogin: async (idToken) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.firebaseLogin(idToken);
      const d = response.data.data || response.data;
      const token = d.token || d.access_token;
      const user = {
        id: d._id || d.id,
        name: d.name || '',
        email: d.email || '',
        role: d.role || 'buyer',
        location: d.location || '',
      };

      tokenUtils.setTokens(token, d.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, role: user.role, isAuthenticated: true, token, refreshToken: d.refresh_token, loading: false });
      return { data: user };
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Firebase login failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  forgotPassword: async (email) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.forgotPassword(email);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Password reset request failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  resetPassword: async (token, password) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.resetPassword(token, password);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Password reset failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  changePassword: async (oldPassword, newPassword) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.changePassword(oldPassword, newPassword);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Password change failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  updateProfile: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.updateProfile(data);
      const d = response.data.data || response.data;
      const u = d.user || d.profile || d;
      const updatedUser = {
        id: u.id || u._id || get().user?.id,
        name: u.name || `${u.first_name || ''} ${u.last_name || ''}`.trim() || get().user?.name,
        first_name: u.first_name || (u.name || '').split(' ')[0] || get().user?.first_name,
        last_name: u.last_name || (u.name || '').split(' ').slice(1).join(' ') || get().user?.last_name,
        email: u.email || get().user?.email || '',
        phone: u.phone || get().user?.phone || '',
        role: u.role || get().user?.role || 'buyer',
        location: u.location || get().user?.location || '',
      };
      set({ user: updatedUser, role: updatedUser.role, loading: false });
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Profile update failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  getProfile: async () => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.getProfile();
      const d = response.data.data || response.data;
      const u = d.user || d.profile || d;
      const user = {
        id: u.id || u._id,
        name: u.name || `${u.first_name || ''} ${u.last_name || ''}`.trim(),
        first_name: u.first_name || (u.name || '').split(' ')[0],
        last_name: u.last_name || (u.name || '').split(' ').slice(1).join(' '),
        email: u.email || '',
        phone: u.phone || '',
        role: u.role || get().role || 'buyer',
        location: u.location || '',
      };
      set({ user, role: user.role, loading: false });
      localStorage.setItem('user', JSON.stringify(user));
      return response.data;
    } catch (error) {
      set({ error: error.response?.data?.error || 'Failed to fetch profile', loading: false });
      throw error;
    }
  },

  logout: async () => {
    // Clear tokens and local state instantly so logout is immediate
    tokenUtils.clearTokens();
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      role: null,
      authLoading: false,
      loading: false,
      error: null
    });

    // Make backend logout request in background
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Background logout error:', error);
    }
  },

  // Actions from services/authStore.js
  setToken: (newAccessToken) => {
    localStorage.setItem('access_token', newAccessToken);
    set({ token: newAccessToken, isAuthenticated: true, authLoading: false });
  },

  updateUser: (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    set({ user: userData, role: userData.role });
  },

  initializeAuth: async () => {
    const { token, refreshToken } = get();

    if (token && !isTokenExpired(token)) {
      set({ isAuthenticated: true, authLoading: false });
      return;
    }

    if (refreshToken && !isTokenExpired(refreshToken)) {
      set({ authLoading: true });
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        }, { timeout: 60000 });
        const newToken = response.data.access_token || null;
        if (newToken) {
          localStorage.setItem('access_token', newToken);
          const user = get().user;
          set({
            token: newToken,
            isAuthenticated: true,
            authLoading: false,
            role: user?.role || null,
          });
          return;
        }
      } catch (err) {
        console.warn('[Auth] Token refresh failed during initialization:', err.message);
      }
    }

    tokenUtils.clearTokens();
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      role: null,
      authLoading: false,
    });
  }
}));
