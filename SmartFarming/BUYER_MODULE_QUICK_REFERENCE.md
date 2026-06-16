# 🛒 Buyer Module - Quick Reference Guide

## 🚀 Quick Start

### Backend Setup
```bash
# 1. Add routes to app.py
from routes.buyer_auth import buyer_auth_bp
from routes.buyer_profile import buyer_profile_bp
from routes.buyer_products import buyer_products_bp
from routes.buyer_cart import buyer_cart_bp
from routes.buyer_orders import buyer_orders_bp
from routes.buyer_payments import buyer_payments_bp
from routes.buyer_reviews import buyer_reviews_bp

app.register_blueprint(buyer_auth_bp)
app.register_blueprint(buyer_profile_bp)
app.register_blueprint(buyer_products_bp)
app.register_blueprint(buyer_cart_bp)
app.register_blueprint(buyer_orders_bp)
app.register_blueprint(buyer_payments_bp)
app.register_blueprint(buyer_reviews_bp)

# 2. Import database schema
mysql -u root -p < database/buyer_schema.sql

# 3. Start server
python app.py
```

---

## 📱 Frontend API Endpoints by Screen

### Phone Screen
```javascript
POST /api/buyer-auth/send-otp
POST /api/buyer-auth/verify-otp
```

### Signup Screen
```javascript
POST /api/buyer-auth/signup
```

### Login Screen
```javascript
POST /api/buyer-auth/login
```

### Dashboard Screen
```javascript
GET /api/buyer/dashboard        // Get dashboard with recommendations
GET /api/products/trending      // Get trending products
GET /api/products/nearby-farmers // Get nearby farmers
```

### Product Search Screen
```javascript
GET /api/products?search=...    // Search products
GET /api/products/category/{category} // Products by category
GET /api/products/{id}          // Product details
```

### Cart Screen
```javascript
GET /api/cart/                  // Get all cart items
POST /api/cart/add              // Add to cart
PUT /api/cart/{product_id}      // Update quantity
DELETE /api/cart/{product_id}   // Remove from cart
GET /api/cart/summary           // Get cart totals
```

### Checkout Screen
```javascript
GET /api/buyer/addresses        // Get saved addresses
POST /api/buyer/add-address     // Add new address
GET /api/payments/methods       // Get payment methods
POST /api/payments/{id}/create-razorpay // Init payment
POST /api/orders/               // Create order
```

### Orders Screen
```javascript
GET /api/orders/                // Get all orders
GET /api/orders/{id}            // Order details
```

### Order Tracking Screen
```javascript
GET /api/orders/{id}/track      // Live tracking
```

### Review Screen
```javascript
POST /api/reviews/{order_id}    // Submit review
GET /api/reviews/product/{id}   // Product reviews
GET /api/reviews/farmer/{id}    // Farmer reviews
```

---

## 🔐 Authentication Pattern

```javascript
// All protected endpoints require JWT in header
Authorization: Bearer {access_token}

// Token received from:
POST /api/buyer-auth/signup
POST /api/buyer-auth/login

// Response structure
{
  "success": true,
  "access_token": "eyJ0eXAi...",
  "buyer_id": 1,
  "first_name": "Ramesh"
}
```

---

## 📊 Response Format Standard

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message explaining what went wrong"
}
```

### Paginated Response
```json
{
  "success": true,
  "items": [...],
  "total": 156,
  "page": 1,
  "pages": 8,
  "limit": 20
}
```

---

## 🎨 Data Models

### Buyer Profile
```javascript
{
  buyer_id: number,
  phone: string,
  email: string,
  first_name: string,
  last_name: string,
  location: string,
  city: string,
  state: string,
  pincode: string,
  created_at: datetime
}
```

### Product (from buyer perspective)
```javascript
{
  product_id: number,
  name: string,
  category: string,
  price: number,
  quantity: number,
  rating: number,
  reviews_count: number,
  farmer_id: number,
  farmer_name: string,
  location: string,
  distance_km: number,
  images: []
}
```

### Cart Item
```javascript
{
  cart_id: number,
  product_id: number,
  product_name: string,
  quantity: number,
  unit_price: number,
  total_price: number,
  farmer_id: number,
  farmer_name: string
}
```

### Order
```javascript
{
  order_id: number,
  product_name: string,
  farmer_name: string,
  quantity: number,
  total_amount: number,
  status: "pending|accepted|in_transit|delivered|cancelled",
  payment_status: "pending|completed|failed|refunded",
  delivery_address: string,
  created_at: datetime
}
```

### Review
```javascript
{
  review_id: number,
  product_rating: number,     // 1-5
  product_review: string,
  farmer_rating: number,       // 1-5
  farmer_review: string,
  created_at: datetime
}
```

### Payment
```javascript
{
  payment_id: number,
  order_id: number,
  amount: number,
  payment_method: "card|upi|cod|netbanking",
  status: "pending|completed|failed|refunded",
  transaction_id: string,
  payment_gateway: "razorpay|cash|upi",
  created_at: datetime
}
```

---

## 🔄 User Flows

### Sign Up Flow
```
1. Enter Phone → 2. Verify OTP → 3. Create Account → Dashboard
```

### Search to Purchase Flow
```
1. Search/Browse → 2. View Details → 3. Add to Cart → 4. Checkout → 5. Pay → 6. Order Placed
```

### Order Tracking Flow
```
1. View Orders → 2. Select Order → 3. View Tracking → 4. Receive → 5. Review
```

---

## ⚙️ Database Tables Reference

### buyers
- User profiles for buyers
- 20 columns
- Unique: phone, email
- Indexed: phone, email, location

### cart
- Shopping cart items per buyer
- 7 columns
- Foreign keys: buyer_id, product_id, farmer_id
- Unique: buyer_id + product_id

### payments
- Payment transaction records
- 10 columns
- Foreign keys: order_id, buyer_id
- Unique: transaction_id
- Indexed: order_id, status, created_at

### orders (modified)
- Added buyer_id, delivery_address, buyer_phone, buyer_location, payment_status
- Now links both farmer and buyer

### order_tracking
- Live delivery tracking
- 11 columns
- Real-time location updates
- Unique: order_id

### buyer_reviews
- Separate product and farmer ratings
- 10 columns
- Unique: order_id (one review per order)

### return_requests
- Return and refund management
- 8 columns
- Status: requested|approved|rejected|refunded

### buyer_addresses
- Multiple delivery addresses per buyer
- 11 columns
- Types: home, work, other
- Location coordinates for sorting

---

## 🧪 Testing with Postman

### Sign Up Test
```
1. POST /api/buyer-auth/send-otp
   {"phone":"9876543200","type":"signup"}
   ← Get OTP

