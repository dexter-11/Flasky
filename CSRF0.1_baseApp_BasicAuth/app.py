from flask import Flask, render_template, request, Response, redirect, url_for, flash, render_template_string, jsonify
import sqlite3
import os
from base64 import b64decode

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

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

    # Insert dummy books only if the table is empty
    existing_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_users == 0:
        _users = [
            ("admin", "secret", "NYC"),
            ("user", "password", "JPR")
        ]
        c.executemany("INSERT INTO users (username, password, city) VALUES (?, ?, ?)", _users)

    #print("Database initialized with users and books tables.")
    conn.commit()
    conn.close()

# Check Auth
def check_auth(username, password):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return True if user else False

def authenticate():
    return Response(
        'Could not verify your login.\n'
        'You must provide valid credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_basic_auth(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Basic "):
            return authenticate()
        try:
            decoded = b64decode(auth.split(" ")[1]).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return authenticate()
        if not check_auth(username, password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Update the city
def update_city(city, username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET city = ? WHERE username = ?", (city, username))
    conn.commit()
    conn.close()

# Update the city
def fetch_city(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    city = c.execute("SELECT city FROM users WHERE username = ?", (username,)).fetchone()
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

# Routes
@app.route('/', methods=['GET', 'PUT', 'POST'])
def home():
    return render_template('home.html')


@app.route('/dashboard', methods=['GET','POST'])
@requires_basic_auth
def dashboard():
    auth = request.headers.get("Authorization")
    decoded = b64decode(auth.split(" ")[1]).decode("utf-8")
    username, password = decoded.split(":", 1)
    city = fetch_city(username)[0]
    return render_template('dashboard.html', username=username, city=city)


@app.route('/search', methods=['GET','POST'])
@requires_basic_auth
def search():
    auth = request.headers.get("Authorization")
    decoded = b64decode(auth.split(" ")[1]).decode("utf-8")
    username, password = decoded.split(":", 1)
    search_term = request.form['search']
    books = []
    if search_term:
        books = search_books(search_term)
    city = fetch_city(username)[0]
    return render_template('dashboard.html', username=username, city=city, books=books, show_section='search', search_term=search_term)


@app.route('/update', methods=['POST'])
@requires_basic_auth
def update():
    auth = request.headers.get("Authorization")
    decoded = b64decode(auth.split(" ")[1]).decode("utf-8")
    username, password = decoded.split(":", 1)
    new_city = request.form['city']
    update_city(new_city, username)
    return redirect(url_for('dashboard'))


@app.route("/logout")
def logout():
    # Send 401 with WWW-Authenticate to prompt re-login or stop sending credentials
    return Response("Navigate to / or /dashboard to LOGIN again! Dont try to login here, it'll keep logging you out :)", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


if __name__ == '__main__':
    init_db()
    app.run(ssl_context=('../cert.pem', '../key.pem'), debug=True)

# Vanilla CSRF works here since browser knows Basic Auth