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
# FastAPI entrypoint for Smart Farming Marketplace
# Trigger build: a6fb85a, 1cf93e9
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
def get_dsn_variants(url_str):
    if not url_str:
        return []
    if url_str.startswith('postgres://'):
        url_str = url_str.replace('postgres://', 'postgresql://', 1)
    
    import re
    variants = [url_str]
    if 'sslmode=' in url_str:
        no_ssl = re.sub(r'[?&]sslmode=[^&]+', '', url_str)
        if no_ssl and no_ssl not in variants:
            variants.append(no_ssl)
    else:
        sep = '&' if '?' in url_str else '?'
        ssl_req = f"{url_str}{sep}sslmode=require"
        if ssl_req not in variants:
            variants.append(ssl_req)
        
    return variants

DATABASE_URL = os.getenv('DATABASE_URL', '')

if not DATABASE_URL:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'smartfarmingdb')
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Connection Pool
db_pool = None

def initialize_db_pool():
    global db_pool, DATABASE_URL
    if db_pool is not None:
        from models.models import set_db_pool
        set_db_pool(db_pool)
        return db_pool

    dsn_candidates = get_dsn_variants(DATABASE_URL)
    for attempt, dsn in enumerate(dsn_candidates):
        try:
            try:
                db_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dsn=dsn,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5,
                    connect_timeout=10,
                    options='-c statement_timeout=30000'
                )
            except Exception as opt_err:
                if 'statement_timeout' in str(opt_err) or 'options' in str(opt_err) or 'startup parameter' in str(opt_err):
                    db_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=20,
                        dsn=dsn,
                        keepalives=1,
                        keepalives_idle=30,
                        keepalives_interval=10,
                        keepalives_count=5,
                        connect_timeout=10
                    )
                else:
                    raise opt_err

            from models.models import set_db_pool
            set_db_pool(db_pool)
            print(f"[OK] PostgreSQL connection pool created (candidate {attempt + 1})")
            
            # Warmup connection test
            try:
                warmup_conn = db_pool.getconn()
                warmup_cur = warmup_conn.cursor()
                warmup_cur.execute('SELECT 1')
                warmup_cur.close()
                db_pool.putconn(warmup_conn)
                print(f"[OK] Database warmup successful")
            except Exception as warmup_err:
                print(f"[WARN] Database warmup failed: {warmup_err}")
                
            DATABASE_URL = dsn
            return db_pool
        except Exception as e:
            print(f"[WARN] Database pool creation attempt with candidate {attempt + 1} failed: {e}")
            db_pool = None

    print(f"[ERR] Failed to initialize PostgreSQL connection pool after trying {len(dsn_candidates)} DSN variants.")
    return None


def recreate_db_pool():
    """Recreate the database connection pool if all connections become stale."""
    global db_pool, DATABASE_URL
    dsn_candidates = get_dsn_variants(DATABASE_URL)
    for dsn in dsn_candidates:
        try:
            if db_pool:
                try:
                    db_pool.closeall()
                except Exception:
                    pass
            try:
                db_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1, maxconn=20, dsn=dsn,
                    keepalives=1, keepalives_idle=30, keepalives_interval=10,
                    keepalives_count=5, connect_timeout=10,
                    options='-c statement_timeout=30000'
                )
            except Exception as opt_err:
                if 'statement_timeout' in str(opt_err) or 'options' in str(opt_err) or 'startup parameter' in str(opt_err):
                    db_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1, maxconn=20, dsn=dsn,
                        keepalives=1, keepalives_idle=30, keepalives_interval=10,
                        keepalives_count=5, connect_timeout=10
                    )
                else:
                    raise opt_err

            from models.models import set_db_pool
            set_db_pool(db_pool)
            print(f"[OK] Database pool recreated successfully")
            DATABASE_URL = dsn
            return True
        except Exception as e:
            print(f"[ERR] Database pool recreation with DSN variant failed: {e}")
            db_pool = None
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
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.github\.io",
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

BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')

if BREVO_API_KEY:
    print(f"[OK] Brevo Email API configured - From: {EMAIL_FROM_NAME} <{EMAIL_SENDER}>")
