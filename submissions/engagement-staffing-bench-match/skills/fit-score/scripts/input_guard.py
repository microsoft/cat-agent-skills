"""Fail-closed input handling shared by the staffing engines (byte-identical in every scripts/ folder).

Clean one-line input errors that never echo a value or a supplied path, strict JSON loading
(duplicate keys, non-finite numbers and deep nesting refused), typed field access, one canonical
form for every name and ID comparison, reserved display labels, and atomic LF output writes.
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime

MAX_JSON_DEPTH = 64
MAX_INPUT_BYTES = 20 * 1024 * 1024
MARKER_PREFIX = "[FLAGGED:"


class InputError(Exception):
    """A malformed input; the message names a field path or a label, never a value or a file path."""


def need(condition, message):
    if not condition:
        raise InputError(message)


def run(main):
    """Run an engine main(); any input error or unexpected failure is one clean line and exit 2."""
    try:
        return main()
    except InputError as error:
        print(f"error: {error}", file=sys.stderr, flush=True)
        return 2
    except RecursionError:
        print("error: input nested too deeply; fail closed", file=sys.stderr, flush=True)
        return 2
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001 - fail closed without a traceback or an echoed value
        print(f"error: unexpected {type(error).__name__} while processing input; fail closed",
              file=sys.stderr, flush=True)
        return 2


class ArgumentParser(argparse.ArgumentParser):
    """argparse that reports a bad command line as one InputError and never echoes an argument."""

    def error(self, message):
        usage = self.format_usage().strip()
        usage = usage[len("usage: "):] if usage.startswith("usage: ") else usage
        usage = " ".join(usage.split())
        raise InputError(f"command line: missing or unrecognised arguments; usage: {usage}")


_JSON_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"?|[\[\]{}]')


def _depth_ok(text):
    depth = 0
    for token in _JSON_TOKEN.finditer(text):
        char = token.group(0)
        if char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return False
        elif char in "]}":
            depth -= 1
    return True


def _unique_object(label):
    def hook(pairs):
        seen = set()
        for key, _value in pairs:
            folded = canonical(key)
            need(folded not in seen,
                 f"{label}: an object repeats a member name (not repeated); the file is ambiguous")
            seen.add(folded)
        return dict(pairs)
    return hook


def _no_constant(_name):
    raise InputError("non-finite number (NaN or Infinity) is not valid JSON")


def load_json(path, label):
    """Load one JSON input; every failure is an InputError naming only ``label``."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError(f"{label}: file missing or unreadable") from None
    need(len(raw) <= MAX_INPUT_BYTES, f"{label}: file larger than {MAX_INPUT_BYTES} bytes")
    need(raw.strip(), f"{label}: file is empty")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(f"{label}: not UTF-8 text") from None
    need(_depth_ok(text), f"{label}: JSON nested deeper than {MAX_JSON_DEPTH} levels")
    try:
        document = json.loads(
            text, object_pairs_hook=_unique_object(label), parse_constant=_no_constant
        )
    except json.JSONDecodeError as error:
        raise InputError(f"{label}: not valid JSON (line {error.lineno})") from None
    need(isinstance(document, dict), f"{label}: top level must be a JSON object")
    return document


def write_json(path, payload):
    """Write ``json.dumps(payload, indent=2)`` with LF line endings, atomically (temp file + replace)."""
    data = json.dumps(payload, indent=2).encode("utf-8")
    folder = os.path.dirname(os.path.abspath(path))
    try:
        handle, temp_path = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=folder)
    except OSError:
        raise InputError("output folder missing or not writable") from None
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.replace(temp_path, path)
    except OSError:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise InputError("output file could not be written") from None


# One canonical form for every name, ID and header comparison (output keeps the original value).
def canonical(value):
    text = unicodedata.normalize("NFKC", str(value))
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    return " ".join(text.casefold().split())


