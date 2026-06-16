# 🌾 COMPLETE APPLICATION RUN GUIDE
## Smart Farming Marketplace - Full Stack Implementation

---

## ⚙️ PREREQUISITES CHECK

### Windows System Requirements
- [x] Python 3.8+ installed
- [x] Node.js 16+ installed
- [x] MySQL 5.7+ running
- [x] Git (optional)
- [x] PowerShell or Command Prompt

### Verify Installations
```powershell
# Check Python
python --version

# Check Node.js
node --version
npm --version

# Check MySQL
mysql --version
```

---

## 📋 STEP 1: DATABASE SETUP (5 minutes)

### 1.1 Start MySQL Service
```powershell
# Windows: Start MySQL from Services
# Or use: net start MySQL80
# Or use: mysql.server start (if using Homebrew on Mac)

# Verify MySQL is running
mysql -u root -p -e "SELECT 1"
# Enter password: Sandy@7981
```

### 1.2 Create Database
```powershell
# Open MySQL command prompt
mysql -u root -p

# Enter password: Sandy@7981
```

**Then in MySQL prompt, run:**
```sql
-- Create database
CREATE DATABASE SmartFarmingDB;

-- Use the database
USE SmartFarmingDB;

-- Import schema files (note: run from Command Prompt, not MySQL)
-- Exit MySQL first: EXIT;
```

### 1.3 Import Schema Files
**Exit MySQL first**, then in PowerShell:

```powershell
# Navigate to SmartFarming folder
cd "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming"

# Import all schema files in order
mysql -u root -p -D SmartFarmingDB < database/schema.sql
# Enter password: Sandy@7981

mysql -u root -p -D SmartFarmingDB < database/buyer_schema.sql
mysql -u root -p -D SmartFarmingDB < database/admin_schema.sql
mysql -u root -p -D SmartFarmingDB < database/advanced_features_schema.sql
```

### 1.4 Verify Database Created
```powershell
# Check if database was created
mysql -u root -p -D SmartFarmingDB -e "SHOW TABLES;"
# Enter password: Sandy@7981

# You should see 37+ tables listed
```

✅ **Database Setup Complete!**

---

## 🔧 STEP 2: BACKEND SETUP & RUN (10 minutes)

### 2.1 Navigate to Backend Directory
```powershell
cd backend
```

### 2.2 Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Method 1: Direct PowerShell
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### 2.3 Install Dependencies
```powershell
# Make sure virtual environment is activated (you should see (venv) in prompt)

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 2.4 Verify Backend App File
```powershell
# Check if app.py exists and contains Flask app
Test-Path app.py
```

### 2.5 Start Backend Server
```powershell
# Run Flask application
python app.py

# Expected output:
# * Running on http://127.0.0.1:5000
# * Debug mode: on/off
```

✅ **Backend is running on http://localhost:5000**

---

## 🎨 STEP 3: FRONTEND SETUP & RUN (10 minutes)

### 3.1 Open NEW PowerShell Window (keep backend running)

```powershell
# DO NOT close the backend terminal
# Open a NEW PowerShell/Command Prompt window
```

### 3.2 Navigate to Frontend Directory
```powershell
cd "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\frontend"
```

### 3.3 Install Dependencies
```powershell
# Install npm packages
npm install

# If you get dependency issues:
# npm install --legacy-peer-deps
```

### 3.4 Start Frontend Development Server
```powershell
# Start React development server
npm start

# Expected output:
# webpack compiled...
# Compiled successfully!
# You can now view smart-farming in the browser at http://localhost:3000
```

✅ **Frontend is running on http://localhost:3000**

---

## ✅ STEP 4: VERIFY ALL CONNECTIONS (5 minutes)

### 4.1 Check Backend Connection
```powershell
# Open new PowerShell window
curl http://localhost:5000

# Expected: 404 (backend is running)
# Or check specific endpoint:
curl http://localhost:5000/api/health
```

### 4.2 Frontend Should Auto-Open
- Browser automatically opens to http://localhost:3000
- You should see the beautiful landing page
- Try clicking buttons to navigate

### 4.3 Test API Connection
**In browser console (F12):**
```javascript
// Check if frontend can reach backend
fetch('http://localhost:5000/api/health')
  .then(r => r.json())
  .then(d => console.log('Backend Connected:', d))
  .catch(e => console.log('Error:', e));
