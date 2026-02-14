"""
Production Payment Engine with Real Razorpay Integration
Handles order creation, payment verification, and webhook processing
"""

import logging
import time
import hmac
import hashlib
import razorpay
from datetime import datetime, timedelta
from twilio.rest import Client
from backend.config import Config
from backend.engines.db_engine import get_conn

logger = logging.getLogger(__name__)

# Initialize Twilio Client for proactive notifications
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)


# =========================
# RAZORPAY CLIENT INIT
# =========================

def update_payment_status(order_id, status, payment_id=None, error_message=None):
    """Updates DB and triggers the WhatsApp bot immediately on success"""
    conn = get_conn()
    cur = conn.cursor()
    
    if payment_id:
        cur.execute("""
            UPDATE payment_orders 
            SET status=?, payment_id=?, error_message=?, updated_at=CURRENT_TIMESTAMP
            WHERE order_id=?
        """, (status, payment_id, error_message, order_id))
    else:
        cur.execute("""
            UPDATE payment_orders 
            SET status=?, error_message=?, updated_at=CURRENT_TIMESTAMP
            WHERE order_id=?
        """, (status, error_message, order_id))
    
    conn.commit()
    
    # NEW: Automatically notify user if payment is SUCCESS
    if status == 'SUCCESS':
        cur.execute("SELECT phone, product_type FROM payment_orders WHERE order_id=?", (order_id,))
        order = cur.fetchone()
        if order:
            send_proactive_confirmation(order['phone'], order['product_type'])
    
    conn.close()
    logger.info(f"📊 Payment status updated: {order_id} → {status}")

def send_proactive_confirmation(phone, product_type):
    """Sends a WhatsApp message automatically when the webhook hits"""
    try:
        # Ensure phone format is correct for Twilio
        to_number = phone if "whatsapp:" in phone else f"whatsapp:{phone}"
        
        body_text = (
            f"✅ *Payment Received!*\n\n"
            f"Your payment for *{product_type}* was successful. "
            f"Please wait while we generate your report... ⏳"
        )
        
        twilio_client.messages.create(
            from_=Config.TWILIO_WHATSAPP_NUMBER,
            body=body_text,
            to=to_number
        )
        logger.info(f"🚀 Automatic confirmation sent to {phone}")
    except Exception as e:
        logger.error(f"❌ Failed to send automatic confirmation: {e}")

# ... (keep your existing create_order and verify_webhook_signature
    


# =========================
# PRODUCT PRICING
# =========================

PRODUCT_PRICES = {
    "KUNDALI": Config.KUNDALI_PRICE,
    "QNA": Config.QNA_PRICE,
    "MILAN": Config.MILAN_PRICE
}


# =========================
# CREATE ORDER
# =========================

