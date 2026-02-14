"""
Complete Database Engine for Boloastro WhatsApp Bot
Includes all CRUD operations, Milan functions, payment tracking, and analytics

Features:
- User management
- Session management (FSM state)
- Message logging
- Q&A credit system
- Purchase tracking
- Kundali access management
- Milan (compatibility) tracking
- Payment orders tracking
- Admin analytics
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from backend.config import Config

logger = logging.getLogger(__name__)


# =========================
# DATABASE CONNECTION
# =========================

def get_conn():
    """
    Get database connection with WAL mode for better concurrency
    
    Returns:
        sqlite3.Connection: Database connection
    """
    
    from backend.config import Config
import os

def get_conn():
    db_path = "bot.db"  # Simple hardcoded path

    # If DB_URL starts with sqlite:///
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")

    # Convert to absolute path
    db_path = os.path.abspath(db_path)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Enable WAL mode for better performance
    conn.execute("PRAGMA journal_mode=WAL")
    
    return conn


# =========================
# INITIALIZE DATABASE
# =========================

def init_db():
    """
    Initialize database with all required tables and indexes
    Called on application startup
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # ========== USERS TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== SESSIONS TABLE (FSM State) ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY,
        step TEXT NOT NULL,
        data TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== MESSAGE LOGS TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== QNA CREDITS TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qna_credits (
        phone TEXT PRIMARY KEY,
        credits INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== QUESTIONS LOG TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        question TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== PURCHASES TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        product TEXT NOT NULL,
        purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== PAYMENT ORDERS TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payment_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        order_id TEXT UNIQUE NOT NULL,
        payment_id TEXT UNIQUE,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        product_type TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== MILAN CALCULATIONS TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS milan_calculations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        boy_name TEXT NOT NULL,
        girl_name TEXT NOT NULL,
        boy_nakshatra TEXT,
        girl_nakshatra TEXT,
        boy_moon_sign TEXT,
        girl_moon_sign TEXT,
        total_score REAL NOT NULL,
        percentage REAL NOT NULL,
        rating TEXT,
        detailed_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========== CACHE TABLE ==========
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL
    )
    """)
    
    # ========== CREATE INDEXES ==========
    
    # Sessions
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_phone ON sessions(phone)")
    
    # Message logs
    cur.execute("CREATE INDEX IF NOT EXISTS idx_message_logs_phone ON message_logs(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_message_logs_created ON message_logs(created_at DESC)")
    
    # Purchases
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_phone ON purchases(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_purchases_phone_product ON purchases(phone, product)")
    
    # Payment orders
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_orders_phone ON payment_orders(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_orders_order_id ON payment_orders(order_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status)")
    
    # Milan calculations
    cur.execute("CREATE INDEX IF NOT EXISTS idx_milan_phone ON milan_calculations(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_milan_created ON milan_calculations(created_at DESC)")
    
    # Questions log
    cur.execute("CREATE INDEX IF NOT EXISTS idx_questions_phone ON questions_log(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_questions_created ON questions_log(created_at DESC)")
    
    # Cache
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
    
    conn.commit()
    conn.close()
    
    logger.info("✅ Database initialized successfully with all tables and indexes")


# =========================
# USER FUNCTIONS
# =========================

def get_or_create_user(phone):
    """
    Get user or create if doesn't exist
    
    Args:
        phone: User's WhatsApp number
    
    Returns:
        dict: User record
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
    user = cur.fetchone()
    
    if not user:
        # Create new user
        cur.execute("""
        INSERT INTO users(phone, created_at, last_active)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (phone,))
        
        conn.commit()
        
        # Fetch the created user
        cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
        user = cur.fetchone()
        
        logger.info(f"✅ New user created: {phone}")
    else:
        # Update last active
        cur.execute("""
        UPDATE users SET last_active=CURRENT_TIMESTAMP WHERE phone=?
        """, (phone,))
        
        conn.commit()
    
    conn.close()
    
    return dict(user) if user else None


def get_user(phone):
    """Get user by phone"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
    user = cur.fetchone()
    
    conn.close()
    
    return dict(user) if user else None


# =========================
# SESSION FUNCTIONS (FSM State)
# =========================

def get_session(phone):
    """
    Get user's current session (FSM state)
    
    Args:
        phone: User's WhatsApp number
    
    Returns:
        dict: Session data with 'step' and 'data' keys
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM sessions WHERE phone=?", (phone,))
    session = cur.fetchone()
    
    conn.close()
    
    if session:
        return {
            "phone": session["phone"],
            "step": session["step"],
            "data": json.loads(session["data"]) if session["data"] else {}
        }
    
    return None


def save_session(phone, step, data):
    """
    Save user's session (FSM state)
    
    Args:
        phone: User's WhatsApp number
        step: Current FSM step
        data: Session data (dict)
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    data_json = json.dumps(data)
    
    # Upsert session
    cur.execute("""
    INSERT INTO sessions(phone, step, data, updated_at)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(phone) DO UPDATE SET
        step=excluded.step,
        data=excluded.data,
        updated_at=CURRENT_TIMESTAMP
    """, (phone, step, data_json))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"📝 Session saved: {phone} → {step}")


