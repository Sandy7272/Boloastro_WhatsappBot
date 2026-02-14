"""
Kundali Milan (Gun Milan) Engine
Complete implementation of Ashtakoota system for marriage compatibility
36 points across 8 parameters (Gunas)
"""

import logging

logger = logging.getLogger(__name__)


# =========================
# NAKSHATRA DATA
# =========================

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Varna (Caste) classification by Nakshatra
NAKSHATRA_VARNA = {
    # Brahmin (Spiritual)
    "Ashwini": "Brahmin", "Punarvasu": "Brahmin", "Hasta": "Brahmin",
    "Swati": "Brahmin", "Shravana": "Brahmin", "Revati": "Brahmin",
    
    # Kshatriya (Warrior/Ruler)
    "Bharani": "Kshatriya", "Pushya": "Kshatriya", "Uttara Phalguni": "Kshatriya",
    "Vishakha": "Kshatriya", "Uttara Ashadha": "Kshatriya", "Uttara Bhadrapada": "Kshatriya",
    
    # Vaishya (Merchant)
    "Krittika": "Vaishya", "Ashlesha": "Vaishya", "Chitra": "Vaishya",
    "Jyeshtha": "Vaishya", "Dhanishta": "Vaishya", "Purva Bhadrapada": "Vaishya",
    
    # Shudra (Laborer)
    "Rohini": "Shudra", "Mrigashira": "Shudra", "Ardra": "Shudra",
    "Magha": "Shudra", "Purva Phalguni": "Shudra", "Anuradha": "Shudra",
    "Mula": "Shudra", "Purva Ashadha": "Shudra", "Shatabhisha": "Shudra"
}

# Vashya (Magnetic control) by Nakshatra
NAKSHATRA_VASHYA = {
    # Chatushpada (Quadruped)
    "Ashwini": "Chatushpada", "Bharani": "Chatushpada", "Purva Phalguni": "Chatushpada",
    "Uttara Phalguni": "Chatushpada", "Purva Ashadha": "Chatushpada", "Uttara Ashadha": "Chatushpada",
    "Shravana": "Chatushpada",
    
    # Manava (Human)
    "Rohini": "Manava", "Mrigashira": "Manava", "Ardra": "Manava",
    "Punarvasu": "Manava", "Hasta": "Manava", "Purva Bhadrapada": "Manava",
    "Uttara Bhadrapada": "Manava",
    
    # Jalachara (Aquatic)
    "Krittika": "Jalachara", "Pushya": "Jalachara", "Ashlesha": "Jalachara",
    "Magha": "Jalachara", "Revati": "Jalachara",
    
    # Keeta (Insect)
    "Chitra": "Keeta", "Vishakha": "Keeta", "Jyeshtha": "Keeta",
    
    # Vanachara (Wild)
    "Swati": "Vanachara", "Anuradha": "Vanachara", "Mula": "Vanachara",
    "Dhanishta": "Vanachara", "Shatabhisha": "Vanachara"
}

# Yoni (Animal nature) by Nakshatra
NAKSHATRA_YONI = {
    "Ashwini": ("Horse", "Male"), "Shatabhisha": ("Horse", "Female"),
    "Bharani": ("Elephant", "Male"), "Revati": ("Elephant", "Female"),
    "Pushya": ("Goat", "Male"), "Krittika": ("Goat", "Female"),
    "Rohini": ("Serpent", "Male"), "Mrigashira": ("Serpent", "Female"),
    "Ashlesha": ("Cat", "Male"), "Punarvasu": ("Cat", "Female"),
    "Magha": ("Rat", "Male"), "Purva Phalguni": ("Rat", "Female"),
    "Uttara Phalguni": ("Cow", "Male"), "Uttara Bhadrapada": ("Cow", "Female"),
    "Hasta": ("Buffalo", "Male"), "Swati": ("Buffalo", "Female"),
    "Chitra": ("Tiger", "Male"), "Vishakha": ("Tiger", "Female"),
    "Anuradha": ("Deer", "Male"), "Jyeshtha": ("Deer", "Female"),
    "Mula": ("Dog", "Male"), "Ardra": ("Dog", "Female"),
    "Purva Ashadha": ("Monkey", "Male"), "Shravana": ("Monkey", "Female"),
    "Uttara Ashadha": ("Mongoose", "Male"), "Purva Bhadrapada": ("Mongoose", "Female"),
    "Dhanishta": ("Lion", "Male")
}

