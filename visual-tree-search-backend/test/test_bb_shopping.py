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
    # Navigate to the sign-in page, enter the site credentials and sign in
    print("Attempting to log in")
    username = "emma.lopez@gmail.com"
    password = "Password.123"
    browser_tab.goto("http://128.105.145.205:7770/customer/account/login/")
    browser_tab.get_by_label("Email", exact=True).fill(username)
    browser_tab.get_by_label("Password", exact=True).fill(password)
    browser_tab.get_by_role("button", name="Sign In").click()
    # browser_tab.goto(SITE_LOGIN_URL)

    # browser_tab.get_by_role("textbox", name="username").fill(SITE_USERNAME)
    # browser_tab.get_by_role("textbox", name="password").fill(SITE_PASSWORD)
    # browser_tab.get_by_role("button", name="Login").click()

    # Store the site cookies
    store_cookies(browser_tab)


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
        proxies=True
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