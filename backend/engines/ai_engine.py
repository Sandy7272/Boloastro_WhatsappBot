import time
import logging
from datetime import datetime, timedelta

from backend.config import Config
from backend.engines.transit_engine import get_daily_transits
from backend.engines.db_engine import (
    get_ai_cached_answer,
    save_ai_answer,
    log_api_usage,
    use_api_credit
)

logger = logging.getLogger(__name__)


# =========================
# OPENAI INIT
# =========================

try:
    from openai import OpenAI
    client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
except:
    client = None


# =========================
# RATE LIMIT
# =========================

LAST_CALL = {}
COOLDOWN = 5


# =========================
# COST
# =========================

OPENAI_COST_PER_CALL = 0.01


# =========================
# QUESTION CLASSIFIER
# =========================

def classify_question(question):

    q = question.lower()

    if any(w in q for w in ["career","job","promotion","business","work"]):
        return "CAREER"

    if any(w in q for w in ["marriage","love","relationship","husband","wife"]):
        return "MARRIAGE"

    if any(w in q for w in ["money","finance","income","wealth","salary","profit"]):
        return "FINANCE"

    if any(w in q for w in ["health","ill","disease","medical","problem"]):
        return "HEALTH"

    return "GENERAL"


# =========================
# RULE FOCUS
# =========================

RULE_FOCUS = {
    "CAREER": "10th house, its lord, Sun, Saturn, Jupiter, aspects, dasha & antardasha",
    "MARRIAGE": "7th house, its lord, Venus, Moon, Mars, yogas & antardasha",
    "FINANCE": "2nd & 11th houses, their lords, Jupiter, Venus & wealth yogas",
    "HEALTH": "6th & 8th houses, lords, Moon, Mars & dasha",
    "GENERAL": "overall chart strength, house lords, yogas, dasha & transits"
}


# =========================
# FORMAT HELPERS
# =========================

def format_planets(planets):

    if not planets:
        return "None"

    return "\n".join(
        f"{p['name']} in {p['sign']} (House {p['house']}, {p['degree']}°, Nakshatra: {p['nakshatra']})"
        for p in planets
    )


def format_house_lords(lords):

    if not lords:
        return "None"

    return "\n".join(
        f"House {h}: {lord}" for h, lord in lords.items()
    )


def format_aspects(aspects):

    if not aspects:
        return "None"

    return "\n".join(
        f"{a['planet']} aspects House {a['to_house']}"
        for a in aspects
    )


def format_transits(transits):

    if not transits:
        return "None"

    return "\n".join(
        f"{t['name']} in {t['sign']} at {round(t['degree'],2)}°"
        for t in transits
    )


# =========================
# ANTARDASHA + MONTH FORMAT
# =========================

def format_dasha_timeline(dasha):

    if not dasha:
        return "No dasha data"

    current = dasha.get("current", {})
    upcoming = dasha.get("upcoming", [])

    txt = "CURRENT PERIOD:\n"
    txt += f"{current.get('planet')} : {current.get('start')} → {current.get('end')}\n\n"

    txt += "NEXT ANTARDASHA PERIODS:\n"

    for d in upcoming:
        txt += f"{d['planet']} : {d['start']} → {d['end']}\n"

    return txt


def extract_key_months(dasha):

    months = []

    for d in dasha.get("upcoming", []):

        try:
            start = datetime.fromisoformat(d["start"][:10])
            months.append(start.strftime("%B %Y"))
        except:
            pass

    return ", ".join(months) if months else "Not available"


# =========================
# MONTHLY CALENDAR BUILDER (NEW)
# =========================

def build_month_calendar():

    months = []
    today = datetime.today()

    for i in range(6):
        m = today + timedelta(days=30*i)
        months.append(m.strftime("%B %Y"))

    return "\n".join(f"- {m}" for m in months)


# =========================
# SYSTEM PROMPT (HIGH ACCURACY + NEW FEATURES)
# =========================

