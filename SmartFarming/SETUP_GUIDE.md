# Smart Farming - Farmer Module - Installation & Setup Guide

## 🚀 Quick Start Guide

### Prerequisites
- Node.js 14+ and npm
- Python 3.8+
- MySQL 5.7+
- Android Studio / Xcode (for mobile development)
- React Native CLI

---

## 📦 Backend Setup (Flask)

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Create requirements.txt

```
Flask==2.3.0
Flask-CORS==4.0.0
Flask-JWT-Extended==4.4.4
Flask-MySQLdb==1.0.1
python-dotenv==1.0.0
Werkzeug==2.3.0
scikit-learn==1.3.0
numpy==1.24.0
pandas==2.0.0
requests==2.31.0
celery==5.3.0
redis==5.0.0
```

### 3. Setup Database

```bash
# Create database
mysql -u root -p
CREATE DATABASE smart_farming_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Import schema
USE smart_farming_db;
SOURCE database/schema.sql;
```

### 4. Create .env File

```bash
# backend/.env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_farming_db

JWT_SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DEBUG=True
HOST=0.0.0.0
PORT=5000

# AWS/Cloud credentials (for image upload)
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
AWS_S3_BUCKET=smart-farming-bucket
AWS_REGION=ap-south-1

# SMS Gateway (Twilio/AWS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE=+1234567890
```

### 5. Run Backend Server

```bash
python app.py
# Server runs on http://localhost:5000
```

### 6. Test API Health

```bash
curl http://localhost:5000/api/health
# Response: {"status": "healthy", "service": "Smart Farming API"}
```

---

## 📱 Frontend Setup (React Native)

### 1. Create React Native Project

```bash
react-native init SmartFarming
cd SmartFarming
```

### 2. Install Dependencies

```bash
npm install --save \
  @react-navigation/native \
  @react-navigation/stack \
  @react-navigation/bottom-tabs \
  react-native-screens \
  react-native-safe-area-context \
  react-native-gesture-handler \
  react-native-reanimated \
  @react-native-firebase/app \
  @react-native-firebase/messaging \
  axios \
  redux \
  react-redux \
  redux-thunk \
  redux-persist \
  react-native-paper \
  react-native-vector-icons \
  react-native-maps \
  react-native-image-picker \
  react-native-image-crop-picker \
  react-native-geolocation-service \
  react-native-voice \
  moment \
  date-fns \
  @react-native-async-storage/async-storage
```

### 3. Create API Configuration

```javascript
// frontend/services/api.js
export const API_BASE_URL = 'http://localhost:5000';

// Example API call
export const apiCall = async (endpoint, method = 'GET', data = null, token = null) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    method,
    headers,
  };

  if (data) {
    config.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  return response.json();
};
```

### 4. Setup Redux Store

```javascript
// frontend/redux/store.js
import { createStore, applyMiddleware, combineReducers } from 'redux';
import thunk from 'redux-thunk';
import authReducer from './reducers/authReducer';
import productReducer from './reducers/productReducer';
import orderReducer from './reducers/orderReducer';
import walletReducer from './reducers/walletReducer';

const rootReducer = combineReducers({
  auth: authReducer,
  products: productReducer,
  orders: orderReducer,
  wallet: walletReducer,
});

const store = createStore(rootReducer, applyMiddleware(thunk));
export default store;
```

### 5. Configure Navigation

```javascript
// frontend/navigation/RootNavigator.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

// Import screens
import PhoneScreen from '../screens/PhoneScreen';
import OTPScreen from '../screens/OTPScreen';
import SignupScreen from '../screens/SignupScreen';
import DashboardScreen from '../screens/DashboardScreen';
// ... import other screens

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Auth Navigator
export const AuthNavigator = () => (
  <Stack.Navigator>
    <Stack.Screen name="Phone" component={PhoneScreen} />
    <Stack.Screen name="OTP" component={OTPScreen} />
    <Stack.Screen name="Signup" component={SignupScreen} />
  </Stack.Navigator>
);

// Farmer Navigator
export const FarmerNavigator = () => (
  <Tab.Navigator>
    <Tab.Screen name="Home" component={DashboardScreen} />
    <Tab.Screen name="Products" component={ProductsScreen} />
    <Tab.Screen name="Orders" component={OrdersScreen} />
    <Tab.Screen name="AI" component={AIFeaturesScreen} />
    <Tab.Screen name="Wallet" component={WalletScreen} />
  </Tab.Navigator>
);

export const RootNavigator = ({ isAuthenticated }) => (
  <NavigationContainer>
    {isAuthenticated ? <FarmerNavigator /> : <AuthNavigator />}
  </NavigationContainer>
);
```

