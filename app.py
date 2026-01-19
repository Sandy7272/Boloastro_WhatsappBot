import os
import re
import logging
import traceback
from flask import Flask, request, send_from_directory, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from redis import Redis, ConnectionError
from rq import Queue

# --- Custom Imports ---
from config import Config
from sessions import get_session, save_session
from database import init_db, db_session
from models import User

# --- Logic Imports ---
from admin.admin_engine import can_ask_question, deduct_question
from qa_engine import answer_question
from tasks import generate_report_task
from razorpay_payment import verify_signature, create_payment_link

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# --- Redis Setup (Safe Mode) ---
# अगर Redis नहीं मिला, तो हम काम को "Queue" में डालने के बजाय
# सीधे अभी कर देंगे (ताकि Localhost पर एरर न आए)
USE_REDIS = False
q = None

try:
    redis_conn = Redis.from_url(app.config["REDIS_URL"])
    redis_conn.ping() # Check connection
    q = Queue(connection=redis_conn)
    USE_REDIS = True
    logger.info("✅ Redis connected successfully.")
except Exception as e:
    logger.warning(f"⚠️ Redis not connected (Running in Direct Mode): {e}")

# --------------------------------------------------
# MULTI-LANGUAGE UI TEXT
# --------------------------------------------------
LANG_MAP = {"1": "en", "2": "hi", "3": "mr"}
GENDER_MAP = {"1": "male", "2": "female"}

UI_TEXT = {
    "en": {
        "welcome": (
            "🌟 *Ultimate VIP Kundali Bot* 🌟\n\n"
            "You will receive a premium astrology PDF with:\n"
            "• Career timing\n• Marriage timeline\n• Yogas\n• Dasha effects\n\n"
            "Select Language:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Marathi"
        ),
        "gender": "Select Gender:\n1️⃣ Male\n2️⃣ Female",
        "details": (
            "✍️ *Enter Birth Details*\n\n"
            "Format:\nDD-MM-YYYY, Time, Place\n\n"
            "Example:\n30-09-2000, 10:30 AM, Mumbai"
        ),
        "processing": "🔮 Calculating planetary positions...\nPlease wait 10–15 seconds.",
        "done": (
            "✨ *Your Ultimate VIP Kundali is Ready!* ✨\n\n"
            "You may now ask *2 free questions*.\n"
            "Example:\n• When will I get married?\n• Which year is good for buying a car?"
        ),
        "wait": "⏳ Report is generating, please wait...",
        "error": "⚠️ Invalid format. Date must be DD-MM-YYYY.\nExample: 30-09-2000, 6:30 AM, Mumbai",
        "limit": "🔒 You have used all free questions.\nUpgrade to VIP to continue.",
        "server_busy": "⚠️ Server is busy. Please try again."
    },
    "hi": {
        "welcome": (
            "🌟 *अल्टीमेट वीआईपी कुंडली बॉट* 🌟\n\n"
            "आपको एक प्रीमियम ज्योतिष पीडीएफ प्राप्त होगी जिसमें शामिल हैं:\n"
            "• करियर का समय\n• शादी का योग\n• राजयोग\n• दशा फल\n\n"
            "भाषा चुनें:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी"
        ),
        "gender": "लिंग चुनें:\n1️⃣ पुरुष\n2️⃣ महिला",
        "details": (
            "✍️ *जन्म विवरण दर्ज करें*\n\n"
            "फॉर्मेट:\nDD-MM-YYYY, समय, स्थान\n\n"
            "उदाहरण:\n30-09-2000, 10:30 AM, Mumbai"
        ),
        "processing": "🔮 ग्रहों की स्थिति की गणना की जा रही है...\nकृपया 10-15 सेकंड प्रतीक्षा करें।",
        "done": (
            "✨ *आपकी वीआईपी कुंडली तैयार है!* ✨\n\n"
            "अब आप *2 मुफ्त प्रश्न* पूछ सकते हैं।\n"
            "उदाहरण:\n• मेरी शादी कब होगी?\n• कार खरीदने के लिए कौन सा साल अच्छा है?"
        ),
        "wait": "⏳ रिपोर्ट बन रही है, कृपया प्रतीक्षा करें...",
        "error": "⚠️ गलत फॉर्मेट। तारीख DD-MM-YYYY होनी चाहिए।\nउदाहरण: 30-09-2000, 6:30 AM, Mumbai",
        "limit": "🔒 आपने सभी मुफ्त प्रश्नों का उपयोग कर लिया है।\nजारी रखने के लिए VIP अपग्रेड करें।",
        "server_busy": "⚠️ सर्वर व्यस्त है। कृपया पुनः प्रयास करें।"
    },
    "mr": {
        "welcome": (
            "🌟 *अल्टिमेट व्हीआयपी कुंडली बॉट* 🌟\n\n"
            "तुम्हाला प्रीमियम ज्योतिष पीडीएफ मिळेल:\n"
            "• करिअर\n• विवाह योग\n• राजयोग\n• दशा फळ\n\n"
            "भाषा निवडा:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी"
        ),
        "gender": "लिंग निवडा:\n1️⃣ पुरुष\n2️⃣ महिला",
        "details": (
            "✍️ *जन्म तपशील प्रविष्ट करा*\n\n"
            "स्वरूप:\nDD-MM-YYYY, वेळ, ठिकाण\n\n"
            "उदाहरण:\n30-09-2000, 10:30 AM, Mumbai"
        ),
        "processing": "🔮 ग्रहांच्या स्थितीची गणना करत आहे...\nकृपया १०-१५ सेकंद प्रतीक्षा करा.",
        "done": (
            "✨ *तुमची व्हीआयपी कुंडली तयार आहे!* ✨\n\n"
            "तुम्ही आता *२ मोफत प्रश्न* विचारू शकता.\n"
            "उदाहरण:\n• माझे लग्न कधी होईल?\n• कार घेण्यासाठी कोणते वर्ष चांगले आहे?"
        ),
        "wait": "⏳ रिपोर्ट तयार होत आहे, कृपया प्रतीक्षा करा...",
        "error": "⚠️ चुकीचे स्वरूप. तारीख DD-MM-YYYY असावी.\nउदाहरण: 30-09-2000, 6:30 AM, Mumbai",
        "limit": "🔒 तुम्ही सर्व मोफत प्रश्न वापरले आहेत.\nपुढे चालू ठेवण्यासाठी VIP अपग्रेड करा.",
        "server_busy": "⚠️ सर्व्हर व्यस्त आहे. कृपया पुन्हा प्रयत्न करा."
    }
}

