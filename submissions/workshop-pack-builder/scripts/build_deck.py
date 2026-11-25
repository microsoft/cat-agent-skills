#!/usr/bin/env python3
"""Build the workshop slide deck from a pack spec with python-pptx.

This is the no-dependency fallback. When the pptx skill is available, the
agent may use it instead, with the same slide plan (see
references/pack-outputs.md).

  python build_deck.py workshop.json --out deck.pptx \
      [--source-map source_map.json] [--brand brand.json] [--template brand.potx]

--template  A user-supplied .pptx or .potx. Its slide masters and layouts are
            used; its existing slides are removed from the copy (the original
            file is never changed). Layouts are matched by name (Title Slide,
            Section Header, Title and Content, Title Only, Blank).
--brand     Colors and fonts from extract_brand.py. Ignored for placeholders
            when a template is given (the template styles them).

Slide plan: title, executive summary, agenda, objectives, then per module a
section divider with its duration label, key point slides (four points per
slide, cited in the footer), one slide per activity, and a break slide for
breaks; then a next-steps slide and a sources slide. Every slide gets speaker
notes; module slides end with "Timing: N minutes."
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timedelta

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

NEUTRAL = {"colors": {"dk1": "#1F2937", "lt1": "#FFFFFF", "dk2": "#0F2A44", "lt2": "#F1F4F8",
                      "accent1": "#2563EB", "accent2": "#0D9488", "accent6": "#475569"},
           "fonts": {"major": "Segoe UI Semibold", "minor": "Segoe UI"}, "text_on_accent1": "#FFFFFF"}


def rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Cite:
    """Turns refs like S1.sec2 into short readable labels."""

    def __init__(self, spec, smap):
        self.titles = {s["id"]: s.get("title", s["id"]) for s in spec.get("sources", [])}
        self.units = {}
        if smap:
            for s in smap.get("sources", []):
                self.titles.setdefault(s["id"], s["title"])
                for u in s.get("units", []):
                    self.units[u["ref"]] = u.get("heading") or u.get("label")

    def label(self, refs):
        """Group refs by source: 'Source: [S1] Title: unit A; unit B'."""
        if not refs:
            return ""
        groups = {}
        for r in refs:
            sid = r.split(".")[0]
            unit = self.units.get(r) or (r.split(".", 1)[1] if "." in r else "")
            g = groups.setdefault(sid, [])
            if unit and unit not in g:
                g.append(unit)
        parts = []
        for sid, units in groups.items():
            title = self.titles.get(sid, sid)
            if len(title) > 40:
                title = title[:37].rstrip() + "..."
            parts.append(f"[{sid}] {title}" + (": " + "; ".join(units) if units else ""))
        return ("Sources: " if len(parts) > 1 else "Source: ") + " | ".join(parts)


def open_template(path):
    data = open(path, "rb").read()
    if path.lower().endswith((".potx", ".potm")):
        src = zipfile.ZipFile(io.BytesIO(data))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                b = src.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    b = b.replace(b"presentationml.template.main+xml", b"presentationml.presentation.main+xml")
                dst.writestr(item, b)
        data = buf.getvalue()
    prs = Presentation(io.BytesIO(data))
    # remove existing slides from the copy
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        prs.part.drop_rel(sldId.rId)
        sldIdLst.remove(sldId)
    return prs


def find_layout(prs, *names, fallback_index=None):
    layouts = [l for m in prs.slide_masters for l in m.slide_layouts]
    for want in names:
        for l in layouts:
            if l.name.strip().lower() == want.lower():
                return l
    for want in names:
        for l in layouts:
            if want.lower() in l.name.lower():
                return l
    if fallback_index is not None and fallback_index < len(layouts):
        return layouts[fallback_index]
    return layouts[-1]


class Deck:
    def __init__(self, spec, smap, brand, template):
        self.spec, self.cite = spec, Cite(spec, smap)
        self.b = brand or NEUTRAL
        self.c = {**NEUTRAL["colors"], **self.b.get("colors", {})}
        self.f = {**NEUTRAL["fonts"], **self.b.get("fonts", {})}
        self.templated = bool(template)
        if template:
            self.prs = open_template(template)
        else:
            self.prs = Presentation()
            self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
        self.W, self.H = self.prs.slide_width, self.prs.slide_height
        self.n = 0

    # ---------- primitives ----------
    def _new(self, kind):
        if self.templated:
            names = {"title": ("Title Slide",), "section": ("Section Header", "Section"),
                     "content": ("Title and Content", "Title, Content", "Content"),
                     "titleonly": ("Title Only",)}[kind]
            layout = find_layout(self.prs, *names, fallback_index=1)
        else:
            layout = self.prs.slide_layouts[6]  # Blank
        s = self.prs.slides.add_slide(layout)
        if self.templated:
            required = {"title": ((1, 3), (2, 4)), "section": ((1, 3), (2, 7)),
                        "content": ((1, 3),), "titleonly": ((1, 3),)}[kind]
            for types in required:
                if not any(ph.has_text_frame and ph.placeholder_format.type in types
                           for ph in s.placeholders):
                    raise ValueError(
                        f"template layout '{layout.name}' cannot render a {kind} slide: "
                        f"missing required text placeholder {types}. Add a title and subtitle/body "
                        "placeholder to the layout, or omit --template and use --brand instead.")
        self.n += 1
        return s

    def _text(self, slide, x, y, w, h, text, size=20, bold=False, color=None, font=None, align=PP_ALIGN.LEFT,
              anchor=MSO_ANCHOR.TOP, bullets=None):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        for m in ("margin_left", "margin_right"):
            setattr(tf, m, Inches(0.05))
        lines = bullets if bullets is not None else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = ("\u2022  " + line) if bullets is not None and not re.match(r"\d+\. ", line) else line
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.name = font or self.f["minor"]
            r.font.color.rgb = rgb(color or self.c["dk1"])
            if bullets is not None:
                p.space_after = Pt(10)
        return tb

    def _fill_placeholder(self, slide, idx_types, text=None, bullets=None, size=None, plain=False):
        for ph in slide.placeholders:
            if ph.placeholder_format.type in idx_types:
                tf = ph.text_frame
                tf.clear()
                lines = bullets if bullets is not None else [text]
                for i, line in enumerate(lines):
                    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    p.text = line
                    if bullets is not None and (plain or re.match(r"\d+\. ", line)):
                        pPr = p._p.get_or_add_pPr()
                        pPr.set("indent", "0")
                        pPr.set("marL", "0")
                        pPr.insert(0, pPr.makeelement(qn("a:buNone"), {}))
                    if size:
                        for r in p.runs:
                            r.font.size = Pt(size)
                return ph
        return None

    def _clear_empty_placeholders(self, slide):
        for ph in list(slide.placeholders):
            if ph.has_text_frame and not ph.text_frame.text.strip():
                ph._element.getparent().remove(ph._element)

    def _rect(self, slide, x, y, w, h, color):
        r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        r.fill.solid()
        r.fill.fore_color.rgb = rgb(color)
        r.line.fill.background()
        r.shadow.inherit = False
        return r

    def _chip(self, slide, x, y, text):
        r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(1.6), Inches(0.5))
        r.fill.solid()
        r.fill.fore_color.rgb = rgb(self.c["accent1"])
        r.line.fill.background()
        r.shadow.inherit = False
        tf = r.text_frame
        tf.text = text
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        for run in p.runs:
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.name = self.f["minor"]
            run.font.color.rgb = rgb(self.b.get("text_on_accent1", "#FFFFFF"))
        return r

    def _footer(self, slide, cite_text):
        y = self.H - Inches(0.65)
        if cite_text:
            self._text(slide, Inches(0.6), y, self.W - Inches(2.2), Inches(0.45), cite_text, size=12 if len(cite_text) < 150 else 11,
                       color=self.c.get("accent6", "#475569"))
        self._text(slide, self.W - Inches(1.4), y, Inches(0.9), Inches(0.4), str(self.n), size=12,
                   color=self.c.get("accent6", "#475569"), align=PP_ALIGN.RIGHT)

    @staticmethod
    def _tsize(title, one_line_chars):
        """Title size that keeps the title on one or two lines."""
        n = len(title)
        return 30 if n <= one_line_chars else 24 if n <= one_line_chars * 1.25 else 20

    def _notes(self, slide, text):
        slide.notes_slide.notes_text_frame.text = text

    def _title_body(self, title, bullets, cite_text="", notes="", size=None, plain=False):
        if self.templated:
            s = self._new("content")
            self._fill_placeholder(s, (1, 3), text=title)
            longest = max((len(b) for b in bullets), default=0)
            fs = size or (24 if longest < 90 and len(bullets) <= 4 else 20 if longest < 160 else 16)
            body = self._fill_placeholder(s, (2, 7), bullets=bullets, size=fs, plain=plain)
            if body is None:
                self._text(s, Inches(0.8), Inches(1.7), self.W - Inches(1.6), self.H - Inches(2.6), "",
                           size=size or 20, bullets=bullets)
            self._clear_empty_placeholders(s)
        else:
            s = self._new("content")
            self._rect(s, 0, 0, Inches(0.18), self.H, self.c["accent1"])
            self._text(s, Inches(0.6), Inches(0.45), self.W - Inches(1.2), Inches(1.0), title,
                       size=self._tsize(title, 52), bold=True, color=self.c["dk2"], font=self.f["major"])
            longest = max((len(b) for b in bullets), default=0)
            fs = size or (22 if longest < 90 and len(bullets) <= 4 else 18 if longest < 160 else 16)
            if plain:
                self._text(s, Inches(0.6), Inches(1.65), self.W - Inches(1.2), self.H - Inches(2.5),
                           "\n\n".join(bullets), size=fs)
            else:
                self._text(s, Inches(0.6), Inches(1.65), self.W - Inches(1.2), self.H - Inches(2.5), "",
                           size=fs, bullets=bullets)
        self._footer(s, cite_text)
        if notes:
            self._notes(s, notes)
        return s

    # ---------- slide types ----------
    def title_slide(self):
        sp = self.spec
        sub = sp.get("subtitle", "")
        meta = " | ".join(x for x in [sp.get("format", "").capitalize(), f"{sp.get('total_minutes', '')} minutes",
                                       sp.get("organization", "")] if x)
        if self.templated:
            s = self._new("title")
            self._fill_placeholder(s, (3, 1), text=sp["title"])
            self._fill_placeholder(s, (4, 2), text=f"{sub}\n{meta}".strip())
            self._clear_empty_placeholders(s)
        else:
            s = self._new("title")
            self._rect(s, 0, 0, self.W, self.H, self.c["dk2"])
            self._rect(s, Inches(0.8), Inches(3.7), Inches(1.2), Inches(0.08), self.c["accent1"])
            self._text(s, Inches(0.8), Inches(1.6), self.W - Inches(1.6), Inches(1.9), sp["title"], size=40,
                       bold=True, color="#FFFFFF", font=self.f["major"], anchor=MSO_ANCHOR.BOTTOM)
            self._text(s, Inches(0.8), Inches(3.95), self.W - Inches(1.6), Inches(0.8), sub, size=22, color="#FFFFFF")
            self._text(s, Inches(0.8), Inches(4.75), self.W - Inches(1.6), Inches(0.6), meta, size=16, color="#D0D7E2")
        self._notes(s, "Welcome the group and state the promise of the session. " + sp.get("executive_summary", ""))

    def exec_summary(self):
        self._title_body("Executive summary", [self.spec["executive_summary"]], size=22, plain=True,
                         notes="Read the summary aloud in one breath. It sets expectations for the whole session.")

    def agenda(self):
        sp = self.spec
        start = sp.get("start_time")
        t = datetime.strptime(start, "%H:%M") if start else None
        rows = []
        for m in sp["modules"]:
            if t is not None:
                end = t + timedelta(minutes=m["minutes"])
                rows.append((f"{t:%H:%M}-{end:%H:%M}", m["title"], f"{m['minutes']} min"))
                t = end
            else:
                rows.append(("", m["title"], f"{m['minutes']} min"))
        s = self._new("titleonly" if self.templated else "content")
        if self.templated:
            self._fill_placeholder(s, (1, 3), text="Agenda")
            self._clear_empty_placeholders(s)
        else:
            self._rect(s, 0, 0, Inches(0.18), self.H, self.c["accent1"])
            self._text(s, Inches(0.6), Inches(0.45), self.W - Inches(1.2), Inches(1.0), "Agenda", size=30,
                       bold=True, color=self.c["dk2"], font=self.f["major"])
        n = len(rows) + 1
        row_h = min(Inches(0.55), int((self.H - Inches(2.6)) / n))
        tbl = s.shapes.add_table(n, 3, Inches(0.6), Inches(1.65), self.W - Inches(1.2), row_h * n).table
        tbl.columns[0].width = Inches(2.2)
        tbl.columns[2].width = Inches(1.6)
        tbl.columns[1].width = self.W - Inches(1.2) - Inches(3.8)
        for j, h in enumerate(("Time", "Module", "Duration")):
            tbl.cell(0, j).text = h
        for i, r in enumerate(rows, 1):
            for j, v in enumerate(r):
                tbl.cell(i, j).text = v
        for i in range(n):
            for j in range(3):
                for p in tbl.cell(i, j).text_frame.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(16 if n <= 9 else 12)
                        run.font.name = self.f["minor"]
        self._footer(s, "")
        self._notes(s, f"Walk through the agenda. Total: {sp['total_minutes']} minutes.")

    def objectives(self):
        self._title_body("By the end of this session you will be able to",
                         [f"{i}. {o['text']}" for i, o in enumerate(self.spec["objectives"], 1)],
                         notes="Read the objectives. Ask the group which one matters most to them today.")

    def section(self, idx, m):
        label = f"{m['minutes']} min"
        if self.templated:
            s = self._new("section")
            self._fill_placeholder(s, (1, 3), text=f"{idx}. {m['title']}")
            self._fill_placeholder(s, (2, 7), text=label)
            self._clear_empty_placeholders(s)
        else:
            s = self._new("section")
            self._rect(s, 0, 0, self.W, self.H, self.c["dk2"])
            self._text(s, Inches(0.8), Inches(2.0), self.W - Inches(1.6), Inches(0.6), f"Module {idx}", size=20,
                       color="#D0D7E2")
            self._text(s, Inches(0.8), Inches(2.6), self.W - Inches(1.6), Inches(1.6), m["title"], size=40,
                       bold=True, color="#FFFFFF", font=self.f["major"])
            self._chip(s, Inches(0.8), Inches(4.4), label)
        self._notes(s, f"{m.get('talk_track', '')}\nSetup: {m.get('setup', '')}\nTiming: {m['minutes']} minutes.")

    def key_points(self, m):
        kps = m.get("key_points") or []
        for i in range(0, len(kps), 4):
            chunk = kps[i:i + 4]
            refs = [r for k in chunk for r in k.get("sources", [])]
            title = m["title"] if i == 0 else f"{m['title']} (continued)"
            self._title_body(title, [k["text"] for k in chunk], self.cite.label(refs),
                             notes=f"{m.get('talk_track', '')}\nTiming: {m['minutes']} minutes.")

    def activity(self, m, a):
        kind = "Exercise" if a.get("kind") == "exercise" else "Discussion"
        title = f"{kind}: {a['title']}"
        steps = [f"{i}. {t}" for i, t in enumerate(a.get("instructions", []), 1)]
        if self.templated:
            bullets = steps + [f"Timebox: {a['timebox']} min", f"You produce: {a.get('expected_output', '')}"]
            s = self._title_body(title, bullets, self.cite.label(a.get("sources", [])), size=18)
        else:
            s = self._new("content")
            self._rect(s, 0, 0, Inches(0.18), self.H, self.c["accent2"])
            self._text(s, Inches(0.6), Inches(0.45), self.W - Inches(3.0), Inches(1.0), title,
                       size=self._tsize(title, 40), bold=True, color=self.c["dk2"], font=self.f["major"])
            self._chip(s, self.W - Inches(2.3), Inches(0.6), f"{a['timebox']} min")
            col = (self.W - Inches(1.6)) * 0.58
            self._text(s, Inches(0.6), Inches(1.65), int(col), self.H - Inches(2.5), "",
                       size=18 if len(steps) <= 4 else 16, bullets=steps)
            x2 = Inches(0.6) + int(col) + Inches(0.4)
            w2 = self.W - x2 - Inches(0.6)
            self._rect(s, x2, Inches(1.65), w2, self.H - Inches(2.5), self.c["lt2"])
            side = [f"Goal: {a.get('objective', '')}", f"You produce: {a.get('expected_output', '')}",
                    "Materials: " + ", ".join(a.get("materials", []))]
            self._text(s, x2 + Inches(0.2), Inches(1.85), w2 - Inches(0.4), self.H - Inches(2.9), "", size=15,
                       bullets=side)
            self._footer(s, self.cite.label(a.get("sources", [])))
        debrief = " ".join(a.get("debrief", []))
        self._notes(s, f"Explain the task, then start the timer for {a['timebox']} minutes.\n"
                       f"Debrief questions: {debrief}\nFallback: {a.get('fallback', '')}\n"
                       f"Timing: {a['timebox']} minutes.")

    def break_slide(self, m, clock):
        back = f"Back at {clock}" if clock else "See you in a moment"
        if self.templated:
            s = self._new("section")
            self._fill_placeholder(s, (1, 3), text=f"Break: {m['minutes']} min")
            self._fill_placeholder(s, (2, 7), text=back)
            self._clear_empty_placeholders(s)
        else:
            s = self._new("section")
            self._rect(s, 0, 0, self.W, self.H, self.c["dk2"])
            self._text(s, Inches(0.8), Inches(2.6), self.W - Inches(1.6), Inches(1.4), "Break", size=44, bold=True,
                       color="#FFFFFF", font=self.f["major"])
            self._chip(s, Inches(0.8), Inches(4.1), f"{m['minutes']} min")
            self._text(s, Inches(2.7), Inches(4.1), Inches(5), Inches(0.5), back, size=18, color="#D0D7E2",
                       anchor=MSO_ANCHOR.MIDDLE)
        self._notes(s, f"{m.get('talk_track', '')}\nTiming: {m['minutes']} minutes.")

    def closing(self):
        pts = ["Check your commitment on the date you picked."]
        notes = ["Thank the group."]
        if self.spec.get("survey"):
            pts.insert(0, "Complete the feedback survey.")
            notes.append("Point to the feedback survey.")
        if self.spec.get("follow_up_email"):
            pts.insert(0, "Watch for the follow-up email with the materials.")
            notes.append("Point to the follow-up email.")
        self._title_body("Next steps", pts, notes=" ".join(notes))

    def sources(self):
        lines = []
        for s in self.spec.get("sources", []):
            lines.append(f"[{s['id']}] {s.get('title', '')}. {s.get('location', '')}".strip())
        self._title_body("Sources", lines or ["No sources listed."], size=16,
                         notes="Every factual statement in this deck traces to one of these sources.")

    def build(self, out):
        self.title_slide()
        self.exec_summary()
        self.agenda()
        self.objectives()
        start = self.spec.get("start_time")
        t = datetime.strptime(start, "%H:%M") if start else None
        idx = 0
        for m in self.spec["modules"]:
            if t is not None:
                t = t + timedelta(minutes=m["minutes"])
            if m.get("type") == "break":
                self.break_slide(m, f"{t:%H:%M}" if t else "")
                continue
            idx += 1
            self.section(idx, m)
            self.key_points(m)
            for a in m.get("activities", []):
                self.activity(m, a)
        self.closing()
        self.sources()
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        self.prs.save(out)
        return self.n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-map")
    ap.add_argument("--brand")
    ap.add_argument("--template")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    smap = json.load(open(a.source_map, encoding="utf-8")) if a.source_map else None
    brand = json.load(open(a.brand, encoding="utf-8")) if a.brand else None
    if a.template and not os.path.exists(a.template):
        print(f"ERROR: template not found: {a.template}", file=sys.stderr)
        return 1
    try:
        n = Deck(spec, smap, brand, a.template).build(a.out)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"deck": a.out, "slides": n, "template": a.template or None}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
