"""
Unit tests for the sample activity-log data generator and API endpoints.
"""

import unittest
import json
import os
import sys
import pandas as pd

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from data.sample_data import generate_sample_data

class SampleDataGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.test_csv_path = "/tmp/test_sample_data.csv"

    def tearDown(self):
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)

    def test_sample_data_generator_output(self):
        """Test that generator produces exactly 40 users, 45 days, and 1800 records."""
        df = generate_sample_data(num_users=40, num_days=45, output_path=self.test_csv_path, seed=42)
        
        self.assertEqual(len(df), 1800)
        self.assertEqual(df["user_id"].nunique(), 40)
        self.assertEqual(df["date"].nunique(), 45)

        # Verify all 10 required behavioral fields are present
        expected_columns = [
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
        self.assertEqual(list(df.columns), expected_columns)

        # Verify NO anomaly labels or fake classifications exist in columns
        forbidden_keywords = ["label", "anomaly", "malicious", "threat", "risk", "flag", "score"]
        for col in df.columns:
            for kw in forbidden_keywords:
                self.assertNotIn(kw, col.lower(), f"Unexpected label column found: {col}")

        # Check numeric ranges and bounds
        self.assertTrue((df["after_hours_login"] <= df["login_count"]).all())
        self.assertTrue((df["external_email_count"] <= df["email_count"]).all())
        self.assertTrue((df["sensitive_file_access"] <= df["file_access_count"]).all())
        self.assertTrue((df["web_upload_volume"] >= 0).all())
        self.assertTrue((df["average_session_minutes"] >= 0).all())

    def test_pandas_can_read_generated_csv(self):
        """Test that generated CSV can be cleanly parsed by pandas without missing values."""
        generate_sample_data(num_users=40, num_days=45, output_path=self.test_csv_path, seed=42)
        
        self.assertTrue(os.path.exists(self.test_csv_path))
        df = pd.read_csv(self.test_csv_path)
        self.assertEqual(df.shape, (1800, 10))
        self.assertEqual(df.isnull().sum().sum(), 0)

    def test_api_generate_sample_post(self):
        """Test POST /api/generate-sample returns expected JSON structure."""
        response = self.client.post("/api/generate-sample", json={"num_users": 40, "num_days": 45})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["number_of_records"], 1800)
        self.assertEqual(data["number_of_users"], 40)
        self.assertIn("date_range", data)
        self.assertEqual(data["date_range"]["total_days"], 45)
        self.assertIn("file_location", data)
        self.assertIn("sample_preview", data)
        self.assertEqual(len(data["sample_preview"]), 10)

    def test_api_sample_preview_get(self):
        """Test GET /api/sample-data/preview returns paginated records."""
        response = self.client.get("/api/sample-data/preview?limit=5")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["records"]), 5)
        self.assertIn("unique_users", data)
        self.assertEqual(len(data["unique_users"]), 40)

if __name__ == "__main__":
    unittest.main()
