#!/usr/bin/env python3
"""Regenerate the hidden link allowlist (and optional static snapshot) of a live list page.

The SharePoint HTML viewer only lets a link open when the same address appears
statically in the page. A live list page builds its links at run time, so it
carries a hidden <nav id="link-allowlist"> with a static copy of every link in
the list. Run this whenever list items are added or their links change.

Input (--items): list data in any of these shapes
  * {"headers":[...], "rows":[[...], ...]}            (the live-data "rows" shape)
  * {"value":[{"id":"1","fields":{...}}, ...]}         (Graph list items with fields expanded)
  * [{"ID":1,"Title":...}, ...]                        (plain list of field dicts)

What it does
  * collects every https link from the chosen columns (default: all columns),
    including hyperlink fields ({"Url":...}), HTML anchors and "url, description" text
  * rewrites the block between <!-- link-allowlist:start --> and <!-- link-allowlist:end -->
  * with --snapshot, also writes the data into <script id="snapshot-data"> so the
    page can render a saved copy when live data is not injected

List view sections (scripts/build_list_view.py) on any page
  * pass one items file per list view and the matching section keys with --view, in the same order
  * links are taken only from the columns the view's lv-config maps (link and description), unless --columns is given
  * --snapshot writes each list's rows into that section's lv-snapshot block, keeping only the columns
    the view maps (ID, title, description, link, people, date, filters); sensitive columns never enter it
  * the allowlist is the union of every list's links, so always pass every list view on the page together

Examples
  python allowlist_from_list.py --items items.json --page gallery-preview.html
  python allowlist_from_list.py --items items.json --page gallery-preview.html --snapshot
  python allowlist_from_list.py --items items.json --columns Link --print
  python allowlist_from_list.py --items resources.json events.json --view resources events --page home-preview.html --snapshot
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from urllib.parse import urlsplit

URL_RE = re.compile(r"https://[^\s\"'<>]+")
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)


def to_rows(data) -> tuple[list[str], list[list]]:
    if isinstance(data, dict) and "headers" in data and "rows" in data:
        return list(data["headers"]), [list(r) for r in data["rows"]]
    if isinstance(data, dict) and "format" in data and "content" in data:
        return to_rows(json.loads(data["content"]))
    items = data.get("value", data) if isinstance(data, dict) else data
    dicts = []
    for it in items:
        if isinstance(it, dict) and isinstance(it.get("fields"), dict):
            f = dict(it["fields"])
            f.setdefault("ID", it.get("id") or f.get("id"))
            dicts.append(f)
        elif isinstance(it, dict):
            dicts.append(it)
    headers: list[str] = []
    for d in dicts:
        for k in d:
            if k not in headers and not k.startswith("@odata"):
                headers.append(k)
    rows = []
    for d in dicts:
        rows.append([v if isinstance(v, (str, int, float, bool)) or v is None else json.dumps(v) for v in (d.get(h) for h in headers)])
    return headers, rows


def urls_in(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    text = html.unescape(str(value))
    found = HREF_RE.findall(text) + URL_RE.findall(text)
    out = []
    for u in found:
        u = u.split(", ")[0].rstrip(".,;)")
        try:
            p = urlsplit(u)
        except ValueError:
            continue
        if p.scheme == "https" and p.netloc and not p.username and not p.password:
            out.append(u)
    return out


def collect(headers, rows, columns) -> list[str]:
    idx = [i for i, h in enumerate(headers) if not columns or h in columns]
    seen, out = set(), []
    for r in rows:
        for i in idx:
            if i < len(r):
                for u in urls_in(r[i]):
                    if u not in seen:
                        seen.add(u)
                        out.append(u)
    return out


def nav_block(urls: list[str]) -> str:
    lines = [f'<a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer" tabindex="-1">{html.escape(u)}</a>' for u in urls]
    return ('<!-- link-allowlist:start (static copies of list links so the SharePoint viewer lets them open; '
            'regenerate with scripts/allowlist_from_list.py when list items change) -->\n'
            '<nav id="link-allowlist" hidden aria-hidden="true" style="display:none">\n'
            + "\n".join(lines) + ("\n" if lines else "") +
            '</nav>\n<!-- link-allowlist:end -->')


def view_config(page: str, key: str) -> dict:
    m = re.search(rf'<!-- list-view:{re.escape(key)}:start -->(.*?)<!-- list-view:{re.escape(key)}:end -->', page, re.S)
    if not m:
        raise ValueError(f"no list view section with key {key!r} in the page")
    c = re.search(r'<script type="application/json" class="lv-config">(.*?)</script>', m.group(1), re.S)
    if not c:
        raise ValueError(f"list view {key!r} has no lv-config block")
    return json.loads(c.group(1).replace("<\\/", "</"))


def view_columns(cfg: dict) -> tuple[set[str], set[str]]:
    """(columns the view reads, columns that can hold links), minus anything marked sensitive."""
    cols = cfg.get("columns") or {}
    used = {n for k in ("id", "title", "description", "url", "people", "date") for n in cols.get(k) or []}
    for f in cfg.get("filters") or []:
        used.update(f.get("columns") or [])
    links = set(cols.get("url") or []) | set(cols.get("description") or [])
    sensitive = {s.lower() for s in cfg.get("sensitive") or []}
    keep = lambda names: {n for n in names if n.lower() not in sensitive}
    return keep(used) | {"ID"}, keep(links)


def snapshot_json(headers, rows) -> str:
    snap = {"savedOn": dt.date.today().isoformat(),
            "payload": {"format": "rows", "content": json.dumps({"headers": headers, "rows": rows})}}
    return json.dumps(snap).replace("</", "<\\/")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", required=True, nargs="+", help="list data JSON file(s); one per --view")
    ap.add_argument("--view", nargs="*", default=[], help="list view section keys, same order as --items")
    ap.add_argument("--columns", nargs="*", default=[], help="only take links from these columns")
    ap.add_argument("--page", help="HTML page to update in place")
    ap.add_argument("--snapshot", action="store_true", help="also write the snapshot fallback(s)")
    ap.add_argument("--print", action="store_true", help="print the nav block")
    a = ap.parse_args(argv)

    if a.view and len(a.view) != len(a.items):
        print("--view needs one key per --items file, in the same order.", file=sys.stderr)
        return 2
    if not a.view and len(a.items) > 1:
        print("Several --items files need --view keys (list view sections).", file=sys.stderr)
        return 2
    page = None
    if a.page:
        with open(a.page, encoding="utf-8") as fh:
            page = fh.read()
    elif a.view:
        print("--view needs --page.", file=sys.stderr)
        return 2

    urls: list[str] = []
    result: dict = {"lists": []}
    snapshots: list[tuple[str | None, list, list]] = []
    for n, path in enumerate(a.items):
        with open(path, encoding="utf-8") as fh:
            headers, rows = to_rows(json.load(fh))
        key = a.view[n] if a.view else None
        link_cols = set(a.columns)
        if key:
            try:
                cfg = view_config(page, key)
            except ValueError as e:
                print(str(e), file=sys.stderr)
                return 2
            used, links = view_columns(cfg)
            link_cols = link_cols or links
            keep = [i for i, h in enumerate(headers) if h in used]
            headers, rows = [headers[i] for i in keep], [[r[i] if i < len(r) else None for i in keep] for r in rows]
        found = collect(headers, rows, link_cols)
        urls += [u for u in found if u not in urls]
        result["lists"].append({"view": key, "items": len(rows), "links": len(found)})
        snapshots.append((key, headers, rows))
    block = nav_block(urls)
    result["links"] = len(urls)

    if page is not None:
        page, n = re.subn(r"<!-- link-allowlist:start.*?<!-- link-allowlist:end -->", lambda _m: block, page, count=1, flags=re.S)
        if n != 1:
            print("No link-allowlist:start ... link-allowlist:end markers in the page.", file=sys.stderr)
            return 2
        if a.snapshot:
            for key, headers, rows in snapshots:
                text = snapshot_json(headers, rows)
                if key:
                    pat = rf'(<!-- list-view:{re.escape(key)}:start -->.*?<script type="application/json" class="lv-snapshot">).*?(</script>)'
                else:
                    pat = r'(<script type="application/json" id="snapshot-data">).*?(</script>)'
                page, m = re.subn(pat, lambda mm: mm.group(1) + text + mm.group(2), page, count=1, flags=re.S)
                if m != 1:
                    print(f"No snapshot block for {key or 'the live gallery'} in the page.", file=sys.stderr)
                    return 2
            result["snapshot"] = True
        with open(a.page, "w", encoding="utf-8") as fh:
            fh.write(page)
        result["page"] = a.page
    if a.print or not a.page:
        print(block)
    print(json.dumps(result), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
