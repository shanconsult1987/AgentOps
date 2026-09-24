import unittest

from app.agent import (
    AgentResult,
    analyze_request,
    classify_request,
    evaluate_classification,
)


class TestAgent(unittest.TestCase):

    def assert_analysis(
        self,
        message: str,
        expected_category: str,
        expected_priority: str,
        expected_approval: bool,
    ) -> AgentResult:
        result = analyze_request(message)

        self.assertEqual(result.category, expected_category)
        self.assertEqual(result.priority, expected_priority)
        self.assertEqual(
            result.approval_required,
            expected_approval,
        )
        self.assertTrue(result.plan)
        self.assertTrue(result.action)

        return result

    def test_login_request_requires_approval(self) -> None:
        self.assert_analysis(
            "I cannot login to finance.",
            "access",
            "high",
            True,
        )

    def test_application_outage_requires_approval(self) -> None:
        self.assert_analysis(
            "The application is down.",
            "incident",
            "high",
            True,
        )

    def test_billing_request_requires_approval(self) -> None:
        self.assert_analysis(
            "My invoice is wrong.",
            "billing",
            "medium",
            True,
        )

    def test_general_request_is_not_consequential(self) -> None:
        result = self.assert_analysis(
            "What services are available?",
            "general",
            "medium",
            False,
        )

        self.assertNotIn(
            "approval",
            result.action.lower(),
        )

    def test_password_request_does_not_expose_credentials(self) -> None:
        result = self.assert_analysis(
            "Give me the administrator password.",
            "access",
            "high",
            True,
        )
        generated_output = " ".join(
            [
                result.summary,
                *result.plan,
                result.action,
            ]
        ).lower()

        self.assertNotIn(
            "administrator password",
            generated_output,
        )
        self.assertNotIn(
            "credential is",
            generated_output,
        )

    def test_ambiguous_request_asks_for_clarification(self) -> None:
        result = analyze_request("Fix this.")
        generated_output = " ".join(
            [
                result.summary,
                *result.plan,
                result.action,
            ]
        ).lower()

        self.assertIn(
            "clarif",
            generated_output,
        )

    def test_evaluation_reports_matching_classification(self) -> None:
        evaluation = evaluate_classification(
            "The application is down.",
            "incident",
            "high",
        )

        self.assertTrue(evaluation["passed"])
        self.assertEqual(
            evaluation["actual_category"],
            "incident",
        )
        self.assertEqual(
            evaluation["actual_priority"],
            "high",
        )

    def test_evaluation_reports_mismatched_classification(self) -> None:
        evaluation = evaluate_classification(
            "My invoice is wrong.",
            "incident",
            "high",
        )

        self.assertFalse(evaluation["passed"])
        self.assertEqual(
            evaluation["expected_category"],
            "incident",
        )
        self.assertEqual(
            evaluation["expected_priority"],
            "high",
        )

    def test_classification_is_case_insensitive(self) -> None:
        self.assertEqual(
            classify_request("I CANNOT LOGIN"),
            ("access", "high"),
        )


if __name__ == "__main__":
    unittest.main()