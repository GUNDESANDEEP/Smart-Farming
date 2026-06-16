# 🛒 Buyer Module - Architecture & Implementation Plan

## 📋 Overview

The Buyer Module allows customers to:
- Register and authenticate
- Search and discover products from farmers
- Add products to cart
- Place orders with multiple payment options
- Track deliveries in real-time
- Rate and review products/farmers

---

## 🗄️ Database Schema Changes

### New Tables Required

#### 1. **buyers** (Similar to farmers, but different structure)
```sql
CREATE TABLE buyers (
  buyer_id INT PRIMARY KEY AUTO_INCREMENT,
  phone VARCHAR(10) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50),
  password_hash VARCHAR(255) NOT NULL,
  location VARCHAR(100),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  address TEXT,
  city VARCHAR(50),
  state VARCHAR(50),
  pincode VARCHAR(6),
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_phone (phone),
  INDEX idx_email (email)
);
```

#### 2. **cart** (Shopping cart items)
```sql
CREATE TABLE cart (
  cart_id INT PRIMARY KEY AUTO_INCREMENT,
  buyer_id INT NOT NULL,
  product_id INT NOT NULL,
  farmer_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  price_at_addition DECIMAL(10, 2),
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id),
  UNIQUE KEY unique_cart_item (buyer_id, product_id),
  INDEX idx_buyer (buyer_id)
);
```

#### 3. **payments** (Payment records)
```sql
CREATE TABLE payments (
  payment_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  payment_method ENUM('upi', 'card', 'cod') NOT NULL,
  status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
  transaction_id VARCHAR(100) UNIQUE,
  payment_gateway VARCHAR(50), -- 'razorpay', 'stripe', etc.
  gateway_response JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_buyer (buyer_id),
  INDEX idx_status (status)
);
```

#### 4. **cart** → **orders** (Modify existing orders table)
```sql
-- Add buyer_id to existing orders table
ALTER TABLE orders ADD COLUMN buyer_id INT AFTER farmer_id;
ALTER TABLE orders ADD FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id);
ALTER TABLE orders ADD COLUMN delivery_address TEXT;
ALTER TABLE orders ADD COLUMN buyer_phone VARCHAR(10);
ALTER TABLE orders ADD COLUMN buyer_location VARCHAR(100);
```

#### 5. **order_tracking** (Live tracking)
```sql
CREATE TABLE order_tracking (
  tracking_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  status ENUM('pending', 'accepted', 'packed', 'in_transit', 'delivered', 'cancelled') DEFAULT 'pending',
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  delivery_boy_name VARCHAR(100),
  delivery_boy_phone VARCHAR(10),
  estimated_delivery_time DATETIME,
  actual_delivery_time DATETIME,
  notes TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_status (status)
);
```

#### 6. **buyer_reviews** (Separate from product reviews)
```sql
CREATE TABLE buyer_reviews (
  review_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  product_id INT NOT NULL,
  farmer_id INT NOT NULL,
  product_rating INT CHECK (product_rating >= 1 AND product_rating <= 5),
  farmer_rating INT CHECK (farmer_rating >= 1 AND farmer_rating <= 5),
  product_review TEXT,
  farmer_review TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  INDEX idx_buyer (buyer_id),
  INDEX idx_farmer (farmer_id),
  INDEX idx_product (product_id)
);
```

#### 7. **return_requests** (Return & refund)
```sql
CREATE TABLE return_requests (
  return_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  reason VARCHAR(255) NOT NULL,
  description TEXT,
  status ENUM('requested', 'approved', 'rejected', 'refunded') DEFAULT 'requested',
  refund_amount DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_buyer (buyer_id)
);
```

---

## 🔌 Backend API Routes Structure

### 1. **Buyer Authentication** (`/api/buyer-auth`)
```
POST   /send-otp              → Send OTP for signup/login
POST   /verify-otp            → Verify OTP code
POST   /signup                → Create buyer account
POST   /login                 → Login with email/phone
POST   /logout                → Logout
POST   /forgot-password       → Password reset via OTP
PUT    /verify-token          → Check token validity
```

### 2. **Buyer Profile** (`/api/buyer`)
```
GET    /profile               → Get buyer profile
PUT    /profile               → Update profile
POST   /add-address           → Add delivery address
GET    /addresses             → Get all addresses
PUT    /address/{id}          → Update address
DELETE /address/{id}          → Delete address
GET    /dashboard             → Dashboard with recommendations
```

### 3. **Product Search & Discovery** (`/api/products`)
```
GET    /                      → Search products with filters
GET    /trending              → Get trending products
GET    /nearby-farmers        → Get farmers by location
GET    /farmer/{farmer_id}    → Get all products from farmer
GET    /{product_id}          → Product details with farmer info
GET    /category/{category}   → Products by category
GET    /search?q=...          → Full-text search
```

