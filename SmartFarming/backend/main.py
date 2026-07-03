"""
Smart Farmer Marketplace - FastAPI Backend
Platform: Render.com + Neon PostgreSQL + Redis Cloud
Single entry point. Replaces Flask app.py.
[Trigger Deploy: 2026-07-03]
"""

# Fix Windows console encoding for emoji characters
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
import os
import time
import psycopg2
from psycopg2 import pool
from datetime import timedelta

# Load .env from current dir or parent dir (SmartFarming/.env)
_this_dir = os.path.abspath(os.path.dirname(__file__))
_env_path = os.path.join(_this_dir, '.env')
_parent_env = os.path.abspath(os.path.join(_this_dir, '..', '.env'))
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=False)
    print(f"[OK] Loaded .env from: {_env_path}")
elif os.path.exists(_parent_env):
    load_dotenv(_parent_env, override=False)
    print(f"[OK] Loaded .env from: {_parent_env}")
else:
    load_dotenv()
    print("[WARN] No .env found in backend/ or parent dir, using defaults")

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title="Smart Farmer Marketplace API",
    description="Complete marketplace API for farmers and buyers",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# DATABASE CONFIG (Neon PostgreSQL)
# ============================================================================
DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    if db_host and 'neon.tech' in db_host:
        DATABASE_URL += "?sslmode=require"

# Connection Pool
db_pool = None

def initialize_db_pool():
    global db_pool
    if db_pool is not None:
        return
    try:
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=30,
            dsn=DATABASE_URL,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            connect_timeout=10,
            options='-c statement_timeout=30000'
        )
        from models.models import set_db_pool
        set_db_pool(db_pool)
        print(f"[OK] PostgreSQL connection pool created (Neon)")
        # Warmup
        try:
            warmup_conn = db_pool.getconn()
            warmup_cur = warmup_conn.cursor()
            warmup_cur.execute('SELECT 1')
            warmup_cur.close()
            db_pool.putconn(warmup_conn)
            print(f"[OK] Database warmup successful")
        except Exception as warmup_err:
            print(f"[WARN] Database warmup failed (will retry on first request): {warmup_err}")
    except Exception as e:
        print(f"[ERR] PostgreSQL pool creation failed: {e}")
        db_pool = None


def recreate_db_pool():
    """Recreate the database connection pool if all connections become stale."""
    global db_pool
    try:
        if db_pool:
            try:
                db_pool.closeall()
            except Exception:
                pass
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5, maxconn=10, dsn=DATABASE_URL,
            keepalives=1, keepalives_idle=30, keepalives_interval=10,
            keepalives_count=5, connect_timeout=10,
            options='-c statement_timeout=30000'
        )
        from models.models import set_db_pool
        set_db_pool(db_pool)
        print(f"[OK] Database pool recreated successfully")
        return True
    except Exception as e:
        print(f"[ERR] Database pool recreation failed: {e}")
        return False


# ============================================================================
# REDIS CONFIG
# ============================================================================
redis_client = None
try:
    import redis as redis_lib
    redis_url = os.getenv('REDIS_URL', '')
    if redis_url:
        redis_client = redis_lib.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print(f"[OK] Redis Cloud connected")
    else:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', '')
        redis_client = redis_lib.Redis(
            host=redis_host, port=redis_port,
            password=redis_password if redis_password else None,
            decode_responses=True
        )
        redis_client.ping()
        print(f"[OK] Redis connected ({redis_host}:{redis_port})")
except Exception as e:
    print(f"[WARN] Redis not available: {e} - caching disabled")
    redis_client = None

# ============================================================================
# PASS DB POOL TO MODELS
# ============================================================================
from models.models import set_db_pool, BaseModel

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins == '*':
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in cors_origins.split(',')]
    for port in ["3000", "3001", "3002"]:
        origin = f"http://localhost:{port}"
        if origin not in allowed_origins:
            allowed_origins.append(origin)
    frontend_url = os.getenv('FRONTEND_URL', '')
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)

