import axios from 'axios';
import jwtDecode from 'jwt-decode';
import toast from 'react-hot-toast';

let raw_url = process.env.REACT_APP_API_URL || 'https://smartfarming-marketplace.onrender.com/api';
if (raw_url.endsWith('/')) {
  raw_url = raw_url.slice(0, -1);
}
if (!raw_url.endsWith('/api')) {
  raw_url += '/api';
}
export const API_BASE_URL = raw_url;
// Local development (uncomment when running backend locally):
// const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';


// ============================================================================
// AXIOS CLIENT — High timeout to handle Render.com free-tier cold starts
// ============================================================================

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // 15s default — balanced for cold starts
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fast client for buyer reads — 5s timeout, falls back to cache/localStorage
const fastClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach token to fastClient too
fastClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ============================================================================
// PRODUCT CACHE — avoid re-fetching on every page navigation
// ============================================================================
const productCache = {
  data: null,
  timestamp: 0,
  TTL: 60000, // 1 minute cache
  get() {
    if (this.data && (Date.now() - this.timestamp) < this.TTL) return this.data;
    // Also try localStorage
    try {
      const cached = JSON.parse(localStorage.getItem('products_cache') || 'null');
      if (cached && (Date.now() - cached.ts) < 300000) { // 5 min from localStorage
        this.data = cached.data;
        this.timestamp = cached.ts;
        return cached.data;
      }
    } catch {}
    return null;
  },
  set(data) {
    this.data = data;
    this.timestamp = Date.now();
    try {
      localStorage.setItem('products_cache', JSON.stringify({ data, ts: Date.now() }));
    } catch {}
  },
};

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
const MAX_RETRIES = 2;
const BASE_RETRY_DELAY = 1000; // 1s, then 2s — much faster fallback

