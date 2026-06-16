# 📋 Admin Module - Quick Reference Guide

**Platform:** Smart Farming e-commerce  
**Status:** ✅ Production Ready  
**Endpoints:** 54  
**Database Tables:** 10 new tables (27 total)

---

## 🚀 Quick Start

### 1. Admin Login
```bash
curl -X POST http://localhost:5000/api/admin-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@smartfarming.com",
    "password": "Admin@123"
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJ0eXAi...",
  "admin_id": 1,
  "role": "super_admin"
}
```

### 2. Use Token in Headers
```bash
curl -X GET http://localhost:5000/api/admin/dashboard \
  -H "Authorization: Bearer {access_token}"
```

---

## 📚 Endpoint Categories

### Authentication (6 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin-auth/login` | POST | Admin login |
| `/api/admin-auth/logout` | POST | Admin logout |
| `/api/admin-auth/verify-token` | GET | Check token validity |
| `/api/admin-auth/change-password` | PUT | Change admin password |
| `/api/admin-auth/profile` | GET | Get admin profile |
| `/api/admin-auth/create-admin` | POST | Create new admin (super admin only) |

### Dashboard (5 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/dashboard` | GET | Full dashboard stats |
| `/api/admin/dashboard/quick-stats` | GET | Quick numbers only |
| `/api/admin/dashboard/recent-activity` | GET | Recent admin actions |
| `/api/admin/dashboard/alerts` | GET | System alerts |
| `/api/admin/dashboard/health` | GET | Platform health |

### User Management (10 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/users/farmers` | GET | List all farmers |
| `/api/admin/users/farmers/{id}` | GET | Farmer details |
| `/api/admin/users/farmers/{id}/approve` | PUT | Approve farmer |
| `/api/admin/users/farmers/{id}` | DELETE | Delete farmer |
| `/api/admin/users/buyers` | GET | List all buyers |
| `/api/admin/users/buyers/{id}` | GET | Buyer details |
| `/api/admin/users/buyers/{id}` | DELETE | Delete buyer |
| `/api/admin/users/block` | POST | Block user |
| `/api/admin/users/blocks` | GET | List blocked users |
| `/api/admin/users/blocks/{id}/unblock` | PUT | Unblock user |

### Product Management (10 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/products/pending` | GET | Pending approvals |
| `/api/admin/products/{id}/approve` | POST | Approve product |
| `/api/admin/products/{id}/reject` | POST | Reject product |
| `/api/admin/products/{id}/flag` | POST | Flag for review |
| `/api/admin/products/{id}` | DELETE | Remove product |
| `/api/admin/products/all` | GET | All products |
| `/api/admin/products/categories` | GET | List categories |
| `/api/admin/products/categories` | POST | Create category |
| `/api/admin/products/categories/{id}` | PUT | Update category |
| `/api/admin/products/categories/{id}` | DELETE | Delete category |

### Order Management (8 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/orders` | GET | All orders |
| `/api/admin/orders/{id}` | GET | Order details |
| `/api/admin/orders/disputes` | GET | All disputes |
| `/api/admin/orders/disputes/{id}` | GET | Dispute details |
| `/api/admin/orders/disputes/{id}/resolve` | POST | Resolve dispute |
| `/api/admin/orders/refunds` | GET | Refund requests |
| `/api/admin/orders/refunds/{id}/approve` | POST | Approve refund |
| `/api/admin/orders/refunds/{id}/reject` | POST | Reject refund |

### Analytics (8 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/analytics/dashboard` | GET | Analytics overview |
| `/api/admin/analytics/sales/monthly` | GET | Monthly sales report |
| `/api/admin/analytics/products/top-selling` | GET | Top products |
| `/api/admin/analytics/farmers/top` | GET | Top farmers |
| `/api/admin/analytics/users/active` | GET | Active users |
| `/api/admin/analytics/revenue/breakdown` | GET | Revenue analysis |
| `/api/admin/analytics/trends` | GET | Sales trends |
| `/api/admin/analytics/generate-report` | POST | Custom report |

### AI Monitoring (7 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/ai-monitoring/crop-predictions` | GET | Crop predictions |
| `/api/admin/ai-monitoring/price-predictions` | GET | Price predictions |
| `/api/admin/ai-monitoring/disease-detection` | GET | Disease detection logs |
| `/api/admin/ai-monitoring/fertilizer-suggestions` | GET | Fertilizer logs |
| `/api/admin/ai-monitoring/stats` | GET | AI statistics |
| `/api/admin/ai-monitoring/models/performance` | GET | Model performance |
| `/api/admin/ai-monitoring/errors` | GET | Error analysis |

---

## 🔑 Common Query Parameters

### Pagination
```
?page=1&limit=20
```

### Filtering
```
?status=pending&sort_by=created_at
?days=30  # For analytics
?search=Ravi  # Search by name
```

### Date Range
```
?date_from=2026-05-01&date_to=2026-05-31
```

---

## 💻 Popular Use Cases

### Approve a Pending Farmer
```bash
curl -X PUT http://localhost:5000/api/admin/users/farmers/12/approve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Documents verified"}'
```

