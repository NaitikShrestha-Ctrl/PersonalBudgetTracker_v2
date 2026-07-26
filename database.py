"""
database.py
────────────────────────────────────────────────────────────
SQLite persistence layer for the Personal Budget Tracker.

Replaces the old JSON-file store (pbt_dark.json) with a real
relational database (pbt.db). This module owns the schema and
all raw SQL — the Flask API in api.py is the only thing that
talks to it directly.
────────────────────────────────────────────────────────────
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.expanduser("~"), "pbt.db")


def get_conn():
    """Return a new connection with foreign keys on and dict-like rows."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist. Safe to call every run."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username        TEXT PRIMARY KEY,
            password_hash   TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user            TEXT NOT NULL,
            date            TEXT NOT NULL,
            category        TEXT NOT NULL,
            description     TEXT,
            amount          REAL NOT NULL,
            note            TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS category_budgets (
            user            TEXT NOT NULL,
            category        TEXT NOT NULL,
            amount          REAL NOT NULL,
            PRIMARY KEY (user, category)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            user            TEXT NOT NULL,
            month           TEXT NOT NULL,
            amount          REAL NOT NULL,
            PRIMARY KEY (user, month)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_FILE}")