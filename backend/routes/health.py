from datetime import datetime, timezone
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify backend status and frontend-backend connectivity.
    Returns:
        JSON response with status, project name, version, and server timestamp.
    """
    return jsonify({
        "status": "ok",
        "service": "Privacy-Preserving Adaptive Insider Threat Detection Backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200
