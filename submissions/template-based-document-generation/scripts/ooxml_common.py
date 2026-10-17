"""OOXML primitives shared by the inspector, the filler and the verifier.

Standard library only. Nothing here knows about plans or policies beyond the numeric limits
it is handed.

Two views of a part are provided, and they must agree:

* **Parsed view** (`parse_xml`, `paragraph_tokens`) - ElementTree, read-only. Used by the inspector
  for eligibility and ancestry, and by the verifier for tree comparison.
* **Raw view** (`RawPart`) - a span tree over the part's bytes. Used by the filler, which edits bytes
  in place instead of re-serialising through ElementTree: re-serialisation drops unused `xmlns`
  declarations that `mc:Ignorable` still references, and Word then reports the document as corrupt.

Both compute the paragraph text the same way (text, tabs and line breaks in document order,
nested paragraphs excluded); the filler proves it at run time by hashing each paragraph it touches and
comparing with the manifest.
"""
from __future__ import annotations

import fnmatch
import hashlib
import io
import re
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Any, Iterable
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_TYPE_PREFIX = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


XML_SPACE = f"{{{XML_NS}}}space"
T, TAB, BR, CR, P, R, RPR = w("t"), w("tab"), w("br"), w("cr"), w("p"), w("r"), w("rPr")

# Elements that make any candidate beneath them ineligible. Content controls are not among them: a
# candidate inside a control is filled in place (see inspect_template for data-bound controls).
DENIED_ANCESTORS = {w(x) for x in ("ins", "del", "moveFrom", "moveTo", "fldSimple", "customXml")}
# Run children that mark a run as part of a field or a deletion (rule 2).
FIELD_MARKERS = {w("fldChar"), w("instrText"), w("delText")}


class PackageError(Exception):
    """The package cannot be processed. The message is safe to show to a user."""


# --------------------------------------------------------------------------------------
# Bounded zip reading and faithful rewriting
# --------------------------------------------------------------------------------------

@dataclass
class Entry:
    name: str
    date_time: tuple
    external_attr: int
    create_system: int
    compress_type: int
    is_dir: bool


@dataclass
class Package:
    entries: list[Entry]
    parts: dict[str, bytes]
    sha256: str
    size_bytes: int

    def names(self) -> list[str]:
        return [e.name for e in self.entries if not e.is_dir]


def _check_entry_name(name: str, seen: set[str]) -> None:
    if not name or "\x00" in name:
        raise PackageError("zip entry with an empty or invalid name")
    if name.startswith("/") or "\\" in name or re.match(r"^[A-Za-z]:", name):
        raise PackageError("unsafe zip entry path")
    if any(seg in (".", "..", "") for seg in name.rstrip("/").split("/")):
        raise PackageError("unsafe zip entry path")
    if name in seen:
        raise PackageError("duplicate zip entry")
    seen.add(name)


def read_package(data: bytes, limits: dict[str, Any]) -> Package:
    """Read a .docx within the policy limits. Raises PackageError with a plain-language reason."""
    max_bytes = limits.get("max_template_bytes", 10_000_000)
    if len(data) > max_bytes:
        raise PackageError(f"template is {len(data):,} bytes; the limit is {max_bytes:,}")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return _read_zip(zf, data, limits)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, EOFError, zlib.error) as exc:
        raise PackageError("zip package cannot be read; it may be damaged, encrypted or unsupported") from exc


def _read_zip(zf: zipfile.ZipFile, data: bytes, limits: dict[str, Any]) -> Package:
    infos = zf.infolist()
    if len(infos) > limits.get("max_zip_entries", 2000):
        raise PackageError(f"zip has {len(infos)} entries; the limit is {limits.get('max_zip_entries', 2000)}")
    max_part = limits.get("max_part_bytes", 52_428_800)
    budget = max(len(data), 1) * limits.get("max_expansion_ratio", 100)
    seen: set[str] = set()
    entries: list[Entry] = []
    parts: dict[str, bytes] = {}
    total = 0
    for info in infos:
        if info.orig_filename != info.filename:
            raise PackageError("unsafe zip entry path")
        _check_entry_name(info.filename, seen)
        is_dir = info.filename.endswith("/")
        entries.append(Entry(info.filename, info.date_time, info.external_attr, info.create_system, info.compress_type, is_dir))
        if is_dir:
            continue
        if info.file_size > max_part:
            raise PackageError(f"zip part exceeds the {max_part:,} byte limit")
        total += info.file_size
        if total > budget:
            raise PackageError("zip expands beyond the permitted ratio")
        with zf.open(info) as fh:
            content = fh.read(info.file_size + 1)
        if len(content) != info.file_size:
            raise PackageError("zip part does not match its declared size")
        parts[info.filename] = content
    if "[Content_Types].xml" not in parts or "word/document.xml" not in parts:
        raise PackageError("not a Word document package: [Content_Types].xml or word/document.xml is missing")
    pkg = Package(entries, parts, hashlib.sha256(data).hexdigest(), len(data))
    validate_package_structure(pkg, limits)
    return pkg


