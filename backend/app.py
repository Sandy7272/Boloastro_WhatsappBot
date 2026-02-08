import logging
from flask import Flask, request, Response
import xml.sax.saxutils as saxutils

from backend.engines.fsm_engine import process_message
from backend.engines.db_engine import init_db
from backend.utils.security import validate_twilio_signature
from backend.utils.rate_limiter import is_rate_limited
from worker.worker import start_worker

# ✅ Admin Dashboard + CSV Export + Auth
from backend.admin.admin_dashboard import analytics_bp
from backend.admin.export_reports import export_bp
from backend.admin.admin_auth import auth_bp


# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================
# APP SETUP
# =========================

app = Flask(__name__)

# 🔐 Required for admin login sessions
app.secret_key = "change-this-to-strong-secret-key"


# =========================
# REGISTER ADMIN TOOLS
# =========================

app.register_blueprint(analytics_bp)
app.register_blueprint(export_bp)
app.register_blueprint(auth_bp)


# =========================
# INIT DB + WORKER
# =========================

init_db()
start_worker()


# =========================
# TWILIO WEBHOOK
# =========================

@app.route("/bot", methods=["POST"])
def bot():
    try:
        # 🔐 Validate Twilio request
        if not validate_twilio_signature(request):
            logger.warning("🚫 Unauthorized request blocked")
            return Response("Unauthorized", status=403)

        body = request.form.get("Body", "")
        user = request.form.get("From", "")

        if not body or not user:
            return Response("Bad request", status=400)

        msg = body.strip()

        # ⏱ Rate limiting
        if is_rate_limited(user):
            logger.info(f"⏳ Rate limit hit for {user}")

            wait_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⏳ Please slow down. Try again in a minute.</Message>
</Response>"""

            return Response(wait_twiml, mimetype="application/xml")

        logger.info(f"[USER {user}] {msg}")

        # 🤖 Process message
        reply_text = process_message(user, msg)

        if not reply_text:
            reply_text = "⚠️ Something went wrong. Please type *START*."

        # Escape XML
        reply_text = saxutils.escape(reply_text)

        # Twilio response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""

        return Response(twiml, mimetype="application/xml")

    except Exception:
        logger.exception("❌ Webhook error")

        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⚠️ Temporary error. Please try again.</Message>
</Response>"""

        return Response(error_twiml, mimetype="application/xml")


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    logger.info("🚀 Backend running with analytics + auth + security + rate limit")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
