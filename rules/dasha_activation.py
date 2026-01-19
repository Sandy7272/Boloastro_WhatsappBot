# rules/dasha_activation.py
# -------------------------
# Planet activation timing using Mahadasha / Antardasha
# Paid-level predictive timing logic

PLANET_THEMES = {
    "Sun": "authority, career growth, reputation, leadership",
    "Moon": "emotions, mind, home, mother, stability",
    "Mars": "action, conflict, marriage dynamics, courage",
    "Mercury": "communication, business, learning, trade",
    "Jupiter": "growth, marriage, children, wealth, wisdom",
    "Venus": "love, marriage, luxury, comfort, relationships",
    "Saturn": "delay, karma, discipline, long-term stability",
    "Rahu": "sudden events, ambition, foreign influence",
    "Ketu": "detachment, isolation, inner transformation",
}


def activate_planet_result(planet, house, dasha):
    """
    Returns timing-based activation text for planet results
    """

    activations = []

    current_md = dasha.get("current_mahadasha")
    current_ad = dasha.get("current_antardasha")

    md_start = dasha.get("md_start_year")
    md_end = dasha.get("md_end_year")

    ad_start = dasha.get("ad_start_year")
    ad_end = dasha.get("ad_end_year")

    if current_md == planet:
        activations.append(
            f"{planet} Mahadasha ({md_start} – {md_end})"
        )

    if current_ad == planet:
        activations.append(
            f"{planet} Antardasha ({ad_start} – {ad_end})"
        )

    if activations:
        return (
            f"This planetary placement becomes strongly active during "
            f"{' and '.join(activations)}. "
            f"During this phase, matters related to the {house} house such as "
            f"{PLANET_THEMES.get(planet, 'key life themes')} "
            f"manifest prominently and produce visible life events."
        )

    return (
        f"This placement remains comparatively passive during the current period "
        f"and produces secondary results through transits or related planetary influences."
    )