def write_package(pkg: Package, parts: dict[str, bytes]) -> bytes:
    """Rebuild the archive with the original entry order and per-entry metadata."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for e in pkg.entries:
            zi = zipfile.ZipInfo(e.name, date_time=e.date_time)
            zi.external_attr = e.external_attr
            zi.create_system = e.create_system
            zi.compress_type = e.compress_type
            z.writestr(zi, b"" if e.is_dir else parts[e.name])
        # zipfile substitutes 0o600<<16 whenever external_attr is 0, and 0 is exactly what Word writes.
        # The field exists only in the central directory, which is emitted on close from this list, so
        # restoring it here reproduces the original bytes faithfully.
        for entry, info in zip(pkg.entries, z.filelist):
            info.external_attr = entry.external_attr
            info.create_system = entry.create_system
    return buf.getvalue()


def in_scope(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, pat) for pat in patterns)


# --------------------------------------------------------------------------------------
# Safe parsing
# --------------------------------------------------------------------------------------

class _BoundedTreeBuilder(ET.TreeBuilder):
    def __init__(self, max_depth: int):
        super().__init__()
        self.depth = 0
        self.max_depth = max_depth

    def start(self, tag, attrs):
        self.depth += 1
        if self.depth > self.max_depth:
            raise PackageError("XML part exceeds the permitted nesting depth")
        return super().start(tag, attrs)

    def end(self, tag):
        result = super().end(tag)
        self.depth -= 1
        return result

    def doctype(self, name, pubid, system):
        raise PackageError("XML part contains a prohibited DOCTYPE or ENTITY declaration")


def parse_xml(data: bytes, limits: dict[str, Any], part: str = "") -> ET.Element:
    if len(data) > limits.get("max_part_bytes", 52_428_800):
        raise PackageError("XML part exceeds the permitted byte limit")
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise PackageError("XML part contains a prohibited DOCTYPE or ENTITY declaration")
    try:
        builder = _BoundedTreeBuilder(limits.get("max_xml_depth", 256))
        return ET.fromstring(data, parser=ET.XMLParser(target=builder))
    except (ET.ParseError, ValueError, LookupError) as exc:
        raise PackageError("XML part is not well-formed or uses an unsupported encoding") from exc


# --------------------------------------------------------------------------------------
# Minimum OPC/Word package structure (not full OpenXML schema validation)
# --------------------------------------------------------------------------------------

CT_RELATIONSHIPS = "application/vnd.openxmlformats-package.relationships+xml"
CT_WORD_PREFIX = "application/vnd.openxmlformats-officedocument.wordprocessingml."
CT_MAIN = CT_WORD_PREFIX + "document.main+xml"
MAIN_REL = REL_TYPE_PREFIX + "officeDocument"
_URI_CHARS = re.compile(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$")
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_MIME = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]+/[A-Za-z0-9!#$%&'*+.^_`|~-]+$")
_EXTENSION = re.compile(r"^[A-Za-z0-9_~!$&'()*+,;=:@-]+$")
_NC_START = r"A-Z_a-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2c00-\u2fef\u3001-\ud7ff\uf900-\ufdcf\ufdf0-\ufffd\U00010000-\U000effff"
_NCNAME = re.compile(f"^[{_NC_START}][{_NC_START}0-9.\\-\u00b7\u0300-\u036f\u203f-\u2040]*$")
_WORD_REL_PARTS = {
    REL_TYPE_PREFIX + kind: (CT_WORD_PREFIX + kind + "+xml", w(root))
    for kind, root in (
        ("header", "hdr"), ("footer", "ftr"), ("styles", "styles"),
        ("settings", "settings"), ("numbering", "numbering"),
        ("footnotes", "footnotes"), ("endnotes", "endnotes"),
        ("comments", "comments"), ("fontTable", "fonts"), ("webSettings", "webSettings"),
    )
}


def _uri(value: str):
    if not _URI_CHARS.fullmatch(value) or re.search(r"%(?![0-9A-Fa-f]{2})", value):
        raise PackageError("package contains an invalid URI")
    try:
        return urlsplit(value)
    except ValueError as exc:
        raise PackageError("package contains an invalid URI") from exc


def _uri_segment(segment: str) -> str:
    """Normalize URI escapes, never treating escaped separators as path separators."""
    def escaped(match):
        byte = int(match.group()[1:], 16)
        if byte in (0x2f, 0x5c) or byte < 0x20 or byte == 0x7f:
            raise PackageError("package URI contains a prohibited escape")
        char = chr(byte)
        return char if char in _UNRESERVED else f"%{byte:02X}"

    return re.sub(r"%[0-9A-Fa-f]{2}", escaped, segment)


def _part_key(name: str) -> str:
    """OPC URI identity, independent of filesystem/Windows path semantics."""
    uri = _uri(name)
    if not name.startswith("/") or name.startswith("//") or uri.scheme or uri.netloc or "?" in name or "#" in name:
        raise PackageError("package contains an invalid part name")
    segments = [_uri_segment(seg) for seg in uri.path[1:].split("/")]
    if any(not seg or seg.endswith(".") or "[" in seg or "]" in seg for seg in segments):
        raise PackageError("package contains an invalid part name")
    return "/" + "/".join(segments).lower()


def _resolve_target(source: str, target: str) -> str:
    uri = _uri(target)
    if uri.scheme or uri.netloc or "?" in target or target.startswith("//"):
        raise PackageError("internal relationship does not identify a package part")
    # A fragment identifies a location within the resolved part, not another ZIP member.
    segments = [] if uri.path.startswith("/") else source.split("/")[:-1]
    if not uri.path:
        segments = source.split("/")
    else:
        for raw in uri.path.lstrip("/").split("/"):
            seg = _uri_segment(raw)
            if seg == ".":
                continue
            if seg == "..":
                if not segments:
                    raise PackageError("internal relationship escapes the package root")
                segments.pop()
            else:
                segments.append(seg)
    return _part_key("/" + "/".join(segments))


def is_part_name(name: str) -> bool:
    """Whether a zip entry name is a valid OPC part name.

    Real documents carry entries that are not parts at all. Implementations that delete a part by moving
    its entry aside leave `[trash]/0000.dat` behind: no content type, no relationship, pure debris that
    Word ignores. Such an entry is preserved byte-for-byte but takes no part in package validation.
    """
    try:
        _part_key("/" + name)
        return True
    except PackageError:
        return False


def _relationship_source(name: str) -> str | None:
    if name == "_rels/.rels":
        return ""
    segments = name.split("/")
    if len(segments) >= 2 and segments[-2] == "_rels" and segments[-1].endswith(".rels"):
        source = "/".join(segments[:-2] + [segments[-1][:-5]])
        if not segments[-1][:-5]:
            raise PackageError("relationship part has an invalid source")
        return source
    return None


def _markup_only(el: ET.Element) -> bool:
    return not (el.text or "").strip() and all(not (c.tail or "").strip() for c in el)


def _content_type_map(pkg: Package, keys: dict[str, str], limits: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    root = parse_xml(pkg.parts["[Content_Types].xml"], limits)
    if root.tag != f"{{{CT_NS}}}Types" or not _markup_only(root):
        raise PackageError("content type declarations have an invalid root")
    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    for el in root:
        ct = el.get("ContentType", "").lower()
        if not _MIME.fullmatch(ct) or len(el) or (el.text or "").strip():
            raise PackageError("package contains an invalid content type declaration")
        if el.tag == f"{{{CT_NS}}}Default":
            ext = el.get("Extension", "").lower()
            if not _EXTENSION.fullmatch(ext) or ext in defaults:
                raise PackageError("package contains an invalid or duplicate content type default")
            defaults[ext] = ct
        elif el.tag == f"{{{CT_NS}}}Override":
            key = _part_key(el.get("PartName", ""))
            if key not in keys or key in overrides:
                raise PackageError("package contains an invalid or duplicate content type override")
            overrides[key] = ct
        else:
            raise PackageError("package contains an invalid content type declaration")
    types: dict[str, str] = {}
    for key, name in keys.items():
        leaf = key.rsplit("/", 1)[-1]
        ext = leaf.rsplit(".", 1)[-1] if "." in leaf else ""
        ct = overrides.get(key, defaults.get(ext))
        if not ct:
            raise PackageError("package part has no content type declaration")
        types[name] = ct
    if types["word/document.xml"] != CT_MAIN:
        raise PackageError("main document has an incorrect content type")
    return types, defaults


def validate_package_structure(pkg: Package, limits: dict[str, Any]) -> None:
    """Check required OPC links and basic Word part shapes, without interpreting policy.

    Optional Word parts are not required. Known relationship types constrain their targets;
    opaque parts (including an empty signature origin) are not treated as XML by filename.
    """
    if "_rels/.rels" not in pkg.parts:
        raise PackageError("Word package is missing its root relationships")
    keys: dict[str, str] = {}
    foreign: list[str] = []
    for name in pkg.parts:
        if name == "[Content_Types].xml":
            continue
        if not is_part_name(name):
            foreign.append(name)          # not a part: validated below only for not pretending to be one
            continue
        key = _part_key("/" + name)
        if key in keys:
            raise PackageError("package contains equivalent duplicate part names")
        keys[key] = name
    types, ct_defaults = _content_type_map(pkg, keys, limits)
    for name in foreign:
        leaf = name.rsplit("/", 1)[-1]
        if (leaf.rsplit(".", 1)[-1].lower() if "." in leaf else "") in ct_defaults:
            raise PackageError("package declares a content type for an entry whose name is not a valid part name")
        # Debris is tolerated only when it cannot be mistaken for a real part. A name a filesystem or a
        # lenient reader could fold onto a part ("word/document.xml.") would shadow that part's content.
        if "/" + "/".join(seg.rstrip(". ").lower() for seg in name.split("/")) in keys:
            raise PackageError("package contains an entry whose name can be confused with a real part")
    parsed: dict[str, ET.Element] = {}

    def xml_part(name: str) -> ET.Element:
        if name not in parsed:
            parsed[name] = parse_xml(pkg.parts[name], limits)
        return parsed[name]

    for name, ct in types.items():
        if ct in ("application/xml", "text/xml") or ct.endswith("+xml"):
            xml_part(name)

    main = xml_part("word/document.xml")
    body = main.find(w("body"))
    if (main.tag != w("document") or body is None or not _markup_only(main) or not _markup_only(body)
            or [el.tag for el in main] not in ([w("body")], [w("background"), w("body")])
            or len(list(main.iter(w("body")))) != 1):
        raise PackageError("main document must have a Word document root and one body")

    relationship_parts: dict[str, str] = {}
    for name, ct in types.items():
        source = _relationship_source(name)
        if source is not None:
            if ct != CT_RELATIONSHIPS:
                raise PackageError("relationship part has an incorrect content type")
            if source and _part_key("/" + source) not in keys:
                raise PackageError("relationship part has no source part")
            relationship_parts[name] = source
        elif ct == CT_RELATIONSHIPS:
            raise PackageError("relationship part has an invalid package location")

    relationships: dict[str, dict[str, tuple[str, str, str]]] = {}
    main_count = 0
    for name, source in relationship_parts.items():
        if source and keys[_part_key("/" + source)] in relationship_parts:
            raise PackageError("relationship parts cannot have relationships")
        root = xml_part(name)
        if root.tag != f"{{{PKG_REL_NS}}}Relationships" or not _markup_only(root):
            raise PackageError("relationship part has an invalid root")
        rels: dict[str, tuple[str, str, str]] = {}
        relationships[keys[_part_key("/" + source)] if source else ""] = rels
        for rel in root:
            rid, kind, target = rel.get("Id", ""), rel.get("Type", ""), rel.get("Target", "")
            mode = rel.get("TargetMode", "Internal")
            if (rel.tag != f"{{{PKG_REL_NS}}}Relationship" or len(rel) or (rel.text or "").strip()
                    or not _NCNAME.fullmatch(rid) or rid in rels
                    or not _uri(kind).scheme or not target or mode not in ("Internal", "External")):
                raise PackageError("package contains an invalid or duplicate relationship")
            rels[rid] = (kind, target, mode)
            if kind == MAIN_REL:
                if source or mode != "Internal":
                    raise PackageError("main document relationship must originate at the package root")
                main_count += 1
            if mode == "External":
                if kind in _WORD_REL_PARTS:
                    raise PackageError("Word XML relationship requires an internal target")
                # External targets are opaque to package resolution and remain policy's concern.
                continue
            key = _resolve_target(source, target)
            if key not in keys or keys[key] in relationship_parts:
                raise PackageError("internal relationship target is missing or is not a content part")
            actual = keys[key]
            if kind == MAIN_REL and actual != "word/document.xml":
                raise PackageError("root relationship does not target the main Word document")
            if kind in _WORD_REL_PARTS:
                expected_type, expected_root = _WORD_REL_PARTS[kind]
                if types[actual] != expected_type.lower() or xml_part(actual).tag != expected_root:
                    raise PackageError("Word relationship target has an incorrect content type or root")
            elif kind == REL_TYPE_PREFIX + "image" and not types[actual].startswith("image/"):
                raise PackageError("image relationship target has an incorrect content type")
    if main_count != 1:
        raise PackageError("Word package must have exactly one root main document relationship")

    expected_refs = {
        w("headerReference"): REL_TYPE_PREFIX + "header",
        w("footerReference"): REL_TYPE_PREFIX + "footer",
        w("hyperlink"): REL_TYPE_PREFIX + "hyperlink",
        "{http://schemas.openxmlformats.org/drawingml/2006/main}blip": REL_TYPE_PREFIX + "image",
    }
    # Reference IDs belong to their source part, not to a package-wide ID namespace.
    for name, root in parsed.items():
        if not root.tag.startswith(f"{{{W_NS}}}"):
            continue
        rels = relationships.get(name, {})
        for el in root.iter():
            for attr in (f"{{{R_NS}}}id", f"{{{R_NS}}}embed", f"{{{R_NS}}}link"):
                rid = el.get(attr)
                if rid is not None and (rid not in rels or (el.tag in expected_refs and rels[rid][0] != expected_refs[el.tag])):
                    raise PackageError("Word markup references a missing or inappropriate relationship")


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def ancestors(el: ET.Element, parents: dict[ET.Element, ET.Element]) -> list[ET.Element]:
    out = []
    while el in parents:
        el = parents[el]
        out.append(el)
    return out


# --------------------------------------------------------------------------------------
# Paragraph text model - parsed view
# --------------------------------------------------------------------------------------

@dataclass
class Token:
    kind: str                  # 't' | 'tab' | 'br'
    text: str                  # the contribution to the paragraph text
    start: int                 # offset in the paragraph text
    end: int
    element: ET.Element
    run: ET.Element | None


def paragraph_tokens(p: ET.Element) -> list[Token]:
    """Tokens of one paragraph in document order, excluding anything inside a nested w:p."""
    tokens: list[Token] = []
    pos = 0

    def walk(el: ET.Element, run: ET.Element | None) -> None:
        nonlocal pos
        for child in el:
            tag = child.tag
            if tag == P:
                continue  # a nested paragraph (text box) owns its own text
            if tag == T:
                text = child.text or ""
                tokens.append(Token("t", text, pos, pos + len(text), child, run))
                pos += len(text)
            elif tag == TAB:
                tokens.append(Token("tab", "\t", pos, pos + 1, child, run)); pos += 1
            elif tag in (BR, CR):
                tokens.append(Token("br", "\n", pos, pos + 1, child, run)); pos += 1
            else:
                walk(child, child if tag == R else run)

    walk(p, None)
    return tokens


def paragraph_text(p: ET.Element) -> str:
    return "".join(t.text for t in paragraph_tokens(p))


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def paragraphs(root: ET.Element) -> list[ET.Element]:
    """All w:p elements in document order (depth-first pre-order)."""
    return list(root.iter(P))


def field_state_by_run(root: ET.Element) -> dict[ET.Element, bool]:
    """For every run, whether it lies inside a complex field or carries a field/deletion marker."""
    inside: dict[ET.Element, bool] = {}
    depth = 0
    for run in root.iter(R):
        has_marker = any(c.tag in FIELD_MARKERS for c in run)
        inside[run] = depth > 0 or has_marker
        for c in run:
            if c.tag == w("fldChar"):
                kind = c.get(w("fldCharType"))
                if kind == "begin":
                    depth += 1
                elif kind == "end":
                    depth = max(0, depth - 1)
    return inside


def rpr_signature(run: ET.Element | None) -> str:
    if run is None:
        return "<no-run>"
    rpr = run.find(RPR)
    return "" if rpr is None else ET.tostring(rpr, encoding="unicode")


def run_is_hidden(run: ET.Element) -> bool:
    rpr = run.find(RPR)
    if rpr is None:
        return False
    v = rpr.find(w("vanish"))
    return v is not None and v.get(w("val"), "true") not in ("0", "false")


def run_is_highlighted(run: ET.Element) -> bool:
    rpr = run.find(RPR)
    if rpr is None:
        return False
    h = rpr.find(w("highlight"))
    return h is not None and h.get(w("val"), "") not in ("", "none")


# Real containers: an element whose block-level children (paragraphs and tables) form a
# contiguous sequence a range deletion may address. Everything else (sdt, customXml, ins ...) is
# transparent: a paragraph inside a block-level content control still belongs to the body.
REAL_CONTAINER_LOCALS = ("body", "tc", "txbxContent", "footnote", "endnote", "hdr", "ftr", "comment")
REAL_CONTAINERS = {w(x) for x in REAL_CONTAINER_LOCALS}
CONTAINER_KIND = {w("body"): "body", w("tc"): "cell", w("txbxContent"): "textbox", w("footnote"): "footnote",
                  w("endnote"): "endnote", w("hdr"): "header", w("ftr"): "footer", w("comment"): "other"}


def real_container(el: ET.Element, parents: dict[ET.Element, ET.Element]) -> tuple[ET.Element | None, ET.Element]:
    """(container, block): the nearest real container above `el` and the child of it that holds `el`."""
    block = el
    while block in parents:
        parent = parents[block]
        if parent.tag in REAL_CONTAINERS:
            return parent, block
        block = parent
    return None, block


# --------------------------------------------------------------------------------------
# Raw view - byte-level span tree used by the filler
# --------------------------------------------------------------------------------------

_ENTITY = {b"amp": "&", b"lt": "<", b"gt": ">", b"quot": '"', b"apos": "'"}
_REF_RE = re.compile(rb"&(#x[0-9A-Fa-f]+|#[0-9]+|[A-Za-z]+);")


def unescape(raw: bytes) -> str:
    def repl(m: re.Match) -> bytes:
        ref = m.group(1)
        if ref.startswith(b"#x"):
            return chr(int(ref[2:], 16)).encode("utf-8")
        if ref.startswith(b"#"):
            return chr(int(ref[1:])).encode("utf-8")
        if ref in _ENTITY:
            return _ENTITY[ref].encode("utf-8")
        raise PackageError("undefined entity reference in a text node")
    return _REF_RE.sub(repl, raw).decode("utf-8")


def escape(text: str) -> bytes:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").encode("utf-8")


def needs_preserve(text: str) -> bool:
    return text != text.strip() or "  " in text


# Elements the raw tree keeps as nodes. Every other element is tracked on the stack (so nesting
# and spans stay right) but not materialised, which keeps the tree small on large documents.
RAW_NODE_LOCALS = frozenset((
    "document", "body", "hdr", "ftr", "footnotes", "endnotes", "footnote", "endnote", "comments", "comment",
    "p", "r", "t", "tab", "br", "cr", "pPr", "rPr", "sectPr", "rStyle",
    "tbl", "tr", "tc", "txbxContent",
    "sdt", "sdtPr", "sdtContent", "showingPlcHdr", "dataBinding",
    "bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd", "commentReference",
    "hyperlink", "ins", "del", "moveFrom", "moveTo", "fldSimple", "customXml", "smartTag",
    "drawing", "pict", "footnoteReference", "endnoteReference",
))

# Constructs that carry a document-wide identity (an id, a name, or both). Removing one half of a
# pair breaks the document; duplicating one creates a conflict. Both are refused, never repaired.
PAIRED_MARKER_LOCALS = ("bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd", "commentReference")
IDENTITY_LOCALS = PAIRED_MARKER_LOCALS + ("sdt", "drawing", "pict", "footnoteReference", "endnoteReference")


@dataclass(eq=False)
class RawNode:
    name: str                       # local name, e.g. "p"
    start: int                      # byte offset of '<'
    end: int                        # byte offset just past the closing '>'
    inner_start: int                # just past the start tag
    inner_end: int                  # offset of the end tag ('<' of '</w:x>'), == inner_start when empty
    attrs: bytes
    empty: bool
    parent: RawNode | None = None
    children: list[RawNode] = field(default_factory=list)
    index: int = -1                 # paragraph ordinal for "p" nodes

    def child(self, name: str) -> RawNode | None:
        for c in self.children:
            if c.name == name:
                return c
        return None

    def ancestors(self) -> list[RawNode]:
        out = []
        n = self.parent
        while n is not None:
            out.append(n)
            n = n.parent
        return out


@dataclass
class RawToken:
    kind: str                    # 't' | 'tab' | 'br'
    text: str
    start: int                   # offset in the paragraph text
    end: int
    node: RawNode
    run: RawNode | None


class RawPart:
    """Tokenizes one XML part's bytes into a tree of spans, without re-serialising anything."""

    def __init__(self, data: bytes, part: str = ""):
        self.data = data
        self.part = part
        self.prefix: bytes = b""
        self.root: RawNode | None = None
        self.paragraphs: list[RawNode] = []
        self._tokens: dict[int, list[RawToken]] = {}
        self._scan()

    # ---- tokenizer ------------------------------------------------------------------------
    def _tags(self):
        """Yield (kind, start, end, name, attrs) for every markup token; kind in start/end/empty/other."""
        data = self.data
        n = len(data)
        i = 0
        while i < n:
            lt = data.find(b"<", i)
            if lt < 0:
                break
            if data.startswith(b"<!--", lt):
                gt = data.find(b"-->", lt)
                if gt < 0:
                    raise PackageError(f"{self.part}: unterminated comment")
                yield ("other", lt, gt + 3, b"", b""); i = gt + 3; continue
            if data.startswith(b"<![CDATA[", lt):
                raise PackageError(f"{self.part}: CDATA sections are not supported by the filler")
            if data.startswith(b"<?", lt):
                gt = data.find(b"?>", lt)
                if gt < 0:
                    raise PackageError(f"{self.part}: unterminated processing instruction")
                yield ("other", lt, gt + 2, b"", b""); i = gt + 2; continue
            if data.startswith(b"<!", lt):
                raise PackageError(f"{self.part}: declarations are not permitted")
            j = lt + 1
            quote = None
            while j < n:
                c = data[j:j + 1]
                if quote:
                    if c == quote:
                        quote = None
                elif c in (b'"', b"'"):
                    quote = c
                elif c == b">":
                    break
                j += 1
            if j >= n:
                raise PackageError(f"{self.part}: unterminated tag")
            body = data[lt + 1:j]
            if body.startswith(b"/"):
                yield ("end", lt, j + 1, body[1:].strip(), b"")
            else:
                empty = body.rstrip().endswith(b"/")
                if empty:
                    body = body.rstrip()[:-1]
                m = re.match(rb"[^\s/>]+", body)
                name = m.group(0) if m else b""
                yield ("empty" if empty else "start", lt, j + 1, name, body[len(name):])
            i = j + 1

    def _scan(self) -> None:
        prefix = None
        for kind, s, e, name, attrs in self._tags():
            if kind in ("start", "empty"):
                declared: dict[bytes, bytes] = {}
                for m in re.finditer(rb'xmlns(?::([A-Za-z_][\w.-]*))?\s*=\s*["\']([^"\']*)["\']', attrs):
                    declared[(m.group(1) + b":") if m.group(1) else b""] = m.group(2)
                # The root element's own tag names the prefix this part uses for WordprocessingML, which
                # is authoritative when the namespace is declared under several aliases.
                root_prefix = name.split(b":")[0] + b":" if b":" in name else b""
                if declared.get(root_prefix) == W_NS.encode():
                    prefix = root_prefix
                else:
                    prefix = next((p for p, uri in declared.items() if uri == W_NS.encode()), None)
                break
        if prefix is None:
            raise PackageError(f"{self.part}: the WordprocessingML namespace is not declared on the root element")
        self.prefix = prefix
        plen = len(prefix)
        stack: list[tuple[bytes, RawNode | None]] = []
        nearest: list[RawNode] = []          # materialised ancestors
        for kind, s, e, name, attrs in self._tags():
            if kind == "other":
                continue
            if kind in ("start", "empty"):
                node = None
                if name.startswith(prefix) and (prefix or b":" not in name):
                    local = name[plen:].decode("ascii", "replace")
                    if local in RAW_NODE_LOCALS:
                        node = RawNode(local, s, e, e, e if kind == "empty" else -1, attrs, kind == "empty",
                                       nearest[-1] if nearest else None)
                        if node.parent is not None:
                            node.parent.children.append(node)
                        elif self.root is None:
                            self.root = node
                        if local == "p":
                            node.index = len(self.paragraphs)
                            self.paragraphs.append(node)
                if kind == "start":
                    stack.append((name, node))
                    if node is not None:
                        nearest.append(node)
            else:
                if not stack or stack[-1][0] != name:
                    raise PackageError(f"{self.part}: mismatched end tag")
                _, node = stack.pop()
                if node is not None:
                    node.inner_end = s
                    node.end = e
                    nearest.pop()
        if stack:
            raise PackageError(f"{self.part}: unclosed element")
        if self.root is None:
            raise PackageError(f"{self.part}: no WordprocessingML root element")

    # ---- paragraph text ---------------------------------------------------------------------
    def tokens(self, p: RawNode) -> list[RawToken]:
        if id(p) in self._tokens:
            return self._tokens[id(p)]
        out: list[RawToken] = []
        pos = 0

        def walk(node: RawNode, run: RawNode | None) -> None:
            nonlocal pos
            for c in node.children:
                if c.name == "p":
                    continue
                if c.name == "t":
                    text = unescape(self.data[c.inner_start:c.inner_end])
                    out.append(RawToken("t", text, pos, pos + len(text), c, run)); pos += len(text)
                elif c.name == "tab":
                    out.append(RawToken("tab", "\t", pos, pos + 1, c, run)); pos += 1
                elif c.name in ("br", "cr"):
                    out.append(RawToken("br", "\n", pos, pos + 1, c, run)); pos += 1
                else:
                    walk(c, c if c.name == "r" else run)

        walk(p, None)
        self._tokens[id(p)] = out
        return out

    def text(self, p: RawNode) -> str:
        return "".join(t.text for t in self.tokens(p))

    def tag(self, local: str) -> bytes:
        return self.prefix + local.encode("ascii")

    # ---- structure ---------------------------------------------------------------------------
    def real_container(self, node: RawNode) -> tuple[RawNode | None, RawNode]:
        block = node
        while block.parent is not None:
            if block.parent.name in REAL_CONTAINER_LOCALS:
                return block.parent, block
            block = block.parent
        return None, block

    def row_of(self, p: RawNode) -> RawNode | None:
        n = p.parent
        while n is not None:
            if n.name == "tr":
                return n
            n = n.parent
        return None

    def first_paragraph_in(self, node: RawNode) -> RawNode | None:
        if node.name == "p":
            return node
        for c in node.children:
            found = self.first_paragraph_in(c)
            if found is not None:
                return found
        return None

    def last_paragraph_in(self, node: RawNode) -> RawNode | None:
        for c in reversed(node.children):
            found = self.last_paragraph_in(c)
            if found is not None:
                return found
        return node if node.name == "p" else None

    def paragraph_count_in(self, node: RawNode) -> int:
        return sum(1 for _ in self._iter_paragraphs(node))

    def _iter_paragraphs(self, node: RawNode):
        if node.name == "p":
            yield node
        for c in node.children:
            yield from self._iter_paragraphs(c)

    def identity_constructs_in(self, region: tuple[int, int]) -> list[str]:
        """Identity-bearing constructs wholly inside [start, end): duplicating the region would clash."""
        start, end = region
        found: list[str] = []

        def walk(n: RawNode) -> None:
            if n.end <= start or n.start >= end:
                return
            if n.name in IDENTITY_LOCALS and start <= n.start and n.end <= end and n.name not in found:
                found.append(n.name)
            for c in n.children:
                walk(c)

        assert self.root is not None
        walk(self.root)
        return found

    def markers_in(self, regions: list[tuple[int, int]]) -> list[str]:
        """Bookmark and comment range markers left unbalanced by removing every [start, end) region together."""
        problems: list[str] = []
        ids: dict[str, set[bytes]] = {k: set() for k in PAIRED_MARKER_LOCALS}

        def inside(n: RawNode) -> bool:
            return any(start <= n.start and n.end <= end for start, end in regions)

        def walk(n: RawNode) -> None:
            if not any(n.start < end and n.end > start for start, end in regions):
                return
            if n.name in ids and inside(n):
                m = re.search(rb'\bw:id\s*=\s*["\']([^"\']*)["\']', n.attrs) or re.search(rb'\bid\s*=\s*["\']([^"\']*)["\']', n.attrs)
                ids[n.name].add(m.group(1) if m else b"?")
            for c in n.children:
                walk(c)

        assert self.root is not None
        walk(self.root)
        if ids["bookmarkStart"] != ids["bookmarkEnd"]:
            problems.append("a bookmark starts or ends inside the region but not both")
        if not (ids["commentRangeStart"] == ids["commentRangeEnd"] == ids["commentReference"]):
            problems.append("a comment range or reference would be split by the region")
        return problems


