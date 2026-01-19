from backend.db import get_connection
from backend.services.prokerala_service import generate_kundali_once
from backend.services.ai_service import explain_prediction
from backend.utils.time_parser import parse_time
from backend.utils.city_parser import normalize_city
from backend.services.prokerala_service import generate_kundali_once



def handle_message(phone, msg):
    conn = get_connection()
    cur = conn.cursor()
    msg = msg.strip()

    cur.execute("""
        SELECT name, step, language, wallet_balance,
               dob, tob, birth_place, gender, kundali_json
        FROM users WHERE phone=%s
    """, (phone,))
    user = cur.fetchone()

    # NEW USER
    if not user:
        cur.execute("""
            INSERT INTO users(phone, step)
            VALUES(%s,'name')
        """, (phone,))
        conn.commit()
        return "🙏 Namaste! Welcome to *BoloAstro* 🔮\n\nWhat is your name?"

    name, step, lang, wallet, dob, tob, place, gender, chart = user

    # RESET
    if msg.lower() in ["menu", "reset", "start"]:
        cur.execute("UPDATE users SET step='menu' WHERE phone=%s",(phone,))
        conn.commit()
        return menu(lang, name)

    # ================= NAME =================
    if step == "name":
        cur.execute("""
            UPDATE users SET name=%s, step='language'
            WHERE phone=%s
        """,(msg, phone))
        conn.commit()
        return language_ui()

    # ================= LANGUAGE =================
    if step == "language":
        lang_map = {"1":"en","2":"hi","3":"mr"}
        if msg not in lang_map:
            return language_ui()

        lang = lang_map[msg]
        cur.execute("""
            UPDATE users SET language=%s, step='menu'
            WHERE phone=%s
        """,(lang, phone))
        conn.commit()
        return menu(lang,name)

    # ================= MENU =================
    if step == "menu":

        if msg=="1":
            cur.execute("UPDATE users SET step='dob' WHERE phone=%s",(phone,))
            conn.commit()
            return ui(lang,"dob")

        if msg=="2":
            cur.execute("UPDATE users SET step='question' WHERE phone=%s",(phone,))
            conn.commit()
            return ui(lang,"ask")

        if msg=="3":
            return wallet_ui(wallet,lang)

        if msg=="4":
            cur.execute("UPDATE users SET step='language' WHERE phone=%s",(phone,))
            conn.commit()
            return language_ui()

        return menu(lang,name)

    # ================= DOB =================
    if step=="dob":
        try:
            dob = msg
            datetime.strptime(dob,"%d/%m/%Y")
        except:
            return "❌ Invalid format\nUse DD/MM/YYYY"

        cur.execute("""
            UPDATE users SET dob=%s, step='tob'
            WHERE phone=%s
        """,(dob,phone))
        conn.commit()
        return ui(lang,"tob")

    # ================= TIME =================
    if step=="tob":
        parsed = parse_time(msg)
        if not parsed:
            return "❌ Invalid time\nExamples: 6.30am, 06:30 AM, 18:30"

        cur.execute("""
            UPDATE users SET tob=%s, step='place'
            WHERE phone=%s
        """,(parsed,phone))
        conn.commit()
        return ui(lang,"place")

    # ================= PLACE =================
    if step=="place":
        city = normalize_city(msg)

        cur.execute("""
            UPDATE users SET birth_place=%s, step='gender'
            WHERE phone=%s
        """,(city,phone))
        conn.commit()
        return ui(lang,"gender")

    # ================= GENDER =================
    if step=="gender":
        gmap={"1":"Male","2":"Female"}
        if msg not in gmap:
            return ui(lang,"gender")

        gender=gmap[msg]
        cur.execute("""
            UPDATE users SET gender=%s, step='confirm'
            WHERE phone=%s
        """,(gender,phone))
        conn.commit()

        return confirm(lang,name,dob,tob,place,gender)

    # ================= CONFIRM =================
    if step=="confirm":

        if msg=="1":

            if not chart:
                kundali = generate_kundali_once(dob,tob,place,gender)
                cur.execute("""
                    UPDATE users SET kundali_json=%s
                    WHERE phone=%s
                """,(kundali,phone))
                conn.commit()

            prediction = explain_prediction(name,lang)
            return prediction

        if msg=="2":
            cur.execute("UPDATE users SET step='dob' WHERE phone=%s",(phone,))
            conn.commit()
            return ui(lang,"dob")

        cur.execute("UPDATE users SET step='menu' WHERE phone=%s",(phone,))
        conn.commit()
        return menu(lang,name)

    # ================= QUESTION =================
    if step=="question":
        if wallet<20:
            return recharge(lang)

        answer = explain_prediction(name,lang,msg)

        cur.execute("""
            INSERT INTO user_questions(phone,question,answer)
            VALUES(%s,%s,%s)
        """,(phone,msg,answer))

        cur.execute("""
            UPDATE users
            SET wallet_balance=wallet_balance-20,
                step='menu'
            WHERE phone=%s
        """,(phone,))
        conn.commit()

        return answer+"\n\nType MENU"


# ================= UI =================

def language_ui():
    return """Choose language 🌐

1️⃣ English
2️⃣ हिंदी
3️⃣ मराठी"""

def menu(lang,name):
    if lang=="hi":
        return f"🙏 नमस्ते {name}\n\n1️⃣ कुंडली ₹200\n2️⃣ प्रश्न ₹20\n3️⃣ वॉलेट\n4️⃣ भाषा"
    if lang=="mr":
        return f"🙏 नमस्कार {name}\n\n1️⃣ कुंडली ₹200\n2️⃣ प्रश्न ₹20\n3️⃣ वॉलेट\n4️⃣ भाषा"
    return f"🙏 Hello {name}\n\n1️⃣ Kundali ₹200\n2️⃣ Ask Question ₹20\n3️⃣ Wallet\n4️⃣ Language"

def ui(lang,key):
    data={
        "dob":"📅 DOB (DD/MM/YYYY)",
        "tob":"⏰ Time (6.30am, 18:30)",
        "place":"📍 City name",
        "gender":"👤 Gender\n1 Male\n2 Female",
        "ask":"✍ Ask your question"
    }
    return data[key]

def confirm(lang,name,d,t,p,g):
    return f"""{name}, confirm 👇

DOB: {d}
Time: {t}
Place: {p}
Gender: {g}

1️⃣ Confirm
2️⃣ Edit
3️⃣ Cancel"""

def wallet_ui(b,lang):
    return f"💰 Wallet\nBalance ₹{b}"

def recharge(lang):
    return "❌ Low balance\nRecharge soon"
