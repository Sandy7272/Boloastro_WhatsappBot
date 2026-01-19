# config.py
# All important settings

import os
from dotenv import load_dotenv
load_dotenv() 
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

OPENAI_KEY = "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"
PROKERALA_ID = "4e81c5bf-f6d9-44c4-b5d7-a62a823c849c"
PROKERALA_SECRET = "Ur8YaL1D8tc7cy7Fjji5UrhvqCKisB9U18O4IYUC"

BOT_NAME = "BoloAstro"
QUESTION_COST = 20
REPORT_COST = 200
RECHARGE_AMOUNT = 50
DEFAULT_LANG = "en"
