"""
Authentication monitoring endpoints for logging and tracking.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.middleware.auth_logging import (
    log_auth_event,
    AuthEvent,
    parse_frontend_log,
    track_session_activity,
    get_auth_stats
)

router = APIRouter(prefix="/auth/monitoring", tags=["auth-monitoring"])

# Configure logger
logger = logging.getLogger("auth.api")


class FrontendLogEntry(BaseModel):
    """Schema for frontend log entries."""
    type: str
    level: str = "info"
    message: str
    user_email: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None
    url: Optional[str] = None


class SessionActivity(BaseModel):
    """Schema for session activity tracking."""
    user_email: str
    user_id: str
    action: str
    details: Optional[Dict[str, Any]] = None


@router.post("/log")
async def log_frontend_event(
    log_entry: FrontendLogEntry,
    request: Request
):
    """
    Receive and process frontend authentication logs.

    Args:
        log_entry: Log data from frontend
        request: FastAPI request object

    Returns:
        Success confirmation
    """
    try:
        # Add request metadata
        log_data = log_entry.dict()
        log_data["user_agent"] = request.headers.get("user-agent", log_data.get("user_agent"))
        log_data["url"] = str(request.url)

        # Parse and log the event
        parsed_log = parse_frontend_log(log_data)

        # Map to auth event if applicable
        if log_entry.type == "login_attempt":
            log_auth_event(
                AuthEvent.LOGIN_ATTEMPT,
                user_email=log_entry.user_email,
                metadata=log_entry.metadata,
                request=request
            )
        elif log_entry.type == "login_success":
            log_auth_event(
                AuthEvent.LOGIN_SUCCESS,
                user_email=log_entry.user_email,
                user_id=log_entry.user_id,
                provider=log_entry.metadata.get("provider") if log_entry.metadata else None,
                success=True,
                request=request
            )
        elif log_entry.type == "login_failure":
            log_auth_event(
                AuthEvent.LOGIN_FAILURE,
                user_email=log_entry.user_email,
                success=False,
                error_message=log_entry.message,
                metadata=log_entry.metadata,
                request=request
            )
        elif log_entry.type == "logout":
            log_auth_event(
                AuthEvent.LOGOUT,
                user_email=log_entry.user_email,
                user_id=log_entry.user_id,
                request=request
            )

        logger.info(f"Frontend log processed: {log_entry.type}")
        return {"status": "logged", "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Error processing frontend log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process log entry")


@router.post("/activity")
async def track_activity(
    activity: SessionActivity,
    request: Request
):
    """
    Track user session activity.

    Args:
        activity: Activity data
        request: FastAPI request object

    Returns:
        Success confirmation
    """
    try:
        result = track_session_activity(
            user_email=activity.user_email,
            user_id=activity.user_id,
            action=activity.action,
            details=activity.details
        )

        return {"status": "tracked", "timestamp": result["timestamp"]}

    except Exception as e:
        logger.error(f"Error tracking activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track activity")


@router.get("/stats")
async def get_authentication_stats():
    """
    Get authentication statistics for monitoring.

    Returns:
        Authentication metrics and statistics
    """
    try:
        stats = get_auth_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching auth stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/health")
async def auth_monitoring_health():
    """
    Health check for authentication monitoring.

    Returns:
        Health status of the monitoring system
    """
    return {
        "status": "healthy",
        "service": "auth-monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }