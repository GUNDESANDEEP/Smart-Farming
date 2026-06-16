# 👨‍💼 Admin Module - Architecture & Implementation Plan

## 📋 Overview

The Admin Module provides complete platform management including:
- Dashboard with key metrics
- User management (approve, block, delete farmers/buyers)
- Product moderation (approve, remove, categorize)
- Order monitoring and dispute resolution
- Analytics and reporting
- AI system monitoring and logs

---

## 🗄️ Database Schema

### New Tables Required

#### 1. **admins** (Admin accounts)
```sql
CREATE TABLE IF NOT EXISTS admins (
  admin_id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50),
  role ENUM('super_admin', 'moderator', 'analyst') DEFAULT 'moderator',
  permissions JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login DATETIME,
  is_active BOOLEAN DEFAULT TRUE,
  INDEX idx_email (email),
  INDEX idx_role (role)
);
```

#### 2. **admin_logs** (Admin activity audit trail)
```sql
CREATE TABLE IF NOT EXISTS admin_logs (
  log_id INT PRIMARY KEY AUTO_INCREMENT,
  admin_id INT NOT NULL,
  action VARCHAR(100) NOT NULL,
  module VARCHAR(50),
  entity_type VARCHAR(50),
  entity_id INT,
  old_values JSON,
  new_values JSON,
  description TEXT,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE,
  INDEX idx_admin (admin_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
);
```

#### 3. **user_blocks** (Blocked users)
```sql
CREATE TABLE IF NOT EXISTS user_blocks (
  block_id INT PRIMARY KEY AUTO_INCREMENT,
  buyer_id INT,
  farmer_id INT,
  reason VARCHAR(255) NOT NULL,
  blocked_by INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  is_permanent BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  FOREIGN KEY (blocked_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_buyer (buyer_id),
  INDEX idx_farmer (farmer_id),
  INDEX idx_expires (expires_at)
);
```

#### 4. **product_approvals** (Product moderation)
```sql
CREATE TABLE IF NOT EXISTS product_approvals (
  approval_id INT PRIMARY KEY AUTO_INCREMENT,
  product_id INT NOT NULL,
  farmer_id INT NOT NULL,
  status ENUM('pending', 'approved', 'rejected', 'flagged') DEFAULT 'pending',
  reason_if_rejected TEXT,
  reviewed_by INT,
  reviewed_at DATETIME,
  notes TEXT,
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  UNIQUE KEY unique_product (product_id),
  INDEX idx_status (status),
  INDEX idx_farmer (farmer_id)
);
```

#### 5. **disputes** (Order disputes)
```sql
CREATE TABLE IF NOT EXISTS disputes (
  dispute_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  farmer_id INT NOT NULL,
  complaint_type VARCHAR(100),
  description TEXT,
  status ENUM('open', 'investigating', 'resolved', 'closed') DEFAULT 'open',
  resolved_by INT,
  resolution TEXT,
  resolution_date DATETIME,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  FOREIGN KEY (resolved_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_order (order_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
);
```

#### 6. **refund_requests** (Refund processing)
```sql
CREATE TABLE IF NOT EXISTS refund_requests (
  refund_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  buyer_id INT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  reason VARCHAR(255),
  status ENUM('requested', 'approved', 'rejected', 'processed') DEFAULT 'requested',
  approved_by INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed_at DATETIME,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE CASCADE,
  FOREIGN KEY (approved_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_order (order_id),
  INDEX idx_status (status)
);
```

#### 7. **categories** (Product categories management)
```sql
CREATE TABLE IF NOT EXISTS categories (
  category_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  icon_url VARCHAR(255),
  parent_category_id INT,
  is_active BOOLEAN DEFAULT TRUE,
  created_by INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_category_id) REFERENCES categories(category_id),
  FOREIGN KEY (created_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_name (name),
  INDEX idx_active (is_active)
);
```

#### 8. **ai_logs** (AI prediction/feature logs)
```sql
CREATE TABLE IF NOT EXISTS ai_logs (
  log_id INT PRIMARY KEY AUTO_INCREMENT,
  farmer_id INT,
  log_type ENUM('crop_prediction', 'price_prediction', 'disease_detection', 'fertilizer_suggestion') NOT NULL,
  input_data JSON,
  output_data JSON,
  model_version VARCHAR(50),
  confidence_score DECIMAL(3, 2),
  execution_time_ms INT,
  status ENUM('success', 'error', 'warning') DEFAULT 'success',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
  INDEX idx_farmer (farmer_id),
  INDEX idx_type (log_type),
  INDEX idx_created (created_at)
);
```

