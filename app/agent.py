from dataclasses import dataclass


@dataclass
class AgentResult:
    category: str
    priority: str
    summary: str


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


def analyze_request(message: str) -> AgentResult:
    category, priority = classify_request(message)

    summary = (
        f"Request classified as {category} "
        f"with {priority} priority."
    )

    return AgentResult(
        category=category,
        priority=priority,
        summary=summary,
    )