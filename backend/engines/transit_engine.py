import logging
import datetime
from backend.services.prokerala import get_prokerala_data
from backend.engines.db_engine import get_kundali_cache, save_kundali_cache

logger = logging.getLogger(__name__)

TRANSIT_KEY = "DAILY_TRANSIT"


def get_daily_transits():

    today = datetime.date.today().isoformat()

    cache_key = f"{TRANSIT_KEY}_{today}"

    cached = get_kundali_cache(cache_key)

    if cached:
        logger.info("⚡ Transit cache hit")
        return cached

    # Use noon time (safe for transits)
    time_str = "12:00 PM"

    try:
        transit_data = get_prokerala_data(
            dob=today,
            time_str=time_str,
            latitude=0,
            longitude=0
        )
    except Exception:
        logger.exception("❌ Transit fetch failed")
        return None

    if not transit_data:
        return None

    raw = transit_data.get("raw", transit_data)

    transits = []

    for p in raw.get("planets", []):
        transits.append({
            "name": p.get("name"),
            "sign": p.get("sign"),
            "degree": p.get("degree")
        })

    save_kundali_cache(cache_key, transits)

    logger.info("🌍 Daily transit cached")

    return transits