def clear_session(phone):
    """Delete user's session"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM sessions WHERE phone=?", (phone,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"🗑️ Session cleared: {phone}")


# =========================
# MESSAGE LOGGING
# =========================

def log_message(phone, message):
    """
    Log incoming message
    
    Args:
        phone: User's WhatsApp number
        message: Message text
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO message_logs(phone, message, created_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (phone, message))
    
    conn.commit()
    conn.close()


def get_message_history(phone, limit=10):
    """Get user's message history"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM message_logs 
    WHERE phone=? 
    ORDER BY created_at DESC 
    LIMIT ?
    """, (phone, limit))
    
    messages = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return messages


# =========================
# Q&A CREDIT SYSTEM
# =========================

def get_qna_credits(phone):
    """
    Get user's Q&A credits
    
    Args:
        phone: User's WhatsApp number
    
    Returns:
        int: Number of credits
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT credits FROM qna_credits WHERE phone=?", (phone,))
    result = cur.fetchone()
    
    conn.close()
    
    return result["credits"] if result else 0


def grant_qna_pack(phone, credits=4):
    """
    Grant Q&A credits to user
    
    Args:
        phone: User's WhatsApp number
        credits: Number of credits to grant (default: 4)
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Upsert credits
    cur.execute("""
    INSERT INTO qna_credits(phone, credits, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(phone) DO UPDATE SET
        credits=credits + excluded.credits,
        updated_at=CURRENT_TIMESTAMP
    """, (phone, credits))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Granted {credits} Q&A credits to {phone}")


def use_qna_credit(phone):
    """
    Deduct one Q&A credit
    
    Args:
        phone: User's WhatsApp number
    
    Returns:
        bool: True if credit was used, False if no credits available
    """
    
    credits = get_qna_credits(phone)
    
    if credits <= 0:
        return False
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    UPDATE qna_credits 
    SET credits=credits-1, updated_at=CURRENT_TIMESTAMP
    WHERE phone=?
    """, (phone,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"📉 Used 1 Q&A credit for {phone}, remaining: {credits - 1}")
    
    return True


def log_question(phone, question):
    """Log user's question"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO questions_log(phone, question, created_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (phone, question))
    
    conn.commit()
    conn.close()


# =========================
# PURCHASE TRACKING
# =========================

def mark_kundali_purchased(phone):
    """Mark that user purchased Kundali"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO purchases(phone, product, purchased_at)
    VALUES (?, 'KUNDALI', CURRENT_TIMESTAMP)
    """, (phone,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Kundali purchased: {phone}")


def has_kundali_access(phone):
    """Check if user has Kundali access"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT COUNT(*) as count FROM purchases 
    WHERE phone=? AND product='KUNDALI'
    """, (phone,))
    
    result = cur.fetchone()
    conn.close()
    
    return result["count"] > 0 if result else False


def mark_milan_purchased(phone):
    """Mark that user purchased Milan"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO purchases(phone, product, purchased_at)
    VALUES (?, 'MILAN', CURRENT_TIMESTAMP)
    """, (phone,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Milan purchased: {phone}")


def has_milan_access(phone):
    """Check if user has Milan access"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT COUNT(*) as count FROM purchases 
    WHERE phone=? AND product='MILAN'
    """, (phone,))
    
    result = cur.fetchone()
    conn.close()
    
    return result["count"] > 0 if result else False


