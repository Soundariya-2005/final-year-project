"""
User-Day Behavioral Feature Engineering Pipeline for Insider Threat Detection.

Extracts, aggregates, and validates behavioral metrics for each pseudonymous user per day:
1. login_count
2. after_hours_login
3. file_access_count
4. sensitive_file_access
5. email_count
6. external_email_count
7. web_upload_volume
8. average_session_minutes

Chronological ordering, safe missing value imputation, and database synchronization.
"""

import os
import sys
from datetime import datetime, date
from typing import Union, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from privacy.pseudonymization import pseudonymize_user_id, hash_original_id

REQUIRED_FEATURE_COLUMNS = [
    "pseudonymous_user_id",
    "date",
    "login_count",
    "after_hours_login",
    "file_access_count",
    "sensitive_file_access",
    "email_count",
    "external_email_count",
    "web_upload_volume",
    "average_session_minutes",
]


def extract_behavior_features(data: Union[pd.DataFrame, str, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Extracts and aggregates user-day behavioral features from raw or batch activity logs.

    Args:
        data: Input activity data. Can be a pandas DataFrame, a CSV file path string,
              or a list of record dictionaries.

    Returns:
        pd.DataFrame containing exactly one record per (pseudonymous_user_id, date)
        with the 8 behavioral features, sorted chronologically.
    """
    # 1. Normalize input into a pandas DataFrame
    if isinstance(data, str):
        if not os.path.exists(data):
            raise FileNotFoundError(f"Input file not found at: {data}")
        df = pd.read_csv(data)
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError("Input data must be a pandas DataFrame, CSV file path, or list of dicts.")

    if df.empty:
        return pd.DataFrame(columns=REQUIRED_FEATURE_COLUMNS)

    # 2. Normalize column headers
    df.columns = [str(c).strip().lower() for c in df.columns]

    # 3. Identify user identifier column and ensure pseudonymization
    user_col = None
    for candidate in ["pseudonymous_user_id", "user_id", "pseudonymous_id", "employee_id", "user"]:
        if candidate in df.columns:
            user_col = candidate
            break

    if not user_col:
        raise ValueError(
            "Input data must contain a user identifier column "
            "('pseudonymous_user_id', 'user_id', or 'employee_id')."
        )

    # Convert to pseudonymous_user_id
    def _ensure_pseudonym(val: Any) -> str:
        s = str(val).strip()
        # If it's already in pseudonymous format USR-XXXXXX, keep it
        if s.startswith("USR-"):
            return s
        # Otherwise, deterministically pseudonymize
        return pseudonymize_user_id(s)

    df["pseudonymous_user_id"] = df[user_col].apply(_ensure_pseudonym)

    # 4. Parse and normalize the date column
    date_col = None
    for candidate in ["date", "activity_date", "timestamp", "datetime", "day"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if not date_col:
        raise ValueError("Input data must contain a date column ('date' or 'activity_date').")

    # Safely convert to YYYY-MM-DD string representation
    df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
    # Drop rows where date could not be parsed
    df = df.dropna(subset=["date"])

    # 5. Handle behavioral numeric columns safely with imputation
    numeric_specs = {
        "login_count": ("sum", 0, int),
        "after_hours_login": ("sum", 0, int),
        "file_access_count": ("sum", 0, int),
        "sensitive_file_access": ("sum", 0, int),
        "email_count": ("sum", 0, int),
        "external_email_count": ("sum", 0, int),
        "web_upload_volume": ("sum", 0.0, float),
        "average_session_minutes": ("mean", 0.0, float),
    }

    # Fill missing optional behavioral columns with safe 0 baseline
    for col, (_, default_val, dtype) in numeric_specs.items():
        if col not in df.columns:
            # Check for close aliases (e.g. upload_volume vs web_upload_volume)
            alias_found = False
            for alias in [f"web_{col}", col.replace("web_", ""), col.replace("_count", "")]:
                if alias in df.columns:
                    df[col] = pd.to_numeric(df[alias], errors="coerce").fillna(default_val)
                    alias_found = True
                    break
            if not alias_found:
                df[col] = default_val
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_val)

    # 6. Group by (pseudonymous_user_id, date) to ensure exactly one record per user-day
    agg_dict = {col: agg_fn for col, (agg_fn, _, _) in numeric_specs.items()}
    grouped = df.groupby(["pseudonymous_user_id", "date"], as_index=False).agg(agg_dict)

    # 7. Apply rounding, type enforcement, and logical consistency bounds
    grouped["login_count"] = grouped["login_count"].astype(int)
    grouped["after_hours_login"] = grouped["after_hours_login"].astype(int)
    # after_hours_login cannot exceed login_count
    grouped["after_hours_login"] = np.minimum(grouped["after_hours_login"], grouped["login_count"])

    grouped["file_access_count"] = grouped["file_access_count"].astype(int)
    grouped["sensitive_file_access"] = grouped["sensitive_file_access"].astype(int)
    # sensitive_file_access cannot exceed file_access_count
    grouped["sensitive_file_access"] = np.minimum(grouped["sensitive_file_access"], grouped["file_access_count"])

    grouped["email_count"] = grouped["email_count"].astype(int)
    grouped["external_email_count"] = grouped["external_email_count"].astype(int)
    # external_email_count cannot exceed email_count
    grouped["external_email_count"] = np.minimum(grouped["external_email_count"], grouped["email_count"])

    grouped["web_upload_volume"] = grouped["web_upload_volume"].round(2).astype(float)
    grouped["average_session_minutes"] = grouped["average_session_minutes"].round(1).astype(float)

    # 8. Chronological sorting by pseudonymous user and date
    grouped = grouped.sort_values(by=["pseudonymous_user_id", "date"], ascending=[True, True])
    grouped = grouped.reset_index(drop=True)

    # 9. Return DataFrame with strict column structure
    return grouped[REQUIRED_FEATURE_COLUMNS]


def save_features_to_mysql(features_df: pd.DataFrame, app=None) -> Dict[str, Any]:
    """
    Saves extracted behavioral features into the MySQL behavior_features table.
    Ensures matching user entries exist in the users table.
    Gracefully handles environments where MySQL is offline.

    Args:
        features_df: DataFrame generated by extract_behavior_features().
        app: Optional Flask app instance for app_context.

    Returns:
        Dict detailing synchronization status, count of records inserted/updated, or diagnostic error.
    """
    try:
        from database import db, test_connection
        import models

        if app is None:
            from app import create_app
            app = create_app()

        with app.app_context():
            # First verify MySQL connectivity
            conn_test = test_connection()
            if not conn_test["connected"]:
                return {
                    "synced": False,
                    "status": "mysql_offline",
                    "message": "MySQL is not currently reachable. Features extracted in memory.",
                    "error": conn_test["error"],
                    "records_stored": 0,
                }

            # Map pseudonymous user IDs to user.id database primary keys
            unique_pids = features_df["pseudonymous_user_id"].unique().tolist()
            existing_users = models.User.query.filter(models.User.pseudonymous_id.in_(unique_pids)).all()
            user_map = {u.pseudonymous_id: u.id for u in existing_users}

            # Insert any missing users
            new_users = []
            for pid in unique_pids:
                if pid not in user_map:
                    u = models.User(
                        pseudonymous_id=pid,
                        original_id_hash=hash_original_id(pid),
                    )
                    db.session.add(u)
                    new_users.append(u)

            if new_users:
                db.session.flush()
                for u in new_users:
                    user_map[u.pseudonymous_id] = u.id

            # Insert or update BehaviorFeature records
            stored_count = 0
            for _, row in features_df.iterrows():
                uid = user_map.get(row["pseudonymous_user_id"])
                if not uid:
                    continue

                act_date = datetime.strptime(row["date"], "%Y-%m-%d").date()

                # Check if feature record already exists for (user_id, activity_date)
                existing_feat = models.BehaviorFeature.query.filter_by(
                    user_id=uid, activity_date=act_date
                ).first()

                if existing_feat:
                    # Update fields
                    existing_feat.login_count = int(row["login_count"])
                    existing_feat.after_hours_login = int(row["after_hours_login"])
                    existing_feat.file_access_count = int(row["file_access_count"])
                    existing_feat.sensitive_file_access = int(row["sensitive_file_access"])
                    existing_feat.email_count = int(row["email_count"])
                    existing_feat.external_email_count = int(row["external_email_count"])
                    existing_feat.web_upload_volume = float(row["web_upload_volume"])
                    existing_feat.average_session_minutes = float(row["average_session_minutes"])
                else:
                    new_feat = models.BehaviorFeature(
                        user_id=uid,
                        activity_date=act_date,
                        login_count=int(row["login_count"]),
                        after_hours_login=int(row["after_hours_login"]),
                        file_access_count=int(row["file_access_count"]),
                        sensitive_file_access=int(row["sensitive_file_access"]),
                        email_count=int(row["email_count"]),
                        external_email_count=int(row["external_email_count"]),
                        web_upload_volume=float(row["web_upload_volume"]),
                        average_session_minutes=float(row["average_session_minutes"]),
                    )
                    db.session.add(new_feat)

                stored_count += 1

            db.session.commit()
            return {
                "synced": True,
                "status": "success",
                "message": f"Successfully stored {stored_count} behavioral feature records in MySQL.",
                "records_stored": stored_count,
                "users_synced": len(unique_pids),
            }

    except Exception as e:
        return {
            "synced": False,
            "status": "error",
            "message": "Database synchronization failed.",
            "error": str(e),
            "records_stored": 0,
        }


if __name__ == "__main__":
    sample_csv = os.path.join(backend_dir, "data", "sample_data.csv")
    print(f"[*] Testing feature extraction using: {sample_csv}")
    feat_df = extract_behavior_features(sample_csv)
    print(f"[+] Extraction complete:")
    print(f"    - Number of users: {feat_df['pseudonymous_user_id'].nunique()}")
    print(f"    - Number of user-day records: {len(feat_df)}")
    print(f"    - Date range: {feat_df['date'].min()} to {feat_df['date'].max()}")
    print("\n[+] Feature DataFrame Preview (first 5 records):")
    print(feat_df.head(5).to_string(index=False))
