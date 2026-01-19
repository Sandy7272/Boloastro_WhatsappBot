# rules/confidence_score.py
# ------------------------
# Year-wise Confidence Score Engine (0–100)

CONFIDENCE_PLANETS = {
    "Sun": 15,
    "Jupiter": 20,
    "Venus": 15,
    "Mercury": 10,
    "Moon": 10,
    "Mars": 5,
    "Saturn": -10,
    "Rahu": -5,
    "Ketu": -5,
}


def derive_confidence_scores(chart, dasha, birth_year, years=20):
    """
    Returns year-wise confidence score (0–100).
    Handles List vs Dict chart formats.
    """

    birth_year = int(birth_year)
    scores = []

    md = dasha.get("current_mahadasha", "Unknown")
    md_start = dasha.get("md_start_year")
    md_end = dasha.get("md_end_year")

    # --- 1. FIND PLANET HOUSES (Safe Logic) ---
    planet_houses = {}
    
    if isinstance(chart, list):
        for house in chart:
            h_num = house.get("house")
            for p in house.get("planets", []):
                planet_houses[p] = h_num
    elif isinstance(chart, dict):
        planet_houses = {k.replace("_house", ""): v for k, v in chart.items()}

    sun_house = planet_houses.get("Sun")
    moon_house = planet_houses.get("Moon")

    # --- 2. CALCULATE SCORES ---
    for i in range(years):
        year = birth_year + i
        age = i

        score = 50  # neutral base

        # ---- Dasha impact ----
        if md_start <= year <= md_end:
            score += CONFIDENCE_PLANETS.get(md, 0)

        # ---- House support ----
        if sun_house in {1, 5, 9, 10, 11}:
            score += 10
        if moon_house in {1, 4, 7, 11}:
            score += 5

        # ---- Boundaries ----
        score = max(10, min(100, score))

        scores.append({
            "year": year,
            "age": age,
            "confidence": score
        })

    return scores