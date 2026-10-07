"""
Sample Activity-Log Data Generator for Insider Threat Detection System.

Generates realistic enterprise user activity records across 45 days for 40 users (1,800 records).
Simulates normal baseline behavioral patterns with 3 users exhibiting gradual behavioral deviation
(e.g., escalating after-hours access, sensitive file touches, web uploads, external emails).

IMPORTANT:
- No ground-truth anomaly or malicious labels are included in the dataset.
- The Isolation Forest algorithm will learn anomaly detection solely from these behavioral metrics.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def generate_sample_data(
    num_users: int = 40,
    num_days: int = 45,
    output_path: str = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic enterprise user behavioral activity logs.

    Args:
        num_users: Total number of employees to simulate (default 40).
        num_days: Consecutive monitoring period in days (default 45).
        output_path: Target CSV file path (defaults to backend/data/sample_data.csv).
        seed: Random seed for reproducible project demonstration.

    Returns:
        pandas.DataFrame containing exactly the 10 required behavioral fields:
        [user_id, date, login_count, after_hours_login, file_access_count,
         sensitive_file_access, email_count, external_email_count,
         web_upload_volume, average_session_minutes]
    """
    np.random.seed(seed)
    random.seed(seed)

    if output_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "sample_data.csv")

    # Generate user IDs: USR-1001 to USR-1040
    user_ids = [f"USR-{1000 + i + 1}" for i in range(num_users)]

    # Designated users who will exhibit gradual behavioral divergence over time
    # (Notice: No labels are placed in the output CSV; only numerical behavior changes)
    gradual_users = {
        user_ids[11]: "exfiltration",      # USR-1012: Escalating file access & large web upload volume
        user_ids[24]: "after_hours_recon", # USR-1025: Escalating after-hours logins & long sessions
        user_ids[37]: "ip_leakage",        # USR-1038: Escalating external emails & sensitive files
    }

    # Reference timeline: 45 consecutive calendar days
    start_date = datetime(2026, 8, 15)
    dates = [start_date + timedelta(days=d) for d in range(num_days)]

    records = []

    for user in user_ids:
        # Base user baseline variations (some users naturally work slightly more or less)
        user_login_base = max(1, int(np.random.normal(2, 0.5)))
        user_file_base = max(8, int(np.random.normal(20, 4)))
        user_email_base = max(5, int(np.random.normal(15, 3)))
        user_upload_base = max(0.5, float(np.random.normal(3.5, 1.0)))
        user_session_base = max(25.0, float(np.random.normal(50.0, 8.0)))

        is_gradual = user in gradual_users
        anomaly_type = gradual_users.get(user)

        for day_idx, current_date in enumerate(dates):
            is_weekend = current_date.weekday() >= 5
            date_str = current_date.strftime("%Y-%m-%d")

            # Progressive drift factor: starts at day 22 and escalates gradually to day 44
            progress = 0.0
            if is_gradual and day_idx >= 22:
                # Progression scale from 0.0 to 1.0
                progress = min(1.0, (day_idx - 21) / 23.0)

            if is_weekend:
                # Normal weekend behavior: minimal activity
                if is_gradual and progress > 0.4:
                    # Anomaly user begins working/logging in on weekends
                    login_count = int(np.random.poisson(2 + 2 * progress))
                    after_hours_login = login_count
                    file_access_count = int(np.random.poisson(15 + 30 * progress))
                    sensitive_file_access = int(np.random.poisson(2 + 8 * progress))
                    email_count = int(np.random.poisson(3 + 5 * progress))
                    external_email_count = int(np.random.poisson(1 + 4 * progress))
                    web_upload_volume = round(float(np.random.uniform(5.0, 40.0 * progress)), 2)
                    average_session_minutes = round(float(np.random.normal(60.0 + 40.0 * progress, 15.0)), 1)
                else:
                    # Normal employee on weekend (0 or rare quick check-in)
                    if random.random() < 0.12:
                        login_count = 1
                        after_hours_login = 1
                        file_access_count = random.randint(1, 4)
                        sensitive_file_access = 0
                        email_count = random.randint(0, 3)
                        external_email_count = 0
                        web_upload_volume = round(float(np.random.uniform(0.1, 1.5)), 2)
                        average_session_minutes = round(float(np.random.uniform(10.0, 30.0)), 1)
                    else:
                        login_count = 0
                        after_hours_login = 0
                        file_access_count = 0
                        sensitive_file_access = 0
                        email_count = 0
                        external_email_count = 0
                        web_upload_volume = 0.0
                        average_session_minutes = 0.0
            else:
                # Regular Weekday Behavior
                if not is_gradual or progress == 0.0:
                    # Standard baseline behavior with natural daily variation
                    login_count = max(1, int(np.random.normal(user_login_base, 0.7)))
                    after_hours_login = 1 if (random.random() < 0.08) else 0
                    file_access_count = max(5, int(np.random.normal(user_file_base, 5.0)))
                    # Sensitive files are rare in normal business operations
                    sensitive_file_access = 1 if (random.random() < 0.05) else 0
                    email_count = max(4, int(np.random.normal(user_email_base, 4.0)))
                    external_email_count = int(np.random.binomial(email_count, 0.12))
                    web_upload_volume = round(max(0.1, float(np.random.normal(user_upload_base, 1.2))), 2)
                    average_session_minutes = round(max(20.0, float(np.random.normal(user_session_base, 10.0))), 1)

                else:
                    # Gradual deviation based on profile
                    if anomaly_type == "exfiltration":
                        # USR-1012: Massive surge in file access, sensitive files, and web upload volume
                        login_count = max(2, int(np.random.normal(user_login_base + 3 * progress, 1.0)))
                        after_hours_login = int(np.random.poisson(1.5 * progress))
                        file_access_count = max(15, int(np.random.normal(user_file_base + 120 * progress, 15.0)))
                        sensitive_file_access = max(0, int(np.random.poisson(18 * progress)))
                        email_count = max(5, int(np.random.normal(user_email_base, 4.0)))
                        external_email_count = int(np.random.binomial(email_count, 0.15))
                        # Web upload volume dramatically increases (data exfiltration)
                        web_upload_volume = round(float(np.random.normal(user_upload_base + 320.0 * progress, 45.0 * progress)), 2)
                        web_upload_volume = max(0.5, web_upload_volume)
                        average_session_minutes = round(max(30.0, float(np.random.normal(user_session_base + 70.0 * progress, 15.0))), 1)

                    elif anomaly_type == "after_hours_recon":
                        # USR-1025: High after-hours logins, long unusual night sessions, reconnaissance
                        login_count = max(3, int(np.random.normal(user_login_base + 6 * progress, 1.5)))
                        after_hours_login = max(1, int(np.random.poisson(4.5 * progress + 1)))
                        file_access_count = max(10, int(np.random.normal(user_file_base + 65 * progress, 10.0)))
                        sensitive_file_access = max(0, int(np.random.poisson(8 * progress)))
                        email_count = max(2, int(np.random.normal(user_email_base - 3 * progress, 3.0)))
                        external_email_count = int(np.random.binomial(email_count, 0.10))
                        web_upload_volume = round(max(1.0, float(np.random.normal(user_upload_base + 45.0 * progress, 8.0))), 2)
                        # Sessions last substantially longer (e.g., overnight execution)
                        average_session_minutes = round(max(40.0, float(np.random.normal(user_session_base + 180.0 * progress, 25.0))), 1)

                    elif anomaly_type == "ip_leakage":
                        # USR-1038: High external emails, sensitive files accessed and transferred
                        login_count = max(2, int(np.random.normal(user_login_base + 2 * progress, 0.8)))
                        after_hours_login = int(np.random.poisson(1.2 * progress))
                        file_access_count = max(12, int(np.random.normal(user_file_base + 45 * progress, 8.0)))
                        sensitive_file_access = max(0, int(np.random.poisson(14 * progress)))
                        # Email volume and external ratio surge
                        email_count = max(10, int(np.random.normal(user_email_base + 35 * progress, 6.0)))
                        external_ratio = min(0.85, 0.15 + 0.65 * progress)
                        external_email_count = max(1, int(np.random.binomial(email_count, external_ratio)))
                        web_upload_volume = round(max(1.0, float(np.random.normal(user_upload_base + 35.0 * progress, 6.0))), 2)
                        average_session_minutes = round(max(30.0, float(np.random.normal(user_session_base + 50.0 * progress, 12.0))), 1)

            # Enforce clean bounds
            after_hours_login = min(after_hours_login, login_count)
            external_email_count = min(external_email_count, email_count)
            sensitive_file_access = min(sensitive_file_access, file_access_count)

            records.append({
                "user_id": user,
                "date": date_str,
                "login_count": int(login_count),
                "after_hours_login": int(after_hours_login),
                "file_access_count": int(file_access_count),
                "sensitive_file_access": int(sensitive_file_access),
                "email_count": int(email_count),
                "external_email_count": int(external_email_count),
                "web_upload_volume": round(float(web_upload_volume), 2),
                "average_session_minutes": round(float(average_session_minutes), 1),
            })

    # Create DataFrame with exact column order
    df = pd.DataFrame(records)
    column_order = [
        "user_id",
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
    df = df[column_order]

    # Ensure target directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    return df


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_csv = os.path.join(current_dir, "sample_data.csv")
    print(f"[*] Generating sample activity dataset -> {target_csv} ...")
    generated_df = generate_sample_data(num_users=40, num_days=45, output_path=target_csv)
    print(f"[+] Successfully generated {len(generated_df)} records.")
    print(f"[+] Unique users: {generated_df['user_id'].nunique()}")
    print(f"[+] Date range: {generated_df['date'].min()} to {generated_df['date'].max()}")
    print("\nSample records (first 5 rows):")
    print(generated_df.head(5).to_string(index=False))
