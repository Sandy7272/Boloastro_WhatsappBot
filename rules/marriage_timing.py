from datetime import datetime

def derive_marriage_timeline(chart, dasha):
    """
    Calculates marriage timing safely.
    Prevents crashing if Dasha dates are missing.
    """
    current_year = datetime.now().year
    timeline = {}

    # --- 1. SAFE DATA EXTRACTION ---
    raw_end_year = dasha.get("current_mahadasha_end_year")
    
    if raw_end_year is None:
        md_end = current_year + 5
    else:
        try:
            # Date ko clean karke sirf Year nikalo
            md_end = int(str(raw_end_year).split('-')[0][:4])
        except (ValueError, TypeError):
            md_end = current_year + 5

    # --- 2. CALCULATE TIMING ---
    timeline["marriage_start"] = md_end - 2
    timeline["marriage_end"] = md_end + 1
    
    # Logic for Description
    h7 = None
    if isinstance(chart, list):
        for house in chart:
            if house.get("house") == 7:
                h7 = house
                break
    elif isinstance(chart, dict):
        h7 = chart.get(7)

    if h7 and "Saturn" in str(h7):
        desc = "Marriage might be slightly delayed due to Saturn's influence."
    elif h7 and "Jupiter" in str(h7):
        desc = "Timely marriage with good stability indicated."
    else:
        desc = "Standard marriage timeline indicated as per dasha."

    # --- 3. FINAL RETURN (ALL KEYS ADDED) ---
    return {
        "prediction_text": f"{desc} Strong chances between {timeline['marriage_start']} and {timeline['marriage_end']}.",
        "marriage_start": timeline["marriage_start"],
        "marriage_end": timeline["marriage_end"],
        "stability_after": timeline["marriage_end"] + 1  # <--- Added Missing Key
    }