```

**Expected output in console:**
```
Backend Connected: {status: 'ok', message: 'API is running'}
```

---

## 🧪 STEP 5: TEST COMPLETE SIGNUP FLOW (10 minutes)

### 5.1 Test Landing Page
1. Open http://localhost:3000 in browser
2. See beautiful landing page with animations ✅
3. Click "Get Started" button → Goes to login page ✅

### 5.2 Test Login Page
1. Should see Farmer/Buyer/Admin tabs
2. Enter email/phone: `test@example.com`
3. Enter password: `Password123`
4. Click "Login" button
5. See loading spinner ✅

### 5.3 Test Signup Flow
1. Click "Create New Account"
2. See signup dropdown
3. Click "Become a Farmer"
4. Fill Step 1: Name, Email, Phone
5. Click Next → Step 2
6. Fill Step 2: Password, City, District
7. Click Next → Step 3
8. Fill Step 3: Farm Name
9. Check Terms & Conditions
10. Click "Create Account"

### 5.4 Monitor Backend Console
Watch the backend terminal for:
```
POST /api/auth/farmer/signup
Status: 200 OK
```

✅ **All connections working!**

---

## 📊 ARCHITECTURE VISUALIZATION

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
│              http://localhost:3000                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │           React Frontend (npm start)             │  │
│  │  - Landing Page                                  │  │
│  │  - Login Page                                    │  │
│  │  - Signup Page                                   │  │
│  │  - Dashboard Pages (Farmer/Buyer/Admin)         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────────┘
               │ HTTPS/REST API Calls
               │ JWT Token in Headers
               ▼
┌─────────────────────────────────────────────────────────┐
│            Flask Backend Server                         │
│          http://localhost:5000                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Route Handlers (18 Blueprints)                 │  │
│  │  - /api/auth/*          (Authentication)        │  │
│  │  - /api/farmer/*        (Farmer Routes)         │  │
│  │  - /api/buyer/*         (Buyer Routes)          │  │
│  │  - /api/admin/*         (Admin Routes)          │  │
│  │  - /api/products/*      (Product Management)    │  │
│  │  - /api/orders/*        (Order Management)      │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Middleware                                      │  │
│  │  - JWT Verification                             │  │
│  │  - Error Handling                               │  │
│  │  - CORS Protection                              │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────────┘
               │ SQL Queries
               │ Connection Pooling
               ▼
┌─────────────────────────────────────────────────────────┐
│             MySQL Database                              │
│          SmartFarmingDB (localhost)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  37+ Tables with Foreign Keys                   │  │
│  │  - Users (Farmers, Buyers, Admins)             │  │
│  │  - Products & Orders                           │  │
│  │  - Payments & Cart                             │  │
│  │  - Reviews & Ratings                           │  │
│  │  - Notifications & Messages                    │  │
│  │  - Analytics & Reports                         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 DATA FLOW DIAGRAM

### Signup Flow
```
User (Browser)
    ↓
[Fill Signup Form] (3 Steps)
    ↓
[Submit Form]
    ↓ POST /api/auth/farmer/signup
Frontend Validation ← Validation Errors
    ↓
[JWT Header]
    ↓
Backend (Flask)
    ↓
[Validate Input]
    ↓ Input Error
Form Validation ← Validation Errors
    ↓
[Hash Password - bcrypt]
    ↓
[Database Query - INSERT]
    ↓
MySQL Database
    ↓
[Generate JWT Token]
    ↓
[Return: {token, user_id, user_data}]
    ↓
Frontend (store token in localStorage)
    ↓
[Redirect to Dashboard]
    ↓
User Dashboard ✅
```

### Login Flow
```
User (Browser)
    ↓
[Select Role: Farmer/Buyer/Admin]
    ↓
[Enter Email/Phone + Password]
    ↓
[Submit Login Form]
    ↓ POST /api/auth/{role}/login
Backend (Flask)
    ↓
[Find User in Database]
    ↓ User Not Found
[Login Error] ← Show Error Message
    ↓
[Compare Password - bcrypt]
    ↓ Password Invalid
[Login Error] ← Show Error Message
    ↓
[Generate JWT Token]
    ↓
[Return: {token, user_id, role, user_data}]
    ↓
Frontend (store token in localStorage)
    ↓
[Add JWT to all future API requests]
    ↓
[Redirect to Dashboard based on role]
    ↓
User Dashboard ✅
```

---

## 🚨 TROUBLESHOOTING

### Issue 1: Backend Port Already in Use
**Error**: `Address already in use`
```powershell
# Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in app.py: app.run(port=5001)
```

### Issue 2: Frontend Port Already in Use
**Error**: `Port 3000 already in use`
```powershell
# Kill process using port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or the app will ask to use 3001
```

### Issue 3: MySQL Connection Error
**Error**: `Can't connect to MySQL server`
```powershell
# Check MySQL is running
mysql -u root -p -e "SELECT 1"

# If not running, start it:
# Services → MySQL80 → Start
# Or: net start MySQL80
```

### Issue 4: CORS Error in Browser
**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: Backend already configured for CORS
- Check that backend is running
- Check that frontend is making requests to http://localhost:5000
- In frontend, API client should have correct base URL

