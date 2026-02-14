"""
Order Model
Represents payment orders in the system
Maps to the existing 'payment_orders' table
"""

from sqlalchemy import Column, String, Numeric, DateTime, Integer, Text
from sqlalchemy.sql import func
from backend.utils.database import Base


class Order(Base):
    """
    Payment Order Model
    
    Represents a payment order created via Razorpay.
    Includes all necessary fields for tracking payment status,
    handling refunds, and debugging issues.
    """
    
    __tablename__ = 'payment_orders'  # Use your existing table name
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Order ID (internal unique identifier)
    order_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # User phone number
    phone = Column(String(50), nullable=False, index=True)
    
    # Product type (KUNDALI, QNA, MILAN)
    product_type = Column(String(50), nullable=False)
    
    # Payment amount in INR
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Currency (default: INR)
    currency = Column(String(3), default='INR')
    
    # Payment status (INITIATED, PENDING, PROCESSING, SUCCESS, FAILED, REFUNDED)
    status = Column(String(50), default='INITIATED', index=True)
    
    # Razorpay order ID (from Razorpay API)
    razorpay_order_id = Column(String(255), index=True)
    
    # Razorpay payment ID (after payment completion)
    payment_id = Column(String(255), index=True)
    
    # Payment method used (card, upi, netbanking, etc.)
    payment_method = Column(String(50))
    
    # Error code (if payment failed)
    error_code = Column(String(50))
    
    # Error description (human-readable error message)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, onupdate=func.now())
    paid_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Order {self.order_id} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'phone': self.phone,
            'product_type': self.product_type,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'razorpay_order_id': self.razorpay_order_id,
            'payment_id': self.payment_id,
            'payment_method': self.payment_method,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.status == 'SUCCESS'
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status in ['INITIATED', 'PENDING']
    
    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.status == 'FAILED'