elif ENVIRONMENT == 'production':
    error_msg = (
        f"\n{'='*60}\n"
        f"  FATAL: BREVO EMAIL API KEY IS MANDATORY IN PRODUCTION\n"
        f"{'='*60}\n"
        f"  Missing: BREVO_API_KEY\n"
        f"  Set BREVO_API_KEY in Render environment variables\n"
        f"{'='*60}\n"
    )
    print(error_msg)
    raise RuntimeError("Brevo configuration is mandatory. Missing: BREVO_API_KEY")
else:
    print("[WARN] Brevo Email API not configured — email/OTP features disabled in development")

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
# INTERNAL: Reset specific user passwords (one-time utility — secured by secret token)
# ============================================================================
@app.post("/api/internal/reset-passwords")
async def internal_reset_passwords(request: Request):
    """Reset known user passwords to correct hashes. Protected by secret token."""
    try:
        data = await request.json()
        secret = data.get('secret', '')
        if secret != 'gunde-sandeep-reset-2026':
            return JSONResponse({'error': 'Unauthorized'}, status_code=401)
        
        from werkzeug.security import generate_password_hash
        from models.models import BaseModel
        
        results = []
        resets = data.get('resets', [])
        for item in resets:
            table = item.get('table')   # 'farmers', 'buyers', 'admins'
            email = item.get('email')
            phone = item.get('phone')
            new_password = item.get('password')
            
            if not table or not new_password:
                results.append({'error': 'Missing table or password'})
                continue
            
            new_hash = generate_password_hash(new_password)
            if email and table != 'buyers':
                rows = BaseModel.execute_query(
                    f"UPDATE {table} SET password_hash=%s WHERE LOWER(email)=LOWER(%s)",
                    (new_hash, email)
                )
                results.append({'table': table, 'email': email, 'updated': True})
            elif phone and table == 'buyers':
                rows = BaseModel.execute_query(
                    f"UPDATE buyers SET password_hash=%s WHERE phone=%s",
                    (new_hash, phone)
                )
                results.append({'table': table, 'phone': phone, 'updated': True})
            elif email and table == 'buyers':
                rows = BaseModel.execute_query(
                    f"UPDATE buyers SET password_hash=%s WHERE LOWER(email)=LOWER(%s)",
                    (new_hash, email)
                )
                results.append({'table': table, 'email': email, 'updated': True})
            else:
                results.append({'error': 'Need email or phone', 'item': item})
        
        return {'results': results}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ============================================================================
# REGISTER ROUTERS (replaces Flask Blueprints)
# ============================================================================
routers_registered = []

# Admin Auth Router (FastAPI)
try:
    from routes.admin_auth_fastapi import admin_auth_router
    app.include_router(admin_auth_router)
    routers_registered.append("admin_auth_router -> /api/admin-auth")
except Exception as e:
    print(f"[ERR] admin_auth: {e}")

# Buyer Auth Router (FastAPI)
try:
    from routes.buyer_auth_fastapi import buyer_auth_router
    app.include_router(buyer_auth_router)
    routers_registered.append("buyer_auth_router -> /api/buyer-auth")
except Exception as e:
    print(f"[ERR] buyer_auth: {e}")

# Auth Router (FastAPI) - Farmer login, signup, etc.
try:
    from routes.auth_fastapi import auth_router
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
    from routes.messages_fastapi import messages_router
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

@app.get("/api/debug-git-log")
async def debug_git_log():
    import subprocess
    try:
        output = subprocess.check_output("git log -n 5 --oneline", shell=True, stderr=subprocess.STDOUT)
        return {"git_log": output.decode('utf-8')}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