def build_system_prompt(lang, astro_system):

    base_prompt = f"""
You are VedShree, a master Vedic astrologer with 30+ years of real-world experience.

Astrology System: {astro_system}

STRICT RULES:

• Use house lords, planetary aspects (drishti), yogas, nakshatra
• Use Mahadasha AND Antardasha strongly
• Use transits as event triggers
• Avoid generic horoscope language
• Explain astrological logic clearly
• Use probability wording (strong, moderate, weak)
• Mention EXACT MONTHS wherever possible
• Give practical one-step remedy

NEW OUTPUT FEATURES (MANDATORY):

1️⃣ Probability Score (0–100%)

2️⃣ Life Area Strength Meter (0–10):
Career | Marriage | Finance | Health | Overall

3️⃣ Month-by-Month Prediction Calendar (next 6 months)

MANDATORY FORMAT:

Prediction Level:

Probability Score:

Life Area Strength Meter:

Main Astrological Reasons:
- House lord influence
- Planet placement & aspects
- Dasha + Antardasha effect
- Transit activation

Month-by-Month Forecast:

Best Months:

Caution Months:

Long Term Outlook (1–3 years):

Remedy:
"""

    if lang == "HI":
        base_prompt += "\nRespond fully in Hindi."
    elif lang == "MR":
        base_prompt += "\nRespond fully in Marathi."
    else:
        base_prompt += "\nRespond in English."

    return base_prompt


# =========================
# MAIN AI FUNCTION
# =========================

def ask_ai(phone, question, data):

    # ---------- CACHE ----------
    cached = get_ai_cached_answer(phone, question)

    if cached:
        log_api_usage("OPENAI_CACHE", 0)
        return cached

    # ---------- RATE LIMIT ----------
    now = time.time()

    if now - LAST_CALL.get(phone, 0) < COOLDOWN:
        return "⏳ Please wait a moment before asking again."

    LAST_CALL[phone] = now

    if not client:
        return "⚠️ AI service unavailable right now."

    # ---------- DATA ----------

    lang = data.get("lang", "EN")
    astro_system = data.get("astro_system", "LAHIRI")
    kundali = data.get("kundali", {})

    planets_text = format_planets(kundali.get("planets", []))
    lords_text = format_house_lords(kundali.get("house_lords", {}))
    aspects_text = format_aspects(kundali.get("aspects", []))
    transits_text = format_transits(get_daily_transits())

    yogas = kundali.get("yogas", [])
    yogas_text = "\n".join(y["name"] for y in yogas) if yogas else "None"

    dasha_timeline = kundali.get("dasha_timeline", {})
    dasha_text = format_dasha_timeline(dasha_timeline)
    key_months = extract_key_months(dasha_timeline)

    calendar_text = build_month_calendar()

    qtype = classify_question(question)

    # ---------- PROMPTS ----------

    system_instruction = build_system_prompt(lang, astro_system)

    user_prompt = f"""
CLIENT DETAILS
Name: {data.get('name')}
DOB: {data.get('dob')} {data.get('time')}
Place: {data.get('place')}

CORE CHART
Ascendant: {kundali.get('lagna')}
Sun Sign: {kundali.get('sun_sign')}
Moon Sign: {kundali.get('moon_sign')}
Nakshatra: {kundali.get('nakshatra')} (Pada {kundali.get('pada')})

PLANETS:
{planets_text}

HOUSE LORDS:
{lords_text}

ASPECTS:
{aspects_text}

YOGAS:
{yogas_text}

MANGLIK:
{kundali.get('manglik')}

DASHA + ANTARDASHA:
{dasha_text}

IMPORTANT UPCOMING MONTHS:
{key_months}

CURRENT TRANSITS:
{transits_text}

MONTH CALENDAR:
{calendar_text}

ANALYSIS FOCUS:
{RULE_FOCUS[qtype]}

USER QUESTION:
{question}
"""

    logger.info(f"🔮 Calling OpenAI: {question}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1100
        )

        answer = response.choices[0].message.content.strip()

        final_answer = f"🔮 *Vedic Astrology Insight*\n\n{answer}"

        save_ai_answer(phone, question, final_answer)

        log_api_usage("OPENAI", OPENAI_COST_PER_CALL)
        use_api_credit("OPENAI", 1)

        return final_answer

    except Exception as e:
        logger.error(f"❌ OpenAI error: {e}")

        return (
            "⚠️ AI service is busy right now.\n"
            "Please try again in a few minutes."
        )
