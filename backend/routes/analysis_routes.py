"""
Flask REST API routes for Insider Threat Analysis Pipeline, Dashboard Metrics,
User Threat Profiling, Risk Trends, and SHAP Explainability.
"""

import os
import json
import io
from flask import Blueprint, jsonify, request, current_app
import pandas as pd
import numpy as np

from ml.adaptive_profile import DEFAULT_ALPHA
from ml.anomaly_detection import DEFAULT_CONTAMINATION, BEHAVIORAL_FEATURES
from ml.risk_engine import DEFAULT_RISK_DECAY, DEFAULT_RISK_GAIN
from ml.explainability import get_user_explanations
from services.pipeline import (
    execute_analysis_pipeline,
    get_pipeline_state,
    pipeline_state,
)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api")


def _get_active_state():
    """Retrieves or initializes the active pipeline state."""
    return get_pipeline_state()


# -----------------------------------------------------------------------------
# 1. Pipeline Execution Endpoint: POST /api/analyze
# -----------------------------------------------------------------------------
@analysis_bp.route("/analyze", methods=["POST"])
def analyze_pipeline():
    """
    POST /api/analyze
    Executes complete 11-stage pipeline:
    CSV Upload -> Validation -> Preprocessing -> Pseudonymization ->
    Feature Engineering -> Adaptive Profiling -> Isolation Forest ->
    Progressive Risk -> Risk Classification -> SHAP Explanation ->
    MySQL Storage -> API Response
    """
    payload = request.get_json(silent=True) or {}
    form_data = request.form or {}

    alpha = float(form_data.get("alpha") or payload.get("alpha") or DEFAULT_ALPHA)
    contamination = float(form_data.get("contamination") or payload.get("contamination") or DEFAULT_CONTAMINATION)
    risk_decay = float(form_data.get("risk_decay") or payload.get("risk_decay") or DEFAULT_RISK_DECAY)
    risk_gain = float(form_data.get("risk_gain") or payload.get("risk_gain") or DEFAULT_RISK_GAIN)

    filename = "sample_data.csv"
    data_input = None

    # Check for uploaded file
    if "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            filename = uploaded_file.filename
            data_input = io.StringIO(uploaded_file.read().decode("utf-8", errors="replace"))

    # Fallback to local sample dataset
    if data_input is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_input = os.path.join(base_dir, "data", "sample_data.csv")
        filename = "sample_data.csv"

    try:
        result = execute_analysis_pipeline(
            data_input=data_input,
            alpha=alpha,
            contamination=contamination,
            risk_decay=risk_decay,
            risk_gain=risk_gain,
            filename=filename,
            sync_to_db=True,
            app=current_app,
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "analysis_status": "error",
            "message": str(e),
        }), 400


# -----------------------------------------------------------------------------
# 2. Dashboard Summary Endpoint: GET /api/dashboard-summary
# -----------------------------------------------------------------------------
@analysis_bp.route("/dashboard-summary", methods=["GET"])
def get_dashboard_summary():
    """
    GET /api/dashboard-summary
    Returns summary statistics for the executive dashboard:
    - Total Users
    - Activity Records
    - High Risk Users
    - Critical Risk Users
    - Total Anomalies
    """
    state = _get_active_state()
    features_df = state["features_df"]
    risk_df = state["risk_df"]
    anomaly_df = state["anomaly_df"]
    expl_summary = state["explanation_summary"]

    total_users = int(features_df["pseudonymous_user_id"].nunique())
    total_records = len(features_df)
    total_anomalies = int(anomaly_df["anomaly_flag"].sum())

    # Calculate user latest risk level
    user_latest_risks = {}
    for uid, group in risk_df.groupby("pseudonymous_user_id"):
        latest = group.sort_values("date").iloc[-1]
        user_latest_risks[uid] = latest["risk_level"]

    level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for lvl in user_latest_risks.values():
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    high_risk_users = level_counts.get("HIGH", 0)
    critical_risk_users = level_counts.get("CRITICAL", 0)

    # Date range
    date_min = str(features_df["date"].min())
    date_max = str(features_df["date"].max())

    # Daily risk score trend (average across organization)
    daily_trend = (
        risk_df.groupby("date")
        .agg(
            avg_risk=("risk_score", "mean"),
            max_risk=("risk_score", "max"),
            anomalies=("anomaly_flag", "sum"),
        )
        .reset_index()
    )
    daily_trend["avg_risk"] = daily_trend["avg_risk"].round(2)
    daily_trend["max_risk"] = daily_trend["max_risk"].round(2)

    return jsonify({
        "status": "success",
        "total_users": total_users,
        "activity_records": total_records,
        "high_risk_users": high_risk_users,
        "critical_risk_users": critical_risk_users,
        "total_anomalies": total_anomalies,
        "risk_level_distribution": level_counts,
        "date_range": {"start": date_min, "end": date_max},
        "daily_trend": daily_trend.to_dict(orient="records"),
        "top_contributing_factors": expl_summary.get("global_feature_importance", []) if expl_summary else [],
        "last_run_id": state["last_run_id"],
        "last_run_time": state["last_run_time"],
        "parameters": state["parameters"],
    }), 200


