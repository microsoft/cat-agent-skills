#!/usr/bin/env python3
"""Map every source slide to the best template layout and write the plan.

  python plan_mapping.py --template brand.potx --source deck.pptx \
      --json-out mapping.json --md-out mapping.md [--override 6=1 --override "10=Contoso Clean"]

Rules (first match wins, see references/mapping-rules.md):
  title         -> title layout, else section, else title only
  section       -> section layout, else title, else title only
  content       -> content layout, else caption content, else title only + free content
  two_content   -> two content layout, else comparison, else title only + free content
  comparison    -> comparison layout, else two content (headers merged into each column), else title only
  picture       -> picture layout, else caption content, else content, else title only
  caption_content -> caption content layout, else content, else title only
  title_only    -> title only layout, else content (placeholder removed), else blank
  blank         -> blank layout, else title only
When a kind matches several layouts, the one whose type attribute matches and
whose name is shortest wins. --override SLIDE=LAYOUT takes a layout index or
exact name and is recorded as "user override". You can also edit the JSON.

The plan sets "mode": "rebuild", or "restyle" when the template has no usable
layouts (no layout with a title and a body or content placeholder).
Prints the Markdown table to show the user before building. Read-only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck_model import read_slide  # noqa: E402
from pptx_common import classify_layout, open_deck  # noqa: E402

CHAIN = {
    "title": ["title", "section", "title_only"],
    "section": ["section", "title", "title_only"],
    "content": ["content", "caption_content", "title_only"],
    "two_content": ["two_content", "comparison", "title_only"],
    "comparison": ["comparison", "two_content", "title_only"],
    "picture": ["picture", "caption_content", "content", "title_only"],
    "caption_content": ["caption_content", "content", "title_only"],
    "title_only": ["title_only", "content", "blank"],
    "blank": ["blank", "title_only"],
}
PREFERRED_TYPE = {"title": "title", "section": "secHead", "content": "obj", "two_content": "twoObj",
                  "comparison": "twoTxTwoObj", "picture": "picTx", "caption_content": "objTx",
                  "title_only": "titleOnly", "blank": "blank"}


def layout_table(prs):
    W, H = prs.slide_width, prs.slide_height
    rows = []
    for i, l in enumerate(prs.slide_layouts):
        kind, why = classify_layout(l, W, H)
        rows.append({"index": i, "name": l.name, "kind": kind, "type": l._element.get("type"), "why": why})
    return rows


def pick(kind, layouts):
    for step, k in enumerate(CHAIN.get(kind, ["title_only"])):
        cands = [l for l in layouts if l["kind"] == k]
        if cands:
            cands.sort(key=lambda l: (l["type"] != PREFERRED_TYPE.get(k), len(l["name"])))
            note = "exact match" if step == 0 else f"no {kind.replace('_', ' ')} layout, fell back to {k.replace('_', ' ')}"
            return cands[0], note
    any_title = [l for l in layouts if l["kind"] != "blank"]
    return (any_title[0] if any_title else layouts[0]), "no matching layout; first available used"


def resolve_override(val, layouts):
    if val.isdigit():
        i = int(val)
        if 0 <= i < len(layouts):
            return layouts[i]
    for l in layouts:
        if l["name"] == val:
            return l
    raise ValueError(f"no template layout '{val}'")


def plan(template, source, overrides):
    tprs = open_deck(template)
    sprs = open_deck(source)
    layouts = layout_table(tprs)
    usable = any(l["kind"] in ("content", "two_content", "comparison", "caption_content") for l in layouts)
    W, H = sprs.slide_width, sprs.slide_height
    slides = []
    for i, s in enumerate(sprs.slides, 1):
        m = read_slide(s, i, W, H)
        entry = {"slide": i, "title": m["title"][:80], "source_layout": m["layout"], "kind": m["kind"],
                 "kind_reason": m["kind_reason"], "split": False}
        if usable:
            lay, note = pick(m["kind"], layouts)
            if str(i) in overrides:
                lay, note = resolve_override(overrides[str(i)], layouts), "user override"
            entry.update({"target_layout": lay["name"], "target_layout_index": lay["index"],
                          "target_kind": lay["kind"], "reason": note})
        slides.append(entry)
    return {
        "source": os.path.abspath(source), "template": os.path.abspath(template),
        "mode": "rebuild" if usable else "restyle",
        "mode_reason": "template has usable layouts" if usable else
        "template has no layout with a title and a body or content placeholder: restyle a copy of the source",
        "template_layouts": layouts, "slides": slides,
        "fit": {"title_floor_pt": 24, "body_floor_pt": 14, "table_floor_pt": 10},
    }


def table_md(p):
    if p["mode"] == "restyle":
        return ("Mode: restyle (fallback). " + p["mode_reason"] + "\n\n"
                f"{len(p['slides'])} slides keep their current layouts; theme colors and fonts come from the brand file.")
    out = ["| # | Source slide | Source layout | Template layout | Why |", "|---|---|---|---|---|"]
    for s in p["slides"]:
        out.append(f"| {s['slide']} | {s['title'][:40] or '(no title)'} | {s['source_layout']} | "
                   f"{s['target_layout']} | {s['reason']}; {s['kind_reason']} |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--md-out")
    ap.add_argument("--override", action="append", default=[], help="SLIDE=LAYOUT_INDEX_OR_NAME")
    a = ap.parse_args(argv)
    ov = {}
    for o in a.override:
        k, _, v = o.partition("=")
        if not k.strip().isdigit() or not v:
            print(f"ERROR: bad --override '{o}', use SLIDE=LAYOUT", file=sys.stderr)
            return 2
        ov[k.strip()] = v.strip()
    try:
        p = plan(a.template, a.source, ov)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    with open(a.json_out, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=1)
    md = table_md(p)
    if a.md_out:
        with open(a.md_out, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
