"""
ai_helper.py
-------------
Builds Ultimate VIP Kundali data
(No AI, only rules + templates)
"""

from rules.rules import derive_values
from templates.mr.vip import TEMPLATE as MR_TEMPLATE
from templates.hi.vip import TEMPLATE as HI_TEMPLATE
from templates.en.vip import TEMPLATE as EN_TEMPLATE


TEMPLATE_MAP = {
    "mr": MR_TEMPLATE,
    "hi": HI_TEMPLATE,
    "en": EN_TEMPLATE
}


# --------------------------------------------------
# SANITIZER (FONT / UNICODE SAFE)
# --------------------------------------------------

def sanitize_text(text: str) -> str:
    """
    Removes or replaces decorative symbols
    not supported by Devanagari fonts.
    """
    return (
        text
        .replace("━", "-")
        .replace("═", "-")
        .replace("🔹", "")
        .replace("→", "->")
    )


# --------------------------------------------------
# TEMPLATE FILLER (STRICT + SAFE)
# --------------------------------------------------

def fill_template(template_text: str, values: dict) -> str:
    """
    Safely replace placeholders.
    If any placeholder is missing → raise error.
    Also sanitizes unsupported glyphs.
    """
    try:
        filled = template_text.format(**values)
        return sanitize_text(filled)
    except KeyError as e:
        raise Exception(f"❌ Missing placeholder value: {e}")


# --------------------------------------------------
# MAIN BUILDER
# --------------------------------------------------

def build_vip_kundali(chart, planets, dasha, language, user):
    """
    MAIN ENTRY POINT
    Called from app.py
    """

    # 1️⃣ Compute all astrology values
    values = derive_values(
        chart=chart,
        planets=planets,
        dasha=dasha,
        user=user,
        language=language
    )

    # 2️⃣ Select correct language template
    template = TEMPLATE_MAP[language]

    # 3️⃣ Build final rendered sections
    kundali_text = {}

    for section, text in template.items():
        kundali_text[section] = fill_template(text, values)

    # 4️⃣ Return structured result
    return {
        "sections": kundali_text,
        "values": values
    }
