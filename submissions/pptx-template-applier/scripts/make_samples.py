#!/usr/bin/env python3
"""Generate the fictional Contoso sample files for the worked example.

Writes three files into --out-dir (all content is fictional and illustrative):

  contoso-q3-review.pptx        source deck, 4:3, default Office look, 11 slides:
                                title, section, bullets on three levels, two
                                column, comparison, table, chart, picture with
                                caption, an overflowing bullet slide, a free-form
                                slide (shapes, a grouped picture) and a closing
                                slide with a link. Speaker notes on every slide.
  contoso-brand-template.potx   brand template, 16:9, Contoso theme colors and
                                fonts, renamed layouts (one without a layout
                                type), a dark section layout, a master accent
                                bar and footer, and three sample slides with
                                placeholder-style sample text.
  contoso-color-sheet.pptx      a brand deck that is only a color sheet: one
                                slide of swatches and a Blank layout only, for
                                the fallback (restyle) mode.

Usage:
  python make_samples.py --out-dir working/sample

python-pptx and Pillow. Nothing is downloaded.
"""
from __future__ import annotations

import argparse
import copy
import io
import os
import zipfile

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu, Inches, Pt

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

CONTOSO = {"dk1": "1E293B", "lt1": "FFFFFF", "dk2": "0B3954", "lt2": "EEF3F6",
           "accent1": "0F766E", "accent2": "C2410C", "accent3": "5B4B8A", "accent4": "2E86AB",
           "accent5": "A23B72", "accent6": "6B7280", "hlink": "0E7490", "folHlink": "5B4B8A"}
CONTOSO_FONTS = {"major": "Georgia", "minor": "Verdana"}


