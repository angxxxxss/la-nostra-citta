import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Config:
    ENVIRONMENT = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-before-deploying")
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    REDIS_URL = os.getenv("REDIS_URL", "")
    RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR", str(ROOT / "instance" / "flask_sessions"))
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "20")) * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(ROOT / "instance" / "uploads"))
    DATABASE_HOST = os.getenv("DATABASE_HOST", "").strip()
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "3306"))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "la_nostra_citta")
    DATABASE_USER = os.getenv("DATABASE_USER", "").strip()
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_SSL_CA = os.getenv("DATABASE_SSL_CA", "").strip()
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_TEST_NAME = os.getenv("DATABASE_TEST_NAME", "la_nostra_citta_test")
    WTF_CSRF_TIME_LIMIT = 60 * 60
    JSON_AS_ASCII = False
