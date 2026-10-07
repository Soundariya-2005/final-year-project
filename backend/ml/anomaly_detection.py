"""
Isolation Forest Anomaly Detection Engine for Insider Threat Detection.

Uses sklearn.ensemble.IsolationForest to detect unsupervised behavioral anomalies
across 8 behavioral dimensions:
1. login_count
2. after_hours_login
3. file_access_count
4. sensitive_file_access
5. email_count
6. external_email_count
7. web_upload_volume
8. average_session_minutes

Default contamination: 0.07 (7% expected anomaly rate).
Persists results to MySQL anomaly_results table while preserving pseudonymous IDs and dates.
"""

import os
import sys
from typing import Union, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Ensure backend root is on Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ml.feature_engineering import extract_behavior_features, REQUIRED_FEATURE_COLUMNS

BEHAVIORAL_FEATURES = [
    "login_count",
    "after_hours_login",
    "file_access_count",
    "sensitive_file_access",
    "email_count",
    "external_email_count",
    "web_upload_volume",
    "average_session_minutes",
]

DEFAULT_CONTAMINATION = 0.07
MODEL_DIR = os.path.join(backend_dir, "data", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")


def get_default_contamination_from_settings() -> float:
    """Reads contamination setting from database if present, else DEFAULT_CONTAMINATION."""
    try:
        from database import db
        import models
        setting = models.Setting.query.first()
        if setting and setting.contamination is not None:
            return float(setting.contamination)
    except Exception:
        pass
    return DEFAULT_CONTAMINATION


def detect_anomalies(
    features: Union[pd.DataFrame, str, List[Dict[str, Any]]],
    contamination: float = DEFAULT_CONTAMINATION,
    save_model: bool = True,
    seed: int = 42
) -> Tuple[pd.DataFrame, IsolationForest]:
    """
    Trains an Isolation Forest model on actual behavioral features and detects anomalies.

    Args:
        features: Input feature data (DataFrame, CSV path, or list of dicts).
        contamination: Proportion of outliers in the data set (default 0.07).
        save_model: Whether to persist the trained model artifact to disk.
        seed: Random seed for reproducible results.

    Returns:
        Tuple of (results_dataframe, trained_isolation_forest_model)
        DataFrame contains:
        - pseudonymous_user_id
        - date
        - anomaly_score (continuous score 0.0 to 1.0, higher = more anomalous)
        - anomaly_flag (bool: True if anomalous, False if normal)
        - prediction (str: 'anomalous' or 'normal')
        - raw_decision_score (float from decision_function)
        - all original behavioral feature values
    """
    # 1. Validate contamination parameter
    if not (0.0 < contamination < 0.5):
        raise ValueError(f"Contamination must be in range (0.0, 0.5), received: {contamination}")

    # 2. Extract & normalize feature data
    if isinstance(features, (str, list)):
        df = extract_behavior_features(features)
    elif isinstance(features, pd.DataFrame):
        req_cols = {"pseudonymous_user_id", "date"}.union(set(BEHAVIORAL_FEATURES))
        if req_cols.issubset(set(features.columns)):
            df = features.copy()
        else:
            df = extract_behavior_features(features)
    else:
        raise TypeError("features must be a DataFrame, CSV file path, or list of dicts.")

    if df.empty:
        empty_res = pd.DataFrame(columns=[
            "pseudonymous_user_id", "date", "anomaly_score", "anomaly_flag", "prediction"
        ])
        return empty_res, None

    # 3. Prepare Feature Matrix X
    X = df[BEHAVIORAL_FEATURES].values.astype(np.float64)

    # 4. Train actual Isolation Forest model
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X)

    # 5. Predictions & Decision Functions
    # sklearn Isolation Forest: -1 for anomaly, +1 for normal
    raw_preds = model.predict(X)
    raw_decision = model.decision_function(X)

    # In sklearn: decision_function is negative for anomalies and positive for normal observations.
    # Convert to intuitive continuous anomaly score [0.0, 1.0] where 1.0 is highest anomaly:
    min_dec = np.min(raw_decision)
    max_dec = np.max(raw_decision)
    if max_dec > min_dec:
        # Invert so lower decision score maps to higher anomaly score
        normalized_scores = (max_dec - raw_decision) / (max_dec - min_dec)
    else:
        normalized_scores = np.zeros(len(raw_decision))

    # 6. Build Results DataFrame preserving user_id and dates
    results_df = df.copy()
    results_df["raw_decision_score"] = np.round(raw_decision, 4)
    results_df["anomaly_score"] = np.round(normalized_scores, 4)
    results_df["anomaly_flag"] = raw_preds == -1
    results_df["prediction"] = np.where(results_df["anomaly_flag"], "anomalous", "normal")

    # 7. Persist model artifact
    if save_model:
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)

    return results_df, model


