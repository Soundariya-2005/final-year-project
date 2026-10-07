"""
Explainable AI (XAI) Module for Insider Threat Detection using SHAP.

Uses shap.TreeExplainer directly on the trained sklearn.ensemble.IsolationForest model.
Calculates additive feature attributions for all 8 behavioral dimensions:
1. login_count
2. after_hours_login
3. file_access_count
4. sensitive_file_access
5. email_count
6. external_email_count
7. web_upload_volume
8. average_session_minutes

Technical Approach (Viva & Technical Documentation):
- TreeExplainer calculates exact Shapley values for tree ensembles based on game theory.
- In Isolation Forest, shorter average path lengths correspond to anomaly isolation.
- Negative SHAP contributions push the observation closer to isolation (increasing anomaly likelihood),
  while positive SHAP values represent normal baseline behavior.
- Direction is standardized into:
  - 'INCREASES_RISK': Feature pushed the observation towards anomalous isolation.
  - 'DECREASES_RISK': Feature behaved within normal baseline bounds.
- Explanations are stored in the MySQL risk_explanations table.
"""

import os
import sys
from typing import Union, List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import IsolationForest

# Ensure backend root is on Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ml.anomaly_detection import (
    detect_anomalies,
    BEHAVIORAL_FEATURES,
    DEFAULT_CONTAMINATION,
    MODEL_PATH,
)


