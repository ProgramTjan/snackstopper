import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///snackstopper.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:dev@example.com")

    DEFAULT_REMINDER_TIME = os.getenv("DEFAULT_REMINDER_TIME", "16:50")
    DEFAULT_AVERAGE_AMOUNT = float(os.getenv("DEFAULT_AVERAGE_AMOUNT", "7.50"))
