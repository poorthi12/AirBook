import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = (os.getenv("MONGO_URI") or "").strip().strip("'\"")
SECRET_KEY = os.getenv(
    "SECRET_KEY", "airbook-skybook-fixed-production-secret-key"
).strip().strip("'\"")

# Email Settings
MAIL_SERVER = (os.getenv("MAIL_SERVER") or "smtp.gmail.com").strip().strip("'\"")

# Clean port and ensure integer (Default to 465 for reliable SSL on cloud hosts)
raw_port = str(os.getenv("MAIL_PORT", "465")).strip().strip("'\"")
try:
    MAIL_PORT = int(raw_port)
except ValueError:
    MAIL_PORT = 465

# Clean credentials and remove accidental spaces/quotes
MAIL_USERNAME = (os.getenv("MAIL_USERNAME") or "").strip().strip("'\"")
MAIL_PASSWORD = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip().strip("'\"")
MAIL_DEFAULT_SENDER = (
    os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME
).strip().strip("'\"")

# SSL / TLS configuration
raw_ssl = os.getenv("MAIL_USE_SSL")
raw_tls = os.getenv("MAIL_USE_TLS")

if raw_ssl is not None:
    MAIL_USE_SSL = raw_ssl.strip().strip("'\"").lower() in {"1", "true", "yes", "on"}
else:
    MAIL_USE_SSL = (MAIL_PORT == 465)

if raw_tls is not None:
    MAIL_USE_TLS = raw_tls.strip().strip("'\"").lower() in {"1", "true", "yes", "on"}
else:
    MAIL_USE_TLS = (MAIL_PORT == 587)

# Flask-Mail will crash if BOTH SSL and TLS are True simultaneously
if MAIL_USE_SSL and MAIL_USE_TLS:
    if MAIL_PORT == 465:
        MAIL_USE_TLS = False
    else:
        MAIL_USE_SSL = False