def explain_anomalies_shap(
    features_df: pd.DataFrame,
    model: Optional[IsolationForest] = None,
    user_id: Optional[str] = None,
    date_filter: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes genuine SHAP values using shap.TreeExplainer on the trained Isolation Forest.

    Args:
        features_df: Feature DataFrame (must contain BEHAVIORAL_FEATURES).
        model: Trained Isolation Forest model instance. If None, trains one.
        user_id: Optional pseudonymous user ID filter.
        date_filter: Optional YYYY-MM-DD date filter.

    Returns:
        Tuple of (explanations_dataframe, summary_dict)
        explanations_dataframe contains:
        - pseudonymous_user_id
        - date
        - feature
        - feature_value
        - shap_value
        - contribution (magnitude |shap_value|)
        - direction ('INCREASES_RISK' or 'DECREASES_RISK')
        - rank (importance rank for this observation)
    """
    # 1. Train or load Isolation Forest if not provided
    if model is None:
        features_df, model = detect_anomalies(features_df, contamination=DEFAULT_CONTAMINATION)

    # Filter data if requested
    eval_df = features_df.copy()
    if user_id:
        eval_df = eval_df[eval_df["pseudonymous_user_id"] == user_id]
    if date_filter:
        eval_df = eval_df[eval_df["date"] == date_filter]

    if eval_df.empty:
        return pd.DataFrame(), {}

    eval_df = eval_df.reset_index(drop=True)
    X = eval_df[BEHAVIORAL_FEATURES].values.astype(np.float64)

    # 2. Compute exact SHAP values using TreeExplainer
    explainer = shap.TreeExplainer(model)
    raw_shap_values = explainer.shap_values(X)

    # Ensure 2D numpy array: (n_samples, n_features)
    shap_matrix = np.array(raw_shap_values)
    if shap_matrix.ndim == 3:
        # In multi-class cases, take the anomalous class slice
        shap_matrix = shap_matrix[:, :, 0]

    # 3. Build long-form explanation records
    records = []
    n_samples = len(eval_df)

    for i in range(n_samples):
        row = eval_df.iloc[i]
        p_id = row["pseudonymous_user_id"]
        d_val = row["date"]

        row_shap = shap_matrix[i]
        # In Isolation Forest: negative SHAP value indicates pushed towards anomalous leaf
        # We classify direction based on impact towards anomaly
        feature_contributions = []

        for f_idx, feat_name in enumerate(BEHAVIORAL_FEATURES):
            val = float(row[feat_name])
            s_val = float(row_shap[f_idx])
            # Magnitude of contribution
            magnitude = round(abs(s_val), 4)

            # In Isolation Forest, negative score pushes towards anomaly (isolation)
            if s_val < 0:
                direction = "INCREASES_RISK"
            else:
                direction = "DECREASES_RISK"

            feature_contributions.append({
                "pseudonymous_user_id": p_id,
                "date": d_val,
                "feature": feat_name,
                "feature_value": round(val, 2),
                "shap_value": round(s_val, 4),
                "contribution": magnitude,
                "direction": direction,
            })

        # Rank features for this observation by contribution magnitude descending
        feature_contributions.sort(key=lambda x: x["contribution"], reverse=True)
        for rank, entry in enumerate(feature_contributions, start=1):
            entry["rank"] = rank
            records.append(entry)

    explanation_df = pd.DataFrame(records)

    # Global feature importance summary across analyzed dataset
    mean_abs_shap = np.mean(np.abs(shap_matrix), axis=0)
    global_importance = sorted(
        [
            {"feature": feat, "mean_absolute_shap": round(float(mean_abs_shap[idx]), 4)}
            for idx, feat in enumerate(BEHAVIORAL_FEATURES)
        ],
        key=lambda x: x["mean_absolute_shap"],
        reverse=True
    )

    summary = {
        "total_records_explained": n_samples,
        "features_analyzed": BEHAVIORAL_FEATURES,
        "global_feature_importance": global_importance,
        "top_feature_overall": global_importance[0]["feature"] if global_importance else None,
    }

    return explanation_df, summary


def get_user_explanations(
    explanation_df: pd.DataFrame,
    user_id: str,
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Retrieves the top contributing features for a given user across their anomalous events.
    Answers:
    1. What features contributed most?
    2. Which features increased the anomaly?
    3. Which features had lower contribution?
    """
    user_records = explanation_df[explanation_df["pseudonymous_user_id"] == user_id]
    if user_records.empty:
        return {
            "user_id": user_id,
            "status": "not_found",
            "message": f"No explanation records found for user '{user_id}'.",
            "explanations": [],
        }

    # Aggregate contributions for this user
    feature_agg = user_records.groupby("feature").agg({
        "contribution": "mean",
        "shap_value": "mean",
        "feature_value": "mean",
    }).reset_index()

    feature_agg["contribution"] = feature_agg["contribution"].round(4)
    feature_agg["shap_value"] = feature_agg["shap_value"].round(4)
    feature_agg["feature_value"] = feature_agg["feature_value"].round(2)

    # Sort by contribution descending
    feature_agg = feature_agg.sort_values("contribution", ascending=False)

    top_increasing = feature_agg[feature_agg["shap_value"] < 0].head(top_n).to_dict(orient="records")
    top_decreasing = feature_agg[feature_agg["shap_value"] >= 0].head(top_n).to_dict(orient="records")

    # Timeline of daily top contributing features
    timeline = []
    for d, d_group in user_records.groupby("date"):
        top_driver = d_group.sort_values("contribution", ascending=False).iloc[0]
        timeline.append({
            "date": d,
            "top_feature": top_driver["feature"],
            "feature_value": top_driver["feature_value"],
            "contribution": top_driver["contribution"],
            "direction": top_driver["direction"],
        })

    return {
        "user_id": user_id,
        "status": "success",
        "total_days_analyzed": user_records["date"].nunique(),
        "top_features_overall": feature_agg.head(top_n).to_dict(orient="records"),
        "features_increasing_anomaly": top_increasing,
        "features_decreasing_anomaly": top_decreasing,
        "daily_primary_drivers": timeline,
    }


def save_explanations_to_mysql(explanation_df: pd.DataFrame, app=None) -> Dict[str, Any]:
    """
    Saves SHAP feature explanations into the MySQL risk_explanations table.
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
                    "message": "MySQL is offline. SHAP explanations held in memory.",
                    "records_stored": 0,
                }

            unique_pids = explanation_df["pseudonymous_user_id"].unique().tolist()
            existing_users = models.User.query.filter(models.User.pseudonymous_id.in_(unique_pids)).all()
            user_map = {u.pseudonymous_id: u.id for u in existing_users}

            stored_count = 0
            # Only store top 3 features per user-day to optimize storage
            top_explanations = explanation_df[explanation_df["rank"] <= 3]

            for _, row in top_explanations.iterrows():
                uid = user_map.get(row["pseudonymous_user_id"])
                if not uid:
                    continue

                act_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                feat_name = str(row["feature"])

                existing_record = models.RiskExplanation.query.filter_by(
                    user_id=uid, activity_date=act_date, feature=feat_name
                ).first()

                if existing_record:
                    existing_record.contribution = float(row["contribution"])
                    existing_record.direction = str(row["direction"])
                else:
                    new_rec = models.RiskExplanation(
                        user_id=uid,
                        activity_date=act_date,
                        feature=feat_name,
                        contribution=float(row["contribution"]),
                        direction=str(row["direction"]),
                    )
                    db.session.add(new_rec)

                stored_count += 1

            db.session.commit()
            return {
                "synced": True,
                "status": "success",
                "message": f"Successfully stored {stored_count} top SHAP explanations in MySQL.",
                "records_stored": stored_count,
            }

    except Exception as e:
        return {
            "synced": False,
            "status": "error",
            "message": "Database sync failed for SHAP explanations.",
            "error": str(e),
            "records_stored": 0,
        }


if __name__ == "__main__":
    sample_csv = os.path.join(backend_dir, "data", "sample_data.csv")
    print(f"[*] Calculating SHAP feature attributions on: {sample_csv} ...")

    from ml.anomaly_detection import detect_anomalies
    anom_df, model = detect_anomalies(sample_csv)
    expl_df, summary = explain_anomalies_shap(anom_df, model=model)

    print(f"[+] Total explanation rows: {len(expl_df)}")
    print(f"[+] Global Feature Importance Ranking (mean |SHAP|):")
    for item in summary["global_feature_importance"]:
        print(f"    - {item['feature']:<25}: {item['mean_absolute_shap']:.4f}")

    # Show single user explanation for USR-1012 (Data Exfiltration Drift)
    print("\n--- Example SHAP Explanation for USR-1012 ---")
    u_expl = get_user_explanations(expl_df, "USR-1012", top_n=5)
    print(f"User: {u_expl['user_id']}")
    print(f"Features that increased anomaly risk most:")
    for f in u_expl["features_increasing_anomaly"]:
        print(f"  * {f['feature']:<25} | Value: {f['feature_value']:<8} | SHAP: {f['shap_value']:<8} | Contribution: {f['contribution']}")
