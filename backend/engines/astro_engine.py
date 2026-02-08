import logging
import hashlib
import json

from backend.services.geocode import geocode_city
from backend.services.prokerala import get_prokerala_data
from backend.engines.db_engine import (
    get_kundali_cache,
    save_kundali_cache,
    log_api_usage,
    use_api_credit
)

logger = logging.getLogger(__name__)

# =========================
# COST CONFIG
# =========================

PROKERALA_COST_PER_CALL = 0.02


# =========================
# SIGN LORD MAP (VEDIC)
# =========================

SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}


# =========================
# VEDIC ASPECT RULES
# =========================

ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
    "Sun": [7],
    "Moon": [7],
    "Mercury": [7],
    "Venus": [7],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9]
}


# =========================
# CACHE KEY
# =========================

def _build_hash(place, dob, time_str):
    return hashlib.md5(f"{place}|{dob}|{time_str}".encode()).hexdigest()


# =========================
# NORMALIZE PLANETS
# =========================

def _normalize_planets(raw_chart):

    planets = []

    for p in raw_chart.get("planets", []):

        planets.append({
            "name": p.get("name"),
            "sign": p.get("sign"),
            "house": p.get("house"),
            "degree": round(p.get("degree", 0), 2),
            "nakshatra": (
                p.get("nakshatra", {}).get("name")
                if isinstance(p.get("nakshatra"), dict)
                else p.get("nakshatra")
            )
        })

    return planets


# =========================
# DASHA TIMELINE
# =========================

def _normalize_dasha(raw_chart):

    dasha = raw_chart.get("dasha", {})

    current = dasha.get("current", {})
    upcoming = dasha.get("next", [])

    return {
        "current": {
            "planet": current.get("planet"),
            "start": current.get("start"),
            "end": current.get("end")
        },
        "upcoming": [
            {
                "planet": d.get("planet"),
                "start": d.get("start"),
                "end": d.get("end")
            }
            for d in upcoming[:3]
        ]
    }


# =========================
# ADVANCED ASTRO DATA
# =========================

def _extract_advanced(raw):

    nak = raw.get("nakshatra_details", {})

    nakshatra = nak.get("nakshatra", {}).get("name")
    pada = nak.get("nakshatra", {}).get("pada")

    moon_rasi = nak.get("chandra_rasi", {}).get("name")
    sun_rasi = nak.get("soorya_rasi", {}).get("name")

    yogas = []
    for y in raw.get("yoga_details", []):
        yogas.append({
            "name": y.get("name"),
            "description": y.get("description")
        })

    manglik = raw.get("mangal_dosha", {}).get("has_dosha", False)

    return {
        "nakshatra": nakshatra,
        "pada": pada,
        "moon_rasi": moon_rasi,
        "sun_rasi": sun_rasi,
        "yogas": yogas,
        "manglik": manglik
    }


# =========================
# HOUSE LORDS
# =========================

def calculate_house_lords(planets):

    house_lords = {}

    for p in planets:
        sign = p["sign"]
        house = p["house"]

        lord = SIGN_LORDS.get(sign)

        if lord:
            house_lords[house] = lord

    return house_lords


# =========================
# PLANET ASPECTS (DRISHTI)
# =========================

def calculate_aspects(planets):

    aspects = []

    for p in planets:

        planet = p["name"]
        house = p["house"]

        aspect_offsets = ASPECTS.get(planet, [])

        for offset in aspect_offsets:

            target_house = ((house + offset - 1) % 12) + 1

            aspects.append({
                "planet": planet,
                "from_house": house,
                "to_house": target_house
            })

    return aspects


# =========================
# MAIN FUNCTION
# =========================

def get_kundali_cached(data):

    place = data.get("place")
    dob = data.get("dob")
    time_str = data.get("time")

    # ---------- CACHE ----------

    cache_key = _build_hash(place, dob, time_str)

    cached = get_kundali_cache(cache_key)

    if cached:
        logger.info("⚡ Kundali cache hit")
        return cached

    # ---------- GEOCODE ----------

    geo = geocode_city(place)

    if not geo:
        logger.warning(f"❌ Geocoding failed: {place}")
        return None

    lat = geo["lat"]
    lon = geo["lon"]

    logger.info(f"📍 {place} -> {lat},{lon}")

    # ---------- PROKERALA ----------

    try:
        astro = get_prokerala_data(
            dob=dob,
            time_str=time_str,
            latitude=lat,
            longitude=lon
        )
    except Exception:
        logger.exception("❌ Prokerala failed")
        return None

    if not astro:
        return None

    raw_chart = astro.get("raw", astro)

    # 👀 Debug (remove in production)
    print("\n========== RAW PROKERALA JSON ==========\n")
    print(json.dumps(raw_chart, indent=2))
    print("\n=======================================\n")

    # ---------- NORMALIZATION ----------

    planets = _normalize_planets(raw_chart)
    dasha_timeline = _normalize_dasha(raw_chart)
    advanced = _extract_advanced(raw_chart)

    house_lords = calculate_house_lords(planets)
    aspects = calculate_aspects(planets)

    # ---------- FINAL DATA ----------

    kundali_data = {

        # CORE
        "lagna": astro.get("lagna"),
        "moon_sign": astro.get("moon_sign"),
        "sun_sign": astro.get("sun_sign"),
        "current_dasha": astro.get("current_dasha"),

        # PROFESSIONAL
        "planets": planets,
        "dasha_timeline": dasha_timeline,

        # ADVANCED VEDIC
        "nakshatra": advanced["nakshatra"],
        "pada": advanced["pada"],
        "moon_rasi": advanced["moon_rasi"],
        "sun_rasi": advanced["sun_rasi"],
        "yogas": advanced["yogas"],
        "manglik": advanced["manglik"],

        # 🔥 REAL ASTRO INTELLIGENCE
        "house_lords": house_lords,
        "aspects": aspects,

        "coordinates": {
            "lat": lat,
            "lon": lon,
            "place": place
        }
    }

    # ---------- CACHE ----------

    save_kundali_cache(cache_key, kundali_data)

    logger.info("💾 Kundali cached (full professional logic)")

    # ---------- COST ----------

    log_api_usage("PROKERALA", PROKERALA_COST_PER_CALL)
    use_api_credit("PROKERALA", 1)

    return kundali_data