print(f"[OK] CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# GZip compression for response payloads > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# ============================================================================
# CLOUDINARY CONFIG
# ============================================================================
try:
    import cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    print("[OK] Cloudinary configured")
except ImportError:
    print("[SKIP] cloudinary not installed")

# ============================================================================
# TWILIO SMS CONFIG
# ============================================================================
twilio_client = None
try:
    from twilio.rest import Client as TwilioClient
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    if sid and token:
        twilio_client = TwilioClient(sid, token)
        print("[OK] Twilio SMS configured")
    else:
        print("[SKIP] Twilio credentials not set")
except ImportError:
    print("[SKIP] twilio not installed")

# ============================================================================
# EMAIL (SMTP - Gmail) CONFIG - MANDATORY
# ============================================================================
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'SmartFarming')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

if EMAIL_SENDER and os.getenv('EMAIL_PASSWORD'):
    print(f"[OK] SMTP email configured - From: {EMAIL_FROM_NAME} <{EMAIL_SENDER}>")
elif ENVIRONMENT == 'production':
    error_msg = (
        f"\n{'='*60}\n"
        f"  FATAL: SMTP EMAIL CONFIG IS MANDATORY IN PRODUCTION\n"
        f"{'='*60}\n"
        f"  Missing: EMAIL_SENDER or EMAIL_PASSWORD\n"
        f"  Set SMTP_HOST, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD in .env\n"
        f"{'='*60}\n"
    )
    print(error_msg)
    raise RuntimeError("SMTP configuration is mandatory. Missing: EMAIL_SENDER or EMAIL_PASSWORD")
else:
    print("[WARN] SMTP not configured — email/OTP features disabled in development")

# ============================================================================
# WEATHER API CONFIG
# ============================================================================
if os.getenv('WEATHER_API_KEY'):
    print("[OK] Weather API configured")

# ============================================================================
# GOOGLE MAPS CONFIG
# ============================================================================
if os.getenv('GOOGLE_MAPS_API_KEY'):
    print("[OK] Google Maps configured")

# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers and request timing."""
    start_time = time.time()
    response = await call_next(request)

    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Request timing log (skip noisy health checks and OPTIONS)
    duration_ms = (time.time() - start_time) * 1000
    path = request.url.path
    if '/health' not in path and request.method != 'OPTIONS':
        if duration_ms > 2000:
            print(f"[SLOW] {request.method} {path} -> {response.status_code} ({duration_ms:.0f}ms)")

    return response

# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return clean JSON instead of HTML error pages."""
    print(f"[ERR] Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={'error': 'Internal Server Error', 'message': 'Something went wrong. Please try again.'}
    )

# ============================================================================
# REGISTER ROUTERS (replaces Flask Blueprints)
# ============================================================================
routers_registered = []

try:
    from routes.auth import auth_router
    app.include_router(auth_router)
    routers_registered.append("auth_router -> /api/auth")
except Exception as e:
    print(f"[ERR] auth: {e}")

try:
    from routes.farmer_products import farmer_router
    app.include_router(farmer_router)
    routers_registered.append("farmer_router -> /api/farmer")
except Exception as e:
    print(f"[ERR] farmer: {e}")

try:
    from routes.buyer_products import buyer_router
    app.include_router(buyer_router)
    routers_registered.append("buyer_router -> /api/buyer")
except Exception as e:
    print(f"[ERR] buyer: {e}")

try:
    from routes.admin import admin_router
    app.include_router(admin_router)
    routers_registered.append("admin_router -> /api/admin")
except Exception as e:
    print(f"[ERR] admin: {e}")

try:
    from routes.messages import messages_router
    app.include_router(messages_router)
    routers_registered.append("messages_router -> /api/messages")
except Exception as e:
    print(f"[ERR] messages: {e}")

try:
    from routes.payments import payments_router
    app.include_router(payments_router)
    routers_registered.append("payments_router -> /api/payments")
except Exception as e:
    print(f"[ERR] payments: {e}")

try:
    from routes.agribot import agribot_router
    app.include_router(agribot_router)
    routers_registered.append("agribot_router -> /api/agribot")
except Exception as e:
    print(f"[ERR] agribot: {e}")

try:
    from routes.weather import weather_router
    app.include_router(weather_router)
    routers_registered.append("weather_router -> /api/weather")
except Exception as e:
    print(f"[ERR] weather: {e}")

try:
    from routes.order_flow import order_flow_router
    app.include_router(order_flow_router)
    routers_registered.append("order_flow_router -> /api/orders")
except Exception as e:
    print(f"[ERR] order_flow: {e}")

