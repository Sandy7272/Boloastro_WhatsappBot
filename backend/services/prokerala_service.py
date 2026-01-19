import requests, time, json, os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PROKERALA_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET")

TOKEN_URL = "https://api.prokerala.com/token"
BASE_URL  = "https://api.prokerala.com/v2"

token_cache = {
    "access_token": None,
    "expiry": 0
}


# ================= TOKEN =================

def get_access_token():

    if token_cache["access_token"] and time.time() < token_cache["expiry"]:
        return token_cache["access_token"]

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    r = requests.post(TOKEN_URL, data=data)
    res = r.json()

    token_cache["access_token"] = res["access_token"]
    token_cache["expiry"] = time.time() + res["expires_in"] - 60

    return token_cache["access_token"]


def headers():
    return {
        "Authorization": f"Bearer {get_access_token()}"
    }


# ================= GEO =================

def geocode_city(city):

    url = f"{BASE_URL}/geocoding"
    params = {"address": city}

    r = requests.get(url, headers=headers(), params=params)
    data = r.json()

    loc = data["data"][0]["geometry"]["location"]

    return loc["lat"], loc["lng"]


# ================= MAIN KUNDALI =================

def generate_kundali_once(dob, tob, place, gender):

    lat, lon = geocode_city(place)

    payload = {
        "ayanamsa": 1,  # Lahiri
        "coordinates": f"{lat},{lon}",
        "datetime": format_datetime(dob, tob)
    }

    result = {}

    result["planet_positions"] = call_api(
        "/astrology/planet-position/advanced", payload
    )

    result["kundali"] = call_api(
        "/astrology/kundali/advanced", payload
    )

    result["dasha"] = call_api(
        "/astrology/dasha-periods", payload
    )

    result["mangal"] = call_api(
        "/astrology/mangal-dosha", payload
    )

    result["panchang"] = call_api(
        "/astrology/panchang/advanced", payload
    )

    return json.dumps(result)


# ================= HELPERS =================

def call_api(endpoint, payload):

    url = BASE_URL + endpoint

    r = requests.get(url, headers=headers(), params=payload)

    if r.status_code != 200:
        raise Exception(f"Prokerala API Error: {r.text}")

    return r.json()


def format_datetime(dob, tob):

    # dob = 30/09/2000
    d,m,y = dob.split("/")
    date = f"{y}-{m}-{d}"

    return f"{date}T{tob}:00+05:30"
