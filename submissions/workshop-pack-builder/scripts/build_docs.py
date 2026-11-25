#!/usr/bin/env python3
"""Build the workshop documents from a pack spec with python-docx.

This is the no-dependency fallback. When the docx skill is available, the
agent may use it instead, with the same section plan (see
references/pack-outputs.md).

  python build_docs.py workshop.json --out-dir pack/ \
      [--source-map source_map.json] [--brand brand.json] [--html] \
      [--only agenda,guide,workbook,preread,survey,email,html]

Writes (each only when its data is in the spec):
  agenda.docx                 Executive summary, session details, agenda, objectives
  agenda-one-page.docx        Landscape one-page view of the agenda
  facilitator-guide.docx      Summary, at a glance, setup, run of show per module
                              (talk track, key points with sources, activities,
                              fallbacks, debrief), gaps, sources
  participant-workbook.docx   Summary, objectives, one exercise sheet per activity
  pre-read.docx               From spec.pre_read
  feedback-survey.docx        From spec.survey
  follow-up-email-draft.md    From spec.follow_up_email. A draft: never sent.
  workshop.html               With --html: a self-contained page, no external resources

Every document starts with an executive summary.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Pt, RGBColor, Inches

from extract_brand import contrast

NEUTRAL = {"colors": {"dk1": "#1F2937", "dk2": "#0F2A44", "accent1": "#2563EB", "lt2": "#F1F4F8"},
           "fonts": {"major": "Segoe UI Semibold", "minor": "Segoe UI"}}


def _rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Cite:
    def __init__(self, spec, smap):
        self.titles = {s["id"]: s.get("title", s["id"]) for s in spec.get("sources", [])}
        self.units = {}
        if smap:
            for s in smap.get("sources", []):
                self.titles.setdefault(s["id"], s["title"])
                for u in s.get("units", []):
                    self.units[u["ref"]] = u.get("heading") or u.get("label")

    def short(self, refs):
        if not refs:
            return ""
        parts = []
        for r in refs:
            sid = r.split(".")[0]
            unit = self.units.get(r) or (r.split(".", 1)[1] if "." in r else "")
            parts.append(f"{sid}: {unit}" if unit else sid)
        return "(" + "; ".join(dict.fromkeys(parts)) + ")"


def clock_rows(spec):
    start = spec.get("start_time")
    t = datetime.strptime(start, "%H:%M") if start else None
    rows = []
    for m in spec["modules"]:
        if t is not None:
            end = t + timedelta(minutes=m["minutes"])
            rows.append((f"{t:%H:%M}-{end:%H:%M}", m))
            t = end
        else:
            rows.append(("", m))
    return rows


class Doc:
    def __init__(self, brand):
        b = brand or NEUTRAL
        self.c = {**NEUTRAL["colors"], **b.get("colors", {})}
        self.f = {**NEUTRAL["fonts"], **b.get("fonts", {})}
        self.d = Document()
        st = self.d.styles["Normal"]
        st.font.name = self.f["minor"]
        st.font.size = Pt(11)
        for lvl, size in ((0, 24), (1, 16), (2, 13), (3, 12)):
            name = "Title" if lvl == 0 else f"Heading {lvl}"
            s = self.d.styles[name]
            s.font.name = self.f["major"]
            s.font.size = Pt(size)
            s.font.color.rgb = _rgb(self.c["dk2"])

    def h(self, text, lvl=1):
        return self.d.add_heading(text, level=lvl)

    def p(self, text, bold_lead=None, italic=False):
        para = self.d.add_paragraph()
        if bold_lead:
            r = para.add_run(bold_lead + " ")
            r.bold = True
        r = para.add_run(text)
        r.italic = italic
        return para

    def bullets(self, items, numbered=False):
        style = "List Number" if numbered else "List Bullet"
        for it in items:
            self.d.add_paragraph(it, style=style)

    def table(self, header, rows, widths=None):
        t = self.d.add_table(rows=1, cols=len(header))
        t.style = "Light Grid Accent 1"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(header):
            t.rows[0].cells[i].text = h
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cells[i].text = str(v)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        return t

    def lines(self, n=3):
        for _ in range(n):
            self.d.add_paragraph("_" * 80)

    def landscape(self):
        s = self.d.sections[0]
        s.orientation = WD_ORIENT.LANDSCAPE
        s.page_width, s.page_height = s.page_height, s.page_width
        for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(s, m, Inches(0.6))

    def save(self, path):
        self.d.save(path)
        return path


def details(spec):
    a = spec.get("audience", {})
    out = [("Audience", a.get("who", "")), ("Level", a.get("level", "")), ("Group size", str(a.get("size", ""))),
           ("Format", spec.get("format", "")), ("Length", f"{spec['total_minutes']} minutes")]
    if spec.get("start_time"):
        out.append(("Start", spec["start_time"]))
    if spec.get("constraints"):
        out.append(("Constraints", "; ".join(spec["constraints"])))
    return [(k, v) for k, v in out if v]


def build_agenda(spec, cite, brand, out_dir):
    d = Doc(brand)
    d.d.add_heading(spec["title"], 0)
    if spec.get("subtitle"):
        d.p(spec["subtitle"], italic=True)
    d.h("Executive summary")
    d.p(spec["executive_summary"])
    d.h("Session details")
    d.table(["Item", "Detail"], details(spec), widths=[1.6, 4.8])
    d.h("Agenda")
    d.table(["Time", "Module", "Minutes", "Activity"],
            [(t, m["title"], m["minutes"], ", ".join(a["title"] for a in m.get("activities", [])) or "-")
             for t, m in clock_rows(spec)], widths=[1.2, 2.6, 0.8, 2.4])
    d.p(f"{spec['total_minutes']} minutes.", bold_lead="Total:")
    d.h("Learning objectives")
    d.p("By the end of this session you will be able to:")
    d.bullets([o["text"] for o in spec["objectives"]], numbered=True)
    paths = [d.save(os.path.join(out_dir, "agenda.docx"))]

    one = Doc(brand)
    one.landscape()
    one.d.add_heading(spec["title"], 0)
    one.h("Executive summary", 2)
    one.p(spec["executive_summary"])
    one.table(["Time", "Module", "Minutes", "What you do"],
              [(t, m["title"], m["minutes"], "; ".join(a["title"] for a in m.get("activities", [])) or "-")
               for t, m in clock_rows(spec)], widths=[1.3, 3.6, 0.9, 4.0])
    one.p(f"{spec.get('format', '').capitalize()} | {spec['total_minutes']} minutes | "
          f"{spec.get('audience', {}).get('size', '')} participants")
    paths.append(one.save(os.path.join(out_dir, "agenda-one-page.docx")))
    return paths


def build_guide(spec, cite, brand, out_dir):
    d = Doc(brand)
    d.d.add_heading(f"Facilitator guide: {spec['title']}", 0)
    d.h("Executive summary")
    d.p(spec["executive_summary"])
    d.h("At a glance")
    d.table(["Item", "Detail"], details(spec), widths=[1.6, 4.8])
    d.h("Learning objectives")
    d.bullets([f"{o['id']}: {o['text']}" for o in spec["objectives"]])
    d.h("Before the session")
    setup = [f"{m['title']}: {m['setup']}" for m in spec["modules"] if m.get("setup")]
    d.bullets(setup or ["No setup notes in the spec."])
    mats = sorted({x for m in spec["modules"] for a in m.get("activities", []) for x in a.get("materials", [])})
    if mats:
        d.h("Materials", 2)
        d.bullets(mats)
    d.h("Run of show")
    d.table(["Time", "Module", "Minutes", "Objectives"],
            [(t, m["title"], m["minutes"], ", ".join(m.get("objectives", [])) or "-") for t, m in clock_rows(spec)],
            widths=[1.2, 3.2, 0.8, 1.6])
    for t, m in clock_rows(spec):
        d.h(f"{m['title']} ({m['minutes']} min{', ' + t if t else ''})", 2)
        if m.get("talk_track"):
            d.p(m["talk_track"], bold_lead="Talk track:")
        if m.get("key_points"):
            d.p("", bold_lead="Key points and sources:")
            d.bullets([f"{k['text']} {cite.short(k.get('sources', []))}".strip() for k in m["key_points"]])
        if m.get("setup"):
            d.p(m["setup"], bold_lead="Setup:")
        if m.get("fallback"):
            d.p(m["fallback"], bold_lead="If something fails:")
        for a in m.get("activities", []):
            kind = "Exercise" if a.get("kind") == "exercise" else "Discussion"
            d.h(f"{kind}: {a['title']} ({a['timebox']} min)", 3)
            d.p(a.get("objective", ""), bold_lead="Objective:")
            d.p("", bold_lead="Instructions:")
            d.bullets(a.get("instructions", []), numbered=True)
            d.p(", ".join(a.get("materials", [])) or "-", bold_lead="Materials:")
            d.p(a.get("expected_output", ""), bold_lead="Expected output:")
            d.p("", bold_lead="Debrief questions:")
            d.bullets(a.get("debrief", []))
            d.p(a.get("fallback", ""), bold_lead="Fallback:")
            if a.get("sources"):
                d.p(cite.short(a["sources"]), bold_lead="Grounded in:")
        d.p(f"Timing: {m['minutes']} minutes.", italic=True)
    d.h("Gaps in the sources")
    d.bullets(spec.get("gaps") or ["None recorded."])
    d.h("Sources")
    d.bullets([f"[{s['id']}] {s.get('title', '')}. {s.get('location', '')}" for s in spec.get("sources", [])])
    return [d.save(os.path.join(out_dir, "facilitator-guide.docx"))]


def build_workbook(spec, cite, brand, out_dir):
    d = Doc(brand)
    d.d.add_heading(f"Participant workbook: {spec['title']}", 0)
    d.h("Executive summary")
    d.p(spec["executive_summary"])
    d.h("What you will be able to do")
    d.bullets([o["text"] for o in spec["objectives"]], numbered=True)
    d.h("Agenda")
    d.table(["Time", "Module", "Minutes"], [(t, m["title"], m["minutes"]) for t, m in clock_rows(spec)],
            widths=[1.3, 4.0, 1.0])
    n = 0
    for m in spec["modules"]:
        for a in m.get("activities", []):
            if a.get("kind") != "exercise":
                continue
            n += 1
            d.d.add_page_break()
            d.h(f"Exercise sheet {n}: {a['title']}")
            d.p(f"{a['timebox']} minutes", bold_lead="Timebox:")
            d.p(a.get("objective", ""), bold_lead="Goal:")
            d.p("", bold_lead="Steps:")
            d.bullets(a.get("instructions", []), numbered=True)
            d.p(", ".join(a.get("materials", [])) or "-", bold_lead="You need:")
            d.p(a.get("expected_output", ""), bold_lead="You produce:")
            if a.get("sources"):
                d.p(cite.short(a["sources"]), bold_lead="Grounded in:")
            d.h("Your work", 3)
            d.lines(8)
            d.h("Reflect", 3)
            for q in a.get("debrief", []):
                d.p(q)
                d.lines(2)
    if n == 0:
        d.h("Notes")
        d.lines(10)
    d.h("Sources")
    d.bullets([f"[{s['id']}] {s.get('title', '')}" for s in spec.get("sources", [])])
    return [d.save(os.path.join(out_dir, "participant-workbook.docx"))]


def build_preread(spec, cite, brand, out_dir):
    pr = spec.get("pre_read")
    if not pr:
        return []
    d = Doc(brand)
    d.d.add_heading(f"Before the session: {spec['title']}", 0)
    d.h("Executive summary")
    d.p(pr.get("summary", ""))
    if pr.get("minutes"):
        d.p(f"About {pr['minutes']} minutes.", bold_lead="Time needed:")
    d.h("What to do")
    d.bullets([f"{i['text']} {cite.short(i.get('sources', []))}".strip() for i in pr.get("items", [])], numbered=True)
    d.h("Session details")
    d.table(["Item", "Detail"], details(spec), widths=[1.6, 4.8])
    return [d.save(os.path.join(out_dir, "pre-read.docx"))]


def build_survey(spec, cite, brand, out_dir):
    sv = spec.get("survey")
    if not sv:
        return []
    d = Doc(brand)
    d.d.add_heading(f"Feedback: {spec['title']}", 0)
    d.h("Executive summary")
    d.p("Tell us what worked and what to change. The survey takes about five minutes and is anonymous unless you add your name.")
    for i, q in enumerate(sv.get("questions", []), 1):
        d.h(f"{i}. {q['text']}", 3)
        if q.get("type") == "scale":
            d.p("1 = not at all   2   3   4   5 = completely   (circle one)")
        else:
            d.lines(3)
    return [d.save(os.path.join(out_dir, "feedback-survey.docx"))]


def build_email(spec, out_dir):
    em = spec.get("follow_up_email")
    if not em:
        return []
    lines = ["DRAFT. Not sent. Review, then send it yourself.", "",
             f"Subject: {em.get('subject', spec['title'])}", "", "Hello everyone,", "", em.get("summary", ""), ""]
    lines += [f"- {p}" for p in em.get("points", [])]
    lines += ["", "Attached: the slide deck and the participant workbook.", "", "Thank you,", em.get("sign_off", "The facilitation team")]
    path = os.path.join(out_dir, "follow-up-email-draft.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return [path]


def _css_string(value):
    # HTML parses style end tags before CSS, so escape markup as well as CSS syntax.
    return '"' + re.sub(r"[^a-zA-Z0-9 _-]", lambda m: f"\\{ord(m[0]):x} ", value) + '"'


def build_html(spec, cite, brand, out_dir):
    b = brand or NEUTRAL
    c = {**NEUTRAL["colors"], **b.get("colors", {})}
    f = {**NEUTRAL["fonts"], **b.get("fonts", {})}
    for name, value in c.items():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"invalid HTML brand color {name}: expected #RRGGBB")
    header_text = max(("#000000", "#FFFFFF"), key=lambda fg: contrast(fg, c["dk2"]))
    chip_text = max(("#000000", "#FFFFFF"), key=lambda fg: contrast(fg, c["accent1"]))
    f = {name: _css_string(value) for name, value in f.items()}
    e = html.escape
    rows = "".join(f"<tr><td>{e(t)}</td><td>{e(m['title'])}</td><td>{m['minutes']} min</td></tr>"
                   for t, m in clock_rows(spec))
    objs = "".join(f"<li>{e(o['text'])}</li>" for o in spec["objectives"])
    mods = ""
    for m in spec["modules"]:
        if m.get("type") == "break":
            continue
        kps = "".join(f"<li>{e(k['text'])} <span class='src'>{e(cite.short(k.get('sources', [])))}</span></li>"
                      for k in m.get("key_points", []))
        acts = "".join(f"<p class='act'><b>{e(a['title'])}</b> ({a['timebox']} min): {e(a.get('objective', ''))}</p>"
                       for a in m.get("activities", []))
        mods += f"<section><h3>{e(m['title'])} <span class='chip'>{m['minutes']} min</span></h3><ul>{kps}</ul>{acts}</section>"
    srcs = "".join(f"<li>[{e(s['id'])}] {e(s.get('title', ''))}</li>" for s in spec.get("sources", []))
    page = f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(spec['title'])}</title>
<style>
body{{font-family:{f['minor']},system-ui,sans-serif;color:{c['dk1']};margin:0;line-height:1.5}}
header{{background:{c['dk2']};color:{header_text};padding:48px 8vw}} header h1{{margin:0 0 8px;font-family:{f['major']},system-ui,sans-serif}}
main{{padding:24px 8vw;max-width:960px}} h2{{color:{c['dk2']};border-bottom:3px solid {c['accent1']};padding-bottom:4px}}
table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid #d5dbe3;padding:8px;text-align:left}}
.chip{{background:{c['accent1']};color:{chip_text};border-radius:12px;padding:2px 10px;font-size:.8em}}
.src{{color:#5b6573;font-size:.85em}} section{{background:{c.get('lt2', '#F1F4F8')};padding:12px 20px;margin:12px 0;border-radius:8px}}
@media print{{header{{background:none;color:{c['dk2']}}}}}
</style></head><body>
<header><h1>{e(spec['title'])}</h1><p>{e(spec.get('subtitle', ''))}</p></header>
<main><h2>Executive summary</h2><p>{e(spec['executive_summary'])}</p>
<h2>Agenda</h2><table><tr><th>Time</th><th>Module</th><th>Length</th></tr>{rows}</table>
<h2>What you will be able to do</h2><ol>{objs}</ol>
<h2>Modules</h2>{mods}
<h2>Sources</h2><ul>{srcs}</ul></main></body></html>
"""
    path = os.path.join(out_dir, "workshop.html")
    open(path, "w", encoding="utf-8").write(page)
    return [path]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--source-map")
    ap.add_argument("--brand")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--only", help="comma list: agenda,guide,workbook,preread,survey,email,html")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    smap = json.load(open(a.source_map, encoding="utf-8")) if a.source_map else None
    brand = json.load(open(a.brand, encoding="utf-8")) if a.brand else None
    os.makedirs(a.out_dir, exist_ok=True)
    cite = Cite(spec, smap)
    want = set((a.only or "agenda,guide,workbook,preread,survey,email" + (",html" if a.html else "")).split(","))
    out = []
    if "agenda" in want:
        out += build_agenda(spec, cite, brand, a.out_dir)
    if "guide" in want:
        out += build_guide(spec, cite, brand, a.out_dir)
    if "workbook" in want:
        out += build_workbook(spec, cite, brand, a.out_dir)
    if "preread" in want:
        out += build_preread(spec, cite, brand, a.out_dir)
    if "survey" in want:
        out += build_survey(spec, cite, brand, a.out_dir)
    if "email" in want:
        out += build_email(spec, a.out_dir)
    if "html" in want:
        out += build_html(spec, cite, brand, a.out_dir)
    print(json.dumps({"written": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
