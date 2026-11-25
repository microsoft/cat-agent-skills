#!/usr/bin/env python3
"""Propose and build a list view section from a SharePoint list's column schema.

Reads the list's column definitions (the JSON from GET /sites/{site-id}/lists/{list-id}/columns,
or the column listing tool) plus optional sample items, and proposes the view:

  title        Title
  description  first multi-line text column
  link         first hyperlink column
  people       first person column (not Created By / Modified By)
  date         a dateTime column with a "published", "due" or similar name, else Modified
  filters      ranked: choice and managed metadata (term), yes/no (as a toggle), person, lookup;
               columns where the sample shows one value or more than 25 values are skipped;
               the top 3 show in the bar, the rest go into a "More filters" panel
  sort         newest first, oldest first (when a date exists), title A to Z
  table        title, the first two filters, people, date

Hidden columns, system columns (ContentType, Attachments, _UIVersionString, compliance and
Teams or media metadata columns, Created By, Modified By) and columns passed to --sensitive or
--exclude are never used. The proposal prints as a short table so the agent can confirm it
with the user before building.

Examples
  # 1. propose only (print the mapping table)
  python build_list_view.py --columns columns.json --items items.json --label "Resources"
  # 2. build: write the config, and add or update the section in a page
  python build_list_view.py --columns columns.json --items items.json --label "Resources" \\
      --web-url https://<tenant>.sharepoint.com/sites/<site> --list-id <list-guid> --key resources \\
      --layout cards --sensitive InternalNotes --h2 "Everything you need to get started." \\
      --eyebrow Resources --intro "Guides, templates and recordings, updated by the team." \\
      --into Contoso-Activation-Program.html
  # override the proposed filters (in order) or how many show in the bar
  ... --filters Category Audience Featured --primary 2
  # fallback when scripts are blocked: a static, dated snapshot of the same view (no scripts)
  # use all approved rows after following every continuation page, not the proposal sample
  ... --items approved-items.json --publication-approved --static-snapshot --into Contoso-Activation-Program.html

Exit codes: 0 ok, 2 bad input (no Title column, page markers missing, bad arguments)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from allowlist_from_list import require_expanded_values, require_publication_approval, to_rows

HERE = Path(__file__).resolve().parent
BLOCK = HERE.parent / "assets" / "list-view-block.html"

SYSTEM = {
    "contenttype", "contenttypeid", "attachments", "_uiversionstring", "_uiversion", "edit", "linktitlenomenu",
    "linktitle", "linktitle2", "doctype", "docicon", "itemchildcount", "folderchildcount", "selecttitle",
    "_complianceflags", "_compliancetag", "_compliancetagwrittentime", "_compliancetaguserid", "_isrecord",
    "complianceassetid", "appauthor", "appeditor", "_colortag", "_moderationstatus", "_moderationcomments",
    "author", "editor", "created_x0020_by", "modified_x0020_by", "fileleafref", "filedirref", "fileref",
    "permmask", "uniqueid", "guid", "workflowversion", "workflowinstanceid", "parentversionstring",
    "parentleafname", "instanceid", "order", "smtotalsize", "smlastmodifieddate", "smtotalfilestreamsize",
    "smtotalfilecount", "_hascopydestinations", "_copysource", "owshiddenversion", "_level", "_iscurrentversion",
    "taxcatchall", "taxcatchalllabel", "taxkeyword", "taxkeywordtaxhtfield", "sharedwithusers", "sharedwithdetails",
    "_activity", "_shortcuturl", "_shortcutsiteid", "_shortcutwebid", "_shortcutuniqueid", "_virusstatus",
    "_virusvendorid", "_virusinfo", "_commentflags", "_commentcount", "_likecount", "_displayname",
    "_dlc_docid", "_dlc_docidurl", "_dlc_docidpersistid", "_ip_unifiedcompliancepolicyproperties",
    "_ip_unifiedcompliancepolicyuiaction", "_restricted", "_checkinComment".lower(), "checkoutuser", "id",
}
SYSTEM_PREFIXES = ("mediaservice", "_flow_", "_dlc_", "_ip_", "_shortcut", "odata__", "_compliance", "_vti_")
DATE_HINTS = ("publish", "due", "release", "event", "start", "date", "posted", "effective")
DEFAULT_PRIMARY = 3
MAX_DISTINCT = 25


def col_type(c: dict) -> str:
    for t in ("choice", "boolean", "dateTime", "personOrGroup", "lookup", "number", "currency", "hyperlinkOrPicture",
              "term", "calculated", "geolocation", "thumbnail", "contentApprovalStatus"):
        if t in c:
            if t == "hyperlinkOrPicture" and (c.get(t) or {}).get("isPicture"):
                return "picture"
            return t
    if "text" in c:
        return "note" if (c.get("text") or {}).get("allowMultipleLines") else "text"
    return "other"


def is_multi(c: dict, t: str) -> bool:
    f = c.get({"personOrGroup": "personOrGroup", "lookup": "lookup", "term": "term", "choice": "choice"}.get(t, ""), {}) or {}
    return bool(f.get("allowMultipleSelections") or f.get("allowMultipleSelection") or f.get("allowMultipleValues"))


def is_system(c: dict) -> bool:
    name = str(c.get("name", ""))
    low = name.lower()
    if low in SYSTEM or low.startswith(SYSTEM_PREFIXES):
        return True
    if re.fullmatch(r"[0-9a-f]{32}|[a-z][0-9a-f]{31}", low):  # hidden taxonomy notes, e.g. Teams image tags
        return True
    return False


def load_columns(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cols = data.get("value", data.get("columns", data)) if isinstance(data, dict) else data
    if not isinstance(cols, list):
        raise SystemExit("columns JSON must be a list or {\"value\": [...]}")
    return [c for c in cols if isinstance(c, dict) and c.get("name")]


def load_items(path: str | None, complete: bool = False) -> list[dict]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "format" in data and "content" in data:
        data = json.loads(data["content"])
    if complete and isinstance(data, dict) and data.get("@odata.nextLink"):
        raise ValueError("Incomplete items: follow every @odata.nextLink and combine all items before building a static snapshot.")
    if isinstance(data, dict) and "headers" in data and "rows" in data:
        return [dict(zip(data["headers"], r)) for r in data["rows"]]
    items = data.get("value", data) if isinstance(data, dict) else data
    out = []
    for it in items or []:
        if isinstance(it, dict) and isinstance(it.get("fields"), dict):
            out.append(dict(it["fields"]))
        elif isinstance(it, dict):
            out.append(it)
    return out


def values_of(item: dict, name: str) -> list[str]:
    v = item.get(name)
    if v is None or v == "":
        return []
    if isinstance(v, str) and v[:1] in "[{":
        try:
            v = json.loads(v)
        except ValueError:
            pass
    if isinstance(v, dict):
        v = [v]
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, dict):
                x = x.get("LookupValue") or x.get("Value") or x.get("Label") or x.get("Title") or x.get("displayName")
            if x not in (None, ""):
                out.append(str(x))
        return out
    if isinstance(v, bool):
        return ["Yes" if v else "No"]
    s = str(v)
    if re.match(r"^\d+;#", s):
        return [p for i, p in enumerate(s.split(";#")) if i % 2 == 1 and p]
    return [p.strip() for p in re.split(r";#|;", s) if p.strip()]


def sample_multi(items: list[dict], name: str) -> bool:
    """Graph does not always flag multi-choice columns; a sample value that is a list, or holds ;#, is multi."""
    for it in items:
        v = it.get(name)
        if isinstance(v, list) or (isinstance(v, str) and (";#" in v or v.startswith("["))):
            return True
    return False


