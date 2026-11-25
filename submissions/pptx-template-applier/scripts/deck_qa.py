#!/usr/bin/env python3
"""Visual QA for a rebuilt or restyled deck: layout lint plus rendering.

  python deck_qa.py rebuilt.pptx --out-dir preview/ [--template brand.potx] [--source deck.pptx] [--json-out qa.json]
                    [--dpi 60] [--per-sheet 12] [--lint-only]

1. Lint (python-pptx, no rendering). Each finding names the slide:
   FAIL off_slide           a shape runs outside the slide
   FAIL overflow            text needs clearly more lines than its box holds
   FAIL leftover_text       template prompt or sample text left on a slide ("Click to add title",
                            "Lorem ipsum", or any sample slide text read from --template). Lines
                            that also appear in --source are content and never flagged.
   FAIL contrast            text below WCAG AA (4.5:1, or 3:1 for 18 pt+ or 14 pt+ bold) on a known
                            solid background
   WARN overflow_risk       text is close to filling its box
   WARN overlap             two shapes on a slide overlap, or a shape covers template decor
                            (bar, logo, footer text on the layout or master)
   WARN empty_placeholder   a placeholder with no text (shows "Click to add ..." when editing)
   WARN small_font          text under 12 pt (10 pt in tables)
   WARN no_notes            no speaker notes
2. Rendering: LibreOffice (soffice) to PDF, pdftoppm to one PNG per slide, Pillow contact sheets
   (contact-1.png, ...). Open every contact sheet: the lint cannot see everything.

When soffice or pdftoppm is missing the lint still runs and the result says the visual check must be
done by opening the deck. Exit 1 when the lint has a FAIL.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argument lists, no shell
import sys

from pptx.enum.shapes import MSO_SHAPE_TYPE

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apply_template import char_factor, default_sizes, text_height_pt  # noqa: E402
from deck_model import graphic_type, paragraphs_of  # noqa: E402
from pptx_common import (A, P, clr_map, contrast, emu_box, first_color_child, open_deck,  # noqa: E402
                         ph_type, picture_bounds, resolve_color, role_of, text_of, theme_colors, theme_fonts)

PROMPTS = re.compile(r"click to (add|edit)|lorem ipsum|dolor sit amet|your (text|title|subtitle|logo) here|"
                     r"(title|headline|subtitle|text) goes here|replace (this|with)|sample (text|headline|title)|"
                     r"insert (text|title|picture)|placeholder text|xx/xx|\[(name|date|title)\]", re.I)
EMU_PT = 12700


def deck_lines(path):
    out = set()
    if not path:
        return out
    prs = open_deck(path)
    for s in prs.slides:
        for sh in s.shapes:
            texts = [text_of(sh)]
            if getattr(sh, "has_table", False) and sh.has_table:
                texts += [c.text for r in sh.table.rows for c in r.cells]
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                texts += [text_of(x) for x in sh.shapes]
            for t in texts:
                for line in t.splitlines():
                    line = line.strip()
                    if len(line) >= 6:
                        out.add(line.lower())
    return out


def _bg_color(slide, colors, cmap):
    for part in (slide, slide.slide_layout, slide.slide_layout.slide_master):
        bg = part._element.find(f"{P}cSld/{P}bg")
        if bg is None:
            continue
        bgpr = bg.find(f"{P}bgPr")
        if bgpr is not None:
            sf = bgpr.find(f"{A}solidFill")
            if sf is not None:
                return resolve_color(first_color_child(sf), colors, cmap)
            return None  # gradient, picture or pattern: unknown
        ref = bg.find(f"{P}bgRef")
        if ref is not None:
            return resolve_color(first_color_child(ref), colors, cmap)
    return colors.get("lt1", "FFFFFF")


def _shape_fill(sh, colors, cmap):
    sppr = sh._element.find(f"{P}spPr")
    if sppr is None:
        return "inherit"
    if sppr.find(f"{A}noFill") is not None:
        return "inherit"
    sf = sppr.find(f"{A}solidFill")
    if sf is not None:
        return resolve_color(first_color_child(sf), colors, cmap)
    if sppr.find(f"{A}gradFill") is not None or sppr.find(f"{A}blipFill") is not None:
        return None
    style = sh._element.find(f"{P}style/{A}fillRef")
    if style is not None and style.get("idx", "0") != "0":
        return resolve_color(first_color_child(style), colors, cmap)
    return "inherit"


def _lst_color(lst, level, colors, cmap):
    if lst is None:
        return None
    sf = lst.find(f"{A}lvl{level + 1}pPr/{A}defRPr/{A}solidFill")
    return resolve_color(first_color_child(sf), colors, cmap) if sf is not None else None


def _text_color(sh, run_el, level, colors, cmap):
    rpr = run_el.find(f"{A}rPr")
    if rpr is not None and rpr.find(f"{A}solidFill") is not None:
        return resolve_color(first_color_child(rpr.find(f"{A}solidFill")), colors, cmap)
    lst = sh._element.find(f"{P}txBody/{A}lstStyle")
    c = _lst_color(lst, level, colors, cmap)
    if c:
        return c
    master = sh.part.slide_layout.slide_master if hasattr(sh.part, "slide_layout") else None
    if sh.is_placeholder:
        idx = sh.placeholder_format.idx
        role = role_of(ph_type(sh))
        layout = sh.part.slide_layout
        for lph in layout.placeholders:
            if lph.placeholder_format.idx == idx:
                c = _lst_color(lph._element.find(f"{P}txBody/{A}lstStyle"), level, colors, cmap)
                if c:
                    return c
                for mph in master.placeholders:
                    if ph_type(mph) == ph_type(lph):
                        c = _lst_color(mph._element.find(f"{P}txBody/{A}lstStyle"), level, colors, cmap)
                        if c:
                            return c
                break
        styles = master._element.find(f"{P}txStyles")
        if styles is not None:
            c = _lst_color(styles.find(f"{P}titleStyle" if role == "title" else f"{P}bodyStyle"), level, colors, cmap)
            if c:
                return c
    else:
        ref = sh._element.find(f"{P}style/{A}fontRef")
        if ref is not None and first_color_child(ref) is not None:
            return resolve_color(first_color_child(ref), colors, cmap)
        if master is not None:
            styles = master._element.find(f"{P}txStyles")
            if styles is not None:
                c = _lst_color(styles.find(f"{P}otherStyle"), level, colors, cmap)
                if c:
                    return c
    return resolve_color(_scheme("tx1"), colors, cmap)


def _scheme(val):
    from lxml import etree
    return etree.Element(f"{A}schemeClr", val=val)


def _decor_boxes(slide, W, H):
    out = []
    for part in (slide.slide_layout, slide.slide_layout.slide_master):
        for sh in part.shapes:
            if sh.is_placeholder:
                continue
            b = emu_box(sh)
            if b and b[2] * b[3] < 0.5 * W * H:
                out.append((sh.name, b))
    return out


def _inter(a, b):
    x = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    y = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return x * y


def lint(path, template=None, require_notes=True, source=None):
    prs = open_deck(path)
    W, H = prs.slide_width, prs.slide_height
    own = deck_lines(source)
    leftovers = deck_lines(template) - own  # text the source also has is content, not leftover
    out = []

    def add(level, i, check, detail):
        out.append({"level": level, "slide": i, "check": check, "detail": detail})

    for i, s in enumerate(prs.slides, 1):
        master = s.slide_layout.slide_master
        colors, cmap = theme_colors(prs, master), clr_map(prs, master)
        cf = char_factor(theme_fonts(prs, master))
        bg = _bg_color(s, colors, cmap)
        boxes = []
        for sh in s.shapes:
            b = picture_bounds(sh) if graphic_type(sh) == "picture" else emu_box(sh)
            if b:
                if b[0] < -9525 or b[1] < -9525 or b[0] + b[2] > W + 9525 or b[1] + b[3] > H + 9525:
                    add("FAIL", i, "off_slide", f"'{sh.name}' runs outside the slide")
                if b[2] * b[3] < 0.9 * W * H:
                    boxes.append((sh, b))
            texts = []
            if sh.has_text_frame:
                texts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                texts += [c.text for r in sh.table.rows for c in r.cells]
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                texts += [text_of(x) for x in sh.shapes]
            for t in texts:
                for line in t.splitlines():
                    ls = line.strip()
                    if ls and ls.lower() not in own and (PROMPTS.search(ls) or ls.lower() in leftovers):
                        add("FAIL", i, "leftover_text", f"'{sh.name}' holds template or prompt text: \"{ls[:60]}\"")
            if sh.is_placeholder and sh.has_text_frame and not sh.text_frame.text.strip():
                add("WARN", i, "empty_placeholder", f"'{sh.name}' is empty and shows a prompt when editing")
            if getattr(sh, "has_table", False) and sh.has_table:
                sizes = [r.font.size.pt for row in sh.table.rows for c in row.cells
                         for p in c.text_frame.paragraphs for r in p.runs if r.font.size]
                if sizes and min(sizes) < 10:
                    add("WARN", i, "small_font", f"table '{sh.name}' uses {min(sizes):g} pt")
            if sh.has_text_frame and sh.text_frame.text.strip() and b:
                _text_checks(sh, b, s, i, add, colors, cmap, bg, cf)
        # overlaps between slide shapes
        for a_i in range(len(boxes)):
            for b_i in range(a_i + 1, len(boxes)):
                (sa, ba), (sb, bb) = boxes[a_i], boxes[b_i]
                inter = _inter(ba, bb)
                small = min(ba[2] * ba[3], bb[2] * bb[3]) or 1
                if inter / small > 0.05:
                    add("WARN", i, "overlap", f"'{sa.name}' and '{sb.name}' overlap ({inter / small:.0%} of the smaller)")
        for name, db in _decor_boxes(s, W, H):
            for sh, b in boxes:
                inter = _inter(b, db)
                if inter and inter / ((db[2] * db[3]) or 1) > 0.1:
                    add("WARN", i, "overlap", f"'{sh.name}' covers template decor '{name}'")
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if require_notes and not notes:
            add("WARN", i, "no_notes", "no speaker notes")
    return len(prs.slides), out


def _text_checks(sh, b, s, i, add, colors, cmap, bg, cf):
    paras = paragraphs_of(sh.text_frame)
    explicit = [r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
    if sh.is_placeholder:
        role = role_of(ph_type(sh))
        base = default_sizes(sh, "title" if role == "title" else "text", s.slide_layout, s.slide_layout.slide_master)
    else:
        base = [18.0] * 5
    sizes = list(base)
    if explicit:
        sizes = [max(explicit)] + [min(explicit)] * 4 if len(set(explicit)) > 1 else [explicit[0]] * 5
    if explicit and min(explicit) < 12:
        add("WARN", i, "small_font", f"'{sh.name}' uses {min(explicit):g} pt")
    w = b[2] / EMU_PT - 14.4
    h = b[3] / EMU_PT - 7.2
    need = text_height_pt(paras, w, sizes, cf)
    if need > h * 1.25:
        add("FAIL", i, "overflow", f"'{sh.name}' needs about {need:.0f} pt of height, has {h:.0f}: shorten, shrink or split")
    elif need > h * 1.02:
        add("WARN", i, "overflow_risk", f"'{sh.name}' is close to full ({need:.0f} of {h:.0f} pt): check the render")
    fill = _shape_fill(sh, colors, cmap)
    back = bg if fill == "inherit" else fill
    if not back:
        return
    worst = None
    for lvl_i, p in enumerate(sh.text_frame.paragraphs):
        for r in p.runs:
            if not r.text.strip():
                continue
            fg = _text_color(sh, r._r, p.level, colors, cmap)
            if not fg:
                continue
            size = r.font.size.pt if r.font.size else sizes[min(p.level, 4)]
            large = size >= 18 or (size >= 14 and bool(r.font.bold))
            need_ratio = 3.0 if large else 4.5
            ratio = contrast(fg, back)
            if ratio < need_ratio and (worst is None or ratio < worst[0]):
                worst = (ratio, fg, need_ratio)
    if worst:
        add("FAIL", i, "contrast", f"'{sh.name}' text #{worst[1]} on #{back} is {worst[0]}:1, needs {worst[2]}:1")


def render(path, out_dir, dpi, per_sheet):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        return None, "soffice or pdftoppm not found: lint only. Open the deck and check each slide by eye"
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".pdf")
    if os.path.exists(pdf):
        os.remove(pdf)
    for old in glob.glob(os.path.join(out_dir, "slide-*.png")) + glob.glob(os.path.join(out_dir, "contact-*.png")):
        os.remove(old)
    argv = [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, path]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=300)  # nosec B603 - fixed argv, no shell
    if r.returncode != 0 or not os.path.exists(pdf):
        return None, f"PDF conversion failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[:300]}"
    argv = [pdftoppm, "-png", "-r", str(dpi), pdf, os.path.join(out_dir, "slide")]
    subprocess.run(argv, check=True, timeout=300)  # nosec B603 - fixed argv, no shell
    pngs = sorted(glob.glob(os.path.join(out_dir, "slide-*.png")))
    sheets = []
    try:
        from PIL import Image, ImageDraw
        for k in range(0, len(pngs), per_sheet):
            imgs = [Image.open(p) for p in pngs[k:k + per_sheet]]
            w, h = imgs[0].size
            cols = 3
            rows = -(-len(imgs) // cols)
            sheet = Image.new("RGB", (cols * (w + 12) + 12, rows * (h + 30) + 12), (200, 200, 200))
            d = ImageDraw.Draw(sheet)
            for j, im in enumerate(imgs):
                x, y = 12 + (j % cols) * (w + 12), 12 + (j // cols) * (h + 30)
                sheet.paste(im, (x, y + 20))
                d.text((x, y + 4), f"Slide {k + j + 1}", fill="black")
            sp = os.path.join(out_dir, f"contact-{k // per_sheet + 1}.png")
            sheet.save(sp)
            sheets.append(sp)
    except ImportError:
        return {"pdf": pdf, "slides": pngs, "contact_sheets": []}, "Pillow missing: open the slide PNGs one by one"
    return {"pdf": pdf, "slides": pngs, "contact_sheets": sheets}, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out-dir", default="preview")
    ap.add_argument("--template", help="template whose sample slide text counts as leftover text")
    ap.add_argument("--source", help="original deck: its own text never counts as leftover text")
    ap.add_argument("--json-out")
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--per-sheet", type=int, default=12)
    ap.add_argument("--lint-only", action="store_true")
    ap.add_argument("--no-notes-ok", action="store_true", help="do not warn on slides without notes")
    a = ap.parse_args(argv)
    n, findings = lint(a.deck, a.template, not a.no_notes_ok, a.source)
    result = {"deck": a.deck, "slides": n, "lint": findings}
    if a.lint_only:
        result["render_note"] = "lint only (--lint-only): open the deck and check each slide by eye"
    else:
        rendered, err = render(a.deck, a.out_dir, a.dpi, a.per_sheet)
        result["render"] = rendered
        if err:
            result["render_note"] = err
    result["fails"] = sum(1 for f in findings if f["level"] == "FAIL")
    result["warnings"] = sum(1 for f in findings if f["level"] == "WARN")
    result["passed_lint"] = result["fails"] == 0
    js = json.dumps(result, indent=1)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            fh.write(js)
    for f in findings:
        print(f"{f['level']} slide {f['slide']} {f['check']}: {f['detail']}")
    print(f"slides: {n} | FAIL: {result['fails']} | WARN: {result['warnings']}")
    if result.get("render"):
        print("contact sheets: " + ", ".join(result["render"]["contact_sheets"]))
    if result.get("render_note"):
        print("NOTE: " + result["render_note"])
    return 1 if result["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
