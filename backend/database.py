import sqlite3
import os

DATABASE = "database/screen_time.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():

    os.makedirs("database", exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor()

    # STUDENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # TRACKED APPS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            app_name TEXT NOT NULL,
            package_name TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (student_id)
            REFERENCES students(id),

            UNIQUE(student_id, package_name)
        )
    """)

    # APP LIMITS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            package_name TEXT NOT NULL,
            daily_limit_minutes INTEGER NOT NULL,
            warnings_enabled INTEGER DEFAULT 1,
            warning_percentage INTEGER DEFAULT 80,

            FOREIGN KEY (student_id)
            REFERENCES students(id),

            UNIQUE(student_id, package_name)
        )
    """)

    # SESSIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            package_name TEXT NOT NULL,
            app_name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration INTEGER DEFAULT 0,

            FOREIGN KEY (student_id)
            REFERENCES students(id)
        )
    """)

    # DAILY USAGE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            usage_date DATE NOT NULL,
            package_name TEXT NOT NULL,
            app_name TEXT NOT NULL,

            usage_minutes INTEGER DEFAULT 0,
            daily_limit_minutes INTEGER,

            warning_sent INTEGER DEFAULT 0,
            limit_reached INTEGER DEFAULT 0,
            limit_exceeded INTEGER DEFAULT 0,

            exceeded_by_minutes INTEGER DEFAULT 0,

            FOREIGN KEY (student_id)
            REFERENCES students(id),

            UNIQUE(student_id, usage_date, package_name)
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")