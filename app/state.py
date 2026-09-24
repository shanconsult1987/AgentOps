import json
from pathlib import Path
from typing import Any


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "requests.json"
)


def load_requests() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        return []

    return []


def save_requests(
    requests: list[dict[str, Any]],
) -> None:

    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = DATA_FILE.with_suffix(
        ".tmp"
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            requests,
            file,
            indent=2,
        )

    temporary_file.replace(DATA_FILE)