#!/usr/bin/env python3
"""Quality gate for a SharePoint HTML page: static checks plus headless-browser checks.

Static checks (always run, no browser needed)
  * leftover {{PLACEHOLDER}} tokens, empty or "#" links, images without alt text
  * static mode: exactly one <style> element and no <script>, except the list view runtime
    and its JSON blocks when the page has list view sections (build_list_view.py)
  * list view sections: each lv-config source matches a ka-livedata-manifest entry, allowlist present
  * live mode: manifest and page config present and in agreement, allowlist markers present
  * SharePoint folder links that are not AllItems.aspx?id= links (they land at the library root)
  * links without target="_top" (static mode) or "_blank" (live list links)
  * em dashes in visible text (house style), duplicate ids

Browser checks (Playwright for Python, if installed)
  * screenshots at each width (default 1440 and 390) in light and dark mode
  * horizontal overflow and elements that stick out of the viewport
  * WCAG AA text contrast on solid backgrounds (text on gradients or images is listed as "unverified")
  * live mode and list views: --sample-data injects window.__LD_RESULTS__ so the items render as on
    SharePoint; every [data-list-view] section and the live gallery must reach data-state="ready"

If Playwright is missing, the script runs the static checks, exits 2 and prints the
steps to do the same review with a browser tool.

Usage
  python visual_check.py page.html --out shots/ [--mode static|live] [--sample-data rows.json]
                         [--sample-data <view-key>=rows.json ...]
                         [--widths 1440 390] [--list-links]
Exit codes: 0 clean, 1 issues found, 2 browser checks skipped (static checks still reported)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.imgs, self.ids, self.styles, self.scripts = [], [], [], 0, []
        self.text, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a":
            self.links.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "style":
            self.styles += 1
            self._skip += 1
        elif tag == "script":
            self.scripts.append(a)
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def static_checks(html: str, mode: str) -> list[dict]:
    s = Scan()
    s.feed(html)
    issues = []

    def add(sev, check, detail):
        issues.append({"severity": sev, "check": check, "detail": detail})

    for tok in sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", html))):
        add("error", "placeholder", f"unfilled placeholder {tok}")
    dups = sorted({i for i in s.ids if s.ids.count(i) > 1})
    if dups:
        add("error", "duplicate-id", ", ".join(dups))
    for img in s.imgs:
        if "alt" not in img:
            add("error", "img-alt", img.get("src", "")[:80])
    visible = " ".join(s.text)
    if "\u2014" in visible:
        add("warn", "em-dash", "visible text contains an em dash; rewrite with a comma, colon or period")
    nav_allow = re.search(r'<nav id="link-allowlist".*?</nav>', html, re.S)
    allow_hrefs = set(re.findall(r'href="([^"]+)"', nav_allow.group(0))) if nav_allow else set()
    for a in s.links:
        href = a.get("href")
        if href is None or href.strip() in ("", "#"):
            add("error", "empty-link", str(a)[:120])
            continue
        if href in allow_hrefs:
            continue
        u = urlsplit(href)
        if u.netloc.endswith(".sharepoint.com") and ("/Shared%20Documents/" in u.path or "/Shared Documents/" in u.path) \
                and not u.path.lower().endswith("/forms/allitems.aspx") and "." not in u.path.rsplit("/", 1)[-1]:
            add("error", "folder-link", f"{href} points at the folder URL; use AllItems.aspx?id= (build_folder_links.py)")
        if mode == "static" and u.scheme in ("http", "https") and a.get("target") != "_top":
            add("warn", "target", f'{href[:90]} has no target="_top"; it may open inside the page frame')
    views = [(k, b) for k, b in re.findall(r'<!-- list-view:([a-z][a-z0-9-]*):start -->(.*?)<!-- list-view:\1:end -->', html, re.S)
             if 'data-list-view="' in b]  # static snapshot sections (no data-list-view) need no binding
    manifest = []
    mm = re.search(r'<script type="application/json" class="ka-livedata-manifest">(.*?)</script>', html, re.S)
    if mm:
        try:
            manifest = json.loads(mm.group(1))
        except ValueError as e:
            add("error", "binding", f"cannot parse ka-livedata-manifest: {e}")
    for key, body in views:
        c = re.search(r'<script type="application/json" class="lv-config">(.*?)</script>', body, re.S)
        try:
            src = (json.loads(c.group(1)) if c else {}).get("source") or {}
        except ValueError as e:
            add("error", "binding", f"list view {key}: cannot parse lv-config: {e}")
            continue
        entry = next((x for x in manifest if isinstance(x, dict) and x.get("spItemUrl") == src.get("spItemUrl")), None)
        if not entry or any(entry.get(k) != src.get(k) for k in ("kind", "spItemUrl", "webUrl", "listId", "label")):
            add("error", "binding", f"list view {key}: lv-config source has no matching ka-livedata-manifest entry")
    if views:
        if 'id="list-view-runtime"' not in html:
            add("error", "list-view-runtime", "list view sections found but no list-view-runtime script")
        if "link-allowlist:start" not in html:
            add("error", "allowlist", "link-allowlist markers missing")
        elif not allow_hrefs:
            add("warn", "allowlist", "allowlist is empty; run allowlist_from_list.py after the list has items")
        add("info", "scripts-required", f"{len(views)} list view(s): the page needs scripts to run; confirm with the script probe")
    if mode == "static":
        if s.styles != 1:
            add("error", "one-style", f"found {s.styles} style elements; static pages use exactly one")
        code = [x for x in s.scripts if x.get("type") != "application/json"]
        allowed = [x for x in code if views and x.get("id") == "list-view-runtime"]
        if len(code) > len(allowed):
            add("error", "no-script", f"found {len(code) - len(allowed)} script elements; static pages use none"
                + (" besides the list view runtime" if views else ""))
    else:
        m = re.search(r'<script type="application/json" class="ka-livedata-manifest">(.*?)</script>', html, re.S)
        c = re.search(r'<script type="application/json" id="site-page-config">(.*?)</script>', html, re.S)
        if not m or not c:
            add("error", "binding", "manifest or site-page-config block missing")
        else:
            try:
                man, cfg = json.loads(m.group(1)), json.loads(c.group(1))
                exp = cfg.get("publicationSource") or {}
                src = next((x for x in man if x.get("spItemUrl") == exp.get("spItemUrl")), None)
                if not src or any(src.get(k) != exp.get(k) for k in ("kind", "spItemUrl", "webUrl", "listId", "label")):
                    add("error", "binding", "manifest and site-page-config.publicationSource disagree")
            except (ValueError, AttributeError) as e:
                add("error", "binding", f"cannot parse binding JSON: {e}")
        if "link-allowlist:start" not in html:
            add("error", "allowlist", "link-allowlist markers missing")
        elif not allow_hrefs:
            add("warn", "allowlist", "allowlist is empty; run allowlist_from_list.py after the list has items")
    return issues


CONTRAST_JS = r"""
() => {
  const lum = c => { const v = c.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
                     return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
                       return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 }; };
  const out = { fails: [], unverified: 0, checked: 0, overflow: [], scrollWidth: document.documentElement.scrollWidth, viewport: innerWidth };
  const W = innerWidth;
  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || r.width === 0) continue;
    if (r.right > W + 1 && cs.position !== "fixed" && !el.closest("[aria-hidden=true]")) {
      let clipped = false;
      for (let p = el.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === "hidden" || o === "clip" || o === "auto") { clipped = true; break; } }
      if (!clipped) out.overflow.push({ tag: el.tagName.toLowerCase(), cls: el.className && String(el.className).slice(0, 40), right: Math.round(r.right) });
    }
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const fg = parse(cs.color); if (!fg) continue;
    if (cs.backgroundClip === "text" || cs.webkitBackgroundClip === "text") continue;
    let bg = null, unverified = false;
    for (let p = el; p; p = p.parentElement) {
      const ps = getComputedStyle(p);
      if (ps.backgroundImage && ps.backgroundImage !== "none") { unverified = true; break; }
      const b = parse(ps.backgroundColor); if (b && b.a >= 0.95) { bg = b.rgb; break; }
      if (b && b.a > 0.05) { unverified = true; break; }
    }
    if (!bg && !unverified) bg = [255, 255, 255];
    if (unverified) { out.unverified++; continue; }
    out.checked++;
    const L1 = lum(fg.rgb), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight, 10) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    if (ratio < need) out.fails.push({ text: el.textContent.trim().slice(0, 50), ratio: Math.round(ratio * 100) / 100, need, color: cs.color, tag: el.tagName.toLowerCase() });
  }
  out.fails = out.fails.slice(0, 25); out.overflow = out.overflow.slice(0, 25);
  return out;
}
"""

FALLBACK_STEPS = """Playwright is not installed, so only static checks ran. Do the visual pass with a browser tool:
  1. Open the local file (or the uploaded preview page) in the browser.
  2. Set the window to 1440 px wide, take a full-page screenshot; repeat at 390 px.
  3. Repeat both in dark mode (OS or browser dark mode; live pages also accept ?theme=dark).
  4. Look for: horizontal scrolling, text running out of cards, misaligned card rows,
     low-contrast text (gray on gray, white on light gradient), and broken images.
  5. Click every link once; folder links must open the folder itself, not the library root.
  6. Fix, then repeat until clean."""


def browser_checks(page: Path, out: Path, widths, sample, mode) -> tuple[list[dict], list[str]]:
    from playwright.sync_api import sync_playwright  # type: ignore
    results, shots = [], []
    init = None
    html = page.read_text(encoding="utf-8")
    has_views = 'data-list-view="' in html
    if sample:
        injected = {}
        for spec in sample:
            key, _, path = spec.rpartition("=") if "=" in spec and not Path(spec).exists() else ("", "", spec)
            if key:
                body = re.search(rf'<!-- list-view:{re.escape(key)}:start -->(.*?)<!-- list-view:', html, re.S)
                m = re.search(r'"spItemUrl"\s*:\s*"([^"]+)"', body.group(1)) if body else None
            else:
                cfg = re.search(r'<script type="application/json" id="site-page-config">(.*?)</script>', html, re.S)
                m = re.search(r'"spItemUrl"\s*:\s*"([^"]+)"', cfg.group(1) if cfg else html)
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if "format" not in payload:
                payload = {"format": "rows", "content": json.dumps(payload)}
            injected[m.group(1) if m else ""] = payload
        init = f"window.__LD_RESULTS__ = {json.dumps(injected)};"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("light", "dark"):
            for w in widths:
                ctx = browser.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme)
                if init:
                    ctx.add_init_script(init)
                pg = ctx.new_page()
                errors = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.goto(page.resolve().as_uri())
                pg.wait_for_timeout(400)
                shot = out / f"{page.stem}-{w}-{scheme}.png"
                pg.screenshot(path=str(shot), full_page=True)
                shots.append(str(shot))
                data = pg.evaluate(CONTRAST_JS)
                if data["scrollWidth"] > data["viewport"] + 1:
                    results.append({"severity": "error", "check": "overflow", "detail": f"{w}px {scheme}: page is {data['scrollWidth']}px wide"})
                for o in data["overflow"][:5]:
                    results.append({"severity": "warn", "check": "overflow-element", "detail": f"{w}px {scheme}: {o}"})
                for f in data["fails"]:
                    results.append({"severity": "error", "check": "contrast", "detail": f"{w}px {scheme}: {f}"})
                for e in errors:
                    results.append({"severity": "error", "check": "js-error", "detail": f"{w}px {scheme}: {e}"})
                if mode == "live" and 'id="gallery"' in html:
                    state = pg.evaluate("() => (document.getElementById('gallery') || {}).dataset?.state || ''")
                    if state != "ready":
                        results.append({"severity": "warn" if not sample else "error", "check": "live-state",
                                        "detail": f"{w}px {scheme}: gallery state '{state}' (pass --sample-data to render cards)"})
                if has_views:
                    states = pg.evaluate("() => [...document.querySelectorAll('[data-list-view]')].map(n => [n.dataset.listView, n.dataset.state])")
                    for key, state in states:
                        if state != "ready":
                            results.append({"severity": "warn" if not sample else "error", "check": "list-view-state",
                                            "detail": f"{w}px {scheme}: list view {key} state '{state}' (pass --sample-data {key}=rows.json)"})
                results.append({"severity": "info", "check": "contrast-coverage",
                                "detail": f"{w}px {scheme}: {data['checked']} text elements checked, {data['unverified']} on gradients or images (review in the screenshot)"})
                ctx.close()
        browser.close()
    return results, shots


def list_links(html: str) -> list[dict]:
    """No network calls: list every link so it can be click-tested in the browser tool."""
    return [{"severity": "info", "check": "click-test", "detail": href}
            for href in sorted(set(re.findall(r'href="(https?://[^"]+)"', html)))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--out", default="visual-check")
    ap.add_argument("--mode", choices=["static", "live", "aspx"], help="default: live if a site-page-config block is present")
    ap.add_argument("--widths", nargs="+", type=int, default=[1440, 390])
    ap.add_argument("--sample-data", nargs="+", help="rows JSON to inject as __LD_RESULTS__: a file for the live gallery, or <view-key>=file per list view")
    ap.add_argument("--list-links", action="store_true", help="list every link for the browser click-test")
    a = ap.parse_args(argv)

    page = Path(a.page)
    html = page.read_text(encoding="utf-8")
    mode = a.mode or ("live" if 'id="site-page-config"' in html else "static")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    issues = static_checks(html, mode) if mode != "aspx" else []
    shots: list[str] = []
    browser = "playwright"
    try:
        more, shots = browser_checks(page, out, a.widths, a.sample_data, mode)
        issues += more
    except ImportError:
        browser = "none"
    if a.list_links:
        issues += list_links(html)
    errors = [i for i in issues if i["severity"] == "error"]
    report = {"page": str(page), "mode": mode, "browser": browser, "screenshots": shots,
              "errors": len(errors), "warnings": sum(i["severity"] == "warn" for i in issues), "issues": issues}
    (out / "visual-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if browser == "none":
        print("\n" + FALLBACK_STEPS, file=sys.stderr)
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
