import os

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "supersecret-jwt-key")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
SUPPORTED_LANGUAGES = ["sv"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@localhost")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", ADMIN_EMAIL)
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8010")
