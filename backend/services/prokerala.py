import requests
import logging
import time
from datetime import datetime
import pytz

from backend.config import Config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.prokerala.com/v2/astrology/kundli"
TOKEN_URL = "https://api.prokerala.com/token"

# =========================
# TOKEN CACHE (IN MEMORY)
# =========================

_CACHED_TOKEN = None
_TOKEN_EXPIRY = 0


# =========================
# ACCESS TOKEN
# =========================

def get_access_token():
    """
    Automatically generates or reuses Prokerala Access Token
    """

    global _CACHED_TOKEN, _TOKEN_EXPIRY

    # 1️⃣ In-memory token cache
    if _CACHED_TOKEN and time.time() < _TOKEN_EXPIRY:
        return _CACHED_TOKEN

    # 2️⃣ Token from .env (if manually set)
    env_token = Config.PROKERALA_ACCESS_TOKEN

    if env_token and isinstance(env_token, str) and env_token.strip():
        if env_token.count(".") == 2:   # JWT format check
            return env_token.strip()

    # 3️⃣ Generate new token from API
    logger.info("🔄 Generating new Prokerala access token...")

    payload = {
        "grant_type": "client_credentials",
        "client_id": Config.PROKERALA_CLIENT_ID,
        "client_secret": Config.PROKERALA_CLIENT_SECRET
    }

    try:
        response = requests.post(TOKEN_URL, data=payload, timeout=10)

        if response.status_code != 200:
            logger.error(f"❌ Token generation failed: {response.text}")
            return None

        data = response.json()

        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        _CACHED_TOKEN = new_token
        _TOKEN_EXPIRY = time.time() + expires_in - 60

        logger.info("✅ Prokerala token generated")

        return new_token

    except Exception as e:
        logger.error(f"❌ Token request error: {e}")
        return None


# =========================
# MAIN PROKERALA API CALL
# =========================

def get_prokerala_data(dob, time_str, latitude, longitude, ayanamsa=1):
    """
    Fetch kundali data from Prokerala Astrology API
    Includes sandbox fallback handling
    """

    # -------------------------
    # GET TOKEN
    # -------------------------

    token = get_access_token()

    if not token:
        return None

    # -------------------------
    # PREPARE DATETIME
    # -------------------------

    try:
        local_tz = pytz.timezone("Asia/Kolkata")

        dt = datetime.strptime(
            f"{dob} {time_str}",
            "%d-%m-%Y %I:%M %p"
        )

        dt = local_tz.localize(dt)
        iso_datetime = dt.isoformat()

    except Exception as e:
        logger.error(f"❌ Date parsing error: {e}")
        return None

    # -------------------------
    # PREPARE REQUEST
    # -------------------------

    params = {
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": iso_datetime,
        "chart_type": "rasi"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    logger.info(f"🌌 Prokerala request -> {iso_datetime}")

    try:
        # -------------------------
        # FIRST ATTEMPT
        # -------------------------
        response = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        # -------------------------
        # SANDBOX FIX
        # -------------------------
        if response.status_code == 400 and "sandbox" in response.text.lower():
            logger.warning("⚠️ Sandbox limit detected — retrying with Jan 1st")

            dt_sandbox = dt.replace(month=1, day=1)
            params["datetime"] = dt_sandbox.isoformat()

            response = requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                timeout=15
            )

        # -------------------------
        # AUTH ERROR
        # -------------------------
        if response.status_code == 401:
            logger.error("❌ Prokerala token expired — clearing cache")

            global _CACHED_TOKEN
            _CACHED_TOKEN = None

            return None

        # -------------------------
        # OTHER ERRORS
        # -------------------------
        if response.status_code != 200:
            logger.error(
                f"❌ Prokerala API error {response.status_code}: {response.text}"
            )
            return None

        # -------------------------
        # SUCCESS
        # -------------------------
        data = response.json()
        chart = data.get("data", {})

        return {
            "lagna": chart.get("ascendant", {}).get("sign"),
            "moon_sign": chart.get("moon", {}).get("sign"),
            "sun_sign": chart.get("sun", {}).get("sign"),
            "current_dasha": chart.get("dasha", {}).get("current", {}).get("planet"),
            "planets": [p.get("name") for p in chart.get("planets", [])],
            "raw": chart
        }

    except Exception:
        logger.exception("❌ Prokerala request failed")
        return None
