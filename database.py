import sqlite3


def get_db():

    conn = sqlite3.connect("task.db")
    conn.row_factory = sqlite3.Row

    return conn


def create_tables():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            priority TEXT,
            status TEXT,
            assignee TEXT,
            reviewer TEXT,
            due_date TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_history (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user TEXT,
            action TEXT,
            comment TEXT,
            image TEXT,
            review_time TEXT
        )
    """)

    conn.commit()
    conn.close()

create_tables()
print("Database Created")