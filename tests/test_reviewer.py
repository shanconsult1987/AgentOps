import unittest

from app.reviewer import review_plan


class ReviewPlanTests(unittest.TestCase):

    def test_high_priority_consequential_action_requires_approval(
        self,
    ) -> None:
        result = review_plan(
            "access",
            "high",
            "Recommend an access change.",
        )

        self.assertEqual(result["decision"], "APPROVAL_REQUIRED")
        self.assertEqual(
            result["risks"],
            [
                "High-priority request.",
                "Consequential action.",
            ],
        )
        self.assertEqual(
            result["action"],
            "Recommend an access change.",
        )

    def test_medium_priority_consequential_action_requires_approval(
        self,
    ) -> None:
        result = review_plan(
            "billing",
            "medium",
            "Recommend a billing correction.",
        )

        self.assertEqual(result["decision"], "APPROVAL_REQUIRED")
        self.assertEqual(
            result["risks"],
            ["Consequential action."],
        )

    def test_high_priority_general_action_requires_approval(
        self,
    ) -> None:
        result = review_plan(
            "general",
            "high",
            "Provide an informational response.",
        )

        self.assertEqual(result["decision"], "APPROVAL_REQUIRED")
        self.assertEqual(
            result["risks"],
            ["High-priority request."],
        )

    def test_medium_priority_general_action_is_safe(self) -> None:
        result = review_plan(
            "general",
            "medium",
            "Provide an informational response.",
        )

        self.assertEqual(result["decision"], "SAFE_TO_EXECUTE")
        self.assertEqual(result["risks"], [])
        self.assertEqual(
            result["action"],
            "Provide an informational response.",
        )


if __name__ == "__main__":
    unittest.main()
