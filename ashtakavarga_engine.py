# ashtakavarga_engine.py
# ---------------------
# Professional Ashtakavarga Engine
# (Premium Kundali Feature)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Simplified traditional benefic houses per planet
ASHTAKA_RULES = {
    "Sun":      [3, 6, 10, 11],
    "Moon":     [1, 3, 6, 7, 10, 11],
    "Mars":     [3, 6, 10, 11],
    "Mercury":  [1, 3, 5, 6, 9, 10, 11],
    "Jupiter":  [2, 5, 7, 9, 11],
    "Venus":    [1, 2, 3, 4, 5, 8, 9, 11],
    "Saturn":   [3, 6, 10, 11]
}

# --------------------------------------------------
# BHINNASHTAKAVARGA
# --------------------------------------------------

def calculate_bhinnashtakavarga(planets):
    """
    Returns planet-wise Ashtakavarga scores
    """
    bav = {}

    for p in PLANETS:
        bav[p] = {i: 0 for i in range(1, 13)}

    for ref in PLANETS:
        ref_house = next(
            int(p["House"]) for p in planets if p["Planet"] == ref
        )

        for target in PLANETS:
            good_houses = ASHTAKA_RULES[target]
            for h in good_houses:
                score_house = ((ref_house + h - 1) % 12) + 1
                bav[target][score_house] += 1

    return bav

# --------------------------------------------------
# SARVASHTAKAVARGA
# --------------------------------------------------

def calculate_sarvashtakavarga(bav):
    """
    Sum of all planet scores per house
    """
    sav = {i: 0 for i in range(1, 13)}

    for planet in bav.values():
        for house, score in planet.items():
            sav[house] += score

    return sav

# --------------------------------------------------
# INTERPRETATION
# --------------------------------------------------

def interpret_house_strength(score):
    if score >= 30:
        return "Very Strong"
    elif score >= 25:
        return "Strong"
    elif score >= 20:
        return "Average"
    else:
        return "Weak"

# --------------------------------------------------
# MAIN ENTRY
# --------------------------------------------------

def calculate_ashtakavarga(planets):
    """
    planets → list from astro_engine
    """

    bav = calculate_bhinnashtakavarga(planets)
    sav = calculate_sarvashtakavarga(bav)

    house_analysis = {
        house: {
            "Score": score,
            "Strength": interpret_house_strength(score)
        }
        for house, score in sav.items()
    }

    return {
        "Bhinnashtakavarga": bav,
        "Sarvashtakavarga": house_analysis
    }