# --------------------------------------------------------------------------------------
# Byte-level edits
# --------------------------------------------------------------------------------------

@dataclass
class Edit:
    start: int
    end: int
    replacement: bytes


def _t_element(tag: bytes, attrs: bytes, text: str) -> bytes:
    """Serialise a w:t with the original attributes minus xml:space, adding it when needed."""
    attrs = re.sub(rb'\s+xml:space\s*=\s*["\'][^"\']*["\']', b"", attrs).rstrip()
    if attrs:
        attrs = b" " + attrs.lstrip()
    if needs_preserve(text):
        attrs += b' xml:space="preserve"'
    if text == "":
        return b"<" + tag + attrs + b"/>"
    return b"<" + tag + attrs + b">" + escape(text) + b"</" + tag + b">"


def value_content(tag: bytes, prefix: bytes, text: str) -> bytes:
    """w:t segments separated by w:br / w:tab elements, all destined for the same run."""
    out = b""
    segment = ""
    for ch in text:
        if ch in ("\n", "\t"):
            if segment:
                out += _t_element(tag, b"", segment); segment = ""
            out += b"<" + prefix + (b"br/>" if ch == "\n" else b"tab/>")
        else:
            segment += ch
    if segment:
        out += _t_element(tag, b"", segment)
    return out


