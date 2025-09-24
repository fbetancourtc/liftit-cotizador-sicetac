from __future__ import annotations

from typing import Dict, Any
from fastapi import Request

def get_current_user_dev(request: Request) -> Dict[str, Any]:
    """
    Development-only authentication bypass.
    Returns a mock user for testing purposes.
    """
    return {
        "sub": "dev-user-123",
        "email": "dev@example.com",
        "role": "admin",
        "iat": 1700000000,
        "exp": 9999999999
    }