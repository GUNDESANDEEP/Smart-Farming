# 🚀 DEPLOYMENT GUIDE - PRODUCTION READINESS

**Smart Farming Admin Module - Production Deployment**  
**Date:** June 2026  
**Status:** Ready to Deploy

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Database Setup
- [ ] MySQL server running on production
- [ ] Database `smart_farming_db` created
- [ ] Run `admin_schema.sql` to create 10 new tables
- [ ] Verify all 27 tables exist
- [ ] Create initial super admin account
- [ ] Test database connection

### Backend Configuration
- [ ] Flask app configured for production
- [ ] JWT secret key configured (non-default)
- [ ] All 7 admin routes registered as blueprints
- [ ] CORS enabled for frontend domain
- [ ] Error logging configured
- [ ] Database connection pooling set up

### Security Verification
- [ ] SSL certificates installed (HTTPS enabled)
- [ ] CORS restricted to trusted origins
- [ ] JWT token expiry set (recommend 24 hours)
- [ ] Password hashing verified (bcrypt with salt rounds)
- [ ] Rate limiting configured (optional)
- [ ] Admin login attempts logged

### Testing Before Deployment
- [ ] All 54 endpoints tested locally
- [ ] Authentication flow validated
- [ ] Pagination tested
- [ ] Error scenarios handled
- [ ] Database transactions working
- [ ] Audit logging functional

---

## 🔧 DEPLOYMENT STEPS

### Step 1: Database Setup
```bash
# Connect to production MySQL
mysql -h production-server.com -u admin -p

# Create database if not exists
CREATE DATABASE smart_farming_db;
USE smart_farming_db;

# Import schema
SOURCE /path/to/admin_schema.sql;

# Verify tables
SHOW TABLES;
# Should show 27 tables
```

### Step 2: Create Super Admin Account
```sql
INSERT INTO admins (
  email,
  password_hash,
  first_name,
  last_name,
  role,
  is_active
) VALUES (
  'superadmin@smartfarming.com',
  '$2b$12$abcdefghijklmnopqrstuvwxyz123456789',  -- bcrypt hash
  'Super',
  'Admin',
  'super_admin',
  TRUE
);
```

### Step 3: Update Flask Configuration
```python
# config.py
import os

class ProductionConfig:
    # Database
    DATABASE = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': 'smart_farming_db'
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # Non-default
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION = 86400  # 24 hours
    
    # Security
    CORS_ORIGINS = ['https://app.smartfarming.com', 'https://admin.smartfarming.com']
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/smartfarming/admin.log'

# main.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config.from_object('config.ProductionConfig')

# Initialize extensions
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
JWTManager(app)

# Register blueprints
from backend.routes.admin_auth import admin_auth_bp
from backend.routes.admin_dashboard import admin_dashboard_bp
from backend.routes.admin_users import admin_users_bp
from backend.routes.admin_products import admin_products_bp
from backend.routes.admin_orders import admin_orders_bp
from backend.routes.admin_analytics import admin_analytics_bp
from backend.routes.admin_monitoring import admin_monitoring_bp

app.register_blueprint(admin_auth_bp)
app.register_blueprint(admin_dashboard_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(admin_products_bp)
app.register_blueprint(admin_orders_bp)
app.register_blueprint(admin_analytics_bp)
app.register_blueprint(admin_monitoring_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 4: Deploy Backend
```bash
# Option A: Docker Deployment
docker build -t smartfarming-admin:latest .
docker run -d --name smartfarming-admin \
  -e DB_HOST=db.example.com \
  -e JWT_SECRET_KEY=your_secret_key \
  -p 5000:5000 \
  smartfarming-admin:latest

# Option B: Traditional Server
cd /var/www/smartfarming
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Step 5: Verify Deployment
```bash
# Test authentication endpoint
curl -X POST https://api.smartfarming.com/api/admin-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@smartfarming.com",
    "password": "InitialPassword123!"
  }'

# Expected: 200 response with access_token
```

---

## 🔍 MONITORING POST-DEPLOYMENT

### Health Check Endpoints
```bash
# Every 5 minutes
curl https://api.smartfarming.com/api/admin/dashboard/health

# Log response time and status code
```

### Monitoring Dashboard
- API Response times (target: < 200ms)
- Error rate (target: < 1%)
- Database connection pool status
- Admin login attempts
- Failed API requests

### Alerting Rules
- [ ] Response time > 500ms → Alert
- [ ] Error rate > 5% → Alert
- [ ] Database connection failures → Critical
- [ ] Unauthorized access attempts → Warning
- [ ] Admin action anomalies → Warning

---

## 📊 POST-DEPLOYMENT VERIFICATION

### Test All Endpoint Categories
```bash
TOKEN="<your_jwt_token>"

# 1. Dashboard (5 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/dashboard

# 2. Users (10 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/users/farmers?page=1

# 3. Products (10 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/products/pending

# 4. Orders (8 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/orders?page=1

# 5. Analytics (8 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/analytics/dashboard

# 6. AI Monitoring (7 endpoints)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.smartfarming.com/api/admin/ai-monitoring/stats
```

---

## 🛡️ SECURITY HARDENING

### SSL/TLS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.smartfarming.com;
    
    ssl_certificate /etc/ssl/certs/smartfarming.crt;
    ssl_certificate_key /etc/ssl/private/smartfarming.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
}
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to auth endpoints
@admin_auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass
```

### Environment Variables
```bash
# .env (Production Server)
DB_HOST=db.smartfarming.com
DB_USER=smartfarming_user
DB_PASSWORD=<strong_password>
JWT_SECRET_KEY=<random_secret_key>
ADMIN_EMAIL=superadmin@smartfarming.com
LOG_LEVEL=INFO
```

---

## 📈 SCALING CONSIDERATIONS

### Database Optimization
```sql
-- Add more indexes for production
CREATE INDEX idx_admin_logs_admin_created 
ON admin_logs(admin_id, created_at);

CREATE INDEX idx_disputes_status_created 
ON disputes(status, created_at);

-- Set up connection pooling
-- Recommended: 10-20 connections per app instance
```

### Caching Layer
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@admin_dashboard_bp.route('/')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_dashboard():
    return {...}
```

### Load Balancing
```nginx
upstream admin_backend {
    server app1.internal:5000 weight=1;
    server app2.internal:5000 weight=1;
    server app3.internal:5000 weight=1;
}

server {
    listen 443 ssl;
    
    location / {
        proxy_pass http://admin_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ✅ PRODUCTION CHECKLIST - FINAL

- [ ] Database migrated & verified
- [ ] Super admin account created
- [ ] Backend deployed & running
- [ ] SSL certificates installed
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Logging configured & verified
- [ ] Monitoring alerts set up
- [ ] Backup strategy implemented
- [ ] All 54 endpoints tested
- [ ] Role-based access verified
- [ ] Audit logging functional
- [ ] Performance baseline established
- [ ] Incident response plan ready

---

## 🚨 ROLLBACK PROCEDURE

If issues occur:
```bash
# 1. Check application logs
tail -f /var/log/smartfarming/admin.log

# 2. Stop current deployment
docker stop smartfarming-admin

# 3. Restore previous version
docker run -d --name smartfarming-admin-v1 \
  -e DB_HOST=db.example.com \
  smartfarming-admin:v1.0

# 4. Verify functionality
curl https://api.smartfarming.com/api/admin/dashboard/health

# 5. Notify team
```

---

**Deployment Ready! Proceed to Frontend Development.** ✅
