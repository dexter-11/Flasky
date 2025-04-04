from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string, jsonify
import sqlite3
import os
import re
from db_setup import init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

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


@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    # for POST method request.forms['search']
    # for GET method request.args.get('search', '')
    search_term = request.args.get('search', '')
    books = []
    if search_term:
        books = search_books(search_term)
    city = fetch_city(session['user_id'])[0]
    return render_template('dashboard.html', username=session['username'], city=city, books=books, show_section='search', search_term=search_term)


@app.route('/update', methods=['POST'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
    app.run(debug=True)