def png_bytes(w, h, label, bg=(214, 228, 236), fg=(11, 57, 84)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    d.polygon([(0, h), (w * 0.35, h * 0.45), (w * 0.6, h * 0.75), (w * 0.8, h * 0.5), (w, h)], fill=(120, 160, 140))
    d.ellipse([w * 0.72, h * 0.1, w * 0.86, h * 0.1 + w * 0.14], fill=(240, 190, 90))
    d.text((12, 10), label, fill=fg)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def set_theme(prs, colors, fonts, name="Contoso"):
    part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(part.blob)
    root.set("name", name)
    scheme = root.find(f".//{A}clrScheme")
    scheme.set("name", name)
    for el in list(scheme):
        slot = el.tag.split("}")[-1]
        if slot in colors:
            for ch in list(el):
                el.remove(ch)
            etree.SubElement(el, f"{A}srgbClr", val=colors[slot])
    fs = root.find(f".//{A}fontScheme")
    fs.set("name", name)
    for key, tag in (("major", "majorFont"), ("minor", "minorFont")):
        fs.find(f"{A}{tag}/{A}latin").set("typeface", fonts[key])
    part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def scale_x(prs, factor):
    """Stretch master and layout shapes horizontally (4:3 to 16:9)."""
    els = [prs.slide_master._element] + [l._element for l in prs.slide_layouts]
    for root in els:
        for xfrm in root.iter(f"{A}xfrm"):
            off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
            if off is not None:
                off.set("x", str(int(int(off.get("x")) * factor)))
            if ext is not None:
                ext.set("cx", str(int(int(ext.get("cx")) * factor)))


def drop_slide(prs, index):
    sld = prs.slides._sldIdLst[index]
    prs.part.drop_rel(sld.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"))
    prs.slides._sldIdLst.remove(sld)


def drop_layout(prs, layout):
    master = prs.slide_master
    lst = master._element.find(f"{P}sldLayoutIdLst")
    for el in list(lst):
        rid = el.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        if master.part.related_part(rid) is layout.part:
            master.part.drop_rel(rid)
            lst.remove(el)


def save_as_potx(prs, path):
    buf = io.BytesIO()
    prs.save(buf)
    zin = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"presentationml.presentation.main+xml", b"presentationml.template.main+xml")
            zout.writestr(item, data)


def bullets(tf, items):
    """items: list of (level, text) or (level, [(text, bold, italic, url)])."""
    tf.text = ""
    first = True
    for level, content in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        runs = [(content, False, False, None)] if isinstance(content, str) else content
        for text, bold, italic, url in runs:
            r = p.add_run()
            r.text = text
            r.font.bold = bold or None
            r.font.italic = italic or None
            if url:
                r.hyperlink.address = url


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def make_source(path):
    prs = Presentation()  # 4:3, Office theme
    L = {l.name: l for l in prs.slide_layouts}

    s = prs.slides.add_slide(L["Title Slide"])
    s.shapes.title.text = "Contoso Field Services: Q3 Review"
    s.placeholders[1].text = "Operations team update (illustrative example)"
    notes(s, "Welcome everyone. All numbers in this deck are illustrative.")

    s = prs.slides.add_slide(L["Section Header"])
    s.shapes.title.text = "Results"
    s.placeholders[1].text = "What changed this quarter"
    notes(s, "First, the results.")

    s = prs.slides.add_slide(L["Title and Content"])
    s.shapes.title.text = "Quarter highlights"
    bullets(s.placeholders[1].text_frame, [
        (0, [("First-visit fix rate rose to 82 percent", True, False, None)]),
        (1, "Up from 74 percent in Q2"),
        (2, "Largest gain in the north region"),
        (0, "Average travel time per visit fell by 10 minutes"),
        (1, [("Driven by the new ", False, False, None), ("route planner", False, True, None)]),
        (0, "Customer satisfaction held at 4.5 out of 5"),
    ])
    notes(s, "Stress the fix rate. The travel time number comes from the route planner pilot.")

    s = prs.slides.add_slide(L["Two Content"])
    s.shapes.title.text = "Before and after the scheduling tool"
    bullets(s.placeholders[1].text_frame, [(0, "Before"), (1, "Paper job sheets"), (1, "Calls to dispatch for every change")])
    bullets(s.placeholders[2].text_frame, [(0, "After"), (1, "Jobs on the mobile app"), (1, "Changes pushed in real time")])
    notes(s, "Left is the old process, right is the new one.")

    s = prs.slides.add_slide(L["Comparison"])
    s.shapes.title.text = "Two options for Q4"
    s.placeholders[1].text = "Option A: expand the pilot"
    bullets(s.placeholders[2].text_frame, [(0, "Two more regions"), (0, "Low cost"), (0, "Results in 60 days")])
    s.placeholders[3].text = "Option B: full rollout"
    bullets(s.placeholders[4].text_frame, [(0, "All six regions"), (0, "Needs training budget"), (0, "Results in one quarter")])
    notes(s, "We recommend option A. Ask the room for a decision.")

    s = prs.slides.add_slide(L["Title Only"])
    s.shapes.title.text = "Results by region"
    rows = [["Region", "Visits", "Fix rate", "Satisfaction"],
            ["North", "1,240", "86%", "4.6"], ["South", "980", "80%", "4.4"],
            ["East", "1,105", "81%", "4.5"], ["West", "870", "79%", "4.5"]]
    gf = s.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.8), Inches(8.8), Inches(3.2))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = gf.table.cell(r, c)
            cell.text = val
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0x7F, 0x3F, 0x98)
    notes(s, "North leads on every measure.")

    s = prs.slides.add_slide(L["Title and Content"])
    s.shapes.title.text = "Visits per month"
    ph = s.placeholders[1]
    box = (ph.left, ph.top, ph.width, ph.height)
    ph._element.getparent().remove(ph._element)
    cd = CategoryChartData()
    cd.categories = ["July", "August", "September"]
    cd.add_series("Planned", (1300, 1350, 1400))
    cd.add_series("Completed", (1280, 1390, 1525))
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, *box, cd).chart
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    for i, col in enumerate((RGBColor(0xFF, 0xC0, 0x00), RGBColor(0x70, 0xAD, 0x47))):
        ch.plots[0].series[i].format.fill.solid()
        ch.plots[0].series[i].format.fill.fore_color.rgb = col
    notes(s, "Completed visits passed the plan in August.")

    s = prs.slides.add_slide(L["Picture with Caption"])
    s.shapes.title.text = "New service van"
    s.placeholders[1].insert_picture(io.BytesIO(png_bytes(800, 500, "Illustrative photo")))
    s.placeholders[2].text = "The new vans carry parts for 90 percent of jobs."
    notes(s, "Photo is a placeholder illustration.")

    s = prs.slides.add_slide(L["Title and Content"])
    s.shapes.title.text = "Lessons learned from the pilot"
    bullets(s.placeholders[1].text_frame, [
        (0, "Train dispatchers before technicians so the first week runs smoothly"),
        (0, "Keep a paper fallback for the first two weeks in every region"),
        (1, "Two regions needed it during a network outage"),
        (0, "Load the parts catalog into the app before go-live"),
        (0, "Name one local champion per depot to answer questions"),
        (0, "Review the route planner settings every Friday during the pilot"),
        (1, "Default travel speeds were too optimistic in rural areas"),
        (0, "Share a weekly one-page update with depot managers"),
        (0, "Collect technician feedback in the app, not by email"),
        (0, "Plan the rollout around the holiday peak, not through it"),
        (0, "Budget time for data cleanup of customer addresses"),
        (0, "Agree on the success measures before the pilot starts"),
    ])
    notes(s, "This slide is long on purpose. It tests text fitting and the split option.")

    s = prs.slides.add_slide(L["Blank"])
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(0.9))
    tb.text_frame.text = "Rollout path"
    tb.text_frame.paragraphs[0].runs[0].font.size = Pt(32)
    tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    for i, (label, col) in enumerate((("Plan", "4472C4"), ("Pilot", "ED7D31"), ("Scale", "70AD47"))):
        sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6 + i * 3.1), Inches(2.4), Inches(2.6), Inches(1.6))
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(col)
        sh.line.fill.background()
        sh.text_frame.text = label
        sh.text_frame.paragraphs[0].runs[0].font.size = Pt(24)
        sh.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    grp = s.shapes.add_group_shape()
    grp.shapes.add_picture(io.BytesIO(png_bytes(200, 200, "Logo", bg=(230, 230, 230))), Inches(0.6), Inches(4.9), Inches(1.2), Inches(1.2))
    t = grp.shapes.add_textbox(Inches(1.9), Inches(5.2), Inches(5), Inches(0.6))
    t.text_frame.text = "Contoso Field Services (fictional company)"
    notes(s, "Three stages. We are at the end of the pilot.")

    s = prs.slides.add_slide(L["Title and Content"])
    s.shapes.title.text = "Next steps"
    bullets(s.placeholders[1].text_frame, [
        (0, "Decide between option A and option B by October 30"),
        (0, [("Read the pilot summary at ", False, False, None), ("example.com/pilot", False, False, "https://example.com/pilot")]),
        (0, "Send questions to the operations team"),
    ])
    notes(s, "Close with the decision we need.")
    prs.save(path)


