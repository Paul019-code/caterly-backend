# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # ENHANCED: Require environment variables in production
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    # Add validation for required security keys
    if not SECRET_KEY or not JWT_SECRET_KEY:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY and JWT_SECRET_KEY must be set in production")
        else:
            # Fallback for development only
            SECRET_KEY = SECRET_KEY or "dev-secret-key-change-in-production"
            JWT_SECRET_KEY = JWT_SECRET_KEY or "dev-jwt-secret-change-in-production"

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///caterly.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT expiration times
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # File upload configuration
    UPLOAD_FOLDER = 'app/static/uploads/menu_items'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Security headers (for production)
    if os.environ.get("FLASK_ENV") == "production":
        # Force HTTPS in production
        PREFERRED_URL_SCHEME = 'https'