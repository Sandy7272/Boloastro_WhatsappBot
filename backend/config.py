import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # ---------------- APP ----------------

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]

    ENV = os.getenv("ENV", "DEV")

    # PRICING
    KUNDALI_PRICE = int(os.getenv("KUNDALI_PRICE", 200))
    QNA_PRICE = int(os.getenv("QNA_PRICE", 99))

    # ---------------- DATABASE ----------------

    DB_URL = os.getenv(
        "DB_URL",
        os.getenv("DATABASE_URL", "sqlite:///bot.db")
    )

    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------------- REDIS ----------------

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ---------------- TWILIO ----------------

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv(
        "TWILIO_WHATSAPP_NUMBER",
        "whatsapp:+14155238886"
    )

    # ---------------- RAZORPAY ----------------

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    # ---------------- APIS ----------------

    PROKERALA_CLIENT_ID = os.getenv("PROKERALA_CLIENT_ID")
    PROKERALA_CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET")
    PROKERALA_ACCESS_TOKEN = os.getenv("PROKERALA_ACCESS_TOKEN")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
