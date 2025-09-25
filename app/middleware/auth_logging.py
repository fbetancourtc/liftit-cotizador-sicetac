"""
Authentication logging middleware for production monitoring.
Tracks authentication events and user sessions for debugging and audit.
"""

from fastapi import Request
from fastapi.responses import Response
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

# Configure authentication logger
auth_logger = logging.getLogger("auth")
auth_logger.setLevel(logging.INFO)

# Create file handler for auth logs
auth_handler = logging.FileHandler("auth_events.log")
auth_handler.setLevel(logging.INFO)

# Create console handler for important events
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
auth_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
auth_logger.addHandler(auth_handler)
auth_logger.addHandler(console_handler)


class AuthEvent:
    """Structure for authentication events."""

    LOGIN_ATTEMPT = "LOGIN_ATTEMPT"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    SESSION_CHECK = "SESSION_CHECK"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    OAUTH_ERROR = "OAUTH_ERROR"


def log_auth_event(
    event_type: str,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    provider: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """
    Log an authentication event with structured data.

    Args:
        event_type: Type of authentication event
        user_email: Email of the user (if available)
        user_id: User ID (if available)
        provider: Authentication provider (google, email, etc.)
        success: Whether the operation succeeded
        error_message: Error message if operation failed
        metadata: Additional context data
        request: FastAPI request object for IP/UA tracking
    """
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "success": success,
        "user_email": user_email,
        "user_id": user_id,
        "provider": provider,
    }

    # Add request metadata if available
    if request:
        event_data.update({
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        })

    # Add error information if present
    if error_message:
        event_data["error"] = error_message
        event_data["stack_trace"] = traceback.format_exc() if not success else None

    # Add additional metadata
    if metadata:
        event_data["metadata"] = metadata

    # Log at appropriate level
    log_message = json.dumps(event_data, indent=2)

    if success:
        auth_logger.info(log_message)
    else:
        auth_logger.error(log_message)

    return event_data


def track_session_activity(
    user_email: str,
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Track user session activity for audit purposes.

    Args:
        user_email: Email of the active user
        user_id: User ID
        action: Action performed by user
        details: Additional action details
    """
    activity_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_email": user_email,
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }

    auth_logger.info(f"SESSION_ACTIVITY: {json.dumps(activity_data)}")
    return activity_data


class AuthLoggingMiddleware:
    """Middleware to track authentication-related requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Track OAuth callbacks
        if "/auth/callback" in str(request.url):
            log_auth_event(
                AuthEvent.OAUTH_CALLBACK,
                metadata={"url": str(request.url)},
                request=request
            )

        # Track API authentication endpoints
        if request.url.path == "/api/auth/session":
            log_auth_event(
                AuthEvent.SESSION_CHECK,
                request=request
            )

        response = await call_next(request)
        return response


# Helper functions for frontend logging
def parse_frontend_log(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and structure frontend authentication logs.

    Args:
        log_data: Raw log data from frontend

    Returns:
        Structured log entry
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "frontend",
        "type": log_data.get("type", "unknown"),
        "level": log_data.get("level", "info"),
        "message": log_data.get("message"),
        "user_email": log_data.get("user_email"),
        "metadata": log_data.get("metadata", {}),
        "user_agent": log_data.get("user_agent"),
        "url": log_data.get("url")
    }


# Monitoring helper functions
def get_auth_stats() -> Dict[str, Any]:
    """
    Get authentication statistics for monitoring.

    Returns:
        Dictionary with authentication metrics
    """
    # This would connect to your logging backend in production
    return {
        "total_logins_today": 0,
        "failed_attempts": 0,
        "active_sessions": 0,
        "providers_used": {
            "google": 0,
            "email": 0
        }
    }


def alert_on_suspicious_activity(event_data: Dict[str, Any]):
    """
    Send alerts for suspicious authentication patterns.

    Args:
        event_data: Event data to analyze
    """
    # Check for multiple failed attempts
    # Check for unusual login locations
    # Check for rapid session creation
    # In production, this would integrate with your alerting system
    pass