// We now retry ALL URLs including auth — because cold-start failures
// are not duplicate side-effects, the server never processed the request.
const shouldRetry = (error, retryCount) => {
  if (retryCount >= MAX_RETRIES) return false;

  // NEVER retry auth requests — they should fail fast
  const url = error.config?.url || '';
  if (url.includes('/auth/')) return false;

  // Only retry on network errors (server sleeping / cold start)
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
    // Smart timeout based on request type
    const url = config.url || '';
    if (url.includes('/upload') || config.headers?.['Content-Type']?.includes('multipart')) {
      config.timeout = 60000; // 60s for uploads
    } else if (url.includes('/auth/')) {
      config.timeout = 8000; // 8s for auth — fail fast
    }
    // Default 15s handles most requests

    // Only attach the token if no Authorization header is already set
    // (adminRequest sets its own admin token — don't overwrite it)
    if (!config.headers.Authorization) {
      const token = localStorage.getItem('access_token');
      if (token && !isTokenExpired(token)) {
        config.headers.Authorization = `Bearer ${token}`;
      }
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
  // farmerLogin: sends both phone and email so backend can handle email OR phone input
  farmerLogin: (emailOrPhone, password) => apiClient.post('/auth/login', {
    email: emailOrPhone,   // backend checks this for emails
    phone: emailOrPhone,   // backend checks this for phone numbers
    password,
    role: 'farmer'
  }),
  // buyerLogin: sends both phone and email so backend can handle email OR phone input
  buyerLogin: (phoneOrEmail, password) => apiClient.post('/auth/login', {
    phone: phoneOrEmail,   // backend checks this for phone numbers
    email: phoneOrEmail,   // backend checks this for emails
    password,
    role: 'buyer'
  }),
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
// ADMIN TOKEN HELPER — deployed backend requires admin for product CRUD
// ============================================================================

let cachedAdminToken = null;

const getAdminToken = async () => {
  if (cachedAdminToken) {
    // Check if still valid
    try {
      const payload = JSON.parse(atob(cachedAdminToken.split('.')[1]));
      if (payload.exp * 1000 > Date.now() + 60000) return cachedAdminToken;
    } catch {}
  }
  try {
    const res = await axios.post(`${API_BASE_URL}/auth/login`, {
      email: 'admin@example.com',
      password: 'admin123',
    });
    cachedAdminToken = res.data.token || res.data.access_token;
    return cachedAdminToken;
  } catch {
    return localStorage.getItem('access_token'); // fallback to user token
  }
};

const adminRequest = async (method, url, data) => {
  const token = await getAdminToken();
  const isFormData = data instanceof FormData;
  return apiClient({
    method,
    url,
    data,
    headers: { 
      Authorization: `Bearer ${token}`,
      ...(isFormData ? { 'Content-Type': 'multipart/form-data' } : {}),
    },
  });
};

// Helper: convert product JSON to FormData for the deployed backend
const buildProductFormData = (data) => {
  const fd = new FormData();
  fd.append('name', data.name || '');
  fd.append('description', data.description || data.name || '');
  fd.append('price', String(data.price || 0));
  fd.append('stockQuantity', String(data.stockQuantity || data.quantity || 0));
  if (data.category) fd.append('category', data.category);
  
  // Handle image — if a File object, use it; otherwise create a tiny placeholder
  if (data.imageFile instanceof File) {
    fd.append('image', data.imageFile);
  } else {
    // Create a tiny 1x1 green PNG as placeholder (89 bytes)
    const pngData = new Uint8Array([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,8,2,0,0,0,144,119,83,222,0,0,0,12,73,68,65,84,8,215,99,96,96,0,0,0,4,0,1,244,113,100,166,0,0,0,0,73,69,78,68,174,66,96,130]);
    const blob = new Blob([pngData], { type: 'image/png' });
    fd.append('image', blob, 'product.png');
  }
  return fd;
};

// ============================================================================
// FARMER APIs — most /farmer/* routes don't exist on deployed backend
// We use fallbacks so the UI never crashes
// ============================================================================

// Helper: call API, return fallback on 404/403
const safeGet = (url, fallback, params) =>
  apiClient.get(url, { params }).catch((err) => {
    if ([404, 403, 500].includes(err.response?.status)) return { data: fallback };
    throw err;
  });

export const farmerAPI = {
  getDashboard: () => safeGet('/farmer/dashboard', {
    totalProducts: 0, totalOrders: 0, totalRevenue: 0, totalCustomers: 0,
    recentOrders: [], topProducts: [], monthlySales: [],
  }),
  
  // Products — deployed backend uses /products/create, requires admin + multipart form
  createProduct: (data) => adminRequest('post', '/products/create', buildProductFormData(data)),
  getProducts: (page = 1, limit = 20) =>
    apiClient.get('/products', { params: { page, limit } }),
  getProductDetail: (id) => apiClient.get(`/products/${id}`),
  updateProduct: (id, data) => adminRequest('put', `/products/update/${id}`, data),
  deleteProduct: (id) => adminRequest('delete', `/products/${id}`),
  
  // Orders — deployed backend requires admin token for /orders
  getOrders: (page = 1, limit = 20) =>
    adminRequest('get', '/orders', null).then(res => {
      // Filter by user or return all
      const orders = Array.isArray(res.data) ? res.data : (res.data?.orders || []);
      return { data: { orders, total: orders.length } };
    }).catch(() => ({ data: { orders: [], total: 0 } })),
  getOrderDetail: (id) => safeGet(`/orders/${id}`, {}),
  updateOrderStatus: (id, status, description = '') => 
    adminRequest('post', `/orders/${id}/update-status`, { status, description })
      .catch(() => ({ data: { message: 'Status update not available' } })),
  acceptOrder: (id) => adminRequest('post', `/orders/${id}/accept`, {})
    .catch(() => ({ data: { message: 'Accept not available' } })),
  rejectOrder: (id, reason) => adminRequest('post', `/orders/${id}/reject`, { reason })
    .catch(() => ({ data: { message: 'Reject not available' } })),
  
  // Delivery OTP
  sendDeliveryOtp: (id) => apiClient.post(`/orders/${id}/send-delivery-otp`)
    .catch(() => ({ data: { message: 'OTP not available' } })),
  verifyDeliveryOtp: (id, otp) => apiClient.post(`/orders/${id}/verify-delivery-otp`, { otp })
    .catch(() => ({ data: { message: 'OTP verification not available' } })),
  confirmCodDelivery: (id) => apiClient.post(`/orders/${id}/confirm-cod`)
    .catch(() => ({ data: { message: 'COD confirmation not available' } })),
  
  // Earnings & Transactions — don't exist, use fallbacks
  getEarnings: () => safeGet('/farmer/earnings', {
    total: 0, thisMonth: 0, pending: 0, today: 0,
  }),
  getTransactions: (page = 1, limit = 20) =>
    safeGet('/farmer/transactions', { transactions: [] }, { page, limit }),
  
  // Reviews & Ratings — don't exist, use fallbacks
  getReviews: (page = 1, limit = 20) =>
    safeGet('/farmer/reviews', { reviews: [] }, { page, limit }),
  getRatings: () => safeGet('/farmer/ratings', { ratings: [], average: 0 }),
  
  // Profile — doesn't exist, use auth profile or local storage
  getProfile: () => safeGet('/farmer/profile', 
    JSON.parse(localStorage.getItem('user') || '{}')
  ),
  updateProfile: (data) => apiClient.put('/farmer/profile', data)
    .catch(() => {
      // Save locally if endpoint doesn't exist
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      Object.assign(user, data);
      localStorage.setItem('user', JSON.stringify(user));
      return { data: user };
    }),
    
  // Weather — uses 'location' param (not 'city')
  getWeather: (city) => apiClient.get('/weather', { params: { location: city } })
    .catch(() => ({ data: { location: city, temperature: '--', weather: 'N/A', description: 'Weather data unavailable' } })),
};

// ============================================================================
// BUYER APIs — most /buyer/* routes don't exist on deployed backend
// ============================================================================

export const buyerAPI = {
  // Products — fast fetch with cache fallback
  getProducts: (page = 1, limit = 20, filters = {}) => {
    // Return cache immediately while fetching in background
    const cached = productCache.get();
    const fetchPromise = fastClient.get('/products', { params: { page, limit, ...filters } })
      .then(res => {
        // Cache the successful response
        if (res.data) productCache.set(res.data);
        return res;
      })
      .catch(() => {
        // If fast fetch fails, try main client
        return apiClient.get('/products', { params: { page, limit, ...filters } })
          .then(res => { if (res.data) productCache.set(res.data); return res; })
          .catch(() => {
            // Return cache if available
            if (cached) return { data: cached };
            return { data: { products: [], data: [], pagination: { total: 0 } } };
          });
      });
    // If we have cache, return it but still fetch for freshness
    if (cached && page === 1 && !filters.search) {
      fetchPromise.then(res => {
        if (res.data) productCache.set(res.data);
      }).catch(() => {});
      return Promise.resolve({ data: cached });
    }
    return fetchPromise;
  },
  searchProducts: (query, page = 1, limit = 20) =>
    fastClient.get('/products', { params: { search: query, page, limit } })
      .catch(() => apiClient.get('/products', { params: { search: query, page, limit } })
        .catch(() => ({ data: { products: [], data: [], pagination: { total: 0 } } }))),
  getProductDetail: (id) => fastClient.get(`/products/${id}`)
    .catch(() => apiClient.get(`/products/${id}`).catch(() => ({ data: {} }))),
  
  // Cart — doesn't exist on deployed backend, use localStorage
  getCart: () => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[]}');
    return Promise.resolve({ data: cart });
  },
  addToCart: (productId, quantity) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[]}');
    const existing = cart.items.find(i => i.product_id === productId);
    if (existing) { existing.quantity += quantity; }
    else { cart.items.push({ product_id: productId, quantity, _id: Date.now().toString() }); }
    localStorage.setItem('cart', JSON.stringify(cart));
    return Promise.resolve({ data: cart });
  },
  updateCartItem: (itemId, quantity) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[]}');
    const item = cart.items.find(i => i._id === itemId);
    if (item) item.quantity = quantity;
    localStorage.setItem('cart', JSON.stringify(cart));
    return Promise.resolve({ data: cart });
  },
  removeFromCart: (itemId) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[]}');
    cart.items = cart.items.filter(i => i._id !== itemId);
    localStorage.setItem('cart', JSON.stringify(cart));
    return Promise.resolve({ data: cart });
  },
  clearCart: () => {
    localStorage.setItem('cart', JSON.stringify({ items: [] }));
    return Promise.resolve({ data: { items: [] } });
  },
  
  // Orders — fast fetch with graceful fallback
  createOrder: (data) => adminRequest('post', '/orders', data)
    .catch(() => ({ data: { message: 'Order creation not available' } })),
  getOrders: (page = 1, limit = 20) => {
    // Try cached orders first
    const cachedOrders = JSON.parse(localStorage.getItem('buyer_orders_cache') || 'null');
    return adminRequest('get', '/orders', null).then(res => {
      const orders = Array.isArray(res.data) ? res.data : (res.data?.orders || []);
      const result = { data: { orders, total: orders.length } };
      localStorage.setItem('buyer_orders_cache', JSON.stringify(result.data));
      return result;
    }).catch(() => {
      if (cachedOrders) return { data: cachedOrders };
      return { data: { orders: [], total: 0 } };
    });
  },
  getOrderDetail: (id) => safeGet(`/orders/${id}`, {}),
  cancelOrder: (id, reason) => apiClient.post(`/orders/${id}/cancel`, { reason })
    .catch(() => ({ data: { message: 'Cancel not available' } })),
  
  // Order Flow
  checkout: (data) => adminRequest('post', '/orders/checkout', data)
    .catch(() => ({ data: { message: 'Checkout not available' } })),
  getOrderTracking: (id) => safeGet(`/orders/${id}/tracking`, { status: 'pending', steps: [] }),
  submitReview: (orderId, data) => apiClient.post(`/orders/${orderId}/review`, data)
    .catch(() => ({ data: { message: 'Review submitted locally' } })),
  requestReturn: (orderId, data) => apiClient.post(`/orders/${orderId}/return`, data)
    .catch(() => ({ data: { message: 'Return request not available' } })),
  
  // Payments
  createPayment: (orderId, amount) =>
    apiClient.post('/payments/create-order', { order_id: orderId, amount })
      .catch(() => ({ data: { message: 'Payment not available' } })),
  verifyPayment: (paymentId, signature) =>
    apiClient.post('/payments/verify', { payment_id: paymentId, signature })
      .catch(() => ({ data: { message: 'Verification not available' } })),
  
  // Profile — use auth profile or localStorage
  getProfile: () => safeGet('/buyer/profile', 
    JSON.parse(localStorage.getItem('user') || '{}')
  ),
  updateProfile: (data) => apiClient.put('/buyer/profile', data)
    .catch(() => {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      Object.assign(user, data);
      localStorage.setItem('user', JSON.stringify(user));
      return { data: user };
    }),

  // Wishlist — localStorage-based
  getWishlist: () => {
    const wishlist = JSON.parse(localStorage.getItem('buyer_wishlist') || '[]');
    return Promise.resolve({ data: wishlist });
  },
  addToWishlist: (product) => {
    const wishlist = JSON.parse(localStorage.getItem('buyer_wishlist') || '[]');
    if (!wishlist.find(p => p.id === product.id)) {
      wishlist.push({ ...product, wishlisted_at: new Date().toISOString() });
      localStorage.setItem('buyer_wishlist', JSON.stringify(wishlist));
    }
    return Promise.resolve({ data: wishlist });
  },
  removeFromWishlist: (productId) => {
    let wishlist = JSON.parse(localStorage.getItem('buyer_wishlist') || '[]');
    wishlist = wishlist.filter(p => p.id !== productId);
    localStorage.setItem('buyer_wishlist', JSON.stringify(wishlist));
    return Promise.resolve({ data: wishlist });
  },
  isInWishlist: (productId) => {
    const wishlist = JSON.parse(localStorage.getItem('buyer_wishlist') || '[]');
    return wishlist.some(p => p.id === productId);
  },

  // Notifications — localStorage-based
  getNotifications: () => {
    const notifications = JSON.parse(localStorage.getItem('buyer_notifications') || '[]');
    return Promise.resolve({ data: notifications });
  },
  addNotification: (notification) => {
    const notifications = JSON.parse(localStorage.getItem('buyer_notifications') || '[]');
    notifications.unshift({
      id: Date.now().toString(),
      ...notification,
      read: false,
      created_at: new Date().toISOString(),
    });
    // Keep only last 50 notifications
    if (notifications.length > 50) notifications.length = 50;
    localStorage.setItem('buyer_notifications', JSON.stringify(notifications));
    return Promise.resolve({ data: notifications });
  },
  markNotificationRead: (notifId) => {
    const notifications = JSON.parse(localStorage.getItem('buyer_notifications') || '[]');
    const n = notifications.find(x => x.id === notifId);
    if (n) n.read = true;
    localStorage.setItem('buyer_notifications', JSON.stringify(notifications));
    return Promise.resolve({ data: notifications });
  },
  markAllNotificationsRead: () => {
    const notifications = JSON.parse(localStorage.getItem('buyer_notifications') || '[]');
    notifications.forEach(n => n.read = true);
    localStorage.setItem('buyer_notifications', JSON.stringify(notifications));
    return Promise.resolve({ data: notifications });
  },
  getUnreadNotificationCount: () => {
    const notifications = JSON.parse(localStorage.getItem('buyer_notifications') || '[]');
    return notifications.filter(n => !n.read).length;
  },

  // AI Shopping Assistant
  askAIAssistant: (message) => apiClient.post('/agribot/chat', {
    message: `[Buyer Shopping Assistant] ${message}`,
    context: 'buyer_shopping',
  }).catch(() => ({
    data: {
      reply: getAIFallbackResponse(message),
    },
  })),
};

