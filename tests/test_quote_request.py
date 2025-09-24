import pytest
from pydantic import ValidationError

from app.models.quotes import QuoteRequest


def test_valid_quote_request():
    req = QuoteRequest(
        period="202401",
        configuration="3S3",
        origin="11001000",
        destination="50010000",
        logistics_hours=2.5,
    )
    assert req.configuration == "3S3"
    assert req.logistics_hours == 2.5


def test_invalid_period():
    with pytest.raises(ValidationError):
        QuoteRequest(
            period="20241",
            configuration="3S3",
            origin="11001000",
            destination="50010000",
        )


def test_invalid_configuration():
    with pytest.raises(ValidationError):
        QuoteRequest(
            period="202401",
            configuration="1S1",
            origin="11001000",
            destination="50010000",
        )
