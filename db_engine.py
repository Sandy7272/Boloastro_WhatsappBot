import sqlite3

DB_PATH = "bot.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY,
        step TEXT,
        data TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kundali_cache (
        hash TEXT PRIMARY KEY,
        payload TEXT
    )
    """)

    conn.commit()
    conn.close()
