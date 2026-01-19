from backend.services.ai_service import answer_question
from backend.db import get_connection

def process_question(phone, question, lang):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT wallet_balance,name FROM users WHERE phone=%s",(phone,))
    bal,name = cur.fetchone()

    if bal<20:
        return {
            "en":"❌ Low balance. Recharge wallet.",
            "hi":"❌ बैलेंस कम है",
            "mr":"❌ बॅलन्स कमी आहे"
        }[lang]

    cur.execute("""
        UPDATE users
        SET wallet_balance=wallet_balance-20
        WHERE phone=%s
    """,(phone,))
    conn.commit()

    ai_ans = answer_question(question)

    cur.execute("""
        INSERT INTO user_questions(phone,question,answer)
        VALUES(%s,%s,%s)
    """,(phone,question,ai_ans))
    conn.commit()

    return f"✨ {name}, your answer\n\n{ai_ans}"
