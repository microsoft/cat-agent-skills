#!/usr/bin/env python3
"""Build and check SharePoint folder links that open the folder itself.

A plain folder URL (https://host/sites/x/Shared Documents/Folder) often lands at
the top of the library. A link that opens the folder uses the library view
page with an id= parameter holding the URL-encoded server-relative folder path:

  https://host/sites/x/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2Fx%2FShared%20Documents%2FFolder

Subcommands
  sanitize  Clean proposed folder names (characters SharePoint rejects), report renames.
  links     Build links for folder names.
  check     Upkeep: compare the folder links in an HTML page with the library's
            current folders; report ok, broken, likely renamed and unlinked folders.
            With --fix-out, write a copy of the page with ONLY the changed links fixed.

Folder listings can be a JSON list of names, or the JSON from a drive children
call ({"value":[{"name":..., "folder":{...}}]}) or a list of such items.

Examples
  python build_folder_links.py sanitize "Plan / Build" "Q&A: Ops"
  python build_folder_links.py links --site https://contoso.sharepoint.com/sites/Program \
      --names "0 Program" "Activate" "Adopt"
  python build_folder_links.py check --site https://contoso.sharepoint.com/sites/Program \
      --page page.html --folders children.json --fix-out page.fixed.html
"""
from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
from urllib.parse import parse_qs, quote, unquote, urlsplit

# Characters SharePoint and OneDrive reject in file and folder names.
INVALID = '"*:<>?/\\|'
RESERVED = {"con", "prn", "aux", "nul", "_vti_", "desktop.ini"} | {f"com{i}" for i in range(10)} | {f"lpt{i}" for i in range(10)}


def sanitize(name: str) -> str:
    out = name
    for ch in INVALID:
        out = out.replace(ch, " - " if ch == "/" else " ")
    out = re.sub(r"\s+", " ", out).strip().rstrip(".").strip()
    out = re.sub(r"(\s-\s)+", " - ", out)
    if out.lower() in RESERVED or out.startswith("~$"):
        out = f"{out} folder"
    return out[:250] or "Untitled"


def site_parts(site: str) -> tuple[str, str]:
    u = urlsplit(site.rstrip("/"))
    return f"{u.scheme}://{u.netloc}", u.path  # origin, server-relative site path


def folder_link(site: str, folder_path: str, library: str = "Shared Documents") -> str:
    origin, site_path = site_parts(site)
    lib_path = f"{site_path}/{library}".replace("//", "/")
    server_rel = f"{lib_path}/{folder_path.strip('/')}"
    return f"{origin}{quote(lib_path)}/Forms/AllItems.aspx?id={quote(server_rel, safe='')}"


def folder_from_link(href: str, site: str, library: str) -> str | None:
    u = urlsplit(html.unescape(href))
    if not u.path.lower().endswith("/forms/allitems.aspx"):
        return None
    ids = parse_qs(u.query).get("id")
    if not ids:
        return None
    _, site_path = site_parts(site)
    prefix = f"{site_path}/{library}/".replace("//", "/")
    path = unquote(ids[0]) if "%" in ids[0] else ids[0]
    if not path.lower().startswith(prefix.lower()):
        return None
    return path[len(prefix):].strip("/")