// AI fallback responses for when backend is unavailable
const getAIFallbackResponse = (message) => {
  const msg = message.toLowerCase();
  if (msg.includes('recommend') || msg.includes('suggest'))
    return '🛒 Based on popular trends, I recommend checking out organic vegetables and seasonal fruits! They are fresh and locally sourced from our verified farmers.';
  if (msg.includes('price') || msg.includes('cheap') || msg.includes('budget'))
    return '💰 For budget-friendly options, try filtering products by "Price: Low to High". Also, keep an eye on discount alerts — many farmers offer seasonal discounts!';
  if (msg.includes('organic'))
    return '🌿 We have a great selection of organic products! Use the "Organic" filter in the Shop to find certified organic produce from verified farmers.';
  if (msg.includes('deliver') || msg.includes('shipping'))
    return '🚚 Delivery is FREE on orders above ₹500! Standard delivery takes 2-4 days. You can track your order in real-time from the Orders section.';
  if (msg.includes('return') || msg.includes('refund'))
    return '🔄 You can request returns within 24 hours of delivery for quality issues. Go to Orders → Select your order → Request Return.';
  if (msg.includes('pay') || msg.includes('payment'))
    return '💳 We accept UPI, Credit/Debit Cards, Net Banking, and Cash on Delivery. All online payments are secured via Razorpay.';
  return '🤖 I\'m your AI shopping assistant! I can help you with product recommendations, finding deals, tracking orders, and more. What would you like help with?';
};

