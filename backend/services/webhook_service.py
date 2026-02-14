"""
Idempotent Webhook Processing Service
Prevents race conditions and duplicate payment processing
"""

from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class WebhookStatus(Enum):
    """Webhook processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"


class WebhookService:
    """
    Idempotent webhook processor
    
    Ensures webhooks are processed exactly once,
    even if Razorpay sends duplicates
    """
    
    def __init__(self, webhook_repo, order_repo, entitlement_service):
        """
        Initialize webhook service
        
        Args:
            webhook_repo: WebhookRepository instance
            order_repo: OrderRepository instance
            entitlement_service: EntitlementService instance
        """
        self.webhook_repo = webhook_repo
        self.order_repo = order_repo
        self.entitlement_service = entitlement_service
    
    def process_event(
        self,
        event_id: str,
        event_type: str,
        event_data: dict
    ) -> Dict[str, Any]:
        """
        Process webhook event idempotently
        
        Args:
            event_id: Unique event ID from Razorpay
            event_type: Event type (e.g., 'payment.captured')
            event_data: Full event payload
        
        Returns:
            dict: Processing result
        """
        logger.info(f"Processing webhook event: {event_id} - {event_type}")
        
        # Step 1: Check if event already processed (idempotency check)
        if self.webhook_repo.event_exists(event_id):
            logger.warning(f"Duplicate webhook event detected: {event_id}")
            return {
                "status": WebhookStatus.DUPLICATE.value,
                "message": "Event already processed",
                "event_id": event_id
            }
        
        # Step 2: Store event atomically (within transaction)
        try:
            self.webhook_repo.store_event(
                event_id=event_id,
                event_type=event_type,
                payload=event_data,
                status=WebhookStatus.PENDING.value
            )
        except Exception as e:
            # If store fails (duplicate), another thread processed it
            logger.warning(f"Failed to store event (likely duplicate): {e}")
            return {
                "status": WebhookStatus.DUPLICATE.value,
                "message": "Event already being processed",
                "event_id": event_id
            }
        
        # Step 3: Route to appropriate handler
        handler_map = {
            "payment.captured": self._handle_payment_captured,
            "payment.failed": self._handle_payment_failed,
            "refund.created": self._handle_refund_created,
        }
        
        handler = handler_map.get(event_type)
        
        if not handler:
            logger.error(f"Unknown event type: {event_type}")
            self.webhook_repo.update_status(event_id, WebhookStatus.FAILED.value)
            return {
                "status": WebhookStatus.FAILED.value,
                "error": f"Unknown event type: {event_type}",
                "event_id": event_id
            }
        
        # Step 4: Process event
        try:
            result = handler(event_id, event_data)
            self.webhook_repo.update_status(event_id, WebhookStatus.COMPLETED.value)
            return result
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            self.webhook_repo.update_status(
                event_id,
                WebhookStatus.FAILED.value,
                error_message=str(e)
            )
            return {
                "status": WebhookStatus.FAILED.value,
                "error": str(e),
                "event_id": event_id
            }
    
    def _handle_payment_captured(self, event_id: str, event_data: dict) -> dict:
        """
        Handle payment.captured event
        
        This is where the magic happens - atomic order update with row locking
        """
        payload = event_data.get("payload", {})
        payment = payload.get("payment", {})
        
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        amount = payment.get("amount", 0) / 100  # Convert paise to rupees
        
        if not order_id:
            raise ValueError("Missing order_id in payment event")
        
        logger.info(f"Processing payment captured: order={order_id}, payment={payment_id}")
        
        # CRITICAL: Use transaction with row-level lock
        with self.order_repo.atomic_transaction():
            # Step 1: Get order with FOR UPDATE lock (prevents concurrent updates)
            order = self.order_repo.get_by_razorpay_order_id_with_lock(order_id)
            
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Step 2: Validate order state
            if order.status not in ["INITIATED", "PENDING"]:
                logger.warning(
                    f"Order {order_id} status={order.status}, expected PENDING. "
                    f"Likely already processed."
                )
                return {
                    "status": "invalid_state",
                    "message": f"Order status is {order.status}",
                    "order_id": order_id
                }
            
            # Step 3: Validate amount
            if abs(order.amount - amount) > 0.01:  # Allow 1 paisa difference
                raise ValueError(
                    f"Amount mismatch: order={order.amount}, payment={amount}"
                )
            
            # Step 4: Update order (still within locked transaction)
            order.status = "PROCESSING"
            order.razorpay_payment_id = payment_id
            order.updated_at = datetime.now()
            self.order_repo.save(order)
            
            # Step 5: Grant entitlement (idempotent - service handles duplicates)
            try:
                self.entitlement_service.grant(
                    user_id=order.user_id,
                    product_type=order.product_type,
                    order_id=order.id,
                    metadata={
                        "event_id": event_id,
                        "payment_id": payment_id
                    }
                )
            except Exception as e:
                logger.error(f"Failed to grant entitlement: {e}")
                # Don't raise - we'll retry via background job
            
            # Step 6: Update final order status
            order.status = "SUCCESS"
            order.paid_at = datetime.now()
            self.order_repo.save(order)
            
            # Transaction commits here (lock released)
        
        # Step 7: Queue background notifications (after transaction)
        try:
            from app.workers.notification_worker import send_success_notification
            send_success_notification.delay(
                user_id=order.user_id,
                product_type=order.product_type,
                order_id=order.id
            )
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            # Don't fail the webhook - notification can be retried
        
        logger.info(f"✅ Payment processed successfully: order={order_id}")
        
        return {
            "status": "success",
            "order_id": order_id,
            "user_id": order.user_id,
            "product_type": order.product_type,
            "amount": amount
        }
    
    def _handle_payment_failed(self, event_id: str, event_data: dict) -> dict:
        """
        Handle payment.failed event
        """
        payload = event_data.get("payload", {})
        payment = payload.get("payment", {})
        
        order_id = payment.get("order_id")
        error_code = payment.get("error_code")
        error_description = payment.get("error_description")
        
        logger.info(f"Processing payment failed: order={order_id}, error={error_code}")
        
        with self.order_repo.atomic_transaction():
            order = self.order_repo.get_by_razorpay_order_id_with_lock(order_id)
            
            if order:
                order.status = "FAILED"
                order.error_code = error_code
                order.error_description = error_description
                order.updated_at = datetime.now()
                self.order_repo.save(order)
        
        # Queue retry notification (if retries enabled)
        try:
            from app.workers.payment_worker import queue_payment_retry
            queue_payment_retry.delay(order.id)
        except Exception as e:
            logger.error(f"Failed to queue retry: {e}")
        
        return {
            "status": "failed",
            "order_id": order_id,
            "error": error_code
        }
    
    def _handle_refund_created(self, event_id: str, event_data: dict) -> dict:
        """
        Handle refund.created event
        """
        payload = event_data.get("payload", {})
        refund = payload.get("refund", {})
        payment_id = refund.get("payment_id")
        amount = refund.get("amount", 0) / 100
        
        logger.info(f"Processing refund: payment={payment_id}, amount={amount}")
        
        with self.order_repo.atomic_transaction():
            order = self.order_repo.get_by_payment_id_with_lock(payment_id)
            
            if order:
                # Revoke entitlement
                try:
                    self.entitlement_service.revoke(
                        user_id=order.user_id,
                        product_type=order.product_type,
                        order_id=order.id,
                        reason="REFUND"
                    )
                except Exception as e:
                    logger.error(f"Failed to revoke entitlement: {e}")
                
                order.status = "REFUNDED"
                order.updated_at = datetime.now()
                self.order_repo.save(order)
        
        return {
            "status": "refunded",
            "payment_id": payment_id,
            "amount": amount
        }
    
    def get_event_status(self, event_id: str) -> Optional[str]:
        """
        Get processing status of an event
        
        Args:
            event_id: Event ID
        
        Returns:
            str: Status or None if not found
        """
        return self.webhook_repo.get_event_status(event_id)
    
    def retry_failed_event(self, event_id: str) -> dict:
        """
        Retry a failed webhook event
        
        Args:
            event_id: Event ID to retry
        
        Returns:
            dict: Retry result
        """
        event = self.webhook_repo.get_event(event_id)
        
        if not event:
            return {"error": "Event not found"}
        
        if event.status != WebhookStatus.FAILED.value:
            return {"error": f"Event status is {event.status}, cannot retry"}
        
        # Reset status to pending
        self.webhook_repo.update_status(event_id, WebhookStatus.PENDING.value)
        
        # Reprocess
        return self.process_event(
            event_id=event.event_id,
            event_type=event.event_type,
            event_data=json.loads(event.payload)
        )


# ===================
# HELPER FUNCTIONS
# ===================

def extract_order_id_from_event(event_data: dict) -> Optional[str]:
    """
    Extract order ID from webhook event
    
    Args:
        event_data: Webhook event payload
    
    Returns:
        str: Order ID or None
    """
    try:
        return event_data.get("payload", {}).get("payment", {}).get("order_id")
    except Exception:
        return None


def extract_payment_id_from_event(event_data: dict) -> Optional[str]:
    """
    Extract payment ID from webhook event
    
    Args:
        event_data: Webhook event payload
    
    Returns:
        str: Payment ID or None
    """
    try:
        return event_data.get("payload", {}).get("payment", {}).get("id")
    except Exception:
        return None


def is_retry_event(event_data: dict) -> bool:
    """
    Check if this is a retry/duplicate event from Razorpay
    
    Args:
        event_data: Webhook event payload
    
    Returns:
        bool: True if this is a retry
    """
    # Razorpay doesn't explicitly mark retries,
    # so we use our idempotency check (event_id)
    # This is just a helper to log retries
    return False  # Actual check done by event_exists()


if __name__ == "__main__":
    # Example usage (requires actual repositories)
    print("Idempotent Webhook Service")
    print("This service ensures webhooks are processed exactly once.")
    print("Even if Razorpay sends duplicate events, only one will succeed.")