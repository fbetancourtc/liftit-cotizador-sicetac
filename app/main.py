from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.models.database import init_database


def create_app() -> FastAPI:
    settings = get_settings()
    # Set root_path for subpath deployment
    root_path = os.environ.get('BASE_PATH', '/sicetac')
    app = FastAPI(
        title=settings.app_name,
        description="MVP FastAPI service for Sicetac quotations",
        version="1.0.0",
        root_path=root_path
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*", "https://micarga.flexos.ai"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    # Mount static files for the frontend - for local development
    if os.path.exists("app/static"):
        # For local development, mount at /static for direct access
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
        # Also mount at /sicetac/static for compatibility with production paths
        app.mount("/sicetac/static", StaticFiles(directory="app/static"), name="sicetac_static")

    @app.get("/", tags=["ops"])
    async def root():
        # Serve the login page as the home page
        if os.path.exists("app/static/login.html"):
            return FileResponse("app/static/login.html")
        return {"service": settings.app_name, "environment": settings.environment}

    @app.get("/api/config", tags=["ops"])
    async def get_config():
        # Return public configuration for the frontend
        # Handle missing or default values gracefully
        url = settings.supabase_project_url if settings.supabase_project_url != "https://your-project-ref.supabase.co" else ""
        key = settings.supabase_anon_key if settings.supabase_anon_key else ""
        return {
            "supabase_url": url,
            "supabase_anon_key": key
        }

    @app.get("/app", tags=["ops"])
    async def app_page():
        # Serve the main application interface
        if os.path.exists("app/static/index.html"):
            return FileResponse("app/static/index.html")
        return {"error": "Application page not found"}

    @app.get("/login", tags=["ops"])
    async def login_page():
        # Also serve the login page at /login for compatibility
        if os.path.exists("app/static/login.html"):
            return FileResponse("app/static/login.html")
        return {"error": "Login page not found"}

    @app.get("/dashboard", tags=["ops"])
    async def dashboard():
        # Serve the dashboard interface if it exists
        if os.path.exists("app/static/dashboard.html"):
            return FileResponse("app/static/dashboard.html")
        return {"error": "Dashboard not found"}

    @app.on_event("startup")
    async def startup_event():
        # Initialize database tables
        init_database()

    return app


app = create_app()
