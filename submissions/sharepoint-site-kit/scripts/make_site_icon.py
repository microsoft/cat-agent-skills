#!/usr/bin/env python3
"""Make a SharePoint site icon from the page palette (no stock logos, no generic symbols).

Draws the hero motif of the page (deep band color plus two skewed rounded shapes
in the accent gradient colors) with optional initials, keeping all content inside
the central circle so SharePoint's round icon crop does not cut it.

Writes <out>-512.png and <out>-256.png.

Usage
  python make_site_icon.py --brand brand.json --out site-icon [--initials CA]
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


def skew_shape(size, box, skew, radius, fill):
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill)
    return layer.transform(layer.size, Image.AFFINE, (1, skew, -skew * size / 2, 0, 1, 0), resample=Image.BICUBIC)


def gradient_fill(size, c1, c2):
    g = Image.new("RGBA", (size, size))
    px = g.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)) + (255,)
    return g


def make(size: int, navy, colors, initials: str | None):
    img = Image.new("RGBA", (size, size), navy + (255,))
    c = colors + [colors[-1]] * (3 - len(colors))
    # Shapes stay inside a circle of about 75% diameter, so the round icon crop never cuts them.
    for box, c1, c2, alpha in (
        ((0.44, 0.22, 0.72, 0.56), c[0], c[1], 235),
        ((0.28, 0.44, 0.56, 0.78), c[1], c[2], 220),
    ):
        b = tuple(int(v * size) for v in box)
        mask = skew_shape(size, b, 0.2, int(size * 0.09), (255, 255, 255, alpha)).split()[3]
        img.paste(gradient_fill(size, c1, c2), (0, 0), mask)
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
    big = make(512, hex_rgb(navy), [hex_rgb(x) for x in colors], a.initials)
    big.save(f"{a.out}-512.png")
    big.resize((256, 256), Image.LANCZOS).save(f"{a.out}-256.png")
    print(json.dumps({"written": [f"{a.out}-512.png", f"{a.out}-256.png"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
