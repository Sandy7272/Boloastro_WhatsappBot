# qa_engine.py
# ------------
# Fully Automated Q&A Engine (Deterministic)

def answer_question(question, values):
    q = question.lower()

    summary = values["SUMMARY"]
    ashtaka = values["ASHTAKAVARGA"]["Sarvashtakavarga"]

    # ---------------- Marriage ----------------
    if any(k in q for k in ["marriage", "shaadi", "lagna"]):
        return summary["Marriage Summary"]

    # ---------------- Career ----------------
    if any(k in q for k in ["career", "job", "promotion", "business"]):
        return summary["Career Summary"]

    # ---------------- Money ----------------
    if any(k in q for k in ["money", "wealth", "income", "finance"]):
        return summary["Wealth Summary"]

    # ---------------- Vehicle ----------------
    if any(k in q for k in ["car", "vehicle", "bike"]):
        h4 = ashtaka[4]
        return (
            f"Vehicle purchase is linked to the 4th house.\n\n"
            f"Your 4th house score: {h4['Score']} ({h4['Strength']}).\n"
            f"Growth-phase years are more suitable for vehicle purchase."
        )

    # ---------------- Property ----------------
    if any(k in q for k in ["house", "property", "flat", "home"]):
        h4 = ashtaka[4]
        return (
            f"Property matters depend on long-term stability.\n\n"
            f"4th house strength: {h4['Strength']}.\n"
            f"Results improve during strong planetary periods."
        )

    # ---------------- Stress ----------------
    if any(k in q for k in ["stress", "problem", "difficult"]):
        years = summary["Yearly Trend Table"]
        stress = [y for y in years if y["Trend"] == "Stress Phase"]
        return (
            "Stress-prone years:\n" +
            "\n".join([f"{y['Year']} (Age {y['Age']})" for y in stress[:5]])
        )

    # ---------------- Default ----------------
    return (
        "Please ask a clear question related to:\n"
        "Marriage, Career, Money, Vehicle, Property, or Stress Years."
    )
