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
  * collects every https link from the explicitly approved gallery columns,
    including hyperlink fields ({"Url":...}), HTML anchors and "url, description" text
  * rewrites the block between <!-- link-allowlist:start --> and <!-- link-allowlist:end -->
  * with --snapshot, also writes the data into <script id="snapshot-data"> so the
    page can render a saved copy when live data is not injected; without it,
    clears previous saved rows so earlier publication approvals cannot linger

List view sections (scripts/build_list_view.py) on any page
  * pass one items file per list view and the matching section keys with --view, in the same order
  * links are taken only from the columns the view's lv-config maps (link and description), unless --columns is given
  * --snapshot writes each list's rows into that section's lv-snapshot block, keeping only the columns
    the view maps (ID, title, description, link, people, date, filters); sensitive columns never enter it
  * the allowlist is the union of every list's links, so always pass every list view on the page together
  * include the live gallery as --view @gallery with its matching --items file;
    --columns is required for the gallery and limits BOTH snapshots and links
  * inputs must contain all continuation pages and expanded person/lookup display values,
    not just a proposal sample or unresolved <Name>LookupId fields
  * --publication-approved attests that every supplied row is explicitly approved for
    the page audience; caller access and column approval alone are NOT row approval.
    For a list without approval, supply [] and --snapshot to remove its saved data and links.

Examples
  # Only after explicit row/audience approval, using approved rows from the complete export:
  python allowlist_from_list.py --items items.json --publication-approved --columns ID Title Link --page gallery-preview.html
  python allowlist_from_list.py --items items.json --publication-approved --columns ID Title Link --page gallery-preview.html --snapshot
  python allowlist_from_list.py --items items.json --publication-approved --columns Link --print
  python allowlist_from_list.py --items resources.json events.json --publication-approved --view resources events --page home-preview.html --snapshot
  python allowlist_from_list.py --items gallery.json resources.json --publication-approved --view @gallery resources --columns ID Title Link --page home-preview.html --snapshot
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
    if isinstance(data, dict) and data.get("@odata.nextLink"):
        raise ValueError("Incomplete items: follow every @odata.nextLink and combine all items before refreshing.")
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


def require_publication_approval(rows, approved: bool) -> None:
    if rows and not approved:
        raise ValueError("Explicit row/audience publication approval is required (--publication-approved). "
                         "Caller access and approved columns are not enough. Supply only approved rows, "
                         "or an empty export to omit an unapproved list's saved data and links.")


def require_expanded_values(headers, rows, columns) -> None:
    """Reject unresolved IDs rather than proposing or saving unusable display values."""
    def unresolved(value):
        if isinstance(value, str) and value[:1] in "[{":
            try:
                value = json.loads(value)
            except ValueError:
                return False
        if isinstance(value, list):
            return any(unresolved(v) for v in value)
        if isinstance(value, dict):
            return ("LookupId" in value and not any(
                value.get(k) for k in ("LookupValue", "Value", "Label", "Title", "displayName")
            ))
        return False

    indexes = {h: i for i, h in enumerate(headers)}
    for name in columns:
        i, lookup = indexes.get(name), indexes.get(f"{name}LookupId")
        for row in rows:
            value = row[i] if i is not None and i < len(row) else None
            lookup_value = row[lookup] if lookup is not None and lookup < len(row) else None
            if (lookup_value not in (None, "", []) and value in (None, "", [])) or unresolved(value):
                raise ValueError(
                    f"{name}: unresolved lookup IDs; use an expanded tool payload or resolve IDs to "
                    f"audience-approved display values under {name!r} before building or refreshing."
                )
        if name.endswith("LookupId") and i is not None:
            raise ValueError(f"{name}: map the expanded display column, not a LookupId column.")


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
    idx = [i for i, h in enumerate(headers) if h in columns]
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


def refresh_page(page: str | None, item_paths: list[str], keys: list[str | None],
                 columns: list[str], snapshot: bool = False,
                 publication_approved: bool = False) -> tuple[str | None, dict, str]:
    """Prepare a complete refresh in memory; callers write only after all inputs pass."""
    if len(keys) != len(item_paths):
        raise ValueError("Provide one view key per items file, in the same order.")
    if page is None and any(key is not None for key in keys):
        raise ValueError("List view keys need a page.")
    if len(set(keys)) != len(keys):
        raise ValueError("Each view (including @gallery) must appear only once.")
    if None in keys and not columns:
        raise ValueError("Gallery input requires --columns with the audience-approved column set for snapshots and links.")
    if page is not None:
        expected = set(re.findall(r'data-list-view="([^"]+)"', page))
        if 'id="site-page-config"' in page:
            expected.add(None)
        if set(keys) != expected:
            raise ValueError("Include every live section and the gallery (@gallery) in one refresh; "
                             "the --view keys must match the page.")

    urls: list[str] = []
    result: dict = {"lists": []}
    snapshots: list[tuple[str | None, list, list]] = []
    for n, path in enumerate(item_paths):
        with open(path, encoding="utf-8") as fh:
            headers, rows = to_rows(json.load(fh))
            require_publication_approval(rows, publication_approved)
        key = keys[n]
        link_cols = set(columns)
        if key:
            cfg = view_config(page, key)
            used, links = view_columns(cfg)
            link_cols = links if None in keys else (link_cols or links)
        else:
            used = set(columns)
        require_expanded_values(headers, rows, used)
        if not headers and not rows:
            headers = sorted(used)
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
            raise ValueError("No link-allowlist:start ... link-allowlist:end markers in the page.")
        for key, headers, rows in snapshots:
            text = snapshot_json(headers, rows) if snapshot else "null"
            if key:
                pat = rf'(<!-- list-view:{re.escape(key)}:start -->.*?<script type="application/json" class="lv-snapshot">).*?(</script>)'
            else:
                pat = r'(<script type="application/json" id="snapshot-data">).*?(</script>)'
            page, m = re.subn(pat, lambda mm: mm.group(1) + text + mm.group(2), page, count=1, flags=re.S)
            if m != 1 and snapshot:
                raise ValueError(f"No snapshot block for {key or 'the live gallery'} in the page.")
        result["snapshot"] = snapshot
    return page, result, block


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", required=True, nargs="+", help="list data JSON file(s); one per --view")
    ap.add_argument("--view", nargs="*", default=[], help="section keys or @gallery, same order as --items")
    ap.add_argument("--columns", nargs="+", default=[], help="audience-approved gallery columns (snapshots AND links); optional link subset for section-only refreshes")
    ap.add_argument("--page", help="HTML page to update in place")
    ap.add_argument("--snapshot", action="store_true", help="also write the snapshot fallback(s)")
    ap.add_argument("--publication-approved", action="store_true",
                    help="attest that every supplied row is explicitly approved for the page audience")
    ap.add_argument("--print", action="store_true", help="print the nav block")
    a = ap.parse_args(argv)
    page = None
    if a.page:
        with open(a.page, encoding="utf-8") as fh:
            page = fh.read()
    keys = [None if k == "@gallery" else k for k in a.view] if a.view else [None]
    try:
        page, result, block = refresh_page(page, a.items, keys, a.columns, a.snapshot, a.publication_approved)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    if a.page:
        with open(a.page, "w", encoding="utf-8") as fh:
            fh.write(page)
        result["page"] = a.page
    if a.print or not a.page:
        print(block)
    print(json.dumps(result), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
