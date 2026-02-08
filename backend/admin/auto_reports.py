import csv
import os
from datetime import datetime, date

from backend.engines.db_engine import get_conn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)


# =========================
# DAILY ACTIVITY REPORT
# =========================

def generate_daily_report():

    today = date.today().isoformat()
    filename = f"daily_report_{today}.csv"
    filepath = os.path.join(REPORT_DIR, filename)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT phone, message, created_at
        FROM message_logs
        WHERE DATE(created_at)=DATE('now')
    """)

    rows = cur.fetchall()
    conn.close()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Phone", "Message", "Time"])

        for r in rows:
            writer.writerow([r["phone"], r["message"], r["created_at"]])

    return filepath


# =========================
# MONTHLY BUSINESS REPORT
# =========================

def generate_monthly_report():

    month = datetime.now().strftime("%Y-%m")
    filename = f"monthly_report_{month}.csv"
    filepath = os.path.join(REPORT_DIR, filename)

    conn = get_conn()
    cur = conn.cursor()

    # Earnings
    cur.execute("""
        SELECT SUM(amount) 
        FROM payments 
        WHERE status='SUCCESS'
        AND strftime('%Y-%m', created_at)=?
    """, (month,))

    earnings = cur.fetchone()[0] or 0

    # Costs
    cur.execute("""
        SELECT SUM(cost)
        FROM api_usage
        WHERE strftime('%Y-%m', created_at)=?
    """, (month,))

    cost = cur.fetchone()[0] or 0

    profit = round(earnings - cost, 2)

    conn.close()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Month", "Earnings", "Cost", "Profit"])
        writer.writerow([month, earnings, round(cost,2), profit])

    return filepath
