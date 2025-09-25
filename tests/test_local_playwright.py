from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Error as PlaywrightError

BASE_URL = "http://127.0.0.1:5050"


@contextmanager
def _launch_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            browser.close()


def test_login_page_loads():
    """Ensure the local login page renders key elements without crashing."""
    with _launch_browser() as browser:
        page = browser.new_page()
        response = page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=15000)
        assert response and response.ok, "Expected 200 OK when loading the login page"

        # Wait for the Google sign-in button to become interactable once config loads.
        page.wait_for_selector("#googleSignIn:not([disabled])", timeout=15000)

        assert "Login - Liftit Cotizador SICETAC" in page.title()
        assert "Continuar con Google" in page.inner_text("#googleSignIn")

        # Fetch the runtime config exposed via the API to ensure Supabase settings resolve.
        api_response = page.request.get(f"{BASE_URL}/sicetac/api/config")
        config = api_response.json()
        assert config["supabase_url"].endswith("supabase.co")
        assert config["supabase_anon_key"].startswith("eyJ")


def test_app_page_accessible():
    """The main app shell should return HTML even without authentication."""
    with _launch_browser() as browser:
        page = browser.new_page()
        response = page.goto(f"{BASE_URL}/app", wait_until="domcontentloaded", timeout=15000)
        assert response and response.status == 200
        assert "Cotizador" in page.content()


def main() -> None:
    try:
        test_login_page_loads()
        test_app_page_accessible()
    except AssertionError as exc:
        print(f"❌ Assertion failed: {exc}")
        raise SystemExit(1) from exc
    except PlaywrightError as exc:
        print(f"❌ Playwright error: {exc}")
        raise SystemExit(2) from exc
    else:
        print("✅ Local Playwright checks passed")


if __name__ == "__main__":
    main()
