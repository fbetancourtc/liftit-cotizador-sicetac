from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.supabase_client import SupabaseService


router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: Optional[dict] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    message: Optional[str] = None


@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest) -> AuthResponse:
    """Sign in with email and password."""
    try:
        result = await SupabaseService.sign_in_with_email(
            credentials.email,
            credentials.password
        )

        if not result.get("session"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        return AuthResponse(
            user=result.get("user"),
            access_token=result["session"]["access_token"],
            refresh_token=result["session"]["refresh_token"],
            expires_in=result["session"]["expires_in"]
        )
    except Exception as e:
        if "Invalid login credentials" in str(e):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/signup", response_model=AuthResponse)
async def signup(credentials: SignUpRequest) -> AuthResponse:
    """Sign up a new user with email and password."""
    try:
        result = await SupabaseService.sign_up(
            credentials.email,
            credentials.password
        )

        if not result.get("user"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        # Check if email confirmation is required
        if result.get("user") and not result.get("session"):
            return AuthResponse(
                user=result.get("user"),
                message="Please check your email to confirm your account"
            )

        return AuthResponse(
            user=result.get("user"),
            access_token=result["session"]["access_token"] if result.get("session") else None,
            refresh_token=result["session"]["refresh_token"] if result.get("session") else None,
            expires_in=result["session"]["expires_in"] if result.get("session") else None
        )
    except Exception as e:
        if "User already registered" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: TokenRefreshRequest) -> AuthResponse:
    """Refresh the access token using a refresh token."""
    try:
        result = await SupabaseService.refresh_session(request.refresh_token)

        if not result.get("session"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        return AuthResponse(
            user=result.get("user"),
            access_token=result["session"]["access_token"],
            refresh_token=result["session"]["refresh_token"],
            expires_in=result["session"]["expires_in"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


@router.post("/logout")
async def logout() -> dict:
    """Sign out the current user."""
    # Note: Supabase client-side logout doesn't require server validation
    # The actual logout happens on the client by removing the stored tokens
    return {"message": "Logged out successfully"}