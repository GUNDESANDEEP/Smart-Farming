#!/usr/bin/env python
"""
Run Flask app using Waitress WSGI server (Windows-friendly alternative)
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_file)

# Import the Flask app from backend
from backend.app import app
from waitress import serve

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    host = '0.0.0.0'
    
    print(f"\n✅ Starting Smart Farming Backend with Waitress")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   URL: http://localhost:{port}")
    print(f"\n📡 Waiting for requests...\n")
    
    serve(app, host=host, port=port)
