# Smart Farmer Marketplace - Backend API

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Last Updated:** June 2026

---

## Quick Start

### 1. Database Setup (One Time)

```bash
cd backend
python init_db.py
```

This script will:
- ✓ Create MySQL database
- ✓ Import complete schema (25+ tables)
- ✓ Create admin user
- ✓ Verify all tables

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

**Required Variables:**
```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=smart_farming
JWT_SECRET_KEY=your-secret-key
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Start Backend

```bash
# Development mode
python startup.py

# Production mode
SERVER_TYPE=production python startup.py
```

Backend will be available at: **http://localhost:5000**

---

## API Endpoints

### Authentication (15 endpoints)
```
POST   /api/auth/register           - User registration
POST   /api/auth/login              - Email/password login
POST   /api/auth/firebase-login     - Google/Firebase login
POST   /api/auth/verify-email       - Verify email with OTP
POST   /api/auth/otp-login          - Request OTP login
POST   /api/auth/verify-otp-login   - Verify OTP and login
POST   /api/auth/forgot-password    - Request password reset
POST   /api/auth/reset-password     - Reset with token
POST   /api/auth/change-password    - Change password (auth required)
POST   /api/auth/refresh-token      - Refresh JWT token
POST   /api/auth/logout             - Logout
GET    /api/auth/profile            - Get profile (auth required)
PUT    /api/auth/profile            - Update profile (auth required)
GET    /api/auth/verification-status - Check verification
```

### Farmer Module (17 endpoints)
```
GET    /api/farmer/dashboard        - Dashboard statistics
POST   /api/farmer/products         - Create product
GET    /api/farmer/products         - List products
GET    /api/farmer/products/:id     - Get product details
PUT    /api/farmer/products/:id     - Update product
DELETE /api/farmer/products/:id     - Delete product
GET    /api/farmer/orders           - List orders
GET    /api/farmer/orders/:id       - Get order details
PUT    /api/farmer/orders/:id/status - Update order status
POST   /api/farmer/orders/:id/accept - Accept order
POST   /api/farmer/orders/:id/reject - Reject order
GET    /api/farmer/earnings         - Get earnings
GET    /api/farmer/transactions     - Transaction history
GET    /api/farmer/reviews          - Product reviews
GET    /api/farmer/ratings          - Farmer ratings
GET    /api/farmer/profile          - Get profile
PUT    /api/farmer/profile          - Update profile
```

### Buyer Module (17 endpoints)
```
GET    /api/buyer/products          - Browse products
GET    /api/buyer/products/:id      - Get product details
GET    /api/buyer/products/search   - Search with filters
GET    /api/buyer/cart              - Get shopping cart
POST   /api/buyer/cart/items        - Add to cart
PUT    /api/buyer/cart/items/:id    - Update cart item
DELETE /api/buyer/cart/items/:id    - Remove from cart
POST   /api/buyer/cart/clear        - Clear cart
POST   /api/buyer/orders            - Create order
GET    /api/buyer/orders            - List orders
GET    /api/buyer/orders/:id        - Get order details
POST   /api/buyer/orders/:id/cancel - Cancel order
POST   /api/buyer/payments/create   - Create Razorpay payment
POST   /api/buyer/payments/verify   - Verify payment
POST   /api/buyer/orders/:id/review - Create review
GET    /api/buyer/profile           - Get profile
PUT    /api/buyer/profile           - Update profile
```

### Admin Module (17 endpoints)
```
GET    /api/admin/dashboard         - Admin dashboard
GET    /api/admin/users             - List users
GET    /api/admin/users/:id         - Get user details
POST   /api/admin/users/:id/suspend - Suspend user
POST   /api/admin/users/:id/activate - Activate user
GET    /api/admin/farmers/pending-verification - Pending farmers
POST   /api/admin/farmers/:id/verify - Verify farmer
POST   /api/admin/farmers/:id/reject - Reject farmer
GET    /api/admin/products/pending-approval - Pending products
POST   /api/admin/products/:id/approve - Approve product
POST   /api/admin/products/:id/reject - Reject product
GET    /api/admin/analytics/revenue - Revenue analytics
GET    /api/admin/analytics/orders  - Orders analytics
GET    /api/admin/analytics/users   - Users analytics
GET    /api/admin/disputes          - Get disputes
POST   /api/admin/disputes/:id/resolve - Resolve dispute
GET    /api/admin/audit-logs        - Audit logs
```

### Messaging Module (7 endpoints)
```
GET    /api/messages/conversations  - Get conversations
GET    /api/messages/conversations/:id - Get/create conversation
GET    /api/messages/conversations/:id/messages - Get messages
POST   /api/messages/conversations/:id/send - Send message
DELETE /api/messages/messages/:id   - Delete message
POST   /api/messages/messages/:id/read - Mark as read
GET    /api/messages/conversations/:id/unread-count - Unread count
```

---

## Testing

### Test API Endpoints

```bash
python test_api.py
```

This will test:
- ✓ Health check
- ✓ API information
- ✓ Farmer registration & login
- ✓ Buyer registration & login
- ✓ Farmer dashboard
- ✓ Product browsing
- ✓ Buyer profile

---

## File Structure

```
backend/
├── app.py                      - Main Flask application
├── startup.py                  - Backend startup script
├── init_db.py                  - Database initialization
├── test_api.py                 - API test suite
├── requirements.txt            - Python dependencies
├── .env.example                - Environment template
│
├── models/
│   └── models.py              - Data models (1000+ lines)
│
├── routes/
│   ├── auth.py                - Authentication (600+ lines)
│   ├── farmer_products.py     - Farmer module (500+ lines)
│   ├── buyer_products.py      - Buyer module (600+ lines)
│   ├── admin.py               - Admin module (500+ lines)
│   └── messages.py            - Messaging system (300+ lines)
│
├── utils/
│   ├── file_upload.py         - Cloudinary integration
│   ├── email_service.py       - Email notifications
│   └── middleware.py          - Utilities & middleware
│
└── database/
    └── complete_schema.sql    - Database schema (1400+ lines)
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Flask | 3.0.0 |
| Database | MySQL | 5.7+ |
| Authentication | JWT | HS256 |
| Password Hashing | bcrypt | 4.0.1 |
| Payments | Razorpay | 1.3.0 |
| File Storage | Cloudinary | 1.36.0 |
| Firebase | firebase-admin | 6.1.0 |
| CORS | Flask-CORS | 4.0.0 |

