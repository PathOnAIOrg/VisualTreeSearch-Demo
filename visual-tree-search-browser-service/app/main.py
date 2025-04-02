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
import boto3

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

@app.get("/")
async def root():
    return {"message": "Web Automation API is running!"}

@app.get("/hello")
async def hello():
    return {"message": "Hello World!"}

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

async def download_cookies_from_s3():
    """Download cookies from S3 and return them as a list"""
    s3_client = boto3.client('s3')
    temp_cookie_path = "/tmp/shopping.json"
    try:
        # Check if file exists in S3
        try:
            s3_client.head_object(Bucket='test-litewebagent', Key='shopping.json')
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("No existing cookies file in S3")
                return None
            else:
                # Something else went wrong
                raise e

        # If we get here, file exists, so download it
        s3_client.download_file('test-litewebagent', 'shopping.json', temp_cookie_path)
        with open(temp_cookie_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to download cookies from S3: {str(e)}")
        return None

async def check_login_status(page, site_url) -> bool:
    """Check if we're on the customer account page rather than the login page."""
    await page.goto(f"{site_url}/customer/account/")
    await page.wait_for_load_state("networkidle")

    title = await page.title()
    if "Login" in title:
        print("User is not logged in (title contains 'Login')")
        return False
    else:
        print("User is already logged in (account page). Title:", title)
        return True

async def restore_cookies(page, cookies):
    """Restore cookies to the browser"""
    if not cookies:
        return False
    try:
        await page.context.add_cookies(cookies)
        print(f"Restored {len(cookies)} cookie(s) to the browser context")
        return True
    except Exception as e:
        print(f"Failed to restore cookies: {str(e)}")
        return False

@app.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_user(request: AuthenticationRequest):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # First try to restore cookies from S3
            cookies = await download_cookies_from_s3()
            if cookies:
                cookies_restored = await restore_cookies(page, cookies)
                if cookies_restored and await check_login_status(page, request.site_url):
                    print("Successfully logged in with existing cookies")
                    return AuthenticationResponse(
                        status="success",
                        message="Successfully authenticated using existing cookies"
                    )

            # If we get here, either there were no cookies or they didn't work
            # Proceed with fresh authentication
            print("Existing cookies failed or not found, proceeding with fresh authentication")

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

            # Check login status
            await page.goto(f"{request.site_url}/customer/account/")
            page_title = await page.title()
            
            # Get new cookies
            new_cookies = await context.cookies()
            
            # Check if login was successful
            if "Login" not in page_title:
                # Save and upload new cookies
                temp_cookie_path = "/tmp/shopping.json"
                with open(temp_cookie_path, 'w') as f:
                    json.dump(new_cookies, f, indent=4)
                
                try:
                    s3_client = boto3.client('s3')
                    s3_client.upload_file(
                        temp_cookie_path,
                        'test-litewebagent',
                        'shopping.json'
                    )
                    print("Successfully uploaded new cookies to S3")
                except Exception as e:
                    print(f"Failed to upload new cookies to S3: {str(e)}")

                return AuthenticationResponse(
                    status="success",
                    message="Successfully authenticated with fresh login"
                )
            else:
                return AuthenticationResponse(
                    status="error",
                    message="Authentication failed - still on login page"
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