def plan_paragraph_edits(raw: RawPart, p: RawNode, spans: list[tuple[int, int, str]]) -> list[Edit]:
    """Edits that replace each (char_start, char_end, text) span in one paragraph.

    Each span is consolidated into its first owning w:t and replaced there; later owning w:t
    elements lose the covered characters. Only 't' tokens may overlap a span. A token that owns
    several spans is rewritten once, with every span applied in one pass.
    """
    tokens = raw.tokens(p)
    tag = raw.tag("t")
    pieces: dict[int, list[tuple[int, int, str | None]]] = {}
    order: dict[int, RawToken] = {}
    for s, e, rendered in spans:
        owners = [t for t in tokens if t.start < e and t.end > s]
        if not owners:
            raise PackageError(f"paragraph {p.index}: no text token owns span {s}-{e}")
        if any(t.kind != "t" for t in owners):
            raise PackageError(f"paragraph {p.index}: span {s}-{e} covers a tab or break")
        for i, t in enumerate(owners):
            a, b = max(s, t.start) - t.start, min(e, t.end) - t.start
            pieces.setdefault(id(t), []).append((a, b, rendered if i == 0 else None))
            order[id(t)] = t
    edits: list[Edit] = []
    for tid, cuts in pieces.items():
        t = order[tid]
        cuts.sort(key=lambda c: c[0])
        out = b""
        cursor = 0
        text = t.text
        for a, b, rendered in cuts:
            if a < cursor:
                raise PackageError(f"paragraph {p.index}: overlapping spans in one text node")
            keep = text[cursor:a]
            if keep:
                out += _t_element(tag, t.node.attrs, keep)
            if rendered is not None:
                out += value_content(tag, raw.prefix, rendered)
            cursor = b
        tail = text[cursor:]
        if tail:
            out += _t_element(tag, t.node.attrs, tail)
        if not out:
            out = _t_element(tag, t.node.attrs, "")
        edits.append(Edit(t.node.start, t.node.end, out))
    return edits