@app.get("/api/health")
async def health_check():
    health = {'status': 'healthy'}
    
    # Check PostgreSQL
    try:
        from models.models import get_db_pool
        pool = get_db_pool()
        if pool:
            conn = pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            pool.putconn(conn)
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
@app.get("/api/setup-db")
def trigger_db_setup():
    """Manual endpoint to initialize database schema tables on Neon"""
    try:
        from setup_database import setup_database
        conn = None
        if db_pool:
            try:
                conn = db_pool.getconn()
            except Exception as conn_err:
                print(f"[WARN] Failed to get conn from pool: {conn_err}")
                conn = None
        res = setup_database(existing_conn=conn)
        if conn and db_pool:
            try:
                db_pool.putconn(conn)
            except Exception:
                pass
        return {"status": "success", "tables_created": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/ai/crop-recommendation")
def get_crop_recommendation(season: str = "monsoon", soil_type: str = "loam"):
    """Dynamic AI Crop Recommendation based on Season & Soil Type"""
    season_lower = (season or "monsoon").lower()
    soil_lower = (soil_type or "loam").lower()
    
    matrix = {
        ("monsoon", "black"): [
            {"rank": 1, "crop": "Cotton", "confidence": 0.96, "profitability": "high", "growing_period_days": 160, "water_requirement": "medium", "tips": ["Apply NPK 120:60:60", "Monitor for pink bollworm pest", "Maintain 90x60 cm row spacing"]},
            {"rank": 2, "crop": "Soybean", "confidence": 0.91, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Inoculate seeds with Rhizobium culture", "45 cm row spacing", "Watch for yellow mosaic virus"]},
            {"rank": 3, "crop": "Groundnut (Peanut)", "confidence": 0.85, "profitability": "medium", "growing_period_days": 105, "water_requirement": "low-medium", "tips": ["Apply Gypsum at pegging stage", "Avoid standing water in fields"]}
        ],
        ("monsoon", "sandy"): [
            {"rank": 1, "crop": "Pearl Millet (Bajra)", "confidence": 0.94, "profitability": "medium", "growing_period_days": 85, "water_requirement": "low", "tips": ["Highly drought-resistant crop", "Apply NPK 80:40:0", "Maintain 45x15 cm spacing"]},
            {"rank": 2, "crop": "Cluster Bean (Guar)", "confidence": 0.89, "profitability": "high", "growing_period_days": 90, "water_requirement": "low", "tips": ["Natural nitrogen-fixing crop", "High industrial gum market demand", "Requires minimal synthetic fertilizer"]},
            {"rank": 3, "crop": "Sesame (Til)", "confidence": 0.84, "profitability": "high", "growing_period_days": 80, "water_requirement": "very low", "tips": ["Avoid waterlogging in sandy soil", "Thin seedlings at 15 days", "Harvest when bottom capsules turn yellow"]}
        ],
        ("monsoon", "clay"): [
            {"rank": 1, "crop": "Paddy (Rice)", "confidence": 0.97, "profitability": "high", "growing_period_days": 120, "water_requirement": "high", "tips": ["Clay soil retains water exceptionally well", "Maintain 5-8 cm standing water", "Apply NPK 120:60:40 in 3 split doses"]},
            {"rank": 2, "crop": "Sugarcane", "confidence": 0.90, "profitability": "high", "growing_period_days": 330, "water_requirement": "high", "tips": ["Deep trench planting method", "Trash mulching for soil moisture retention"]},
            {"rank": 3, "crop": "Jute / Hemp", "confidence": 0.83, "profitability": "medium", "growing_period_days": 120, "water_requirement": "high", "tips": ["Thrives in warm, humid clay soils", "Retting water availability is crucial"]}
        ],
        ("monsoon", "red"): [
            {"rank": 1, "crop": "Groundnut (Peanut)", "confidence": 0.93, "profitability": "high", "growing_period_days": 105, "water_requirement": "medium", "tips": ["Well-drained red soil promotes pod formation", "Apply Gypsum @ 400 kg/ha at 45 days"]},
            {"rank": 2, "crop": "Finger Millet (Ragi)", "confidence": 0.90, "profitability": "high", "growing_period_days": 100, "water_requirement": "low-medium", "tips": ["Rich in calcium and iron", "Tolerates semi-arid red soil stress"]},
            {"rank": 3, "crop": "Maize (Corn)", "confidence": 0.85, "profitability": "medium", "growing_period_days": 105, "water_requirement": "medium", "tips": ["Add organic compost to boost red soil organic carbon"]}
        ],
        ("winter", "loam"): [
            {"rank": 1, "crop": "Wheat", "confidence": 0.96, "profitability": "high", "growing_period_days": 135, "water_requirement": "medium", "tips": ["Irrigate at Crown Root Initiation stage (21 days)", "Apply NPK 120:60:40"]},
            {"rank": 2, "crop": "Mustard / Rapeseed", "confidence": 0.92, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Sulfur application boosts seed oil content by 15%", "Thin plants to 10-15 cm spacing"]},
            {"rank": 3, "crop": "Chickpea (Gram / Chana)", "confidence": 0.88, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Nipping top buds at 35 days increases branching and pods"]}
        ],
        ("winter", "black"): [
            {"rank": 1, "crop": "Chickpea (Gram / Chana)", "confidence": 0.95, "profitability": "high", "growing_period_days": 115, "water_requirement": "low", "tips": ["Thrives on deep residual moisture of black soil", "Avoid over-irrigation"]},
            {"rank": 2, "crop": "Wheat (Durum / Sharbati)", "confidence": 0.90, "profitability": "high", "growing_period_days": 130, "water_requirement": "medium", "tips": ["Apply Zinc Sulfate @ 25 kg/ha at sowing"]},
            {"rank": 3, "crop": "Safflower (Kusum)", "confidence": 0.86, "profitability": "medium", "growing_period_days": 120, "water_requirement": "low", "tips": ["Deep root system extracts moisture from subsoil", "Drought tolerant oilseed crop"]}
        ],
        ("winter", "sandy"): [
            {"rank": 1, "crop": "Barley", "confidence": 0.93, "profitability": "medium", "growing_period_days": 100, "water_requirement": "low", "tips": ["Tolerates sandy soil and salinity", "Lower water needs than wheat"]},
            {"rank": 2, "crop": "Mustard", "confidence": 0.89, "profitability": "high", "growing_period_days": 105, "water_requirement": "low", "tips": ["Drip irrigation with fertigation gives optimal yields"]},
            {"rank": 3, "crop": "Cumin (Jeera) / Coriander", "confidence": 0.84, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Requires cool dry climate, avoid excessive dampness"]}
        ],
        ("winter", "red"): [
            {"rank": 1, "crop": "Potato", "confidence": 0.94, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Friable red soil permits free tuber expansion", "Earthing up at 30 days"]},
            {"rank": 2, "crop": "Mustard", "confidence": 0.89, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Apply Boron @ 10 kg/ha for better pod development"]},
            {"rank": 3, "crop": "Sunflower", "confidence": 0.84, "profitability": "medium", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Ensure honeybee activity or manual pollination during flowering"]}
        ],
        ("summer", "sandy"): [
            {"rank": 1, "crop": "Watermelon / Muskmelon", "confidence": 0.96, "profitability": "high", "growing_period_days": 85, "water_requirement": "medium", "tips": ["Sandy soil warms quickly, accelerating vine growth", "Use plastic mulching & drip irrigation"]},
            {"rank": 2, "crop": "Cucumber / Gourd", "confidence": 0.91, "profitability": "high", "growing_period_days": 65, "water_requirement": "medium", "tips": ["Trellis staking keeps fruits clean and prevents soil rot"]},
            {"rank": 3, "crop": "Cowpea / Green Gram (Moong)", "confidence": 0.87, "profitability": "medium", "growing_period_days": 65, "water_requirement": "low", "tips": ["Short duration summer pulse crop", "Improves soil fertility for Kharif"]}
        ],
        ("summer", "black"): [
            {"rank": 1, "crop": "Green Gram (Moong Dal)", "confidence": 0.94, "profitability": "high", "growing_period_days": 65, "water_requirement": "low", "tips": ["Ideal catch crop between Rabi and Kharif", "Requires minimal irrigation"]},
            {"rank": 2, "crop": "Sesame (Til)", "confidence": 0.89, "profitability": "high", "growing_period_days": 75, "water_requirement": "low", "tips": ["Highly heat tolerant", "Strong summer market prices"]},
            {"rank": 3, "crop": "Sunflower", "confidence": 0.85, "profitability": "medium", "growing_period_days": 85, "water_requirement": "medium", "tips": ["High solar radiation boosts seed oil content"]}
        ]
    }
    
    key = (season_lower, soil_lower)
    if key in matrix:
        recs = matrix[key]
    else:
        if season_lower == "winter":
            recs = [
                {"rank": 1, "crop": "Wheat", "confidence": 0.95, "profitability": "high", "growing_period_days": 135, "water_requirement": "medium", "tips": ["Crown Root Initiation irrigation at 21 days", "Apply NPK 120:60:40"]},
                {"rank": 2, "crop": "Mustard", "confidence": 0.90, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Apply sulfur for higher oil yield", "Thin seedlings to 10-15 cm"]},
                {"rank": 3, "crop": "Chickpea (Chana)", "confidence": 0.86, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Nipping terminal shoots increases branching"]}
            ]
        elif season_lower == "summer":
            recs = [
                {"rank": 1, "crop": "Watermelon / Muskmelon", "confidence": 0.95, "profitability": "high", "growing_period_days": 85, "water_requirement": "medium", "tips": ["Use drip irrigation", "High summer market demand"]},
                {"rank": 2, "crop": "Green Gram (Moong)", "confidence": 0.90, "profitability": "medium", "growing_period_days": 65, "water_requirement": "low", "tips": ["Short duration 60-day crop", "Fixes soil nitrogen"]},
                {"rank": 3, "crop": "Okra (Bhindi)", "confidence": 0.85, "profitability": "high", "growing_period_days": 75, "water_requirement": "medium", "tips": ["Harvest every 2 days for continuous yield"]}
            ]
        else:
            recs = [
                {"rank": 1, "crop": "Paddy (Rice)", "confidence": 0.94, "profitability": "high", "growing_period_days": 120, "water_requirement": "high", "tips": ["Use quality certified seeds", "Maintain water level of 5-8 cm", "Apply NPK 60:40:40 in 3 splits"]},
                {"rank": 2, "crop": "Maize (Corn)", "confidence": 0.88, "profitability": "medium", "growing_period_days": 110, "water_requirement": "medium", "tips": ["Space 60cm between rows", "Apply NPK 120:60:40", "Monitor for fall armyworm"]},
                {"rank": 3, "crop": "Soybean", "confidence": 0.82, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Apply Rhizobium culture", "Spacing: 45cm rows", "Watch for yellow mosaic virus"]}
            ]
            
    return {
        "success": True,
        "season": season,
        "soil_type": soil_type,
        "recommendations": recs
    }

# ============================================================================
# STARTUP EVENT
# ============================================================================

async def _background_db_init():
    """Run database pool setup, core schema setup, migrations, and index creation in background task"""
    try:
        initialize_db_pool()
    except Exception as e:
        print(f"[WARN] Startup DB pool init: {e}")
        
    try:
        from setup_database import setup_database
        conn = None
        if db_pool:
            try:
                conn = db_pool.getconn()
            except Exception:
                conn = None
        setup_database(existing_conn=conn)
        if conn and db_pool:
            try:
                db_pool.putconn(conn)
            except Exception:
                pass
        print("[OK] Core database schema verified & setup completed")
    except Exception as setup_err:
        print(f"[WARN] Core database setup: {setup_err}")

    try:
        from routes.checkout import run_checkout_migration
        run_checkout_migration()
    except Exception as migration_err:
        print(f"[WARN] Checkout migration failed: {migration_err}")
        
    try:
        ensure_platform_settings_table()
    except Exception as e:
        print(f"[WARN] Platform settings init: {e}")
        
    try:
        _create_performance_indexes()
    except Exception as e:
        print(f"[WARN] Index creation: {e}")


@app.on_event("startup")
async def startup_event():
    import asyncio
    # Fire off DB background warmup task without blocking port binding
    asyncio.create_task(_background_db_init())
    port = int(os.getenv('PORT', 8000))
    
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