#### 9. **analytics_reports** (Generated reports)
```sql
CREATE TABLE IF NOT EXISTS analytics_reports (
  report_id INT PRIMARY KEY AUTO_INCREMENT,
  report_type VARCHAR(50),
  period_start DATE,
  period_end DATE,
  data JSON,
  generated_by INT,
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (generated_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_type (report_type),
  INDEX idx_period (period_start, period_end)
);
```

#### 10. **platform_settings** (Admin configuration)
```sql
CREATE TABLE IF NOT EXISTS platform_settings (
  setting_id INT PRIMARY KEY AUTO_INCREMENT,
  setting_key VARCHAR(100) NOT NULL UNIQUE,
  setting_value JSON,
  description TEXT,
  updated_by INT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (updated_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
  INDEX idx_key (setting_key)
);
```

---

## 🔌 Backend API Routes Structure

### 1. **Admin Authentication** (`/api/admin-auth`)
```
POST   /login                  → Login with email/password
POST   /logout                 → Logout
GET    /verify-token          → Verify JWT token
PUT    /change-password        → Change password
GET    /profile                → Get admin profile
```

### 2. **Dashboard** (`/api/admin/dashboard`)
```
GET    /                       → Main dashboard stats
GET    /quick-stats            → Key metrics
GET    /recent-activity        → Recent actions
GET    /alerts                 → System alerts
```

### 3. **User Management** (`/api/admin/users`)
```
GET    /farmers                → List all farmers
GET    /farmers/{id}           → Farmer details
PUT    /farmers/{id}/approve   → Approve farmer
DELETE /farmers/{id}           → Delete farmer

GET    /buyers                 → List all buyers
GET    /buyers/{id}            → Buyer details
DELETE /buyers/{id}            → Delete buyer

POST   /block                  → Block user (farmer/buyer)
GET    /blocks                 → List blocked users
PUT    /blocks/{id}/unblock    → Unblock user
```

### 4. **Product Management** (`/api/admin/products`)
```
GET    /pending                → Pending products for approval
POST   /{id}/approve           → Approve product
POST   /{id}/reject            → Reject product
DELETE /{id}                   → Remove fake product
GET    /all                    → All products with status

GET    /categories             → List categories
POST   /categories             → Create category
PUT    /categories/{id}        → Update category
DELETE /categories/{id}        → Delete category
```

### 5. **Order Management** (`/api/admin/orders`)
```
GET    /                       → All orders
GET    /{id}                   → Order details
GET    /disputes               → List disputes
POST   /disputes/{id}/resolve  → Resolve dispute
GET    /refunds                → Refund requests
POST   /refunds/{id}/approve   → Approve refund
POST   /refunds/{id}/reject    → Reject refund
```

### 6. **Analytics** (`/api/admin/analytics`)
```
GET    /dashboard              → Analytics dashboard
GET    /sales/monthly          → Monthly sales report
GET    /products/top-selling   → Top selling products
GET    /users/active           → Active users
GET    /revenue/breakdown      → Revenue breakdown
GET    /trends                 → Sales trends
```

### 7. **AI Monitoring** (`/api/admin/ai-monitoring`)
```
GET    /crop-predictions       → Crop prediction logs
GET    /price-predictions      → Price prediction logs
GET    /disease-detection      → Disease detection logs
GET    /fertilizer-suggestions → Fertilizer suggestion logs
GET    /stats                  → AI usage statistics
```

### 8. **Settings** (`/api/admin/settings`)
```
GET    /                       → Get all settings
PUT    /{key}                  → Update setting
GET    /logs                   → Admin action logs
```

---

## 📱 Admin Dashboard UI Sections

### 1. **Dashboard Overview**
- Total Farmers (count, new this month)
- Total Buyers (count, new this month)
- Total Orders (pending, completed)
- Total Revenue (this month, breakdown by source)
- Recent Activities (last 10 actions)

### 2. **Quick Actions**
- View Pending Approvals (products, farmers)
- Active Disputes
- Pending Refunds
- Blocked Users

