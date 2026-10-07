"""
Unified Analysis Pipeline Service for Privacy-Preserving Adaptive Insider Threat Detection.

Orchestrates the complete 11-stage analysis workflow:
Stage 1:  CSV Ingestion & Validation
Stage 2:  Data Cleaning & Preprocessing
Stage 3:  Deterministic Pseudonymization & Identity Masking
Stage 4:  User-Day Behavioral Feature Engineering
Stage 5:  Adaptive Behavioral Profiling (EWMA baseline & deviation)
Stage 6:  Unsupervised Isolation Forest Anomaly Detection
Stage 7:  Accumulative Progressive Risk Engine
Stage 8:  Risk Tier Classification (LOW, MEDIUM, HIGH, CRITICAL)
Stage 9:  Game-Theoretic SHAP Explainability (TreeExplainer)
Stage 10: Persistent MySQL Storage / Run Logging
Stage 11: Sanitized API Response Packaging (Privacy-Preserving)
"""

import os
import sys
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Union, List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure backend root is on Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from privacy.pseudonymization import pseudonymize_user_id, hash_original_id
from ml.feature_engineering import extract_behavior_features, REQUIRED_FEATURE_COLUMNS
from ml.adaptive_profile import calculate_adaptive_profile, DEFAULT_ALPHA
from ml.anomaly_detection import (
    detect_anomalies,
    get_anomaly_summary,
    save_anomaly_results_to_mysql,
    BEHAVIORAL_FEATURES,
    DEFAULT_CONTAMINATION,
)
from ml.risk_engine import (
    calculate_progressive_risk,
    get_risk_summary,
    save_risk_scores_to_mysql,
    classify_risk_level,
    DEFAULT_RISK_DECAY,
    DEFAULT_RISK_GAIN,
)
from ml.explainability import (
    explain_anomalies_shap,
    get_user_explanations,
    save_explanations_to_mysql,
)

# In-memory pipeline repository cache shared across all dashboard API endpoints
pipeline_state = {
    "last_run_id": None,
    "last_run_time": None,
    "filename": "sample_data.csv",
    "parameters": {
        "alpha": DEFAULT_ALPHA,
        "contamination": DEFAULT_CONTAMINATION,
        "risk_decay": DEFAULT_RISK_DECAY,
        "risk_gain": DEFAULT_RISK_GAIN,
    },
    "features_df": None,
    "profile_df": None,
    "anomaly_df": None,
    "risk_df": None,
    "explanation_df": None,
    "explanation_summary": None,
    "model": None,
    "analysis_runs_history": [],
}


def validate_and_preprocess_csv(
    file_or_path: Union[str, io.BytesIO, io.StringIO, pd.DataFrame]
) -> pd.DataFrame:
    """
    Stage 1 & 2: Validates schema integrity, data types, and normalizes columns.
    Ensures safe handling of missing values and strips identity leaks.
    """
    if isinstance(file_or_path, pd.DataFrame):
        df = file_or_path.copy()
    elif isinstance(file_or_path, str):
        if not os.path.exists(file_or_path):
            raise FileNotFoundError(f"Input file not found at: {file_or_path}")
        df = pd.read_csv(file_or_path)
    else:
        df = pd.read_csv(file_or_path)

    if df.empty:
        raise ValueError("Uploaded dataset is empty. At least one activity record is required.")

    # Standardize column headers
    df.columns = [c.strip().lower() for c in df.columns]

    # Validate that date and user columns exist
    user_col = None
    for cand in ["user_id", "userid", "user", "employee_id", "original_id", "pseudonymous_user_id"]:
        if cand in df.columns:
            user_col = cand
            break

    if not user_col:
        raise ValueError("Dataset missing user identification column (expected 'user_id' or 'employee_id').")

    date_col = None
    for cand in ["date", "activity_date", "timestamp", "datetime"]:
        if cand in df.columns:
            date_col = cand
            break

    if not date_col:
        raise ValueError("Dataset missing date column (expected 'date' or 'activity_date').")

    # Rename to canonical user_id and date
    df = df.rename(columns={user_col: "user_id", date_col: "date"})

    # Validate date parsing
    try:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Failed to parse date column: {e}")

    # Ensure all behavioral columns exist, default to 0 if missing
    for feat in BEHAVIORAL_FEATURES:
        if feat not in df.columns:
            df[feat] = 0.0
        else:
            df[feat] = pd.to_numeric(df[feat], errors="coerce").fillna(0.0)

    # Sort strictly chronologically per user
    df = df.sort_values(by=["user_id", "date"]).reset_index(drop=True)
    return df


