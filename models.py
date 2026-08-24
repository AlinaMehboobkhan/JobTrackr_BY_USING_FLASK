import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
DATABASE = os.getenv('DATABASE_URL', 'database.db')  # Default to 'database.db'

def init_db():
    """Initialize the database and create tables if they do not exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            )
        ''')

        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_title TEXT,
                company TEXT,
                status TEXT,
                applied_date TEXT,
                follow_up_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Available Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS available_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                company TEXT,
                posted_date TEXT
            )
        ''')

        conn.commit()
        logging.info("✅ Database initialized.")

    except sqlite3.Error as e:
        logging.error(f"❌ An error occurred during init: {e}")
    finally:
        if conn:
            conn.close()

def make_alina_admin():
    """Make the user 'alina' an admin. Create if doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Hash the password
        password_hash = generate_password_hash('alina9918')

        # Check if 'alina' exists
        cursor.execute("SELECT * FROM users WHERE username = 'alina'")
        user = cursor.fetchone()

        if user:
            # Update admin status and password
            cursor.execute('''
                UPDATE users
                SET is_admin = 1, password = ?
                WHERE username = 'alina'
            ''', (password_hash,))
            logging.info("✅ Updated 'alina' to admin with new password.")
        else:
            # Insert new admin user
            cursor.execute('''
                INSERT INTO users (username, email, password, is_admin)
                VALUES (?, ?, ?, 1)
            ''', ('alina', 'alina@example.com', password_hash))
            logging.info("✅ Created new user 'alina' as admin.")

        conn.commit()

    except sqlite3.Error as e:
        logging.error(f"❌ Failed to set 'alina' as admin: {e}")
    finally:
        if conn:
            conn.close()

# Run setup
if __name__ == '__main__':
    init_db()
    make_alina_admin()
