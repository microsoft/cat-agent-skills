import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import checkpoint
import runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def start(self, session="game"):
        return runner.handle_request(
            {"protocol": 1, "action": "start", "session_id": session, "request_id": "start", "seed": 42}, self.root
        )

    def test_turn_dedup_and_conflict(self):
        self.start()
        request = {
            "action": "step",
            "protocol": 1,
            "session_id": "game",
            "request_id": "one",
            "base_sequence": 0,
            "raw_input": "no",
        }
        first = runner.handle_request(request, self.root)
        second = runner.handle_request(request, self.root)
        self.assertEqual(first["sequence"], 1)
        self.assertTrue(second["replayed"])
        with self.assertRaises(checkpoint.SequenceConflict):
            runner.handle_request({**request, "request_id": "two"}, self.root)

    def test_invalid_input_does_not_create_a_journal_or_advance(self):
        self.start()
        for request_id, raw_input, error in (
            ("blank", " \t", runner.EmptyInput),
            ("large", "x" * 16_385, runner.InputTooLarge),
        ):
            with self.assertRaises(error):
                runner.handle_request(
                    {
                        "protocol": 1,
                        "action": "step",
                        "session_id": "game",
                        "request_id": request_id,
                        "base_sequence": 0,
                        "raw_input": raw_input,
                    },
                    self.root,
                )
        status = runner.handle_request(
            {"protocol": 1, "action": "status", "session_id": "game", "request_id": "status"}, self.root
        )
        self.assertEqual(status["sequence"], 0)
        self.assertFalse((self.root / "game" / "pending-turn.json").exists())

    def test_second_start_returns_cached_state(self):
        first = self.start()
        second = runner.handle_request(
            {"protocol": 1, "action": "start", "session_id": "game", "request_id": "start-again", "seed": 999},
            self.root,
        )
        self.assertEqual(second["sequence"], first["sequence"])
        self.assertEqual(second["text"], first["text"])
        self.assertTrue(second["replayed"])

    def test_request_id_cannot_change_input(self):
        self.start()
        request = {
            "protocol": 1, "action": "step", "session_id": "game", "request_id": "one", "base_sequence": 0, "raw_input": "no"
        }
        runner.handle_request(request, self.root)
        with self.assertRaises(runner.RequestError):
            runner.handle_request({**request, "raw_input": "yes"}, self.root)

    def test_responses_and_checkpoints_are_text_only(self):
        response = self.start()
        checkpoint_document = checkpoint.load_checkpoint(self.root / "game" / "checkpoint.json")
        for document in (response, checkpoint_document):
            self.assertIn("text", document)
            self.assertFalse(any(key.startswith("image_") for key in document))

    def test_session_identifier_blocks_traversal(self):
        with self.assertRaises(runner.RequestError):
            runner.handle_request({"protocol": 1, "action": "status", "session_id": "../escape", "request_id": "status"}, self.root)

    def test_reset_is_scoped(self):
        self.start("one")
        self.start("two")
        runner.handle_request({"protocol": 1, "action": "reset", "session_id": "one", "request_id": "reset"}, self.root)
        self.assertFalse(runner.handle_request({"protocol": 1, "action": "status", "session_id": "one", "request_id": "status1"}, self.root)["exists"])
        self.assertTrue(runner.handle_request({"protocol": 1, "action": "status", "session_id": "two", "request_id": "status2"}, self.root)["exists"])


if __name__ == "__main__":
    unittest.main()
