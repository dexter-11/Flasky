from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# In-memory user storage (for demonstration purposes)
users = {}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists!')
            return redirect(url_for('register'))

        users[username] = generate_password_hash(password)
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_password_hash = users.get(username)
        if user_password_hash and check_password_hash(user_password_hash, password):
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to log in first!')
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])


@app.route('/delete', methods=['POST'])
def delete_account():
    if 'username' in session:
        del users[session['username']]
        session.pop('username', None)
        flash('Account deleted successfully!')
    else:
        flash('You need to log in first!')

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out!')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
