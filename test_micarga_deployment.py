#!/usr/bin/env python3
"""
Test script for micarga.flexos.ai/sicetac deployment using Playwright
"""

from playwright.sync_api import sync_playwright
import sys
import time

def test_micarga_deployment():
    """Test the deployment at micarga.flexos.ai/sicetac"""

    print("🧪 Testing micarga.flexos.ai/sicetac deployment with Playwright...")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to False to see the browser
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True  # In case of SSL issues
        )
        page = context.new_page()

        # Test 1: Try to access micarga.flexos.ai/sicetac
        print("\n1. Testing micarga.flexos.ai/sicetac...")
        try:
            response = page.goto('https://micarga.flexos.ai/sicetac',
                               wait_until='domcontentloaded',
                               timeout=10000)

            if response:
                status = response.status
                print(f"   Status: {status}")

                if status == 200:
                    print("   ✅ Page loaded successfully!")

                    # Take screenshot
                    page.screenshot(path='micarga_sicetac_page.png')
                    print("   📸 Screenshot saved as 'micarga_sicetac_page.png'")

                    # Check page title
                    title = page.title()
                    print(f"   📄 Page title: {title}")

                    # Check for key elements
                    print("\n2. Checking for key elements...")

                    # Check for login form elements
                    elements_to_check = [
                        ('h1', 'Main heading'),
                        ('#quoteForm', 'Quote form'),
                        ('#loginModal', 'Login modal'),
                        ('button[type="submit"]', 'Submit button'),
                        ('.container', 'Container element')
                    ]

                    for selector, description in elements_to_check:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                print(f"   ✅ Found: {description}")
                            else:
                                print(f"   ❌ Missing: {description}")
                        except:
                            print(f"   ❌ Error checking: {description}")

                    # Check for any error messages
                    error_elements = page.query_selector_all('.error, .alert-error')
                    if error_elements:
                        print(f"\n   ⚠️ Found {len(error_elements)} error messages on page")

                elif status == 404:
                    print("   ❌ Page not found (404) - Domain routing not configured")
                elif status == 301 or status == 302:
                    location = response.headers.get('location', 'unknown')
                    print(f"   ↪️ Redirect detected to: {location}")
                else:
                    print(f"   ⚠️ Unexpected status code: {status}")
            else:
                print("   ❌ No response received")

        except Exception as e:
            print(f"   ❌ Error accessing micarga.flexos.ai/sicetac: {str(e)}")
            print("   This likely means the domain is not configured or not pointing to Vercel")

        # Test 2: Try the Vercel URL for comparison
        print("\n3. Testing Vercel deployment URL for comparison...")
        try:
            vercel_url = "https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac"
            response = page.goto(vercel_url,
                               wait_until='domcontentloaded',
                               timeout=10000)

            if response and response.status == 200:
                print(f"   ✅ Vercel URL works: {vercel_url}")
                page.screenshot(path='vercel_deployment.png')
                print("   📸 Screenshot saved as 'vercel_deployment.png'")
            else:
                print(f"   ❌ Vercel URL status: {response.status if response else 'No response'}")

        except Exception as e:
            print(f"   ❌ Error accessing Vercel URL: {str(e)}")

        # Keep browser open for a moment to review
        print("\n4. Browser will close in 5 seconds...")
        time.sleep(5)

        browser.close()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nSummary:")
    print("- If micarga.flexos.ai/sicetac works: Domain is configured correctly")
    print("- If only Vercel URL works: Need to configure custom domain in Vercel")
    print("- Check screenshots for visual verification")

if __name__ == "__main__":
    test_micarga_deployment()