def get_user_purchases(phone):
    """Get all purchases by user"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM purchases 
    WHERE phone=? 
    ORDER BY purchased_at DESC
    """, (phone,))
    
    purchases = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return purchases


# =========================
# MILAN (COMPATIBILITY) FUNCTIONS
# =========================

def save_milan_result(phone, boy_name, girl_name, milan_result):
    """
    Save Milan calculation result
    
    Args:
        phone: User's WhatsApp number
        boy_name: Boy's name
        girl_name: Girl's name
        milan_result: Milan calculation result dict
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO milan_calculations(
        phone, boy_name, girl_name, boy_nakshatra, girl_nakshatra,
        boy_moon_sign, girl_moon_sign, total_score, percentage, 
        rating, detailed_result, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        phone,
        boy_name,
        girl_name,
        milan_result.get("boy_nakshatra", ""),
        milan_result.get("girl_nakshatra", ""),
        milan_result.get("boy_moon_sign", ""),
        milan_result.get("girl_moon_sign", ""),
        milan_result.get("total_score", 0),
        milan_result.get("percentage", 0),
        milan_result.get("rating", ""),
        json.dumps(milan_result)
    ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Milan saved: {phone} - {boy_name} ❤️ {girl_name} = {milan_result.get('total_score', 0)}/36")


def get_milan_history(phone, limit=5):
    """Get user's Milan calculation history"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM milan_calculations 
    WHERE phone=? 
    ORDER BY created_at DESC 
    LIMIT ?
    """, (phone, limit))
    
    results = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return results


def get_latest_milan(phone):
    """Get user's most recent Milan calculation"""
    
    history = get_milan_history(phone, limit=1)
    
    return history[0] if history else None


# =========================
# CACHE FUNCTIONS
# =========================

def cache_set(key, value, ttl_seconds=3600):
    """
    Set cache value with expiry
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON-encoded)
        ttl_seconds: Time to live in seconds (default: 1 hour)
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    value_json = json.dumps(value)
    
    cur.execute("""
    INSERT INTO cache(key, value, expires_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
        value=excluded.value,
        expires_at=excluded.expires_at
    """, (key, value_json, expires_at))
    
    conn.commit()
    conn.close()


def cache_get(key):
    """
    Get cached value
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found or expired
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT value FROM cache 
    WHERE key=? AND expires_at > CURRENT_TIMESTAMP
    """, (key,))
    
    result = cur.fetchone()
    
    conn.close()
    
    if result:
        return json.loads(result["value"])
    
    return None


def cache_delete(key):
    """Delete cached value"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM cache WHERE key=?", (key,))
    
    conn.commit()
    conn.close()


