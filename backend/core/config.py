import os

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "supersecret-jwt-key")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
SUPPORTED_LANGUAGES = ["sv"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
