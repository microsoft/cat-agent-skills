import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


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

    def test_runner_timeout_is_configurable(self):
        completed = SimpleNamespace(stdout='{"ok":true}', returncode=0)
        with mock.patch.object(smoke_test.subprocess, "run", return_value=completed) as run:
            response = smoke_test._invoke_runner(Path("state"), {}, timeout_seconds=12.5)
        self.assertTrue(response["ok"])
        self.assertEqual(run.call_args.kwargs["timeout"], 12.5)

    def test_apache_license_manifest_attribution(self):
        manifest = json.loads(
            (smoke_test.SKILL_ROOT / "references" / "licenses" / "BUNDLE_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        apache = next(item for item in manifest["files"] if item["path"] == "references/licenses/Apache-2.0.txt")
        self.assertEqual(apache["copyright"], "The Apache Software Foundation")
        self.assertFalse(apache["modified"])

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