# Gana (Temperament) by Nakshatra
NAKSHATRA_GANA = {
    # Deva Gana (Divine/God-like)
    "Ashwini": "Deva", "Mrigashira": "Deva", "Punarvasu": "Deva",
    "Pushya": "Deva", "Hasta": "Deva", "Swati": "Deva",
    "Anuradha": "Deva", "Shravana": "Deva", "Revati": "Deva",
    
    # Manushya Gana (Human)
    "Bharani": "Manushya", "Rohini": "Manushya", "Ardra": "Manushya",
    "Purva Phalguni": "Manushya", "Uttara Phalguni": "Manushya", "Purva Ashadha": "Manushya",
    "Uttara Ashadha": "Manushya", "Purva Bhadrapada": "Manushya", "Uttara Bhadrapada": "Manushya",
    
    # Rakshasa Gana (Demon/Aggressive)
    "Krittika": "Rakshasa", "Ashlesha": "Rakshasa", "Magha": "Rakshasa",
    "Chitra": "Rakshasa", "Vishakha": "Rakshasa", "Jyeshtha": "Rakshasa",
    "Mula": "Rakshasa", "Dhanishta": "Rakshasa", "Shatabhisha": "Rakshasa"
}

# Nadi (Pulse/Health) by Nakshatra
NAKSHATRA_NADI = {
    # Adi Nadi
    "Ashwini": "Adi", "Ardra": "Adi", "Punarvasu": "Adi",
    "Uttara Phalguni": "Adi", "Hasta": "Adi", "Jyeshtha": "Adi",
    "Mula": "Adi", "Shatabhisha": "Adi", "Purva Bhadrapada": "Adi",
    
    # Madhya Nadi
    "Bharani": "Madhya", "Mrigashira": "Madhya", "Pushya": "Madhya",
    "Purva Phalguni": "Madhya", "Chitra": "Madhya", "Anuradha": "Madhya",
    "Purva Ashadha": "Madhya", "Dhanishta": "Madhya", "Uttara Bhadrapada": "Madhya",
    
    # Antya Nadi
    "Krittika": "Antya", "Rohini": "Antya", "Ashlesha": "Antya",
    "Magha": "Antya", "Swati": "Antya", "Vishakha": "Antya",
    "Uttara Ashadha": "Antya", "Shravana": "Antya", "Revati": "Antya"
}


# =========================
# 1. VARNA KUTA (1 point)
# =========================

def calculate_varna_kuta(boy_nakshatra, girl_nakshatra):
    """
    Varna represents spiritual development
    1 point if boy's varna >= girl's varna
    """
    
    varna_order = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}
    
    boy_varna = NAKSHATRA_VARNA.get(boy_nakshatra, "Shudra")
    girl_varna = NAKSHATRA_VARNA.get(girl_nakshatra, "Shudra")
    
    if varna_order[boy_varna] >= varna_order[girl_varna]:
        return 1
    
    return 0


# =========================
# 2. VASHYA KUTA (2 points)
# =========================

def calculate_vashya_kuta(boy_nakshatra, girl_nakshatra):
    """
    Vashya represents magnetic control and attraction
    2 points if compatible, 0 if not
    """
    
    boy_vashya = NAKSHATRA_VASHYA.get(boy_nakshatra, "Manava")
    girl_vashya = NAKSHATRA_VASHYA.get(girl_nakshatra, "Manava")
    
    # Full compatibility
    if boy_vashya == girl_vashya:
        return 2
    
    # Partial compatibility rules
    compatible_pairs = [
        ("Chatushpada", "Manava"),
        ("Manava", "Chatushpada"),
        ("Jalachara", "Manava"),
        ("Manava", "Jalachara")
    ]
    
    if (boy_vashya, girl_vashya) in compatible_pairs:
        return 1
    
    return 0


# =========================
# 3. TARA KUTA (3 points)
# =========================

def calculate_tara_kuta(boy_nakshatra, girl_nakshatra):
    """
    Tara represents health and well-being
    Based on birth star counting from each other
    """
    
    try:
        boy_index = NAKSHATRAS.index(boy_nakshatra)
        girl_index = NAKSHATRAS.index(girl_nakshatra)
    except ValueError:
        return 0
    
    # Count from girl to boy
    count = ((boy_index - girl_index) % 27) + 1
    tara_from_girl = (count % 9)
    if tara_from_girl == 0:
        tara_from_girl = 9
    
    # Count from boy to girl
    count = ((girl_index - boy_index) % 27) + 1
    tara_from_boy = (count % 9)
    if tara_from_boy == 0:
        tara_from_boy = 9
    
    # Favorable taras: 3, 5, 7
    favorable = [3, 5, 7]
    
    if tara_from_girl in favorable and tara_from_boy in favorable:
        return 3
    elif tara_from_girl in favorable or tara_from_boy in favorable:
        return 1.5
    
    return 0


