import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database.sqlite3"


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    return sqlite3.connect(path)


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist and insert sample data."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            survey_date TEXT,
            answers TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT,
            message_text TEXT,
            status TEXT,
            sent_at TEXT,
            FOREIGN KEY(user_phone) REFERENCES users(phone)
        )
        """
    )
    conn.commit()

    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (phone, name, survey_date, answers) VALUES (?, ?, ?, ?)",
            ("+1234567890", "Alice", datetime.utcnow().isoformat(), "yes")
        )
        cursor.execute(
            "INSERT INTO users (phone, name, survey_date, answers) VALUES (?, ?, ?, ?)",
            ("+1987654321", "Bob", datetime.utcnow().isoformat(), "no")
        )
        conn.commit()

        cursor.execute(
            "INSERT INTO messages (user_phone, message_text, status, sent_at) VALUES (?, ?, ?, ?)",
            ("+1234567890", "Hello Alice", "sent", datetime.utcnow().isoformat())
        )
        cursor.execute(
            "INSERT INTO messages (user_phone, message_text, status, sent_at) VALUES (?, ?, ?, ?)",
            ("+1987654321", "Hello Bob", "sent", datetime.utcnow().isoformat())
        )
        conn.commit()


def log_message(conn: sqlite3.Connection, user_phone: str, message_text: str, status: str) -> int:
    """Insert a record into the messages table and return its row ID."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_phone, message_text, status, sent_at) VALUES (?, ?, ?, ?)",
        (user_phone, message_text, status, datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


if __name__ == "__main__":
    with get_connection() as connection:
        init_db(connection)
        print("Database initialized at", DB_PATH)
