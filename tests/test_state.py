import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import state


class RequestStateTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_file = (
            Path(self.temporary_directory.name)
            / "nested"
            / "requests.json"
        )
        data_file_patch = patch.object(
            state,
            "DATA_FILE",
            self.data_file,
        )
        data_file_patch.start()
        self.addCleanup(data_file_patch.stop)

    def test_load_returns_empty_list_when_file_is_missing(self) -> None:
        self.assertEqual(state.load_requests(), [])

    def test_save_and_load_requests_round_trip(self) -> None:
        requests = [
            {
                "id": 1,
                "category": "access",
            },
        ]

        state.save_requests(requests)

        self.assertEqual(state.load_requests(), requests)
        self.assertTrue(self.data_file.exists())
        self.assertFalse(
            self.data_file.with_suffix(".tmp").exists()
        )

    def test_save_replaces_existing_file(self) -> None:
        state.save_requests([{"id": 1}])
        state.save_requests([{"id": 2}])

        self.assertEqual(
            json.loads(
                self.data_file.read_text(encoding="utf-8")
            ),
            [{"id": 2}],
        )

    def test_load_returns_empty_list_for_invalid_json(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text("{invalid", encoding="utf-8")

        self.assertEqual(state.load_requests(), [])

    def test_load_returns_empty_list_for_non_list_json(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text(
            '{"id": 1}',
            encoding="utf-8",
        )

        self.assertEqual(state.load_requests(), [])

    def test_load_returns_empty_list_for_read_error(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text("[]", encoding="utf-8")

        with patch.object(
            Path,
            "open",
            side_effect=OSError("read failed"),
        ):
            self.assertEqual(state.load_requests(), [])


if __name__ == "__main__":
    unittest.main()
