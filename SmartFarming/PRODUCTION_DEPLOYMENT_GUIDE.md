# Smart Farming Platform - Complete Production Deployment Guide
**Version: 1.0** | **Status: Production Ready** | **Last Updated: 2024**

## Executive Summary
Complete deployment guide for the Smart Farming multi-module e-commerce platform (146 endpoints, 27 database tables, 5,900+ lines of code).

---

## Phase 1: Pre-Deployment Checklist ✓

### 1.1 Environment Verification
- [ ] Production server OS verified (Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+)
- [ ] Python 3.8+ installed: `python --version`
- [ ] MySQL 5.7+ or MariaDB 10.2+ installed: `mysql --version`
- [ ] Node.js 14+ installed (for frontend): `node --version`
- [ ] Git installed: `git --version`
- [ ] SSL certificates obtained and stored securely

### 1.2 System Resources
- [ ] Minimum 4GB RAM available
- [ ] Minimum 20GB free disk space
- [ ] Firewall ports open: 80, 443, 3306 (database - internal only), 5000 (Flask)
- [ ] Sufficient bandwidth allocated (estimate: 50-100 Mbps for production)
- [ ] Load balancer configured (if using distributed deployment)

### 1.3 Security Configuration
- [ ] SSH keys generated and secure
- [ ] Firewall rules configured
- [ ] DDoS protection enabled
- [ ] Rate limiting configured
- [ ] Web Application Firewall (WAF) enabled
- [ ] CORS policy defined: Allow specific origins only
- [ ] Database root password set to strong value (20+ characters)

### 1.4 Network Setup
- [ ] Domain name registered and DNS configured
- [ ] SSL/TLS certificates installed
- [ ] CDN configured (if applicable)
- [ ] Email service provider configured (Gmail, SendGrid, AWS SES)
- [ ] Webhook endpoints whitelisted if external

### 1.5 Monitoring & Logging
- [ ] Logging service configured (ELK Stack, Splunk, or Cloud Logging)
- [ ] Monitoring service setup (Prometheus, DataDog, New Relic)
- [ ] Alert thresholds configured
- [ ] Backup strategy defined
- [ ] Disaster recovery plan documented

---

## Phase 2: Database Setup

### 2.1 Create Production Database

```bash
# Connect to MySQL
mysql -u root -p

# Create database
CREATE DATABASE smart_farming CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smartfarming_user'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON smart_farming.* TO 'smartfarming_user'@'localhost';
FLUSH PRIVILEGES;

# Exit MySQL
EXIT;
```

### 2.2 Import Database Schema

```bash
# Import all schemas in order
mysql -u smartfarming_user -p smart_farming < database/farmer_schema.sql
mysql -u smartfarming_user -p smart_farming < database/buyer_schema.sql
mysql -u smartfarming_user -p smart_farming < database/admin_schema.sql
mysql -u smartfarming_user -p smart_farming < database/advanced_features_schema.sql

# Verify import
mysql -u smartfarming_user -p smart_farming -e "SHOW TABLES;"
```

### 2.3 Database Verification

```sql
-- Check total tables
SELECT COUNT(*) as total_tables FROM information_schema.tables 
WHERE table_schema='smart_farming';

-- Expected: 37+ tables (including views)

-- Check indexes
SELECT COUNT(*) as total_indexes FROM information_schema.statistics 
WHERE table_schema='smart_farming';

-- Expected: 60+ indexes

-- Check stored procedures (if any)
SELECT COUNT(*) as total_procedures FROM information_schema.routines 
WHERE routine_schema='smart_farming';
```

### 2.4 Data Backup Strategy

```bash
# Daily backup script (add to cron)
#!/bin/bash
BACKUP_DIR="/backups/smart_farming"
DATE=$(date +"%Y%m%d_%H%M%S")
mysqldump -u smartfarming_user -p${DB_PASSWORD} smart_farming \
  | gzip > $BACKUP_DIR/smart_farming_$DATE.sql.gz

# Add to crontab (daily at 2 AM)
# 0 2 * * * /opt/scripts/backup_database.sh
```

