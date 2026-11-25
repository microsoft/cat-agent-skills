#!/usr/bin/env python3
"""Quality gate for a workshop pack. Static: it reads files, it runs nothing.

  python check_pack.py workshop.json [--source-map source_map.json] \
      [--pack-dir pack/] [--deck pack/deck.pptx] [--html] [--json]

Checks (FAIL blocks delivery, WARN needs a look):
  timing        module labels and timeboxes are 5/10/15/20/30/45/60 and the
                modules add up to total_minutes (uses timing.py)
  coverage      every objective is covered by at least one module, and every
                objective a module names exists
  activity      every module except breaks has at least one activity
  exercise      every activity has objective, timebox, instructions, materials,
                expected_output, debrief and fallback
  citations     every key point and activity cites a source; with --source-map,
                every cited ref exists in the map
  gaps          spec.gaps exists (an empty list is fine; a missing key is a WARN)
  pack          with --pack-dir: all five core files and optional outputs with
                data in the spec exist; --html also requires workshop.html
  placeholders  no TODO, TBD, XXX, lorem ipsum, [insert ...], {{...}}, <field> tokens
                tokens in the spec or in any .docx/.pptx/.md/.html in --pack-dir
  writing       no em dashes, no filler words, "understand" not used as an
                objective verb, executive summary present at the top of every
                document in --pack-dir
  deck          with --deck: the layout lint from deck_preview.py. The visual
                check itself is done by looking at the rendered slides.
Exit 1 when any FAIL.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timing  # noqa: E402

FILLER = ["genuinely", "honestly", "really", "very", "simply", "just", "basically", "actually", "literally",
          "totally", "quite"]
PLACEHOLDER = [r"\bTODO\b", r"\bTBD\b", r"\bXXX+\b", r"lorem ipsum", r"\[(?:insert|add|your|placeholder|tbc)[^\]]*\]",
               r"\{\{[^}]*\}\}", r"<[a-z][a-z0-9 #/,.'-]{1,40}>", r"&lt;[a-z][^&]{1,40}&gt;", r"\?\?\?"]
EXERCISE_FIELDS = ["objective", "timebox", "instructions", "materials", "expected_output", "debrief", "fallback"]


def R(level, where, check, detail):
    return {"level": level, "where": where, "check": check, "detail": detail}


def spec_strings(obj, path="spec"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("sources", "location"):
                continue
            yield from spec_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from spec_strings(v, f"{path}[{i}]")


def text_findings(where, text):
    out = []
    for ch, label in (("\u2014", "em dash"), ("&mdash;", "em dash entity"), ("&#8212;", "em dash entity")):
        n = text.count(ch)
        if n:
            out.append(R("FAIL", where, "em_dash", f"{n} x {label}"))
    for w in FILLER:
        for m in re.finditer(r"(?<![\w-])" + w + r"(?![\w-])", text, flags=re.I):
            ctx = text[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
            out.append(R("WARN", where, "filler_word", f"'{w}': ...{ctx}..."))
            break
    for p in PLACEHOLDER:
        m = re.search(p, text, flags=re.I)
        if m:
            out.append(R("FAIL", where, "placeholder", f"unresolved '{m.group(0)}'"))
    return out


def docx_text(path):
    import docx
    d = docx.Document(path)
    paras = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            paras.append(" | ".join(c.text for c in row.cells))
    return paras


def pptx_text(path):
    from pptx import Presentation
    prs = Presentation(path)
    out = []
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                out.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                out += [c.text for row in sh.table.rows for c in row.cells]
        if s.has_notes_slide:
            out.append(s.notes_slide.notes_text_frame.text)
    return out


def check(spec, smap, pack_dir, deck, require_html=False):
    res = []
    # timing
    for r in timing.check_spec(spec):
        r["check"] = "timing:" + r["check"]
        res.append(r)
    # coverage
    obj_ids = [o.get("id") for o in spec.get("objectives", [])]
    if not obj_ids:
        res.append(R("FAIL", "spec", "coverage", "no learning objectives"))
    covered = set()
    for m in spec.get("modules", []):
        for oid in m.get("objectives", []):
            if oid not in obj_ids:
                res.append(R("FAIL", m.get("id", "?"), "coverage", f"names unknown objective {oid}"))
            covered.add(oid)
    for oid in obj_ids:
        if oid not in covered:
            res.append(R("FAIL", oid, "coverage", "objective is not covered by any module"))
    for o in spec.get("objectives", []):
        if re.search(r"\b(understand|know|learn about|be aware)\b", o.get("text", ""), flags=re.I):
            res.append(R("WARN", o.get("id"), "objective_verb", "use an observable verb (explain, map, build, decide), not understand/know"))
    # activity + exercise fields + citations
    known_refs = set()
    source_list = smap.get("sources", []) if smap is not None else spec.get("sources", [])
    known_sources = {s["id"] for s in source_list}
    if smap is not None:
        for s in smap.get("sources", []):
            for u in s.get("units", []):
                known_refs.add(u["ref"])

    def check_refs(where, refs):
        if not refs:
            res.append(R("FAIL", where, "citations", "no source cited"))
            return
        for ref in refs:
            sid = ref.split(".")[0]
            if sid not in known_sources:
                res.append(R("FAIL", where, "citations", f"cites unknown source {sid}"))
            elif smap is not None and "." in ref and ref not in known_refs:
                res.append(R("FAIL", where, "citations", f"cites {ref}, which is not in the source map"))

    for m in spec.get("modules", []):
        mid = m.get("id", "?")
        if m.get("type") != "break":
            if not m.get("activities"):
                res.append(R("FAIL", mid, "activity", "module has no activity"))
            for i, k in enumerate(m.get("key_points", [])):
                check_refs(f"{mid}.kp{i + 1}", k.get("sources"))
        for a in m.get("activities", []):
            aid = f"{mid}/{a.get('id', '?')}"
            missing = [f for f in EXERCISE_FIELDS if not a.get(f)]
            if missing:
                res.append(R("FAIL", aid, "exercise", "missing " + ", ".join(missing)))
            check_refs(aid, a.get("sources"))
    for i, item in enumerate((spec.get("pre_read") or {}).get("items", []), 1):
        if item.get("sources"):
            check_refs(f"pre_read.item{i}", item["sources"])
    if not spec.get("executive_summary"):
        res.append(R("FAIL", "spec", "writing", "no executive_summary"))
    if "gaps" not in spec:
        res.append(R("WARN", "spec", "gaps", "no gaps list: record what the sources do not cover (an empty list is fine)"))
    # spec text
    for where, t in spec_strings(spec):
        for f in text_findings(where, t):
            res.append(f)
    # pack files
    if require_html and not pack_dir:
        res.append(R("FAIL", "pack", "pack", "--html requires --pack-dir to check workshop.html"))
    if pack_dir:
        required = ["agenda.docx", "agenda-one-page.docx", "deck.pptx",
                    "facilitator-guide.docx", "participant-workbook.docx"]
        for key, name in (("pre_read", "pre-read.docx"), ("survey", "feedback-survey.docx"),
                          ("follow_up_email", "follow-up-email-draft.md")):
            if spec.get(key):
                required.append(name)
        if require_html:
            required.append("workshop.html")
        for name in required:
            if not os.path.isfile(os.path.join(pack_dir, name)):
                res.append(R("FAIL", name, "pack", "missing required deliverable"))
        files = sorted(glob.glob(os.path.join(pack_dir, "*")))
        if not files:
            res.append(R("FAIL", pack_dir, "pack", "no files in the pack folder"))
        for path in files:
            name = os.path.basename(path)
            ext = os.path.splitext(name)[1].lower()
            try:
                if ext == ".docx":
                    paras = docx_text(path)
                    text = "\n".join(paras)
                    head = [p.strip().lower() for p in paras if p.strip()][:4]
                    if not any(h.startswith("executive summary") for h in head):
                        res.append(R("FAIL", name, "exec_summary", "document does not start with an executive summary"))
                elif ext == ".pptx":
                    paras = pptx_text(path)
                    text = "\n".join(paras)
                    if "executive summary" not in "\n".join(paras[:12]).lower():
                        res.append(R("WARN", name, "exec_summary", "no executive summary slide near the start"))
                elif ext in (".md", ".html", ".htm", ".txt"):
                    text = open(path, encoding="utf-8", errors="replace").read()
                    if ext in (".html", ".htm"):
                        if re.search(r"<(script|link|img|iframe)[^>]+(src|href)\s*=\s*[\"']https?:", text, flags=re.I):
                            res.append(R("FAIL", name, "html", "external resource in the page"))
                        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
                        text = re.sub(r"<[^>]+>", " ", text)
                        if "executive summary" not in text.lower()[:2000]:
                            res.append(R("FAIL", name, "exec_summary", "page does not start with an executive summary"))
                else:
                    continue
            except Exception as e:  # noqa: BLE001
                res.append(R("FAIL", name, "read", f"could not read: {e}"))
                continue
            for f in text_findings(name, text):
                res.append(f)
    # deck lint
    if deck:
        try:
            import deck_preview
            n, lint = deck_preview.lint(deck)
            for f in lint:
                res.append(R(f["level"], f"slide {f['slide']}", "deck:" + f["check"], f["detail"]))
            res.append(R("INFO", os.path.basename(deck), "deck", f"{n} slides linted. Visual check: render with deck_preview.py and look at every slide."))
        except Exception as e:  # noqa: BLE001
            res.append(R("FAIL", deck, "deck", f"could not lint: {e}"))
    else:
        res.append(R("WARN", "deck", "deck", "deck not checked: pass --deck"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--source-map")
    ap.add_argument("--pack-dir")
    ap.add_argument("--deck")
    ap.add_argument("--html", action="store_true", help="require the requested workshop.html in --pack-dir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    smap = json.load(open(a.source_map, encoding="utf-8")) if a.source_map else None
    res = check(spec, smap, a.pack_dir, a.deck, require_html=a.html)
    fails = [r for r in res if r["level"] == "FAIL"]
    warns = [r for r in res if r["level"] == "WARN"]
    if a.json:
        print(json.dumps({"passed": not fails, "fails": len(fails), "warns": len(warns), "results": res}, indent=1))
    else:
        for r in res:
            print(f"{r['level']:<5} {r['where']:<28} {r['check']:<22} {r['detail']}")
        print("PASSED" if not fails else f"FAILED: {len(fails)}", f"({len(warns)} warnings)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
