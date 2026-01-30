import dateparser
import re

def parse_user_input(text):
    """
    Smartly extracts DOB, Time, and Place from user text.
    Expects format: "Date, Time, Place" (flexible date/time formats).
    """
    try:
        # 1. Split by comma (we still need commas to separate City from Date)
        parts = [x.strip() for x in text.split(",")]
        
        # We need at least 3 parts: Date, Time, Place
        if len(parts) < 3:
            return None

        # 2. Smart Date Parsing
        raw_date = parts[0]
        parsed_date = dateparser.parse(raw_date, settings={'DATE_ORDER': 'DMY'})
        
        if not parsed_date:
            return None
        
        # Convert to strict format for API: DD-MM-YYYY
        final_dob = parsed_date.strftime("%d-%m-%Y")

        # 3. Smart Time Parsing
        raw_time = parts[1]
        # dateparser works for time too
        parsed_time = dateparser.parse(raw_time)
        
        if not parsed_time:
            return None
            
        # Convert to strict format for API: HH:MM
        final_time = parsed_time.strftime("%H:%M")

        # 4. Place (Just take the string)
        final_place = parts[2].title() # Capitalize first letters

        return {
            "DOB": final_dob,
            "Time": final_time,
            "Place": final_place
        }

    except Exception as e:
        print(f"Parsing Error: {e}")
        return None