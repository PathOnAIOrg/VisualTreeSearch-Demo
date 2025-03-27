import os
import asyncio
import json
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv
from browserbase import Browserbase
import aiohttp

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

SITE_URL = "http://128.105.145.205:7770"
SITE_LOGIN_URL = f"{SITE_URL}/customer/account/login/"

async def debug_browser_state(browser):
    """
    Print detailed information about browser contexts and their pages.
    """
    print("\n=== Browser State Debug ===")
    
    # List all contexts
    contexts = browser.contexts
    print(f"\nTotal contexts: {len(contexts)}")
    
    for i, context in enumerate(contexts):
        print(f"\nContext {i}:")
        pages = context.pages
        print(f"- Number of pages: {len(pages)}")
        
        for j, page in enumerate(pages):
            print(f"  - Page {j}: {page.url}")
        
    print("\n========================")

# TODO: change to use the page that corresponds to active tab
async def get_non_extension_context_and_page(browser):
    """
    Get the first context and page that don't belong to a Chrome extension.
    
    Args:
        browser: Playwright browser instance
    Returns:
        tuple: (context, page) or (None, None) if not found
    """
    for context in browser.contexts:
        for page in context.pages:
            if not page.url.startswith("chrome-extension://"):
                return context, page
    return None, None

async def create_session() -> str:
    """
    Create a Browserbase session - a single browser instance.

    :returns: The new session's ID.
    """
    sessions_url = "https://www.browserbase.com/v1/sessions"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    json = {"projectId": PROJECT_ID}

    async with aiohttp.ClientSession() as session:
        async with session.post(sessions_url, json=json, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["id"]




async def store_cookies(browser_tab: Page, cookie_file_path: str):
    """Retrieve all the cookies for SITE_URL and store them to a file, then print them in markdown."""
    all_cookies = await browser_tab.context.cookies(SITE_URL)
    with open(cookie_file_path, "w") as cookie_file:
        json.dump(all_cookies, cookie_file, indent=4)

    print(f"Saved {len(all_cookies)} cookie(s) from the browser context")


async def restore_cookies(browser_tab: Page, cookie_file_path: str):
    """Load cookies from our local file into the current browser context, if present."""
    try:
        with open(cookie_file_path) as cookie_file:
            cookies = json.load(cookie_file)
    except FileNotFoundError:
        print("No cookie file found. Will need to authenticate.")
        return False

    await browser_tab.context.add_cookies(cookies)
    print(f"Restored {len(cookies)} cookie(s) to the browser context")
    return True


async def authenticate(browser_tab: Page, cookie_file_path: str):
    """Authenticate to Magento using Playwright form submission, then show a detailed cookie table."""
    print("Attempting login with Playwright form submission")
    username = "emma.lopez@gmail.com"
    password = "Password.123"

    # Start fresh without cookies
    await browser_tab.context.clear_cookies()
    print("Cleared cookies before login.\n")

    # Optional: set a test cookie
    await browser_tab.context.add_cookies([{
        "name": "test_cookie",
        "value": "1",
        "domain": "128.105.145.205",
        "path": "/",
    }])

    # Navigate to login page
    await browser_tab.goto(SITE_LOGIN_URL)
    await browser_tab.wait_for_load_state("networkidle")

    print("Current URL:", browser_tab.url)
    print("Filling in login form...\n")

    # Fill the username
    email_field = await browser_tab.query_selector("#email")
    if email_field:
        await email_field.fill(username)
        print("Filled email field")
    else:
        print("⚠️ Could not find email field")

    # Fill the password
    password_field = await browser_tab.query_selector("#pass")
    if password_field:
        await password_field.fill(password)
        print("Filled password field")
    else:
        print("⚠️ Could not find password field")

    print("Examining form elements...\n")
    form_elements = await browser_tab.query_selector_all("form.form-login input, form#login-form input")
    for element in form_elements:
        name = await element.get_attribute("name")
        value = await element.get_attribute("value")
        input_type = await element.get_attribute("type")
        if name:
            print(f"  Form input: {name} = {value if value else '[empty]'} (type: {input_type})")

    print("\nClicking login button...")
    login_button = (
        await browser_tab.query_selector(".action.login.primary")
        or await browser_tab.query_selector("#send2")
        or await browser_tab.query_selector("button[type='submit']")
    )

    if login_button:
        print(f"Found login button: id={await login_button.get_attribute('id')} type={await login_button.get_attribute('type')}")
        try:
            async with browser_tab.expect_navigation(wait_until="networkidle", timeout=15000):
                await login_button.click()
            print("Clicked login button and waited for navigation.\n")
        except Exception as e:
            print(f"Navigation timeout or error after clicking login: {e}")
    else:
        print("⚠️ Could not find login button!")

    # Save the cookies regardless of success
    await store_cookies(browser_tab, cookie_file_path)

    # Check if login succeeded
    print("Checking if login succeeded...\n")

    cookies = await browser_tab.context.cookies()
    print(f"Cookies after login attempt ({len(cookies)}) (Markdown Table):\n")
    print()

    # Check for Magento 2's typical session cookie (PHPSESSID) or Magento 1's (frontend)
    magento_session_cookies = [c for c in cookies if c["name"] in ("frontend", "frontend_cid", "PHPSESSID")]
    if magento_session_cookies:
        print(f"✅ Found {len(magento_session_cookies)} potential Magento session cookie(s): {', '.join(c['name'] for c in magento_session_cookies)}")
    else:
        print("❌ No Magento 'frontend' or 'PHPSESSID' cookie found - likely not authenticated.\n")

    # Navigate to account page to confirm
    await browser_tab.goto(f"{SITE_URL}/customer/account/")
    await browser_tab.wait_for_load_state("networkidle")

    # Check if we're truly logged in by searching for My Account or a welcome message
    is_logged_in = False
    welcome_msg = await browser_tab.query_selector(".box-information .box-content p") or await browser_tab.query_selector(".welcome-msg")
    if welcome_msg:
        welcome_text = await welcome_msg.text_content()
        if "Emma" in welcome_text:
            is_logged_in = True
            print(f"✅ Found welcome message containing 'Emma': {welcome_text.strip()}")

    page_title = await browser_tab.title()
    if "My Account" in page_title and "Login" not in page_title:
        is_logged_in = True
        print(f"✅ Page title indicates logged in: {page_title}")

    if is_logged_in:
        print("✅ Successfully logged in!\n")
        return True
    else:
        current_title = await browser_tab.title()
        print(f"❌ Login verification failed. Current page: {browser_tab.url} | Title: {current_title}\n")
        content = await browser_tab.content()
        snippet = content[:500].replace("\n", " ")
        print(f"Page content snippet:\n{snippet}...\n")
        return False

async def check_login_status(browser_tab: Page) -> bool:
    """Check if we're on the customer account page rather than the login page."""
    await browser_tab.goto(f"{SITE_URL}/customer/account/")
    await browser_tab.wait_for_load_state("networkidle")

    title = await browser_tab.title()
    if "Login" in title:
        print("User is not logged in (title contains 'Login')")
        return False
    else:
        print("User is already logged in (account page). Title:", title)
        return True

class AsyncPlaywrightManager:
    def __init__(self, storage_state=None, headless=False, mode="chromium", session_id=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.lock = asyncio.Lock()
        self.headless = headless
        self.mode = mode
        self.session_id = session_id
        self.live_browser_url = None
        self.credentials = None
        self.bb = None if mode != "browserbase" else Browserbase(api_key=API_KEY)


    async def initialize(self):
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                
                if self.mode == "browserbase":
                    # Create or use existing Browserbase session
                    session = self.bb.sessions.create(
                        project_id=PROJECT_ID,
                        proxies=False,
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
                            "solveCaptchas": True,
                        },
                    )
                    self.session_id = session.id
                    self.browser = await self.playwright.chromium.connect_over_cdp(session.connectUrl)
                
                    print(f"Connected to Browserbase. {self.browser.browser_type.name} v{self.browser.version}")
                    await debug_browser_state(self.browser)
                    
                    # Use the common setup method
                    # First try to restore cookies
                    self.context = self.browser.contexts[0]
                    self.page = self.context.pages[0]
                    cookies_restored = await restore_cookies(self.page, self.storage_state)
                    
                    if cookies_restored and await check_login_status(self.page):
                        print("Using existing session cookies\n")
                    else:
                        print("Need to authenticate\n")
                        # TODO: implement the authenticate function for browserbase
                        success = await authenticate(self.page, self.storage_state)
                        if not success:
                            print("❌ Authentication didn't succeed fully.\n")

                    
                    await debug_browser_state(self.browser)
                
                elif self.mode == "chromium":
                    self.browser = await self.playwright.chromium.launch(headless=self.headless)
                    self.context = await self.browser.new_context()
                    self.page = await self.context.new_page()
                    cookies_restored = await restore_cookies(self.page, self.storage_state)

                    if cookies_restored and await check_login_status(self.page):
                        print("Using existing session cookies\n")
                    else:
                        print("Need to authenticate\n")
                        success = await authenticate(self.page, self.storage_state)
                        if not success:
                            print("❌ Authentication didn't succeed fully.\n")
                    
                else:
                    raise ValueError(f"Invalid mode: {self.mode}. Expected 'cdp', 'browserbase', or 'chromium'")
    
    async def get_live_browser_url(self):
        if self.mode == "browserbase":
            debug_info = self.bb.sessions.debug(self.session_id)
            self.live_browser_url = debug_info.debugger_url
        return self.live_browser_url
    
    async def get_session_id(self):
        return self.session_id
    
    async def get_browser(self):
        if self.browser is None:
            await self.initialize()
        return self.browser
    
    async def get_context(self):
        if self.context is None:
            await self.initialize()
        return self.context
    
    async def get_page(self):
        if self.page is None:
            await self.initialize()
        return self.page
    
    async def close(self):
        async with self.lock:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

async def setup_playwright(storage_state=None, headless=False, mode="chromium", session_id=None):
    playwright_manager = AsyncPlaywrightManager(storage_state=storage_state, headless=headless, mode=mode, session_id=session_id)
    browser = await playwright_manager.get_browser()
    context = await playwright_manager.get_context()
    page = await playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    return playwright_manager

async def test_chromium_mode():
    """Test the Playwright manager in Chromium mode"""
    print("\n=== Testing Chromium Mode ===")
    manager = await setup_playwright(storage_state="../../../shopping.json", mode="chromium", headless=False)
    
    try:
        page = await manager.get_page()
        await page.goto("http://128.105.145.205:7770/sales/order/history/")
        print(f"Current URL: {page.url}")
        await asyncio.sleep(3)  # Wait to see the page
    finally:
        print("Closing Chromium browser...")    
        await manager.close()

async def test_browserbase_mode():
    """Test the Playwright manager in Browserbase mode"""
    print("\n=== Testing Browserbase Mode ===")
    manager = await setup_playwright(storage_state="../../../shopping.json", mode="browserbase")
    
    try:
        page = await manager.get_page()
        print(f"Session ID: {await manager.get_session_id()}")
        print(f"Live Browser URL: {await manager.get_live_browser_url()}")
        import webbrowser
        print("Opening debugger URL in your default browser...")
        webbrowser.open(await manager.get_live_browser_url())
        await page.pause()
        await page.goto("http://128.105.145.205:7770/")
        await page.goto("http://128.105.145.205:7770/sales/order/history/")
        print(f"Current URL: {page.url}")
        print(f"You can view the browser at: {await manager.get_live_browser_url()}")
        await asyncio.sleep(10)  # Give more time to check the live URL
    finally:
        print("Closing Browserbase browser...")
        await manager.close()

async def main():
    """Main function to test different browser modes"""
    # Test Chromium mode
    await test_chromium_mode()
    
    # Test Browserbase mode
    await test_browserbase_mode()

if __name__ == "__main__":
    asyncio.run(main())