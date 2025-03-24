# README

## Set Up
create .env file
```
BROWSERBASE_PROJECT_ID=""
BROWSERBASE_API_KEY=""
```
then create virtual environment using the requirements.txt file


## Tests
```
python test_browserbase_auto_login.py
python test_bb.py
python test_bb_shopping.py
```

```
python test_bb_shopping.py 
Connected to Browserbase. chromium version 128.0.6613.18
Live view URL (fullscreen): https://www.browserbase.com/devtools-fullscreen/inspector.html?wss=connect.browserbase.com/debug/5628a58f-db90-4fef-be1d-c5a8388e64e5/devtools/page/32E38AC153DCFFE4BD2920FACD19AA02?debug=true
Live view URL (with browser UI): https://www.browserbase.com/devtools/inspector.html?wss=connect.browserbase.com/debug/5628a58f-db90-4fef-be1d-c5a8388e64e5/devtools/page/32E38AC153DCFFE4BD2920FACD19AA02?debug=true
No cookie file found. Will need to authenticate.
Need to authenticate
Attempting login with Playwright form submission
Current URL: http://128.105.145.205:7770/customer/account/login/
Filling in login form...
Filled email field
Filled password field
Examining form elements...
Form input: form_key = 6ixFKbhpEDvxKsPY (type: hidden)
Form input: login[username] = [empty] (type: email)
Form input: login[password] = [empty] (type: password)
Form input: show-password = [empty] (type: checkbox)
Form input: username = [empty] (type: email)
Form input: password = [empty] (type: password)
Form input: captcha_form_id = user_login (type: hidden)
Form input: context = checkout (type: hidden)
Clicking login button...
Found login button: send2 (type: submit)
⚠️ Redirected back to login page: http://128.105.145.205:7770/customer/account/loginPost/
Saved 13 cookie(s) from the browser context
Checking if login succeeded...
Cookies after login attempt (13):
  - test_cookie = 1 (domain: 128.105.145.205, path: /)
  - PHPSESSID = 2517749c83... (domain: 128.105.145.205, path: /)
  - form_key = 6ixFKbhpED... (domain: 128.105.145.205, path: /)
  - mage-cache-storage = {} (domain: 128.105.145.205, path: /)
  - mage-cache-storage-section-invalidation = {} (domain: 128.105.145.205, path: /)
  - mage-cache-sessid = true (domain: 128.105.145.205, path: /)
  - mage-messages =  (domain: 128.105.145.205, path: /)
  - recently_viewed_product = {} (domain: 128.105.145.205, path: /)
  - recently_viewed_product_previous = {} (domain: 128.105.145.205, path: /)
  - recently_compared_product = {} (domain: 128.105.145.205, path: /)
  - recently_compared_product_previous = {} (domain: 128.105.145.205, path: /)
  - product_data_storage = {} (domain: 128.105.145.205, path: /)
  - section_data_ids = {%22messag... (domain: 128.105.145.205, path: /)
❌ No Magento frontend cookies found - login likely failed
❌ Login verification failed. Current page: http://128.105.145.205:7770/customer/account/ | Title: Customer Login

Page content excerpt:
<!DOCTYPE html><html lang="en"><head>
        <script>
    var LOCALE = 'en\u002DUS';
    var BASE_URL = 'http\u003A\u002F\u002F128.105.145.205\u003A7770\u002F';
    var require = {
        'baseUrl': 'http\u003A\u002F\u002F128.105.145.205\u003A7770\u002Fstatic\u002Fversion1681826198\u002Ffrontend\u002FMagento\u002Fblank\u002Fen_US'
    };</script>        <meta charset="utf-8">
<meta name="title" content="Customer Login">
<meta name="robots" content="INDEX,FOLLOW">
<meta name="viewport" content=...

⚠️ Trying fallback login method with fetch API...
Found form_key: 6ixFKbhpEDvxKsPY
Form action URL: http://128.105.145.205:7770/customer/account/loginPost/
XHR login result: {'status': 200, 'statusText': 'OK', 'headers': {'cache-control': 'max-age=0, must-revalidate, no-cache, no-store\r', 'connection': 'close\r', 'content-encoding': 'gzip\r', 'content-security-policy-report-only': "font-src data: 'self' 'unsafe-inline'; form-action geostag.cardinalcommerce.com geo.cardinalcommerce.com 1eafstag.cardinalcommerce.com 1eaf.cardinalcommerce.com centinelapistag.cardinalcommerce.com centinelapi.cardinalcommerce.com pilot-payflowlink.paypal.com www.paypal.com www.sandbox.paypal.com *.cardinalcommerce.com *.paypal.com 3ds-secure.cardcomplete.com www.clicksafe.lloydstsb.com pay.activa-card.com *.wirecard.com acs.sia.eu *.touchtechpayments.com www.securesuite.co.uk rsa3dsauth.com *.monzo.com *.arcot.com *.wlp-acs.com 'self' 'unsafe-inline'; frame-ancestors 'self'; frame-src fast.amc.demdex.net *.adobe.com bid.g.doubleclick.net *.youtube.com *.youtube-nocookie.com geostag.cardinalcommerce.com geo.cardinalcommerce.com 1eafstag.cardinalcommerce.com 1eaf.cardinalcommerce.com centinelapistag.cardinalcommerce.com centinelapi.cardinalcommerce.com www.paypal.com www.sandbox.paypal.com pilot-payflowlink.paypal.com player.vimeo.com https://www.google.com/recaptcha/ c.paypal.com checkout.paypal.com assets.braintreegateway.com pay.google.com *.cardinalcommerce.com *.paypal.com * 'self' 'unsafe-inline'; img-src assets.adobedtm.com amcglobal.sc.omtrdc.net dpm.demdex.net cm.everesttech.net *.adobe.com widgets.magentocommerce.com data: www.googleadservices.com www.google-analytics.com googleads.g.doubleclick.net www.google.com bid.g.doubleclick.net analytics.google.com www.googletagmanager.com *.ftcdn.net *.behance.net t.paypal.com www.paypal.com www.paypalobjects.com fpdbs.paypal.com fpdbs.sandbox.paypal.com *.vimeocdn.com i.ytimg.com *.youtube.com validator.swagger.io www.sandbox.paypal.com b.stats.paypal.com dub.stats.paypal.com assets.braintreegateway.com c.paypal.com checkout.paypal.com *.paypal.com data: 'self' 'unsafe-inline'; script-src assets.adobedtm.com *.adobe.com www.googleadservices.com www.google-analytics.com googleads.g.doubleclick.net analytics.google.com www.googletagmanager.com *.newrelic.com *.nr-data.net geostag.cardinalcommerce.com 1eafstag.cardinalcommerce.com geoapi.cardinalcommerce.com 1eafapi.cardinalcommerce.com songbird.cardinalcommerce.com includestest.ccdc02.com www.paypal.com www.sandbox.paypal.com www.paypalobjects.com t.paypal.com s.ytimg.com www.googleapis.com vimeo.com www.vimeo.com *.vimeocdn.com *.youtube.com https://www.gstatic.com/recaptcha/ https://www.google.com/recaptcha/ js.braintreegateway.com assets.braintreegateway.com c.paypal.com pay.google.com api.braintreegateway.com api.sandbox.braintreegateway.com client-analytics.braintreegateway.com client-analytics.sandbox.braintreegateway.com *.paypal.com songbirdstag.cardinalcommerce.com 'self' 'unsafe-inline' 'unsafe-eval'; style-src *.adobe.com unsafe-inline assets.braintreegateway.com 'self' 'unsafe-inline'; object-src 'self' 'unsafe-inline'; media-src *.adobe.com 'self' 'unsafe-inline'; manifest-src 'self' 'unsafe-inline'; connect-src dpm.demdex.net amcglobal.sc.omtrdc.net www.google-analytics.com www.googleadservices.com analytics.google.com www.googletagmanager.com *.newrelic.com *.nr-data.net vimeo.com geostag.cardinalcommerce.com geo.cardinalcommerce.com 1eafstag.cardinalcommerce.com 1eaf.cardinalcommerce.com centinelapistag.cardinalcommerce.com centinelapi.cardinalcommerce.com www.sandbox.paypal.com www.paypalobjects.com www.paypal.com pilot-payflowlink.paypal.com api.braintreegateway.com api.sandbox.braintreegateway.com client-analytics.braintreegateway.com client-analytics.sandbox.braintreegateway.com *.braintree-api.com *.paypal.com *.cardinalcommerce.com 'self' 'unsafe-inline'; child-src assets.braintreegateway.com c.paypal.com *.paypal.com http: https: blob: 'self' 'unsafe-inline'; default-src 'self' 'unsafe-inline' 'unsafe-eval'; base-uri 'self' 'unsafe-inline';\r", 'content-type': 'text/html; charset=UTF-8\r', 'date': 'Mon, 24 Mar 2025 18:10:33 GMT\r', 'expires': 'Sun, 24 Mar 2024 18:10:33 GMT\r', 'login-required': 'true\r', 'pragma': 'no-cache\r', 'server': 'nginx/1.22.1\r', 'transfer-encoding': 'chunked\r', 'vary': 'Accept-Encoding\r', 'x-content-type-options': 'nosniff\r', 'x-frame-options': 'SAMEORIGIN\r', 'x-magento-tags': 'FPC\r', 'x-powered-by': 'PHP/8.1.17\r', 'x-xss-protection': '1; mode=block'}, 'url': 'http://128.105.145.205:7770/customer/account/loginPost/', 'redirected': False, 'ok': True}
❌ Fallback login also failed
Accessing protected URL: http://128.105.145.205:7770/sales/order/history
Final page: http://128.105.145.205:7770/sales/order/history | Title: Customer Login
❌ Failed to access protected page - still seeing login page
```