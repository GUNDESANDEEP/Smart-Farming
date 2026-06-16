import axios from 'axios';
import jwtDecode from 'jwt-decode';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - Add JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor - Handle token expiration and refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh-token`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          apiClient.defaults.headers.common.Authorization = `Bearer ${access_token}`;
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

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
    return apiClient.post('/auth/refresh-token', { refresh_token: refreshToken });
  },
  logout: () => apiClient.post('/auth/logout'),
  getProfile: () => apiClient.get('/auth/profile'),
  updateProfile: (data) => apiClient.put('/auth/profile', data),
  getVerificationStatus: () => apiClient.get('/auth/verification-status'),
  sendOTP: (email) => apiClient.post('/auth/send-otp', { email }),
  verifyOTP: (email, otp) => apiClient.post('/auth/verify-otp', { email, otp }),
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
  getOrderDetail: (id) => apiClient.get(`/farmer/orders/${id}`),
  updateOrderStatus: (id, status) => apiClient.put(`/farmer/orders/${id}/status`, { status }),
  acceptOrder: (id) => apiClient.post(`/farmer/orders/${id}/accept`),
  rejectOrder: (id, reason) => apiClient.post(`/farmer/orders/${id}/reject`, { reason }),
  
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
  getOrderDetail: (id) => apiClient.get(`/buyer/orders/${id}`),
  cancelOrder: (id, reason) => apiClient.post(`/buyer/orders/${id}/cancel`, { reason }),
  
  // Payments
  createPayment: (orderId, amount) =>
    apiClient.post('/buyer/payments/create', { order_id: orderId, amount }),
  verifyPayment: (paymentId, signature) =>
    apiClient.post('/buyer/payments/verify', { payment_id: paymentId, signature }),
  
  // Reviews
  submitReview: (orderId, data) =>
    apiClient.post(`/buyer/orders/${orderId}/review`, data),
  
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
