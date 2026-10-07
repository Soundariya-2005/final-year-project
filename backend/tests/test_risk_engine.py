"""
Unit tests for Progressive Risk Engine.
"""

import unittest
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from ml.risk_engine import (
    calculate_progressive_risk,
    classify_risk_level,
    DEFAULT_RISK_DECAY,
    DEFAULT_RISK_GAIN,
)

class RiskEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")

    def test_progressive_risk_formula_and_decay(self):
        """Verify: risk(t) = decay * risk(t-1) + gain * anomaly(t)."""
        decay = 0.88
        gain = 0.13

        # Scenario: Day 0 normal, Day 1 anomaly, Day 2 normal (decay)
        synthetic_anomalies = [
            {"user_id": "USR-TEST", "date": "2026-09-01", "anomaly_flag": False, "anomaly_score": 0.0},
            {"user_id": "USR-TEST", "date": "2026-09-02", "anomaly_flag": True, "anomaly_score": 1.0},
            {"user_id": "USR-TEST", "date": "2026-09-03", "anomaly_flag": False, "anomaly_score": 0.0},
        ]

        risk_df = calculate_progressive_risk(synthetic_anomalies, decay=decay, gain=gain)

        # Day 0: 0.0 -> LOW
        self.assertEqual(risk_df.iloc[0]["risk_score"], 0.0)
        self.assertEqual(risk_df.iloc[0]["risk_level"], "LOW")

        # Day 1: Single anomaly impulse = 100 * 0.13 = 13.0 -> LOW
        # (Isolated anomaly does NOT jump to CRITICAL)
        d1 = risk_df.iloc[1]
        self.assertAlmostEqual(d1["risk_score"], 13.0, places=1)
        self.assertEqual(d1["risk_level"], "LOW")

        # Day 2: Decays by 0.88: 13.0 * 0.88 = 11.44 -> LOW
        d2 = risk_df.iloc[2]
        self.assertAlmostEqual(d2["risk_score"], 11.44, places=1)
        self.assertEqual(d2["risk_level"], "LOW")

    def test_repeated_anomalies_accumulate(self):
        """Verify repeated anomalies accumulate into HIGH and CRITICAL."""
        # 10 consecutive anomalous days
        streak = [
            {"user_id": "USR-ANOM", "date": f"2026-09-{i+1:02d}", "anomaly_flag": True, "anomaly_score": 1.0}
            for i in range(12)
        ]
        risk_df = calculate_progressive_risk(streak, decay=0.88, gain=0.13)

        # Risk must strictly increase across consecutive anomaly days
        scores = risk_df["risk_score"].tolist()
        self.assertTrue(all(scores[i] < scores[i+1] for i in range(len(scores)-1)))
        # Eventually breaches CRITICAL (>= 75)
        self.assertGreaterEqual(scores[-1], 75.0)
        self.assertEqual(risk_df.iloc[-1]["risk_level"], "CRITICAL")

    def test_risk_level_thresholds(self):
        """Verify risk tier classifications."""
        self.assertEqual(classify_risk_level(10.0), "LOW")
        self.assertEqual(classify_risk_level(30.0), "MEDIUM")
        self.assertEqual(classify_risk_level(60.0), "HIGH")
        self.assertEqual(classify_risk_level(85.0), "CRITICAL")

if __name__ == "__main__":
    unittest.main()