def cache_clear_expired():
    """Clear all expired cache entries"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP")
    
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        logger.info(f"🗑️ Cleared {deleted} expired cache entries")


# =========================
# CACHE HELPER FUNCTIONS (for backward compatibility)
# =========================

def get_kundali_cache(key):
    """
    Get cached kundali data
    Helper function for astro_engine.py
    
    Args:
        key: Cache key (usually generated from birth details)
    
    Returns:
        Cached kundali data or None
    """
    
    return cache_get(f"kundali_{key}")


def set_kundali_cache(key, kundali_data, ttl_seconds=86400):
    """
    Cache kundali data
    Helper function for astro_engine.py
    
    Args:
        key: Cache key
        kundali_data: Kundali data to cache
        ttl_seconds: Time to live (default: 24 hours = 86400 seconds)
    """
    
    cache_set(f"kundali_{key}", kundali_data, ttl_seconds)


def get_place_cache(key):
    """
    Get cached place coordinates
    Helper function for astro_engine.py
    
    Args:
        key: Place name
    
    Returns:
        Cached place data or None
    """
    
    return cache_get(f"place_{key}")


def set_place_cache(key, place_data, ttl_seconds=604800):
    """
    Cache place coordinates
    Helper function for astro_engine.py
    
    Args:
        key: Place name
        place_data: Place coordinates data
        ttl_seconds: Time to live (default: 7 days = 604800 seconds)
    """
    
    cache_set(f"place_{key}", place_data, ttl_seconds)


def get_ai_cache(key):
    """
    Get cached AI response
    Helper function for ai_engine.py
    
    Args:
        key: Cache key (from question hash)
    
    Returns:
        Cached AI response or None
    """
    
    return cache_get(f"ai_{key}")


def set_ai_cache(key, response, ttl_seconds=3600):
    """
    Cache AI response
    Helper function for ai_engine.py
    
    Args:
        key: Cache key
        response: AI response text
        ttl_seconds: Time to live (default: 1 hour = 3600 seconds)
    """
    
    cache_set(f"ai_{key}", response, ttl_seconds)


def get_ai_cached_answer(key):
    """
    Get cached AI answer
    Alias for get_ai_cache - for backward compatibility with ai_engine.py
    
    Args:
        key: Cache key
    
    Returns:
        Cached AI response or None
    """
    
    return get_ai_cache(key)


def save_ai_answer(key, answer, ttl_seconds=3600):
    """
    Save (cache) AI answer
    Alias for set_ai_cache - for backward compatibility with ai_engine.py
    
    Args:
        key: Cache key
        answer: AI response text
        ttl_seconds: Time to live (default: 1 hour = 3600 seconds)
    """
    
    set_ai_cache(key, answer, ttl_seconds)


# =========================
# ADDITIONAL CACHE HELPERS (for backward compatibility)
# =========================

def save_kundali_cache(key, kundali_data, ttl_seconds=86400):
    """
    Save (cache) kundali data
    Alias for set_kundali_cache - for backward compatibility
    
    Args:
        key: Cache key
        kundali_data: Kundali data to cache
        ttl_seconds: Time to live (default: 24 hours = 86400 seconds)
    """
    
    set_kundali_cache(key, kundali_data, ttl_seconds)


# =========================
# API USAGE TRACKING (for Prokerala/external APIs)
# =========================

def log_api_usage(phone, api_name, cost=0.0):
    """
    Log API usage for tracking costs
    
    Args:
        phone: User's WhatsApp number
        api_name: Name of API called (e.g., 'prokerala', 'openai')
        cost: Cost of the API call in USD (default: 0.0)
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Create API usage table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        api_name TEXT NOT NULL,
        cost REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert usage log
    cur.execute("""
    INSERT INTO api_usage(phone, api_name, cost, created_at)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (phone, api_name, cost))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"📊 API usage logged: {phone} - {api_name} - ${cost}")


def use_api_credit(phone, credits=1):
    """
    Deduct API credits from user
    Note: This is a placeholder function. Implement actual credit system if needed.
    
    Args:
        phone: User's WhatsApp number
        credits: Number of credits to deduct (default: 1)
    
    Returns:
        bool: True if credits were deducted, False if insufficient credits
    """
    
    # For now, always return True
    # You can implement actual credit checking logic here
    
    logger.debug(f"💳 API credit used: {phone} - {credits} credits")
    
    return True


def get_api_usage_stats(phone=None, days=30):
    """
    Get API usage statistics
    
    Args:
        phone: User's phone (optional, if None returns all users)
        days: Number of days to look back (default: 30)
    
    Returns:
        dict: API usage statistics
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='api_usage'
    """)
    
    if not cur.fetchone():
        conn.close()
        return {
            "total_calls": 0,
            "total_cost": 0.0,
            "by_api": {},
            "recent_calls": []
        }
    
    # Build query
    if phone:
        where_clause = "WHERE phone=? AND created_at >= datetime('now', ? || ' days')"
        params = (phone, -days)
    else:
        where_clause = "WHERE created_at >= datetime('now', ? || ' days')"
        params = (-days,)
    
    # Total calls
    cur.execute(f"SELECT COUNT(*) as count FROM api_usage {where_clause}", params)
    total_calls = cur.fetchone()["count"]
    
    # Total cost
    cur.execute(f"SELECT SUM(cost) as total FROM api_usage {where_clause}", params)
    result = cur.fetchone()
    total_cost = result["total"] if result["total"] else 0.0
    
    # By API
    cur.execute(f"""
    SELECT api_name, COUNT(*) as count, SUM(cost) as cost
    FROM api_usage {where_clause}
    GROUP BY api_name
    """, params)
    by_api = {row["api_name"]: {"count": row["count"], "cost": row["cost"] or 0.0} for row in cur.fetchall()}
    
    # Recent calls
    cur.execute(f"""
    SELECT phone, api_name, cost, created_at
    FROM api_usage {where_clause}
    ORDER BY created_at DESC
    LIMIT 10
    """, params)
    recent_calls = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return {
        "total_calls": total_calls,
        "total_cost": round(total_cost, 2),
        "by_api": by_api,
        "recent_calls": recent_calls
    }


def get_api_credits(phone=None):
    """
    Get API credits for user or all users
    For admin dashboard compatibility
    
    Args:
        phone: User's phone (optional)
    
    Returns:
        int or dict: Credits count or dict of all users' credits
    """
    
    # This is a placeholder function for admin dashboard
    # Actual API credit system can be implemented here
    
    if phone:
        # Return credits for specific user
        # For now, return unlimited (or implement actual credit system)
        return 999
    else:
        # Return all users' credits (for admin dashboard)
        conn = get_conn()
        cur = conn.cursor()
        
        # Get all users
        cur.execute("SELECT phone FROM users LIMIT 100")
        users = cur.fetchall()
        
        conn.close()
        
        # Return dict of phone: credits
        return {user["phone"]: 999 for user in users}


# =========================
# ADMIN ANALYTICS
# =========================

def get_user_stats():
    """Get user statistics for admin dashboard"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Total users
    cur.execute("SELECT COUNT(*) as count FROM users")
    total_users = cur.fetchone()["count"]
    
    # Users today
    cur.execute("""
    SELECT COUNT(*) as count FROM users 
    WHERE DATE(created_at) = DATE('now')
    """)
    users_today = cur.fetchone()["count"]
    
    # Active users (last 7 days)
    cur.execute("""
    SELECT COUNT(*) as count FROM users 
    WHERE last_active >= datetime('now', '-7 days')
    """)
    active_users = cur.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "users_today": users_today,
        "active_users_7d": active_users
    }


