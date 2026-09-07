#!/usr/bin/env python3
"""Render a snapshot into a single self-contained HTML report.

Combines the capability report and the Python library inventory into one
themed, dependency-free HTML file you can open in any browser or share.

    python generate_html_report.py snapshot.json --out report.html

The output inlines all CSS and JS (no external assets) and adapts to light
or dark automatically; force a mode with `?theme=dark` in the URL.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict

THEME_SCRIPT = """<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("theme");
    const theme = param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>"""

CSS = """
:root{color-scheme:light;--cp-bg:#f7f4ef;--cp-bg-elevated:#fcfbf8;--cp-surface:#ffffff;--cp-surface-soft:#f5f5f5;--cp-border:#dedede;--cp-border-strong:#919191;--cp-text:#242424;--cp-text-muted:#5c5c5c;--cp-text-soft:#6f6f6f;--cp-accent:#b11f4b;--cp-accent-hover:#9a1a41;--cp-accent-soft:rgba(177,31,75,0.08);--cp-accent-fg:#ffffff;--cp-success:#16a34a;--cp-danger:#dc2626;--cp-warning:#f59e0b;--cp-link:#0078d4;--cp-shadow:0 18px 48px rgba(0,0,0,0.12);--cp-highlight:rgba(177,31,75,0.12);}
html[data-theme="dark"]{color-scheme:dark;--cp-bg:#3d3b3a;--cp-bg-elevated:#343231;--cp-surface:#292929;--cp-surface-soft:#2e2e2e;--cp-border:#474747;--cp-border-strong:#5f5f5f;--cp-text:#dedede;--cp-text-muted:#919191;--cp-text-soft:#b0b0b0;--cp-accent:#fd8ea1;--cp-accent-hover:#fb7b91;--cp-accent-soft:rgba(253,142,161,0.14);--cp-accent-fg:#1a1a1a;--cp-success:#4ade80;--cp-danger:#f87171;--cp-warning:#fbbf24;--cp-link:#4da6ff;--cp-shadow:0 18px 48px rgba(0,0,0,0.32);--cp-highlight:rgba(253,142,161,0.12);}
*{box-sizing:border-box}
body{margin:0;background:var(--cp-bg);color:var(--cp-text);font-family:"Segoe UI",Aptos,Calibri,-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.5;}
.wrap{max-width:1100px;margin:0 auto;padding:2rem 1.25rem 4rem;}
header.hero{background:var(--cp-surface);border:1px solid var(--cp-border);border-radius:16px;padding:1.75rem 2rem;box-shadow:0 0 2px rgba(0,0,0,0.12),0 1px 2px rgba(0,0,0,0.14);}
h1{margin:0 0 .35rem;font-size:1.6rem;}
h2{margin:2.25rem 0 .9rem;font-size:1.2rem;border-bottom:2px solid var(--cp-accent-soft);padding-bottom:.35rem;}
.sub{color:var(--cp-text-muted);font-size:.92rem;}
.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;margin-top:1rem;font-size:.9rem;}
.meta div{color:var(--cp-text-muted);} .meta b{color:var(--cp-text);font-weight:600;}
code{font-family:Consolas,"Courier New",Courier,monospace;background:var(--cp-surface-soft);border:1px solid var(--cp-border);border-radius:6px;padding:.05rem .35rem;font-size:.85em;}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-top:1.5rem;}
.card{background:var(--cp-surface);border:1px solid var(--cp-border);border-radius:16px;padding:1.1rem 1.25rem;box-shadow:0 0 2px rgba(0,0,0,0.12),0 1px 2px rgba(0,0,0,0.14);}
.card .num{font-size:1.9rem;font-weight:700;color:var(--cp-accent);line-height:1;}
.card .lbl{color:var(--cp-text-muted);font-size:.82rem;margin-top:.35rem;text-transform:uppercase;letter-spacing:.03em;}
table{width:100%;border-collapse:collapse;background:var(--cp-surface);border:1px solid var(--cp-border);border-radius:12px;overflow:hidden;margin-top:.5rem;}
th,td{text-align:left;padding:.55rem .8rem;border-bottom:1px solid var(--cp-border);font-size:.9rem;vertical-align:top;}
th{background:var(--cp-surface-soft);color:var(--cp-text-soft);font-weight:600;text-transform:uppercase;font-size:.72rem;letter-spacing:.04em;}
tr:last-child td{border-bottom:none;}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;}
a{color:var(--cp-link);text-decoration:none;} a:hover{text-decoration:underline;}
.pill{display:inline-block;padding:.1rem .55rem;border-radius:999px;font-size:.75rem;font-weight:600;border:1px solid transparent;}
.pill.available{color:var(--cp-success);background:color-mix(in srgb,var(--cp-success) 12%,transparent);border-color:color-mix(in srgb,var(--cp-success) 30%,transparent);}
.pill.unverified,.pill.unknown,.pill.notvisible{color:var(--cp-warning);background:color-mix(in srgb,var(--cp-warning) 14%,transparent);border-color:color-mix(in srgb,var(--cp-warning) 32%,transparent);}
.pill.restricted{color:var(--cp-danger);background:color-mix(in srgb,var(--cp-danger) 12%,transparent);border-color:color-mix(in srgb,var(--cp-danger) 30%,transparent);}
.group-title{margin:1.4rem 0 .4rem;font-weight:600;color:var(--cp-accent);font-size:1rem;}
details{margin-top:.5rem;} summary{cursor:pointer;color:var(--cp-text-soft);font-size:.9rem;}
.foot{margin-top:3rem;color:var(--cp-text-muted);font-size:.8rem;text-align:center;}
.chip-row{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem;}
.chip{background:var(--cp-surface);border:1px solid var(--cp-border);border-radius:8px;padding:.2rem .55rem;font-size:.8rem;font-family:Consolas,monospace;}
"""


def esc(v) -> str:
    return html.escape(str(v)) if v is not None else ""


def _pill(status) -> str:
    cls = str(status).replace("-", "")
    return f'<span class="pill {cls}">{esc(status)}</span>'


def render(snapshot: dict) -> str:
    s = snapshot
    rt = s.get("runtime", {})
    summ = s.get("summary", {})
    caps = s.get("capabilities", []) or []
    libs = s.get("pythonLibraries", []) or []

    def by_prefix(pfx: str) -> list[str]:
        return sorted(
            c["id"].split(":", 1)[1]
            for c in caps
            if str(c.get("id", "")).startswith(pfx)
        )

    tools = by_prefix("tool:")
    skills = by_prefix("skill:")
    mcp_servers = by_prefix("mcp.server:")
    mcp_tools = by_prefix("mcp.tool:")
    runtime_caps = sorted(
        (
            c
            for c in caps
            if str(c.get("id", "")).startswith("runtime.")
            or c.get("id") == "python.runtime"
        ),
        key=lambda c: c["id"],
    )

    cataloged = [l for l in libs if l.get("catalogStatus") != "uncataloged"]
    uncat = sorted(
        (l for l in libs if l.get("catalogStatus") == "uncataloged"),
        key=lambda l: l.get("name", "").lower(),
    )
    by_cat: dict[str, list] = defaultdict(list)
    for l in cataloged:
        by_cat[l.get("category", "Uncategorized")].append(l)

    p: list[str] = []
    p.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    p.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    p.append("<title>Agent Harness Capability Report</title>")
    p.append(THEME_SCRIPT)
    p.append(f"<style>{CSS}</style></head><body><div class='wrap'>")

    p.append("<header class='hero'>")
    p.append("<h1>Agent Harness Capability Report</h1>")
    p.append(
        "<div class='sub'>Observed capabilities of the current agent harness "
        "&mdash; generated by <code>agent-harness-explorer</code>.</div>"
    )
    p.append("<div class='meta'>")
    for label, val in [
        ("Observed", s.get("capturedAt")),
        ("Python", rt.get("pythonVersion")),
        ("Platform", rt.get("platform")),
        ("Skill", s.get("skillVersion")),
        ("Probe suite", s.get("probeSuiteVersion")),
        ("Catalog", s.get("catalogVersion")),
    ]:
        p.append(f"<div>{esc(label)}: <b>{esc(val)}</b></div>")
    p.append("</div>")
    p.append(
        f"<div class='meta'><div>Fingerprint: <code>{esc(s.get('fingerprint'))}</code></div></div>"
    )
    p.append("</header>")

    p.append("<div class='cards'>")
    for lbl, key in [
        ("Python libraries", "libraries"),
        ("Uncataloged", "uncataloged"),
        ("Available caps", "available"),
        ("Tools/Skills/MCP", "visible"),
        ("Restricted", "restricted"),
        ("Unknown/unverified", "unknown"),
    ]:
        p.append(
            f"<div class='card'><div class='num'>{esc(summ.get(key, 0))}</div>"
            f"<div class='lbl'>{esc(lbl)}</div></div>"
        )
    p.append("</div>")

    p.append("<h2>Runtime &amp; environment</h2>")
    p.append(
        "<table><thead><tr><th>Capability</th><th>Status</th><th>Value</th></tr></thead><tbody>"
    )
    for c in runtime_caps:
        val = c.get("value")
        val = "" if val is None else val
        p.append(
            f"<tr><td><code>{esc(c.get('id'))}</code></td>"
            f"<td>{_pill(c.get('status'))}</td><td>{esc(val)}</td></tr>"
        )
    p.append("</tbody></table>")

    def chip_block(title: str, items: list[str]) -> None:
        p.append(
            f"<div class='group-title'>{esc(title)} <span class='sub'>({len(items)})</span></div>"
        )
        if not items:
            p.append("<div class='sub'>None observed.</div>")
            return
        p.append("<div class='chip-row'>")
        for it in items:
            p.append(f"<span class='chip'>{esc(it)}</span>")
        p.append("</div>")

    p.append("<h2>Tools, skills &amp; MCP</h2>")
    p.append(
        "<div class='sub'>Enumerated from the agent's own context. Absent items are "
        "recorded as <code>not-visible</code>, never unsupported.</div>"
    )
    chip_block("Built-in tools", tools)
    chip_block("Agent skills", skills)
    chip_block("MCP servers", mcp_servers)
    chip_block("MCP tools", mcp_tools)

    p.append("<h2>Python library inventory</h2>")
    p.append(
        f"<div class='sub'>{len(libs)} discovered &mdash; {len(cataloged)} cataloged, "
        f"{len(uncat)} new.</div>"
    )
    for cat in sorted(by_cat):
        p.append(f"<div class='group-title'>{esc(cat)}</div>")
        p.append(
            "<table><thead><tr><th>Library</th><th class='num'>Version</th>"
            "<th>Description</th><th>Docs</th></tr></thead><tbody>"
        )
        for l in sorted(by_cat[cat], key=lambda x: x.get("name", "").lower()):
            doc = l.get("documentationUrl", "")
            doc_cell = (
                f"<a href='{esc(doc)}' target='_blank' rel='noopener'>Documentation</a>"
                if doc
                else "&mdash;"
            )
            p.append(
                f"<tr><td><b>{esc(l.get('name'))}</b></td>"
                f"<td class='num'>{esc(l.get('version'))}</td>"
                f"<td>{esc(l.get('description'))}</td><td>{doc_cell}</td></tr>"
            )
        p.append("</tbody></table>")

    p.append(f"<div class='group-title'>New packages ({len(uncat)})</div>")
    described = sum(
        1 for l in uncat if l.get("descriptionSource") == "package-metadata"
    )
    p.append(
        "<details open><summary>These packages are not yet in the "
        "agent-harness-explorer skill&rsquo;s curated catalog. Descriptions below "
        "are read from each package&rsquo;s installed metadata "
        f"({described} of {len(uncat)} self-described).</summary>"
    )
    p.append(
        "<table style='margin-top:.8rem'><thead><tr><th>Library</th>"
        "<th class='num'>Version</th><th>Description</th><th>Docs</th>"
        "</tr></thead><tbody>"
    )
    for l in sorted(uncat, key=lambda x: x.get("name", "").lower()):
        doc = l.get("documentationUrl", "")
        doc_cell = (
            f"<a href='{esc(doc)}' target='_blank' rel='noopener'>Link</a>"
            if doc
            else "&mdash;"
        )
        desc = esc(l.get("description")) or "<span class='sub'>&mdash;</span>"
        p.append(
            f"<tr><td><b>{esc(l.get('name'))}</b></td>"
            f"<td class='num'>{esc(l.get('version'))}</td>"
            f"<td>{desc}</td><td>{doc_cell}</td></tr>"
        )
    p.append("</tbody></table></details>")

    warnings = s.get("warnings", []) or []
    if warnings:
        p.append("<h2>Warnings</h2><ul>")
        for w in warnings:
            p.append(f"<li class='sub'>{esc(w)}</li>")
        p.append("</ul>")

    p.append(
        f"<div class='foot'>Snapshot <code>{esc(s.get('snapshotId'))}</code> "
        "&middot; generated by agent-harness-explorer</div>"
    )
    p.append("</div></body></html>")
    return "".join(p)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render a snapshot as HTML.")
    parser.add_argument("snapshot")
    parser.add_argument("--out")
    args = parser.parse_args(argv[1:])

    with open(args.snapshot, encoding="utf-8") as fh:
        snapshot = json.load(fh)
    doc = render(snapshot)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(doc)
        print(f"Wrote HTML report to {args.out}")
    else:
        sys.stdout.write(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