# --------------------------------------------------
# SECURITY DECORATOR
# --------------------------------------------------
def validate_twilio_request(f):
    def decorated_function(*args, **kwargs):
        # Localhost testing ke liye validation skip karein
        if app.config.get("SKIP_TWILIO_VALIDATION", False) or app.debug:
            return f(*args, **kwargs)

        url = request.url
        post_vars = request.form.to_dict()
        signature = request.headers.get('X-Twilio-Signature', '')
        validator = RequestValidator(app.config["TWILIO_AUTH_TOKEN"])

        if not validator.validate(url, post_vars, signature):
            return abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# --------------------------------------------------
# INPUT PARSING UTILITY
# --------------------------------------------------
def parse_birth_details(text):
    match = re.search(r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})', text)
    if not match:
        return None
    dob = match.group(1)
    parts = [x.strip() for x in text.split(",", 2)]
    if len(parts) < 3:
        return None
    return {"DOB": dob, "Time": parts[1], "Place": parts[2]}

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
# --- Updated Route for PDF ---
@app.route("/generated_pdfs/<filename>")
def serve_pdf(filename):
    # Folder ka pakka pata (Absolute Path) nikalo
    directory = os.path.join(os.getcwd(), "generated_pdfs")
    
    # Check karo ki file wahan hai ya nahi (Debugging ke liye)
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found at: {file_path}")
        return "File not found on server", 404
        
    return send_from_directory(directory, filename)

