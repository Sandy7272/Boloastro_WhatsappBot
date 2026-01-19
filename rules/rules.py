# rules/rules.py
# --------
# Master rule engine combining
# Planet-in-house meanings + Dasha activation timing

from rules.dasha_activation import activate_planet_result
from rules.marriage_timing import derive_marriage_timeline
from rules.career_timing import derive_career_timeline
from rules.yoga_engine import (
    detect_manglik,
    detect_raj_yoga,
    detect_dhan_yoga,
    detect_kaal_sarp
)

# Try importing yearly forecast, fallback if missing
try:
    from rules.yearly_forecast import derive_yearly_forecast
    derive_20_year_forecast = derive_yearly_forecast 
except ImportError:
    def derive_yearly_forecast(*args, **kwargs): return []
    derive_20_year_forecast = derive_yearly_forecast

from rules.stress_growth import derive_stress_growth_table
from rules.career_money import derive_career_money_chart
from rules.confidence_score import derive_confidence_scores
from rules.summary_page import derive_summary_page
from rules.dasha_table import derive_dasha_table
from rules.vimshottari_table import format_vimshottari_table
from rules.pratyantar_dasha import format_pratyantar_dasha
from rules.gochar import derive_gochar_report
from astro_engine import get_current_gochar


# ---------------- IMPORT PLANET DATABASES ----------------
# (Assuming all imports are correct in your local setup)
from rules.planets.sun.sun_en import SUN_DB as SUN_EN
from rules.planets.sun.sun_hi import SUN_DB as SUN_HI
from rules.planets.sun.sun_mr import SUN_DB as SUN_MR
from rules.planets.moon.moon_en import MOON_DB as MOON_EN
from rules.planets.moon.moon_hi import MOON_DB as MOON_HI
from rules.planets.moon.moon_mr import MOON_DB as MOON_MR
from rules.planets.mars.mars_en import MARS_DB as MARS_EN
from rules.planets.mars.mars_hi import MARS_DB as MARS_HI
from rules.planets.mars.mars_mr import MARS_DB as MARS_MR
from rules.planets.mercury.mercury_en import MERCURY_DB as MERCURY_EN
from rules.planets.mercury.mercury_hi import MERCURY_DB as MERCURY_HI
from rules.planets.mercury.mercury_mr import MERCURY_DB as MERCURY_MR
from rules.planets.jupiter.jupiter_en import JUPITER_DB as JUPITER_EN
from rules.planets.jupiter.jupiter_hi import JUPITER_DB as JUPITER_HI
from rules.planets.jupiter.jupiter_mr import JUPITER_DB as JUPITER_MR
from rules.planets.venus.venus_en import VENUS_DB as VENUS_EN
from rules.planets.venus.venus_hi import VENUS_DB as VENUS_HI
from rules.planets.venus.venus_mr import VENUS_DB as VENUS_MR
from rules.planets.saturn.saturn_en import SATURN_DB as SATURN_EN
from rules.planets.saturn.saturn_hi import SATURN_DB as SATURN_HI
from rules.planets.saturn.saturn_mr import SATURN_DB as SATURN_MR
from rules.planets.rahu.rahu_en import RAHU_DB as RAHU_EN
from rules.planets.rahu.rahu_hi import RAHU_DB as RAHU_HI
from rules.planets.rahu.rahu_mr import RAHU_DB as RAHU_MR
from rules.planets.ketu.ketu_en import KETU_DB as KETU_EN
from rules.planets.ketu.ketu_hi import KETU_DB as KETU_HI
from rules.planets.ketu.ketu_mr import KETU_DB as KETU_MR


# ---------------- MASTER MAP ----------------

PLANET_DB = {
    "en": {
        "Sun": SUN_EN, "Moon": MOON_EN, "Mars": MARS_EN,
        "Mercury": MERCURY_EN, "Jupiter": JUPITER_EN,
        "Venus": VENUS_EN, "Saturn": SATURN_EN,
        "Rahu": RAHU_EN, "Ketu": KETU_EN
    },
    "hi": {
        "Sun": SUN_HI, "Moon": MOON_HI, "Mars": MARS_HI,
        "Mercury": MERCURY_HI, "Jupiter": JUPITER_HI,
        "Venus": VENUS_HI, "Saturn": SATURN_HI,
        "Rahu": RAHU_HI, "Ketu": KETU_HI
    },
    "mr": {
        "Sun": SUN_MR, "Moon": MOON_MR, "Mars": MARS_MR,
        "Mercury": MERCURY_MR, "Jupiter": JUPITER_MR,
        "Venus": VENUS_MR, "Saturn": SATURN_MR,
        "Rahu": RAHU_MR, "Ketu": KETU_MR
    }
}


# ---------------- CORE FUNCTION ----------------

def get_planet_house_analysis(planet, house, dasha, language="en"):
    try:
        base_text = PLANET_DB.get(language, PLANET_DB["en"])[planet].get(house, "Data missing")
    except Exception:
        return "[Data missing for this planetary placement]"

    timing_text = activate_planet_result(planet, house, dasha)
    return base_text + "\n\n<b>Activation Timing</b>\n\n" + timing_text


