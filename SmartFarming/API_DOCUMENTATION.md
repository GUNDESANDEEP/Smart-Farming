# Smart Farm Marketplace - Backend API Documentation

## Base URL
```
http://localhost:5000/api
```

## Response Format
All API responses follow this format:
```json
{
  "success": true,
  "data": {},
  "message": "Success message"
}
```

## Error Response
```json
{
  "success": false,
  "error": "Error message",
  "status": 400
}
```

---

## Authentication Endpoints

### 1. Farmer Login
```
POST /api/auth/farmer-login
Content-Type: application/json

{
  "email": "farmer@example.com",
  "password": "password123"
}

Response:
{
  "success": true,
  "data": {
    "token": "jwt_token",
    "user": {
      "id": 1,
      "name": "John Farmer",
      "email": "farmer@example.com",
      "role": "farmer"
    }
  }
}
```

### 2. Buyer Login
```
POST /api/buyer-auth/login
Content-Type: application/json

{
  "phone": "9876543210",
  "password": "password123"
}

Response:
{
  "success": true,
  "data": {
    "token": "jwt_token",
    "user": {
      "id": 2,
      "name": "Jane Buyer",
      "phone": "9876543210",
      "role": "buyer"
    }
  }
}
```

### 3. Admin Login
```
POST /api/admin-auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "password123"
}

Response: Same as farmer login
```

### 4. Send OTP
```
POST /api/auth/send-otp
Content-Type: application/json

{
  "phone": "9876543210"
}

Response:
{
  "success": true,
  "message": "OTP sent to phone number"
}
```

### 5. Verify OTP
```
POST /api/auth/verify-otp
Content-Type: application/json

{
  "phone": "9876543210",
  "otp": "123456"
}

Response:
{
  "success": true,
  "data": {
    "token": "jwt_token",
    "user": {...}
  }
}
```

### 6. Farmer Signup
```
POST /api/auth/farmer-signup
Content-Type: application/json

{
  "name": "John Farmer",
  "email": "farmer@example.com",
  "phone": "9876543210",
  "password": "password123",
  "location": "Karnataka",
  "farmName": "Green Fields Farm",
  "farmSize": 50,
  "farmSizeUnit": "acres"
}

Response:
{
  "success": true,
  "data": {
    "token": "jwt_token",
    "user": {...}
  }
}
```

### 7. Buyer Signup
```
POST /api/buyer-auth/signup
Content-Type: application/json

{
  "name": "Jane Buyer",
  "email": "buyer@example.com",
  "phone": "9876543210",
  "password": "password123",
  "location": "Bangalore"
}

Response: Same as farmer signup
```

---

## Farmer APIs

### 1. Get Farmer Profile
```
GET /api/farmer/profile
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "userId": 1,
    "farmName": "Green Fields Farm",
    "farmLocation": "Karnataka",
    "averageRating": 4.5,
    "totalReviews": 150,
    "totalSales": 500,
    "totalEarnings": 125000
  }
}
```

### 2. Update Farmer Profile
```
PUT /api/farmer/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "farmName": "Updated Farm Name",
  "bankAccountNumber": "1234567890",
  "ifscCode": "SBIN0001234"
}

Response:
{
  "success": true,
  "data": {...}
}
```

### 3. Get Farmer Products
```
GET /api/farmer/products
Authorization: Bearer {token}
Query params: ?page=1&limit=10&status=approved

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Fresh Tomatoes",
      "price": 40,
      "priceUnit": "kg",
      "stock": 1000,
      "status": "approved",
      "imageUrl": "https://..."
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25
  }
}
```

### 4. Add Product
```
POST /api/farmer/products
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Fresh Tomatoes",
  "description": "Organic, pesticide-free tomatoes",
  "category": "Vegetables",
  "subCategory": "Tomatoes",
  "price": 40,
  "priceUnit": "kg",
  "stockQuantity": 1000,
  "unitOfMeasure": "kg",
  "harvestDate": "2024-06-01",
  "expiryDate": "2024-06-10",
  "organic": true,
  "pesticineFree": true,
  "certificationUrl": "https://..."
}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Fresh Tomatoes",
    "status": "pending"
  }
}
```

### 5. Update Product
```
PUT /api/farmer/products/:id
Authorization: Bearer {token}
Content-Type: application/json

{
  "price": 45,
  "stockQuantity": 900
}

Response: {...}
```

