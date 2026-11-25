#!/usr/bin/env python3
"""Turn the mapping, build and QA results into the short chat summary.

  python summarize_run.py --mapping mapping.json --build build.json --qa qa.json [--md-out summary.md]

For the restyle fallback pass the restyle report as --build and omit --mapping.
Every number comes from the JSON files; nothing is re-counted by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def load(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def summarize(mapping, build, qa):
    out = []
    mode = build.get("mode", "rebuild")
    if mode == "rebuild":
        out.append(f"Converted: {build['source_slides']} source slides into {build['output_slides']} slides on "
                   f"{os.path.basename(build['template'])} | file: {os.path.basename(build['out'])}")
        if mapping:
            out += ["", "| # | Source slide | Template layout | Why |", "|---|---|---|---|"]
            outs = {s["source_slide"]: s["output_slides"] for s in build.get("slides", [])}
            for s in mapping["slides"]:
                o = outs.get(s["slide"], [])
                tag = f" (now {o[0]}-{o[-1]})" if len(o) > 1 else ""
                out.append(f"| {s['slide']}{tag} | {s['title'][:40] or '(no title)'} | {s.get('target_layout', '')} | {s.get('reason', '')} |")
    else:
        out.append(f"Restyled (fallback, the template has no usable layouts): {build['slides']} slides | "
                   f"file: {os.path.basename(build['out'])}")
    fixes = build.get("fixes", [])
    out += ["", f"Fixes made ({len(fixes)}):"]
    out += [f"- {'slide ' + str(f['slide']) + ': ' if isinstance(f, dict) and f.get('slide') else ''}"
            f"{f['detail'] if isinstance(f, dict) else f}" for f in fixes[:15]]
    if len(fixes) > 15:
        out.append(f"- and {len(fixes) - 15} more in the build report")
    if build.get("color_map"):
        out.append("- colors mapped to theme: " + ", ".join(f"{k} to {v}" for k, v in list(build["color_map"].items())[:8]))
    warns = [w for w in build.get("warnings", [])]
    over = build.get("overflow", [])
    lint = (qa or {}).get("lint", [])
    out += ["", "Warnings:"]
    if not (warns or over or lint):
        out.append("- none")
    for w in warns:
        out.append(f"- {'slide ' + str(w['slide']) + ': ' if isinstance(w, dict) else ''}{w['detail'] if isinstance(w, dict) else w}")
    for o in over:
        out.append(f"- slide {o['slide']}: {o['detail']}")
    for f in lint:
        out.append(f"- {f['level']} output slide {f['slide']} {f['check']}: {f['detail']}")
    if qa:
        r = qa.get("render") or {}
        sheets = len(r.get("contact_sheets", []))
        out += ["", f"Visual QA: lint {qa['fails']} FAIL, {qa['warnings']} WARN | "
                    + (f"rendered {len(r.get('slides', []))} slides on {sheets} contact sheet(s)" if r
                       else qa.get("render_note", "not rendered"))]
    out += ["", "Please check: fonts on a machine with the brand fonts installed, chart labels and number formats, "
                "picture crops, any slide listed above, and the speaker notes."]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping")
    ap.add_argument("--build", required=True)
    ap.add_argument("--qa")
    ap.add_argument("--md-out")
    a = ap.parse_args(argv)
    md = summarize(load(a.mapping), load(a.build), load(a.qa))
    if a.md_out:
        with open(a.md_out, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
