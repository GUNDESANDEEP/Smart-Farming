"""
Middleware & Utilities - Rate Limiting, Validation, Error Handling
"""

from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import re
from collections import defaultdict

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier, max_requests=100, window_seconds=3600):
        """Check if request is allowed"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Remove old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add new request
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit(max_requests=100, window_seconds=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window_seconds} seconds'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format (India)"""
        pattern = r'^[6-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_otp(otp):
        """Validate OTP format (6 digits)"""
        return bool(re.match(r'^\d{6}$', otp))
    
    @staticmethod
    def validate_price(price):
        """Validate price is positive number"""
        try:
            price_float = float(price)
            return price_float > 0, price_float
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_quantity(quantity):
        """Validate quantity is positive integer"""
        try:
            qty_int = int(quantity)
            return qty_int > 0, qty_int
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_rating(rating):
        """Validate rating is between 1 and 5"""
        try:
            rating_float = float(rating)
            return 1 <= rating_float <= 5, rating_float
        except ValueError:
            return False, None
    
    @staticmethod
    def sanitize_input(input_str):
        """Remove potentially dangerous characters"""
        # Remove SQL injection attempts
        dangerous_patterns = [';', '--', '/*', '*/', 'UNION', 'SELECT', 'DROP', 'INSERT', 'UPDATE', 'DELETE']
        
        sanitized = input_str
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        return sanitized.strip()

# ============================================================================
# REQUEST VALIDATION MIDDLEWARE
# ============================================================================

def validate_json(f):
    """Validate request has JSON content"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

def validate_required_fields(required_fields):
    """Validate required fields in JSON request"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ERROR HANDLING UTILITIES
# ============================================================================

class APIError(Exception):
    """Custom API error class"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

# ============================================================================
# RESPONSE FORMATTING
# ============================================================================

class Response:
    """Standardized response formatting"""
    
    @staticmethod
    def success(data=None, message='Success', status_code=200):
        """Format successful response"""
        response = {
            'status': 'success',
            'message': message
        }
        if data:
            response['data'] = data
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message, status_code=400, errors=None):
        """Format error response"""
        response = {
            'status': 'error',
            'error': message
        }
        if errors:
            response['errors'] = errors
        
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(items, page, limit, total=None, message='Success'):
        """Format paginated response"""
        return jsonify({
            'status': 'success',
            'message': message,
            'data': items,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'has_next': total > (page * limit) if total else None
            }
        }), 200

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class Logger:
    """Request and error logging"""
    
    @staticmethod
    def log_request(method, endpoint, user_id=None, status=None):
        """Log API request"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {method} {endpoint}"
        if user_id:
            log_message += f" - User: {user_id}"
        if status:
            log_message += f" - Status: {status}"
        
        print(log_message)
    
    @staticmethod
    def log_error(error_type, message, context=None):
        """Log error"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] ERROR: {error_type} - {message}"
        if context:
            log_message += f" - Context: {context}"
        
        print(log_message)

# ============================================================================
# SECURITY UTILITIES
# ============================================================================

class Security:
    """Security utilities"""
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe upload"""
        # Remove special characters
        import re
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        return filename
    
    @staticmethod
    def generate_secure_filename(original_filename, user_id):
        """Generate secure filename with user ID"""
        import secrets
        import os
        
        filename = Security.sanitize_filename(original_filename)
        name, ext = os.path.splitext(filename)
        
        # Add random string to prevent collisions
        random_suffix = secrets.token_hex(4)
        
        return f"{user_id}_{random_suffix}_{name}{ext}"
