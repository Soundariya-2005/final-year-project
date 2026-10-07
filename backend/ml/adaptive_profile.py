"""
Adaptive User Profiling Module for Insider Threat Detection.

Implements Exponential Weighted Moving Average (EWMA) behavioral baseline tracking:
    baseline(t) = (1 - alpha) * baseline(t-1) + alpha * x(t)

Default alpha = 0.15

Key Concepts for Viva / Technical Presentation:
1. User-Specific Profiles: Each employee maintains an independent baseline per behavioral feature.
2. Chronological Adaptation: Daily observations incrementally update the baseline.
3. Inertia & Sensitivity:
   - High alpha (e.g. 0.5): Fast adaptation, susceptible to baseline poisoning.
   - Low alpha (e.g. 0.05): Slow adaptation, high inertia.
   - Default alpha = 0.15 balances stability (85% historical weight) with adaptive learning (15% new observation).
4. Deviation Calculation:
   - deviation(t) = x(t) - baseline(t-1)
   - Measures how far today's action deviates from established historical habits.
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

from ml.feature_engineering import extract_behavior_features

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

DEFAULT_ALPHA = 0.15


def get_default_alpha_from_settings() -> float:
    """
    Attempts to read the alpha setting from the database settings table if available,
    otherwise returns DEFAULT_ALPHA (0.15).
    """
    try:
        from database import db
        import models
        setting = models.Setting.query.first()
        if setting and setting.alpha is not None:
            return float(setting.alpha)
    except Exception:
        pass
    return DEFAULT_ALPHA


def calculate_adaptive_profile(
    features: Union[pd.DataFrame, str, List[Dict[str, Any]]],
    alpha: float = DEFAULT_ALPHA
) -> pd.DataFrame:
    """
    Calculates adaptive behavioral baselines and deviations for each user across time.

    Formula:
        For day t = 0:
            baseline(0) = x(0)
            deviation(0) = 0.0
        For day t > 0:
            deviation(t) = x(t) - baseline(t-1)
            baseline(t)  = (1 - alpha) * baseline(t-1) + alpha * x(t)

    Args:
        features: Input feature data (DataFrame, CSV path, or list of records).
        alpha: Adaptation learning rate between 0 and 1 (default 0.15).

    Returns:
        pd.DataFrame containing:
        - pseudonymous_user_id
        - date
        - For each feature f:
            - f (current value)
            - f_baseline (historical adaptive baseline)
            - f_deviation (current deviation from prior baseline)
    """
    # 1. Validate alpha
    if not (0.0 < alpha <= 1.0):
        raise ValueError(f"Alpha must be in range (0.0, 1.0], received: {alpha}")

    # 2. Extract and ensure normalized behavioral features
    if isinstance(features, (str, list)):
        df = extract_behavior_features(features)
    elif isinstance(features, pd.DataFrame):
        # If columns match required structure, use directly; otherwise normalize
        req_cols = {"pseudonymous_user_id", "date"}.union(set(BEHAVIORAL_FEATURES))
        if req_cols.issubset(set(features.columns)):
            df = features.copy()
        else:
            df = extract_behavior_features(features)
    else:
        raise TypeError("features must be a DataFrame, CSV file path, or list of dicts.")

    if df.empty:
        return pd.DataFrame()

    # 3. Ensure strictly chronological ordering per user
    user_col = "pseudonymous_user_id"
    df = df.sort_values(by=[user_col, "date"], ascending=[True, True]).reset_index(drop=True)

    # 4. Process each user's timeline independently
    processed_records = []

    for user_id, group in df.groupby(user_col, sort=False):
        group = group.reset_index(drop=True)
        num_days = len(group)

        # Baseline state dictionary tracking baseline(t-1)
        current_baseline = {}

        for t in range(num_days):
            row = group.iloc[t]
            date_val = row["date"]

            record_out = {
                "pseudonymous_user_id": user_id,
                "date": date_val,
            }

            for feat in BEHAVIORAL_FEATURES:
                x_t = float(row[feat])
                record_out[feat] = round(x_t, 2)

                if t == 0:
                    # Day 0 initialization: baseline equals initial observation
                    baseline_t = x_t
                    deviation_t = 0.0
                else:
                    # Previous day baseline
                    prev_baseline = current_baseline[feat]
                    # Deviation against prior baseline habits
                    deviation_t = x_t - prev_baseline
                    # EWMA adaptive update formula
                    baseline_t = (1.0 - alpha) * prev_baseline + alpha * x_t

                current_baseline[feat] = baseline_t

                record_out[f"{feat}_baseline"] = round(baseline_t, 2)
                record_out[f"{feat}_deviation"] = round(deviation_t, 2)

            processed_records.append(record_out)

    result_df = pd.DataFrame(processed_records)
    return result_df


def get_user_profile_summary(
    profile_df: pd.DataFrame,
    user_id: str
) -> Dict[str, Any]:
    """
    Returns a clean summary of a single user's behavioral baseline progression across days.
    Ideal for presentation demonstration and step-by-step viva explanation.
    """
    user_records = profile_df[profile_df["pseudonymous_user_id"] == user_id].copy()
    if user_records.empty:
        raise ValueError(f"User '{user_id}' not found in profile DataFrame.")

    user_records = user_records.sort_values("date").reset_index(drop=True)

    progression = []
    for idx, row in user_records.iterrows():
        day_info = {
            "day_index": idx,
            "date": row["date"],
            "features": {},
        }
        for f in BEHAVIORAL_FEATURES:
            day_info["features"][f] = {
                "current_value": row[f],
                "baseline": row[f"{f}_baseline"],
                "deviation": row[f"{f}_deviation"],
            }
        progression.append(day_info)

    return {
        "user_id": user_id,
        "total_days": len(user_records),
        "start_date": user_records["date"].min(),
        "end_date": user_records["date"].max(),
        "daily_progression": progression,
    }


if __name__ == "__main__":
    sample_csv = os.path.join(backend_dir, "data", "sample_data.csv")
    print(f"[*] Calculating adaptive profiles with alpha = {DEFAULT_ALPHA} on {sample_csv} ...")

    profile_df = calculate_adaptive_profile(sample_csv, alpha=DEFAULT_ALPHA)
    print(f"[+] Profile calculation complete: {len(profile_df)} records across {profile_df['pseudonymous_user_id'].nunique()} users.")

    # Demonstration for viva: show how USR-1001 baseline shifts over first 5 days
    demo_user = "USR-1001"
    summary = get_user_profile_summary(profile_df, demo_user)
    print(f"\n================================================================================")
    print(f" DEMONSTRATION FOR VIVA: Adaptive Baseline Progression for {demo_user} (alpha = {DEFAULT_ALPHA})")
    print(f" Formula: baseline(t) = (1 - alpha) * baseline(t-1) + alpha * x(t)")
    print(f"================================================================================")

    feat_demo = "file_access_count"
    print(f"Tracking Feature: '{feat_demo}' across first 6 days:\n")
    print(f"{'Day':<5} | {'Date':<10} | {'Current x(t)':<12} | {'Prior Base':<12} | {'New Base':<12} | {'Deviation':<10}")
    print("-" * 75)

    for i in range(min(6, len(summary["daily_progression"]))):
        d = summary["daily_progression"][i]
        curr = d["features"][feat_demo]["current_value"]
        base = d["features"][feat_demo]["baseline"]
        dev = d["features"][feat_demo]["deviation"]
        prior_base = (
            "N/A (Day 0)"
            if i == 0
            else f"{summary['daily_progression'][i-1]['features'][feat_demo]['baseline']:.2f}"
        )
        print(f"{i:<5} | {d['date']:<10} | {curr:<12.1f} | {prior_base:<12} | {base:<12.2f} | {dev:<+10.2f}")
    print("=" * 75)
