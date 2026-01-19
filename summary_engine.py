# summary_engine.py
# -----------------
# Master Conclusion & Verdict Engine
# (Paid Kundali Final Pages)

from datetime import datetime

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def score_to_label(score):
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Strong"
    elif score >= 50:
        return "Moderate"
    else:
        return "Weak"


def house_strength_label(strength):
    return {
        "Very Strong": "highly supportive",
        "Strong": "supportive",
        "Average": "moderately supportive",
        "Weak": "challenging"
    }.get(strength, "average")


# --------------------------------------------------
# AGE & YEAR CALCULATION
# --------------------------------------------------

def get_age(dob):
    dob_dt = datetime.strptime(dob, "%d-%m-%Y")
    today = datetime.today()
    return today.year - dob_dt.year


def build_year_table(start_age=18, years=20):
    current_year = datetime.today().year
    return [
        {
            "Year": current_year + i,
            "Age": start_age + i
        }
        for i in range(years)
    ]


# --------------------------------------------------
# CORE SUMMARY LOGIC
# --------------------------------------------------

def generate_summary(values):
    """
    values = {
        SHADBALA,
        ASHTAKAVARGA,
        DASHA,
        GOCHAR,
        DOB,
        CAREER_HOUSE,
        MARRIAGE_HOUSE
    }
    """

    shadbala = values["SHADBALA"]
    ashtaka = values["ASHTAKAVARGA"]["Sarvashtakavarga"]

    # ---------------- CAREER ----------------
    career_house = 10
    career_score = ashtaka[career_house]["Score"]
    career_strength = ashtaka[career_house]["Strength"]

    career_verdict = (
        f"The tenth house shows {house_strength_label(career_strength)} "
        f"conditions for professional growth. Career progress is shaped "
        f"by consistency, responsibility, and long-term planning rather "
        f"than sudden gains."
    )

    # ---------------- MARRIAGE ----------------
    marriage_house = 7
    marriage_score = ashtaka[marriage_house]["Score"]
    marriage_strength = ashtaka[marriage_house]["Strength"]

    marriage_verdict = (
        f"The seventh house indicates {house_strength_label(marriage_strength)} "
        f"marital prospects. Stability improves with maturity, and relationships "
        f"develop through understanding and shared responsibility."
    )

    # ---------------- WEALTH ----------------
    wealth_score = (ashtaka[2]["Score"] + ashtaka[11]["Score"]) / 2
    wealth_label = score_to_label(wealth_score * 3)

    wealth_verdict = (
        f"Financial accumulation follows a {wealth_label.lower()} pattern. "
        f"Wealth grows through structured effort and long-term planning "
        f"rather than speculative or impulsive decisions."
    )

    # ---------------- PLANETARY POWER ----------------
    strong_planets = [
        p for p, v in shadbala.items()
        if v["Strength Level"] in ["Very Strong", "Strong"]
    ]

    weak_planets = [
        p for p, v in shadbala.items()
        if v["Strength Level"] == "Weak"
    ]

    # ---------------- CONFIDENCE SCORE ----------------
    avg_bala = sum(v["Total Shadbala"] for v in shadbala.values()) / len(shadbala)
    confidence_score = min(95, int(avg_bala / 3))

    # ---------------- YEARLY TREND ----------------
    age = get_age(values["DOB"])
    years = build_year_table(age, 20)

    for y in years:
        if y["Age"] % 6 == 0:
            y["Trend"] = "Growth Phase"
        elif y["Age"] % 4 == 0:
            y["Trend"] = "Stress Phase"
        else:
            y["Trend"] = "Neutral Phase"

    # ---------------- FINAL SUMMARY ----------------
    return {
        "Career Summary": career_verdict,
        "Marriage Summary": marriage_verdict,
        "Wealth Summary": wealth_verdict,
        "Strong Planets": strong_planets,
        "Weak Planets": weak_planets,
        "Confidence Score": f"{confidence_score}%",
        "Yearly Trend Table": years
    }
