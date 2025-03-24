import os
import asyncio
import json
import aiohttp
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

'''
python test/test_browserbase_auto_login.py
'''

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

async def create_session() -> str:
    """Create a Browserbase session and return the session ID."""
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
    """Get the URL to show the live view for the current browser session."""
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
    """Read account credentials from the storage state file."""
    try:
        with open(storage_state_path, 'r') as f:
            data = json.load(f)
            # Check for credentials in the root of the JSON file
            if 'credentials' in data:
                return data['credentials']
            # Check if file contains cookies (indicating it's a storage state file)
            if 'cookies' in data:
                print(f"Found storage state file with cookies at {storage_state_path}")
                return None
    except Exception as e:
        print(f"Error reading credentials from {storage_state_path}: {e}")
    return None

async def main(storage_state_path = "shopping.json"):
    print(f"Starting Browserbase auto-login test with credentials from {storage_state_path}")
    
    # Create a Browserbase session
    session_id = await create_session()
    browser_url = await get_browser_url(session_id)
    print(f"Session ID: {session_id}")
    print(f"Live Browser URL: {browser_url}")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(
            f"wss://connect.browserbase.com?apiKey={API_KEY}&sessionId={session_id}"
        )
        
        # Set up context with viewport and user agent
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        # Add storage state if provided
        if storage_state_path:
            context_options["storage_state"] = storage_state_path
            print(f"Using storage state from: {storage_state_path}")
        
        try:
            # Create browser context and page
            context = await browser.new_context(**context_options)
            page = await context.new_page()

            
            if not storage_state_path:
                username = "emma.lopez@gmail.com"
                password = "Password.123"
                await page.goto("http://128.105.145.205:7770/customer/account/login/")
                await page.get_by_label("Email", exact=True).fill(username)
                await page.get_by_label("Password", exact=True).fill(password)
                await page.get_by_role("button", name="Sign In").click()
            print(f"Current URL after login: {page.url}")
                    
            # Navigate to a protected page to verify login success
            target_url = "http://128.105.145.205:7770/"  # Update with your target URL
            print(f"Navigating to target URL: {target_url}")
            await page.goto(target_url)
            await asyncio.sleep(5)
            print(f"Current URL after navigation: {page.url}")
            target_url = "http://128.105.145.205:7770/sales/order/history/"  # Update with your target URL
            print(f"Navigating to target URL: {target_url}")
            await page.goto(target_url)
            print(f"Current URL after navigation: {page.url}")
            
            # Wait to allow viewing the page in the live browser
            print(f"You can view the browser at: {browser_url}")
            print("Keeping the browser open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
        finally:
            # Clean up
            await context.close()
            await browser.close()
            print("Browser closed")

if __name__ == "__main__":
    asyncio.run(main(storage_state_path = "shopping_v1.json"))
    asyncio.run(main(storage_state_path = None))