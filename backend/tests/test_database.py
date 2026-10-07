"""
Unit tests for MySQL database configuration, models, and health endpoints.
"""

import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database import db, test_connection
from config import Config
from models import (
    User,
    ActivityLog,
    BehaviorFeature,
    AnomalyResult,
    RiskScore,
    RiskExplanation,
    AnalysisRun,
    Setting,
)

class DatabaseLayerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_all_models_registered(self):
        """Verify that all 8 required domain models are defined with correct table names."""
        expected_tables = {
            "users",
            "activity_logs",
            "behavior_features",
            "anomaly_results",
            "risk_scores",
            "risk_explanations",
            "analysis_runs",
            "settings",
        }
        registered_tables = set(db.metadata.tables.keys())
        for table in expected_tables:
            self.assertIn(table, registered_tables, f"Missing required table: {table}")

    def test_user_model_fields(self):
        """Verify User model has required privacy fields."""
        table = db.metadata.tables["users"]
        column_names = {c.name for c in table.columns}
        self.assertIn("id", column_names)
        self.assertIn("pseudonymous_id", column_names)
        self.assertIn("original_id_hash", column_names)
        self.assertIn("created_at", column_names)

    def test_activity_log_model_fields(self):
        """Verify ActivityLog model schema."""
        table = db.metadata.tables["activity_logs"]
        column_names = {c.name for c in table.columns}
        self.assertIn("id", column_names)
        self.assertIn("user_id", column_names)
        self.assertIn("activity_date", column_names)
        self.assertIn("activity_data", column_names)
        self.assertIn("created_at", column_names)

    def test_behavior_features_model_fields(self):
        """Verify BehaviorFeature model contains all specified behavioral metrics."""
        table = db.metadata.tables["behavior_features"]
        column_names = {c.name for c in table.columns}
        required_fields = {
            "id", "user_id", "activity_date", "login_count", "after_hours_login",
            "file_access_count", "sensitive_file_access", "email_count",
            "external_email_count", "web_upload_volume", "average_session_minutes"
        }
        for field in required_fields:
            self.assertIn(field, column_names, f"BehaviorFeature missing {field}")

    def test_anomaly_results_model_fields(self):
        """Verify AnomalyResult model schema."""
        table = db.metadata.tables["anomaly_results"]
        column_names = {c.name for c in table.columns}
        for field in ["id", "user_id", "activity_date", "anomaly_score", "anomaly_flag"]:
            self.assertIn(field, column_names)

    def test_risk_scores_model_fields(self):
        """Verify RiskScore model schema."""
        table = db.metadata.tables["risk_scores"]
        column_names = {c.name for c in table.columns}
        for field in ["id", "user_id", "activity_date", "risk_score", "risk_level"]:
            self.assertIn(field, column_names)

    def test_risk_explanations_model_fields(self):
        """Verify RiskExplanation model schema."""
        table = db.metadata.tables["risk_explanations"]
        column_names = {c.name for c in table.columns}
        for field in ["id", "user_id", "activity_date", "feature", "contribution", "direction"]:
            self.assertIn(field, column_names)

    def test_analysis_runs_model_fields(self):
        """Verify AnalysisRun model schema."""
        table = db.metadata.tables["analysis_runs"]
        column_names = {c.name for c in table.columns}
        for field in ["id", "filename", "record_count", "user_count", "parameters", "created_at"]:
            self.assertIn(field, column_names)

    def test_settings_model_fields(self):
        """Verify Setting model schema."""
        table = db.metadata.tables["settings"]
        column_names = {c.name for c in table.columns}
        for field in ["id", "alpha", "contamination", "risk_decay", "risk_gain"]:
            self.assertIn(field, column_names)

    def test_connection_testing_mechanism(self):
        """Verify test_connection returns structured dict and does not raise uncaught errors."""
        with self.app.app_context():
            result = test_connection()
            self.assertIsInstance(result, dict)
            self.assertIn("connected", result)
            self.assertIn("status", result)
            self.assertIn("message", result)

    def test_database_status_endpoint(self):
        """Verify GET /api/database/status returns diagnostic details."""
        response = self.client.get("/api/database/status")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("connected", data)
        self.assertIn("status", data)
        self.assertIn("connection_details", data)
        self.assertEqual(data["connection_details"]["dialect"], "mysql")
        self.assertEqual(data["connection_details"]["driver"], "pymysql")
        self.assertIn("defined_models", data)
        self.assertEqual(len(data["defined_models"]), 8)

    def test_database_schema_endpoint(self):
        """Verify GET /api/database/schema returns metadata for all 8 tables."""
        response = self.client.get("/api/database/schema")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["total_tables"], 8)
        self.assertIn("users", data["tables"])
        self.assertIn("activity_logs", data["tables"])
        self.assertIn("behavior_features", data["tables"])


if __name__ == "__main__":
    unittest.main()
