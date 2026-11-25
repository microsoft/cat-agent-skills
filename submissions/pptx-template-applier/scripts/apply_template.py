#!/usr/bin/env python3
"""Rebuild a source deck on a brand template, following mapping.json.

  python apply_template.py --mapping mapping.json --out rebuilt.pptx --report-out build.json \
      [--split-overflow all|3,9] [--title-floor 24] [--body-floor 14] [--table-floor 10]

What it does, per source slide in order:
  1. Adds a slide on the mapped template layout (the template's own sample
     slides are removed; masters and layouts stay).
  2. Fills the title, subtitle and body placeholders. Bullet levels, bold,
     italic, underline and links are kept; hard-coded fonts, sizes and colors
     are dropped so the template's theme applies.
  3. Rebuilds tables (themed table style, merges kept) and category charts
     (data, legend and title kept; series recolored to theme accents 1 to 6).
  4. Places pictures (no cropping: fitted inside the area) and other shapes.
     Shapes and groups are copied with their pictures and links; hard-coded
     colors are mapped to theme slots and hard-coded font faces dropped.
     Free content keeps its relative layout, scaled into the template's
     content area.
  5. Copies the speaker notes.
  6. Fits text: shrinks placeholder text in steps down to the floor sizes.
     A slide that still overflows is split into continuation slides only when
     --split-overflow names it (ask the user first); otherwise it is reported.
  7. Removes unused empty placeholders so no "Click to add" prompt remains.

Never writes the source or template: --out must be a new path.
The report lists every fix, warning and overflow for the chat summary.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import math
import os
import sys

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.util import Emu, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck_model import para_text, paragraphs_of, read_slide  # noqa: E402
from pptx_common import (A, P, R, R_NS, emu_box, open_deck, ph_type, picture_bounds, role_of,  # noqa: E402
                         theme_colors, theme_fonts)
from restyle import build_color_map, remap_colors, strip_fonts  # noqa: E402

EMU_PT = 12700
EMU_IN = 914400
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
ACCENT_THEME = [MSO_THEME_COLOR.ACCENT_1, MSO_THEME_COLOR.ACCENT_2, MSO_THEME_COLOR.ACCENT_3,
                MSO_THEME_COLOR.ACCENT_4, MSO_THEME_COLOR.ACCENT_5, MSO_THEME_COLOR.ACCENT_6]
WIDE_FONTS = ("verdana", "tahoma", "segoe", "trebuchet", "century gothic", "arial black", "lucida")
DEFAULT_SIZES = {"title": [44], "subtitle": [24, 20, 18], "text": [28, 24, 20, 20, 20], "content": [28, 24, 20, 20, 20]}


class Report:
    def __init__(self):
        self.fixes, self.warnings, self.overflow, self.slides = [], [], [], []

    def fix(self, slide, msg):
        self.fixes.append({"slide": slide, "detail": msg})

    def warn(self, slide, msg):
        self.warnings.append({"slide": slide, "detail": msg})


# ---------------- template preparation ----------------

def remove_sample_slides(prs):
    lst = prs.slides._sldIdLst
    n = len(lst)
    for sld in list(lst):
        prs.part.drop_rel(sld.get(f"{R}id"))
        lst.remove(sld)
    return n


# ---------------- text ----------------

def write_paragraphs(tf, paragraphs, sizes=None):
    """Write paragraphs into a text frame. sizes: list of pt per level, or None for theme sizes."""
    from lxml import etree
    body = tf._txBody
    for p in list(body.findall(f"{A}p")):
        body.remove(p)
    for para in paragraphs or [{"level": 0, "runs": []}]:
        p = tf.add_paragraph() if body.findall(f"{A}p") else _first_p(tf)
        p.level = min(max(para.get("level", 0), 0), 8)
        bullet = para.get("bullet")
        if bullet is not None:
            etree.SubElement(p._p.get_or_add_pPr(), f"{A}{bullet['tag']}", bullet["attrs"])
        for run in para["runs"]:
            if run.get("kind") == "break":
                p.add_line_break()
                continue
            r = p.add_run()
            r.text = run["text"]
            if run.get("bold") is not None:
                r.font.bold = run["bold"]
            if run.get("italic") is not None:
                r.font.italic = run["italic"]
            if run.get("underline"):
                r.font.underline = True
            if run.get("url"):
                r.hyperlink.address = run["url"]
            if sizes:
                r.font.size = Pt(sizes[min(p.level, len(sizes) - 1)])


def _first_p(tf):
    body = tf._txBody
    from pptx.text.text import _Paragraph
    p = body.add_p()
    return _Paragraph(p, tf)


def _lvl_size(el, level):
    if el is None:
        return None
    lvl = el.find(f"{A}lvl{level + 1}pPr/{A}defRPr")
    if lvl is not None and lvl.get("sz"):
        return int(lvl.get("sz")) / 100
    return None


def default_sizes(slide_ph, role, layout, master):
    """Theme font size per level for a placeholder: layout list style, master placeholder, master text styles."""
    idx = slide_ph.placeholder_format.idx
    lay_ph = None
    for ph in layout.placeholders:
        if ph.placeholder_format.idx == idx:
            lay_ph = ph
            break
    sources = []
    if lay_ph is not None:
        sources.append(lay_ph._element.find(f"{P}txBody/{A}lstStyle"))
        t = ph_type(lay_ph)
        for mph in master.placeholders:
            if ph_type(mph) == t or (role == "title" and role_of(ph_type(mph)) == "title"):
                sources.append(mph._element.find(f"{P}txBody/{A}lstStyle"))
                break
    styles = master._element.find(f"{P}txStyles")
    if styles is not None:
        sources.append(styles.find(f"{P}titleStyle" if role == "title" else f"{P}bodyStyle"))
    out = []
    base = DEFAULT_SIZES.get(role, DEFAULT_SIZES["text"])
    for level in range(5):
        size = None
        for s in sources:
            size = _lvl_size(s, level)
            if size:
                break
        out.append(size or base[min(level, len(base) - 1)])
    return out


def char_factor(fonts):
    f = (fonts.get("minor") or "").lower()
    return 0.55 if any(w in f for w in WIDE_FONTS) else 0.5


def text_height_pt(paragraphs, width_pt, sizes, cf):
    h = 0.0
    for p in paragraphs:
        lvl = min(p.get("level", 0), len(sizes) - 1)
        size = sizes[lvl]
        indent = 27 * p.get("level", 0) + (18 if p.get("level", 0) or len(paragraphs) > 1 else 0)
        cpl = max(1, int((width_pt - indent) / (size * cf)))
        lines = sum(max(1, math.ceil(len(line) / cpl)) for line in para_text(p).replace("\v", "\n").split("\n"))
        h += lines * size * 1.2 + size * 0.15
    return h


def box_inner_pt(box):
    w = box[2] / EMU_PT - 14.4
    h = box[3] / EMU_PT - 7.2
    return w, h


def fit_sizes(paragraphs, box, base, floor, cf):
    """Return (sizes, fits). Shrinks in 2 pt steps of the first level, keeping level ratios."""
    w, h = box_inner_pt(box)
    if text_height_pt(paragraphs, w, base, cf) <= h:
        return None, True
    top = base[0]
    while top - 2 >= floor:
        top -= 2
        sizes = [max(floor, round(s * top / base[0])) for s in base]
        if text_height_pt(paragraphs, w, sizes, cf) <= h:
            return sizes, True
    sizes = [max(floor, round(s * floor / base[0])) for s in base]
    return sizes, text_height_pt(paragraphs, w, sizes, cf) <= h


def split_paragraphs(paragraphs, box, sizes, cf):
    """Split at top-level bullets into chunks that fit at the given sizes."""
    w, h = box_inner_pt(box)
    groups, cur = [], []
    for p in paragraphs:
        if p.get("level", 0) == 0 and cur:
            groups.append(cur)
            cur = []
        cur.append(p)
    if cur:
        groups.append(cur)
    chunks, chunk = [], []
    for g in groups:
        if chunk and text_height_pt(chunk + g, w, sizes, cf) > h:
            chunks.append(chunk)
            chunk = []
        chunk = chunk + g
    if chunk:
        chunks.append(chunk)
    return chunks


# ---------------- geometry ----------------

def union(boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    l = min(b[0] for b in boxes)
    t = min(b[1] for b in boxes)
    r = max(b[0] + b[2] for b in boxes)
    btm = max(b[1] + b[3] for b in boxes)
    return (l, t, r - l, btm - t)


def make_transform(src_union, area, max_scale=1.4):
    if not src_union:
        return lambda b: b, 1.0
    s = min(area[2] / max(src_union[2], 1), area[3] / max(src_union[3], 1), max_scale)
    ox = area[0] + (area[2] - src_union[2] * s) / 2
    oy = area[1]

    def tf(b):
        return (int(ox + (b[0] - src_union[0]) * s), int(oy + (b[1] - src_union[1]) * s), int(b[2] * s), int(b[3] * s))
    return tf, s


def fit_inside(aspect, area):
    """Largest box with the given width/height ratio centered in area."""
    w, h = area[2], area[3]
    if w / h > aspect:
        nw = int(h * aspect)
        return (area[0] + (w - nw) // 2, area[1], nw, h)
    nh = int(w / aspect)
    return (area[0], area[1] + (h - nh) // 2, w, nh)


def content_area(slide, W, H, title_box=None):
    """Area below the title (placeholder or text box) of the new slide, or the whole slide with margins."""
    margin = int(0.5 * EMU_IN)
    tb = title_box
    if tb is None:
        for ph in slide.placeholders:
            if role_of(ph_type(ph)) == "title" and ph.top is not None:
                tb = emu_box(ph)
                break
    bottom = H - int(0.65 * EMU_IN)
    if tb is not None and tb[1] > H * 0.5:
        # title sits low on the layout (caption style): use the space above it
        return (max(tb[0], margin), margin, min(tb[2], W - 2 * margin), max(tb[1] - margin - int(0.15 * EMU_IN), int(EMU_IN)))
    if tb is not None:
        top = tb[1] + tb[3] + int(0.15 * EMU_IN)
        left, width = max(tb[0], margin), min(tb[2], W - 2 * margin)
    else:
        top, left, width = int(0.4 * EMU_IN), margin, W - 2 * margin
    return (left, top, width, max(bottom - top, int(EMU_IN)))


# ---------------- copying shapes ----------------

def copy_rels(el, src_part, dst_part, rep, slide_no):
    """Re-point r:* references of a copied element. Returns False when a part type cannot be carried over."""
    ok = True
    for node in el.iter():
        for attr, val in list(node.attrib.items()):
            if not attr.startswith("{%s}" % R_NS):
                continue
            rel = src_part.rels.get(val) if hasattr(src_part.rels, "get") else src_part.rels[val]
            if rel is None:
                continue
            if rel.is_external:
                node.set(attr, dst_part.relate_to(rel.target_ref, rel.reltype, is_external=True))
            elif rel.reltype.endswith("/image"):
                _, rid = dst_part.get_or_add_image_part(io.BytesIO(rel.target_part.blob))
                node.set(attr, rid)
            elif rel.reltype.endswith("/hyperlink") or rel.reltype.endswith("/slide"):
                node.attrib.pop(attr)  # internal slide jumps are dropped: slide numbers change
            else:
                ok = False
    return ok


def set_xfrm(el, box):
    xfrm = None
    for path in (f"{P}spPr/{A}xfrm", f"{P}grpSpPr/{A}xfrm", f"{P}xfrm"):
        xfrm = el.find(path)
        if xfrm is not None:
            break
    if xfrm is None:
        return
    off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
    if off is not None:
        off.set("x", str(box[0]))
        off.set("y", str(box[1]))
    if ext is not None:
        ext.set("cx", str(box[2]))
        ext.set("cy", str(box[3]))


def scale_font_sizes(el, s, floor=10):
    if abs(s - 1) < 0.05:
        return
    for tag in ("rPr", "defRPr", "endParaRPr"):
        for node in el.iter(f"{A}{tag}"):
            if node.get("sz"):
                node.set("sz", str(max(floor * 100, int(int(node.get("sz")) * s / 100) * 100)))


def copy_shape(sh, src_slide, dst_slide, box, scale, cmap, rep, n, shape_ids):
    el = copy.deepcopy(sh._element)
    if not copy_rels(el, src_slide.part, dst_slide.part, rep, n):
        rep.warn(n, f"'{sh.name}' holds an embedded object or diagram that cannot be carried over: re-add it by hand")
        return None
    set_xfrm(el, box)
    remap_colors(el, cmap)
    strip_fonts(el)
    scale_font_sizes(el, scale)
    next_id = _next_id(dst_slide)
    for nv in el.iter(f"{P}cNvPr"):
        shape_ids[nv.get("id")] = str(next_id)
        nv.set("id", str(next_id))
        next_id += 1
    dst_slide.shapes._spTree.append(el)
    return el


def _next_id(slide):
    ids = [int(x) for x in slide.shapes._spTree.xpath("//p:cNvPr/@id") if str(x).isdigit()]
    return max(ids + [1]) + 1


def remap_connections(slide, shape_ids, rep, n):
    """Resolve after all shapes are placed, including connectors copied before their targets."""
    for tag in ("stCxn", "endCxn"):
        for node in list(slide._element.iter(f"{A}{tag}")):
            target = shape_ids.get(node.get("id"))
            if target is not None:
                node.set("id", target)
            else:
                node.getparent().remove(node)
                rep.warn(n, "connector endpoint detached because its source target was not carried over")


def add_picture(sh, dst_slide, area):
    blob = sh.image.blob
    width, height = picture_bounds(sh)[2:]
    scale = min(area[2] / max(width, 1), area[3] / max(height, 1))
    w, h = max(1, int(sh.width * scale)), max(1, int(sh.height * scale))
    box = (int(area[0] + (area[2] - w) / 2), int(area[1] + (area[3] - h) / 2), w, h)
    pic = dst_slide.shapes.add_picture(io.BytesIO(blob), *box)
    for side in ("crop_left", "crop_right", "crop_top", "crop_bottom"):
        try:
            setattr(pic, side, getattr(sh, side))
        except (AttributeError, ValueError):
            pass
    pic.name = sh.name
    pic.rotation = sh.rotation
    source_xfrm = sh._element.find(f"{P}spPr/{A}xfrm")
    if source_xfrm is not None:
        for attr in ("flipH", "flipV"):
            if source_xfrm.get(attr) is not None:
                pic._element.spPr.xfrm.set(attr, source_xfrm.get(attr))
    copy_picture_links(sh, pic, dst_slide)
    return pic


def copy_picture_links(source, target, dst_slide):
    source_nv = source._element.find(f"{P}nvPicPr/{P}cNvPr")
    target_nv = target._element.find(f"{P}nvPicPr/{P}cNvPr")
    for tag in ("hlinkClick", "hlinkHover"):
        link = source_nv.find(f"{A}{tag}")
        if link is None:
            continue
        rel = source.part.rels.get(link.get(f"{R}id"))
        if rel is None or not rel.is_external:
            continue  # Internal slide jumps cannot survive slide renumbering.
        new = copy.deepcopy(link)
        new.set(f"{R}id", dst_slide.part.relate_to(rel.target_ref, rel.reltype, is_external=True))
        target_nv.append(new)


def rebuild_table(sh, dst_slide, area, floor, rep, n, cf):
    src = sh.table
    rows, cols = len(src.rows), len(src.columns)
    widths = [c.width for c in src.columns]
    total = sum(widths) or 1
    def row_heights(size):
        heights = [int((size * 1.2 + 10) * EMU_PT)] * rows
        for r in range(rows):
            for c in range(cols):
                cell = src.cell(r, c)
                if cell.is_spanned:
                    continue
                span_w = sum(widths[c:c + cell.span_width]) / total * area[2] / EMU_PT - 14
                cpl = max(1, int(span_w / (size * cf)))
                lines = sum(max(1, math.ceil(len(line) / cpl)) for line in
                            cell.text.replace("\v", "\n").split("\n"))
                need = math.ceil((lines * size * 1.2 + 10) * EMU_PT)
                end = r + cell.span_height
                deficit = need - sum(heights[r:end])
                if deficit > 0:
                    extra = math.ceil(deficit / cell.span_height)
                    for row in range(r, end):
                        heights[row] += extra
        return heights

    size = 18
    heights = row_heights(size)
    while size > floor:
        if sum(heights) <= area[3]:
            break
        size -= 1
        heights = row_heights(size)
    gf = dst_slide.shapes.add_table(rows, cols, area[0], area[1], area[2], sum(heights))
    gf.name = sh.name
    t = gf.table
    for c in range(cols):
        t.columns[c].width = Emu(int(widths[c] / total * area[2]))
    for r, height in enumerate(heights):
        t.rows[r].height = Emu(height)
    for flag in ("first_row", "first_col", "last_row", "last_col", "horz_banding", "vert_banding"):
        try:
            setattr(t, flag, getattr(src, flag))
        except AttributeError:
            pass
    for r in range(rows):
        for c in range(cols):
            scell = src.cell(r, c)
            if scell.is_merge_origin:
                t.cell(r, c).merge(t.cell(r + scell.span_height - 1, c + scell.span_width - 1))
    for r in range(rows):
        for c in range(cols):
            scell = src.cell(r, c)
            if scell.is_spanned:
                continue
            write_paragraphs(t.cell(r, c).text_frame, paragraphs_of(scell.text_frame) or [{"level": 0, "runs": []}], [size])
    if sum(heights) > area[3]:
        rep.overflow.append({"slide": n, "shape": sh.name, "detail": "table is taller than the content area at the floor size"})
    rep.fix(n, f"table '{sh.name}' rebuilt with the template's themed table style at {size} pt")
    return gf


CHART_UNSUPPORTED = {XL_CHART_TYPE.XY_SCATTER, XL_CHART_TYPE.XY_SCATTER_LINES, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,
                     XL_CHART_TYPE.XY_SCATTER_SMOOTH, XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS,
                     XL_CHART_TYPE.BUBBLE, XL_CHART_TYPE.BUBBLE_THREE_D_EFFECT}
PIE_TYPES = {XL_CHART_TYPE.PIE, XL_CHART_TYPE.PIE_EXPLODED, XL_CHART_TYPE.DOUGHNUT,
             XL_CHART_TYPE.DOUGHNUT_EXPLODED, XL_CHART_TYPE.THREE_D_PIE}
LINE_TYPES = {XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS, XL_CHART_TYPE.LINE_STACKED,
              XL_CHART_TYPE.LINE_MARKERS_STACKED, XL_CHART_TYPE.RADAR, XL_CHART_TYPE.RADAR_MARKERS}


def copy_chart_text(root, src, dst, rep, n, context):
    """Freeze workbook-linked text before carrying chart text into a new workbook."""
    from lxml import etree
    for ref in list(root.iter(f"{C}strRef")):
        cached = ref.findall(f"{C}strCache/{C}pt/{C}v")
        parent = ref.getparent()
        if cached:
            rich = etree.Element(f"{C}rich")
            etree.SubElement(rich, f"{A}bodyPr")
            etree.SubElement(rich, f"{A}lstStyle")
            p = etree.SubElement(rich, f"{A}p")
            r = etree.SubElement(p, f"{A}r")
            etree.SubElement(r, f"{A}t").text = "".join(v.text or "" for v in cached)
            parent.replace(ref, rich)
            rep.warn(n, f"{context} workbook-linked text frozen to its cached displayed text")
        else:
            parent.getparent().remove(parent)
            rep.warn(n, f"{context} has workbook-linked text without cached text: re-add it by hand")
    if not copy_rels(root, src.part, dst.part, rep, n):
        rep.warn(n, f"{context} has an unsupported embedded part: re-add it by hand")
        return False
    return True


def copy_chart_labels(src, dst, rep, n, name):
    """Keep plot/series label XML, including per-point text and number formats."""
    pairs = [(src.plots[0]._element, dst.plots[0]._element)]
    pairs += [(s._element, d._element) for s, d in zip(src.series, dst.series)]
    for source, target in pairs:
        labels = source.find(f"{C}dLbls")
        if labels is None:
            continue
        labels = copy.deepcopy(labels)
        if labels.find(f".//{C}extLst") is not None:
            rep.warn(n, f"chart '{name}' uses extended label settings: verify them by hand; workbook-linked extensions may not carry over")
        if not copy_chart_text(labels, src, dst, rep, n, f"chart '{name}' label"):
            continue
        existing = target.find(f"{C}dLbls")
        if existing is not None:
            target.remove(existing)
        # python-pptx knows the different schema order for plot- and series-level labels.
        target._insert_dLbls(labels)


def copy_chart_axes(src, dst, rep, n, name):
    source_area = src._chartSpace.find(f"{C}chart/{C}plotArea")
    target_area = dst._chartSpace.find(f"{C}chart/{C}plotArea")
    for tag in ("catAx", "dateAx", "valAx", "serAx"):
        sources = source_area.findall(f"{C}{tag}")
        targets = target_area.findall(f"{C}{tag}")
        for i, source in enumerate(sources):
            if i >= len(targets):
                rep.warn(n, f"chart '{name}' {tag} settings cannot be carried over: verify its axis title and number format")
                continue
            target = targets[i]
            for setting in ("title", "numFmt"):
                node = source.find(f"{C}{setting}")
                if node is None:
                    continue
                insert = getattr(target, f"_insert_{setting}", None)
                if insert is None:
                    rep.warn(n, f"chart '{name}' {tag} {setting} is not supported: re-add it by hand")
                    continue
                node = copy.deepcopy(node)
                if setting == "title" and not copy_chart_text(node, src, dst, rep, n, f"chart '{name}' axis title"):
                    continue
                if setting == "title" and node.find(f"{C}tx") is None:
                    continue
                existing = target.find(f"{C}{setting}")
                if existing is not None:
                    target.remove(existing)
                insert(node)


def rebuild_chart(sh, dst_slide, area, rep, n):
    src = sh.chart
    try:
        ctype = src.chart_type
    except (NotImplementedError, KeyError, ValueError):
        ctype = None
    if ctype is None or ctype in CHART_UNSUPPORTED or len(src.plots) != 1:
        return None
    plot = src.plots[0]
    cd = CategoryChartData()
    cd.categories = [str(c) for c in plot.categories]
    for s in plot.series:
        fmt = s._element.find(f"{C}val/{C}numRef/{C}numCache/{C}formatCode")
        if fmt is None:
            fmt = s._element.find(f"{C}val/{C}numLit/{C}formatCode")
        cd.add_series(s.name, [v if v is not None else None for v in s.values],
                      number_format=fmt.text if fmt is not None else None)
    gf = dst_slide.shapes.add_chart(ctype, *area, cd)
    gf.name = sh.name
    ch = gf.chart
    ch.has_legend = src.has_legend
    if src.has_legend:
        ch.legend.position = src.legend.position
        ch.legend.include_in_layout = False
    if src.has_title and src.chart_title.has_text_frame and src.chart_title.text_frame.text.strip():
        ch.has_title = True
        ch.chart_title.text_frame.text = src.chart_title.text_frame.text
    else:
        ch.has_title = False
    copy_chart_labels(src, ch, rep, n, sh.name)
    copy_chart_axes(src, ch, rep, n, sh.name)
    if ctype in PIE_TYPES:
        for j, pt in enumerate(ch.plots[0].series[0].points):
            pt.format.fill.solid()
            pt.format.fill.fore_color.theme_color = ACCENT_THEME[j % 6]
    else:
        for i, s in enumerate(ch.plots[0].series):
            if ctype in LINE_TYPES:
                s.format.line.color.theme_color = ACCENT_THEME[i % 6]
            else:
                s.format.fill.solid()
                s.format.fill.fore_color.theme_color = ACCENT_THEME[i % 6]
    rep.fix(n, f"chart '{sh.name}' rebuilt from its data; series recolored to theme accents")
    return gf


def place_graphic(g, src_slide, dst_slide, box, scale, cmap, floor_table, rep, n, cf, shape_ids):
    sh, typ = g["shape"], g["type"]
    if typ == "table":
        return rebuild_table(sh, dst_slide, box, floor_table, rep, n, cf)
    if typ == "chart":
        out = rebuild_chart(sh, dst_slide, box, rep, n)
        if out is None:
            rep.warn(n, f"chart '{sh.name}' is a type this script does not rebuild (scatter, bubble or combo): "
                        "copied as a picture is not possible, re-insert it by hand from the source deck")
        return out
    if typ == "picture":
        return add_picture(sh, dst_slide, box)
    return copy_shape(sh, src_slide, dst_slide, box, scale, cmap, rep, n, shape_ids)


# ---------------- slide build ----------------

def placeholders_by_role(slide):
    out = {"title": [], "subtitle": [], "body": [], "picture": []}
    for ph in slide.placeholders:
        role = role_of(ph_type(ph))
        if role in ("text", "content"):
            out["body"].append(ph)
        elif role in out:
            out[role].append(ph)
    W = slide.part.package.presentation_part.presentation.slide_width
    out["body"].sort(key=lambda p: (round(p.left / (W / 4)), p.top))
    return out


def remove_shape(sh):
    sh._element.getparent().remove(sh._element)


def fill_text_ph(ph, paragraphs, role, layout, master, cf, floors, rep, n, label):
    base = default_sizes(ph, role, layout, master)
    floor = floors["title"] if role == "title" else floors["body"]
    sizes, fits = fit_sizes(paragraphs, emu_box(ph), base, floor, cf)
    write_paragraphs(ph.text_frame, paragraphs, sizes)
    if sizes:
        rep.fix(n, f"{label} text shrunk from {base[0]:g} to {sizes[0]:g} pt to fit")
    return fits, base, sizes


def build_slide(prs, m, entry, src_slide, cmap, cf, floors, split, rep, out_no):
    layout = prs.slide_masters[entry.get("target_master_index", 0)].slide_layouts[entry["target_layout_index"]]
    master = layout.slide_master
    W, H = prs.slide_width, prs.slide_height
    n = entry["slide"]
    slide = prs.slides.add_slide(layout)
    made = [slide]
    phs = placeholders_by_role(slide)
    texts = [dict(t) for t in m["texts"]]
    graphics = list(m["graphics"])
    pictures = list(m["pictures"])
    used = set()
    shape_ids = {}

    # comparison source onto a two-column target: merge each header into its column
    if m["kind"] == "comparison" and len(phs["body"]) == 2 and len(texts) == 4:
        merged = []
        for hdr, body in ((texts[0], texts[1]), (texts[2], texts[3])):
            hp = [dict(p, level=0, runs=[dict(r, bold=True) for r in p["runs"]]) for p in hdr["paragraphs"]]
            merged.append({"paragraphs": hp + body["paragraphs"], "box": body["box"], "role": "content"})
        texts = merged
        rep.fix(n, "comparison headers merged into the top of each column (no comparison layout)")

    # title
    title_text = m["title"]
    title_box = None
    if title_text:
        if phs["title"]:
            ph = phs["title"][0]
            fill_text_ph(ph, [{"level": 0, "runs": _title_runs(m)}], "title", layout, master, cf, floors, rep, n, "title")
            used.add(ph.shape_id)
        else:
            tb = slide.shapes.add_textbox(int(0.5 * EMU_IN), int(0.3 * EMU_IN), W - EMU_IN, int(1.0 * EMU_IN))
            write_paragraphs(tb.text_frame, [{"level": 0, "runs": _title_runs(m)}], [32])
            for r in tb.text_frame.paragraphs[0].runs:
                r.font.name = "+mj-lt"  # theme heading font
            tb.name = "Title (text box)"
            title_box = emu_box(tb)
            ph = tb
            rep.warn(n, "target layout has no title placeholder: title placed in a text box")
        if m.get("title_shape") is not None:
            shape_ids[str(m["title_shape"].shape_id)] = str(ph.shape_id)

    # subtitle
    if m["subtitle"]:
        target = phs["subtitle"][0] if phs["subtitle"] else next((p for p in phs["body"] if p.shape_id not in used), None)
        if target is not None:
            fill_text_ph(target, m["subtitle"], "subtitle", layout, master, cf, floors, rep, n, "subtitle")
            used.add(target.shape_id)
            if m.get("subtitle_shape") is not None:
                shape_ids[str(m["subtitle_shape"].shape_id)] = str(target.shape_id)
        else:
            texts.insert(0, {"paragraphs": m["subtitle"], "box": None, "role": "text",
                             "shape": m.get("subtitle_shape")})

    # one graphic and no body text: give it the content placeholder area
    free_bodies = [p for p in phs["body"] if p.shape_id not in used]
    if not texts and len(graphics) == 1 and free_bodies and graphics[0]["type"] in ("table", "chart", "picture"):
        ph = free_bodies[0]
        box = emu_box(ph)
        remove_shape(ph)
        used.add(ph.shape_id)
        placed = place_graphic(graphics[0], src_slide, slide, box, 1.0, cmap, floors["table"], rep, n, cf, shape_ids)
        if placed is not None:
            shape_ids[str(graphics[0]["shape"].shape_id)] = str(placed.shape_id)
        graphics = []

    # body text into body placeholders in reading order
    overflow_parts = []
    free_bodies = [p for p in phs["body"] if p.shape_id not in used]
    reserved_pictures = len([p for p in phs["picture"] if p.shape_id not in used])
    all_pictures = pictures + [g for g in graphics if g["type"] == "picture"]
    joint_graphics = [g for g in graphics if g["type"] != "picture"] + all_pictures[reserved_pictures:]
    joint_transform = None
    if texts and joint_graphics and all(t.get("box") for t in texts):
        area = union([emu_box(p) for p in free_bodies]) or content_area(slide, W, H, title_box)
        joint_transform = make_transform(union([it["box"] for it in texts + joint_graphics if it.get("box")]), area)
        rep.fix(n, "body text and extra graphics laid out together to preserve their relative positions")
    leftovers = []
    for t in texts:
        if free_bodies:
            ph = free_bodies.pop(0)
            if joint_transform is not None:
                ph.left, ph.top, ph.width, ph.height = joint_transform[0](t["box"])
            fits, base, sizes = fill_text_ph(ph, t["paragraphs"], "text", layout, master, cf, floors, rep, n, "body")
            used.add(ph.shape_id)
            if t.get("shape") is not None:
                shape_ids[str(t["shape"].shape_id)] = str(ph.shape_id)
            if not fits:
                overflow_parts.append((ph, t, base))
        else:
            leftovers.append(t)

    # pictures from picture placeholders
    for pic in pictures:
        tgt = next((p for p in phs["picture"] if p.shape_id not in used), None)
        if tgt is not None:
            box = emu_box(tgt)
            remove_shape(tgt)
            used.add(tgt.shape_id)
            placed = add_picture(pic["shape"], slide, box)
            shape_ids[str(pic["shape"].shape_id)] = str(placed.shape_id)
            rep.fix(n, "picture fitted inside the template's picture area (not cropped)")
        else:
            graphics.append({"shape": pic["shape"], "type": "picture", "box": pic["box"]})

    # free pictures go into unused picture placeholders first
    for tgt in [p for p in phs["picture"] if p.shape_id not in used]:
        pic = next((g for g in graphics if g["type"] == "picture"), None)
        if pic is None:
            break
        box = emu_box(tgt)
        remove_shape(tgt)
        used.add(tgt.shape_id)
        placed = add_picture(pic["shape"], slide, box)
        shape_ids[str(pic["shape"].shape_id)] = str(placed.shape_id)
        graphics.remove(pic)
        rep.fix(n, "picture fitted inside the template's picture area (not cropped)")

    # free content: keep relative layout, scale into the content area
    free_items = [("text", t) for t in leftovers] + [("graphic", g) for g in graphics]
    if free_items:
        area = content_area(slide, W, H, title_box)
        unused_bodies = [p for p in phs["body"] if p.shape_id not in used]
        if unused_bodies:
            area = tuple(emu_box(unused_bodies[0])) if len(unused_bodies) == 1 else area
        src_boxes = [it[1]["box"] for it in free_items if it[1].get("box")]
        tf, scale = joint_transform or make_transform(union(src_boxes), area)
        for kind, it in free_items:
            box = tf(it["box"]) if it.get("box") else area
            if kind == "text":
                tb = slide.shapes.add_textbox(*box)
                tb.text_frame.word_wrap = True
                write_paragraphs(tb.text_frame, it["paragraphs"], [max(floors["body"], round(18 * scale))])
                if it.get("shape") is not None:
                    shape_ids[str(it["shape"].shape_id)] = str(tb.shape_id)
                rep.warn(n, "body text placed in a text box (no matching placeholder)")
            else:
                placed = place_graphic(it, src_slide, slide, box, scale, cmap, floors["table"], rep, n, cf, shape_ids)
                if placed is not None and hasattr(placed, "shape_id"):
                    shape_ids[str(it["shape"].shape_id)] = str(placed.shape_id)
        if graphics:
            rep.fix(n, f"{len(graphics)} free item(s) scaled into the content area (scale {scale:.2f}); colors mapped to theme")
    remap_connections(slide, shape_ids, rep, n)

    # remaining empty placeholders
    removed = 0
    for ph in list(slide.placeholders):
        if ph.shape_id in used:
            continue
        if ph.has_text_frame and not ph.text_frame.text.strip():
            remove_shape(ph)
            removed += 1
    if removed:
        rep.fix(n, f"{removed} unused empty placeholder(s) removed")

    # notes
    if m["notes"].strip():
        slide.notes_slide.notes_text_frame.text = m["notes"]

    # overflow: split or report
    for ph, t, base in overflow_parts:
        if split and len(overflow_parts) == 1 and len(phs["body"]) == 1 and not m["graphics"]:
            sizes = [max(floors["body"], round(s * 0.8)) for s in base]
            chunks = split_paragraphs(t["paragraphs"], emu_box(ph), sizes, cf)
            w, h = box_inner_pt(emu_box(ph))
            if len(chunks) > 1 and all(text_height_pt(chunk, w, sizes, cf) <= h for chunk in chunks):
                write_paragraphs(ph.text_frame, chunks[0], sizes)
                for k, chunk in enumerate(chunks[1:], 2):
                    extra = prs.slides.add_slide(layout)
                    xph = placeholders_by_role(extra)
                    if xph["title"]:
                        fill_text_ph(xph["title"][0], [{"level": 0, "runs": [{"text": f"{m['title']} (continued)"}]}],
                                     "title", layout, master, cf, floors, rep, n, "continuation title")
                    if xph["body"]:
                        write_paragraphs(xph["body"][0].text_frame, chunk, sizes)
                    for ph2 in list(extra.placeholders):
                        if ph2.has_text_frame and not ph2.text_frame.text.strip():
                            remove_shape(ph2)
                    extra.notes_slide.notes_text_frame.text = f"Continued from the slide '{m['title']}'."
                    made.append(extra)
                rep.fix(n, f"split into {len(chunks)} slides at {sizes[0]:g} pt (user agreed)")
                continue
        rep.overflow.append({"slide": n, "output_slide": out_no, "shape": ph.name,
                             "detail": f"text still overflows at the {floors['body']} pt floor: shorten it, or rerun with --split-overflow {n}"})
    return made


def _title_runs(m):
    ts = m.get("title_shape")
    if ts is not None and ts.has_text_frame:
        runs = []
        for i, p in enumerate(paragraphs_of(ts.text_frame)):
            if i:
                runs.append({"text": "\v", "kind": "break"})
            runs += [dict(r, bold=None) for r in p["runs"]]
        if "".join(r["text"] for r in runs).strip():
            return runs
    return [{"text": m["title"]}]


def build(mapping, out, split_spec, floors):
    src_path, tpl_path = mapping["source"], mapping["template"]
    for p in (src_path, tpl_path):
        if os.path.abspath(out) == os.path.abspath(p):
            raise ValueError("--out must be a new file; the source and template are never overwritten")
    rep = Report()
    prs = open_deck(tpl_path)
    removed = remove_sample_slides(prs)
    if removed:
        rep.fix(0, f"{removed} template sample slide(s) removed; masters and layouts kept")
    sprs = open_deck(src_path)
    SW, SH = sprs.slide_width, sprs.slide_height
    cmap = build_color_map([s._element for s in sprs.slides], theme_colors(sprs))
    split_all = split_spec == "all"
    split_set = set() if split_all or not split_spec else {int(x) for x in split_spec.split(",") if x.strip().isdigit()}
    out_no = 1
    for entry, s in zip(mapping["slides"], sprs.slides):
        master = prs.slide_masters[entry.get("target_master_index", 0)]
        cf = char_factor(theme_fonts(prs, master))
        m = read_slide(s, entry["slide"], SW, SH)
        do_split = split_all or entry["slide"] in split_set or entry.get("split")
        made = build_slide(prs, m, entry, s, cmap, cf, floors, do_split, rep, out_no)
        rep.slides.append({"source_slide": entry["slide"], "output_slides": list(range(out_no, out_no + len(made))),
                           "layout": entry["target_layout"]})
        out_no += len(made)
    prs.save(out)
    return {
        "mode": "rebuild", "source": src_path, "template": tpl_path, "out": out,
        "source_slides": len(sprs.slides), "output_slides": len(prs.slides),
        "color_map": {f"#{k}": v for k, v in cmap.items()},
        "slides": rep.slides, "fixes": rep.fixes, "warnings": rep.warnings, "overflow": rep.overflow,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report-out")
    ap.add_argument("--split-overflow", default="", help="'all' or comma-separated source slide numbers")
    ap.add_argument("--title-floor", type=int, default=None)
    ap.add_argument("--body-floor", type=int, default=None)
    ap.add_argument("--table-floor", type=int, default=None)
    a = ap.parse_args(argv)
    with open(a.mapping, encoding="utf-8") as fh:
        mapping = json.load(fh)
    if mapping.get("mode") != "rebuild":
        print("ERROR: mapping mode is 'restyle': run restyle.py instead (see SKILL.md, fallback mode)", file=sys.stderr)
        return 2
    fit = mapping.get("fit", {})
    floors = {"title": a.title_floor or fit.get("title_floor_pt", 24),
              "body": a.body_floor or fit.get("body_floor_pt", 14),
              "table": a.table_floor or fit.get("table_floor_pt", 10)}
    try:
        rep = build(mapping, a.out, a.split_overflow, floors)
    except (ValueError, OSError, KeyError, IndexError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if a.report_out:
        with open(a.report_out, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    print(json.dumps({k: rep[k] for k in ("out", "source_slides", "output_slides")}, indent=1))
    print(f"fixes: {len(rep['fixes'])}, warnings: {len(rep['warnings'])}, overflow: {len(rep['overflow'])}")
    for o in rep["overflow"]:
        print(f"  OVERFLOW slide {o['slide']}: {o['detail']}")
    for w in rep["warnings"]:
        print(f"  WARN slide {w['slide']}: {w['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
