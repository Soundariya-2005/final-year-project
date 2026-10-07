"""
Flask REST API routes for Adaptive User Profiling.
Provides endpoints to calculate baselines and deviations with configurable alpha.
"""

import os
from flask import Blueprint, jsonify, request
import pandas as pd
from ml.adaptive_profile import (
    calculate_adaptive_profile,
    get_user_profile_summary,
    DEFAULT_ALPHA,
    BEHAVIORAL_FEATURES,
    get_default_alpha_from_settings,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

def get_sample_csv_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "sample_data.csv")


@profile_bp.route("/adaptive", methods=["POST", "GET"])
def adaptive_profile_endpoint():
    """
    POST/GET /api/profile/adaptive
    Calculates adaptive EWMA baselines and behavioral deviations.
    Supports customizable alpha (default 0.15).
    """
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        alpha = float(payload.get("alpha", get_default_alpha_from_settings()))
        user_id = payload.get("user_id")
        limit = min(int(payload.get("limit", 25)), 100)
        offset = max(int(payload.get("offset", 0)), 0)
    else:
        alpha = float(request.args.get("alpha", get_default_alpha_from_settings()))
        user_id = request.args.get("user_id")
        limit = min(int(request.args.get("limit", 25)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)

    sample_csv = get_sample_csv_path()
    if not os.path.exists(sample_csv):
        from data.sample_data import generate_sample_data
        generate_sample_data(output_path=sample_csv)

    try:
        profile_df = calculate_adaptive_profile(sample_csv, alpha=alpha)

        # Single user progression demonstration if user_id specified or default demo
        demo_user = user_id or "USR-1001"
        try:
            demo_summary = get_user_profile_summary(profile_df, demo_user)
        except Exception:
            demo_summary = None

        # Filter by user if requested
        filtered_df = profile_df
        if user_id:
            filtered_df = profile_df[profile_df["pseudonymous_user_id"] == user_id]

        total_records = len(filtered_df)
        sliced_df = filtered_df.iloc[offset : offset + limit]

        return jsonify({
            "status": "success",
            "message": "Adaptive user profile calculated successfully",
            "alpha_used": alpha,
            "formula": "baseline(t) = (1 - alpha) * baseline(t-1) + alpha * x(t)",
            "behavioral_features": BEHAVIORAL_FEATURES,
            "total_users": int(profile_df["pseudonymous_user_id"].nunique()),
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "records": sliced_df.to_dict(orient="records"),
            "demo_summary": demo_summary,
            "unique_users": sorted(profile_df["pseudonymous_user_id"].unique().tolist()),
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@profile_bp.route("/user/<user_id>", methods=["GET"])
def get_single_user_profile(user_id: str):
    """
    GET /api/profile/user/<user_id>?alpha=0.15
    Returns step-by-step chronological baseline progression for a specific user.
    """
    alpha = float(request.args.get("alpha", get_default_alpha_from_settings()))
    sample_csv = get_sample_csv_path()

    try:
        profile_df = calculate_adaptive_profile(sample_csv, alpha=alpha)
        summary = get_user_profile_summary(profile_df, user_id)
        return jsonify({
            "status": "success",
            "alpha": alpha,
            "user_summary": summary,
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 404
