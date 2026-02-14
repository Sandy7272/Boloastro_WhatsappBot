"""
Entitlement Service
Manages user access to paid products (KUNDALI, QNA, MILAN)
Integrates with existing db_engine for backward compatibility
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EntitlementService:
    """
    Service for managing user entitlements (access to products)
    
    Integrates with existing db_engine functions while providing
    a clean service interface for new code.
    """
    
    def __init__(self, session=None):
        """
        Initialize entitlement service
        
        Args:
            session: SQLAlchemy session (optional)
        """
        self.session = session
    
    def grant(
        self, 
        user_id: str, 
        product_type: str, 
        order_id: str = None,
        metadata: dict = None
    ):
        """
        Grant access to a product
        
        Args:
            user_id: User identifier (phone number)
            product_type: Product type (KUNDALI, QNA, MILAN)
            order_id: Associated order ID
            metadata: Additional metadata (event_id, payment_id, etc.)
        """
        # Import here to avoid circular imports
        from backend.engines.db_engine import (
            mark_kundali_purchased,
            mark_milan_purchased,
            grant_qna_pack
        )
        
        # Ensure phone is in correct format
        phone = self._normalize_phone(user_id)
        
        logger.info(f"🎁 Granting {product_type} to {phone}")
        
        try:
            if product_type == "KUNDALI":
                mark_kundali_purchased(phone)
                logger.info(f"✅ KUNDALI access granted to {phone}")
            
            elif product_type == "MILAN":
                mark_milan_purchased(phone)
                logger.info(f"✅ MILAN access granted to {phone}")
            
            elif product_type == "QNA":
                # Grant 4 QnA credits (QnA pack)
                grant_qna_pack(phone, credits=4)
                logger.info(f"✅ QNA pack (4 credits) granted to {phone}")
            
            else:
                logger.warning(f"⚠️ Unknown product type: {product_type}")
                raise ValueError(f"Unknown product type: {product_type}")
            
            # Log the grant for analytics
            self._log_entitlement_grant(phone, product_type, order_id, metadata)
            
            return {
                "success": True,
                "user_id": phone,
                "product_type": product_type,
                "granted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to grant {product_type} to {phone}: {e}")
            raise
    
    def revoke(
        self,
        user_id: str,
        product_type: str,
        order_id: str = None,
        reason: str = None
    ):
        """
        Revoke access to a product (for refunds)
        
        Args:
            user_id: User identifier
            product_type: Product type
            order_id: Associated order ID
            reason: Reason for revocation (REFUND, DISPUTE, etc.)
        """
        phone = self._normalize_phone(user_id)
        
        logger.warning(f"⚠️ Revoking {product_type} from {phone} - Reason: {reason}")
        
        # TODO: Implement revocation logic
        # This requires updating db_engine to support revocation
        # For now, just log it
        
        self._log_entitlement_revoke(phone, product_type, order_id, reason)
        
        return {
            "success": True,
            "user_id": phone,
            "product_type": product_type,
            "revoked_at": datetime.now().isoformat(),
            "reason": reason
        }
    
    def check_access(self, user_id: str, product_type: str) -> bool:
        """
        Check if user has access to a product
        
        Args:
            user_id: User identifier
            product_type: Product type
        
        Returns:
            bool: True if user has access
        """
        from backend.engines.db_engine import (
            has_kundali_access,
            has_milan_access,
            get_qna_credits
        )
        
        phone = self._normalize_phone(user_id)
        
        if product_type == "KUNDALI":
            return has_kundali_access(phone)
        
        elif product_type == "MILAN":
            return has_milan_access(phone)
        
        elif product_type == "QNA":
            credits = get_qna_credits(phone)
            return credits > 0
        
        else:
            return False
    
    def get_user_entitlements(self, user_id: str) -> dict:
        """
        Get all entitlements for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            dict: User's entitlements
        """
        from backend.engines.db_engine import (
            has_kundali_access,
            has_milan_access,
            get_qna_credits
        )
        
        phone = self._normalize_phone(user_id)
        
        return {
            "user_id": phone,
            "kundali_access": has_kundali_access(phone),
            "milan_access": has_milan_access(phone),
            "qna_credits": get_qna_credits(phone)
        }
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to whatsapp:+91... format
        
        Args:
            phone: Phone number
        
        Returns:
            str: Normalized phone number
        """
        if phone.startswith("whatsapp:"):
            return phone
        
        if phone.startswith("+"):
            return f"whatsapp:{phone}"
        
        # Assume Indian number
        return f"whatsapp:+91{phone}"
    
    def _log_entitlement_grant(
        self,
        phone: str,
        product_type: str,
        order_id: str,
        metadata: dict
    ):
        """Log entitlement grant for analytics"""
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO entitlement_log (
                    phone, product_type, action, order_id, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                phone,
                product_type,
                "GRANT",
                order_id,
                str(metadata) if metadata else None
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            # Don't fail if logging fails
            logger.debug(f"Failed to log entitlement grant: {e}")
    
    def _log_entitlement_revoke(
        self,
        phone: str,
        product_type: str,
        order_id: str,
        reason: str
    ):
        """Log entitlement revocation for analytics"""
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO entitlement_log (
                    phone, product_type, action, order_id, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                phone,
                product_type,
                "REVOKE",
                order_id,
                reason
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.debug(f"Failed to log entitlement revoke: {e}")


# Singleton instance for easy import
_entitlement_service = EntitlementService()


def get_entitlement_service() -> EntitlementService:
    """Get entitlement service instance"""
    return _entitlement_service