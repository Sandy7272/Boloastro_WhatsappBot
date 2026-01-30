import requests
import logging
from config import Config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.prokerala.com/v2/astrology/kundli"


def get_prokerala_data(dob, time, latitude, longitude, ayanamsa=1):
    """
    Fetch kundali data from Prokerala Astrology API.

    IMPORTANT:
    - This function expects latitude & longitude ONLY
    - City name should NEVER be passed here
    """

    # -------------------------------
    # Prepare datetime (ISO format)
    # -------------------------------
    # dob: DD-MM-YYYY
    # time: HH:MM AM/PM

    from datetime import datetime
    import pytz

    local_tz = pytz.timezone("Asia/Kolkata")

    dt = datetime.strptime(
        f"{dob} {time}",
        "%d-%m-%Y %I:%M %p"
    )

    dt = local_tz.localize(dt)
    # SANDBOX LIMITATION
    if Config.ENV == "DEV":
        dt = dt.replace(month=1, day=1)

    iso_datetime = dt.isoformat()

    # -------------------------------
    # Request
    # -------------------------------
    params = {
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": iso_datetime,
        "chart_type": "rasi"
    }

    headers = {
        "Authorization": f"Bearer {Config.PROKERALA_ACCESS_TOKEN}"
    }

    logger.info(
        f"Prokerala request → lat={latitude}, lon={longitude}, dt={iso_datetime}"
    )

    response = requests.get(
        BASE_URL,
        params=params,
        headers=headers,
        timeout=15
    )

    if response.status_code != 200:
        logger.error(
            f"Prokerala API error {response.status_code}: {response.text}"
        )
        response.raise_for_status()

    data = response.json()

    # -------------------------------
    # Normalize minimal structure
    # -------------------------------
    try:
        chart = data["data"]

        return {
            "lagna": chart.get("ascendant", {}).get("sign"),
            "moon_sign": chart.get("moon", {}).get("sign"),
            "sun_sign": chart.get("sun", {}).get("sign"),
            "current_dasha": chart.get("dasha", {}).get("current", {}).get("planet"),
            "planets": [
                p.get("name") for p in chart.get("planets", [])
            ],
            "raw": chart
        }

    except Exception:
        logger.exception("Failed to parse Prokerala response")
        return data
