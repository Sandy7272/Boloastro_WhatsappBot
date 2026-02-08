import logging

from backend.engines.db_engine import (
    get_session,
    save_session,
    clear_session,
    get_or_create_user,
    log_message,
    log_question
)

from backend.engines.astro_engine import get_kundali_cached
from backend.engines.ai_engine import ask_ai
from backend.engines.payment_engine import create_order, verify_payment

from backend.utils.validators import valid_dob, valid_time
from backend.utils.whatsapp_buttons import (
    main_menu,
    language_menu,
    astrology_system_menu,
    confirm_menu,
    payment_menu,
    qna_menu,
    qna_ready_message,
    help_menu
)

logger = logging.getLogger(__name__)


# =========================
# RESET
# =========================

def reset(phone):
    save_session(phone, "MENU", {"lang": "MR", "preview_used": False})


# =========================
# TEXT
# =========================

TEXT = {
    "ASK_NAME": {
        "EN": "👤 Please enter your full name",
        "HI": "👤 कृपया अपना पूरा नाम दर्ज करें",
        "MR": "👤 कृपया तुमचे पूर्ण नाव लिहा"
    },
    "ASK_DOB": {
        "EN": "📅 Enter Date of Birth (DD-MM-YYYY)",
        "HI": "📅 जन्म तिथि दर्ज करें (DD-MM-YYYY)",
        "MR": "📅 जन्म तारीख टाका (DD-MM-YYYY)"
    },
    "ASK_TIME": {
        "EN": "⏰ Enter Birth Time (HH:MM AM/PM)",
        "HI": "⏰ जन्म समय दर्ज करें (HH:MM AM/PM)",
        "MR": "⏰ जन्म वेळ टाका (HH:MM AM/PM)"
    },
    "ASK_PLACE": {
        "EN": "📍 Enter Birth Place (city only)",
        "HI": "📍 जन्म स्थान दर्ज करें (केवल शहर)",
        "MR": "📍 जन्म ठिकाण टाका (फक्त शहर)"
    },
    "INVALID_PLACE": {
        "EN": "❌ Place not found. Please enter city name only (e.g. Pune)",
        "HI": "❌ स्थान सापडले नाही. फक्त शहराचे नाव लिहा (उदा. Pune)",
        "MR": "❌ ठिकाण सापडले नाही. फक्त शहराचे नाव टाका (उदा. Pune)"
    },
    "PREVIEW_NOTICE": {
        "EN": "✨ Here is a FREE short preview. For full detailed prediction, please upgrade 💳",
        "HI": "✨ यह एक मुफ्त झलक है। पूरी भविष्यवाणी के लिए भुगतान करें 💳",
        "MR": "✨ हा मोफत प्रिव्ह्यू आहे. पूर्ण भविष्यवाणीसाठी अपग्रेड करा 💳"
    }
}


# =========================
# MAIN FSM
# =========================

def process_message(phone, msg):

    # 📊 Analytics
    get_or_create_user(phone)
    log_message(phone, msg)

    msg = msg.strip()

    # ---------- RESET ----------
    if msg.lower() in ["hi", "start", "reset"]:
        reset(phone)
        return main_menu("MR")

    s = get_session(phone)

    if not s:
        reset(phone)
        return main_menu("MR")

    step = s["step"]
    data = s["data"]

    lang = data.get("lang", "MR")
    preview_used = data.get("preview_used", False)

    # ---------- MENU ----------
    if step == "MENU":

        if msg == "1":
            data["mode"] = "KUNDALI"
            save_session(phone, "ASTRO_SYSTEM", data)
            return astrology_system_menu(lang)

        if msg == "2":
            data["mode"] = "QNA"
            save_session(phone, "ASTRO_SYSTEM", data)
            return astrology_system_menu(lang)

        if msg == "3":
            save_session(phone, "LANG", data)
            return language_menu()

        if msg == "4":
            return help_menu(lang)

        return main_menu(lang)

    # ---------- ASTRO SYSTEM ----------
    if step == "ASTRO_SYSTEM":

        if msg == "1":
            data["astro_system"] = "LAHIRI"
        elif msg == "2":
            data["astro_system"] = "KP"
        else:
            return astrology_system_menu(lang)

        save_session(phone, "ASK_NAME", data)
        return TEXT["ASK_NAME"][lang]

    # ---------- LANGUAGE ----------
    if step == "LANG":

        if msg == "1":
            data["lang"] = "EN"
        elif msg == "2":
            data["lang"] = "HI"
        elif msg == "3":
            data["lang"] = "MR"
        else:
            return language_menu()

        save_session(phone, "MENU", data)
        return "✅ Language updated\n\n" + main_menu(data["lang"])

    # ---------- ASK NAME ----------
    if step == "ASK_NAME":
        data["name"] = msg
        save_session(phone, "ASK_DOB", data)
        return TEXT["ASK_DOB"][lang]

    # ---------- ASK DOB ----------
    if step == "ASK_DOB":

        if not valid_dob(msg):
            return TEXT["ASK_DOB"][lang]

        data["dob"] = msg
        save_session(phone, "ASK_TIME", data)
        return TEXT["ASK_TIME"][lang]

    # ---------- ASK TIME ----------
    if step == "ASK_TIME":

        if not valid_time(msg):
            return TEXT["ASK_TIME"][lang]

        data["time"] = msg
        save_session(phone, "ASK_PLACE", data)
        return TEXT["ASK_PLACE"][lang]

    # ---------- ASK PLACE ----------
    if step == "ASK_PLACE":

        data["place"] = msg

        kundali = get_kundali_cached(data)

        if not kundali:
            return TEXT["INVALID_PLACE"][lang]

        data["kundali"] = kundali

        # Go to QNA directly
        save_session(phone, "QNA", data)

        return qna_ready_message(lang) + "\n\n" + qna_menu(lang)

    # ---------- QNA ----------
    if step == "QNA":

        PRESET = {
            "1": {"EN": "Career prediction", "HI": "करियर भविष्यवाणी", "MR": "करिअर भविष्यवाणी"},
            "2": {"EN": "Love and marriage prediction", "HI": "प्रेम आणि विवाह भविष्यवाणी", "MR": "प्रेम आणि विवाह भविष्यवाणी"},
            "3": {"EN": "Finance and stability prediction", "HI": "आर्थिक स्थिरता भविष्यवाणी", "MR": "आर्थिक स्थिरता भविष्यवाणी"}
        }

        question = PRESET[msg][lang] if msg in PRESET else msg

        log_question(phone, question)

        # ----------------------------
        # 🎁 FREE PREVIEW (ONE TIME)
        # ----------------------------

        if not preview_used:

            data["preview_used"] = True
            save_session(phone, "QNA", data)

            short_preview = ask_ai(phone, question, data)

            return (
                short_preview[:600] +  # short snippet
                "\n\n" +
                TEXT["PREVIEW_NOTICE"][lang] +
                "\n\n" +
                payment_menu(create_order(phone), lang)
            )

        # ----------------------------
        # 💳 PAID FLOW
        # ----------------------------

        if not verify_payment(phone):
            return payment_menu(create_order(phone), lang)

        full_answer = ask_ai(phone, question, data)

        return full_answer + "\n\n" + qna_menu(lang)

    # ---------- FALLBACK ----------
    reset(phone)
    return main_menu(lang)