# -----------------------------------------------------------------------------
# 3. Users List Endpoint: GET /api/users
# -----------------------------------------------------------------------------
@analysis_bp.route("/users", methods=["GET"])
def get_users_list():
    """
    GET /api/users
    Returns all pseudonymous users with:
    - pseudonymous ID
    - latest risk score
    - latest risk level
    - anomaly count
    - last activity date
    """
    state = _get_active_state()
    risk_df = state["risk_df"]
    features_df = state["features_df"]

    users = []
    for uid, group in risk_df.groupby("pseudonymous_user_id"):
        sorted_group = group.sort_values("date")
        latest = sorted_group.iloc[-1]
        anomaly_count = int(sorted_group["anomaly_flag"].sum())
        highest_risk = float(sorted_group["risk_score"].max())

        # Average upload and file accesses
        user_feats = features_df[features_df["pseudonymous_user_id"] == uid]
        avg_upload = round(float(user_feats["web_upload_volume"].mean()), 2)
        avg_file_access = round(float(user_feats["file_access_count"].mean()), 2)

        users.append({
            "pseudonymous_id": uid,
            "latest_risk_score": round(float(latest["risk_score"]), 2),
            "latest_risk_level": latest["risk_level"],
            "peak_risk_score": round(highest_risk, 2),
            "anomaly_count": anomaly_count,
            "last_activity_date": str(latest["date"]),
            "avg_web_upload_volume": avg_upload,
            "avg_file_access_count": avg_file_access,
        })

    # Sort descending by latest risk score, then peak risk
    users.sort(key=lambda u: (u["latest_risk_score"], u["peak_risk_score"]), reverse=True)

    # Optional filter by level
    level_filter = request.args.get("level")
    if level_filter:
        users = [u for u in users if u["latest_risk_level"].upper() == level_filter.upper()]

    return jsonify({
        "status": "success",
        "total_users": len(users),
        "users": users,
    }), 200


# -----------------------------------------------------------------------------
# 4. Single User Detail Endpoint: GET /api/users/<pseudonymous_id>
# -----------------------------------------------------------------------------
@analysis_bp.route("/users/<pseudonymous_id>", methods=["GET"])
def get_user_detail(pseudonymous_id: str):
    """
    GET /api/users/<pseudonymous_id>
    Returns comprehensive behavioral, risk, anomaly, and SHAP details for an individual user:
    - current risk
    - risk level
    - risk history
    - behavioral features
    - anomaly history
    - top SHAP factors
    """
    state = _get_active_state()
    risk_df = state["risk_df"]
    features_df = state["features_df"]
    expl_df = state["explanation_df"]

    user_risk = risk_df[risk_df["pseudonymous_user_id"] == pseudonymous_id]
    if user_risk.empty:
        return jsonify({"status": "error", "message": f"User '{pseudonymous_id}' not found."}), 404

    sorted_risk = user_risk.sort_values("date")
    latest = sorted_risk.iloc[-1]

    # Risk history
    risk_history = [
        {
            "date": str(r["date"]),
            "risk_score": round(float(r["risk_score"]), 2),
            "risk_level": r["risk_level"],
            "anomaly_flag": bool(r["anomaly_flag"]),
            "anomaly_score": round(float(r["anomaly_score"]), 4),
        }
        for _, r in sorted_risk.iterrows()
    ]

    # Behavioral features history & aggregates
    user_feats = features_df[features_df["pseudonymous_user_id"] == pseudonymous_id].sort_values("date")
    feature_means = {feat: round(float(user_feats[feat].mean()), 2) for feat in BEHAVIORAL_FEATURES}
    feature_latest = {feat: round(float(user_feats.iloc[-1][feat]), 2) for feat in BEHAVIORAL_FEATURES}

    # Anomaly history (only flagged days)
    anomalies = [r for r in risk_history if r["anomaly_flag"]]

    # Top SHAP factors
    shap_explanations = get_user_explanations(expl_df, pseudonymous_id, top_n=6)

    return jsonify({
        "status": "success",
        "pseudonymous_id": pseudonymous_id,
        "current_risk": round(float(latest["risk_score"]), 2),
        "risk_level": latest["risk_level"],
        "anomaly_count": len(anomalies),
        "last_activity_date": str(latest["date"]),
        "risk_history": risk_history,
        "behavioral_summary": {
            "averages": feature_means,
            "latest": feature_latest,
        },
        "anomaly_history": anomalies,
        "top_shap_factors": shap_explanations.get("top_features_overall", []),
        "features_increasing_anomaly": shap_explanations.get("features_increasing_anomaly", []),
        "features_decreasing_anomaly": shap_explanations.get("features_decreasing_anomaly", []),
    }), 200


