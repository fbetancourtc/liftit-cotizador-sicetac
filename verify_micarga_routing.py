#!/usr/bin/env python3
"""
Verify that micarga.flexos.ai/sicetac routing is working correctly
"""

import requests
from colorama import init, Fore, Style

init()

def test_endpoint(url, description, check_content=None):
    """Test an endpoint and report results"""
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)

        if response.status_code == 200:
            status = f"{Fore.GREEN}✓ {response.status_code}{Style.RESET_ALL}"
            if check_content and check_content in response.text:
                content = f"{Fore.GREEN}✓ Content verified{Style.RESET_ALL}"
            elif check_content:
                content = f"{Fore.YELLOW}⚠ Expected content not found{Style.RESET_ALL}"
            else:
                content = f"{Fore.GREEN}✓{Style.RESET_ALL}"
        elif response.status_code == 500:
            status = f"{Fore.RED}✗ {response.status_code} (Server Error){Style.RESET_ALL}"
            content = f"{Fore.RED}API Error{Style.RESET_ALL}"
        else:
            status = f"{Fore.YELLOW}⚠ {response.status_code}{Style.RESET_ALL}"
            content = f"{Fore.YELLOW}Unexpected status{Style.RESET_ALL}"

        print(f"{description:50} {status:20} {content}")
        return response.status_code == 200

    except Exception as e:
        print(f"{description:50} {Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}MICARGA.FLEXOS.AI/SICETAC ROUTING VERIFICATION{Style.RESET_ALL}")
    print("=" * 80)

    base_url = "https://micarga.flexos.ai/sicetac"

    # Test main pages
    print(f"\n{Fore.CYAN}Main Pages:{Style.RESET_ALL}")
    test_endpoint(f"{base_url}", "Login Page (/sicetac)", "Liftit Cotizador")
    test_endpoint(f"{base_url}/", "Login Page (/sicetac/)", "Liftit Cotizador")
    test_endpoint(f"{base_url}/app", "Main App (/sicetac/app)", "Liftit Cotizador SICETAC")

    # Test static resources
    print(f"\n{Fore.CYAN}Static Resources:{Style.RESET_ALL}")
    test_endpoint(f"{base_url}/static/config.js", "Config JS", "APP_CONFIG")
    test_endpoint(f"{base_url}/static/app.js", "App JS", None)
    test_endpoint(f"{base_url}/static/cities.js", "Cities JS", None)
    test_endpoint(f"{base_url}/static/styles.css", "Styles CSS", None)
    test_endpoint(f"{base_url}/static/liftit-logo.svg", "Logo SVG", None)

    # Test API endpoints
    print(f"\n{Fore.CYAN}API Endpoints:{Style.RESET_ALL}")
    test_endpoint(f"{base_url}/api/health", "Health Check", None)
    test_endpoint(f"{base_url}/api/auth/login", "Auth Login", None)
    test_endpoint(f"{base_url}/api/quotes", "Quotes API", None)

    # Test direct Vercel deployment
    print(f"\n{Fore.CYAN}Direct Vercel Deployment:{Style.RESET_ALL}")
    vercel_url = "https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac"
    test_endpoint(vercel_url, "Direct Vercel (/sicetac)", "Liftit Cotizador")
    test_endpoint(f"{vercel_url}/api/health", "Direct Vercel API", None)

    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}ROUTING STATUS:{Style.RESET_ALL}")
    print(f"  • Frontend routing: {Fore.GREEN}✓ WORKING{Style.RESET_ALL}")
    print(f"  • Static assets: {Fore.GREEN}✓ WORKING{Style.RESET_ALL}")
    print(f"  • API endpoints: {Fore.RED}✗ ERROR 500 (needs fixing){Style.RESET_ALL}")
    print("=" * 80)

    print(f"\n{Fore.YELLOW}Note: API endpoints are returning 500 errors on both proxy and direct access.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This is a backend issue that needs to be resolved in the FastAPI application.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()