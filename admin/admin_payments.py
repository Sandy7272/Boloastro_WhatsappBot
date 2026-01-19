# admin_payments.py

from datetime import datetime
from admin_db import get_db

def log_payment(user_id, amount, tier):
    db = get_db()
    c = db.cursor()

    c.execute("""
    INSERT INTO payments (user_id, amount, tier, timestamp)
    VALUES (?, ?, ?, ?)
    """, (user_id, amount, tier, datetime.now().isoformat()))

    db.commit()
    db.close()