def get_marriage_prediction(chart, dasha):
    t = derive_marriage_timeline(chart, dasha)

    text = "<b>Marriage Timeline</b>\n\n"
    if t.get("delay_phase"):
        text += f"Delay Phase: {t['delay_phase']}\n"

    # SAFE ACCESS using .get()
    start = t.get("marriage_start", "2026")
    end = t.get("marriage_end", "2028")
    stable = t.get("stability_after", "2029")

    text += (
        f"Marriage Window: {start} – {end}\n"
        f"Stability After Marriage: {stable} onwards"
    )
    return text

def get_career_prediction(chart, dasha):
    t = derive_career_timeline(chart, dasha)

    text = "<b>Career Timeline</b>\n\n"
    if t.get("career_pressure"):
        text += f"Pressure / Transition Phase: {t['career_pressure']}\n"

    # SAFE ACCESS using .get()
    start = t.get("career_rise_start", "2025")
    peak = t.get("career_peak", "2027-2029")
    stable = t.get("career_stability", "2030")

    text += (
        f"Career Rise Begins: {start}\n"
        f"Career Peak Period: {peak}\n"
        f"Long-term Stability: {stable} onwards"
    )
    return text


def get_yoga_report(chart):
    try:
        manglik = detect_manglik(chart)
        raj = detect_raj_yoga(chart)
        dhan = detect_dhan_yoga(chart)
        kaal = detect_kaal_sarp(chart)

        text = "<b>Dosha & Yoga Analysis</b>\n\n"
        text += f"Manglik Dosha: {manglik['status']}\n{manglik['description']}\n\n"
        text += f"Raj Yoga: {raj['status']}\n{raj['description']}\n\n"
        text += f"Dhan Yoga: {dhan['status']}\n{dhan['description']}\n\n"
        text += f"Kaal Sarp Yoga: {kaal['status']}\n{kaal['description']}"
        return text
    except Exception:
        return "Yoga Analysis not available due to chart data error."

def get_yearly_prediction(user, dasha):
    try:
        birth_year = int(user["DOB"].split("-")[2])
        forecast = derive_yearly_forecast(dasha, birth_year)
        text = "<b>Year-wise Life Forecast</b>\n\n"
        for f in forecast:
            text += (
                f"Year: {f.get('year')} (Age {f.get('age')})\n"
                f"Status: {f.get('status')}\n"
                f"Focus: {f.get('theme')}\n\n"
            )
        return text
    except Exception:
        return "Yearly forecast currently unavailable."

def get_20_year_prediction(user, dasha):
    try:
        birth_year = int(user["DOB"].split("-")[2])
        forecast = derive_yearly_forecast(dasha, birth_year)
        text = "<b>20-Year Life Forecast</b>\n\n"
        for f in forecast:
            text += (
                f"Year: {f.get('year')} (Age {f.get('age')})\n"
                f"Phase: {f.get('status')}\n"
                f"Life Focus: {f.get('theme')}\n\n"
            )
        return text
    except Exception:
        return "20-Year forecast unavailable."

def get_stress_growth_report(user, dasha):
    birth_year = int(user["DOB"].split("-")[2])
    table = derive_stress_growth_table(dasha, birth_year)
    text = "<b>Stress vs Growth Years</b>\n\n"
    for row in table:
        text += (
            f"Year: {row['year']} (Age {row['age']})\n"
            f"Category: {row['phase']}\n"
            f"Observation: {row['note']}\n\n"
        )
    return text

def get_career_money_report(user, chart, dasha):
    birth_year = int(user["DOB"].split("-")[2])
    table = derive_career_money_chart(chart, dasha, birth_year)
    text = "<b>Career vs Money Timeline</b>\n\n"
    for row in table:
        text += (
            f"Year: {row['year']} (Age {row['age']})\n"
            f"Career Strength: {row['career_score']}\n"
            f"Money Strength: {row['money_score']}\n"
            f"Dominance: {row['result']}\n\n"
        )
    return text

def get_confidence_report(user, chart, dasha):
    birth_year = int(user["DOB"].split("-")[2])
    table = derive_confidence_scores(chart, dasha, birth_year)
    text = "<b>Year-wise Confidence Index</b>\n\n"
    for row in table:
        text += (
            f"Year: {row['year']} (Age {row['age']})\n"
            f"Confidence Score: {row['confidence']} / 100\n\n"
        )
    return text

def get_final_summary(confidence_scores, stress_growth_table, career_timeline, marriage_timeline):
    return derive_summary_page(
        confidence_scores,
        stress_growth_table,
        career_timeline,
        marriage_timeline
    )

def get_dasha_report(dasha):
    return derive_dasha_table(dasha)

def get_full_vimshottari(user):
    start_year = int(user["DOB"].split("-")[2])
    return format_vimshottari_table(start_year)

def get_pratyantar_report(dasha):
    md = dasha.get("current_mahadasha")
    ad = dasha.get("current_antardasha")
    ad_start = dasha.get("ad_start_year")
    ad_end = dasha.get("ad_end_year")

    if not (md and ad and ad_start and ad_end):
        return "Pratyantar Dasha data is not available."

    return format_pratyantar_dasha(md_planet=md, ad_planet=ad, ad_start=ad_start, ad_end=ad_end)

def get_gochar_prediction(chart):
    try:
        transits = get_current_gochar()
        return derive_gochar_report(chart, transits)
    except Exception:
        return "Gochar report unavailable."