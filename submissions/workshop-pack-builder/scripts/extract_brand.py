#!/usr/bin/env python3
"""Extract brand colors and fonts from a PowerPoint template or deck.

Reads the theme of a .pptx, .potx or .pptm (ppt/theme/theme*.xml, the one
the first slide master uses) and writes a small brand JSON that
build_deck.py and build_docs.py accept with --brand:

  {"source": "...", "colors": {"dk1": "#1F2937", ..., "accent1": "#2563EB"},
   "fonts": {"major": "Segoe UI Semibold", "minor": "Segoe UI"},
   "text_on_accent1": "#FFFFFF", "contrast_accent1_on_lt1": 4.9}

Without a file, --neutral writes a built-in neutral palette.

Usage:
  python extract_brand.py template.potx --json-out brand.json
  python extract_brand.py --neutral --json-out brand.json

Standard library only. Reads XML from the zip; never runs content from it.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET  # nosec B405 - DOCTYPE is rejected before parsing; defusedxml used when installed
import zipfile

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]
NEUTRAL = {"dk1": "#1F2937", "lt1": "#FFFFFF", "dk2": "#0F2A44", "lt2": "#F1F4F8",
           "accent1": "#2563EB", "accent2": "#0D9488", "accent3": "#7C3AED", "accent4": "#D97706",
           "accent5": "#DB2777", "accent6": "#475569", "hlink": "#1D4ED8", "folHlink": "#6D28D9"}
NEUTRAL_FONTS = {"major": "Segoe UI Semibold", "minor": "Segoe UI"}


def _lum(h: str) -> float:
    h = h.lstrip("#")
    def lin(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def _theme_path(z: zipfile.ZipFile) -> str | None:
    names = z.namelist()
    rels = "ppt/slideMasters/_rels/slideMaster1.xml.rels"
    if rels in names:
        m = re.search(r'Target="([^"]*theme[^"]*\.xml)"', z.read(rels).decode("utf-8", "replace"))
        if m:
            p = posixpath.normpath(posixpath.join("ppt/slideMasters", m.group(1)))
            if p in names:
                return p
    themes = sorted(n for n in names if re.match(r"ppt/theme/theme\d+\.xml$", n))
    return themes[0] if themes else None


def extract(path: str) -> dict:
    with zipfile.ZipFile(path) as z:
        tp = _theme_path(z)
        if not tp:
            raise ValueError("no theme found in the file")
        data = z.read(tp)
    if b"<!DOCTYPE" in data[:4096].upper() or b"<!ENTITY" in data.upper():
        raise ValueError("theme XML declares a DOCTYPE or entities; refusing to parse")
    try:
        from defusedxml.ElementTree import fromstring as safe_fromstring
        root = safe_fromstring(data)
    except ImportError:
        root = ET.fromstring(data)  # nosec B314 - DOCTYPE and entities rejected above
    colors = {}
    scheme = root.find(f".//{A}clrScheme")
    if scheme is not None:
        for slot in SLOTS:
            el = scheme.find(f"{A}{slot}")
            if el is None:
                continue
            srgb = el.find(f"{A}srgbClr")
            sysc = el.find(f"{A}sysClr")
            if srgb is not None:
                colors[slot] = "#" + srgb.get("val", "000000").upper()
            elif sysc is not None:
                colors[slot] = "#" + (sysc.get("lastClr") or ("000000" if slot.startswith("dk") else "FFFFFF")).upper()
    fonts = {}
    for key, tag in (("major", "majorFont"), ("minor", "minorFont")):
        el = root.find(f".//{A}fontScheme/{A}{tag}/{A}latin")
        if el is not None and el.get("typeface"):
            fonts[key] = el.get("typeface")
    missing = [s for s in SLOTS if s not in colors]
    for s in missing:
        colors[s] = NEUTRAL[s]
    for k, v in NEUTRAL_FONTS.items():
        fonts.setdefault(k, v)
    return {"source": path, "colors": colors, "fonts": fonts, "filled_from_neutral": missing}


def finish(brand: dict) -> dict:
    c = brand["colors"]
    a1 = c["accent1"]
    brand["text_on_accent1"] = "#FFFFFF" if contrast(a1, "#FFFFFF") >= contrast(a1, "#000000") else "#000000"
    brand["contrast_accent1_on_lt1"] = contrast(a1, c["lt1"])
    brand["contrast_dk1_on_lt1"] = contrast(c["dk1"], c["lt1"])
    if brand["contrast_dk1_on_lt1"] < 4.5:
        brand.setdefault("warnings", []).append("body text color dk1 on lt1 is below WCAG AA 4.5:1")
    return brand


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--neutral", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)
    if a.neutral or not a.file:
        brand = {"source": "neutral", "colors": dict(NEUTRAL), "fonts": dict(NEUTRAL_FONTS), "filled_from_neutral": []}
    else:
        try:
            brand = extract(a.file)
        except (zipfile.BadZipFile, ValueError, KeyError, ET.ParseError) as e:
            print(f"ERROR: {e}. Use --neutral or ask for a .pptx/.potx.", file=sys.stderr)
            return 1
    brand = finish(brand)
    js = json.dumps(brand, indent=1)
    if a.json_out:
        open(a.json_out, "w", encoding="utf-8").write(js)
    print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main())