### 6. Create App.js

```javascript
// frontend/App.js
import React, { useEffect, useState } from 'react';
import { Provider } from 'react-redux';
import AsyncStorage from '@react-native-async-storage/async-storage';
import store from './redux/store';
import { RootNavigator } from './navigation/RootNavigator';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    const token = await AsyncStorage.getItem('accessToken');
    setIsAuthenticated(!!token);
  };

  return (
    <Provider store={store}>
      <RootNavigator isAuthenticated={isAuthenticated} />
    </Provider>
  );
}
```

### 7. Run on Android

```bash
npx react-native run-android
```

### 8. Run on iOS

```bash
npx react-native run-ios
```

---

## 📊 Database Connection Test

```bash
# Test with curl
curl -X GET http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","type":"signup"}'
```

---

## 🔧 Environment Variables

### Backend (.env)
- `DB_HOST`: MySQL host
- `DB_USER`: MySQL username
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: Database name
- `JWT_SECRET_KEY`: Secret for JWT tokens
- `AWS_S3_BUCKET`: S3 bucket for image uploads

### Frontend (API Configuration)
- `API_BASE_URL`: Backend API URL (http://localhost:5000)

---

## 📁 Project Structure

```
SmartFarming/
├── backend/
│   ├── app.py                 # Flask app entry point
│   ├── requirements.txt         # Python dependencies
│   ├── routes/
│   │   ├── auth.py            # Authentication routes
│   │   ├── farmer.py          # Farmer profile routes
│   │   ├── products.py        # Product management
│   │   ├── orders.py          # Order management
│   │   ├── ai_features.py     # AI predictions
│   │   ├── wallet.py          # Payment & wallet
│   │   └── weather.py         # Weather data
│   ├── models/
│   │   └── models.py          # Database models
│   ├── utils/
│   │   ├── validators.py      # Input validation
│   │   ├── ml_models.py       # ML models for AI
│   │   └── notifications.py   # SMS/Email notifications
│   └── .env                   # Environment variables
│
├── frontend/
│   ├── screens/
│   │   ├── PhoneScreen.js
│   │   ├── OTPScreen.js
│   │   ├── SignupScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── ProductsScreen.js
│   │   ├── OrdersScreen.js
│   │   ├── WalletScreen.js
│   │   └── AIFeaturesScreen.js
│   ├── styles/
│   │   ├── colors.js
│   │   └── spacing.js
│   ├── services/
│   │   ├── api.js
│   │   └── storage.js
│   ├── redux/
│   │   ├── store.js
│   │   ├── actions/
│   │   └── reducers/
│   ├── navigation/
│   │   └── RootNavigator.js
│   ├── App.js
│   └── package.json
│
├── database/
│   └── schema.sql             # MySQL schema
│
├── ARCHITECTURE.md            # Technical documentation
├── UIUX_DESIGN.md            # UI/UX specifications
└── README.md
```

---

## 🧪 Testing

### Backend Tests
```bash
pytest tests/
```

### Frontend Tests
```bash
npm test
```

---

## 🚀 Deployment

### Backend Deployment (Heroku)
```bash
heroku login
heroku create smart-farming-api
git push heroku main
heroku config:set DB_HOST=your_rds_host
```

### Frontend Deployment (Play Store / App Store)
```bash
# Android
cd android
./gradlew bundleRelease

# iOS
cd ios
xcode-select --install
```

---

## ✅ Checklist

- [ ] Backend server running on port 5000
- [ ] MySQL database created and schema imported
- [ ] All environment variables configured
- [ ] Frontend dependencies installed
- [ ] Navigation structure setup
- [ ] API integration working
- [ ] Redux store configured
- [ ] Authentication flow tested
- [ ] Dashboard screen rendering correctly

---

## 📞 Support & Documentation

- Backend API Docs: [ARCHITECTURE.md](./ARCHITECTURE.md)
- UI/UX Design: [UIUX_DESIGN.md](./UIUX_DESIGN.md)
- Database Schema: [database/schema.sql](./database/schema.sql)

---

## 🎯 Next Steps

1. ✅ Authentication & Registration (Complete)
2. ✅ Dashboard UI (Complete)
3. 🔄 Product Management (In Progress)
4. 🔄 Order Management (In Progress)
5. 🔄 AI Features (In Progress)
6. 🔄 Wallet & Payments (In Progress)
7. 📋 Weather Integration (Pending)
8. 📋 Voice Support (Pending)
9. 📋 Push Notifications (Pending)

