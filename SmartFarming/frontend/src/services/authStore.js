import { create } from 'zustand';
import axios from 'axios';
import { API_BASE_URL } from './api';

// ============================================================================
// JWT HELPERS
// ============================================================================

/** Decode a JWT token payload without verification */
const decodeToken = (token) => {
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

/** Check if a JWT token is expired (with 30-second buffer) */
const isTokenExpired = (token) => {
  const payload = decodeToken(token);
  if (!payload || !payload.exp) return true;
  return payload.exp * 1000 < Date.now() + 30000;
};

/** Try to refresh the access token using the refresh token */
const refreshAccessToken = async (refreshToken) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    }, { timeout: 60000 });
    return response.data.access_token || null;
  } catch (err) {
    console.warn('[Auth] Token refresh failed:', err.message);
    return null;
  }
};

// ============================================================================
// INITIAL STATE — Recover session from localStorage
// ============================================================================

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

  // If access token exists and is NOT expired, user is authenticated
  if (accessToken && !isTokenExpired(accessToken)) {
    return {
      user,
      token: accessToken,
      refreshToken,
      isAuthenticated: true,
      role: user?.role || null,
      authLoading: false,
    };
  }

  // If access token is expired but refresh token exists and is not expired,
  // mark as "loading" — the async init will try to refresh
  if (refreshToken && !isTokenExpired(refreshToken)) {
    return {
      user,
      token: null,
      refreshToken,
      isAuthenticated: false,
      role: user?.role || null,
      authLoading: true, // will attempt refresh on mount
    };
  }

  // Both tokens expired or missing — clean slate
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  return {
    user: null,
    token: null,
    refreshToken: null,
    isAuthenticated: false,
    role: null,
    authLoading: false,
  };
};

// ============================================================================
// ZUSTAND STORE
// ============================================================================

const useAuthStore = create((set, get) => ({
  ...getInitialState(),

  /**
   * Login — called after successful authentication.
   * Stores both access and refresh tokens.
   */
  login: (userData, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
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

  /**
   * Logout — clears all auth state and localStorage.
   */
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      role: null,
      authLoading: false,
    });
  },

  /**
   * Update the access token after a successful refresh.
   * Called by the API interceptor.
   */
  setToken: (newAccessToken) => {
    localStorage.setItem('access_token', newAccessToken);
    set({ token: newAccessToken, isAuthenticated: true, authLoading: false });
  },

  /**
   * Update user data without changing tokens.
   */
  updateUser: (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    set({ user: userData, role: userData.role });
  },

  /**
   * Initialize auth on app startup.
   * If the access token is expired but refresh token is valid,
   * attempt a silent refresh. This runs once on App mount.
   */
  initializeAuth: async () => {
    const { token, refreshToken } = get();

    // Case 1: Access token is valid — nothing to do
    if (token && !isTokenExpired(token)) {
      set({ isAuthenticated: true, authLoading: false });
      return;
    }

    // Case 2: Access token expired, try refresh
    if (refreshToken && !isTokenExpired(refreshToken)) {
      set({ authLoading: true });
      const newToken = await refreshAccessToken(refreshToken);

      if (newToken) {
        localStorage.setItem('access_token', newToken);
        const user = get().user;
        set({
          token: newToken,
          isAuthenticated: true,
          authLoading: false,
          role: user?.role || null,
        });
        console.log('[Auth] Session restored via token refresh');
        return;
      }
    }

    // Case 3: Both expired — clean up
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      role: null,
      authLoading: false,
    });
  },
}));

export default useAuthStore;
