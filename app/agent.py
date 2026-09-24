from dataclasses import dataclass


@dataclass
class AgentResult:
    category: str
    priority: str
    summary: str
    plan: list[str]
    action: str
    approval_required: bool


def classify_request(message: str) -> tuple[str, str]:

    text = message.lower()

    if any(
        word in text
        for word in (
            "login",
            "log in",
            "access",
            "permission",
            "password",
        )
    ):
        return "access", "high"

    if any(
        word in text
        for word in (
            "invoice",
            "billing",
            "bill",
            "payment",
        )
    ):
        return "billing", "medium"

    if any(
        word in text
        for word in (
            "down",
            "outage",
            "incident",
            "error",
            "slow",
        )
    ):
        return "incident", "high"

    return "general", "medium"


def create_plan(
    category: str,
) -> list[str]:

    plans = {

        "access": [
            "Validate the access request.",
            "Check required business justification.",
            "Prepare an access recommendation.",
            "Request human approval.",
        ],

        "billing": [
            "Validate billing information.",
            "Review the billing request.",
            "Prepare a billing recommendation.",
            "Request human approval.",
        ],

        "incident": [
            "Capture incident details.",
            "Assess operational impact.",
            "Prepare remediation recommendation.",
            "Request human approval.",
        ],

        "general": [
            "Understand the request.",
            "Prepare an informational response.",
        ],
    }

    return plans.get(
        category,
        plans["general"],
    )


def create_action(
    category: str,
) -> str:

    actions = {

        "access":
            "Recommend an access change.",

        "billing":
            "Recommend a billing correction.",

        "incident":
            "Recommend incident remediation.",

        "general":
            "Provide an informational response.",
    }

    return actions.get(
        category,
        actions["general"],
    )


def needs_clarification(message: str) -> bool:
    normalized_message = message.strip().lower().rstrip(".!?")

    return normalized_message in {
        "fix this",
        "help",
        "help me",
    }


def analyze_request(
    message: str,
) -> AgentResult:

    category, priority = classify_request(
        message
    )

    plan = create_plan(
        category
    )

    action = create_action(
        category
    )

    if needs_clarification(message):
        plan = [
            "Ask the requester to clarify the problem.",
        ]
        action = "Request clarification."

    approval_required = (
        category != "general"
    )

    summary = (
        f"Request classified as {category} "
        f"with {priority} priority."
    )

    return AgentResult(
        category=category,
        priority=priority,
        summary=summary,
        plan=plan,
        action=action,
        approval_required=approval_required,
    )

def evaluate_classification(
    message: str,
    expected_category: str,
    expected_priority: str,
) -> dict:

    actual_category, actual_priority = (
        classify_request(message)
    )

    return {
        "passed":
            (
                actual_category
                == expected_category
                and actual_priority
                == expected_priority
            ),
        "actual_category":
            actual_category,
        "actual_priority":
            actual_priority,
        "expected_category":
            expected_category,
        "expected_priority":
            expected_priority,
    }