# -----------------------------------------------------------------------------
# 5. User Risk Trend Endpoint: GET /api/users/<pseudonymous_id>/risk-trend
# -----------------------------------------------------------------------------
@analysis_bp.route("/users/<pseudonymous_id>/risk-trend", methods=["GET"])
def get_user_risk_trend(pseudonymous_id: str):
    """
    GET /api/users/<pseudonymous_id>/risk-trend
    Returns day-by-day risk progression with EWMA deviations.
    """
    state = _get_active_state()
    risk_df = state["risk_df"]
    profile_df = state["profile_df"]

    user_risk = risk_df[risk_df["pseudonymous_user_id"] == pseudonymous_id]
    if user_risk.empty:
        return jsonify({"status": "error", "message": f"User '{pseudonymous_id}' not found."}), 404

    sorted_risk = user_risk.sort_values("date")
    user_prof = profile_df[profile_df["pseudonymous_user_id"] == pseudonymous_id].sort_values("date") if profile_df is not None else None

    trend = []
    for _, r in sorted_risk.iterrows():
        d = str(r["date"])
        entry = {
            "date": d,
            "risk_score": round(float(r["risk_score"]), 2),
            "risk_level": r["risk_level"],
            "anomaly_flag": bool(r["anomaly_flag"]),
            "anomaly_score": round(float(r["anomaly_score"]), 4),
        }
        # Add primary deviation if profile is present
        if user_prof is not None:
            prof_row = user_prof[user_prof["date"] == d]
            if not prof_row.empty:
                entry["web_upload_deviation"] = round(float(prof_row.iloc[0].get("web_upload_volume_deviation", 0.0)), 2)
                entry["file_access_deviation"] = round(float(prof_row.iloc[0].get("file_access_count_deviation", 0.0)), 2)
                entry["after_hours_deviation"] = round(float(prof_row.iloc[0].get("after_hours_login_deviation", 0.0)), 2)
        trend.append(entry)

    return jsonify({
        "status": "success",
        "pseudonymous_id": pseudonymous_id,
        "trend": trend,
    }), 200


# -----------------------------------------------------------------------------
# 6. User Explanations Endpoint: GET /api/users/<pseudonymous_id>/explanations
# -----------------------------------------------------------------------------
@analysis_bp.route("/users/<pseudonymous_id>/explanations", methods=["GET"])
def get_user_shap_explanations(pseudonymous_id: str):
    """
    GET /api/users/<pseudonymous_id>/explanations
    Returns the top contributing behavioral features for a specific user.
    """
    state = _get_active_state()
    expl_df = state["explanation_df"]

    top_n = min(int(request.args.get("top_n", 5)), 8)
    user_expl = get_user_explanations(expl_df, pseudonymous_id, top_n=top_n)

    if user_expl.get("status") == "not_found":
        return jsonify(user_expl), 404

    return jsonify({
        "status": "success",
        "user_id": pseudonymous_id,
        "explanation": user_expl,
    }), 200


