# 🌾 Smart Farming - Farmer Module

**A complete end-to-end Smart Farming application for farmers with AI features, real-time order management, and direct selling capabilities.**

---

## 📋 Project Overview

Smart Farming is a comprehensive platform that empowers farmers with:
- Direct access to buyers (eliminating middlemen)
- AI-powered crop recommendations and price predictions
- Real-time weather information
- Digital wallet and easy payments
- Order management and delivery tracking
- Voice support in multiple languages (Telugu, Hindi, English)

### 🎯 Problem Statement
Farmers struggle with:
- Finding buyers directly (low profit margins due to middlemen)
- Lack of market data and price predictions
- Poor crop planning and fertilizer selection
- Unpredictable weather impacts

### 💡 Our Solution
Smart Farming platform provides:
- **Direct Selling**: Connect farmers directly with buyers
- **AI Intelligence**: Crop recommendations, price predictions, fertilizer guidance
- **Real-time Data**: Live weather, market prices, demand trends
- **Easy Operations**: Intuitive mobile app, order management, payment processing
- **Support**: Multi-language voice support for accessibility

---

## ✨ Key Features - Farmer Module

### 1️⃣ Registration & Authentication
- **OTP-based signup** (SMS verification)
- **Secure login** with JWT tokens
- **Profile completion** (land area, crops, experience)
- **Forgot password** functionality
- **Phone number verification** to prevent duplicates

### 2️⃣ Dashboard
- **Real-time stats**: Products, orders, earnings
- **Live weather** for farmer's location
- **Recent orders** with quick actions
- **AI suggestions** card
- **Quick action buttons** (Add product, View orders, Withdraw)

### 3️⃣ Product Management
- **Add products** with images and descriptions
- **Set prices** based on market rates
- **Update quantities** in real-time
- **Product images** upload to AWS S3
- **View analytics** (sold quantity, ratings, reviews)
- **Category-based organization**

### 4️⃣ Order Management
- **Accept/Reject orders** from buyers
- **Real-time order status** updates
- **Delivery tracking** with GPS
- **Order history** and insights
- **Customer communication** system
- **Notification alerts** for new orders

### 5️⃣ AI Features
- **Crop Recommendations** (based on season, location, soil)
- **Price Prediction** (7-day, 30-day, 90-day forecasts)
- **Fertilizer Suggestions** (customized dosage per land area)
- **Disease Detection** (image-based - Phase 2)
- **Weather Alerts** (frost, hail, heavy rain warnings)

### 6️⃣ Wallet & Payments
- **Earnings tracking** (daily, weekly, monthly)
- **Bank account management**
- **Easy withdrawals** to savings account
- **Transaction history** with filters
- **Payment gateway integration** (Razorpay, Stripe)
- **Withdrawal status** monitoring

### 7️⃣ Weather Integration
- **Live weather data** for farmer's location
- **7-day forecast** with rainfall predictions
- **Weather alerts** for crop-threatening conditions
- **Historical weather** data analysis
- **Wind speed, humidity, pressure** information

---

## 🏗️ Technology Stack

### Frontend
- **Framework**: React Native (Cross-platform iOS/Android)
- **State Management**: Redux + Redux Thunk
- **Navigation**: React Navigation (Stack + Tabs)
- **UI Libraries**: React Native Paper, Vector Icons
- **Maps**: React Native Maps
- **Storage**: AsyncStorage (local persistence)
- **Image Handling**: Image Picker, Crop Picker
- **Voice**: Voice support (React Native Voice)

### Backend
- **Framework**: Flask (Python)
- **Database**: MySQL 5.7+
- **Authentication**: JWT (JSON Web Tokens)
- **API**: RESTful API with CORS
- **Caching**: Redis (for OTP, prices)
- **Background Jobs**: Celery (async tasks)
- **File Storage**: AWS S3 (product images)

### AI/ML
- **ML Library**: Scikit-learn
- **Models**:
  - Crop Recommendation (Random Forest Classifier)
  - Price Prediction (Linear Regression / ARIMA)
  - Disease Detection (CNN with TensorFlow - Phase 2)
- **Data Processing**: Pandas, NumPy

### Database
- **Primary**: MySQL
- **Cache**: Redis
- **Schema**: 10 tables with optimized indexes

### Infrastructure
- **Backend Hosting**: AWS/Heroku
- **Database**: AWS RDS (MySQL)
- **File Storage**: AWS S3
- **SMS Gateway**: Twilio/AWS SNS
- **Payment Gateway**: Razorpay/Stripe

---

## 📂 Project Structure

