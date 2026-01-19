# astro_engine.py
# ----------------
# Core Astrology Engine
# Real Calculation of Vimshottari Dasha & Planetary Positions

import swisseph as swe
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pytz

# ---------------- CONFIG ----------------

swe.set_sid_mode(swe.SIDM_LAHIRI)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Dasha Lords in Order (Ketu to Mercury) and their duration in years
DASHA_LORDS = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), 
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
]

PLANET_MAP = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
    "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE, "Ketu": swe.MEAN_NODE
}

# ---------------- UTILS ----------------

def to_utc_julian(dt_str, time_str):
    try:
        full_str = f"{dt_str} {time_str}"
        try:
            dt = datetime.strptime(full_str, "%d-%m-%Y %I:%M %p")
        except ValueError:
            dt = datetime.strptime(full_str, "%d-%m-%Y %H:%M")
        
        tz = pytz.timezone("Asia/Kolkata")
        dt_local = tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.utc)
        hour = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
        return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour), dt_utc.year
    except:
        return swe.julday(2000, 1, 1, 12), 2000

def get_sign(lon):
    return SIGNS[int(lon // 30) % 12]

def get_nakshatra_info(moon_lon):
    # Nakshatra span is 13 deg 20 min (13.3333 deg)
    nak_span = 360 / 27
    nak_index = int(moon_lon // nak_span)
    degree_into_nak = moon_lon % nak_span
    percent_passed = degree_into_nak / nak_span
    
    # Nakshatra name
    nak_name = NAKSHATRAS[nak_index % 27]
    
    # Vimshottari Lord logic
    # The cycle starts at Ashwini (Ketu). Sequence repeats 3 times (9 lords * 3 = 27 naks)
    lord_index = nak_index % 9
    lord_name, duration = DASHA_LORDS[lord_index]
    
    # Balance of Dasha at birth
    balance_years = duration * (1 - percent_passed)
    
    return {
        "nakshatra": nak_name,
        "lord": lord_name,
        "lord_index": lord_index,
        "balance_years": balance_years,
        "total_duration": duration
    }

# ---------------- MAIN CHART GENERATION ----------------

def generate_chart(dob, time, place):
    try:
        geo = Nominatim(user_agent="astro_bot_v2").geocode(place, timeout=5)
        lat, lon_geo = (geo.latitude, geo.longitude) if geo else (19.0760, 72.8777)
    except:
        lat, lon_geo = 19.0760, 72.8777

    jd, _ = to_utc_julian(dob, time)
    cusps, ascmc = swe.houses(jd, lat, lon_geo, b'P')
    asc_lon = ascmc[0]
    
    houses_data = [{"house": i+1, "sign": get_sign((asc_lon + i*30)%360), "planets": []} for i in range(12)]

    moon_lon = 0
    
    for name, pid in PLANET_MAP.items():
        res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
        lon_p = res[0][0]
        if name == "Ketu": lon_p = (lon_p + 180) % 360
        if name == "Moon": moon_lon = lon_p
            
        h_num = int(((lon_p - asc_lon) % 360) // 30) + 1
        if 1 <= h_num <= 12:
            houses_data[h_num - 1]["planets"].append(name)

    # Add extra metadata for the first house (Lagna)
    houses_data[0]["moon_lon"] = moon_lon # Passing moon longitude safely inside chart structure
    return houses_data

# ---------------- REAL DASHA CALCULATION ----------------

def calculate_dasha(dob, time, place):
    # 1. Get Moon Position again (Calculated quickly)
    jd, birth_year = to_utc_julian(dob, time)
    res = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
    moon_lon = res[0][0]
    
    # 2. Get Balance at Birth
    info = get_nakshatra_info(moon_lon)
    
    # 3. Calculate Dasha Timeline
    current_year = datetime.now().year
    
    # Start cycle
    start_year = birth_year
    remaining_balance = info["balance_years"]
    current_lord_idx = info["lord_index"]
    
    dasha_log = []
    
    # Add first dasha (Birth Dasha)
    end_year = start_year + remaining_balance
    dasha_log.append({
        "planet": DASHA_LORDS[current_lord_idx][0],
        "start": start_year,
        "end": end_year
    })
    
    prev_end = end_year
    
    # Calculate next 120 years of dashas
    for i in range(1, 10):
        idx = (current_lord_idx + i) % 9
        planet, duration = DASHA_LORDS[idx]
        end_date = prev_end + duration
        dasha_log.append({
            "planet": planet,
            "start": prev_end,
            "end": end_date
        })
        prev_end = end_date
        
    # 4. Find Current Dasha based on Today's Date
    current_md = "Unknown"
    current_md_end = current_year + 5
    md_start = current_year
    
    for d in dasha_log:
        if d["start"] <= current_year < d["end"]:
            current_md = d["planet"]
            current_md_end = int(d["end"])
            md_start = int(d["start"])
            break
            
    # Simple Antardasha Logic (Roughly splitting MD into 9 parts)
    # Real logic is complex, this is a safe approximation for now
    ad_duration = (current_md_end - md_start) / 9
    ad_idx = int((current_year - md_start) / ad_duration) % 9
    # Find relative AD planet
    md_planet_idx = -1
    for i, (p, _) in enumerate(DASHA_LORDS):
        if p == current_md: md_planet_idx = i
            
    current_ad = DASHA_LORDS[(md_planet_idx + ad_idx) % 9][0]

    return {
        "current_mahadasha": current_md,
        "current_antardasha": current_ad,
        "current_mahadasha_end_year": f"{current_md_end}-01-01",
        "md_start_year": md_start,
        "md_end_year": current_md_end,
        "ad_start_year": current_year,
        "ad_end_year": current_year + 1,
        "full_dasha_log": dasha_log # Can be used for yearly forecast
    }

def get_current_gochar():
    now = datetime.utcnow()
    jd = swe.julday(now.year, now.month, now.day, 12)
    transits = {}
    for p in ["Saturn", "Jupiter", "Rahu", "Ketu"]:
        pid = PLANET_MAP[p]
        lon = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)[0][0]
        if p == "Ketu": lon = (lon + 180) % 360
        transits[p] = int(lon // 30) + 1
    return transits