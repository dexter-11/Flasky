from flask import Flask, make_response, render_template, request, redirect, url_for, session, flash, \
    jsonify, current_app
import sqlite3
import os
import secrets
#from flask_cors import CORS
import hmac
import hashlib
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
RECAPTCHA_SECRET = '6LdLZjcrAAAAANLRAmZBdM6K_nGPYJeELPWKT9QR'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
# CORS(app,
#      origins=["*"],
#      methods=["POST", "PUT", "DELETE", "OPTIONS"],
#      allow_headers=["Content-Type", "X-CSRF-Header"],
#      supports_credentials=True,
#      max_age=240
# )


# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    city TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )''')

    # Insert dummy books only if the table is empty
    existing_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if existing_books == 0:
        dummy_books = [
            ("The Great Gatsby", "F. Scott Fitzgerald", 1925),
            ("To Kill a Mockingbird", "Harper Lee", 1960),
            ("1984", "George Orwell", 1949),
            ("Pride and Prejudice", "Jane Austen", 1813),
            ("The Catcher in the Rye", "J.D. Salinger", 1951),
            ("Moby-Dick", "Herman Melville", 1851),
            ("War and Peace", "Leo Tolstoy", 1869),
            ("The Hobbit", "J.R.R. Tolkien", 1937),
            ("Crime and Punishment", "Fyodor Dostoevsky", 1866),
            ("Brave New World", "Aldous Huxley", 1932)
        ]

        c.executemany("INSERT INTO books (name, author, year) VALUES (?, ?, ?)", dummy_books)

    #print("Database initialized with users and books tables.")
    conn.commit()
    conn.close()

def generate_csrf_token(signed_session):
    token = secrets.token_urlsafe(16)
    message = f"{len(signed_session)}!{signed_session}!{len(token)}!{token}"
    digest = hmac.new(app.secret_key, message.encode(), hashlib.sha256).hexdigest()
    csrf_token = f"{digest}.{token}"
    return csrf_token

def verify_csrf_token(csrf_token, signed_session):
    digest, random_token = csrf_token.split(".")
    reconstruct_message = f"{len(signed_session)}!{signed_session}!{len(random_token)}!{random_token}"
    reconstruct_digest = hmac.new(app.secret_key, reconstruct_message.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(digest, reconstruct_digest):
        return True
    else:
        return False
    # # Insecure XOR comparison - Check?
    # if len(digest) != len(reconstruct_digest):
    #     return False
    #
    # result = 0
    # for a, b in zip(digest, reconstruct_digest):
    #     result |= ord(a) ^ ord(b)
    #
    # if result == 0:
    #     return True
    # else:
    #     return False


# User authentication
def authenticate_user(username, password):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# Add a new user
def add_user(username, password, city):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, city) VALUES (?, ?, ?)", (username, password, city))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Delete a user
def delete_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# Update the city
def update_city(city, user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET city = ? WHERE id = ?", (city, user_id))
    conn.commit()
    conn.close()

# Update the city
def fetch_city(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    city = c.execute("SELECT city FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return city

# Search books
def search_books(search_term):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    books = c.execute(
            "SELECT * FROM books WHERE name LIKE ? OR author LIKE ?",
            (f'%{search_term}%', f'%{search_term}%')
        ).fetchall()
    conn.commit()
    conn.close()
    return books

# Validate CSRF token from Cookie and Header
def validate_CSRF():
    csrf_cookie = request.cookies.get("__Host-csrf_token")
    csrf_form = request.headers.get("X-CSRF-Header")
    signed_session = request.cookies.get("session")
    if csrf_cookie == csrf_form :
        if verify_csrf_token(csrf_cookie, signed_session):
            return True
        else:
            response = make_response("""
                            <script>
                                alert("reCAPTCHA validation failure!");
                                window.location.href = "/";
                            </script>
                        """)
            return response
    else:
        response = make_response("""
                <script>
                    alert("CSRF Token Mismatch!");
                    window.location.href = "/";
                </script>
            """)
        return response

# Validate reCAPTCHA token
def validate_reCAPTCHA():
    recaptcha_token = request.form['g-recaptcha-response']
    if recaptcha_token:
        # Verify the token with Google
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': RECAPTCHA_SECRET,
            'response': recaptcha_token
        })
        result = response.json()
        if result.get('success'):
            return True
        else:
            response = make_response("""
                            <script>
                                alert("reCAPTCHA validation failure!");
                                window.location.href = "/";
                            </script>
                        """)
            return response
    else:
        response = make_response("""
                <script>
                    alert("reCAPTCHA validation failure!");
                    window.location.href = "/";
                </script>
            """)
        return response

# Routes
@app.route('/', methods=['GET', 'PUT', 'POST'])
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]

            # Get a serializer to sign the session cookie. The Session cookie is not available from requests yet!
            serializer = current_app.session_interface.get_signing_serializer(current_app)
            if not serializer:
                raise RuntimeError("Could not get session serializer")
            signed_session = serializer.dumps(dict(session))

            # Set CSRF cookie
            response = make_response(redirect(url_for('dashboard')))
            # Set CSRF cookie with __Host- prefix
            response.set_cookie(
                "__Host-csrf_token",
                generate_csrf_token(signed_session),
                secure=True,
                samesite="Strict",
                path="/"
            )
            return response
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        city = request.form['city']
        if add_user(username, password, city):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists', 'error')
    return render_template('register.html')

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    city = fetch_city(session['user_id'])[0]
    return render_template('dashboard.html', username=session['username'], city=city)


@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_term = request.args.get('search', '')
    books = []
    if search_term:
        books = search_books(search_term)
    city = fetch_city(session['user_id'])[0]
    # Set CSRF cookie in response
    resp = make_response(render_template('dashboard.html', username=session['username'], city=city, books=books, show_section='search', search_term=search_term))
    return resp


@app.route('/update', methods=['POST'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    validate_csrf = validate_CSRF()
    if validate_csrf is not True:
       return validate_csrf

    validate_recaptcha = validate_reCAPTCHA()
    if validate_recaptcha is not True:
        return validate_recaptcha

    new_city = request.form['city']
    update_city(new_city, session['user_id'])
    return redirect(url_for('dashboard'))


@app.route('/delete', methods=['PUT'])
def delete():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    delete_user(session['user_id'])
    session.clear()
    return jsonify({"message": "Account deleted successfully"}), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/reset_database')
def reset_database():
    os.remove('database.db')
    os.system('touch database.db')
    init_db()
    return redirect(url_for('home', reset_db=1))

if __name__ == '__main__':
    init_db()
    app.run(ssl_context=('../cert.pem', '../key.pem'), debug=True)


# Works only on LOCALHOST & FLASKY.LOCAL.HOST domains because of Captcha registration.

#Even if I turn off CSRF Token verification, ReCAPTCHA is not allowing the CSRF to happen because of g_captcha_response param.