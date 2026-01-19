import os

# ---------------------------------------------
# 👇 अपना Ngrok URL यहाँ पेस्ट करें (http/https के साथ)
# यह वही लिंक होना चाहिए जो अभी Ngrok टर्मिनल में चल रहा है
# ---------------------------------------------
BASE_URL = "https://asternal-misty-undeprecated.ngrok-free.dev" 
# 👆 अगर आपका Ngrok URL बदल गया है, तो इसे अपडेट करें!

def get_public_pdf_url(filepath):
    """
    Bypasses AWS S3.
    Serves the PDF directly from your laptop via Ngrok.
    """
    try:
        # File ka naam nikalo (e.g., VIP_Kundali_123.pdf)
        filename = os.path.basename(filepath)
        
        # Local Link banao
        # app.py mein humne '/generated_pdfs/' route banaya hai, ye wahi use karega
        public_url = f"{BASE_URL}/generated_pdfs/{filename}"
        
        print(f"✅ Local PDF Link Generated: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Error generating link: {e}")
        return None