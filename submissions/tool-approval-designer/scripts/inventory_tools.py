#!/usr/bin/env python3
"""Bounded static inventory of approval-relevant agent tools.

Reads a codebase and reports, per tool, what the code can actually prove: the
declared approval mode, and advisory signals about writes, external visibility,
and blast radius.

This script does not issue verdicts. It supplies evidence for the four questions
in ``references/surfaces-and-contracts.md``; a human answers them and rules.

It is deliberately conservative about what counts as a tool. ``@tool`` is a
common decorator name, so a Python tool is only reported as ``parsed`` when the
decorator can be traced to an ``agent_framework`` import. A ``@tool`` borrowed
from another library, or defined in the file being read, is skipped with a note
rather than reported with an ``approval_mode`` it does not have. A bare ``@tool``
that cannot be traced at all is kept but labelled ``best-effort``.

Standard library only. No third-party packages, no shell invocation, and no
OS-specific paths, so the same command works on every runtime this skill
targets.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

INVENTORY_NAME = "tool-approval-inventory"
INVENTORY_VERSION = "1.0.0"

MIN_PYTHON = (3, 9)

# --------------------------------------------------------------------------
# Vocabularies
#
# Deliberately curated rather than exhaustive. A term earns its place only if
# matching it as a whole token is far more often right than wrong. Terms that
# collide with common standard-library calls (``close``, ``add``, ``set``) are
# restricted to the tool's own name and docstring, where the author's intent is
# unambiguous, instead of being matched against every call in the body.
# --------------------------------------------------------------------------

BODY_WRITE_VERBS = frozenset(
    {
        "archive",
        "charge",
        "commit",
        "create",
        "delete",
        "deploy",
        "deprovision",
        "drop",
        "escalate",
        "grant",
        "insert",
        "invite",
        "notify",
        "patch",
        "pay",
        "post",
        "provision",
        "publish",
        "purge",
        "put",
        "refund",
        "remove",
        "revoke",
        "rotate",
        "save",
        "send",
        "terminate",
        "transfer",
        "update",
        "upload",
        "write",
    }
)

NAME_ONLY_WRITE_VERBS = frozenset(
    {
        "approve",
        "assign",
        "cancel",
        "close",
        "disable",
        "enable",
        "enroll",
        "merge",
        "reject",
        "rename",
        "reset",
        "schedule",
        "submit",
        "subscribe",
        "unsubscribe",
    }
)

NAME_WRITE_VERBS = BODY_WRITE_VERBS | NAME_ONLY_WRITE_VERBS

EXTERNAL_TERMS = frozenset(
    {
        "customer",
        "email",
        "external",
        "facebook",
        "invoice",
        "linkedin",
        "mail",
        "partner",
        "pay",
        "payment",
        "payout",
        "paypal",
        "portal",
        "public",
        "publish",
        "recipient",
        "refund",
        "ses",
        "sendgrid",
        "smtp",
        "sms",
        "stripe",
        "subscriber",
        "supplier",
        "tweet",
        "twilio",
        "vendor",
        "webhook",
        "whatsapp",
        "wire",
    }
)

BLAST_NAME_TERMS = frozenset(
    {"all", "batch", "broadcast", "bulk", "each", "every", "many", "mass", "multi"}
)

BLAST_PARAM_NAMES = frozenset(
    {
        "accounts",
        "addresses",
        "customers",
        "emails",
        "files",
        "items",
        "messages",
        "orders",
        "recipients",
        "records",
        "rows",
        "targets",
        "tickets",
        "users",
    }
)

COLLECTION_ANNOTATION = re.compile(
    r"\b(?:list|List|Sequence|Iterable|Collection|set|Set|tuple|Tuple|frozenset)\s*\["
)

SQL_WRITE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE|TRUNCATE\s+TABLE|ALTER\s+TABLE)\b",
    re.IGNORECASE,
)

HTTP_WRITE_METHODS = frozenset({"post", "put", "patch", "delete"})
# Python file modes are order-independent flag strings: exactly one of r, w, a
# or x, optionally 'b' or 't' for the encoding, optionally '+' for update. Any
# mode containing w, a, x or + can write, so test for those flags rather than
# enumerating permutations, which misses 'wb+', 'w+b', 'rb+', 'x+b' and friends.
WRITE_FILE_MODE_FLAGS = frozenset({"w", "a", "x", "+"})

APPROVAL_MODES = frozenset({"always_require", "never_require", "conditional"})
AGENT_FRAMEWORK = "agent_framework"
DEFAULT_APPROVAL_MODE = "never_require"
GATING_MODES = frozenset({"always_require", "conditional"})
DYNAMIC_APPROVAL_MODE = "<dynamic>"

SKIP_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "env",
        "node_modules",
        "site-packages",
        "venv",
    }
)

TEST_FILE = re.compile(r"(?:^test_.*\.py$)|(?:_test\.py$)|(?:_test\.go$)")

# Go is not parseable with the standard library, so detection is a bounded
# regular expression over calls into the ``tool`` package and is always reported
# as best-effort.
GO_APPROVAL_WRAP = re.compile(
    r"tool\.ApprovalRequiredFunc\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*[,)]"
)
GO_TOOL_BINDING = re.compile(
    r"^\s*(?:var\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:?=\s*tool\.([A-Za-z_][A-Za-z0-9_]*)\(",
    re.MULTILINE,
)


def tokenize(value: str) -> list[str]:
    """Split snake_case, camelCase, and punctuation into lowercase tokens."""
    value = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", value)
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return re.findall(r"[a-z0-9]+", value.lower())


@dataclass
class Signal:
    category: str
    where: str
    evidence: str


@dataclass
class ToolRecord:
    name: str
    function: str
    language: str
    detection: str
    source: str
    line: int
    docstring: str
    parameters: list[str]
    approval_mode: str
    approval_mode_explicit: bool
    gated: bool
    proposed_write: str
    proposed_visibility: str
    proposed_blast: str
    signals: list[Signal] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def needs_attention(self) -> bool:
        return self.proposed_write == "write" and not self.gated

    @property
    def needs_urgent_attention(self) -> bool:
        return self.needs_attention and self.proposed_visibility == "external"


@dataclass
class Inventory:
    root: str
    tools: list[ToolRecord] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "tools": len(self.tools),
            "gated": sum(1 for t in self.tools if t.gated),
            "ungated": sum(1 for t in self.tools if not t.gated),
            "approval_mode_explicit": sum(1 for t in self.tools if t.approval_mode_explicit),
            "write_signalled": sum(1 for t in self.tools if t.proposed_write == "write"),
            "external_signalled": sum(
                1 for t in self.tools if t.proposed_visibility == "external"
            ),
            "many_signalled": sum(1 for t in self.tools if t.proposed_blast == "many"),
            "ungated_write": sum(1 for t in self.tools if t.needs_attention),
            "ungated_write_external": sum(1 for t in self.tools if t.needs_urgent_attention),
            "best_effort": sum(1 for t in self.tools if t.detection == "best-effort"),
        }


# --------------------------------------------------------------------------
# Python analysis
# --------------------------------------------------------------------------


def is_agent_framework_module(name: str | None) -> bool:
    return bool(name) and (
        name == AGENT_FRAMEWORK or name.startswith(AGENT_FRAMEWORK + ".")
    )


class ToolProvenance:
    """Where a ``@tool`` decorator in one file came from.

    The inventory only claims to read Agent Framework tools, so a ``@tool``
    borrowed from another library must not be reported as one. Detection is
    therefore split three ways rather than answered yes or no.
    """

    CONFIRMED = "confirmed"  # traced to an agent_framework import
    FOREIGN = "foreign"  # traced to something else, so not ours
    UNATTRIBUTED = "unattributed"  # named 'tool' but nothing to trace it to


@dataclass
class ToolOrigins:
    """Names in one module that could introduce a ``@tool`` decorator."""

    confirmed: set[str]
    foreign: dict[str, str]
    modules: set[str]
    star_imported: bool

    def classify_bare(self, name: str) -> str | None:
        if name in self.confirmed:
            return ToolProvenance.CONFIRMED
        if name in self.foreign:
            return ToolProvenance.FOREIGN
        if name == "tool":
            return (
                ToolProvenance.CONFIRMED
                if self.star_imported
                else ToolProvenance.UNATTRIBUTED
            )
        return None


def collect_tool_decorator_aliases(tree: ast.Module) -> ToolOrigins:
    """Classify every name in one module that could introduce a ``@tool``."""
    confirmed: set[str] = set()
    foreign: dict[str, str] = {}
    modules: set[str] = set()
    star_imported = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            from_agent_framework = is_agent_framework_module(node.module)
            for alias in node.names:
                if alias.name == "*":
                    if from_agent_framework:
                        star_imported = True
                    continue
                if alias.name != "tool":
                    continue
                local = alias.asname or alias.name
                if from_agent_framework:
                    confirmed.add(local)
                    foreign.pop(local, None)
                elif local not in confirmed:
                    foreign[local] = node.module or "a relative import"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if is_agent_framework_module(alias.name):
                    modules.add(alias.asname or alias.name.split(".")[0])

    # A decorator defined in this file is this file's own, not the framework's.
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == "tool" and node.name not in confirmed:
                foreign.setdefault("tool", "a definition in this file")

    return ToolOrigins(
        confirmed=confirmed,
        foreign=foreign,
        modules=modules,
        star_imported=star_imported,
    )


def decorator_target(node: ast.expr) -> ast.expr:
    return node.func if isinstance(node, ast.Call) else node


def tool_decorator_provenance(node: ast.expr, origins: ToolOrigins) -> str | None:
    """Return a ``ToolProvenance`` value, or ``None`` if this is not a tool."""
    target = decorator_target(node)
    if isinstance(target, ast.Name):
        return origins.classify_bare(target.id)
    if isinstance(target, ast.Attribute) and target.attr == "tool":
        root = target.value
        while isinstance(root, ast.Attribute):
            root = root.value
        if not isinstance(root, ast.Name):
            return None
        if root.id in origins.modules:
            return ToolProvenance.CONFIRMED
        if root.id == AGENT_FRAMEWORK:
            # Names the framework, but the import is missing. That is broken
            # Python, so do not claim it as confirmed; surface it instead.
            return ToolProvenance.UNATTRIBUTED
    return None


def unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive on exotic nodes
        return "?"


def parameter_signatures(node: ast.AST) -> list[str]:
    args = node.args
    collected: list[ast.arg] = []
    collected.extend(getattr(args, "posonlyargs", []) or [])
    collected.extend(args.args)
    if args.vararg is not None:
        collected.append(args.vararg)
    collected.extend(args.kwonlyargs)
    if args.kwarg is not None:
        collected.append(args.kwarg)
    signatures = []
    for argument in collected:
        if argument.annotation is None:
            signatures.append(argument.arg)
        else:
            signatures.append(f"{argument.arg}: {unparse(argument.annotation)}")
    return signatures


def read_approval_mode(decorator: ast.expr) -> tuple[str, bool, list[str]]:
    """Return (effective mode, explicitly declared, notes)."""
    notes: list[str] = []
    if not isinstance(decorator, ast.Call):
        return DEFAULT_APPROVAL_MODE, False, notes
    for keyword in decorator.keywords:
        if keyword.arg != "approval_mode":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            mode = value.value
            if mode not in APPROVAL_MODES:
                notes.append(
                    f"approval_mode {mode!r} is not one of the documented modes "
                    f"({', '.join(sorted(APPROVAL_MODES))})."
                )
            if mode == "conditional":
                notes.append(
                    "approval_mode is 'conditional', so the gating logic is supplied by "
                    "the maker and is not visible to this inventory. Review it directly."
                )
            return mode, True, notes
        notes.append(
            "approval_mode is set from an expression rather than a literal, so the "
            "effective mode cannot be read statically. Confirm it by reading the code."
        )
        return DYNAMIC_APPROVAL_MODE, True, notes
    return DEFAULT_APPROVAL_MODE, False, notes


def read_tool_name(decorator: ast.expr, fallback: str) -> str:
    if isinstance(decorator, ast.Call):
        for keyword in decorator.keywords:
            if (
                keyword.arg == "name"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                return keyword.value.value
    return fallback


def call_name(node: ast.Call) -> str:
    target = node.func
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def open_write_evidence(node: ast.Call) -> str | None:
    """Return evidence when an ``open()`` call can write, else ``None``."""
    if call_name(node) != "open":
        return None
    mode_node: ast.expr | None = None
    if len(node.args) >= 2:
        mode_node = node.args[1]
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if mode_node is None:
        return None  # open(path) defaults to 'r'.
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        mode = mode_node.value.strip()
        if WRITE_FILE_MODE_FLAGS.intersection(mode):
            return f"open(..., {mode!r}) call"
        return None
    # A mode computed at runtime could be anything. Calling it read-only would
    # hide a possible write, which is the wrong direction for an inventory whose
    # output feeds a gating decision, so surface it and let a human resolve it.
    return "open() call whose mode is computed at runtime"


def body_write_signals(node: ast.AST) -> list[Signal]:
    signals: list[Signal] = []
    seen: set[tuple[str, str]] = set()

    def record(category: str, where: str, evidence: str) -> None:
        key = (category, evidence)
        if key in seen:
            return
        seen.add(key)
        signals.append(Signal(category=category, where=where, evidence=evidence))

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = call_name(child)
            if not name:
                continue
            open_evidence = open_write_evidence(child)
            if open_evidence:
                record("write", "body", open_evidence)
                continue
            tokens = set(tokenize(name))
            hits = tokens & BODY_WRITE_VERBS
            if hits:
                record("write", "body", f"calls {name}()")
            if isinstance(child.func, ast.Attribute) and name in HTTP_WRITE_METHODS:
                record("write", "body", f"HTTP-style {name.upper()} call")
            external = tokens & EXTERNAL_TERMS
            if external:
                record("external", "body", f"calls {name}()")
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            if SQL_WRITE.search(child.value):
                record("write", "body", "contains a data-modifying SQL statement")
    return signals


def loop_contains_write(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            if body_write_signals(child):
                return True
    return False


def text_signals(name: str, docstring: str) -> list[Signal]:
    signals: list[Signal] = []
    name_tokens = set(tokenize(name))
    doc_tokens = set(tokenize(docstring))

    for hit in sorted(name_tokens & NAME_WRITE_VERBS):
        signals.append(Signal("write", "name", f"tool name contains {hit!r}"))
    for hit in sorted(doc_tokens & NAME_WRITE_VERBS):
        signals.append(Signal("write", "docstring", f"docstring contains {hit!r}"))
    for hit in sorted(name_tokens & EXTERNAL_TERMS):
        signals.append(Signal("external", "name", f"tool name contains {hit!r}"))
    for hit in sorted(doc_tokens & EXTERNAL_TERMS):
        signals.append(Signal("external", "docstring", f"docstring contains {hit!r}"))
    for hit in sorted(name_tokens & BLAST_NAME_TERMS):
        signals.append(Signal("blast", "name", f"tool name contains {hit!r}"))
    return signals


def parameter_signals(signatures: list[str]) -> list[Signal]:
    signals: list[Signal] = []
    for signature in signatures:
        parameter = signature.split(":", 1)[0].strip().lstrip("*")
        if parameter.lower() in BLAST_PARAM_NAMES or parameter.lower().endswith(
            ("_ids", "_list")
        ):
            signals.append(
                Signal("blast", "parameters", f"parameter {parameter!r} names a collection")
            )
        if ":" in signature and COLLECTION_ANNOTATION.search(signature.split(":", 1)[1]):
            signals.append(
                Signal(
                    "blast",
                    "parameters",
                    f"parameter {parameter!r} is annotated as a collection",
                )
            )
    return signals


def build_record(
    node: ast.AST,
    decorator: ast.expr,
    source: str,
    provenance: str = ToolProvenance.CONFIRMED,
) -> ToolRecord:
    function_name = node.name
    tool_name = read_tool_name(decorator, function_name)
    approval_mode, explicit, notes = read_approval_mode(decorator)
    docstring = (ast.get_docstring(node) or "").strip()
    summary = docstring.splitlines()[0].strip() if docstring else ""
    signatures = parameter_signatures(node)

    signals: list[Signal] = []
    signals.extend(text_signals(tool_name, summary))
    signals.extend(body_write_signals(node))
    signals.extend(parameter_signals(signatures))
    if loop_contains_write(node):
        signals.append(Signal("blast", "body", "writes inside a loop"))

    categories = {signal.category for signal in signals}
    proposed_write = "write" if "write" in categories else "read"
    proposed_visibility = "external" if "external" in categories else "internal-or-unknown"
    proposed_blast = "many" if "blast" in categories else "one"

    if proposed_write == "read" and proposed_visibility == "external":
        notes.append(
            "External wording was detected but no write signal was found. Confirm whether "
            "this tool only reads externally-owned data."
        )

    if provenance == ToolProvenance.UNATTRIBUTED:
        notes.append(
            f"This decorator could not be traced to an {AGENT_FRAMEWORK} import in "
            "this file. It is listed as best-effort in case the import is indirect. "
            "Confirm it is an Agent Framework tool before relying on the "
            "approval_mode column."
        )

    return ToolRecord(
        name=tool_name,
        function=function_name,
        language="python",
        detection=(
            "parsed" if provenance == ToolProvenance.CONFIRMED else "best-effort"
        ),
        source=source,
        line=node.lineno,
        docstring=summary,
        parameters=signatures,
        approval_mode=approval_mode,
        approval_mode_explicit=explicit,
        gated=approval_mode in GATING_MODES,
        proposed_write=proposed_write,
        proposed_visibility=proposed_visibility,
        proposed_blast=proposed_blast,
        signals=signals,
        notes=notes,
    )


def scan_python(text: str, source: str) -> tuple[list[ToolRecord], list[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return [], [f"{source}: skipped, could not be parsed as Python ({error.msg})."]

    origins = collect_tool_decorator_aliases(tree)
    records: list[ToolRecord] = []
    skipped: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            provenance = tool_decorator_provenance(decorator, origins)
            if provenance is None:
                continue
            if provenance == ToolProvenance.FOREIGN:
                target = decorator_target(decorator)
                origin = origins.foreign.get(getattr(target, "id", ""), "elsewhere")
                skipped[origin] = skipped.get(origin, 0) + 1
                break
            records.append(build_record(node, decorator, source, provenance))
            break

    notes: list[str] = []
    for origin in sorted(skipped):
        count = skipped[origin]
        notes.append(
            f"{source}: skipped {quantify(count, 'decorated function')} because "
            f"'tool' comes from {origin}, not {AGENT_FRAMEWORK}."
        )
    return records, notes


# --------------------------------------------------------------------------
# Go analysis (bounded, best-effort)
# --------------------------------------------------------------------------


def scan_go(text: str, source: str) -> tuple[list[ToolRecord], list[str]]:
    wrapped: dict[str, int] = {}
    for match in GO_APPROVAL_WRAP.finditer(text):
        wrapped.setdefault(match.group(1), text.count("\n", 0, match.start()) + 1)

    bindings: dict[str, int] = {}
    for match in GO_TOOL_BINDING.finditer(text):
        identifier, constructor = match.group(1), match.group(2)
        if constructor == "ApprovalRequiredFunc":
            continue
        # Measure from the identifier, not the match: the pattern's leading
        # '^\s*' swallows the preceding newline, so match.start() reports the
        # blank line above any declaration that has one.
        bindings.setdefault(identifier, text.count("\n", 0, match.start(1)) + 1)

    records: list[ToolRecord] = []
    for identifier in sorted(set(bindings) | set(wrapped)):
        gated = identifier in wrapped
        notes = [
            "Go detection is best-effort: a bounded regular-expression match, not "
            "a parse. Signals are not extracted, so answer all four questions "
            "manually."
        ]
        # A tool declared in another file has no binding here. Point at the
        # approval call rather than emitting a line 0 nobody can navigate to.
        if identifier in bindings:
            line = bindings[identifier]
        else:
            line = wrapped[identifier]
            notes.append(
                "The declaration was not found in this file, so the line points at "
                "the tool.ApprovalRequiredFunc call, not at the tool itself."
            )
        records.append(
            ToolRecord(
                name=identifier,
                function=identifier,
                language="go",
                detection="best-effort",
                source=source,
                line=line,
                docstring="",
                parameters=[],
                approval_mode="always_require" if gated else DEFAULT_APPROVAL_MODE,
                approval_mode_explicit=gated,
                gated=gated,
                proposed_write="read",
                proposed_visibility="internal-or-unknown",
                proposed_blast="one",
                signals=[],
                notes=notes,
            )
        )
    return records, []


# --------------------------------------------------------------------------
# Walking
# --------------------------------------------------------------------------


def source_suffixes(languages: set[str]) -> set[str]:
    suffixes = set()
    if "python" in languages:
        suffixes.add(".py")
    if "go" in languages:
        suffixes.add(".go")
    return suffixes


def iter_source_files(root: Path, languages: set[str], include_tests: bool):
    suffixes = source_suffixes(languages)

    if root.is_file():
        # An explicit path is an explicit request. Honour it even when the name
        # looks like a test, rather than returning a silently empty inventory
        # and making the caller guess that --include-tests was the problem.
        if root.suffix in suffixes:
            yield root
        return

    candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune in place, and prune by directory NAME rather than by testing the
        # whole path. Filtering after root.rglob("*") still pays to walk and
        # allocate every path inside node_modules and .git, which is the cost
        # SKIP_DIRECTORIES exists to avoid. It is also wrong: a path test
        # inspects the ancestors above root too, so scanning a repo that happens
        # to live under a directory called build, dist, env or venv would skip
        # every file and report an empty inventory. Only names at or below root
        # are ours to judge.
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRECTORIES]
        if not include_tests:
            dirnames[:] = [name for name in dirnames if name != "tests"]
        current = Path(dirpath)
        candidates.extend(
            current / name for name in filenames if Path(name).suffix in suffixes
        )

    # Sorted as a whole, not per directory, so the order does not depend on the
    # traversal and the output stays deterministic across platforms.
    for path in sorted(candidates):
        # Only the filename is tested here, for the same reason: a directory
        # named tests below root has already been pruned, so anything a path
        # test could still add is an ancestor above root, which is not a
        # statement about the caller's code. Pointing the inventory at a
        # directory that is itself named tests is an explicit request and is
        # honoured, exactly as naming a single test file is.
        if not include_tests and TEST_FILE.search(path.name):
            continue
        yield path


def relative_source(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root if root.is_dir() else root.parent).as_posix()
    except ValueError:
        return path.as_posix()


def build_inventory(
    root: Path, languages: set[str], include_tests: bool
) -> Inventory:
    inventory = Inventory(root=root.as_posix())
    if root.is_file() and root.suffix not in source_suffixes(languages):
        inventory.notes.append(
            f"{root.as_posix()}: skipped, this inventory reads "
            f"{', '.join(sorted(source_suffixes(languages))) or 'no suffixes'} and "
            "was pointed at a file it does not read."
        )
    for path in iter_source_files(root, languages, include_tests):
        source = relative_source(path, root)
        try:
            # utf-8-sig, not utf-8: CPython accepts a source file with a BOM, so
            # a Windows-authored tool file must not be reported as unparseable.
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError) as error:
            inventory.notes.append(f"{source}: skipped, could not be read ({error}).")
            continue
        if path.suffix == ".py":
            records, notes = scan_python(text, source)
        else:
            records, notes = scan_go(text, source)
        inventory.tools.extend(records)
        inventory.notes.extend(notes)

    inventory.tools.sort(key=lambda record: (record.source, record.line, record.name))
    return inventory


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

HONESTY_FOOTER = (
    "Signals are advisory evidence, not verdicts. This inventory cannot tell you who can\n"
    "reverse a write or whether a result leaves the organisation. Answer the four questions\n"
    "in references/surfaces-and-contracts.md, then record the verdict and its reason."
)


def quantify(count: int, singular: str, plural: str | None = None) -> str:
    """Render a count with a noun that agrees with it: '1 tool', '3 tools'."""
    if plural is None:
        plural = singular + "s"
    return f"{count} {singular if count == 1 else plural}"


def agree(count: int, singular: str, plural: str) -> str:
    """Pick the verb form that agrees with a count: 'looks' against 'look'."""
    return singular if count == 1 else plural


def render_table(inventory: Inventory) -> str:
    headers = ["Tool", "Lang", "Approval", "Write", "External", "Blast", "Source"]
    rows = [
        [
            record.name,
            record.language,
            record.approval_mode + ("" if record.approval_mode_explicit else " (default)"),
            record.proposed_write,
            "external" if record.proposed_visibility == "external" else "unknown",
            record.proposed_blast,
            f"{record.source}:{record.line}",
        ]
        for record in inventory.tools
    ]

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells: list[str]) -> str:
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)).rstrip()

    out = [line(headers), line(["-" * width for width in widths])]
    out.extend(line(row) for row in rows)
    if not rows:
        out.append("(no tools found)")

    counts = inventory.counts()
    out.append("")
    out.append(
        f"{quantify(counts['tools'], 'tool')}: "
        f"{counts['gated']} gated, {counts['ungated']} ungated."
    )
    out.append(
        "Signals: "
        f"{quantify(counts['write_signalled'], 'write signal')}, "
        f"{quantify(counts['external_signalled'], 'external-visibility signal')}, "
        f"{quantify(counts['many_signalled'], 'blast-radius signal')}."
    )
    out.append(
        "Needs a ruling: "
        f"{quantify(counts['ungated_write'], 'ungated tool')} with a write signal, "
        f"of which {counts['ungated_write_external']} also "
        f"{agree(counts['ungated_write_external'], 'looks', 'look')} externally visible."
    )
    if counts["best_effort"]:
        out.append(
            f"{quantify(counts['best_effort'], 'entry', 'entries')} "
            f"{agree(counts['best_effort'], 'is a best-effort match', 'are best-effort matches')} "
            "and may be incomplete."
        )

    attention = [record for record in inventory.tools if record.needs_attention]
    if attention:
        out.append("")
        out.append(
            f"Ungated {agree(len(attention), 'tool', 'tools')} with a write signal:"
        )
        for record in attention:
            evidence = "; ".join(
                signal.evidence for signal in record.signals if signal.category == "write"
            )
            out.append(f"  {record.name}: {evidence or 'no evidence recorded'}")

    notes = inventory.notes + [
        f"{record.name}: {note}" for record in inventory.tools for note in record.notes
    ]
    if notes:
        out.append("")
        out.append("Notes:")
        out.extend(f"  {note}" for note in notes)

    out.append("")
    out.append(HONESTY_FOOTER)
    return "\n".join(out)


def render_json(inventory: Inventory) -> str:
    payload = {
        "inventory": INVENTORY_NAME,
        "version": INVENTORY_VERSION,
        "root": inventory.root,
        "counts": inventory.counts(),
        "tools": [asdict(record) for record in inventory.tools],
        "notes": inventory.notes,
        "disclaimer": " ".join(HONESTY_FOOTER.split()),
    }
    return json.dumps(payload, indent=2, sort_keys=False)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inventory_tools.py",
        description=(
            "Inventory agent tools and their declared approval mode, with advisory "
            "signals for the four gating questions."
        ),
    )
    parser.add_argument("path", help="File or directory to scan.")
    parser.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    parser.add_argument(
        "--lang",
        choices=("auto", "python", "go"),
        default="auto",
        help="Restrict the scan to one language. 'auto' scans Python and Go.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("none", "ungated-write", "ungated-write-external"),
        default="none",
        help="Exit with status 1 when the named condition is present.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help=(
            "Include test files and tests/ directories when scanning a directory. "
            "They are skipped by default. A file passed directly is always read."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"{INVENTORY_NAME} {INVENTORY_VERSION}"
    )
    return parser


def gate_triggered(inventory: Inventory, condition: str) -> bool:
    if condition == "ungated-write":
        return any(record.needs_attention for record in inventory.tools)
    if condition == "ungated-write-external":
        return any(record.needs_urgent_attention for record in inventory.tools)
    return False


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        print(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.",
            file=sys.stderr,
        )
        return 2

    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.exists():
        print(f"Path not found: {root.as_posix()}", file=sys.stderr)
        return 2

    languages = {"python", "go"} if args.lang == "auto" else {args.lang}
    inventory = build_inventory(root, languages, args.include_tests)

    if args.format == "json":
        print(render_json(inventory))
    else:
        print(render_table(inventory))

    return 1 if gate_triggered(inventory, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