def execute_analysis_pipeline(
    data_input: Union[str, io.BytesIO, io.StringIO, pd.DataFrame],
    alpha: float = DEFAULT_ALPHA,
    contamination: float = DEFAULT_CONTAMINATION,
    risk_decay: float = DEFAULT_RISK_DECAY,
    risk_gain: float = DEFAULT_RISK_GAIN,
    filename: str = "dataset.csv",
    sync_to_db: bool = True,
    app = None,
) -> Dict[str, Any]:
    """
    Executes the full end-to-end pipeline through all 11 stages.
    """
    run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    # --- Stage 1 & 2: Validation & Preprocessing ---
    raw_df = validate_and_preprocess_csv(data_input)

    # --- Stage 3: Pseudonymization ---
    # Apply deterministic pseudonymization to user IDs if they haven't been pseudonymized yet
    pseudonymized_users = []
    for uid in raw_df["user_id"].astype(str):
        if str(uid).startswith("USR-"):
            pseudonymized_users.append(str(uid))
        else:
            pseudonymized_users.append(pseudonymize_user_id(str(uid)))
    raw_df["pseudonymous_user_id"] = pseudonymized_users

    # Drop original user_id column permanently from downstream frames
    if "user_id" in raw_df.columns:
        raw_df = raw_df.drop(columns=["user_id"])

    # --- Stage 4: Feature Engineering ---
    features_df = extract_behavior_features(raw_df)

    # --- Stage 5: Adaptive Profiling ---
    profile_df = calculate_adaptive_profile(features_df, alpha=alpha)

    # --- Stage 6: Isolation Forest Anomaly Detection ---
    anomaly_df, model = detect_anomalies(features_df, contamination=contamination)
    anomaly_summary = get_anomaly_summary(anomaly_df)

    # --- Stage 7 & 8: Progressive Risk Engine & Risk Classification ---
    risk_df = calculate_progressive_risk(anomaly_df, decay=risk_decay, gain=risk_gain)
    risk_summary = get_risk_summary(risk_df)

    # --- Stage 9: SHAP Explainability ---
    explanation_df, explanation_summary = explain_anomalies_shap(anomaly_df, model=model)

    # --- Cache State for fast dashboard querying ---
    pipeline_state["last_run_id"] = run_id
    pipeline_state["last_run_time"] = datetime.now(timezone.utc).isoformat()
    pipeline_state["filename"] = filename
    pipeline_state["parameters"] = {
        "alpha": alpha,
        "contamination": contamination,
        "risk_decay": risk_decay,
        "risk_gain": risk_gain,
    }
    pipeline_state["features_df"] = features_df
    pipeline_state["profile_df"] = profile_df
    pipeline_state["anomaly_df"] = anomaly_df
    pipeline_state["risk_df"] = risk_df
    pipeline_state["explanation_df"] = explanation_df
    pipeline_state["explanation_summary"] = explanation_summary
    pipeline_state["model"] = model

    # --- Stage 10: Persistent MySQL Storage ---
    db_sync = {
        "connected": False,
        "records_synced": 0,
        "status": "offline_cached",
    }

    if sync_to_db:
        try:
            from database import db, test_connection
            import models

            if app is None:
                from app import create_app
                app = create_app()

            with app.app_context():
                conn = test_connection()
                if conn["connected"]:
                    db_sync["connected"] = True
                    # 1. Sync Pseudonymous Users
                    unique_users = features_df["pseudonymous_user_id"].unique()
                    for u in unique_users:
                        existing = models.User.query.filter_by(pseudonymous_id=u).first()
                        if not existing:
                            dummy_hash = hash_original_id(u)
                            new_u = models.User(pseudonymous_id=u, original_id_hash=dummy_hash)
                            db.session.add(new_u)
                    db.session.commit()

                    # 2. Sync Anomalies, Risk Scores, and Explanations
                    save_anomaly_results_to_mysql(anomaly_df, app=app)
                    save_risk_scores_to_mysql(risk_df, app=app)
                    save_explanations_to_mysql(explanation_df, app=app)

                    # 3. Save Analysis Run
                    run_rec = models.AnalysisRun(
                        filename=filename,
                        record_count=len(features_df),
                        user_count=int(features_df["pseudonymous_user_id"].nunique()),
                        parameters=json.dumps(pipeline_state["parameters"]),
                    )
                    db.session.add(run_rec)
                    db.session.commit()
                    db_sync["status"] = "synced"
                    db_sync["records_synced"] = len(features_df)
                else:
                    db_sync["status"] = "mysql_offline"
        except Exception as e:
            db_sync["status"] = f"db_sync_error: {str(e)}"

    # Record in history list
    run_entry = {
        "id": run_id,
        "filename": filename,
        "record_count": len(features_df),
        "user_count": int(features_df["pseudonymous_user_id"].nunique()),
        "total_anomalies": int(anomaly_summary["anomaly_count"]),
        "high_risk_users": int(risk_summary.get("latest_snapshot_distribution", {}).get("HIGH", 0)),
        "critical_risk_users": int(risk_summary.get("latest_snapshot_distribution", {}).get("CRITICAL", 0)),
        "date_range": {
            "start": str(features_df["date"].min()),
            "end": str(features_df["date"].max()),
        },
        "parameters": pipeline_state["parameters"],
        "created_at": pipeline_state["last_run_time"],
        "database_sync": db_sync,
    }
    pipeline_state["analysis_runs_history"].insert(0, run_entry)

    # --- Stage 11: API Response Packaging ---
    return {
        "analysis_status": "completed",
        "analysis_run_id": run_id,
        "number_of_records": len(features_df),
        "number_of_users": int(features_df["pseudonymous_user_id"].nunique()),
        "number_of_anomalies": int(anomaly_summary["anomaly_count"]),
        "high_risk_user_count": int(risk_summary.get("latest_snapshot_distribution", {}).get("HIGH", 0)),
        "critical_risk_user_count": int(risk_summary.get("latest_snapshot_distribution", {}).get("CRITICAL", 0)),
        "date_range": {
            "start": str(features_df["date"].min()),
            "end": str(features_df["date"].max()),
        },
        "parameters": pipeline_state["parameters"],
        "pipeline_stages": [
            "CSV Upload",
            "Validation",
            "Preprocessing",
            "Pseudonymization",
            "Feature Engineering",
            "Adaptive Profiling",
            "Isolation Forest",
            "Progressive Risk",
            "Risk Classification",
            "SHAP Explanation",
            "MySQL Storage",
            "API Response",
        ],
        "database_sync": db_sync,
    }


def get_pipeline_state() -> Dict[str, Any]:
    """Retrieves current in-memory pipeline state or initializes from sample data."""
    if pipeline_state["features_df"] is None:
        sample_path = os.path.join(backend_dir, "data", "sample_data.csv")
        if not os.path.exists(sample_path):
            from data.sample_data import generate_sample_data
            generate_sample_data(output_path=sample_path)
        execute_analysis_pipeline(sample_path, filename="sample_data.csv")
    return pipeline_state
