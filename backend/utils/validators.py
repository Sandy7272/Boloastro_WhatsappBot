"""
Super User-Friendly Input Validators
Accepts multiple date/time formats, natural language parsing
Smart validation with helpful error messages
"""

import re
from datetime import datetime
import dateparser  # For smart date parsing


# =========================
# SMART DATE VALIDATION (MULTIPLE FORMATS)
# =========================

def valid_dob(dob_str):
    """
    Validate date of birth - accepts MANY formats!
    
    Supported formats:
    - 12-01-2000
    - 12/01/2000
    - 12.01.2000
    - 12 01 2000
    - 12-Jan-2000
    - 12 January 2000
    - January 12, 2000
    - 2000-01-12
    
    Args:
        dob_str: Date string to validate
    
    Returns:
        tuple: (is_valid, error_message_dict, normalized_date)
    """
    
    if not dob_str or len(dob_str.strip()) < 6:
        return False, {
            "EN": "❌ Date of birth cannot be empty.",
            "HI": "❌ जन्म तिथि खाली नहीं हो सकती।",
            "MR": "❌ जन्म तारीख रिकामी असू शकत नाही.",
            "TA": "❌ பிறந்த தேதி காலியாக இருக்க முடியாது.",
            "TE": "❌ పుట్టిన తేదీ ఖాళీగా ఉండకూడదు.",
            "BN": "❌ জন্ম তারিখ খালি থাকতে পারবে না।"
        }, None
    
    # Clean input
    dob_str = dob_str.strip()
    
    # Try to parse with dateparser (handles multiple formats)
    try:
        parsed_date = dateparser.parse(
            dob_str,
            settings={
                'STRICT_PARSING': False,
                'PREFER_DATES_FROM': 'past',
                'DATE_ORDER': 'DMY'  # Day-Month-Year (Indian format)
            }
        )
        
        if not parsed_date:
            # Fallback: try manual parsing
            parsed_date = parse_date_manual(dob_str)
        
        if not parsed_date:
            return False, {
                "EN": f"❌ Could not understand date: '{dob_str}'\n\n✅ Try formats like:\n• 12-01-2000\n• 12/01/2000\n• 12 Jan 2000\n• 12 January 2000",
                "HI": f"❌ तारीख समझ नहीं आई: '{dob_str}'\n\n✅ इन प्रारूपों का प्रयास करें:\n• 12-01-2000\n• 12/01/2000\n• 12 जन 2000",
                "MR": f"❌ तारीख समजली नाही: '{dob_str}'\n\n✅ या स्वरूपात प्रयत्न करा:\n• 12-01-2000\n• 12/01/2000\n• 12 जान 2000",
                "TA": f"❌ தேதி புரியவில்லை: '{dob_str}'\n\n✅ இந்த வடிவங்களை முயற்சிக்கவும்:\n• 12-01-2000\n• 12/01/2000",
                "TE": f"❌ తేదీ అర్థం కాలేదు: '{dob_str}'\n\n✅ ఈ ఆకృతులను ప్రయత్నించండి:\n• 12-01-2000\n• 12/01/2000",
                "BN": f"❌ তারিখ বুঝতে পারিনি: '{dob_str}'\n\n✅ এই ফর্ম্যাট চেষ্টা করুন:\n• 12-01-2000\n• 12/01/2000"
            }, None
        
        # Validate year range
        current_year = datetime.now().year
        if not (1900 <= parsed_date.year <= current_year):
            return False, {
                "EN": f"❌ Year must be between 1900-{current_year}. You entered: {parsed_date.year}",
                "HI": f"❌ वर्ष 1900-{current_year} के बीच होना चाहिए। आपने लिखा: {parsed_date.year}",
                "MR": f"❌ वर्ष 1900-{current_year} दरम्यान असावे. तुम्ही लिहिले: {parsed_date.year}",
                "TA": f"❌ ஆண்டு 1900-{current_year} இடையில் இருக்க வேண்டும். நீங்கள் உள்ளிட்டது: {parsed_date.year}",
                "TE": f"❌ సంవత్సరం 1900-{current_year} మధ్య ఉండాలి. మీరు నమోదు చేసింది: {parsed_date.year}",
                "BN": f"❌ বছর 1900-{current_year} এর মধ্যে হতে হবে। আপনি লিখেছেন: {parsed_date.year}"
            }, None
        
        # Check if date is in future
        if parsed_date > datetime.now():
            return False, {
                "EN": "❌ Birth date cannot be in the future!",
                "HI": "❌ जन्म तिथि भविष्य में नहीं हो सकती!",
                "MR": "❌ जन्म तारीख भविष्यात असू शकत नाही!",
                "TA": "❌ பிறந்த தேதி எதிர்காலத்தில் இருக்க முடியாது!",
                "TE": "❌ పుట్టిన తేదీ భవిష్యత్తులో ఉండకూడదు!",
                "BN": "❌ জন্ম তারিখ ভবিষ্যতে হতে পারবে না!"
            }, None
        
        # Normalize to DD-MM-YYYY format
        normalized = parsed_date.strftime("%d-%m-%Y")
        
        return True, None, normalized
        
    except Exception as e:
        return False, {
            "EN": f"❌ Invalid date format. Try: 12-01-2000 or 12 Jan 2000",
            "HI": f"❌ अमान्य तारीख। प्रयास करें: 12-01-2000 या 12 जन 2000",
            "MR": f"❌ अवैध तारीख. प्रयत्न करा: 12-01-2000 किंवा 12 जान 2000",
            "TA": f"❌ தவறான தேதி. முயற்சி: 12-01-2000 அல்லது 12 ஜன 2000",
            "TE": f"❌ చెల్లని తేదీ. ప్రయత్నం: 12-01-2000 లేదా 12 జన 2000",
            "BN": f"❌ অবৈধ তারিখ। চেষ্টা করুন: 12-01-2000 বা 12 জান 2000"
        }, None


