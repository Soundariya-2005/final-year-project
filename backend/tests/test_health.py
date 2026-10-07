import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

class HealthEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_health_endpoint_status(self):
        """Test GET /api/health returns HTTP 200 with status ok."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)
        self.assertIn("version", data)
        self.assertIn("timestamp", data)

    def test_direct_health_endpoint(self):
        """Test GET /health alias returns HTTP 200."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")

if __name__ == "__main__":
    unittest.main()