```
SmartFarming/
├── backend/                    # Flask backend
│   ├── app.py                 # Entry point
│   ├── requirements.txt        # Dependencies
│   ├── routes/
│   │   ├── auth.py            # Authentication (OTP, Login, Signup)
│   │   ├── farmer.py          # Farmer profile & dashboard
│   │   ├── products.py        # Product CRUD operations
│   │   ├── orders.py          # Order management
│   │   ├── ai_features.py     # AI predictions (Crop, Price, Fertilizer)
│   │   ├── wallet.py          # Earnings & withdrawals
│   │   └── weather.py         # Weather data
│   ├── models/
│   │   └── models.py          # Database models (Farmer, Product, Order, etc.)
│   ├── utils/
│   │   ├── validators.py      # Input validation
│   │   ├── ml_models.py       # Scikit-learn models
│   │   └── notifications.py   # SMS/Email
│   └── .env                   # Configuration
│
├── frontend/                   # React Native app
│   ├── screens/
│   │   ├── PhoneScreen.js              # Phone number entry
│   │   ├── OTPScreen.js                # OTP verification
│   │   ├── SignupScreen.js             # Account creation
│   │   ├── DashboardScreen.js          # Main dashboard
│   │   ├── ProductsScreen.js           # Products list
│   │   ├── AddProductScreen.js         # Add new product
│   │   ├── EditProductScreen.js        # Edit product
│   │   ├── OrdersScreen.js             # Orders list
│   │   ├── OrderDetailsScreen.js       # Order details
│   │   ├── WalletScreen.js             # Earnings & wallet
│   │   ├── AIFeaturesScreen.js         # AI suggestions hub
│   │   ├── CropRecommendationScreen.js # Crop recommendations
│   │   ├── PricePredictionScreen.js    # Price forecasts
│   │   ├── FertilizerScreen.js         # Fertilizer guide
│   │   └── ProfileScreen.js            # User profile
│   ├── components/
│   │   ├── StatCard.js        # Stat card component
│   │   ├── OrderCard.js       # Order display card
│   │   ├── ProductCard.js     # Product display card
│   │   ├── Button.js          # Custom button
│   │   ├── Input.js           # Custom input field
│   │   └── LoadingSpinner.js  # Loading indicator
│   ├── styles/
│   │   ├── colors.js          # Color palette
│   │   ├── spacing.js         # Spacing scale
│   │   └── fonts.js           # Typography
│   ├── services/
│   │   ├── api.js             # API service
│   │   ├── storage.js         # Local storage
│   │   └── auth.js            # Auth service
│   ├── redux/
│   │   ├── store.js           # Redux store
│   │   ├── actions/           # Action creators
│   │   └── reducers/          # Reducers
│   ├── navigation/
│   │   └── RootNavigator.js   # App navigation
│   ├── App.js                 # App entry point
│   └── package.json           # Dependencies
│
├── database/
│   └── schema.sql             # MySQL schema & tables
│
├── ARCHITECTURE.md            # Technical architecture
├── UIUX_DESIGN.md            # UI/UX specifications
├── SETUP_GUIDE.md            # Installation & setup
└── README.md                  # This file
```

---

## 🗄️ Database Schema

### Core Tables
1. **farmers** - User accounts with profile info
2. **products** - Farmer's product listings
3. **orders** - Buyer orders and transactions
4. **wallet** - Earnings and balance tracking
5. **transactions** - Payment history
6. **ai_predictions** - ML model results
7. **weather** - Weather data
8. **otp_verification** - OTP records
9. **notifications** - User notifications
10. **reviews** - Product reviews and ratings

Each table includes:
- Primary keys for unique identification
- Foreign keys for relationships
- Timestamps (created_at, updated_at)
- Indexes for query optimization

---

## 🔐 Security Features

- **OTP Verification**: SMS-based phone verification
- **Password Hashing**: Bcrypt password encryption
- **JWT Tokens**: Stateless authentication
- **CORS**: Cross-origin request handling
- **Input Validation**: Client and server-side validation
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: API rate limiting (Phase 2)
- **SSL/TLS**: HTTPS encryption
- **Bank Data Masking**: Secure bank account display

---

## 📊 API Endpoints Summary

### Authentication (`/api/auth`)
- `POST /send-otp` - Send OTP to phone
- `POST /verify-otp` - Verify OTP code
- `POST /signup` - Create account
- `POST /login` - Login with credentials
- `POST /forgot-password` - Password reset
- `POST /logout` - Logout user
- `GET /verify-token` - Check token validity

### Farmer Profile (`/api/farmer`)
- `GET /profile` - Get farmer info
- `PUT /profile` - Update profile
- `GET /dashboard` - Dashboard statistics
- `POST /complete-profile` - Complete signup

### Products (`/api/products`)
- `GET /` - Get all products
- `POST /` - Create new product
- `GET /{id}` - Get product details
- `PUT /{id}` - Update product
- `DELETE /{id}` - Delete product
- `GET /search` - Search products

### Orders (`/api/orders`)
- `GET /` - Get farmer's orders
- `POST /{id}/accept` - Accept order
- `POST /{id}/reject` - Reject order
- `PUT /{id}/status` - Update status
- `GET /{id}/track` - Track delivery

