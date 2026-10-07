"""
Unit tests for the end-to-end 11-stage analysis pipeline and Dashboard APIs.
"""

import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.pipeline import execute_analysis_pipeline, get_pipeline_state


class PipelineAndDashboardAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.sample_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv"))

    def test_complete_analysis_pipeline(self):
        """Tests the end-to-end pipeline execution from CSV to SHAP and API response."""
        res = execute_analysis_pipeline(
            self.sample_csv,
            alpha=0.15,
            contamination=0.07,
            risk_decay=0.88,
            risk_gain=0.13,
            filename="sample_data.csv",
            sync_to_db=False,
        )
        self.assertEqual(res["analysis_status"], "completed")
        self.assertTrue(res["analysis_run_id"].startswith("RUN-"))
        self.assertEqual(res["number_of_records"], 1800)
        self.assertEqual(res["number_of_users"], 40)
        self.assertGreater(res["number_of_anomalies"], 0)
        self.assertIn("date_range", res)
        self.assertEqual(len(res["pipeline_stages"]), 12)

    def test_post_analyze_endpoint(self):
        """Tests POST /api/analyze."""
        response = self.client.post(
            "/api/analyze",
            data=json.dumps({"alpha": 0.15, "contamination": 0.07, "risk_decay": 0.88, "risk_gain": 0.13}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["analysis_status"], "completed")
        self.assertEqual(data["number_of_users"], 40)
        self.assertEqual(data["number_of_records"], 1800)

    def test_dashboard_summary_endpoint(self):
        """Tests GET /api/dashboard-summary."""
        response = self.client.get("/api/dashboard-summary")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_users"], 40)
        self.assertEqual(data["activity_records"], 1800)
        self.assertIn("high_risk_users", data)
        self.assertIn("critical_risk_users", data)
        self.assertIn("total_anomalies", data)
        self.assertIn("risk_level_distribution", data)

    def test_users_list_endpoint(self):
        """Tests GET /api/users."""
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_users"], 40)
        first_user = data["users"][0]
        self.assertIn("pseudonymous_id", first_user)
        self.assertIn("latest_risk_score", first_user)
        self.assertIn("latest_risk_level", first_user)
        self.assertIn("anomaly_count", first_user)
        self.assertIn("last_activity_date", first_user)

    def test_user_detail_and_risk_trend_endpoints(self):
        """Tests GET /api/users/<pseudonymous_id> and GET /api/users/<pseudonymous_id>/risk-trend."""
        users_resp = self.client.get("/api/users")
        first_uid = json.loads(users_resp.data)["users"][0]["pseudonymous_id"]

        detail_resp = self.client.get(f"/api/users/{first_uid}")
        self.assertEqual(detail_resp.status_code, 200)
        detail = json.loads(detail_resp.data)
        self.assertEqual(detail["pseudonymous_id"], first_uid)
        self.assertIn("current_risk", detail)
        self.assertIn("risk_level", detail)
        self.assertIn("risk_history", detail)
        self.assertIn("behavioral_summary", detail)
        self.assertIn("top_shap_factors", detail)

        trend_resp = self.client.get(f"/api/users/{first_uid}/risk-trend")
        self.assertEqual(trend_resp.status_code, 200)
        trend = json.loads(trend_resp.data)
        self.assertEqual(trend["pseudonymous_id"], first_uid)
        self.assertTrue(len(trend["trend"]) > 0)

    def test_alerts_and_runs_endpoints(self):
        """Tests GET /api/alerts and GET /api/analysis-runs."""
        alerts_resp = self.client.get("/api/alerts")
        self.assertEqual(alerts_resp.status_code, 200)
        alerts = json.loads(alerts_resp.data)
        self.assertIn("total_alerts", alerts)
        self.assertIn("critical_count", alerts)
        self.assertIn("high_count", alerts)

        runs_resp = self.client.get("/api/analysis-runs")
        self.assertEqual(runs_resp.status_code, 200)
        runs = json.loads(runs_resp.data)
        self.assertIn("total_runs", runs)


if __name__ == "__main__":
    unittest.main()