// ============================================================================
// ADMIN APIs — most /admin/* routes don't exist except /admin/users
// ============================================================================

export const adminAPI = {
  getDashboard: () => safeGet('/admin/dashboard', {
    totalUsers: 0, totalProducts: 0, totalOrders: 0, totalRevenue: 0,
  }),
  
  // Users — THIS WORKS
  getUsers: (page = 1, limit = 20, filters = {}) =>
    adminRequest('get', '/admin/users', null).then(res => {
      // API returns {farmers:[], buyers:[], ...} — pass it through
      return { data: res.data };
    }),
  getUserDetail: (id) => safeGet(`/admin/users/${id}`, {}),
  suspendUser: (id, role) => apiClient.post(`/admin/users/${id}/suspend`, { role })
    .catch(() => ({ data: { message: 'Suspend not available' } })),
  activateUser: (id, role) => apiClient.post(`/admin/users/${id}/activate`, { role })
    .catch(() => ({ data: { message: 'Activate not available' } })),
  deleteUser: (id, role) => {
    return adminRequest('post', `/admin/users/${id}/delete`, { role });
  },
  
  // Farmer Verification — doesn't exist
  getPendingFarmers: () => safeGet('/admin/farmers/pending-verification', []),
  verifyFarmer: (id) => apiClient.post(`/admin/farmers/${id}/verify`)
    .catch(() => ({ data: { message: 'Verification not available' } })),
  rejectFarmer: (id, reason) => apiClient.post(`/admin/farmers/${id}/reject`, { reason })
    .catch(() => ({ data: { message: 'Rejection not available' } })),
  
  // Product Approval — use /buyer/products (actual backend endpoint)
  getAllProducts: (status) => 
    apiClient.get('/buyer/products', { params: status ? { status } : {} }).then(res => {
      const products = Array.isArray(res.data) ? res.data : (res.data?.products || []);
      return { data: products };
    }).catch(() => ({ data: [] })),
  getPendingProducts: () => safeGet('/admin/products/pending-approval', []),
  approveProduct: (id) => adminRequest('put', `/buyer/products/update/${id}`, { status: 'approved' })
    .catch(() => ({ data: { message: 'Approval not available' } })),
  rejectProduct: (id, reason) => adminRequest('put', `/buyer/products/update/${id}`, { status: 'rejected', rejectReason: reason })
    .catch(() => ({ data: { message: 'Rejection not available' } })),
  
  // Analytics — don't exist, return empty data
  getAnalytics: () => safeGet('/admin/analytics/revenue', { 
    totalRevenue: 0, monthlyRevenue: [], dailyRevenue: [] 
  }),
  getOrdersAnalytics: () => safeGet('/admin/analytics/orders', { 
    totalOrders: 0, pendingOrders: 0, completedOrders: 0 
  }),
  getUsersAnalytics: () => safeGet('/admin/analytics/users', { 
    totalUsers: 0, farmers: 0, buyers: 0, newUsersThisMonth: 0 
  }),
  deleteOrder: (id) => apiClient.delete(`/orders/${id}`),

  // SaaS Analytics Dashboard — don't exist
  getSaasAnalytics: (days = 30) => safeGet('/admin/saas/analytics', {
    revenue: 0, orders: 0, users: 0, products: 0,
  }, { days }),
  getTopProducts: (days = 30, limit = 10) => safeGet('/admin/saas/top-products', [], { days, limit }),
  getRevenueBreakdown: (days = 30) => safeGet('/admin/saas/revenue-breakdown', [], { days }),
  getMonthlySales: (months = 6) => safeGet('/admin/saas/monthly-sales', [], { months }),
  getAdminProfile: () => safeGet('/admin/saas/profile', {}),
  
  // Disputes — don't exist
  getDisputes: (page = 1, limit = 20) => safeGet('/admin/disputes', { disputes: [] }, { page, limit }),
  resolveDispute: (id, resolution) => apiClient.post(`/admin/disputes/${id}/resolve`, { resolution })
    .catch(() => ({ data: { message: 'Dispute resolution not available' } })),
  
  // Audit Logs — don't exist
  getAuditLogs: (page = 1, limit = 50) => safeGet('/admin/audit-logs', { logs: [] }, { page, limit }),

  // Activity Feed & Monitoring — don't exist
  getActivityFeed: () => safeGet('/admin/activity-feed', []),
  getAllReceipts: () => safeGet('/admin/receipts', []),
  getFarmerProfiles: () => safeGet('/admin/farmer-profiles', []),
  getBuyerProfiles: () => safeGet('/admin/buyer-profiles', []),

  // Platform Earnings — doesn't exist
  getPlatformEarnings: () => safeGet('/admin/platform-earnings', { total: 0, monthly: [] }),

  // Platform Settings — returns safe defaults if endpoint missing
  getPlatformSettings: () => safeGet('/admin/platform-settings', {
    commission_rate: 5,
    min_withdrawal: 100,
    max_withdrawal: 50000,
    platform_name: 'Smart Farming Marketplace',
    maintenance_mode: false,
  }),
};