def empty_paragraph_fill_edit(raw: RawPart, p: RawNode, text: str) -> Edit:
    """Give a paragraph with no text a single run carrying `text`, using the paragraph mark's rPr."""
    ppr = p.child("pPr")
    rpr = ppr.child("rPr") if ppr is not None else None
    rpr_bytes = raw.data[rpr.start:rpr.end] if rpr is not None else b""
    run = b"<" + raw.tag("r") + b">" + rpr_bytes + value_content(raw.tag("t"), raw.prefix, text) + b"</" + raw.tag("r") + b">"
    if p.empty:
        start_tag = raw.data[p.start:p.end].rstrip()
        start_tag = start_tag[:-2].rstrip() + b">"     # "<w:p .../>" -> "<w:p ...>"
        return Edit(p.start, p.end, start_tag + run + b"</" + raw.tag("p") + b">")
    return Edit(p.inner_end, p.inner_end, run)


def control_placeholder_edits(raw: RawPart, sdt: RawNode, first_run: RawNode | None) -> list[Edit]:
    """When a content control receives real content: drop showingPlcHdr and the PlaceholderText style."""
    edits: list[Edit] = []
    pr = sdt.child("sdtPr")
    if pr is not None:
        flag = pr.child("showingPlcHdr")
        if flag is not None:
            edits.append(Edit(flag.start, flag.end, b""))
    if first_run is not None:
        rpr = first_run.child("rPr")
        if rpr is not None:
            style = rpr.child("rStyle")
            if style is not None and re.search(rb'val\s*=\s*["\']PlaceholderText["\']', style.attrs):
                edits.append(Edit(style.start, style.end, b""))
    return edits