2. POST /api/buyer-auth/verify-otp
   {"phone":"9876543200","otp":"123456"}
   ← Get verification_token

3. POST /api/buyer-auth/signup
   {
     "phone":"9876543200",
     "first_name":"Ramesh",
     "email":"ramesh@test.com",
     "password":"Secure123!",
     "location":"Hyderabad"
   }
   ← Get access_token
```

### Product Search Test
```
GET /api/products?
  search=tomato&
  category=vegetables&
  min_price=30&
  max_price=50&
  page=1&
  limit=10
```

### Create Order Test
```
1. POST /api/cart/add
   {"product_id":1,"quantity":2}

2. POST /api/orders
   {
     "address_id":1,
     "payment_method":"razorpay"
   }
   ← Get order_id

3. POST /api/payments/{order_id}/create-razorpay
   ← Get razorpay_order_id
```

---

## 🛠️ Common Integration Patterns

### Axios Instance
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000
});

// Add token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
    }
    return Promise.reject(error);
  }
);

export default api;
```

### API Service Methods
```javascript
export const buyerAPI = {
  // Auth
  sendOTP: (phone) => api.post('/buyer-auth/send-otp', {phone}),
  verifyOTP: (phone, otp) => api.post('/buyer-auth/verify-otp', {phone, otp}),
  signup: (data) => api.post('/buyer-auth/signup', data),
  login: (phone, password) => api.post('/buyer-auth/login', {phone, password}),
  
  // Products
  searchProducts: (params) => api.get('/products', {params}),
  getProduct: (id) => api.get(`/products/${id}`),
  getTrending: () => api.get('/products/trending'),
  getNearbyFarmers: (lat, lon) => api.get('/products/nearby-farmers', {params: {latitude: lat, longitude: lon}}),
  
  // Cart
  getCart: () => api.get('/cart/'),
  addToCart: (product_id, quantity) => api.post('/cart/add', {product_id, quantity}),
  updateCart: (product_id, quantity) => api.put(`/cart/${product_id}`, {quantity}),
  removeFromCart: (product_id) => api.delete(`/cart/${product_id}`),
  
  // Orders
  createOrder: (address_id, payment_method) => api.post('/orders/', {address_id, payment_method}),
  getOrders: (page = 1) => api.get('/orders/', {params: {page}}),
  getOrderDetails: (id) => api.get(`/orders/${id}`),
  trackOrder: (id) => api.get(`/orders/${id}/track`),
  
  // Reviews
  submitReview: (order_id, data) => api.post(`/reviews/${order_id}`, data),
  getProductReviews: (id) => api.get(`/reviews/product/${id}`)
};
```

---

## 🔍 Debugging Tips

### Check Token
```javascript
const token = localStorage.getItem('access_token');
console.log('Token:', token);
```

### Log API Responses
```javascript
api.interceptors.response.use(
  response => {
    console.log('API Response:', response.data);
    return response;
  },
  error => {
    console.error('API Error:', error.response?.data);
    return Promise.reject(error);
  }
);
```

### Common Errors
```
401 Unauthorized → Token missing or expired
404 Not Found → Resource doesn't exist
400 Bad Request → Invalid request data
409 Conflict → Resource already exists (e.g., duplicate email)
500 Server Error → Backend issue
```

---

## 📈 Performance Tips

1. **Pagination**: Always paginate list results
2. **Caching**: Cache product data & search results
3. **Lazy Loading**: Load images as user scrolls
4. **Debounce**: Debounce search requests
5. **Offline Support**: Cache orders & reviews
6. **Compression**: Enable gzip on server

---

## 🔐 Security Checklist

- [ ] Store JWT in secure storage (not localStorage in production)
- [ ] Send tokens only via HTTPS
- [ ] Implement token refresh mechanism
- [ ] Validate input before sending to API
- [ ] Never expose sensitive data in logs
- [ ] Clear cache on logout
- [ ] Handle 401 errors by redirecting to login
- [ ] Use HTTPS for all API calls

---

## 📚 Additional Resources

- [Buyer Module Plan](./BUYER_MODULE_PLAN.md) - Architecture details
- [Buyer Module Implementation](./BUYER_MODULE_IMPLEMENTATION.md) - Complete endpoint reference
- [Database Schema](./database/buyer_schema.sql) - SQL implementation
- [Route Files](./backend/routes/) - Source code for all endpoints

---

**Ready to build the frontend!** 🎉
