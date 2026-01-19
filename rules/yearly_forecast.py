# rules/yearly_forecast.py

def derive_yearly_forecast(dasha, birth_year, years=20):
    forecast = []
    
    # Get the real calculation log from new astro_engine
    dasha_log = dasha.get("full_dasha_log", [])
    
    if not dasha_log:
        # Fallback if log is missing
        return [{"year": birth_year+i, "age": i, "status": "General", "theme": "Mixed Results"} for i in range(years)]

    for i in range(years):
        current_year = birth_year + i
        
        # Find which Dasha is active in this year
        active_lord = "Unknown"
        for d in dasha_log:
            if d["start"] <= current_year < d["end"]:
                active_lord = d["planet"]
                break
        
        # Theme logic
        if active_lord in ["Jupiter", "Venus", "Mercury"]:
            status = "Growth Phase"
            theme = f"Influence of {active_lord} brings learning and expansion."
        elif active_lord in ["Saturn", "Rahu", "Ketu"]:
            status = "Transformation Phase"
            theme = f"Influence of {active_lord} brings discipline and changes."
        elif active_lord in ["Sun", "Mars"]:
            status = "Action Phase"
            theme = f"High energy period driven by {active_lord}."
        else:
            status = "Stability Phase"
            theme = f"Period ruled by {active_lord}."

        forecast.append({
            "year": current_year,
            "age": i,
            "status": status,
            "theme": theme
        })
        
    return forecast