# Smart Farming - Authentication Architecture & API Keys Guide

## Overview
This project uses a **multi-layered authentication system** with 5 different authentication types depending on the user role and use case.

---

## 1. JWT (JSON Web Token) Authentication

### Purpose
Primary authentication method for all API requests after initial login.

### How It Works
1. User logs in with credentials (Email/Password for Admin, Phone/OTP for Farmer/Buyer)
2. Server validates credentials and creates a JWT token
3. Client stores JWT token (localStorage, AsyncStorage, etc.)
4. Client includes JWT in Authorization header for all API requests: `Authorization: Bearer <token>`
5. Server validates JWT for every protected endpoint

### Key Configuration
```
JWT_SECRET_KEY = "your-super-secret-key-change-in-production"
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
```

### JWT Token Content
```json
{
  "identity": "user_id",
  "type": "admin/farmer/buyer",
  "role": "super_admin/moderator/analyst",
  "email": "user@example.com",
  "iat": 1234567890,
  "exp": 1234654290
}
```

### Usage Examples

#### Farmer Login
```python
POST /api/auth/login
{
  "phone": "9876543210",
  "otp": "123456"
}

Response:
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "farmer_id": 1,
  "name": "Raj Kumar"
}
```

#### Admin Login
```python
POST /api/admin-auth/login
{
  "email": "admin@smartfarming.com",
  "password": "SecurePass123!"
}

Response:
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "admin_id": 1,
  "role": "super_admin"
}
```

#### API Request with JWT
```python
GET /api/farmer/profile
Headers: {
  "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 2. OTP (One Time Password) Authentication

### Purpose
Secure phone-based authentication for Farmers and Buyers during signup/login.

### How It Works
1. User enters phone number
2. Server generates 6-digit OTP and sends via SMS (Twilio)
3. User receives SMS and enters OTP
4. Server validates OTP (must match and not expired)
5. Server creates verification token
6. User can proceed with account creation/login

### Key Configuration
```
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "your-auth-token"
TWILIO_PHONE_NUMBER = "+1234567890"
```

### OTP Rules
- **Length**: 6 digits
- **Expiry**: 10 minutes
- **Max Attempts**: 3
- **Resend Limit**: Can resend after 30 seconds

### API Flow

#### Step 1: Send OTP
```python
POST /api/auth/send-otp
{
  "phone": "9876543210",
  "type": "signup"  # or "login"
}

Response:
{
  "success": true,
  "message": "OTP sent to 9876****210",
  "expires_in": 600  # seconds
}
```

#### Step 2: Verify OTP
```python
POST /api/auth/verify-otp
{
  "phone": "9876543210",
  "otp": "123456"
}

Response:
{
  "success": true,
  "verification_token": "temp_token_xyz",
  "message": "OTP verified"
}
```

#### Step 3: Create Password & Account
```python
POST /api/auth/register
{
  "phone": "9876543210",
  "verification_token": "temp_token_xyz",
  "password": "SecurePass123!",
  "first_name": "Raj",
  "last_name": "Kumar",
  "location": "Punjab"
}

Response:
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "farmer_id": 1
}
```

---

## 3. Email/Password Authentication (Admin)

### Purpose
Traditional email and password-based login for Admin users.

### How It Works
1. Admin enters email and password
2. Server retrieves admin record by email
3. Server compares provided password with stored hash (Bcrypt)
4. If valid, server generates JWT token
5. Admin is logged in and can access admin endpoints

### Key Configuration
```
BCRYPT_ROUNDS = 10  # Password hash strength
EMAIL = "admin@smartfarming.com"
PASSWORD = "SecurePass123!"
```

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

### Password Hashing
- **Algorithm**: Bcrypt
- **Rounds**: 10 (2^10 iterations)
- **Never stored as**: Plain text
- **Comparison**: Using `check_password_hash()`

### Admin Login API
```python
POST /api/admin-auth/login
{
  "email": "admin@smartfarming.com",
  "password": "SecurePass123!"
}

Response:
{
  "success": true,
  "message": "Login successful",
  "admin_id": 1,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "super_admin",
  "first_name": "Super",
  "permissions": ["user_management", "product_approval", "order_management"]
}
```

---

## 4. Buyer Authentication (OTP + Email)

### Purpose
Phone-based OTP authentication for Buyers (similar to Farmers but with email optional).

### How It Works
1. Buyer sends phone number to `/api/buyer-auth/send-otp`
2. System checks if phone exists
   - If new: Send OTP for signup
   - If exists: Send OTP for login
3. Buyer verifies OTP
4. Buyer creates password (for signup) or receives JWT (for login)

### Buyer Registration Flow
```python
# Step 1: Send OTP
POST /api/buyer-auth/send-otp
{
  "phone": "9876543210",
  "type": "signup"
}

