import axios from 'axios';
import toast from 'react-hot-toast';

// ============================================================================
// API BASE URL — auto-detect local vs production
// ============================================================================
const isBrowserLocalHost = () => {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname;
  return host === 'localhost' || host === '127.0.0.1';
};

export const isRemoteApi = (baseUrl) =>
  typeof baseUrl === 'string' &&
  (baseUrl.includes('onrender.com') || baseUrl.startsWith('https://'));

const resolveApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) return process.env.REACT_APP_API_URL;
  if (isBrowserLocalHost()) return '/api';
  return 'https://smartfarming-marketplace.onrender.com/api';
};

export const API_BASE_URL = resolveApiBaseUrl();

// ============================================================================
// SERVER WARMUP — wake Render free tier before login/dashboard calls
// ============================================================================
let warmupPromise = null;

export const warmupServer = () => {
  if (!isRemoteApi(API_BASE_URL)) return Promise.resolve(true);
  if (warmupPromise) return warmupPromise;

  warmupPromise = axios
    .get(`${API_BASE_URL}/health`, { timeout: 90000 })
    .then(() => true)
    .catch(() => false)
    .finally(() => {
      warmupPromise = null;
    });

  return warmupPromise;
};


// ============================================================================
// AXIOS CLIENT — High timeout to handle Render.com free-tier cold starts
// ============================================================================

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: isRemoteApi(API_BASE_URL) ? 90000 : 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fast client for buyer reads — falls back to cache/localStorage
const fastClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: isRemoteApi(API_BASE_URL) ? 30000 : 8000,
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
  TTL: 120000, // 2 minute in-memory cache
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
const RETRY_STATUS_CODES = [502, 503, 504, 0];
const getMaxRetries = () => (isRemoteApi(API_BASE_URL) ? 6 : 3);
const BASE_RETRY_DELAY = isRemoteApi(API_BASE_URL) ? 3000 : 1000;

const shouldRetry = (error, retryCount) => {
  if (retryCount >= getMaxRetries()) return false;

  const isNetworkOrTimeout =
    !error.response ||
    error.code === 'ECONNABORTED' ||
    error.message?.includes('timeout');
  const isGateway =
    error.response && RETRY_STATUS_CODES.includes(error.response.status);

  if (!isNetworkOrTimeout && !isGateway) return false;

  const url = error.config?.url || '';
  // Don't retry auth when credentials are wrong — only on unreachable server
  if (url.includes('/auth/') && error.response && error.response.status < 500) {
    return false;
  }

  return true;
};

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ============================================================================
// SERVER WAKEUP TOAST — Show a single persistent toast while retrying
// ============================================================================
let wakeupToastId = null;

