#!/usr/bin/env python3
"""Deterministic, field-safe DOCX template inspection and filling.

The engine edits only visible WordprocessingML text in the main document,
headers, and footers. It preserves all other package parts and never rewrites
Word field instructions (PAGE, NUMPAGES, TOC, cross-references, and similar).

Template contract:
  Scalars:        {{document.title}} or {{sections.purpose}}
  Repeating rows: {{items[].name}} (one outer array path per template table row;
                  nested arrays supported: {{items[].sub[].field}})

Usage:
  python docx_template.py inspect template.docx --output manifest.json
  python docx_template.py fill template.docx data.json output.docx
  python docx_template.py validate output.docx --template template.docx
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_STRICT = "http://purl.oclc.org/ooxml/wordprocessingml/main"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}
XML_SPACE = f"{{{XML}}}space"

REQUIRED_PARTS = {"[Content_Types].xml", "word/document.xml"}
SUPPORTED_PART_RE = re.compile(r"^word/(?:document|header\d+|footer\d+)\.xml$")
TOKEN_RE = re.compile(
    r"\{\{\s*"
    r"([A-Za-z_][A-Za-z0-9_-]*(?:\[\])?"
    r"(?:\.[A-Za-z_][A-Za-z0-9_-]*(?:\[\])?)*)"
    r"\s*\}\}"
)
# Conditional block markers — each must occupy its own paragraph exclusively.
COND_IF_RE = re.compile(
    r"^\s*\{\{#if\s+(.+?)\s*\}\}\s*$"
)
COND_ELSE_RE = re.compile(r"^\s*\{\{#else\}\}\s*$")
COND_ENDIF_RE = re.compile(r"^\s*\{\{/if\}\}\s*$")
COND_SWITCH_RE = re.compile(
    r"^\s*\{\{#switch\s+([A-Za-z_][A-Za-z0-9_.]*)\s*\}\}\s*$"
)
COND_CASE_RE = re.compile(
    r"^\s*\{\{#case\s+(?:\"([^\"]*)\"|([A-Za-z0-9_.+-]*))\s*\}\}\s*$"
)
COND_ENDSWITCH_RE = re.compile(r"^\s*\{\{/switch\}\}\s*$")
# Matches any conditional marker so callers can skip them quickly.
_COND_MARKER_RE = re.compile(
    r"^\s*\{\{(?:#if\b|#else\b|/if\b|#switch\b|#case\b|/switch\b)"
)
# Candidate-token scanner used for unresolved-token detection.
# Excludes valid conditional markers so they don't surface as malformed.
TOKEN_CANDIDATE_RE = re.compile(
    r"\{\{(?!(?:#if|#else|/if|#switch|#case|/switch)\b).*?\}\}",
    re.DOTALL,
)
MAX_PACKAGE_FILES = 10_000
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
DEFAULT_MISSING = "Not specified in approved sources"


class TemplateError(RuntimeError):
    """Raised when the template contract or DOCX package is invalid."""


@dataclass
class FillReport:
    template: str
    output: str
    replaced_fields: set[str] = field(default_factory=set)
    defaulted_fields: set[str] = field(default_factory=set)
    repeated_rows: dict[str, int] = field(default_factory=dict)
    modified_parts: set[str] = field(default_factory=set)
    field_signature_preserved: bool = True
    conditional_fields: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        return {
            "template": self.template,
            "output": self.output,
            "replaced_fields": sorted(self.replaced_fields),
            "defaulted_fields": sorted(self.defaulted_fields),
            "repeated_rows": dict(sorted(self.repeated_rows.items())),
            "modified_parts": sorted(self.modified_parts),
            "field_signature_preserved": self.field_signature_preserved,
            "conditional_fields": sorted(self.conditional_fields),
        }


def _w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def _safe_parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_blank_text=False,
        recover=False,
        huge_tree=False,
    )


def _parse_xml(content: bytes, part_name: str) -> etree._Element:
    try:
        return etree.fromstring(content, parser=_safe_parser())
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise TemplateError(f"Invalid XML in {part_name}: {exc}") from exc


def _assert_transitional_namespace(root: etree._Element, part: str) -> None:
    """Raise TemplateError if *root* declares the Strict OOXML wordprocessingML namespace.

    Strict OOXML uses a different namespace URI to the Transitional profile the
    engine is built against.  Accepting a Strict package silently would leave
    every token unfound and report false success.
    """
    ns_values = set(root.nsmap.values())
    if W_STRICT in ns_values:
        raise TemplateError(
            f"Strict OOXML is not supported ({part!r} declares "
            f"{W_STRICT!r}). Open the document in Word, go to File → "
            "Save As, and choose 'Word Document (.docx)' to save it as "
            "Transitional OOXML before using this engine."
        )


def _serialize_xml(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        standalone=True,
    )


def _validate_zip_entries(infos: list[zipfile.ZipInfo]) -> None:
    if len(infos) > MAX_PACKAGE_FILES:
        raise TemplateError(
            f"DOCX contains too many package entries ({len(infos)} > "
            f"{MAX_PACKAGE_FILES})."
        )
    total = sum(info.file_size for info in infos)
    if total > MAX_UNCOMPRESSED_BYTES:
        raise TemplateError(
            f"DOCX uncompressed size is too large ({total} bytes > "
            f"{MAX_UNCOMPRESSED_BYTES})."
        )
    names = [info.filename for info in infos]
    for name in names:
        normalized = name.replace("\\", "/")
        if (
            normalized.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized)
            or ".." in normalized.split("/")
        ):
            raise TemplateError(f"DOCX contains unsafe package entry name: {name!r}.")
    if len(names) != len(set(names)):
        raise TemplateError("DOCX contains duplicate package entry names.")
    missing = REQUIRED_PARTS - set(names)
    if missing:
        raise TemplateError(
            "Not a valid DOCX package; missing: " + ", ".join(sorted(missing))
        )


def _read_package(path: str | os.PathLike[str]) -> tuple[
    dict[str, bytes], dict[str, zipfile.ZipInfo]
]:
    source = Path(path)
    if not source.is_file():
        raise TemplateError(f"DOCX file not found: {source}")
    if source.suffix.lower() != ".docx":
        raise TemplateError(f"Expected a .docx file: {source}")
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            _validate_zip_entries(infos)
            content = {info.filename: archive.read(info.filename) for info in infos}
            metadata = {info.filename: info for info in infos}
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise TemplateError(f"Cannot read DOCX package {source}: {exc}") from exc
    doc_root = _parse_xml(content["word/document.xml"], "word/document.xml")
    _assert_transitional_namespace(doc_root, "word/document.xml")
    return content, metadata


def _supported_parts(package: Mapping[str, bytes]) -> list[str]:
    return sorted(name for name in package if SUPPORTED_PART_RE.match(name))


def _text_nodes(paragraph: etree._Element) -> list[etree._Element]:
    """Visible text nodes, excluding simple and complex Word-field contents."""
    nodes: list[etree._Element] = []
    field_depth = 0
    for node in paragraph.iter():
        if node.tag == _w("fldChar"):
            kind = node.get(_w("fldCharType"), "")
            if kind == "begin":
                field_depth += 1
            elif kind == "end":
                field_depth = max(0, field_depth - 1)
            continue
        if node.tag != _w("t") or field_depth:
            continue
        if any(ancestor.tag == _w("fldSimple") for ancestor in node.iterancestors()):
            continue
        nodes.append(node)
    return nodes


def _paragraph_text(paragraph: etree._Element) -> str:
    return "".join(node.text or "" for node in _text_nodes(paragraph))


def _row_text(row: etree._Element) -> str:
    return "".join(_paragraph_text(p) for p in row.iter(_w("p")))


def _set_text(node: etree._Element, text: str) -> None:
    node.text = text
    if text[:1].isspace() or text[-1:].isspace():
        node.set(XML_SPACE, "preserve")
    elif XML_SPACE in node.attrib:
        del node.attrib[XML_SPACE]


def _find_node_offset(
    spans: list[tuple[int, int, etree._Element]], position: int, *, end: bool = False
) -> tuple[int, etree._Element, int]:
    for index, (start, stop, node) in enumerate(spans):
        if start <= position < stop or (end and position == stop and stop > start):
            return index, node, position - start
    if spans and position == spans[-1][1]:
        start, _, node = spans[-1]
        return len(spans) - 1, node, position - start
    raise TemplateError("Internal placeholder offset could not be mapped to a run.")


_ZWSP = "\u200B"


def _escape_brace_sequences(text: str) -> str:
    """Insert a zero-width space between consecutive brace chars in *text*.

    This prevents ``{{...}}`` sequences in user-supplied or missing-value
    replacement text from being flagged as unresolved placeholders by
    ``_unresolved_tokens``.  The zero-width space is invisible in Word but
    breaks both ``TOKEN_CANDIDATE_RE`` and the literal ``{{`` / ``}}`` checks.
    """
    return text.replace("{{", "{" + _ZWSP + "{").replace("}}", "}" + _ZWSP + "}")


def _replace_in_paragraph(
    paragraph: etree._Element,
    resolver: Callable[[str], str | None],
    *,
    allow_array_tokens: bool,
) -> set[str]:
    """Replace tokens even when Word split them across multiple runs."""
    nodes = _text_nodes(paragraph)
    if not nodes:
        return set()
    text = "".join(node.text or "" for node in nodes)
    matches = list(TOKEN_RE.finditer(text))
    replaced: set[str] = set()
    if not matches:
        return replaced

    spans: list[tuple[int, int, etree._Element]] = []
    cursor = 0
    for node in nodes:
        value = node.text or ""
        spans.append((cursor, cursor + len(value), node))
        cursor += len(value)

    # Reverse order keeps original offsets valid when two tokens share a run.
    for match in reversed(matches):
        key = match.group(1)
        is_array = "[]" in key
        if is_array and not allow_array_tokens:
            continue
        replacement = resolver(key)
        if replacement is None:
            continue
        # Escape any {{...}} sequences in the replacement value so they are
        # not treated as unresolved template placeholders after insertion.
        replacement = _escape_brace_sequences(replacement)

        first_i, first, first_offset = _find_node_offset(spans, match.start())
        last_i, last, last_offset = _find_node_offset(
            spans, match.end(), end=True
        )
        first_text = first.text or ""
        last_text = last.text or ""

        if first is last:
            _set_text(
                first,
                first_text[:first_offset] + replacement + first_text[last_offset:],
            )
        else:
            _set_text(first, first_text[:first_offset] + replacement)
            for node_i in range(first_i + 1, last_i):
                _set_text(spans[node_i][2], "")
            _set_text(last, last_text[last_offset:])
        replaced.add(key)
    return replaced


def _convert_newlines(root: etree._Element) -> None:
    """Turn replacement newlines into Word line-break elements."""
    for text_node in list(root.iter(_w("t"))):
        value = text_node.text or ""
        if "\n" not in value:
            continue
        parent = text_node.getparent()
        if parent is None or parent.tag != _w("r"):
            continue
        index = parent.index(text_node)
        parent.remove(text_node)
        lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for line_i, line in enumerate(lines):
            new_text = etree.Element(_w("t"))
            _set_text(new_text, line)
            parent.insert(index, new_text)
            index += 1
            if line_i != len(lines) - 1:
                parent.insert(index, etree.Element(_w("br")))
                index += 1


def _tokens_in_element(element: etree._Element) -> list[str]:
    tokens: list[str] = []
    for paragraph in element.iter(_w("p")):
        tokens.extend(match.group(1) for match in TOKEN_RE.finditer(_paragraph_text(paragraph)))
    return tokens


def _array_token(key: str) -> tuple[str, str] | None:
    """Parse the first array marker in *key*.

    Returns ``(array_path, item_path)`` where *item_path* may itself contain
    further ``[]`` markers for deeply nested arrays — callers recurse as needed.
    Returns ``None`` when the key contains no ``[]`` marker.
    """
    segments = key.split(".")
    marked = [i for i, segment in enumerate(segments) if segment.endswith("[]")]
    if not marked:
        return None
    # Split at the FIRST [] only; the remainder (item_path) may contain
    # additional [] markers for deeper nesting levels.
    index = marked[0]
    segments[index] = segments[index][:-2]
    array_path = ".".join(segments[: index + 1])
    item_path = ".".join(segments[index + 1 :])
    if not item_path:
        raise TemplateError(f"Repeating token must name an item field: {key}")
    return array_path, item_path


def _classify_array_token(
    key: str,
    path_prefix: str,
    arrays: dict[str, set[str]],
) -> None:
    """Recursively register a (possibly nested) array token into *arrays*.

    Flat dotted keys are used for each nesting level, e.g.::

        {{findings[].title}}          → arrays["findings"].add("title")
        {{findings[].hosts[].name}}   → arrays["findings.hosts"].add("name")
    """
    parsed = _array_token(key)
    if parsed is None:
        return
    array_name, item_path = parsed
    full_path = path_prefix + array_name
    if "[]" in item_path:
        # item_path is itself a nested array token; recurse to register deeper level.
        _classify_array_token(item_path, full_path + ".", arrays)
    else:
        arrays.setdefault(full_path, set()).add(item_path)


_MISSING = object()


def _lookup(data: Any, path: str) -> Any:
    current = data
    if not path:
        return current
    for segment in path.split("."):
        if isinstance(current, Mapping) and segment in current:
            current = current[segment]
        else:
            return _MISSING
    return current


def _as_text(value: Any, path: str) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    raise TemplateError(
        f"Placeholder {path!r} requires a scalar value, got "
        f"{type(value).__name__}."
    )


def _is_within_subtree(
    row: etree._Element,
    subtree: etree._Element,
) -> bool:
    """Return ``True`` only when *row* is still reachable from *subtree*.

    Walking up through ``getparent()`` must eventually reach *subtree* itself
    (which has no parent in its own tree, whether it is the document root or a
    freshly deep-copied ``w:tr`` clone that has not yet been inserted).  Rows
    inside a detached outer row terminate at that detached element instead and
    therefore return ``False``.
    """
    current = row
    while True:
        parent = current.getparent()
        if parent is None:
            return current is subtree
        current = parent


def _expand_flat_cross_product(
    template_row: etree._Element,
    outer_items: list[Any],
    local_outer_path: str,
    missing_value: str,
    report: FillReport,
    token_prefix: str,
    path_prefix: str,
    parent: etree._Element,
    insert_at_ref: list[int],
) -> None:
    """Recursively expand *template_row* for each (outer × inner × …) combination.

    Fills tokens at the current nesting level and, when further ``[]`` markers
    remain, recurses to handle the next level before inserting the final clones.
    All clones are inserted into *parent* starting at ``insert_at_ref[0]``.
    """
    next_prefix = token_prefix + local_outer_path + "[]."
    next_path = path_prefix + local_outer_path

    for outer_idx, outer_item in enumerate(outer_items):
        if not isinstance(outer_item, Mapping):
            raise TemplateError(
                f"{next_path}[{outer_idx}] must be a JSON object."
            )
        clone = copy.deepcopy(template_row)

        def resolve_leaf(
            key: str,
            _oi: Mapping[str, Any] = outer_item,
            _oidx: int = outer_idx,
        ) -> str | None:
            if not key.startswith(token_prefix):
                return None
            local = key[len(token_prefix):]
            parsed = _array_token(local)
            if parsed is None or parsed[0] != local_outer_path:
                return None
            item_path = parsed[1]
            if "[]" in item_path:
                return None  # leave nested tokens for the next recursion level
            value = _lookup(_oi, item_path)
            if value is _MISSING:
                report.defaulted_fields.add(f"{next_path}[{_oidx}].{item_path}")
                return missing_value
            report.replaced_fields.add(f"{next_path}[{_oidx}].{item_path}")
            return _as_text(value, f"{next_path}[].{item_path}")

        for paragraph in clone.iter(_w("p")):
            _replace_in_paragraph(paragraph, resolve_leaf, allow_array_tokens=True)

        # Discover remaining nested tokens in this clone.
        remaining_keys = _tokens_in_element(clone)
        prefixed = [
            (k, k[len(next_prefix):])
            for k in remaining_keys
            if k.startswith(next_prefix)
        ]
        next_array_locals = [
            (orig, loc) for orig, loc in prefixed if _array_token(loc) is not None
        ]

        if next_array_locals:
            next_outer_paths = {_array_token(loc)[0] for _, loc in next_array_locals}
            if len(next_outer_paths) != 1:
                raise TemplateError(
                    "A repeating table row may reference only one array at each "
                    "nesting level; found: "
                    + ", ".join(sorted(str(p) for p in next_outer_paths))
                )
            next_outer_path = next(iter(next_outer_paths))
            next_outer_items = _lookup(outer_item, next_outer_path)
            if next_outer_items is _MISSING:
                next_outer_items = []
                report.defaulted_fields.add(f"{next_path}.{next_outer_path}")
            if not isinstance(next_outer_items, list):
                raise TemplateError(
                    f"Nested repeating array "
                    f"{(next_path + '.' + next_outer_path)!r} requires a JSON array."
                )
            # Track item count at the next nesting level.
            next_level_key = next_path + "." + next_outer_path
            report.repeated_rows[next_level_key] = (
                report.repeated_rows.get(next_level_key, 0) + len(next_outer_items)
            )
            _expand_flat_cross_product(
                clone,
                next_outer_items,
                next_outer_path,
                missing_value,
                report,
                next_prefix,
                next_path + ".",
                parent,
                insert_at_ref,
            )
        else:
            parent.insert(insert_at_ref[0], clone)
            insert_at_ref[0] += 1


def _expand_rows_in_subtree(
    subtree: etree._Element,
    data: Mapping[str, Any],
    missing_value: str,
    report: FillReport,
    *,
    token_prefix: str = "",
    path_prefix: str = "",
) -> bool:
    """Expand all template ``w:tr`` rows found within *subtree*.

    *token_prefix* restricts which tokens are handled at this nesting depth
    (e.g. ``"findings[]."`` when recursing inside a findings clone).  *data* is
    the JSON object for the current nesting level.

    Supports two expansion modes:

    * **Case A — nested tables**: the outer template row contains a nested
      ``w:tbl`` whose own template rows carry deeper tokens.  Each outer item
      produces one clone; the recursive call expands inner rows within that
      clone using the outer item as the data root.

    * **Case B — flat cross-product**: every nested token lives directly in
      the template row's cells (not in a sub-table).  One output row is
      produced per combination of outer × inner × … items.
    """
    changed = False
    for row in list(subtree.iter(_w("tr"))):
        # Skip the subtree element itself when called recursively on a w:tr clone,
        # and skip any row that is no longer reachable from subtree — this covers
        # both directly removed template rows (getparent() is None) and inner rows
        # of a removed outer row (getparent() points into a detached fragment).
        if row is subtree or not _is_within_subtree(row, subtree):
            continue

        all_keys = _tokens_in_element(row)
        # Restrict to tokens that belong to the current prefix level.
        local_map: dict[str, str] = {
            k: k[len(token_prefix):]
            for k in all_keys
            if k.startswith(token_prefix)
        }
        array_locals = [
            (orig, local)
            for orig, local in local_map.items()
            if _array_token(local) is not None
        ]
        if not array_locals:
            continue

        # All tokens in this row must share a single outermost array at this level.
        local_outer_paths = {_array_token(local)[0] for _, local in array_locals}
        if len(local_outer_paths) != 1:
            raise TemplateError(
                "A repeating table row may reference only one array at each "
                "nesting level; found: "
                + ", ".join(sorted(str(p) for p in local_outer_paths))
            )
        local_outer_path = next(iter(local_outer_paths))

        outer_items = _lookup(data, local_outer_path)
        if outer_items is _MISSING:
            outer_items = []
            report.defaulted_fields.add(path_prefix + local_outer_path)
        if not isinstance(outer_items, list):
            raise TemplateError(
                f"Repeating row {(path_prefix + local_outer_path)!r} "
                f"requires a JSON array."
            )

        parent = row.getparent()
        if parent is None:
            raise TemplateError("Repeating table row has no parent table.")

        next_prefix = token_prefix + local_outer_path + "[]."
        next_path = path_prefix + local_outer_path

        # Separate nested (multi-level) tokens from leaf tokens.
        nested_local_tokens = [
            (orig, local)
            for orig, local in array_locals
            if "[]" in _array_token(local)[1]  # type: ignore[index]
        ]

        # Determine which nested tokens live in sub-table rows vs. direct cells.
        sub_rows = [r for r in row.iter(_w("tr")) if r is not row]
        sub_row_token_set: set[str] = {
            t for sr in sub_rows for t in _tokens_in_element(sr)
        }
        nested_direct = [
            (o, l) for o, l in nested_local_tokens if o not in sub_row_token_set
        ]
        nested_in_sub = [
            (o, l) for o, l in nested_local_tokens if o in sub_row_token_set
        ]

        if nested_direct and nested_in_sub:
            raise TemplateError(
                "A template row may not mix nested-array tokens in direct cells "
                "with nested-array tokens inside a nested table; "
                "use separate tables for each array level."
            )

        # For flat cross-product rows, every nested token at this level must
        # reference the same next-level array path.
        if nested_direct:
            inner_paths: set[str] = set()
            for _, local in nested_direct:
                item_path = _array_token(local)[1]  # type: ignore[index]
                inner_parsed = _array_token(item_path)
                if inner_parsed:
                    inner_paths.add(inner_parsed[0])
            if len(inner_paths) > 1:
                raise TemplateError(
                    "A flat repeating row may reference only one nested array "
                    "at each level; found: " + ", ".join(sorted(inner_paths))
                )

        insert_at = parent.index(row)

        if nested_direct:
            # Case B — flat cross-product.
            # Track the outer item count here; _expand_flat_cross_product
            # accumulates counts for deeper levels.
            report.repeated_rows[next_path] = (
                report.repeated_rows.get(next_path, 0) + len(outer_items)
            )
            insert_at_ref = [insert_at]
            _expand_flat_cross_product(
                row,
                outer_items,
                local_outer_path,
                missing_value,
                report,
                token_prefix,
                path_prefix,
                parent,
                insert_at_ref,
            )
        else:
            # Case A or simple — one clone per outer item.
            for outer_idx, outer_item in enumerate(outer_items):
                if not isinstance(outer_item, Mapping):
                    raise TemplateError(
                        f"{next_path}[{outer_idx}] must be a JSON object."
                    )
                clone = copy.deepcopy(row)

                def resolve_outer(
                    key: str,
                    _oi: Mapping[str, Any] = outer_item,
                    _oidx: int = outer_idx,
                ) -> str | None:
                    if not key.startswith(token_prefix):
                        return None
                    local = key[len(token_prefix):]
                    parsed = _array_token(local)
                    if parsed is None or parsed[0] != local_outer_path:
                        return None
                    item_path = parsed[1]
                    if "[]" in item_path:
                        return None  # leave nested for the recursive inner pass
                    value = _lookup(_oi, item_path)
                    if value is _MISSING:
                        report.defaulted_fields.add(
                            f"{next_path}[{_oidx}].{item_path}"
                        )
                        return missing_value
                    report.replaced_fields.add(f"{next_path}[{_oidx}].{item_path}")
                    return _as_text(value, f"{next_path}[].{item_path}")

                for paragraph in clone.iter(_w("p")):
                    _replace_in_paragraph(
                        paragraph, resolve_outer, allow_array_tokens=True
                    )

                # Recursively expand nested sub-table rows within this clone (Case A).
                if nested_local_tokens:
                    _expand_rows_in_subtree(
                        clone,
                        outer_item,
                        missing_value,
                        report,
                        token_prefix=next_prefix,
                        path_prefix=next_path + ".",
                    )

                parent.insert(insert_at, clone)
                insert_at += 1

            report.repeated_rows[next_path] = (
                report.repeated_rows.get(next_path, 0) + len(outer_items)
            )

        parent.remove(row)
        changed = True

    return changed


# ---------------------------------------------------------------------------
# Conditional block evaluation
# ---------------------------------------------------------------------------

# Splits on && or || only outside of double-quoted strings.
_LOGICAL_SPLIT_RE = re.compile(r'(\|\||&&)(?=(?:[^"]*"[^"]*")*[^"]*$)')


def _split_logical(expr: str, op: str) -> list[str]:
    """Split *expr* on *op* (``"&&"`` or ``"||"``) outside quoted strings."""
    parts: list[str] = []
    last = 0
    for m in _LOGICAL_SPLIT_RE.finditer(expr):
        if m.group(1) == op:
            parts.append(expr[last:m.start()].strip())
            last = m.end()
    parts.append(expr[last:].strip())
    return parts


def _parse_atomic(expr: str, data: Any) -> bool:
    """Evaluate a single atomic condition (no ``&&`` / ``||``) against *data*.

    Supported forms::

        path                     # truthy check
        path == "string"
        path == 42
        path == true
        path == false
        path == null
        path != <any of the above>
    """
    expr = expr.strip()

    # Detect operator — check != before == to avoid matching the = in !=
    for op in ("!=", "=="):
        idx = expr.find(op)
        if idx == -1:
            continue
        path_part = expr[:idx].strip()
        rhs_raw = expr[idx + len(op):].strip()
        value = _lookup(data, path_part)
        if value is _MISSING:
            value = None

        # Parse the RHS literal
        if rhs_raw.startswith('"') and rhs_raw.endswith('"'):
            rhs: Any = rhs_raw[1:-1]
        elif rhs_raw == "true":
            rhs = True
        elif rhs_raw == "false":
            rhs = False
        elif rhs_raw == "null":
            rhs = None
        else:
            try:
                rhs = int(rhs_raw)
            except ValueError:
                try:
                    rhs = float(rhs_raw)
                except ValueError:
                    rhs = rhs_raw

        # Coerce value to the RHS type for comparison when sensible
        if isinstance(rhs, str) and not isinstance(value, str):
            coerced = str(value) if value is not None else ""
        else:
            coerced = value

        result = coerced == rhs
        return result if op == "==" else not result

    # Bare path — truthy check
    value = _lookup(data, expr)
    if value is _MISSING or value is None or value is False:
        return False
    if isinstance(value, str) and value == "":
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    return True


def _parse_condition(expr: str, data: Any) -> bool:
    """Evaluate a condition expression against *data*.

    Supports ``&&`` (AND) and ``||`` (OR) with standard precedence
    (``&&`` binds tighter than ``||``).  Operators inside quoted strings are
    not treated as logical operators.

    Examples::

        employee.type == "permanent"
        employee.type == "permanent" && employee.status == "active"
        employee.is_senior || employee.is_lead
        employee.type == "permanent" && employee.bonus_eligible || employee.is_exec
    """
    # Split on || first (lowest precedence); each part is an AND-clause.
    or_clauses = _split_logical(expr.strip(), "||")
    for or_clause in or_clauses:
        # All atoms in an AND-clause must be true.
        and_atoms = _split_logical(or_clause, "&&")
        if all(_parse_atomic(atom, data) for atom in and_atoms):
            return True
    return False


def _classify_marker(text: str) -> tuple[str, str]:
    """Return ``(kind, payload)`` for a conditional-marker paragraph text.

    *kind* is one of ``"if"``, ``"else"``, ``"endif"``, ``"switch"``,
    ``"case"``, ``"endswitch"``, or ``""`` (not a marker).  *payload* is the
    expression or case value string, empty when not applicable.
    """
    if _COND_MARKER_RE.search(text) is None:
        return "", ""
    m = COND_IF_RE.match(text)
    if m:
        return "if", m.group(1)
    if COND_ELSE_RE.match(text):
        return "else", ""
    if COND_ENDIF_RE.match(text):
        return "endif", ""
    m = COND_SWITCH_RE.match(text)
    if m:
        return "switch", m.group(1)
    m = COND_CASE_RE.match(text)
    if m:
        # group(1) is the quoted string value, group(2) is unquoted
        return "case", m.group(1) if m.group(1) is not None else (m.group(2) or "")
    if COND_ENDSWITCH_RE.match(text):
        return "endswitch", ""
    return "", ""


def _marker_kind_in_paragraph(paragraph: etree._Element) -> tuple[str, str]:
    """Return ``(kind, payload)`` for *paragraph* if it is a conditional marker."""
    return _classify_marker(_paragraph_text(paragraph))


def _remove_elements(elements: list[etree._Element]) -> None:
    for el in elements:
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)


def _process_if_block(
    sequence: list[etree._Element],
    start: int,
    data: Any,
    report: FillReport,
) -> int:
    """Process an ``#if`` block starting at *start*.

    Collects the if-branch and optional else-branch, evaluates the condition,
    removes the losing branch and all marker paragraphs from *sequence* in
    place.  Returns the index of the element immediately after ``{{/if}}``.
    """
    marker_para = sequence[start]
    _, expr = _marker_kind_in_paragraph(marker_para)
    condition = _parse_condition(expr, data)

    # Extract the condition path for reporting
    path_part = re.split(r"\s*(?:==|!=)\s*", expr, maxsplit=1)[0].strip()
    report.conditional_fields.add(path_part)

    if_branch: list[etree._Element] = []
    else_branch: list[etree._Element] = []
    else_markers: list[etree._Element] = []
    active = if_branch
    i = start + 1
    depth = 1
    while i < len(sequence):
        el = sequence[i]
        # Only paragraphs can carry markers
        if el.tag == _w("p"):
            kind, _ = _marker_kind_in_paragraph(el)
        elif el.tag == _w("tbl"):
            # Tables can't carry top-level markers; collect into active branch
            active.append(el)
            i += 1
            continue
        else:
            kind = ""
        if kind == "if" or kind == "switch":
            depth += 1
        if depth == 1:
            if kind == "else":
                else_markers.append(el)
                active = else_branch
                i += 1
                continue
            if kind == "endif":
                # Remove the #if, #else, and /if marker paragraphs plus losing branch.
                _remove_elements([marker_para] + else_markers + [el])
                _remove_elements(else_branch if condition else if_branch)
                return i + 1
        if kind in ("if", "else", "endif", "switch", "case", "endswitch"):
            if depth > 1 and kind in ("endif", "endswitch"):
                depth -= 1
        active.append(el)
        i += 1

    raise TemplateError("Conditional block {{#if}} has no matching {{/if}}.")


def _process_switch_block(
    sequence: list[etree._Element],
    start: int,
    data: Any,
    report: FillReport,
) -> int:
    """Process a ``#switch`` block starting at *start*.

    Evaluates the switch value, collects all ``#case`` branches, keeps only
    the matching one (first match wins), and removes all others plus all
    marker paragraphs.  Returns the index after ``{{/switch}}``.
    """
    marker_para = sequence[start]
    _, switch_path = _marker_kind_in_paragraph(marker_para)
    report.conditional_fields.add(switch_path)

    raw_value = _lookup(data, switch_path)
    switch_value = str(raw_value) if raw_value not in (_MISSING, None) else ""

    # Collect branches: list of (case_value_str, [elements])
    branches: list[tuple[str, list[etree._Element]]] = []
    current_case: str | None = None
    current_elements: list[etree._Element] = []
    i = start + 1

    while i < len(sequence):
        el = sequence[i]
        if el.tag == _w("p"):
            kind, payload = _marker_kind_in_paragraph(el)
        else:
            kind, payload = "", ""

        if kind == "case":
            if current_case is not None:
                branches.append((current_case, current_elements))
            current_case = payload
            current_elements = []
            i += 1
            continue
        if kind == "endswitch":
            if current_case is not None:
                branches.append((current_case, current_elements))
            # Remove the switch and endswitch markers
            _remove_elements([marker_para, el])
            # Remove all case-marker paragraphs and losing branches
            matched = False
            for case_val, case_elements in branches:
                if not matched and case_val == switch_value:
                    matched = True
                else:
                    _remove_elements(case_elements)
            # Find and remove case-marker paragraphs (they live in sequence)
            for j in range(start + 1, i):
                cand = sequence[j]
                if cand.tag == _w("p"):
                    k2, _ = _marker_kind_in_paragraph(cand)
                    if k2 == "case":
                        _remove_elements([cand])
            return i + 1
        if current_case is not None:
            current_elements.append(el)
        i += 1

    raise TemplateError("Conditional block {{#switch}} has no matching {{/switch}}.")


def _evaluate_conditionals_in_sequence(
    sequence: list[etree._Element],
    data: Any,
    report: FillReport,
) -> None:
    """Process all ``#if`` and ``#switch`` blocks in *sequence* in order.

    *sequence* is a list of sibling elements (body children or table-row
    children).  Conditional markers must be ``w:p`` elements.  Elements
    removed from the XML tree are also dropped from *sequence* in place so
    subsequent passes see the correct state.
    """
    i = 0
    while i < len(sequence):
        el = sequence[i]
        if el.tag != _w("p"):
            i += 1
            continue
        kind, _ = _marker_kind_in_paragraph(el)
        if kind == "if":
            # Capture parent before any removal detaches the marker paragraph.
            parent = el.getparent()
            _process_if_block(sequence, i, data, report)
            if parent is not None:
                existing = set(id(e) for e in parent)
                sequence[:] = [e for e in sequence if id(e) in existing]
            i = 0  # restart after modification
        elif kind == "switch":
            parent = el.getparent()
            _process_switch_block(sequence, i, data, report)
            if parent is not None:
                existing = set(id(e) for e in parent)
                sequence[:] = [e for e in sequence if id(e) in existing]
            i = 0
        else:
            i += 1


def _evaluate_conditionals(
    root: etree._Element,
    data: Any,
    report: FillReport,
) -> bool:
    """Evaluate all conditional blocks in *root* and remove false branches.

    Processes two levels:
    1. Direct children of ``w:body`` (body-level blocks).
    2. Direct ``w:tr`` children of each ``w:tbl`` (row-level blocks, where the
       marker paragraph lives in the first cell of a row).

    Returns ``True`` if any element was removed.
    """
    body = root.find(_w("body"))
    if body is None:
        # Headers/footers have a direct sequence of paragraphs, not a w:body.
        sequence = list(root)
        before = len(sequence)
        _evaluate_conditionals_in_sequence(sequence, data, report)
        return len(list(root)) != before

    changed = False

    # Body-level pass
    sequence = list(body)
    before_count = len(sequence)
    _evaluate_conditionals_in_sequence(sequence, data, report)
    if len(list(body)) != before_count:
        changed = True

    # Row-level pass: iterate every table in the document
    for tbl in root.iter(_w("tbl")):
        rows = list(tbl.findall(_w("tr")))
        if not rows:
            continue
        before_rows = len(rows)
        # Build a sequence of row elements; treat the first cell's first
        # paragraph text as the potential marker for each row.
        row_sequence = list(rows)
        _evaluate_conditionals_in_row_sequence(row_sequence, data, report)
        if len(tbl.findall(_w("tr"))) != before_rows:
            changed = True

    return changed


def _evaluate_conditionals_in_row_sequence(
    rows: list[etree._Element],
    data: Any,
    report: FillReport,
) -> None:
    """Process conditional markers that live in the first cell of table rows.

    A row is treated as a marker row when its **entire** visible text (across
    all cells) matches a conditional marker pattern.
    """
    i = 0
    while i < len(rows):
        row = rows[i]
        row_text = _row_text(row)
        kind, _ = _classify_marker(row_text)
        if kind not in ("if", "switch"):
            i += 1
            continue

        # Capture the parent table NOW, before any removal detaches the row.
        tbl = row.getparent()

        if kind == "if":
            _, expr = _classify_marker(row_text)
            condition = _parse_condition(expr, data)
            path_part = re.split(r"\s*(?:==|!=)\s*", expr, maxsplit=1)[0].strip()
            report.conditional_fields.add(path_part)

            if_rows: list[etree._Element] = []
            else_rows: list[etree._Element] = []
            else_marker_rows: list[etree._Element] = []
            active: list[etree._Element] = if_rows
            j = i + 1
            found_end = False
            while j < len(rows):
                r = rows[j]
                rt = _row_text(r)
                k2, _ = _classify_marker(rt)
                if k2 == "else":
                    else_marker_rows.append(r)
                    active = else_rows
                    j += 1
                    continue
                if k2 == "endif":
                    _remove_elements([row] + else_marker_rows + [r])
                    _remove_elements(else_rows if condition else if_rows)
                    if tbl is not None:
                        existing = set(id(e) for e in tbl)
                        rows[:] = [e for e in rows if id(e) in existing]
                    i = 0
                    found_end = True
                    break
                active.append(r)
                j += 1
            if not found_end:
                raise TemplateError(
                    "Conditional row block {{#if}} has no matching {{/if}}."
                )

        elif kind == "switch":
            _, switch_path = _classify_marker(row_text)
            report.conditional_fields.add(switch_path)
            raw_value = _lookup(data, switch_path)
            switch_value = (
                str(raw_value) if raw_value not in (_MISSING, None) else ""
            )

            branches: list[tuple[str, list[etree._Element]]] = []
            current_case: str | None = None
            current_rows: list[etree._Element] = []
            j = i + 1
            found_end = False
            while j < len(rows):
                r = rows[j]
                rt = _row_text(r)
                k2, payload = _classify_marker(rt)
                if k2 == "case":
                    if current_case is not None:
                        branches.append((current_case, current_rows))
                    current_case = payload
                    current_rows = []
                    j += 1
                    continue
                if k2 == "endswitch":
                    if current_case is not None:
                        branches.append((current_case, current_rows))
                    # Remove switch/endswitch marker rows and losing branches
                    _remove_elements([row, r])
                    matched = False
                    for case_val, case_rows in branches:
                        if not matched and case_val == switch_value:
                            matched = True
                        else:
                            _remove_elements(case_rows)
                    # Remove all case-marker rows between i+1 and j
                    for rr in rows[i + 1: j]:
                        if _classify_marker(_row_text(rr))[0] == "case":
                            _remove_elements([rr])
                    if tbl is not None:
                        existing = set(id(e) for e in tbl)
                        rows[:] = [e for e in rows if id(e) in existing]
                    i = 0
                    found_end = True
                    break
                if current_case is not None:
                    current_rows.append(r)
                j += 1
            if not found_end:
                raise TemplateError(
                    "Conditional row block {{#switch}} has no matching {{/switch}}."
                )
        else:
            i += 1


def _expand_repeating_rows(
    root: etree._Element,
    data: Mapping[str, Any],
    missing_value: str,
    report: FillReport,
) -> bool:
    return _expand_rows_in_subtree(root, data, missing_value, report)


def _replace_scalars(
    root: etree._Element,
    data: Mapping[str, Any],
    missing_value: str,
    report: FillReport,
) -> bool:
    changed = False

    def resolve_scalar(key: str) -> str | None:
        if "[]" in key:
            return None
        value = _lookup(data, key)
        if value is _MISSING:
            report.defaulted_fields.add(key)
            return missing_value
        report.replaced_fields.add(key)
        return _as_text(value, key)

    for paragraph in root.iter(_w("p")):
        replaced = _replace_in_paragraph(
            paragraph, resolve_scalar, allow_array_tokens=False
        )
        changed = changed or bool(replaced)
    return changed


def _field_signature(root: etree._Element) -> dict[str, Any]:
    instructions = [
        re.sub(r"\s+", " ", (node.text or "").strip())
        for node in root.iter(_w("instrText"))
    ]
    simple = [
        re.sub(r"\s+", " ", (node.get(_w("instr")) or "").strip())
        for node in root.iter(_w("fldSimple"))
    ]
    fld_chars: dict[str, int] = {}
    for node in root.iter(_w("fldChar")):
        kind = node.get(_w("fldCharType"), "")
        fld_chars[kind] = fld_chars.get(kind, 0) + 1
    return {
        "instructions": instructions,
        "simple_fields": simple,
        "field_chars": dict(sorted(fld_chars.items())),
    }


def _package_field_signature(package: Mapping[str, bytes]) -> dict[str, Any]:
    signature: dict[str, Any] = {}
    for part in _supported_parts(package):
        root = _parse_xml(package[part], part)
        part_sig = _field_signature(root)
        if (
            part_sig["instructions"]
            or part_sig["simple_fields"]
            or part_sig["field_chars"]
        ):
            signature[part] = part_sig
    return signature


def _scan_part(
    root: etree._Element,
) -> tuple[set[str], dict[str, set[str]], list[str], set[str]]:
    scalar: set[str] = set()
    arrays: dict[str, set[str]] = {}
    malformed: list[str] = []
    conditional_paths: set[str] = set()
    for paragraph in root.iter(_w("p")):
        text = _paragraph_text(paragraph)
        # Skip conditional marker paragraphs — they are not token placeholders.
        kind, payload = _classify_marker(text)
        if kind in ("if", "switch"):
            path_part = re.split(r"\s*(?:==|!=)\s*", payload, maxsplit=1)[0].strip()
            conditional_paths.add(path_part)
            continue
        if kind in ("else", "endif", "case", "endswitch"):
            continue
        valid_spans = {match.span() for match in TOKEN_RE.finditer(text)}
        for candidate in TOKEN_CANDIDATE_RE.finditer(text):
            if candidate.span() not in valid_spans:
                malformed.append(candidate.group(0))
        without_valid_tokens = TOKEN_RE.sub("", text)
        if "{{" in without_valid_tokens or "}}" in without_valid_tokens:
            excerpt = without_valid_tokens.strip()
            malformed.append(excerpt[:120] or "unmatched placeholder braces")
        for match in TOKEN_RE.finditer(text):
            key = match.group(1)
            parsed = _array_token(key)
            if parsed is None:
                scalar.add(key)
            else:
                _classify_array_token(key, "", arrays)
    return scalar, arrays, malformed, conditional_paths


def inspect_template(path: str | os.PathLike[str]) -> dict[str, Any]:
    package, _ = _read_package(path)
    scalars: set[str] = set()
    arrays: dict[str, set[str]] = {}
    malformed: list[str] = []
    conditional_paths: set[str] = set()
    by_part: dict[str, dict[str, Any]] = {}
    for part in _supported_parts(package):
        root = _parse_xml(package[part], part)
        part_scalars, part_arrays, part_malformed, part_cond = _scan_part(root)
        scalars.update(part_scalars)
        malformed.extend(part_malformed)
        conditional_paths.update(part_cond)
        for array_path, fields in part_arrays.items():
            arrays.setdefault(array_path, set()).update(fields)
        by_part[part] = {
            "scalar_placeholders": sorted(part_scalars),
            "repeating_arrays": {
                key: sorted(value) for key, value in sorted(part_arrays.items())
            },
            "conditional_paths": sorted(part_cond),
        }
    if malformed:
        raise TemplateError(
            "Malformed placeholder(s): " + ", ".join(sorted(set(malformed)))
        )
    return {
        "template": Path(path).name,
        "scalar_placeholders": sorted(scalars),
        "repeating_arrays": {
            key: sorted(value) for key, value in sorted(arrays.items())
        },
        "conditional_paths": sorted(conditional_paths),
        "parts": by_part,
        "word_fields": _package_field_signature(package),
    }


def _unresolved_tokens(package: Mapping[str, bytes]) -> list[dict[str, str]]:
    unresolved: list[dict[str, str]] = []
    for part in _supported_parts(package):
        root = _parse_xml(package[part], part)
        for paragraph in root.iter(_w("p")):
            text = _paragraph_text(paragraph)
            # In a filled document every conditional marker must have been
            # removed by _evaluate_conditionals.  Any that remain are stray
            # template syntax — report them as unresolved tokens.
            if _COND_MARKER_RE.search(text):
                unresolved.append({"part": part, "token": text.strip()[:120]})
                continue
            for match in TOKEN_CANDIDATE_RE.finditer(text):
                unresolved.append({"part": part, "token": match.group(0)})
            without_candidates = TOKEN_CANDIDATE_RE.sub("", text)
            if "{{" in without_candidates or "}}" in without_candidates:
                unresolved.append(
                    {"part": part, "token": "unmatched placeholder braces"}
                )
    return unresolved


def _write_package(
    output_path: Path,
    package: Mapping[str, bytes],
    metadata: Mapping[str, zipfile.ZipInfo],
) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w") as archive:
            for name, content in package.items():
                info = metadata[name]
                archive.writestr(info, content)
    except OSError as exc:
        raise TemplateError(f"Cannot write DOCX package {output_path}: {exc}") from exc


def fill_template(
    template_path: str | os.PathLike[str],
    data: Mapping[str, Any],
    output_path: str | os.PathLike[str],
    *,
    missing_value: str = DEFAULT_MISSING,
) -> dict[str, Any]:
    source = Path(template_path).resolve()
    output = Path(output_path).resolve()
    if source == output:
        raise TemplateError("Output path must differ from the template path.")
    if output.suffix.lower() != ".docx":
        raise TemplateError("Output path must end with .docx.")
    if not isinstance(data, Mapping):
        raise TemplateError("Fill data must be a JSON object.")

    package, metadata = _read_package(source)
    original_fields = _package_field_signature(package)
    report = FillReport(template=str(source), output=str(output))

    for part in _supported_parts(package):
        root = _parse_xml(package[part], part)
        changed = _evaluate_conditionals(root, data, report)
        changed = _expand_repeating_rows(root, data, missing_value, report) or changed
        changed = _replace_scalars(root, data, missing_value, report) or changed
        if changed:
            _convert_newlines(root)
            package[part] = _serialize_xml(root)
            report.modified_parts.add(part)

    unresolved = _unresolved_tokens(package)
    if unresolved:
        details = ", ".join(
            f"{item['token']} in {item['part']}" for item in unresolved
        )
        raise TemplateError(f"Unresolved placeholder(s) remain: {details}")

    output_fields = _package_field_signature(package)
    report.field_signature_preserved = output_fields == original_fields
    if not report.field_signature_preserved:
        raise TemplateError(
            "Word field instructions changed during filling; output was not written."
        )

    # Write to a sibling temp file first so the requested output path is never
    # created unless validation succeeds.  On any failure the temp file is
    # removed and the output path is left untouched.
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(
            suffix=".docx", dir=output.parent, prefix=".tmp-fill-"
        )
    except OSError as exc:
        raise TemplateError(f"Cannot write DOCX package {output}: {exc}") from exc
    tmp_path = Path(tmp_name)
    try:
        os.close(tmp_fd)
        _write_package(tmp_path, package, metadata)
        validation = validate_docx(tmp_path, template_path=source)
        tmp_path.replace(output)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    result = report.as_dict()
    result["validation"] = validation
    return result


def validate_docx(
    path: str | os.PathLike[str],
    *,
    template_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    package, _ = _read_package(path)
    # Parse every XML part so corrupt output fails loudly.
    for name, content in package.items():
        if name.endswith(".xml") or name.endswith(".rels"):
            _parse_xml(content, name)
    unresolved = _unresolved_tokens(package)
    if unresolved:
        details = ", ".join(
            f"{item['token']} in {item['part']}" for item in unresolved
        )
        raise TemplateError(f"Unresolved placeholder(s): {details}")

    fields = _package_field_signature(package)
    fields_preserved: bool | None = None
    if template_path is not None:
        template, _ = _read_package(template_path)
        fields_preserved = fields == _package_field_signature(template)
        if not fields_preserved:
            raise TemplateError("Word field signature differs from the template.")

    return {
        "document": str(Path(path).resolve()),
        "valid_docx": True,
        "unresolved_placeholders": [],
        "field_signature_preserved": fields_preserved,
        "word_fields": fields,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }


def _load_json(path: str | os.PathLike[str]) -> Any:
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateError(f"Cannot read JSON {path}: {exc}") from exc


def _write_json(data: Mapping[str, Any], destination: str | None) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    try:
        if destination:
            path = Path(destination)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
        print(text)
    except OSError as exc:
        raise TemplateError(f"Cannot write JSON {destination}: {exc}") from exc


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, fill, and validate deterministic Word templates."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Discover placeholders and fields")
    inspect_p.add_argument("template", help="Input .docx template")
    inspect_p.add_argument("--output", help="Optional manifest JSON path")

    fill_p = sub.add_parser("fill", help="Fill a template from JSON")
    fill_p.add_argument("template", help="Input .docx template")
    fill_p.add_argument("data", help="Template-shaped JSON object")
    fill_p.add_argument("output", help="New output .docx path")
    fill_p.add_argument(
        "--missing",
        default=DEFAULT_MISSING,
        help=f"Fallback for absent scalar values (default: {DEFAULT_MISSING!r})",
    )
    fill_p.add_argument("--summary", help="Optional fill-summary JSON path")

    validate_p = sub.add_parser("validate", help="Validate an output DOCX")
    validate_p.add_argument("document", help="DOCX to validate")
    validate_p.add_argument(
        "--template", help="Original template for Word-field comparison"
    )
    validate_p.add_argument("--output", help="Optional validation JSON path")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = _build_cli().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "inspect":
            result = inspect_template(args.template)
            _write_json(result, args.output)
        elif args.command == "fill":
            result = fill_template(
                args.template,
                _load_json(args.data),
                args.output,
                missing_value=args.missing,
            )
            _write_json(result, args.summary)
        else:
            result = validate_docx(
                args.document, template_path=args.template
            )
            _write_json(result, args.output)
        return 0
    except TemplateError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
