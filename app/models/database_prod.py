from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

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
    user_id = Column(String(255), nullable=True, index=True)
    company_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active", index=True)

    # Calculated fields
    total_cost = Column(Float, nullable=True)
    selected_quote_index = Column(Integer, nullable=True)

    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_period_config', 'period', 'configuration'),
        Index('idx_route', 'origin_code', 'destination_code'),
        Index('idx_created_at', 'created_at'),
    )


def get_database_url():
    """Get database URL from environment or use default"""
    if os.getenv('ENVIRONMENT') == 'production':
        return os.getenv('DATABASE_URL', 'postgresql://sicetac_user:password@localhost:5432/sicetac_db')
    else:
        return "sqlite:///./quotations.db"


# Database connection setup
DATABASE_URL = get_database_url()

# Configure engine based on environment
if 'postgresql' in DATABASE_URL:
    # Production PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
else:
    # Development SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )

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