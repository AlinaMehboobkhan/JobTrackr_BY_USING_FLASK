import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm, JobForm, AvailableJobForm, EditProfileForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

def get_db_connection():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        flash(f"Database connection error: {e}", 'danger')
        return None


def init_db():
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT NOT NULL,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        job_title TEXT,
                        company TEXT,
                        status TEXT,
                        applied_date TEXT,
                        follow_up_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS available_jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_title TEXT,
                        company TEXT,
                        posted_date TEXT)''')
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db_connection()
    if conn is None:
        return None
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user



# ========================= Routes =========================

@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])
    if not user:
        flash("User not found.", 'danger')
        return redirect(url_for('login'))

    jobs = conn.execute('SELECT * FROM jobs WHERE user_id = ?', (session['user_id'],)).fetchall()
    followups = conn.execute('SELECT * FROM jobs WHERE user_id = ? AND follow_up_date IS NOT NULL ORDER BY follow_up_date',
                             (session['user_id'],)).fetchall()
    available_jobs = conn.execute('SELECT * FROM available_jobs').fetchall()
    conn.close()

    current_user = {
        'username': user['username'],
        'is_admin': user['is_admin']
    }

    return render_template('dashboard.html', jobs=jobs, followups=followups, available_jobs=available_jobs, current_user=current_user)
@app.route('/jobs')
def job_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('job_list.html', jobs=jobs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(
        username=request.form.get('username', ''),
        email=request.form.get('email', ''),
        password=request.form.get('password', ''),
        confirm_password=request.form.get('confirm_password', '')
    )
    if request.method == 'POST':
        if form.validate():
            conn = get_db_connection()
            if conn is None:
                return redirect(url_for('login'))
            hashed_pw = generate_password_hash(form.password)
            try:
                conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                             (form.username, form.email, hashed_pw))
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists.', 'danger')
            finally:
                conn.close()
        else:
            for field, error in form.errors.items():
                flash(error, 'danger')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(
        username=request.form.get('username', ''),
        password=request.form.get('password', '')
    )
    if request.method == 'POST':
        if form.validate():
            conn = get_db_connection()
            if conn is None:
                return redirect(url_for('login'))
            user = conn.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
            conn.close()
            if user and check_password_hash(user['password'], form.password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_job():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        company = request.form.get('company', '').strip()
        status = request.form.get('status', '').strip()
        applied_date = request.form.get('applied_date', '').strip()
        follow_up_date = request.form.get('follow_up_date', '').strip() or None

        if not job_title or not company or not status or not applied_date:
            flash("Please fill out all required fields.", "danger")
            return redirect(url_for('add_job'))

        conn = get_db_connection()
        if conn is None:
            return redirect(url_for('login'))

        try:
            conn.execute('''
                INSERT INTO jobs (user_id, job_title, company, status, applied_date, follow_up_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], job_title, company, status, applied_date, follow_up_date))
            conn.commit()
            flash('Job added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding job: {e}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('dashboard'))

    return render_template('add_job.html')



@app.route('/available-jobs')
def available_jobs():
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))
    jobs = conn.execute('SELECT * FROM available_jobs ORDER BY posted_date DESC').fetchall()
    conn.close()
    return render_template('available_jobs.html', jobs=jobs)


@app.route('/apply/<int:job_id>')
def apply_to_available_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))
    job = conn.execute('SELECT * FROM available_jobs WHERE id = ?', (job_id,)).fetchone()
    if job:
        conn.execute('''INSERT INTO jobs (user_id, job_title, company, status, applied_date)
                        VALUES (?, ?, ?, ?, ?)''',
                     (session['user_id'], job['job_title'], job['company'], 'Applied', datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        flash('Applied successfully!', 'success')
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/manage-available-jobs', methods=['GET', 'POST'])
def manage_available_jobs():
    if not session.get('is_admin'):
        flash("Unauthorized access", "danger")
        return redirect(url_for('dashboard'))

    form = AvailableJobForm(
        job_title=request.form.get('job_title', ''),
        company=request.form.get('company', ''),
        posted_date=request.form.get('posted_date', '')
    )

    conn = get_db_connection()
    if request.method == 'POST':
        if form.validate():
            try:
                conn.execute('INSERT INTO available_jobs (job_title, company, posted_date) VALUES (?, ?, ?)',
                             (form.job_title, form.company, form.posted_date))
                conn.commit()
                flash("Job posted successfully!", "success")
            except Exception as e:
                flash(f"Database error: {e}", "danger")
        else:
            for field, error in form.errors.items():
                flash(error, "danger")

    jobs = conn.execute('SELECT * FROM available_jobs ORDER BY posted_date DESC').fetchall()
    conn.close()
    return render_template('manage_available_jobs.html', form=form, jobs=jobs)


@app.route('/delete-available-job/<int:job_id>', methods=['POST'])
def delete_available_job(job_id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))
    conn.execute('DELETE FROM available_jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    flash('Job deleted successfully.', 'info')
    return redirect(url_for('manage_available_jobs'))


@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))
    users = conn.execute('SELECT * FROM users').fetchall()
    jobs = conn.execute('SELECT * FROM available_jobs').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users, jobs=jobs)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])
    if not user:
        flash("User not found.", 'danger')
        return redirect(url_for('login'))

    current_user = {
        'username': user['username'],
        'email': user['email']
    }

    return render_template('profile.html', current_user=current_user)


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])
    if not user:
        flash("User not found.", 'danger')
        return redirect(url_for('login'))

    form = EditProfileForm(
        username=request.form.get('username', user['username']),
        email=request.form.get('email', user['email'])
    )

    if request.method == 'POST':
        if form.validate():
            conn = get_db_connection()
            if conn is None:
                return redirect(url_for('login'))

            conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?',
                         (form.username, form.email, session['user_id']))
            conn.commit()
            conn.close()
            flash('Profile updated!', 'success')
            return redirect(url_for('profile'))

    return render_template('edit_profile.html', form=form, user=user)



@app.route('/followups')
def followups():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('login'))
    followups = conn.execute('SELECT * FROM jobs WHERE user_id = ? AND follow_up_date IS NOT NULL ORDER BY follow_up_date',
                             (session['user_id'],)).fetchall()
    conn.close()
    return render_template('followups.html', followups=followups)


# ========================= Run App =========================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