@app.route("/bot", methods=["POST"])
# @validate_twilio_request  <-- Commented out for local testing
def bot():
    user = request.values.get("From")
    text = request.values.get("Body", "").strip()

    # 1. LOAD SESSION
    session = get_session(user)
    resp = MessagingResponse()
    msg = resp.message()

    # Default Language (Fallback)
    lang = session.get("language", "en")

    # --- RESET COMMANDS ---
    if text.lower() in ["hi", "hello", "start", "reset", "नमस्ते", "नमस्कार"]:
        session.clear()
        session["stage"] = "LANG"
        # Welcome message hamesha English/Hindi mixed default se start karein
        # ya English se, kyunki abhi tak bhasha pata nahi hai.
        msg.body(UI_TEXT["en"]["welcome"]) 
        save_session(user, session)
        return str(resp)

    # --- STAGE 1: LANGUAGE ---
    if session.get("stage") == "LANG":
        if text in LANG_MAP:
            selected_lang = LANG_MAP[text]
            session["language"] = selected_lang
            session["stage"] = "GENDER"
            # Ab user ki chuni hui bhasha use karein
            msg.body(UI_TEXT[selected_lang]["gender"])
        else:
            msg.body("Type 1, 2, or 3.")
        
        save_session(user, session)
        return str(resp)

    # --- STAGE 2: GENDER ---
    if session.get("stage") == "GENDER":
        if text in GENDER_MAP:
            session["gender"] = GENDER_MAP[text]
            session["stage"] = "DETAILS"
            msg.body(UI_TEXT[lang]["details"])
        else:
            msg.body("Type 1 or 2.")
        
        save_session(user, session)
        return str(resp)

    # --- STAGE 3: DETAILS & GENERATION ---
    if session.get("stage") == "DETAILS":
        parsed_data = parse_birth_details(text)
        
        if parsed_data:
            session["details"] = parsed_data
            session["details"]["Gender"] = session.get("gender")
            
            session["stage"] = "WAIT"
            session["ready"] = False
            save_session(user, session)

            msg.body(UI_TEXT[lang]["processing"])
            
            # --- REDIS vs DIRECT EXECUTION LOGIC ---
            try:
                if USE_REDIS:
                    # Agar Server/Redis hai, toh Queue use karein
                    q.enqueue(
                        generate_report_task,
                        phone_number=user,
                        details=session["details"],
                        language=session["language"]
                    )
                else:
                    # LOCAL TESTING: Agar Redis nahi hai, toh Direct Function chalayein
                    logger.info("⚠️ Redis not found. Running task synchronously...")
                    generate_report_task(
                        phone_number=user,
                        details=session["details"],
                        language=session["language"]
                    )
                    # Task khatam hone ke baad session reload karein
                    # Note: generate_report_task internally updates session['ready'] = True
                    
            except Exception as e:
                logger.error(f"Execution Error: {e}")
                msg.body(UI_TEXT[lang]["server_busy"])
                return str(resp)
                
        else:
            msg.body(UI_TEXT[lang]["error"])
            save_session(user, session)
            
        return str(resp)

    # --- STAGE 4: WAIT / POLLING ---
    if session.get("stage") == "WAIT":
        session = get_session(user) # Reload latest state
        if session.get("ready"):
            msg.body(UI_TEXT[lang]["done"])
            if session.get("pdf_url"):
                msg.media(session["pdf_url"])
            session["stage"] = "QNA"
        else:
            msg.body(UI_TEXT[lang]["wait"])
        
        save_session(user, session)
        return str(resp)

    # --- STAGE 5: Q&A MODE ---
    if session.get("stage") == "QNA":
        if not can_ask_question(user):
            link, link_id = create_payment_link(user)
            if link:
                msg.body(f"{UI_TEXT[lang]['limit']}\n\n👇: {link}")
            else:
                msg.body(UI_TEXT[lang]['server_busy'])
            save_session(user, session)
            return str(resp)

        try:
            answer = answer_question(
                question=text,
                chart=session.get("chart"),
                dasha=session.get("dasha"),
                language=lang  # Pass language to QA Engine
            )
            deduct_question(user)
            msg.body(answer)
        except Exception as e:
            logger.error(f"Q&A Error: {e}")
            msg.body("Error processing question.")
            
        save_session(user, session)
        return str(resp)

    return str(resp)

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    return "OK", 200

if __name__ == "__main__":
    init_db()
    os.makedirs("generated_pdfs", exist_ok=True)
    # Debug mode ON hai, aur Redis check upar handle kar liya hai
    app.run(debug=True, port=5000)