def id_key(value):
    """Canonical ID: canonical() with '-', '_', '.' and whitespace folded. Blank IDs return None."""
    if value is None or isinstance(value, bool) or not isinstance(value, str):
        return None
    folded = re.sub(r"[\s\-_.\u2010-\u2015\u2212]+", "-", canonical(value)).strip("-")
    return folded or None


def engagement_id_key(value):
    """An engagement ID compares exactly as supplied, surrounding whitespace aside; it is never
    folded (the rule 9.5 canonical folding is for candidate IDs only). Blank IDs return None."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


_ID_SEP = r"[\s\-_.\u2010-\u2015\u2212]"
_ID_JOIN = r"[\-_.\u2010-\u2015\u2212]"


_ID_TOKEN = re.compile(r"[^\W_]+(?:" + _ID_JOIN + r"+[^\W_]+)*")
_ID_LIKE = re.compile(r"[^\W\d_]+" + _ID_SEP + r"+\d")


_WORD = re.compile(r"\w")
_ALNUM = re.compile(r"[^\W_]")


def _quiet(char):
    """A neighbour that never joins an ID to a further component: whitespace, an apostrophe or a
    word character (the match's own lookarounds already exclude the last)."""
    return char.isspace() or char in "'\u2019" or _WORD.match(char) is not None


def _component_counts(text, begin, end):
    """True when text[begin:end] (one component) holds a digit or is a single character and is not a
    whole ID such as C-102 (indexes only; nothing is copied)."""
    if _ID_LIKE.match(text, begin, end):
        return False
    return end - begin == 1 or any(text[index].isdigit() for index in range(begin, end))


def _extends_id(text, end):
    """True when the text right after a matched ID (``end`` indexes its first character) continues
    that ID: punctuation such as '/', ':' or '#' directly followed by a component that holds a digit
    or is a single character (C-101/2, C-101:2, C-101#2, C-101/A). Another whole ID (C-101/C-102),
    prose (C-101:review), a space, an apostrophe or the end of a sentence does not. Linear: only
    the neighbouring component is read."""
    if len(text) - end < 2 or _quiet(text[end]):
        return False
    token = _ID_TOKEN.match(text, end + 1)
    return token is not None and _component_counts(text, token.start(), token.end())


_ID_PART_CHAR = re.compile(r"[^\W_]|" + _ID_JOIN)


def _prefixes_id(text, start):
    """True when the text right before a matched ID (``start`` indexes its first character) makes it
    part of a longer ID: a component that holds a digit or is a single character directly followed
    by punctuation such as '/', ':' or '#' (X/C-101, 2:C-101, A#C-101). The whole preceding
    component is read, however long, by walking back over it by index. Another whole ID
    (C-100/C-101), prose (re:C-101), a space, an apostrophe, an opening bracket or quote at the start
    of the text does not."""
    if start < 2 or _quiet(text[start - 1]) or not _ALNUM.match(text, start - 2):
        return False
    begin = start - 2
    while begin > 0 and _ID_PART_CHAR.match(text, begin - 1):
        begin -= 1
    while not _ALNUM.match(text, begin):
        begin += 1
    return _component_counts(text, begin, start - 1)


def mentions_id(text, value):
    """True when free text names the ID ``value`` in id_key()'s canonical form (rule 9.5): any run of
    whitespace, '-', '_', '.' or a Unicode dash may separate its parts. Part of a longer ID never
    matches (C-1 is not found in C-10, C-101, C-1.5, C-1/2 or X/C-1)."""
    key = id_key(value)
    if key is None or not isinstance(text, str):
        return False
    body = (_ID_SEP + "+").join(re.escape(part) for part in key.split("-"))
    pattern = rf"(?<!\w)(?<!\w{_ID_JOIN}){body}(?!\w)(?!{_ID_JOIN}\w)"
    folded = canonical(text)
    return any(
        not _extends_id(folded, match.end()) and not _prefixes_id(folded, match.start())
        for match in re.finditer(pattern, folded)
    )


RESERVED_WORDS = {
    "unknown", "unknown candidate", "unknown role", "none", "null", "n/a", "na", "tbd", "redacted",
    "withheld", "flagged", "anonymous", "candidate", "role", "bench record", "role record",
    "citation unknown",
}


def has_marker(value):
    return isinstance(value, str) and MARKER_PREFIX.casefold() in canonical(value)


def is_reserved_label(value):
    """True for display fallbacks and marker forms the engines emit; such values are never data."""
    if not isinstance(value, str):
        return False
    folded = canonical(value)
    if has_marker(value) or folded in RESERVED_WORDS:
        return True
    return bool(re.fullmatch(r"[<\[(].*[>\])]", folded))


# Typed field access; ``where`` is a field path such as roles[0].role_id.
_KINDS = {
    "obj": (dict, "an object"),
    "list": (list, "an array"),
    "str": (str, "a string"),
    "bool": (bool, "true or false"),
}


def kind_of(value, kind):
    if kind == "num":
        return is_num(value)
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, _KINDS[kind][0])