### 4. **Shopping Cart** (`/api/cart`)
```
GET    /                      → Get cart items
POST   /add                   → Add to cart
PUT    /{product_id}          → Update quantity
DELETE /{product_id}          → Remove from cart
DELETE /                      → Clear cart
GET    /summary               → Cart totals & tax
```

### 5. **Orders** (`/api/orders`)
```
POST   /                      → Create order from cart
GET    /                      → Get buyer's orders
GET    /{order_id}            → Order details
PUT    /{order_id}/cancel     → Cancel order
GET    /{order_id}/track      → Live tracking
POST   /{order_id}/return     → Request return
GET    /{order_id}/return     → Return status
```

### 6. **Payments** (`/api/payments`)
```
POST   /{order_id}/verify-cod → Verify COD capability
POST   /{order_id}/create-razorpay → Create Razorpay order
POST   /{order_id}/verify-razorpay  → Verify payment
GET    /{order_id}/status     → Payment status
POST   /{order_id}/refund     → Request refund
```

### 7. **Reviews & Ratings** (`/api/reviews`)
```
POST   /{order_id}            → Submit review & rating
GET    /product/{product_id}  → Get product reviews
GET    /farmer/{farmer_id}    → Get farmer reviews
PUT    /{review_id}           → Edit review
DELETE /{review_id}           → Delete review
```

---

## 📱 Frontend Screens

### Authentication (3 screens)
1. **BuyerPhoneScreen** - Phone entry with validation
2. **BuyerOTPScreen** - OTP verification (6 digits)
3. **BuyerSignupScreen** - Account creation form

### Discovery (4 screens)
4. **BuyerDashboardScreen** - Home with recommendations
5. **ProductSearchScreen** - Search with filters
6. **ProductListScreen** - Category or search results
7. **ProductDetailScreen** - Single product with farmer info

### Shopping (3 screens)
8. **CartScreen** - Shopping cart items
9. **CheckoutScreen** - Delivery & payment info
10. **OrderConfirmationScreen** - Order placed confirmation

### Orders (3 screens)
11. **OrdersScreen** - List of all buyer's orders
12. **OrderTrackingScreen** - Live tracking map
13. **OrderDetailsScreen** - Full order info

### Reviews (2 screens)
14. **ReviewProductScreen** - Rate and review
15. **OrderHistoryScreen** - Past orders for reviews

---

## 🎨 UI/UX Differences from Farmer Module

### Color Scheme (Buyer Focused)
- **Primary**: #2196F3 (Blue - trust, discovery)
- **Secondary**: #4CAF50 (Green - nature/farmers)
- **Accent**: #FF9800 (Orange - offers/deals)

### Key Features
- **Personalized**: Show trending for user
- **Location-based**: Nearby farmers and same-day delivery
- **Social proof**: Reviews and ratings prominent
- **Payment variety**: Multiple payment options
- **Real-time**: Live tracking with map
- **Easy returns**: Return management system

---

## 📊 API Response Examples

### Dashboard Response
```json
{
  "success": true,
  "dashboard": {
    "personalized_recommendations": [
      {
        "product_id": 1,
        "name": "Organic Tomatoes",
        "farmer_name": "Ravi Kumar",
        "distance": "2.5 km",
        "price": 40,
        "rating": 4.5,
        "reason": "Similar to your purchases"
      }
    ],
    "trending_products": [
      {
        "product_id": 5,
        "name": "Fresh Milk",
        "orders_this_week": 245,
        "trending_score": 9.8
      }
    ],
    "nearby_farmers": [
      {
        "farmer_id": 1,
        "name": "Ravi Kumar",
        "location": "Hyderabad",
        "distance": "2.5 km",
        "products_count": 12,
        "rating": 4.6
      }
    ]
  }
}
```

### Cart Response
```json
{
  "success": true,
  "cart": {
    "items": [
      {
        "cart_id": 1,
        "product_id": 1,
        "product_name": "Organic Tomatoes",
        "farmer_name": "Ravi Kumar",
        "farmer_id": 1,
        "quantity": 2,
        "unit_price": 40,
        "total_price": 80
      }
    ],
    "summary": {
      "subtotal": 240,
      "tax": 24,
      "delivery_fee": 50,
      "total": 314
    }
  }
}
```

### Order Response
```json
{
  "success": true,
  "order": {
    "order_id": 101,
    "status": "in_transit",
    "buyer_name": "Ramesh",
    "farmer_name": "Ravi Kumar",
    "product_name": "Organic Tomatoes",
    "quantity": 2,
    "total_amount": 314,
    "delivery_address": "123 Main St, Hyderabad",
    "estimated_delivery": "2026-06-02 06:00 PM",
    "tracking": {
      "status": "in_transit",
      "delivery_boy_name": "Rajesh",
      "delivery_boy_phone": "9876543210",
      "latitude": 17.3850,
      "longitude": 78.4867
    }
  }
}
```

