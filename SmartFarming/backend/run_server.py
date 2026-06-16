"""
Smart Farming Backend - Waitress Server Runner
Uses Waitress WSGI server which works better on Windows
"""
import os
import sys
from app import app
from dotenv import load_dotenv
from waitress import serve

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    try:
        host = '127.0.0.1'
        port = int(os.getenv('PORT', 8000))
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Smart Farming Backend")
        print(f"{'='*60}")
        print(f"Server: Waitress (Windows-optimized)")
        print(f"Address: http://{host}:{port}")
        print(f"Database: SmartFarmingDB (root@localhost)")
        print(f"Debug: OFF")
        print(f"{'='*60}\n")
        
        # Use Waitress for better Windows compatibility
        serve(
            app,
            host=host,
            port=port,
            threads=4,
            _quiet=False
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