def delete_edit(node: RawNode) -> Edit:
    return Edit(node.start, node.end, b"")


def clear_paragraph_edit(raw: RawPart, p: RawNode) -> Edit:
    """Empty a paragraph but keep it (and its pPr): the sole paragraph of a table cell may not vanish."""
    if p.empty:
        return Edit(p.start, p.end, raw.data[p.start:p.end])
    ppr = p.child("pPr")
    ppr_bytes = raw.data[ppr.start:ppr.end] if ppr is not None else b""
    return Edit(p.start, p.end, raw.data[p.start:p.inner_start] + ppr_bytes + b"</" + raw.tag("p") + b">")


def _ppr_without_sectpr(raw: RawPart, ppr: RawNode | None) -> bytes:
    if ppr is None:
        return b""
    sect = ppr.child("sectPr")
    if sect is None:
        return raw.data[ppr.start:ppr.end]
    return raw.data[ppr.start:sect.start] + raw.data[sect.end:ppr.end]


def insert_after_edit(raw: RawPart, p: RawNode, texts: list[str]) -> Edit:
    """New paragraphs after `p`, inheriting its pPr (minus any section break) and its first run's rPr."""
    ppr = p.child("pPr")
    first_run = next((c for c in p.children if c.name == "r"), None)
    rpr = first_run.child("rPr") if first_run is not None else None
    rpr_bytes = raw.data[rpr.start:rpr.end] if rpr is not None else b""
    out = b""
    for text in texts:
        out += (b"<" + raw.tag("p") + b">" + _ppr_without_sectpr(raw, ppr) + b"<" + raw.tag("r") + b">" + rpr_bytes
                + value_content(raw.tag("t"), raw.prefix, text) + b"</" + raw.tag("r") + b">" + b"</" + raw.tag("p") + b">")
    return Edit(p.end, p.end, out)


