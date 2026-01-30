import logging
from services.geocode import geocode_city
from services.prokerala import get_prokerala_data

logger = logging.getLogger(__name__)


def get_kundali_cached(data):
    """
    Resolve place → coordinates → Prokerala kundali
    This function is called ONCE per user
    """

    place = data.get("place")
    dob = data.get("dob")
    time = data.get("time")

    # 1️⃣ Geocode place
    geo = geocode_city(place)
    if not geo:
        logger.warning(f"Geocoding failed for place: {place}")
        return None

    lat = geo["lat"]
    lon = geo["lon"]

    logger.info(f"Geocoded {place} → {lat},{lon}")

    # 2️⃣ Call Prokerala
    try:
        astro = get_prokerala_data(
            dob=dob,
            time=time,
            latitude=lat,
            longitude=lon
        )
    except Exception:
        logger.exception("Prokerala API failed")
        return None

    # 3️⃣ Normalize for FSM + AI
    return {
        "lagna": astro.get("lagna"),
        "moon_sign": astro.get("moon_sign"),
        "sun_sign": astro.get("sun_sign"),
        "current_dasha": astro.get("current_dasha"),
        "planets": astro.get("planets", []),
        "coordinates": {
            "lat": lat,
            "lon": lon,
            "place": place
        },
        "raw": astro.get("raw", astro)
    }