def save_anomaly_results_to_mysql(results_df: pd.DataFrame, app=None) -> Dict[str, Any]:
    """
    Saves anomaly detection results to the MySQL anomaly_results table.
    Gracefully handles environments where MySQL is offline.
    """
    try:
        from database import db, test_connection
        import models
        from datetime import datetime

        if app is None:
            from app import create_app
            app = create_app()

        with app.app_context():
            conn_test = test_connection()
            if not conn_test["connected"]:
                return {
                    "synced": False,
                    "status": "mysql_offline",
                    "message": "MySQL is offline. Anomaly detection results held in memory.",
                    "records_stored": 0,
                }

            # Map pseudonymous user IDs to User table primary keys
            unique_pids = results_df["pseudonymous_user_id"].unique().tolist()
            existing_users = models.User.query.filter(models.User.pseudonymous_id.in_(unique_pids)).all()
            user_map = {u.pseudonymous_id: u.id for u in existing_users}

            stored_count = 0
            for _, row in results_df.iterrows():
                uid = user_map.get(row["pseudonymous_user_id"])
                if not uid:
                    continue

                act_date = datetime.strptime(row["date"], "%Y-%m-%d").date()

                existing_record = models.AnomalyResult.query.filter_by(
                    user_id=uid, activity_date=act_date
                ).first()

                if existing_record:
                    existing_record.anomaly_score = float(row["anomaly_score"])
                    existing_record.anomaly_flag = bool(row["anomaly_flag"])
                else:
                    new_record = models.AnomalyResult(
                        user_id=uid,
                        activity_date=act_date,
                        anomaly_score=float(row["anomaly_score"]),
                        anomaly_flag=bool(row["anomaly_flag"]),
                    )
                    db.session.add(new_record)

                stored_count += 1

            db.session.commit()
            return {
                "synced": True,
                "status": "success",
                "message": f"Successfully stored {stored_count} anomaly records in MySQL.",
                "records_stored": stored_count,
            }

    except Exception as e:
        return {
            "synced": False,
            "status": "error",
            "message": "Database sync failed for anomaly results.",
            "error": str(e),
            "records_stored": 0,
        }


def get_anomaly_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates structured diagnostic metrics on anomaly detection performance."""
    total_records = len(results_df)
    anomaly_records = results_df[results_df["anomaly_flag"]]
    anomaly_count = len(anomaly_records)
    pct = (anomaly_count / total_records * 100.0) if total_records > 0 else 0.0

    flagged_users = sorted(anomaly_records["pseudonymous_user_id"].unique().tolist())

    return {
        "total_records": total_records,
        "anomaly_count": anomaly_count,
        "normal_count": total_records - anomaly_count,
        "percentage_anomalous": round(pct, 2),
        "unique_users_flagged": len(flagged_users),
        "flagged_user_ids": flagged_users,
    }


if __name__ == "__main__":
    sample_csv = os.path.join(backend_dir, "data", "sample_data.csv")
    print(f"[*] Training Isolation Forest on: {sample_csv} (contamination={DEFAULT_CONTAMINATION}) ...")

    results_df, trained_model = detect_anomalies(sample_csv, contamination=DEFAULT_CONTAMINATION)
    summary = get_anomaly_summary(results_df)

    print(f"[+] Total records analyzed: {summary['total_records']}")
    print(f"[+] Total anomalies detected: {summary['anomaly_count']}")
    print(f"[+] Percentage anomalous: {summary['percentage_anomalous']}%")
    print(f"[+] Flagged users ({summary['unique_users_flagged']}): {summary['flagged_user_ids']}")

    print("\n--- Example Anomalous Records (Top 5 Highest Anomaly Scores) ---")
    anom_rows = results_df[results_df["anomaly_flag"]].sort_values("anomaly_score", ascending=False).head(5)
    cols_show = ["pseudonymous_user_id", "date", "anomaly_score", "prediction", "file_access_count", "sensitive_file_access", "web_upload_volume"]
    print(anom_rows[cols_show].to_string(index=False))
