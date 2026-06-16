"""
Smart Farmer Marketplace - Flask Backend
Single entry point. 5 consolidated blueprints.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

app = Flask(__name__)

# ============================================================================
# DATABASE CONFIG
# ============================================================================
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'SmartFarmingDB')
app.config['MYSQL_CHARSET'] = 'utf8mb4'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# ============================================================================
# JWT CONFIG
# ============================================================================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# ============================================================================
# INIT EXTENSIONS
# ============================================================================
mysql = MySQL(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {
    "origins": [
        os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        "http://localhost:3000",
        "https://smart-farming-marketplace.vercel.app",
        "*"
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Pass MySQL to models
from models.models import set_mysql_instance
set_mysql_instance(mysql)

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
        app.config['TWILIO_PHONE'] = os.getenv('TWILIO_PHONE_NUMBER')
        print("[OK] Twilio SMS configured")
    else:
        print("[SKIP] Twilio credentials not set")
except ImportError:
    print("[SKIP] twilio not installed")

# ============================================================================
# EMAIL (SMTP) CONFIG
# ============================================================================
app.config['SMTP_HOST'] = os.getenv('SMTP_HOST', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['EMAIL_SENDER'] = os.getenv('EMAIL_SENDER')
app.config['EMAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['EMAIL_FROM_NAME'] = os.getenv('EMAIL_FROM_NAME', 'SmartFarming')
if app.config['EMAIL_SENDER'] and app.config['EMAIL_PASSWORD']:
    print("[OK] Email SMTP configured")
else:
    print("[SKIP] Email credentials not set")

# ============================================================================
# WEATHER API CONFIG
# ============================================================================
app.config['WEATHER_API_KEY'] = os.getenv('WEATHER_API_KEY')
if app.config['WEATHER_API_KEY']:
    print("[OK] Weather API configured")

# ============================================================================
# GOOGLE MAPS CONFIG
# ============================================================================
app.config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY')
if app.config['GOOGLE_MAPS_API_KEY']:
    print("[OK] Google Maps configured")

# ============================================================================
# SOCKET.IO (optional)
# ============================================================================
socketio = None
try:
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    from socket_events import register_socketio
    register_socketio(app)
    print("[OK] Socket.IO initialized")
except ImportError:
    print("[SKIP] flask-socketio not installed, real-time features disabled")
except Exception as e:
    print(f"[SKIP] Socket.IO init failed: {e}")

# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================
blueprints_registered = []

try:
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    blueprints_registered.append(f"auth_bp -> {auth_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] auth: {e}")

try:
    from routes.farmer_products import farmer_bp
    app.register_blueprint(farmer_bp)
    blueprints_registered.append(f"farmer_bp -> {farmer_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] farmer: {e}")

try:
    from routes.buyer_products import buyer_bp
    app.register_blueprint(buyer_bp)
    blueprints_registered.append(f"buyer_bp -> {buyer_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] buyer: {e}")

try:
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    blueprints_registered.append(f"admin_bp -> {admin_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] admin: {e}")

try:
    from routes.messages import messages_bp
    app.register_blueprint(messages_bp)
    blueprints_registered.append(f"messages_bp -> {messages_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] messages: {e}")

try:
    from routes.payments import payments_bp
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    blueprints_registered.append(f"payments_bp -> /api/payments")
except Exception as e:
    print(f"[ERR] payments: {e}")

try:
    from routes.agribot import agribot_bp
    app.register_blueprint(agribot_bp)
    blueprints_registered.append(f"agribot_bp -> {agribot_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] agribot: {e}")

try:
    from routes.weather import weather_bp
    app.register_blueprint(weather_bp)
    blueprints_registered.append(f"weather_bp -> {weather_bp.url_prefix}")
except Exception as e:
    print(f"[ERR] weather: {e}")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden', 'message': 'Permission denied'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'Something went wrong'}), 500

# ============================================================================
# JWT ERROR HANDLERS
# ============================================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({'error': 'Token expired', 'message': 'Please login again'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'message': 'Token is malformed'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization required', 'message': 'Missing token'}), 401

# ============================================================================
# SECURITY HEADERS
# ============================================================================

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'Smart Farmer Marketplace API',
        'version': '2.0.0',
        'blueprints': blueprints_registered,
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
    }), 200

# Weather API is now handled by weather_bp blueprint (/api/weather)

# ============================================================================
# IMAGE UPLOAD (Cloudinary)
# ============================================================================

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload image to Cloudinary"""
    try:
        import cloudinary.uploader
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        folder = request.form.get('folder', 'smartfarm')
        result = cloudinary.uploader.upload(file, folder=folder)
        return jsonify({
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'width': result.get('width'),
            'height': result.get('height'),
        }), 200
    except ImportError:
        return jsonify({'error': 'Cloudinary not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    ============================================
    Smart Farmer Marketplace v2.0
    ============================================
    Database: {app.config['MYSQL_DB']}
    Port: {port}
    Blueprints: {len(blueprints_registered)}
    """)
    for bp in blueprints_registered:
        print(f"    [OK] {bp}")
    print(f"""
    ============================================
    """)
    
    if socketio:
        socketio.run(app, host='0.0.0.0', port=port, debug=debug)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug)
