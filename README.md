# Flasky
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

Trying to host on https://www.pythonanywhere.com/user/dexter0/ <br>
LIVE Link - https://dexter0.pythonanywhere.com/

## INDEX

##### 0. CSRF_baseApp
- Base app with registration, login, update, search, delete & logout functions.
- Search is vulnerable to basic XSS.
- No CSRF / CORS implementations here.
##### 1. CSRF1.0_host-validation
- Host header validating with Referer header
##### 2. CSRF1.1_synchronizer-token
- Token stored in session
  - Token not being discarded separately right now on Logout.
- Same token attached with POST/PUT requests in form/header pulled from session.
- There shouldn't be any `csrf_token` cookie being passed!
- Validated on submission
- Implemented in update, search, delete functions
##### 3. CSRF2_contentType-validation
- Content Type header being validated
  - `allowed_types = ["application/x-www-form-urlencoded", "multipart/form-data", "application/json"]`
##### 4. CSRF3.0_double-submit-cookie-viaPOSTparam-weaktoken
- CSRF token assigned on Login.
- Javascript auto appends same CSRF token to a form submission.
- Implemented in update, search functions
##### 5. CSRF3.1_doublesubmitcookie-viaPOSTparam-insecureCORS
- Same as CSRF3.0 setup
- Insecure CORS
  - `ACAO: *`
  - `ACAM: PUT, POST, OPTIONS`
  - `ACAH: X-CSRF-Header`
  - `ACAC: true`
  - `ACMA: 240`
##### 6. CSRF3.2_double-submit-cookie-viaHeader-weaktoken
- CSRF token assigned on Login.
- Javascript auto appends same CSRF token to `X-CSRF-Header` on form submission.
- Implemented in update, search functions
##### 7. CSRF3.3_doublesubmitcookie-viaHeader-insecureCORS
- Same as CSRF3.2 setup
- Insecure CORS
  - `ACAO: *`
  - `ACAM: PUT, POST, OPTIONS`
  - `ACAH: X-CSRF-Header`
  - `ACAC: true`
  - `ACMA: 240`
##### 7. CSRF4_doublesubmitcookie-viaHeader-StrongMitigation (In-progress)
- TBD


## Working notes with @grey.shell
- [ ] On Asus, working on `ubuntu-dev` / Windows Pycharm | On PC, working on `kali-pentest`
- [ ] We’ll start tweaking and building on this one by one for different vulnerabilities and its defences.
CSRF, SOP, XSS, CSP
- [ ] Keep SSRF and XXE in another bucket

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
https://skf.gitbook.io/asvs-write-ups/csrf/csrf <br>