# Step 2: Verify OTP
POST /api/buyer-auth/verify-otp
{
  "phone": "9876543210",
  "otp": "123456"
}

# Step 3: Complete Signup
POST /api/buyer-auth/signup
{
  "phone": "9876543210",
  "verification_token": "temp_token",
  "password": "BuyerPass123!",
  "email": "buyer@example.com",
  "first_name": "Rahul",
  "last_name": "Singh"
}
```

### Buyer Login Flow
```python
# Step 1: Send OTP
POST /api/buyer-auth/send-otp
{
  "phone": "9876543210",
  "type": "login"
}

# Step 2: Verify OTP
POST /api/buyer-auth/verify-otp
{
  "phone": "9876543210",
  "otp": "123456"
}

Response (on login):
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "buyer_id": 1,
  "name": "Rahul Singh"
}
```

---

## 5. API Key Authentication (Optional)

### Purpose
For third-party integrations and external service authentication.

### Usage
- **Weather API**: OpenWeatherMap requires API key
- **Payment Webhooks**: Razorpay/Stripe require webhook signature verification
- **SMS Service**: Twilio requires account credentials

### Environment Variables
```
WEATHER_API_KEY = "your-openweathermap-key"
RAZORPAY_KEY_ID = "rzp_test_xxxxx"
RAZORPAY_KEY_SECRET = "xxxxx"
STRIPE_SECRET_KEY = "sk_test_xxxxx"
```

---

## Authentication Endpoints Summary

### Farmer Authentication
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/api/auth/send-otp` | POST | Send OTP for signup/login | No |
| `/api/auth/verify-otp` | POST | Verify OTP code | No |
| `/api/auth/register` | POST | Complete farmer registration | No (uses verification token) |
| `/api/auth/login` | POST | Login with OTP | No |
| `/api/auth/logout` | POST | Logout | Yes (JWT) |
| `/api/auth/forgot-password` | POST | Reset password | No |

### Admin Authentication
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/api/admin-auth/login` | POST | Admin login with email/password | No |
| `/api/admin-auth/logout` | POST | Admin logout | Yes (JWT) |
| `/api/admin-auth/change-password` | POST | Change admin password | Yes (JWT) |
| `/api/admin-auth/verify-token` | GET | Verify JWT validity | Yes (JWT) |

### Buyer Authentication
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/api/buyer-auth/send-otp` | POST | Send OTP for buyer signup/login | No |
| `/api/buyer-auth/verify-otp` | POST | Verify OTP code | No |
| `/api/buyer-auth/signup` | POST | Complete buyer registration | No |
| `/api/buyer-auth/login` | POST | Buyer login | No |

---

## Security Best Practices

### 1. JWT Token Storage
```javascript
// Frontend - DO NOT store in localStorage for sensitive apps
localStorage.setItem('access_token', token);

// Mobile (React Native) - Use AsyncStorage
AsyncStorage.setItem('access_token', token);

// Best Practice: Use HttpOnly cookies (server-side set)
// Prevents XSS attacks
```

### 2. Password Requirements
```
✅ Minimum 8 characters
✅ Mixed case (A-Z, a-z)
✅ Numbers (0-9)
✅ Special characters (!@#$%^&*)
❌ Common words (password, 123456, qwerty)
❌ User's name or email
```

### 3. Rate Limiting
```
- Login attempts: Max 5 per 15 minutes
- OTP verification: Max 3 attempts per OTP
- API requests: 100 requests per minute (configurable)
```

### 4. Token Expiration
```
JWT Token: 24 hours
OTP: 10 minutes
Session: 30 minutes (configurable)
```

### 5. Secure Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
X-Requested-With: XMLHttpRequest
```

---

## Environment Variables Checklist

### Required (Must have)
- [ ] JWT_SECRET_KEY
- [ ] DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
- [ ] SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD
- [ ] TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

### Optional (Nice to have)
- [ ] AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (for S3)
- [ ] RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (for payments)
- [ ] STRIPE_SECRET_KEY (alternative payment)
- [ ] WEATHER_API_KEY (for weather features)

### Production Must-have (Additional)
- [ ] SENTRY_DSN (error tracking)
- [ ] LOG_FILE_PATH (centralized logging)
- [ ] CORS_ORIGINS (restrict to specific domains)
- [ ] SSL_CERTIFICATE_PATH (HTTPS)

---

## Testing Authentication

### Using Postman

#### 1. Farmer Login
```
POST http://localhost:5000/api/auth/send-otp
{
  "phone": "9876543210",
  "type": "signup"
}