def add_master_decor(prs, W, H):
    """Accent bar and footer text on the slide master (built on a scratch slide, then moved)."""
    tmp = prs.slides.add_slide(prs.slide_layouts[6])
    bar = tmp.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.theme_color = MSO_THEME_COLOR.ACCENT_1
    bar.line.fill.background()
    bar.name = "Brand bar"
    ft = tmp.shapes.add_textbox(Inches(0.5), H - Inches(0.45), Inches(5), Inches(0.3))
    ft.text_frame.text = "Contoso | Illustrative brand template"
    ft.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
    ft.text_frame.paragraphs[0].runs[0].font.color.theme_color = MSO_THEME_COLOR.ACCENT_6
    ft.name = "Brand footer"
    tree = prs.slide_master._element.find(f"{P}cSld/{P}spTree")
    for sh in (bar, ft):
        tree.insert(2, copy.deepcopy(sh._element))
    drop_slide(prs, len(prs.slides) - 1)


def set_layout_dark(layout):
    csld = layout._element.find(f"{P}cSld")
    bg = etree.SubElement(csld, f"{P}bg")
    csld.remove(bg)
    csld.insert(0, bg)
    bgpr = etree.SubElement(bg, f"{P}bgPr")
    fill = etree.SubElement(bgpr, f"{A}solidFill")
    etree.SubElement(fill, f"{A}schemeClr", val="tx2")
    etree.SubElement(bgpr, f"{A}effectLst")
    for ph in layout.placeholders:
        tx = ph._element.find(f"{P}txBody")
        if tx is None:
            continue
        lst = tx.find(f"{A}lstStyle")
        if lst is None:
            lst = etree.Element(f"{A}lstStyle")
            tx.insert(1, lst)
        lvl = lst.find(f"{A}lvl1pPr")
        if lvl is None:
            lvl = etree.SubElement(lst, f"{A}lvl1pPr")
        d = lvl.find(f"{A}defRPr")
        if d is None:
            d = etree.SubElement(lvl, f"{A}defRPr")
        for old in d.findall(f"{A}solidFill"):
            d.remove(old)
        f = etree.Element(f"{A}solidFill")
        etree.SubElement(f, f"{A}schemeClr", val="bg1")
        d.insert(0, f)


