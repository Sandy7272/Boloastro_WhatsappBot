# rules/pratyantar_dasha.py
# ------------------------
# Pratyantar Dasha (MD → AD → PD)
# Ultra-detailed timing engine (Paid / Enterprise grade)

VIMSHOTTARI_ORDER = [
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17),
]

DASHA_THEMES = {
    "Sun": "authority, recognition, leadership matters",
    "Moon": "emotions, family, mental focus",
    "Mars": "action, conflict, decisive events",
    "Mercury": "business, communication, learning",
    "Jupiter": "growth, marriage, expansion",
    "Venus": "relationships, comfort, luxury",
    "Saturn": "delay, pressure, responsibility",
    "Rahu": "sudden change, ambition, instability",
    "Ketu": "detachment, isolation, internal shift",
}


def build_pratyantar_dasha(md_planet, ad_planet, ad_start, ad_years):
    """
    Builds Pratyantar Dasha inside an Antardasha
    """

    pd_list = []
    current_year = ad_start

    for pd_planet, pd_years in VIMSHOTTARI_ORDER:
        duration = (ad_years * pd_years) / 120.0
        pd_start = current_year
        pd_end = pd_start + duration

        pd_list.append({
            "planet": pd_planet,
            "start": round(pd_start, 2),
            "end": round(pd_end, 2),
            "theme": DASHA_THEMES.get(pd_planet, "mixed events")
        })

        current_year = pd_end

    return pd_list


def format_pratyantar_dasha(md_planet, ad_planet, ad_start, ad_end):
    """
    Returns formatted Pratyantar Dasha section
    """

    ad_years = ad_end - ad_start
    pd_table = build_pratyantar_dasha(md_planet, ad_planet, ad_start, ad_years)

    text = (
        "<b>Pratyantar Dasha (Sub-Period Analysis)</b>\n\n"
        f"Mahadasha: {md_planet}\n"
        f"Antardasha: {ad_planet} ({round(ad_start,2)} – {round(ad_end,2)})\n\n"
    )

    for pd in pd_table:
        text += (
            f"{pd['planet']} Pratyantar: "
            f"{pd['start']} – {pd['end']}\n"
            f"Focus: {pd['theme']}\n\n"
        )

    return text
