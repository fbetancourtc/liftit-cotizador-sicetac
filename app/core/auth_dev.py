from __future__ import annotations

import logging
from typing import Dict, Any
from fastapi import Request

logger = logging.getLogger(__name__)

def get_current_user_dev(request: Request) -> Dict[str, Any]:
    """
    Development-only authentication bypass.
    Returns a mock user for testing purposes.
    """
    logger.debug("Using development authentication bypass")
    logger.debug(f"Request path: {request.url.path}")
    logger.debug(f"Request method: {request.method}")

    mock_user = {
        "sub": "dev-user-123",
        "email": "dev@example.com",
        "role": "admin",
        "iat": 1700000000,
        "exp": 9999999999
    }
    logger.debug(f"Returning mock user: {mock_user['email']}")
    return mock_user