def _kind_name(kind):
    return {"num": "a number", "int": "an integer"}.get(kind) or _KINDS[kind][1]


def is_num(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def field(obj, key, kind, where, required=True, nullable=False):
    """Return obj[key] checked against ``kind``; absent/None only when allowed. Never coerces."""
    need(isinstance(obj, dict), f"{where} must be an object")
    path = f"{where}.{key}" if where else key
    if key not in obj:
        need(not required, f"{path} is required")
        return None
    value = obj[key]
    if value is None:
        need(nullable or not required, f"{path} must not be null")
        return None
    need(kind_of(value, kind), f"{path} must be {_kind_name(kind)}")
    return value


def text_list(obj, key, where, required=True):
    """A list of non-reserved strings (absent only when not required; never null)."""
    path = f"{where}.{key}" if where else key
    values = field(obj, key, "list", where, required=required)
    if values is None:
        return None
    for index, item in enumerate(values):
        need(isinstance(item, str), f"{path}[{index}] must be a string")
    return values


def check_id(value, path):
    need(isinstance(value, str), f"{path} must be a string identifier")
    need(id_key(value) is not None, f"{path} must not be blank")
    need(not is_reserved_label(value), f"{path} uses a reserved label form")
    return value


def check_name(value, path):
    need(isinstance(value, str) and value.strip(), f"{path} must be a non-blank string")
    need(not is_reserved_label(value), f"{path} uses a reserved label form")
    return value


def check_pct(value, path):
    need(is_num(value), f"{path} must be a number")
    need(0 <= value <= 100, f"{path} must be between 0 and 100")
    return value


def check_confidence(value, path):
    need(is_num(value), f"{path} must be a number")
    need(0 <= value <= 1, f"{path} must be between 0 and 1")
    return value


def check_date(value, path):
    need(isinstance(value, str), f"{path} must be a YYYY-MM-DD date")
    try:
        need(len(value) == 10, f"{path} must be a YYYY-MM-DD date")
        return date.fromisoformat(value)
    except ValueError:
        raise InputError(f"{path} must be a YYYY-MM-DD date") from None


_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z")


def check_timestamp(value, path):
    need(isinstance(value, str) and _TIMESTAMP_RE.fullmatch(value),
         f"{path} must be an ISO 8601 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)")
    try:
        datetime.fromisoformat(value[:-1])
    except ValueError:
        raise InputError(f"{path} must be an ISO 8601 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)") from None
    return value


def duplicate_keys(values):
    """Canonical ID keys that occur more than once (blank keys are never equal to each other)."""
    seen, repeated = set(), []
    for value in values:
        key = id_key(value)
        if key is None:
            continue
        if key in seen and key not in repeated:
            repeated.append(key)
        seen.add(key)
    return repeated


def same_document(left, right):
    """Exact deep equality for re-derivation (rule 9.8): same JSON types, same members, same values.

    Unlike ``==`` it never treats ``1``, ``1.0`` and ``true`` as equal and never folds case or
    whitespace. Member order is not compared (it carries no data).
    """
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_document(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_document(a, b) for a, b in zip(left, right))
    return left == right
