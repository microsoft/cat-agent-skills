import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import checkpoint


class CheckpointTests(unittest.TestCase):
    def test_round_trip_and_hash_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            payload = {"schema": 1, "sequence": 2}
            checkpoint.write_checkpoint(path, payload)
            self.assertEqual(checkpoint.load_checkpoint(path), payload)
            document = json.loads(path.read_text())
            document["sequence"] = 3
            path.write_text(json.dumps(document))
            with self.assertRaises(checkpoint.CheckpointError):
                checkpoint.load_checkpoint(path)

    def test_lock_is_reusable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lock"
            with checkpoint.session_lock(path):
                self.assertTrue(path.exists())
            with checkpoint.session_lock(path):
                pass


if __name__ == "__main__":
    unittest.main()

