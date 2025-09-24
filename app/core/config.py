from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application configuration sourced from environment variables."""

    app_name: str = Field(default="Liftit Cotizador SICETAC")
    environment: str = Field(default="local")

    # Supabase auth integration
    supabase_project_url: str = Field(
        default="https://your-project-ref.supabase.co",
        validation_alias="SUPABASE_PROJECT_URL",
    )
    supabase_jwks_url: str | None = Field(
        default=None,
        validation_alias="SUPABASE_JWKS_URL",
        description="Optional override for the Supabase JWKS endpoint.",
    )
    supabase_audience: str | None = Field(
        default=None,
        validation_alias="SUPABASE_JWT_AUDIENCE",
        description="Audience claim expected on Supabase-issued JWTs.",
    )
    supabase_anon_key: str = Field(
        default="",
        validation_alias="SUPABASE_ANON_KEY",
        description="Supabase anonymous/public key for client authentication.",
    )

    # RNDC / SiceTac service credentials
    sicetac_username: str = Field(default="", validation_alias="SICETAC_USERNAME")
    sicetac_password: str = Field(default="", validation_alias="SICETAC_PASSWORD")
    sicetac_endpoint: str = Field(
        default="http://rndcws.mintransporte.gov.co:8080/ws/rndcService",
        validation_alias="SICETAC_ENDPOINT",
        description="Full endpoint that accepts the Sicetac XML payloads.",
    )
    sicetac_timeout_seconds: float = Field(
        default=20.0,
        validation_alias="SICETAC_TIMEOUT_SECONDS",
    )
    sicetac_verify_ssl: bool = Field(default=False, validation_alias="SICETAC_VERIFY_SSL")

    # Database configuration
    database_url: str = Field(
        default="sqlite:///./quotations.db",
        validation_alias="DATABASE_URL",
        description="Database connection URL. Use PostgreSQL for production on Vercel."
    )

    request_log_samples: int = Field(
        default=100,
        validation_alias="REQUEST_LOG_SAMPLES",
        description="Limits structured logging of upstream SOAP requests to avoid leaking credentials.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def jwks_url(self) -> str:
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        project_url = self.supabase_project_url.rstrip("/")
        return f"{project_url}/auth/v1/jwks"


@lru_cache
def get_settings() -> Settings:
    return Settings()
