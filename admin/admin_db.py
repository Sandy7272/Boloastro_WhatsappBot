# admin_db.py

import sqlite3
from admin_config import DB_PATH

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        tier TEXT,
        joined TEXT,
        reports INTEGER,
        questions_left INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        amount INTEGER,
        tier TEXT,
        timestamp TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS pdf_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        filename TEXT,
        timestamp TEXT
    )
    """)

    db.commit()
    db.close()
