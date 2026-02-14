"""
Enterprise-Grade Configuration Management
"""

from typing import Optional, List
import os
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "BoloAstro"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    DATABASE_URL: str = "sqlite:///bot.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 0
    REDIS_QUEUE_DB: int = 1
    REDIS_SESSION_DB: int = 2
    REDIS_MAX_CONNECTIONS: int = 50

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_TIME_LIMIT: int = 300
    CELERY_TASK_SOFT_TIME_LIMIT: int = 240

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_CURRENCY: str = "INR"
    PAYMENT_LINK_EXPIRY_MINUTES: int = 60
    PAYMENT_RETRY_DELAY_MINUTES: int = 60
    MAX_PAYMENT_RETRY_ATTEMPTS: int = 3

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # =========================
    # PROKERALA
    # =========================
    PROKERALA_CLIENT_SECRET: str = ""
    PROKERALA_CLIENT_ID: str = ""
    PROKERALA_API_KEY: str = ""
    PROKERALA_MODE: str = "sandbox"  # ADD THIS LINE
    PROKERALA_TIMEOUT_SECONDS: int = 10
    PROKERALA_MAX_RETRIES: int = 3

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 500
    OPENAI_TEMPERATURE: float = 0.7

    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    SESSION_TIMEOUT_MINUTES: int = 30
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    KUNDALI_PRICE: int = 200
    QNA_PRICE: int = 99
    MILAN_PRICE: int = 199
    QNA_PACK_SIZE: int = 4

    S3_BUCKET: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "ap-south-1"
    S3_ENDPOINT: Optional[str] = None

    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    DATADOG_API_KEY: Optional[str] = None
    DATADOG_APP_KEY: Optional[str] = None

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    ENABLE_ANALYTICS: bool = True
    ENABLE_REVENUE_TRACKING: bool = True
    ENABLE_PAYMENT_RETRY: bool = True
    ENABLE_UPSELL: bool = True
    ENABLE_ABANDONED_CART_RECOVERY: bool = True

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"
    
    @property
    def DB_URL(self) -> str:
        return self.DATABASE_URL
    
    @property
    def WEBHOOK_SECRET(self) -> str:
        return self.RAZORPAY_WEBHOOK_SECRET
    
    @property
    def ENV(self) -> str:
        return self.ENVIRONMENT


# OUTSIDE THE CLASS!
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
Config = settings

__all__ = ['Settings', 'settings', 'Config', 'get_settings']