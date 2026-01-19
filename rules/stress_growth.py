# rules/stress_growth.py
# ---------------------
# Stress vs Growth Year Classification Engine
# Paid astrology app grade logic

STRESS_PLANETS = {"Saturn", "Rahu", "Ketu", "Mars"}
GROWTH_PLANETS = {"Jupiter", "Venus", "Sun", "Mercury", "Moon"}


def derive_stress_growth_table(dasha, birth_year, years=20):
    """
    Returns a table classifying years as Stress / Growth / Neutral
    """

    birth_year = int(birth_year)
    table = []

    md = dasha.get("current_mahadasha", "Unknown")
    md_start = dasha.get("md_start_year")
    md_end = dasha.get("md_end_year")

    for i in range(years):
        year = birth_year + i
        age = i

        if md_start <= year <= md_end:
            if md in STRESS_PLANETS:
                phase = "Stress Year"
                note = "Increased pressure, responsibility, or uncertainty"
            elif md in GROWTH_PLANETS:
                phase = "Growth Year"
                note = "Expansion, progress, and constructive outcomes"
            else:
                phase = "Neutral Year"
                note = "Balanced results without extremes"
        else:
            phase = "Transition Year"
            note = "Preparatory phase or change in life direction"

        table.append({
            "year": year,
            "age": age,
            "phase": phase,
            "note": note
        })

    return table
