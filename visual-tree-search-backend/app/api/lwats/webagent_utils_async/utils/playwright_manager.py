import os
import asyncio
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import aiohttp

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

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


async def get_browser_url(session_id: str) -> str:
    """
    Get the URL to show the live view for the current browser session.

    :returns: URL
    """
    session_url = f"https://www.browserbase.com/v1/sessions/{session_id}/debug"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(session_url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["debuggerUrl"]

async def read_account_credentials(storage_state_path):
    """
    Read account credentials from the storage state file.
    
    Args:
        storage_state_path: Path to the storage state file (e.g., shopping.json)
    Returns:
        dict: Dictionary containing account credentials if found, None otherwise
    """
    try:
        with open(storage_state_path, 'r') as f:
            data = json.load(f)
            # Look for credentials in the root of the JSON file
            if 'credentials' in data:
                return data['credentials']
            # Also check if the file contains cookies (indicating it's a storage state file)
            if 'cookies' in data:
                print(f"Found storage state file with cookies at {storage_state_path}")
                return None
    except Exception as e:
        print(f"Error reading credentials from {storage_state_path}: {e}")
    return None

async def auto_login(page, credentials):
    """
    Perform auto-login based on the website and credentials provided.
    
    Args:
        page: Playwright page object
        credentials: Dictionary containing login credentials and website info
    """
    print(f"=== Starting auto_login process ===")
    
    if not credentials:
        print("No credentials provided, aborting login")
        return False
    
    print(f"Credentials contain keys: {', '.join(credentials.keys())}")
    
    try:
        # Navigate to login page if specified
        if 'login_url' in credentials:
            print(f"Navigating to login page: {credentials['login_url']}")
            await page.goto(credentials['login_url'])
            print(f"Navigation complete, current URL: {page.url}")
        else:
            print("No login_url provided, assuming we're already on the login page")
        
        # Click the Sign In button if we're on the main page
        print("Looking for Sign In button...")
        sign_in_button = page.get_by_role("link", name="Sign In")
        if sign_in_button:
            print("Sign In button found, clicking...")
            await sign_in_button.click()
            print("Waiting for page to load after clicking Sign In button")
            await page.wait_for_load_state('networkidle')
            print(f"Page loaded, current URL: {page.url}")
        else:
            print("No Sign In button found, assuming we're already on the login form")
        
        # Wait for login form to be ready
        print("Waiting for page to be ready for login form interaction")
        await page.wait_for_load_state('networkidle')
        print("Page ready for login form interaction")
        
        # Fill in username/email
        if 'username_field' in credentials and 'username' in credentials:
            print(f"Found username field selector: {credentials['username_field']}")
            print(f"Filling username field with: {credentials['username']}")
            await page.fill(credentials['username_field'], credentials['username'])
            print("Username filled successfully")
        else:
            print("Missing username_field or username in credentials")
        
        # Fill in password
        if 'password_field' in credentials and 'password' in credentials:
            print(f"Found password field selector: {credentials['password_field']}")
            print(f"Filling password field with: {credentials['password']}")
            await page.fill(credentials['password_field'], credentials['password'])
            print("Password filled successfully")
        else:
            print("Missing password_field or password in credentials")
        
        # Click the Sign In button in the login form
        print("Looking for Sign In button in login form...")
        login_form_button = page.get_by_role("button", name="Sign In")
        if login_form_button:
            print("Sign In button in login form found, clicking...")
            await login_form_button.click()
            print("Waiting for page to load after clicking login button")
            await page.wait_for_load_state('networkidle')
            print(f"Page loaded, current URL: {page.url}")
        else:
            print("No Sign In button found in login form, login may have failed")
        
        # Wait for login to complete
        print("Waiting for final page load after login attempt")
        await page.wait_for_load_state('networkidle')
        print(f"Final page after login attempt loaded, current URL: {page.url}")
        
        # Check if login was successful
        if 'success_indicator' in credentials and len(credentials['success_indicator']) > 0:
            print(f"Waiting for success indicator: {credentials['success_indicator']}")
            await page.wait_for_selector(credentials['success_indicator'])
            print("Success indicator found, login confirmed successful")
        else:
            print("No success_indicator provided, unable to confirm login success")
        
        print("=== Auto-login process completed successfully ===")
        return True
    
    except Exception as e:
        print(f"=== Error during auto-login process ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Current URL when error occurred: {page.url if page else 'Unknown'}")
        print("=== Auto-login process failed ===")
        return False

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
    
    async def setup_context_and_page(self, context_options=None):
        """Common function to handle context and page setup"""
        if context_options is None:
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

        if self.storage_state:
            context_options["storage_state"] = self.storage_state
            print(f"Using storage state from: {self.storage_state}")
            # Read credentials if storage state file exists
            self.credentials = await read_account_credentials(self.storage_state)

        contexts = self.browser.contexts
        if contexts:
            print("Found existing contexts, using the first one")
            self.context = contexts[0]
            if self.context.pages:
                print(f"Found existing page at URL: {self.context.pages[0].url}")
                self.page = self.context.pages[0]
            else:
                print("No pages in existing context, creating new page")
                self.page = await self.context.new_page()
        else:
            print("No existing contexts found, creating new one")
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
        # Attempt auto-login if credentials are available
        if self.credentials:
            print("Attempting auto-login...")
            success = await auto_login(self.page, self.credentials)
            if success:
                print("Auto-login successful")
            else:
                print("Auto-login failed")

    async def initialize(self):
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                
                if self.mode == "cdp":
                    chrome_url = "http://localhost:9222"
                    self.browser = await self.playwright.chromium.connect_over_cdp(chrome_url)
                    print('debug mode entered')
                    await debug_browser_state(self.browser)
                    
                    # Get non-extension context and page
                    self.context, self.page = await get_non_extension_context_and_page(self.browser)
                    if not self.context or not self.page:
                        raise ValueError("No non-extension context and page found in CDP browser")
                    
                    await debug_browser_state(self.browser)
                
                elif self.mode == "browserbase":
                    if self.session_id is None:
                        self.session_id = await create_session()
                    
                    self.live_browser_url = await get_browser_url(self.session_id)
                    
                    self.browser = await self.playwright.chromium.connect_over_cdp(
                        f"wss://connect.browserbase.com?apiKey={API_KEY}&sessionId={self.session_id}"
                    )
                    
                    await debug_browser_state(self.browser)
                    
                    # Use the common setup method
                    await self.setup_context_and_page()
                    
                    await debug_browser_state(self.browser)
                
                elif self.mode == "chromium":
                    self.browser = await self.playwright.chromium.launch(headless=self.headless)
                    
                    # Use the common setup method
                    await self.setup_context_and_page()
                    
                else:
                    raise ValueError(f"Invalid mode: {self.mode}. Expected 'cdp', 'browserbase', or 'chromium'")
    
    async def get_live_browser_url(self):
        if self.mode == "browserbase":
            self.live_browser_url = await get_browser_url(self.session_id)
        return self.live_browser_url
    
    def get_session_id(self):
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
        print(f"Navigating to example.com...")
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
        print(f"Session ID: {manager.get_session_id()}")
        print(f"Live Browser URL: {await manager.get_live_browser_url()}")
        print(f"Navigating to example.com...")
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
    #await test_chromium_mode()
    
    # Test Browserbase mode
    await test_browserbase_mode()

if __name__ == "__main__":
    asyncio.run(main())