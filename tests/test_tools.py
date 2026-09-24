import unittest
from datetime import datetime

from app.tools import execute_action


class ExecuteActionTests(unittest.TestCase):

    def test_unapproved_action_is_blocked(self) -> None:
        result = execute_action("access", approved=False)

        self.assertFalse(result["success"])
        self.assertEqual(
            result["message"],
            "Action blocked because approval has not been granted.",
        )
        self.assertNotIn("executed_at", result)

    def test_approved_action_is_recorded(self) -> None:
        result = execute_action("incident", approved=True)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "Incident remediation recommendation recorded.",
        )
        datetime.fromisoformat(result["executed_at"])

    def test_unknown_approved_action_has_no_available_action(
        self,
    ) -> None:
        result = execute_action("unknown", approved=True)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "No action available.",
        )


if __name__ == "__main__":
    unittest.main()
