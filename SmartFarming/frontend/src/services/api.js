import axios from 'axios';
import jwtDecode from 'jwt-decode';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://smart-farming-backend.onrender.com/api';

// ============================================================================
// AXIOS CLIENT — High timeout to handle Render.com free-tier cold starts
// ============================================================================

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s default — Render free tier can take 30-50s to wake
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// JWT HELPER — check expiry client-side
// ============================================================================
const isTokenExpired = (token) => {
  if (!token) return true;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (!payload.exp) return false;
    return payload.exp * 1000 < Date.now() + 30000; // 30s buffer
  } catch {
    return true;
  }
};

// ============================================================================
// RETRY CONFIG — Aggressive retries for Render cold starts
// ============================================================================
const RETRY_STATUS_CODES = [502, 503, 504, 0]; // 0 = network error
const MAX_RETRIES = 3;
const BASE_RETRY_DELAY = 2000; // 2s, then 4s, then 8s

// We now retry ALL URLs including auth — because cold-start failures
// are not duplicate side-effects, the server never processed the request.
const shouldRetry = (error, retryCount) => {
  if (retryCount >= MAX_RETRIES) return false;

  // Always retry on network errors (server sleeping / cold start)
  if (!error.response) return true;

  // Retry on timeout
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) return true;

  // Retry on server overload / gateway errors
  if (RETRY_STATUS_CODES.includes(error.response.status)) return true;

  return false;
};

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ============================================================================
// SERVER WAKEUP TOAST — Show a single persistent toast while retrying
// ============================================================================
let wakeupToastId = null;

const showWakeupToast = () => {
  if (!wakeupToastId) {
    wakeupToastId = toast.loading(
      '☕ Server is waking up... This takes ~30 seconds on free hosting. Please wait.',
      { duration: 90000, id: 'server-wakeup' }
    );
  }
};

const dismissWakeupToast = () => {
  if (wakeupToastId) {
    toast.dismiss('server-wakeup');
    wakeupToastId = null;
  }
};

// ============================================================================
// REFRESH LOCK — Prevent multiple simultaneous refresh requests
// ============================================================================
let isRefreshing = false;
let refreshSubscribers = [];

const onRefreshed = (newToken) => {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
};

const addRefreshSubscriber = (callback) => {
  refreshSubscribers.push(callback);
};

