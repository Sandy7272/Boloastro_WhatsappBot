"""
OrderRepository
Data access layer for payment orders
Handles row-level locking for atomic updates
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from backend.models.order import Order
import logging

logger = logging.getLogger(__name__)


class OrderRepository:
    """
    Repository for order operations
    
    Provides atomic database operations with row-level locking
    to prevent race conditions during payment processing.
    """
    
    def __init__(self, session):
        """
        Initialize repository
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    @contextmanager
    def atomic_transaction(self):
        """
        Context manager for atomic transactions
        
        Usage:
            with order_repo.atomic_transaction():
                order = order_repo.get_with_lock(order_id)
                order.status = "SUCCESS"
                order_repo.save(order)
                # Commits automatically on success
                # Rolls back automatically on exception
        """
        try:
            yield
            self.session.commit()
            logger.debug("✅ Transaction committed")
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Transaction failed: {e}")
            raise
    
    def get_by_razorpay_order_id_with_lock(self, razorpay_order_id: str):
        """
        Get order with row-level lock (SELECT FOR UPDATE)
        
        This is CRITICAL for idempotency!
        Prevents concurrent updates to the same order.
        
        Args:
            razorpay_order_id: Razorpay order ID
        
        Returns:
            Order or None
        """
        order = self.session.query(Order).filter_by(
            razorpay_order_id=razorpay_order_id
        ).with_for_update().first()
        
        if order:
            logger.debug(f"🔒 Locked order: {razorpay_order_id}")
        
        return order
    
    def get_by_payment_id_with_lock(self, payment_id: str):
        """
        Get order by payment ID with row lock
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            Order or None
        """
        order = self.session.query(Order).filter_by(
            payment_id=payment_id
        ).with_for_update().first()
        
        if order:
            logger.debug(f"🔒 Locked order by payment_id: {payment_id}")
        
        return order
    
    def get_by_order_id(self, order_id: str):
        """
        Get order by internal order ID (without lock)
        
        Args:
            order_id: Internal order ID
        
        Returns:
            Order or None
        """
        return self.session.query(Order).filter_by(
            order_id=order_id
        ).first()
    
    def get_by_id(self, id: int):
        """
        Get order by primary key
        
        Args:
            id: Order primary key
        
        Returns:
            Order or None
        """
        return self.session.query(Order).filter_by(id=id).first()
    
    def save(self, order):
        """
        Save order to database
        
        Args:
            order: Order object
        
        Returns:
            Order: The saved order
        """
        self.session.add(order)
        self.session.flush()
        logger.debug(f"💾 Saved order: {order.order_id}")
        return order
    
    def get_orders_by_phone(self, phone: str, limit: int = 100):
        """
        Get all orders for a user
        
        Args:
            phone: User phone number
            limit: Maximum number of orders
        
        Returns:
            list: List of Order objects
        """
        return self.session.query(Order).filter_by(
            phone=phone
        ).order_by(
            Order.created_at.desc()
        ).limit(limit).all()
    
    def get_orders_by_status(self, status: str, limit: int = 100):
        """
        Get orders by status
        
        Args:
            status: Order status
            limit: Maximum number of orders
        
        Returns:
            list: List of Order objects
        """
        return self.session.query(Order).filter_by(
            status=status
        ).order_by(
            Order.created_at.desc()
        ).limit(limit).all()
    
    def get_pending_orders(self, older_than_minutes: int = 60):
        """
        Get pending orders older than specified time
        
        Useful for finding abandoned payments
        
        Args:
            older_than_minutes: Age threshold in minutes
        
        Returns:
            list: List of pending Order objects
        """
        cutoff_time = datetime.now() - timedelta(minutes=older_than_minutes)
        
        return self.session.query(Order).filter(
            Order.status.in_(['INITIATED', 'PENDING']),
            Order.created_at < cutoff_time
        ).all()
    
    def get_successful_orders_today(self):
        """
        Get all successful orders from today
        
        Returns:
            list: List of Order objects
        """
        from sqlalchemy import func, cast, Date
        
        today = datetime.now().date()
        
        return self.session.query(Order).filter(
            Order.status == 'SUCCESS',
            cast(Order.paid_at, Date) == today
        ).all()
    
    def count_orders_by_status(self, status: str) -> int:
        """
        Count orders by status
        
        Args:
            status: Order status
        
        Returns:
            int: Count of orders
        """
        return self.session.query(Order).filter_by(status=status).count()
    
    def get_order_stats(self) -> dict:
        """
        Get order statistics
        
        Returns:
            dict: Statistics including counts and revenue
        """
        from sqlalchemy import func
        
        stats = {}
        
        # Count by status
        status_counts = self.session.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        
        for status, count in status_counts:
            stats[f'{status.lower()}_count'] = count
        
        # Total revenue
        total_revenue = self.session.query(
            func.sum(Order.amount)
        ).filter(Order.status == 'SUCCESS').scalar()
        
        stats['total_revenue'] = float(total_revenue) if total_revenue else 0.0
        
        # Success rate
        total_orders = sum([count for _, count in status_counts])
        success_count = next(
            (count for status, count in status_counts if status == 'SUCCESS'),
            0
        )
        
        stats['success_rate'] = (
            (success_count / total_orders * 100) if total_orders > 0 else 0.0
        )
        
        return stats
    
    def update_order_status(
        self,
        order_id: str,
        status: str,
        payment_id: str = None,
        error_message: str = None
    ):
        """
        Update order status
        
        Args:
            order_id: Order ID
            status: New status
            payment_id: Optional payment ID
            error_message: Optional error message
        """
        order = self.get_by_order_id(order_id)
        
        if order:
            order.status = status
            order.updated_at = datetime.now()
            
            if payment_id:
                order.payment_id = payment_id
            
            if error_message:
                order.error_message = error_message
            
            if status == 'SUCCESS':
                order.paid_at = datetime.now()
            
            self.save(order)
            logger.info(f"📊 Order {order_id} status updated: {status}")
        else:
            logger.warning(f"⚠️ Order not found: {order_id}")