### Wallet (`/api/wallet`)
- `GET /balance` - Get balance & earnings
- `GET /transactions` - Transaction history
- `POST /withdraw` - Request withdrawal
- `GET /withdrawals` - Withdrawal history
- `POST /bank-account` - Add bank account
- `GET /summary` - Earnings summary

### AI Features (`/api/ai`)
- `GET /crop-recommendation` - Crop suggestions
- `GET /price-prediction/{id}` - Price forecast
- `GET /fertilizer-suggestion` - Fertilizer guide
- `POST /disease-detection` - Disease detection (Phase 2)
- `GET /predictions` - All predictions

### Weather (`/api/weather`)
- `GET /{location}` - Current weather
- `GET /{location}/forecast` - 7-day forecast
- `GET /{location}/alerts` - Weather alerts
- `GET /my-location` - Farmer's location weather

---

## 🎨 UI/UX Design

### Design System
- **Color Palette**: Green primary (#4CAF50), Orange secondary, Red for alerts
- **Typography**: Roboto font family, 16px base size
- **Spacing**: 8px grid system (4, 8, 12, 16, 24, 32px)
- **Components**: Cards, buttons, inputs, modals, bottom sheets
- **Icons**: Material Design Icons (48 icons)
- **Animations**: 200ms transitions, smooth interactions

### Screen Designs
1. **Auth Screens** - Clean, simple, step-by-step flow
2. **Dashboard** - Cards layout with stats, weather, AI suggestions
3. **Products** - Grid view with product cards, edit/delete actions
4. **Orders** - List view with status badges, quick actions
5. **Wallet** - Large balance card, transaction history list
6. **AI Features** - Card-based layout with detailed predictions

---

## 🚀 Getting Started

### Quick Setup (5 minutes)

#### Backend
```bash
cd backend
pip install -r requirements.txt
# Configure .env file
python app.py
```

#### Frontend
```bash
cd frontend
npm install
npx react-native run-android  # or run-ios
```

#### Database
```bash
mysql -u root -p < database/schema.sql
```

For detailed instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)

---

## 📈 Development Roadmap

### ✅ Phase 1: Core Farmer Module (Complete)
- Authentication & registration
- Farmer dashboard
- Product management (CRUD)
- Order management
- Wallet & earnings
- Weather integration
- AI features (Crop, Price, Fertilizer)

### 🔄 Phase 2: Advanced Features
- Disease detection with image recognition
- Voice support (Telugu, Hindi, English)
- Advanced analytics & insights
- Farmer community forum
- Blog & learning resources
- Compliance with APEDA regulations

### 📋 Phase 3: Buyer Module
- Buyer registration & profile
- Product search & filtering
- Shopping cart & checkout
- Order placement & tracking
- Ratings & reviews
- Favorites & wishlist

### 🔜 Phase 4: Integration & Expansion
- Multi-language support
- Video tutorials
- Offline mode
- Advanced payment options
- Logistics integration
- Government scheme information

---

## 💡 Key Insights & Real-World Impact

### Problem Solved
- **Revenue Increase**: Farmers earn 20-30% more by eliminating middlemen
- **Market Access**: Real-time price data helps farmers make better selling decisions
- **Crop Planning**: AI recommendations improve yield and profitability
- **Financial Inclusion**: Digital wallet enables easy banking access
- **Weather Resilience**: Timely alerts help farmers protect crops

### Target Users
- Small-scale farmers (1-5 hectares)
- Vegetable & fruit growers
- Grain farmers in monsoon season
- Farmers with smartphone access
- Age group: 25-65 years

### Market Opportunity
- India: 140 million farmers, 60% use smartphones
- Untapped market: Online farm-to-consumer platform
- Revenue Model: Commissions (2-3%), Premium features, Advertising

---

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical architecture & API design
- **[UIUX_DESIGN.md](./UIUX_DESIGN.md)** - UI/UX specifications & design system
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Installation & configuration
- **[DATABASE.md](./database/schema.sql)** - Database schema & relationships

---

## 🤝 Contributing

This project is built for farmers and society. Contributions are welcome!

### How to Contribute
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📞 Support & Contact

- **Email**: support@smartfarming.in
- **Phone**: +91-XXXX-XXXX-XXXX
- **Website**: https://www.smartfarming.in
- **Documentation**: [docs.smartfarming.in](https://docs.smartfarming.in)

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) file for details.

---

## 🙏 Acknowledgments

- **Target Audience**: Indian farmers striving for better livelihoods
- **AI Models**: Scikit-learn, TensorFlow communities
- **Open Source**: React Native, Flask, MySQL communities
- **Inspiration**: Farmer stories and real-world agricultural challenges

---

## 🎯 Vision

> **"Empowering farmers with technology to earn fair prices, plan better crops, and build sustainable livelihoods."**

Smart Farming is more than an app—it's a movement to revolutionize agriculture and give farmers the power they deserve.

---

**Built with ❤️ for Farmers | Made in India | Open Source**