def parse_date_manual(dob_str):
    """
    Manual date parsing as fallback
    """
    
    # Common separators: -, /, ., space
    date_str = re.sub(r'[,]', '', dob_str)  # Remove commas
    
    # Try different formats
    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %m %Y",
        "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%d %m %y",
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y",
        "%B %d, %Y", "%b %d, %Y",
        "%d-%m-%Y", "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None


# =========================
# SMART TIME VALIDATION (MULTIPLE FORMATS)
# =========================

def valid_time(time_str):
    """
    Validate time - accepts MANY formats!
    
    Supported formats:
    - 9:30 AM
    - 09:30 AM
    - 9:30am (no space)
    - 0930 (military)
    - 21:30 (24-hour)
    - 9.30 AM
    - 930 AM
    
    Args:
        time_str: Time string to validate
    
    Returns:
        tuple: (is_valid, error_message_dict, normalized_time)
    """
    
    if not time_str or len(time_str.strip()) < 3:
        return False, {
            "EN": "❌ Birth time cannot be empty.",
            "HI": "❌ जन्म समय खाली नहीं हो सकता।",
            "MR": "❌ जन्म वेळ रिकामी असू शकत नाही.",
            "TA": "❌ பிறந்த நேரம் காலியாக இருக்க முடியாது.",
            "TE": "❌ పుట్టిన సమయం ఖాళీగా ఉండకూడదు.",
            "BN": "❌ জন্ম সময় খালি থাকতে পারবে না।"
        }, None
    
    time_str = time_str.strip().upper()
    
    try:
        parsed_time = parse_time_smart(time_str)
        
        if not parsed_time:
            return False, {
                "EN": "❌ Could not understand time.\n\n✅ Try formats like:\n• 9:30 AM\n• 09:30 AM\n• 21:30\n• 0930",
                "HI": "❌ समय समझ नहीं आया।\n\n✅ इन प्रारूपों का प्रयास करें:\n• 9:30 AM\n• 09:30 AM\n• 21:30",
                "MR": "❌ वेळ समजली नाही.\n\n✅ या स्वरूपात प्रयत्न करा:\n• 9:30 AM\n• 09:30 AM\n• 21:30",
                "TA": "❌ நேரம் புரியவில்லை.\n\n✅ இந்த வடிவங்களை முயற்சிக்கவும்:\n• 9:30 AM\n• 09:30 AM\n• 21:30",
                "TE": "❌ సమయం అర్థం కాలేదు.\n\n✅ ఈ ఆకృతులను ప్రయత్నించండి:\n• 9:30 AM\n• 09:30 AM\n• 21:30",
                "BN": "❌ সময় বুঝতে পারিনি.\n\n✅ এই ফর্ম্যাট চেষ্টা করুন:\n• 9:30 AM\n• 09:30 AM\n• 21:30"
            }, None
        
        # Normalize to HH:MM AM/PM format
        normalized = parsed_time.strftime("%I:%M %p")
        
        return True, None, normalized
        
    except Exception as e:
        return False, {
            "EN": "❌ Invalid time format. Try: 09:30 AM",
            "HI": "❌ अमान्य समय। प्रयास करें: 09:30 AM",
            "MR": "❌ अवैध वेळ. प्रयत्न करा: 09:30 AM",
            "TA": "❌ தவறான நேரம். முயற்சி: 09:30 AM",
            "TE": "❌ చెల్లని సమయం. ప్రయత్నం: 09:30 AM",
            "BN": "❌ অবৈধ সময়। চেষ্টা করুন: 09:30 AM"
        }, None