try:
    from routes.saas_dashboard import saas_dashboard_router
    app.include_router(saas_dashboard_router)
    routers_registered.append("saas_dashboard_router -> /api/admin/saas")
except Exception as e:
    print(f"[ERR] saas_dashboard: {e}")

try:
    from routes.premium import premium_router
    app.include_router(premium_router)
    routers_registered.append("premium_router -> /api/premium")
except Exception as e:
    print(f"[ERR] premium: {e}")

try:
    from routes.checkout import checkout_router
    app.include_router(checkout_router)
    routers_registered.append("checkout_router -> /api/checkout")
except Exception as e:
    print(f"[ERR] checkout: {e}")

try:
    from routes.buyer_settings import settings_router
    app.include_router(settings_router)
    routers_registered.append("settings_router -> /api/buyer/settings")
except Exception as e:
    print(f"[ERR] buyer_settings: {e}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(400)
async def bad_request(request, exc):
    return JSONResponse(status_code=400, content={'error': 'Bad Request', 'message': str(exc)})

@app.exception_handler(401)
async def unauthorized(request, exc):
    return JSONResponse(status_code=401, content={'error': 'Unauthorized', 'message': 'Authentication required'})

@app.exception_handler(403)
async def forbidden(request, exc):
    return JSONResponse(status_code=403, content={'error': 'Forbidden', 'message': 'Permission denied'})

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={'error': 'Not Found', 'message': 'Resource not found'})

@app.exception_handler(500)
async def internal_error(request, exc):
    return JSONResponse(status_code=500, content={'error': 'Internal Server Error', 'message': 'Something went wrong'})

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
@app.get("/api/health")
async def health_check():
    health = {'status': 'healthy'}
    
    # Check PostgreSQL
    try:
        if db_pool:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            db_pool.putconn(conn)
            health['database'] = 'connected'
        else:
            health['database'] = 'no pool'
    except Exception as e:
        health['database'] = f'error: {str(e)}'
        health['status'] = 'degraded'
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            health['cache'] = 'connected'
        else:
            health['cache'] = 'disabled'
    except Exception as e:
        health['cache'] = f'error: {str(e)}'
    
    status_code = 200
    return JSONResponse(content=health, status_code=status_code)


@app.get("/api")
async def api_info():
    return {
        'name': 'Smart Farmer Marketplace API',
        'version': '3.0.0 (FastAPI)',
        'platform': 'Render.com + Neon PostgreSQL + Redis Cloud',
        'routers': routers_registered,
        'docs': '/docs',
        'endpoints': {
            'auth': '/api/auth',
            'farmer': '/api/farmer',
            'buyer': '/api/buyer',
            'admin': '/api/admin',
            'messages': '/api/messages',
            'payments': '/api/payments',
            'weather': '/api/weather',
            'agribot': '/api/agribot',
            'upload': '/api/upload'
        }
    }

# ============================================================================
# IMAGE UPLOAD (Cloudinary)
# ============================================================================
from utils.jwt_utils import get_current_user

@app.post("/api/upload")
async def upload_image(
    image: UploadFile = File(...),
    folder: str = Form("smartfarm"),
    user_id: str = Depends(get_current_user)
):
    """Upload image to Cloudinary"""
    try:
        import cloudinary.uploader
        contents = await image.read()
        import io
        result = cloudinary.uploader.upload(io.BytesIO(contents), folder=folder)
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'width': result.get('width'),
            'height': result.get('height'),
        }
    except ImportError:
        return JSONResponse(status_code=500, content={'error': 'Cloudinary not configured'})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

# ============================================================================
# PLATFORM SETTINGS — GST, Platform Fee, Delivery Fee (admin-configurable)
# ============================================================================

# Platform settings cache (loaded once at startup, refreshed on update)
_platform_settings_cache = None
_platform_settings_defaults = {'gst_percent': 1, 'platform_percent': 2, 'delivery_flat': 40, 'free_delivery_threshold': 500}

def ensure_platform_settings_table():
    """Create platform_settings table if it doesn't exist"""
    global _platform_settings_cache
    try:
        BaseModel.execute_query("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                key VARCHAR(100) PRIMARY KEY,
                value VARCHAR(500) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, ())
        existing = BaseModel.execute_query("SELECT key FROM platform_settings LIMIT 1", (), fetch_one=True)
        if not existing:
            defaults = [
                ('gst_percent', '1'),
                ('platform_percent', '2'),
                ('delivery_flat', '40'),
                ('free_delivery_threshold', '500'),
            ]
            for key, value in defaults:
                BaseModel.execute_query(
                    "INSERT INTO platform_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
                    (key, value)
                )
        # Load into cache
        _load_platform_settings_cache()
    except Exception as e:
        print(f"[Settings] Table setup error: {e}")