def propose(cols: list[dict], items: list[dict], sensitive: set[str], exclude: set[str],
            forced: list[str] | None, primary: int) -> dict:
    skipped: list[tuple[str, str]] = []
    usable = []
    for c in cols:
        name, disp = c["name"], c.get("displayName") or c["name"]
        keys = {name.lower(), disp.lower()}
        t = col_type(c)
        if keys & sensitive:
            skipped.append((disp, "marked sensitive"))
            continue
        if keys & exclude:
            skipped.append((disp, "excluded"))
            continue
        if name in ("Title", "Modified", "Created"):
            usable.append((c, t))
            continue
        if c.get("hidden"):
            skipped.append((disp, "hidden"))
            continue
        if is_system(c):
            skipped.append((disp, "system"))
            continue
        usable.append((c, t))

    display_columns = {c["name"] for c, t in usable if t in ("personOrGroup", "lookup")}
    require_expanded_values(*to_rows(items), display_columns)

    def first(types, pred=lambda c: True):
        return next((c for c, t in usable if t in types and pred(c)), None)

    title = next((c for c, _ in usable if c["name"] == "Title"), None)
    desc = first({"note"})
    link = first({"hyperlinkOrPicture"})
    people = first({"personOrGroup"})
    dates = [c for c, t in usable if t == "dateTime" and c["name"] not in ("Created", "Modified")]
    date = next((c for h in DATE_HINTS for c in dates if h in (c["name"] + " " + str(c.get("displayName", ""))).lower()), None)
    date = date or (dates[0] if dates else None) or next((c for c, _ in usable if c["name"] == "Modified"), None)

    rank = {"choice": 0, "term": 0, "boolean": 1, "personOrGroup": 2, "lookup": 3}
    cands = [(c, t) for c, t in usable if t in rank and c["name"] != "Title"]
    if forced:
        want = [f.lower() for f in forced]
        cands = sorted([(c, t) for c, t in usable if {c["name"].lower(), str(c.get("displayName", "")).lower()} & set(want)],
                       key=lambda ct: min(want.index(k) for k in (ct[0]["name"].lower(), str(ct[0].get("displayName", "")).lower()) if k in want))
    else:
        cands = sorted(cands, key=lambda ct: rank[ct[1]])
    filters, notes = [], []
    for c, t in cands:
        disp = c.get("displayName") or c["name"]
        distinct = None
        if items:
            distinct = len({v for it in items for v in values_of(it, c["name"])})
            if t != "boolean" and not forced and (distinct <= 1 or distinct > MAX_DISTINCT):
                skipped.append((disp, f"filter skipped: {distinct} distinct value{'' if distinct == 1 else 's'} in the sample"))
                continue
            if t == "boolean" and not forced and distinct <= 1:
                skipped.append((disp, "filter skipped: one value in the sample"))
                continue
        f = {"key": re.sub(r"[^a-z0-9]+", "-", disp.lower()).strip("-") or c["name"].lower(),
             "label": disp, "columns": list(dict.fromkeys([c["name"], disp])), "type": t,
             "multi": t != "boolean" and (is_multi(c, t) or t == "personOrGroup" or sample_multi(items, c["name"])),
             "pills": t in ("choice", "term")}
        if t == "choice":
            ch = (c.get("choice") or {}).get("choices") or []
            if ch:
                f["choices"] = ch
        if t == "boolean":
            f["toggleLabel"] = f"Only {disp.lower()}"
        filters.append(f)
        notes.append(distinct)
    keys_seen: set[str] = set()
    for f in filters:
        base, n = f["key"], 2
        while f["key"] in keys_seen:
            f["key"] = f"{base}-{n}"
            n += 1
        keys_seen.add(f["key"])
    for i, f in enumerate(filters):
        f["primary"] = i < primary
    cand = lambda c, extra=(): list(dict.fromkeys([c["name"], c.get("displayName") or c["name"], *extra])) if c else []
    columns = {"id": ["ID"], "title": cand(title, ["LinkTitle"]) or ["Title", "LinkTitle"],
               "description": cand(desc), "url": cand(link), "people": cand(people), "date": cand(date)}
    table = [{"field": "title", "label": (title or {}).get("displayName") or "Title"}]
    table += [{"field": f"f:{f['key']}", "label": f["label"]} for f in filters if f["type"] != "boolean"][:2]
    if people:
        table.append({"field": "people", "label": people.get("displayName") or people["name"]})
    if date:
        table.append({"field": "date", "label": date.get("displayName") or date["name"]})
    return {"columns": columns, "filters": filters, "table": table, "skipped": skipped, "distinct": notes,
            "has_title": title is not None, "date_label": (date or {}).get("displayName")}


