"""
Smart Farming Backend - FastAPI Server Runner
Uses Uvicorn for FastAPI
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    try:
        import uvicorn
        host = '0.0.0.0'  # Listen on all interfaces for Render/production
        port = int(os.getenv('PORT', 8000))
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Smart Farming Backend (FastAPI)")
        print(f"{'='*60}")
        print(f"Server: Uvicorn (FastAPI)")
        print(f"Address: http://0.0.0.0:{port}")
        print(f"Database: Neon PostgreSQL (Render)")
        print(f"Debug: OFF")
        print(f"{'='*60}\n")
        
        # Run with Uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
