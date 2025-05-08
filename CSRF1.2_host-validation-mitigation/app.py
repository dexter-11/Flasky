from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string, make_response, jsonify
import sqlite3
import os
import re

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

# Host Validation
def check_referer():
    host = request.headers.get("Host").split(":")[0]    #removing the port from host
    #origin = request.headers.get("Origin")
    # Whoever tries to do CSRF (POST request using Javascript), Origin header comes up
    #if origin:
    #    check_host = origin
    #else:
    #In this case, Origin headers is always coming up so discarded above logic.
    referer = request.headers.get("Referer")
    # Escape host to safely use in regex (in case of dots etc.)
    #pattern = f"^https?://{re.escape(host)}"
    if referer and re.match(f"^.*{re.escape(host)}.*$", referer):
        return True
    else:
        response = make_response("""
                <script>
                    alert("Invalid referrer detected!");
                    window.location.href = "/";
                </script>
            """)
        return response


## Routes
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

    referer_check = check_referer()
    if referer_check is not True:
        return referer_check
    search_term = request.form['search']
    books = []
    if search_term:
        books = search_books(search_term)
    city = fetch_city(session['user_id'])[0]
    return render_template('dashboard.html', username=session['username'], city=city, books=books, show_section='search', search_term=search_term)


@app.route('/update', methods=['POST'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    referer_check = check_referer()
    if referer_check is not True:
        return referer_check
    new_city = request.form['city']
    update_city(new_city, session['user_id'])
    return redirect(url_for('dashboard'))

@app.route('/delete', methods=['PUT'])
def delete():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    referer_check = check_referer()
    if referer_check is not True:
        return referer_check
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

# @app.after_request
# def set_referrer_policy(response):
#     response.headers['Referrer-Policy'] = 'unsafe-url'
#     return response

if __name__ == '__main__':
    init_db()
    app.run(ssl_context=('../cert.pem', '../key.pem'), debug=True)
    #Needed to add since when we tried exploiting from Cloud, due to this being a Cross-Origin request, the cookie was dropped.
    # To set SameSite=None for session cookies in your Flask app, you can configure it using Flask’s SESSION_COOKIE_SAMESITE setting in app.config.
    # You also must set SESSION_COOKIE_SECURE = True when using SameSite=None, otherwise browsers will block the cookie.


# We can generate a Referer header by Clicking a link or Submitting a form or Script-based navigation or embedded content.
# <a href="https://target.com/page">Go</a>
# window.location.href = "https://target.com/page";
# <img src="https://target.com/track.png">
# https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Cross-Site%20Request%20Forgery

# Here to bypass the regex, our filename or directory or a subdomain should match the hostname. TO VERIFY!

# referer header is not showing filename or directory, just the host
# That's expected behavior in many modern browsers due to privacy-focused defaults for the Referer header. If you're seeing only the origin (like http://127.0.0.1:5000) instead of the full URL (like http://127.0.0.1:5000/dashboard), it’s because the browser is intentionally stripping the path and query parameters.
# 🔍 Why this happens:
# Most browsers now default to: `Referrer-Policy: strict-origin-when-cross-origin`
# Under this policy:
# - Same-origin requests → send the full URL.
# - Cross-origin requests → send only the origin.
# But even for same-origin requests, if HTTPS is not used or the policy is explicitly set to something stricter, only the origin may be sent.


#Browser drops the Referer full URL.
#You're correct — and this behavior is influenced by browser security models, not just the server-side headers.
#Even if you explicitly set a permissive Referrer-Policy like no-referrer-when-downgrade or unsafe-url from your Flask server, the browser ultimately decides what to send in the Referer header,

# Only vulnerable on the subdomain context, if we're able to match the regex.
# Mitigation - Origin check with host - strong regex