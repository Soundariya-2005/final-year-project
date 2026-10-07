"""
Flask routes for generating and inspecting the demonstration sample activity-log dataset.
"""

import os
from flask import Blueprint, jsonify, request
import pandas as pd
from data.sample_data import generate_sample_data

sample_bp = Blueprint("sample_data", __name__, url_prefix="/api")

def get_csv_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "sample_data.csv")


@sample_bp.route("/generate-sample", methods=["POST", "GET"])
def handle_generate_sample():
    """
    POST /api/generate-sample:
    Generates synthetic activity-log records and saves to backend/data/sample_data.csv.
    Returns:
        JSON with number of records, number of users, date range, and file status.
    """
    csv_file = get_csv_path()

    # If GET and file exists, return the existing file's summary
    if request.method == "GET" and os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            preview_rows = df.head(10).to_dict(orient="records")
            return jsonify({
                "status": "success",
                "message": "Sample data retrieved successfully",
                "number_of_records": int(len(df)),
                "number_of_users": int(df["user_id"].nunique()),
                "date_range": {
                    "start_date": str(df["date"].min()),
                    "end_date": str(df["date"].max()),
                    "total_days": int(df["date"].nunique())
                },
                "file_location": "backend/data/sample_data.csv",
                "columns": list(df.columns),
                "sample_preview": preview_rows
            }), 200
        except Exception as e:
            # If reading failed, regenerate below
            pass

    # Extract optional parameters for custom generation
    data = request.get_json(silent=True) or {}
    num_users = int(data.get("num_users", 40))
    num_days = int(data.get("num_days", 45))
    seed = int(data.get("seed", 42))

    try:
        df = generate_sample_data(
            num_users=num_users,
            num_days=num_days,
            output_path=csv_file,
            seed=seed
        )

        preview_rows = df.head(10).to_dict(orient="records")

        return jsonify({
            "status": "success",
            "message": "Sample activity log data generated successfully",
            "number_of_records": int(len(df)),
            "number_of_users": int(df["user_id"].nunique()),
            "date_range": {
                "start_date": str(df["date"].min()),
                "end_date": str(df["date"].max()),
                "total_days": int(df["date"].nunique())
            },
            "file_location": "backend/data/sample_data.csv",
            "columns": list(df.columns),
            "sample_preview": preview_rows
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate sample data: {str(e)}",
            "file_location": "backend/data/sample_data.csv"
        }), 500


@sample_bp.route("/sample-data/preview", methods=["GET"])
def sample_preview():
    """
    GET /api/sample-data/preview:
    Returns sample records with optional limit, offset, or user filter.
    """
    csv_file = get_csv_path()
    if not os.path.exists(csv_file):
        # Auto-generate if missing
        generate_sample_data(output_path=csv_file)

    try:
        df = pd.read_csv(csv_file)
        user_filter = request.args.get("user_id")
        if user_filter:
            df = df[df["user_id"] == user_filter]

        limit = min(int(request.args.get("limit", 25)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)

        total_matching = len(df)
        sliced_df = df.iloc[offset : offset + limit]

        return jsonify({
            "status": "ok",
            "total_records": total_matching,
            "limit": limit,
            "offset": offset,
            "records": sliced_df.to_dict(orient="records"),
            "unique_users": sorted(df["user_id"].unique().tolist())
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
