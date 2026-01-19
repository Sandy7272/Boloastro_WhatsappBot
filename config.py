import os
from dotenv import load_dotenv

# .env file load karne ki koshish karega
load_dotenv()

class Config:
    # --- 1. FLASK SECURITY ---
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-unsafe-key")

    # --- 2. DATABASE (SQLite for Local) ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///astrology_bot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- 3. REDIS (Task Queue) ---
    # Localhost ke liye yahi rahne dein
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # --- 4. TWILIO CREDENTIALS (CRITICAL FIX) ---
    # Ye wahi naam hain jo tasks.py dhoond raha tha.
    # Agar aapke paas .env file nahi hai, to 'os.getenv' hata kar
    # seedha apni strings paste kar dein.
    
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") 
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    # --- 5. AWS S3 (Optional for Local) ---
    # Abhi local mode me hum file laptop par save kar rahe hain,
    # isliye inki zarurat nahi hai, par future ke liye rakh sakte hain.
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # --- 6. RAZORPAY (Payments) ---
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "my_hidden_secret")