def repeat_row_edit(raw: RawPart, tr: RawNode, copies: list[list[Edit]], budget: int = 0) -> Edit:
    """Replace a row by N copies, each with its own (absolute-offset) inner edits applied.

    The size is budgeted before anything is built. A permitted row can be megabytes and a permitted
    repeat can be hundreds of items, so checking the result afterwards means allocating the gigabyte
    first and discovering the problem only once it exists.
    """
    row = tr.end - tr.start
    if budget:
        grown = sum(row + sum(len(e.replacement) - (e.end - e.start) for e in edits) for edits in copies)
        if grown > budget:
            raise PackageError(f"repeating this row would produce {grown:,} bytes, beyond the {budget:,} byte limit")
    out: list[bytes] = []
    for edits in copies:
        out.append(apply_edits(raw.data[tr.start:tr.end], [Edit(e.start - tr.start, e.end - tr.start, e.replacement) for e in edits]))
    return Edit(tr.start, tr.end, b"".join(out))


def apply_edits(data: bytes, edits: list[Edit]) -> bytes:
    """Apply non-overlapping edits in one pass. A zero-length edit (an insert) at the same offset as a
    deletion sorts first, so an insert after paragraph X lands right after X even when X's next sibling
    is removed."""
    ordered = sorted(edits, key=lambda e: (e.start, e.end))
    out: list[bytes] = []
    cursor = 0
    for ed in ordered:
        if ed.start < cursor:
            raise PackageError("overlapping edits")
        out.append(data[cursor:ed.start])
        out.append(ed.replacement)
        cursor = ed.end
    out.append(data[cursor:])
    return b"".join(out)
