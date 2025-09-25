"""
Rate limiting middleware for API protection.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("rate_limit")


class RateLimitManager:
    """
    Token bucket algorithm for rate limiting.
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        burst_size: Optional[int] = None
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or max_requests * 2
        self.buckets: Dict[str, Dict] = defaultdict(self._create_bucket)

    def _create_bucket(self) -> Dict:
        """Create a new token bucket."""
        return {
            "tokens": self.max_requests,
            "last_refill": time.time(),
            "request_count": 0,
            "window_start": time.time()
        }

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Priority: API key > User ID > IP address

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"

        # Check for authenticated user
        if hasattr(request.state, "user"):
            user = request.state.user
            if user and user.get("email"):
                return f"user:{user['email']}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _refill_tokens(self, bucket: Dict):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket["last_refill"]

        # Calculate tokens to add
        tokens_to_add = (elapsed / self.window_seconds) * self.max_requests

        # Add tokens, cap at burst size
        bucket["tokens"] = min(
            bucket["tokens"] + tokens_to_add,
            self.burst_size
        )
        bucket["last_refill"] = now

        # Reset window if needed
        if now - bucket["window_start"] >= self.window_seconds:
            bucket["request_count"] = 0
            bucket["window_start"] = now

    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limits.
        Returns (allowed, limit_info).
        """
        client_id = self._get_client_id(request)
        bucket = self.buckets[client_id]

        # Refill tokens
        self._refill_tokens(bucket)

        # Check if tokens available
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            bucket["request_count"] += 1

            limit_info = {
                "limit": self.max_requests,
                "remaining": int(bucket["tokens"]),
                "reset": int(bucket["window_start"] + self.window_seconds),
                "retry_after": None
            }
            return True, limit_info

        # Calculate retry after
        retry_after = self.window_seconds - (time.time() - bucket["window_start"])

        limit_info = {
            "limit": self.max_requests,
            "remaining": 0,
            "reset": int(bucket["window_start"] + self.window_seconds),
            "retry_after": int(retry_after)
        }
        return False, limit_info

    def get_stats(self) -> Dict:
        """Get rate limiting statistics."""
        now = time.time()
        active_buckets = sum(
            1 for b in self.buckets.values()
            if now - b["last_refill"] < 300  # Active in last 5 minutes
        )

        return {
            "total_clients": len(self.buckets),
            "active_clients": active_buckets,
            "max_requests_per_window": self.max_requests,
            "window_seconds": self.window_seconds,
            "burst_size": self.burst_size
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.
    """

    # Different limits for different endpoints
    ENDPOINT_LIMITS = {
        "/api/quote": {"max_requests": 60, "window": 60},  # 60 per minute
        "/api/quotes": {"max_requests": 30, "window": 60},  # 30 per minute
        "/api/auth": {"max_requests": 10, "window": 60},  # 10 per minute
        "/api/health": {"max_requests": 100, "window": 60},  # 100 per minute
        "default": {"max_requests": 100, "window": 60}  # 100 per minute
    }

    def __init__(self, app, **options):
        super().__init__(app)
        self.managers = {}

        # Create rate limit managers for each endpoint
        for endpoint, limits in self.ENDPOINT_LIMITS.items():
            self.managers[endpoint] = RateLimitManager(
                max_requests=limits["max_requests"],
                window_seconds=limits["window"]
            )

    def _get_endpoint_path(self, path: str) -> str:
        """Get the endpoint path for rate limiting."""
        # Remove trailing slashes and parameters
        path = path.rstrip("/").split("?")[0]

        # Match to configured endpoints
        for endpoint in self.ENDPOINT_LIMITS.keys():
            if endpoint != "default" and path.startswith(endpoint):
                return endpoint

        return "default"

    def _should_rate_limit(self, request: Request) -> bool:
        """Check if request should be rate limited."""
        # Skip rate limiting for:
        # - Static files
        # - WebSocket connections
        # - Health checks from monitoring

        path = request.url.path

        if path.startswith("/static/"):
            return False

        if path.startswith("/ws"):
            return False

        # Allow monitoring services
        user_agent = request.headers.get("User-Agent", "")
        if any(monitor in user_agent for monitor in ["Datadog", "Pingdom", "UptimeRobot"]):
            return False

        return True

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""

        # Check if should rate limit
        if not self._should_rate_limit(request):
            return await call_next(request)

        # Get appropriate rate limiter
        endpoint = self._get_endpoint_path(request.url.path)
        manager = self.managers.get(endpoint, self.managers["default"])

        # Check rate limit
        allowed, limit_info = manager.check_rate_limit(request)

        # Add rate limit headers
        response = None

        if allowed:
            response = await call_next(request)
        else:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {manager._get_client_id(request)} "
                f"on {endpoint}"
            )

            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {limit_info['retry_after']} seconds",
                    "retry_after": limit_info["retry_after"]
                }
            )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])

        if limit_info["retry_after"]:
            response.headers["Retry-After"] = str(limit_info["retry_after"])

        return response


class APIKeyValidator:
    """
    API key validation for B2B clients.
    """

    def __init__(self):
        # In production, these would be stored in database
        self.api_keys = {
            "test_key_123": {
                "client": "Test Client",
                "tier": "basic",
                "rate_limit": 100,
                "created_at": datetime.utcnow()
            }
        }

    def validate_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return client info."""
        return self.api_keys.get(api_key)

    def create_key(self, client_name: str, tier: str = "basic") -> str:
        """Create a new API key for a client."""
        import secrets

        api_key = f"lft_{secrets.token_urlsafe(32)}"

        self.api_keys[api_key] = {
            "client": client_name,
            "tier": tier,
            "rate_limit": 100 if tier == "basic" else 1000,
            "created_at": datetime.utcnow()
        }

        return api_key

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False


# Global instances
rate_limit_manager = RateLimitManager()
api_key_validator = APIKeyValidator()