import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_OPENAI_MODEL = "gpt-6-astra"


class OpenAIConfigurationError(RuntimeError):
    pass


def load_openai_environment() -> None:
    load_dotenv(
        dotenv_path=ENV_FILE,
        override=False,
    )


def get_openai_model() -> str:
    load_openai_environment()

    return (
        os.getenv(
            "OPENAI_MODEL",
            DEFAULT_OPENAI_MODEL,
        ).strip()
        or DEFAULT_OPENAI_MODEL
    )


def create_openai_client() -> OpenAI:
    load_openai_environment()
    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise OpenAIConfigurationError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(api_key=api_key)
