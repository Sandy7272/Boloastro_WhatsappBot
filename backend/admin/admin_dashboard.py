from flask import Blueprint, render_template_string, session, redirect
from backend.engines.db_engine import (
    get_conn,
    get_api_credits
)

analytics_bp = Blueprint("analytics", __name__, url_prefix="/admin")


# =========================
# 🔐 LOGIN PROTECTION
# =========================

@analytics_bp.before_request
def protect_admin():
    if not session.get("admin"):
        return redirect("/admin/login")


# =========================
# DASHBOARD HTML
# =========================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BoloAstro Business Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; background:#f4f6f8; padding:30px; }
        h1 { margin-bottom:20px; }

        .card {
            background:white;
            padding:20px;
            margin:10px;
            border-radius:8px;
            display:inline-block;
            width:220px;
            box-shadow:0 2px 6px rgba(0,0,0,.1);
        }

        .value {
            font-size:26px;
            color:#007bff;
            margin-top:8px;
        }

        .chart-box {
            background:white;
            padding:20px;
            margin-top:30px;
            border-radius:8px;
        }
    </style>
</head>
<body>

<h1>📊 BoloAstro Full Analytics Dashboard</h1>

<!-- BASIC STATS -->
<div class="card">Users<div class="value">{{users}}</div></div>
<div class="card">Messages<div class="value">{{messages}}</div></div>
<div class="card">Questions<div class="value">{{questions}}</div></div>

<!-- API USAGE -->
<div class="card">OpenAI Calls<div class="value">{{openai_calls}}</div></div>
<div class="card">Cache Hits<div class="value">{{cache_calls}}</div></div>
<div class="card">Prokerala Calls<div class="value">{{prokerala_calls}}</div></div>

<!-- LIVE CREDITS -->
<div class="card">OpenAI Credits Left<div class="value">{{openai_left}}</div></div>
<div class="card">Prokerala Credits Left<div class="value">{{prokerala_left}}</div></div>

<!-- COSTS -->
<div class="card">OpenAI Cost 💰<div class="value">{{openai_cost}}</div></div>
<div class="card">Prokerala Cost 💰<div class="value">{{prokerala_cost}}</div></div>
<div class="card">Total Cost 💸<div class="value">{{total_cost}}</div></div>

<!-- BUSINESS -->
<div class="card">Earnings 💵<div class="value">{{earnings}}</div></div>
<div class="card">PROFIT 📈<div class="value">{{profit}}</div></div>

<!-- DAILY CHART -->
<div class="chart-box">
<h2>📈 Messages Per Day</h2>
<canvas id="msgChart"></canvas>
</div>

<!-- MONTHLY CHARTS -->
<div class="chart-box">
<h2>📊 Monthly Profit</h2>
<canvas id="profitChart"></canvas>
</div>

<div class="chart-box">
<h2>💸 Monthly API Cost</h2>
<canvas id="costChart"></canvas>
</div>

<script>

const msgLabels = {{ msg_labels | safe }};
const msgData = {{ msg_data | safe }};

new Chart(document.getElementById("msgChart"), {
    type: "line",
    data: {
        labels: msgLabels,
        datasets: [{
            label: "Messages",
            data: msgData,
            borderColor: "#007bff",
            fill: false,
            tension: 0.3
        }]
    }
});

const months = {{ months | safe }};
const profits = {{ profits | safe }};
const costs = {{ costs | safe }};

new Chart(document.getElementById("profitChart"), {
    type: "line",
    data: {
        labels: months,
        datasets: [{
            label: "Profit",
            data: profits,
            borderColor: "#28a745",
            fill: false,
            tension: 0.3
        }]
    }
});

new Chart(document.getElementById("costChart"), {
    type: "bar",
    data: {
        labels: months,
        datasets: [{
            label: "Cost",
            data: costs,
            backgroundColor: "#dc3545"
        }]
    }
});

</script>

</body>
</html>
"""


# =========================
# ROUTE
# =========================

@analytics_bp.route("/analytics")
def analytics():

    conn = get_conn()
    cur = conn.cursor()

    # USERS
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    # ACTIVITY
    cur.execute("SELECT COUNT(*) FROM message_logs")
    messages = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM question_logs")
    questions = cur.fetchone()[0]

    # API USAGE COUNTS
    cur.execute("SELECT COUNT(*) FROM api_usage WHERE service='OPENAI'")
    openai_calls = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM api_usage WHERE service='OPENAI_CACHE'")
    cache_calls = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM api_usage WHERE service='PROKERALA'")
    prokerala_calls = cur.fetchone()[0]

    # COSTS
    cur.execute("SELECT SUM(cost) FROM api_usage WHERE service='OPENAI'")
    openai_cost = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(cost) FROM api_usage WHERE service='PROKERALA'")
    prokerala_cost = cur.fetchone()[0] or 0

    total_cost = round(openai_cost + prokerala_cost, 2)

    # EARNINGS
    cur.execute("SELECT SUM(amount) FROM payments WHERE status='SUCCESS'")
    earnings = cur.fetchone()[0] or 0

    profit = round(earnings - total_cost, 2)

    # 📈 MESSAGES PER DAY
    cur.execute("""
        SELECT DATE(created_at), COUNT(*)
        FROM message_logs
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)

    rows = cur.fetchall()

    msg_labels = [r[0] for r in rows]
    msg_data = [r[1] for r in rows]

    # 📊 MONTHLY COST
    cur.execute("""
        SELECT strftime('%Y-%m', created_at), SUM(cost)
        FROM api_usage
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY 1
    """)

    monthly_rows = cur.fetchall()
    conn.close()

    months = [r[0] for r in monthly_rows]
    costs = [round(r[1],2) for r in monthly_rows]

    # Simple profit per month (earnings evenly split)
    profits = []

    if months:
        avg_earn = earnings / len(months)
        for c in costs:
            profits.append(round(avg_earn - c, 2))

    # 🔮 LIVE CREDITS
    openai_total, openai_used = get_api_credits("OPENAI")
    pro_total, pro_used = get_api_credits("PROKERALA")

    return render_template_string(
        HTML,
        users=users,
        messages=messages,
        questions=questions,

        openai_calls=openai_calls,
        cache_calls=cache_calls,
        prokerala_calls=prokerala_calls,

        openai_left=openai_total - openai_used,
        prokerala_left=pro_total - pro_used,

        openai_cost=round(openai_cost, 2),
        prokerala_cost=round(prokerala_cost, 2),
        total_cost=total_cost,

        earnings=round(earnings,2),
        profit=profit,

        msg_labels=msg_labels,
        msg_data=msg_data,

        months=months,
        profits=profits,
        costs=costs
    )
