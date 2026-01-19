from backend.services.prokerala_service import get_kundali
from backend.services.ai_service import explain_kundali
from backend.db import get_cursor


def kundali_flow(phone):
    cur = get_cursor()

    cur.execute("SELECT dob FROM users WHERE phone=%s",(phone,))
    dob = cur.fetchone()[0]

    if not dob:
        return "Enter DOB (DD/MM/YYYY)"

    data = get_kundali(phone)
    explanation = explain_kundali(data)

    cur.execute("INSERT INTO kundali_reports(phone,report) VALUES(%s,%s)",
                (phone, explanation))
    cur.connection.commit()

    return explanation + "\n\nPay ₹200 to get PDF report"