def print_table(p: dict, out=sys.stdout) -> None:
    def show(names):
        return names[0] if names else "(none)"
    rows = [("Title", show(p["columns"]["title"])), ("Description", show(p["columns"]["description"])),
            ("Link", show(p["columns"]["url"])), ("People", show(p["columns"]["people"])), ("Date", show(p["columns"]["date"]))]
    print("| Role | Column |", file=out)
    print("|---|---|", file=out)
    for r in rows:
        print(f"| {r[0]} | {r[1]} |", file=out)
    print("", file=out)
    print("| # | Filter | Column | Kind | Where |", file=out)
    print("|---|---|---|---|---|", file=out)
    for i, (f, d) in enumerate(zip(p["filters"], p["distinct"]), 1):
        kind = {"boolean": "toggle"}.get(f["type"], ("multi-select" if f["multi"] else "single select"))
        where = "bar" if f["primary"] else "More filters"
        extra = f", {d} values in sample" if d is not None else ", not checked against data"
        print(f"| {i} | {f['label']} | {f['columns'][0]} | {kind}{extra} | {where} |", file=out)
    if not p["filters"]:
        print("| - | (no filter columns found) | | | |", file=out)
    print("", file=out)
    print("Sort: " + ", ".join(["newest first", "oldest first"] if p["columns"]["date"] else []) +
          (", " if p["columns"]["date"] else "") + "title A to Z", file=out)
    print("Table columns: " + ", ".join(c["label"] for c in p["table"]), file=out)
    if p["skipped"]:
        print("Not used: " + "; ".join(f"{n} ({why})" for n, why in p["skipped"]), file=out)


