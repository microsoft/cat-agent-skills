import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import runtime_adapter as adapter


class RuntimeAdapterTests(unittest.TestCase):
    def test_start_and_replay_are_exact(self):
        expected = "WELCOME TO ADVENTURE!!  WOULD YOU LIKE INSTRUCTIONS?\n\n"
        self.assertEqual(adapter.start(123)[1].text, expected)
        state = adapter.canonical_state(123, ["no", "enter"])
        self.assertEqual(adapter.step(state, "get lamp"), adapter.step(state, "get lamp"))

    def test_parser_matches_traditional_cli(self):
        self.assertEqual(adapter.tokenize("  GET, shiny-lamp! "), ["get", "shiny", "lamp"])

    def test_raw_transport_is_preserved_in_canonical_state(self):
        raw = "  GeT, lamp\\路径\nnow  "
        next_state, _ = adapter.step(adapter.canonical_state(5, ["no"]), raw)
        self.assertEqual(adapter.decode_state(next_state)["transcript"][-1], raw)

    def test_maximum_size_input_is_accepted(self):
        raw = "x" * adapter.MAX_COMMAND_BYTES
        next_state, _ = adapter.step(adapter.canonical_state(5, ["no"]), raw)
        self.assertEqual(adapter.decode_state(next_state)["transcript"][-1], raw)

    def test_input_limits(self):
        for bad in ("", " \t\n", "x" * (adapter.MAX_COMMAND_BYTES + 1)):
            with self.assertRaises(adapter.AdapterError):
                adapter.validate_command(bad)

    def test_save_uses_memory_not_a_path(self):
        state = adapter.canonical_state(1, ["no"])
        self.assertEqual(adapter.step(state, "save ../../escape.sav")[1].text, "GAME SAVED\n")

    def test_state_shape_is_strict(self):
        with self.assertRaises(adapter.AdapterError):
            adapter.inspect_state(b'{"runtime":"adventure-1.7","schema":99,"seed":1,"transcript":[]}')
        with self.assertRaises(adapter.AdapterError):
            adapter.decode_state(b'{"schema":1,"runtime":"adventure-1.7","seed":1,"transcript":[]}\n')


if __name__ == "__main__":
    unittest.main()
