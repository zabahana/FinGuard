import unittest

try:
    from fastapi.testclient import TestClient
    from finguard.api import app
except ImportError:
    TestClient = None


@unittest.skipIf(TestClient is None, "Install .[api] and httpx to test the optional API")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_scoped_reads(self):
        self.assertTrue(self.client.get("/health").json()["synthetic"])
        response = self.client.get("/api/transaction-history", params={"customer_id": "C10452"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(t["customer_id"] == "C10452" for t in response.json()))
        self.assertEqual(self.client.get("/api/risk-score", params={"customer_id": "C20813"}).status_code, 403)

    def test_sensitive_notes_denied(self):
        response = self.client.post("/api/case-management", json={"customer_id": "C10452", "text": "SSN 000-00-1045"})
        self.assertEqual(response.status_code, 403)

    def test_clean_note_validated_without_persistence(self):
        response = self.client.post("/api/case-management", json={"customer_id": "C10452", "text": "Review TX002"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["persisted"])

    def test_unavailable_mutation_and_invalid_input(self):
        self.assertEqual(self.client.post("/api/wire-transfer").status_code, 404)
        self.assertEqual(self.client.post("/api/risk-score").status_code, 405)
        self.assertEqual(self.client.post("/api/case-management", json={"customer_id": "C10452", "text": ""}).status_code, 422)