---

## Phase 3: Backend Deployment

### 3.1 Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify critical packages
pip list | grep -E "Flask|mysql-connector|PyJWT|requests"
```

### 3.2 Flask Configuration

Create `config.py`:

```python
import os
from datetime import timedelta

class ProductionConfig:
    # Flask Settings
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'smartfarming_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'smart_farming')
    DB_CHARSET = 'utf8mb4'
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-to-secure-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CORS
    CORS_ORIGINS = [
        'https://app.smartfarming.com',
        'https://admin.smartfarming.com',
        'https://www.smartfarming.com'
    ]
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/smart_farming/app.log'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'redis://localhost:6379'
    RATELIMIT_DEFAULT = '100/hour'

config = ProductionConfig()
```

### 3.3 Environment Variables Setup

Create `.env` file (never commit to Git):

```bash
# Database
DB_HOST=localhost
DB_USER=smartfarming_user
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_NAME=smart_farming

# JWT
JWT_SECRET_KEY=your-secret-key-here-min-32-chars

# Email Service
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Webhook Settings
WEBHOOK_TIMEOUT=10
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_DELAY=60

# Flask
FLASK_ENV=production
FLASK_DEBUG=0

# Admin Settings
ADMIN_EMAIL=admin@smartfarming.com
```

### 3.4 Register All Blueprint Routes

Create `app.py`:

```python
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
from config import ProductionConfig

app = Flask(__name__)
app.config.from_object(ProductionConfig)