# =========================
# 4. YONI KUTA (4 points)
# =========================

def calculate_yoni_kuta(boy_nakshatra, girl_nakshatra):
    """
    Yoni represents sexual compatibility and intimacy
    Based on animal nature
    """
    
    boy_yoni = NAKSHATRA_YONI.get(boy_nakshatra, ("Horse", "Male"))
    girl_yoni = NAKSHATRA_YONI.get(girl_nakshatra, ("Horse", "Female"))
    
    boy_animal = boy_yoni[0]
    girl_animal = girl_yoni[0]
    
    # Perfect match - same animal
    if boy_animal == girl_animal:
        return 4
    
    # Friendly animals
    friendly = {
        "Horse": ["Horse", "Elephant"],
        "Elephant": ["Horse", "Goat"],
        "Goat": ["Elephant", "Cow"],
        "Serpent": ["Cat"],
        "Cat": ["Rat", "Serpent"],
        "Rat": ["Cat"],
        "Cow": ["Goat", "Buffalo"],
        "Buffalo": ["Cow"],
        "Tiger": ["Deer"],
        "Deer": ["Tiger", "Monkey"],
        "Dog": ["Monkey"],
        "Monkey": ["Dog", "Deer"],
        "Mongoose": ["Lion"],
        "Lion": ["Mongoose"]
    }
    
    if girl_animal in friendly.get(boy_animal, []):
        return 3
    
    # Neutral
    return 2


# =========================
# 5. GRAHA MAITRI KUTA (5 points)
# =========================

def calculate_graha_maitri(boy_moon_sign, girl_moon_sign):
    """
    Graha Maitri represents mental compatibility
    Based on moon sign lords' friendship
    """
    
    # Planetary friendship
    friends = {
        "Mars": ["Sun", "Moon", "Jupiter"],
        "Sun": ["Moon", "Mars", "Jupiter"],
        "Moon": ["Sun", "Mercury"],
        "Mercury": ["Sun", "Venus"],
        "Jupiter": ["Sun", "Moon", "Mars"],
        "Venus": ["Mercury", "Saturn"],
        "Saturn": ["Mercury", "Venus"]
    }
    
    # Sign lords
    sign_lords = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    
    boy_lord = sign_lords.get(boy_moon_sign, "Moon")
    girl_lord = sign_lords.get(girl_moon_sign, "Moon")
    
    # Same lord
    if boy_lord == girl_lord:
        return 5
    
    # Friends
    if girl_lord in friends.get(boy_lord, []) and boy_lord in friends.get(girl_lord, []):
        return 4
    
    # One-way friendship
    if girl_lord in friends.get(boy_lord, []) or boy_lord in friends.get(girl_lord, []):
        return 3
    
    # Neutral
    return 2.5


# =========================
# 6. GANA KUTA (6 points)
# =========================

def calculate_gana_kuta(boy_nakshatra, girl_nakshatra):
    """
    Gana represents temperament and nature
    """
    
    boy_gana = NAKSHATRA_GANA.get(boy_nakshatra, "Manushya")
    girl_gana = NAKSHATRA_GANA.get(girl_nakshatra, "Manushya")
    
    # Same gana
    if boy_gana == girl_gana:
        return 6
    
    # Compatible combinations
    if boy_gana == "Deva" and girl_gana == "Manushya":
        return 5
    if boy_gana == "Manushya" and girl_gana == "Deva":
        return 6
    if boy_gana == "Manushya" and girl_gana == "Rakshasa":
        return 0
    if boy_gana == "Rakshasa" and girl_gana == "Manushya":
        return 1
    
    # Deva-Rakshasa (worst)
    return 0


# =========================
# 7. BHAKOOT KUTA (7 points)
# =========================

