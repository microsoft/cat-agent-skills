#!/usr/bin/env python3
"""Build a citable source map from the user's reference material.

Reads .pptx (slide text and speaker notes), .docx (sections by heading, plus
tables), .pdf (per page), .md / .txt (sections by heading) and .html / .htm
(sections by heading; use this for URLs you fetched and saved). Every unit gets
a stable citation ref:

  S1.slide3   S2.sec4   S3.page7   (S<n> = source number in input order)

The script never fetches anything from the network. Fetch a URL with your web
tool, save the text as .md or .html, and pass the URL with --url so the map
records where it came from:

  python build_source_map.py deck.pptx guide.docx paper.pdf saved_page.md \
      --url saved_page.md=https://example.org/article \
      --json-out source_map.json --md-out source_map.md

A file that cannot be read (protected, corrupt, unsupported) is listed under
"errors" and the rest still map. Exit code 1 only when no source could be read.

Needs python-pptx, python-docx and pypdf (pdfplumber is used as a fallback for
PDFs when installed). beautifulsoup4 is optional for HTML.
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import os
import re
import sys

NUM_RE = re.compile(r"[^.!?\n]*?(?:\d[\d,.]*\s?(?:%|percent|million|billion|k\b|x\b)|\$\s?\d[\d,.]*|\b(?:19|20)\d\d\b|\b\d{2,}[\d,.]*\b)[^.!?\n]*[.!?]?")


def _clean(t: str) -> str:
    t = t.replace("\x0b", " ").replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", t)).strip()


def read_pptx(path):
    from pptx import Presentation
    prs = Presentation(path)
    units = []
    for i, slide in enumerate(prs.slides, 1):
        title, parts = "", []
        for sh in slide.shapes:
            texts = []
            if sh.has_text_frame:
                texts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    texts.append(" | ".join(c.text for c in row.cells))
            if sh.shape_type == 6 and hasattr(sh, "shapes"):  # group
                for g in sh.shapes:
                    if g.has_text_frame:
                        texts.append(g.text_frame.text)
            t = _clean("\n".join(texts))
            if not t:
                continue
            if not title and sh.is_placeholder and sh.placeholder_format.type in (1, 3):  # TITLE, CENTER_TITLE
                title = t
            else:
                parts.append(t)
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = _clean(slide.notes_slide.notes_text_frame.text)
        units.append({"ref_suffix": f"slide{i}", "label": f"Slide {i}", "heading": title,
                      "text": "\n".join(parts), "notes": notes})
    return units, (prs.core_properties.title or "")


def read_docx(path):
    import docx
    d = docx.Document(path)
    units, cur = [], {"heading": "", "lines": []}

    def flush():
        if cur["heading"] or cur["lines"]:
            n = len(units) + 1
            units.append({"ref_suffix": f"sec{n}", "label": f"Section {n}", "heading": cur["heading"],
                          "text": _clean("\n".join(cur["lines"]))})

    for p in d.paragraphs:
        style = (p.style.name or "").lower() if p.style is not None else ""
        if style.startswith("heading") or style == "title":
            flush()
            cur = {"heading": _clean(p.text), "lines": []}
        elif p.text.strip():
            cur["lines"].append(p.text)
    flush()
    for ti, tbl in enumerate(d.tables, 1):
        rows = [" | ".join(_clean(c.text) for c in r.cells) for r in tbl.rows]
        units.append({"ref_suffix": f"table{ti}", "label": f"Table {ti}", "heading": "",
                      "text": "\n".join(rows)})
    return units, (d.core_properties.title or "")


def read_pdf(path):
    units = []
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        if r.is_encrypted:
            r.decrypt("")
        pages = [p.extract_text() or "" for p in r.pages]
        title = (r.metadata.title if r.metadata and r.metadata.title else "")
    except Exception:  # noqa: BLE001 - fall back below
        pages, title = [], ""
    if not any(p.strip() for p in pages):
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                pages = [pg.extract_text() or "" for pg in pdf.pages]
        except Exception as e:  # noqa: BLE001
            print(f"note: pdfplumber fallback failed for {path}: {e}", file=sys.stderr)
    for i, t in enumerate(pages, 1):
        units.append({"ref_suffix": f"page{i}", "label": f"Page {i}", "heading": "", "text": _clean(t)})
    if not units or not any(u["text"] for u in units):
        raise ValueError("no extractable text (scanned PDF?): run OCR first or ask for a text version")
    return units, title


def _split_headed(lines, is_heading):
    units, cur = [], {"heading": "", "lines": []}

    def flush():
        if cur["heading"] or any(l.strip() for l in cur["lines"]):
            n = len(units) + 1
            units.append({"ref_suffix": f"sec{n}", "label": f"Section {n}", "heading": cur["heading"],
                          "text": _clean("\n".join(cur["lines"]))})

    for line in lines:
        h = is_heading(line)
        if h is not None:
            flush()
            cur = {"heading": h, "lines": []}
        else:
            cur["lines"].append(line)
    flush()
    return units


def read_md(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    url = None
    m = re.match(r"\s*(?:Source|URL)\s*:\s*(https?://\S+)", text, flags=re.I)
    if m:
        url = m.group(1)
    title = ""
    tm = re.search(r"^#\s+(.+)$", text, flags=re.M)
    if tm:
        title = tm.group(1).strip()

    def is_h(line):
        hm = re.match(r"^#{1,3}\s+(.+)$", line)
        return hm.group(1).strip() if hm else None

    return _split_headed(text.splitlines(), is_h), title, url


def read_html(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    title = ""
    tm = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.S | re.I)
    if tm:
        title = _clean(htmllib.unescape(re.sub(r"<[^>]+>", "", tm.group(1))))
    url = None
    cm = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', raw, flags=re.I)
    if cm:
        url = cm.group(1)
    body = re.sub(r"<(head|script|style|nav|footer|header|noscript)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    body = re.sub(r"<h([1-3])[^>]*>(.*?)</h\1>", lambda m: "\n@@H@@" + re.sub(r"<[^>]+>", "", m.group(2)) + "\n", body, flags=re.S | re.I)
    body = re.sub(r"<(br|/p|/li|/div|/tr)[^>]*>", "\n", body, flags=re.I)
    body = htmllib.unescape(re.sub(r"<[^>]+>", " ", body))
    lines = [l.strip() for l in body.splitlines()]

    def is_h(line):
        return _clean(line[5:]) if line.startswith("@@H@@") else None

    return _split_headed([l for l in lines if l], is_h), title, url


def extract_numbers(ref, text):
    out = []
    for m in NUM_RE.finditer(text or ""):
        s = _clean(m.group(0))
        if 8 <= len(s) <= 240:
            out.append({"ref": ref, "snippet": s})
    return out


def build(paths, urls, max_chars):
    sources, errors, n = [], [], 0
    for path in paths:
        ext = os.path.splitext(path)[1].lower()
        url = urls.get(path) or urls.get(os.path.basename(path))
        try:
            if ext == ".pptx":
                units, title = read_pptx(path); kind = "deck"
            elif ext == ".docx":
                units, title = read_docx(path); kind = "document"
            elif ext == ".pdf":
                units, title = read_pdf(path); kind = "pdf"
            elif ext in (".md", ".markdown", ".txt"):
                units, title, u2 = read_md(path); kind = "web page" if (url or u2) else "text"; url = url or u2
            elif ext in (".html", ".htm"):
                units, title, u2 = read_html(path); kind = "web page"; url = url or u2
            else:
                raise ValueError(f"unsupported file type '{ext}' (convert .ppt/.doc to .pptx/.docx first)")
        except Exception as e:  # noqa: BLE001
            errors.append({"path": path, "error": f"{type(e).__name__}: {e}"})
            continue
        n += 1
        sid = f"S{n}"
        out_units, numbers, words = [], [], 0
        for u in units:
            ref = f"{sid}.{u['ref_suffix']}"
            text = u.get("text", "")
            if max_chars and len(text) > max_chars:
                text = text[:max_chars] + " [truncated]"
            entry = {"ref": ref, "label": u["label"], "heading": u.get("heading", ""), "text": text}
            if u.get("notes"):
                entry["notes"] = u["notes"]
            wc = len((u.get("text", "") + " " + u.get("notes", "")).split())
            entry["words"] = wc
            words += wc
            out_units.append(entry)
            numbers += extract_numbers(ref, u.get("text", "") + "\n" + u.get("notes", ""))
        sources.append({"id": sid, "title": title or os.path.splitext(os.path.basename(path))[0],
                        "type": kind, "path": path, "url": url, "words": words,
                        "units": out_units, "numeric_claims": numbers})
    return {"sources": sources, "errors": errors}


def to_markdown(smap):
    out = ["# Source map", ""]
    out.append("| ID | Title | Type | Units | Words | Location |")
    out.append("|---|---|---|---|---|---|")
    for s in smap["sources"]:
        out.append(f"| {s['id']} | {s['title']} | {s['type']} | {len(s['units'])} | {s['words']} | {s['url'] or s['path']} |")
    if smap["errors"]:
        out += ["", "## Could not read", ""] + [f"- {e['path']}: {e['error']}" for e in smap["errors"]]
    for s in smap["sources"]:
        out += ["", f"## {s['id']} {s['title']}", ""]
        for u in s["units"]:
            head = f" {u['heading']}" if u["heading"] else ""
            first = (u["text"] or u.get("notes", "")).replace("\n", " ")
            out.append(f"- **{u['ref']}** ({u['label']}){head}: {first[:160]}{'...' if len(first) > 160 else ''}")
        if s["numeric_claims"]:
            out += ["", "Numbers and dates to cite exactly:"]
            out += [f"- {c['ref']}: {c['snippet']}" for c in s["numeric_claims"][:25]]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="files or folders")
    ap.add_argument("--url", action="append", default=[], help="FILE=URL for a saved web page")
    ap.add_argument("--json-out")
    ap.add_argument("--md-out")
    ap.add_argument("--max-chars", type=int, default=6000, help="truncate a unit's text (0 = no limit)")
    a = ap.parse_args(argv)
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                files += [os.path.join(root, x) for x in sorted(names) if not x.startswith((".", "~$"))]
        else:
            files.append(p)
    urls = dict(u.split("=", 1) for u in a.url)
    smap = build(files, urls, a.max_chars)
    js = json.dumps(smap, indent=1, ensure_ascii=False)
    for path in (a.json_out, a.md_out):
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if a.json_out:
        open(a.json_out, "w", encoding="utf-8").write(js)
    if a.md_out:
        open(a.md_out, "w", encoding="utf-8").write(to_markdown(smap))
    print(json.dumps({"sources": [{"id": s["id"], "title": s["title"], "units": len(s["units"]), "words": s["words"]}
                                  for s in smap["sources"]], "errors": smap["errors"]}, indent=1))
    return 0 if smap["sources"] else 1


if __name__ == "__main__":
    sys.exit(main())