def parse_time_smart(time_str):
    """
    Smart time parsing
    """
    
    # Remove extra spaces
    time_str = re.sub(r'\s+', ' ', time_str.strip())
    
    # Replace dots with colons
    time_str = time_str.replace('.', ':')
    
    # Add colon if missing (e.g., 930 AM -> 9:30 AM)
    if ':' not in time_str and ('AM' in time_str or 'PM' in time_str):
        # Extract digits and AM/PM
        digits = re.findall(r'\d+', time_str)[0]
        am_pm = 'AM' if 'AM' in time_str else 'PM'
        
        if len(digits) == 3:  # e.g., 930
            time_str = f"{digits[0]}:{digits[1:]} {am_pm}"
        elif len(digits) == 4:  # e.g., 0930
            time_str = f"{digits[:2]}:{digits[2:]} {am_pm}"
    
    # Try different time formats
    formats = [
        "%I:%M %p",      # 9:30 AM
        "%I:%M%p",       # 9:30AM (no space)
        "%H:%M",         # 21:30 (24-hour)
        "%H%M",          # 2130 (military)
        "%I %p",         # 9 AM (no minutes)
        "%I:%M %p",      # 09:30 AM
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except:
            continue
    
    return None


# =========================
# PLACE VALIDATION
# =========================

def validate_place(place_str):
    """
    Validate place name
    """
    
    if not place_str or len(place_str.strip()) < 2:
        return False
    
    # Remove special characters except spaces, hyphens, apostrophes
    cleaned = re.sub(r'[^a-zA-Z\s\-\'\u0900-\u097F\u0980-\u09FF\u0A80-\u0AFF\u0B00-\u0B7F\u0C00-\u0C7F]', '', place_str)
    
    if len(cleaned.strip()) < 2:
        return False
    
    return True


# =========================
# NAME VALIDATION
# =========================

def validate_name(name_str):
    """
    Validate person name
    """
    
    if not name_str or len(name_str.strip()) < 2:
        return False, None
    
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', name_str.strip())
    
    # Allow letters, spaces, and common name characters in multiple scripts
    if len(cleaned) < 2:
        return False, None
    
    return True, cleaned


# =========================
# PHONE NUMBER VALIDATION
# =========================

def validate_phone(phone_str):
    """
    Validate WhatsApp phone number format
    """
    
    pattern = r'^whatsapp:\+\d{10,15}$'
    return bool(re.match(pattern, phone_str))


# =========================
# MESSAGE SANITIZATION
# =========================

def sanitize_message(msg_str):
    """
    Sanitize user message
    """
    
    if not msg_str:
        return ""
    
    # Remove null bytes
    cleaned = msg_str.replace('\x00', '')
    
    # Remove control characters except newline and tab
    cleaned = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned)
    
    # Limit length
    max_length = 1000
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


# =========================
# GENDER VALIDATION (for Milan)
# =========================

def validate_gender(gender_str):
    """
    Validate gender input
    """
    
    gender_lower = gender_str.lower().strip()
    
    male_keywords = ['male', 'boy', 'man', 'groom', 'लड़का', 'पुरुष', 'वर', 'मुलगा', 'ஆண்', 'అబ్బాయి', 'ছেলে']
    female_keywords = ['female', 'girl', 'woman', 'bride', 'लड़की', 'स्त्री', 'वधू', 'मुलगी', 'பெண்', 'అమ్మాయి', 'মেয়ে']
    
    if any(keyword in gender_lower for keyword in male_keywords):
        return True, "MALE"
    
    if any(keyword in gender_lower for keyword in female_keywords):
        return True, "FEMALE"
    
    return False, None


# =========================
# AMOUNT VALIDATION
# =========================

def validate_amount(amount):
    """
    Validate payment amount
    """
    
    try:
        amount_float = float(amount)
        
        if 1 <= amount_float <= 100000:
            return True
        
        return False
        
    except (ValueError, TypeError):
        return False