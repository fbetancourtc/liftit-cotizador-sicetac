from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from cachetools import TTLCache
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings


def _retry_jwks_fetch(func):
    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


class _JWKSCache:
    """Caches the Supabase JWKS document to minimise network calls."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._cache = TTLCache(maxsize=1, ttl=ttl_seconds)

    def get(self) -> Optional[Dict[str, Any]]:
        try:
            return self._cache["jwks"]
        except KeyError:
            return None

    def set(self, value: Dict[str, Any]) -> None:
        self._cache["jwks"] = value


class SupabaseJWTBearer(HTTPBearer):
    """Validates Supabase-issued JWTs using the project's JWKS endpoint."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(auto_error=False)
        self.settings = settings
        self._jwks_cache = _JWKSCache()
        self._issuer = f"{self.settings.supabase_project_url.rstrip('/')}/auth/v1"

    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        token = credentials.credentials
        try:
            payload = await self._decode_jwt(token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            ) from exc
        request.state.user = payload
        return payload

    async def _decode_jwt(self, token: str) -> Dict[str, Any]:
        jwks = await self._get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        if key is None:
            raise JWTError("Unable to locate matching key")

        options = {"verify_aud": bool(self.settings.supabase_audience)}
        audience = self.settings.supabase_audience if self.settings.supabase_audience else None
        return jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience=audience,
            issuer=self._issuer,
            options=options,
        )

    @_retry_jwks_fetch
    async def _download_jwks(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.settings.jwks_url, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def _get_jwks(self) -> Dict[str, Any]:
        cached = self._jwks_cache.get()
        if cached is not None:
            return cached
        jwks = await self._download_jwks()
        self._jwks_cache.set(jwks)
        return jwks


jwt_auth_scheme = SupabaseJWTBearer(get_settings())


def get_current_user(payload: Dict[str, Any] = Depends(jwt_auth_scheme)) -> Dict[str, Any]:
    """Dependency that exposes the decoded Supabase JWT claims to route handlers."""

    return payload
