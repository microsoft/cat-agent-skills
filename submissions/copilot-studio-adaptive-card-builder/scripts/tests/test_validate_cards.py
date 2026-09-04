from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "validate_cards.py"
SUBMISSION_ROOT = SCRIPT_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("validate_cards", SCRIPT_PATH)
assert SPEC and SPEC.loader
validate_cards = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_cards
SPEC.loader.exec_module(validate_cards)


def base_card() -> dict:
    return {
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "fallbackText": "Please use the plain-text interaction.",
        "body": [
            {
                "type": "TextBlock",
                "text": "Request",
                "style": "heading",
                "wrap": True,
            }
        ],
    }


def submit_action(action_id: str = "save") -> dict:
    return {
        "type": "Action.Submit",
        "title": "Save request",
        "data": {
            "cardId": "request_v1",
            "actionId": action_id,
            "actionSubmitId": f"request_v1_{action_id}",
            "intent": f"request.{action_id}",
            "riskLevel": "none",
        },
    }


def input_text(input_id: str = "requestTitle") -> dict:
    return {
        "type": "Input.Text",
        "id": input_id,
        "label": "Request title",
        "isRequired": True,
        "errorMessage": "Enter a request title.",
        "maxLength": 120,
    }


class CardLinterTests(unittest.TestCase):
    def lint(self, card: dict, profile: str = "portable-1.5", mode: str = "auto"):
        return validate_cards.CardLinter(profile, mode).lint(card, "memory.json")

    def codes(self, result) -> set[str]:
        return {item.code for item in result.errors}

    def test_valid_informational_card(self):
        result = self.lint(base_card(), mode="informational")
        self.assertTrue(result.ok)
        self.assertEqual(result.mode, "informational")

    def test_valid_interactive_card(self):
        card = base_card()
        card["body"].append(input_text())
        card["actions"] = [submit_action()]
        result = self.lint(card, mode="interactive")
        self.assertTrue(result.ok)

    def test_approval_template_uses_downstream_conditional_comment_contract(self):
        template_path = (
            SUBMISSION_ROOT / "assets" / "templates" / "approval-decision.json"
        )
        card = json.loads(template_path.read_text(encoding="utf-8"))
        review_comment = next(
            element
            for element in card["body"]
            if element.get("id") == "reviewComment"
        )
        self.assertEqual(review_comment["label"], "Review comment (optional)")
        self.assertNotIn("isRequired", review_comment)
        self.assertNotIn("errorMessage", review_comment)

        action_ids = {action["data"]["actionId"] for action in card["actions"]}
        self.assertEqual(action_ids, {"approve", "reject", "request_changes"})
        guidance = " ".join(
            element.get("text", "")
            for element in card["body"]
            if element.get("type") == "TextBlock"
        ).lower()
        self.assertIn("optional for approval", guidance)
        self.assertIn("reject or request changes", guidance)
        self.assertIn("require a comment", guidance)

    def test_invalid_json_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"type":', encoding="utf-8")
            result = validate_cards.lint_path(path, "portable-1.5", "auto")
        self.assertIn("JSON.SYNTAX", self.codes(result))

    def test_duplicate_json_key_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text(
                '{"type":"AdaptiveCard","type":"AdaptiveCard"}', encoding="utf-8"
            )
            result = validate_cards.lint_path(path, "portable-1.5", "auto")
        self.assertIn("JSON.DUPLICATE_KEY", self.codes(result))

    def test_nonstandard_json_constant_is_reported(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "constant.json"
                path.write_text(f'{{"value": {constant}}}', encoding="utf-8")
                result = validate_cards.lint_path(path, "portable-1.5", "auto")
            self.assertIn("JSON.CONSTANT", self.codes(result))

    def test_invalid_utf8_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-encoding.json"
            path.write_bytes(b"\xff\xfe\x00")
            result = validate_cards.lint_path(path, "portable-1.5", "auto")
        self.assertIn("FILE.ENCODING", self.codes(result))

    def test_version_exceeds_teams_profile(self):
        card = base_card()
        card["version"] = "1.6"
        result = self.lint(card, profile="teams-1.5")
        self.assertIn("HOST.VERSION", self.codes(result))

    def test_action_execute_is_rejected_for_web_chat(self):
        card = base_card()
        card["version"] = "1.6"
        card["actions"] = [{"type": "Action.Execute", "title": "Run"}]
        result = self.lint(card, profile="web-chat-1.6")
        self.assertIn("HOST.ACTION", self.codes(result))

    def test_duplicate_input_ids_are_rejected(self):
        card = base_card()
        card["body"].extend([input_text("details"), input_text("details")])
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("INPUT.DUPLICATE_ID", self.codes(result))

    def test_column_set_accepts_only_columns(self):
        card = base_card()
        card["body"].append(
            {
                "type": "ColumnSet",
                "columns": [
                    {"type": "TextBlock", "text": "Invalid child", "wrap": True}
                ],
            }
        )
        result = self.lint(card)
        self.assertIn("COLUMNSET.COLUMN_TYPE", self.codes(result))

    def test_is_multiline_must_be_boolean(self):
        card = base_card()
        field = input_text()
        field["isMultiline"] = "true"
        card["body"].append(field)
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("INPUT.MULTILINE_TYPE", self.codes(result))

    def test_invalid_date_and_time_values_are_rejected(self):
        for element_type, value in (("Input.Date", "tomorrow"), ("Input.Time", "99:99")):
            with self.subTest(element_type=element_type):
                card = base_card()
                card["body"].append(
                    {
                        "type": element_type,
                        "id": "scheduledValue",
                        "label": "Scheduled value",
                        "value": value,
                    }
                )
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertIn("INPUT.RANGE_FORMAT", self.codes(result))

    def test_missing_input_label_is_rejected(self):
        card = base_card()
        field = input_text()
        del field["label"]
        card["body"].append(field)
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("ACCESS.LABEL", self.codes(result))

    def test_required_input_needs_error_message(self):
        card = base_card()
        field = input_text()
        del field["errorMessage"]
        card["body"].append(field)
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("ACCESS.ERROR_MESSAGE", self.codes(result))

    def test_hidden_input_is_rejected(self):
        card = base_card()
        field = input_text()
        field["isVisible"] = False
        card["body"].append(field)
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("ACCESS.HIDDEN_INPUT", self.codes(result))

    def test_duplicate_choice_values_are_rejected(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.ChoiceSet",
                "id": "category",
                "label": "Category",
                "choices": [
                    {"title": "One", "value": "same"},
                    {"title": "Two", "value": "same"},
                ],
            }
        )
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("CHOICESET.DUPLICATE_VALUE", self.codes(result))

    def test_submit_contract_is_required(self):
        card = base_card()
        card["actions"] = [{"type": "Action.Submit", "title": "Save request"}]
        result = self.lint(card)
        self.assertIn("SUBMIT.DATA", self.codes(result))

    def test_duplicate_submit_ids_are_rejected(self):
        card = base_card()
        first = submit_action("one")
        second = submit_action("two")
        second["data"]["actionSubmitId"] = first["data"]["actionSubmitId"]
        card["actions"] = [first, second]
        result = self.lint(card)
        self.assertIn("SUBMIT.DUPLICATE_ID", self.codes(result))

    def test_template_expression_is_rejected(self):
        card = base_card()
        card["body"][0]["text"] = "${Topic.Title}"
        result = self.lint(card)
        matches = [
            item
            for item in result.errors
            if item.code == "DYNAMIC.TEMPLATE" and item.path == "$.body[0].text"
        ]
        self.assertEqual(len(matches), 1)

    def test_diagnostic_deduplication_preserves_distinct_findings(self):
        linter = validate_cards.CardLinter("portable-1.5", "auto")
        linter.error("TEST.CODE", "$.value", "Test message.")
        linter.error("TEST.CODE", "$.value", "Test message.")
        linter.warning("TEST.CODE", "$.value", "Test message.")
        linter.error("TEST.OTHER_CODE", "$.value", "Test message.")
        linter.error("TEST.CODE", "$.other", "Test message.")
        linter.error("TEST.CODE", "$.value", "Other message.")

        self.assertEqual(len(linter.errors), 4)
        self.assertEqual(len(linter.warnings), 1)
        self.assertEqual(len({*linter.errors, *linter.warnings}), 5)

    def test_http_open_url_is_rejected(self):
        card = base_card()
        card["actions"] = [
            {
                "type": "Action.OpenUrl",
                "title": "View documentation",
                "url": "http://example.com",
            }
        ]
        result = self.lint(card)
        self.assertIn("OPENURL.HTTPS", self.codes(result))

    def test_secret_input_is_rejected(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Text",
                "id": "apiToken",
                "label": "API token",
            }
        )
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertIn("PRIVACY.SECRET_INPUT", self.codes(result))

    def test_secret_property_separator_variants_are_rejected(self):
        for key in (
            "accessToken",
            "apiKey",
            "access_token",
            "api-key",
            "private.key",
            "clientSecret",
            "refresh token",
        ):
            with self.subTest(key=key):
                card = base_card()
                action = submit_action()
                action["data"][key] = "synthetic-value"
                card["actions"] = [action]
                result = self.lint(card)
                self.assertIn("PRIVACY.SECRET_PROPERTY", self.codes(result))

    def test_innocuous_property_names_are_not_rejected(self):
        card = base_card()
        action = submit_action()
        action["data"].update(
            {
                "tokenizer": "word-piece",
                "secretary": "Sample User",
                "credentialType": "training",
                "accessTokenStatus": "not-configured",
                "apiKeyLabel": "integration setting",
            }
        )
        card["actions"] = [action]
        result = self.lint(card)
        self.assertNotIn("PRIVACY.SECRET_PROPERTY", self.codes(result))

    def test_embedded_token_is_rejected(self):
        card = base_card()
        card["body"][0]["text"] = "Bearer " + ("a" * 26)
        result = self.lint(card)
        self.assertIn("PRIVACY.SECRET_VALUE", self.codes(result))

    def test_destructive_action_requires_confirmation(self):
        card = base_card()
        action = submit_action("delete")
        action["title"] = "Delete workspace"
        action["data"]["intent"] = "workspace.delete"
        action["data"]["riskLevel"] = "destructive"
        card["actions"] = [action]
        result = self.lint(card)
        self.assertIn("SAFETY.CONFIRMATION_FLAG", self.codes(result))
        self.assertIn("SAFETY.CONFIRMATION_BINDING", self.codes(result))

    def test_destructive_action_with_confirmation_passes(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Toggle",
                "id": "confirmDeletion",
                "label": "Deletion confirmation",
                "title": "I understand this permanently deletes the workspace.",
                "isRequired": True,
                "errorMessage": "Confirm permanent deletion to continue.",
                "valueOn": "true",
                "valueOff": "false",
            }
        )
        action = submit_action("delete")
        action["title"] = "Delete workspace"
        action["data"]["intent"] = "workspace.delete"
        action["data"]["riskLevel"] = "destructive"
        action["data"]["requiresExplicitConfirmation"] = True
        action["data"]["confirmationInputId"] = "confirmDeletion"
        card["actions"] = [action]
        result = self.lint(card)
        self.assertTrue(result.ok)

    def test_destructive_action_rejects_prechecked_confirmation(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Toggle",
                "id": "confirmWipe",
                "label": "Wipe confirmation",
                "title": "I understand this wipes the device.",
                "isRequired": True,
                "errorMessage": "Confirm the wipe to continue.",
                "value": "true",
                "valueOn": "true",
                "valueOff": "false",
            }
        )
        action = submit_action("wipe")
        action["title"] = "Wipe device"
        action["data"].update(
            {
                "intent": "device.wipe",
                "riskLevel": "destructive",
                "requiresExplicitConfirmation": True,
                "confirmationInputId": "confirmWipe",
            }
        )
        card["actions"] = [action]
        result = self.lint(card)
        self.assertIn("SAFETY.PRECHECKED_CONFIRMATION", self.codes(result))

    def test_destructive_action_rejects_associated_inputs_none(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Toggle",
                "id": "confirmWipe",
                "label": "Wipe confirmation",
                "title": "I understand this wipes the device.",
                "isRequired": True,
                "errorMessage": "Confirm the wipe to continue.",
            }
        )
        action = submit_action("wipe")
        action["title"] = "Wipe device"
        action["associatedInputs"] = "none"
        action["data"].update(
            {
                "intent": "device.wipe",
                "riskLevel": "destructive",
                "requiresExplicitConfirmation": True,
                "confirmationInputId": "confirmWipe",
            }
        )
        card["actions"] = [action]
        result = self.lint(card)
        self.assertIn("SAFETY.ASSOCIATED_INPUTS", self.codes(result))

    def test_identical_toggle_values_are_rejected(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Toggle",
                "id": "confirmWipe",
                "label": "Wipe confirmation",
                "title": "I understand this wipes the device.",
                "isRequired": True,
                "errorMessage": "Confirm the wipe to continue.",
                "valueOn": "yes",
                "valueOff": "yes",
            }
        )
        action = submit_action("wipe")
        action["title"] = "Wipe device"
        action["data"].update(
            {
                "intent": "device.wipe",
                "riskLevel": "destructive",
                "requiresExplicitConfirmation": True,
                "confirmationInputId": "confirmWipe",
            }
        )
        card["actions"] = [action]
        result = self.lint(card)
        self.assertIn("TOGGLE.DISTINCT_VALUES", self.codes(result))

    def test_consequential_action_cannot_bypass_inputs(self):
        card = base_card()
        card["body"].append(input_text())
        action = submit_action()
        action["associatedInputs"] = "none"
        action["data"]["riskLevel"] = "consequential"
        card["actions"] = [action]
        result = self.lint(card)
        self.assertIn("SUBMIT.INPUT_BYPASS", self.codes(result))

    def test_explicit_escape_action_can_bypass_inputs(self):
        card = base_card()
        card["body"].append(input_text())
        action = submit_action("cancel")
        action["title"] = "Cancel and go back"
        action["associatedInputs"] = "none"
        action["data"]["isEscapeAction"] = True
        card["actions"] = [action]
        result = self.lint(card)
        self.assertTrue(result.ok)

    def test_batch_duplicate_submit_ids_are_rejected(self):
        first_card = base_card()
        first_card["actions"] = [submit_action()]
        second_card = base_card()
        second_card["actions"] = [submit_action()]
        first = self.lint(first_card)
        first.file = "first.json"
        second = self.lint(second_card)
        second.file = "second.json"
        validate_cards.apply_batch_checks([first, second])
        self.assertIn("SUBMIT.DUPLICATE_ID_BATCH", self.codes(second))

    def test_informational_mode_rejects_submit(self):
        card = base_card()
        card["actions"] = [submit_action()]
        result = self.lint(card, mode="informational")
        self.assertIn("MODE.SUBMIT", self.codes(result))

    def test_interactive_mode_requires_submit(self):
        result = self.lint(base_card(), mode="interactive")
        self.assertIn("MODE.SUBMIT", self.codes(result))

    def test_root_property_is_rejected(self):
        card = base_card()
        card["refresh"] = {}
        result = self.lint(card)
        self.assertIn("ROOT.PROPERTY", self.codes(result))

    def test_unwrapped_text_is_rejected(self):
        card = base_card()
        del card["body"][0]["wrap"]
        result = self.lint(card)
        self.assertIn("MOBILE.WRAP", self.codes(result))

    def test_non_heading_first_element_is_rejected(self):
        card = base_card()
        del card["body"][0]["style"]
        result = self.lint(card)
        self.assertIn("ACCESS.HEADING", self.codes(result))


if __name__ == "__main__":
    unittest.main()
