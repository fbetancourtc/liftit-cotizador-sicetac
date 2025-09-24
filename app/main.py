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
    app = FastAPI(
        title=settings.app_name,
        description="MVP FastAPI service for Sicetac quotations",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    # Mount static files for the frontend
    if os.path.exists("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", tags=["ops"])
    async def root():
        # Serve the HTML interface if it exists
        if os.path.exists("app/static/index.html"):
            return FileResponse("app/static/index.html")
        return {"service": settings.app_name, "environment": settings.environment}

    @app.get("/login", tags=["ops"])
    async def login_page():
        # Serve the login page
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
