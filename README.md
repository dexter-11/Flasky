# Flasky
Sample Flask application to practice different types of web vulnerabilities by both black-box and white-box testing methodologies.

Note - Tested with Python 3.8.10 & 3.13.1

```bash
git clone https://github.com/dexter-11/Flasky.git
cd flasky
python3 -m venv flask-venv
source flask-venv/bin/activate #OR powershell -noexit -ep bypass -File .\flasky-venv\Scripts\Activate.ps1
pip3 install -r requirements.txt

python3 app.py
```

Trying to host on https://www.pythonanywhere.com/user/dexter0/

LIVE Link - https://dexter0.pythonanywhere.com/


While registering ask Gender and will change using CSRF. <-- MAKE THIS HOME CODE
Will make branches for different type of code changes.
POST -> Updating the gender after login
