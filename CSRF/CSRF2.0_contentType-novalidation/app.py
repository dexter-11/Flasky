from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string, jsonify
import sqlite3
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

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
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
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


@app.route('/search', methods=['GET','POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_term = request.form['search']
    books = []
    if search_term:
        books = search_books(search_term)
    city = fetch_city(session['user_id'])[0]
    return render_template('dashboard.html', username=session['username'], city=city, books=books, show_section='search', search_term=search_term)
    # https://github.com/greyshell/sqli_lab/blob/main/flask_app/app.py#L213


@app.route('/update', methods=['POST'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    data = json.loads(request.data)     #request.get_json() is triggering Flask's built-in request validation
    #we manually decoded the POST body as JSON
    if not data or 'city' not in data:
        return jsonify({"error": "Invalid request"}), 400
    new_city = data['city']
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

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    init_db()
    app.run(ssl_context=('../cert.pem', '../key.pem'), debug=True)