#!/usr/bin/env python3
"""Render a deck to slide images for the visual check, plus a layout lint.

  python deck_preview.py deck.pptx --out-dir preview/ [--dpi 60] [--lint-only]

1. Layout lint (python-pptx, no rendering): shapes that run off the slide,
   empty placeholders, text boxes whose text likely overflows (a character
   estimate from box size and font size), fonts under 12 pt, and slides with
   no speaker notes. Each finding names the slide number.
2. Rendering: LibreOffice (soffice) converts the deck to PDF, pdftoppm
   writes one PNG per slide, and Pillow builds contact sheets of 12 slides
   (contact-1.png, contact-2.png, ...). Open the contact sheets and look at
   every slide: the lint cannot see overlaps, clipped text or poor contrast.

When soffice or pdftoppm is missing, the lint still runs and the script says
the visual check must be done by opening the deck. Exit 1 when the lint finds
an off-slide shape or likely overflow.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argument lists, no shell
import sys

from pptx import Presentation
from pptx.util import Emu, Pt


def lint(path):
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    out = []
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.left is None or sh.width is None:
                continue
            if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W + Emu(9525) or sh.top + sh.height > H + Emu(9525):
                out.append({"level": "FAIL", "slide": i, "check": "off_slide", "detail": f"'{sh.name}' runs off the slide"})
            if sh.is_placeholder and sh.has_text_frame and not sh.text_frame.text.strip():
                out.append({"level": "WARN", "slide": i, "check": "empty_placeholder", "detail": f"'{sh.name}' is empty"})
            if sh.has_text_frame and sh.text_frame.text.strip():
                sizes = [r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
                size = max(sizes) if sizes else 18.0
                if sizes and min(sizes) < 12:
                    out.append({"level": "WARN", "slide": i, "check": "small_font", "detail": f"'{sh.name}' uses {min(sizes):g} pt"})
                w_in, h_in = sh.width / 914400, sh.height / 914400
                chars_per_line = max(1, int(w_in * 72 / (size * 0.52)))
                lines_avail = max(1, int(h_in * 72 / (size * 1.25)))
                need = 0
                for p in sh.text_frame.paragraphs:
                    t = "".join(r.text for r in p.runs) or p.text
                    need += max(1, -(-len(t) // chars_per_line))
                if need > lines_avail * 1.1 and not sh.is_placeholder:
                    out.append({"level": "FAIL", "slide": i, "check": "overflow",
                                "detail": f"'{sh.name}' needs about {need} lines, fits {lines_avail}: shorten or split"})
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if not notes:
            out.append({"level": "WARN", "slide": i, "check": "no_notes", "detail": "no speaker notes"})
    return len(prs.slides), out


def render(path, out_dir, dpi):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        return None, "soffice or pdftoppm not found: open the deck and check each slide by eye"
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".pdf")
    if os.path.exists(pdf):
        os.remove(pdf)
    argv = [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, path]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=240)  # nosec B603 - fixed argv, no shell
    if r.returncode != 0 or not os.path.exists(pdf):
        return None, f"PDF conversion failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[:300]}"
    for old in glob.glob(os.path.join(out_dir, "slide-*.png")):
        os.remove(old)
    argv = [pdftoppm, "-png", "-r", str(dpi), pdf, os.path.join(out_dir, "slide")]
    subprocess.run(argv, check=True, timeout=240)  # nosec B603 - fixed argv, no shell
    pngs = sorted(glob.glob(os.path.join(out_dir, "slide-*.png")))
    sheets = []
    try:
        from PIL import Image, ImageDraw
        for k in range(0, len(pngs), 12):
            imgs = [Image.open(p) for p in pngs[k:k + 12]]
            w, h = imgs[0].size
            cols = 3
            rows = -(-len(imgs) // cols)
            sheet = Image.new("RGB", (cols * (w + 10) + 10, rows * (h + 30) + 10), "white")
            d = ImageDraw.Draw(sheet)
            for j, im in enumerate(imgs):
                x, y = 10 + (j % cols) * (w + 10), 10 + (j // cols) * (h + 30)
                sheet.paste(im, (x, y + 20))
                d.text((x, y + 4), f"Slide {k + j + 1}", fill="black")
            sp = os.path.join(out_dir, f"contact-{k // 12 + 1}.png")
            sheet.save(sp)
            sheets.append(sp)
    except ImportError:
        pass
    return {"pdf": pdf, "slides": pngs, "contact_sheets": sheets}, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out-dir", default="preview")
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--lint-only", action="store_true")
    a = ap.parse_args(argv)
    n, findings = lint(a.deck)
    result = {"deck": a.deck, "slides": n, "lint": findings}
    if not a.lint_only:
        rendered, err = render(a.deck, a.out_dir, a.dpi)
        result["render"] = rendered
        if err:
            result["render_note"] = err
    fails = [f for f in findings if f["level"] == "FAIL"]
    result["passed_lint"] = not fails
    print(json.dumps(result, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
