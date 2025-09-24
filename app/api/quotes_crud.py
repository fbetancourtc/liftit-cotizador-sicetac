from __future__ import annotations

from typing import List, Optional
from datetime import datetime
import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.models.quotes import QuoteRequest, QuoteResponse
from app.models.database import QuotationDB, get_db
from app.services.sicetac import SicetacClient
import json

# Use development auth if environment is local
if os.getenv('ENVIRONMENT', 'local') == 'local':
    from app.core.auth_dev import get_current_user_dev as get_current_user
else:
    from app.core.auth import get_current_user


router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuotationCreate(BaseModel):
    request: QuoteRequest
    company_name: Optional[str] = None
    notes: Optional[str] = None


class QuotationUpdate(BaseModel):
    company_name: Optional[str] = None
    notes: Optional[str] = None
    selected_quote_index: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(active|archived|deleted)$")


class QuotationResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    period: str
    configuration: str
    origin_code: str
    destination_code: str
    cargo_type: Optional[str]
    unit_type: Optional[str]
    logistics_hours: float
    quotes_data: dict
    user_id: Optional[str]
    company_name: Optional[str]
    notes: Optional[str]
    status: str
    total_cost: Optional[float]
    selected_quote_index: Optional[int]

    class Config:
        from_attributes = True


def _sicetac_client(settings: Settings = Depends(get_settings)) -> SicetacClient:
    return SicetacClient(settings)


@router.post("/", response_model=QuotationResponse)
async def create_quotation(
    quotation_data: QuotationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    sicetac_client: SicetacClient = Depends(_sicetac_client),
) -> QuotationResponse:
    """Create a new quotation by fetching data from Sicetac and storing it"""

    # Fetch quotes from Sicetac
    quotes = await sicetac_client.fetch_quotes(quotation_data.request)

    # Calculate total cost (minimum of all quotes)
    total_cost = min(q.minimum_payable for q in quotes) if quotes else None

    # Prepare quotes data for storage
    quotes_data = {
        "request": quotation_data.request.model_dump(),
        "quotes": [q.model_dump() for q in quotes]
    }

    # Create database entry
    db_quotation = QuotationDB(
        period=quotation_data.request.period,
        configuration=quotation_data.request.configuration,
        origin_code=quotation_data.request.origin,
        destination_code=quotation_data.request.destination,
        cargo_type=quotation_data.request.cargo_type,
        unit_type=quotation_data.request.unit_type,
        logistics_hours=quotation_data.request.logistics_hours,
        quotes_data=quotes_data,
        user_id=current_user.get("sub"),
        company_name=quotation_data.company_name,
        notes=quotation_data.notes,
        total_cost=total_cost
    )

    db.add(db_quotation)
    db.commit()
    db.refresh(db_quotation)

    return QuotationResponse.model_validate(db_quotation)


@router.get("/", response_model=List[QuotationResponse])
async def list_quotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(active|archived|deleted)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[QuotationResponse]:
    """List all quotations for the current user"""

    query = db.query(QuotationDB).filter(QuotationDB.user_id == current_user.get("sub"))

    if status:
        query = query.filter(QuotationDB.status == status)

    quotations = query.offset(skip).limit(limit).all()

    return [QuotationResponse.model_validate(q) for q in quotations]


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(
    quotation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuotationResponse:
    """Get a specific quotation by ID"""

    quotation = db.query(QuotationDB).filter(
        QuotationDB.id == quotation_id,
        QuotationDB.user_id == current_user.get("sub")
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found"
        )

    return QuotationResponse.model_validate(quotation)


@router.patch("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation_id: int,
    update_data: QuotationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuotationResponse:
    """Update a quotation's metadata"""

    quotation = db.query(QuotationDB).filter(
        QuotationDB.id == quotation_id,
        QuotationDB.user_id == current_user.get("sub")
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found"
        )

    # Update fields if provided
    if update_data.company_name is not None:
        quotation.company_name = update_data.company_name
    if update_data.notes is not None:
        quotation.notes = update_data.notes
    if update_data.selected_quote_index is not None:
        quotation.selected_quote_index = update_data.selected_quote_index
    if update_data.status is not None:
        quotation.status = update_data.status

    quotation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(quotation)

    return QuotationResponse.model_validate(quotation)


@router.delete("/{quotation_id}")
async def delete_quotation(
    quotation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Soft delete a quotation (mark as deleted)"""

    quotation = db.query(QuotationDB).filter(
        QuotationDB.id == quotation_id,
        QuotationDB.user_id == current_user.get("sub")
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found"
        )

    quotation.status = "deleted"
    quotation.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Quotation deleted successfully"}