### Issue 5: Virtual Environment Not Activated
**Error**: `pip: command not found`
```powershell
# Make sure to activate venv before running commands
cd backend
.\venv\Scripts\Activate.ps1

# You should see (venv) in the prompt
```

### Issue 6: NPM Dependencies Issue
**Error**: `Cannot find module react`
```powershell
# Clear node_modules and reinstall
cd frontend
rm -r node_modules package-lock.json
npm install --legacy-peer-deps
```

### Issue 7: Database Import Error
**Error**: `ERROR 1044: Access denied`
```powershell
# Try with -u root -p flags and proper syntax
mysql -u root -p SmartFarmingDB < database/schema.sql

# Make sure file path is correct
# Make sure database SmartFarmingDB exists first
```

---

## 📱 TESTING CHECKLIST

### ✅ Frontend
- [ ] Landing page loads with animations
- [ ] Login page shows user type tabs
- [ ] Signup page shows 3-step form
- [ ] Navigation between pages works
- [ ] Form validation shows error messages
- [ ] All buttons are clickable
- [ ] Responsive on mobile (F12 → Toggle device toolbar)

### ✅ Backend
- [ ] Backend server starts on http://localhost:5000
- [ ] No error messages in console
- [ ] CORS headers are present
- [ ] API endpoints respond correctly

### ✅ Database
- [ ] MySQL is running
- [ ] SmartFarmingDB database exists
- [ ] All 37+ tables are created
- [ ] Tables have correct columns

### ✅ Integration
- [ ] Frontend can reach backend API
- [ ] API responses show in Network tab (F12)
- [ ] No CORS errors
- [ ] No MySQL connection errors

---

## 🎯 COMPLETE RUN SEQUENCE (Copy & Paste)

### Terminal 1: Backend
```powershell
cd "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\backend"
.\venv\Scripts\Activate.ps1
python app.py
```

### Terminal 2: Frontend
```powershell
cd "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\frontend"
npm start
```

### Terminal 3: Database
```powershell
cd "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming"
mysql -u root -p SmartFarmingDB -e "SELECT COUNT(*) as 'Table Count' FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'SmartFarmingDB';"
```

---

## 📊 EXPECTED CONSOLE OUTPUTS

### Backend Console (python app.py)
```
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * WARNING: This is a development server. Do not use it in production.
 * Use a production WSGI server instead.
 * Restarting with stat reloader
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

### Frontend Console (npm start)
```
webpack compiled successfully
Compiled successfully!

You can now view smart-farming in the browser at:

  http://localhost:3000

Note that the development build is not optimized.
To create a production build, use npm run build.
```

### Browser Console (F12)
```
[HMR] connected
GET http://localhost:5000/api/health 200 OK
```

---

## 🔑 DEFAULT TEST CREDENTIALS

### Farmer Account
- Email: `farmer@example.com`
- Password: `Password123`
- Role: `Farmer`

### Buyer Account
- Phone: `9999999999`
- Password: `Password123`
- Role: `Buyer`

### Admin Account
- Email: `admin@example.com`
- Password: `Admin123`
- Role: `Admin`

---

## ⚡ QUICK REFERENCE

| Component | URL | Port | Status |
|-----------|-----|------|--------|
| Frontend | http://localhost:3000 | 3000 | ✅ |
| Backend | http://localhost:5000 | 5000 | ✅ |
| Database | localhost | 3306 | ✅ |
| MySQL Root | - | - | user: `root` pass: `Sandy@7981` |

---

## 📈 WHAT HAPPENS WHEN YOU RUN EVERYTHING

1. **User navigates to http://localhost:3000**
   - React app loads with beautiful landing page
   - Animations start playing
   - Page is fully interactive

2. **User clicks "Get Started"**
   - Frontend router navigates to login page
   - Login page renders with form

3. **User enters credentials and clicks "Login"**
   - Frontend validates form
   - Frontend sends POST request to http://localhost:5000/api/auth/farmer/login
   - Backend receives request
   - Backend checks database for user
   - Backend compares password hash
   - Backend generates JWT token
   - Backend sends token back to frontend
   - Frontend stores token in localStorage
   - Frontend redirects to dashboard
   - Dashboard page loads

4. **User can now use the application**
   - All API requests include JWT token
   - Backend verifies token before processing
   - Protected routes only accessible with valid token

---

## 🎊 YOU'RE READY!

Everything is set up and ready to run. Just follow the steps above and your complete Smart Farming Marketplace will be:

✅ Running on Frontend
✅ Running on Backend
✅ Connected to Database
✅ All APIs working
✅ Authentication ready
✅ Beautiful UI showing

**Let's go!** 🚀

---

**Last Updated**: 2024-06-04
**Version**: 1.0 - Complete Running Guide
**Status**: READY TO RUN
