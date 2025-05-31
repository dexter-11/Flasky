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

- - -
## INDEX

### 1. CSRF

### 2. SSRF + XXE


- - -

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
