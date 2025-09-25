"""
Production-ready FastAPI application with all services integrated.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import routes
from app.api import routes, websocket

# Import middleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth_logging import AuthLoggingMiddleware

# Import services
from app.services.realtime import initialize_realtime_services, shutdown_realtime_services
from app.services.cache import initialize_cache
from app.services.monitoring import initialize_monitoring, metrics_collector, health_checker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    """
    logger.info("Starting production application...")

    # Initialize services
    try:
        # Initialize cache
        cache_service = await initialize_cache()
        app.state.cache = cache_service

        # Initialize real-time services
        await initialize_realtime_services()

        # Initialize monitoring
        await initialize_monitoring()

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down production application...")

    try:
        await shutdown_realtime_services()
        if hasattr(app.state, "cache") and app.state.cache:
            await app.state.cache.disconnect()

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Liftit Sicetac API",
    description="Real-time trucking fare pricing system",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://liftit.co,https://*.liftit.co").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.liftit.co", "localhost", "127.0.0.1"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Auth logging middleware
app.add_middleware(AuthLoggingMiddleware)

# Performance monitoring middleware
@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    """Monitor request performance."""
    import uuid
    from app.services.monitoring import performance_monitor

    request_id = str(uuid.uuid4())[:8]
    performance_monitor.start_request(request_id)

    try:
        response = await call_next(request)

        performance_monitor.end_request(
            request_id,
            request.url.path,
            response.status_code,
            request.method
        )

        return response

    except Exception as e:
        performance_monitor.record_error(
            type(e).__name__,
            request.url.path
        )
        raise


# Mount static files
app.mount("/sicetac/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
app.include_router(routes.router, prefix="/sicetac/api")
app.include_router(websocket.router, prefix="/sicetac")


# Root redirect
@app.get("/")
async def root():
    """Redirect to main application."""
    return JSONResponse(
        content={"redirect": "/sicetac/"},
        status_code=307,
        headers={"Location": "/sicetac/"}
    )


# Main application page
@app.get("/sicetac/")
async def sicetac_root():
    """Serve the main application."""
    with open("app/static/index.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)


# Login page
@app.get("/sicetac/login")
async def sicetac_login():
    """Serve the login page."""
    with open("app/static/login.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)


# Health endpoints
@app.get("/health")
async def health():
    """Basic health check."""
    return {"status": "healthy", "service": "sicetac-api"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with all service statuses."""
    return await health_checker.run_checks()


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Get application metrics."""
    return {
        "http_requests": metrics_collector.get_stats("http.request.count"),
        "response_times": metrics_collector.get_stats("http.request.duration"),
        "errors": metrics_collector.get_stats("error.count"),
        "cache": {
            "hits": metrics_collector.get_stats("cache.hit"),
            "misses": metrics_collector.get_stats("cache.miss")
        }
    }


# Admin endpoints
@app.get("/api/admin/cache/stats")
async def cache_stats(request: Request):
    """Get cache statistics (admin only)."""
    if hasattr(request.app.state, "cache"):
        return request.app.state.cache.get_stats()
    return {"status": "cache not initialized"}


@app.post("/api/admin/cache/clear")
async def clear_cache(request: Request, pattern: str = "*"):
    """Clear cache entries (admin only)."""
    if hasattr(request.app.state, "cache"):
        count = await request.app.state.cache.clear_pattern(pattern)
        return {"cleared": count, "pattern": pattern}
    return {"error": "cache not initialized"}


if __name__ == "__main__":
    # Production server configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    workers = int(os.getenv("WORKERS", 4))

    logger.info(f"Starting production server on {host}:{port} with {workers} workers")

    uvicorn.run(
        "app.main_production:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        use_colors=False,
        loop="uvloop"  # High-performance event loop
    )