# Flasky (Python version)
Flask application to practice different types of web vulnerabilities by both black-box and white-box testing methodologies.

> Note - Tested with Python 3.8.10 & 3.13.1

## RUN THE CODE
```bash
git clone https://github.com/dexter-11/Flasky.git
cd flasky
python3 -m venv flask-venv
source flask-venv/bin/activate #OR powershell -noexit -ep bypass -File .\flasky-venv\Scripts\Activate.ps1
pip3 install -r requirements.txt

python3 app.py
```

- - -
## INDEX - Cross-Site Scripting (XSS) 

### SCENARIO 1.0 - Unauthenticated Reflected XSS via GET ###
- Part of BaseApp
- `GET https://127.0.0.1:5000/login?error=`
- PoC - https://127.0.0.1:5000/login?error=%3Cimg%20src=x%20onerror=confirm(1)%3E

### SCENARIO 1.1 - Server-side Reflected XSS with Cookie fetchable ###
- App - **[XSS1.1_reflected-ServerXSS-CookieHTTPOnlyFalse](XSS1.1_reflected-ServerXSS-CookieHTTPOnlyFalse)**
- `GET https://127.0.0.1:5000/search` + `app.config['SESSION_COOKIE_HTTPONLY'] = False`
- Default Flask behaviour - **SESSION_COOKIE_HTTPONLY = True**

### SCENARIO 1.2 - Server-side Reflected XSS via GET ###
- Part of BaseApp
- `GET https://127.0.0.1:5000/search`

### SCENARIO 1.3 - Server-side Reflected XSS via POST ###
- Part of BaseApp
- `POST https://127.0.0.1:5000/search`

### SCENARIO 1.4 - Server-side Reflected XSS - 100% Mitigation through Strong CSRF Protection ### 
- App - **[XSS1.4_reflected-ServerXSS-POST-StrongCSRFProtection](XSS1.4_reflected-ServerXSS-POST-StrongCSRFProtection)**
- `POST https://127.0.0.1:5000/search` + + Strong CSRF Protection via Header verification ONLY. No Captcha.

### SCENARIO 2.0 - Server-side Stored XSS ###
- Part of BaseApp
- `POST https://127.0.0.1:5000/feedback` 

### SCENARIO 3.0 - Client-side Reflected XSS via GET (DOM) ###
- Part of BaseApp
- `https://127.0.0.1:5000/color` (in URL element)
- `https://127.0.0.1:5000/quote` (in User input) - NOT PRACTICAL
> HTML5 specifies that a `<script>` tag inserted with innerHTML should not execute. 
- Working Payload - `<img src=x onerror=alert(1)/>`

#### ~~SCENARIO 3.1 - Client-side XSS via POST~~ - IGNORE ###
- App - **[XSS3.1_reflectedDOM-ClientXSS-POST](XSS3.1_reflectedDOM-ClientXSS-POST)**
- Might not be practically possible. Both by design, and for exploitation.

### SCENARIO 4.0 - Client-side Stored XSS (DOM) ###
- Part of BaseApp
- `https://127.0.0.1:5000/post` (in DB)
- `https://127.0.0.1:5000/notes` (in Local Storage) - NOT PRACTICAL
> HTML5 specifies that a `<script>` tag inserted with innerHTML should not execute. 
- Working Payload - `<img src=x onerror=alert(1)/>`

- - -
## DOMPurify
### SCENARIO 5.0 ###
- - App - **[XSS5.0_BaseApp_withDOMPurify](XSS5.0_BaseApp_withDOMPurify)**.
- ONLY FOR `/post` ENDPOINT implemented here.
- CSP switched off
```js
// In JS file
 DOMPurify.sanitize(htmlinput, {
   USE_PROFILES: {html: true},            // default safe html profile
   ALLOWED_TAGS: ['b','i','em','strong','a','p','ul','li'],
   ALLOWED_ATTR: ['href','title']         // allow only safe attrs
 });
```
#### EXPLOIT CODE -
1. Simple img src payload: `<img src=x onerror=alert(1)>`
2. mXSS (mutation XSS) - Try nested tags: `<noscript><p title="</noscript><img src=x onerror=alert(1)>">`
3. Case sensitivity bypass: `<ImG sRc=x oNeRRoR=alert(1)>`
4. Namespace confusion: `<svg><script>alert(1)</script></svg>`

- - -
## Content Security Policy (CSP)
### SCENARIO 6.0 - Weak CSP ###
- App - **[XSS6.0_BaseApp_withWeakCSP](XSS6.0_BaseApp_withWeakCSP)**.
- Server and DOM Functionalities are working!
- **All vulnerabilities are back now - Both Server + DOM XSS**
```python
response.headers['Content-Security-Policy'] = (
            "default-src 'self';"
            "object-src 'none';"
            "base-uri 'none';"
            "frame-ancestors 'none';"
            "script-src 'self' 'unsafe-inline';"
            "style-src 'self' 'unsafe-inline';"
        )
```

