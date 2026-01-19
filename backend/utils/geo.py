import requests

def geocode(city):
    url = f"https://nominatim.openstreetmap.org/search"
    r = requests.get(url, params={
        "q": city,
        "format": "json"
    })

    data = r.json()
    if not data:
        return None,None

    return data[0]["lat"], data[0]["lon"]
