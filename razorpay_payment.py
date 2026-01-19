import razorpay
import time
import logging
from config import Config

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))

def create_payment_link(user_phone, amount=99):
    """
    Generates a payment link for the user to upgrade to VIP.
    """
    if not Config.ENABLE_PAYMENTS:
        return None, "Payments are currently disabled."

    try:
        # Expire link in 15 minutes to prevent spam
        expire_by = int(time.time()) + (15 * 60)

        payload = {
            "amount": amount * 100,  # Amount in paise (99 INR -> 9900)
            "currency": "INR",
            "accept_partial": False,
            "description": "Upgrade to Ultimate VIP Kundali",
            "customer": {
                "contact": user_phone,
                "email": "user@example.com"  # Optional, or ask user for email
            },
            "notify": {
                "sms": True,
                "email": False
            },
            "reminder_enable": True,
            "notes": {
                "user_phone": user_phone,
                "plan": "vip"
            },
            "expire_by": expire_by
        }

        response = client.payment_link.create(payload)
        
        short_url = response.get("short_url")
        link_id = response.get("id")
        
        logger.info(f"💰 Generated Payment Link for {user_phone}: {short_url}")
        return short_url, link_id

    except Exception as e:
        logger.error(f"❌ Razorpay Error: {e}")
        return None, None

def verify_signature(request_data, signature):
    """
    Verifies that the webhook actually came from Razorpay.
    """
    try:
        # Razorpay expects the raw body as bytes/string for verification
        return client.utility.verify_webhook_signature(
            request_data,
            signature,
            Config.RAZORPAY_WEBHOOK_SECRET  # You need to add this to Config
        )
    except Exception as e:
        logger.error(f"❌ Signature Verification Failed: {e}")
        return False