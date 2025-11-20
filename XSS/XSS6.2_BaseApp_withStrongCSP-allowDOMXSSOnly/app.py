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
import time
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_COOKIE_SECURE'] = True       # Only send over HTTPS
#app.config['SESSION_COOKIE_HTTPONLY'] = False     # JavaScript can access cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'None'    # None, Lax, Strict

DB_PATH = "database.db"

def generate_nonce():
    return secrets.token_urlsafe(16)

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

@app.route("/feedback", methods=["GET","POST"])
def feedback():
    if not session.get("username"):
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        if "delete_id" in request.form:
            fid = request.form.get("delete_id")
            conn.execute("DELETE FROM feedbacks WHERE id=?", (fid,))
        else:
            content = request.form.get("content","")
            conn.execute("INSERT INTO feedbacks (author, content) VALUES (?,?)",
                         (session.get("username"), content))
        conn.commit()
        conn.close()
        # ✅ Always redirect after POST to avoid duplicate/strange UI
        return redirect(url_for("feedback"))

    cur = conn.execute("SELECT * FROM feedbacks ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("feedback.html", items=rows, username=session['username'])

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

# ✅ https://github.com/deepmarketer666/DOM-XSS
# ✅ https://portswigger.net/web-security/cross-site-scripting/dom-based/lab-dom-xss-reflected
@app.route("/quote")
def quote():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("quote.html")

# ✅ Reflected DOM-XSS Via URL fragment
@app.route("/color")
def color():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("color.html")



# https://portswigger.net/web-security/cross-site-scripting/dom-based/lab-dom-xss-stored
@app.route("/notes")
def notes():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("notes.html")


## ✅ Stored DOM-XSS
#    This gets stored in DB, but fetched and appended by Javascript.
@app.route('/comments', methods=['GET'])
def get_comments():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    post_id = request.args.get('post_id', 'demo')
    conn = get_db()
    rows = conn.execute(
        "SELECT id, post_id, author, body, created_at FROM comments WHERE post_id=? ORDER BY id ASC",
        (post_id,)
    ).fetchall()
    conn.close()
    comments = [{"id": r["id"], "post_id": r["post_id"], "author": r["author"],
                 "body": r["body"], "date": r["created_at"]} for r in rows]
    return jsonify(comments)

@app.route('/post/comment', methods=['POST'])
def post_comment():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    post_id = request.form.get('postId', 'demo')
    author = request.form.get('name', '')
    body = request.form.get('comment', '')
    ts = int(time.time() * 1000)
    conn = get_db()
    conn.execute("INSERT INTO comments (post_id, author, body, created_at) VALUES (?,?,?,?)",
                 (post_id, author, body, ts))
    conn.commit(); conn.close()
    return redirect(url_for('post', post_id=post_id))

@app.route('/post')
def post():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    post_id = request.args.get('post_id', request.args.get('postId', 'demo'))
    return render_template('post.html', post_id=post_id)


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

#set CSP header globally after every request
@app.after_request
def add_csp_headers(response):
    nonce = g.get("csp_nonce", "")
    response.headers['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic';"
                    "object-src 'none'; "
                    "base-uri 'none'; "
                    "frame-ancestors 'none'; "
                    "style-src 'self' 'unsafe-inline';"
                )
    return response

@app.before_request
def set_nonce():
    g.csp_nonce = generate_nonce()

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", ssl_context=('../cert.pem', '../key.pem'), debug=True)



# Mention real-world attack scenarios for each case + exploit code + Mitigation

### Scenario 6.2 ###
# DOM XSS via eval (no unsafe-inline needed)
#     response.headers['Content-Security-Policy'] = (
#                     "default-src 'self';"
#                     "object-src 'none';"
#                     "base-uri 'none';"
#                     "frame-ancestors 'none';"
#                     "script-src 'self' 'unsafe-inline' 'unsafe-eval';"
#                     "style-src 'self' 'unsafe-inline';"
#                 )


# "script-src 'self' 'unsafe-inline'" --> IS BLOCKING THE EVAL-BASED XSS ATTACKS.
# We need to add 'unsafe-eval' to allow eval() and similar (new Function, etc.) inside trusted scripts via 'unsafe-eval'.