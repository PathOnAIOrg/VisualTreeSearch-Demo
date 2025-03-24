# The first time this file is run, the authentication cookies will be stored
# to a file. Subsequent runs will load those cookies from the file.
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


def store_cookies(browser_tab: Page):
    # Retrieve all the cookies for this URL
    all_cookies = browser_tab.context.cookies(SITE_URL)

    # You might want to put these in some durable storage, but for now
    # just keep them in a simple file as JSON.
    with open(COOKIE_FILE, "w") as cookie_file:
        json.dump(all_cookies, cookie_file, indent=4)

    print(f"Saved {len(all_cookies)} cookie(s) from the browser context")


def restore_cookies(browser_tab: Page):
    # Return all cookies to the browser context
    try:
        with open(COOKIE_FILE) as cookie_file:
            cookies = json.load(cookie_file)
    except FileNotFoundError:
        # No cookies to restore
        print("No cookie file found. Will need to authenticate.")
        return False

    browser_tab.context.add_cookies(cookies)
    print(f"Restored {len(cookies)} cookie(s) to the browser context")
    return True


def authenticate(browser_tab: Page):
    """Authenticate to Magento using Playwright form submission."""
    print("Attempting login with Playwright form submission")
    username = "emma.lopez@gmail.com"
    password = "Password.123"
    
    # Start fresh without cookies
    browser_tab.context.clear_cookies()
    
    # Set domain to ensure cookies are properly saved
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
    
    # Fill in login form using Playwright
    print("Filling in login form...")
    
    # Find and fill the username field
    email_field = browser_tab.query_selector("#email")
    if email_field:
        email_field.fill(username)
        print("Filled email field")
    else:
        print("⚠️ Could not find email field")
    
    # Find and fill the password field
    password_field = browser_tab.query_selector("#pass")
    if password_field:
        password_field.fill(password)
        print("Filled password field")
    else:
        print("⚠️ Could not find password field")
    
    # Inspect the form to see all hidden inputs
    print("Examining form elements...")
    form_elements = browser_tab.query_selector_all("form.form-login input, form#login-form input")
    for element in form_elements:
        name = element.get_attribute("name")
        value = element.get_attribute("value")
        input_type = element.get_attribute("type")
        if name:
            print(f"Form input: {name} = {value if value else '[empty]'} (type: {input_type})")
    
    # Click the login button and wait for navigation
    print("Clicking login button...")
    
    # Some Magento sites use different selectors, so try a few common ones
    login_button = (
        browser_tab.query_selector(".action.login.primary") or
        browser_tab.query_selector("#send2") or
        browser_tab.query_selector("button[type='submit']")
    )
    
    if login_button:
        print(f"Found login button: {login_button.get_attribute('id')} (type: {login_button.get_attribute('type')})")
        
        # Interacting with localStorage to check for any cookie-related settings
        cookie_settings = browser_tab.evaluate("""() => {
            const settings = {};
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.includes('cookie') || key.includes('session'))) {
                        settings[key] = localStorage.getItem(key);
                    }
                }
            } catch (e) {
                console.error("localStorage error:", e);
            }
            return settings;
        }""")
        
        if cookie_settings:
            print(f"Found cookie-related localStorage settings: {cookie_settings}")
        
        # Enable cookie tracking before clicking
        browser_tab.evaluate("""() => {
            try {
                // Attempt to set a permissive environment for cookies
                document.cookie = "cookie_test=1; path=/; domain=128.105.145.205; SameSite=None;";
                console.log("Test cookie set:", document.cookie);
            } catch (e) {
                console.error("Cookie error:", e);
            }
        }""")
        
        # Click and wait for navigation to complete
        try:
            # Using Promise.all to wait for navigation and network idle
            with browser_tab.expect_navigation(wait_until="networkidle", timeout=15000):
                login_button.click()
            browser_tab.screenshot(path="screenshot_after_click.png")
        except Exception as e:
            print(f"Navigation timeout or error: {e}")
            browser_tab.screenshot(path="screenshot_after_error.png")
        
        # Check if we got redirected to login page again
        if "/login" in browser_tab.url:
            print(f"⚠️ Redirected back to login page: {browser_tab.url}")
            
            # Try to debug the issue by examining the page
            error_message = browser_tab.query_selector(".message-error") or browser_tab.query_selector(".error-msg")
            if error_message:
                print(f"Error message: {error_message.text_content()}")
    else:
        print("⚠️ Could not find login button!")
    
    # Save the cookies regardless of success
    store_cookies(browser_tab)
    
    # Check if login succeeded
    print("Checking if login succeeded...")
    
    # Check cookie status before navigating away
    cookies = browser_tab.context.cookies()
    print(f"Cookies after login attempt ({len(cookies)}):")
    for cookie in cookies:
        cookie_value = cookie['value'][:10] + "..." if len(cookie['value']) > 10 else cookie['value']
        print(f"  - {cookie['name']} = {cookie_value} (domain: {cookie.get('domain', 'none')}, path: {cookie.get('path', '/')})")
    
    # Check specifically for frontend cookie
    frontend_cookies = [c for c in cookies if 'frontend' in c.get('name', '')]
    if frontend_cookies:
        print(f"✅ Found {len(frontend_cookies)} Magento frontend cookie(s)")
    else:
        print("❌ No Magento frontend cookies found - login likely failed")
    
    # Navigate to account page
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_after_login.png")
    
    # Verify login status by checking page content
    is_logged_in = False
    
    # Try multiple ways to check login status
    try:
        # Check if we can see customer dashboard elements
        welcome_msg = browser_tab.query_selector(".box-information .box-content p") or browser_tab.query_selector(".welcome-msg")
        account_nav = browser_tab.query_selector(".block-dashboard-info") or browser_tab.query_selector(".block-dashboard-addresses")
        
        if welcome_msg and "Emma" in welcome_msg.text_content():
            is_logged_in = True
            print(f"✅ Welcome message found: {welcome_msg.text_content().strip()}")
        
        if account_nav:
            is_logged_in = True
            print("✅ Dashboard navigation elements found")
            
        # Check page title
        if "My Account" in browser_tab.title() and "Login" not in browser_tab.title():
            is_logged_in = True
            print(f"✅ Page title indicates logged in: {browser_tab.title()}")
            
    except Exception as e:
        print(f"Error checking login status: {e}")
    
    if is_logged_in:
        print("✅ Successfully logged in!")
        return True
    else:
        print(f"❌ Login verification failed. Current page: {browser_tab.url} | Title: {browser_tab.title()}")
        
        # Debug: print page content to help diagnose issues
        print("\nPage content excerpt:")
        content = browser_tab.content()
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Try fallback method: using the direct POST method with fetch
        return fallback_login_post(browser_tab)


