#!/usr/bin/env python3
"""
Test OAuth flow using Playwright with Chrome browser
Tests the local environment at localhost:5050
"""

from playwright.sync_api import sync_playwright
import json
import time


def test_oauth_flow():
    """Test the OAuth configuration and flow at localhost:5050"""

    with sync_playwright() as p:
        # Launch Chrome browser in non-headless mode for visibility
        browser = p.chromium.launch(
            headless=False,
            channel="chrome"  # Use Google Chrome if installed
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 720}
        )

        page = context.new_page()

        print("🌐 Opening localhost:5050/sicetac...")
        page.goto("http://localhost:5050/sicetac")

        # Wait for the page to load
        page.wait_for_load_state("networkidle")

        # Take a screenshot of the login page
        page.screenshot(path="login_page.png")
        print("📸 Screenshot saved: login_page.png")

        # Check if we're on the login page
        title = page.title()
        print(f"📄 Page title: {title}")

        # Test config endpoint
        print("\n🔧 Testing /sicetac/api/config endpoint...")
        config_response = page.evaluate("""
            async () => {
                const response = await fetch('http://localhost:5050/sicetac/api/config');
                return await response.json();
            }
        """)

        print("✅ Config response:")
        print(json.dumps(config_response, indent=2))

        # Verify the Supabase URL is correct
        expected_url = "https://pwurztydqaykrwaafdux.supabase.co"
        actual_url = config_response.get("supabase_url", "").strip()

        if actual_url == expected_url:
            print(f"✅ Supabase URL is correct: {actual_url}")
        else:
            print(f"❌ Supabase URL mismatch!")
            print(f"   Expected: {expected_url}")
            print(f"   Actual: {actual_url}")

        # Check for Google Sign In button
        print("\n🔍 Looking for Google Sign In button...")
        try:
            # Wait for auth content to be visible
            page.wait_for_selector('#authContent', state='visible', timeout=5000)

            google_button = page.locator('#googleSignIn')
            if google_button.is_visible():
                print("✅ Google Sign In button found")

                # Click the button to test OAuth redirect
                print("\n🚀 Clicking Google Sign In button...")
                google_button.click()

                # Wait a moment for redirect
                page.wait_for_timeout(2000)

                # Check the current URL
                current_url = page.url
                print(f"📍 Current URL after click: {current_url}")

                # Take screenshot of OAuth page
                page.screenshot(path="oauth_redirect.png")
                print("📸 Screenshot saved: oauth_redirect.png")

                # Check if we're redirected to Google or see an error
                if "accounts.google.com" in current_url:
                    print("✅ Successfully redirected to Google OAuth")

                    # Check for redirect_uri in the URL
                    if "redirect_uri" in current_url:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(current_url)
                        params = urllib.parse.parse_qs(parsed.query)
                        redirect_uri = params.get('redirect_uri', [''])[0]
                        print(f"🔗 Redirect URI: {redirect_uri}")

                        if "pwurztydqaykrwaafdux.supabase.co" in redirect_uri:
                            print("✅ Correct Supabase project in redirect URI!")
                        elif "wzdhfopftxsyydjjakvi.supabase.co" in redirect_uri:
                            print("❌ Old Supabase project still in redirect URI!")
                        else:
                            print(f"⚠️ Unknown redirect URI: {redirect_uri}")
                else:
                    print(f"⚠️ Not redirected to Google, current URL: {current_url}")

            else:
                print("❌ Google Sign In button not found")
        except Exception as e:
            print(f"❌ Error finding/clicking Google button: {e}")

        # Keep browser open for manual inspection
        print("\n👀 Browser will stay open for 10 seconds for manual inspection...")
        time.sleep(10)

        browser.close()
        print("\n✅ Test completed!")


if __name__ == "__main__":
    test_oauth_flow()