### Get Dashboard Stats
```bash
curl -X GET http://localhost:5000/api/admin/dashboard \
  -H "Authorization: Bearer {token}"
```

### Get Pending Products
```bash
curl -X GET 'http://localhost:5000/api/admin/products/pending?page=1&limit=20' \
  -H "Authorization: Bearer {token}"
```

### Approve Product
```bash
curl -X POST http://localhost:5000/api/admin/products/45/approve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Quality verified"}'
```

### Reject Product
```bash
curl -X POST http://localhost:5000/api/admin/products/45/reject \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Prohibited product"}'
```

### Get All Orders
```bash
curl -X GET 'http://localhost:5000/api/admin/orders?page=1&limit=20&status=pending' \
  -H "Authorization: Bearer {token}"
```

### Resolve Dispute
```bash
curl -X POST http://localhost:5000/api/admin/orders/disputes/1/resolve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "Full refund approved",
    "refund_amount": 450.99,
    "notes": "Product damaged in transit"
  }'
```

### Approve Refund
```bash
curl -X POST http://localhost:5000/api/admin/orders/refunds/5/approve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Approved due to quality issue"}'
```

### Get Analytics Dashboard
```bash
curl -X GET http://localhost:5000/api/admin/analytics/dashboard \
  -H "Authorization: Bearer {token}"
```

### Get Top Products
```bash
curl -X GET 'http://localhost:5000/api/admin/analytics/products/top-selling?limit=10&days=30' \
  -H "Authorization: Bearer {token}"
```

### Get AI Statistics
```bash
curl -X GET http://localhost:5000/api/admin/ai-monitoring/stats \
  -H "Authorization: Bearer {token}"
```

### Block User
```bash
curl -X POST http://localhost:5000/api/admin/users/block \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_type": "farmer",
    "user_id": 23,
    "reason": "Suspicious activity",
    "is_permanent": false,
    "expires_days": 30
  }'
```

---

## 🎯 Response Examples

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Paginated Response
```json
{
  "success": true,
  "farmers": [...],
  "pagination": {
    "total": 1250,
    "page": 1,
    "limit": 20,
    "pages": 63
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Only super admin can create admins"
}
```

---

## 🔐 Admin Roles

### Super Admin
- All permissions
- Can manage other admins
- Can delete users
- Can modify settings

### Moderator
- Approve farmers/products
- Resolve disputes
- Block users
- View analytics

### Analyst
- View-only access
- Can generate reports
- Cannot modify anything

---

## 📊 Database Tables

### Core Admin Tables
1. `admins` - Admin accounts
2. `admin_logs` - Action audit trail
3. `user_blocks` - Blocked users
4. `product_approvals` - Product moderation
5. `disputes` - Order disputes
6. `refund_requests` - Refund tracking
7. `categories` - Product categories
8. `ai_logs` - AI prediction logs
9. `analytics_reports` - Generated reports
10. `platform_settings` - System configuration

---

## ⚡ Performance Tips

1. **Use Pagination**
   - Always include `?page=1&limit=20`
   - Don't fetch all records without pagination

2. **Filter Early**
   - Use `?status=pending` to reduce results
   - Use date ranges to limit data

3. **Cache Results**
   - Dashboard stats don't change every second
   - Cache analytics results for 5-10 minutes

4. **Use Limit Parameter**
   - Top products: `?limit=10` (not 100)
   - Recent activity: `?limit=20` (not 500)

---

## 🧪 Testing Endpoints

### Postman Collection
```
Base URL: http://localhost:5000
Auth: Bearer Token in Authorization header

Requests:
1. POST /api/admin-auth/login (get token)
2. GET /api/admin/dashboard
3. GET /api/admin/users/farmers
4. GET /api/admin/products/pending
5. GET /api/admin/orders
6. GET /api/admin/analytics/dashboard
```

---

## 🚨 Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid data) |
| 401 | Unauthorized (invalid token) |
| 403 | Forbidden (permission denied) |
| 404 | Not found (resource doesn't exist) |
| 500 | Server error |

---

## 📞 Common Issues

### "Invalid token"
- Check Bearer token is included in Authorization header
- Token might have expired

### "Only super admin can..."
- Use super_admin account for this operation
- Moderator role doesn't have this permission

### "Farmer not found"
- Check farmer_id is correct
- Farmer might have been deleted

### "Paginate me" (too many results)
- Always include `?page=1&limit=20` in GET requests
- Don't request all records without pagination

---

## 🎓 Integration with Frontend

### React/React Native Example
```javascript
// Admin login
const login = async (email, password) => {
  const res = await fetch('/api/admin-auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  localStorage.setItem('admin_token', data.access_token);
  return data;
};

// Get dashboard
const getDashboard = async () => {
  const token = localStorage.getItem('admin_token');
  const res = await fetch('/api/admin/dashboard', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return res.json();
};

// Approve farmer
const approveFarmer = async (farmerId, notes) => {
  const token = localStorage.getItem('admin_token');
  const res = await fetch(`/api/admin/users/farmers/${farmerId}/approve`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ notes })
  });
  return res.json();
};
```

---

**Quick Ref Summary: 54 endpoints, 10 tables, 3 roles, complete platform management** ⚡
