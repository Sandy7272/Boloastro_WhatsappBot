import os
from dotenv import load_dotenv
from google import genai

# Load .env
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("❌ GOOGLE_API_KEY NOT FOUND")
    exit()

print("✅ API KEY LOADED")

# Create client
client = genai.Client(api_key=API_KEY)

# List models
print("\n📦 AVAILABLE MODELS:")
models = client.models.list()

for m in models:
    print("-", m.name)
