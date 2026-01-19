# rules/vimshottari_table.py
# -------------------------
# Full Vimshottari Dasha Table (9 Mahadashas + Antardashas)
# Paid-grade, AstroSage-style

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

DASHA_EFFECTS = {
    "Sun": ("authority, leadership", "status-linked income", "confidence"),
    "Moon": ("public interaction", "family support", "emotional focus"),
    "Mars": ("action, competition", "risk-reward cycles", "assertiveness"),
    "Mercury": ("business, trade", "multiple incomes", "analysis"),
    "Jupiter": ("growth, guidance", "wealth expansion", "optimism"),
    "Venus": ("creativity, partnerships", "luxury & comfort", "harmony"),
    "Saturn": ("slow progress", "delayed stability", "discipline"),
    "Rahu": ("sudden rise", "irregular gains", "ambition"),
    "Ketu": ("detachment", "reduced material focus", "withdrawal"),
}


def build_vimshottari_table(start_year):
    """
    Builds full Vimshottari timeline from start year
    Returns list of Mahadasha blocks with Antardashas
    """

    timeline = []
    current_year = int(start_year)

    for md_planet, md_years in VIMSHOTTARI_ORDER:
        md_start = current_year
        md_end = current_year + md_years

        md_block = {
            "planet": md_planet,
            "start": md_start,
            "end": md_end,
            "antardasha": []
        }

        # Antardashas proportional
        for ad_planet, ad_years in VIMSHOTTARI_ORDER:
            ad_duration = (md_years * ad_years) / 120.0
            ad_start = current_year
            ad_end = ad_start + ad_duration

            md_block["antardasha"].append({
                "planet": ad_planet,
                "start": round(ad_start, 2),
                "end": round(ad_end, 2)
            })

            current_year = ad_end

        timeline.append(md_block)

        current_year = md_end

    return timeline


def format_vimshottari_table(start_year):
    table = build_vimshottari_table(start_year)
    text = "<b>Complete Vimshottari Dasha Timeline</b>\n\n"

    for md in table:
        eff = DASHA_EFFECTS.get(md["planet"], ("—", "—", "—"))
        text += (
            f"Mahadasha: {md['planet']} ({md['start']} – {md['end']})\n"
            f"Career: {eff[0]}\n"
            f"Money: {eff[1]}\n"
            f"Mind: {eff[2]}\n"
            f"Antardashas:\n"
        )

        for ad in md["antardasha"]:
            text += f"  - {ad['planet']}: {ad['start']} – {ad['end']}\n"

        text += "\n"

    return text