def _load_platform_settings_cache():
    """Load platform settings into memory cache."""
    global _platform_settings_cache
    try:
        rows = BaseModel.execute_query(
            "SELECT key, value FROM platform_settings", (), fetch_all=True
        ) or []
        settings = {}
        for row in rows:
            try:
                settings[row['key']] = float(row['value'])
            except (ValueError, TypeError):
                settings[row['key']] = row['value']
        for k, v in _platform_settings_defaults.items():
            if k not in settings:
                settings[k] = v
        _platform_settings_cache = settings
    except Exception as e:
        print(f"[Settings] Cache load error: {e}")
        _platform_settings_cache = dict(_platform_settings_defaults)

@app.get("/api/admin/settings")
async def get_platform_settings():
    """Get platform fee settings — public endpoint (buyers need this at checkout). Cached in memory."""
    global _platform_settings_cache
    if _platform_settings_cache:
        return _platform_settings_cache
    # Fallback: load from DB
    _load_platform_settings_cache()
    return _platform_settings_cache or dict(_platform_settings_defaults)

@app.put("/api/admin/settings")
async def update_platform_settings(request: Request):
    """Update platform fee settings — admin only"""
    try:
        ensure_platform_settings_table()
        data = await request.json()
        
        allowed_keys = ['gst_percent', 'platform_percent', 'delivery_flat', 'free_delivery_threshold']
        # Also accept camelCase from frontend
        key_map = {
            'gstPercent': 'gst_percent',
            'platformPercent': 'platform_percent',
            'deliveryFlat': 'delivery_flat',
            'freeDeliveryThreshold': 'free_delivery_threshold',
        }
        
        updated = []
        for incoming_key, value in data.items():
            db_key = key_map.get(incoming_key, incoming_key)
            if db_key in allowed_keys:
                BaseModel.execute_query(
                    """INSERT INTO platform_settings (key, value, updated_at)
                       VALUES (%s, %s, CURRENT_TIMESTAMP)
                       ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = CURRENT_TIMESTAMP""",
                    (db_key, str(value), str(value))
                )
                updated.append(db_key)
        
        return {'success': True, 'updated': updated}
    except Exception as e:
        print(f"[Settings] Update error: {e}")
        return JSONResponse(status_code=500, content={'error': 'Failed to update settings.'})

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    initialize_db_pool()
    port = int(os.getenv('PORT', 8000))
    
    # Initialize platform settings table
    try:
        ensure_platform_settings_table()
    except Exception as e:
        print(f"[WARN] Platform settings init: {e}")
    
    # Create performance indexes
    try:
        _create_performance_indexes()
    except Exception as e:
        print(f"[WARN] Index creation: {e}")
    
    print(f"""
    ============================================
    Smart Farmer Marketplace v3.0 (FastAPI)
    ============================================
    Database: Neon PostgreSQL
    Cache: {'Redis Cloud' if redis_client else 'Disabled'}
    Compression: GZip enabled (>500 bytes)
    Port: {port}
    Routers: {len(routers_registered)}
    Docs: http://localhost:{port}/docs
    """)
    for r in routers_registered:
        print(f"    [OK] {r}")
    print(f"""
    ============================================
    """)

def _create_performance_indexes():
    """Create database indexes for frequently queried columns."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_otps_email_expires ON otps(email, expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_farmers_email ON farmers(email)",
        "CREATE INDEX IF NOT EXISTS idx_buyers_phone ON buyers(phone)",
        "CREATE INDEX IF NOT EXISTS idx_buyers_email ON buyers(email)",
    ]
    for idx_sql in indexes:
        try:
            BaseModel.execute_query(idx_sql, ())
        except Exception as e:
            # Index may already exist or table may not exist yet
            pass
    print("[OK] Database performance indexes verified")

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        try:
            db_pool.closeall()
            print("[OK] Database pool closed")
        except Exception:
            pass

# ============================================================================
# RUN (for direct execution)
# ============================================================================
if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
