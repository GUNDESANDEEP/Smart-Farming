# Smart Farmer Marketplace - Docker & Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB storage minimum

### 1. Clone & Setup

```bash
git clone <repository>
cd SmartFarming
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```env
# Database
MYSQL_PASSWORD=your-secure-password
MYSQL_DB=smart_farming

# Authentication
JWT_SECRET_KEY=your-very-long-secret-key-minimum-32-chars

# Email Service
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=xxx
CLOUDINARY_API_SECRET=xxx

# Payments
RAZORPAY_KEY=key_xxxxx
RAZORPAY_SECRET=secret_xxxxx

# Firebase
FIREBASE_PROJECT_ID=your-project
```

### 3. Start Services

```bash
# Start all services (backend, frontend, MySQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 4. Access Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:5000 |
| MySQL | localhost:3306 |
| Redis | localhost:6379 |

### 5. Initialize Database

```bash
# Run migrations/schema setup
docker-compose exec backend python init_db.py
```

---

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Frontend        │  │  Backend         │               │
│  │  React:3000      │  │  Flask:5000      │               │
│  └──────┬───────────┘  └──────┬───────────┘               │
│         │                      │                          │
│         └──────────────────────┴──────────────┐           │
│                                               │           │
│                              ┌────────────────┼──────┐    │
│                              │                │      │    │
│                         ┌────▼──────┐  ┌─────▼──┐  │    │
│                         │ MySQL:3306│  │ Redis  │  │    │
│                         └───────────┘  └────────┘  │    │
│                                                    │    │
│                                            ┌───────▼──┐ │
│                                            │  Nginx   │ │
│                                            │  :80/:443│ │
│                                            └──────────┘ │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Deployment to Production

### Option 1: AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 20.04)
# 2. Install Docker & Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# 3. Clone repository and setup
git clone <repo>
cd SmartFarming
cp .env.example .env
# Edit .env with production values

# 4. Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Setup SSL with Let's Encrypt
# (Follow certbot instructions for HTTPS)
```

### Option 2: DigitalOcean App Platform

```bash
# 1. Create app.yaml in root directory
# 2. Upload to GitHub
# 3. Connect repository to DigitalOcean App Platform
# 4. Set environment variables in dashboard
# 5. Deploy automatically on push to main branch
```

### Option 3: Heroku

```bash
# 1. Create Heroku app
heroku create smartfarmer

# 2. Add buildpack for Python
heroku buildpacks:add heroku/python

# 3. Set environment variables
heroku config:set JWT_SECRET_KEY=xxx
heroku config:set MYSQL_PASSWORD=xxx
# ... other variables

# 4. Deploy
git push heroku main
```

### Option 4: Docker Hub & Automated Deployment

```bash
# Build and push images
docker-compose build
docker tag smartfarmer-backend username/smartfarmer-backend:1.0
docker tag smartfarmer-frontend username/smartfarmer-frontend:1.0
docker push username/smartfarmer-backend:1.0
docker push username/smartfarmer-frontend:1.0

# Pull and run on production server
docker pull username/smartfarmer-backend:1.0
docker pull username/smartfarmer-frontend:1.0
docker-compose up -d
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate strong JWT secret key
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Enable database backups
- [ ] Use environment variables for all secrets
- [ ] Enable rate limiting on API
- [ ] Setup CORS properly for frontend domain

### Performance
- [ ] Enable Redis caching
- [ ] Setup CDN for static assets
- [ ] Enable gzip compression
- [ ] Configure database indexes
- [ ] Setup monitoring & alerts
- [ ] Enable logging to ELK stack or similar
- [ ] Configure auto-scaling if cloud-hosted

### Reliability
- [ ] Setup automated backups
- [ ] Configure health checks
- [ ] Setup monitoring & alerting
- [ ] Document rollback procedures
- [ ] Test disaster recovery
- [ ] Setup load balancing if needed

### Monitoring & Logging

```bash
# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mysql

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend bash

# Monitor resource usage
docker stats

# Check container health
docker-compose ps
```

---

## Troubleshooting

### Backend not connecting to MySQL
```bash
# Check MySQL is running
docker-compose ps

# Check MySQL logs
docker-compose logs mysql

# Verify connection string
docker-compose exec backend python
>>> import MySQLdb
>>> conn = MySQLdb.connect(host='mysql', user='root', passwd='pass', db='smart_farming')
```

### Frontend can't connect to backend
```bash
# Check backend is running
curl http://localhost:5000/health

# Check network connectivity
docker network ls
docker network inspect smartfarming_smartfarmer-network
```

### Port already in use
```bash
# Find process using port
lsof -i :3000  # Find process on port 3000
kill -9 <PID>  # Kill process

# Or use different ports
docker-compose -f docker-compose.yml -p smartfarmer-prod up -d
```

### Database migration issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d mysql
# Wait for MySQL to start
sleep 30
docker-compose exec backend python init_db.py
```

---

## Performance Optimization

### Database
```sql
-- Add indexes for common queries
CREATE INDEX idx_product_farmer ON products(farmer_id);
CREATE INDEX idx_order_buyer ON orders(buyer_id);
CREATE INDEX idx_order_status ON orders(status);
CREATE FULLTEXT INDEX ft_products ON products(name, description);
```

### Redis Caching
```python
# Configure Redis for session caching and rate limiting
REDIS_URL = 'redis://redis:6379/0'
CACHE_TYPE = 'redis'
SESSION_TYPE = 'redis'
```

### Frontend
```javascript
// Enable code splitting and lazy loading
const Marketplace = lazy(() => import('./pages/buyer/Marketplace'));
const Dashboard = lazy(() => import('./pages/farmer/Dashboard'));
```

---

## Backup & Recovery

### Database Backup
```bash
# Backup MySQL database
docker-compose exec mysql mysqldump -u root -p smart_farming > backup.sql

# Restore from backup
docker-compose exec -T mysql mysql -u root -p smart_farming < backup.sql

# Automated backup (daily)
0 2 * * * docker-compose exec -T mysql mysqldump -u root -p smart_farming > /backups/smart_farming_$(date +\%Y\%m\%d).sql
```

### Data Export
```bash
# Export products
docker-compose exec mysql mysql -u root -p -e "SELECT * FROM products" smart_farming > products.csv

# Export users
docker-compose exec mysql mysql -u root -p -e "SELECT * FROM users" smart_farming > users.csv
```

---

## Health Checks

```bash
# Backend health
curl http://localhost:5000/health

# Frontend health
curl http://localhost:3000/

# Database connection
docker-compose exec backend python -c "from models.models import User; print('DB OK')"

# Redis connection
docker-compose exec redis redis-cli ping
```

---

## Scaling

### Horizontal Scaling (Multiple Backend Instances)
```yaml
# docker-compose.yml - add multiple backend instances
backend-1:
  # ... backend configuration
backend-2:
  # ... backend configuration
backend-3:
  # ... backend configuration

# Behind Nginx load balancer
nginx:
  # ... routes requests to backend-1, backend-2, backend-3
```

### Vertical Scaling
```bash
# Increase container resources
docker update --memory 2g smartfarmer-backend
docker update --cpus 2 smartfarmer-backend
```

---

## Support & Documentation

- API Docs: [Backend README.md](backend/README.md)
- Frontend Docs: [Frontend README.md](frontend/README.md)
- Issues: Create GitHub issue
- Email: support@smartfarmer.com

---

**Version:** 1.0.0  
**Last Updated:** June 2026  
**Status:** ✅ Production Ready

---

**Happy Farming! 🌾**
