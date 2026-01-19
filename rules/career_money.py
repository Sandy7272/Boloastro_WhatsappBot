# rules/career_money.py
# --------------------
# Career vs Money strength comparison (20-year)

CAREER_PLANETS = {"Sun", "Saturn", "Mercury", "Mars"}
MONEY_PLANETS = {"Jupiter", "Venus", "Moon"}

CAREER_HOUSES = {6, 10, 11}
MONEY_HOUSES = {2, 5, 9, 11}


def derive_career_money_chart(chart, dasha, birth_year, years=20):
    """
    Returns year-wise Career vs Money strength table.
    Handles both List (New Engine) and Dict (Old Engine) chart formats.
    """

    birth_year = int(birth_year)
    table = []

    md = dasha.get("current_mahadasha", "Unknown")
    md_start = dasha.get("md_start_year")
    md_end = dasha.get("md_end_year")

    # --- 1. FIND PLANET HOUSES (Safe Logic) ---
    planet_houses = {}
    
    if isinstance(chart, list):
        # Naya Format: List of houses iterate karein
        for house in chart:
            h_num = house.get("house")
            for p in house.get("planets", []):
                planet_houses[p] = h_num
    elif isinstance(chart, dict):
        # Purana Format: Direct keys
        # Fallback logic just in case
        planet_houses = {k.replace("_house", ""): v for k, v in chart.items()}

    sun_house = planet_houses.get("Sun")
    jupiter_house = planet_houses.get("Jupiter")
    venus_house = planet_houses.get("Venus")

    # --- 2. GENERATE TABLE ---
    for i in range(years):
        year = birth_year + i
        age = i

        career_score = 0
        money_score = 0

        # ---- Dasha influence ----
        if md in CAREER_PLANETS and md_start <= year <= md_end:
            career_score += 2
        if md in MONEY_PLANETS and md_start <= year <= md_end:
            money_score += 2

        # ---- Planet house strength ----
        if sun_house in CAREER_HOUSES:
            career_score += 1
        if jupiter_house in MONEY_HOUSES:
            money_score += 1
        if venus_house in MONEY_HOUSES:
            money_score += 1

        # ---- Classification ----
        if career_score > money_score:
            result = "Career Dominant Year"
        elif money_score > career_score:
            result = "Money Dominant Year"
        else:
            result = "Balanced Year"

        table.append({
            "year": year,
            "age": age,
            "career_score": career_score,
            "money_score": money_score,
            "result": result
        })

    return table