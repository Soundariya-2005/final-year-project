"""
Flask Application Entry Point for Privacy-Preserving Adaptive Insider Threat Detection.
"""

import os
import sys
from flask import Flask, jsonify

# Add backend directory to sys.path if running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config_by_name
from database import db, init_db
import models  # Register SQLAlchemy models
from routes.health import health_bp
from routes.database_routes import db_bp
from routes.sample_data_routes import sample_bp
from routes.privacy_routes import privacy_bp
from routes.feature_routes import feature_bp
from routes.profile_routes import profile_bp
from routes.analysis_routes import analysis_bp

def create_app(config_name=None):
    """Application factory for the Flask app."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize SQLAlchemy with the Flask application
    init_db(app)

    # Optional CORS support if flask_cors is available
    try:
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    except ImportError:
        pass

    # Register blueprints
    # health_bp defines /health and /api/health
    app.register_blueprint(health_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(sample_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(feature_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analysis_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error", "status": 500}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"[*] Starting Insider Threat Detection Flask API on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
