import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


APP_DIRECTORY = str(
    Path(__file__).resolve().parents[1] / "app"
)
if APP_DIRECTORY not in sys.path:
    sys.path.insert(0, APP_DIRECTORY)

app_module = importlib.import_module("app.app")


class AppRouteTests(unittest.TestCase):

    def setUp(self) -> None:
        app_module.app.config.update(
            TESTING=True,
        )
        self.client = app_module.app.test_client()

    def test_dashboard_renders_requests_and_metrics(self) -> None:
        requests = [
            self.make_request(
                request_id=1,
                priority="high",
                status="AWAITING_APPROVAL",
            ),
            self.make_request(
                request_id=2,
                priority="medium",
                status="APPROVED",
            ),
            self.make_request(
                request_id=3,
                priority="medium",
                status="EXECUTED",
                execution_message="Completed.",
            ),
        ]

        with patch.object(
            app_module,
            "load_requests",
            return_value=requests,
        ):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Request #1", page)
        self.assertIn("AWAITING_APPROVAL", page)
        self.assertIn("Execute Approved Action", page)
        self.assertIn("Completed.", page)

    def test_create_request_ignores_empty_message(self) -> None:
        with (
            patch.object(app_module, "load_requests") as load_requests,
            patch.object(app_module, "save_requests") as save_requests,
        ):
            response = self.client.post(
                "/request",
                data={"message": "   "},
            )

        self.assertEqual(response.status_code, 302)
        load_requests.assert_not_called()
        save_requests.assert_not_called()

    def test_create_consequential_request_awaits_approval(
        self,
    ) -> None:
        existing_requests = [
            {"id": 4},
            {},
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=existing_requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
            patch.object(
                app_module,
                "validate_plan",
                return_value=self.valid_validation(),
            ),
        ):
            response = self.client.post(
                "/request",
                data={"message": "I cannot login."},
            )

        self.assertEqual(response.status_code, 302)
        saved_requests = save_requests.call_args.args[0]
        created = saved_requests[0]
        self.assertEqual(created["id"], 5)
        self.assertEqual(created["category"], "access")
        self.assertEqual(created["status"], "AWAITING_APPROVAL")
        self.assertEqual(
            created["review_decision"],
            "APPROVAL_REQUIRED",
        )

    def test_create_general_request_is_ready(self) -> None:
        requests: list[dict] = []

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
            patch.object(
                app_module,
                "validate_plan",
                return_value=self.valid_validation(),
            ),
        ):
            response = self.client.post(
                "/request",
                data={"message": "What services are available?"},
            )

        self.assertEqual(response.status_code, 302)
        created = save_requests.call_args.args[0][0]
        self.assertEqual(created["id"], 1)
        self.assertEqual(created["category"], "general")
        self.assertEqual(created["status"], "READY")
        self.assertEqual(
            created["review_decision"],
            "SAFE_TO_EXECUTE",
        )

    def test_rejected_plan_does_not_reach_reviewer(self) -> None:
        requests: list[dict] = []
        validation = SimpleNamespace(
            valid=False,
            summary="The plan is unsafe.",
            concerns=["The plan could expose credentials."],
        )

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
            patch.object(
                app_module,
                "validate_plan",
                return_value=validation,
            ),
            patch.object(
                app_module,
                "review_plan",
            ) as review_plan,
        ):
            response = self.client.post(
                "/request",
                data={
                    "message":
                        "Give me the administrator password.",
                },
            )

        self.assertEqual(response.status_code, 302)
        review_plan.assert_not_called()
        created = save_requests.call_args.args[0][0]
        self.assertEqual(created["status"], "PLAN_REJECTED")
        self.assertEqual(
            created["review_decision"],
            "NOT_REVIEWED",
        )
        self.assertFalse(created["plan_validation_valid"])
        self.assertEqual(
            created["plan_validation_concerns"],
            ["The plan could expose credentials."],
        )

    def test_approve_waiting_request(self) -> None:
        requests = [
            self.make_request(
                request_id=1,
                status="AWAITING_APPROVAL",
            ),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
        ):
            response = self.client.post("/approve/1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(requests[0]["status"], "APPROVED")
        save_requests.assert_called_once_with(requests)

    def test_approve_does_not_change_non_waiting_request(
        self,
    ) -> None:
        requests = [
            self.make_request(
                request_id=1,
                status="READY",
            ),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(app_module, "save_requests"),
        ):
            self.client.post("/approve/1")

        self.assertEqual(requests[0]["status"], "READY")

    def test_approve_unknown_request_preserves_state(self) -> None:
        requests = [
            self.make_request(request_id=1),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
        ):
            self.client.post("/approve/99")

        save_requests.assert_called_once_with(requests)

    def test_execute_blocks_unapproved_request(self) -> None:
        requests = [
            self.make_request(
                request_id=1,
                status="AWAITING_APPROVAL",
            ),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(app_module, "save_requests"),
            patch.object(
                app_module,
                "execute_action",
            ) as execute_action,
        ):
            response = self.client.post("/execute/1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            requests[0]["execution_message"],
            "Execution blocked.",
        )
        execute_action.assert_not_called()

    def test_execute_approved_request(self) -> None:
        requests = [
            self.make_request(
                request_id=1,
                status="APPROVED",
            ),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(app_module, "save_requests"),
            patch.object(
                app_module,
                "execute_action",
                return_value={
                    "success": True,
                    "message": "Completed.",
                },
            ) as execute_action,
        ):
            self.client.post("/execute/1")

        execute_action.assert_called_once_with(
            "general",
            approved=True,
        )
        self.assertEqual(requests[0]["status"], "EXECUTED")
        self.assertEqual(
            requests[0]["execution_message"],
            "Completed.",
        )

    def test_failed_execution_preserves_approved_status(
        self,
    ) -> None:
        requests = [
            self.make_request(
                request_id=1,
                status="APPROVED",
            ),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(app_module, "save_requests"),
            patch.object(
                app_module,
                "execute_action",
                return_value={
                    "success": False,
                    "message": "Execution failed.",
                },
            ),
        ):
            self.client.post("/execute/1")

        self.assertEqual(requests[0]["status"], "APPROVED")
        self.assertEqual(
            requests[0]["execution_message"],
            "Execution failed.",
        )

    def test_execute_unknown_request_preserves_state(self) -> None:
        requests = [
            self.make_request(request_id=1),
        ]

        with (
            patch.object(
                app_module,
                "load_requests",
                return_value=requests,
            ),
            patch.object(
                app_module,
                "save_requests",
            ) as save_requests,
        ):
            self.client.post("/execute/99")

        save_requests.assert_called_once_with(requests)

    @staticmethod
    def make_request(
        request_id: int,
        priority: str = "medium",
        status: str = "READY",
        execution_message: str = "",
    ) -> dict:
        return {
            "id": request_id,
            "message": "Test request",
            "category": "general",
            "priority": priority,
            "summary": "Test summary",
            "plan": ["Test plan"],
            "action": "Test action",
            "plan_validation_model": "gpt-6-astra",
            "plan_validation_valid": True,
            "plan_validation_summary": "The plan is valid.",
            "plan_validation_concerns": [],
            "review_decision": "SAFE_TO_EXECUTE",
            "review_risks": [],
            "status": status,
            "execution_message": execution_message,
            "created": "2026-09-24T00:00:00",
        }

    @staticmethod
    def valid_validation() -> SimpleNamespace:
        return SimpleNamespace(
            valid=True,
            summary="The plan is valid.",
            concerns=[],
        )


if __name__ == "__main__":
    unittest.main()
