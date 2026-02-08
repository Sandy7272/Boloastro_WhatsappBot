import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# =========================
# RATE LIMIT CONFIG
# =========================

MAX_REQUESTS = 10        # messages
TIME_WINDOW = 60        # seconds


# =========================
# STORAGE (IN MEMORY)
# =========================

_user_requests = defaultdict(deque)


# =========================
# MAIN CHECK FUNCTION
# =========================

def is_rate_limited(user_id):
    """
    Returns True if user exceeded limit
    """

    now = time.time()
    requests = _user_requests[user_id]

    # Remove old timestamps
    while requests and now - requests[0] > TIME_WINDOW:
        requests.popleft()

    # Check limit
    if len(requests) >= MAX_REQUESTS:
        logger.warning(f"⏱ Rate limit hit for {user_id}")
        return True

    # Record current request
    requests.append(now)

    return False