---

## 🔄 User Journey Map

### Sign Up to Purchase Flow
```
1. BuyerPhoneScreen
   ↓
2. BuyerOTPScreen (Verify OTP)
   ↓
3. BuyerSignupScreen (Create account)
   ↓
4. BuyerDashboardScreen (Home)
   ↓ (Browse/Search)
5. ProductSearchScreen / ProductListScreen
   ↓ (Select product)
6. ProductDetailScreen (View product & farmer)
   ↓ (Add to cart)
7. CartScreen
   ↓ (Checkout)
8. CheckoutScreen (Delivery address + payment)
   ↓ (Place order)
9. OrderConfirmationScreen
   ↓
10. OrdersScreen (View all orders)
    ↓ (Track)
11. OrderTrackingScreen (Live tracking)
    ↓
12. ReviewProductScreen (After delivery)
```

---

## 🔐 Authentication Flow

```
Buyer Registration:
Phone Entry → OTP (10 min) → Account Creation → Dashboard

Buyer Login:
Phone/Email → OTP → Dashboard

Buyer Checkout:
Cart → Address Selection → Payment Method → Verification → Order Created
```

---

## 💾 Database Statistics

### Current (Farmer Module)
- 10 tables
- 1000+ lines of SQL

### With Buyer Module
- 17 tables (7 new additions)
- 2000+ lines of SQL
- More complex relationships

---

## 📅 Implementation Phases

### Phase 1: Core Backend (Highest Priority)
- [ ] Create new database tables
- [ ] Build buyer authentication routes
- [ ] Build product search API
- [ ] Build cart management API
- [ ] Build order creation API
- [ ] Build payment verification API

### Phase 2: Frontend - Authentication (Next)
- [ ] Create buyer auth screens (3 screens)
- [ ] Test authentication flow

### Phase 3: Frontend - Discovery (Then)
- [ ] Create dashboard & search screens (4 screens)
- [ ] Integrate product search API

### Phase 4: Frontend - Shopping (Then)
- [ ] Create cart & checkout screens (3 screens)
- [ ] Integrate payment gateway

### Phase 5: Frontend - Orders & Tracking (Then)
- [ ] Create order screens (3 screens)
- [ ] Integrate live tracking

### Phase 6: Frontend - Reviews (Finally)
- [ ] Create review screens (2 screens)
- [ ] Integrate review API

### Phase 7: Documentation & Testing
- [ ] Write Buyer Module documentation
- [ ] API testing
- [ ] End-to-end testing

---

## 🚀 Success Criteria

✅ All 7 API route modules complete
✅ All 15 frontend screens complete
✅ Payment integration working
✅ Live tracking functional
✅ Reviews & ratings system working
✅ Comprehensive documentation
✅ Production-ready code

---

## 📊 Complexity Analysis

| Component | Farmer Module | Buyer Module | Complexity |
|-----------|---------------|--------------|-----------|
| Auth Routes | 8 endpoints | 7 endpoints | Similar |
| Product Routes | 6 endpoints | 7 endpoints | Similar |
| Cart | N/A | 6 endpoints | New |
| Orders | 5 endpoints | 5 endpoints | Similar |
| Payments | 1 endpoint | 4 endpoints | More complex |
| Reviews | Structure only | 5 endpoints | New |
| Tracking | Structure only | 2 endpoints | New |
| **Total** | **40+ endpoints** | **40+ endpoints** | **Similar effort** |

---

## 🎯 Key Differentiators

### Compared to Farmer Module:
- ✅ Multiple payment options (Razorpay + COD)
- ✅ Live location tracking with maps
- ✅ Product search & discovery engine
- ✅ Shopping cart management
- ✅ Return/refund system
- ✅ Dual ratings (product + farmer)
- ✅ Personalized recommendations

---

## 💡 Implementation Tips

1. **Reuse Authentication Pattern**: Copy Farmer auth, modify for buyers
2. **Reuse Cart Pattern**: Create similar to wallet balance tracking
3. **Search Implementation**: Use full-text search on products table
4. **Tracking System**: Use WebSockets for real-time updates
5. **Payment Gateway**: Use Razorpay SDK for seamless integration
6. **Location Services**: Use Google Maps API for tracking & nearby

---

## 📝 Next Steps

1. ✅ Create database schema SQL file
2. ✅ Create buyer authentication routes
3. ✅ Create product search API
4. ✅ Create cart management API
5. ✅ Create order management API
6. ✅ Create payment API
7. ✅ Create review API
8. Create buyer frontend screens (Auth → Dashboard → Search → Cart → Checkout → Orders)
9. Integrate all screens with APIs
10. Document Buyer Module completely

---

**Ready to start building the Buyer Module! 🚀**

Starting with Phase 1: Core Backend API Development
