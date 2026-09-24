from datetime import datetime


def execute_action(
    category: str,
    approved: bool,
) -> dict:

    if not approved:

        return {
            "success": False,
            "message":
                "Action blocked because approval "
                "has not been granted.",
        }

    actions = {

        "access":
            "Access recommendation recorded.",

        "billing":
            "Billing recommendation recorded.",

        "incident":
            "Incident remediation recommendation recorded.",

        "general":
            "Informational response completed.",
    }

    message = actions.get(
        category,
        "No action available.",
    )

    return {
        "success": True,
        "message": message,
        "executed_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),
    }