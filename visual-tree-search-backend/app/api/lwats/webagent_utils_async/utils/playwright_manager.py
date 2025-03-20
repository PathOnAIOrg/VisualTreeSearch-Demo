import os
import asyncio
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
        if self.mode == "browserbase" and self.session_id:
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
    manager = await setup_playwright(mode="chromium", headless=False)
    
    try:
        page = await manager.get_page()
        print(f"Navigating to example.com...")
        await page.goto("https://example.com")
        print(f"Current URL: {page.url}")
        await asyncio.sleep(3)  # Wait to see the page
    finally:
        print("Closing Chromium browser...")
        await manager.close()

async def test_browserbase_mode():
    """Test the Playwright manager in Browserbase mode"""
    print("\n=== Testing Browserbase Mode ===")
    manager = await setup_playwright(mode="browserbase")
    
    try:
        page = await manager.get_page()
        print(f"Session ID: {manager.get_session_id()}")
        print(f"Live Browser URL: {await manager.get_live_browser_url()}")
        print(f"Navigating to example.com...")
        await page.goto("http://128.105.145.205:7770/")
        print(f"Current URL: {page.url}")
        print(f"You can view the browser at: {await manager.get_live_browser_url()}")
        await asyncio.sleep(100)  # Give more time to check the live URL
    finally:
        print("Closing Browserbase browser...")
        await manager.close()

async def main():
    """Main function to test different browser modes"""
    # # Test Chromium mode
    # await test_chromium_mode()
    
    # Test Browserbase mode
    await test_browserbase_mode()

if __name__ == "__main__":
    asyncio.run(main())