import logging
from services.prokerala import get_prokerala_data
from pdf_egine import generate_pdf
from file_host import get_public_pdf_url
from sessions import get_session, save_session
from razorpay_payment import create_payment_link
from twilio.rest import Client
from config import Config

logger = logging.getLogger(__name__)

def format_astro_data_for_pdf(data):
    """
    Converts raw JSON data into readable strings for the PDF generator.
    """
    sections = {}
    
    # 1. Format Planet Positions
    planets = data.get("planets", [])
    p_text = "Planet | Rasi | Degree\n----------------------\n"
    for p in planets:
        p_name = p.get("name", "")
        rasi = p.get("rasi", {}).get("name", "")
        deg = p.get("longitude", 0.0)
        p_text += f"{p_name} | {rasi} | {deg:.2f}\n"
    sections["Planetary Positions"] = p_text

    # 2. Format Mangal Dosha
    dosha = data.get("dosha", {})
    has_dosha = "Yes" if dosha.get("has_mangal_dosha") else "No"
    desc = dosha.get("description", "No description available.")
    sections["Mangal Dosha Analysis"] = f"Has Dosha: {has_dosha}\n\n{desc}"
    
    # 3. Add placeholder for charts (since PDF gen handles text)
    sections["Chart Overview"] = "Detailed Rasi and Navamsa charts are calculated based on your birth time."
    
    return sections

def generate_report_task(phone_number, details, language):
    logger.info(f"🚀 Starting Task for {phone_number}")
    session = get_session(phone_number)

    try:
        # 1. Fetch Data from Prokerala
        dob = details.get("DOB")
        tob = details.get("Time")
        place = details.get("Place")
        
        astro_data = get_prokerala_data(dob, tob, place)
        
        # 2. Save Raw Data for Q&A Later
        session["astro_data"] = astro_data
        save_session(phone_number, session)

        # 3. Generate PDF
        # Convert JSON to text sections for the PDF
        pdf_sections = format_astro_data_for_pdf(astro_data)
        
        pdf_path = generate_pdf(
            user=phone_number,
            language=language,
            sections=pdf_sections,
            values=details
        )
        
        # Get public URL
        pdf_url = get_public_pdf_url(pdf_path)
        
        # 4. Update Session: Report Ready but Payment Pending
        session = get_session(phone_number) 
        session["pdf_url"] = pdf_url
        session["ready"] = True
        session["payment_status"] = "PENDING"
        save_session(phone_number, session)

        # 5. Generate Payment Link
        link, link_id = create_payment_link(phone_number, amount=99)

        # 6. Send WhatsApp Message
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        msg_body = (
            "✅ *Kundali Generated Successfully!* \n\n"
            "Your premium PDF report is ready. \n"
            "To download the file and unlock the AI Astrologer (Q&A), please pay ₹99.\n\n"
            f"👇 *Pay Here to Unlock:* \n{link}"
        )

        client.messages.create(
            from_=Config.TWILIO_WHATSAPP_NUMBER,
            to=phone_number,
            body=msg_body
        )
        logger.info(f"💰 Payment link sent to {phone_number}")

    except Exception as e:
        logger.error(f"❌ Task Failed: {e}")
        # Optional: Send error message to user