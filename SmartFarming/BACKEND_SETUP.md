# Smart Farm Marketplace - Backend Setup Guide

## Prerequisites

- Python 3.8+
- MySQL 5.7+ or MySQL 8.0+
- pip (Python package manager)
- Git

## Installation Steps

### 1. Clone or Navigate to Backend Folder

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the backend folder:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=SmartFarmingDB

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=86400

# Email Configuration (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Payment Gateway (Razorpay)
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Weather API
WEATHER_API_KEY=your-openweathermap-api-key
WEATHER_API_URL=https://api.openweathermap.org/data/3.0/stations

# AI/ML Configuration
CROP_RECOMMENDATION_MODEL_PATH=models/crop_recommendation.pkl
PRICE_FORECAST_MODEL_PATH=models/price_forecast.pkl

# AWS Configuration (if using S3 for file uploads)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=smartfarm-uploads
AWS_REGION=ap-south-1

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 5. Create MySQL Database

```bash
# Open MySQL terminal
mysql -u root -p

# Create database
CREATE DATABASE SmartFarmingDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Exit MySQL
exit
```

### 6. Run Database Migrations

```bash
# Import schema
mysql -u root -p SmartFarmingDB < database/schema.sql
mysql -u root -p SmartFarmingDB < database/buyer_schema.sql
mysql -u root -p SmartFarmingDB < database/admin_schema.sql
mysql -u root -p SmartFarmingDB < database/advanced_features_schema.sql

# Or from project root
mysql -u root -p SmartFarmingDB < DATABASE_SCHEMA.sql
```

### 7. Run the Application

```bash
python app.py
```

Server will start at: `http://localhost:5000`

## Project Structure

```
backend/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── models/
│   ├── models.py                  # Database models
│   └── __init__.py
├── routes/
│   ├── auth.py                    # Farmer authentication
│   ├── buyer_auth.py              # Buyer authentication
│   ├── admin_auth.py              # Admin authentication
│   ├── farmer.py                  # Farmer endpoints
│   ├── buyer_products.py          # Buyer product browsing
│   ├── buyer_cart.py              # Shopping cart
│   ├── buyer_orders.py            # Buyer orders
│   ├── buyer_payments.py          # Payment processing
│   ├── buyer_profile.py           # Buyer profile
│   ├── buyer_reviews.py           # Product reviews
│   ├── admin_dashboard.py         # Admin dashboard
│   ├── admin_users.py             # User management
│   ├── admin_products.py          # Product management
│   ├── admin_orders.py            # Order management
│   ├── admin_analytics.py         # Analytics
│   ├── admin_monitoring.py        # System monitoring
│   ├── admin_advanced_features.py # Advanced features
│   ├── orders.py                  # Order management
│   ├── products.py                # Product management
│   ├── wallet.py                  # Wallet management
│   ├── weather.py                 # Weather data
│   ├── ai_features.py             # AI features
│   └── __init__.py
├── utils/
│   ├── decorators.py              # Custom decorators
│   ├── validators.py              # Input validation
│   ├── helpers.py                 # Helper functions
│   ├── pagination.py              # Pagination utilities
│   ├── email_service.py           # Email functionality
│   ├── sms_service.py             # SMS functionality
│   ├── file_upload.py             # File upload handling
│   └── __init__.py
└── database/
    ├── schema.sql                 # Core schema
    ├── buyer_schema.sql           # Buyer module schema
    ├── admin_schema.sql           # Admin module schema
    └── advanced_features_schema.sql # Advanced features schema
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=backend

# Run comprehensive test suite
python -m pytest tests/test_comprehensive.py -v
```

## Development Commands

```bash
# Start development server with auto-reload
flask run --reload

# Interactive shell
flask shell

# Database initialization
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()

# Run Celery (for background tasks)
celery -A app.celery worker -l info
```

## API Testing with cURL

```bash
# Farmer Login
curl -X POST http://localhost:5000/api/auth/farmer-login \
  -H "Content-Type: application/json" \
  -d '{"email":"farmer@example.com","password":"password123"}'

# Get Farmer Products
curl -X GET http://localhost:5000/api/farmer/products \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get Buyer Products
curl -X GET http://localhost:5000/api/buyer/products \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Backup & Restore

```bash
# Backup database
mysqldump -u root -p SmartFarmingDB > backup.sql

# Restore database
mysql -u root -p SmartFarmingDB < backup.sql

# Compressed backup
mysqldump -u root -p SmartFarmingDB | gzip > backup.sql.gz
```

## Docker Setup (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: SmartFarmingDB
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      DB_HOST: mysql
      DB_USER: root
      DB_PASSWORD: root
      DB_NAME: SmartFarmingDB
    depends_on:
      - mysql
    volumes:
      - .:/app

volumes:
  mysql_data:
```

Run with Docker:

```bash
docker-compose up
```

## Troubleshooting

### MySQL Connection Error
```
Error: Can't connect to MySQL server

Solution:
1. Verify MySQL is running: sudo service mysql status
2. Check credentials in .env file
3. Ensure database exists: mysql -u root -p -e "SHOW DATABASES;"
```

### Import Error: No module named 'MySQLdb'
```
Solution:
pip install flask-mysqldb
```

### JWT Token Issues
```
Solution:
1. Check JWT_SECRET_KEY in .env
2. Verify token hasn't expired
3. Clear browser cache/localStorage
```

### CORS Issues
```
Solution:
Flask-CORS is already configured in app.py
Ensure frontend requests include correct headers
```

## Performance Optimization

### Database Indexing
```sql
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_farmer_id ON products(farmer_id);
CREATE INDEX idx_buyer_id ON orders(buyer_id);
CREATE FULLTEXT INDEX ft_search ON products(name, description);
```

### Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/products')
@cache.cached(timeout=300)
def get_products():
    return Products.query.all()
```

### Connection Pooling
```python
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

## Deployment

### Gunicorn (Production Server)

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name smartfarm.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Supervisor Configuration

```ini
[program:smartfarm]
command=/home/user/smartfarm/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
directory=/home/user/smartfarm/backend
user=smartfarm
autostart=true
autorestart=true
stderr_logfile=/var/log/smartfarm/err.log
stdout_logfile=/var/log/smartfarm/out.log
```

## Monitoring & Logging

### Application Logs
```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Error Tracking (Sentry)
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

## Support & Documentation

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- JWT: https://flask-jwt-extended.readthedocs.io/
- MySQL: https://dev.mysql.com/doc/

## Next Steps

1. ✅ Set up environment variables
2. ✅ Create MySQL database
3. ✅ Run migrations
4. ✅ Start development server
5. ✅ Test API endpoints
6. ✅ Integrate frontend
7. ✅ Set up CI/CD pipeline
8. ✅ Deploy to production

## Questions?

Contact: support@smartfarm.com
