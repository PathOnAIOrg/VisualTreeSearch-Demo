import json
import os
from browserbase import Browserbase
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]

SITE_URL = "http://128.105.145.205:7770"
SITE_LOGIN_URL = "http://128.105.145.205:7770/customer/account/login/"
SITE_PROTECTED_URL = "http://128.105.145.205:7770/sales/order/history"

# This would typically be stored in some other durable storage or even kept in
# memory. Here, we're just going to serialize them to disk using json dump/load.
# Ensure these are well secured as anyone with this information can log in!
COOKIE_FILE = "test-cookies.json"


def print_cookie_table_markdown(cookies: list):
    """
    Print cookie details in a Markdown table for easier debugging.
    Shows name, domain, path, value snippet, httpOnly, secure, sameSite, expires.
    """
    if not cookies:
        print("No cookies to display.")
        return

    # Print the header
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
        # Truncate the value in the table for readability
        value_snippet = value[:10] + "..." if len(value) > 10 else value

        print(f"| {name} | {value_snippet} | {domain} | {path} | {http_only} | {secure} | {same_site} | {expires} |")


def store_cookies(browser_tab: Page):
    """Retrieve all the cookies for SITE_URL and store them to a file, then print them in markdown."""
    all_cookies = browser_tab.context.cookies(SITE_URL)
    with open(COOKIE_FILE, "w") as cookie_file:
        json.dump(all_cookies, cookie_file, indent=4)

    print(f"Saved {len(all_cookies)} cookie(s) from the browser context")
    print("\n### Cookies Just Stored (Markdown Table)\n")
    print_cookie_table_markdown(all_cookies)
    print()  # extra newline


def restore_cookies(browser_tab: Page):
    """Load cookies from our local file into the current browser context, if present."""
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
    """Authenticate to Magento using Playwright form submission, then show a detailed cookie table."""
    print("Attempting login with Playwright form submission")
    username = "emma.lopez@gmail.com"
    password = "Password.123"
    
    # Start fresh without cookies
    browser_tab.context.clear_cookies()
    print("Cleared cookies before login.\n")

    # Optional: set a test cookie
    browser_tab.context.add_cookies([{
        "name": "test_cookie",
        "value": "1",
        "domain": "128.105.145.205",
        "path": "/",
    }])
    
    # Navigate to login page
    browser_tab.goto(SITE_LOGIN_URL)
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_login_page.png")
    
    print("Current URL:", browser_tab.url)
    print("Filling in login form...\n")
    
    # Fill the username
    email_field = browser_tab.query_selector("#email")
    if email_field:
        email_field.fill(username)
        print("Filled email field")
    else:
        print("⚠️ Could not find email field")
    
    # Fill the password
    password_field = browser_tab.query_selector("#pass")
    if password_field:
        password_field.fill(password)
        print("Filled password field")
    else:
        print("⚠️ Could not find password field")
    
    print("Examining form elements...\n")
    form_elements = browser_tab.query_selector_all("form.form-login input, form#login-form input")
    for element in form_elements:
        name = element.get_attribute("name")
        value = element.get_attribute("value")
        input_type = element.get_attribute("type")
        if name:
            print(f"  Form input: {name} = {value if value else '[empty]'} (type: {input_type})")
    
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
        except Exception as e:
            print(f"Navigation timeout or error after clicking login: {e}")
            browser_tab.screenshot(path="screenshot_after_error.png")
    else:
        print("⚠️ Could not find login button!")
    
    # Save the cookies regardless of success
    store_cookies(browser_tab)
    
    # Check if login succeeded
    print("Checking if login succeeded...\n")
    
    cookies = browser_tab.context.cookies()
    print(f"Cookies after login attempt ({len(cookies)}) (Markdown Table):\n")
    print_cookie_table_markdown(cookies)
    print()

    # Check for Magento 2's typical session cookie (PHPSESSID) or Magento 1's (frontend)
    magento_session_cookies = [c for c in cookies if c["name"] in ("frontend", "frontend_cid", "PHPSESSID")]
    if magento_session_cookies:
        print(f"✅ Found {len(magento_session_cookies)} potential Magento session cookie(s): {', '.join(c['name'] for c in magento_session_cookies)}")
    else:
        print("❌ No Magento 'frontend' or 'PHPSESSID' cookie found - likely not authenticated.\n")
    
    # Navigate to account page to confirm
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_after_login.png")
    
    # Check if we're truly logged in by searching for My Account or a welcome message
    is_logged_in = False
    
    welcome_msg = browser_tab.query_selector(".box-information .box-content p") or browser_tab.query_selector(".welcome-msg")
    if welcome_msg and "Emma" in welcome_msg.text_content():
        is_logged_in = True
        print(f"✅ Found welcome message containing 'Emma': {welcome_msg.text_content().strip()}")
    
    page_title = browser_tab.title()
    if "My Account" in page_title and "Login" not in page_title:
        is_logged_in = True
        print(f"✅ Page title indicates logged in: {page_title}")
    
    if is_logged_in:
        print("✅ Successfully logged in!\n")
        return True
    else:
        print(f"❌ Login verification failed. Current page: {browser_tab.url} | Title: {browser_tab.title()}\n")
        # Print partial page content
        content_snippet = browser_tab.content()[:500].replace("\n", " ")
        print(f"Page content snippet:\n{content_snippet}...\n")
        return False


