"""
Failed Payment Retry Worker
Automatically retries failed payments with new payment links
Expected Impact: +₹2,00,000/month
"""

from celery import shared_task
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(name='backend.workers.payment_retry.retry_failed_payments', bind=True, max_retries=3)
def retry_failed_payments(self):
    """
    Periodic task to retry failed payments
    
    Runs every 2 hours to:
    1. Find failed payments from last 24 hours
    2. Generate new payment link
    3. Send retry notification
    4. Track retry attempts
    
    Returns:
        dict: Retry statistics
    """
    logger.info("🔄 Starting failed payment retry process...")
    
    from backend.engines.db_engine import get_conn
    from backend.services.payment.payment_service import get_payment_service
    from backend.services.notification.notification_service import get_notification_service
    
    payment_service = get_payment_service()
    notification_service = get_notification_service()
    
    stats = {
        "total_failed": 0,
        "retry_links_sent": 0,
        "max_retries_reached": 0,
        "errors": 0
    }
    
    try:
        # Get failed payments from last 24 hours
        failed_orders = _get_failed_orders(hours=24)
        stats["total_failed"] = len(failed_orders)
        
        logger.info(f"📊 Found {len(failed_orders)} failed payments")
        
        for order in failed_orders:
            try:
                order_id = order.get("order_id")
                phone = order.get("phone")
                product_type = order.get("product_type")
                error_code = order.get("error_code")
                
                # Check retry count
                retry_count = _get_retry_count(order_id)
                
                from backend.config import Config
                max_retries = Config.MAX_PAYMENT_RETRY_ATTEMPTS
                
                if retry_count >= max_retries:
                    stats["max_retries_reached"] += 1
                    logger.info(f"⏭️ Max retries reached for {order_id}")
                    continue
                
                # Check if retriable error
                if not _is_retriable_error(error_code):
                    logger.info(f"⏭️ Non-retriable error for {order_id}: {error_code}")
                    continue
                
                # Generate new payment link
                new_order = payment_service.create_payment_order(
                    phone=phone,
                    product_type=product_type
                )
                
                if not new_order.get("success"):
                    logger.error(f"❌ Failed to create retry order for {order_id}")
                    stats["errors"] += 1
                    continue
                
                # Send retry notification
                payment_link = new_order.get("payment_link")
                success = _send_retry_notification(
                    phone=phone,
                    product_type=product_type,
                    payment_link=payment_link,
                    error_code=error_code,
                    retry_count=retry_count + 1
                )
                
                if success:
                    stats["retry_links_sent"] += 1
                    _increment_retry_count(order_id)
                    logger.info(f"✅ Retry link sent for {order_id} (attempt {retry_count + 1})")
            
            except Exception as e:
                logger.error(f"❌ Error processing failed order {order_id}: {e}")
                stats["errors"] += 1
                continue
        
        logger.info(f"✅ Retry process complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"❌ Failed payment retry process failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes


def _get_failed_orders(hours: int = 24):
    """Get failed orders from last N hours"""
    from backend.engines.db_engine import get_conn
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT *
        FROM payment_orders
        WHERE status = 'FAILED'
        AND created_at >= ?
        ORDER BY created_at DESC
    """, (cutoff_time,))
    
    orders = cursor.fetchall()
    conn.close()
    
    return [dict(order) for order in orders]


def _is_retriable_error(error_code: str) -> bool:
    """
    Check if error is retriable
    
    Retriable errors:
    - Insufficient balance
    - Card declined
    - Network issues
    - Timeout
    
    Non-retriable errors:
    - Invalid card
    - Fraud detected
    - Account closed
    """
    if not error_code:
        return True  # Unknown errors are retriable
    
    retriable_errors = [
        'insufficient_balance',
        'insufficient_funds',
        'card_declined',
        'transaction_declined',
        'network_error',
        'timeout',
        'gateway_error',
        'issuer_down',
        'try_again'
    ]
    
    non_retriable_errors = [
        'invalid_card',
        'fraud',
        'stolen_card',
        'lost_card',
        'restricted_card',
        'account_closed',
        'card_expired',
        'invalid_cvv',
        'incorrect_pin'
    ]
    
    error_lower = error_code.lower()
    
    # Check if explicitly non-retriable
    for err in non_retriable_errors:
        if err in error_lower:
            return False
    
    # Check if explicitly retriable
    for err in retriable_errors:
        if err in error_lower:
            return True
    
    # Default to retriable for unknown errors
    return True


def _send_retry_notification(
    phone: str,
    product_type: str,
    payment_link: str,
    error_code: str,
    retry_count: int
) -> bool:
    """Send retry notification with new payment link"""
    from backend.services.notification.notification_service import get_notification_service
    
    # Get user-friendly error message
    error_msg = _get_error_message(error_code)
    
    message = f"""
💳 *Payment Retry - Attempt #{retry_count}*

Your previous {product_type} payment failed.
Reason: {error_msg}

We've created a new payment link for you:
{payment_link}

💡 Tips:
- Check card balance
- Use different payment method
- Contact your bank if issue persists

Need help? Reply 'HELP'
"""
    
    notification_service = get_notification_service()
    return notification_service._send_message(phone, message.strip())


def _get_error_message(error_code: str) -> str:
    """Get user-friendly error message"""
    if not error_code:
        return "Payment processing error"
    
    error_messages = {
        'insufficient_balance': 'Insufficient balance in account',
        'card_declined': 'Card was declined by bank',
        'network_error': 'Network connectivity issue',
        'timeout': 'Payment timed out',
        'invalid_card': 'Invalid card details',
        'card_expired': 'Card has expired'
    }
    
    error_lower = error_code.lower()
    for key, msg in error_messages.items():
        if key in error_lower:
            return msg
    
    return "Payment processing issue"


def _get_retry_count(order_id: str) -> int:
    """Get retry count for order"""
    from backend.engines.db_engine import get_conn
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Create retry_log table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_retry_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                retry_attempt INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get max retry attempt
        cursor.execute("""
            SELECT COALESCE(MAX(retry_attempt), 0) as max_retry
            FROM payment_retry_log
            WHERE order_id = ?
        """, (order_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result["max_retry"]
    
    except Exception as e:
        logger.debug(f"Error getting retry count: {e}")
        return 0


def _increment_retry_count(order_id: str):
    """Increment retry count for order"""
    from backend.engines.db_engine import get_conn
    
    try:
        retry_count = _get_retry_count(order_id)
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO payment_retry_log (order_id, retry_attempt)
            VALUES (?, ?)
        """, (order_id, retry_count + 1))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.debug(f"Error incrementing retry count: {e}")


