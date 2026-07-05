import { create } from 'zustand';
import { authAPI, tokenUtils } from './api';

export const useAuthStore = create((set) => ({
  user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null,
  loading: false,
  error: null,
  isAuthenticated: tokenUtils.isAuthenticated(),

  setUser: (user) => {
    set({ user });
    localStorage.setItem('user', JSON.stringify(user));
  },

  setError: (error) => set({ error }),

  register: async (email, password, firstName, lastName, phone, role) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        phone,
        role,
      });
      
      const { access_token, refresh_token, user } = response.data.data;
      tokenUtils.setTokens(access_token, refresh_token);
      set({ user, isAuthenticated: true, loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Registration failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.login(email, password);
      
      const { access_token, refresh_token, user } = response.data.data;
      tokenUtils.setTokens(access_token, refresh_token);
      set({ user, isAuthenticated: true, loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Login failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  verifyEmail: async (otp) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.verifyEmail(otp);
      set({ loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Email verification failed';
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
      const errorMsg = error.response?.data?.error || 'OTP request failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  verifyOTPLogin: async (phone, otp) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.verifyOTPLogin(phone, otp);
      
      const { access_token, refresh_token, user } = response.data.data;
      tokenUtils.setTokens(access_token, refresh_token);
      set({ user, isAuthenticated: true, loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'OTP verification failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  firebaseLogin: async (idToken) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.firebaseLogin(idToken);
      
      const { access_token, refresh_token, user } = response.data.data;
      tokenUtils.setTokens(access_token, refresh_token);
      set({ user, isAuthenticated: true, loading: false });
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Firebase login failed';
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
      const errorMsg = error.response?.data?.error || 'Password reset request failed';
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
      const errorMsg = error.response?.data?.error || 'Password reset failed';
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
      const errorMsg = error.response?.data?.error || 'Password change failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  updateProfile: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.updateProfile(data);
      const updatedUser = response.data.data;
      set({ user: updatedUser, loading: false });
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Profile update failed';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  getProfile: async () => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.getProfile();
      const user = response.data.data;
      set({ user, loading: false });
      localStorage.setItem('user', JSON.stringify(user));
      return response.data;
    } catch (error) {
      set({ error: error.response?.data?.error || 'Failed to fetch profile', loading: false });
      throw error;
    }
  },

  logout: async () => {
    set({ loading: true });
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      tokenUtils.clearTokens();
      set({ user: null, isAuthenticated: false, loading: false, error: null });
    }
  },

  clearError: () => set({ error: null }),
}));
