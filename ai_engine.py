import time
import sys
import subprocess

try:
    from openai import OpenAI
    client = OpenAI(api_key=...)
except ImportError:
    print("Error: openai package is not installed.", file=sys.stderr)
    print("Install it using: pip install openai", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    from openai import OpenAI

from config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

LAST_CALL = {}
COOLDOWN = 10  # seconds


# ================= SYSTEM PROMPT BUILDER =================

def build_system_prompt(lang, astro_system):

    if astro_system == "KP":
        if lang == "MR":
            return (
                "तुम्ही अनुभवी KP (कृष्णमूर्ती पद्धती) ज्योतिषी आहात.\n"
                "उत्तर KP पद्धतीने द्या.\n"
                "घरे, कस्ट लॉर्ड, सब-लॉर्ड, घटना व वेळ यावर लक्ष द्या.\n"
                "उत्तर अचूक, सखोल व व्यावसायिक असावे.\n"
                "किमान 8–12 ओळी लिहा.\n"
                "AI असल्याचा उल्लेख करू नका."
            )

        if lang == "HI":
            return (
                "आप एक अनुभवी KP (कृष्णमूर्ति पद्धति) ज्योतिषी हैं.\n"
                "उत्तर KP पद्धति से दें.\n"
                "कस्ट लॉर्ड, सब-लॉर्ड, घटना और समय पर ध्यान दें.\n"
                "उत्तर विस्तृत और पेशेवर हो.\n"
                "कम से कम 8–12 पंक्तियाँ लिखें.\n"
                "AI होने का उल्लेख न करें."
            )

        return (
            "You are a senior KP astrologer.\n"
            "Answer strictly using KP astrology principles.\n"
            "Focus on cusps, sub-lords, event timing and certainty.\n"
            "Give precise, confident, paid-consultation level answers.\n"
            "Write at least 8–12 meaningful lines.\n"
            "Never mention AI."
        )

    # ---------- LAHIRI (DEFAULT) ----------
    if lang == "MR":
        return (
            "तुम्ही अनुभवी वैदिक (लाहिरी) ज्योतिषी आहात.\n"
            "उत्तर समतोल, व्यावहारिक आणि मार्गदर्शक असावे.\n"
            "किमान 8–12 ओळी लिहा.\n"
            "AI असल्याचा उल्लेख करू नका."
        )

    if lang == "HI":
        return (
            "आप एक अनुभवी वैदिक (लाहिरी) ज्योतिषी हैं.\n"
            "उत्तर संतुलित, व्यावहारिक और मार्गदर्शक दें.\n"
            "कम से कम 8–12 पंक्तियाँ लिखें.\n"
            "AI होने का उल्लेख न करें."
        )

    return (
        "You are an experienced Vedic astrologer (Lahiri system).\n"
        "Give balanced, thoughtful and professional guidance.\n"
        "Write at least 8–12 meaningful lines.\n"
        "Never mention AI."
    )


# ================= MAIN AI FUNCTION =================

def ask_ai(phone, question, data):

    now = time.time()
    if now - LAST_CALL.get(phone, 0) < COOLDOWN:
        return "⏳ कृपया थोड्या वेळाने पुन्हा विचारा."

    LAST_CALL[phone] = now

    lang = data.get("lang", "EN")
    astro_system = data.get("astro_system", "LAHIRI")
    kundali = data.get("kundali", {})

    system_prompt = build_system_prompt(lang, astro_system)

    context = f"""
Birth Details:
Name: {data.get('name')}
DOB: {data.get('dob')}
Time: {data.get('time')}
Place: {data.get('place')}

Astrology System: {astro_system}

Kundali Summary:
Lagna: {kundali.get('lagna')}
Moon Sign: {kundali.get('moon_sign')}
Sun Sign: {kundali.get('sun_sign')}
Current Dasha: {kundali.get('current_dasha')}
Planets: {", ".join(kundali.get('planets', []))}

User Question:
{question}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ],
        temperature=0.6
    )

    return "🔮 *Astrology Guidance*\n\n" + res.choices[0].message.content.strip()
