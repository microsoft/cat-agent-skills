#!/usr/bin/env python3
"""Bounded semantic linter for Copilot Studio Adaptive Card artifacts.

This validates a conservative, documented subset used by this skill. It is not
full Adaptive Cards schema validation and does not prove host rendering.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

VALIDATOR_NAME = "copilot-studio-adaptive-card-linter"
VALIDATOR_VERSION = "1.0.0"

SCHEMA_URLS = {
    "http://adaptivecards.io/schemas/adaptive-card.json",
    "https://adaptivecards.io/schemas/adaptive-card.json",
    "http://adaptivecards.microsoft.com/schemas/adaptive-card.json",
    "https://adaptivecards.microsoft.com/schemas/adaptive-card.json",
}

PROFILES = {
    "portable-1.5": (1, 5),
    "teams-1.5": (1, 5),
    "omnichannel-1.5": (1, 5),
    "web-chat-1.6": (1, 6),
    "test-chat-1.6": (1, 6),
}

ALLOWED_ELEMENTS = {
    "TextBlock",
    "FactSet",
    "Container",
    "ColumnSet",
    "Column",
    "ActionSet",
    "Input.Text",
    "Input.Number",
    "Input.Date",
    "Input.Time",
    "Input.Toggle",
    "Input.ChoiceSet",
}

ALLOWED_ACTIONS = {"Action.Submit", "Action.OpenUrl"}

ROOT_PROPERTIES = {
    "$schema",
    "type",
    "version",
    "body",
    "actions",
    "fallbackText",
    "lang",
    "rtl",
    "speak",
}

INPUT_TYPES = {
    "Input.Text",
    "Input.Number",
    "Input.Date",
    "Input.Time",
    "Input.Toggle",
    "Input.ChoiceSet",
}

SUBMIT_CONTRACT_FIELDS = (
    "cardId",
    "actionId",
    "actionSubmitId",
    "intent",
    "riskLevel",
)
RISK_LEVELS = {"none", "consequential", "destructive"}
DESTRUCTIVE_TERMS = {
    "delete",
    "remove",
    "revoke",
    "terminate",
    "destroy",
    "erase",
    "purge",
    "wipe",
    "factory reset",
    "deprovision",
    "format device",
    "drop database",
}
def normalize_sensitive_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


SECRET_FIELD_TERMS = {
    "api key",
    "access token",
    "auth token",
    "bearer token",
    "client secret",
    "connection string",
    "credentials",
    "id token",
    "passphrase",
    "password",
    "password hash",
    "passwd",
    "private key",
    "refresh token",
    "sas token",
    "secret",
    "secret key",
    "signing key",
    "token",
    "credential",
}
NORMALIZED_SECRET_FIELD_TERMS = {
    normalize_sensitive_name(term) for term in SECRET_FIELD_TERMS
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
TEMPLATE_EXPRESSION_PATTERN = re.compile(r"\$\{[^}]+\}|\{\{[^}]+\}\}")
VAGUE_ACTION_TITLES = {"click", "click here", "go", "submit", "continue"}

ELEMENT_PROPERTIES = {
    "TextBlock": {
        "type", "text", "wrap", "style", "weight", "size", "color",
        "isSubtle", "spacing", "separator", "id",
    },
    "FactSet": {"type", "facts", "spacing", "separator", "id"},
    "Container": {"type", "items", "style", "spacing", "separator", "id"},
    "ColumnSet": {"type", "columns", "spacing", "separator", "id"},
    "Column": {"type", "items", "width", "spacing", "separator", "id"},
    "ActionSet": {"type", "actions", "spacing", "separator", "id"},
    "Input.Text": {
        "type", "id", "label", "isRequired", "errorMessage", "placeholder",
        "value", "maxLength", "isMultiline", "regex", "style",
    },
    "Input.Number": {
        "type", "id", "label", "isRequired", "errorMessage", "placeholder",
        "value", "min", "max",
    },
    "Input.Date": {
        "type", "id", "label", "isRequired", "errorMessage", "placeholder",
        "value", "min", "max",
    },
    "Input.Time": {
        "type", "id", "label", "isRequired", "errorMessage", "placeholder",
        "value", "min", "max",
    },
    "Input.Toggle": {
        "type", "id", "label", "title", "isRequired", "errorMessage",
        "value", "valueOn", "valueOff", "wrap",
    },
    "Input.ChoiceSet": {
        "type", "id", "label", "isRequired", "errorMessage", "placeholder",
        "value", "choices", "style", "isMultiSelect", "wrap",
    },
}

ACTION_PROPERTIES = {
    "Action.Submit": {
        "type", "title", "data", "associatedInputs", "tooltip", "isEnabled",
    },
    "Action.OpenUrl": {"type", "title", "url", "tooltip", "isEnabled"},
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a property name."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f'duplicate JSON property "{key}"')
        result[key] = value
    return result


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class LintResult:
    file: str
    profile: str
    mode: str
    errors: list[Diagnostic]
    warnings: list[Diagnostic]
    submit_ids: list[tuple[str, str]]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "profile": self.profile,
            "mode": self.mode,
            "validator": VALIDATOR_NAME,
            "validatorVersion": VALIDATOR_VERSION,
            "scope": "bounded semantic lint, not official schema validation",
            "ok": self.ok,
            "errors": [asdict(item) for item in self.errors],
            "warnings": [asdict(item) for item in self.warnings],
            "submitIds": [submit_id for submit_id, _ in self.submit_ids],
            "hostRenderingTested": False,
        }


class CardLinter:
    def __init__(self, profile: str, requested_mode: str) -> None:
        self.profile = profile
        self.max_version = PROFILES[profile]
        self.requested_mode = requested_mode
        self.errors: list[Diagnostic] = []
        self.warnings: list[Diagnostic] = []
        self.card_version = (0, 0)
        self.input_ids: dict[str, str] = {}
        self.confirmation_toggles: list[dict[str, Any]] = []
        self.submit_actions: list[tuple[dict[str, Any], str]] = []
        self.open_url_actions: list[tuple[dict[str, Any], str]] = []
        self.input_count = 0

    def error(self, code: str, path: str, message: str) -> None:
        self.errors.append(Diagnostic("error", code, path, message))

    def warning(self, code: str, path: str, message: str) -> None:
        self.warnings.append(Diagnostic("warning", code, path, message))

    def lint(self, card: Any, source: str) -> LintResult:
        if not isinstance(card, dict):
            self.error("ROOT.TYPE", "$", "The JSON root must be an object.")
            return self._result(source, self.requested_mode)

        self._check_root(card)
        self._scan_sensitive_values(card, "$")

        body = card.get("body")
        if isinstance(body, list):
            for index, element in enumerate(body):
                self._walk_element(element, f"$.body[{index}]")

        actions = card.get("actions")
        if isinstance(actions, list):
            for index, action in enumerate(actions):
                self._walk_action(action, f"$.actions[{index}]")

        mode = self._resolve_mode()
        self._check_mode(card, mode)
        self._check_submit_contracts()
        self._check_destructive_actions()
        self._check_mobile_density(card)
        return self._result(source, mode)

    def _result(self, source: str, mode: str) -> LintResult:
        self.errors.sort(key=lambda item: (item.path, item.code))
        self.warnings.sort(key=lambda item: (item.path, item.code))
        return LintResult(
            file=source,
            profile=self.profile,
            mode=mode,
            errors=self.errors,
            warnings=self.warnings,
            submit_ids=[
                (str(action["data"]["actionSubmitId"]), path)
                for action, path in self.submit_actions
                if isinstance(action.get("data"), dict)
                and isinstance(action["data"].get("actionSubmitId"), str)
                and action["data"]["actionSubmitId"]
            ],
        )

    def _check_root(self, card: dict[str, Any]) -> None:
        for key in card:
            if key not in ROOT_PROPERTIES:
                self.error(
                    "ROOT.PROPERTY",
                    f"$.{key}",
                    f'Root property "{key}" is outside this linter policy.',
                )

        if card.get("type") != "AdaptiveCard":
            self.error(
                "ROOT.ADAPTIVE_CARD",
                "$.type",
                'Root "type" must be "AdaptiveCard".',
            )

        schema = card.get("$schema")
        if schema not in SCHEMA_URLS:
            self.error(
                "ROOT.SCHEMA",
                "$.$schema",
                "Use an official Adaptive Cards schema URL.",
            )

        version = card.get("version")
        parsed_version = self._parse_version(version)
        if parsed_version is None:
            self.error(
                "ROOT.VERSION",
                "$.version",
                'Root "version" must be a major.minor string such as "1.5".',
            )
        else:
            self.card_version = parsed_version
            if parsed_version > self.max_version:
                maximum = ".".join(str(part) for part in self.max_version)
                self.error(
                    "HOST.VERSION",
                    "$.version",
                    f'Card version {version} exceeds profile "{self.profile}" maximum {maximum}.',
                )
            if parsed_version < (1, 3):
                self.error(
                    "POLICY.VERSION",
                    "$.version",
                    "This package requires schema 1.3 or later for accessible labels and input validation.",
                )

        body = card.get("body")
        if not isinstance(body, list) or not body:
            self.error("ROOT.BODY", "$.body", 'Root "body" must be a nonempty array.')
        elif not (
            isinstance(body[0], dict)
            and body[0].get("type") == "TextBlock"
            and body[0].get("style") == "heading"
        ):
            self.error(
                "ACCESS.HEADING",
                "$.body[0]",
                'The first body element must be a TextBlock with style "heading".',
            )

        actions = card.get("actions")
        if actions is not None and not isinstance(actions, list):
            self.error("ROOT.ACTIONS", "$.actions", 'Root "actions" must be an array.')
        for key in ("lang", "speak"):
            value = card.get(key)
            if value is not None and not isinstance(value, str):
                self.error(
                    "ROOT.PROPERTY_TYPE",
                    f"$.{key}",
                    f'"{key}" must be a string.',
                )
        if card.get("rtl") is not None and not isinstance(card["rtl"], bool):
            self.error(
                "ROOT.PROPERTY_TYPE",
                "$.rtl",
                '"rtl" must be boolean.',
            )

        fallback = card.get("fallbackText")
        if not isinstance(fallback, str) or len(fallback.strip()) < 10:
            self.error(
                "FALLBACK.TEXT",
                "$.fallbackText",
                "Provide meaningful plain fallbackText with at least 10 characters.",
            )
        elif TEMPLATE_EXPRESSION_PATTERN.search(fallback):
            self.error(
                "FALLBACK.TEMPLATE",
                "$.fallbackText",
                "fallbackText must not depend on unresolved template expressions.",
            )

    @staticmethod
    def _parse_version(value: Any) -> tuple[int, int] | None:
        if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+", value):
            return None
        major, minor = value.split(".", 1)
        return int(major), int(minor)

    def _walk_element(
        self, element: Any, path: str, *, column_allowed: bool = False
    ) -> None:
        if not isinstance(element, dict):
            self.error("ELEMENT.OBJECT", path, "Every card element must be an object.")
            return

        element_type = element.get("type")
        if not isinstance(element_type, str):
            self.error("ELEMENT.TYPE", f"{path}.type", 'Element "type" is required.')
            return
        if element_type not in ALLOWED_ELEMENTS:
            self.error(
                "HOST.ELEMENT",
                f"{path}.type",
                f'Element "{element_type}" is outside the bounded host profile.',
            )
            return
        if element_type == "Column" and not column_allowed:
            self.error(
                "COLUMN.PARENT",
                path,
                "Column is valid only inside ColumnSet.columns.",
            )
            return

        self._check_allowed_properties(
            element, path, ELEMENT_PROPERTIES[element_type], "element"
        )
        self._check_common_property_types(element, path)

        self._check_feature_versions(element, path, element_type)

        if element_type == "TextBlock":
            self._check_text_block(element, path)
        elif element_type == "FactSet":
            self._check_fact_set(element, path)
        elif element_type in {"Container", "Column"}:
            self._walk_child_elements(element, path, "items")
        elif element_type == "ColumnSet":
            self.warning(
                "ACCESS.COLUMN_ORDER",
                path,
                "Verify ColumnSet focus order and mobile layout in every target channel.",
            )
            self._walk_columns(element, path)
        elif element_type == "ActionSet":
            self._walk_actions_property(element, path)
        elif element_type in INPUT_TYPES:
            self._check_input(element, path, element_type)

        select_action = element.get("selectAction")
        if select_action is not None:
            self.error(
                "HOST.SELECT_ACTION",
                f"{path}.selectAction",
                "selectAction is outside this package's explicit action policy.",
            )

    def _walk_child_elements(
        self, element: dict[str, Any], path: str, property_name: str
    ) -> None:
        children = element.get(property_name)
        child_path = f"{path}.{property_name}"
        if not isinstance(children, list) or not children:
            self.error(
                "ELEMENT.CHILDREN",
                child_path,
                f'"{property_name}" must be a nonempty array.',
            )
            return
        for index, child in enumerate(children):
            self._walk_element(child, f"{child_path}[{index}]")

    def _walk_columns(self, element: dict[str, Any], path: str) -> None:
        columns = element.get("columns")
        child_path = f"{path}.columns"
        if not isinstance(columns, list) or not columns:
            self.error(
                "COLUMNSET.COLUMNS",
                child_path,
                '"columns" must be a nonempty array of Column objects.',
            )
            return
        for index, column in enumerate(columns):
            column_path = f"{child_path}[{index}]"
            if not isinstance(column, dict) or column.get("type") != "Column":
                self.error(
                    "COLUMNSET.COLUMN_TYPE",
                    column_path,
                    "ColumnSet.columns accepts only Column objects.",
                )
                continue
            self._walk_element(column, column_path, column_allowed=True)

    def _walk_actions_property(self, element: dict[str, Any], path: str) -> None:
        actions = element.get("actions")
        if not isinstance(actions, list) or not actions:
            self.error(
                "ACTIONSET.ACTIONS",
                f"{path}.actions",
                '"actions" must be a nonempty array.',
            )
            return
        for index, action in enumerate(actions):
            self._walk_action(action, f"{path}.actions[{index}]")

    def _check_text_block(self, element: dict[str, Any], path: str) -> None:
        text = element.get("text")
        if not isinstance(text, str) or not text.strip():
            self.error(
                "TEXT.VALUE",
                f"{path}.text",
                'TextBlock "text" must be a nonempty string.',
            )
        elif TEMPLATE_EXPRESSION_PATTERN.search(text):
            self.error(
                "DYNAMIC.TEMPLATE",
                f"{path}.text",
                "Do not use ${...} or {{...}} binding in paste-ready JSON. Use a separate Power Fx card formula.",
            )
        if element.get("wrap") is not True:
            self.error(
                "MOBILE.WRAP",
                f"{path}.wrap",
                'Every TextBlock must set "wrap": true.',
            )
        if element.get("style") not in (None, "default", "heading"):
            self.error(
                "TEXT.STYLE",
                f"{path}.style",
                'TextBlock style must be "default" or "heading".',
            )
        for key in ("weight", "size", "color"):
            value = element.get(key)
            if value is not None and not isinstance(value, str):
                self.error(
                    "TEXT.PROPERTY_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be a string.',
                )

    def _check_fact_set(self, element: dict[str, Any], path: str) -> None:
        facts = element.get("facts")
        if not isinstance(facts, list) or not facts:
            self.error("FACTSET.FACTS", f"{path}.facts", '"facts" must be nonempty.')
            return
        for index, fact in enumerate(facts):
            fact_path = f"{path}.facts[{index}]"
            if not isinstance(fact, dict):
                self.error("FACTSET.FACT", fact_path, "Each fact must be an object.")
                continue
            for key in ("title", "value"):
                if not isinstance(fact.get(key), str) or not fact[key].strip():
                    self.error(
                        "FACTSET.VALUE",
                        f"{fact_path}.{key}",
                        f'Fact "{key}" must be a nonempty string.',
                    )

    def _check_input(
        self, element: dict[str, Any], path: str, element_type: str
    ) -> None:
        self.input_count += 1
        input_id = element.get("id")
        if not isinstance(input_id, str) or not ID_PATTERN.fullmatch(input_id):
            self.error(
                "INPUT.ID",
                f"{path}.id",
                "Input id must start with a letter and contain at most 64 letters, numbers, or underscores.",
            )
        elif input_id in self.input_ids:
            self.error(
                "INPUT.DUPLICATE_ID",
                f"{path}.id",
                f'Input id "{input_id}" duplicates {self.input_ids[input_id]}.',
            )
        else:
            self.input_ids[input_id] = f"{path}.id"

        label = element.get("label")
        if not isinstance(label, str) or not label.strip():
            self.error(
                "ACCESS.LABEL",
                f"{path}.label",
                "Every input must have a meaningful label.",
            )

        if element.get("isVisible") is False:
            self.error(
                "ACCESS.HIDDEN_INPUT",
                f"{path}.isVisible",
                "Inputs must remain visible in the bounded accessibility profile.",
            )

        is_required = element.get("isRequired")
        if is_required is not None and not isinstance(is_required, bool):
            self.error(
                "INPUT.REQUIRED_TYPE",
                f"{path}.isRequired",
                '"isRequired" must be boolean.',
            )
        if is_required is True:
            error_message = element.get("errorMessage")
            if not isinstance(error_message, str) or not error_message.strip():
                self.error(
                    "ACCESS.ERROR_MESSAGE",
                    f"{path}.errorMessage",
                    "Every required input must have a useful errorMessage.",
                )

        for key in ("label", "placeholder", "errorMessage"):
            value = element.get(key)
            if value is not None and not isinstance(value, str):
                self.error(
                    "INPUT.PROPERTY_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be a string.',
                )

        self._check_secret_field(input_id, label, path)

        if element_type == "Input.Text":
            self._check_text_input(element, path)
        elif element_type == "Input.ChoiceSet":
            self._check_choice_set(element, path)
        elif element_type == "Input.Toggle":
            self._check_toggle(element, path)
        elif element_type == "Input.Number":
            self._check_number_input(element, path)
        elif element_type in {"Input.Date", "Input.Time"}:
            self._check_range_input(element, path, element_type)

    def _check_text_input(self, element: dict[str, Any], path: str) -> None:
        is_multiline = element.get("isMultiline")
        if is_multiline is not None and not isinstance(is_multiline, bool):
            self.error(
                "INPUT.MULTILINE_TYPE",
                f"{path}.isMultiline",
                '"isMultiline" must be boolean.',
            )
        style = element.get("style")
        if style == "password":
            self.error(
                "PRIVACY.PASSWORD_STYLE",
                f"{path}.style",
                "Do not collect passwords in an Adaptive Card.",
            )
        elif style not in (None, "text", "email", "tel", "url"):
            self.error(
                "INPUT.TEXT_STYLE",
                f"{path}.style",
                '"style" must be text, email, tel, or url in the bounded profile.',
            )
        if element.get("value") is not None and not isinstance(element["value"], str):
            self.error(
                "INPUT.VALUE_TYPE",
                f"{path}.value",
                'Input.Text "value" must be a string.',
            )
        max_length = element.get("maxLength")
        if max_length is not None and (
            not isinstance(max_length, int)
            or isinstance(max_length, bool)
            or max_length <= 0
        ):
            self.error(
                "INPUT.MAX_LENGTH",
                f"{path}.maxLength",
                '"maxLength" must be a positive integer.',
            )
        regex = element.get("regex")
        if regex is not None:
            if not isinstance(regex, str) or not regex:
                self.error(
                    "INPUT.REGEX",
                    f"{path}.regex",
                    '"regex" must be a nonempty string.',
                )
            else:
                try:
                    re.compile(regex)
                except re.error as error:
                    self.error(
                        "INPUT.REGEX",
                        f"{path}.regex",
                        f"Regex could not be parsed by the bounded linter: {error}.",
                    )

    def _check_choice_set(self, element: dict[str, Any], path: str) -> None:
        choices = element.get("choices")
        if not isinstance(choices, list) or not choices:
            self.error(
                "CHOICESET.CHOICES",
                f"{path}.choices",
                '"choices" must be a nonempty array.',
            )
            return
        values: set[str] = set()
        for index, choice in enumerate(choices):
            choice_path = f"{path}.choices[{index}]"
            if not isinstance(choice, dict):
                self.error(
                    "CHOICESET.CHOICE", choice_path, "Each choice must be an object."
                )
                continue
            for key in ("title", "value"):
                value = choice.get(key)
                if not isinstance(value, str) or not value.strip():
                    self.error(
                        "CHOICESET.VALUE",
                        f"{choice_path}.{key}",
                        f'Choice "{key}" must be a nonempty string.',
                    )
            value = choice.get("value")
            if isinstance(value, str):
                if value in values:
                    self.error(
                        "CHOICESET.DUPLICATE_VALUE",
                        f"{choice_path}.value",
                        f'Choice value "{value}" is duplicated.',
                    )
                values.add(value)
        if element.get("style") not in (None, "compact", "expanded"):
            self.error(
                "CHOICESET.STYLE",
                f"{path}.style",
                'Use "compact" or "expanded" in the bounded profile.',
            )
        is_multi = element.get("isMultiSelect")
        if is_multi is not None and not isinstance(is_multi, bool):
            self.error(
                "CHOICESET.MULTI_TYPE",
                f"{path}.isMultiSelect",
                '"isMultiSelect" must be boolean.',
            )
        if element.get("value") is not None and not isinstance(element["value"], str):
            self.error(
                "INPUT.VALUE_TYPE",
                f"{path}.value",
                'Input.ChoiceSet "value" must be a string.',
            )

    def _check_toggle(self, element: dict[str, Any], path: str) -> None:
        title = element.get("title")
        if not isinstance(title, str) or not title.strip():
            self.error(
                "TOGGLE.TITLE",
                f"{path}.title",
                'Input.Toggle requires a descriptive "title".',
            )
        if (
            isinstance(element.get("id"), str)
            and "confirm" in element["id"].lower()
        ):
            self.confirmation_toggles.append(element)
        for key in ("value", "valueOn", "valueOff"):
            value = element.get(key)
            if value is not None and not isinstance(value, str):
                self.error(
                    "TOGGLE.VALUE_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be a string.',
                )
        value_on = element.get("valueOn", "true")
        value_off = element.get("valueOff", "false")
        if (
            not isinstance(value_on, str)
            or not isinstance(value_off, str)
            or not value_on
            or not value_off
            or value_on == value_off
        ):
            self.error(
                "TOGGLE.DISTINCT_VALUES",
                path,
                "Input.Toggle valueOn and valueOff must be distinct, nonempty strings.",
            )

    def _check_number_input(self, element: dict[str, Any], path: str) -> None:
        minimum = element.get("min")
        maximum = element.get("max")
        for key, value in (("min", minimum), ("max", maximum)):
            if value is not None and (
                not isinstance(value, (int, float)) or isinstance(value, bool)
            ):
                self.error(
                    "NUMBER.RANGE_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be a number.',
                )
        value = element.get("value")
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            self.error(
                "INPUT.VALUE_TYPE",
                f"{path}.value",
                'Input.Number "value" must be a number.',
            )
        if (
            isinstance(minimum, (int, float))
            and not isinstance(minimum, bool)
            and isinstance(maximum, (int, float))
            and not isinstance(maximum, bool)
            and minimum > maximum
        ):
            self.error(
                "NUMBER.RANGE",
                path,
                '"min" must not exceed "max".',
            )

    def _check_range_input(
        self, element: dict[str, Any], path: str, element_type: str
    ) -> None:
        minimum = element.get("min")
        maximum = element.get("max")
        for key, value in (("min", minimum), ("max", maximum)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                self.error(
                    "INPUT.RANGE_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be a nonempty string.',
                )
        parser = date.fromisoformat if element_type == "Input.Date" else time.fromisoformat
        pattern = (
            re.compile(r"^\d{4}-\d{2}-\d{2}$")
            if element_type == "Input.Date"
            else re.compile(r"^\d{2}:\d{2}$")
        )
        parsed: dict[str, date | time] = {}
        for key in ("value", "min", "max"):
            value = element.get(key)
            if value is None or not isinstance(value, str):
                continue
            if not pattern.fullmatch(value):
                self.error(
                    "INPUT.RANGE_FORMAT",
                    f"{path}.{key}",
                    f'{element_type} "{key}" must use '
                    + ("YYYY-MM-DD." if element_type == "Input.Date" else "HH:MM."),
                )
                continue
            try:
                parsed[key] = parser(value)
            except ValueError:
                self.error(
                    "INPUT.RANGE_FORMAT",
                    f"{path}.{key}",
                    f'{element_type} "{key}" is not a valid calendar value.',
                )
        if "min" in parsed and "max" in parsed and parsed["min"] > parsed["max"]:
            self.error(
                "INPUT.RANGE",
                path,
                '"min" must not exceed "max".',
            )
        if "value" in parsed and "min" in parsed and parsed["value"] < parsed["min"]:
            self.error(
                "INPUT.VALUE_RANGE",
                f"{path}.value",
                '"value" must not be earlier than "min".',
            )
        if "value" in parsed and "max" in parsed and parsed["value"] > parsed["max"]:
            self.error(
                "INPUT.VALUE_RANGE",
                f"{path}.value",
                '"value" must not be later than "max".',
            )
        if element.get("value") is not None and not isinstance(element["value"], str):
            self.error(
                "INPUT.VALUE_TYPE",
                f"{path}.value",
                'Date and time input "value" must be a string.',
            )

    def _walk_action(self, action: Any, path: str) -> None:
        if not isinstance(action, dict):
            self.error("ACTION.OBJECT", path, "Every action must be an object.")
            return
        action_type = action.get("type")
        if not isinstance(action_type, str):
            self.error("ACTION.TYPE", f"{path}.type", 'Action "type" is required.')
            return
        if action_type not in ALLOWED_ACTIONS:
            extra = ""
            if action_type == "Action.Execute" and self.profile == "web-chat-1.6":
                extra = " Microsoft documents that Bot Framework Web Chat does not support Action.Execute."
            self.error(
                "HOST.ACTION",
                f"{path}.type",
                f'Action "{action_type}" is outside the bounded host profile.{extra}',
            )
            return

        self._check_allowed_properties(
            action, path, ACTION_PROPERTIES[action_type], "action"
        )
        tooltip = action.get("tooltip")
        if tooltip is not None and not isinstance(tooltip, str):
            self.error(
                "ACTION.PROPERTY_TYPE",
                f"{path}.tooltip",
                '"tooltip" must be a string.',
            )
        is_enabled = action.get("isEnabled")
        if is_enabled is not None and not isinstance(is_enabled, bool):
            self.error(
                "ACTION.PROPERTY_TYPE",
                f"{path}.isEnabled",
                '"isEnabled" must be boolean.',
            )
        self._check_feature_versions(action, path, action_type)
        title = action.get("title")
        if not isinstance(title, str) or not title.strip():
            self.error(
                "ACTION.TITLE",
                f"{path}.title",
                "Every action needs a descriptive title.",
            )
        elif title.strip().lower() in VAGUE_ACTION_TITLES:
            self.warning(
                "ACCESS.ACTION_TITLE",
                f"{path}.title",
                f'Action title "{title}" is vague when announced without context.',
            )

        if action_type == "Action.Submit":
            associated_inputs = action.get("associatedInputs")
            if associated_inputs not in (None, "auto", "none"):
                self.error(
                    "SUBMIT.ASSOCIATED_INPUTS",
                    f"{path}.associatedInputs",
                    'associatedInputs must be "auto" or "none".',
                )
            self.submit_actions.append((action, path))
        elif action_type == "Action.OpenUrl":
            self.open_url_actions.append((action, path))
            self._check_open_url(action, path)

    def _check_open_url(self, action: dict[str, Any], path: str) -> None:
        url = action.get("url")
        if not isinstance(url, str) or not url.strip():
            self.error(
                "OPENURL.URL", f"{path}.url", "Action.OpenUrl requires a URL."
            )
            return
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            self.error(
                "OPENURL.HTTPS",
                f"{path}.url",
                "Action.OpenUrl must use an absolute HTTPS URL.",
            )

    def _check_feature_versions(
        self, node: dict[str, Any], path: str, node_type: str
    ) -> None:
        minimums = {
            "label": (1, 3),
            "isRequired": (1, 3),
            "errorMessage": (1, 3),
            "tooltip": (1, 5),
            "isEnabled": (1, 5),
            "mode": (1, 5),
        }
        if node_type == "TextBlock" and node.get("style") == "heading":
            minimums["style"] = (1, 5)
        for property_name, minimum in minimums.items():
            if property_name in node and self.card_version < minimum:
                version = ".".join(str(part) for part in minimum)
                self.error(
                    "SCHEMA.FEATURE_VERSION",
                    f"{path}.{property_name}",
                    f'"{property_name}" requires Adaptive Cards {version} or later.',
                )

    def _resolve_mode(self) -> str:
        if self.requested_mode != "auto":
            return self.requested_mode
        return "interactive" if self.input_count or self.submit_actions else "informational"

    def _check_mode(self, card: dict[str, Any], mode: str) -> None:
        if mode == "interactive" and not self.submit_actions:
            self.error(
                "MODE.SUBMIT",
                "$.actions",
                "Interactive cards require at least one Action.Submit.",
            )
        if mode == "informational":
            if self.input_count:
                self.error(
                    "MODE.INPUT",
                    "$.body",
                    "Informational cards must not contain input elements.",
                )
            if self.submit_actions:
                self.error(
                    "MODE.SUBMIT",
                    "$.actions",
                    "Informational cards must not contain Action.Submit.",
                )

    def _check_submit_contracts(self) -> None:
        seen_submit_ids: dict[str, str] = {}
        for action, path in self.submit_actions:
            data = action.get("data")
            if not isinstance(data, dict):
                self.error(
                    "SUBMIT.DATA",
                    f"{path}.data",
                    "Action.Submit data must be an object with the package identity contract.",
                )
                continue
            for field in SUBMIT_CONTRACT_FIELDS:
                value = data.get(field)
                if not isinstance(value, str) or not value.strip():
                    self.error(
                        "SUBMIT.CONTRACT",
                        f"{path}.data.{field}",
                        f'Action.Submit data requires nonempty "{field}".',
                    )
            risk_level = data.get("riskLevel")
            if isinstance(risk_level, str) and risk_level not in RISK_LEVELS:
                self.error(
                    "SUBMIT.RISK_LEVEL",
                    f"{path}.data.riskLevel",
                    "riskLevel must be none, consequential, or destructive.",
                )
            if action.get("associatedInputs") == "none":
                if risk_level != "none" or data.get("isEscapeAction") is not True:
                    self.error(
                        "SUBMIT.INPUT_BYPASS",
                        f"{path}.associatedInputs",
                        'associatedInputs: "none" is allowed only when riskLevel is "none" and isEscapeAction is true.',
                    )
            submit_id = data.get("actionSubmitId")
            if isinstance(submit_id, str) and submit_id:
                if submit_id in seen_submit_ids:
                    self.error(
                        "SUBMIT.DUPLICATE_ID",
                        f"{path}.data.actionSubmitId",
                        f'actionSubmitId "{submit_id}" duplicates {seen_submit_ids[submit_id]}.',
                    )
                seen_submit_ids[submit_id] = f"{path}.data.actionSubmitId"

    def _check_destructive_actions(self) -> None:
        for action, path in self.submit_actions:
            text_parts = [str(action.get("title", ""))]
            data = action.get("data")
            if isinstance(data, dict):
                text_parts.extend(str(data.get(key, "")) for key in ("actionId", "intent"))
            normalized = " ".join(text_parts).lower()
            known_destructive = any(term in normalized for term in DESTRUCTIVE_TERMS)
            declared_destructive = (
                isinstance(data, dict) and data.get("riskLevel") == "destructive"
            )
            if known_destructive and not declared_destructive:
                self.error(
                    "SAFETY.RISK_CLASSIFICATION",
                    f"{path}.data.riskLevel",
                    "The action appears destructive and must declare riskLevel: destructive.",
                )
            if not known_destructive and not declared_destructive:
                continue
            if action.get("associatedInputs") == "none":
                self.error(
                    "SAFETY.ASSOCIATED_INPUTS",
                    f"{path}.associatedInputs",
                    "A destructive action must submit and validate its confirmation input.",
                )
            if not isinstance(data, dict) or data.get("requiresExplicitConfirmation") is not True:
                self.error(
                    "SAFETY.CONFIRMATION_FLAG",
                    f"{path}.data.requiresExplicitConfirmation",
                    "Destructive actions require requiresExplicitConfirmation: true.",
                )
            confirmation_id = (
                data.get("confirmationInputId") if isinstance(data, dict) else None
            )
            matching_toggles = [
                toggle
                for toggle in self.confirmation_toggles
                if toggle.get("id") == confirmation_id
            ]
            if not isinstance(confirmation_id, str) or not confirmation_id:
                self.error(
                    "SAFETY.CONFIRMATION_BINDING",
                    f"{path}.data.confirmationInputId",
                    "Destructive actions must name their confirmationInputId.",
                )
            elif not matching_toggles:
                self.error(
                    "SAFETY.CONFIRMATION_INPUT",
                    path,
                    "confirmationInputId must match a visible Input.Toggle whose id contains 'confirm'.",
                )
            else:
                toggle = matching_toggles[0]
                valid_toggle = (
                    toggle.get("isRequired") is True
                    and isinstance(toggle.get("errorMessage"), str)
                    and bool(toggle["errorMessage"].strip())
                )
                if not valid_toggle:
                    self.error(
                        "SAFETY.CONFIRMATION_INPUT",
                        path,
                        "The bound confirmation toggle must be required and have an errorMessage.",
                    )
                value_on = str(toggle.get("valueOn", "true"))
                value_off = str(toggle.get("valueOff", "false"))
                initial_value = str(toggle.get("value", value_off))
                if initial_value == value_on:
                    self.error(
                        "SAFETY.PRECHECKED_CONFIRMATION",
                        f"{path}.data.confirmationInputId",
                        "The bound confirmation toggle must be initially off.",
                    )

    def _check_mobile_density(self, card: dict[str, Any]) -> None:
        actions = card.get("actions")
        if isinstance(actions, list) and len(actions) > 3:
            self.warning(
                "MOBILE.ACTION_COUNT",
                "$.actions",
                "More than three primary actions may be difficult to use on mobile.",
            )
        body = card.get("body")
        if isinstance(body, list) and len(body) > 12:
            self.warning(
                "MOBILE.DENSITY",
                "$.body",
                "A long card body may be difficult to scan on mobile. Consider splitting the interaction.",
            )

    def _check_secret_field(self, input_id: Any, label: Any, path: str) -> None:
        normalized = normalize_sensitive_name(f"{input_id or ''} {label or ''}")
        if any(term in normalized for term in NORMALIZED_SECRET_FIELD_TERMS):
            self.error(
                "PRIVACY.SECRET_INPUT",
                path,
                "Do not collect passwords, secrets, tokens, API keys, private keys, or credentials in a card.",
            )

    def _check_allowed_properties(
        self,
        node: dict[str, Any],
        path: str,
        allowed: set[str],
        kind: str,
    ) -> None:
        for key in node:
            if key not in allowed:
                self.error(
                    f"{kind.upper()}.PROPERTY",
                    f"{path}.{key}",
                    f'Property "{key}" is outside the bounded {kind} policy.',
                )

    def _check_common_property_types(
        self, element: dict[str, Any], path: str
    ) -> None:
        for key in ("separator", "isSubtle", "wrap"):
            value = element.get(key)
            if value is not None and not isinstance(value, bool):
                self.error(
                    "ELEMENT.BOOLEAN_TYPE",
                    f"{path}.{key}",
                    f'"{key}" must be boolean.',
                )

    def _scan_sensitive_values(self, value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized_key = normalize_sensitive_name(key)
                if normalized_key in NORMALIZED_SECRET_FIELD_TERMS:
                    self.error(
                        "PRIVACY.SECRET_PROPERTY",
                        f"{path}.{key}",
                        f'Property "{key}" appears to contain secret material.',
                    )
                self._scan_sensitive_values(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._scan_sensitive_values(child, f"{path}[{index}]")
        elif isinstance(value, str):
            if TEMPLATE_EXPRESSION_PATTERN.search(value):
                self.error(
                    "DYNAMIC.TEMPLATE",
                    path,
                    "Do not use ${...} or {{...}} binding in paste-ready JSON. Use a separate Power Fx card formula.",
                )
            if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
                self.error(
                    "PRIVACY.SECRET_VALUE",
                    path,
                    "Value resembles a credential or access token.",
                )


def load_card(path: Path) -> tuple[Any | None, Diagnostic | None]:
    try:
        source = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        return None, Diagnostic(
            "error", "FILE.ENCODING", "$", f"File must be valid UTF-8: {error}."
        )
    except OSError as error:
        return None, Diagnostic("error", "FILE.READ", "$", str(error))
    try:
        return (
            json.loads(
                source,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"nonstandard JSON constant {value}")
                ),
            ),
            None,
        )
    except DuplicateKeyError as error:
        return None, Diagnostic("error", "JSON.DUPLICATE_KEY", "$", str(error))
    except json.JSONDecodeError as error:
        location = f"line {error.lineno}, column {error.colno}"
        return None, Diagnostic(
            "error", "JSON.SYNTAX", "$", f"{error.msg} at {location}."
        )
    except ValueError as error:
        return None, Diagnostic("error", "JSON.CONSTANT", "$", f"{error}.")


def collect_json_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            files.extend(
                candidate
                for candidate in sorted(path.rglob("*.json"))
                if candidate.is_file()
            )
        else:
            files.append(path)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def lint_path(path: Path, profile: str, mode: str) -> LintResult:
    card, load_error = load_card(path)
    if load_error:
        return LintResult(
            file=str(path),
            profile=profile,
            mode=mode,
            errors=[load_error],
            warnings=[],
            submit_ids=[],
        )
    return CardLinter(profile, mode).lint(card, str(path))


def apply_batch_checks(results: list[LintResult]) -> None:
    seen: dict[str, tuple[LintResult, str]] = {}
    for result in results:
        for submit_id, local_path in result.submit_ids:
            if submit_id not in seen:
                seen[submit_id] = (result, local_path)
                continue
            first_result, _ = seen[submit_id]
            result.errors.append(
                Diagnostic(
                    "error",
                    "SUBMIT.DUPLICATE_ID_BATCH",
                    local_path,
                    f'actionSubmitId "{submit_id}" also appears in {first_result.file}.',
                )
            )
            result.errors.sort(key=lambda item: (item.path, item.code))


def print_text(results: list[LintResult]) -> None:
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(
            f"{status} {result.file} "
            f"[profile={result.profile}, mode={result.mode}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}]"
        )
        for item in [*result.errors, *result.warnings]:
            print(
                f"  {item.severity.upper()} {item.code} "
                f"{item.path}: {item.message}"
            )
    print(
        f"\n{VALIDATOR_NAME} {VALIDATOR_VERSION}: "
        f"{sum(result.ok for result in results)}/{len(results)} cards passed. "
        "Scope: bounded semantic lint, not official schema validation. "
        "Host rendering was not tested."
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Copilot Studio Adaptive Card JSON against a conservative host "
            "profile. This is not full official schema validation."
        )
    )
    parser.add_argument("paths", nargs="+", help="JSON files or directories")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="portable-1.5",
        help="Copilot Studio host profile",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "interactive", "informational"),
        default="auto",
        help="Expected Copilot Studio node mode",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit nonzero when warnings are present",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    files = collect_json_files(args.paths)
    if not files:
        print("No JSON files found.", file=sys.stderr)
        return 2
    results = [lint_path(path, args.profile, args.mode) for path in files]
    apply_batch_checks(results)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "validator": VALIDATOR_NAME,
                    "validatorVersion": VALIDATOR_VERSION,
                    "results": [result.to_dict() for result in results],
                },
                indent=2,
            )
        )
    else:
        print_text(results)
    has_errors = any(result.errors for result in results)
    has_warnings = any(result.warnings for result in results)
    return 1 if has_errors or (args.warnings_as_errors and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
