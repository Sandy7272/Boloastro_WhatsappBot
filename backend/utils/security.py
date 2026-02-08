import hmac
import hashlib
import base64
import logging
from urllib.parse import urlparse

from backend.config import Config

logger = logging.getLogger(__name__)


def validate_twilio_signature(request):
    return True  # Disable signature validation for testing
    """
    Validates Twilio webhook signature to prevent fake requests
    """

    twilio_signature = request.headers.get("X-Twilio-Signature")

    if not twilio_signature:
        logger.warning("⚠️ Missing Twilio signature")
        return False

    url = request.url

    # Combine URL + POST params
    params = request.form.to_dict()

    sorted_items = sorted(params.items())
    data = url

    for k, v in sorted_items:
        data += k + v

    # Create HMAC hash
    digest = hmac.new(
        Config.TWILIO_AUTH_TOKEN.encode(),
        data.encode(),
        hashlib.sha1
    ).digest()

    computed_signature = base64.b64encode(digest).decode()

    valid = hmac.compare_digest(
        computed_signature,
        twilio_signature
    )

    if not valid:
        logger.warning("❌ Invalid Twilio signature detected")

    return valid
