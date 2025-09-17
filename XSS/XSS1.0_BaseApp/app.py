"""
Flask XSS Practice App (intentionally vulnerable)
-------------------------------------------------
Run locally ONLY. Do not deploy. This app contains stored and reflected XSS sinks
for learning purposes.

Then open: http://127.0.0.1:5000/
Login:

Uses template files under ./templates directory.
"""
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

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
            return redirect(url_for("feedback"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# this also gets stored in DB, but if fetched and appended by Javascript, not directly. Look into this.
# Think of attack scenarios while creating
#move behind auth
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

#Two separate cases - GET and POST
@app.route('/search', methods=['GET'])
def search():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    search_term = request.args.get("q")
    books, q_provided = None, False
    if search_term is not None:
        q_provided = True
        conn = get_db()
        books = conn.execute(
            "SELECT * FROM books WHERE name LIKE ? OR author LIKE ?",
            (f'%{search_term}%', f'%{search_term}%')
        ).fetchall()
        conn.commit()
        conn.close()
    return render_template("search.html", username=session['username'], results=books, q=search_term, q_provided=q_provided)

@app.route('/search-form', methods=['POST'])
def search():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    search_term = request.form.get("q")
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
    return render_template("search-form.html", username=session['username'], results=books, q=search_term, q_provided=q_provided)

#URL se uthake DOM pe jana hai something like #abc or location
#2 scenarios - GET and POST
# https://github.com/deepmarketer666/DOM-XSS
#PortSwigger Academy - https://portswigger.net/web-security/all-labs#cross-site-scripting
# https://portswigger.net/web-security/cross-site-scripting/dom-based/lab-dom-xss-reflected
# https://portswigger.net/web-security/cross-site-scripting/dom-based/lab-dom-xss-stored
@app.route("/quote")
def quote():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("quote.html")

@app.route("/notes")
def notes():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("notes.html")

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


##Keep outside auth below:
#Login page XSS when username is incorrect - give error with reflected XSS
#Server side Reflected XSS
#we need to see if it redirects or actually triggers XSS if payload sent to a user who is already logged in.