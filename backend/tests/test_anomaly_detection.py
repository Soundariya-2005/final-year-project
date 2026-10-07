"""
Unit tests for Isolation Forest anomaly detection engine.
"""

import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from ml.anomaly_detection import (
    detect_anomalies,
    get_anomaly_summary,
    DEFAULT_CONTAMINATION,
    BEHAVIORAL_FEATURES,
)

class AnomalyDetectionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.sample_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv"))

    def test_isolation_forest_execution_on_dataset(self):
        """Verify Isolation Forest runs on actual 1800 records with contamination=0.07."""
        self.assertTrue(os.path.exists(self.sample_csv))

        results_df, model = detect_anomalies(self.sample_csv, contamination=DEFAULT_CONTAMINATION)

        self.assertIsNotNone(model)
        self.assertEqual(len(results_df), 1800)
        self.assertIn("anomaly_score", results_df.columns)
        self.assertIn("anomaly_flag", results_df.columns)
        self.assertIn("prediction", results_df.columns)

        summary = get_anomaly_summary(results_df)
        self.assertEqual(summary["total_records"], 1800)
        # Expected ~7% anomalies (around 126 records)
        self.assertAlmostEqual(summary["percentage_anomalous"], 7.0, delta=1.0)
        self.assertGreater(summary["anomaly_count"], 100)

        # Anomaly scores must be within [0.0, 1.0]
        self.assertTrue((results_df["anomaly_score"] >= 0.0).all())
        self.assertTrue((results_df["anomaly_score"] <= 1.0).all())

    def test_pseudonymous_ids_and_dates_preserved(self):
        """Verify pseudonymous IDs and dates are preserved throughout anomaly detection."""
        results_df, _ = detect_anomalies(self.sample_csv, contamination=DEFAULT_CONTAMINATION)
        self.assertIn("pseudonymous_user_id", results_df.columns)
        self.assertIn("date", results_df.columns)
        self.assertEqual(results_df["pseudonymous_user_id"].nunique(), 40)

if __name__ == "__main__":
    unittest.main()
