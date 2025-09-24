from __future__ import annotations
import os
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.quotes import QuoteRequest, QuoteResponse
from app.services.sicetac import SicetacClient
from app.api import quotes_crud
from app.api import auth_routes

# Use development auth if environment is local
if os.getenv('ENVIRONMENT', 'local') == 'local':
    from app.core.auth_dev import get_current_user_dev as get_current_user
else:
    from app.core.auth import get_current_user

router = APIRouter()


@router.get("/healthz", tags=["ops"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def _sicetac_client(settings: Settings = Depends(get_settings)) -> SicetacClient:
    return SicetacClient(settings)


@router.post("/quote", response_model=QuoteResponse, tags=["quotes"])
async def create_quote(
    quote_request: QuoteRequest,
    _: dict = Depends(get_current_user),
    sicetac_client: SicetacClient = Depends(_sicetac_client),
) -> QuoteResponse:
    """Create a quick quote without persistence (direct Sicetac query)"""
    quotes = await sicetac_client.fetch_quotes(quote_request)
    return QuoteResponse(request=quote_request, quotes=quotes)


# Include CRUD routes
router.include_router(quotes_crud.router)

# Include auth routes (these don't require authentication)
router.include_router(auth_routes.router)