### SCENARIO 6.1 - Strict CSP (non-functional DOM) ###
- App - **[XSS6.1_BaseApp_withStrongCSP-blockALLXSS_nonFunctionalDOM](XSS6.1_BaseApp_withStrongCSP-blockALLXSS_nonFunctionalDOM)**.
- Default/Standard CSP, every payload blocked, Web UI works as expected.
- Server functionalities are working! **DOM is broken.**
```python
 response.headers['Content-Security-Policy'] = (
         "default-src 'none';"
         "object-src 'none';"
         "base-uri 'none';"
         "frame-ancestors 'none';"
         "style-src 'self' 'unsafe-inline';"
     )
```
- \+ `"default-src 'self';"`
- Same outcome as above

- \+ `"script-src 'self';"`
- Same outcome as above


### SCENARIO 7.0 - Very Strict CSP with Hash (non-functional DOM) ###
- App - **[XSS7.0_BaseApp_withStrongCSP-hash_staticScripts_nonFunctionalDOM](XSS7.0_BaseApp_withStrongCSP-hash_staticScripts_nonFunctionalDOM)**.
- Hash-based CSP implementation - STATIC SCRIPTS only
- Server functionalities are working! **DOM is broken.**
- No XSS will work here. Not even DOM is functional because no inline scripts allowed except the one with the correct hash.
- **Real-world scenario:** Static websites.

```python
response.headers['Content-Security-Policy'] = (
            "default-src 'self';"
            "object-src 'none';"
            "base-uri 'none';"
            "frame-ancestors 'none';"
            f"script-src 'sha256-{ALLOWED_INLINE_HASH}' 'sha256-{ALLOWED_RESET_HASH}'; "
            "style-src 'self' 'unsafe-inline';"
        )
```

### SCENARIO 7.1 - Weak CSP with Static Nonce ###
- App - **[XSS7.1_BaseApp_withWeakCSP_staticNonce](XSS7.1_BaseApp_withWeakCSP_staticNonce)**.
- Application uses static nonce - VULNERABLE
- **Real world scenario:** An attacker manages to inject a script tag with the known static nonce into a vulnerable input field, allowing the script to execute despite the CSP.
#### Exploit
- `<script nonce="{static_NONCE}">alert(1)</script>`

```python
response.headers['Content-Security-Policy'] = (
            "default-src 'self';"
            "object-src 'none';"
            "base-uri 'none';"
            "frame-ancestors 'none';"
            f"script-src 'self' 'nonce-{static_NONCE}' strict-dynamic;"
            "style-src 'self' 'unsafe-inline';"
        )
```


### SCENARIO 7.2 - Strict CSP with Dynamic Nonce - 100% MITIGATION ###
- App - **[XSS7.2_BaseApp_withStrongCSP-viaDynamicNonce-FunctionalApp](XSS7.2_BaseApp_withStrongCSP-viaDynamicNonce-FunctionalApp)**.
- Start relaxing above CSP header via dynamic nonce to make app's DOM functional and mitigated XSS.
- **NO XSS PAYLOADS WORK!** Complete application is functioning as expected.
```python
response.headers['Content-Security-Policy'] = (
        "default-src 'self';"
        "object-src 'none';"
        "base-uri 'none';"
        "frame-ancestors 'none';"
        f"script-src 'self' 'nonce-{dynamicNONCE}' 'strict-dynamic';"
        "style-src 'self' 'unsafe-inline';"
    )
```

#### ~~SCENARIO 7.3 - Weak CSP with Nonce (allow DOM XSS Only)~~ - IGNORE ###
- App - **[XSS7.3_BaseApp_withWeakCSP-withNonce_allowDOMXSSOnly](XSS7.3_BaseApp_withWeakCSP-withNonce_allowDOMXSSOnly)**.
- INCOMPLETE CODE. Not able to get it working as expected!! Later...
```python
response.headers['Content-Security-Policy'] = (
                "default-src 'self';"
                "object-src 'none';"
                "base-uri 'none';"
                "frame-ancestors 'none';"
                "script-src 'self' 'unsafe-inline' 'unsafe-eval';" 
                #^^ becomes vulnerable now, but how is this different from 6.0
                "style-src 'self' 'unsafe-inline';"
            )
```
- - -

### SCENARIO 8.0 - Framework-level 100% mitigation ###
- App - **[XSS8.0_BaseApp_FrameworkMitigation](XSS8.0_BaseApp_FrameworkMitigation)**.
- **Default behaviour in any Flask app.**
- `|safe` in HTML files not present - Context based output encoding applied.
- Can this be bypassed?

- - -

### Additional Credits 
@grey.shell

### References
https://helloflask.com/en/ <br>
https://github.com/patrickloeber/flask-todo  <br>
https://github.com/XD-DENG/flask-example?tab=readme-ov-file  <br>
https://github.com/pallets/flask/tree/main/examples/tutorial/flaskr Blog <br>
 <br>
https://github.com/we45/Vulnerable-Flask-App  SQLAlchemy <br>
https://github.com/videvelopers/Vulnerable-Flask-App/blob/main/vulnerable-flask-app-linux.py Only API <br>
https://github.com/guiadeappsec/vuln-flask-web-app GOOD <br>
https://dev.to/snyk/how-to-secure-python-flask-applications-2156  <br>