@shared_task(name='backend.workers.payment_retry.manual_retry')
def manual_retry(order_id: str):
    """
    Manual retry for specific order
    
    Args:
        order_id: Order ID to retry
    
    Returns:
        dict: Retry result
    """
    from backend.services.payment.payment_service import get_payment_service
    from backend.services.notification.notification_service import get_notification_service
    
    try:
        payment_service = get_payment_service()
        
        # Get order details
        order = payment_service.get_order_status(order_id)
        
        if not order.get("success"):
            return {"success": False, "error": "Order not found"}
        
        if order.get("status") != "FAILED":
            return {"success": False, "error": "Order is not failed"}
        
        # Create new order
        new_order = payment_service.create_payment_order(
            phone=order.get("phone"),
            product_type=order.get("product_type")
        )
        
        if not new_order.get("success"):
            return {"success": False, "error": "Failed to create retry order"}
        
        # Send notification
        notification_service = get_notification_service()
        notification_service._send_message(
            phone=order.get("phone"),
            message=f"New payment link: {new_order.get('payment_link')}"
        )
        
        # Increment retry count
        _increment_retry_count(order_id)
        
        return {
            "success": True,
            "new_order_id": new_order.get("order_id"),
            "payment_link": new_order.get("payment_link")
        }
    
    except Exception as e:
        logger.error(f"❌ Manual retry failed: {e}")
        return {"success": False, "error": str(e)}