# Initialize extensions
CORS(app, resources={
    r"/api/*": {
        "origins": app.config['CORS_ORIGINS'],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
JWTManager(app)

# Configure logging
logging.basicConfig(
    filename=app.config['LOG_FILE'],
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Register Blueprints - Farmer Module
from routes.farmer_auth import farmer_auth
from routes.farmer_profile import farmer_profile
from routes.farmer_products import farmer_products
from routes.farmer_orders import farmer_orders
from routes.farmer_wallet import farmer_wallet
from routes.farmer_ai import farmer_ai
from routes.farmer_weather import farmer_weather

app.register_blueprint(farmer_auth, url_prefix='/api')
app.register_blueprint(farmer_profile, url_prefix='/api')
app.register_blueprint(farmer_products, url_prefix='/api')
app.register_blueprint(farmer_orders, url_prefix='/api')
app.register_blueprint(farmer_wallet, url_prefix='/api')
app.register_blueprint(farmer_ai, url_prefix='/api')
app.register_blueprint(farmer_weather, url_prefix='/api')

# Register Blueprints - Buyer Module
from routes.buyer_auth import buyer_auth
from routes.buyer_profile import buyer_profile
from routes.buyer_products import buyer_products
from routes.buyer_cart import buyer_cart
from routes.buyer_orders import buyer_orders
from routes.buyer_payments import buyer_payments
from routes.buyer_reviews import buyer_reviews
from routes.buyer_wishlist import buyer_wishlist

app.register_blueprint(buyer_auth, url_prefix='/api')
app.register_blueprint(buyer_profile, url_prefix='/api')
app.register_blueprint(buyer_products, url_prefix='/api')
app.register_blueprint(buyer_cart, url_prefix='/api')
app.register_blueprint(buyer_orders, url_prefix='/api')
app.register_blueprint(buyer_payments, url_prefix='/api')
app.register_blueprint(buyer_reviews, url_prefix='/api')
app.register_blueprint(buyer_wishlist, url_prefix='/api')

# Register Blueprints - Admin Module
from routes.admin_auth import admin_auth
from routes.admin_dashboard import admin_dashboard
from routes.admin_users import admin_users
from routes.admin_products import admin_products
from routes.admin_orders import admin_orders
from routes.admin_analytics import admin_analytics
from routes.admin_monitoring import admin_monitoring
from routes.admin_advanced_features import admin_features

app.register_blueprint(admin_auth, url_prefix='/api')
app.register_blueprint(admin_dashboard, url_prefix='/api')
app.register_blueprint(admin_users, url_prefix='/api')
app.register_blueprint(admin_products, url_prefix='/api')
app.register_blueprint(admin_orders, url_prefix='/api')
app.register_blueprint(admin_analytics, url_prefix='/api')
app.register_blueprint(admin_monitoring, url_prefix='/api')
app.register_blueprint(admin_features, url_prefix='/api')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'success': False, 'error': 'Endpoint not found'}, 404

@app.errorhandler(500)
def server_error(error):
    return {'success': False, 'error': 'Internal server error'}, 500

if __name__ == '__main__':
    # For production, use gunicorn instead
    app.run(debug=False, host='0.0.0.0', port=5000)
```

### 3.5 Create Admin Super User

```python
# Create file: create_super_admin.py
import mysql.connector
from bcrypt import hashpw, gensalt
from datetime import datetime
import os

def create_super_admin():
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = db.cursor()
    
    email = input("Enter admin email: ")
    password = input("Enter admin password (min 8 chars): ")
    
    if len(password) < 8:
        print("Password must be at least 8 characters!")
        return
    
    hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
    
    try:
        cursor.execute("""
            INSERT INTO admins (
                email, password_hash, first_name, last_name,
                role, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            email,
            hashed_password,
            "System",
            "Administrator",
            "super_admin",
            "active",
            datetime.now()
        ))
        
        db.commit()
        print(f"✓ Super admin created: {email}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        cursor.close()
        db.close()

if __name__ == '__main__':
    create_super_admin()

# Run: python create_super_admin.py
```

---

## Phase 4: Frontend Deployment

### 4.1 React Native Build

```bash
# Install dependencies
cd frontend
npm install

# Build APK (Android)
npx expo build:android

# Build IPA (iOS)
npx expo build:ios

# Or for web build
npm run build
```

### 4.2 Deploy Web Frontend

```bash
# Build for production
npm run build

# Upload to web server
scp -r build/* user@server.com:/var/www/smartfarming

# Set up Nginx (if using)
# See Nginx configuration below
```

### 4.3 Nginx Configuration

Create `/etc/nginx/sites-available/smartfarming`:

```nginx
server {
    listen 443 ssl http2;
    server_name app.smartfarming.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/smartfarming.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartfarming.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # React frontend
    root /var/www/smartfarming;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security: block access to sensitive files
    location ~ /\. {
        deny all;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name app.smartfarming.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Phase 5: Production Server Setup

### 5.1 Gunicorn Configuration

Create `gunicorn_config.py`:

```python
# Gunicorn configuration for production
bind = "0.0.0.0:5000"
workers = 4  # 2 * CPU cores + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 5

# Logging
accesslog = "/var/log/smart_farming/access.log"
errorlog = "/var/log/smart_farming/error.log"
loglevel = "info"

# Performance
max_requests = 1000
max_requests_jitter = 100
```

### 5.2 Systemd Service

Create `/etc/systemd/system/smartfarming.service`:

```ini
[Unit]
Description=Smart Farming API Server
After=network.target mysql.service

[Service]
User=smartfarming
WorkingDirectory=/opt/smartfarming
Environment="PATH=/opt/smartfarming/venv/bin"
EnvironmentFile=/opt/smartfarming/.env
ExecStart=/opt/smartfarming/venv/bin/gunicorn \
    --config gunicorn_config.py app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.3 Start Services

```bash
# Enable and start service
sudo systemctl enable smartfarming
sudo systemctl start smartfarming

# Check status
sudo systemctl status smartfarming

# View logs
sudo journalctl -u smartfarming -f
```

---

## Phase 6: Security Hardening

### 6.1 SSL/TLS Configuration

```bash
# Install Certbot for Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot certonly --nginx -d smartfarming.com -d www.smartfarming.com

# Auto-renew (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 6.2 Firewall Rules

```bash
# UFW (Uncomplicated Firewall)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3306/tcp  # MySQL (from internal only)
```

### 6.3 Database Security

```sql
-- Remove default users
DROP USER IF EXISTS ''@'localhost';
DROP USER IF EXISTS ''@'%';
DROP USER IF EXISTS 'root'@'%';

-- Restrict database user
REVOKE ALL PRIVILEGES ON *.* FROM 'smartfarming_user'@'%';
GRANT ALL PRIVILEGES ON smart_farming.* TO 'smartfarming_user'@'localhost';
FLUSH PRIVILEGES;

-- Enable password validation
INSTALL PLUGIN validate_password SONAME 'validate_password.so';
SET GLOBAL validate_password_policy='MEDIUM';
```

### 6.4 API Rate Limiting

```python
# Add to Flask app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# Apply to sensitive endpoints
@app.route('/api/admin-auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def admin_login():
    # Login endpoint logic
    pass
```

---

## Phase 7: Monitoring & Logging

### 7.1 Application Logging

```python
# Configure Python logging
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    '/var/log/smart_farming/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app.logger.addHandler(handler)
```

### 7.2 Monitor Endpoints

```bash
# Test API connectivity
curl -X GET http://localhost:5000/api/health

# Test database connection
mysql -u smartfarming_user -p -e "SELECT 1;"

# Check logs
tail -f /var/log/smart_farming/app.log
tail -f /var/log/smart_farming/error.log
```

### 7.3 Monitoring Stack (Prometheus)

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'smartfarming'
    static_configs:
      - targets: ['localhost:5000']

  - job_name: 'mysql'
    static_configs:
      - targets: ['localhost:3306']
```

---

## Phase 8: Testing Before Go-Live

### 8.1 Endpoint Testing

```bash
#!/bin/bash

# Test Farmer Login
curl -X POST http://localhost:5000/api/farmer-auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","otp":"123456"}'

# Test Buyer Products
curl -X GET http://localhost:5000/api/buyer/products?page=1&limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test Admin Dashboard
curl -X GET http://localhost:5000/api/admin/dashboard \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Test Health Check
curl -X GET http://localhost:5000/api/health
```

### 8.2 Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/health

# Using wrk (better)
wrk -t12 -c400 -d30s http://localhost:5000/api/health
```

### 8.3 Database Performance

```sql
-- Check query performance
EXPLAIN SELECT * FROM products WHERE farmer_id = 1;

-- Check table sizes
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb
FROM information_schema.TABLES
WHERE table_schema = 'smart_farming'
ORDER BY size_mb DESC;

-- Check slow queries (if enabled)
SELECT * FROM mysql.slow_log LIMIT 10;
```

---

## Phase 9: Post-Deployment Verification

### 9.1 Functionality Checklist

#### Farmer Module (40 endpoints)
- [ ] Farmer OTP login working
- [ ] Farmer profile create/update
- [ ] Product creation & listing
- [ ] Order tracking
- [ ] Wallet balance updates
- [ ] Weather API integration
- [ ] AI crop prediction working

#### Buyer Module (52 endpoints)
- [ ] Buyer registration & login
- [ ] Product search & filtering
- [ ] Cart add/remove functionality
- [ ] Order checkout process
- [ ] Payment gateway integration
- [ ] Order tracking
- [ ] Product reviews working

#### Admin Module (54 endpoints)
- [ ] Admin login with email/password
- [ ] Dashboard statistics updating
- [ ] Farmer approval workflow
- [ ] Product moderation
- [ ] Order monitoring
- [ ] Analytics dashboard
- [ ] Dispute resolution
- [ ] Batch operations
- [ ] Email notifications sending
- [ ] Webhooks triggering

### 9.2 Performance Metrics

```
Target Metrics:
- API Response Time: < 200ms (p95)
- Database Query Time: < 100ms (p95)
- Server Uptime: > 99.9%
- Error Rate: < 0.1%
- Active Concurrent Users: > 1000
```

### 9.3 Security Verification

- [ ] SSL certificate valid and trusted
- [ ] HTTPS enforced on all endpoints
- [ ] SQL injection protection working
- [ ] XSS protection headers present
- [ ] CORS policy restricted to allowed origins
- [ ] Passwords properly hashed (bcrypt)
- [ ] JWT tokens expiring correctly
- [ ] Rate limiting preventing abuse
- [ ] Error messages not exposing sensitive info

---

## Phase 10: Disaster Recovery & Rollback

### 10.1 Backup Strategy

```bash
# Daily backups
0 2 * * * mysqldump -u smartfarming_user -p${PASS} smart_farming | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# Weekly code backups
0 3 * * 0 tar -czf /backups/code_$(date +%Y%m%d).tar.gz /opt/smartfarming/
```

### 10.2 Rollback Procedure

```bash
# Stop current version
sudo systemctl stop smartfarming

# Restore previous version
cd /opt/smartfarming
git checkout PREVIOUS_COMMIT

# Restart
sudo systemctl start smartfarming

# Check status
sudo systemctl status smartfarming
```

### 10.3 Database Rollback

```bash
# Restore from backup
mysql -u smartfarming_user -p smart_farming < /backups/db_20240101.sql.gz

# Verify data integrity
SELECT COUNT(*) FROM admins;
SELECT COUNT(*) FROM farmers;
SELECT COUNT(*) FROM buyers;
```

---

## Phase 11: Ongoing Maintenance

### 11.1 Weekly Tasks
- [ ] Check server disk space
- [ ] Review error logs
- [ ] Verify backup completion
- [ ] Monitor API performance metrics
- [ ] Check SSL certificate expiry

### 11.2 Monthly Tasks
- [ ] Database optimization (OPTIMIZE TABLE)
- [ ] Review and clean old logs
- [ ] Update dependencies (security patches)
- [ ] Database corruption check (mysqlcheck)
- [ ] Review admin logs for security issues

### 11.3 Quarterly Tasks
- [ ] Load testing
- [ ] Security audit
- [ ] Disaster recovery test
- [ ] Performance baseline measurement
- [ ] Database schema optimization

---

## Critical Contacts & Resources

### Support Contacts
- **Database Issues**: DevOps Team
- **API Issues**: Backend Team
- **Frontend Issues**: Frontend Team
- **Security**: Security Team

### Documentation Links
- API Documentation: `/docs/API_REFERENCE.md`
- Database Schema: `/docs/DATABASE_SCHEMA.md`
- Admin Guide: `/docs/ADMIN_GUIDE.md`
- Troubleshooting: `/docs/TROUBLESHOOTING.md`

### External Services
- Email Service: SendGrid / AWS SES
- SMS Service: Twilio (optional)
- Payment Gateway: Stripe / Razorpay
- Monitoring: DataDog / New Relic

---

## Deployment Completion Checklist

- [ ] All database tables created and verified
- [ ] Super admin account created
- [ ] Flask app configured and tested
- [ ] All blueprints registered successfully
- [ ] SSL certificates installed
- [ ] Nginx/Apache configured
- [ ] Gunicorn/uWSGI service running
- [ ] Monitoring and logging active
- [ ] Backups scheduled
- [ ] Security hardening complete
- [ ] Load testing passed
- [ ] All endpoints functional
- [ ] Performance metrics acceptable
- [ ] Team trained on procedures
- [ ] Go-live approval received

**Status: Ready for Production** ✅

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to database | Check DB_HOST, DB_USER, DB_PASSWORD, firewall rules |
| API returning 500 errors | Check Flask logs: `tail -f /var/log/smart_farming/error.log` |
| SSL certificate errors | Renew cert: `sudo certbot renew`, verify in Nginx |
| High API response time | Check database indexes, add caching (Redis) |
| Out of disk space | Clean old logs, archives; add more storage |
| Service won't start | Check systemd status: `sudo journalctl -u smartfarming -f` |

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintained By**: DevOps Team  
**Next Review**: Quarterly
