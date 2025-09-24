from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

Base = declarative_base()


class QuotationDB(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Request details
    period = Column(String(6), nullable=False)
    configuration = Column(String(10), nullable=False)
    origin_code = Column(String(8), nullable=False)
    destination_code = Column(String(8), nullable=False)
    cargo_type = Column(String(50), nullable=True)
    unit_type = Column(String(50), nullable=True)
    logistics_hours = Column(Float, default=0.0)

    # Quote results (stored as JSON for flexibility)
    quotes_data = Column(JSON, nullable=False)

    # Metadata
    user_id = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active, archived, deleted

    # Calculated fields
    total_cost = Column(Float, nullable=True)
    selected_quote_index = Column(Integer, nullable=True)


# Database connection setup
settings = get_settings()
DATABASE_URL = settings.database_url

# Configure the engine based on the database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration for local development
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL configuration for production (Vercel)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize the database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()