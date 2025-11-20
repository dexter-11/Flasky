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
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
import sqlite3
import os
import hashlib, base64

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_COOKIE_SECURE'] = True       # Only send over HTTPS
#app.config['SESSION_COOKIE_HTTPONLY'] = False     # JavaScript can access cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'None'    # None, Lax, Strict

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
            return redirect(url_for("home"))
        else:
            return redirect(url_for("login", error=f"Username {u} is incorrect."))
    # ✅ Login page XSS when username is incorrect - give error with reflected XSS
    #       See if it redirects or actually triggers XSS if payload sent to a user who is already logged in - DOESN'T TRIGGER!
    error = request.args.get("error")
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ✅ Two cases - GET and POST
@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    search_term = None
    method_used = None

    if request.method == "POST":
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


# ✅ Reflected DOM-XSS Via URL fragment
@app.route("/color")
def color():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("color.html")


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

# The single allowed inline script content (exact bytes matter)
# Keep this string identical to the inline <script> content in the template below.
ALLOWED_INLINE_SCRIPT = "confirm('Allowed script running here! Cannot XSS');"
ALLOWED_RESET_SCRIPT = """
      localStorage.clear();
      sessionStorage.clear();
      alert("App has been reset. Local & Session storage cleared.");
      window.location = "/";
    """

def sha256_b64(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode('utf-8'))
    return base64.b64encode(h.digest()).decode('ascii')

ALLOWED_INLINE_HASH = sha256_b64(ALLOWED_INLINE_SCRIPT)  # computed once on startup
ALLOWED_RESET_HASH = sha256_b64(ALLOWED_RESET_SCRIPT)  # computed once on startup

@app.before_request
def attach_hash():
    # make the hash available to templates
    g.allowed_script_hash = ALLOWED_INLINE_HASH
    g.allowed_script_hash = ALLOWED_RESET_HASH

#set CSP header globally after every request
@app.after_request
def add_csp_headers(response):
    response.headers['Content-Security-Policy'] = (
            "default-src 'self';"
            "object-src 'none';"
            "base-uri 'none';"
            "frame-ancestors 'none';"
            f"script-src 'sha256-{ALLOWED_INLINE_HASH}' 'sha256-{ALLOWED_RESET_HASH}'; "
            "style-src 'self' 'unsafe-inline';"
        )
    return response

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", ssl_context=('../cert.pem', '../key.pem'), debug=True)


### SCENARIO 7.0 ###
# Hash-based CSP implementation - STATIC SCRIPTS only
# No XSS will work here. Not even DOM is functional because no inline scripts allowed except the one with the correct hash.
# Real-world scenario: Static websites.
