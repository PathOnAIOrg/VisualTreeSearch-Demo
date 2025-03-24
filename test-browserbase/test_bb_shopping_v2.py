import json
import os
from browserbase import Browserbase
from playwright.sync_api import (
    sync_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

SITE_URL = "http://128.105.145.205:7770"
SITE_LOGIN_URL = f"{SITE_URL}/customer/account/login/"
SITE_PROTECTED_URL = f"{SITE_URL}/sales/order/history"
COOKIE_FILE = "test-cookies.json"

def print_cookie_table_markdown(cookies: list):
    if not cookies:
        print("No cookies to display.")
        return

    print("| **Name** | **Value (first 10 chars)** | **Domain**          | **Path** | **HttpOnly** | **Secure** | **SameSite** | **Expires** |")
    print("|----------|----------------------------|---------------------|----------|-------------|-----------|-------------|------------|")
    for c in cookies:
        name = c.get("name", "")
        value = c.get("value", "")
        domain = c.get("domain", "")
        path = c.get("path", "")
        http_only = str(c.get("httpOnly", False))
        secure = str(c.get("secure", False))
        same_site = c.get("sameSite", "")
        expires = c.get("expires", "")
        value_snippet = value[:10] + "..." if len(value) > 10 else value

        print(f"| {name} | {value_snippet} | {domain} | {path} | {http_only} | {secure} | {same_site} | {expires} |")

def store_cookies(browser_tab: Page):
    all_cookies = browser_tab.context.cookies(SITE_URL)
    with open(COOKIE_FILE, "w") as cookie_file:
        json.dump(all_cookies, cookie_file, indent=4)

    print(f"Saved {len(all_cookies)} cookie(s) from the browser context")
    print("\n### Cookies Just Stored (Markdown Table)\n")
    print_cookie_table_markdown(all_cookies)
    print()

def restore_cookies(browser_tab: Page):
    try:
        with open(COOKIE_FILE) as cookie_file:
            cookies = json.load(cookie_file)
    except FileNotFoundError:
        print("No cookie file found. Will need to authenticate.")
        return False

    browser_tab.context.add_cookies(cookies)
    print(f"Restored {len(cookies)} cookie(s) to the browser context")
    print("\n### Cookies Just Restored (Markdown Table)\n")
    print_cookie_table_markdown(cookies)
    print()
    return True

def authenticate(browser_tab: Page):
    print("Attempting login with Playwright form submission.\n")

    username = "emma.lopez@gmail.com"
    password = "Password.123"

    # Clear existing cookies
    browser_tab.context.clear_cookies()
    print("Cleared cookies before login.\n")

    # (Optional) Set a test cookie
    browser_tab.context.add_cookies([{
        "name": "test_cookie",
        "value": "1",
        "domain": "128.105.145.205",
        "path": "/",
    }])

    # Slow down steps for better visibility
    browser_tab.wait_for_timeout(1000)

    # Navigate to the login page
    browser_tab.goto(SITE_LOGIN_URL)
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.wait_for_timeout(1000)
    browser_tab.screenshot(path="screenshot_login_page.png")
    
    print(f"Current URL: {browser_tab.url}")
    print("Filling in login form...\n")
    # Pause to debug in DevTools if needed:
    # browser_tab.pause()

    # Fill fields
    if browser_tab.query_selector("#email"):
        browser_tab.fill("#email", username)
        print("Filled email field.")
    else:
        print("⚠️ Could not find email field!")

    if browser_tab.query_selector("#pass"):
        browser_tab.fill("#pass", password)
        print("Filled password field.")
    else:
        print("⚠️ Could not find password field!")

    # Slight pause
    browser_tab.wait_for_timeout(1000)
    
    print("Examining form elements...\n")
    form_elements = browser_tab.query_selector_all("form.form-login input, form#login-form input")
    for element in form_elements:
        name = element.get_attribute("name")
        value = element.get_attribute("value")
        input_type = element.get_attribute("type")
        if name:
            print(f"  Form input: {name} = {value or '[empty]'} (type: {input_type})")

    print("\nClicking login button...")

    login_button = (
        browser_tab.query_selector(".action.login.primary") or
        browser_tab.query_selector("#send2") or
        browser_tab.query_selector("button[type='submit']")
    )

    if login_button:
        print(f"Found login button: id={login_button.get_attribute('id')} type={login_button.get_attribute('type')}")
        try:
            with browser_tab.expect_navigation(wait_until="networkidle", timeout=15000):
                login_button.click()
            browser_tab.screenshot(path="screenshot_after_click.png")
            print("Clicked login button and waited for navigation.\n")
        except PlaywrightTimeoutError:
            print("❌ Timed out waiting for navigation after clicking login.")
        except Exception as e:
            print(f"❌ Navigation error: {e}")
    else:
        print("⚠️ Could not find login button!")

    # Save cookies after form submission
    store_cookies(browser_tab)

    # Check if login succeeded
    print("Checking if login succeeded...\n")

    cookies = browser_tab.context.cookies()
    print(f"Cookies after login attempt ({len(cookies)}):\n")
    print_cookie_table_markdown(cookies)
    print()

    # Look for Magento 2 or Magento 1 session cookies
    magento_session_cookies = [c for c in cookies if c["name"] in ("frontend", "frontend_cid", "PHPSESSID")]
    if magento_session_cookies:
        print(f"✅ Potential Magento session cookie(s): {[c['name'] for c in magento_session_cookies]}")
    else:
        print("❌ No 'frontend' or 'PHPSESSID' cookie found - likely not authenticated.\n")

    # Navigate to account page to double-check
    browser_tab.goto(f"{SITE_URL}/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_after_login.png")

    page_title = browser_tab.title()
    print(f"Account Page Title: {page_title}")

    is_logged_in = False
    if "Login" not in page_title and "customer/account/login" not in browser_tab.url:
        # Possibly logged in, let's see if there's a welcome or "My Account"
        print("Not seeing 'Login' in the title or URL. Checking for additional clues...")
        welcome_msg = browser_tab.query_selector(".box-information .box-content p") or browser_tab.query_selector(".welcome-msg")
        if welcome_msg and "Emma" in welcome_msg.text_content():
            is_logged_in = True
            print(f"✅ Found welcome message with 'Emma': {welcome_msg.text_content().strip()}")

        if "My Account" in page_title:
            is_logged_in = True
            print(f"✅ Page title suggests logged in: {page_title}")
    else:
        print("❌ Looks like we're still on a login page or not recognized. URL:", browser_tab.url)

    if is_logged_in:
        print("✅ Successfully logged in!\n")
        return True
    else:
        print("❌ Login verification failed at account page check.\n")
        snippet = browser_tab.content()[:500].replace("\n", " ")
        print(f"Page content snippet:\n{snippet}...\n")
        return False

def log_request(request):
    print(f"-> [Request] {request.method} {request.url}")

def log_response(response):
    print(f"<- [Response] {response.status} {response.url}")

def run(browser_tab: Page):
    """
    Main test flow:
     1) Log all network requests/responses.
     2) Optionally restore cookies and check if we're logged in.
     3) Otherwise, authenticate.
     4) Then goto /sales/order/history to see if we remain logged in.
    """
    # 1) Attach logging for requests/responses
    browser_tab.on("request", log_request)
    browser_tab.on("response", log_response)

    # 2) Try restoring
    cookies_restored = restore_cookies(browser_tab)
    if cookies_restored:
        # See if we are already logged in
        browser_tab.goto(f"{SITE_URL}/customer/account/")
        browser_tab.wait_for_load_state("networkidle")
        if "Login" in browser_tab.title():
            print("Not logged in (restored cookies didn't work).")
        else:
            print("Already logged in from restored cookies. Title:", browser_tab.title())

    # 3) If not logged in, do authenticate
    if "Login" in browser_tab.title():
        print("\nProceeding with authentication.\n")
        success = authenticate(browser_tab)
        if not success:
            print("❌ Authentication didn't succeed fully, continuing anyway.\n")

    # 4) Attempt accessing the protected URL
    print(f"Accessing protected URL: {SITE_PROTECTED_URL}")
    browser_tab.goto(SITE_PROTECTED_URL)
    browser_tab.wait_for_load_state("networkidle")
    print(f"Final page: {browser_tab.url}\nTitle: {browser_tab.title()}")
    browser_tab.screenshot(path="screenshot_final.png")

    if "login" in browser_tab.url or "Login" in browser_tab.title():
        print("❌ We appear to still be on a login page. Authentication didn't stick.")
    else:
        print("✅ Successfully accessed protected page without redirect to login. Possibly logged in.")

def main():
    with sync_playwright() as pw:
        bb = Browserbase(api_key=API_KEY)
        session = bb.sessions.create(project_id=PROJECT_ID, proxies=False)
        browser = pw.chromium.connect_over_cdp(session.connectUrl)
        
        print(
            "Connected to Browserbase.",
            f"{browser.browser_type.name} version {browser.version}"
        )
        
        context = browser.contexts[0]
        page = context.pages[0]
        
        live_info = bb.sessions.debug(session.id)
        print("Live view URL (fullscreen):", live_info.debugger_fullscreen_url)
        print("Live view URL (with browser UI):", live_info.debugger_url)

        try:
            run(page)
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    main()