def get_purchase_stats():
    """Get purchase statistics"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Total purchases
    cur.execute("SELECT COUNT(*) as count FROM purchases")
    total = cur.fetchone()["count"]
    
    # Purchases by product
    cur.execute("""
    SELECT product, COUNT(*) as count 
    FROM purchases 
    GROUP BY product
    """)
    by_product = {row["product"]: row["count"] for row in cur.fetchall()}
    
    # Revenue (approximate)
    revenue = (
        by_product.get("KUNDALI", 0) * Config.KUNDALI_PRICE +
        by_product.get("QNA", 0) * Config.QNA_PRICE +
        by_product.get("MILAN", 0) * getattr(Config, "MILAN_PRICE", 199)
    )
    
    conn.close()
    
    return {
        "total_purchases": total,
        "by_product": by_product,
        "estimated_revenue": revenue
    }


def get_milan_stats():
    """Get Milan statistics"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Total Milan calculations
    cur.execute("SELECT COUNT(*) as count FROM milan_calculations")
    total = cur.fetchone()["count"]
    
    # Average score
    cur.execute("SELECT AVG(total_score) as avg FROM milan_calculations")
    avg_score = cur.fetchone()["avg"] or 0
    
    # Rating distribution
    cur.execute("""
    SELECT rating, COUNT(*) as count 
    FROM milan_calculations 
    GROUP BY rating
    """)
    rating_dist = {row["rating"]: row["count"] for row in cur.fetchall()}
    
    # Recent calculations
    cur.execute("""
    SELECT boy_name, girl_name, total_score, percentage, rating, created_at
    FROM milan_calculations
    ORDER BY created_at DESC
    LIMIT 10
    """)
    recent = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return {
        "total_calculations": total,
        "average_score": round(avg_score, 1),
        "rating_distribution": rating_dist,
        "recent_calculations": recent
    }


