"""Regression tests for assets/templates/approval_renderer.py.

The renderer ships as copy-paste material, so a defect in it lands directly in
someone's agent. Redaction is the part that matters most: it is the boundary
that keeps a secret out of the approval text a human is about to read and, in
many deployments, out of the transcript that text is logged into.

Run from the skill root (the directory containing SKILL.md):

    python scripts/tests/test_approval_renderer.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TEMPLATE_PATH = (
    Path(__file__).parents[2] / "assets" / "templates" / "approval_renderer.py"
)
SPEC = importlib.util.spec_from_file_location("approval_renderer", TEMPLATE_PATH)
assert SPEC and SPEC.loader
approval_renderer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = approval_renderer
SPEC.loader.exec_module(approval_renderer)

ApprovalSpec = approval_renderer.ApprovalSpec
mask = approval_renderer.mask
render_approval_request = approval_renderer.render_approval_request


class RedactionTests(unittest.TestCase):
    def test_always_redact_list_is_masked(self):
        self.assertEqual(mask("api_key", "sk-live-123", frozenset()), "[redacted]")

    def test_always_redact_is_case_insensitive_on_the_argument(self):
        self.assertEqual(mask("API_KEY", "sk-live-123", frozenset()), "[redacted]")

    def test_spec_redaction_matches_regardless_of_declared_case(self):
        """A spec declaring 'ApiKey' must still mask an argument named 'apiKey'."""
        self.assertEqual(
            mask("apiKey", "sk-live-123", frozenset({"ApiKey"})), "[redacted]"
        )

    def test_spec_redaction_matches_regardless_of_argument_case(self):
        self.assertEqual(
            mask("SessionToken", "abc", frozenset({"sessiontoken"})), "[redacted]"
        )

    def test_ordinary_value_is_not_masked(self):
        self.assertEqual(mask("subject", "Your order", frozenset()), "Your order")

    def test_redaction_survives_the_render_path(self):
        spec = ApprovalSpec(
            action="Call a partner API",
            target="{endpoint}",
            consequence="The partner receives the call.",
            reversibility="Nobody.",
            detail_arguments=("ApiKey",),
            redact=frozenset({"apikey"}),
        )
        rendered = render_approval_request(
            "call_partner",
            {"endpoint": "/v1/pay", "ApiKey": "sk-live-do-not-log"},
            {"call_partner": spec},
        )
        self.assertIn("[redacted]", rendered)
        self.assertNotIn("sk-live-do-not-log", rendered)


class TruncationTests(unittest.TestCase):
    def test_long_value_is_shortened_but_its_size_is_stated(self):
        value = "x" * 500
        rendered = mask("body", value, frozenset())
        self.assertIn("500 characters total", rendered)
        self.assertLess(len(rendered), len(value))

    def test_short_value_is_untouched(self):
        self.assertEqual(mask("body", "hello", frozenset()), "hello")


class RenderTests(unittest.TestCase):
    def test_a_bare_tool_name_is_never_the_whole_request(self):
        """The anti-pattern this template exists to replace."""
        rendered = render_approval_request(
            "send_customer_email",
            {
                "to": "hans@contoso.example",
                "subject": "Shipped",
                "body": "Your order left the warehouse.",
            },
        )
        self.assertNotEqual(rendered.strip(), "send_customer_email")
        self.assertIn("hans@contoso.example", rendered)
        self.assertIn("Reversible by:", rendered)

    def test_missing_spec_still_shows_the_values_and_says_it_is_a_gap(self):
        rendered = render_approval_request("unknown_tool", {"amount": 500})
        self.assertIn("500", rendered)
        self.assertIn("No approval wording is defined", rendered)

    def test_missing_spec_path_still_redacts(self):
        rendered = render_approval_request("unknown_tool", {"api_key": "sk-live-123"})
        self.assertIn("[redacted]", rendered)
        self.assertNotIn("sk-live-123", rendered)

    def test_scale_argument_reports_the_count(self):
        rendered = render_approval_request(
            "close_tickets",
            {"ticket_ids": [1, 2, 3, 4], "resolution": "Duplicate"},
        )
        self.assertIn("4 items affected by this single approval", rendered)

    def test_scale_argument_that_is_not_a_collection_says_so(self):
        rendered = render_approval_request(
            "close_tickets",
            {"ticket_ids": 7, "resolution": "Duplicate"},
        )
        self.assertIn("unknown", rendered)

    def test_unresolvable_target_does_not_raise(self):
        rendered = render_approval_request("issue_refund", {"amount": 500})
        self.assertIn("target could not be resolved", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
