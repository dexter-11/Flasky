"""
Flask XSS Practice App (intentionally vulnerable)
-------------------------------------------------
Run locally ONLY. Do not deploy. This app contains stored and reflected XSS sinks
for learning purposes.
PortSwigger Academy - https://portswigger.net/web-security/all-labs#cross-site-scripting

Then open: http://127.0.0.1:5000/
Login:

Uses template files under ./templates directory.
"""
from flask import Flask, render_template, request, redirect, url_for, session, make_response, current_app
import sqlite3
import os
import secrets
import hmac
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
#CORS(app,
#      origins=["*"],
#      methods=["POST", "PUT", "DELETE", "OPTIONS"],
#      allow_headers=["Content-Type", "X-CSRF-Header"],
#      supports_credentials=True,
#      max_age=240
# )

DB_PATH = "database.db"

# ---------- DB helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS users')
    cur.execute('DROP TABLE IF EXISTS feedbacks')
    cur.execute('DROP TABLE IF EXISTS books')
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )''')
    cur.execute('''
          CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            author TEXT,
            body TEXT,
            created_at INTEGER
          )
          ''')
    cur.execute("CREATE TABLE IF NOT EXISTS feedbacks (id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT, content TEXT)")
    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", ("admin", "password"))

    # Insert dummy books only if the table is empty
    existing_books = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
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
        cur.executemany("INSERT INTO books (name, author, year) VALUES (?, ?, ?)", dummy_books)

    conn.commit()
    conn.close()

def generate_csrf_token(signed_session):
    token = secrets.token_urlsafe(16)
    message = f"{len(signed_session)}!{signed_session}!{len(token)}!{token}"
    digest = hmac.new(app.secret_key, message.encode(), hashlib.sha256).hexdigest()
    #print("GEN: digest:", repr(digest))
    csrf_token = f"{digest}.{token}"
    return csrf_token

def verify_csrf_token(csrf_token, signed_session):
    digest, random_token = csrf_token.split(".")
    reconstruct_message = f"{len(signed_session)}!{signed_session}!{len(random_token)}!{random_token}"
    reconstruct_digest = hmac.new(app.secret_key, reconstruct_message.encode(), hashlib.sha256).hexdigest()
    #print("VERIFY: digest:", repr(reconstruct_digest))
    if hmac.compare_digest(digest, reconstruct_digest):
        return True
    else:
        return False

# Validate CSRF token from Cookie and Header
def validate_CSRF():
    csrf_cookie = request.cookies.get("__Host-csrf_token")
    csrf_form = request.headers.get("X-CSRF-Header")
    signed_session = request.cookies.get("session")

    # debug prints (temporary)
    #print("SERVER: __Host-csrf_token cookie:", repr(csrf_cookie))
    #print("SERVER: X-CSRF-Header header:", repr(csrf_form))
    #print("SERVER: signed_session from cookie:", repr(signed_session))

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


# ---------- Routes ----------
@app.route('/', methods=['GET', 'PUT', 'POST'])
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)", (u,p))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists")
    return render_template("register.html", error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("username"):
        return redirect(url_for("home"))

    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        conn = get_db()
        cur = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        row = cur.fetchone()
        conn.close()
        if row:
            session['user_id'] = row[0]
            session['username'] = row[1]

            # Get a serializer to sign the session cookie. The Session cookie is not available from requests yet!
            serializer = current_app.session_interface.get_signing_serializer(current_app)
            if not serializer:
                raise RuntimeError("Could not get session serializer")
            signed_session = serializer.dumps(dict(session))
            #print("Session Gen:", repr(signed_session))

            # Set CSRF cookie
            response = make_response(redirect(url_for('home')))
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
            return redirect(url_for("login", error=f"Username {u} is incorrect."))

    error = request.args.get("error")
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


#@app.route("/feedback", methods=["GET","POST"])


# ✅ Two cases - GET and POST
@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    search_term = None
    method_used = None

    if request.method == "POST":
        validate_csrf = validate_CSRF()
        #print(validate_csrf)
        if validate_csrf is not True:
            return validate_csrf
        search_term = request.form.get("q_post")
        method_used = "POST"
    elif request.method == "GET":
        search_term = request.args.get("q_get")
        method_used = "GET"

    books, q_provided = None, False
    if search_term:
        q_provided = True
        conn = get_db()
        books = conn.execute(
            "SELECT * FROM books WHERE name LIKE ? OR author LIKE ?",
            (f'%{search_term}%', f'%{search_term}%')
        ).fetchall()
        conn.commit()
        conn.close()

    return render_template(
        "search.html",
        username=session['username'],
        results=books,
        q=search_term,
        q_provided=q_provided,
        method_used=method_used
    )


#@app.route("/quote")

#@app.route("/color")

#@app.route("/notes")

#@app.route('/comments', methods=['GET'])

#@app.route('/post/comment', methods=['POST'])

#@app.route('/post')


@app.route("/reset", methods=["POST"])
def reset():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    session.clear()
    return """
    <script>
      localStorage.clear();
      sessionStorage.clear();
      alert("App has been reset. Local & Session storage cleared.");
      window.location = "/";
    </script>
    """

if __name__ == '__main__':
    init_db()
    app.run(ssl_context=('../cert.pem', '../key.pem'), debug=True)


# Mention real-world attack scenarios for each case + exploit code + Mitigation

### SCENARIO 1.4 ###
#   POST https://127.0.0.1:5000/search + Strong CSRF Protection via Header verification ONLY. No Captcha.
