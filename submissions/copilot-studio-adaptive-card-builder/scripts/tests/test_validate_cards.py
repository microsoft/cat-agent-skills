from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


def confirmed_action_card() -> dict:
    card = base_card()
    card["body"].append(
        {
            "type": "Input.Toggle",
            "id": "acknowledgeOperation",
            "label": "Operation confirmation",
            "title": "I understand this operation cannot be undone.",
            "isRequired": True,
            "errorMessage": "Confirm the operation before proceeding.",
        }
    )
    action = submit_action()
    action["data"].update(
        riskLevel="destructive",
        requiresExplicitConfirmation=True,
        confirmationInputId="acknowledgeOperation",
    )
    card["actions"] = [action]
    return card


class CardLinterTests(unittest.TestCase):
    def lint(self, card: dict, profile: str = "portable-1.5", mode: str = "auto"):
        return validate_cards.CardLinter(profile, mode).lint(card, "memory.json")

    def codes(self, result) -> set[str]:
        return {item.code for item in result.errors}

    def assert_card_diagnostic_without_traceback(self, card: dict, code: str):
        self.assertIn(code, self.codes(self.lint(card)))
        self.assert_source_diagnostic_without_traceback(json.dumps(card), code)

    def assert_source_diagnostic_without_traceback(self, source: str, code: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(source, encoding="utf-8")
            for output_format in ("text", "json"):
                with self.subTest(output_format=output_format):
                    process = subprocess.run(
                        [
                            sys.executable, "-B", str(SCRIPT_PATH), str(path),
                            "--format", output_format, "--warnings-as-errors",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=15,
                    )
                    self.assertEqual(process.returncode, 1)
                    self.assertEqual(process.stderr, "")
                    self.assertNotIn("Traceback", process.stdout)
                    if output_format == "json":
                        result = json.loads(process.stdout)["results"][0]
                        self.assertFalse(result["ok"])
                        self.assertIn(code, {item["code"] for item in result["errors"]})
                    else:
                        self.assertIn("FAIL ", process.stdout)
                        self.assertIn(code, process.stdout)

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

    def test_catalog_outputs_match_all_bundled_templates(self):
        reference = (
            SUBMISSION_ROOT / "references" / "host-profiles-and-contracts.md"
        ).read_text(encoding="utf-8")

        def objects(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from objects(child)
            elif isinstance(value, list):
                for child in value:
                    yield from objects(child)

        documented_templates = set()
        for row in reference.splitlines():
            if not re.match(r"^\| `[^`]+\.json`", row):
                continue
            cells = row.split("|")
            name = cells[1].strip(" `")
            documented_templates.add(name)
            with self.subTest(template=name):
                card = json.loads(
                    (SUBMISSION_ROOT / "assets" / "templates" / name).read_text(
                        encoding="utf-8"
                    )
                )
                nodes = list(objects(card))
                inputs = {
                    node["id"] for node in nodes
                    if node.get("type", "").startswith("Input.")
                }
                actions = [
                    node for node in nodes if node.get("type") == "Action.Submit"
                ]
                data_keys = {key for action in actions for key in action["data"]}
                documented = set(re.findall(r"`([^`]+)`", cells[4]))
                self.assertFalse(documented - inputs - data_keys)
                self.assertFalse(inputs - documented)
                self.assertEqual(
                    cells[2].strip(), "Interactive" if actions else "Informational"
                )
        self.assertEqual(
            documented_templates,
            {path.name for path in (SUBMISSION_ROOT / "assets" / "templates").glob("*.json")},
        )

    def test_wiring_requires_card_and_submit_identity_before_action_branch(self):
        skill = (SUBMISSION_ROOT / "SKILL.md").read_text(encoding="utf-8")
        wiring = skill.split("### 6. Produce Copilot Studio wiring", 1)[1]
        step = next(line for line in wiring.splitlines() if line.startswith("5. "))
        self.assertIn("exact expected `cardId` and `actionSubmitId`", step)
        self.assertIn("trusted conversation state", step)
        self.assertNotIn("`actionSubmitId` or `actionId`", skill)
        reference = (
            SUBMISSION_ROOT / "references" / "host-profiles-and-contracts.md"
        ).read_text(encoding="utf-8")
        self.assertIn("cardId equals approval_decision_v1", reference)
        self.assertIn("actionSubmitId equals approval_decision_v1_approve", reference)
        self.assertIn("Never branch on `actionId` alone", reference)

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

    def test_deep_container_json_reports_depth_diagnostic(self):
        for depth in (500, 2000, 20000):
            with self.subTest(depth=depth):
                card = base_card()
                card["body"].append("__NESTED__")
                fragment = (
                    '{"type":"Container","items":[' * depth
                    + '{"type":"TextBlock","text":"Nested","wrap":true}'
                    + "]}" * depth
                )
                source = json.dumps(card).replace('"__NESTED__"', fragment)
                self.assert_source_diagnostic_without_traceback(source, "JSON.DEPTH")

    def test_deep_raw_arrays_report_depth_diagnostic(self):
        for source in ("[" * 100000, "[" * 2000, "[" * 2000 + "0" + "]" * 2000):
            with self.subTest(length=len(source)):
                self.assert_source_diagnostic_without_traceback(source, "JSON.DEPTH")

    def test_in_memory_deep_card_is_rejected_before_recursive_walk(self):
        card = base_card()
        nested = {"type": "TextBlock", "text": "Nested", "wrap": True}
        for _ in range(500):
            nested = {"type": "Container", "items": [nested]}
        card["body"].append(nested)
        with patch.object(validate_cards.CardLinter, "_lint_card") as walk:
            result = self.lint(card)
        walk.assert_not_called()
        self.assertEqual(self.codes(result), {"JSON.DEPTH"})

    def test_depth_preflight_precedes_json_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deep.json"
            path.write_text("[" * (validate_cards.MAX_JSON_DEPTH + 1))
            with patch.object(validate_cards.json, "loads") as parse:
                card, error = validate_cards.load_card(path)
            parse.assert_not_called()
            self.assertIsNone(card)
            self.assertEqual(error.code, "JSON.DEPTH")

    def test_json_depth_boundary_matches_file_and_object_checks(self):
        for depth in (63, 64, 65):
            with self.subTest(depth=depth):
                card = base_card()
                action = submit_action()
                value = "plain"
                for _ in range(depth - 4):
                    value = [value]
                action["data"]["context"] = value
                card["actions"] = [action]
                source = json.dumps(card)
                self.assertEqual(validate_cards.source_exceeds_depth(source), depth > 64)
                self.assertEqual(validate_cards.value_exceeds_depth(card), depth > 64)
                result = self.lint(card)
                if depth > 64:
                    self.assertEqual(self.codes(result), {"JSON.DEPTH"})
                    self.assert_source_diagnostic_without_traceback(source, "JSON.DEPTH")
                else:
                    self.assertTrue(result.passes(warnings_as_errors=True), result.errors)
                    with tempfile.TemporaryDirectory() as directory:
                        path = Path(directory) / "boundary.json"
                        path.write_text(source)
                        loaded = validate_cards.lint_path(path, "portable-1.5", "auto")
                        self.assertTrue(loaded.passes(warnings_as_errors=True), loaded.errors)
        for depth in (64, 65):
            with self.subTest(container_walk_depth=depth):
                card = base_card()
                action = submit_action()
                node = {"type": "ActionSet", "actions": [action]}
                for _ in range(29):
                    node = {"type": "Container", "items": [node]}
                card["body"].append(node)
                if depth == 65:
                    action["data"]["context"] = {}
                source = json.dumps(card)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "containers.json"
                    path.write_text(source)
                    result = validate_cards.lint_path(path, "portable-1.5", "auto")
                self.assertEqual(
                    self.codes(result), {"JSON.DEPTH"} if depth == 65 else set()
                )
                self.assertFalse(result.warnings)

    def test_depth_scanner_ignores_brackets_in_escaped_strings(self):
        card = base_card()
        card["body"][0]["text"] = 'Quotes " brackets [ { } ] backslash \\" ' * 200
        source = json.dumps(card)
        self.assertFalse(validate_cards.source_exceeds_depth(source))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quoted.json"
            path.write_text(source)
            result = validate_cards.lint_path(path, "portable-1.5", "auto")
        self.assertNotIn("JSON.DEPTH", self.codes(result))
        self.assertNotIn("JSON.SYNTAX", self.codes(result))

    def test_parser_recursion_guard_returns_structured_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "card.json"
            path.write_text(json.dumps(base_card()))
            with patch.object(validate_cards.json, "loads", side_effect=RecursionError):
                result = validate_cards.lint_path(path, "portable-1.5", "auto")
        self.assertEqual(self.codes(result), {"JSON.DEPTH"})

    def test_walker_recursion_guard_returns_structured_diagnostic(self):
        with patch.object(
            validate_cards.CardLinter, "_scan_sensitive_values", side_effect=RecursionError
        ):
            result = self.lint(base_card())
        self.assertEqual(self.codes(result), {"JSON.DEPTH"})

    def test_version_exceeds_teams_profile(self):
        card = base_card()
        card["version"] = "1.6"
        result = self.lint(card, profile="teams-1.5")
        self.assertIn("HOST.VERSION", self.codes(result))

    def test_oversized_version_components_report_diagnostic(self):
        for version in ("9" * 5000 + ".5", "1." + "9" * 5000, "1234567890.5"):
            with self.subTest(component_length=max(map(len, version.split(".")))):
                card = base_card()
                card["version"] = version
                self.assert_card_diagnostic_without_traceback(card, "ROOT.VERSION")
        self.assertEqual(
            validate_cards.CardLinter._parse_version("123456789.987654321"),
            (123456789, 987654321),
        )

    def test_regex_repetition_overflow_reports_diagnostic(self):
        card = base_card()
        field = input_text()
        field["regex"] = "a{9999999999999999999999999}"
        card["body"].append(field)
        card["actions"] = [submit_action()]
        self.assert_card_diagnostic_without_traceback(card, "INPUT.REGEX")

    def test_regex_recursion_failure_reports_diagnostic(self):
        card = base_card()
        field = input_text()
        field["regex"] = "(" * 1000 + "a" + ")" * 1000
        card["body"].append(field)
        card["actions"] = [submit_action()]
        self.assert_card_diagnostic_without_traceback(card, "INPUT.REGEX")

    def test_versions_below_1_5_report_explicit_policy_minimum(self):
        for profile in validate_cards.PROFILES:
            for version in ("1.0", "1.2", "1.3", "1.4"):
                for heading in (True, False):
                    with self.subTest(profile=profile, version=version, heading=heading):
                        card = base_card()
                        card["version"] = version
                        if not heading:
                            del card["body"][0]["style"]
                        result = self.lint(card, profile=profile)
                        errors = [
                            item for item in result.errors
                            if item.code == "POLICY.VERSION"
                        ]
                        self.assertEqual(len(errors), 1)
                        self.assertEqual(errors[0].path, "$.version")
                        self.assertIn("1.5 or later", errors[0].message)

    def test_versions_from_1_5_preserve_profile_caps_and_heading_requirement(self):
        for profile, maximum in validate_cards.PROFILES.items():
            for version in ("1.5", "1.6", "1.7"):
                with self.subTest(profile=profile, version=version):
                    card = base_card()
                    card["version"] = version
                    result = self.lint(card, profile=profile)
                    self.assertNotIn("POLICY.VERSION", self.codes(result))
                    if tuple(map(int, version.split("."))) <= maximum:
                        self.assertTrue(result.ok, result.errors)
                    else:
                        self.assertIn("HOST.VERSION", self.codes(result))
                    del card["body"][0]["style"]
                    self.assertIn("ACCESS.HEADING", self.codes(self.lint(card, profile)))

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

    def test_required_property_presence_is_checked_for_every_input_type(self):
        for element_type in sorted(validate_cards.INPUT_TYPES):
            for value in (None, "true", 0, [], True, False):
                with self.subTest(element_type=element_type, isRequired=value):
                    card = base_card()
                    field = {"type": element_type, "id": "entry", "label": "Value"}
                    if element_type == "Input.Toggle":
                        field["title"] = "Acknowledge details"
                    elif element_type == "Input.ChoiceSet":
                        field["choices"] = [{"title": "One", "value": "one"}]
                    field["isRequired"] = value
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    expected = (
                        {"INPUT.REQUIRED_TYPE"} if not isinstance(value, bool)
                        else {"ACCESS.ERROR_MESSAGE"} if value else set()
                    )
                    self.assertEqual(self.codes(result), expected)
                    self.assertFalse(result.warnings)
        card = base_card()
        field = input_text()
        field["isRequired"] = None
        del field["errorMessage"]
        card["body"].append(field)
        card["actions"] = [submit_action()]
        self.assert_card_diagnostic_without_traceback(card, "INPUT.REQUIRED_TYPE")

    def test_input_visibility_boolean_policy_is_consistent(self):
        for element_type in sorted(validate_cards.INPUT_TYPES):
            for value in (True, False, None, "true", 0, []):
                with self.subTest(element_type=element_type, isVisible=value):
                    card = base_card()
                    field = {
                        "type": element_type, "id": "entry", "label": "Value",
                        "isVisible": value,
                    }
                    if element_type == "Input.Toggle":
                        field["title"] = "Acknowledge details"
                    elif element_type == "Input.ChoiceSet":
                        field["choices"] = [{"title": "One", "value": "one"}]
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    expected = (
                        {"ELEMENT.BOOLEAN_TYPE"} if not isinstance(value, bool)
                        else set() if value else {"ACCESS.HIDDEN_INPUT"}
                    )
                    self.assertEqual(self.codes(result), expected)
                    self.assertFalse(result.warnings)

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

    def test_non_object_submit_data_reports_every_contract_field(self):
        for data in ("notanobject", 42, [], None):
            with self.subTest(data=data):
                card = base_card()
                card["body"].append(input_text("cardId"))
                action = submit_action()
                action["data"] = data
                card["actions"] = [action]
                result = self.lint(card)
                self.assertEqual(self.codes(result), {"SUBMIT.DATA", "SUBMIT.CONTRACT"})
                self.assertEqual(
                    {item.path for item in result.errors if item.code == "SUBMIT.CONTRACT"},
                    {f"$.actions[0].data.{key}" for key in validate_cards.SUBMIT_CONTRACT_FIELDS},
                )
                self.assertEqual(len(result.errors), 6)
                self.assertIs(action["data"], data)
                self.assertFalse(result.warnings)
                self.assert_card_diagnostic_without_traceback(card, "SUBMIT.CONTRACT")

    def test_submit_data_keys_cannot_collide_with_input_ids(self):
        keys = (
            *validate_cards.SUBMIT_CONTRACT_FIELDS,
            "requiresExplicitConfirmation",
            "confirmationInputId",
            "isEscapeAction",
            "recordId",
        )
        for key in keys:
            for association in (None, "auto"):
                with self.subTest(key=key, association=association):
                    card = base_card()
                    card["body"].append(input_text(key))
                    card["actions"] = [submit_action("one"), submit_action("two")]
                    for action in card["actions"]:
                        action["data"].setdefault(key, "synthetic-value")
                        if association is not None:
                            action["associatedInputs"] = association
                    result = self.lint(card)
                    collisions = [
                        item for item in result.errors
                        if item.code == "SUBMIT.INPUT_DATA_COLLISION"
                    ]
                    self.assertEqual(
                        [item.path for item in collisions],
                        [f"$.actions[{index}].data.{key}" for index in range(2)],
                    )

    def test_nested_submit_data_collision_is_checked_after_input_traversal(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Container",
                "items": [
                    {"type": "ActionSet", "actions": [submit_action()]},
                    input_text("actionId"),
                ],
            }
        )
        result = self.lint(card)
        collisions = [
            item for item in result.errors
            if item.code == "SUBMIT.INPUT_DATA_COLLISION"
        ]
        self.assertEqual(len(collisions), 1)
        self.assertEqual(
            collisions[0].path, "$.body[1].items[0].actions[0].data.actionId"
        )

    def test_submit_data_collision_uses_exact_top_level_keys(self):
        card = base_card()
        card["body"].append(input_text("recordId"))
        action = submit_action()
        action["data"].update(
            {
                "RecordId": "case-sensitive",
                "recordIdLabel": "Record",
                "details": {"recordId": "nested"},
            }
        )
        card["actions"] = [action]
        result = self.lint(card)
        self.assertTrue(result.ok, result.errors)

    def test_escape_action_without_associated_inputs_has_no_data_collision(self):
        card = base_card()
        card["body"].append(input_text("actionId"))
        action = submit_action("cancel")
        action["associatedInputs"] = "none"
        action["data"]["isEscapeAction"] = True
        card["actions"] = [action]
        result = self.lint(card)
        self.assertTrue(result.ok, result.errors)

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

    def test_malformed_open_url_reports_diagnostic(self):
        for url in ("https://[::1", "https://[invalid]", "https://example.com\uff1a443"):
            with self.subTest(url=url):
                card = base_card()
                card["actions"] = [
                    {"type": "Action.OpenUrl", "title": "View documentation", "url": url}
                ]
                self.assert_card_diagnostic_without_traceback(card, "OPENURL.HTTPS")

    def test_open_url_userinfo_is_rejected(self):
        for userinfo in ("user:pass", "admin", "token:secret", "", ":"):
            with self.subTest(userinfo=userinfo):
                card = base_card()
                card["actions"] = [{
                    "type": "Action.OpenUrl", "title": "View documentation",
                    "url": f"https://{userinfo}@example.com/x",
                }]
                self.assert_card_diagnostic_without_traceback(card, "OPENURL.HTTPS")

    def test_open_url_invalid_ports_are_rejected(self):
        for port in ("bad", "99999", "-1"):
            with self.subTest(port=port):
                card = base_card()
                card["actions"] = [{
                    "type": "Action.OpenUrl", "title": "View documentation",
                    "url": f"https://example.com:{port}/x",
                }]
                self.assert_card_diagnostic_without_traceback(card, "OPENURL.HTTPS")

    def test_valid_https_urls_with_optional_ports_remain_allowed(self):
        for url in (
            "https://example.com/x",
            "https://example.com:443/x",
            "https://example.com:65535/x",
            "https://[::1]:8443/x",
            "https://example.com/user@example.com",
        ):
            with self.subTest(url=url):
                card = base_card()
                card["actions"] = [{
                    "type": "Action.OpenUrl", "title": "View documentation", "url": url,
                }]
                result = self.lint(card)
                self.assertTrue(result.passes(warnings_as_errors=True), result.errors)

    def test_secret_input_identifier_variants_are_rejected(self):
        for input_id in (
            "accessToken",
            "access_token",
            "apiKey",
            "apiToken",
            "clientSecret",
            "refreshToken",
            "bearerToken",
            "idToken",
            "sasToken",
            "connectionString",
            "passphrase",
            "passwordHash",
            "signingKey",
        ):
            with self.subTest(input_id=input_id):
                card = base_card()
                card["body"].append(
                    {
                        "type": "Input.Text",
                        "id": input_id,
                        "label": "Sensitive value",
                    }
                )
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertIn("PRIVACY.SECRET_INPUT", self.codes(result))

    def test_secret_input_natural_label_variants_are_rejected(self):
        for label in (
            "Enter access token",
            "Please provide your API key",
            "API-key",
            "Private.key",
            "Current client secret",
            "Connection string (required)",
        ):
            with self.subTest(label=label):
                card = base_card()
                card["body"].append(
                    {
                        "type": "Input.Text",
                        "id": "sensitiveValue",
                        "label": label,
                    }
                )
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertIn("PRIVACY.SECRET_INPUT", self.codes(result))

    def test_compound_secret_token_input_ids_are_rejected(self):
        for input_id in (
            "secretToken", "SecretToken", "secret_token", "SECRET_TOKEN",
            "secrettoken", "secretTokenInput",
        ):
            with self.subTest(input_id=input_id):
                card = base_card()
                card["body"].append(
                    {"type": "Input.Text", "id": input_id, "label": "Service value"}
                )
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertEqual(self.codes(result), {"PRIVACY.SECRET_INPUT"})
                self.assertEqual(result.errors[0].path, "$.body[1]")

    def test_compound_secret_token_visible_prompt_variants_are_rejected(self):
        for property_name in ("label", "placeholder", "errorMessage", "title"):
            for prompt in (
                "secretToken", "secret_token", "secret-token", "secret.token",
                "secret token", "secret:token", "SECRET TOKEN",
                "Paste your secret token here",
            ):
                with self.subTest(property=property_name, prompt=prompt):
                    card = base_card()
                    field = {
                        "type": "Input.Toggle" if property_name == "title" else "Input.Text",
                        "id": "entry",
                        "label": "Service value",
                    }
                    field[property_name] = prompt
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    self.assertEqual(self.codes(result), {"PRIVACY.SECRET_INPUT"})
                    self.assertEqual(len(result.errors), 1)

    def test_compound_secret_token_action_data_key_variants_are_rejected(self):
        for key in (
            "secretToken", "secret_token", "secret-token", "secret.token",
            "secret token", "secret:token", "SECRET TOKEN", "secrettoken",
        ):
            with self.subTest(key=key):
                card = base_card()
                action = submit_action()
                action["data"][key] = "synthetic-value"
                card["actions"] = [action]
                result = self.lint(card)
                self.assertEqual(self.codes(result), {"PRIVACY.SECRET_PROPERTY"})
                self.assertEqual(result.errors[0].path, f"$.actions[0].data.{key}")

    def test_secret_terms_are_detected_anywhere_in_input_prompts(self):
        prompts = (
            "Enter your password",
            "API token",
            "Paste your API token",
            "Enter API token to continue",
            "Password confirmation",
            "secret token input",
            "For the next step, supply a private.key now",
            "Your connectionString goes here",
            "Confirm the client secret before continuing",
            "Optional signing-key for integration setup",
            "Enter your access-token after verification",
            "RefreshToken used by this integration",
            "Put your apikey here",
            "Integration secrettoken required",
        )
        for surface in ("label", "placeholder", "errorMessage", "title"):
            for prompt in prompts:
                with self.subTest(surface=surface, prompt=prompt):
                    card = base_card()
                    field = {
                        "type": "Input.Toggle" if surface == "title" else "Input.Text",
                        "id": "entry",
                        "label": "Service value",
                    }
                    field[surface] = prompt
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    self.assertEqual(self.codes(result), {"PRIVACY.SECRET_INPUT"})
                    self.assertEqual(len(result.errors), 1)

    def test_secret_subsequences_are_detected_in_input_identifiers(self):
        for input_id in (
            "serviceAccessTokenValue", "passwordConfirmation", "secretTokenInput",
            "currentPrivateKey", "integration_connection_string", "api_key_entry",
            "service_apikey_value",
        ):
            with self.subTest(input_id=input_id):
                card = base_card()
                card["body"].append(input_text(input_id))
                card["actions"] = [submit_action()]
                self.assertIn("PRIVACY.SECRET_INPUT", self.codes(self.lint(card)))

    def test_every_benign_phrase_is_explicitly_documented_and_passes(self):
        reference = (
            SUBMISSION_ROOT / "references" / "host-profiles-and-contracts.md"
        ).read_text(encoding="utf-8")
        for phrase in validate_cards.BENIGN_INPUT_PHRASES:
            self.assertIn(f"`{phrase}`", reference)
            words = phrase.split()
            camel_case = words[0] + "".join(word.title() for word in words[1:])
            for text in (phrase, camel_case, phrase.replace(" ", "_"), phrase.upper()):
                with self.subTest(phrase=phrase, text=text):
                    card = base_card()
                    field = input_text()
                    field["label"] = f"Please enter {text} to continue"
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    self.assertTrue(self.lint(card).ok)

    def test_benign_exceptions_cannot_hide_separate_secret_terms(self):
        for phrase in validate_cards.BENIGN_INPUT_PHRASES:
            for prompt in (
                f"{phrase} and password",
                f"API key followed by {phrase}",
                f"{phrase} and its secret value",
                f"private {phrase} key",
            ):
                with self.subTest(phrase=phrase, prompt=prompt):
                    card = base_card()
                    field = input_text()
                    field["label"] = prompt
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    # Exception removal must not join noncontiguous words.
                    if prompt.startswith("private ") and prompt.endswith(" key"):
                        self.assertNotIn("PRIVACY.SECRET_INPUT", self.codes(result))
                    else:
                        self.assertIn("PRIVACY.SECRET_INPUT", self.codes(result))

    def test_benign_id_does_not_exempt_secret_prompt_on_same_input(self):
        card = base_card()
        card["body"].append(
            {
                "type": "Input.Text",
                "id": "secretSantaName",
                "label": "Secret Santa name",
                "placeholder": "Paste your secret token to check its status",
            }
        )
        card["actions"] = [submit_action()]
        self.assertIn("PRIVACY.SECRET_INPUT", self.codes(self.lint(card)))

    def test_new_unlisted_compounds_with_secret_terms_are_flagged(self):
        for input_id in (
            "tokenUsage", "passwordHelp", "secretProject", "secretQuestion",
            "secretQuestionAnswer",
            "privateKeyLabel",
        ):
            with self.subTest(input_id=input_id):
                card = base_card()
                card["body"].append(input_text(input_id))
                card["actions"] = [submit_action()]
                self.assertIn("PRIVACY.SECRET_INPUT", self.codes(self.lint(card)))

    def test_tokenization_preserves_lexical_words(self):
        for word in ("keyword", "keywords", "tokenizer", "secretary"):
            self.assertEqual(validate_cards.tokenize_sensitive_name(word), [word])
        for value, expected in (
            ("APIKey", ["api", "key"]),
            ("keyFindings", ["key", "findings"]),
            ("secretTokenizer", ["secret", "tokenizer"]),
            ("private.key", ["private", "key"]),
        ):
            self.assertEqual(validate_cards.tokenize_sensitive_name(value), expected)

    def test_input_exceptions_do_not_change_non_input_secret_key_policy(self):
        for key in validate_cards.SECRET_FIELD_TERMS:
            with self.subTest(key=key):
                card = base_card()
                action = submit_action()
                action["data"][key] = "synthetic-value"
                card["actions"] = [action]
                self.assertIn("PRIVACY.SECRET_PROPERTY", self.codes(self.lint(card)))
        card = base_card()
        action = submit_action()
        action["data"]["serviceAccessTokenValue"] = "synthetic-value"
        card["actions"] = [action]
        self.assertTrue(self.lint(card).ok)

    def test_compound_names_follow_strict_input_policy(self):
        names = (
            ("tokenCount", "Token count", True),
            ("keyword", "Keyword", False),
            ("keywords", "Keywords", False),
            ("passwordPolicyUrl", "Password policy URL", True),
            ("secretSantaName", "Secret Santa name", False),
            ("accessLevel", "Access level", False),
            ("keyFindings", "Key findings", False),
            ("secretTokenStatus", "Secret token status", True),
            ("secretTokenLabel", "Secret token label", True),
            ("secretTokenizer", "Secret tokenizer", True),
            ("secretaryTokenCount", "Secretary token count", True),
            ("privateKeyLabel", "Private key label", True),
            ("passwordHelp", "Password help", True),
            ("tokenUsage", "Token usage", True),
        )
        for surface in ("id", "label", "placeholder", "errorMessage", "title", "data"):
            for input_id, prompt, sensitive in names:
                with self.subTest(surface=surface, input_id=input_id):
                    card = base_card()
                    action = submit_action()
                    if surface == "data":
                        action["data"][input_id] = "synthetic-value"
                    else:
                        field = {
                            "type": "Input.Toggle" if surface == "title" else "Input.Text",
                            "id": "entry",
                            "label": "Service value",
                        }
                        field[surface] = input_id if surface == "id" else prompt
                        card["body"].append(field)
                    card["actions"] = [action]
                    result = self.lint(card)
                    expected = {"PRIVACY.SECRET_INPUT"} if sensitive and surface != "data" else set()
                    self.assertEqual(self.codes(result), expected)
                    self.assertFalse(result.warnings)

    def test_input_names_distinguish_lexical_words_from_secret_metadata(self):
        for input_id, label, sensitive in (
            ("tokenizer", "Tokenizer", False),
            ("secretary", "Secretary", False),
            ("credentialType", "Credential type", True),
            ("accessTokenStatus", "Access token status", True),
            ("apiKeyLabel", "API key label", True),
            ("passwordPolicy", "Password policy", True),
            ("signingKeyStatus", "Signing key status", True),
            ("connectionStringFormat", "Connection string format", True),
        ):
            with self.subTest(input_id=input_id, label=label):
                card = base_card()
                card["body"].append(
                    {
                        "type": "Input.Text",
                        "id": input_id,
                        "label": label,
                    }
                )
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertEqual(
                    self.codes(result), {"PRIVACY.SECRET_INPUT"} if sensitive else set()
                )

    def test_secret_input_visible_prompts_are_rejected(self):
        for property_name in ("label", "placeholder", "errorMessage", "title"):
            for prompt in (
                "Paste your API token",
                "Please enter your access_token here",
                "Provide private.key",
                "Client secret (required)",
            ):
                with self.subTest(property=property_name, prompt=prompt):
                    card = base_card()
                    field = {
                        "type": "Input.Toggle" if property_name == "title" else "Input.Text",
                        "id": "entry",
                        "label": "Value",
                    }
                    field[property_name] = prompt
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    matches = [
                        item for item in result.errors
                        if item.code == "PRIVACY.SECRET_INPUT"
                    ]
                    self.assertEqual(len(matches), 1)
                    self.assertEqual(matches[0].path, "$.body[1]")

    def test_visible_prompts_do_not_receive_metadata_exemptions(self):
        for property_name in ("label", "placeholder", "errorMessage", "title"):
            for prompt, sensitive in (
                ("Tokenizer", False),
                ("Secretary", False),
                ("Enter credential type", True),
                ("Enter access token status", True),
                ("Provide API key label", True),
                ("Paste your password policy", True),
                ("Connection string format", True),
            ):
                with self.subTest(property=property_name, prompt=prompt):
                    card = base_card()
                    field = {
                        "type": "Input.Toggle" if property_name == "title" else "Input.Text",
                        "id": "entry",
                        "label": "Value",
                    }
                    field[property_name] = prompt
                    card["body"].append(field)
                    card["actions"] = [submit_action()]
                    result = self.lint(card)
                    self.assertEqual(
                        self.codes(result), {"PRIVACY.SECRET_INPUT"} if sensitive else set()
                    )

    def test_non_string_placeholder_reports_type_error_without_crashing(self):
        for placeholder in (42, True, [], {}):
            with self.subTest(placeholder=placeholder):
                card = base_card()
                field = input_text()
                field["placeholder"] = placeholder
                card["body"].append(field)
                card["actions"] = [submit_action()]
                result = self.lint(card)
                self.assertIn("INPUT.PROPERTY_TYPE", self.codes(result))
                self.assertNotIn("PRIVACY.SECRET_INPUT", self.codes(result))

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

    def test_custom_payload_strings_require_destructive_classification(self):
        for payload in (
            {"operation": "delete"},
            {"custom": {"operation": "delete"}},
            {"steps": ["inspect", {"operation": "delete"}]},
            {"steps": [["delete"]]},
            {"cardId": "delete_workspace_v1"},
            {"actionSubmitId": "request_delete_v1"},
        ):
            with self.subTest(payload=payload):
                card = base_card()
                action = submit_action()
                action["data"].update(payload)
                card["actions"] = [action]
                result = self.lint(card)
                self.assertIn("SAFETY.RISK_CLASSIFICATION", self.codes(result))
                self.assertIn("SAFETY.CONFIRMATION_FLAG", self.codes(result))
                self.assertIn("SAFETY.CONFIRMATION_BINDING", self.codes(result))

    def test_destructive_payload_prose_fails_closed_without_exceptions(self):
        for text in ("Do not delete this item.", "Previously removed.", "deProvision"):
            with self.subTest(text=text):
                card = base_card()
                action = submit_action()
                action["data"]["description"] = text
                card["actions"] = [action]
                self.assertIn("SAFETY.RISK_CLASSIFICATION", self.codes(self.lint(card)))

    def test_multiword_destructive_identifiers_require_classification(self):
        for term in ("drop database", "factory reset", "format device"):
            words = term.split()
            variants = (
                term,
                "_".join(words),
                "-".join(words),
                ".".join(words),
                words[0] + "".join(word.title() for word in words[1:]),
                "_".join(words).upper(),
                "request_" + "_".join(words) + "_v1",
            )
            for text in variants:
                for surface in ("title", "actionId", "operation"):
                    with self.subTest(text=text, surface=surface):
                        card = base_card()
                        action = submit_action()
                        if surface == "title":
                            action["title"] = text
                        else:
                            action["data"][surface] = text
                        card["actions"] = [action]
                        self.assertIn(
                            "SAFETY.RISK_CLASSIFICATION", self.codes(self.lint(card))
                        )

    def test_benign_payload_values_do_not_require_destructive_classification(self):
        for payload in (
            {"operation": "archive"},
            {"steps": ["inspect", {"operation": "preview"}], "limit": 5, "dryRun": True},
            {"first": "drop", "second": "database"},
            {"delete": False},
        ):
            with self.subTest(payload=payload):
                card = base_card()
                action = submit_action()
                action["data"].update(payload)
                card["actions"] = [action]
                result = self.lint(card)
                self.assertTrue(result.passes(warnings_as_errors=True), result.errors)

    def test_classified_custom_operation_with_confirmation_passes(self):
        card = confirmed_action_card()
        card["actions"][0]["data"]["custom"] = {"steps": ["delete"]}
        result = self.lint(card)
        self.assertTrue(result.passes(warnings_as_errors=True), result.errors)

    def test_confirmation_uses_literal_schema_default(self):
        for values, expected in (
            ({}, None),
            ({"valueOn": "false", "valueOff": "true"}, "SAFETY.PRECHECKED_CONFIRMATION"),
            ({"valueOn": "yes", "valueOff": "no"}, "SAFETY.CONFIRMATION_INITIAL_VALUE"),
            ({"valueOn": "yes", "valueOff": "false"}, None),
        ):
            with self.subTest(values=values):
                card = confirmed_action_card()
                card["body"][1].update(values)
                result = self.lint(card)
                self.assertEqual(self.codes(result), {expected} if expected else set())
                self.assertFalse(result.warnings)

    def test_confirmation_custom_explicit_initial_values(self):
        for on, off, initial, expected in (
            ("false", "true", "true", None),
            ("false", "true", "false", "SAFETY.PRECHECKED_CONFIRMATION"),
            ("yes", "no", "no", None),
            ("yes", "no", "yes", "SAFETY.PRECHECKED_CONFIRMATION"),
            ("yes", "no", "unknown", "SAFETY.CONFIRMATION_INITIAL_VALUE"),
            ("yes", "no", "", "SAFETY.CONFIRMATION_INITIAL_VALUE"),
            ("yes", "no", None, "SAFETY.CONFIRMATION_INITIAL_VALUE"),
        ):
            with self.subTest(on=on, off=off, initial=initial):
                card = confirmed_action_card()
                card["body"][1].update(valueOn=on, valueOff=off, value=initial)
                result = self.lint(card)
                self.assertEqual(self.codes(result), {expected} if expected else set())
                self.assertFalse(result.warnings)

    def test_confirmation_initial_state_policy_is_destructive_only(self):
        card = confirmed_action_card()
        card["body"][1].update(valueOn="false", valueOff="true")
        card["actions"] = [submit_action()]
        result = self.lint(card)
        self.assertTrue(result.passes(warnings_as_errors=True), result.errors)

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

    def test_confirmation_binding_does_not_require_confirm_in_toggle_id(self):
        cases = (
            ({}, "acknowledgeDeletion", None),
            ({}, "differentToggle", "SAFETY.CONFIRMATION_INPUT"),
            ({"type": "Input.Text"}, "acknowledgeDeletion", "SAFETY.CONFIRMATION_INPUT"),
            ({"isRequired": False}, "acknowledgeDeletion", "SAFETY.CONFIRMATION_INPUT"),
            ({"errorMessage": ""}, "acknowledgeDeletion", "SAFETY.CONFIRMATION_INPUT"),
            ({"isVisible": False}, "acknowledgeDeletion", "ACCESS.HIDDEN_INPUT"),
            ({"value": "true"}, "acknowledgeDeletion", "SAFETY.PRECHECKED_CONFIRMATION"),
            ({"valueOn": "false"}, "acknowledgeDeletion", "TOGGLE.DISTINCT_VALUES"),
        )
        for changes, binding, expected_error in cases:
            with self.subTest(changes=changes, binding=binding):
                card = base_card()
                toggle = {
                    "type": "Input.Toggle",
                    "id": "acknowledgeDeletion",
                    "label": "Deletion acknowledgement",
                    "title": "I understand this permanently deletes the workspace.",
                    "isRequired": True,
                    "errorMessage": "Acknowledge permanent deletion to continue.",
                }
                toggle.update(changes)
                card["body"].append({"type": "Container", "items": [toggle]})
                action = submit_action("delete")
                action["data"].update(
                    {
                        "riskLevel": "destructive",
                        "requiresExplicitConfirmation": True,
                        "confirmationInputId": binding,
                    }
                )
                card["actions"] = [action]
                result = self.lint(card)
                if expected_error:
                    self.assertIn(expected_error, self.codes(result))
                else:
                    self.assertTrue(result.ok, result.errors)

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

    def test_cli_text_and_json_status_match_exit_code(self):
        for condition in ("clean", "warning", "error"):
            for strict in (False, True):
                for output_format in ("text", "json"):
                    with self.subTest(condition=condition, strict=strict, format=output_format):
                        card = base_card()
                        if condition == "warning":
                            card["actions"] = [
                                submit_action(str(index)) for index in range(4)
                            ]
                        elif condition == "error":
                            del card["body"][0]["wrap"]
                        with tempfile.TemporaryDirectory() as directory:
                            path = Path(directory) / "card.json"
                            path.write_text(json.dumps(card), encoding="utf-8")
                            command = [
                                sys.executable, "-B", str(SCRIPT_PATH), str(path),
                                "--format", output_format,
                            ]
                            if strict:
                                command.append("--warnings-as-errors")
                            process = subprocess.run(
                                command, capture_output=True, text=True, check=False
                            )
                        passed = condition == "clean" or (condition == "warning" and not strict)
                        self.assertEqual(process.returncode, 0 if passed else 1, process.stderr)
                        self.assertEqual(process.stderr, "")
                        if output_format == "json":
                            result = json.loads(process.stdout)["results"][0]
                            self.assertEqual(result["ok"], passed)
                            self.assertEqual(len(result["warnings"]), int(condition == "warning"))
                            self.assertEqual(len(result["errors"]), int(condition == "error"))
                        else:
                            self.assertTrue(process.stdout.startswith("PASS " if passed else "FAIL "))
                            self.assertIn(f"{int(passed)}/1 cards passed.", process.stdout)

    def test_strict_cli_summary_counts_only_passing_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            clean_path = Path(directory) / "clean.json"
            clean_path.write_text(json.dumps(base_card()), encoding="utf-8")
            warned_card = base_card()
            warned_card["actions"] = [submit_action(str(index)) for index in range(4)]
            warned_path = Path(directory) / "warned.json"
            warned_path.write_text(json.dumps(warned_card), encoding="utf-8")
            process = subprocess.run(
                [
                    sys.executable, "-B", str(SCRIPT_PATH), directory,
                    "--warnings-as-errors",
                ],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertIn(f"PASS {clean_path}", process.stdout)
        self.assertIn(f"FAIL {warned_path}", process.stdout)
        self.assertIn("1/2 cards passed.", process.stdout)


if __name__ == "__main__":
    unittest.main()
