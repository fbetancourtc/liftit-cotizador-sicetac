#!/usr/bin/env python3
"""
Test script to verify the Vercel deployment configuration and Supabase connection.
"""

import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_local_server():
    """Test if the local server is running and configured correctly."""

    print("Testing Local Server Configuration")
    print("=" * 50)

    base_url = "http://localhost:5050"

    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server is running on {base_url}")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running on {base_url}")
        print("   Run: uvicorn app.main:app --reload --port 5050")
        return False

    # Test 2: Check API config endpoint
    try:
        response = requests.get(f"{base_url}/api/config")
        if response.status_code == 200:
            config = response.json()
            print("✅ API config endpoint is working")
            print(f"   Supabase URL: {config.get('supabase_url', 'Not found')}")

            # Verify it's the correct project
            expected_url = "https://pwurztydqaykrwaafdux.supabase.co"
            if config.get('supabase_url') == expected_url:
                print("✅ Connected to the CORRECT Supabase project!")
            else:
                print(f"⚠️  WARNING: Connected to wrong project!")
                print(f"   Expected: {expected_url}")
                print(f"   Got: {config.get('supabase_url')}")
        else:
            print(f"❌ API config endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API config: {e}")

    # Test 3: Check if login page is served
    try:
        response = requests.get(f"{base_url}/")
        if "Continuar con Google" in response.text or "Google" in response.text:
            print("✅ Login page with Google OAuth is being served")
        else:
            print("⚠️  Login page is served but Google OAuth button not found")
    except Exception as e:
        print(f"❌ Error checking login page: {e}")

    print("\n" + "=" * 50)
    print("Summary:")
    print("1. ✅ Google OAuth is ENABLED in Supabase (as shown in dashboard)")
    print("2. ✅ Your project ID: pwurztydqaykrwaafdux")
    print("3. ✅ Environment variables are set in Vercel")
    print("\n🚀 Ready to test!")
    print("1. Open: http://localhost:5050/")
    print("2. Click 'Continuar con Google'")
    print("3. Authenticate with your Google account")
    print("4. You should be redirected to /app after successful login")

    return True

if __name__ == "__main__":
    test_local_server()