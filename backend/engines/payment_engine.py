import logging

logger = logging.getLogger(__name__)

# ==========================================
# 🚧 BYPASS MODE PAYMENT ENGINE
# ==========================================

def create_order(phone):
    """
    Returns a dummy link. 
    In 'Bypass Mode', clicking this isn't strictly necessary 
    if verify_payment() returns True, but we need to return a string 
    so the bot doesn't crash when creating the button.
    """
    logger.info(f"🚧 BYPASS: Generating dummy link for {phone}")
    
    # This acts as a dummy 'Pay Now' link. 
    # You can just send any message to the bot to proceed.
    return "https://wa.me/settings" 

def verify_payment(phone):
    """
    ALWAYS returns True.
    This tells the bot 'Yes, this user has paid' no matter what.
    """
    logger.info(f"🚧 BYPASS: Auto-approving payment for {phone}")
    return True

def verify_webhook_signature(request_data, signature):
    """
    Dummy signature check always returning True.
    """
    return True