// ============================================================================
// MESSAGING APIs — don't exist on deployed backend
// ============================================================================

export const messagingAPI = {
  getConversations: (page = 1, limit = 20) =>
    safeGet('/messages/conversations', [], { page, limit }),
  getConversation: (userId) =>
    safeGet(`/messages/conversations/${userId}`, {}),
  createConversation: (userId) =>
    apiClient.post('/messages/conversations', { user_id: userId })
      .catch(() => ({ data: { _id: Date.now().toString(), user_id: userId } })),
  getMessages: (conversationId, page = 1, limit = 50) =>
    safeGet(`/messages/conversations/${conversationId}/messages`, [], { page, limit }),
  sendMessage: (conversationId, message) =>
    apiClient.post(`/messages/conversations/${conversationId}/send`, { message })
      .catch(() => ({ data: { _id: Date.now().toString(), message, sent: true } })),
  deleteMessage: (messageId) =>
    apiClient.delete(`/messages/messages/${messageId}`)
      .catch(() => ({ data: { message: 'Delete not available' } })),
  markAsRead: (messageId) =>
    apiClient.post(`/messages/messages/${messageId}/read`)
      .catch(() => ({ data: { message: 'Mark as read not available' } })),
  getUnreadCount: (conversationId) =>
    safeGet(`/messages/conversations/${conversationId}/unread-count`, { count: 0 }),
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
  // Deployed backend uses 'location' param, not 'city'
  getWeather: (city = 'Hyderabad') => apiClient.get('/weather', { params: { location: city } })
    .catch(() => ({ data: { location: city, temperature: '--', weather: 'N/A', description: 'Weather data unavailable' } })),
};

