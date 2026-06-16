# Smart Farm Marketplace - React Frontend

## Setup Instructions

### Prerequisites
- Node.js v14+ and npm v6+
- Backend API running on `http://localhost:5000`

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm start
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── pages/
│   │   ├── LandingPage.js
│   │   ├── LoginPage.js
│   │   ├── SignupPage.js
│   │   ├── FarmerDashboard.js
│   │   ├── BuyerDashboard.js
│   │   └── AdminDashboard.js
│   ├── components/
│   │   ├── Navigation.js
│   │   └── ProtectedRoute.js
│   ├── services/
│   │   ├── api.js
│   │   └── authStore.js
│   ├── hooks/
│   │   └── useAuth.js
│   ├── styles/
│   │   ├── index.css
│   │   ├── landing.css
│   │   ├── auth.css
│   │   ├── navigation.css
│   │   └── dashboard.css
│   ├── App.js
│   └── index.js
├── package.json
├── .env
└── .gitignore
```

## Key Features

### Authentication
- Farmer, Buyer, and Admin login/signup
- Email and OTP verification
- JWT-based authentication
- Role-based access control
- Forgot password functionality

### Farmer Dashboard
- Add, edit, delete products
- Inventory management
- Order management
- Real-time earnings tracking
- Weather dashboard
- Crop recommendations

### Buyer Dashboard
- Browse and search products
- Advanced filters
- Shopping cart
- Wishlist
- Order tracking
- Payment gateway integration
- Reviews and ratings

### Admin Dashboard
- User management
- Product approval workflow
- Order monitoring
- Revenue analytics
- AI usage logs
- Dispute resolution

## UI/UX Features

- Modern glassmorphism design
- Purple-blue gradient theme
- Responsive mobile-first layout
- Smooth page transitions
- Dark mode support
- Lottie animations
- Professional dashboard cards

## API Endpoints

### Authentication
- `POST /api/auth/farmer-login` - Farmer login
- `POST /api/buyer-auth/login` - Buyer login
- `POST /api/admin-auth/login` - Admin login
- `POST /api/auth/send-otp` - Send OTP
- `POST /api/auth/verify-otp` - Verify OTP
- `POST /api/auth/farmer-signup` - Farmer registration
- `POST /api/buyer-auth/signup` - Buyer registration

### Farmer APIs
- `GET /api/farmer/profile` - Get profile
- `GET /api/farmer/products` - List products
- `POST /api/farmer/products` - Add product
- `PUT /api/farmer/products/:id` - Update product
- `DELETE /api/farmer/products/:id` - Delete product
- `GET /api/farmer/orders` - List orders
- `GET /api/farmer/earnings` - Get earnings

### Buyer APIs
- `GET /api/buyer/products` - List products
- `GET /api/buyer/products/search` - Search products
- `GET /api/buyer/cart` - Get cart
- `POST /api/buyer/cart/add` - Add to cart
- `GET /api/buyer/orders` - List orders
- `POST /api/buyer/orders` - Create order
- `GET /api/buyer/wishlist` - Get wishlist

### Admin APIs
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/users` - List users
- `GET /api/admin/products/pending` - Pending products
- `GET /api/admin/orders` - List orders
- `GET /api/admin/analytics` - Analytics data

## Technologies Used

- **React** 18.2.0 - UI Library
- **React Router** 6.14.2 - Routing
- **Axios** 1.4.0 - HTTP Client
- **Zustand** 4.3.9 - State Management
- **React Hot Toast** 2.4.1 - Notifications
- **Recharts** 2.8.0 - Charts
- **React Icons** 4.11.0 - Icons
- **Lottie React** 2.4.0 - Animations

## Environment Variables

```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
REACT_APP_APP_NAME=SmartFarm Marketplace
REACT_APP_VERSION=1.0.0
```

## Deployment

### Vercel
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Deploy the build folder
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Troubleshooting

### CORS Issues
- Ensure backend has CORS enabled
- Check API_URL in .env

### Authentication Issues
- Clear localStorage
- Check JWT token expiration
- Verify backend credentials

### API Connection
- Start backend server on port 5000
- Check network tab in DevTools
- Verify API endpoints are correct

## Contributing

1. Create feature branch: `git checkout -b feature/feature-name`
2. Commit changes: `git commit -m 'Add feature'`
3. Push to branch: `git push origin feature/feature-name`
4. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

For support, email support@smartfarm.com or visit https://smartfarm.com/support
