"""
Unit tests for Adaptive User Profiling:
1. Exact mathematical formula verification (EWMA: (1 - alpha) * base(t-1) + alpha * x(t))
2. User baseline isolation
3. Chronological ordering
4. All 8 behavioral features tracked
5. Customizable alpha
6. REST API endpoints
"""

import unittest
import json
import os
import sys
import pandas as pd

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from ml.adaptive_profile import (
    calculate_adaptive_profile,
    get_user_profile_summary,
    DEFAULT_ALPHA,
    BEHAVIORAL_FEATURES,
)

class AdaptiveProfileTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.sample_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv"))

    def test_adaptive_ewma_mathematical_formula(self):
        """Verify the exact formula: baseline(t) = (1 - alpha) * baseline(t-1) + alpha * x(t)."""
        alpha = 0.15
        simple_test_data = [
            {"user_id": "USR-TEST", "date": "2026-09-01", "file_access_count": 10},
            {"user_id": "USR-TEST", "date": "2026-09-02", "file_access_count": 20},
            {"user_id": "USR-TEST", "date": "2026-09-03", "file_access_count": 20},
        ]

        prof_df = calculate_adaptive_profile(simple_test_data, alpha=alpha)
        self.assertEqual(len(prof_df), 3)

        # Day 0: baseline(0) = 10, deviation(0) = 0
        r0 = prof_df.iloc[0]
        self.assertEqual(r0["file_access_count"], 10.0)
        self.assertEqual(r0["file_access_count_baseline"], 10.0)
        self.assertEqual(r0["file_access_count_deviation"], 0.0)

        # Day 1:
        # deviation(1) = x(1) - baseline(0) = 20 - 10 = +10.0
        # baseline(1)  = (1 - 0.15) * 10 + 0.15 * 20 = 8.5 + 3.0 = 11.5
        r1 = prof_df.iloc[1]
        self.assertEqual(r1["file_access_count"], 20.0)
        self.assertAlmostEqual(r1["file_access_count_deviation"], 10.0, places=2)
        self.assertAlmostEqual(r1["file_access_count_baseline"], 11.5, places=2)

        # Day 2:
        # deviation(2) = x(2) - baseline(1) = 20 - 11.5 = +8.5
        # baseline(2)  = (0.85 * 11.5) + (0.15 * 20) = 9.775 + 3.0 = 12.78
        r2 = prof_df.iloc[2]
        self.assertEqual(r2["file_access_count"], 20.0)
        self.assertAlmostEqual(r2["file_access_count_deviation"], 8.5, places=2)
        self.assertAlmostEqual(r2["file_access_count_baseline"], 12.78, places=2)

    def test_user_baseline_isolation(self):
        """Verify that each user's baseline is tracked independently without cross-talk."""
        multi_user_data = [
            {"user_id": "USR-A", "date": "2026-09-01", "web_upload_volume": 10.0},
            {"user_id": "USR-B", "date": "2026-09-01", "web_upload_volume": 500.0},
            {"user_id": "USR-A", "date": "2026-09-02", "web_upload_volume": 10.0},
            {"user_id": "USR-B", "date": "2026-09-02", "web_upload_volume": 500.0},
        ]

        prof_df = calculate_adaptive_profile(multi_user_data, alpha=0.15)

        user_a = prof_df[prof_df["pseudonymous_user_id"] == "USR-A"].iloc[1]
        user_b = prof_df[prof_df["pseudonymous_user_id"] == "USR-B"].iloc[1]

        # USR-A's baseline should remain near 10.0, completely unaffected by USR-B's 500.0
        self.assertAlmostEqual(user_a["web_upload_volume_baseline"], 10.0, places=1)
        self.assertAlmostEqual(user_b["web_upload_volume_baseline"], 500.0, places=1)

    def test_full_dataset_execution(self):
        """Test profiling on sample_data.csv with all 8 features."""
        prof_df = calculate_adaptive_profile(self.sample_csv, alpha=DEFAULT_ALPHA)

        self.assertEqual(len(prof_df), 1800)
        self.assertEqual(prof_df["pseudonymous_user_id"].nunique(), 40)

        # Check that baseline and deviation exist for all 8 features
        for f in BEHAVIORAL_FEATURES:
            self.assertIn(f, prof_df.columns)
            self.assertIn(f"{f}_baseline", prof_df.columns)
            self.assertIn(f"{f}_deviation", prof_df.columns)

    def test_configurable_alpha(self):
        """Verify that changing alpha modulates the adaptation rate."""
        data = [
            {"user_id": "USR-TEST", "date": "2026-09-01", "login_count": 2},
            {"user_id": "USR-TEST", "date": "2026-09-02", "login_count": 10},
        ]

        # Low alpha = 0.05 (slow adaptation)
        df_low = calculate_adaptive_profile(data, alpha=0.05)
        # High alpha = 0.50 (fast adaptation)
        df_high = calculate_adaptive_profile(data, alpha=0.50)

        base_low = df_low.iloc[1]["login_count_baseline"]   # (0.95 * 2) + (0.05 * 10) = 1.9 + 0.5 = 2.4
        base_high = df_high.iloc[1]["login_count_baseline"] # (0.50 * 2) + (0.50 * 10) = 1.0 + 5.0 = 6.0

        self.assertAlmostEqual(base_low, 2.4, places=2)
        self.assertAlmostEqual(base_high, 6.0, places=2)
        self.assertLess(base_low, base_high)

    def test_api_adaptive_profile_endpoint(self):
        """Test POST /api/profile/adaptive returns proper JSON structure."""
        response = self.client.post("/api/profile/adaptive", json={"alpha": 0.15, "limit": 10})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["alpha_used"], 0.15)
        self.assertEqual(data["total_users"], 40)
        self.assertEqual(len(data["records"]), 10)
        self.assertIn("demo_summary", data)

    def test_api_single_user_endpoint(self):
        """Test GET /api/profile/user/<user_id> endpoint."""
        response = self.client.get("/api/profile/user/USR-1001?alpha=0.15")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_summary"]["user_id"], "USR-1001")
        self.assertEqual(len(data["user_summary"]["daily_progression"]), 45)

if __name__ == "__main__":
    unittest.main()
