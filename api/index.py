"""
Vercel serverless function handler for FastAPI application.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import the app module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set default environment variables if not present to prevent initialization errors
os.environ.setdefault('DATABASE_URL', 'sqlite:///./quotations.db')
os.environ.setdefault('SICETAC_USERNAME', 'test')
os.environ.setdefault('SICETAC_PASSWORD', 'test')
os.environ.setdefault('SICETAC_ENDPOINT', 'http://rndcws.mintransporte.gov.co:8080/ws/rndcService')

try:
    # Try to import the FastAPI app
    from app.main import create_app
    # Create the FastAPI application instance
    app = create_app()
except Exception as e:
    print(f"Error creating main app: {e}")
    # Fallback to a minimal working app if main app fails
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse

    app = FastAPI(title="SICETAC Quotation System - Fallback Mode")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/healthz")
    async def health_check():
        return {"status": "ok", "message": "Service is running in fallback mode"}

    @app.get("/api/config")
    async def get_config():
        return {
            "supabase_url": os.environ.get("SUPABASE_PROJECT_URL", ""),
            "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", "")
        }

    @app.get("/")
    async def root():
        return {"message": "SICETAC Quotation System", "status": "fallback mode"}

    @app.get("/app")
    async def app_page():
        return {"message": "Application page", "status": "fallback mode"}

# Handler for Vercel
handler = app