#!/usr/bin/env python3
"""Prepare an uploaded image for the hero background and, optionally, a palette inspired by it.

Use only an image the user supplied or approved for this page (a photo, a texture, an
illustration). Never use a product logo or a screenshot of one as a background, and never
pull internal profile photos.

What it does
  * resizes to at most --max-width px wide and re-encodes as JPEG (quality steps down until
    the data URI is under --max-kb, default 180 KB), so the page stays one self-contained file
  * writes a CSS custom property line: --hero-img:url(data:image/jpeg;base64,...)
    to paste into the hero as style="--hero-img:url(...)" together with class "motif-image"
  * --palette-out: picks six distinct, usable colors from the image (median cut) and writes a
    palette JSON in the format extract_brand.py --palette reads. Use it when there is no
    PowerPoint template, or when the user asks for the page to take its colors from the image.
    With a template, the template colors win; the image only supplies the picture.

Usage
  python prepare_hero_image.py photo.jpg --css-out hero-img.css [--palette-out image-palette.json]
  python extract_brand.py --palette image-palette.json --inject Page-Name.html
Requires Pillow.
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import io
import json
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow")


def encode(img: Image.Image, max_kb: int) -> tuple[str, int]:
    for q in (82, 74, 66, 58, 50, 42):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        if len(data) / 1024 <= max_kb:
            return data, q
    return data, q


def hexc(rgb) -> str:
    return "%02X%02X%02X" % tuple(int(c) for c in rgb[:3])


def palette(img: Image.Image) -> dict:
    small = img.copy()
    small.thumbnail((160, 160))
    q = small.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: 16 * 3]
    counts = sorted(q.getcolors(), reverse=True)
    cols = []
    for n, idx in counts:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
        cols.append({"rgb": rgb, "n": n, "h": h, "l": l, "s": s})
    # accents: saturated, mid lightness, hues at least 0.06 apart; fill up with the rest
    cand = sorted([c for c in cols if c["s"] > 0.25 and 0.25 < c["l"] < 0.75], key=lambda c: -c["n"] * (0.5 + c["s"]))
    accents = []
    for c in cand + sorted(cols, key=lambda c: -c["s"]):
        if all(min(abs(c["h"] - a["h"]), 1 - abs(c["h"] - a["h"])) > 0.06 or c["s"] < 0.15 for a in accents) and c not in accents:
            accents.append(c)
        if len(accents) == 6:
            break
    while len(accents) < 6:
        accents.append(accents[len(accents) % max(1, len(accents))])
    darkest = min(cols, key=lambda c: c["l"])
    h, _, s = darkest["h"], darkest["l"], darkest["s"]
    navy = tuple(int(v * 255) for v in colorsys.hls_to_rgb(h, 0.13, min(s, 0.6)))
    out = {"dk1": "16181D", "lt1": "FFFFFF", "dk2": hexc(navy), "lt2": "F3F4F6"}
    for i, a in enumerate(accents, 1):
        out[f"accent{i}"] = hexc(a["rgb"])
    out["hlink"] = out["accent1"]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--css-out", help="file for the --hero-img line")
    ap.add_argument("--palette-out", help="palette JSON for extract_brand.py --palette")
    ap.add_argument("--max-width", type=int, default=1600)
    ap.add_argument("--max-kb", type=int, default=180)
    a = ap.parse_args(argv)
    img = Image.open(a.image)
    img = img.convert("RGB")
    if img.width > a.max_width:
        img = img.resize((a.max_width, round(img.height * a.max_width / img.width)), Image.LANCZOS)
    data, q = encode(img, a.max_kb)
    line = f"--hero-img:url(data:image/jpeg;base64,{data})"
    if a.css_out:
        with open(a.css_out, "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
    result = {"width": img.width, "height": img.height, "jpeg_quality": q, "data_uri_kb": round(len(data) / 1024)}
    if len(data) / 1024 > a.max_kb:
        result["warning"] = "still over --max-kb; lower --max-width"
    if a.palette_out:
        pal = palette(img)
        with open(a.palette_out, "w", encoding="utf-8") as fh:
            json.dump(pal, fh, indent=2)
        result["palette"] = pal
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
