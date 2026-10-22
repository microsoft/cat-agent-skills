#!/usr/bin/env python3
"""Render an SAP <-> Power Platform architecture report (self-contained HTML).

Usage:
  python3 render_report.py --spec spec.json --out /app/created
  python3 render_report.py --spec spec.json --out . --name contoso-sap

Standard library only. No JavaScript in the output (works in Teams/Outlook previews).
Each run writes a NEW versioned file (<name>-v1.html, -v2.html, ...) and prints its path.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

CONF_COLORS = {"high": "#107c10", "medium": "#c19c00", "low": "#d13438"}
SEVERITY_COLORS = {"high": "#d13438", "medium": "#c19c00", "low": "#107c10"}
FIT_COLORS = {"recommended": "#107c10", "complementary": "#0f6cbd", "not a fit": "#8a8886"}


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value):
    """Return the URL only if it is an absolute http(s) link; otherwise None (rendered as text)."""
    url = str(value or "").strip()
    # Drop control characters and whitespace that browsers ignore inside schemes ("java\nscript:").
    if not url or re.search(r"[\x00-\x20\x7f]", url):
        return None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return None
    return url


def source_item(s):
    title = s.get("title") or s.get("url")
    url = safe_url(s.get("url"))
    if url:
        return '<li><a href="%s">%s</a></li>' % (esc(url), esc(title))
    raw = str(s.get("url") or "").strip()
    suffix = " (%s)" % esc(raw) if raw and raw != str(title) else ""
    return "<li>%s%s</li>" % (esc(title), suffix)


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return (s or "sap-integration-architecture")[:60].rstrip("-")


def next_path(out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while (out_dir / ("%s-v%d.html" % (name, n))).exists():
        n += 1
    return out_dir / ("%s-v%d.html" % (name, n))


def wrap(label, width):
    words, lines, cur = str(label).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:3] or [""]


def svg_chain(labels, color):
    """Horizontal chain of boxes with arrows; wraps to a second row after 4 boxes."""
    labels = [str(x) for x in labels][:7]
    if len(labels) < 2:
        return ""
    box_w, box_h, gap, per_row = 170, 64, 40, 4
    rows = (len(labels) + per_row - 1) // per_row
    width = per_row * box_w + (per_row - 1) * gap + 20
    height = rows * box_h + (rows - 1) * 50 + 20
    parts = ['<svg role="img" viewBox="0 0 %d %d" width="100%%" xmlns="http://www.w3.org/2000/svg">' % (width, height),
             '<defs><marker id="a%s" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#605e5c"/></marker></defs>' % color[1:]]
    pos = []
    for i, label in enumerate(labels):
        r, c = divmod(i, per_row)
        x, y = 10 + c * (box_w + gap), 10 + r * (box_h + 50)
        pos.append((x, y))
        parts.append('<rect x="%d" y="%d" rx="10" width="%d" height="%d" fill="#fff" stroke="%s" stroke-width="2"/>'
                     % (x, y, box_w, box_h, color))
        lines = wrap(label, 20)
        start = y + box_h / 2 - (len(lines) - 1) * 8 + 5
        for j, line in enumerate(lines):
            parts.append('<text x="%d" y="%.0f" text-anchor="middle" font-size="13" fill="#201f1e">%s</text>'
                         % (x + box_w / 2, start + j * 16, esc(line)))
    for i in range(len(pos) - 1):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if y1 == y2:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#605e5c" stroke-width="2" marker-end="url(#a%s)"/>'
                         % (x1 + box_w, y1 + box_h / 2, x2 - 4, y2 + box_h / 2, color[1:]))
        else:
            parts.append('<path d="M%d %d V%d H%d V%d" fill="none" stroke="#605e5c" stroke-width="2" marker-end="url(#a%s)"/>'
                         % (x1 + box_w / 2, y1 + box_h, y1 + box_h + 25, x2 + box_w / 2, y2 - 4, color[1:]))
    parts.append("</svg>")
    return "".join(parts)


def table(headers, rows):
    if not rows:
        return ""
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (head, body)


def badge(level, colors=CONF_COLORS):
    level = str(level or "").lower()
    return '<span class="badge" style="background:%s">%s</span>' % (colors.get(level, "#605e5c"), esc(level or "n/a"))


def section(title, inner):
    return '<section><h2>%s</h2>%s</section>' % (esc(title), inner) if inner else ""


def ul(items):
    items = [i for i in (items or []) if str(i).strip()]
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(i) for i in items) if items else ""


def render(spec):
    rec = spec.get("recommendation") or {}
    ver = spec.get("verification") or {}
    mode = ver.get("mode", "baseline")
    ver_text = ("Checked on Microsoft Learn %s" if mode == "live" else "Baseline guidance %s (not re-checked)") % ver.get("date", "")

    facts = table(["Topic", "Value", "Source"],
                  [[esc(f.get("topic")), esc(f.get("value")),
                    '<span class="src %s">%s</span>' % ("assume" if "assum" in str(f.get("source", "")).lower() else "",
                                                         esc(f.get("source", "")))]
                   for f in spec.get("facts", [])])
    alts = table(["Pattern", "Better when"],
                 [["<b>%s</b>" % esc(a.get("name")), esc(a.get("when"))]
                  for a in spec.get("alternatives", [])])
    prereq = table(["Role", "Prerequisite"],
                   [[esc(p.get("role")), esc(p.get("item"))] for p in spec.get("prerequisites", [])])
    risks = table(["Risk", "Severity", "Mitigation"],
                  [[esc(r.get("risk")), badge(r.get("severity"), SEVERITY_COLORS), esc(r.get("mitigation"))]
                   for r in spec.get("risks", [])])
    steps = "".join("<h3>%s</h3>%s" % (esc(s.get("phase")), ul(s.get("items")))
                    for s in spec.get("steps", []))
    sources = "<ol>%s</ol>" % "".join(source_item(s) for s in spec.get("sources", [])) if spec.get("sources") else ""
    diagrams = ""
    if spec.get("flow"):
        diagrams += "<h3>Data flow</h3>" + svg_chain(spec["flow"], "#0f6cbd")
    if spec.get("identity_flow"):
        diagrams += "<h3>Identity flow</h3>" + svg_chain(spec["identity_flow"], "#8764b8")

    rec_html = ""
    if rec:
        rec_html = ('<div class="rec"><div class="rec-head"><span class="pname">%s</span>%s</div>'
                    '%s<p><b>Identity:</b> %s</p></div>'
                    % (esc(rec.get("name")), badge(rec.get("confidence")),
                       ul(rec.get("why")), esc(rec.get("identity", "—"))))

    positioning = ""
    for block in spec.get("positioning", []) or []:
        rows = [["<b>%s</b>" % esc(o.get("name")),
                 badge(o.get("fit"), FIT_COLORS), esc(o.get("why"))]
                for o in block.get("options", [])]
        positioning += "<h3>%s</h3>%s" % (esc(block.get("question", "")), table(["Option", "Fit", "Why"], rows))
        if block.get("together"):
            positioning += "<p><b>How they work together</b></p>" + ul(block.get("together"))

    css = """