def parts() -> dict[str, str]:
    text = BLOCK.read_text(encoding="utf-8")
    chunks = re.split(r"<!-- part:([a-z]+) -->\n", text)
    return {chunks[i]: chunks[i + 1].strip() + "\n" for i in range(1, len(chunks) - 1, 2)}


def fill(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        if v:
            text = text.replace("{{" + k + "}}", v)
    return text


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def insert_into(page: str, key: str, source: dict, section: str, pt: dict[str, str], replace_runtime: bool = True) -> tuple[str, list[str]]:
    done = []
    others = re.sub(rf"<!-- list-view:{re.escape(key)}:start -->.*?<!-- list-view:{re.escape(key)}:end -->",
                    "", page, flags=re.S)
    for tag in re.finditer(r'<script type="application/json" (?:id="site-page-config"|class="lv-config")>(.*?)</script>', others, re.S):
        config = json.loads(tag.group(1).replace("<\\/", "</"))
        existing = config.get("publicationSource") or config.get("source") or {}
        if existing.get("spItemUrl") == source["spItemUrl"] and any(
            existing.get(k) != source.get(k) for k in ("kind", "spItemUrl", "webUrl", "listId", "label")
        ):
            raise ValueError("Conflicting shared list metadata: update the gallery and all other section "
                             "source configs together before rebuilding. No page changes were written.")
    # 1. CSS, once, inside the page's single style element
    if "list-view:css:start" not in page:
        if "</style>" not in page:
            raise ValueError("page has no <style> element")
        i = page.rindex("</style>")
        page = page[:i] + "\n" + pt["css"] + page[i:]
        done.append("css added")
    # 2. manifest entry keyed by spItemUrl
    m = re.search(r'(<script type="application/json" class="ka-livedata-manifest">)(.*?)(</script>)', page, re.S)
    if m:
        try:
            man = json.loads(m.group(2) or "[]")
        except ValueError as e:
            raise ValueError(f"cannot parse the ka-livedata-manifest: {e}")
        man = [x for x in man if not (isinstance(x, dict) and x.get("spItemUrl") == source["spItemUrl"])] + [source]
        page = page[:m.start()] + m.group(1) + json.dumps(man, ensure_ascii=False).replace("</", "<\\/") + m.group(3) + page[m.end():]
        done.append("manifest entry merged")
    else:
        tag = '<script type="application/json" class="ka-livedata-manifest">' + json.dumps([source], ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
        if "</title>" in page:
            i = page.index("</title>") + len("</title>")
            page = page[:i] + "\n" + tag.rstrip("\n") + page[i:]
        else:
            i = page.index("</head>")
            page = page[:i] + tag + page[i:]
        done.append("manifest added")
    # 3. section: replace the same key, else the insert marker, else before the wrap that closes <main>
    sm = re.search(rf"<!-- list-view:{re.escape(key)}:start -->.*?<!-- list-view:{re.escape(key)}:end -->\n?", page, re.S)
    if sm:
        old_snap = re.search(r'<script type="application/json" class="lv-snapshot">(.*?)</script>', sm.group(0), re.S)
        config_pattern = r'<script type="application/json" class="lv-config">(.*?)</script>'
        old_config = re.search(config_pattern, sm.group(0), re.S)
        new_config = re.search(config_pattern, section, re.S)
        compatible = False
        if old_config and new_config:
            try:
                old_cfg = json.loads(old_config.group(1))
                new_cfg = json.loads(new_config.group(1))
                compatible = isinstance(old_cfg, dict) and isinstance(new_cfg, dict) and all(
                    old_cfg.get(k) == new_cfg.get(k) for k in ("source", "columns", "filters", "sensitive")
                )
            except ValueError:
                pass
        if old_snap and compatible:
            section = re.sub(r'(<script type="application/json" class="lv-snapshot">).*?(</script>)',
                             lambda mm: mm.group(1) + old_snap.group(1) + mm.group(2), section, count=1, flags=re.S)
        page = page[:sm.start()] + section + page[sm.end():]
        status = "snapshot kept" if old_snap and compatible else "snapshot cleared; regenerate before upload"
        done.append(f"section {key} replaced ({status})")
    elif "<!-- list-view:insert -->" in page:
        page = page.replace("<!-- list-view:insert -->", section + "<!-- list-view:insert -->", 1)
        done.append(f"section {key} added at the list-view:insert marker")
    else:
        mm = re.search(r"</div>\s*</main>", page)
        if not mm:
            raise ValueError("no <!-- list-view:insert --> marker and no </div></main> to insert before")
        page = page[:mm.start()] + section + page[mm.start():]
        done.append(f"section {key} added at the end of main")
    # 4. allowlist, once
    if "link-allowlist:start" not in page:
        i = page.rindex("</body>")
        page = page[:i] + pt["allowlist"] + page[i:]
        done.append("allowlist markers added (empty; run allowlist_from_list.py)")
    # 5. runtime, once (refreshed to the skill's current version)
    rm = re.search(r'<script id="list-view-runtime">.*?</script>\n?', page, re.S)
    if rm:
        if replace_runtime:
            page = page[:rm.start()] + pt["runtime"] + page[rm.end():]
            done.append("runtime refreshed")
    else:
        i = page.rindex("</body>")
        page = page[:i] + pt["runtime"] + page[i:]
        done.append("runtime added")
    return page, done


def _text(v) -> str:
    import html as _h
    s = re.sub(r"<[^>]*>", " ", _h.unescape(str(v or "")))
    return re.sub(r"\s+", " ", s).strip()


def _url(v) -> str:
    from urllib.parse import urlsplit
    if isinstance(v, dict):
        v = v.get("Url") or v.get("url") or ""
    s = str(v or "")
    if s.startswith("{"):
        try:
            o = json.loads(s)
            s = str(o.get("Url") or o.get("url") or "")
        except ValueError:
            pass
    m = re.search(r'href\s*=\s*["\']([^"\']+)', s)
    s = (m.group(1) if m else s).split(", ")[0].strip()
    try:
        u = urlsplit(s)
    except ValueError:
        return ""
    return s if u.scheme == "https" and u.netloc and not u.username and not u.password else ""


def static_section(key: str, label: str, cfg: dict, items: list[dict], layout: str, eyebrow: str, h2: str, intro: str) -> str:
    """Script-free snapshot of the list view, with a dated note."""
    import datetime as dt
    cols = cfg["columns"]

    def pick(it, names):
        for n in names or []:
            if n in it and it[n] not in (None, ""):
                return it[n]
        return None
    facets = [f for f in cfg["filters"] if f["type"] not in ("boolean",)][:2]
    rows = []
    for it in items:
        title = _text(pick(it, cols["title"]))
        if not title:
            continue
        d = str(pick(it, cols["date"]) or "")[:10]
        rows.append({"title": title, "desc": _text(pick(it, cols["description"])), "url": _url(pick(it, cols["url"])),
                     "people": ", ".join(values_of(it, (cols["people"] or [""])[0])) if cols["people"] else "",
                     "date": d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else "",
                     "facets": [(f, values_of(it, f["columns"][0])) for f in facets]})
    rows.sort(key=lambda r: (r["date"] or "", r["title"]), reverse=bool(cols["date"]))
    today = dt.date.today().isoformat()
    note = f'Saved copy of the {esc(label)} list from {today}. It does not update by itself.'
    out = [f'<!-- list-view:{key}:start -->',
           f'<section class="lv lv-static" id="lv-{key}" aria-labelledby="h-lv-{key}">',
           f'<div class="sh"><div><div class="kick"><i></i>{esc(eyebrow)}</div><h2 id="h-lv-{key}">{esc(h2)}</h2></div><p>{esc(intro)}</p></div>',
           f'<p class="lv-note">{note}</p>', f'<p class="lv-count">{len(rows)} {esc(cfg["itemNoun"][0 if len(rows) == 1 else 1])}</p>']
    def link(r):
        return (f'<a href="{esc(r["url"])}" target="_top" rel="noopener noreferrer">{esc(r["title"])}</a>' if r["url"] else esc(r["title"]))
    def fpills(f, vs):
        ch = f.get("choices") or []
        return "".join('<span class="lv-pill lv-c%d">%s</span>' % (ch.index(v) % 6 if v in ch else 0, esc(v)) for v in vs)

    def pills(r):
        return "".join(fpills(f, vs) for f, vs in r["facets"])
    if layout == "table":
        heads = ["Title"] + [f["label"] for f in facets] + (["People"] if cols["people"] else []) + (["Date"] if cols["date"] else [])
        out.append(f'<div class="lv-tablewrap" role="region" aria-label="{esc(label)} table" tabindex="0"><table class="lv-table"><caption class="lv-vh">{esc(label)}</caption><thead><tr>'
                   + "".join(f'<th scope="col">{esc(h)}</th>' for h in heads) + "</tr></thead><tbody>")
        for r in rows:
            cells = [f'<th scope="row">{link(r)}</th>'] + ["<td>" + fpills(f, vs) + "</td>" for f, vs in r["facets"]]
            if cols["people"]:
                cells.append(f'<td>{esc(r["people"])}</td>')
            if cols["date"]:
                cells.append(f'<td>{esc(r["date"])}</td>')
            out.append("<tr>" + "".join(cells) + "</tr>")
        out.append("</tbody></table></div>")
    else:
        out.append('<ul class="lv-cards">')
        for r in rows:
            parts_ = [f'<div class="lv-meta">{pills(r)}' + (f'<time class="lv-date" datetime="{r["date"]}">{r["date"]}</time>' if r["date"] else "") + "</div>",
                      f'<h3>{link(r)}</h3>']
            if r["desc"]:
                parts_.append(f'<p class="lv-desc">{esc(r["desc"])}</p>')
            if r["people"]:
                parts_.append(f'<p class="lv-people">{esc(r["people"])}</p>')
            out.append(f'<li><article class="lv-card">{"".join(parts_)}</article></li>')
        out.append("</ul>")
    out += ["</section>", f"<!-- list-view:{key}:end -->", ""]
    return "\n".join(out)


def make_static(page: str, key: str, source: dict, section: str, pt: dict[str, str]) -> tuple[str, list[str]]:
    done = []
    if "list-view:css:start" not in page:
        i = page.rindex("</style>")
        page = page[:i] + "\n" + pt["css"] + page[i:]
        done.append("css added")
    sm = re.search(rf"<!-- list-view:{re.escape(key)}:start -->.*?<!-- list-view:{re.escape(key)}:end -->\n?", page, re.S)
    if sm:
        page = page[:sm.start()] + section + page[sm.end():]
        done.append(f"section {key} replaced by a static snapshot")
    elif "<!-- list-view:insert -->" in page:
        page = page.replace("<!-- list-view:insert -->", section + "<!-- list-view:insert -->", 1)
        done.append(f"static section {key} added at the marker")
    else:
        mm = re.search(r"</div>\s*</main>", page)
        page = page[:mm.start()] + section + page[mm.start():]
        done.append(f"static section {key} added at the end of main")
    m = re.search(r'(<script type="application/json" class="ka-livedata-manifest">)(.*?)(</script>)', page, re.S)
    if m:
        references = []
        for tag in re.finditer(r'<script type="application/json" (?:id="site-page-config"|class="lv-config")>(.*?)</script>', page, re.S):
            config = json.loads(tag.group(1).replace("<\\/", "</"))
            references.append((config.get("publicationSource") or config.get("source") or {}).get("spItemUrl"))
        if source["spItemUrl"] not in references:
            man = [x for x in json.loads(m.group(2) or "[]") if not (isinstance(x, dict) and x.get("spItemUrl") == source["spItemUrl"])]
            page = page[:m.start()] + (m.group(1) + json.dumps(man, ensure_ascii=False).replace("</", "<\\/") + m.group(3) if man else "") + page[m.end():]
            done.append("manifest entry removed" + ("" if man else " (manifest now empty, removed)"))
        else:
            done.append("manifest entry kept for another live consumer")
    if 'data-list-view="' not in page and 'id="site-page-config"' not in page:
        page, n = re.subn(r'<script id="list-view-runtime">.*?</script>\n?', "", page, flags=re.S)
        if n:
            done.append("runtime removed: no live list views left, the page is script-free again")
        page = re.sub(r'\n?<!-- link-allowlist:start.*?<!-- link-allowlist:end -->\n?', "\n", page, flags=re.S)
    return page, done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--columns", required=True, help="column definitions JSON (columns endpoint)")
    ap.add_argument("--items", help="optional sample items JSON (Graph items, rows shape, or list of dicts)")
    ap.add_argument("--label", required=True, help="list display name (must match the manifest label)")
    ap.add_argument("--key", help="section key, lowercase letters, digits, hyphens (default: from the label)")
    ap.add_argument("--web-url", help="site URL of the page AND the list (same site)")
    ap.add_argument("--list-id", help="list GUID")
    ap.add_argument("--layout", choices=["cards", "table"], default="cards")
    ap.add_argument("--layouts", nargs="+", choices=["cards", "table"], default=["cards", "table"], help="layouts the toggle offers")
    ap.add_argument("--sensitive", nargs="*", default=[], help="columns never to show, filter or snapshot")
    ap.add_argument("--exclude", nargs="*", default=[], help="other columns to leave out")
    ap.add_argument("--filters", nargs="*", help="override the proposed filter columns, in order")
    ap.add_argument("--primary", type=int, default=DEFAULT_PRIMARY, help="filters shown in the bar (rest go to More filters)")
    ap.add_argument("--noun", default="item,items", help="singular,plural for the result count")
    ap.add_argument("--eyebrow"), ap.add_argument("--h2"), ap.add_argument("--intro")
    ap.add_argument("--config-out", help="write the lv-config JSON here")
    ap.add_argument("--section-out", help="write the filled section markup here")
    ap.add_argument("--into", help="page to add or update the list view in (in place)")
    ap.add_argument("--json", action="store_true", help="print the proposal as JSON instead of the table")
    ap.add_argument("--static-snapshot", action="store_true", help="fallback: write a script-free, dated snapshot from complete, row-approved --items (not a proposal sample)")
    ap.add_argument("--publication-approved", action="store_true",
                    help="attest that every static snapshot row is explicitly approved for the page audience")
    a = ap.parse_args(argv)

    try:
        cols = load_columns(a.columns)
        items = load_items(a.items, complete=a.static_snapshot)
        if a.static_snapshot:
            require_publication_approval(items, a.publication_approved)
        p = propose(cols, items, {s.lower() for s in a.sensitive}, {s.lower() for s in a.exclude}, a.filters, a.primary)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    if not p["has_title"]:
        print("The list has no Title column; pick the title column by hand (--filters does not change this).", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({k: v for k, v in p.items() if k not in ("distinct",)}, indent=2))
    else:
        print_table(p)

    building = a.config_out or a.section_out or a.into
    if not building:
        return 0
    if not (a.web_url and a.list_id):
        print("--web-url and --list-id are required to build (the list must be on the same site as the page).", file=sys.stderr)
        return 2
    key = a.key or re.sub(r"[^a-z0-9]+", "-", a.label.lower()).strip("-")
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", key):
        print(f"invalid --key {key!r}: start with a letter; lowercase letters, digits and hyphens only", file=sys.stderr)
        return 2
    web = a.web_url.rstrip("/")
    source = {"kind": "list", "spItemUrl": f"list:{web}/{a.list_id}", "webUrl": web, "listId": a.list_id, "label": a.label}
    noun = [x.strip() for x in a.noun.split(",")][:2]
    cfg = {"key": key, "source": source, "itemNoun": noun if len(noun) == 2 else ["item", "items"],
           "layout": a.layout, "layouts": list(dict.fromkeys(a.layouts)), "columns": p["columns"],
           "filters": p["filters"], "table": p["table"], "defaultSort": "newest" if p["columns"]["date"] else "title",
           "sensitive": sorted(set(a.sensitive))}
    cfg_json = json.dumps(cfg, ensure_ascii=False)
    pt = parts()
    section = fill(pt["section"], {"LV_KEY": key, "LV_CONFIG_JSON": cfg_json.replace("</", "<\\/"),
                                   "LIST_DISPLAY_NAME": esc(a.label), "LV_EYEBROW": esc(a.eyebrow or ""),
                                   "LV_H2": esc(a.h2 or ""), "LV_INTRO": esc(a.intro or "")})
    if a.static_snapshot:
        if not a.items:
            print("--static-snapshot needs --items (the current list items).", file=sys.stderr)
            return 2
        sensitive = {x.lower() for x in a.sensitive}
        items = [{k: v for k, v in it.items() if k.lower() not in sensitive} for it in items]
        section = static_section(key, a.label, cfg, items, a.layout, a.eyebrow or "{{LV_EYEBROW}}", a.h2 or "{{LV_H2}}", a.intro or "{{LV_INTRO}}")
    if a.into:
        page_path = Path(a.into)
        page = page_path.read_text(encoding="utf-8")
        try:
            page, done = (make_static if a.static_snapshot else insert_into)(page, key, source, section, pt)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
    if a.config_out:
        Path(a.config_out).write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    if a.section_out:
        Path(a.section_out).write_text(section, encoding="utf-8")
    if a.into:
        page_path.write_text(page, encoding="utf-8")
        print(json.dumps({"page": a.into, "key": key, "changes": done,
                          "next": ["fill any {{LV_*}} placeholders left", "allowlist_from_list.py --items <approved-items.json> "
                                   f"--publication-approved --page {a.into} --snapshot --view {key} "
                                   "(include every live view and @gallery if present)", "visual_check.py with --sample-data "
                                   f"{key}=<rows.json>"]}, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
