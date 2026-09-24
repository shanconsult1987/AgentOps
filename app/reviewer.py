def review_plan(
    category: str,
    priority: str,
    action: str,
) -> dict:

    risks = []

    if priority == "high":

        risks.append(
            "High-priority request."
        )

    if category in {
        "access",
        "billing",
        "incident",
    }:

        risks.append(
            "Consequential action."
        )

    if risks:

        return {
            "decision":
                "APPROVAL_REQUIRED",
            "risks": risks,
            "action": action,
        }

    return {
        "decision":
            "SAFE_TO_EXECUTE",
        "risks": [],
        "action": action,
    }