body{font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;color:#201f1e;margin:0;background:#f5f5f5}
main{max-width:1040px;margin:0 auto;background:#fff;padding:32px 40px 48px}
header{border-bottom:4px solid #0f6cbd;margin-bottom:24px;padding-bottom:12px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;color:#0f6cbd;margin:28px 0 10px}h3{font-size:15px;margin:16px 0 6px}
.meta{color:#605e5c;font-size:13px}.summary{font-size:16px;background:#eff6fc;border-left:4px solid #0f6cbd;padding:12px 16px}
.rec{border:1px solid #c7e0f4;border-radius:10px;padding:14px 18px;background:#fafcff}
.rec-head{display:flex;gap:10px;align-items:center;font-size:18px;margin-bottom:6px}
.pname{font-weight:600}
.badge{color:#fff;border-radius:10px;padding:1px 9px;font-size:12px;text-transform:uppercase}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #e1dfdd;padding:7px 9px;text-align:left;vertical-align:top}
th{background:#f3f2f1}.src{font-size:12px;color:#605e5c}.src.assume{color:#a4262c;font-weight:600}
footer{margin-top:32px;font-size:12px;color:#605e5c;border-top:1px solid #e1dfdd;padding-top:10px}
a{color:#0f6cbd}@media print{body{background:#fff}main{padding:0}}
"""
    notes = ul(ver.get("notes"))
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head>
<body><main><header><h1>%s</h1><div class="meta">%s · %s · %s</div></header>
%s%s%s%s%s%s%s%s%s%s%s%s
<footer>Generated by the SAP–Power Platform Integration Architect skill. Architecture guidance only — not licensing, pricing or legal advice.
Confirm SAP API usage and licensing with your SAP and Microsoft account teams. Validate every step with your SAP Basis, security and Power Platform admins.</footer>
</main></body></html>""" % (
        esc(spec.get("title")), css, esc(spec.get("title")),
        esc(spec.get("subtitle", "SAP + Microsoft architecture advice")), esc(spec.get("date", "")), esc(ver_text),
        '<p class="summary">%s</p>' % esc(spec["summary"]) if spec.get("summary") else "",
        section("Positioning", positioning),
        section("Recommendation", rec_html),
        section("Architecture", diagrams),
        section("Facts and assumptions", facts),
        section("Alternatives", alts),
        section("Prerequisites by role", prereq),
        section("Implementation steps", steps),
        section("Risks", risks),
        section("Open questions", ul(spec.get("open_questions"))),
        section("Currency check", notes),
        section("Sources", sources),
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, help="path to the JSON spec")
    ap.add_argument("--out", default=".", help="output folder (host file-output dir)")
    ap.add_argument("--name", help="base file name (default: from title)")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
    except Exception as e:
        print("ERROR: cannot read spec: %s" % e, file=sys.stderr)
        return 2
    if not spec.get("title") or not (spec.get("recommendation") or spec.get("positioning")):
        print("ERROR: spec needs 'title' and at least one of 'recommendation' or 'positioning'", file=sys.stderr)
        return 2
    path = next_path(Path(a.out), slug(a.name or spec["title"]))
    path.write_text(render(spec), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
