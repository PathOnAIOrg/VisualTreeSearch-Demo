import json
import os
from pathlib import Path

from browserbase import Browserbase
from playwright.sync_api import (
    sync_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)
from dotenv import load_dotenv

# Load environment variables from .env file if needed
load_dotenv()

API_KEY = os.environ.get("BROWSERBASE_API_KEY", "")
PROJECT_ID = os.environ.get("BROWSERBASE_PROJECT_ID", "")

SITE_URL = "http://128.105.145.205:7770"
SITE_LOGIN_URL = f"{SITE_URL}/customer/account/login/"
SITE_PROTECTED_URL = f"{SITE_URL}/sales/order/history"
COOKIE_FILE = "test-cookies_v3.json"

############################
# 1) Captcha/Recaptcha Logging Tools
############################

def enable_captcha_logging(page: Page):
    """
    Listen for requests/responses containing 'captcha' or 'recaptcha' in the URL.
    This helps detect if reCAPTCHA or other captcha scripts are loading.
    """
    def on_request(request):
        url_lower = request.url.lower()
        if "captcha" in url_lower or "recaptcha" in url_lower:
            print(f"[CAPTCHA-REQUEST] {request.method} -> {request.url}")

    def on_response(response):
        url_lower = response.url.lower()
        if "captcha" in url_lower or "recaptcha" in url_lower:
            print(f"[CAPTCHA-RESPONSE] {response.status} -> {response.url}")

    page.on("request", on_request)
    page.on("response", on_response)


def enable_console_logging(page: Page):
    """
    Listen for console messages that might mention 'captcha', 'recaptcha', or 'login-required'.
    Some security or captcha modules might log hidden errors.
    """
    def on_console(msg):
        text_lower = msg.text.lower()
        if "captcha" in text_lower or "recaptcha" in text_lower or "login-required" in text_lower:
            print(f"[CONSOLE] {msg.type}: {msg.text}")
    page.on("console", on_console)


############################
# 2) Helper functions
############################

def print_cookie_table_markdown(cookies: list):
    """Print cookie details in a Markdown table for debugging."""
    if not cookies:
        print("No cookies to display.")
        return

    print("| **Name** | **Value** (truncated) | **Domain** | **Path** | **HttpOnly** | **Secure** | **SameSite** | **Expires** |")
    print("|----------|------------------------|------------|----------|-------------|-----------|-------------|------------|")

    for c in cookies:
        name = c.get("name", "")
        value = c.get("value", "")
        domain = c.get("domain", "")
        path = c.get("path", "")
        http_only = c.get("httpOnly", False)
        secure = c.get("secure", False)
        same_site = c.get("sameSite", "")
        expires = c.get("expires", "")
        truncated_value = (value[:10] + "...") if len(value) > 10 else value

        print(f"| {name} | {truncated_value} | {domain} | {path} | {http_only} | {secure} | {same_site} | {expires} |")


def store_cookies(page: Page):
    """Store all cookies for SITE_URL to disk and print them in a table."""
    cookies = page.context.cookies(SITE_URL)
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"Saved {len(cookies)} cookie(s) to {COOKIE_FILE}.\n")
    print("#### Stored Cookies (Markdown Table)\n")
    print_cookie_table_markdown(cookies)
    print()


############################
# 3) Main Login Flow
############################