def fallback_login_post(browser_tab: Page):
    """Fallback login method using fetch API."""
    print("\n⚠️ Trying fallback login method with fetch API...")
    
    # Navigate to login page to get a fresh form_key
    browser_tab.goto(SITE_LOGIN_URL)
    browser_tab.wait_for_load_state("networkidle")
    
    # Extract form_key
    form_key_element = browser_tab.query_selector("input[name='form_key']")
    form_key = form_key_element.get_attribute("value") if form_key_element else ""
    print(f"Found form_key: {form_key}")
    
    username = "emma.lopez@gmail.com"
    password = "Password.123"
    
    # Get the exact form action URL
    form = browser_tab.query_selector("form.form-login") or browser_tab.query_selector("form#login-form")
    form_action = form.get_attribute("action") if form else SITE_URL + "/customer/account/loginPost/"
    print(f"Form action URL: {form_action}")
    
    # Attempt to use XMLHttpRequest for better cookie handling
    result = browser_tab.evaluate("""async (credentials) => {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', credentials.formAction, true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.withCredentials = true;
            
            xhr.onload = function() {
                const responseHeaders = {};
                const rawHeaders = xhr.getAllResponseHeaders().trim().split('\\n');
                rawHeaders.forEach(line => {
                    const parts = line.split(': ');
                    const name = parts.shift();
                    if (name) {
                        responseHeaders[name] = parts.join(': ');
                    }
                });
                
                resolve({
                    status: xhr.status,
                    statusText: xhr.statusText,
                    headers: responseHeaders,
                    url: xhr.responseURL || credentials.formAction,
                    redirected: xhr.responseURL !== credentials.formAction,
                    ok: xhr.status >= 200 && xhr.status < 300
                });
            };
            
            xhr.onerror = function() {
                reject(new Error('Network request failed'));
            };
            
            // Prepare form data
            const formData = new FormData();
            formData.append('form_key', credentials.formKey);
            formData.append('login[username]', credentials.username);
            formData.append('login[password]', credentials.password);
            
            // Convert FormData to URL-encoded string
            const params = new URLSearchParams();
            for (const pair of formData.entries()) {
                params.append(pair[0], pair[1]);
            }
            
            xhr.send(params.toString());
        });
    }""", {
        "username": username, 
        "password": password, 
        "formKey": form_key,
        "formAction": form_action
    })
    
    print(f"XHR login result: {result}")
    
    # Now navigate to the account page to see if we're logged in
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_after_fallback.png")
    
    # Check for login success
    if "Login" in browser_tab.title():
        print("❌ Fallback login also failed")
        return False
    else:
        print("✅ Fallback login successful!")
        # Save the cookies for future use
        store_cookies(browser_tab)
        return True


