"""
Smart Farmer Marketplace - Complete Backend Startup Script
Production-ready backend with all features initialized
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     SMART FARMER MARKETPLACE - Backend Server                ║
    ║     Production Ready - Enterprise Grade                       ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

def check_environment():
    """Check if environment is properly configured"""
    print("✓ Checking environment configuration...")
    
    required_vars = [
        'MYSQL_HOST',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
        'MYSQL_DB',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("  Please configure .env file")
        return False
    
    print("✓ Environment variables configured")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("✓ Checking Python dependencies...")
    
    try:
        import flask
        import flask_cors
        import flask_jwt_extended
        import flask_mysqldb
        import dotenv
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Check database connection"""
    print("✓ Checking database connection...")
    
    try:
        import MySQLdb
        
        host = os.getenv('MYSQL_HOST', 'localhost')
        user = os.getenv('MYSQL_USER', 'root')
        password = os.getenv('MYSQL_PASSWORD', '')
        db = os.getenv('MYSQL_DB', 'smart_farming')
        
        conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=db
        )
        conn.close()
        
        print(f"✓ Connected to database: {db}@{host}")
        return True
    
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def print_startup_info():
    """Print startup information"""
    port = int(os.getenv('FLASK_PORT', 5000))
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("\n" + "="*60)
    print("SERVER CONFIGURATION")
    print("="*60)
    print(f"Host:              0.0.0.0")
    print(f"Port:              {port}")
    print(f"Debug Mode:        {debug}")
    print(f"Frontend URL:      {frontend_url}")
    print(f"Database:          {os.getenv('MYSQL_DB', 'smart_farming')}")
    print("="*60 + "\n")
    
    print("AVAILABLE ENDPOINTS:")
    print("-"*60)
    print("Health Check:      GET /health")
    print("API Info:          GET /api")
    print("Authentication:    /api/auth")
    print("Farmer Module:     /api/farmer")
    print("Buyer Module:      /api/buyer")
    print("Admin Module:      /api/admin")
    print("Messaging:         /api/messages")
    print("-"*60 + "\n")

def start_server():
    """Start the Flask development server"""
    print("\n✓ Starting backend server...")
    print("Press CTRL+C to stop the server\n")
    
    try:
        from app import app
        
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            use_reloader=debug
        )
    
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    
    except Exception as e:
        print(f"\n✗ Server error: {e}")
        sys.exit(1)

def start_production_server():
    """Start with production WSGI server (Waitress)"""
    print("\n✓ Starting backend with Waitress (production)...")
    print("Press CTRL+C to stop the server\n")
    
    try:
        from waitress import serve
        from app import app, socketio
        
        port = int(os.getenv('FLASK_PORT', 5000))
        
        print(f"Starting with Waitress + Socket.IO...")
        socketio.run(app, host='0.0.0.0', port=port)
    
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    
    except ImportError:
        print("✗ Waitress not installed")
        print("  Run: pip install waitress")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Server error: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print_banner()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run checks
    print("\n" + "="*60)
    print("PRE-FLIGHT CHECKS")
    print("="*60 + "\n")
    
    checks = [
        check_environment(),
        check_dependencies(),
        check_database_connection()
    ]
    
    if not all(checks):
        print("\n✗ Pre-flight checks failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✓ All checks passed!\n")
    
    # Print startup info
    print_startup_info()
    
    # Determine server type
    server_type = os.getenv('SERVER_TYPE', 'development').lower()
    
    if server_type == 'production':
        start_production_server()
    else:
        start_server()

if __name__ == '__main__':
    main()
