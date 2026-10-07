import os
from urllib.parse import quote_plus
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    """Base application configuration for Flask and MySQL / SQLAlchemy."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False

    # --------------------------------------------------------------------------
    # MySQL Database Configuration via Environment Variables
    # No credentials are hard-coded in the source code.
    # --------------------------------------------------------------------------
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "insider_threat_db")
    DB_USER = os.getenv("DB_USER", "threat_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # Direct database connection URL (if provided)
    # e.g., mysql+pymysql://username:password@hostname:3306/dbname
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    if DATABASE_URL:
        # Standardize mysql:// to mysql+pymysql:// for PyMySQL driver compatibility
        if DATABASE_URL.startswith("mysql://"):
            SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Construct SQLAlchemy MySQL URL using individual parameters
        # URL-encode password if it contains special characters
        encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        if encoded_password:
            user_pass = f"{DB_USER}:{encoded_password}"
        else:
            user_pass = f"{DB_USER}"
            
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{user_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # SQLAlchemy Engine Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_timeout": 5,
        "connect_args": {
            "connect_timeout": 5,
        },
    }
    JSON_SORT_KEYS = False

    @classmethod
    def get_db_info(cls):
        """Returns safe, non-sensitive database connection details for diagnostics."""
        return {
            "dialect": "mysql",
            "driver": "pymysql",
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "database": cls.DB_NAME,
            "user": cls.DB_USER,
            "has_password": bool(cls.DB_PASSWORD or "password" in cls.DATABASE_URL.lower()),
            "configured_via_url": bool(cls.DATABASE_URL),
        }


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    # In testing, preserve MySQL config unless explicitly overridden


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False


# Map environment names to configuration objects
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
