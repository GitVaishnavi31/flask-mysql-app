import os
from flask import Flask, render_template, request, redirect, flash, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MySQL configuration
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
app.secret_key = os.environ.get("SECRET_KEY")

mysql = MySQL(app)

# Home route
@app.route('/')
def home():
    return redirect('/login')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):  # user[2] is password column
            session['username'] = user[1]  # username
            session['role'] = user[3]      # role
            flash("Login successful!")

            if user[3] == 'admin':
                return redirect('/dashboard')
            elif user[3] == 'engineer':
                return redirect('/form')
        else:
            flash("Invalid username or password.")
            return redirect('/login')

    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'engineer'  # fixed role for all registered users

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Username already exists.")
            cur.close()
            return redirect('/register')

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    (username, hashed_password, role))
        mysql.connection.commit()
        cur.close()

        flash("Registration successful! Please log in.")
        return redirect('/login')

    return render_template('register.html')

# Admin dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session and session.get('role') == 'admin':
        return render_template('dashboard.html', username=session['username'])
    else:
        flash("Access denied. Admins only.")
        return redirect('/login')

# Engineer job form
@app.route('/form', methods=['GET', 'POST'])
def form_page():
    if 'username' in session and session.get('role') == 'engineer':
        if request.method == 'POST':
            job_id = request.form['job_id']
            job_no = request.form['job_no']
            client_name = request.form['client_name']
            end_client_name = request.form['end_client_name']
            sales_engineer = request.form['sales_engineer']

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO jobs (job_id, job_no, client_name, end_client_name, sales_engineer)
                VALUES (%s, %s, %s, %s, %s)
            """, (job_id, job_no, client_name, end_client_name, sales_engineer))
            mysql.connection.commit()
            cur.close()

            flash("Job submitted successfully!")
            return redirect('/form')

        return render_template('form.html', username=session['username'])
    else:
        flash("Access denied. Engineers only.")
        return redirect('/login')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.")
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
