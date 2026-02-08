# shadbala_engine.py
# -----------------
# Professional Shadbala Strength Engine
# (Paid Kundali Standard)

import math
from datetime import datetime

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

NAISARGIKA_BALA = {
    "Sun": 60,
    "Moon": 51,
    "Mars": 42,
    "Mercury": 34,
    "Jupiter": 56,
    "Venus": 43,
    "Saturn": 39,
    "Rahu": 30,
    "Ketu": 30
}

DIG_BALA_HOUSES = {
    "Sun": 10,
    "Moon": 4,
    "Mars": 10,
    "Mercury": 1,
    "Jupiter": 1,
    "Venus": 4,
    "Saturn": 7
}

EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra"
}

DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries"
}

# --------------------------------------------------
# BALAS
# --------------------------------------------------

def sthana_bala(planet):
    """Positional strength"""
    sign = planet["Sign"]
    name = planet["Planet"]

    if name in EXALTATION_SIGNS and sign == EXALTATION_SIGNS[name]:
        return 60
    if name in DEBILITATION_SIGNS and sign == DEBILITATION_SIGNS[name]:
        return 10
    return 30


def dig_bala(planet):
    """Directional strength"""
    name = planet["Planet"]
    house = planet["House"]

    if name in DIG_BALA_HOUSES and house == DIG_BALA_HOUSES[name]:
        return 60
    return 30


def kala_bala(planet, birth_time):
    """Day/Night strength"""
    hour = birth_time.hour
    is_day = 6 <= hour <= 18
    name = planet["Planet"]

    if name in ["Sun", "Jupiter", "Saturn"] and is_day:
        return 60
    if name in ["Moon", "Mars", "Venus"] and not is_day:
        return 60
    return 30


def cheshta_bala(planet):
    """Motion strength (retro logic expandable)"""
    # Swiss Ephemeris retrograde flag can be added later
    return 30


def drik_bala(planet):
    """Aspect strength placeholder"""
    return 30


# --------------------------------------------------
# MAIN SHADBALA CALCULATION
# --------------------------------------------------

def calculate_shadbala(planets, dob, time):
    """
    planets → list from astro_engine
    dob/time → user input
    """

    birth_dt = datetime.strptime(
        f"{dob} {time}", "%d-%m-%Y %H:%M"
    )

    result = {}

    for p in planets:
        name = p["Planet"]

        sb = sthana_bala(p)
        db = dig_bala(p)
        kb = kala_bala(p, birth_dt)
        cb = cheshta_bala(p)
        drb = drik_bala(p)
        nb = NAISARGIKA_BALA.get(name, 30)

        total = sb + db + kb + cb + drb + nb

        result[name] = {
            "Sthana Bala": sb,
            "Dig Bala": db,
            "Kala Bala": kb,
            "Cheshta Bala": cb,
            "Drik Bala": drb,
            "Naisargika Bala": nb,
            "Total Shadbala": total,
            "Strength Level": (
                "Very Strong" if total >= 260 else
                "Strong" if total >= 220 else
                "Average" if total >= 180 else
                "Weak"
            )
        }

    return result
