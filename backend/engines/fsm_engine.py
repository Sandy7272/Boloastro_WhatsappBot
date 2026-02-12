import logging

from backend.engines.db_engine import (
    get_session,
    save_session,
    clear_session,
    get_or_create_user,
    log_message,
    log_question,

    grant_qna_pack,
    use_qna_credit,
    get_qna_credits,
    mark_kundali_purchased,
    has_kundali_access,
    mark_milan_purchased
)

from backend.engines.astro_engine import get_kundali_cached
from backend.engines.ai_engine import ask_ai
from backend.engines.payment_engine import create_order, verify_payment

from backend.utils.validators import valid_dob, valid_time
from backend.utils.whatsapp_buttons import (
    main_menu,
    language_menu,
    astrology_system_menu,
    payment_menu,
    qna_menu,
    qna_ready_message,
    help_menu
)

logger = logging.getLogger(__name__)


# ================= RESET =================

def reset(phone):
    save_session(phone, "MENU", {
        "lang": "MR",
        "preview_used": False
    })


# ================= PREMIUM LOADER =================

LOADER = {
    "EN": [
        "🔭 Calculating planetary positions...",
        "📜 Reading your birth chart...",
        "✨ Preparing personalized insights..."
    ],
    "HI": [
        "🔭 ग्रह स्थिति देख रहे हैं...",
        "📜 कुंडली विश्लेषण...",
        "✨ आपकी भविष्यवाणी तैयार हो रही है..."
    ],
    "MR": [
        "🔭 ग्रह स्थिती तपासत आहोत...",
        "📜 कुंडली विश्लेषण सुरू आहे...",
        "✨ तुमचे वैयक्तिक मार्गदर्शन तयार होतेय..."
    ]
}


# ================= TEXT =================

TEXT = {
    "ASK_NAME": {
        "EN": "👤 Please enter your full name",
        "HI": "👤 कृपया अपना पूरा नाम दर्ज करें",
        "MR": "👤 कृपया तुमचे पूर्ण नाव लिहा"
    },
    "ASK_DOB": {
        "EN": "📅 Enter Date of Birth (DD-MM-YYYY)",
        "HI": "📅 जन्म तिथि दर्ज करें",
        "MR": "📅 जन्म तारीख टाका"
    },
    "ASK_TIME": {
        "EN": "⏰ Enter Birth Time (HH:MM AM/PM)",
        "HI": "⏰ जन्म समय दर्ज करें",
        "MR": "⏰ जन्म वेळ टाका"
    },
    "ASK_PLACE": {
        "EN": "📍 Enter Birth City (example: Pune)",
        "HI": "📍 जन्म स्थान लिखें",
        "MR": "📍 जन्म ठिकाण टाका"
    },
    "INVALID_PLACE": {
        "EN": "❌ City not found.",
        "HI": "❌ स्थान नहीं मिला।",
        "MR": "❌ ठिकाण सापडले नाही."
    }
}


# ================= MAIN FSM =================

def process_message(phone, msg):

    get_or_create_user(phone)
    log_message(phone, msg)

    msg = msg.strip()

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

    # ================= MENU =================

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
            data["mode"] = "MILAN"
            save_session(phone, "ASTRO_SYSTEM", data)
            return astrology_system_menu(lang)

        if msg == "4":
            save_session(phone, "LANG", data)
            return language_menu()

        if msg == "5":
            return help_menu(lang)

        return main_menu(lang)

    # ================= ASTRO SYSTEM =================

    if step == "ASTRO_SYSTEM":

        if msg == "1":
            data["astro_system"] = "LAHIRI"
        elif msg == "2":
            data["astro_system"] = "KP"
        else:
            return astrology_system_menu(lang)

        save_session(phone, "ASK_NAME", data)
        return TEXT["ASK_NAME"][lang]

    # ================= LANGUAGE =================

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
        return main_menu(data["lang"])

    # ================= COLLECT DETAILS =================

    if step == "ASK_NAME":
        data["name"] = msg
        save_session(phone, "ASK_DOB", data)
        return TEXT["ASK_DOB"][lang]

    if step == "ASK_DOB":

        if not valid_dob(msg):
            return TEXT["ASK_DOB"][lang]

        data["dob"] = msg
        save_session(phone, "ASK_TIME", data)
        return TEXT["ASK_TIME"][lang]

    if step == "ASK_TIME":

        if not valid_time(msg):
            return TEXT["ASK_TIME"][lang]

        data["time"] = msg
        save_session(phone, "ASK_PLACE", data)
        return TEXT["ASK_PLACE"][lang]

    # ================= PLACE =================

    if step == "ASK_PLACE":

        data["place"] = msg
        kundali = get_kundali_cached(data)

        if not kundali:
            return TEXT["INVALID_PLACE"][lang]

        data["kundali"] = kundali

        loader_text = "\n".join(LOADER.get(lang, LOADER["EN"]))

        # ---- KUNDALI ----
        if data["mode"] == "KUNDALI":

            if has_kundali_access(phone):
                return loader_text + "\n\nYour kundali already unlocked."

            save_session(phone, "PAY_KUNDALI", data)
            return loader_text + "\n\n" + payment_menu(create_order(phone), lang)

        # ---- QNA ----
        if data["mode"] == "QNA":
            save_session(phone, "QNA", data)
            return loader_text + "\n\n" + qna_ready_message(lang) + "\n\n" + qna_menu(lang)

        # ---- MILAN ----
        if data["mode"] == "MILAN":
            save_session(phone, "PAY_MILAN", data)
            return loader_text + "\n\n" + payment_menu(create_order(phone), lang)

    # ================= PAYMENTS =================

    if step == "PAY_KUNDALI":

        if verify_payment(phone):
            mark_kundali_purchased(phone)
            save_session(phone, "MENU", data)
            return "✅ Your premium kundali is unlocked."

        return payment_menu(create_order(phone), lang)

    if step == "PAY_MILAN":

        if verify_payment(phone):
            mark_milan_purchased(phone)
            save_session(phone, "MENU", data)
            return "✅ Kundali Milan unlocked."

        return payment_menu(create_order(phone), lang)

    # ================= QNA =================

    if step == "QNA":

        credits = get_qna_credits(phone)

        if credits <= 0:

            if verify_payment(phone):
                grant_qna_pack(phone, 4)
                credits = 4
            else:
                return payment_menu(create_order(phone), lang)

        use_qna_credit(phone)
        remaining = credits - 1

        log_question(phone, msg)
        answer = ask_ai(phone, msg, data)

        return (
            answer +
            f"\n\nQuestions remaining: {remaining}" +
            "\n\n" + qna_menu(lang)
        )

    # ================= FALLBACK =================

    reset(phone)
    return main_menu(lang)
