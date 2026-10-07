"""
Progressive Risk Engine for Insider Threat Early Warning System.

Implements chronological risk accumulation and decay:
    risk(t) = decay * risk(t-1) + gain * anomaly(t)

Defaults:
    risk_decay = 0.88
    risk_gain  = 0.13

Risk is represented on a 0–100 scale:
    0–24  : LOW
    25–49 : MEDIUM
    50–74 : HIGH
    75–100: CRITICAL

Key Properties:
1. Chronological Progression: Processed per user in strict calendar order.
2. Accumulation: Repeated anomalies compound over consecutive days into HIGH and CRITICAL.
3. Resilience: A single isolated anomaly produces modest risk (~13 points), avoiding false CRITICAL alarms.
4. Gradual Decay: Subsequent normal behavior allows the score to decay toward 0.
"""

import os
import sys
from typing import Union, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Ensure backend root is on Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

DEFAULT_RISK_DECAY = 0.88
DEFAULT_RISK_GAIN = 0.13

# Configurable risk thresholds
RISK_THRESHOLDS = {
    "LOW": (0.0, 24.99),
    "MEDIUM": (25.0, 49.99),
    "HIGH": (50.0, 74.99),
    "CRITICAL": (75.0, 100.0),
}


def classify_risk_level(score: float) -> str:
    """Classifies a numerical risk score (0-100) into its severity tier."""
    if score >= 75.0:
        return "CRITICAL"
    elif score >= 50.0:
        return "HIGH"
    elif score >= 25.0:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_progressive_risk(
    anomaly_results: Union[pd.DataFrame, str, List[Dict[str, Any]]],
    decay: float = DEFAULT_RISK_DECAY,
    gain: float = DEFAULT_RISK_GAIN
) -> pd.DataFrame:
    """
    Computes progressive risk scores chronologically for each user.

    Formula:
        For day t = 0:
            risk(0) = gain * anomaly_input(0)
        For day t > 0:
            risk(t) = min(100.0, max(0.0, decay * risk(t-1) + gain * anomaly_input(t)))

    Where anomaly_input(t) is scaled to [0, 100] when anomalous:
        anomaly_input(t) = (anomaly_score * 100) if anomaly_flag else 0.0

    Args:
        anomaly_results: DataFrame, CSV path, or list of dicts with
                         ['pseudonymous_user_id', 'date', 'anomaly_score', 'anomaly_flag'].
        decay: Rate of risk decay per day of normal activity (default 0.88).
        gain: Rate of risk accumulation per anomaly unit (default 0.13).

    Returns:
        pd.DataFrame with:
        - pseudonymous_user_id
        - date
        - risk_score (float 0.0 - 100.0)
        - risk_level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        - anomaly_flag
        - anomaly_score
    """
    # 1. Normalize input into a DataFrame
    if isinstance(anomaly_results, str):
        # If it's a raw feature file, run anomaly detection first
        from ml.anomaly_detection import detect_anomalies
        df, _ = detect_anomalies(anomaly_results)
    elif isinstance(anomaly_results, list):
        df = pd.DataFrame(anomaly_results)
    elif isinstance(anomaly_results, pd.DataFrame):
        df = anomaly_results.copy()
    else:
        raise TypeError("anomaly_results must be a DataFrame, CSV file path, or list of dicts.")

    if df.empty:
        return pd.DataFrame(columns=["pseudonymous_user_id", "date", "risk_score", "risk_level"])

    # Standardize column naming
    user_col = None
    for cand in ["pseudonymous_user_id", "user_id", "pseudonymous_id"]:
        if cand in df.columns:
            user_col = cand
            break
    if not user_col:
        raise ValueError("Missing user column ('pseudonymous_user_id' or 'user_id').")

    df["pseudonymous_user_id"] = df[user_col]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # If anomaly_score or anomaly_flag missing, detect them
    if "anomaly_flag" not in df.columns or "anomaly_score" not in df.columns:
        from ml.anomaly_detection import detect_anomalies
        df, _ = detect_anomalies(df)

    # 2. Sort chronologically per user
    df = df.sort_values(by=["pseudonymous_user_id", "date"], ascending=[True, True]).reset_index(drop=True)

    # 3. Progressive accumulation loop
    results = []

    for user_id, group in df.groupby("pseudonymous_user_id", sort=False):
        group = group.reset_index(drop=True)
        num_days = len(group)

        prior_risk = 0.0

        for t in range(num_days):
            row = group.iloc[t]
            is_anom = bool(row["anomaly_flag"])
            score_val = float(row["anomaly_score"])

            # Anomaly input signal on a 0-100 scale:
            if is_anom:
                # Severity-weighted impulse: higher anomaly score yields stronger impulse (up to 100)
                anomaly_signal = max(60.0, score_val * 100.0)
            else:
                anomaly_signal = 0.0

            # Progressive formula:
            if t == 0:
                current_risk = gain * anomaly_signal
            else:
                current_risk = (decay * prior_risk) + (gain * anomaly_signal)

            # Enforce 0 - 100 boundary
            current_risk = min(100.0, max(0.0, current_risk))
            current_risk_rounded = round(current_risk, 2)
            level = classify_risk_level(current_risk_rounded)

            prior_risk = current_risk

            rec = {
                "pseudonymous_user_id": user_id,
                "date": row["date"],
                "risk_score": current_risk_rounded,
                "risk_level": level,
                "anomaly_flag": is_anom,
                "anomaly_score": score_val,
            }
            results.append(rec)

    risk_df = pd.DataFrame(results)
    return risk_df


