import re
import requests
import logging
from datetime import datetime
from backend.config import Config

logger = logging.getLogger(__name__)


def get_access_token():
    """Get access token from Prokerala API"""
    try:
        logger.info("🔄 Generating new Prokerala access token...")
        url = "https://api.prokerala.com/token"
        
        payload = {
            "client_id": Config.PROKERALA_CLIENT_ID,
            "client_secret": Config.PROKERALA_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            logger.info("✅ Prokerala token generated")
            return token
        else:
            logger.error(f"❌ Failed to get token: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error getting token: {e}")
        return None


def fix_datetime_for_sandbox(datetime_str: str) -> str:
    """
    Fix datetime for Prokerala sandbox - only accepts Jan 1st
    """
    is_sandbox = (
        'test' in str(Config.PROKERALA_CLIENT_ID).lower() or
        'sandbox' in str(Config.PROKERALA_CLIENT_ID).lower() or
        'demo' in str(Config.PROKERALA_CLIENT_ID).lower()
    )
    
    if is_sandbox:
        match = re.match(r'(\d{4})-\d{2}-\d{2}(T.+)', datetime_str)
        if match:
            year = match.group(1)
            time_part = match.group(2)
            fixed = f"{year}-01-01{time_part}"
            logger.warning(f"⚠️ Sandbox mode: Using Jan 1st instead of original date")
            return fixed
    
    return datetime_str


def combine_datetime(dob: str, time_str: str) -> str:
    """
    Combine date and time into ISO datetime format
    
    Args:
        dob: Date in DD-MM-YYYY format (e.g., "15-08-1990")
        time_str: Time in HH:MM AM/PM format (e.g., "09:30 AM")
    
    Returns:
        ISO datetime string (e.g., "1990-08-15T09:30:00+05:30")
    """
    try:
        # Parse date (DD-MM-YYYY)
        day, month, year = dob.split('-')
        
        # Parse time (HH:MM AM/PM)
        time_str = time_str.strip().upper()
        
        # Handle 12-hour format
        if 'AM' in time_str or 'PM' in time_str:
            time_part = time_str.replace('AM', '').replace('PM', '').strip()
            hours, minutes = time_part.split(':')
            hours = int(hours)
            minutes = int(minutes)
            
            # Convert to 24-hour format
            if 'PM' in time_str and hours != 12:
                hours += 12
            elif 'AM' in time_str and hours == 12:
                hours = 0
        else:
            # Already 24-hour format
            hours, minutes = map(int, time_str.split(':'))
        
        # Create ISO format: YYYY-MM-DDTHH:MM:SS+05:30
        iso_datetime = f"{year}-{month}-{day}T{hours:02d}:{minutes:02d}:00+05:30"
        
        return iso_datetime
    
    except Exception as e:
        logger.error(f"❌ Error combining datetime: {e}")
        logger.error(f"   dob={dob}, time_str={time_str}")
        return None


def get_kundali_data(datetime_str, lat, lon):
    """
    Get kundali data from Prokerala API
    
    Args:
        datetime_str: ISO datetime (e.g., "1990-08-15T09:30:00+05:30")
        lat: Latitude
        lon: Longitude
    
    Returns:
        dict: Kundali data from Prokerala
    """
    logger.info(f"🌌 Prokerala request -> {datetime_str}")
    
    # FIX: Handle sandbox mode
    datetime_str = fix_datetime_for_sandbox(datetime_str)
    
    try:
        token = get_access_token()
        
        if not token:
            logger.error("❌ Could not obtain access token")
            return None
        
        url = "https://api.prokerala.com/v2/astrology/kundli"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "ayanamsa": 1,
            "coordinates": f"{lat},{lon}",
            "datetime": datetime_str,
            "chart_type": "rasi"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Prokerala kundali data received")
            return response.json()
        else:
            logger.error(f"❌ Prokerala API error {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Prokerala API exception: {e}")
        return None


def get_prokerala_data(**kwargs):
    """
    Backward compatibility wrapper
    
    Accepts various parameter combinations:
    - dob + time_str + latitude + longitude
    - datetime_str + lat + lon
    """
    # Check if we have separate dob and time_str
    if 'dob' in kwargs and 'time_str' in kwargs:
        dob = kwargs['dob']
        time_str = kwargs['time_str']
        lat = kwargs.get('latitude') or kwargs.get('lat')
        lon = kwargs.get('longitude') or kwargs.get('lon')
        
        # Combine date and time
        datetime_str = combine_datetime(dob, time_str)
        
        if not datetime_str:
            return None
        
        return get_kundali_data(datetime_str, lat, lon)
    
    # Check for datetime_str directly
    elif 'datetime_str' in kwargs or 'dob' in kwargs:
        datetime_str = kwargs.get('datetime_str') or kwargs.get('dob')
        lat = kwargs.get('latitude') or kwargs.get('lat')
        lon = kwargs.get('longitude') or kwargs.get('lon')
        
        return get_kundali_data(datetime_str, lat, lon)
    
    else:
        logger.error("❌ Invalid parameters for get_prokerala_data")
        return None


__all__ = ['get_kundali_data', 'get_prokerala_data', 'get_access_token']