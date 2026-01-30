from db_engine import get_conn
from validators import valid_dob, valid_time
from astro_engine import get_kundali_cached
from ai_engine import ask_ai
from payment_engine import create_order, verify_payment
from whatsapp_buttons import (
    main_menu,
    language_menu,
    astrology_system_menu,
    confirm_menu,
    payment_menu,
    qna_menu,
    qna_ready_message,
    help_menu
)
import json
import logging

logger = logging.getLogger(__name__)

# ================= DB HELPERS =================

def get_session(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT step,data FROM sessions WHERE phone=?", (phone,))
    row = cur.fetchone()
    conn.close()
    return None if not row else {"step": row[0], "data": json.loads(row[1])}


def save_session(phone, step, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO sessions (phone, step, data)
    VALUES (?, ?, ?)
    ON CONFLICT(phone)
    DO UPDATE SET step=?, data=?
    """, (phone, step, json.dumps(data), step, json.dumps(data)))
    conn.commit()
    conn.close()


def reset(phone):
    save_session(phone, "MENU", {"lang": "MR"})


# ================= LANGUAGE PROMPTS =================

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
    }
}


# ================= FSM CORE =================

def process_message(phone, msg):
    msg = msg.strip()

    # -------- GLOBAL RESET --------
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

        try:
            kundali = get_kundali_cached(data)
        except Exception as e:
            logger.exception("Place validation failed")
            return TEXT["INVALID_PLACE"][lang]

        if not kundali:
            return TEXT["INVALID_PLACE"][lang]

        data["kundali"] = kundali

        if data["mode"] == "QNA":
            save_session(phone, "QNA", data)
            return qna_ready_message(lang) + "\n\n" + qna_menu(lang)

        save_session(phone, "CONFIRM", data)
        return confirm_menu(
            data["name"],
            data["dob"],
            data["time"],
            data["place"],
            lang
        )

    # ---------- CONFIRM ----------
    if step == "CONFIRM":

        if msg == "1":
            save_session(phone, "PAYMENT", data)
            return payment_menu(create_order(phone), lang)

        if msg == "2":
            save_session(phone, "ASK_DOB", data)
            return TEXT["ASK_DOB"][lang]

        return confirm_menu(
            data["name"],
            data["dob"],
            data["time"],
            data["place"],
            lang
        )

    # ---------- PAYMENT ----------
    if step == "PAYMENT":

        if verify_payment(phone):
            save_session(phone, "QNA", data)
            return qna_menu(lang)

        return payment_menu(create_order(phone), lang)

    # ---------- QNA ----------
    if step == "QNA":

        if not verify_payment(phone):
            return payment_menu(create_order(phone), lang)

        PRESET = {
            "1": {
                "EN": "Career prediction",
                "HI": "करियर भविष्यवाणी",
                "MR": "करिअर भविष्यवाणी"
            },
            "2": {
                "EN": "Love and marriage prediction",
                "HI": "प्रेम आणि विवाह भविष्यवाणी",
                "MR": "प्रेम आणि विवाह भविष्यवाणी"
            },
            "3": {
                "EN": "Finance and stability prediction",
                "HI": "आर्थिक स्थिरता भविष्यवाणी",
                "MR": "आर्थिक स्थिरता भविष्यवाणी"
            }
        }

        question = PRESET[msg][lang] if msg in PRESET else msg
        answer = ask_ai(phone, question, data)

        return answer + "\n\n" + qna_menu(lang)

    reset(phone)
    return main_menu(lang)
