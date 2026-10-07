"""
Routes package for the Privacy-Preserving Insider Threat Detection backend.
"""
from .health import health_bp
from .database_routes import db_bp
from .sample_data_routes import sample_bp
from .privacy_routes import privacy_bp
from .feature_routes import feature_bp
from .profile_routes import profile_bp
from .analysis_routes import analysis_bp

__all__ = [
    "health_bp",
    "db_bp",
    "sample_bp",
    "privacy_bp",
    "feature_bp",
    "profile_bp",
    "analysis_bp",
]
