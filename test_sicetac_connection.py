#!/usr/bin/env python3
"""
Test SICETAC connection with real credentials
"""

import httpx
import json
import sys

def test_sicetac_quote():
    """Test the SICETAC quote endpoint with a real request"""

    # Test data for a known route
    test_quote = {
        "period": "202501",  # Format: yyyymm
        "configuration": "3S3",  # Valid configuration
        "origin": "11001000",  # Bogotá D.C. DIVIPOLA code
        "destination": "05001000",  # Medellín DIVIPOLA code
        "cargo_type": "GENERAL",  # Valid cargo type
        "unit_type": "ESTACAS",  # Valid unit type (ESTACAS, TRAYLER, or TERMOKING)
        "logistics_hours": 8,
        "company_name": "TEST COMPANY"
    }

    url = "http://localhost:5050/sicetac/api/quote"

    print("🚀 Testing SICETAC connection at localhost:5050...")
    print(f"📦 Test quote data: {json.dumps(test_quote, indent=2)}")

    try:
        # Make the request
        response = httpx.post(
            url,
            json=test_quote,
            timeout=30.0,
            headers={
                "Content-Type": "application/json"
            }
        )

        print(f"\n📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Got response from SICETAC")
            print(f"\n📊 Response data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if "quotes" in data and data["quotes"]:
                print(f"\n✨ Found {len(data['quotes'])} quotes")
                for i, quote in enumerate(data["quotes"], 1):
                    print(f"\nQuote {i}:")
                    print(f"  Route: {quote.get('route_name', 'N/A')}")
                    print(f"  Unit Type: {quote.get('unit_type', 'N/A')}")
                    print(f"  Minimum Payable: ${quote.get('minimum_payable', 0):,.2f}")
                    print(f"  Distance: {quote.get('distance_km', 0)} km")
            else:
                print("⚠️ No quotes returned in response")

        elif response.status_code == 422:
            print("❌ Validation error:")
            print(response.text)
        elif response.status_code == 502:
            print("❌ Bad Gateway - SICETAC service may be unavailable")
            print(response.text)
        elif response.status_code == 401:
            print("❌ Authentication required - please login first")
        elif response.status_code == 404:
            print("❌ No quotes found for this route")
            print(response.text)
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(response.text)

    except httpx.ConnectError:
        print("❌ Could not connect to localhost:5050")
        print("   Make sure the server is running: uvicorn app.main:app --reload --port 5050")
        sys.exit(1)
    except httpx.TimeoutException:
        print("❌ Request timed out after 30 seconds")
        print("   SICETAC service may be slow or unavailable")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_sicetac_quote()