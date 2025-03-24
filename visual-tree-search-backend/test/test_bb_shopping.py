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

# Credentials to use for testing the login flow.
# For testing only! Don't store secrets in code.
# SITE_USERNAME = "practice"
# SITE_PASSWORD = "SuperSecretPassword!"

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
        return

    browser_tab.context.add_cookies(cookies)
    print(f"Restored {len(cookies)} cookie(s) to the browser context")


def authenticate(browser_tab: Page):
    """Authenticate using direct form data submission."""
    print("Attempting login with direct form submission")
    username = "emma.lopez@gmail.com"
    password = "Password.123"
    
    # Start fresh without cookies
    browser_tab.context.clear_cookies()
    
    # Navigate to login page
    browser_tab.goto("http://128.105.145.205:7770/customer/account/login/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_login_page.png")
    
    # Extract form_key
    form_key_element = browser_tab.query_selector("input[name='form_key']")
    form_key = form_key_element.get_attribute("value") if form_key_element else ""
    print(f"Found form_key: {form_key}")
    
    # Instead of filling the form and clicking, let's try a different approach.
    # Correct syntax for evaluate with arguments - the function is the first arg, followed by args dict
    print("Submitting login data using fetch API...")
    
    result = browser_tab.evaluate("""async (credentials) => {
        // Build the form data
        const formData = new FormData();
        formData.append('form_key', credentials.formKey);
        formData.append('login[username]', credentials.username);
        formData.append('login[password]', credentials.password);
        
        // Get the form action URL
        const form = document.querySelector('form.form-login') || document.querySelector('form#login-form');
        const actionUrl = form ? form.action : window.location.origin + '/customer/account/loginPost/';
        
        console.log('Submitting to:', actionUrl);
        
        try {
            // Submit using fetch API with same-origin credentials
            const response = await fetch(actionUrl, {
                method: 'POST',
                body: formData,
                redirect: 'follow',
                credentials: 'same-origin'
            });
            
            console.log('Response status:', response.status);
            console.log('Response URL:', response.url);
            
            // Check if we received a redirect
            if (response.redirected) {
                console.log('Redirected to:', response.url);
                return { success: true, redirectUrl: response.url };
            }
            
            // If we got HTML response, we'll navigate there
            const text = await response.text();
            console.log('Response length:', text.length);
            
            return { 
                success: response.ok, 
                status: response.status,
                url: response.url,
                text: text.substring(0, 100) + '...' // Just show beginning for logging
            };
        } catch (error) {
            console.error('Fetch error:', error);
            return { success: false, error: error.toString() };
        }
    }""", {"username": username, "password": password, "formKey": form_key})
    
    print(f"Fetch result: {result}")
    
    # 2. Now manually navigate to the account page to see if we're logged in
    print("Checking if login succeeded by navigating to account page...")
    browser_tab.goto("http://128.105.145.205:7770/customer/account/")
    browser_tab.wait_for_load_state("networkidle")
    browser_tab.screenshot(path="screenshot_after_login.png")
    
    # 3. First, examine cookies to see if we got a session cookie
    cookies = browser_tab.context.cookies()
    frontend_cookies = [c for c in cookies if 'frontend' in c.get('name', '')]
    
    if frontend_cookies:
        print(f"Found {len(frontend_cookies)} Magento session cookies:")
        for cookie in frontend_cookies:
            print(f"  - {cookie['name']} = {cookie['value'][:10]}... (expires: {cookie.get('expires', 'session')})")
    else:
        print("No Magento session cookies found - login likely failed")
    
    # 4. Check page content for login indicators
    is_logged_in = "My Account" in browser_tab.title()
    customer_name = None
    
    try:
        # Try to find welcome message which typically contains customer name
        welcome_msg = browser_tab.query_selector(".box-information .box-content p")
        if welcome_msg:
            customer_name = welcome_msg.text_content().strip()
            if "Emma" in customer_name:
                is_logged_in = True
    except Exception:
        pass
    
    if is_logged_in:
        print(f"✅ Successfully logged in! Welcome message: {customer_name}")
        return True
    else:
        print(f"❌ Login verification failed. Current page: {browser_tab.url} | Title: {browser_tab.title()}")
        
        # Try one more approach - attempt to access a protected page
        print("Attempting to access order history as final verification...")
        browser_tab.goto("http://128.105.145.205:7770/sales/order/history")
        browser_tab.wait_for_load_state("networkidle")
        


def run(browser_tab: Page):
    # Load up any stored cookies
    restore_cookies(browser_tab)

    # Instruct the browser to go to a protected page
    browser_tab.goto("http://128.105.145.205:7770/customer/account/login/")
    print(browser_tab.url)

    
    # Redirected, almost certainly need to log in.
    authenticate(browser_tab)

    # Try again
    browser_tab.goto(SITE_PROTECTED_URL)

    # Print out a bit of info about the page it landed on
    print(f"{browser_tab.url=} | {browser_tab.title()=}")

    ...


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
    browser_tab.goto("https://www.google.com")

    try:
        # Perform our browser commands
        run(browser_tab)

    finally:
        # Clean up
        browser_tab.close()
        browser.close()