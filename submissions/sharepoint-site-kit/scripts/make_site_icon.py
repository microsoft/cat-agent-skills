#!/usr/bin/env python3
"""Make a SharePoint site icon from the page palette (no stock logos, no generic symbols).

Draws the page's hero motif on the deep band color: soft glowing orbs (default),
concentric arcs, or a dot grid, in the theme accent colors, with optional initials.
All content stays inside the central circle so SharePoint's round icon crop does not
cut it. The motifs are generic on purpose: never imitate a product logo.

Writes <out>-512.png and <out>-256.png.

Usage
  python make_site_icon.py --brand brand.json --out site-icon [--initials CA] [--motif orbs|arcs|grid]
  python make_site_icon.py --navy "#101A2E" --colors "#2563EB" "#0D9488" "#7C3AED" --out site-icon

Setting the icon is a manual step for the user:
  Settings (gear) > Change the look > Header > Site logo > Change
Requires Pillow.
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow")


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def glow(size, center, radius, color, alpha, blur):
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = center
    ImageDraw.Draw(layer).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(blur))


def make(size: int, navy, colors, initials: str | None, motif: str = "orbs"):
    img = Image.new("RGBA", (size, size), navy + (255,))
    c = colors + [colors[-1]] * (3 - len(colors))
    if motif == "arcs":
        d = ImageDraw.Draw(img)
        cx, cy = int(size * 0.78), int(size * 0.22)
        for i, r in enumerate(range(int(size * 0.12), int(size * 0.9), int(size * 0.07))):
            a = max(40, 200 - i * 18)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c[0] + (a,), width=max(2, size // 128))
        img = Image.alpha_composite(img, glow(size, (int(size * 0.3), int(size * 0.75)), int(size * 0.2), c[1], 200, size // 10))
    elif motif == "grid":
        d = ImageDraw.Draw(img)
        step = size // 14
        for y in range(step // 2, size, step):
            for x in range(step // 2, size, step):
                a = int(60 + 160 * x / size)
                r = max(2, size // 150)
                d.ellipse((x - r, y - r, x + r, y + r), fill=c[0] + (a,))
        img = Image.alpha_composite(img, glow(size, (int(size * 0.7), int(size * 0.3)), int(size * 0.2), c[1], 210, size // 10))
    else:
        for center, rad, col, alpha in (((0.64, 0.34), 0.24, c[0], 235), ((0.36, 0.66), 0.2, c[1], 225), ((0.6, 0.7), 0.12, c[2], 200)):
            img = Image.alpha_composite(img, glow(size, (int(center[0] * size), int(center[1] * size)), int(rad * size), col, alpha, size // 12))
    if initials:
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.26))
        except OSError:
            font = ImageFont.load_default()
        box = d.textbbox((0, 0), initials, font=font)
        w, h = box[2] - box[0], box[3] - box[1]
        d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1]), initials, font=font, fill=(255, 255, 255, 255))
    circle = Image.new("L", (size, size), 0)
    ImageDraw.Draw(circle).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), navy + (255,))
    out.paste(img, (0, 0), circle.filter(ImageFilter.GaussianBlur(0.5)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand", help="brand JSON from extract_brand.py")
    ap.add_argument("--navy")
    ap.add_argument("--colors", nargs="+")
    ap.add_argument("--initials")
    ap.add_argument("--motif", choices=["orbs", "arcs", "grid"], default="orbs")
    ap.add_argument("--out", default="site-icon")
    a = ap.parse_args(argv)
    if a.brand:
        with open(a.brand, encoding="utf-8") as fh:
            t = json.load(fh)["tokens_light"]
        navy, colors = t["--navy"], [t["--accent"], t["--accent2"], t["--accent3"]]
    else:
        if not (a.navy and a.colors):
            ap.error("give --brand or --navy and --colors")
        navy, colors = a.navy, a.colors
    big = make(512, hex_rgb(navy), [hex_rgb(x) for x in colors], a.initials, a.motif)
    big.save(f"{a.out}-512.png")
    big.resize((256, 256), Image.LANCZOS).save(f"{a.out}-256.png")
    print(json.dumps({"written": [f"{a.out}-512.png", f"{a.out}-256.png"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
