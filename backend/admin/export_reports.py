from flask import Blueprint, Response
import csv
from io import StringIO
from backend.engines.db_engine import get_conn

export_bp = Blueprint("export", __name__, url_prefix="/admin")


def generate_csv(query, headers):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for r in rows:
        writer.writerow(r)

    return output.getvalue()


@export_bp.route("/export/users")
def export_users():
    csv_data = generate_csv(
        "SELECT phone, name, created_at FROM users",
        ["phone", "name", "created_at"]
    )
    return Response(csv_data, mimetype="text/csv")


@export_bp.route("/export/messages")
def export_messages():
    csv_data = generate_csv(
        "SELECT phone, message, created_at FROM message_logs",
        ["phone", "message", "created_at"]
    )
    return Response(csv_data, mimetype="text/csv")


@export_bp.route("/export/questions")
def export_questions():
    csv_data = generate_csv(
        "SELECT phone, question, created_at FROM question_logs",
        ["phone", "question", "created_at"]
    )
    return Response(csv_data, mimetype="text/csv")
