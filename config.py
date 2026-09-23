import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv(
    "SECRET_KEY", "airbook-skybook-fixed-production-secret-key"
)

# Email Settings
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_USE_SSL = (
    str(os.getenv("MAIL_USE_SSL", "True" if MAIL_PORT == 465 else "False"))
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)
MAIL_USE_TLS = (
    str(os.getenv("MAIL_USE_TLS", "False" if MAIL_PORT == 465 else "True"))
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

MAIL_USERNAME = (os.getenv("MAIL_USERNAME") or "").strip()
# Remove accidental spaces that Google App Passwords often have
MAIL_PASSWORD = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME