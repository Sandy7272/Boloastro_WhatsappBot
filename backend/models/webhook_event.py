"""
WebhookEvent Model
Stores all Razorpay webhook events for idempotency checking
Prevents duplicate webhook processing and race conditions
"""

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from backend.utils.database import Base


class WebhookEvent(Base):
    """
    Webhook Event Model - Ensures idempotent webhook processing
    
    Each Razorpay event has a unique event_id. By storing this,
    we can detect and reject duplicate webhook deliveries.
    """
    
    __tablename__ = 'webhook_events'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Razorpay event ID (unique identifier from Razorpay)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Event type (e.g., 'payment.captured', 'payment.failed', 'refund.created')
    event_type = Column(String(100), nullable=False)
    
    # Associated order ID (from the payment)
    order_id = Column(String(255), index=True)
    
    # Full webhook payload as JSON string
    payload = Column(Text, nullable=False)
    
    # Processing status (PENDING, PROCESSING, COMPLETED, FAILED, DUPLICATE)
    status = Column(String(50), default='PENDING', index=True)
    
    # Error message if processing failed
    error_message = Column(Text)
    
    # When processing completed
    processed_at = Column(DateTime)
    
    # When webhook was received
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<WebhookEvent {self.event_id} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'order_id': self.order_id,
            'status': self.status,
            'error_message': self.error_message,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }