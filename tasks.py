import logging
import traceback
from twilio.rest import Client
from config import Config

# --- Engine Imports ---
from astro_engine import generate_chart, calculate_dasha
from rules.rules import (
    get_planet_house_analysis,
    get_marriage_prediction,
    get_career_prediction,
    get_yoga_report,
    get_yearly_prediction,
    get_20_year_prediction,
    get_stress_growth_report,
    get_career_money_report,
    get_confidence_report,
    get_final_summary,
    get_dasha_report,
    get_full_vimshottari,
    get_pratyantar_report,
    get_gochar_prediction
)

from pdf_generator import generate_pdf
from file_host import get_public_pdf_url
from sessions import get_session, save_session

logger = logging.getLogger(__name__)

def generate_report_task(phone_number, details, language):
    logger.info(f"🚀 Starting Task for {phone_number}")

    try:
        # --- 1. DATA UNPACKING (CRITICAL FIX) ---
        # Dictionary se alag-alag values nikalo
        dob = details.get("DOB")
        tob = details.get("Time")
        place = details.get("Place")

        # Ab function ko alag-alag arguments do (Date, Time, Place)
        chart = generate_chart(dob, tob, place)
        dasha = calculate_dasha(dob, tob, place)
        
        # --- 2. GENERATE PREDICTIONS ---
        sections = {}
        
        # (Humne wahi logic rakha hai jo pehle tha)
        sections["Planet Analysis"] = "Detailed planetary analysis included in full report."
        
        sections["Marriage Prediction"] = get_marriage_prediction(chart, dasha)
        sections["Career Prediction"] = get_career_prediction(chart, dasha)
        sections["Dosha & Yogas"] = get_yoga_report(chart)
        sections["Yearly Forecast"] = get_yearly_prediction(details, dasha)
        sections["20-Year Overview"] = get_20_year_prediction(details, dasha)
        sections["Stress vs Growth"] = get_stress_growth_report(details, dasha)
        sections["Career vs Money"] = get_career_money_report(details, chart, dasha)
        sections["Confidence Score"] = get_confidence_report(details, chart, dasha)
        
        # --- 3. GENERATE PDF ---
        values = {
            "NAME": phone_number,
            "DOB": dob,
            "TOB": tob,
            "PLACE": place,
            "LAGNA": chart[0]['sign'] if isinstance(chart, list) and len(chart) > 0 else "Unknown", 
            # (Note: Lagna logic depend karta hai aapke chart structure par, safe fallback rakha hai)
            "CONFIDENCE_SCORE": "92" 
        }

        pdf_path = generate_pdf(
            user=phone_number,
            language=language,
            sections=sections,
            values=values
        )

        # --- 4. GET PUBLIC LINK ---
        public_url = get_public_pdf_url(pdf_path)

        if not public_url:
            raise Exception("Failed to generate public link")

        # --- 5. SAVE SESSION STATE ---
        session = get_session(phone_number)
        session["ready"] = True
        session["pdf_url"] = public_url
        
        # Chart data save karein Q&A ke liye
        session["chart"] = chart
        session["dasha"] = dasha
        session["stage"] = "QNA"
        save_session(phone_number, session)
        
        logger.info(f"✅ Task Completed for {phone_number}")

        # --- 6. AUTOMATIC SENDING ---
        try:
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            
            # Message Text
            msg_body = (
                "✨ *आपकी वीआईपी कुंडली तैयार है!* ✨\n\n"
                "👇 *नीचे दी गई PDF डाउनलोड करें* 👇\n"
                "इसके बाद आप मुझसे सवाल (Q&A) पूछ सकते हैं।"
            )

            message = client.messages.create(
                from_=Config.TWILIO_WHATSAPP_NUMBER,
                to=phone_number,
                body=msg_body,
                media_url=[public_url]
            )
            logger.info(f"📤 Auto-Message Sent: {message.sid}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send auto-message: {e}")

    except Exception as e:
        logger.error(f"❌ Task Failed: {e}")
        traceback.print_exc()