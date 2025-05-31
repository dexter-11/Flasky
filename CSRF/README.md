# CSRF INDEX

### 0. CSRF_baseApp
- Base app with registration, login, update, search, delete & logout functions.
- Search is vulnerable to basic XSS.
- No CSRF / CORS implementations here.
### 1. CSRF1.0_host-validation
- Host header validating with Referer header
### 2. CSRF1.1_synchronizer-token
- Token stored in session
  - Token not being discarded separately right now on Logout.
- Same token attached with POST/PUT requests in form/header pulled from session.
- There shouldn't be any `csrf_token` cookie being passed!
- Validated on submission
- Implemented in update, search, delete functions
### 3. CSRF2_contentType-validation
- Content Type header being validated
  - `allowed_types = ["application/x-www-form-urlencoded", "multipart/form-data", "application/json"]`
### 4. CSRF3.0_double-submit-cookie-viaPOSTparam-weaktoken
- CSRF token assigned on Login.
- Javascript auto appends same CSRF token to a form submission.
- Implemented in update, search functions
### 5. CSRF3.1_doublesubmitcookie-viaPOSTparam-insecureCORS
- Same as CSRF3.0 setup
- Insecure CORS
  - `ACAO: *`
  - `ACAM: PUT, POST, OPTIONS`
  - `ACAH: X-CSRF-Header`
  - `ACAC: true`
  - `ACMA: 240`
### 6. CSRF3.2_double-submit-cookie-viaHeader-weaktoken
- CSRF token assigned on Login.
- Javascript auto appends same CSRF token to `X-CSRF-Header` on form submission.
- Implemented in update, search functions
### 7. CSRF3.3_doublesubmitcookie-viaHeader-insecureCORS
- Same as CSRF3.2 setup
- Insecure CORS
  - `ACAO: *`
  - `ACAM: PUT, POST, OPTIONS`
  - `ACAH: X-CSRF-Header`
  - `ACAC: true`
  - `ACMA: 240`
### 7. CSRF4_doublesubmitcookie-viaHeader-StrongMitigation (In-progress)
- TBD


## Working notes with @grey.shell


### References
https://skf.gitbook.io/asvs-write-ups/csrf/csrf <br>
