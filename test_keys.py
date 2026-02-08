import requests
import os
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

CLIENT_ID = os.getenv("PROKERALA_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET")

print(f"🆔 Client ID: {CLIENT_ID}")
print(f"🔑 Client Secret: {CLIENT_SECRET}")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERROR: Keys are missing in .env file!")
    exit()

print("\n🔄 Testing keys with ProKerala...")

response = requests.post(
    "https://api.prokerala.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)

if response.status_code == 200:
    print("✅ SUCCESS! Your keys are correct.")
    print("Token:", response.json().get("access_token")[:10] + "...")
else:
    print("❌ FAILED! ProKerala rejected your keys.")
    print("Response:", response.text)