### 6. Delete Product
```
DELETE /api/farmer/products/:id
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Product deleted"
}
```

### 7. Get Farmer Orders
```
GET /api/farmer/orders
Authorization: Bearer {token}
Query params: ?status=pending&page=1

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "orderNumber": "ORD-001",
      "buyerName": "Jane Buyer",
      "totalAmount": 1500,
      "status": "pending",
      "createdAt": "2024-06-01T10:00:00Z"
    }
  ]
}
```

### 8. Update Order Status
```
PUT /api/farmer/orders/:id/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "packed"
}

Response: {...}
```

### 9. Get Farmer Earnings
```
GET /api/farmer/earnings
Authorization: Bearer {token}
Query params: ?period=month

Response:
{
  "success": true,
  "data": {
    "total": 250000,
    "thisMonth": 25000,
    "pending": 5000,
    "rating": 4.5,
    "breakdown": {
      "completed": 245000,
      "pending": 5000,
      "refunded": 0
    }
  }
}
```

### 10. Get Farmer Analytics
```
GET /api/farmer/analytics
Authorization: Bearer {token}
Query params: ?period=month

Response:
{
  "success": true,
  "data": {
    "totalSales": 50,
    "totalRevenue": 50000,
    "averageOrderValue": 1000,
    "topProducts": [...],
    "salesTrend": [...]
  }
}
```

---

## Buyer APIs

### 1. Get Buyer Profile
```
GET /api/buyer/profile
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "userId": 2,
    "phoneVerified": true,
    "loyaltyPoints": 500,
    "totalSpent": 45000,
    "totalOrders": 25
  }
}
```

### 2. Get Products (with filters)
```
GET /api/buyer/products
Authorization: Bearer {token}
Query params: ?category=Vegetables&minPrice=0&maxPrice=100&page=1&limit=20

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Fresh Tomatoes",
      "farmer": "Green Fields Farm",
      "price": 40,
      "priceUnit": "kg",
      "imageUrl": "https://...",
      "rating": 4.5,
      "reviews": 150,
      "organic": true
    }
  ],
  "pagination": {...}
}
```

### 3. Search Products
```
GET /api/buyer/products/search
Authorization: Bearer {token}
Query params: ?q=tomato&location=Karnataka

Response: Same as get products
```

### 4. Get Product Details
```
GET /api/buyer/products/:id
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Fresh Tomatoes",
    "description": "...",
    "price": 40,
    "farmer": {...},
    "reviews": [...],
    "images": [...]
  }
}
```

### 5. Get Shopping Cart
```
GET /api/buyer/cart
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "items": [
      {
        "id": 1,
        "productId": 1,
        "productName": "Fresh Tomatoes",
        "quantity": 5,
        "price": 40,
        "subtotal": 200
      }
    ],
    "total": 200
  }
}
```

### 6. Add to Cart
```
POST /api/buyer/cart/add
Authorization: Bearer {token}
Content-Type: application/json

{
  "productId": 1,
  "quantity": 5
}

Response: {...}
```

### 7. Update Cart Item
```
PUT /api/buyer/cart/update
Authorization: Bearer {token}
Content-Type: application/json

{
  "productId": 1,
  "quantity": 10
}

Response: {...}
```

### 8. Remove from Cart
```
DELETE /api/buyer/cart/:productId
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Item removed from cart"
}
```

### 9. Get Orders
```
GET /api/buyer/orders
Authorization: Bearer {token}
Query params: ?status=delivered&page=1

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "orderNumber": "ORD-001",
      "items": [...],
      "totalAmount": 1500,
      "status": "delivered",
      "createdAt": "2024-06-01T10:00:00Z"
    }
  ]
}
```

### 10. Create Order
```
POST /api/buyer/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "deliveryAddressId": 1,
  "paymentMethod": "razorpay",
  "notes": "Deliver in morning"
}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "orderNumber": "ORD-001",
    "paymentLink": "https://razorpay.com/..."
  }
}
```

### 11. Track Order
```
GET /api/buyer/orders/:id/tracking
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "status": "shipped",
    "location": "Bangalore Distribution Center",
    "estimatedDelivery": "2024-06-05",
    "timeline": [...]
  }
}
```

### 12. Submit Review
```
POST /api/buyer/orders/:orderId/review
Authorization: Bearer {token}
Content-Type: application/json

{
  "rating": 5,
  "reviewText": "Excellent quality tomatoes!",
  "images": ["https://..."]
}

Response:
{
  "success": true,
  "data": {...}
}
```