def calculate_bhakoot_kuta(boy_moon_sign, girl_moon_sign):
    """
    Bhakoot represents prosperity and family welfare
    Based on sign positions
    """
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    try:
        boy_pos = signs.index(boy_moon_sign)
        girl_pos = signs.index(girl_moon_sign)
    except ValueError:
        return 0
    
    diff = abs(boy_pos - girl_pos)
    
    # Favorable positions: 2, 3, 4, 5, 7, 9
    favorable = [1, 2, 3, 4, 6, 8]  # (diff+1 because of indexing)
    
    if diff in favorable:
        return 7
    
    # Dwi-Dwadasha (2-12) - worst
    if diff == 1 or diff == 11:
        return 0
    
    # Shadashtak (6-8)
    if diff == 5 or diff == 7:
        return 0
    
    return 3.5


# =========================
# 8. NADI KUTA (8 points)
# =========================

def calculate_nadi_kuta(boy_nakshatra, girl_nakshatra):
    """
    Nadi represents health and progeny
    MOST IMPORTANT - 8 points
    """
    
    boy_nadi = NAKSHATRA_NADI.get(boy_nakshatra, "Madhya")
    girl_nadi = NAKSHATRA_NADI.get(girl_nakshatra, "Madhya")
    
    # Different Nadi - excellent
    if boy_nadi != girl_nadi:
        return 8
    
    # Same Nadi - very bad (health issues, no progeny)
    return 0


# =========================
# MAIN GUN MILAN CALCULATION
# =========================

def calculate_gun_milan(boy_kundali, girl_kundali):
    """
    Calculate complete Gun Milan (Ashtakoota)
    
    Args:
        boy_kundali: Boy's kundali data with nakshatra, moon_sign
        girl_kundali: Girl's kundali data with nakshatra, moon_sign
    
    Returns:
        dict: Detailed Milan results
    """
    
    try:
        boy_nakshatra = boy_kundali.get("nakshatra", "")
        girl_nakshatra = girl_kundali.get("nakshatra", "")
        
        boy_moon_sign = boy_kundali.get("moon_sign", "")
        girl_moon_sign = girl_kundali.get("moon_sign", "")
        
        # Calculate each Kuta
        scores = {
            "Varna": {
                "obtained": calculate_varna_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 1,
                "description": "Spiritual compatibility & ego"
            },
            "Vashya": {
                "obtained": calculate_vashya_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 2,
                "description": "Mutual attraction & control"
            },
            "Tara": {
                "obtained": calculate_tara_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 3,
                "description": "Health & longevity"
            },
            "Yoni": {
                "obtained": calculate_yoni_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 4,
                "description": "Sexual compatibility & intimacy"
            },
            "Graha Maitri": {
                "obtained": calculate_graha_maitri(boy_moon_sign, girl_moon_sign),
                "maximum": 5,
                "description": "Mental compatibility & understanding"
            },
            "Gana": {
                "obtained": calculate_gana_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 6,
                "description": "Temperament & nature"
            },
            "Bhakoot": {
                "obtained": calculate_bhakoot_kuta(boy_moon_sign, girl_moon_sign),
                "maximum": 7,
                "description": "Love & family welfare"
            },
            "Nadi": {
                "obtained": calculate_nadi_kuta(boy_nakshatra, girl_nakshatra),
                "maximum": 8,
                "description": "Health & progeny (CRITICAL)"
            }
        }
        
        # Calculate total
        total_obtained = sum(score["obtained"] for score in scores.values())
        total_maximum = 36
        
        # Percentage
        percentage = (total_obtained / total_maximum) * 100
        
        # Rating
        if total_obtained >= 28:
            rating = "Excellent"
            recommendation = "Highly Compatible - Excellent Match"
        elif total_obtained >= 24:
            rating = "Very Good"
            recommendation = "Very Compatible - Good for Marriage"
        elif total_obtained >= 18:
            rating = "Good"
            recommendation = "Compatible - Marriage Can Proceed"
        elif total_obtained >= 14:
            rating = "Average"
            recommendation = "Moderate Compatibility - Consult Astrologer"
        else:
            rating = "Poor"
            recommendation = "Low Compatibility - Not Recommended"
        
        # Check critical issues
        critical_issues = []
        
        if scores["Nadi"]["obtained"] == 0:
            critical_issues.append("⚠️ Same Nadi - Health & progeny concerns (can be nullified in some cases)")
        
        if scores["Bhakoot"]["obtained"] == 0:
            critical_issues.append("⚠️ Bhakoot Dosha - Financial & family issues")
        
        if scores["Gana"]["obtained"] == 0:
            critical_issues.append("⚠️ Gana Dosha - Temperament mismatch")
        
        # Positive points
        positive_points = []
        
        if scores["Nadi"]["obtained"] == 8:
            positive_points.append("✅ Different Nadi - Excellent for health & children")
        
        if scores["Graha Maitri"]["obtained"] >= 4:
            positive_points.append("✅ Strong mental compatibility")
        
        if scores["Yoni"]["obtained"] >= 3:
            positive_points.append("✅ Good physical compatibility")
        
        if total_obtained >= 24:
            positive_points.append("✅ Total score indicates strong compatibility")
        
        result = {
            "total_score": round(total_obtained, 1),
            "maximum_score": total_maximum,
            "percentage": round(percentage, 1),
            "rating": rating,
            "recommendation": recommendation,
            "detailed_scores": scores,
            "critical_issues": critical_issues,
            "positive_points": positive_points,
            "boy_nakshatra": boy_nakshatra,
            "girl_nakshatra": girl_nakshatra,
            "boy_moon_sign": boy_moon_sign,
            "girl_moon_sign": girl_moon_sign
        }
        
        logger.info(f"✅ Gun Milan calculated: {total_obtained}/36 ({percentage}%)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Gun Milan calculation error: {e}")
        return None


