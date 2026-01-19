# rules/dasha_table.py
# -------------------
# Mahadasha / Antardasha Timeline Engine
# Paid-grade (AstroSage-style)

DASHA_EFFECTS = {
    "Sun": {
        "career": "authority, leadership, visibility",
        "money": "steady income, status-linked gains",
        "mind": "confidence, ego awareness",
    },
    "Moon": {
        "career": "public interaction, adaptability",
        "money": "fluctuating income, family support",
        "mind": "emotional sensitivity, intuition",
    },
    "Mars": {
        "career": "action-driven roles, competition",
        "money": "sudden expenses, risk-reward cycles",
        "mind": "assertiveness, impatience",
    },
    "Mercury": {
        "career": "business, communication, trade",
        "money": "multiple income streams",
        "mind": "analytical thinking",
    },
    "Jupiter": {
        "career": "growth, guidance, authority",
        "money": "wealth expansion, assets",
        "mind": "optimism, wisdom",
    },
    "Venus": {
        "career": "creative fields, partnerships",
        "money": "luxury, comforts, gains",
        "mind": "emotional balance",
    },
    "Saturn": {
        "career": "slow progress, responsibility",
        "money": "delayed but stable gains",
        "mind": "discipline, pressure",
    },
    "Rahu": {
        "career": "sudden rise, unconventional paths",
        "money": "irregular gains",
        "mind": "restlessness, ambition",
    },
    "Ketu": {
        "career": "detachment, behind-the-scenes work",
        "money": "reduced material focus",
        "mind": "introspection, withdrawal",
    },
}


def derive_dasha_table(dasha):
    """
    Returns formatted Mahadasha + Antardasha table
    """

    md = dasha.get("current_mahadasha")
    ad = dasha.get("current_antardasha")

    md_start = dasha.get("md_start_year")
    md_end = dasha.get("md_end_year")

    ad_start = dasha.get("ad_start_year")
    ad_end = dasha.get("ad_end_year")

    text = "<b>Mahadasha & Antardasha Analysis</b>\n\n"

    # ---- MAHADASHA ----
    if md:
        eff = DASHA_EFFECTS.get(md, {})
        text += (
            f"Mahadasha: {md}\n"
            f"Period: {md_start} – {md_end}\n"
            f"Career Impact: {eff.get('career','—')}\n"
            f"Financial Impact: {eff.get('money','—')}\n"
            f"Mental State: {eff.get('mind','—')}\n\n"
        )

    # ---- ANTARDASHA ----
    if ad:
        eff = DASHA_EFFECTS.get(ad, {})
        text += (
            f"Antardasha: {ad}\n"
            f"Period: {ad_start} – {ad_end}\n"
            f"Career Impact: {eff.get('career','—')}\n"
            f"Financial Impact: {eff.get('money','—')}\n"
            f"Mental State: {eff.get('mind','—')}\n"
        )

    return text
