"""
Enterprise Security Utilities
- Webhook signature validation
- Rate limiting
- Input validation
- Secret management
"""

import hmac
import hashlib
import time
from functools import wraps
from typing import Optional, Callable
import logging
import re

logger = logging.getLogger(__name__)


# ============================
# WEBHOOK SIGNATURE VALIDATION
# ============================

def verify_razorpay_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify Razorpay webhook signature
    
    Args:
        payload: Raw request body as string
        signature: X-Razorpay-Signature header
        secret: Razorpay webhook secret
    
    Returns:
        bool: True if signature is valid
    
    Example:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Razorpay-Signature')
        if not verify_razorpay_signature(payload, signature, WEBHOOK_SECRET):
            abort(401)
    """
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def verify_twilio_signature(
    url: str,
    params: dict,
    signature: str,
    auth_token: str
) -> bool:
    """
    Verify Twilio webhook signature
    
    Args:
        url: Full URL of the webhook
        params: POST parameters
        signature: X-Twilio-Signature header
        auth_token: Twilio auth token
    
    Returns:
        bool: True if signature is valid
    """
    try:
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Build data string
        data = url + ''.join(f'{k}{v}' for k, v in sorted_params)
        
        # Compute signature
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64 encode
        import base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode()
        
        return hmac.compare_digest(expected_signature_b64, signature)
    
    except Exception as e:
        logger.error(f"Twilio signature verification error: {e}")
        return False


# ============================
# RATE LIMITING
# ============================

class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis-based rate limiting
    """
    
    def __init__(self):
        self.requests = {}  # {key: [(timestamp, count), ...]}
        self.cleanup_interval = 60  # Cleanup old entries every minute
        self.last_cleanup = time.time()
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)
        
        # Get request history for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if now - ts < window_seconds
        ]
        
        # Count requests in window
        total_requests = sum(count for _, count in self.requests[key])
        
        if total_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for key: {key}")
            return False
        
        # Add this request
        self.requests[key].append((now, 1))
        return True
    
    def _cleanup(self, now: float):
        """Remove old entries"""
        self.requests = {
            k: v for k, v in self.requests.items()
            if any(now - ts < 3600 for ts, _ in v)  # Keep last hour
        }
        self.last_cleanup = now


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator for rate limiting
    
    Usage:
        @app.route("/webhook")
        @rate_limit(max_requests=30, window_seconds=60)
        def webhook():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # Get client identifier
            key = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if not _rate_limiter.is_allowed(key, max_requests, window_seconds):
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {max_requests} requests per {window_seconds} seconds"
                }), 429
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================
# INPUT VALIDATION
# ============================

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number (should include country code)
    
    Returns:
        bool: True if valid
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Should be 10-15 digits
    if not (10 <= len(digits) <= 15):
        return False
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address
    
    Args:
        email: Email address
    
    Returns:
        bool: True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove any SQL injection patterns (basic)
    sql_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', '--', ';']
    for keyword in sql_keywords:
        text = text.replace(keyword, '')
    
    # Strip whitespace
    text = text.strip()
    
    return text


def validate_amount(amount: float, min_amount: float = 1.0, max_amount: float = 100000.0) -> bool:
    """
    Validate payment amount
    
    Args:
        amount: Amount in INR
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
    
    Returns:
        bool: True if valid
    """
    try:
        amount = float(amount)
        return min_amount <= amount <= max_amount
    except (ValueError, TypeError):
        return False


# ============================
# SECRET MANAGEMENT
# ============================

class SecretManager:
    """
    Secure secret management
    """
    
    def __init__(self):
        self._secrets = {}
    
    def set_secret(self, key: str, value: str):
        """Store a secret"""
        self._secrets[key] = value
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret"""
        return self._secrets.get(key, default)
    
    def has_secret(self, key: str) -> bool:
        """Check if secret exists"""
        return key in self._secrets
    
    def load_from_env(self, keys: list):
        """Load secrets from environment variables"""
        import os
        for key in keys:
            value = os.getenv(key)
            if value:
                self._secrets[key] = value
                logger.info(f"Loaded secret: {key}")
            else:
                logger.warning(f"Secret not found in environment: {key}")


# Global secret manager
_secret_manager = SecretManager()


def get_secret_manager() -> SecretManager:
    """Get global secret manager"""
    return _secret_manager


# ============================
# SESSION SECURITY
# ============================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    
    Args:
        length: Token length
    
    Returns:
        str: Secure random token (hex)
    """
    import secrets
    return secrets.token_hex(length)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password
    """
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        hashed: Hashed password
    
    Returns:
        bool: True if password matches
    """
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ============================
# IP WHITELIST
# ============================

class IPWhitelist:
    """
    IP whitelist for webhook endpoints
    """
    
    def __init__(self, allowed_ips: list = None, allowed_ranges: list = None):
        """
        Initialize IP whitelist
        
        Args:
            allowed_ips: List of allowed IP addresses
            allowed_ranges: List of allowed IP ranges (CIDR notation)
        """
        self.allowed_ips = set(allowed_ips or [])
        self.allowed_ranges = allowed_ranges or []
    
    def is_allowed(self, ip: str) -> bool:
        """
        Check if IP is whitelisted
        
        Args:
            ip: IP address to check
        
        Returns:
            bool: True if IP is allowed
        """
        # Check direct IP match
        if ip in self.allowed_ips:
            return True
        
        # Check IP ranges
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            for range_str in self.allowed_ranges:
                network = ipaddress.ip_network(range_str)
                if ip_obj in network:
                    return True
        except Exception as e:
            logger.error(f"IP validation error: {e}")
        
        return False


# Razorpay webhook IPs (example - update with actual IPs)
RAZORPAY_WEBHOOK_IPS = IPWhitelist(
    allowed_ranges=[
        "3.7.70.0/24",
        "3.6.119.0/24"
    ]
)


# ============================
# SECURITY HEADERS
# ============================

def add_security_headers(response):
    """
    Add security headers to Flask response
    
    Usage:
        @app.after_request
        def after_request(response):
            return add_security_headers(response)
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response


if __name__ == "__main__":
    # Test webhook signature validation
    payload = '{"event":"payment.captured","payload":{}}'
    secret = "test_secret"
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Signature valid: {verify_razorpay_signature(payload, signature, secret)}")
    
    # Test rate limiter
    limiter = RateLimiter()
    for i in range(100):
        allowed = limiter.is_allowed("test_key", max_requests=10, window_seconds=60)
        if not allowed:
            print(f"Rate limit hit at request {i+1}")
            break
    
    # Test input validation
    print(f"Phone valid: {validate_phone_number('+919876543210')}")
    print(f"Email valid: {validate_email('user@example.com')}")
    print(f"Amount valid: {validate_amount(200)}")

    # =========================
# BACKWARD COMPATIBILITY ALIASES
# =========================

# Old code uses these names, new code uses verify_*
validate_twilio_signature = verify_twilio_signature
validate_razorpay_signature = verify_razorpay_signature

# Export all for compatibility
__all__ = [
    'verify_razorpay_signature',
    'verify_twilio_signature',
    'validate_twilio_signature',  # Alias
    'validate_razorpay_signature',  # Alias
    'rate_limit',
    'RateLimiter',
    'validate_phone_number',
    'validate_email',
    'sanitize_input',
    'validate_amount',
    'SecretManager',
    'get_secret_manager',
    'generate_secure_token',
    'hash_password',
    'verify_password',
    'IPWhitelist',
    'RAZORPAY_WEBHOOK_IPS',
    'add_security_headers'
]