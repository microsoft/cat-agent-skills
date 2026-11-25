#!/usr/bin/env python3
"""Recolor and refont helpers, plus the restyle fallback mode.

Fallback mode (the template has no usable layouts, for example a brand deck
that is only a color sheet): copy the source deck, replace its theme colors
and fonts with the brand values from extract_brand.py, map hard-coded RGB
colors in shapes and text to theme slots, and drop hard-coded font faces from
slides, layouts, masters and charts so the theme fonts apply. Layouts,
positions and content stay as they are.

  python extract_brand.py brand-sheet.pptx --json-out brand.json
  python restyle.py --source deck.pptx --brand brand.json --out restyled.pptx --report-out restyle.json

The source file is read from memory and never written; --out must differ
from the source. Helpers used by apply_template.py:
  build_color_map(prs_or_elements, src_colors) -> {"RRGGBB": "accent1", ...}
  remap_colors(element, cmap)    replace a:srgbClr with a:schemeClr
  strip_fonts(element)           drop explicit latin, ea and cs typefaces
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import sys

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx_common import A, nearest_slot, open_deck, rgb_tuple, theme_colors, theme_part  # noqa: E402

SCHEME_NAME = {"dk1": "tx1", "lt1": "bg1", "dk2": "tx2", "lt2": "bg2"}
ACCENTS = [f"accent{i}" for i in range(1, 7)]


def _sat_light(hexval):
    r, g, b = (c / 255 for c in rgb_tuple(hexval))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s, l


def _skip(el):
    p = el.getparent()
    while p is not None:
        if p.tag in (f"{A}blip",):
            return True
        p = p.getparent()
    return False


def collect_rgb(elements):
    seen = []
    for root in elements:
        for el in root.iter(f"{A}srgbClr"):
            if _skip(el):
                continue
            v = (el.get("val") or "").upper()
            if len(v) == 6 and v not in seen:
                seen.append(v)
    return seen


def build_color_map(elements, src_colors: dict) -> dict:
    """Map each hard-coded color to a theme slot.

    1. Close to a source theme color (distance < 24): keep that slot, so the
       author's theme intent carries over.
    2. Chromatic color: the next unused accent, in order of first use.
    3. Neutral color (low saturation): dk1, lt1, dk2 or lt2 by lightness.
    """
    cmap, used = {}, []
    for v in collect_rgb(elements):
        slot, dist = nearest_slot(v, src_colors) if src_colors else (None, 1e9)
        if slot and dist < 24:
            cmap[v] = slot
            if slot in ACCENTS and slot not in used:
                used.append(slot)
            continue
        s, l = _sat_light(v)
        if s < 0.2 or l > 0.93 or l < 0.08:
            cmap[v] = "lt1" if l > 0.85 else ("lt2" if l > 0.6 else ("dk2" if l > 0.25 else "dk1"))
            continue
        free = [a for a in ACCENTS if a not in used]
        slot = free[0] if free else ACCENTS[len(cmap) % 6]
        used.append(slot)
        cmap[v] = slot
    return cmap


def remap_colors(root, cmap: dict) -> int:
    n = 0
    for el in list(root.iter(f"{A}srgbClr")):
        if _skip(el):
            continue
        v = (el.get("val") or "").upper()
        slot = cmap.get(v)
        if not slot:
            continue
        new = etree.Element(f"{A}schemeClr", val=SCHEME_NAME.get(slot, slot))
        for ch in el:
            new.append(ch)
        el.getparent().replace(el, new)
        n += 1
    return n


def strip_fonts(root) -> int:
    n = 0
    for tag in ("latin", "ea", "cs"):
        for el in list(root.iter(f"{A}{tag}")):
            par = el.getparent()
            if par is None or par.tag.split("}")[-1] not in ("rPr", "defRPr", "endParaRPr"):
                continue
            tf = el.get("typeface", "")
            if tf.startswith("+"):
                continue
            par.remove(el)
            n += 1
    return n


def set_theme(prs, brand: dict):
    """Replace the color and font scheme of every theme the deck's masters use."""
    parts = []
    for master in prs.slide_masters:
        from pptx.opc.constants import RELATIONSHIP_TYPE as RT
        tp = master.part.part_related_by(RT.THEME)
        if tp not in parts:
            parts.append(tp)
    for part in parts:
        root = etree.fromstring(part.blob, parser=etree.XMLParser(resolve_entities=False, no_network=True))
        scheme = root.find(f".//{A}clrScheme")
        for el in list(scheme):
            slot = el.tag.split("}")[-1]
            val = brand["colors"].get(slot)
            if val:
                for ch in list(el):
                    el.remove(ch)
                etree.SubElement(el, f"{A}srgbClr", val=val.lstrip("#").upper())
        for key, tag in (("major", "majorFont"), ("minor", "minorFont")):
            lat = root.find(f".//{A}fontScheme/{A}{tag}/{A}latin")
            if lat is not None and brand.get("fonts", {}).get(key):
                lat.set("typeface", brand["fonts"][key])
        part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def restyle(source, brand_path, out):
    if os.path.abspath(source) == os.path.abspath(out):
        raise ValueError("--out must be a new file; the source is never overwritten")
    with open(brand_path, encoding="utf-8") as fh:
        brand = json.load(fh)
    prs = open_deck(source)
    src_colors = theme_colors(prs)
    elements = [s._element for s in prs.slides]
    elements += [l._element for m in prs.slide_masters for l in m.slide_layouts]
    elements += [m._element for m in prs.slide_masters]
    charts = []
    for s in prs.slides:
        for sh in s.shapes:
            if getattr(sh, "has_chart", False) and sh.has_chart:
                charts.append(sh.chart)
    cmap = build_color_map(elements + [c._chartSpace for c in charts], src_colors)
    recolored = sum(remap_colors(e, cmap) for e in elements + [c._chartSpace for c in charts])
    fonts = sum(strip_fonts(e) for e in elements + [c._chartSpace for c in charts])
    set_theme(prs, brand)
    fit_fixes, overflow = fit_text(prs, brand)
    prs.save(out)
    return {"mode": "restyle", "source": source, "brand": brand.get("source"), "out": out,
            "slides": len(prs.slides), "color_map": {f"#{k}": v for k, v in cmap.items()},
            "colors_recolored": recolored, "font_overrides_removed": fonts,
            "fixes": [f"theme colors and fonts replaced with {brand['fonts'].get('major')} / {brand['fonts'].get('minor')}",
                      f"{recolored} hard-coded colors mapped to theme slots",
                      f"{fonts} hard-coded font faces removed so theme fonts apply"] + fit_fixes,
            "overflow": overflow,
            "warnings": ["layouts, positions and backgrounds are unchanged: check each slide by eye"]}


