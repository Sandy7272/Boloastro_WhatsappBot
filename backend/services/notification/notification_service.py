"""
Notification Service
Sends WhatsApp notifications to users
"""

import logging
from typing import Optional
from twilio.rest import Client

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification Service - Sends WhatsApp messages
    
    Handles:
    - Payment confirmations
    - Payment reminders
    - Product delivery notifications
    - Promotional messages
    """
    
    def __init__(self):
        """Initialize Twilio client"""
        from backend.config import Config
        
        self.client = Client(
            Config.TWILIO_ACCOUNT_SID,
            Config.TWILIO_AUTH_TOKEN
        )
        self.from_number = Config.TWILIO_WHATSAPP_NUMBER
    
    def send_payment_success(
        self,
        phone: str,
        product_type: str,
        order_id: str
    ) -> bool:
        """
        Send payment success notification
        
        Args:
            phone: User phone number
            product_type: Product purchased
            order_id: Order ID
        
        Returns:
            bool: Success status
        """
        messages = {
            "KUNDALI": "✅ *Payment Successful!*\n\nYour Kundali report is being generated. You'll receive it within 5 minutes.",
            "QNA": "✅ *Payment Successful!*\n\n4 Q&A credits have been added to your account. Ask away!",
            "MILAN": "✅ *Payment Successful!*\n\nYour Milan (compatibility) report is being generated. You'll receive it shortly."
        }
        
        message = messages.get(product_type, "✅ Payment successful! Thank you for your purchase.")
        
        return self._send_message(phone, message)
    
    def send_payment_reminder(
        self,
        phone: str,
        product_type: str,
        payment_link: str,
        hours_since: int = 1
    ) -> bool:
        """
        Send abandoned payment reminder
        
        Args:
            phone: User phone number
            product_type: Product
            payment_link: Payment link
            hours_since: Hours since initiation
        
        Returns:
            bool: Success status
        """
        message = f"""
⏰ *Payment Reminder*

Your {product_type} payment is still pending.

Complete your payment here:
{payment_link}

Need help? Reply 'HELP'
"""
        
        return self._send_message(phone, message.strip())
    
    def send_payment_failed(
        self,
        phone: str,
        product_type: str,
        reason: str = None
    ) -> bool:
        """
        Send payment failed notification
        
        Args:
            phone: User phone number
            product_type: Product
            reason: Failure reason
        
        Returns:
            bool: Success status
        """
        message = f"""
❌ *Payment Failed*

Your {product_type} payment could not be completed.

{f'Reason: {reason}' if reason else ''}

Reply 'RETRY' to try again or 'HELP' for support.
"""
        
        return self._send_message(phone, message.strip())
    
    def send_kundali_ready(self, phone: str, pdf_url: str) -> bool:
        """
        Send Kundali ready notification
        
        Args:
            phone: User phone number
            pdf_url: PDF download link
        
        Returns:
            bool: Success status
        """
        message = f"""
🎉 *Your Kundali is Ready!*

Download your personalized Kundali report:
{pdf_url}

This link is valid for 7 days.
"""
        
        return self._send_message(phone, message.strip())
    
    def send_special_offer(
        self,
        phone: str,
        offer_text: str
    ) -> bool:
        """
        Send promotional offer
        
        Args:
            phone: User phone number
            offer_text: Offer message
        
        Returns:
            bool: Success status
        """
        message = f"""
🎁 *Special Offer for You!*

{offer_text}

Reply 'YES' to avail this offer.
"""
        
        return self._send_message(phone, message.strip())
    
    def _send_message(self, phone: str, message: str) -> bool:
        """
        Internal method to send WhatsApp message
        
        Args:
            phone: Phone number
            message: Message text
        
        Returns:
            bool: Success status
        """
        try:
            # Normalize phone format
            if not phone.startswith("whatsapp:"):
                if phone.startswith("+"):
                    phone = f"whatsapp:{phone}"
                else:
                    phone = f"whatsapp:+91{phone}"
            
            # Send message
            self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=phone
            )
            
            logger.info(f"📤 Notification sent to {phone}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send notification to {phone}: {e}")
            return False
    
    def send_bulk_notification(
        self,
        phone_numbers: list,
        message: str
    ) -> dict:
        """
        Send bulk notifications
        
        Args:
            phone_numbers: List of phone numbers
            message: Message to send
        
        Returns:
            dict: Results (sent, failed)
        """
        sent = 0
        failed = 0
        
        for phone in phone_numbers:
            if self._send_message(phone, message):
                sent += 1
            else:
                failed += 1
        
        logger.info(f"📊 Bulk notification: {sent} sent, {failed} failed")
        
        return {
            "total": len(phone_numbers),
            "sent": sent,
            "failed": failed
        }


# Singleton
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service