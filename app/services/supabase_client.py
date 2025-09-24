from __future__ import annotations

from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.core.config import get_settings


class SupabaseService:
    """Service for interacting with Supabase authentication and database."""

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create a Supabase client instance."""
        if cls._client is None:
            settings = get_settings()
            cls._client = create_client(
                settings.supabase_project_url,
                settings.supabase_anon_key
            )
        return cls._client

    @classmethod
    async def sign_in_with_email(cls, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with email and password."""
        client = cls.get_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {
            "user": response.user.model_dump() if response.user else None,
            "session": {
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None,
                "expires_in": response.session.expires_in if response.session else None,
            } if response.session else None
        }

    @classmethod
    async def sign_up(cls, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user with email and password."""
        client = cls.get_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        return {
            "user": response.user.model_dump() if response.user else None,
            "session": {
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None,
                "expires_in": response.session.expires_in if response.session else None,
            } if response.session else None
        }

    @classmethod
    async def sign_out(cls, access_token: str) -> None:
        """Sign out the current user."""
        client = cls.get_client()
        client.auth.sign_out()

    @classmethod
    async def get_user(cls, access_token: str) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user."""
        client = cls.get_client()
        client.auth._headers["Authorization"] = f"Bearer {access_token}"
        response = client.auth.get_user()
        if response and response.user:
            return response.user.model_dump()
        return None

    @classmethod
    async def refresh_session(cls, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using a refresh token."""
        client = cls.get_client()
        response = client.auth.refresh_session(refresh_token)
        return {
            "user": response.user.model_dump() if response.user else None,
            "session": {
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None,
                "expires_in": response.session.expires_in if response.session else None,
            } if response.session else None
        }