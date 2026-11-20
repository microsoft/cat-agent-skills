"""Namespace-aware XML parsing without serialising or consulting the filler's raw view."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import xml.etree.ElementTree as ET
from xml.parsers import expat

MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
XML_NS = "http://www.w3.org/XML/1998/namespace"
_SEPARATOR = "\x1f"
_PREFIX_LISTS = {f"{{{MC_NS}}}{name}" for name in ("Ignorable", "MustUnderstand")}
_QNAME_LISTS = {f"{{{MC_NS}}}{name}" for name in ("ProcessContent", "PreserveElements", "PreserveAttributes")}


class NamespaceError(ValueError):
    """A controlled, content-free parsing or namespace-validation failure."""

    def __init__(self) -> None:
        super().__init__("XML namespace validation failed")


@dataclass
class NamespaceTree:
    root: ET.Element
    declarations: dict[ET.Element, dict[str, str]]


def _name_start(char: str) -> bool:
    cp = ord(char)
    return char == "_" or "A" <= char <= "Z" or "a" <= char <= "z" or any(
        lo <= cp <= hi for lo, hi in (
            (0xC0, 0xD6), (0xD8, 0xF6), (0xF8, 0x2FF), (0x370, 0x37D),
            (0x37F, 0x1FFF), (0x200C, 0x200D), (0x2070, 0x218F), (0x2C00, 0x2FEF),
            (0x3001, 0xD7FF), (0xF900, 0xFDCF), (0xFDF0, 0xFFFD), (0x10000, 0xEFFFF),
        )
    )


def _ncname(value: str) -> bool:
    return bool(value) and _name_start(value[0]) and all(
        _name_start(c) or c in "-." or "0" <= c <= "9" or ord(c) == 0xB7
        or 0x300 <= ord(c) <= 0x36F or 0x203F <= ord(c) <= 0x2040
        for c in value[1:]
    )


def _tokens(value: str) -> list[str]:
    # XML list values use XML whitespace, not every Unicode whitespace character.
    return [v for v in value.replace("\t", " ").replace("\r", " ").replace("\n", " ").split(" ") if v]


def _bound_prefix(prefix: str, scope: dict[str, str]) -> bool:
    return _ncname(prefix) and bool(scope.get(prefix))


def _qname(value: str, scope: dict[str, str]) -> bool:
    pieces = value.split(":")
    if len(pieces) == 1:
        return _ncname(value)
    return (len(pieces) == 2 and _bound_prefix(pieces[0], scope)
            and (pieces[1] == "*" or _ncname(pieces[1])))


def _validate_mc(tag: str, attributes: dict[str, str], scope: dict[str, str]) -> None:
    for name, value in attributes.items():
        if name in _PREFIX_LISTS:
            if not all(_bound_prefix(v, scope) for v in _tokens(value)):
                raise NamespaceError()
        elif name in _QNAME_LISTS:
            if not all(_qname(v, scope) for v in _tokens(value)):
                raise NamespaceError()
    if tag == f"{{{MC_NS}}}Choice":
        requires = _tokens(attributes.get("Requires", ""))
        if not requires or not all(_bound_prefix(v, scope) for v in requires):
            raise NamespaceError()


def parse_namespaces(data: bytes, limits: dict[str, Any]) -> NamespaceTree:
    """Retain each element's declarations and validate MC references in their actual scope.

    Expat supplies namespace events for aliases, default namespaces and shadowing. DTDs and
    entities are rejected by parser callbacks, including when the input is not UTF-8.
    """
    if len(data) > limits.get("max_part_bytes", 52_428_800):
        raise NamespaceError()
    parser = expat.ParserCreate(namespace_separator=_SEPARATOR)
    builder = ET.TreeBuilder()
    declarations: dict[ET.Element, dict[str, str]] = {}
    pending: dict[str, str] = {}
    scopes: list[dict[str, str]] = [{"xml": XML_NS}]
    max_depth = limits.get("max_xml_depth", 256)

    def expanded(name: str) -> str:
        if _SEPARATOR not in name:
            return name
        uri, local = name.split(_SEPARATOR)
        return f"{{{uri}}}{local}"

    def namespace(prefix: str | None, uri: str | None) -> None:
        pending[prefix or ""] = uri or ""

    def start(name: str, attributes: dict[str, str]) -> None:
        if len(scopes) > max_depth:
            raise NamespaceError()
        scope = dict(scopes[-1])
        scope.update(pending)
        tag = expanded(name)
        attrs = {expanded(k): v for k, v in attributes.items()}
        _validate_mc(tag, attrs, scope)
        element = builder.start(tag, attrs)
        declarations[element] = dict(pending)
        pending.clear()
        scopes.append(scope)

    def end(name: str) -> None:
        builder.end(expanded(name))
        scopes.pop()

    def forbidden(*_args: Any) -> None:
        raise NamespaceError()

    parser.StartNamespaceDeclHandler = namespace
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = forbidden
    parser.EntityDeclHandler = forbidden
    parser.ExternalEntityRefHandler = forbidden
    try:
        parser.Parse(data, True)
        root = builder.close()
    except (expat.ExpatError, ET.ParseError, ValueError):
        raise NamespaceError() from None
    return NamespaceTree(root, declarations)


def namespaces_preserved(original: NamespaceTree, candidate: NamespaceTree,
                         first_owning_runs: set[ET.Element], text_tags: set[str],
                         text_tag: str, expected_text_lengths: dict[ET.Element, int]) -> bool:
    """Compare declaration locations independently of ElementTree's expanded-name equality."""
    def text_scopes(run: ET.Element, tree: NamespaceTree, expected: bool) -> list[tuple]:
        scopes = []
        position = region = empty_ordinal = 0
        for child in run:
            if child.tag not in text_tags:
                region += 1
                empty_ordinal = 0
                continue
            length = len(child.text or "") if child.tag == text_tag else 1
            if expected:
                length = expected_text_lengths.get(child, length)
            if tree.declarations[child]:
                scopes.append((region, position, position + length, empty_ordinal if not length else 0,
                               child.tag, tree.declarations[child]))
            position += length
            empty_ordinal = empty_ordinal + 1 if not length else 0
        return scopes

    def walk(a: ET.Element, c: ET.Element) -> bool:
        if a.tag != c.tag or original.declarations[a] != candidate.declarations[c]:
            return False
        aa, cc = list(a), list(c)
        if a in first_owning_runs:
            ta = [el for el in aa if el.tag in text_tags]
            tc = [el for el in cc if el.tag in text_tags]
            if any(len(el) for el in ta + tc):
                return False
            # Text can split into text/tab/break leaves. Anchor any local declarations to
            # the original text interval after the authorised edits, rather than child indices.
            if text_scopes(a, original, True) != text_scopes(c, candidate, False):
                return False
            aa = [el for el in aa if el.tag not in text_tags]
            cc = [el for el in cc if el.tag not in text_tags]
        return len(aa) == len(cc) and all(walk(x, y) for x, y in zip(aa, cc))

    return walk(original.root, candidate.root)
