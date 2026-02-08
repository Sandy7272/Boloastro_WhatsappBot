import sqlite3
import json
from pathlib import Path

# =========================
# DATABASE PATH
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "bot.db"


# =========================
# CONNECTION (FAST MODE)
# =========================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ⚡ Performance tuning
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


# =========================
# INIT DATABASE
# =========================

def init_db():

    conn = get_conn()
    cur = conn.cursor()

    # ---------------- USERS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- SESSIONS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY,
        step TEXT,
        data TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- KUNDALI CACHE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kundali_cache (
        hash TEXT PRIMARY KEY,
        payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- AI CACHE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        question TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- PAYMENTS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        amount REAL,
        status TEXT,
        reference TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # 📊 ANALYTICS
    # =========================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS question_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        question TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # 💰 API USAGE + COST
    # =========================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT,
        cost REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # 💳 API CREDITS TRACKER
    # =========================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_credits (
        service TEXT PRIMARY KEY,
        total REAL,
        used REAL DEFAULT 0
    )
    """)

    # Default credits (you can change anytime)
    cur.execute("""
    INSERT OR IGNORE INTO api_credits(service, total, used)
    VALUES 
        ('OPENAI', 1000, 0),
        ('PROKERALA', 1000, 0)
    """)

    conn.commit()
    conn.close()


# =========================
# API CREDITS HELPERS
# =========================

def set_api_credits(service, total):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO api_credits(service,total,used)
    VALUES(?,?, COALESCE(
        (SELECT used FROM api_credits WHERE service=?), 0
    ))
    """, (service, total, service))

    conn.commit()
    conn.close()


def use_api_credit(service, amount=1):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE api_credits
    SET used = used + ?
    WHERE service=?
    """, (amount, service))

    conn.commit()
    conn.close()


def get_api_credits(service):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT total, used FROM api_credits WHERE service=?
    """, (service,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return 0, 0

    return row["total"], row["used"]


# =========================
# ANALYTICS HELPERS
# =========================

def log_message(phone, message):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO message_logs(phone,message) VALUES (?,?)",
        (phone, message)
    )

    conn.commit()
    conn.close()


def log_question(phone, question):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO question_logs(phone,question) VALUES (?,?)",
        (phone, question)
    )

    conn.commit()
    conn.close()


def log_api_usage(service, cost):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO api_usage(service,cost) VALUES (?,?)",
        (service, cost)
    )

    conn.commit()
    conn.close()


# =========================
# SESSION HELPERS
# =========================

def get_session(phone):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sessions WHERE phone=?", (phone,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "step": row["step"],
        "data": json.loads(row["data"]) if row["data"] else {}
    }


def save_session(phone, step, data):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO sessions(phone,step,data)
    VALUES(?,?,?)
    ON CONFLICT(phone) DO UPDATE SET
        step=excluded.step,
        data=excluded.data,
        updated_at=CURRENT_TIMESTAMP
    """, (phone, step, json.dumps(data)))

    conn.commit()
    conn.close()


def clear_session(phone):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM sessions WHERE phone=?", (phone,))
    conn.commit()
    conn.close()


# =========================
# KUNDALI CACHE
# =========================

def get_kundali_cache(hash_key):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT payload FROM kundali_cache WHERE hash=?",
        (hash_key,)
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return json.loads(row["payload"])

    return None


def save_kundali_cache(hash_key, payload):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO kundali_cache(hash,payload)
    VALUES(?,?)
    """, (hash_key, json.dumps(payload)))

    conn.commit()
    conn.close()


# =========================
# AI CACHE
# =========================

def get_ai_cached_answer(phone, question):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT answer FROM ai_cache
    WHERE phone=? AND question=?
    """, (phone, question))

    row = cur.fetchone()
    conn.close()

    return row["answer"] if row else None


def save_ai_answer(phone, question, answer):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO ai_cache(phone,question,answer)
    VALUES(?,?,?)
    """, (phone, question, answer))

    conn.commit()
    conn.close()


# =========================
# PAYMENTS
# =========================

def save_payment(phone, amount, status, reference=None):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO payments(phone,amount,status,reference)
    VALUES(?,?,?,?)
    """, (phone, amount, status, reference))

    conn.commit()
    conn.close()


def get_latest_payment(phone):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM payments
    WHERE phone=?
    ORDER BY created_at DESC
    LIMIT 1
    """, (phone,))

    row = cur.fetchone()
    conn.close()

    return row

# =========================
# USER HELPER
# =========================

def get_or_create_user(phone, name=None):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users(phone, name) VALUES (?,?)",
            (phone, name)
        )
        conn.commit()

    conn.close()
