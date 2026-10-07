"""
Unit tests for the Privacy-Preserving Layer:
1. Deterministic Pseudonymization (EMP001 -> same ID every time; EMP002 -> distinct ID)
2. Data Minimization
3. Non-exposure of original ID in normal API responses
4. Controlled authorized lookup mechanism
"""

import unittest
import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from privacy.pseudonymization import (
    pseudonymize_user_id,
    hash_original_id,
    identity_vault,
    apply_data_minimization,
    ControlledIdentityVault,
    ADMIN_KEY,
)

class PrivacyPreservingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.vault = ControlledIdentityVault()

    def test_deterministic_pseudonymization_same_id(self):
        """Verify that EMP001 produces the exact same pseudonymous ID every time."""
        id_run1 = pseudonymize_user_id("EMP001")
        id_run2 = pseudonymize_user_id("EMP001")
        id_run3 = pseudonymize_user_id("EMP001")

        self.assertEqual(id_run1, id_run2)
        self.assertEqual(id_run2, id_run3)
        self.assertTrue(id_run1.startswith("USR-"))
        self.assertEqual(len(id_run1), 10)  # "USR-" (4) + 6 hex chars = 10 chars

    def test_distinct_pseudonymization_different_ids(self):
        """Verify that EMP001 and EMP002 produce different pseudonymous IDs."""
        id_emp1 = pseudonymize_user_id("EMP001")
        id_emp2 = pseudonymize_user_id("EMP002")

        self.assertNotEqual(id_emp1, id_emp2)
        self.assertTrue(id_emp1.startswith("USR-"))
        self.assertTrue(id_emp2.startswith("USR-"))

    def test_sha256_hash_original_id(self):
        """Verify hash_original_id produces valid 64-char hex SHA-256 digest."""
        digest = hash_original_id("EMP001")
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, hash_original_id("EMP001"))

    def test_controlled_identity_vault_registration_and_lookup(self):
        """Verify authorized lookup succeeds only with valid compliance credentials."""
        reg_meta = self.vault.register_user("EMP001")
        p_id = reg_meta["pseudonymous_id"]

        # 1. Unauthorized attempt (no token) must fail
        with self.assertRaises(PermissionError):
            self.vault.authorized_lookup(p_id, auth_token=None)

        # 2. Unauthorized attempt (wrong token) must fail
        with self.assertRaises(PermissionError):
            self.vault.authorized_lookup(p_id, auth_token="invalid-token-12345")

        # 3. Authorized attempt with valid admin token succeeds
        auth_record = self.vault.authorized_lookup(p_id, auth_token=ADMIN_KEY)
        self.assertEqual(auth_record["pseudonymous_id"], p_id)
        self.assertEqual(auth_record["original_id"], "EMP001")
        self.assertTrue(auth_record["access_granted"])

    def test_data_minimization_function(self):
        """Verify data minimization pseudonymizes user_id and strips sensitive personal keys."""
        raw_record = {
            "user_id": "EMP001",
            "name": "Alice Smith",
            "full_name": "Alice Jane Smith",
            "ssn": "123-45-6789",
            "login_count": 3,
            "web_upload_volume": 4.5,
        }

        minimized = apply_data_minimization(raw_record)

        self.assertNotEqual(minimized["user_id"], "EMP001")
        self.assertTrue(minimized["user_id"].startswith("USR-"))
        self.assertNotIn("name", minimized)
        self.assertNotIn("full_name", minimized)
        self.assertNotIn("ssn", minimized)
        self.assertEqual(minimized["login_count"], 3)
        self.assertEqual(minimized["web_upload_volume"], 4.5)

    def test_normal_api_responses_do_not_expose_original_id(self):
        """CRITICAL: Verify normal API endpoints do NOT expose original employee ID."""
        # Call POST /api/privacy/pseudonymize
        response = self.client.post("/api/privacy/pseudonymize", json={"original_id": "EMP001"})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn("pseudonymous_id", data)
        self.assertIn("original_id_hash", data)

        # Ensure "EMP001" is nowhere in the returned JSON body
        raw_response_text = response.data.decode("utf-8")
        self.assertNotIn("EMP001", raw_response_text, "Original ID leaked in normal API response!")

        # Call GET /api/privacy/users
        users_resp = self.client.get("/api/privacy/users")
        self.assertEqual(users_resp.status_code, 200)
        users_text = users_resp.data.decode("utf-8")
        self.assertNotIn("EMP001", users_text, "Original ID leaked in public users list!")

    def test_api_controlled_lookup_access_control(self):
        """Verify API lookup endpoint enforces 403 Forbidden on unauthorized requests."""
        # First register user
        reg_resp = self.client.post("/api/privacy/pseudonymize", json={"original_id": "EMP005"})
        p_id = json.loads(reg_resp.data)["pseudonymous_id"]

        # 1. Attempt lookup without token -> 403 Forbidden
        unauth_resp = self.client.post("/api/privacy/lookup", json={"pseudonymous_id": p_id})
        self.assertEqual(unauth_resp.status_code, 403)
        unauth_data = json.loads(unauth_resp.data)
        self.assertFalse(unauth_data["access_granted"])
        self.assertNotIn("EMP005", unauth_resp.data.decode("utf-8"))

        # 2. Attempt lookup with correct token -> 200 OK
        auth_resp = self.client.post("/api/privacy/lookup", json={
            "pseudonymous_id": p_id,
            "auth_token": ADMIN_KEY
        })
        self.assertEqual(auth_resp.status_code, 200)
        auth_data = json.loads(auth_resp.data)
        self.assertEqual(auth_data["record"]["original_id"], "EMP005")

if __name__ == "__main__":
    unittest.main()
