from __future__ import annotations
import os
import logging
from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_settings
from app.models.quotes import QuoteRequest, QuoteResponse
from app.services.sicetac import SicetacClient
from app.api import quotes_crud
from app.api import auth_routes
from app.api import auth_monitoring

# Use development auth if environment is local
if os.getenv('ENVIRONMENT', 'local') == 'local':
    from app.core.auth_dev import get_current_user_dev as get_current_user
else:
    from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthz", tags=["ops"])
async def healthcheck() -> dict[str, str]:
    logger.debug("Healthcheck endpoint called")
    return {"status": "ok"}


def _sicetac_client(settings: Settings = Depends(get_settings)) -> SicetacClient:
    logger.debug("Creating SICETAC client")
    return SicetacClient(settings)


@router.post("/quote", response_model=QuoteResponse, tags=["quotes"])
async def create_quote(
    quote_request: QuoteRequest,
    _: dict = Depends(get_current_user),
    sicetac_client: SicetacClient = Depends(_sicetac_client),
) -> QuoteResponse:
    """Create a quick quote without persistence (direct Sicetac query)"""
    logger.info("=" * 60)
    logger.info("Quote request received")
    logger.info(f"Period: {quote_request.period}")
    logger.info(f"Configuration: {quote_request.configuration}")
    logger.info(f"Origin: {quote_request.origin}")
    logger.info(f"Destination: {quote_request.destination}")
    logger.info(f"Unit Type: {quote_request.unit_type}")
    logger.info(f"Cargo Type: {quote_request.cargo_type}")
    logger.info(f"Logistics Hours: {quote_request.logistics_hours}")
    logger.info("=" * 60)

    try:
        logger.debug("Fetching quotes from SICETAC...")
        quotes = await sicetac_client.fetch_quotes(quote_request)
        logger.info(f"Successfully fetched {len(quotes)} quotes from SICETAC")
        return QuoteResponse(request=quote_request, quotes=quotes)
    except Exception as e:
        logger.error(f"Failed to fetch quotes: {str(e)}", exc_info=True)
        raise


# Include CRUD routes
router.include_router(quotes_crud.router)

# Include auth routes (these don't require authentication)
router.include_router(auth_routes.router)

# Include auth monitoring routes
router.include_router(auth_monitoring.router)
