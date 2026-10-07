"""
Unit tests for user-day behavioral feature extraction.
"""

import unittest
import json
import os
import sys
import pandas as pd

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from ml.feature_engineering import (
    extract_behavior_features,
    REQUIRED_FEATURE_COLUMNS,
)

class FeatureEngineeringTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.sample_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv"))

    def test_extract_features_from_sample_csv(self):
        """Test feature extraction using the actual 1800-record sample dataset."""
        self.assertTrue(os.path.exists(self.sample_csv), "sample_data.csv must exist")

        feat_df = extract_behavior_features(self.sample_csv)

        # 1. Total record count & user count
        self.assertEqual(len(feat_df), 1800)
        self.assertEqual(feat_df["pseudonymous_user_id"].nunique(), 40)
        self.assertEqual(feat_df["date"].nunique(), 45)

        # 2. Exact column structure
        self.assertEqual(list(feat_df.columns), REQUIRED_FEATURE_COLUMNS)

        # 3. Chronological sorting
        for user, user_df in feat_df.groupby("pseudonymous_user_id"):
            dates = user_df["date"].tolist()
            self.assertEqual(dates, sorted(dates), f"Dates not chronological for {user}")

        # 4. Zero null values
        self.assertEqual(feat_df.isnull().sum().sum(), 0)

    def test_missing_values_and_imputation(self):
        """Test that missing/corrupted behavioral values are safely handled without crashes."""
        dirty_data = [
            {"user_id": "USR-1001", "date": "2026-09-01", "login_count": None, "file_access_count": 10},
            {"user_id": "USR-1001", "date": "2026-09-02", "login_count": 2, "web_upload_volume": None},
            {"user_id": "USR-1002", "date": "invalid-date-string", "login_count": 1},  # Should be dropped
            {"user_id": "USR-1002", "date": "2026-09-01", "login_count": "3"},
        ]

        feat_df = extract_behavior_features(dirty_data)

        self.assertEqual(len(feat_df), 3)  # Invalid date row safely dropped
        self.assertEqual(feat_df.isnull().sum().sum(), 0)
        # Verify USR-1001 on 2026-09-01 has 0 login_count imputed
        r1 = feat_df[(feat_df["pseudonymous_user_id"] == "USR-1001") & (feat_df["date"] == "2026-09-01")].iloc[0]
        self.assertEqual(r1["login_count"], 0)
        self.assertEqual(r1["file_access_count"], 10)

    def test_raw_id_automatic_pseudonymization(self):
        """Test that non-pseudonymous employee IDs (e.g. EMP001) are automatically pseudonymized."""
        raw_records = [
            {"user_id": "EMP001", "date": "2026-09-10", "login_count": 2, "file_access_count": 20},
            {"user_id": "EMP002", "date": "2026-09-10", "login_count": 1, "file_access_count": 12},
        ]

        feat_df = extract_behavior_features(raw_records)

        # Ensure raw IDs are NOT present in output
        self.assertNotIn("EMP001", feat_df["pseudonymous_user_id"].values)
        self.assertNotIn("EMP002", feat_df["pseudonymous_user_id"].values)

        # Ensure valid USR- pseudonyms generated
        for pid in feat_df["pseudonymous_user_id"]:
            self.assertTrue(pid.startswith("USR-"))

    def test_aggregation_of_multiple_events_same_day(self):
        """Test that multiple events for the same user and date are aggregated correctly."""
        multi_records = [
            {"user_id": "USR-1001", "date": "2026-09-05", "login_count": 1, "file_access_count": 10, "web_upload_volume": 2.5, "average_session_minutes": 30.0},
            {"user_id": "USR-1001", "date": "2026-09-05", "login_count": 2, "file_access_count": 15, "web_upload_volume": 4.5, "average_session_minutes": 50.0},
        ]

        feat_df = extract_behavior_features(multi_records)

        self.assertEqual(len(feat_df), 1)  # Aggregated into one user-day record
        row = feat_df.iloc[0]
        self.assertEqual(row["login_count"], 3)  # 1 + 2
        self.assertEqual(row["file_access_count"], 25)  # 10 + 15
        self.assertEqual(row["web_upload_volume"], 7.0)  # 2.5 + 4.5
        self.assertEqual(row["average_session_minutes"], 40.0)  # Mean of (30, 50)

    def test_api_extract_features_endpoint(self):
        """Test POST /api/features/extract endpoint."""
        response = self.client.post("/api/features/extract", json={"sync_to_db": False})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["number_of_users"], 40)
        self.assertEqual(data["number_of_user_day_records"], 1800)
        self.assertIn("feature_dataframe_preview", data)
        self.assertEqual(len(data["feature_dataframe_preview"]), 15)
        self.assertEqual(data["columns"], REQUIRED_FEATURE_COLUMNS)

if __name__ == "__main__":
    unittest.main()