# Copy OTP from console output

POST http://localhost:5000/api/auth/verify-otp
{
  "phone": "9876543210",
  "otp": "123456"
}

# Use verification_token from response

POST http://localhost:5000/api/auth/register
{
  "phone": "9876543210",
  "verification_token": "temp_token",
  "password": "Farmer@123",
  "first_name": "Raj",
  "last_name": "Kumar",
  "location": "Punjab"
}

# Store access_token in Authorization header
```

#### 2. Admin Login
```
POST http://localhost:5000/api/admin-auth/login
{
  "email": "admin@smartfarming.com",
  "password": "Admin@123"
}

# Use access_token in header
Header: Authorization: Bearer <token>
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Invalid email or password` | Wrong admin credentials | Check DB for admin user |
| `OTP expired` | OTP older than 10 minutes | Request new OTP |
| `Token not provided` | Missing Authorization header | Add `Authorization: Bearer <token>` |
| `Invalid token` | JWT signature invalid | Check JWT_SECRET_KEY in .env |
| `Phone already registered` | Phone number exists | Use different phone or login |
| `Email not sent` | SMTP credentials wrong | Check EMAIL_PASSWORD in .env |

---

## Deployment Checklist

### Before Going Live
- [ ] Change JWT_SECRET_KEY to strong random value
- [ ] Update EMAIL_PASSWORD with app-specific password
- [ ] Configure RAZORPAY with production keys
- [ ] Update CORS_ORIGINS to specific domains
- [ ] Set DEBUG=False
- [ ] Enable HTTPS/SSL
- [ ] Configure database backups
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Test all authentication flows
- [ ] Set up rate limiting
- [ ] Enable logging to file

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                   │
│              (Web/Mobile - React/React Native)          │
└────────┬────────────────────────────────────────────────┘
         │
         │ 1. Login Request
         ▼
┌─────────────────────────────────────────────────────────┐
│                   AUTHENTICATION LAYER                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Farmer Auth    │ Admin Auth      │ Buyer Auth    │  │
│  │ (/api/auth)    │ (/api/admin)    │ (/api/buyer)  │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────┘
         │
         │ 2. Credentials Validation
         ▼
┌─────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Farmers Table    │ Admins Table    │ Buyers Table│  │
│  │ (phone, email,   │ (email,         │ (phone,     │  │
│  │  password_hash)  │  password_hash) │  email)     │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────┘
         │
         │ 3. Generate JWT Token
         ▼
┌─────────────────────────────────────────────────────────┐
│                   TOKEN CREATION                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Payload:                                         │  │
│  │ - identity (user_id)                            │  │
│  │ - type (farmer/admin/buyer)                     │  │
│  │ - email, role                                    │  │
│  │ - expiration (24 hours)                          │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────┘
         │
         │ 4. Return Token to Client
         ▼
┌─────────────────────────────────────────────────────────┐
│                    CLIENT STORAGE                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ localStorage (Web)                               │  │
│  │ AsyncStorage (Mobile)                            │  │
│  │ HttpOnly Cookie (Recommended)                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────┘
         │
         │ 5. API Request with JWT in Header
         ▼
┌─────────────────────────────────────────────────────────┐
│                  PROTECTED ENDPOINTS                     │
│  Authorization: Bearer <JWT_TOKEN>                      │
│  GET /api/farmer/profile                                │
│  POST /api/orders/place                                 │
│  GET /api/admin/dashboard                               │
└────────┬────────────────────────────────────────────────┘
         │
         │ 6. Verify JWT Signature
         ▼
┌─────────────────────────────────────────────────────────┐
│                  JWT VERIFICATION                        │
│  ✅ Signature valid (JWT_SECRET_KEY matches)            │
│  ✅ Token not expired                                    │
│  ✅ Claims present (identity, type, role)               │
└────────┬────────────────────────────────────────────────┘
         │
         │ 7. Grant Access to Resource
         ▼
┌─────────────────────────────────────────────────────────┐
│                   AUTHORIZED RESPONSE                    │
│  Status: 200 OK                                          │
│  Data: Protected resource                               │
└─────────────────────────────────────────────────────────┘
```

---

## Need Help?

For authentication issues, check:
1. `.env` file has all required keys
2. JWT_SECRET_KEY matches in all environments
3. Database has user record
4. Token has not expired
5. Authorization header is properly formatted

Contact: support@smartfarming.com
