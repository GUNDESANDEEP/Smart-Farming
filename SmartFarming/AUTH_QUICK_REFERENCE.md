# Smart Farming - Authentication Quick Reference

## 5 Authentication Systems Used

### 1️⃣ JWT (JSON Web Token)
- **Type**: Token-based
- **Key**: `JWT_SECRET_KEY` in .env
- **Duration**: 24 hours
- **Used For**: API request authentication (after login)
- **Header**: `Authorization: Bearer <token>`

### 2️⃣ OTP (One Time Password)
- **Type**: SMS-based verification
- **Key**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- **Duration**: 10 minutes
- **Used For**: Farmer & Buyer signup/login verification
- **Delivery**: SMS via Twilio

### 3️⃣ Email/Password (Admin)
- **Type**: Traditional credentials
- **Key**: Admin email + bcrypt-hashed password
- **Hashing**: Bcrypt (10 rounds)
- **Used For**: Admin panel login
- **Stored In**: Database (admins table)

### 4️⃣ Phone-Based (Farmer & Buyer)
- **Type**: Phone verification + Password
- **Key**: Phone number + Password
- **Used For**: Farmer and Buyer account creation
- **Stored In**: Database (farmers/buyers table)

### 5️⃣ API Key (Third-party)
- **Type**: API credential verification
- **Keys**: 
  - Weather: `WEATHER_API_KEY`
  - Payments: `RAZORPAY_KEY_ID`, `STRIPE_SECRET_KEY`
  - Webhooks: `RAZORPAY_WEBHOOK_SECRET`
- **Used For**: External service integration

---

## Environment Variables Summary

### Critical Security Keys (🔴 MUST KEEP SECRET)
```
JWT_SECRET_KEY              - Signing all JWT tokens
DB_PASSWORD                 - Database access
EMAIL_PASSWORD              - SMTP authentication
TWILIO_AUTH_TOKEN          - SMS service access
RAZORPAY_KEY_SECRET        - Payment processing
STRIPE_SECRET_KEY          - Payment processing
AWS_SECRET_ACCESS_KEY      - AWS service access
SENDGRID_API_KEY           - Email service
WEBHOOK_SECRET             - Webhook validation
```

### Configuration Keys (⚠️ ENVIRONMENT SPECIFIC)
```
DB_HOST                     - Database server
DB_USER                     - Database user
DB_NAME                     - Database name
SMTP_SERVER                 - Email server
SMTP_PORT                   - Email port
EMAIL_SENDER                - From email address
TWILIO_ACCOUNT_SID         - SMS account ID
TWILIO_PHONE_NUMBER        - SMS sender number
RAZORPAY_KEY_ID            - Payment account ID
WEATHER_API_KEY            - Weather service key
```

### Application Settings (✅ GENERAL)
```
ENVIRONMENT                 - dev/staging/prod
DEBUG                       - True/False
HOST                        - Server host
PORT                        - Server port
CORS_ORIGINS               - Allowed origins
LOG_LEVEL                  - Logging level
BCRYPT_ROUNDS              - Password hash strength
```

---

## Files Created

### .env (Development Configuration)
- **Location**: `/SmartFarming/.env`
- **Purpose**: Store all environment variables
- **Status**: ⚠️ DO NOT COMMIT TO GIT
- **Contents**: All 17 variable categories

### .env.example (Template)
- **Location**: `/SmartFarming/.env.example`
- **Purpose**: Template for developers
- **Status**: ✅ Safe to commit to GIT
- **Contents**: Same structure as .env with comments

### AUTH_GUIDE.md (Detailed Documentation)
- **Location**: `/SmartFarming/AUTH_GUIDE.md`
- **Purpose**: Complete authentication guide
- **Contents**:
  - All 5 authentication types explained
  - API endpoint documentation
  - Code examples
  - Security best practices
  - Troubleshooting guide

---

## Authentication Flow by User Type

### 👨‍🌾 Farmer Registration & Login
```
1. POST /api/auth/send-otp (phone)
   ↓
2. Receive SMS with 6-digit OTP
   ↓
3. POST /api/auth/verify-otp (phone + OTP)
   ↓
4. POST /api/auth/register (phone + verification_token + password + details)
   ↓
5. JWT Token received → stored in AsyncStorage
   ↓
6. Make API calls with JWT in header
```

### 👨‍💼 Admin Login
```
1. POST /api/admin-auth/login (email + password)
   ↓
2. Server validates with bcrypt hash
   ↓
3. JWT Token received → stored in localStorage/cookie
   ↓
4. Make API calls with JWT in header
```

### 🛍️ Buyer Registration & Login
```
1. POST /api/buyer-auth/send-otp (phone)
   ↓
2. Receive SMS with 6-digit OTP
   ↓
3. POST /api/buyer-auth/verify-otp (phone + OTP)
   ↓
4. POST /api/buyer-auth/signup (phone + email + password + details)
   ↓
5. JWT Token received → stored in AsyncStorage
   ↓
6. Make API calls with JWT in header
```

---

## All 18 Route Blueprints Registered

