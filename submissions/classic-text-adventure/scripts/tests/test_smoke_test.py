import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import smoke_test


class SmokeHarnessTests(unittest.TestCase):
    def test_case_schema_and_order(self):
        definition = smoke_test.load_cases()
        ids = [case["id"] for case in definition["cases"]]
        self.assertEqual(ids, list(smoke_test.CASE_RUNNERS))

    def test_selected_case_report_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report, code = smoke_test.run_suite(root, {"CTA-SMOKE-GAMEPLAY-003"}, isolate_cases=False)
            self.assertEqual(code, 0)
            self.assertEqual(report["summary"], {"total": 1, "passed": 1, "failed": 0, "skipped": 0})
            self.assertEqual(list(root.iterdir()), [])
            json.dumps(report)

    def test_failure_is_stable_and_sanitized(self):
        case_id = "CTA-SMOKE-GAMEPLAY-003"
        original = smoke_test.CASE_RUNNERS[case_id]
        try:
            smoke_test.CASE_RUNNERS[case_id] = lambda *_: (_ for _ in ()).throw(
                smoke_test.SmokeFailure("expected diagnostic")
            )
            with tempfile.TemporaryDirectory() as directory:
                report, code = smoke_test.run_suite(Path(directory), {case_id}, isolate_cases=False)
            self.assertEqual(code, 1)
            self.assertEqual(report["issues"][0]["code"], case_id)
            self.assertEqual(report["issues"][0]["message"], "expected diagnostic")
        finally:
            smoke_test.CASE_RUNNERS[case_id] = original


if __name__ == "__main__":
    unittest.main()
