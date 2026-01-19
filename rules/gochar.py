# rules/gochar.py
# ----------------
# Gochar (Planetary Transit) Engine
# Paid-grade transit interpretation

GOCHAR_EFFECTS = {
    "Saturn": {
        "career": "slow restructuring, responsibility increase",
        "money": "delayed gains, expense control",
        "mind": "pressure, maturity, discipline",
    },
    "Jupiter": {
        "career": "growth opportunities, recognition",
        "money": "financial expansion, stability",
        "mind": "optimism, clarity",
    },
    "Rahu": {
        "career": "sudden changes, unconventional paths",
        "money": "irregular income patterns",
        "mind": "restlessness, ambition",
    },
    "Ketu": {
        "career": "detachment from roles",
        "money": "reduced material focus",
        "mind": "introspection",
    },
}


def derive_gochar_report(chart, current_transits):
    """
    current_transits = {
        "Saturn": house_number,
        "Jupiter": house_number,
        "Rahu": house_number,
        "Ketu": house_number
    }
    """

    text = "<b>Current Planetary Transits (Gochar)</b>\n\n"

    for planet, house in current_transits.items():
        eff = GOCHAR_EFFECTS.get(planet, {})
        text += (
            f"{planet} Transit in House {house}\n"
            f"Career Impact: {eff.get('career','—')}\n"
            f"Financial Impact: {eff.get('money','—')}\n"
            f"Mental Impact: {eff.get('mind','—')}\n\n"
        )

    text += (
        "Transit results modify ongoing dasha effects. "
        "Stronger outcomes occur when Gochar and Dasha support the same themes."
    )

    return text
