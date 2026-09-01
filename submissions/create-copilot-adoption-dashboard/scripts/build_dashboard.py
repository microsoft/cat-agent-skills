#!/usr/bin/env python3
"""Build a populated Copilot Adoption dashboard from four MAC report exports.

Reads the four Microsoft admin center (MAC) Copilot activity exports, computes
the five-pillar adoption metrics and KPI scorecard defined in
references/adoption-framework.md, and injects the results into the bundled
single-file HTML template (assets/dashboard_template.html), replacing every
template placeholder so the output carries only the customer's real data.

Standard library only. No network access. Reads CSV files, writes one HTML file
and prints a JSON run summary (mapping, KPIs, warnings) to stdout.

Typical use:
    python build_dashboard.py \
        --company "Contoso" --logo /path/logo.png \
        --usage usage.csv --agents-user agents_user.csv \
        --agents-agent agents_agent.csv --chat chat.csv \
        --period 30 --out working/Contoso_Copilot_Adoption_Dashboard.html

If a column cannot be matched, pass --col-map map.json (see the reference).
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

# --------------------------------------------------------------------------- #
# Column-concept keyword aliases. Headers are normalised (lower-cased, all
# non-alphanumerics removed) before matching, so "User Principal Name",
# "user_principal_name" and "UPN" all reduce to comparable tokens.
# --------------------------------------------------------------------------- #

USER_KEYS = ["userprincipalname", "userprincipal", "upn", "useremail",
             "emailaddress", "email", "userid", "user", "displayname", "name"]

CONCEPTS = {
    "prompts": ["promptssubmitted", "totalprompts", "promptcount", "prompts",
                "copilotactions", "actionscount"],
    "active_days": ["activedays", "daysactive", "numberofactivedays", "activedaycount"],
    "last_activity": ["lastactivitydate", "lastactivity", "lastactive"],
    "agents_used": ["numberofagentsused", "agentsused", "numberofagents",
                    "distinctagents", "agentcount", "agentsaccessed"],
    "agent_responses": ["agentresponsesreceived", "agentresponses",
                        "responsesreceived", "responses"],
    "agent_name": ["agentname", "agentdisplayname", "agent", "declarativeagentname"],
    "active_users": ["activeusers", "totalactiveusers", "activeusercount"],
    "active_users_licensed": ["activeuserslicensed", "licensedactiveusers"],
    "active_users_unlicensed": ["activeusersunlicensed", "unlicensedactiveusers"],
    "creator_type": ["creatortype", "creator"],
    "chat_prompts": ["promptssubmitted", "chatprompts", "totalprompts",
                     "promptcount", "prompts"],
    # The MAC exports carry the window they were generated for (default 28 days)
    # and the date the report data was refreshed.
    "report_period": ["reportperiod", "reportingperiod", "reportperioddays",
                      "reportwindow", "windowdays", "period"],
    "report_refresh": ["reportrefreshdate", "reportrefresh", "refreshdate",
                       "datagenerateddate", "reportdate"],
}

# Windows the MAC report picker offers; anything else is accepted but flagged.
STANDARD_PERIODS = {7, 28, 30, 90}
DEFAULT_PERIOD = 28  # MAC default when no Report Period column is present

# App display name -> tokens that identify its per-app last-activity column.
APPS = [
    ("Teams", ["teams"]),
    ("Outlook", ["outlook"]),
    ("Word", ["word"]),
    ("Excel", ["excel"]),
    ("PowerPoint", ["powerpoint", "ppt"]),
    ("OneNote", ["onenote"]),
    ("Loop", ["loop"]),
    ("App", ["copilotapp", "m365copilotapp", "m365app", "copilotmobile", "mobileapp"]),
    ("Edge", ["edge"]),
    ("Web chat", ["webchat", "chatweb", "web"]),
]
ACTIVITY_TOKENS = ["lastactivity", "activitydate", "lastactive", "activity"]

SEGMENT_ORDER = ["Champion", "Habitual", "Casual", "Dormant", "Never"]
DATE_FORMATS = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%d %b %Y",
                "%m/%d/%Y %H:%M", "%d-%b-%Y", "%d.%m.%Y"]
TOP_N = 10  # surfaces + agents shown in the ranked bar panels
TEMPLATE_TOKENS = ["single-period template", "populated by a", "cowork skill",
                   "illustrative", "placeholder", "@dashboard_data",
                   "company name"]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def to_int(v) -> int:
    if v is None:
        return 0
    s = str(v).strip().replace(",", "")
    if not s or s in ("-", "n/a", "na", "none", "null"):
        return 0
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else 0


def parse_date(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s in ("-", "n/a", "na", "none", "null"):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "").strip()).date()
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


_READ_CACHE: dict = {}


def sniff_read(path: str):
    """Read a CSV robustly (BOM + delimiter sniffing). Returns (headers, rows).

    Results are cached per path so the period pre-scan and the pillar
    computation each read a large export only once.
    """
    if path in _READ_CACHE:
        return _READ_CACHE[path]
    headers, dicts = _sniff_read_uncached(path)
    _READ_CACHE[path] = (headers, dicts)
    return headers, dicts


def _sniff_read_uncached(path: str):
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    sample = raw[:8192]
    delim = ","
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        for cand in (";", "\t", "|"):
            if sample.count(cand) > sample.count(","):
                delim = cand
    reader = csv.reader(raw.splitlines(), delimiter=delim)
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    if not rows:
        return [], []
    headers = rows[0]
    dicts = []
    for r in rows[1:]:
        r = list(r) + [""] * (len(headers) - len(r))
        dicts.append({headers[i]: r[i] for i in range(len(headers))})
    return headers, dicts


class Resolver:
    """Resolves concept names to actual header strings for one report."""

    def __init__(self, headers, overrides=None):
        self.headers = headers
        self.norm_map = {norm(h): h for h in headers}
        self.overrides = {k: v for k, v in (overrides or {}).items()}
        self.resolved = {}

    def find(self, concept, aliases):
        if concept in self.overrides:
            self.resolved[concept] = self.overrides[concept]
            return self.overrides[concept]
        for a in aliases:
            na = norm(a)
            if na in self.norm_map:                       # exact normalised hit
                self.resolved[concept] = self.norm_map[na]
                return self.norm_map[na]
        for a in aliases:                                 # substring fallback
            na = norm(a)
            for nh, orig in self.norm_map.items():
                if na and na in nh:
                    self.resolved[concept] = orig
                    return orig
        return None

    def user(self):
        return self.find("user", USER_KEYS)

    def app_columns(self):
        """Map app display name -> header for its per-app activity column."""
        found = {}
        for header in self.headers:
            nh = norm(header)
            if not any(t in nh for t in ACTIVITY_TOKENS):
                continue
            for disp, toks in APPS:
                if disp in found:
                    continue
                if any(t in nh for t in toks):
                    found[disp] = header
                    break
        return found


def detect_period(rows, col):
    """Most-common integer day-count in a Report Period column.

    Values may read "28" or "Last 28 days"; the first integer is taken and only
    plausible day counts (1-365) are considered, so a column holding dates or
    labels simply yields no result instead of a bogus window.
    """
    tally: dict = {}
    for row in rows:
        v = to_int(row.get(col))
        if 1 <= v <= 365:
            tally[v] = tally.get(v, 0) + 1
    if not tally:
        return None, {}
    best = max(tally.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    return best, tally


def prescan(path, overrides, label, warn):
    """Read an export's Report Period / Report Refresh Date before computing.

    The reporting window drives both the dashboard badge and the per-app
    activity recency test, so it is resolved from the data rather than assumed.
    """
    headers, rows = sniff_read(path)
    r = Resolver(headers, overrides)
    c_period = r.find("report_period", CONCEPTS["report_period"])
    c_refresh = r.find("report_refresh", CONCEPTS["report_refresh"])
    period, tally = detect_period(rows, c_period) if c_period else (None, {})
    if c_period and period is None:
        warn.append(f"{label}: '{c_period}' held no usable day count; "
                    "the window was taken from another source.")
    if len(tally) > 1:
        mixed = ", ".join(f"{k}d x{v}" for k, v in sorted(tally.items()))
        warn.append(f"{label}: mixed Report Period values ({mixed}); "
                    f"used the most common ({period} days).")
    if period is not None and period not in STANDARD_PERIODS:
        warn.append(f"{label}: Report Period is {period} days, which is not a "
                    "standard MAC window (7/28/30/90) — verify the export.")
    refresh = None
    if c_refresh:
        dates = [d for d in (parse_date(row.get(c_refresh)) for row in rows) if d]
        if dates:
            refresh = max(dates)
    return {"period": period, "period_column": c_period,
            "refresh_date": refresh, "refresh_column": c_refresh}


def largest_remainder(counts, total):
    """Round a list of counts to integer percentages that sum to 100."""
    if total <= 0:
        return [0] * len(counts)
    raw = [c / total * 100 for c in counts]
    floors = [int(x) for x in raw]
    remainder = 100 - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in range(remainder):
        floors[order[i % len(order)]] += 1
    return floors


# --------------------------------------------------------------------------- #
# Pillar computations
# --------------------------------------------------------------------------- #

def compute_usage(path, report_date, period, overrides, warn):
    headers, rows = sniff_read(path)
    r = Resolver(headers, overrides)
    ukey = r.user()
    if not ukey:
        warn.append("Copilot usage: no user identifier column found — Copilot Chat conversion cannot exclude licensed users.")
    c_prompts = r.find("prompts", CONCEPTS["prompts"])
    c_days = r.find("active_days", CONCEPTS["active_days"])
    c_last = r.find("last_activity", CONCEPTS["last_activity"])
    app_cols = r.app_columns()
    if not c_prompts and not c_days and not app_cols:
        raise ValueError(
            "Copilot usage: could not find prompts, active-days or per-app "
            "activity columns. Headers: " + " | ".join(headers))

    assigned = len(rows)
    seg_counts = {s: 0 for s in SEGMENT_ORDER}
    app_active = {a: 0 for a in app_cols}
    active = habitual = multi_surface = 0
    users = set()

    for row in rows:
        if ukey:
            users.add(norm(row.get(ukey, "")))
        prompts = to_int(row.get(c_prompts)) if c_prompts else 0
        days = to_int(row.get(c_days)) if c_days else 0
        apps_active = 0
        latest_app = None
        for disp, col in app_cols.items():
            d = parse_date(row.get(col))
            cell = (row.get(col) or "").strip()
            is_active = bool(cell) and (d is None or (report_date - d).days <= period)
            if is_active:
                apps_active += 1
                app_active[disp] += 1
            if d and (latest_app is None or d > latest_app):
                latest_app = d
        last = parse_date(row.get(c_last)) if c_last else None
        if last is None:
            last = latest_app
        has_activity = prompts > 0 or days > 0 or apps_active > 0 or last is not None

        if not has_activity:
            seg = "Never"
        elif last is not None and (report_date - last).days >= 28:
            seg = "Dormant"
        elif days >= 12 and (prompts >= 60 or apps_active >= 4):
            seg = "Champion"
        elif days >= 5:
            seg = "Habitual"
        else:
            seg = "Casual"
        seg_counts[seg] += 1
        if has_activity:
            active += 1
        if days >= 5:
            habitual += 1
        if apps_active >= 3:      # framework "multi-surface" breadth KPI
            multi_surface += 1

    counts = [seg_counts[s] for s in SEGMENT_ORDER]
    seg_pct = largest_remainder(counts, assigned)
    # count rides alongside the percentage so the donut can show users on hover.
    segments = [{"name": s, "value": seg_pct[i], "count": seg_counts[s]}
                for i, s in enumerate(SEGMENT_ORDER)]

    surfaces = sorted(
        ({"name": a, "pct": round(app_active[a] / assigned * 100),
          "users": app_active[a]} for a in app_active),
        key=lambda x: (x["pct"], x["users"]), reverse=True)[:TOP_N] if assigned else []

    if not c_days:
        warn.append("Copilot usage: no active-days column — habitual rate and "
                    "Champion/Habitual split are approximate.")

    return {
        "assigned": assigned, "active": active, "users": users,
        "activation": round(active / assigned * 100, 1) if assigned else 0.0,
        "activationSub": f"{active:,} of {assigned:,}",
        "habitual": round(habitual / assigned * 100) if assigned else 0,
        "multiSurface": round(multi_surface / assigned * 100) if assigned else 0,
        "segments": segments, "surfaces": surfaces,
        "mapping": r.resolved | {"apps": app_cols},
    }


def compute_agents_user(path, overrides, warn):
    headers, rows = sniff_read(path)
    r = Resolver(headers, overrides)
    c_agents = r.find("agents_used", CONCEPTS["agents_used"])
    if not c_agents:
        raise ValueError("Agents (per user): no agents-used column. Headers: "
                         + " | ".join(headers))
    adopters = sum(1 for row in rows if to_int(row.get(c_agents)) >= 1)
    return {"agent_users": adopters, "rows": len(rows), "mapping": r.resolved}


def compute_agents_agent(path, base_users, overrides, warn):
    headers, rows = sniff_read(path)
    r = Resolver(headers, overrides)
    c_name = r.find("agent_name", CONCEPTS["agent_name"])
    c_users = r.find("active_users", CONCEPTS["active_users"])
    c_lic = r.find("active_users_licensed", CONCEPTS["active_users_licensed"])
    c_unlic = r.find("active_users_unlicensed", CONCEPTS["active_users_unlicensed"])
    if not c_name:
        raise ValueError("Agents (per agent): no agent-name column. Headers: "
                         + " | ".join(headers))

    def users_for(row):
        if c_users:
            return to_int(row.get(c_users))
        return to_int(row.get(c_lic)) + to_int(row.get(c_unlic))

    agents = [(str(row.get(c_name) or "").strip() or "Unnamed agent", users_for(row))
              for row in rows]
    agents = [a for a in agents if a[0]]
    total_instances = sum(u for _, u in agents)
    base = base_users if base_users and base_users > 0 else total_instances
    if not (base_users and base_users > 0):
        warn.append("Agents (per agent): no distinct agent-user base from the "
                    "per-user report — usage share is relative to total agent "
                    "instances instead of distinct users.")
    # users rides alongside the share so each bar can show the count on hover.
    share = sorted(
        ({"name": n, "pct": min(100, round(u / base * 100)) if base else 0, "users": u}
         for n, u in agents),
        key=lambda x: (x["pct"], x["users"]), reverse=True)[:TOP_N]
    return {"agentShare": share, "mapping": r.resolved}


def compute_chat(path, report_date, licensed_users, overrides, warn):
    headers, rows = sniff_read(path)
    r = Resolver(headers, overrides)
    ukey = r.user()
    c_prompts = r.find("chat_prompts", CONCEPTS["chat_prompts"])
    c_days = r.find("active_days", CONCEPTS["active_days"])
    c_last = r.find("last_activity", CONCEPTS["last_activity"])
    if not c_prompts and not c_days:
        raise ValueError("Copilot Chat: no prompts or active-days column. "
                         "Headers: " + " | ".join(headers))
    if not licensed_users:
        warn.append("Copilot Chat: no Copilot usage report to exclude licensed "
                    "users — every Chat-active user is treated as unlicensed.")

    unlicensed_active = warm = hot = cool = 0
    for row in rows:
        key = norm(row.get(ukey, "")) if ukey else ""
        if licensed_users and key and key in licensed_users:
            continue  # already a licensed in-app user
        p = to_int(row.get(c_prompts)) if c_prompts else 0
        d = to_int(row.get(c_days)) if c_days else 0
        if p < 1 and d < 1:
            continue
        unlicensed_active += 1
        last = parse_date(row.get(c_last)) if c_last else None
        recent = last is not None and (report_date - last).days <= 7
        if p >= 30 and d >= 8 and recent:
            hot += 1
        elif p >= 10 and d >= 3:
            warm += 1
        elif p >= 1 and d >= 1:
            cool += 1

    funnel = [
        {"name": "Unlicensed active", "value": unlicensed_active},
        {"name": "Warm+", "value": warm + hot},
        {"name": "Hot", "value": hot},
    ]
    return {"funnel": funnel, "conversion": warm + hot, "mapping": r.resolved}


# --------------------------------------------------------------------------- #
# Template injection
# --------------------------------------------------------------------------- #

def html_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def encode_logo(path, warn):
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        warn.append(f"Logo file not found ({path}); using the default mark.")
        return ""
    if p.suffix.lower() == ".svg":
        warn.append("SVG logos are not supported because they can contain active content; use PNG/JPG/GIF/WebP instead.")
        return ""
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp"}.get(
        p.suffix.lower(), "image/png")
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def inject(template_text, data, company):
    txt = template_text
    # 1. Remove the template's top explanatory HTML comment.
    txt = re.sub(r"<!--[\s\S]*?@DASHBOARD_DATA[\s\S]*?-->",
                 "<!-- Microsoft 365 Copilot Adoption dashboard "
                 "(generated from admin-center activity exports). -->",
                 txt, count=1)
    # 2. Company-specific <title> and header text node (the JS also sets it at
    #    runtime; replacing the static node leaves no template text in source).
    txt = re.sub(r"<title>[\s\S]*?</title>",
                 f"<title>{html_escape(company)} — Microsoft 365 Copilot Adoption</title>",
                 txt, count=1)
    txt = txt.replace('id="companyName">Company name</span>',
                      f'id="companyName">{html_escape(company)}</span>', 1)
    # 3. Replace the DASHBOARD_DATA block (field-guide comment + object).
    payload = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    block = ("/* Adoption metrics computed from the four Microsoft admin center "
             "report exports. */\nconst DASHBOARD_DATA = " + payload + ";")
    pattern = (r"/\*\s*@DASHBOARD_DATA:BEGIN[\s\S]*?\*/\s*"
               r"const\s+DASHBOARD_DATA\s*=\s*{[\s\S]*?};\s*"
               r"/\*\s*@DASHBOARD_DATA:END[\s\S]*?\*/")
    txt, n = re.subn(pattern, lambda _m: block, txt, count=1)
    if n == 0:
        raise ValueError("Could not locate @DASHBOARD_DATA markers in the template; template format may have changed.")
    txt = txt.replace(
        "  Data, company name and logo are supplied by the Cowork skill.",
        "  Source: Microsoft 365 admin center Copilot activity exports.")
    return txt


def check_no_template_refs(html):
    low = html.lower()
    hits = []
    for tok in TEMPLATE_TOKENS:
        # Ignore the JS fallback literal "company name" inside a || expression.
        if tok == "company name" and '|| "company name"' in low:
            continue
        if tok in low:
            hits.append(tok)
    return hits


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--company", required=True)
    ap.add_argument("--logo", default="")
    ap.add_argument("--usage")
    ap.add_argument("--agents-user", dest="agents_user")
    ap.add_argument("--agents-agent", dest="agents_agent")
    ap.add_argument("--chat")
    # Omit --period to use the window recorded in the exports' Report Period
    # column (MAC default 28 days); pass it only to force a different window.
    ap.add_argument("--period", type=int, default=None)
    ap.add_argument("--report-date", dest="report_date", default="")
    ap.add_argument("--col-map", dest="col_map", default="")
    ap.add_argument("--template", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    template_path = Path(args.template) if args.template else here.parent / "assets" / "dashboard_template.html"
    if not template_path.exists():
        print(json.dumps({"ok": False, "error": f"Template not found: {template_path}"}))
        sys.exit(1)

    col_map = {}
    if args.col_map:
        col_map = json.loads(Path(args.col_map).read_text(encoding="utf-8"))

    warn = []

    # ---- Resolve the reporting window and report date from the exports ----
    # Precedence: explicit flag > Copilot usage export > Copilot Chat export >
    # MAC default. The window feeds the dashboard badge/footer and the per-app
    # activity recency test, so it must reflect the data, not an assumption.
    scans = {}
    if args.usage:
        scans["Copilot usage"] = prescan(args.usage, col_map.get("usage"), "Copilot usage", warn)
    if args.chat:
        scans["Copilot Chat"] = prescan(args.chat, col_map.get("chat"), "Copilot Chat", warn)

    detected_period = detected_from = None
    for label, sc in scans.items():
        if sc["period"] is not None:
            detected_period, detected_from = sc["period"], label
            break
    periods_seen = {lbl: sc["period"] for lbl, sc in scans.items() if sc["period"] is not None}
    if len(set(periods_seen.values())) > 1:
        warn.append("Reports disagree on the window ("
                    + "; ".join(f"{k}: {v}d" for k, v in periods_seen.items())
                    + f") — used {detected_period} days from {detected_from}.")

    if args.period is not None:
        period = args.period
        period_source = "--period flag"
        if detected_period is not None and detected_period != period:
            warn.append(f"--period {period} overrides the {detected_period}-day "
                        f"window recorded in the {detected_from} export.")
    elif detected_period is not None:
        period = detected_period
        period_source = f"Report Period column ({detected_from})"
    else:
        period = DEFAULT_PERIOD
        period_source = f"default ({DEFAULT_PERIOD}-day MAC window)"
        if scans:
            warn.append("No Report Period column found in the exports; assumed "
                        f"the {DEFAULT_PERIOD}-day MAC default. Pass --period to set it.")

    report_date = parse_date(args.report_date) if args.report_date else None
    if args.report_date and report_date is None:
        warn.append(f"Could not parse --report-date '{args.report_date}'; "
                    "using the export's refresh date or today.")
    date_source = "--report-date flag" if report_date else None
    if report_date is None:
        for label, sc in scans.items():
            if sc["refresh_date"]:
                report_date, date_source = sc["refresh_date"], f"Report Refresh Date ({label})"
                break
    if report_date is None:
        report_date, date_source = date.today(), "today (no refresh date in the exports)"

    sources = {"usage": False, "agentsUser": False, "agentsAgent": False, "chat": False}
    kpis = {"activation": 0.0, "activationSub": "— source not provided",
            "habitual": 0, "multiSurface": 0, "agentAdoption": 0, "conversion": 0}
    segments = [{"name": s, "value": 0} for s in SEGMENT_ORDER]
    surfaces, agent_share, funnel = [], [], []
    mapping = {}
    licensed_users = set()
    agent_users = 0

    if args.usage:
        u = compute_usage(args.usage, report_date, period, col_map.get("usage"), warn)
        sources["usage"] = True
        kpis["activation"] = u["activation"]
        kpis["activationSub"] = u["activationSub"]
        kpis["habitual"] = u["habitual"]
        kpis["multiSurface"] = u["multiSurface"]
        segments = u["segments"]
        surfaces = u["surfaces"]
        licensed_users = u["users"]
        mapping["usage"] = u["mapping"]
    else:
        warn.append("No Copilot usage report — activation, habitual, segments and "
                    "surfaces are unavailable; those tiles/panels show as pending.")

    if args.agents_user:
        au = compute_agents_user(args.agents_user, col_map.get("agents_user"), warn)
        sources["agentsUser"] = True
        agent_users = au["agent_users"]
        base = u["assigned"] if args.usage else au["rows"]
        kpis["agentAdoption"] = round(agent_users / base * 100) if base else 0
        mapping["agents_user"] = au["mapping"]

    if args.agents_agent:
        aa = compute_agents_agent(args.agents_agent, agent_users, col_map.get("agents_agent"), warn)
        sources["agentsAgent"] = True
        agent_share = aa["agentShare"]
        mapping["agents_agent"] = aa["mapping"]

    if args.chat:
        ch = compute_chat(args.chat, report_date, licensed_users, col_map.get("chat"), warn)
        sources["chat"] = True
        funnel = ch["funnel"]
        kpis["conversion"] = ch["conversion"]
        mapping["chat"] = ch["mapping"]

    data = {
        "company": args.company,
        "logo": encode_logo(args.logo, warn),
        "reportDate": report_date.isoformat(),
        "periodDays": period,
        "sources": sources,
        "kpis": kpis,
        "segments": segments,
        "surfaces": surfaces,
        "agentShare": agent_share,
        "funnel": funnel,
    }

    template_text = template_path.read_text(encoding="utf-8")
    html = inject(template_text, data, args.company)
    leftover = check_no_template_refs(html)
    if leftover:
        warn.append("Template references still present after injection: "
                    + ", ".join(sorted(set(leftover))))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    summary = {
        "ok": True, "output": str(out_path), "company": args.company,
        "reportDate": data["reportDate"], "periodDays": period,
        "periodSource": period_source, "reportDateSource": date_source,
        "sources": sources, "kpis": kpis,
        "segments": segments, "surfaces": surfaces,
        "agentShare": agent_share, "funnel": funnel,
        "column_mapping": mapping, "warnings": warn,
        "template_reference_check": "clean" if not leftover else "leftover:" + ",".join(leftover),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
