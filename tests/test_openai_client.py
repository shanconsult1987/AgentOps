import os
import unittest
from unittest.mock import patch

from app import openai_client


class OpenAIClientTests(unittest.TestCase):

    def test_get_model_uses_environment_value(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"OPENAI_MODEL": "test-model"},
                clear=True,
            ),
            patch.object(
                openai_client,
                "load_dotenv",
            ),
        ):
            model = openai_client.get_openai_model()

        self.assertEqual(model, "test-model")

    def test_get_model_uses_default_for_blank_value(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"OPENAI_MODEL": "  "},
                clear=True,
            ),
            patch.object(
                openai_client,
                "load_dotenv",
            ),
        ):
            model = openai_client.get_openai_model()

        self.assertEqual(
            model,
            openai_client.DEFAULT_OPENAI_MODEL,
        )

    def test_create_client_uses_configured_api_key(self) -> None:
        configured_client = object()

        with (
            patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "test-key"},
                clear=True,
            ),
            patch.object(
                openai_client,
                "load_dotenv",
            ),
            patch.object(
                openai_client,
                "OpenAI",
                return_value=configured_client,
            ) as openai,
        ):
            client = openai_client.create_openai_client()

        openai.assert_called_once_with(api_key="test-key")
        self.assertIs(client, configured_client)

    def test_create_client_rejects_missing_api_key(self) -> None:
        with (
            patch.dict(
                os.environ,
                {},
                clear=True,
            ),
            patch.object(
                openai_client,
                "load_dotenv",
            ),
        ):
            with self.assertRaisesRegex(
                openai_client.OpenAIConfigurationError,
                "OPENAI_API_KEY",
            ):
                openai_client.create_openai_client()

    def test_environment_loader_uses_project_env_file(self) -> None:
        with patch.object(
            openai_client,
            "load_dotenv",
        ) as load_dotenv:
            openai_client.load_openai_environment()

        load_dotenv.assert_called_once_with(
            dotenv_path=openai_client.ENV_FILE,
            override=False,
        )


if __name__ == "__main__":
    unittest.main()