### Farmer Routes (7)
- ✅ auth_bp → `/api/auth`
- ✅ farmer_bp → `/api/farmer`
- ✅ products_bp → `/api/products`
- ✅ orders_bp → `/api/orders`
- ✅ ai_bp → `/api/ai`
- ✅ wallet_bp → `/api/wallet`
- ✅ weather_bp → `/api/weather`

### Admin Routes (8)
- ✅ admin_auth_bp → `/api/admin-auth`
- ✅ admin_dashboard_bp → `/api/admin/dashboard`
- ✅ admin_products_bp → `/api/admin/products`
- ✅ admin_users_bp → `/api/admin/users`
- ✅ admin_orders_bp → `/api/admin/orders`
- ✅ admin_analytics_bp → `/api/admin/analytics`
- ✅ admin_monitoring_bp → `/api/admin/ai-monitoring`
- ✅ admin_advanced_features_bp → `/api/admin/advanced-features`

### Buyer Routes (7)
- ✅ buyer_auth_bp → `/api/buyer-auth`
- ✅ buyer_products_bp → `/api/products` (buyer view)
- ✅ buyer_cart_bp → `/api/cart`
- ✅ buyer_orders_bp → `/api/orders` (buyer view)
- ✅ buyer_payments_bp → `/api/payments`
- ✅ buyer_profile_bp → `/api/buyer`
- ✅ buyer_reviews_bp → `/api/reviews`

---

## .env File Locations & Status

| File | Path | Status | Commit |
|------|------|--------|--------|
| .env | `/SmartFarming/.env` | ✅ Created | ❌ NO |
| .env.example | `/SmartFarming/.env.example` | ✅ Created | ✅ YES |

---

## How to Set Up Authentications

### Step 1: Create .env File
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use VS Code
```

### Step 2: Update JWT Secret
```env
# Change from default to strong random string
JWT_SECRET_KEY=your-actual-secret-key-32-chars-minimum
```

### Step 3: Configure Database
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=smart_farming_db
```

### Step 4: Setup Email (SMTP)
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
# Use Gmail App Password (not regular password)
EMAIL_PASSWORD=your-16-char-app-password
```

### Step 5: Setup SMS (Twilio)
Get from Twilio dashboard:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### Step 6: Setup Payments (Optional)
```env
# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxx

# OR Stripe
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
```

### Step 7: Test Authentication
```bash
# Run test script
python test_auth_registration.py

# Or manually test endpoints with Postman
```

---

## Security Checklist

- [ ] JWT_SECRET_KEY changed from default
- [ ] .env added to .gitignore
- [ ] Database password is strong (16+ chars)
- [ ] Email app password configured
- [ ] Twilio credentials valid
- [ ] HTTPS enabled in production
- [ ] CORS_ORIGINS restricted to known domains
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Backups scheduled
- [ ] Monitoring set up
- [ ] .env NOT committed to repository

---

## Production Deployment Notes

### Before Deploy
1. Generate new JWT_SECRET_KEY
2. Update all API keys to production values
3. Change DEBUG=False
4. Enable HTTPS/SSL certificate
5. Set ENVIRONMENT=production
6. Update CORS_ORIGINS to specific domains
7. Configure monitoring (Sentry)
8. Set up log aggregation

### Production .env
```env
ENVIRONMENT=production
DEBUG=False
JWT_SECRET_KEY=[STRONG-RANDOM-KEY-FROM-SECURE-GENERATOR]
DB_PASSWORD=[STRONG-DB-PASSWORD]
EMAIL_PASSWORD=[APP-SPECIFIC-PASSWORD]
TWILIO_AUTH_TOKEN=[FROM-TWILIO-PROD]
RAZORPAY_KEY_SECRET=[FROM-RAZORPAY-PROD]
STRIPE_SECRET_KEY=[FROM-STRIPE-PROD]
CORS_ORIGINS=https://smartfarming.com,https://www.smartfarming.com
```

---

## Troubleshooting

### Error: "No module named 'flask'"
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### Error: "Invalid email or password"
- Check admin credentials in database
- Verify password hashing (bcrypt)
- Check database connection

### Error: "OTP expired"
- Request new OTP
- Check system time (NTP sync)

### Error: "Token not provided"
- Add Authorization header
- Format: `Authorization: Bearer <token>`

### Error: "SMS not received"
- Check Twilio balance
- Verify phone number format (with country code)
- Check TWILIO_PHONE_NUMBER configuration

---

## Quick Test Commands

### Test Farmer Authentication
```bash
# Send OTP
curl -X POST http://localhost:5000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","type":"signup"}'

# Verify OTP (use value from console output)
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","otp":"123456"}'
```

### Test Admin Authentication
```bash
curl -X POST http://localhost:5000/api/admin-auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@smartfarming.com","password":"Admin@123"}'
```

### Test Protected Endpoint
```bash
curl -X GET http://localhost:5000/api/farmer/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

---

## Contact & Support

**Documentation**: `/SmartFarming/AUTH_GUIDE.md`
**Configuration**: `/SmartFarming/.env`
**Template**: `/SmartFarming/.env.example`

For issues, check logs and documentation first.