def load_folders(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data.get("value", data) if isinstance(data, dict) else data
    names = []
    for it in items:
        if isinstance(it, str):
            names.append(it)
        elif isinstance(it, dict) and ("folder" in it or it.get("isFolder") or it.get("type") == "folder"):
            names.append(it.get("name", ""))
    return [n for n in names if n]


HREF = re.compile(r'href="([^"]+)"')


def cmd_check(a) -> int:
    with open(a.page, encoding="utf-8") as fh:
        page = fh.read()
    folders = load_folders(a.folders)
    lower = {f.lower(): f for f in folders}
    renames = dict(r.split("=", 1) for r in (a.rename or []))
    report = {"ok": [], "broken": [], "renamed": [], "unlinked": [], "folders": folders}
    linked = set()
    replacements = {}
    for href in sorted(set(HREF.findall(page))):
        rel = folder_from_link(href, a.site, a.library)
        if rel is None:
            continue
        top = rel.split("/")[0]
        if top.lower() in lower and lower[top.lower()] == top:
            report["ok"].append(rel)
            linked.add(top)
            continue
        if top in renames and renames[top] in folders:  # confirmed by the user
            guess = renames[top]
        elif top.lower() in lower:  # case-only change
            guess = lower[top.lower()]
        else:
            close = difflib.get_close_matches(top, folders, n=1, cutoff=0.6)
            guess = close[0] if close else None
        entry = {"link_folder": rel, "href": href}
        if guess:
            entry["suggested_folder"] = guess
            entry["new_href"] = html.escape(folder_link(a.site, guess + rel[len(top):], a.library), quote=True)
            report["renamed"].append(entry)
            replacements[href] = entry["new_href"]
            linked.add(guess)
        else:
            report["broken"].append(entry)
    # The page may know a renamed folder only by its card title; the user confirms each suggestion.
    for f in folders:
        if f not in linked and not f.startswith("0 "):
            report["unlinked"].append({"folder": f, "need": "lead and one-line description to add a card"})
    # A rename to a new word (Kickstarter to Activate) cannot be guessed: pair broken links with unlinked folders.
    if report["broken"] and report["unlinked"]:
        report["possible_renames"] = [{"old": b["link_folder"].split("/")[0],
                                       "candidates": [u["folder"] for u in report["unlinked"]]} for b in report["broken"]]
        report["possible_renames_hint"] = "Ask the user which folder each old link moved to, then rerun with --rename OLD=NEW."
    if a.fix_out:
        fixed = page
        for old, new in replacements.items():
            fixed = fixed.replace(f'href="{old}"', f'href="{new}"')
        for e in report["renamed"]:
            old_top = e["link_folder"].split("/")[0]
            fixed = fixed.replace(f'data-folder="{html.escape(old_top, quote=True)}"',
                                  f'data-folder="{html.escape(e["suggested_folder"], quote=True)}"')
            if re.search(r">\s*" + re.escape(old_top) + r"\s*<", fixed):
                e["title_note"] = f'The page still shows "{old_top}" as visible text; ask whether the card title should change too.'
        with open(a.fix_out, "w", encoding="utf-8") as fh:
            fh.write(fixed)
        report["fixed_copy"] = a.fix_out
        report["changed_links"] = len(replacements)
    report["note"] = ("Renamed matches are guesses by name similarity; confirm each with the user. "
                      "Card titles and descriptions are not changed; update them by hand if the rename changed meaning. "
                      "Click-test every link in a browser before handing over.")
    print(json.dumps(report, indent=2))
    return 1 if report["broken"] else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sanitize"); s.add_argument("names", nargs="+")
    l = sub.add_parser("links")
    l.add_argument("--site", required=True, help="site URL, e.g. https://contoso.sharepoint.com/sites/Program")
    l.add_argument("--library", default="Shared Documents", help="library URL name (default: Shared Documents)")
    l.add_argument("--names", nargs="+", required=True, help="folder names or paths inside the library")
    c = sub.add_parser("check")
    c.add_argument("--site", required=True); c.add_argument("--library", default="Shared Documents")
    c.add_argument("--page", required=True); c.add_argument("--folders", required=True)
    c.add_argument("--fix-out")
    c.add_argument("--rename", nargs="*", help="renames the user confirmed, e.g. Kickstarter=Activate")
    a = ap.parse_args(argv)

    if a.cmd == "sanitize":
        out = [{"proposed": n, "name": sanitize(n), "renamed": sanitize(n) != n} for n in a.names]
        print(json.dumps(out, indent=2))
        return 0
    if a.cmd == "links":
        out = []
        for n in a.names:  # names are real folder names (sanitize first); "/" separates subfolders
            out.append({"folder": n, "link": folder_link(a.site, n, a.library)})
        print(json.dumps(out, indent=2))
        return 0
    return cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
