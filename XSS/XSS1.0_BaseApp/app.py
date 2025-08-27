"""
Flask XSS Practice App (intentionally vulnerable)
-------------------------------------------------
Run locally ONLY. Do not deploy. This app contains stored and reflected XSS sinks
for learning purposes.

Then open: http://127.0.0.1:5000/
Login:

Uses template files under ./templates directory.
"""
import sqlite3, os
from flask import Flask, request, redirect, url_for, render_template, session

app = Flask(__name__)
app.secret_key = "dev-not-secret"

DB_PATH = "database.db"

# ---------- DB helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS feedbacks")
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cur.execute("CREATE TABLE feedbacks (id INTEGER PRIMARY KEY, author TEXT, content TEXT)")
    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", ("admin", "password"))
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()

# ---------- Routes ----------
@app.route("/")
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
            session["user"] = u
            return redirect(url_for("feedback"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/feedback", methods=["GET","POST"])
def feedback():
    if not session.get("user"):
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        if "delete_all" in request.form:
            conn.execute("DELETE FROM feedbacks")
        else:
            content = request.form.get("content","")
            conn.execute("INSERT INTO feedbacks (author, content) VALUES (?,?)",
                         (session.get("user"), content))
        conn.commit()

    cur = conn.execute("SELECT * FROM feedbacks ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("feedback.html", items=rows)

@app.route("/search")
def search():
    if not session.get("user"):
        return redirect(url_for("login"))
    q = request.args.get("q")
    results, q_provided = None, False
    if q is not None:
        q_provided = True
        conn = get_db()
        cur = conn.execute(
            "SELECT * FROM (VALUES (?,?,?)) WHERE 1=0", ("","","","")
        ) # placeholder just to keep structure
        conn.close()
        # Hardcoded list remains for simplicity (same as earlier)
        BOOKS = [
            {"title":"The Web Security Handbook","author":"A. Researcher","year":2020},
            {"title":"Flask for Fun and Profit","author":"J. Dev","year":2022},
            {"title":"XSS Payload Alchemy","author":"C. TFer","year":2019},
            {"title":"Bug Hunter's Field Guide","author":"H. Scout","year":2021},
            {"title":"Learn Jinja2 the Hard Way","author":"T. Templater","year":2018}
        ]
        q_lower = q.lower()
        results = [b for b in BOOKS if q_lower in b["title"].lower() or q_lower in b["author"].lower()]
    return render_template("search.html", results=results, q=q, q_provided=q_provided)

@app.route("/reset", methods=["POST"])
def reset():
    init_db()
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
