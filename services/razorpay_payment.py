import razorpay
import time
import logging
import hmac
import hashlib
from config import Config

logger = logging.getLogger(__name__)

client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))

def create_payment_link(user_phone, amount=99):
    """
    Generates a payment link for ₹99.
    """
    try:
        expire_by = int(time.time()) + (15 * 60) # Link valid for 15 mins

        payload = {
            "amount": amount * 100,
            "currency": "INR",
            "accept_partial": False,
            "description": "Unlock Full Kundali Report & AI Bot",
            "customer": {
                "contact": user_phone
            },
            "notify": {"sms": True, "email": False},
            "reminder_enable": True,
            "notes": {
                "user_phone": user_phone,
                "service": "kundali_bot"
            },
            "expire_by": expire_by
        }

        response = client.payment_link.create(payload)
        return response.get("short_url"), response.get("id")

    except Exception as e:
        logger.error(f"Razorpay Creation Error: {e}")
        return None, None

def verify_signature(request_data, signature):
    """
    Manually verifies the Razorpay Webhook Signature.
    """
    try:
        secret = Config.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            logger.error("RAZORPAY_WEBHOOK_SECRET not set in Config")
            return False

        # Calculate HMAC SHA256
        generated_signature = hmac.new(
            key=bytes(secret, 'utf-8'),
            msg=request_data,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(generated_signature, signature)
    except Exception as e:
        logger.error(f"Signature Verification Failed: {e}")
        return False