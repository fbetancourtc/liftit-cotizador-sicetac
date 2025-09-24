from __future__ import annotations

from typing import Iterable, List, Optional

from pydantic import BaseModel, Field, field_validator

_ALLOWED_CONFIGS = {"2", "3", "2S2", "2S3", "3S2", "3S3"}
_ALLOWED_CARGO_TYPES = {"GENERAL", "CONTENEDOR", "CARGA REFRIGERADA", "GRANEL SÓLIDO"}
_ALLOWED_UNIT_TYPES = {"ESTACAS", "TRAYLER", "TERMOKING"}


class QuoteRequest(BaseModel):
    period: str = Field(..., description="Period in yyyymm format (e.g. 202401).")
    configuration: str = Field(..., description="Truck configuration code (e.g. 3S3).")
    origin: str = Field(..., description="DIVIPOLA origin code with trailing 000 for the municipality head.")
    destination: str = Field(..., description="DIVIPOLA destination code with trailing 000.")
    cargo_type: Optional[str] = Field(
        default=None,
        description="Optional filter for cargo type (General, Contenedor, Carga Refrigerada).",
    )
    unit_type: Optional[str] = Field(
        default=None,
        description="Optional filter for unit type (Estacas, Trayler, Termoking).",
    )
    logistics_hours: float = Field(
        default=0.0,
        ge=0,
        description="Total negotiated logistics hours (loading, unloading, waiting).",
    )
    variables: Optional[List[str]] = Field(
        default=None,
        description="Override the RNDC variables list if a custom payload is needed.",
    )

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if len(value) != 6 or not value.isdigit():
            raise ValueError("Period must follow yyyymm format")
        return value

    @field_validator("configuration")
    @classmethod
    def normalise_configuration(cls, value: str) -> str:
        candidate = value.upper()
        if candidate not in _ALLOWED_CONFIGS:
            raise ValueError(f"Configuration '{value}' is not supported by Sicetac")
        return candidate

    @field_validator("origin", "destination")
    @classmethod
    def validate_divipola(cls, value: str) -> str:
        if len(value) != 8 or not value.isdigit() or not value.endswith("000"):
            raise ValueError("DIVIPOLA codes must be 8 digits ending in 000")
        return value

    @field_validator("cargo_type")
    @classmethod
    def validate_cargo(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value.upper() not in _ALLOWED_CARGO_TYPES:
            raise ValueError(
                "Cargo type must be one of General, Contenedor, Carga Refrigerada, Granel Sólido",
            )
        return value.upper()

    @field_validator("unit_type")
    @classmethod
    def validate_unit(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value.upper() not in _ALLOWED_UNIT_TYPES:
            raise ValueError("Unit type must be one of Estacas, Trayler, Termoking")
        return value.upper()

    @field_validator("variables")
    @classmethod
    def ensure_uppercase(cls, value: Optional[Iterable[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        return [item.strip().upper() for item in value]


class QuoteResult(BaseModel):
    route_code: Optional[str] = Field(default=None, description="RNDC route identifier.")
    route_name: Optional[str] = Field(default=None)
    unit_type: Optional[str] = Field(default=None)
    cargo_type: Optional[str] = Field(default=None)
    mobilization_value: float = Field(..., description="Base mobilization cost from Sicetac.")
    ton_value: Optional[float] = Field(default=None, description="Cost per ton of mobilization.")
    hour_value: Optional[float] = Field(default=None, description="Hourly cost used for logistics time adjustments.")
    distance_km: Optional[float] = Field(default=None)
    minimum_payable: float = Field(..., description="Mobilization value plus logistics hours priced with hour_value.")


class QuoteResponse(BaseModel):
    request: QuoteRequest
    quotes: List[QuoteResult]