### 13. Get Wishlist
```
GET /api/buyer/wishlist
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "productId": 1,
      "productName": "Fresh Tomatoes",
      "price": 40,
      "imageUrl": "https://..."
    }
  ]
}
```

### 14. Add to Wishlist
```
POST /api/buyer/wishlist
Authorization: Bearer {token}
Content-Type: application/json

{
  "productId": 1
}

Response: {...}
```

---

## Admin APIs

### 1. Get Dashboard Stats
```
GET /api/admin/dashboard
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "totalUsers": 1000,
    "totalFarmers": 300,
    "totalBuyers": 700,
    "totalOrders": 5000,
    "totalRevenue": 1000000,
    "pendingProducts": 50,
    "disputes": 10
  }
}
```

### 2. Get Users List
```
GET /api/admin/users
Authorization: Bearer {token}
Query params: ?role=farmer&status=active&page=1

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Farmer",
      "email": "farmer@example.com",
      "role": "farmer",
      "status": "active",
      "createdAt": "2024-01-01"
    }
  ],
  "pagination": {...}
}
```

### 3. Update User
```
PUT /api/admin/users/:id
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "suspended"
}

Response: {...}
```

### 4. Get Pending Products
```
GET /api/admin/products/pending
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Fresh Tomatoes",
      "farmerName": "John Farmer",
      "price": 40,
      "imageUrl": "https://..."
    }
  ]
}
```

### 5. Approve Product
```
POST /api/admin/products/:id/approve
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Product approved"
}
```

### 6. Reject Product
```
POST /api/admin/products/:id/reject
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "Product images are not clear"
}

Response:
{
  "success": true,
  "message": "Product rejected"
}
```

### 7. Get Orders (Admin View)
```
GET /api/admin/orders
Authorization: Bearer {token}
Query params: ?status=pending&page=1

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "orderNumber": "ORD-001",
      "farmerName": "John Farmer",
      "buyerName": "Jane Buyer",
      "totalAmount": 1500,
      "status": "pending"
    }
  ]
}
```

### 8. Get Analytics
```
GET /api/admin/analytics
Authorization: Bearer {token}
Query params: ?period=month

Response:
{
  "success": true,
  "data": {
    "totalOrders": 500,
    "totalRevenue": 500000,
    "averageOrderValue": 1000,
    "userGrowth": [...],
    "topProducts": [...],
    "salesTrend": [...]
  }
}
```

### 9. Get AI Logs
```
GET /api/admin/ai-logs
Authorization: Bearer {token}
Query params: ?model=crop_recommendation&page=1

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "modelName": "crop_recommendation",
      "processingTimeMs": 234,
      "accuracy": 0.95,
      "createdAt": "2024-06-01T10:00:00Z"
    }
  ]
}
```

---

## Common APIs

### 1. Weather Data
```
GET /api/weather
Query params: ?location=Karnataka

Response:
{
  "success": true,
  "data": {
    "location": "Karnataka",
    "temperature": { "min": 20, "max": 35 },
    "humidity": 65,
    "rainfall": 10,
    "windSpeed": 12,
    "forecast": [...]
  }
}
```

### 2. Crop Recommendations
```
GET /api/ai/crop-recommendations
Authorization: Bearer {token}
Query params: ?location=Karnataka&season=monsoon

Response:
{
  "success": true,
  "data": {
    "recommendedCrops": ["Rice", "Sugarcane", "Coconut"],
    "reasoning": "Based on monsoon season and soil type",
    "confidenceScore": 0.92
  }
}
```

### 3. Price Forecasting
```
GET /api/ai/price-forecast/:crop
Query params: ?location=Karnataka

Response:
{
  "success": true,
  "data": {
    "crop": "Tomato",
    "location": "Karnataka",
    "forecastedPrice": 45,
    "confidenceScore": 0.88,
    "trend": "upward"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## Authentication Headers

All protected endpoints require:
```
Authorization: Bearer {jwt_token}
```

---

## Rate Limiting

- 100 requests per minute per IP for non-authenticated endpoints
- 500 requests per minute per user for authenticated endpoints

---

## Pagination

All list endpoints support:
- `page` (default: 1)
- `limit` (default: 20, max: 100)

Response includes:
```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## Support

For API support, email api-support@smartfarm.com
