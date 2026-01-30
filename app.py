from flask import Flask, request, Response
from fsm_engine import process_message
from db_engine import init_db
import logging
import xml.sax.saxutils as saxutils

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

init_db()

@app.route("/bot", methods=["POST"])
def bot():
    try:
        body = request.form.get("Body", "")
        user = request.form.get("From", "")

        msg = body.strip()

        logging.info(f"{user} -> {msg}")

        # 🔥 SINGLE SOURCE OF TRUTH: FSM
        reply_text = process_message(user, msg)

        if not reply_text:
            reply_text = "⚠️ Something went wrong. Please type *START*."

        # Escape XML
        reply_text = saxutils.escape(reply_text)

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""

        return Response(twiml, mimetype="application/xml")

    except Exception as e:
        logging.exception("Webhook error")

        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⚠️ Temporary error. Please try again.</Message>
</Response>"""
        return Response(error_twiml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(debug=True)
