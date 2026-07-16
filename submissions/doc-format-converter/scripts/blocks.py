"""Shared block model for the Universal Document Converter.

Parses Markdown (own mini-parser -- the sandbox has converters *to* Markdown
but no Markdown-parsing package) and HTML (via beautifulsoup4) into a small
list-of-blocks document model that render.py can write out as PDF, DOCX,
PPTX, HTML, Markdown, or plain text.

Supported blocks: heading, paragraph, list, table, code, hr.
Inline formatting is kept as runs: (text, bold, italic, code).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass
class Heading:
    level: int
    runs: list[Run]


@dataclass
class Paragraph:
    runs: list[Run]


@dataclass
class ListBlock:
    ordered: bool
    items: list[list[Run]]


@dataclass
class Table:
    rows: list[list[str]] = field(default_factory=list)  # rows[0] is the header


@dataclass
class CodeBlock:
    text: str
    lang: str = ""


@dataclass
class Hr:
    pass


Block = Heading | Paragraph | ListBlock | Table | CodeBlock | Hr


def plain_text(runs: list[Run]) -> str:
    return "".join(r.text for r in runs)


# --------------------------------------------------------------------------
# Inline Markdown -> runs
# --------------------------------------------------------------------------

_INLINE_RE = re.compile(
    r"(\*\*\*(?P<bi>.+?)\*\*\*"
    r"|\*\*(?P<b>.+?)\*\*"
    r"|__(?P<b2>.+?)__"
    r"|\*(?P<i>[^*]+?)\*"
    r"|_(?P<i2>[^_]+?)_"
    r"|`(?P<c>[^`]+?)`"
    r"|!?\[(?P<label>[^\]]*)\]\((?P<url>[^)]*)\))"
)


def parse_inline(text: str) -> list[Run]:
    runs: list[Run] = []
    pos = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append(Run(text[pos : m.start()]))
        if m.group("bi") is not None:
            runs.append(Run(m.group("bi"), bold=True, italic=True))
        elif m.group("b") is not None:
            runs.append(Run(m.group("b"), bold=True))
        elif m.group("b2") is not None:
            runs.append(Run(m.group("b2"), bold=True))
        elif m.group("i") is not None:
            runs.append(Run(m.group("i"), italic=True))
        elif m.group("i2") is not None:
            runs.append(Run(m.group("i2"), italic=True))
        elif m.group("c") is not None:
            runs.append(Run(m.group("c"), code=True))
        elif m.group("label") is not None:
            label = m.group("label")
            url = m.group("url")
            runs.append(Run(label if label else url))
            if url and label and not m.group(0).startswith("!"):
                runs.append(Run(f" ({url})"))
        pos = m.end()
    if pos < len(text):
        runs.append(Run(text[pos:]))
    return runs or [Run("")]


# --------------------------------------------------------------------------
# Markdown -> blocks
# --------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BULLET_RE = re.compile(r"^\s{0,3}[-*+]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\s{0,3}\d+[.)]\s+(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}.*\|.*$")
_HR_RE = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")


def _split_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_markdown(text: str) -> list[Block]:
    blocks: list[Block] = []
    lines = text.splitlines()
    i = 0
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            blocks.append(Paragraph(parse_inline(" ".join(para_buf))))
            para_buf.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            lang = stripped[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append(CodeBlock("\n".join(code_lines), lang))
            i += 1
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        m = _HEADING_RE.match(line)
        if m:
            flush_para()
            blocks.append(Heading(len(m.group(1)), parse_inline(m.group(2))))
            i += 1
            continue

        if _HR_RE.match(stripped):
            flush_para()
            blocks.append(Hr())
            i += 1
            continue

        if "|" in stripped and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]):
            flush_para()
            table = Table([_split_table_row(line)])
            i += 2
            while i < len(lines) and "|" in lines[i].strip() and lines[i].strip():
                table.rows.append(_split_table_row(lines[i]))
                i += 1
            blocks.append(table)
            continue

        m = _BULLET_RE.match(line) or _ORDERED_RE.match(line)
        if m:
            flush_para()
            ordered = bool(_ORDERED_RE.match(line))
            items: list[list[Run]] = []
            item_re = _ORDERED_RE if ordered else _BULLET_RE
            while i < len(lines):
                m = item_re.match(lines[i])
                if not m:
                    break
                items.append(parse_inline(m.group(1).strip()))
                i += 1
            blocks.append(ListBlock(ordered, items))
            continue

        para_buf.append(stripped)
        i += 1

    flush_para()
    return blocks


# --------------------------------------------------------------------------
# HTML -> blocks
# --------------------------------------------------------------------------

_INLINE_TAGS = {"b", "strong", "i", "em", "code", "span", "a", "u", "sub", "sup"}


def _element_runs(el) -> list[Run]:
    """Flatten an element's inline content into runs."""
    from bs4 import NavigableString, Tag

    runs: list[Run] = []

    def walk(node, bold: bool, italic: bool, code: bool) -> None:
        if isinstance(node, NavigableString):
            text = re.sub(r"\s+", " ", str(node))
            if text:
                runs.append(Run(text, bold=bold, italic=italic, code=code))
        elif isinstance(node, Tag):
            b = bold or node.name in ("b", "strong")
            it = italic or node.name in ("i", "em")
            c = code or node.name == "code"
            for child in node.children:
                walk(child, b, it, c)

    for child in el.children:
        walk(child, False, False, False)

    # trim leading/trailing whitespace across the run list
    while runs and not runs[0].text.strip():
        runs.pop(0)
    while runs and not runs[-1].text.strip():
        runs.pop()
    if runs:
        runs[0].text = runs[0].text.lstrip()
        runs[-1].text = runs[-1].text.rstrip()
    return runs or [Run("")]


def parse_html(text: str) -> list[Block]:
    from bs4 import BeautifulSoup, Tag

    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    root = soup.body or soup

    blocks: list[Block] = []

    def handle(el: Tag) -> None:
        name = el.name
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            blocks.append(Heading(int(name[1]), _element_runs(el)))
        elif name == "p":
            runs = _element_runs(el)
            if plain_text(runs).strip():
                blocks.append(Paragraph(runs))
        elif name in ("ul", "ol"):
            items = [_element_runs(li) for li in el.find_all("li", recursive=False)]
            if items:
                blocks.append(ListBlock(name == "ol", items))
        elif name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = tr.find_all(["th", "td"])
                if cells:
                    rows.append([plain_text(_element_runs(c)).strip() for c in cells])
            if rows:
                blocks.append(Table(rows))
        elif name == "pre":
            blocks.append(CodeBlock(el.get_text().strip("\n")))
        elif name == "hr":
            blocks.append(Hr())
        else:
            recurse(el)

    def recurse(parent) -> None:
        for child in parent.children:
            if isinstance(child, Tag):
                handle(child)
            elif str(child).strip():
                blocks.append(Paragraph(parse_inline(str(child).strip())))

    recurse(root)
    return blocks
