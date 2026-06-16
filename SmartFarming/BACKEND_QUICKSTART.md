# Quick Start Guide - Smart Farmer Marketplace Backend

**Estimated Setup Time:** 10-15 minutes  
**Last Updated:** June 12, 2026

---

## Prerequisites

Ensure you have the following installed:
- **Python 3.8+** - Download from python.org
- **MySQL 5.7+** - Download from mysql.com
- **Git** - For version control

---

## Step 1: Database Setup

### 1.1 Create MySQL Database

```bash
# Open MySQL command line
mysql -h localhost -u root -p

# Create database
CREATE DATABASE smart_farming CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 1.2 Import Database Schema

```bash
# Navigate to project directory
cd "c:\Users\SANDEEP\OneDrive\Farming MARK\SmartFarming"

# Import schema
mysql -h localhost -u root -p smart_farming < database/complete_schema.sql
```

**Expected Output:** Schema imported successfully (no errors)

---

## Step 2: Python Environment Setup

### 2.1 Create Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 2.2 Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected:** 28 packages installed successfully

---

## Step 3: Environment Configuration

### 3.1 Create .env File

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env file (use your preferred editor)
# OR use this command in PowerShell:
notepad .env
```

### 3.2 Configure Environment Variables

**Minimum Required Settings:**

```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DB=smart_farming

# Flask Configuration
FLASK_ENV=development
FLASK_PORT=5000
FRONTEND_URL=http://localhost:3000

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Email Configuration (for OTP/Password Reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Razorpay (Optional - for payments)
RAZORPAY_KEY_ID=rzp_test_xxxxxx
RAZORPAY_KEY_SECRET=xxxxx

# Firebase (Optional - for Google Sign-In)
FIREBASE_PROJECT_ID=your-project-id
```

---

## Step 4: Verify Database Connection

### 4.1 Test Database Setup

```bash
# Run database check script
python check_db.py
```

**Expected Output:**
```
✓ Database connection successful
✓ All tables created
✓ Schema validated
```

---

## Step 5: Start Backend Server

### 5.1 Run Development Server

```bash
# From backend directory with activated virtual environment
python app.py
```

**Expected Output:**
```
============================================
Smart Farmer Marketplace Backend
============================================

Database: smart_farming
Host: localhost
Debug Mode: True
Port: 5000

Frontend URL: http://localhost:3000

Available Endpoints:
- Health Check: GET /health
- API Info: GET /api
- Auth: /api/auth
- Farmer: /api/farmer
- Buyer: /api/buyer
- Admin: /api/admin

============================================

 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

---

## Step 6: Verify Backend is Running

### 6.1 Health Check

Open your browser or use curl:

```bash
# Test health endpoint
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 6.2 API Information

```bash
curl http://localhost:5000/api
```

**Expected Response:**
```json
{
  "name": "Smart Farmer Marketplace API",
  "version": "1.0.0",
  "endpoints": {
    "auth": "/api/auth",
    "farmer": "/api/farmer",
    "buyer": "/api/buyer",
    "admin": "/api/admin (coming soon)"
  }
}
```

---

## Step 7: Create Admin User (First Time Only)

```bash
# Run admin setup script
python setup_admin.py

# Follow the prompts:
# - Email: admin@smartfarmer.com
# - Password: (set strong password)
# - Confirm Password: (confirm)
```

**Expected Output:**
```
Admin user created successfully!
Email: admin@smartfarmer.com
```

---

## Testing the API

### Test Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePassword123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "farmer"
  }'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePassword123"
  }'

# Expected: JWT token in response
# Copy the access_token value
```

### Test Protected Endpoint

```bash
# Use the JWT token from login response
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Troubleshooting

### Issue: "Can't connect to MySQL server"

**Solution:**
```bash
# Verify MySQL is running
# On Windows, check Services (services.msc)
# Or restart MySQL:
net stop MySQL80
net start MySQL80
```

### Issue: "Port 5000 already in use"

**Solution:**
```bash
# Change port in .env file:
# FLASK_PORT=5001

# Or kill process on port 5000:
# On Windows (PowerShell):
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "JWT_SECRET_KEY not configured"

**Solution:**
```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy output and add to .env:
# JWT_SECRET_KEY=your-generated-key
```

---

## Common API Endpoints

### Authentication
```
POST   /api/auth/register           - Register user
POST   /api/auth/login              - Login user
GET    /api/auth/profile            - Get user profile (auth required)
POST   /api/auth/refresh-token      - Refresh JWT token
```

### Farmer Operations
```
GET    /api/farmer/dashboard        - Dashboard stats
GET    /api/farmer/products         - List products
POST   /api/farmer/products         - Create product
GET    /api/farmer/orders           - List orders
```

### Buyer Operations
```
GET    /api/buyer/products          - Browse products
GET    /api/buyer/cart              - Get shopping cart
POST   /api/buyer/cart/items        - Add to cart
POST   /api/buyer/orders            - Create order
```

### Admin Operations
```
GET    /api/admin/dashboard         - Admin dashboard
GET    /api/admin/users             - List users
GET    /api/admin/farmers/pending-verification - Pending farmers
```

---

## Next Steps

1. **Frontend Setup** - Set up React/Next.js frontend
2. **Testing** - Run comprehensive API tests
3. **Deployment** - Deploy to production server
4. **Monitoring** - Set up logging and monitoring

---

## Using Postman for API Testing

1. **Import API Collection**
   - Download Postman from postman.com
   - Create a new collection
   - Add requests for each endpoint

2. **Set Up Environment Variables**
   - `{{base_url}}` = http://localhost:5000
   - `{{token}}` = JWT from login response

3. **Example Request in Postman**
   ```
   Method: POST
   URL: {{base_url}}/api/auth/login
   Headers: Content-Type: application/json
   Body: {
     "email": "farmer@example.com",
     "password": "SecurePassword123"
   }
   ```

---

## Production Deployment

### Using Waitress (Production Server)

```bash
# Run with Waitress (thread-safe, suitable for production)
python run_with_waitress.py

# Or specify host/port:
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

### Using Docker (Optional)

```bash
# Build Docker image
docker build -t smart-farmer-api .

# Run container
docker run -p 5000:5000 smart-farmer-api
```

---

## File Structure

```
backend/
├── app.py                    - Main Flask application
├── requirements.txt          - Python dependencies
├── .env.example             - Environment template
├── .env                     - Configuration (create from .env.example)
├── check_db.py              - Database verification
├── setup_admin.py           - Admin user creation
├── run_with_waitress.py     - Production server
│
├── models/
│   └── models.py            - Database models
│
├── routes/
│   ├── auth.py              - Authentication endpoints
│   ├── farmer_products.py   - Farmer module
│   ├── buyer_products.py    - Buyer module
│   └── admin.py             - Admin module
│
└── venv/                    - Virtual environment (created locally)
```

---

## Support & Documentation

- **API Documentation:** Visit `/api/auth`, `/api/farmer`, `/api/buyer`, `/api/admin` for endpoint lists
- **Database Schema:** See `database/complete_schema.sql`
- **Implementation Details:** See `BACKEND_IMPLEMENTATION_COMPLETE.md`

---

## Quick Commands Reference

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Deactivate virtual environment
deactivate

# Install dependencies
pip install -r requirements.txt

# Start development server
python app.py

# Check database connection
python check_db.py

# Create admin user
python setup_admin.py

# Run with production server
python run_with_waitress.py
```

---

**Status:** ✅ Ready to Use  
**Backend Version:** 1.0.0  
**Last Updated:** June 12, 2026