def check_login_status(browser_tab: Page) -> bool:
    """Check if we're on the customer account page rather than the login page."""
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")

    title = browser_tab.title()
    if "Login" in title:
        print("User is not logged in (title contains 'Login')")
        return False
    else:
        print("User is already logged in (account page). Title:", title)
        return True


def run(browser_tab: Page):
    """Main flow: restore cookies, check if logged in, if not, try authenticate, then visit the protected page."""
    cookies_restored = restore_cookies(browser_tab)

    if cookies_restored and check_login_status(browser_tab):
        print("Using existing session cookies\n")
    else:
        print("Need to authenticate\n")
        success = authenticate(browser_tab)
        if not success:
            print("❌ Authentication didn't succeed fully.\n")

    # Attempt accessing the protected URL
    print(f"Accessing protected URL: {SITE_PROTECTED_URL}")
    browser_tab.goto(SITE_PROTECTED_URL)
    browser_tab.wait_for_load_state("networkidle")
    print(f"Final page: {browser_tab.url} | Title: {browser_tab.title()}")
    
    # Check if we're stuck at login
    if "Login" in browser_tab.title():
        print("❌ Failed to access protected page - still seeing login page")
        browser_tab.screenshot(path="screenshot_final_fail.png")
    else:
        print("✅ Successfully accessing protected page!")
        browser_tab.screenshot(path="screenshot_final_success.png")


def main():
    with sync_playwright() as playwright:
        bb = Browserbase(api_key=API_KEY)
        #session = bb.sessions.create(project_id=os.environ["BROWSERBASE_PROJECT_ID"], proxies=False)
        session = bb.sessions.create(
            project_id=os.environ["BROWSERBASE_PROJECT_ID"],
            browser_settings={
                "fingerprint": {
                    "browsers": ["chrome", "firefox", "edge", "safari"],
                    "devices": ["mobile", "desktop"],
                    "locales": ["en-US", "en-GB"],
                    "operatingSystems": ["android", "ios", "linux", "macos", "windows"],
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
                "solveCaptchas": True,
            },
            proxies=False,
        )
        browser = playwright.chromium.connect_over_cdp(session.connectUrl)

        print(
            "Connected to Browserbase.",
            f"{browser.browser_type.name} version {browser.version}",
        )

        context = browser.contexts[0]
        browser_tab = context.pages[0]
        # Retrieve live view URLs
        live_info = bb.sessions.debug(session.id)
        print("Live view URL (fullscreen):", live_info.debugger_fullscreen_url)
        print("Live view URL (with browser UI):", live_info.debugger_url)

        try:
            run(browser_tab)
        finally:
            # Clean up
            browser_tab.close()
            browser.close()


if __name__ == "__main__":
    main()
