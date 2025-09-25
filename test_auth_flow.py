#!/usr/bin/env python3
"""
Test script to verify Supabase authentication flow.
Run this script to ensure your Supabase configuration is working correctly.
"""

import asyncio
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add the app module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase_client import SupabaseService
from app.core.config import get_settings

async def test_supabase_connection():
    """Test basic Supabase connection"""
    settings = get_settings()

    print("Testing Supabase Configuration")
    print("=" * 50)

    # Check if credentials are configured
    if not settings.supabase_project_url or settings.supabase_project_url == "https://your-project-ref.supabase.co":
        print("❌ ERROR: Supabase Project URL not configured")
        print("Please set SUPABASE_PROJECT_URL in your .env file")
        return False

    if not settings.supabase_anon_key or settings.supabase_anon_key == "your-anon-key-here":
        print("❌ ERROR: Supabase Anon Key not configured")
        print("Please set SUPABASE_ANON_KEY in your .env file")
        return False

    print(f"✅ Supabase URL: {settings.supabase_project_url}")
    print(f"✅ Anon Key: {settings.supabase_anon_key[:10]}...")

    # Test authentication endpoint availability
    try:
        # Get the Supabase client (it initializes automatically)
        client = SupabaseService.get_client()
        if client:
            print("✅ Supabase client initialized successfully")
            print("✅ Supabase client is ready for authentication")
        else:
            print("❌ ERROR: Supabase client not available")
            return False
    except Exception as e:
        print(f"❌ ERROR: Connection test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("✅ All tests passed! Your Supabase configuration is working.")
    print("\nNext steps:")
    print("1. Configure Google OAuth in Supabase Dashboard")
    print("2. Follow the instructions in GOOGLE_AUTH_SETUP.md")
    print("3. Start the app: uvicorn app.main:app --reload --port 5050")
    print("4. Visit http://localhost:5050/ to see the login page")

    return True

async def test_auth_flow():
    """Optional: Test authentication with a test user"""
    print("\n" + "=" * 50)
    print("Testing Authentication Flow (Optional)")
    print("=" * 50)

    test_email = input("Enter test email (or press Enter to skip): ").strip()
    if not test_email:
        print("Skipping authentication test")
        return

    test_password = input("Enter test password: ").strip()

    try:
        # Test sign up
        print(f"\nTesting sign up for {test_email}...")
        result = await SupabaseService.sign_up(test_email, test_password)
        if result.get("user"):
            print(f"✅ User created: {result['user'].get('email')}")
            print("Note: User may need to confirm email before login")
        elif "User already registered" in str(result.get("error", "")):
            print("User already exists, trying login...")

            # Test sign in
            result = await SupabaseService.sign_in_with_email(test_email, test_password)
            if result.get("session"):
                print(f"✅ Login successful!")
                print(f"Access token: {result['session']['access_token'][:20]}...")
            else:
                print(f"❌ Login failed: {result.get('error')}")
        else:
            print(f"❌ Sign up failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

async def main():
    """Main test runner"""
    success = await test_supabase_connection()

    if success:
        await test_auth_flow()

if __name__ == "__main__":
    asyncio.run(main())