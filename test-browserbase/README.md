# README

## 1. Set Up
create .env file
```
BROWSERBASE_PROJECT_ID=""
BROWSERBASE_API_KEY=""
```
then create virtual environment using the requirements.txt file


## 2. Tests
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

## 3. Cookie management
```
(venv) (venv) danqingzhang@Danqings-MBP VisualTreeSearch-demo % ssh -i ~/.ssh/id_rsa_personal pentium3@128.105.145.205
Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-131-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

 * Introducing Expanded Security Maintenance for Applications.
   Receive updates to over 25,000 software packages with your
   Ubuntu Pro subscription. Free for personal use.

     https://ubuntu.com/pro
Last login: Fri Mar 21 04:04:02 2025 from 70.22.181.171
pentium3@node-0:~$ mysql -u root -p1234567890 -h 127.0.0.1 -P 33061 magentodb
mysql: [Warning] Using a password on the command line interface can be insecure.
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 89151
Server version: 5.5.5-10.6.12-MariaDB MariaDB Server

Copyright (c) 2000, 2025, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> SELECT config_id, scope, scope_id, path, value
    -> FROM core_config_data
    -> WHERE path LIKE 'web/cookie/%';
+-----------+---------+----------+----------------------------+----------+
| config_id | scope   | scope_id | path                       | value    |
+-----------+---------+----------+----------------------------+----------+
|        53 | default |        0 | web/cookie/cookie_lifetime | 31536000 |
|        54 | default |        0 | web/cookie/cookie_path     | NULL     |
|        55 | default |        0 | web/cookie/cookie_domain   | NULL     |
|        56 | default |        0 | web/cookie/cookie_httponly | 1        |
+-----------+---------+----------+----------------------------+----------+
4 rows in set (0.01 sec)

mysql> SELECT config_id, scope, scope_id, path, value
    -> FROM core_config_data
    -> WHERE path = 'web/cookie/cookie_secure';
Empty set (0.00 sec)

mysql> SELECT config_id, scope, scope_id, path, value
    -> FROM core_config_data
    -> WHERE path IN (
    ->   'web/unsecure/base_url',
    ->   'web/secure/base_url'
    -> );
+-----------+----------+----------+-----------------------+------------------------------+
| config_id | scope    | scope_id | path                  | value                        |
+-----------+----------+----------+-----------------------+------------------------------+
|         2 | websites |        1 | web/unsecure/base_url | http://128.105.145.205:7770/ |
|        45 | default  |        0 | web/secure/base_url   | http://128.105.145.205:7770/ |
+-----------+----------+----------+-----------------------+------------------------------+
2 rows in set (0.00 sec)

mysql> 
```


## 4. Cookies Just Stored (Markdown Table)

