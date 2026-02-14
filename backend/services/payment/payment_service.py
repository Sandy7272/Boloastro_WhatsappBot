"""
Payment Service
Handles all payment-related business logic
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import razorpay

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Payment Service - Handles payment operations
    
    Provides clean interface for payment operations while
    integrating with existing payment_engine.
    """
    
    def __init__(self, session=None):
        """
        Initialize payment service
        
        Args:
            session: SQLAlchemy session (optional)
        """
        self.session = session
        
        # Initialize Razorpay client
        from backend.config import Config
        self.razorpay_client = razorpay.Client(
            auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET)
        )
    
    def create_payment_order(
        self,
        phone: str,
        product_type: str,
        amount: float = None
    ) -> Dict:
        """
        Create payment order
        
        Args:
            phone: User phone number
            product_type: KUNDALI, QNA, or MILAN
            amount: Order amount (optional, uses default pricing)
        
        Returns:
            dict: Order details with payment link
        """
        from backend.engines.payment_engine import create_order
        from backend.config import Config
        
        # Get amount from pricing if not provided
        if amount is None:
            pricing = {
                "KUNDALI": Config.KUNDALI_PRICE,
                "QNA": Config.QNA_PRICE,
                "MILAN": Config.MILAN_PRICE
            }
            amount = pricing.get(product_type, 0)
        
        logger.info(f"💳 Creating payment order: {phone} - {product_type} - ₹{amount}")
        
        try:
            # Use existing payment_engine function
            result = create_order(phone, product_type)
            
            if result.get("success"):
                logger.info(f"✅ Payment order created: {result.get('order_id')}")
                
                # Track in analytics
                self._track_payment_initiated(phone, product_type, amount)
                
                return {
                    "success": True,
                    "order_id": result.get("order_id"),
                    "razorpay_order_id": result.get("razorpay_order_id"),
                    "payment_link": result.get("payment_link"),
                    "amount": amount,
                    "currency": "INR",
                    "product_type": product_type
                }
            else:
                logger.error(f"❌ Order creation failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        
        except Exception as e:
            logger.error(f"❌ Payment order creation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get order status
        
        Args:
            order_id: Order ID
        
        Returns:
            dict: Order status and details
        """
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM payment_orders
                WHERE order_id = ? OR razorpay_order_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (order_id, order_id))
            
            order = cursor.fetchone()
            conn.close()
            
            if order:
                return {
                    "success": True,
                    "order_id": order["order_id"],
                    "status": order["status"],
                    "product_type": order["product_type"],
                    "amount": order["amount"],
                    "created_at": order["created_at"],
                    "payment_id": order.get("payment_id")
                }
            else:
                return {
                    "success": False,
                    "error": "Order not found"
                }
        
        except Exception as e:
            logger.error(f"❌ Error fetching order status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_orders(self, phone: str, limit: int = 10) -> List[Dict]:
        """
        Get all orders for a user
        
        Args:
            phone: User phone number
            limit: Maximum orders to return
        
        Returns:
            list: User's orders
        """
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM payment_orders
                WHERE phone = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (phone, limit))
            
            orders = cursor.fetchall()
            conn.close()
            
            return [dict(order) for order in orders]
        
        except Exception as e:
            logger.error(f"❌ Error fetching user orders: {e}")
            return []
    
    def get_pending_orders(self, older_than_minutes: int = 60) -> List[Dict]:
        """
        Get pending/abandoned orders
        
        Args:
            older_than_minutes: Age threshold
        
        Returns:
            list: Pending orders
        """
        from backend.engines.db_engine import get_conn
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=older_than_minutes)
            
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM payment_orders
                WHERE status IN ('INITIATED', 'PENDING')
                AND created_at < ?
                ORDER BY created_at DESC
            """, (cutoff_time,))
            
            orders = cursor.fetchall()
            conn.close()
            
            return [dict(order) for order in orders]
        
        except Exception as e:
            logger.error(f"❌ Error fetching pending orders: {e}")
            return []
    
    def retry_payment(self, order_id: str) -> Dict:
        """
        Generate new payment link for failed order
        
        Args:
            order_id: Original order ID
        
        Returns:
            dict: New payment link
        """
        order = self.get_order_status(order_id)
        
        if not order.get("success"):
            return {"success": False, "error": "Order not found"}
        
        if order.get("status") == "SUCCESS":
            return {"success": False, "error": "Order already paid"}
        
        # Create new payment order with same details
        return self.create_payment_order(
            phone=order.get("phone"),
            product_type=order.get("product_type"),
            amount=order.get("amount")
        )
    
    def _track_payment_initiated(self, phone: str, product_type: str, amount: float):
        """Track payment initiation for analytics"""
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            # Create funnel_events table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS funnel_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    product_type TEXT,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert event
            cursor.execute("""
                INSERT INTO funnel_events (phone, event_type, product_type, amount)
                VALUES (?, ?, ?, ?)
            """, (phone, "PAYMENT_INITIATED", product_type, amount))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.debug(f"Failed to track payment initiation: {e}")


# Singleton
_payment_service = None

def get_payment_service() -> PaymentService:
    """Get payment service instance"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service