def save_risk_scores_to_mysql(risk_df: pd.DataFrame, app=None) -> Dict[str, Any]:
    """
    Saves progressive risk scores to the MySQL risk_scores table.
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
                    "message": "MySQL is offline. Risk calculations maintained in memory.",
                    "records_stored": 0,
                }

            unique_pids = risk_df["pseudonymous_user_id"].unique().tolist()
            existing_users = models.User.query.filter(models.User.pseudonymous_id.in_(unique_pids)).all()
            user_map = {u.pseudonymous_id: u.id for u in existing_users}

            stored_count = 0
            for _, row in risk_df.iterrows():
                uid = user_map.get(row["pseudonymous_user_id"])
                if not uid:
                    continue

                act_date = datetime.strptime(row["date"], "%Y-%m-%d").date()

                existing_record = models.RiskScore.query.filter_by(
                    user_id=uid, activity_date=act_date
                ).first()

                if existing_record:
                    existing_record.risk_score = float(row["risk_score"])
                    existing_record.risk_level = str(row["risk_level"])
                else:
                    new_record = models.RiskScore(
                        user_id=uid,
                        activity_date=act_date,
                        risk_score=float(row["risk_score"]),
                        risk_level=str(row["risk_level"]),
                    )
                    db.session.add(new_record)

                stored_count += 1

            db.session.commit()
            return {
                "synced": True,
                "status": "success",
                "message": f"Successfully stored {stored_count} risk scores in MySQL.",
                "records_stored": stored_count,
            }

    except Exception as e:
        return {
            "synced": False,
            "status": "error",
            "message": "Database sync failed for risk scores.",
            "error": str(e),
            "records_stored": 0,
        }


def get_risk_summary(risk_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates distribution summary across risk tiers."""
    counts = risk_df["risk_level"].value_counts().to_dict()
    total = len(risk_df)

    latest_date = risk_df["date"].max()
    latest_snapshot = risk_df[risk_df["date"] == latest_date]
    latest_counts = latest_snapshot["risk_level"].value_counts().to_dict()

    return {
        "total_records": total,
        "overall_distribution": {
            "LOW": counts.get("LOW", 0),
            "MEDIUM": counts.get("MEDIUM", 0),
            "HIGH": counts.get("HIGH", 0),
            "CRITICAL": counts.get("CRITICAL", 0),
        },
        "latest_snapshot_distribution": {
            "LOW": latest_counts.get("LOW", 0),
            "MEDIUM": latest_counts.get("MEDIUM", 0),
            "HIGH": latest_counts.get("HIGH", 0),
            "CRITICAL": latest_counts.get("CRITICAL", 0),
        },
        "max_risk_score": float(risk_df["risk_score"].max()) if total > 0 else 0.0,
        "critical_users": sorted(risk_df[risk_df["risk_level"] == "CRITICAL"]["pseudonymous_user_id"].unique().tolist()),
    }


if __name__ == "__main__":
    sample_csv = os.path.join(backend_dir, "data", "sample_data.csv")
    print(f"[*] Calculating progressive risk on {sample_csv} (decay={DEFAULT_RISK_DECAY}, gain={DEFAULT_RISK_GAIN}) ...")

    from ml.anomaly_detection import detect_anomalies
    anom_df, _ = detect_anomalies(sample_csv)
    risk_df = calculate_progressive_risk(anom_df, decay=DEFAULT_RISK_DECAY, gain=DEFAULT_RISK_GAIN)
    summary = get_risk_summary(risk_df)

    print(f"[+] Total records evaluated: {summary['total_records']}")
    print(f"[+] Distribution across all days: {summary['overall_distribution']}")
    print(f"[+] Latest Day Snapshot ({risk_df['date'].max()}): {summary['latest_snapshot_distribution']}")
    print(f"[+] Users reaching CRITICAL tier: {summary['critical_users']}")

    # Show progression for USR-1012 (Data Exfiltration Drift)
    print("\n--- Example Risk Progression for USR-1012 (Days 20 to 30) ---")
    u_demo = risk_df[risk_df["pseudonymous_user_id"] == "USR-1012"].iloc[20:31]
    print(u_demo[["pseudonymous_user_id", "date", "anomaly_flag", "anomaly_score", "risk_score", "risk_level"]].to_string(index=False))
