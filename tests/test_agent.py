import unittest

from app.agent import (
    analyze_request,
    classify_request,
)


class TestAgent(unittest.TestCase):

    def test_access_request(self):
        category, priority = classify_request(
            "I cannot access finance"
        )

        self.assertEqual(category, "access")
        self.assertEqual(priority, "high")

    def test_billing_request(self):
        category, priority = classify_request(
            "My invoice is incorrect"
        )

        self.assertEqual(category, "billing")
        self.assertEqual(priority, "medium")

    def test_incident_request(self):
        category, priority = classify_request(
            "The application is down"
        )

        self.assertEqual(category, "incident")
        self.assertEqual(priority, "high")

    def test_general_request(self):
        category, priority = classify_request(
            "What services are available?"
        )

        self.assertEqual(category, "general")
        self.assertEqual(priority, "medium")

    def test_analysis(self):
        result = analyze_request(
            "I cannot login"
        )

        self.assertEqual(
            result.category,
            "access",
        )

        self.assertEqual(
            result.priority,
            "high",
        )


if __name__ == "__main__":
    unittest.main()