def make_template(path):
    prs = Presentation()
    W, H = Emu(12192000), Emu(6858000)
    scale_x(prs, 12192000 / prs.slide_width)
    prs.slide_width, prs.slide_height = W, H
    set_theme(prs, CONTOSO, CONTOSO_FONTS)
    L = {l.name: l for l in prs.slide_layouts}
    for n in ("Title and Vertical Text", "Vertical Title and Text"):
        drop_layout(prs, L[n])
    names = {"Title Slide": "Contoso Cover", "Title and Content": "Contoso Content",
             "Section Header": "Contoso Divider", "Two Content": "Contoso Two Column",
             "Comparison": "Contoso Compare", "Title Only": "Contoso Headline Only", "Blank": "Contoso Clean",
             "Content with Caption": "Contoso Content and Caption", "Picture with Caption": "Contoso Photo"}
    for old, new in names.items():
        L[old].name = new
    L["Two Content"]._element.attrib.pop("type", None)  # custom layout: no type, classified by signature
    set_layout_dark(L["Section Header"])
    add_master_decor(prs, W, H)
    s = prs.slides.add_slide(L["Title Slide"])
    s.shapes.title.text = "Presentation title goes here"
    s.placeholders[1].text = "Subtitle or presenter name"
    s = prs.slides.add_slide(L["Title and Content"])
    s.shapes.title.text = "Sample headline for a content slide"
    s.placeholders[1].text = "Replace this sample text with your key message"
    s = prs.slides.add_slide(L["Section Header"])
    s.shapes.title.text = "Section title"
    s.placeholders[1].text = "Short section description"
    save_as_potx(prs, path)


def make_color_sheet(path):
    prs = Presentation()
    W, H = Emu(12192000), Emu(6858000)
    prs.slide_width, prs.slide_height = W, H
    set_theme(prs, CONTOSO, CONTOSO_FONTS)
    keep = prs.slide_layouts[6]
    for l in list(prs.slide_layouts):
        if l is not keep:
            drop_layout(prs, l)
    keep.name = "Color sheet"
    s = prs.slides.add_slide(keep)
    t = s.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(10), Inches(0.8))
    t.text_frame.text = "Contoso brand colors (illustrative)"
    for i, slot in enumerate(("dk2", "accent1", "accent2", "accent3", "accent4", "accent5")):
        x = Inches(0.5 + i * 2.05)
        sw = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.8), Inches(1.8), Inches(1.8))
        sw.fill.solid()
        sw.fill.fore_color.rgb = RGBColor.from_string(CONTOSO[slot])
        sw.line.fill.background()
        lb = s.shapes.add_textbox(x, Inches(3.7), Inches(1.8), Inches(0.5))
        lb.text_frame.text = f"#{CONTOSO[slot]}"
    f = s.shapes.add_textbox(Inches(0.5), Inches(4.6), Inches(10), Inches(0.6))
    f.text_frame.text = "Headings: Georgia. Body: Verdana."
    prs.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="sample")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    src = os.path.join(a.out_dir, "contoso-q3-review.pptx")
    tpl = os.path.join(a.out_dir, "contoso-brand-template.potx")
    cs = os.path.join(a.out_dir, "contoso-color-sheet.pptx")
    make_source(src)
    make_template(tpl)
    make_color_sheet(cs)
    for p in (src, tpl, cs):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
