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
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
#app.config['SESSION_COOKIE_SECURE'] = True       # Only send over HTTPS
#app.config['SESSION_COOKIE_HTTPONLY'] = True     # JavaScript cannot access cookie
#app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # None, Strict

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
    error = request.args.get("error")
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# serve the page
@app.route("/colorture", methods=["GET"])
def colorture():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("colorture.html")

# echo endpoint (POST) - returns JSON echoing back the posted value
@app.route("/api/echo_color", methods=["POST"])
def api_echo_color():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    v = request.form.get("value")
    if v is None:
        js = request.get_json(silent=True) or {}
        v = js.get("value", "")
    return jsonify({"value": v})


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
# Keep reloading in certain periods - Once data is already in API, it should fetch again in the page.
#   Then we will be exploiting the request --> POST /api/echo_color
#   ignore above

### SCENARIO 3.1 ###
# 1. First phish the victim
# 2. Then trigger the JS on Submit button. Check?