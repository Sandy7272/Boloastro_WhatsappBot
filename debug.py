import os
import sys

print("--- DEBUGGING SYSTEM ---")

# 1. CHECK FOLDERS
if not os.path.exists("generated_pdfs"):
    print("❌ 'generated_pdfs' folder missing. Creating it...")
    os.makedirs("generated_pdfs")
else:
    print("✅ 'generated_pdfs' folder exists.")

# 2. CHECK FONTS
font_reg = "fonts/NotoSansDevanagari-Regular.ttf"
font_bold = "fonts/NotoSansDevanagari-Bold.ttf"

if os.path.exists(font_reg):
    print("✅ Regular Font found.")
else:
    print("❌ ERROR: 'NotoSansDevanagari-Regular.ttf' NOT found in 'fonts/' folder.")
    
if os.path.exists(font_bold):
    print("✅ Bold Font found.")
else:
    print("❌ ERROR: 'NotoSansDevanagari-Bold.ttf' NOT found in 'fonts/' folder.")

# 3. CHECK LOGIC (Rules)
try:
    from rules.rules import derive_values
    print("✅ rules.py imported successfully.")
    
    # Test Data
    chart = {"Lagna": "Aries", "LagnaLord": "Mars", "Rashi": "Leo", "RashiLord": "Sun", "Nakshatra": "Ashwini", "Pada": "1", "Gana": "Deva", "Yoni": "Ashwa", "Nadi": "Adi", "Varna": "Kshatriya"}
    planets = [{"Planet": "Mars", "House": "1"}]
    dasha = {"Current": "Jupiter", "End": 2030}
    user = {"user_id": "TestUser", "DOB": "01-01-2000", "Time": "12:00", "Place": "Mumbai"}
    
    # Run Calculation
    vals = derive_values(chart, planets, dasha, user, "en")
    
    # Check for missing keys (The #1 cause of crashes)
    required_keys = ["CAREER_DASHA", "DECISION_STYLE", "WEALTH_GOOD_PERIODS", "SPOUSE_TRAITS"]
    missing = [k for k in required_keys if k not in vals]
    
    if missing:
        print(f"❌ LOGIC ERROR: rules.py is missing these keys: {missing}")
    else:
        print("✅ Logic Engine is PERFECT. All keys present.")

except ImportError:
    print("❌ ERROR: Could not import 'rules.py'. Make sure it exists.")
except Exception as e:
    print(f"❌ LOGIC CRASH: {e}")

print("--------------------------------")