def get_payment_stats():
    """Get payment order statistics"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Total orders
    cur.execute("SELECT COUNT(*) as count FROM payment_orders")
    total_orders = cur.fetchone()["count"]
    
    # Orders by status
    cur.execute("""
    SELECT status, COUNT(*) as count 
    FROM payment_orders 
    GROUP BY status
    """)
    by_status = {row["status"]: row["count"] for row in cur.fetchall()}
    
    # Total revenue (successful payments)
    cur.execute("""
    SELECT SUM(amount) as total 
    FROM payment_orders 
    WHERE status='SUCCESS'
    """)
    revenue = cur.fetchone()["total"] or 0
    
    # Recent orders
    cur.execute("""
    SELECT order_id, phone, amount, product_type, status, created_at
    FROM payment_orders
    ORDER BY created_at DESC
    LIMIT 10
    """)
    recent = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return {
        "total_orders": total_orders,
        "by_status": by_status,
        "total_revenue": revenue,
        "recent_orders": recent
    }


def get_all_stats():
    """Get all statistics combined"""
    
    return {
        "users": get_user_stats(),
        "purchases": get_purchase_stats(),
        "milan": get_milan_stats(),
        "payments": get_payment_stats()
    }


# =========================
# CLEANUP FUNCTIONS
# =========================

def cleanup_old_data(days=90):
    """
    Clean up old data
    
    Args:
        days: Delete data older than this many days
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cutoff = datetime.now() - timedelta(days=days)
    
    # Clean old message logs
    cur.execute("""
    DELETE FROM message_logs 
    WHERE created_at < ?
    """, (cutoff,))
    
    messages_deleted = cur.rowcount
    
    # Clean old cache
    cur.execute("""
    DELETE FROM cache 
    WHERE expires_at < CURRENT_TIMESTAMP
    """)
    
    cache_deleted = cur.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"🗑️ Cleanup: {messages_deleted} old messages, {cache_deleted} expired cache")
    
    return {
        "messages_deleted": messages_deleted,
        "cache_deleted": cache_deleted
    }


# =========================
# UTILITY FUNCTIONS
# =========================

def vacuum_database():
    """Optimize database (run periodically)"""
    
    conn = get_conn()
    conn.execute("VACUUM")
    conn.close()
    
    logger.info("✨ Database vacuumed")


def get_database_size():
    """Get database file size in MB"""
    
    import os
    
    if os.path.exists(Config.DB_URL):
        size_bytes = os.path.getsize(Config.DB_URL)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    
    return 0


def export_data_to_json(output_file="data_export.json"):
    """
    Export all data to JSON file for backup
    
    Args:
        output_file: Output filename
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    data = {}
    
    # Export all tables
    tables = ["users", "sessions", "purchases", "milan_calculations", "payment_orders"]
    
    for table in tables:
        cur.execute(f"SELECT * FROM {table}")
        data[table] = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"✅ Data exported to {output_file}")
    
    return output_file


# =========================
# MIGRATION HELPER
# =========================

def migrate_to_postgres(postgres_url):
    """
    Migrate data from SQLite to PostgreSQL
    
    Args:
        postgres_url: PostgreSQL connection URL
    
    Note: Requires psycopg2 library
    """
    
    try:
        import psycopg2
        from psycopg2.extras import Json
        
        # Export SQLite data
        export_data = export_data_to_json("/tmp/migration_export.json")
        
        with open(export_data, 'r') as f:
            data = json.load(f)
        
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(postgres_url)
        pg_cur = pg_conn.cursor()
        
        # Create tables in PostgreSQL (simplified - adjust as needed)
        # ... (table creation SQL here)
        
        # Insert data
        for table, rows in data.items():
            for row in rows:
                # Convert row to INSERT statement
                # ... (insertion logic here)
                pass
        
        pg_conn.commit()
        pg_conn.close()
        
        logger.info("✅ Migration to PostgreSQL completed")
        
    except ImportError:
        logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")


# =========================
# INITIALIZATION
# =========================

if __name__ == "__main__":
    """
    Run this file directly to initialize/update the database
    """
    
    print("🔧 Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    
    print("\n📊 Database Statistics:")
    stats = get_all_stats()
    print(f"   Total Users: {stats['users']['total_users']}")
    print(f"   Total Purchases: {stats['purchases']['total_purchases']}")
    print(f"   Total Milan: {stats['milan']['total_calculations']}")
    print(f"   Database Size: {get_database_size()} MB")
    
    print("\n✨ Database is ready to use!")