const showWakeupToast = () => {
  if (!wakeupToastId) {
    const message = isRemoteApi(API_BASE_URL)
      ? 'Connecting to server... first load can take up to a minute on free hosting.'
      : 'Connecting to local server...';
    wakeupToastId = toast.loading(message, { duration: 120000, id: 'server-wakeup' });
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
      config.timeout = isRemoteApi(API_BASE_URL) ? 90000 : 15000;
    }
    // Default 15s handles most requests

    // Always attach the token if present — let the backend decide validity.
    // Previously, isTokenExpired() would drop non-JWT tokens (e.g. admin local
    // tokens) causing 401 → auto-logout loops.
    if (!config.headers.Authorization) {
      const token = localStorage.getItem('access_token');
      if (token) {
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

      console.log(`[API] Retry ${originalRequest._retryCount}/${getMaxRetries()} in ${retryDelay}ms: ${originalRequest.url}`);
      await delay(retryDelay);
      return apiClient(originalRequest);
    }

    // All retries exhausted — dismiss wakeup toast
    dismissWakeupToast();

    // ── Timeout error ──
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const timeoutError = new Error(
        isRemoteApi(API_BASE_URL)
          ? 'Server is still starting. Please wait a moment and try again.'
          : 'Backend is not responding. Run SmartFarming/start-local.bat or start the backend with: cd backend && python main.py'
      );
      timeoutError._isTimeoutError = true;
      return Promise.reject(timeoutError);
    }

    // ── Network Error (server completely unreachable after retries) ──
    if (!error.response) {
      const networkError = new Error(
        isRemoteApi(API_BASE_URL)
          ? 'Could not reach the server. Please check your internet connection and try again.'
          : 'Backend is not running. Double-click SmartFarming/start-local.bat to start both servers.'
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

      // Don't auto-logout for non-critical API calls that may not exist
      // These should fail gracefully without destroying the user's session
      const nonCriticalPaths = ['/checkout/', '/farmer-orders', '/wallet', '/order-flow', '/orders/'];
      if (nonCriticalPaths.some(p => url.includes(p))) {
        console.warn(`[API] 401 on non-critical endpoint ${url} — not logging out`);
        return Promise.reject(error);
      }

      // Grace period: don't auto-logout within 10 seconds of login
      // This prevents the dashboard's initial API calls from triggering logout
      const loginTimestamp = parseInt(localStorage.getItem('login_timestamp') || '0', 10);
      if (Date.now() - loginTimestamp < 10000) {
        console.warn('[API] 401 received within login grace period — not logging out');
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
    return isRemoteApi(API_BASE_URL)
      ? 'Server is still starting. Please wait a moment and try again.'
      : 'Backend is not responding. Run SmartFarming/start-local.bat to start the servers.';
  }

  // Network error (server down / cold start exhausted)
  if (error?._isNetworkError || !error?.response) {
    return isRemoteApi(API_BASE_URL)
      ? 'Could not reach the server. Check your connection and try again.'
      : 'Backend is not running. Run SmartFarming/start-local.bat to start both servers.';
  }

  const status = error.response?.status;
  const data = error.response?.data;
  const errorCode = data?.error_code;
  const errorMsg = data?.error || data?.message;

  // 503 — Server warming up (DB connection issue)
  if (status === 503 || errorCode === 'database_error') {
    return 'Server is warming up. Please wait 30 seconds and try again.';
  }

  // 404 — endpoint or resource not found
  if (status === 404) {
    return errorMsg || 'Resource not found. Please refresh and try again.';
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
// ADMIN TOKEN HELPER — deployed backend requires admin for product CRUD
// ============================================================================

let cachedAdminToken = null; // eslint-disable-line no-unused-vars

const getAdminToken = async () => {
  // Use the current user's token if they are admin
  const currentToken = localStorage.getItem('access_token');
  if (currentToken) {
    try {
      const payload = JSON.parse(atob(currentToken.split('.')[1]));
      if (payload.role === 'admin' && payload.exp * 1000 > Date.now() + 60000) {
        return currentToken;
      }
    } catch {}
  }
  // Fallback: return whatever token we have (server will validate)
  return currentToken;
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
  if (data.unit) fd.append('unit', data.unit);
  if (data.location) fd.append('location', data.location);
  if (data.discount_percentage) fd.append('discount_percentage', String(data.discount_percentage));
  if (data.is_organic !== undefined) fd.append('is_organic', String(data.is_organic));
  
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

  createProduct: (data) => apiClient.post('/farmer/products', data),
  getProducts: (page = 1, limit = 20) =>
    apiClient.get('/farmer/products', { params: { page, limit } }),
  getProductDetail: (id) => apiClient.get(`/farmer/products/${id}`),
  updateProduct: (id, data) => apiClient.put(`/farmer/products/${id}`, data),
  deleteProduct: (id) => apiClient.delete(`/farmer/products/${id}`),

  getOrders: (page = 1, limit = 20, status) =>
    apiClient.get('/farmer/orders', { params: { page, limit, status } })
      .catch(() => ({ data: { orders: [], total: 0 } })),
  getOrderDetail: (id) => apiClient.get(`/farmer/orders/${id}`),
  updateOrderStatus: (id, status, description = '') =>
    apiClient.put(`/farmer/orders/${id}/status`, { status, description }),
  acceptOrder: (id) => apiClient.post(`/farmer/orders/${id}/accept`, {}),
  rejectOrder: (id, reason) => apiClient.post(`/farmer/orders/${id}/reject`, { reason }),
  
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
    const cached = productCache.get();
    const fetchPromise = fastClient.get('/buyer/products', { params: { page, limit, ...filters } })
      .then(res => {
        if (res.data) productCache.set(res.data);
        return res;
      })
      .catch(() => {
        return apiClient.get('/buyer/products', { params: { page, limit, ...filters } })
          .then(res => { if (res.data) productCache.set(res.data); return res; })
          .catch(() => {
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
    fastClient.get('/buyer/products/search', { params: { q: query, page, limit } })
      .catch(() => apiClient.get('/buyer/products/search', { params: { q: query, page, limit } })
        .catch(() => ({ data: { products: [], data: [], pagination: { total: 0 } } }))),
  getProductDetail: (id) => fastClient.get(`/buyer/products/${id}`)
    .catch(() => apiClient.get(`/buyer/products/${id}`).catch(() => ({ data: {} }))),
  
  // Cart — doesn't exist on deployed backend, use localStorage with rich product structures
  getCart: () => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[],"total_amount":0}');
    cart.total_amount = cart.items.reduce((s, i) => s + (i.product?.price || 0) * i.quantity, 0);
    return Promise.resolve({ data: cart });
  },
  addToCart: (productOrId, quantity) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[],"total_amount":0}');
    
    const proceedWithProduct = (productObj) => {
      const productId = productObj.id;
      const existing = cart.items.find(i => i.product_id === productId);
      if (existing) {
        existing.quantity += quantity;
      } else {
        cart.items.push({
          product_id: productId,
          quantity,
          product: productObj,
          _id: Date.now().toString()
        });
      }
      cart.total_amount = cart.items.reduce((s, i) => s + (i.product?.price || 0) * i.quantity, 0);
      localStorage.setItem('cart', JSON.stringify(cart));
      return cart;
    };

    if (productOrId && typeof productOrId === 'object') {
      return Promise.resolve({ data: proceedWithProduct(productOrId) });
    } else {
      // Fetch details from local/remote API first
      return apiClient.get(`/buyer/products/${productOrId}`).then(res => {
        const productObj = res.data?.product || res.data;
        const updated = proceedWithProduct(productObj);
        return { data: updated };
      }).catch(() => {
        const fallback = { id: productOrId, name: 'Product', price: 0 };
        const updated = proceedWithProduct(fallback);
        return { data: updated };
      });
    }
  },
  updateCartItem: (itemId, quantity) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[],"total_amount":0}');
    const item = cart.items.find(i => i._id === itemId);
    if (item) item.quantity = quantity;
    cart.total_amount = cart.items.reduce((s, i) => s + (i.product?.price || 0) * i.quantity, 0);
    localStorage.setItem('cart', JSON.stringify(cart));
    return Promise.resolve({ data: cart });
  },
  removeFromCart: (itemId) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '{"items":[],"total_amount":0}');
    cart.items = cart.items.filter(i => i._id !== itemId);
    cart.total_amount = cart.items.reduce((s, i) => s + (i.product?.price || 0) * i.quantity, 0);
    localStorage.setItem('cart', JSON.stringify(cart));
    return Promise.resolve({ data: cart });
  },
  clearCart: () => {
    const cleared = { items: [], total_amount: 0 };
    localStorage.setItem('cart', JSON.stringify(cleared));
    return Promise.resolve({ data: cleared });
  },
  
  // Orders — fast fetch with graceful fallback
  createOrder: (data) => apiClient.post('/buyer/orders', data),
  getOrders: (page = 1, limit = 20) => {
    const cachedOrders = JSON.parse(localStorage.getItem('buyer_orders_cache') || 'null');
    return apiClient.get('/buyer/orders', { params: { page, limit } }).then(res => {
      const orders = res.data?.orders || (Array.isArray(res.data) ? res.data : []);
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
  checkout: (data) => apiClient.post('/orders/checkout', data),
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
  sendNotification: (data) => apiClient.post('/admin/notifications', data),
  getUsers: (page = 1, limit = 20, filters = {}) =>
    apiClient.get('/admin/users', { params: { page, limit, ...filters } }),
  getUserDetail: (id) => safeGet(`/admin/users/${id}`, {}),
  suspendUser: (id, role) => apiClient.post(`/admin/users/${id}/suspend`, { role })
    .catch(() => ({ data: { message: 'Suspend not available' } })),
  activateUser: (id, role) => apiClient.post(`/admin/users/${id}/activate`, { role })
    .catch(() => ({ data: { message: 'Activate not available' } })),
  deleteUser: (id, role) => apiClient.post(`/admin/users/${id}/delete`, { role }),
  
  // Farmer Verification — doesn't exist
  getPendingFarmers: () => safeGet('/admin/farmers/pending-verification', []),
  verifyFarmer: (id) => apiClient.post(`/admin/farmers/${id}/verify`)
    .catch(() => ({ data: { message: 'Verification not available' } })),
  rejectFarmer: (id, reason) => apiClient.post(`/admin/farmers/${id}/reject`, { reason })
    .catch(() => ({ data: { message: 'Rejection not available' } })),
  
  // Product Approval — use /products endpoint (deployed backend)
  getAllProducts: (status) =>
    apiClient.get('/admin/products/all', { params: status ? { status } : {} }).then(res => {
      const products = res.data?.products || (Array.isArray(res.data) ? res.data : []);
      return { data: products };
    }),
  getPendingProducts: () => apiClient.get('/admin/products/pending-approval'),
  approveProduct: (id) => apiClient.post(`/admin/products/${id}/approve`),
  rejectProduct: (id, reason) => apiClient.post(`/admin/products/${id}/reject`, { reason }),
  
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

  // Platform Settings — GST, Platform Fee, Delivery Fee
  getPlatformSettings: () => apiClient.get('/admin/settings').catch(() => {
    // Backend API not deployed yet — read from localStorage (admin saves fees here)
    try {
      const stored = JSON.parse(localStorage.getItem('sf_admin_fees') || '{}');
      if (stored.gstPercent !== undefined) {
        return {
          data: {
            gst_percent: stored.gstPercent ?? 0,
            platform_percent: stored.platformPercent ?? 0,
            delivery_flat: stored.deliveryFlat ?? 0,
            free_delivery_threshold: stored.freeDeliveryThreshold ?? 500,
          }
        };
      }
    } catch {}
    // Ultimate fallback if nothing in localStorage either
    return { data: { gst_percent: 0, platform_percent: 0, delivery_flat: 0, free_delivery_threshold: 500 } };
  }),
  updatePlatformSettings: (data) => adminRequest('put', '/admin/settings', data),
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
    if (!token) return null;
    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch {
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

// ============================================================================
// CHECKOUT & PAYMENT APIs — Zomato-like order flow
// ============================================================================

export const checkoutAPI = {
  // Order calculation
  calculate: (data) => apiClient.post('/checkout/calculate', data),
  
  // Order creation
  createOrder: (data) => apiClient.post('/checkout/create-order', data),
  
  // Razorpay
  createRazorpayOrder: (data) => apiClient.post('/checkout/razorpay-order', data),
  verifyPayment: (data) => apiClient.post('/checkout/verify-payment', data),
  verifyUpiPayment: (data) => apiClient.post('/checkout/verify-upi', data),
  
  // Stripe
  createStripeSession: (data) => apiClient.post('/checkout/create-stripe-session', data),
  verifyStripe: (data) => apiClient.post('/checkout/verify-stripe', data),
  
  // Buyer orders
  getOrders: () => apiClient.get('/checkout/orders'),
  getOrderDetail: (id) => apiClient.get(`/checkout/orders/${id}`),
  cancelOrder: (id, reason) => apiClient.post(`/checkout/orders/${id}/cancel`, { reason }),
  
  // Farmer orders
  getFarmerOrders: () => apiClient.get('/checkout/farmer-orders'),
  acceptOrder: (id) => apiClient.post(`/checkout/farmer-orders/${id}/accept`),
  rejectOrder: (id, reason) => apiClient.post(`/checkout/farmer-orders/${id}/reject`, { reason }),
  updateStatus: (id, status) => apiClient.post(`/checkout/farmer-orders/${id}/status`, { status }),
  collectCash: (id) => apiClient.post(`/checkout/farmer-orders/${id}/collect-cash`),
  
  // Wallet
  getWallet: () => apiClient.get('/checkout/wallet'),
  getWalletTransactions: () => apiClient.get('/checkout/wallet/transactions'),
  
  // Addresses
  getAddresses: () => apiClient.get('/checkout/addresses'),
  saveAddress: (data) => apiClient.post('/checkout/addresses', data),
  
  // Admin
  getAdminDashboard: () => apiClient.get('/checkout/admin/dashboard'),
};

export default apiClient;
