#!/usr/bin/env python3
"""
Test script to debug SICETAC connection with comprehensive logging.
Run this to test the connection and see detailed debug output.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, '/Users/fbetncourtc/Documents/FlexOS/liftit-cotizador-sicetac')

from app.core.config import get_settings
from app.services.sicetac import SicetacClient
from app.models.quotes import QuoteRequest

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_sicetac_connection():
    """Test SICETAC connection with sample data."""
    print("=" * 80)
    print(f"SICETAC DEBUG TEST - {datetime.now()}")
    print("=" * 80)

    # Get settings
    settings = get_settings()
    print(f"\n📌 Environment: {settings.environment}")
    print(f"📌 SICETAC Endpoint: {settings.sicetac_endpoint}")
    print(f"📌 Username configured: {bool(settings.sicetac_username)}")
    print(f"📌 Password configured: {bool(settings.sicetac_password)}")
    print(f"📌 SSL Verification: {settings.sicetac_verify_ssl}")
    print(f"📌 Timeout: {settings.sicetac_timeout_seconds}s")

    # Create test request - using historical period that should have data
    test_request = QuoteRequest(
        period="202401",  # January 2024 - historical data
        configuration="2S3",
        origin="11001000",  # Bogotá
        destination="05001000",  # Medellín
        cargo_type=None,  # Try without cargo type filter
        unit_type=None,  # Try without unit type filter
        logistics_hours=0  # Start with 0 hours
    )

    print(f"\n📝 Test Request:")
    print(f"  - Period: {test_request.period}")
    print(f"  - Configuration: {test_request.configuration}")
    print(f"  - Origin: {test_request.origin} (Bogotá)")
    print(f"  - Destination: {test_request.destination} (Medellín)")
    print(f"  - Cargo Type: {test_request.cargo_type}")
    print(f"  - Unit Type: {test_request.unit_type}")
    print(f"  - Logistics Hours: {test_request.logistics_hours}")

    # Create client and test
    client = SicetacClient(settings)

    print(f"\n🚀 Sending request to SICETAC...")
    print("=" * 80)

    try:
        quotes = await client.fetch_quotes(test_request)

        print(f"\n✅ SUCCESS! Received {len(quotes)} quotes")
        print("=" * 80)

        for i, quote in enumerate(quotes, 1):
            print(f"\n📊 Quote #{i}:")
            print(f"  - Route Code: {quote.route_code}")
            print(f"  - Route Name: {quote.route_name}")
            print(f"  - Unit Type: {quote.unit_type}")
            print(f"  - Cargo Type: {quote.cargo_type}")
            print(f"  - Mobilization Value: ${quote.mobilization_value:,.0f}")
            print(f"  - Ton Value: ${quote.ton_value:,.0f}" if quote.ton_value else "  - Ton Value: N/A")
            print(f"  - Hour Value: ${quote.hour_value:,.0f}" if quote.hour_value else "  - Hour Value: N/A")
            print(f"  - Distance: {quote.distance_km:.1f} km" if quote.distance_km else "  - Distance: N/A")
            print(f"  - Minimum Payable: ${quote.minimum_payable:,.0f}")

        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"\n🔍 Error Type: {type(e).__name__}")

        import traceback
        print("\n📋 Full Stack Trace:")
        traceback.print_exc()

        print("\n" + "=" * 80)
        print("❌ Test failed!")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_sicetac_connection())
    sys.exit(0 if result else 1)