# -----------------------------------------------------------------------------
# 7. Alerts Endpoint: GET /api/alerts
# -----------------------------------------------------------------------------
@analysis_bp.route("/alerts", methods=["GET"])
def get_security_alerts():
    """
    GET /api/alerts
    Returns users with HIGH or CRITICAL risk scores requiring immediate triage.
    """
    state = _get_active_state()
    risk_df = state["risk_df"]
    features_df = state["features_df"]
    expl_df = state["explanation_df"]

    alerts = []
    for uid, group in risk_df.groupby("pseudonymous_user_id"):
        sorted_group = group.sort_values("date")
        latest = sorted_group.iloc[-1]
        lvl = latest["risk_level"]

        if lvl in ["HIGH", "CRITICAL"]:
            # Find primary contributing factor from SHAP
            user_expl = get_user_explanations(expl_df, uid, top_n=1)
            primary_factor = "Unknown"
            if user_expl.get("top_features_overall"):
                primary_factor = user_expl["top_features_overall"][0]["feature"]

            user_feats = features_df[features_df["pseudonymous_user_id"] == uid]
            anomalies_count = int(sorted_group["anomaly_flag"].sum())

            # Severity score 0-100
            score = round(float(latest["risk_score"]), 2)

            alerts.append({
                "alert_id": f"ALT-{uid}-{str(latest['date']).replace('-', '')}",
                "pseudonymous_id": uid,
                "risk_level": lvl,
                "risk_score": score,
                "anomalous_days_count": anomalies_count,
                "last_incident_date": str(latest["date"]),
                "primary_threat_vector": primary_factor,
                "recent_upload_volume_mb": round(float(user_feats.iloc[-1]["web_upload_volume"]), 2),
                "recent_sensitive_files": int(user_feats.iloc[-1]["sensitive_file_access"]),
                "recent_after_hours_logins": int(user_feats.iloc[-1]["after_hours_login"]),
                "status": "ACTIVE_INVESTIGATION" if lvl == "CRITICAL" else "REVIEW_REQUIRED",
            })

    # Sort critical first, then highest risk score
    alerts.sort(key=lambda a: (0 if a["risk_level"] == "CRITICAL" else 1, -a["risk_score"]))

    return jsonify({
        "status": "success",
        "total_alerts": len(alerts),
        "critical_count": sum(1 for a in alerts if a["risk_level"] == "CRITICAL"),
        "high_count": sum(1 for a in alerts if a["risk_level"] == "HIGH"),
        "alerts": alerts,
    }), 200


# -----------------------------------------------------------------------------
# 8. Analysis Runs Endpoint: GET /api/analysis-runs
# -----------------------------------------------------------------------------
@analysis_bp.route("/analysis-runs", methods=["GET"])
def get_analysis_runs():
    """
    GET /api/analysis-runs
    Returns historical batch analysis runs and dataset executions.
    """
    state = _get_active_state()
    runs = state.get("analysis_runs_history", [])

    return jsonify({
        "status": "success",
        "total_runs": len(runs),
        "runs": runs,
    }), 200


# -----------------------------------------------------------------------------
# 9. Settings Endpoints: GET /api/settings, POST /api/settings
# -----------------------------------------------------------------------------
@analysis_bp.route("/settings", methods=["GET", "POST"])
def handle_settings():
    """
    GET /api/settings: Returns current hyper-parameters.
    POST /api/settings: Updates system parameters and triggers pipeline re-run.
    """
    state = _get_active_state()

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        alpha = float(payload.get("alpha", state["parameters"]["alpha"]))
        contamination = float(payload.get("contamination", state["parameters"]["contamination"]))
        risk_decay = float(payload.get("risk_decay", state["parameters"]["risk_decay"]))
        risk_gain = float(payload.get("risk_gain", state["parameters"]["risk_gain"]))

        # Execute pipeline with updated parameters
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_path = os.path.join(base_dir, "data", "sample_data.csv")
        result = execute_analysis_pipeline(
            data_input=sample_path,
            alpha=alpha,
            contamination=contamination,
            risk_decay=risk_decay,
            risk_gain=risk_gain,
            filename="sample_data.csv",
            sync_to_db=True,
            app=current_app,
        )
        return jsonify({
            "status": "success",
            "message": "Settings updated and pipeline re-executed successfully.",
            "parameters": pipeline_state["parameters"],
            "analysis_result": result,
        }), 200

    return jsonify({
        "status": "success",
        "parameters": state["parameters"],
        "default_parameters": {
            "alpha": DEFAULT_ALPHA,
            "contamination": DEFAULT_CONTAMINATION,
            "risk_decay": DEFAULT_RISK_DECAY,
            "risk_gain": DEFAULT_RISK_GAIN,
        },
    }), 200