def fit_text(prs, brand, title_floor=24, body_floor=14):
    """Shrink placeholder text that no longer fits with the brand fonts (same rules as the rebuild)."""
    from apply_template import char_factor, default_sizes, fit_sizes
    from deck_model import paragraphs_of
    from pptx.util import Pt
    from pptx_common import emu_box, ph_type, role_of
    cf = char_factor(brand.get("fonts", {}))
    fixes, overflow = [], []
    for n, s in enumerate(prs.slides, 1):
        for sh in s.placeholders:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            if any(r.font.size for p in sh.text_frame.paragraphs for r in p.runs):
                continue  # the author set sizes: leave them, the QA lint reports any overflow
            role = role_of(ph_type(sh))
            if role == "meta":
                continue
            r2 = "title" if role == "title" else "text"
            base = default_sizes(sh, r2, s.slide_layout, s.slide_layout.slide_master)
            sizes, fits = fit_sizes(paragraphs_of(sh.text_frame), emu_box(sh), base,
                                    title_floor if r2 == "title" else body_floor, cf)
            if sizes:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(sizes[min(p.level, len(sizes) - 1)])
                fixes.append(f"slide {n}: '{sh.name}' text shrunk from {base[0]:g} to {sizes[0]:g} pt to fit the brand fonts")
            if not fits:
                overflow.append({"slide": n, "shape": sh.name,
                                 "detail": "text still overflows at the floor size: shorten it or split the slide by hand"})
    return fixes, overflow


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--brand", required=True, help="brand.json from extract_brand.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report-out")
    a = ap.parse_args(argv)
    try:
        rep = restyle(a.source, a.brand, a.out)
    except (ValueError, OSError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if a.report_out:
        with open(a.report_out, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