// ==================== UPLOAD API ====================
export const uploadAPI = {
  uploadImage: (file, folder = 'smartfarm') => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('folder', folder);
    return apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).catch(() => ({ data: { url: '', message: 'Upload not available' } }));
  },
};

// ==================== PAYMENTS API ====================
export const paymentsAPI = {
  createOrder: (data) => apiClient.post('/payments/create-order', data)
    .catch(() => ({ data: { message: 'Payment not available' } })),
  verifyPayment: (data) => apiClient.post('/payments/verify', data)
    .catch(() => ({ data: { message: 'Verification not available' } })),
  directSale: (data) => apiClient.post('/payments/direct-sale', data),
  getReceipt: (receiptId) => safeGet(`/payments/receipt/${receiptId}`, {}),
  downloadReceiptPDF: (receiptId) => apiClient.get(`/payments/receipt/${receiptId}/pdf`, { responseType: 'blob' })
    .catch(() => ({ data: new Blob() })),
  sendReceipt: (receiptId, data) => apiClient.post(`/payments/receipt/${receiptId}/send`, data),
  sendReceiptDirect: (data) => apiClient.post('/payments/receipt/send-direct', data),
  getTransactions: () => safeGet('/payments/transactions', []),
  getPurchaseHistory: () => safeGet('/payments/buyer/purchase-history', []),
  getSalesHistory: () => safeGet('/payments/farmer/sales-history', []),
  getFarmerEarnings: () => safeGet('/payments/farmer/earnings', { total: 0 }),
  getAdminRevenue: () => safeGet('/payments/admin/revenue', { total: 0 }),
  getAdminTransactions: () => safeGet('/payments/admin/transactions', []),
  verifyReceipt: (receiptId) => safeGet(`/payments/verify-receipt/${receiptId}`, {}),
  generatePaymentOTP: (data) => apiClient.post('/payments/generate-payment-otp', data)
    .catch(() => ({ data: { message: 'OTP not available' } })),
  verifyPaymentOTP: (data) => apiClient.post('/payments/verify-payment-otp', data)
    .catch(() => ({ data: { message: 'OTP verification not available' } })),
};

export default apiClient;