### 3. **Monitoring**
- Order Status Overview
- AI System Health
- System Performance Metrics

---

## 🎨 Admin Interface Differences

### Permissions Based Access
```
Super Admin: All features
Moderator: User management, Product approval, Disputes
Analyst: View-only analytics and reports
```

### Security
- Email/Password login (more secure than farmers/buyers)
- Session-based authentication
- Admin action logging
- IP-based access control

---

## 📊 API Endpoints Summary

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| **Authentication** | 5 | Admin login/session |
| **Dashboard** | 4 | Overview metrics |
| **User Management** | 9 | Farmer/Buyer management |
| **Product Management** | 7 | Product approval & categories |
| **Order Management** | 7 | Order/Dispute/Refund handling |
| **Analytics** | 6 | Reports & insights |
| **AI Monitoring** | 5 | AI system logs |
| **Settings** | 2 | Platform config & logs |
| **TOTAL** | **45 endpoints** | Complete admin panel |

---

## 🔐 Role-Based Access Control

### Super Admin
- ✅ Full access to all features
- ✅ User account management
- ✅ Settings modification
- ✅ Admin log access
- ✅ Refund approval

### Moderator
- ✅ User management (approve/block)
- ✅ Product approval/rejection
- ✅ Dispute resolution
- ✅ View-only analytics
- ❌ Cannot modify settings
- ❌ Cannot manage other admins

### Analyst
- ✅ View analytics & reports
- ✅ View user data
- ✅ View order data
- ✅ View AI logs
- ❌ Cannot perform any modifications

---

## 📈 Data Models

### Admin Profile
```json
{
  "admin_id": 1,
  "email": "admin@smartfarming.com",
  "first_name": "Admin",
  "last_name": "User",
  "role": "super_admin",
  "permissions": ["users_manage", "products_approve", "analytics_view"],
  "last_login": "2026-06-03T10:30:00",
  "is_active": true
}
```

### Dashboard Statistics
```json
{
  "total_farmers": 1250,
  "new_farmers_this_month": 45,
  "total_buyers": 5600,
  "new_buyers_this_month": 320,
  "total_orders": 12450,
  "pending_orders": 34,
  "total_revenue": 45000000,
  "revenue_this_month": 3200000
}
```

### User Block Record
```json
{
  "block_id": 1,
  "user_type": "farmer",
  "user_id": 123,
  "user_name": "Ravi Kumar",
  "reason": "Fake products",
  "blocked_by": "Admin User",
  "created_at": "2026-06-01T10:00:00",
  "is_permanent": true
}
```

---

## 🔄 Admin Workflows

### Product Approval Flow
```
Farmer uploads product → Pending approval
    ↓
Admin reviews product
    ↓
Approve → Product visible to buyers
OR
Reject → Product removed, farmer notified
OR
Flag → Needs further investigation
```

### Dispute Resolution Flow
```
Buyer creates dispute → Open
    ↓
Admin investigates
    ↓
Resolve with refund → Order refunded
OR
Resolve without refund → Dispute closed
OR
Escalate → Further investigation needed
```

### Farmer Approval Flow
```
Farmer registers → Pending approval
    ↓
Admin verifies information
    ↓
Approve → Farmer can start selling
OR
Reject → Farmer account deleted
```

---

## 🚀 Implementation Phases

### Phase 1: Core Backend
- [ ] Create admin tables
- [ ] Build admin auth
- [ ] Create dashboard endpoints
- [ ] Implement user management

### Phase 2: Moderation
- [ ] Product approval system
- [ ] Dispute resolution
- [ ] Refund management

### Phase 3: Analytics
- [ ] Build analytics endpoints
- [ ] Create report generation
- [ ] AI monitoring

### Phase 4: Frontend
- [ ] Admin login screen
- [ ] Dashboard
- [ ] Management screens
- [ ] Analytics screens

---

## 📊 File Structure

```
admin_schema.sql                    (Database)
admin_auth.py                       (Authentication)
admin_dashboard.py                  (Dashboard)
admin_users.py                      (User Management)
admin_products.py                   (Product Management)
admin_orders.py                     (Order Management)
admin_analytics.py                  (Analytics)
admin_monitoring.py                 (AI Monitoring)
admin_settings.py                   (Settings)
```

---

**Ready to implement! Building 45+ admin endpoints with complete role-based access control.** 🚀
