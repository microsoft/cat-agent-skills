#!/usr/bin/env python3
"""Inspect a brand template and a source deck before any build.

  python inspect_decks.py --template brand.potx --source deck.pptx --json-out inspect.json

Template: slide size, every layout (name, layout type, kind, placeholders
with type, index and position in inches), theme colors and fonts (via
extract_brand.py), the sample slides it ships with and their text (used later
to catch leftover template text), and solid swatch colors found on its slides.
It also says whether the template has usable layouts (a title plus a body or
content placeholder). If not, use the restyle fallback.

Source: slide size, theme, and per slide the layout it used, the kind the
mapping rules see, and its content blocks (title, subtitle, body text with
bullet levels, pictures, tables, charts, shapes, groups, notes).

Prints a short Markdown summary; the JSON holds the detail. Read-only: both
files are opened from memory and never written.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck_model import model_summary, read_slide  # noqa: E402
from pptx_common import (classify_layout, layout_placeholders, open_deck, text_of,  # noqa: E402
                         theme_colors, theme_fonts)

EMU_IN = 914400


def _in(box):
    return [round(v / EMU_IN, 2) for v in box] if box else None


def swatches(prs):
    from pptx.enum.dml import MSO_FILL
    c = Counter()
    for s in prs.slides:
        for sh in s.shapes:
            try:
                if sh.fill.type == MSO_FILL.SOLID and sh.fill.fore_color.type is not None:
                    c[str(sh.fill.fore_color.rgb)] += 1
            except (AttributeError, TypeError, ValueError, NotImplementedError):
                continue
    return [k for k, _ in c.most_common(12)]


def inspect_template(path):
    prs = open_deck(path)
    W, H = prs.slide_width, prs.slide_height
    layouts = []
    for i, l in enumerate(prs.slide_layouts):
        kind, why = classify_layout(l, W, H)
        layouts.append({"index": i, "name": l.name, "type": l._element.get("type"), "kind": kind, "why": why,
                        "placeholders": [{"idx": p["idx"], "type": p["type"], "role": p["role"],
                                          "box_in": _in(p["box"])} for p in layout_placeholders(l)]})
    usable = [x for x in layouts if x["kind"] in ("content", "two_content", "comparison", "caption_content")]
    samples = []
    for n, s in enumerate(prs.slides, 1):
        texts = [text_of(sh).strip() for sh in s.shapes if text_of(sh).strip()]
        samples.append({"slide": n, "layout": s.slide_layout.name, "texts": texts})
    return {
        "file": path, "slide_size_in": [round(W / EMU_IN, 2), round(H / EMU_IN, 2)],
        "masters": len(prs.slide_masters), "layouts": layouts, "theme_colors": theme_colors(prs),
        "theme_fonts": theme_fonts(prs), "sample_slides": samples, "swatch_colors": swatches(prs),
        "usable_layouts": bool(usable),
        "recommended_mode": "rebuild" if usable else "restyle",
    }


def inspect_source(path):
    prs = open_deck(path)
    W, H = prs.slide_width, prs.slide_height
    slides = [model_summary(read_slide(s, i, W, H)) for i, s in enumerate(prs.slides, 1)]
    return {"file": path, "slide_size_in": [round(W / EMU_IN, 2), round(H / EMU_IN, 2)],
            "theme_colors": theme_colors(prs), "theme_fonts": theme_fonts(prs), "slides": slides}


def summary_md(t, s):
    out = [f"Template: {os.path.basename(t['file'])} | {t['slide_size_in'][0]} x {t['slide_size_in'][1]} in | "
           f"{len(t['layouts'])} layouts | {len(t['sample_slides'])} sample slides | fonts "
           f"{t['theme_fonts'].get('major')} / {t['theme_fonts'].get('minor')} | accent1 #{t['theme_colors'].get('accent1')}",
           f"Recommended mode: {t['recommended_mode']}", "", "| # | Layout | Kind | Placeholders |", "|---|---|---|---|"]
    for l in t["layouts"]:
        out.append(f"| {l['index']} | {l['name']} | {l['kind']} | {', '.join(p['role'] for p in l['placeholders']) or 'none'} |")
    out += ["", f"Source: {os.path.basename(s['file'])} | {s['slide_size_in'][0]} x {s['slide_size_in'][1]} in | "
            f"{len(s['slides'])} slides", "", "| # | Title | Source layout | Kind | Blocks |", "|---|---|---|---|---|"]
    for m in s["slides"]:
        blocks = ["subtitle"] if m["subtitle"] else []
        if m["texts"]:
            blocks.append(f"{len(m['texts'])} text")
        if m["pictures"]:
            blocks.append(f"{m['pictures']} picture")
        blocks += [g["type"] for g in m["graphics"]]
        if m["notes_chars"]:
            blocks.append("notes")
        out.append(f"| {m['slide']} | {m['title'][:40]} | {m['layout']} | {m['kind']} | {', '.join(blocks)} |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)
    try:
        t = inspect_template(a.template)
        s = inspect_source(a.source)
    except Exception as e:  # noqa: BLE001 - report any unreadable file plainly
        print(f"ERROR: could not read a file: {e}", file=sys.stderr)
        return 1
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump({"template": t, "source": s}, fh, indent=1)
    print(summary_md(t, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
