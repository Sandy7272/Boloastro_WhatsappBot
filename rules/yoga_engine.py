# rules/yoga_engine.py
# --------------------
# Yoga detection engine (Paid-grade)
# Manglik, Raj Yoga, Dhan Yoga, Kaal Sarp
# Supports both List (New) and Dict (Old) chart structures

MANGAL_DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}
RAJ_YOGA_HOUSES = {1, 4, 5, 7, 9, 10}
DHAN_YOGA_HOUSES = {2, 5, 9, 11}

def get_planet_positions(chart):
    """
    Helper function to normalize chart data into a simple dictionary.
    Returns: {'Sun': 1, 'Moon': 4, ...}
    """
    positions = {}
    
    if isinstance(chart, list):
        # NEW ENGINE (List of dicts)
        for house in chart:
            h_num = house.get("house")
            for p in house.get("planets", []):
                positions[p] = h_num
                
    elif isinstance(chart, dict):
        # OLD ENGINE (Direct dict)
        for k, v in chart.items():
            if "_house" in k:
                p_name = k.replace("_house", "")
                positions[p_name] = v
            elif k in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                positions[k] = v
                
    return positions


def detect_manglik(chart):
    pos = get_planet_positions(chart)
    
    mars_house = pos.get("Mars")
    moon_house = pos.get("Moon")
    
    result = {
        "status": "Not Present",
        "description": ""
    }

    if not mars_house:
        return result

    # 1. Check from Lagna (Ascendant)
    is_manglik_lagna = mars_house in MANGAL_DOSHA_HOUSES
    
    # 2. Check from Moon (Chandra Lagna)
    is_manglik_moon = False
    if moon_house:
        # Calculate Mars position relative to Moon
        # Formula: (Mars - Moon + 1) -> Adjust for circular 1-12
        mars_from_moon = (mars_house - moon_house) + 1
        if mars_from_moon <= 0:
            mars_from_moon += 12
            
        if mars_from_moon in MANGAL_DOSHA_HOUSES:
            is_manglik_moon = True

    # 3. Determine Final Status
    if is_manglik_lagna and is_manglik_moon:
        result["status"] = "Present (High Intensity)"
        result["description"] = (
            "Manglik Dosha is present from both Lagna and Moon. "
            "Matching of horoscopes before marriage is highly recommended."
        )
    elif is_manglik_lagna:
        result["status"] = "Present from Lagna"
        result["description"] = (
            "Manglik Dosha is indicated from Lagna. "
            "This influences temperament and requires patience in relationships."
        )
    elif is_manglik_moon:
        result["status"] = "Present from Moon"
        result["description"] = (
            "Manglik Dosha is indicated from Moon chart. "
            "Emotional compatibility should be checked."
        )
    else:
        result["description"] = (
            "Manglik Dosha is not indicated. "
            "Marriage stability is supported astrologically."
        )

    return result


def detect_raj_yoga(chart):
    pos = get_planet_positions(chart)
    
    sun = pos.get("Sun")
    moon = pos.get("Moon")
    jupiter = pos.get("Jupiter")
    saturn = pos.get("Saturn")

    strong_planets = [
        p for p in [sun, moon, jupiter, saturn]
        if p in RAJ_YOGA_HOUSES
    ]

    if len(strong_planets) >= 2:
        return {
            "status": "Present",
            "description": (
                "Raj Yoga is formed due to the placement of key planets "
                "in Kendra or Trikona houses. This indicates authority, "
                "career elevation, and recognition during favorable dashas."
            )
        }

    return {
        "status": "Not Prominent",
        "description": (
            "Strong Raj Yoga formation is not prominent. "
            "Results depend primarily on Dasha activation."
        )
    }


def detect_dhan_yoga(chart):
    pos = get_planet_positions(chart)
    
    jupiter = pos.get("Jupiter")
    venus = pos.get("Venus")
    moon = pos.get("Moon")

    wealth_planets = [
        p for p in [jupiter, venus, moon]
        if p in DHAN_YOGA_HOUSES
    ]

    if len(wealth_planets) >= 2:
        return {
            "status": "Present",
            "description": (
                "Dhan Yoga is indicated, supporting wealth accumulation, "
                "financial stability, and asset creation during active periods."
            )
        }

    return {
        "status": "Moderate",
        "description": (
            "Strong Dhan Yoga is not dominant. "
            "Financial growth occurs gradually through effort and timing."
        )
    }


def detect_kaal_sarp(chart):
    pos = get_planet_positions(chart)
    
    rahu = pos.get("Rahu")
    ketu = pos.get("Ketu")
    
    # Identify all 7 main planets
    main_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_houses = [pos.get(p) for p in main_planets if pos.get(p)]

    if not rahu or not ketu or not planet_houses:
        return {
            "status": "Unknown",
            "description": "Insufficient data to determine Kaal Sarp Yoga."
        }

    # Logic: Check if all planets are on one side of Rahu/Ketu axis
    # Simplified Logic:
    # 1. Sort all planet houses
    # 2. Check if they fall strictly between Rahu and Ketu OR Ketu and Rahu
    
    # For robust check, we need exact degrees, but for house-based:
    lower = min(rahu, ketu)
    upper = max(rahu, ketu)
    
    # Count planets between lower and upper
    between_count = sum(1 for h in planet_houses if lower < h < upper)
    total_planets = len(planet_houses)
    
    # If ALL planets are inside OR NO planets are inside (meaning they are on the other side)
    if between_count == total_planets or between_count == 0:
        return {
            "status": "Present",
            "description": (
                "Kaal Sarp Yoga is indicated. "
                "Life progress may involve sudden changes, delays, "
                "and sharp rises during specific dasha periods."
            )
        }

    return {
        "status": "Not Present",
        "description": (
            "Kaal Sarp Yoga is not indicated. "
            "Life progress remains comparatively balanced."
        )
    }