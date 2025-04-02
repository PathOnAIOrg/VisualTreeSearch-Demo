from fastapi import FastAPI, BackgroundTasks, status, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from playwright.async_api import async_playwright
import time
import uvicorn
from dotenv import load_dotenv
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Web Automation API",
    redirect_slashes=False
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebAutomationRequest(BaseModel):
    url: str
    selector: str = None
    action: str = None
    wait_time: int = 5000  # milliseconds

class WebAutomationResponse(BaseModel):
    status: str
    message: str
    content: str = None
    screenshot_path: str = None

class AuthenticationRequest(BaseModel):
    username: str
    password: str
    site_url: str = "http://128.105.145.205:7770"

class AuthenticationResponse(BaseModel):
    status: str
    message: str
    cookies: list = None
    screenshot_path: str = None

@app.get("/")
async def root():
    return {"message": "Web Automation API is running!"}

@app.get("/hello")
async def hello():
    return {"message": "Hello World!"}

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "uptime": time.time(),
            "service": "web-automation-api"
        }
    )

@app.post("/automate", response_model=WebAutomationResponse)
async def automate_web(request: WebAutomationRequest, background_tasks: BackgroundTasks):
    try:
        result = await run_automation(request)
        return result
    except Exception as e:
        return WebAutomationResponse(
            status="error",
            message=f"Automation failed: {str(e)}"
        )

@app.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_user(request: AuthenticationRequest):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to login page
            login_url = f"{request.site_url}/customer/account/login/"
            await page.goto(login_url, wait_until="networkidle")
            
            # Take screenshot of login page
            login_screenshot = "/tmp/screenshot_login.png"
            await page.screenshot(path=login_screenshot)

            # Fill in login form
            await page.fill("#email", request.username)
            await page.fill("#pass", request.password)

            # Click login button and wait for navigation
            login_button = (
                await page.query_selector(".action.login.primary") or
                await page.query_selector("#send2") or
                await page.query_selector("button[type='submit']")
            )

            if not login_button:
                raise HTTPException(status_code=400, detail="Login button not found")

            # Click and wait for navigation
            async with page.expect_navigation(wait_until="networkidle", timeout=15000):
                await login_button.click()

            # Take screenshot after login attempt
            after_login_screenshot = "/tmp/screenshot_after_login.png"
            await page.screenshot(path=after_login_screenshot)

            cookies = await page.context.cookies()

            # Check for Magento 2's typical session cookie (PHPSESSID) or Magento 1's (frontend)
            magento_session_cookies = [c for c in cookies if c["name"] in ("frontend", "frontend_cid", "PHPSESSID")]
            if magento_session_cookies:
                print(f"✅ Found {len(magento_session_cookies)} potential Magento session cookie(s): {', '.join(c['name'] for c in magento_session_cookies)}")
            else:
                print("❌ No Magento 'frontend' or 'PHPSESSID' cookie found - likely not authenticated.\n")

            # Check login status
            await page.goto(f"{request.site_url}/customer/account/")
            page_title = await page.title()
            print(page_title)
            
            # Get cookies
            cookies = await context.cookies()

            # Check if login was successful
            if "Login" not in page_title:
                return AuthenticationResponse(
                    status="success",
                    message="Successfully authenticated",
                    cookies=cookies,
                    screenshot_path=after_login_screenshot
                )
            else:
                return AuthenticationResponse(
                    status="error",
                    message="Authentication failed - still on login page",
                    screenshot_path=after_login_screenshot
                )

            await browser.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

async def run_automation(request: WebAutomationRequest):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(request.url, wait_until="networkidle")
        
        # Wait for the specified time
        if request.wait_time > 0:
            await page.wait_for_timeout(request.wait_time)
        
        # Perform action if specified
        content = ""
        screenshot_path = None
        
        if request.selector:
            await page.wait_for_selector(request.selector, state="visible")
            
            if request.action == "click":
                await page.click(request.selector)
                await page.wait_for_timeout(1000)  # Wait after click
                
            elif request.action == "extract":
                element = await page.query_selector(request.selector)
                content = await element.inner_text()
        
        # Take a screenshot
        screenshot_path = "/tmp/screenshot.png"
        await page.screenshot(path=screenshot_path)
        
        # Close browser
        await browser.close()
        
        return WebAutomationResponse(
            status="success",
            message="Web automation completed successfully",
            content=content,
            screenshot_path=screenshot_path
        )
    
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)