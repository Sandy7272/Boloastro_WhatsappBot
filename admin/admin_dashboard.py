# admin_dashboard.py

from flask import Flask, render_template_string
from admin_auth import require_admin_auth
from admin_db import get_db

app = Flask(__name__)

HTML = """
<h1>Ultimate VIP Kundali – Admin</h1>

<h3>Users</h3>
<table border=1 cellpadding=8>
<tr>
<th>User</th><th>Tier</th><th>Reports</th><th>Questions</th><th>Joined</th>
</tr>
{% for u in users %}
<tr>
<td>{{u[0]}}</td><td>{{u[1]}}</td><td>{{u[2]}}</td><td>{{u[3]}}</td><td>{{u[4]}}</td>
</tr>
{% endfor %}
</table>

<h3>Payments</h3>
<table border=1 cellpadding=8>
<tr>
<th>User</th><th>Amount</th><th>Tier</th><th>Date</th>
</tr>
{% for p in payments %}
<tr>
<td>{{p[1]}}</td><td>₹{{p[2]}}</td><td>{{p[3]}}</td><td>{{p[4]}}</td>
</tr>
{% endfor %}
</table>
"""

@app.route("/admin")
@require_admin_auth
def admin():
    db = get_db()
    c = db.cursor()

    users = c.execute("SELECT * FROM users").fetchall()
    payments = c.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()

    return render_template_string(HTML, users=users, payments=payments)

if __name__ == "__main__":
    app.run(port=6000)