def create_order(phone, product_type="KUNDALI"):
    """
    Create a Razorpay payment order
    
    Args:
        phone: User phone number
        product_type: 'KUNDALI', 'QNA', or 'MILAN'
    
    Returns:
        str: Payment link URL or None if failed
    """
    
    if not razorpay_client:
        logger.error("Razorpay client not initialized")
        return None
    
    # Get product price
    amount = PRODUCT_PRICES.get(product_type, 200)
    
    try:
        # Create order data
        order_data = {
            "amount": amount * 100,  # Convert to paise (1 INR = 100 paise)
            "currency": "INR",
            "receipt": f"{phone}_{product_type}_{int(time.time())}",
            "notes": {
                "phone": phone,
                "product": product_type,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Create order via Razorpay API
        order = razorpay_client.order.create(data=order_data)
        
        order_id = order['id']
        
        # Save to database
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO payment_orders(phone, order_id, amount, currency, product_type, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', CURRENT_TIMESTAMP)
        """, (phone, order_id, amount, "INR", product_type))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Order created: {order_id} for {phone} - {product_type} - ₹{amount}")
        
        # Generate payment link
        # Generate real payment link using Razorpay Payment Links API
        payment_link = create_payment_link(order_id, amount, phone, product_type)
        
        # Option 2: Payment link API (if you have it configured)
        # payment_link = create_payment_link(order_id, amount, phone, product_type)
        
        return payment_link
        
    except Exception as e:
        logger.error(f"❌ Order creation failed: {e}")
        return None


# =========================
# VERIFY PAYMENT
# =========================

def verify_payment(phone, order_id, payment_id, signature):
    """
    Verify Razorpay payment signature
    
    Args:
        phone: User phone number
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Razorpay signature
    
    Returns:
        bool: True if payment is valid, False otherwise
    """
    
    if not razorpay_client:
        logger.error("Razorpay client not initialized")
        return False
    
    try:
        # Get order from database
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
        SELECT * FROM payment_orders 
        WHERE phone=? AND order_id=? AND status='PENDING'
        """, (phone, order_id))
        
        order = cur.fetchone()
        
        if not order:
            logger.warning(f"Order not found or already processed: {order_id}")
            conn.close()
            return False
        
        # Verify signature
        generated_signature = hmac.new(
            Config.RAZORPAY_KEY_SECRET.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(generated_signature, signature):
            logger.warning(f"Invalid signature for {phone}, order {order_id}")
            conn.close()
            return False
        
        # Fetch payment details from Razorpay
        payment = razorpay_client.payment.fetch(payment_id)
        
        # Verify payment status
        if payment['status'] != 'captured':
            logger.warning(f"Payment not captured: {payment_id}, status: {payment['status']}")
            conn.close()
            return False
        
        # Verify amount matches
        if payment['amount'] != order['amount'] * 100:
            logger.error(f"Amount mismatch! Expected {order['amount']*100}, got {payment['amount']}")
            conn.close()
            return False
        
        # Update payment status
        cur.execute("""
        UPDATE payment_orders 
        SET status='SUCCESS', payment_id=?, updated_at=CURRENT_TIMESTAMP
        WHERE order_id=?
        """, (payment_id, order_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Payment verified: {payment_id} for {phone}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Payment verification failed: {e}")
        return False


# =========================
# CHECK PAYMENT STATUS
# =========================

def check_payment_status(phone):
    """
    Check if user has any successful payment in last 24 hours
    
    Args:
        phone: User phone number
    
    Returns:
        bool: True if user has paid recently, False otherwise
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Check for successful payment in last 24 hours
    cur.execute("""
    SELECT COUNT(*) as count FROM payment_orders 
    WHERE phone=? AND status='SUCCESS' 
    AND updated_at >= datetime('now', '-1 day')
    """, (phone,))
    
    result = cur.fetchone()
    conn.close()
    
    has_payment = result['count'] > 0 if result else False
    
    if has_payment:
        logger.info(f"✅ Payment status check: {phone} has recent payment")
    
    return has_payment


# =========================
# WEBHOOK SIGNATURE VALIDATION
# =========================

def verify_webhook_signature(payload, signature):
    """
    Verify Razorpay webhook signature
    
    CRITICAL: This prevents fake webhook requests
    
    Args:
        payload: Raw webhook payload (bytes or string)
        signature: X-Razorpay-Signature header value
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    
    if not Config.RAZORPAY_WEBHOOK_SECRET:
        logger.error("Webhook secret not configured!")
        return False
    
    try:
        if isinstance(payload, str):
            payload = payload.encode()
        
        # Generate expected signature
        generated_signature = hmac.new(
            Config.RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        valid = hmac.compare_digest(generated_signature, signature)
        
        if not valid:
            logger.warning("❌ Invalid webhook signature")
        
        return valid
        
    except Exception as e:
        logger.error(f"❌ Webhook signature verification failed: {e}")
        return False


# =========================
# HANDLE WEBHOOK EVENTS
# =========================

def handle_payment_webhook(event_data):
    """
    Handle Razorpay webhook events
    
    Args:
        event_data: Webhook event data (dict)
    
    Returns:
        dict: Processing result
    """
    
    event = event_data.get('event', '')
    payload = event_data.get('payload', {})
    
    logger.info(f"📥 Webhook event: {event}")
    
    try:
        if event == 'payment.authorized':
            # Payment authorized but not captured yet
            payment = payload.get('payment', {}).get('entity', {})
            payment_id = payment.get('id')
            order_id = payment.get('order_id')
            
            logger.info(f"💳 Payment authorized: {payment_id} for order {order_id}")
            
            # Update status to AUTHORIZED
            update_payment_status(order_id, 'AUTHORIZED', payment_id)
        
        elif event == 'payment.captured':
            # Payment successfully captured
            payment = payload.get('payment', {}).get('entity', {})
            payment_id = payment.get('id')
            order_id = payment.get('order_id')
            amount = payment.get('amount') / 100  # Convert from paise
            
            logger.info(f"✅ Payment captured: {payment_id} for order {order_id} - ₹{amount}")
            
            # Update status to SUCCESS
            update_payment_status(order_id, 'SUCCESS', payment_id)
        
        elif event == 'payment.failed':
            # Payment failed
            payment = payload.get('payment', {}).get('entity', {})
            payment_id = payment.get('id')
            order_id = payment.get('order_id')
            error = payment.get('error_description', 'Unknown error')
            
            logger.warning(f"❌ Payment failed: {payment_id} for order {order_id} - {error}")
            
            # Update status to FAILED
            update_payment_status(order_id, 'FAILED', payment_id, error)
        
        elif event == 'order.paid':
            # Order fully paid
            order = payload.get('order', {}).get('entity', {})
            order_id = order.get('id')
            
            logger.info(f"✅ Order paid: {order_id}")
        
        else:
            logger.info(f"ℹ️ Unhandled event: {event}")
        
        return {"status": "success", "event": event}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}


# =========================
# UPDATE PAYMENT STATUS
# =========================

def update_payment_status(order_id, status, payment_id=None, error_message=None):
    """
    Update payment status in database
    
    Args:
        order_id: Razorpay order ID
        status: New status (AUTHORIZED, SUCCESS, FAILED, etc.)
        payment_id: Razorpay payment ID (optional)
        error_message: Error message if failed (optional)
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    if payment_id:
        cur.execute("""
        UPDATE payment_orders 
        SET status=?, payment_id=?, error_message=?, updated_at=CURRENT_TIMESTAMP
        WHERE order_id=?
        """, (status, payment_id, error_message, order_id))
    else:
        cur.execute("""
        UPDATE payment_orders 
        SET status=?, error_message=?, updated_at=CURRENT_TIMESTAMP
        WHERE order_id=?
        """, (status, error_message, order_id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"📊 Payment status updated: {order_id} → {status}")


# =========================
# GET ORDER DETAILS
# =========================

def get_order_details(order_id):
    """
    Get order details from database
    
    Args:
        order_id: Razorpay order ID
    
    Returns:
        dict: Order details or None
    """
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM payment_orders WHERE order_id=?
    """, (order_id,))
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return dict(row)


# =========================
# REFUND PAYMENT
# =========================

def refund_payment(payment_id, amount=None, reason="requested_by_customer"):
    """
    Process refund via Razorpay
    
    Args:
        payment_id: Razorpay payment ID
        amount: Amount to refund (None for full refund)
        reason: Refund reason
    
    Returns:
        dict: Refund details or None
    """
    
    if not razorpay_client:
        logger.error("Razorpay client not initialized")
        return None
    
    try:
        refund_data = {
            "payment_id": payment_id,
            "notes": {
                "reason": reason,
                "processed_at": datetime.now().isoformat()
            }
        }
        
        if amount:
            refund_data["amount"] = int(amount * 100)  # Convert to paise
        
        # Create refund
        refund = razorpay_client.payment.refund(payment_id, refund_data)
        
        logger.info(f"✅ Refund processed: {refund['id']} for payment {payment_id}")
        
        return refund
        
    except Exception as e:
        logger.error(f"❌ Refund failed: {e}")
        return None


# =========================
# PAYMENT LINK CREATION (Advanced)
# =========================

def create_payment_link(order_id, amount, phone, product_type):
    """
    Create custom payment link using Razorpay Payment Links API
    
    NOTE: Requires Payment Links API to be enabled on your Razorpay account
    
    Args:
        order_id: Order ID
        amount: Amount in INR
        phone: Customer phone
        product_type: Product type
    
    Returns:
        str: Payment link URL
    """
    
    if not razorpay_client:
        return f"https://rzp.io/i/{order_id}"
    
    try:
        link_data = {
            "amount": amount * 100,
            "currency": "INR",
            "description": f"Boloastro {product_type}",
            "customer": {
                "contact": phone.replace("whatsapp:", "")
            },
            "notify": {
                "sms": False,  # We'll notify via WhatsApp
                "email": False
            },
            "reminder_enable": False,
            "callback_url": "https://your-domain.com/payment/callback",
            "callback_method": "get"
        }
        
        # Create payment link
        link = razorpay_client.payment_link.create(link_data)
        
        logger.info(f"✅ Payment link created: {link['id']}")
        
        return link['short_url']
        
    except Exception as e:
        logger.error(f"❌ Payment link creation failed: {e}")
        # Fallback to standard link
        return f"https://rzp.io/i/{order_id}"