# rules/summary_page.py
# --------------------
# Final Summary Page Engine
# Best Years / Weak Years / Key Life Phases

def derive_summary_page(
    confidence_scores,
    stress_growth_table,
    career_timeline,
    marriage_timeline
):
    """
    Builds final executive-style summary
    """

    best_years = []
    weak_years = []

    for row in confidence_scores:
        if row["confidence"] >= 80:
            best_years.append(row["year"])
        elif row["confidence"] <= 55:
            weak_years.append(row["year"])

    text = "<b>Final Life Summary & Highlights</b>\n\n"

    # ---- BEST YEARS ----
    if best_years:
        text += "⭐ Strong & Favorable Years:\n"
        text += ", ".join(str(y) for y in best_years[:8])
        text += "\n\n"
    else:
        text += "⭐ Strong Years:\nGradual progress without extreme peaks.\n\n"

    # ---- WEAK / CAUTION YEARS ----
    if weak_years:
        text += "⚠️ Caution / Stress Years:\n"
        text += ", ".join(str(y) for y in weak_years[:8])
        text += "\n\n"
    else:
        text += "⚠️ Caution Years:\nNo major stress-dominant phases observed.\n\n"

    # ---- CAREER SUMMARY ----
    text += "💼 Career Highlights:\n"
    text += (
        f"Career rise begins around {career_timeline.get('career_rise_start')}. "
        f"Peak phase observed near {career_timeline.get('career_peak')}. "
        f"Long-term stability after {career_timeline.get('career_stability')}.\n\n"
    )

    # ---- MARRIAGE SUMMARY ----
    text += "💍 Marriage Highlights:\n"
    text += (
        f"Marriage window indicated between "
        f"{marriage_timeline.get('marriage_start')} – {marriage_timeline.get('marriage_end')}. "
        f"Post-marriage stability improves after "
        f"{marriage_timeline.get('stability_after')}.\n\n"
    )

    # ---- FINAL NOTE ----
    text += (
        "This summary is derived from planetary periods, house strength, "
        "and long-term dasha activation. Results intensify during favorable "
        "periods and soften during transition phases."
    )

    return text