// ============================================================================
// REQUEST INTERCEPTOR — Smart timeouts + attach valid token
// ============================================================================
apiClient.interceptors.request.use(
  (config) => {
    // Smart timeout based on request type (all high for cold starts)
    const url = config.url || '';
    if (url.includes('/upload') || config.headers?.['Content-Type']?.includes('multipart')) {
      config.timeout = 90000; // 90s for uploads
    }
    // Default 60s handles cold starts for all other requests

    // Only attach the token if it exists and is not expired
    const token = localStorage.getItem('access_token');
    if (token && !isTokenExpired(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Initialize retry counter
    if (config._retryCount === undefined) {
      config._retryCount = 0;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================================================
// RESPONSE INTERCEPTOR — Auto-retry with wakeup toast, auto-refresh
// ============================================================================
apiClient.interceptors.response.use(
  (response) => {
    // Success — dismiss any wakeup toast
    dismissWakeupToast();
    return response;
  },
  async (error) => {
    const originalRequest = error.config || {};

    // ── Retry logic for transient errors (including cold starts) ──
    if (shouldRetry(error, originalRequest._retryCount || 0)) {
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
      const retryDelay = BASE_RETRY_DELAY * Math.pow(2, originalRequest._retryCount - 1);

      // Show wakeup toast on first retry
      showWakeupToast();

      console.log(`[API] Retry ${originalRequest._retryCount}/${MAX_RETRIES} in ${retryDelay}ms: ${originalRequest.url}`);
      await delay(retryDelay);
      return apiClient(originalRequest);
    }

    // All retries exhausted — dismiss wakeup toast
    dismissWakeupToast();

    // ── Timeout error ──
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const timeoutError = new Error(
        'Server is taking too long to respond. It may be restarting — please try again in 30 seconds.'
      );
      timeoutError._isTimeoutError = true;
      return Promise.reject(timeoutError);
    }

    // ── Network Error (server completely unreachable after retries) ──
    if (!error.response) {
      const networkError = new Error(
        'Server is currently unavailable. It may be restarting — please try again in a minute.'
      );
      networkError._isNetworkError = true;
      return Promise.reject(networkError);
    }

    // ── 401 Unauthorized — Try token refresh ──
    if (error.response.status === 401 && !originalRequest._retry) {
      // Don't try to refresh for login/register/refresh requests themselves
      const url = originalRequest.url || '';
      if (url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');

      // No refresh token — session is gone
      if (!refreshToken || isTokenExpired(refreshToken)) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }

        const silentError = new Error('Session expired. Please login again.');
        silentError._silentAuthRedirect = true;
        return Promise.reject(silentError);
      }

      // If a refresh is already in progress, queue this request
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      // Start refresh
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        }, { timeout: 60000 });

        const { access_token: newToken } = response.data;
        localStorage.setItem('access_token', newToken);

        // Update auth store if available
        try {
          const { default: useAuthStore } = await import('./authStore');
          useAuthStore.getState().setToken(newToken);
        } catch { /* store not available */ }

        isRefreshing = false;
        onRefreshed(newToken);

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshSubscribers = [];

        // Refresh failed — clean up and redirect
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }

        const silentError = new Error('Session expired. Please login again.');
        silentError._silentAuthRedirect = true;
        return Promise.reject(silentError);
      }
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// ERROR MESSAGE HELPER — Map any error to a user-friendly message
// ============================================================================

export const getErrorMessage = (error) => {
  // Silent auth redirects — no message needed
  if (error?._silentAuthRedirect) return null;

  // Timeout
  if (error?._isTimeoutError || error?.code === 'ECONNABORTED') {
    return 'Server is taking too long. It may be restarting — please try again in 30 seconds.';
  }

  // Network error (server down / cold start exhausted)
  if (error?._isNetworkError || !error?.response) {
    return 'Server is currently unavailable. It may be restarting — please try again in a minute.';
  }

  const status = error.response?.status;
  const data = error.response?.data;
  const errorCode = data?.error_code;
  const errorMsg = data?.error || data?.message;

  // 503 — Server warming up (DB connection issue)
  if (status === 503 || errorCode === 'database_error') {
    return 'Server is warming up. Please wait 30 seconds and try again.';
  }

  // 401 — Authentication errors (use backend message directly)
  if (status === 401 && errorMsg) {
    return errorMsg;
  }

  // 400 — Validation errors
  if (status === 400 && errorMsg) {
    return errorMsg;
  }

  // 500 — Server errors
  if (status === 500) {
    return errorMsg || 'Something went wrong on the server. Please try again.';
  }

  // Fallback
  return errorMsg || 'Something went wrong. Please try again.';
};

// ============================================================================
// AUTHENTICATION APIs
// ============================================================================

export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
  farmerLogin: (email, password) => apiClient.post('/auth/login', { email, password, role: 'farmer' }),
  buyerLogin: (phone, password) => apiClient.post('/auth/login', { phone, password, role: 'buyer' }),
  adminLogin: (email, password) => apiClient.post('/auth/login', { email, password, role: 'admin' }),
  firebaseLogin: (idToken) => apiClient.post('/auth/firebase-login', { id_token: idToken }),
  verifyEmail: (otp) => apiClient.post('/auth/verify-email', { otp }),
  otpLogin: (phone) => apiClient.post('/auth/otp-login', { phone }),
  verifyOTPLogin: (phone, otp) => apiClient.post('/auth/verify-otp-login', { phone, otp }),
  forgotPassword: (email) => apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (email, otp, new_password) => apiClient.post('/auth/reset-password', { email, otp, new_password }),
  changePassword: (oldPassword, newPassword) =>
    apiClient.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  refreshToken: () => {
    const refreshToken = localStorage.getItem('refresh_token');
    return axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
  },
  validateSession: () => apiClient.get('/auth/session/validate'),
  logout: () => apiClient.post('/auth/logout'),
  getProfile: () => apiClient.get('/auth/profile'),
  updateProfile: (data) => apiClient.put('/auth/profile', data),
  getVerificationStatus: () => apiClient.get('/auth/verification-status'),
  sendOTP: (email) => apiClient.post('/auth/send-otp', { email }),
  verifyOTP: (email, otp) => apiClient.post('/auth/verify-otp', { email, otp }),
  completeLogin: (email, otp, role) => apiClient.post('/auth/complete-login', { email, otp, role }),
};

// ============================================================================
// FARMER APIs
// ============================================================================

export const farmerAPI = {
  getDashboard: () => apiClient.get('/farmer/dashboard'),
  
  // Products
  createProduct: (data) => apiClient.post('/farmer/products', data),
  getProducts: (page = 1, limit = 20) =>
    apiClient.get('/farmer/products', { params: { page, limit } }),
  getProductDetail: (id) => apiClient.get(`/farmer/products/${id}`),
  updateProduct: (id, data) => apiClient.put(`/farmer/products/${id}`, data),
  deleteProduct: (id) => apiClient.delete(`/farmer/products/${id}`),
  
  // Orders
  getOrders: (page = 1, limit = 20) =>
    apiClient.get('/farmer/orders', { params: { page, limit } }),
  getOrderDetail: (id) => apiClient.get(`/orders/${id}`),
  updateOrderStatus: (id, status, description = '') => 
    apiClient.post(`/orders/${id}/update-status`, { status, description }),
  acceptOrder: (id) => apiClient.post(`/orders/${id}/accept`),
  rejectOrder: (id, reason) => apiClient.post(`/orders/${id}/reject`, { reason }),
  
  // Delivery OTP (Online payment verification)
  sendDeliveryOtp: (id) => apiClient.post(`/orders/${id}/send-delivery-otp`),
  verifyDeliveryOtp: (id, otp) => apiClient.post(`/orders/${id}/verify-delivery-otp`, { otp }),
  
  // COD Delivery confirmation
  confirmCodDelivery: (id) => apiClient.post(`/orders/${id}/confirm-cod`),
  
  // Earnings & Transactions
  getEarnings: () => apiClient.get('/farmer/earnings'),
  getTransactions: (page = 1, limit = 20) =>
    apiClient.get('/farmer/transactions', { params: { page, limit } }),
  
  // Reviews & Ratings
  getReviews: (page = 1, limit = 20) =>
    apiClient.get('/farmer/reviews', { params: { page, limit } }),
  getRatings: () => apiClient.get('/farmer/ratings'),
  
  // Profile
  getProfile: () => apiClient.get('/farmer/profile'),
  updateProfile: (data) => apiClient.put('/farmer/profile', data),
  getWeather: (city) => apiClient.get(`/weather?city=${city}`),
};

// ============================================================================
// BUYER APIs
// ============================================================================

export const buyerAPI = {
  // Products
  getProducts: (page = 1, limit = 20, filters = {}) =>
    apiClient.get('/buyer/products', { params: { page, limit, ...filters } }),
  searchProducts: (query, page = 1, limit = 20) =>
    apiClient.get('/buyer/products/search', { params: { query, page, limit } }),
  getProductDetail: (id) => apiClient.get(`/buyer/products/${id}`),
  
  // Cart
  getCart: () => apiClient.get('/buyer/cart'),
  addToCart: (productId, quantity) =>
    apiClient.post('/buyer/cart/items', { product_id: productId, quantity }),
  updateCartItem: (itemId, quantity) =>
    apiClient.put(`/buyer/cart/items/${itemId}`, { quantity }),
  removeFromCart: (itemId) => apiClient.delete(`/buyer/cart/items/${itemId}`),
  clearCart: () => apiClient.post('/buyer/cart/clear'),
  
  // Orders
  createOrder: (data) => apiClient.post('/buyer/orders', data),
  getOrders: (page = 1, limit = 20) =>
    apiClient.get('/buyer/orders', { params: { page, limit } }),
  getOrderDetail: (id) => apiClient.get(`/orders/${id}`),
  cancelOrder: (id, reason) => apiClient.post(`/orders/${id}/cancel`, { reason }),
  
  // Order Flow
  checkout: (data) => apiClient.post('/orders/checkout', data),
  getOrderTracking: (id) => apiClient.get(`/orders/${id}/tracking`),
  submitReview: (orderId, data) => apiClient.post(`/orders/${orderId}/review`, data),
  requestReturn: (orderId, data) => apiClient.post(`/orders/${orderId}/return`, data),
  
  // Payments
  createPayment: (orderId, amount) =>
    apiClient.post('/buyer/payments/create', { order_id: orderId, amount }),
  verifyPayment: (paymentId, signature) =>
    apiClient.post('/buyer/payments/verify', { payment_id: paymentId, signature }),
  
  // Reviews
  
  // Profile
  getProfile: () => apiClient.get('/buyer/profile'),
  updateProfile: (data) => apiClient.put('/buyer/profile', data),
};

// ============================================================================
// ADMIN APIs
// ============================================================================

export const adminAPI = {
  getDashboard: () => apiClient.get('/admin/dashboard'),
  
  // Users
  getUsers: (page = 1, limit = 20, filters = {}) =>
    apiClient.get('/admin/users', { params: { page, limit, ...filters } }),
  getUserDetail: (id) => apiClient.get(`/admin/users/${id}`),
  suspendUser: (id, role) => apiClient.post(`/admin/users/${id}/suspend`, { role }),
  activateUser: (id, role) => apiClient.post(`/admin/users/${id}/activate`, { role }),
  deleteUser: (id, role) => apiClient.post(`/admin/users/${id}/delete`, { role }),
  
  // Farmer Verification
  getPendingFarmers: () =>
    apiClient.get('/admin/farmers/pending-verification'),
  verifyFarmer: (id) => apiClient.post(`/admin/farmers/${id}/verify`),
  rejectFarmer: (id, reason) =>
    apiClient.post(`/admin/farmers/${id}/reject`, { reason }),
  
  // Product Approval
  getAllProducts: (status) => 
    apiClient.get('/admin/products/all', { params: status ? { status } : {} }),
  getPendingProducts: () =>
    apiClient.get('/admin/products/pending-approval'),
  approveProduct: (id) => apiClient.post(`/admin/products/${id}/approve`),
  rejectProduct: (id, reason) =>
    apiClient.post(`/admin/products/${id}/reject`, { reason }),
  
  // Analytics
  getAnalytics: () => apiClient.get('/admin/analytics/revenue'),
  getOrdersAnalytics: () => apiClient.get('/admin/analytics/orders'),
  getUsersAnalytics: () => apiClient.get('/admin/analytics/users'),

  // SaaS Analytics Dashboard
  getSaasAnalytics: (days = 30) => apiClient.get('/admin/saas/analytics', { params: { days } }),
  getTopProducts: (days = 30, limit = 10) => apiClient.get('/admin/saas/top-products', { params: { days, limit } }),
  getRevenueBreakdown: (days = 30) => apiClient.get('/admin/saas/revenue-breakdown', { params: { days } }),
  getMonthlySales: (months = 6) => apiClient.get('/admin/saas/monthly-sales', { params: { months } }),
  getAdminProfile: () => apiClient.get('/admin/saas/profile'),
  
  // Disputes
  getDisputes: (page = 1, limit = 20) =>
    apiClient.get('/admin/disputes', { params: { page, limit } }),
  resolveDispute: (id, resolution) =>
    apiClient.post(`/admin/disputes/${id}/resolve`, { resolution }),
  
  // Audit Logs
  getAuditLogs: (page = 1, limit = 50) =>
    apiClient.get('/admin/audit-logs', { params: { page, limit } }),

  // Activity Feed & Monitoring
  getActivityFeed: () => apiClient.get('/admin/activity-feed'),
  getAllReceipts: () => apiClient.get('/admin/receipts'),
  getFarmerProfiles: () => apiClient.get('/admin/farmer-profiles'),
  getBuyerProfiles: () => apiClient.get('/admin/buyer-profiles'),

  // Platform Earnings / Revenue Split
  getPlatformEarnings: () => apiClient.get('/admin/platform-earnings'),
};

// ============================================================================
// MESSAGING APIs
// ============================================================================

export const messagingAPI = {
  getConversations: (page = 1, limit = 20) =>
    apiClient.get('/messages/conversations', { params: { page, limit } }),
  getConversation: (userId) =>
    apiClient.get(`/messages/conversations/${userId}`),
  createConversation: (userId) =>
    apiClient.post('/messages/conversations', { user_id: userId }),
  getMessages: (conversationId, page = 1, limit = 50) =>
    apiClient.get(`/messages/conversations/${conversationId}/messages`, {
      params: { page, limit },
    }),
  sendMessage: (conversationId, message) =>
    apiClient.post(`/messages/conversations/${conversationId}/send`, { message }),
  deleteMessage: (messageId) =>
    apiClient.delete(`/messages/messages/${messageId}`),
  markAsRead: (messageId) =>
    apiClient.post(`/messages/messages/${messageId}/read`),
  getUnreadCount: (conversationId) =>
    apiClient.get(`/messages/conversations/${conversationId}/unread-count`),
};

// ============================================================================
// TOKEN UTILITIES
// ============================================================================

export const tokenUtils = {
  setToken: (token) => {
    localStorage.setItem('access_token', token);
  },
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
  },
  getToken: () => localStorage.getItem('access_token'),
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  clearToken: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  isAuthenticated: () => !!localStorage.getItem('access_token'),
  decodeToken: (token) => {
    try {
      return jwtDecode(token);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  },
  isTokenExpired: (token) => {
    const decoded = tokenUtils.decodeToken(token);
    if (!decoded?.exp) return false;
    return decoded.exp * 1000 < Date.now();
  },
};

// ==================== WEATHER API ====================
export const weatherAPI = {
  getWeather: (city = 'Hyderabad') => apiClient.get('/weather', { params: { city } }),
};

// ==================== UPLOAD API ====================
export const uploadAPI = {
  uploadImage: (file, folder = 'smartfarm') => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('folder', folder);
    return apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ==================== PAYMENTS API ====================
export const paymentsAPI = {
  // Razorpay - Create order
  createOrder: (data) => apiClient.post('/payments/create-order', data),
  // Razorpay - Verify payment
  verifyPayment: (data) => apiClient.post('/payments/verify', data),
  // Direct sale (farmer sells in-person)
  directSale: (data) => apiClient.post('/payments/direct-sale', data),
  // Get receipt
  getReceipt: (receiptId) => apiClient.get(`/payments/receipt/${receiptId}`),
  // Download receipt PDF
  downloadReceiptPDF: (receiptId) => apiClient.get(`/payments/receipt/${receiptId}/pdf`, { responseType: 'blob' }),
  // Send receipt (SMS/WhatsApp/Email)
  sendReceipt: (receiptId, data) => apiClient.post(`/payments/receipt/${receiptId}/send`, data),
  // Get transactions
  getTransactions: () => apiClient.get('/payments/transactions'),
  // Buyer purchase history
  getPurchaseHistory: () => apiClient.get('/payments/buyer/purchase-history'),
  // Farmer sales history
  getSalesHistory: () => apiClient.get('/payments/farmer/sales-history'),
  // Farmer earnings
  getFarmerEarnings: () => apiClient.get('/payments/farmer/earnings'),
  // Admin revenue
  getAdminRevenue: () => apiClient.get('/payments/admin/revenue'),
  // Admin transaction reports
  getAdminTransactions: () => apiClient.get('/payments/admin/transactions'),
  // Verify receipt QR
  verifyReceipt: (receiptId) => apiClient.get(`/payments/verify-receipt/${receiptId}`),
  // Payment OTP
  generatePaymentOTP: (data) => apiClient.post('/payments/generate-payment-otp', data),
  verifyPaymentOTP: (data) => apiClient.post('/payments/verify-payment-otp', data),
};

export default apiClient;