---

## Features Implemented

### ✅ Authentication
- Email/Password registration and login
- OTP-based verification
- Firebase/Google Sign-In
- JWT tokens (24-hour access, 30-day refresh)
- Password reset with email
- Email verification

### ✅ Farmer Module
- Product management (CRUD)
- Order management with status tracking
- Dashboard with statistics
- Earnings and wallet system
- Review and rating management
- Profile management

### ✅ Buyer Module
- Product browsing and searching
- Advanced filters (category, price, rating)
- Shopping cart management
- Order creation and tracking
- Razorpay payment integration
- Order cancellation
- Product reviews

### ✅ Admin Module
- User management (suspend/activate)
- Farmer verification workflow
- Product approval system
- Revenue and order analytics
- Dispute resolution
- Comprehensive audit logs

### ✅ Messaging
- Real-time conversations
- Message history with pagination
- Message deletion
- Read/unread status
- User notifications

### ✅ Infrastructure
- Role-based access control
- Input validation & sanitization
- SQL injection prevention
- Rate limiting support
- Error handling middleware
- Comprehensive logging
- Security headers

---

## Security Features

✅ **Password Security**
- Bcrypt hashing (cost factor 10)
- Salted passwords
- Strong password requirements

✅ **API Security**
- JWT token authentication
- Role-based access control (RBAC)
- Parameterized SQL queries
- Input validation
- CORS configuration
- Security headers (XSS, Clickjacking, MIME type protection)

✅ **Payment Security**
- Razorpay signature verification
- HMAC-SHA256 verification
- Amount validation

✅ **Database Security**
- Foreign key constraints
- Transaction integrity
- Proper character encoding (utf8mb4)

---

## Common Commands

### Development
```bash
# Start development server with hot reload
python startup.py

# Test API endpoints
python test_api.py

# Check health
curl http://localhost:5000/health
```

### Production
```bash
# Start with production WSGI server
SERVER_TYPE=production python startup.py

# Or use Waitress directly
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

### Database
```bash
# Initialize database (one time)
python init_db.py

# Check database connection
python models/models.py

# Import additional data
mysql -u root -p smart_farming < database/complete_schema.sql
```

---

## Troubleshooting

### Database Connection Error
```bash
# Verify MySQL is running
# On Windows: Check Services or restart MySQL
net stop MySQL80
net start MySQL80

# Or update .env with correct credentials
```

### Port 5000 Already in Use
```bash
# Change port in .env
FLASK_PORT=5001

# Or kill process on port 5000
lsof -ti:5000 | xargs kill -9  # Linux/Mac
```

### JWT Token Expired
```bash
# Use refresh endpoint to get new access token
POST /api/auth/refresh-token
```

### Cloudinary Upload Failing
```bash
# Verify environment variables in .env
CLOUDINARY_CLOUD_NAME=xxx
CLOUDINARY_API_KEY=xxx
CLOUDINARY_API_SECRET=xxx
```

---

## Performance Tips

1. **Enable Redis caching** for frequently accessed data
2. **Use database indexes** on commonly searched fields
3. **Implement pagination** for large result sets
4. **Enable gzip compression** for API responses
5. **Use CDN** for static assets and images
6. **Monitor query performance** with database logs

---

## Monitoring & Logging

All major operations are logged with:
- Request timestamps
- User IDs
- Status codes
- Error messages
- Execution time

Check logs in:
- Console output (development)
- Application logs (production)
- Database audit_logs table

---

## API Response Format

### Success Response
```json
{
  "status": "success",
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "errors": { ... }
}
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "has_next": true
  }
}
```

---

## Support & Documentation

- API Endpoints: GET `/api`
- Authentication Info: GET `/api/auth`
- Farmer API: GET `/api/farmer`
- Buyer API: GET `/api/buyer`
- Admin API: GET `/api/admin`
- Messaging API: GET `/api/messages`

---

## License & Status

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Quality:** Enterprise-Grade  
**Documentation:** Complete

---

**Happy Coding! 🚀**
