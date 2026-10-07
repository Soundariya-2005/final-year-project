"""
Unit tests for SHAP Explainability Engine and API.
"""

import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from ml.anomaly_detection import detect_anomalies
from ml.explainability import (
    explain_anomalies_shap,
    get_user_explanations,
    BEHAVIORAL_FEATURES,
)

class ExplainabilityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.sample_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv"))

    def test_shap_tree_explainer_computations(self):
        """Verify SHAP produces non-trivial feature attributions for all 8 behavioral features."""
        anom_df, model = detect_anomalies(self.sample_csv, contamination=0.07)
        expl_df, summary = explain_anomalies_shap(anom_df, model=model)

        self.assertFalse(expl_df.empty)
        self.assertEqual(summary["total_records_explained"], 1800)
        self.assertEqual(len(summary["global_feature_importance"]), 8)

        # Ensure all 8 features are evaluated
        evaluated_features = set(expl_df["feature"].unique())
        self.assertEqual(evaluated_features, set(BEHAVIORAL_FEATURES))

        # Check required columns
        for col in ["pseudonymous_user_id", "date", "feature", "shap_value", "contribution", "direction"]:
            self.assertIn(col, expl_df.columns)

    def test_api_user_explanations_endpoint(self):
        """Verify GET /api/users/<pseudonymous_id>/explanations returns top drivers."""
        response = self.client.get("/api/users/USR-1012/explanations")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_id"], "USR-1012")
        self.assertIn("explanation", data)
        self.assertIn("top_features_overall", data["explanation"])
        self.assertIn("features_increasing_anomaly", data["explanation"])
        self.assertIn("features_decreasing_anomaly", data["explanation"])

if __name__ == "__main__":
    unittest.main()
