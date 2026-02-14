"""
WebhookRepository
Data access layer for webhook events
Handles idempotency checking and event storage
"""

from datetime import datetime
from sqlalchemy.exc import IntegrityError
from backend.models.webhook_event import WebhookEvent
import json
import logging

logger = logging.getLogger(__name__)


class WebhookRepository:
    """
    Repository for webhook event operations
    
    Provides idempotency checking and event storage/retrieval.
    All database operations for webhook events go through this class.
    """
    
    def __init__(self, session):
        """
        Initialize repository
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def event_exists(self, event_id: str) -> bool:
        """
        Check if event already exists (idempotency check)
        
        Args:
            event_id: Razorpay event ID
        
        Returns:
            bool: True if event exists, False otherwise
        """
        exists = self.session.query(WebhookEvent).filter_by(
            event_id=event_id
        ).first() is not None
        
        if exists:
            logger.info(f"🔄 Event already exists: {event_id}")
        
        return exists
    
    def store_event(
        self, 
        event_id: str, 
        event_type: str, 
        payload: dict, 
        status: str = 'PENDING'
    ):
        """
        Store webhook event in database
        
        Args:
            event_id: Unique event ID from Razorpay
            event_type: Type of event (e.g., 'payment.captured')
            payload: Full event payload
            status: Initial status (default: PENDING)
        
        Returns:
            WebhookEvent: The created event
        
        Raises:
            ValueError: If event already exists (duplicate)
        """
        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            order_id=self._extract_order_id(payload),
            payload=json.dumps(payload),
            status=status
        )
        
        try:
            self.session.add(event)
            self.session.flush()  # Immediate unique constraint check
            logger.info(f"✅ Stored webhook event: {event_id} - {event_type}")
            return event
        
        except IntegrityError as e:
            self.session.rollback()
            logger.warning(f"⚠️ Duplicate event detected: {event_id}")
            raise ValueError(f"Event {event_id} already exists")
    
    def update_status(
        self, 
        event_id: str, 
        status: str, 
        error_message: str = None
    ):
        """
        Update event processing status
        
        Args:
            event_id: Event ID to update
            status: New status (COMPLETED, FAILED, etc.)
            error_message: Optional error message
        """
        event = self.session.query(WebhookEvent).filter_by(
            event_id=event_id
        ).first()
        
        if event:
            event.status = status
            
            if error_message:
                event.error_message = error_message
            
            if status == 'COMPLETED':
                event.processed_at = datetime.now()
            
            self.session.commit()
            logger.info(f"📊 Updated event {event_id} status: {status}")
        else:
            logger.warning(f"⚠️ Event not found for update: {event_id}")
    
    def get_event(self, event_id: str):
        """
        Get event by ID
        
        Args:
            event_id: Event ID
        
        Returns:
            WebhookEvent or None
        """
        return self.session.query(WebhookEvent).filter_by(
            event_id=event_id
        ).first()
    
    def get_event_status(self, event_id: str) -> str:
        """
        Get status of an event
        
        Args:
            event_id: Event ID
        
        Returns:
            str: Status or None if not found
        """
        event = self.get_event(event_id)
        return event.status if event else None
    
    def get_failed_events(self, limit: int = 100):
        """
        Get failed events for retry
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            list: List of failed WebhookEvent objects
        """
        return self.session.query(WebhookEvent).filter_by(
            status='FAILED'
        ).order_by(
            WebhookEvent.created_at.desc()
        ).limit(limit).all()
    
    def get_pending_events(self, limit: int = 100):
        """
        Get pending events (stuck in processing)
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            list: List of pending WebhookEvent objects
        """
        return self.session.query(WebhookEvent).filter_by(
            status='PENDING'
        ).order_by(
            WebhookEvent.created_at.desc()
        ).limit(limit).all()
    
    def get_events_by_order(self, order_id: str):
        """
        Get all events for a specific order
        
        Args:
            order_id: Order ID
        
        Returns:
            list: List of WebhookEvent objects
        """
        return self.session.query(WebhookEvent).filter_by(
            order_id=order_id
        ).order_by(
            WebhookEvent.created_at.desc()
        ).all()
    
    def _extract_order_id(self, payload: dict) -> str:
        """
        Extract order_id from webhook payload
        
        Args:
            payload: Webhook payload
        
        Returns:
            str: Order ID or None
        """
        try:
            # Try payment object first
            order_id = payload.get("payload", {}).get("payment", {}).get("order_id")
            
            if not order_id:
                # Try order object
                order_id = payload.get("payload", {}).get("order", {}).get("id")
            
            return order_id
        
        except Exception as e:
            logger.warning(f"⚠️ Could not extract order_id: {e}")
            return None
    
    def count_events_by_status(self, status: str) -> int:
        """
        Count events by status
        
        Args:
            status: Event status
        
        Returns:
            int: Count of events
        """
        return self.session.query(WebhookEvent).filter_by(
            status=status
        ).count()
    
    def get_event_stats(self) -> dict:
        """
        Get webhook event statistics
        
        Returns:
            dict: Statistics
        """
        from sqlalchemy import func
        
        stats = {}
        
        # Count by status
        status_counts = self.session.query(
            WebhookEvent.status,
            func.count(WebhookEvent.id)
        ).group_by(WebhookEvent.status).all()
        
        for status, count in status_counts:
            stats[status] = count
        
        # Total events
        stats['total'] = sum(stats.values())
        
        return stats