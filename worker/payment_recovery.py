"""
Payment Recovery Worker
Recovers abandoned payments through automated reminders
Expected Impact: +₹4,00,000/month
"""

from celery import shared_task
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(name='backend.workers.payment_recovery.recover_abandoned_payments', bind=True, max_retries=3)
def recover_abandoned_payments(self):
    """
    Periodic task to recover abandoned payments
    
    Runs every hour to:
    1. Find pending orders older than 1 hour
    2. Send reminder with payment link
    3. Offer discount if older than 24 hours
    
    Returns:
        dict: Recovery statistics
    """
    logger.info("🔄 Starting abandoned payment recovery...")
    
    from backend.services.payment.payment_service import get_payment_service
    from backend.services.notification.notification_service import get_notification_service
    from backend.engines.db_engine import get_conn
    
    payment_service = get_payment_service()
    notification_service = get_notification_service()
    
    stats = {
        "total_abandoned": 0,
        "reminders_sent": 0,
        "discounts_offered": 0,
        "errors": 0
    }
    
    try:
        # Get pending orders older than 1 hour
        pending_orders = payment_service.get_pending_orders(older_than_minutes=60)
        stats["total_abandoned"] = len(pending_orders)
        
        logger.info(f"📊 Found {len(pending_orders)} abandoned payments")
        
        for order in pending_orders:
            try:
                phone = order.get("phone")
                product_type = order.get("product_type")
                order_id = order.get("order_id")
                razorpay_order_id = order.get("razorpay_order_id")
                created_at = datetime.fromisoformat(order.get("created_at"))
                hours_old = (datetime.now() - created_at).total_seconds() / 3600
                
                # Skip if already reminded in last 12 hours
                if _was_recently_reminded(order_id):
                    continue
                
                # Generate payment link
                payment_link = f"https://razorpay.com/payment-link/{razorpay_order_id}"
                
                # Strategy based on age
                if hours_old >= 24:
                    # Offer 10% discount after 24 hours
                    success = _send_discount_offer(
                        phone, product_type, payment_link, order_id
                    )
                    if success:
                        stats["discounts_offered"] += 1
                        stats["reminders_sent"] += 1
                
                else:
                    # Simple reminder for 1-24 hours old
                    success = notification_service.send_payment_reminder(
                        phone=phone,
                        product_type=product_type,
                        payment_link=payment_link,
                        hours_since=int(hours_old)
                    )
                    if success:
                        stats["reminders_sent"] += 1
                
                # Mark as reminded
                _mark_as_reminded(order_id)
            
            except Exception as e:
                logger.error(f"❌ Error processing abandoned order {order_id}: {e}")
                stats["errors"] += 1
                continue
        
        logger.info(f"✅ Recovery complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"❌ Abandoned payment recovery failed: {e}", exc_info=True)
        # Retry after 5 minutes
        raise self.retry(exc=e, countdown=300)


def _send_discount_offer(phone: str, product_type: str, payment_link: str, order_id: str) -> bool:
    """Send special discount offer for old abandoned orders"""
    from backend.services.notification.notification_service import get_notification_service
    
    offer_message = f"""
🎁 *Special Offer - 10% Discount!*

Complete your {product_type} payment and get 10% OFF!

Original: ₹{_get_product_price(product_type)}
Discounted: ₹{int(_get_product_price(product_type) * 0.9)}

Pay here: {payment_link}

Offer valid for 6 hours only!
Reply 'INTERESTED' to get help.
"""
    
    notification_service = get_notification_service()
    return notification_service._send_message(phone, offer_message.strip())


def _get_product_price(product_type: str) -> int:
    """Get product price"""
    from backend.config import Config
    
    prices = {
        "KUNDALI": Config.KUNDALI_PRICE,
        "QNA": Config.QNA_PRICE,
        "MILAN": Config.MILAN_PRICE
    }
    return prices.get(product_type, 0)


def _was_recently_reminded(order_id: str, hours: int = 12) -> bool:
    """Check if order was reminded in last N hours"""
    from backend.engines.db_engine import get_conn
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Create reminder_log table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_reminder_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                reminded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check recent reminders
        cutoff = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM payment_reminder_log
            WHERE order_id = ?
            AND reminded_at > ?
        """, (order_id, cutoff))
        
        result = cursor.fetchone()
        conn.close()
        
        return result["count"] > 0
    
    except Exception as e:
        logger.debug(f"Error checking reminder log: {e}")
        return False


def _mark_as_reminded(order_id: str):
    """Mark order as reminded"""
    from backend.engines.db_engine import get_conn
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO payment_reminder_log (order_id)
            VALUES (?)
        """, (order_id,))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.debug(f"Error marking reminder: {e}")


@shared_task(name='backend.workers.payment_recovery.send_payment_reminder')
def send_payment_reminder(phone: str, product_type: str, order_id: str):
    """
    Send single payment reminder (can be called manually)
    
    Args:
        phone: User phone
        product_type: Product type
        order_id: Order ID
    """
    from backend.services.notification.notification_service import get_notification_service
    from backend.services.payment.payment_service import get_payment_service
    
    try:
        payment_service = get_payment_service()
        order = payment_service.get_order_status(order_id)
        
        if not order.get("success") or order.get("status") != "PENDING":
            return {"success": False, "reason": "Order not pending"}
        
        # Generate payment link
        razorpay_order_id = order.get("razorpay_order_id")
        payment_link = f"https://razorpay.com/payment-link/{razorpay_order_id}"
        
        # Send reminder
        notification_service = get_notification_service()
        success = notification_service.send_payment_reminder(
            phone=phone,
            product_type=product_type,
            payment_link=payment_link
        )
        
        if success:
            _mark_as_reminded(order_id)
        
        return {"success": success}
    
    except Exception as e:
        logger.error(f"❌ Failed to send reminder: {e}")
        return {"success": False, "error": str(e)}