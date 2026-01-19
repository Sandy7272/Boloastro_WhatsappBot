from datetime import datetime

def derive_career_timeline(chart, dasha):
    """
    Calculates career timing safely.
    Includes ALL keys (career_peak, career_stability) to prevent crashing.
    """
    current_year = datetime.now().year
    timeline = {}

    # --- 1. SAFE DATA EXTRACTION ---
    raw_end_year = dasha.get("current_mahadasha_end_year")
    
    if raw_end_year is None:
        md_end = current_year + 5
    else:
        try:
            md_end = int(str(raw_end_year).split('-')[0][:4])
        except (ValueError, TypeError):
            md_end = current_year + 5

    # --- 2. CALCULATE TIMING ---
    timeline["career_rise_start"] = md_end - 4
    timeline["career_rise_end"] = md_end - 1
    
    # 10th House Logic
    h10 = None
    if isinstance(chart, list):
        for house in chart:
            if house.get("house") == 10:
                h10 = house
                break
    elif isinstance(chart, dict):
        h10 = chart.get(10)

    if h10 and "Sun" in str(h10):
        desc = "Strong authority and government favors indicated."
    elif h10 and "Saturn" in str(h10):
        desc = "Slow but steady growth with hard work."
    else:
        desc = "Career growth indicated as per current planetary periods."

    # --- 3. FINAL RETURN (ALL MISSING KEYS ADDED) ---
    return {
        "prediction_text": f"{desc} Peak growth expected between {timeline['career_rise_start']} and {timeline['career_rise_end']}.",
        "career_rise_start": timeline["career_rise_start"],
        "career_rise_end": timeline["career_rise_end"],
        
        # Ye keys pehle missing thi, ab add kar di hain:
        "career_peak": f"{timeline['career_rise_start']} - {timeline['career_rise_end']}",
        "career_stability": timeline["career_rise_end"] + 1,  # <--- Fixed: Added career_stability
        "favorable_years": f"{timeline['career_rise_start']}, {timeline['career_rise_end']}"
    }