| **Name** | **Value (first 10 chars)** | **Domain**          | **Path** | **HttpOnly** | **Secure** | **SameSite** | **Expires** |
|----------|----------------------------|---------------------|----------|-------------|-----------|-------------|------------|
| test_cookie | 1 | 128.105.145.205 | / | False | False | Lax | -1 |
| PHPSESSID | 9e51da9385... | 128.105.145.205 | / | True | False | Lax | 1774377035.337659 |
| form_key | RHI8Ca8byh... | 128.105.145.205 | / | False | False | Lax | 1774377035.337806 |
| mage-cache-storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-storage-section-invalidation | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-sessid | true | 128.105.145.205 | / | False | False | Lax | 1774377034 |
| mage-messages |  | 128.105.145.205 | / | False | False | Strict | 1774377035 |
| recently_viewed_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_viewed_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| product_data_storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| section_data_ids | {%22messag... | 128.105.145.205 | / | False | False | Lax | 1774377034 |

Checking if login succeeded...

Cookies after login attempt (13) (Markdown Table):

| **Name** | **Value (first 10 chars)** | **Domain**          | **Path** | **HttpOnly** | **Secure** | **SameSite** | **Expires** |
|----------|----------------------------|---------------------|----------|-------------|-----------|-------------|------------|
| test_cookie | 1 | 128.105.145.205 | / | False | False | Lax | -1 |
| PHPSESSID | 9e51da9385... | 128.105.145.205 | / | True | False | Lax | 1774377035.337659 |
| form_key | RHI8Ca8byh... | 128.105.145.205 | / | False | False | Lax | 1774377035.337806 |
| mage-cache-storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-storage-section-invalidation | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-sessid | true | 128.105.145.205 | / | False | False | Lax | 1774377034 |
| mage-messages |  | 128.105.145.205 | / | False | False | Strict | 1774377035 |
| recently_viewed_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_viewed_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| product_data_storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| section_data_ids | {%22messag... | 128.105.145.205 | / | False | False | Lax | 1774377034 |


## 5. Magento Cookie Comparison: Remote Browserbase vs Local Chrome

### Remote Browserbase Cookies

| Name | Value (first 10 chars) | Domain | Path | HttpOnly | Secure | SameSite | Expires |
|------|------------------------|--------|------|----------|--------|----------|---------|
| test_cookie | 1 | 128.105.145.205 | / | False | False | Lax | -1 |
| PHPSESSID | 9e51da9385... | 128.105.145.205 | / | True | False | Lax | 1774377035.337659 |
| form_key | RHI8Ca8byh... | 128.105.145.205 | / | False | False | Lax | 1774377035.337806 |
| mage-cache-storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-storage-section-invalidation | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| mage-cache-sessid | true | 128.105.145.205 | / | False | False | Lax | 1774377034 |
| mage-messages |  | 128.105.145.205 | / | False | False | Strict | 1774377035 |
| recently_viewed_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_viewed_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| recently_compared_product_previous | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| product_data_storage | {} | 128.105.145.205 | / | False | False | Lax | 1774377026 |
| section_data_ids | {%22messag... | 128.105.145.205 | / | False | False | Lax | 1774377034 |

### Local Chrome Browser Cookies (From DevTools Screenshot)

| Name | Value | Domain | Path | Expires / Max-Age | Size | HttpOnly | Secure | SameSite | Partition Key | Cross Site | Priority |
|------|-------|--------|------|-------------------|------|----------|--------|----------|--------------|------------|----------|
| PHPSESSID | 61e492df411a16932d7dc3790da00e7e | 128.105.145.205 | / | 2026-03-24T1... | 41 | ✓ |  | Lax |  |  | Medium |
| X-Magento-Vary | 9bf9a599123e6402b85cde6714477a08b817412 | 128.105.145.205 | / | 2026-03-24T1... | 54 | ✓ |  | Lax |  |  | Medium |
| form_key | WdjJuHYiAUcZ8cls | 128.105.145.205 | / | 2026-03-24T1... | 24 |  |  | Lax |  |  | Medium |
| mage-cache-sessid | true | 128.105.145.205 | / | 2026-03-24T1... | 21 |  |  | Lax |  |  | Medium |
| mage-cache-storage | {} | 128.105.145.205 | / | 2026-03-12T2... | 20 |  |  | Lax |  |  | Medium |
| mage-cache-storage-section-invalidation | {} | 128.105.145.205 | / | 2026-03-12T2... | 41 |  |  | Lax |  |  | Medium |
| mage-messages |  | 128.105.145.205 | / | 2026-03-24T1... | 13 |  |  | Strict |  |  | Medium |
| private_content_version | 0ae9963018e21a8c07a7912346cb7835 | 128.105.145.205 | / | 2026-04-28T1... | 55 |  |  | Lax |  |  | Medium |
| product_data_storage | {} | 128.105.145.205 | / | 2026-03-12T2... | 22 |  |  | Lax |  |  | Medium |
| recently_compared_product | {} | 128.105.145.205 | / | 2026-03-12T2... | 27 |  |  | Lax |  |  | Medium |
| recently_compared_product_previous | {} | 128.105.145.205 | / | 2026-03-12T2... | 36 |  |  | Lax |  |  | Medium |
| recently_viewed_product | {} | 128.105.145.205 | / | 2026-03-12T2... | 25 |  |  | Lax |  |  | Medium |
| recently_viewed_product_previous | {} | 128.105.145.205 | / | 2026-03-12T2... | 34 |  |  | Lax |  |  | Medium |
| section_data_ids | {%22customer%22:1742840624%2C%22compare-products%2... | 128.105.145.205 | / | 2026-03-24T1... | 530 |  |  | Lax |  |  | Medium |

### Key Differences

1. **Missing Frontend Cookie:** The remote Browserbase session doesn't have the `X-Magento-Vary` cookie that appears in your local Chrome browser.

2. **Missing Private Content Version:** The remote session is missing the `private_content_version` cookie which helps Magento manage private content caching.

3. **Value Differences:** The cookie values for PHPSESSID and form_key are different between environments (expected).

4. **Section Data IDs Format:** The contents of the section_data_ids cookie appear to have different structures.

These differences may explain why the login isn't working in the remote environment but works in your local browser.