# =========================
# FORMAT MILAN REPORT
# =========================

def format_milan_report(milan_result, lang="EN"):
    """
    Format Gun Milan result as readable report
    """
    
    if not milan_result:
        return "❌ Unable to generate Milan report"
    
    translations = {
        "EN": {
            "title": "🔮 *Kundali Milan Report*",
            "compatibility": "Compatibility Score",
            "rating": "Rating",
            "recommendation": "Recommendation",
            "detailed_scores": "📊 Detailed Scores (Ashtakoota)",
            "positive": "✅ Positive Points",
            "issues": "⚠️ Points to Consider",
            "note": "Note"
        },
        "HI": {
            "title": "🔮 *कुंडली मिलान रिपोर्ट*",
            "compatibility": "अनुकूलता स्कोर",
            "rating": "रेटिंग",
            "recommendation": "सिफारिश",
            "detailed_scores": "📊 विस्तृत स्कोर (अष्टकूट)",
            "positive": "✅ सकारात्मक बिंदु",
            "issues": "⚠️ ध्यान देने योग्य बातें",
            "note": "नोट"
        },
        "MR": {
            "title": "🔮 *कुंडली जुळणी अहवाल*",
            "compatibility": "सुसंगतता गुण",
            "rating": "रेटिंग",
            "recommendation": "शिफारस",
            "detailed_scores": "📊 तपशीलवार गुण (अष्टकूट)",
            "positive": "✅ सकारात्मक मुद्दे",
            "issues": "⚠️ लक्षात घ्यावयाचे मुद्दे",
            "note": "टीप"
        }
    }
    
    t = translations.get(lang, translations["EN"])
    
    report = f"""{t["title"]}

*{milan_result["boy_nakshatra"]}* (Boy) ❤️ *{milan_result["girl_nakshatra"]}* (Girl)

━━━━━━━━━━━━━━━━━━━━━

*{t["compatibility"]}:* {milan_result["total_score"]}/{milan_result["maximum_score"]} ({milan_result["percentage"]}%)

*{t["rating"]}:* {milan_result["rating"]} {'🟢' if milan_result["percentage"] >= 70 else '🟡' if milan_result["percentage"] >= 50 else '🔴'}

*{t["recommendation"]}:* {milan_result["recommendation"]}

━━━━━━━━━━━━━━━━━━━━━

*{t["detailed_scores"]}:*

"""
    
    # Add detailed scores
    for kuta_name, kuta_data in milan_result["detailed_scores"].items():
        obtained = kuta_data["obtained"]
        maximum = kuta_data["maximum"]
        desc = kuta_data["description"]
        
        bar = "█" * int(obtained) + "░" * int(maximum - obtained)
        
        report += f"*{kuta_name}:* {obtained}/{maximum} {bar}\n_{desc}_\n\n"
    
    # Add positive points
    if milan_result["positive_points"]:
        report += f"\n*{t['positive']}:*\n"
        for point in milan_result["positive_points"]:
            report += f"{point}\n"
    
    # Add critical issues
    if milan_result["critical_issues"]:
        report += f"\n*{t['issues']}:*\n"
        for issue in milan_result["critical_issues"]:
            report += f"{issue}\n"
    
    report += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n_{t['note']}: This is a traditional Vedic astrology compatibility analysis. Consult a qualified astrologer for detailed guidance._"
    
    return report