def check_login_status(browser_tab: Page):
    """Check if the user is already logged in."""
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    
    if "Login" in browser_tab.title():
        print("User is not logged in")
        return False
    else:
        print("User is already logged in")
        return True


def run(browser_tab: Page):
    # Load up any stored cookies
    cookies_restored = restore_cookies(browser_tab)

    # Check if we're already logged in
    if cookies_restored and check_login_status(browser_tab):
        print("Using existing session cookies")
    else:
        print("Need to authenticate")
        # Authenticate the user
        authenticate(browser_tab)
    
    # Try accessing the protected URL
    print(f"Accessing protected URL: {SITE_PROTECTED_URL}")
    browser_tab.goto(SITE_PROTECTED_URL)
    browser_tab.wait_for_load_state("networkidle")

    # Print out a bit of info about the page it landed on
    print(f"Final page: {browser_tab.url} | Title: {browser_tab.title()}")
    
    # Check if we're still on a login page
    if "Login" in browser_tab.title():
        print("❌ Failed to access protected page - still seeing login page")
        browser_tab.screenshot(path="screenshot_final_fail.png")
    else:
        print("✅ Successfully accessing protected page")
        browser_tab.screenshot(path="screenshot_final_success.png")


with sync_playwright() as playwright:
    bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])
    # A session is created on the fly
    session = bb.sessions.create(
        project_id=os.environ["BROWSERBASE_PROJECT_ID"],
        proxies=False
    )
    browser = playwright.chromium.connect_over_cdp(session.connectUrl)

    # Print a bit of info about the browser we've connected to
    print(
        "Connected to Browserbase.",
        f"{browser.browser_type.name} version {browser.version}",
    )

    context = browser.contexts[0]
    browser_tab = context.pages[0]
    # Retrieve live view URLs for the running session
    live_info = bb.sessions.debug(session.id)
    print("Live view URL (fullscreen):", live_info.debugger_fullscreen_url)
    print("Live view URL (with browser UI):", live_info.debugger_url)
    
    try:
        # Perform our browser commands
        run(browser_tab)

    finally:
        # Clean up
        browser_tab.close()
        browser.close()