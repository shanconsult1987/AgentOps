import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.agent import (
    PLAN_VALIDATION_MODEL,
    AgentResult,
    PlanValidation,
    PlanValidationError,
    analyze_request,
    classify_request,
    evaluate_classification,
    validate_plan,
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

    def test_validate_plan_uses_structured_openai_response(
        self,
    ) -> None:
        result = analyze_request("I cannot login.")
        expected = PlanValidation(
            valid=True,
            summary="The plan preserves human approval.",
            concerns=[],
        )
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(
            output_parsed=expected,
        )

        validation = validate_plan(
            "I cannot login.",
            result,
            client=client,
        )

        self.assertEqual(validation, expected)
        call = client.responses.parse.call_args
        self.assertEqual(
            call.kwargs["model"],
            PLAN_VALIDATION_MODEL,
        )
        self.assertIs(
            call.kwargs["text_format"],
            PlanValidation,
        )
        self.assertIn(
            "cannot approve or execute",
            call.kwargs["instructions"],
        )
        payload = json.loads(call.kwargs["input"])
        self.assertEqual(
            payload["request"],
            "I cannot login.",
        )
        self.assertTrue(
            payload["analysis"]["approval_required"]
        )

    def test_validate_plan_raises_for_missing_structured_output(
        self,
    ) -> None:
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(
            output_parsed=None,
        )

        with self.assertRaisesRegex(
            PlanValidationError,
            "no structured result",
        ):
            validate_plan(
                "What services are available?",
                analyze_request(
                    "What services are available?"
                ),
                client=client,
            )

    def test_validate_plan_creates_default_openai_client(
        self,
    ) -> None:
        expected = PlanValidation(
            valid=False,
            summary="The plan needs revision.",
            concerns=["Missing validation step."],
        )
        client = Mock()
        client.responses.parse.return_value = SimpleNamespace(
            output_parsed=expected,
        )

        with patch(
            "app.agent.create_openai_client",
            return_value=client,
        ) as create_client:
            validation = validate_plan(
                "Fix this.",
                analyze_request("Fix this."),
            )

        create_client.assert_called_once_with()
        self.assertEqual(validation, expected)


if __name__ == "__main__":
    unittest.main()