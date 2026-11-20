import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as trustguard


class TrustGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db = trustguard.DB_PATH
        trustguard.DB_PATH = Path(self.temp_dir.name) / "test.db"
        trustguard.init_db()
        self.client = trustguard.app.test_client()

    def tearDown(self):
        trustguard.DB_PATH = self.original_db
        self.temp_dir.cleanup()

    def test_payment_and_sensitive_info_indicators(self):
        text = "Pay ₹999 registration fee now and send your OTP to confirm this job offer."
        found = trustguard.indicators_for(text)
        self.assertIn("Upfront payment request", found)
        self.assertIn("Sensitive information request", found)

    def test_suspicious_link_indicator(self):
        self.assertIn("Suspicious link or domain", trustguard.indicators_for("Apply now at https://bit.ly/example"))

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TRUSTGUARD", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["version"], "2.0.0")

    def test_short_message_rejected(self):
        response = self.client.post("/analyze", data={"message": "Too short"})
        self.assertEqual(response.status_code, 400)

    def test_analysis_saved_and_csv_exported(self):
        fake_result = {
            "prediction": "Potentially suspicious patterns found", "probability": 91.2,
            "risk_score": 88, "risk_level": "High", "indicators": ["Upfront payment request"],
            "warning_details": [trustguard.WARNING_GUIDE["Upfront payment request"]],
            "advice_en": "Pause and verify.", "advice_ta": "சரிபார்க்கவும்.",
            "model_probability": 91.2, "rule_signal_count": 1
        }
        with patch.object(trustguard, "analyse_message", return_value=fake_result):
            response = self.client.post("/analyze", data={"message": "Please pay ₹999 registration fee before joining this job."})
        self.assertEqual(response.status_code, 200)
        dashboard = self.client.get("/dashboard")
        self.assertIn(b"Analysis dashboard", dashboard.data)
        export = self.client.get("/export.csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn(b"Risk level", export.data)


if __name__ == "__main__":
    unittest.main()
