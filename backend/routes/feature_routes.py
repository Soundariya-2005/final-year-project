"""
Flask REST API routes for User-Day Behavioral Feature Extraction.
"""

import os
from flask import Blueprint, jsonify, request, current_app
from ml.feature_engineering import (
    extract_behavior_features,
    save_features_to_mysql,
    REQUIRED_FEATURE_COLUMNS,
)

feature_bp = Blueprint("features", __name__, url_prefix="/api/features")

def get_default_sample_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "sample_data.csv")


@feature_bp.route("/extract", methods=["POST", "GET"])
def extract_features_endpoint():
    """
    POST/GET /api/features/extract
    Processes raw activity records into user-day behavioral features.
    Saves features to MySQL behavior_features table if database is reachable.
    
    Returns:
        JSON with number of users, number of records, date range, and preview.
    """
    payload = request.get_json(silent=True) or {}
    custom_records = payload.get("records")
    file_path = payload.get("file_path") or get_default_sample_path()
    sync_db = payload.get("sync_to_db", True)

    try:
        # If custom records provided, extract from them; otherwise extract from sample_data.csv
        if custom_records and isinstance(custom_records, list):
            feat_df = extract_behavior_features(custom_records)
        else:
            if not os.path.exists(file_path):
                # Ensure sample data exists
                from data.sample_data import generate_sample_data
                generate_sample_data(output_path=file_path)

            feat_df = extract_behavior_features(file_path)

        # Attempt database persistence if requested
        db_result = {"synced": False, "status": "skipped"}
        if sync_db:
            db_result = save_features_to_mysql(feat_df, app=current_app)

        preview = feat_df.head(15).to_dict(orient="records")

        return jsonify({
            "status": "success",
            "message": "User-day behavioral features extracted successfully",
            "number_of_users": int(feat_df["pseudonymous_user_id"].nunique()),
            "number_of_user_day_records": int(len(feat_df)),
            "date_range": {
                "start_date": str(feat_df["date"].min()),
                "end_date": str(feat_df["date"].max()),
                "total_days": int(feat_df["date"].nunique()),
            },
            "columns": REQUIRED_FEATURE_COLUMNS,
            "feature_dataframe_preview": preview,
            "database_sync": db_result,
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Feature extraction failed: {str(e)}",
        }), 500


@feature_bp.route("/preview", methods=["GET"])
def get_features_preview():
    """
    GET /api/features/preview
    Returns paginated extracted features with optional user filtering.
    """
    file_path = get_default_sample_path()
    if not os.path.exists(file_path):
        from data.sample_data import generate_sample_data
        generate_sample_data(output_path=file_path)

    try:
        feat_df = extract_behavior_features(file_path)

        user_filter = request.args.get("user_id")
        if user_filter:
            feat_df = feat_df[feat_df["pseudonymous_user_id"] == user_filter]

        limit = min(int(request.args.get("limit", 20)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)

        total_count = len(feat_df)
        slice_df = feat_df.iloc[offset : offset + limit]

        return jsonify({
            "status": "ok",
            "total_records": total_count,
            "limit": limit,
            "offset": offset,
            "records": slice_df.to_dict(orient="records"),
            "unique_users": sorted(feat_df["pseudonymous_user_id"].unique().tolist()),
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