def authenticate(page: Page):
    """Perform a fresh login attempt, ignoring prior cookies."""
    print("Starting authenticate() – clearing cookies, then going to the login page.")
    page.context.clear_cookies()

    # Go to login page
    page.goto(SITE_LOGIN_URL)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="step1_login_page.png")

    print(f"Current URL: {page.url}")
    print("Filling username/password...")

    try:
        page.fill("#email", "emma.lopez@gmail.com")
        page.fill("#pass", "Password.123")
        print("Filled the login form fields.")
    except Exception as e:
        print(f"⚠️ Could not fill login form: {e}")

    # Attempt to click login button and wait for navigation
    login_button_selector = (
        ".action.login.primary, #send2, form#login-form button[type='submit']"
    )
    button_found = page.query_selector(login_button_selector)
    if button_found:
        try:
            with page.expect_navigation(wait_until="networkidle", timeout=15000):
                page.click(login_button_selector)
            page.screenshot(path="step2_after_click.png")
            print("Clicked login button and waited for navigation.\n")
        except PlaywrightTimeoutError:
            print("❌ Timed out waiting for navigation after click.")
        except Exception as e:
            print(f"❌ Unexpected error clicking login: {e}")
    else:
        print("⚠️ No login button found with the known selectors.")

    # Print final cookies
    print("Cookies right after login attempt:")
    store_cookies(page)

    # Check final URL / title
    final_url = page.url
    final_title = page.title()
    print(f"After login attempt => URL: {final_url} | Title: {final_title}")
    page.screenshot(path="step3_after_login.png")

    # If it still looks like a login page, we probably failed
    if "login" in final_url.lower() or "customer login" in final_title.lower():
        snippet = page.content()[:500].replace("\n", " ")
        print(f"❌ Looks like we're still on a login page. HTML snippet:\n{snippet}...")
        return False

    print("✅ Possibly logged in – not on the login page anymore.")
    return True


def run_flow(page: Page):
    """
    Main flow:
    1) Attach captcha logging for requests + console
    2) Attempt login
    3) Visit the protected page
    4) Check final result
    """
    # Attach extra logging for captcha or recaptcha references
    enable_captcha_logging(page)
    enable_console_logging(page)

    print("Performing login with authenticate() ...\n")
    success = authenticate(page)
    if not success:
        print("Login attempt didn't look successful, but continuing anyway...\n")

    # Then go to protected page
    print(f"Visiting protected URL: {SITE_PROTECTED_URL} ...")
    page.goto(SITE_PROTECTED_URL)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="step4_protected_page.png")

    final_url = page.url
    final_title = page.title()
    print(f"Protected page => URL: {final_url} | Title: {final_title}")

    # If still on the login page or "Customer Login", session didn't stick
    if "login" in final_url.lower() or "customer login" in final_title.lower():
        print("❌ We are still on the login page – session not recognized.")
    else:
        print("✅ Accessed the protected page – login session seems to have stuck.")


############################
# 4) Script Entry
############################

def main():
    with sync_playwright() as p:
        bb = Browserbase(api_key=API_KEY)
        # Create a Browserbase session
        session = bb.sessions.create(
            project_id=PROJECT_ID, 
            proxies=False,
            # Optional: Browser/automation settings
            browser_settings={
                "fingerprint": {
                    "browsers": ["chrome", "firefox", "edge", "safari"],
                    "devices": ["mobile", "desktop"],
                    "locales": ["en-US"],
                    "operatingSystems": ["linux", "macos", "windows"],
                    "screen": {
                        "maxHeight": 1080,
                        "maxWidth": 1920,
                        "minHeight": 1080,
                        "minWidth": 1920,
                    },
                    "viewport": {
                        "width": 1920,
                        "height": 1080,
                    },
                },
                # Tells Browserbase to attempt solving captchas (if your plan allows it)
                "solveCaptchas": True,
            },
        )

        browser = p.chromium.connect_over_cdp(session.connectUrl)

        print(f"Connected to Browserbase. {browser.browser_type.name} v{browser.version}")

        # Grab default context/page
        context = browser.contexts[0]
        page = context.pages[0]

        # Print live debugger links
        debug_info = bb.sessions.debug(session.id)
        print("Live view URL (fullscreen):", debug_info.debugger_fullscreen_url)
        print("Live view URL (with browser UI):", debug_info.debugger_url)

        try:
            run_flow(page)
        finally:
            page.close()
            browser.close()


if __name__ == "__main__":
    main()
