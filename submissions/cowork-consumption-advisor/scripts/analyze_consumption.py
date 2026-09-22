#!/usr/bin/env python3
"""
Cowork & Work IQ Consumption Advisor - analysis engine.

Reads Microsoft 365 admin center exports (auto-detected by column headers, not file name):
  * Copilot > Cost Management > Consumption > Users            (user-level credits)
  * Copilot > Cost Management > Consumption > Groups           (group-level credits)
  * Copilot > Cost Management > Consumption > Agents & Services (service split, prepaid vs PAYG)
  * Copilot > Cost Management > Configuration > Spending policies
  * Copilot > Cowork > Usage > user details                    (tasks, active days)
  * Optional org/directory data (--org): Microsoft Graph user JSON (from
    /users?$select=...&$expand=manager) or a CSV with UPN, Department, Manager, JobTitle,
    Country/UsageLocation, CostCenter - enables per-department and per-manager reporting.

Produces:
  * <out>/consumption-analysis.json   - every computed figure (machine readable)
  * <out>/consumption-report.html     - self-contained interactive report (no CDN, works offline)
  * <out>/consumption-summary.md      - short executive summary for chat

Standard library only. Never modifies anything in the tenant - reporting only.

Usage:
  python analyze_consumption.py --input <folder-or-files...> --out <folder>
        [--rate 0.01] [--prepaid-rate 0.008] [--currency USD]
        [--period auto|monthly|ytd] [--near-limit 0.8] [--dormant-days 30]
        [--org <folder-or-files of Graph JSON / org CSV>]
        [--tenant-name Contoso] [--title "Contoso - Cowork consumption"] [--anonymize]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import hashlib
import hmac
import html
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

# --------------------------------------------------------------------------- helpers

INVISIBLE = re.compile(r"[\u200e\u200f\u202a-\u202e\ufeff\u00a0]")


def clean(s):
    if s is None:
        return ""
    return INVISIBLE.sub("", str(s)).strip()


def norm_key(s):
    return re.sub(r"[^a-z0-9]", "", clean(s).lower())


def to_int(v, default=0):
    s = clean(v).replace(",", "")
    if s in ("", "-", "—", "–"):
        return default
    m = re.search(r"-?\d+(\.\d+)?", s)
    return int(float(m.group())) if m else default


def to_float(v, default=0.0):
    s = clean(v).replace(",", "").replace("%", "")
    if s in ("", "-", "—", "–"):
        return default
    m = re.search(r"-?\d+(\.\d+)?", s)
    return float(m.group()) if m else default


def to_date(v):
    s = clean(v)
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s[:26], fmt).date()
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    rows = [r for r in rows if any(clean(c) for c in r)]
    if not rows:
        return [], []
    header = [clean(h) for h in rows[0]]
    keys = [norm_key(h) for h in header]
    out = []
    for r in rows[1:]:
        r = list(r) + [""] * (len(keys) - len(r))
        out.append({k: r[i] for i, k in enumerate(keys)})
    return header, out


# --------------------------------------------------------------------------- detection

SIGNATURES = {
    # type: set of normalised columns that must ALL be present
    "users": {"userprincipalname", "monthlycreditsused"},
    "groups": {"groupid", "monthlycreditsused"},
    "services": {"servicename", "monthlycreditsused"},
    "policies": {"spendingpolicy", "creditsused"},
    "cowork_usage": {"userprincipalname", "totaltasks"},
    "org": {"userprincipalname"},   # plus department / manager - see detect_type
}


def detect_type(keys):
    ks = set(keys)
    # users export also has 'userid'; cowork usage has 'totaltasks'
    for t in ("cowork_usage", "services", "groups", "policies", "users"):
        if SIGNATURES[t] <= ks:
            return t
    if "userprincipalname" in ks and ks & {"department", "manager", "managerdisplayname", "managerupn", "jobtitle", "costcenter"}:
        return "org"
    return None


def collect_inputs(inputs, exts=(".csv",)):
    files = []
    for p in inputs:
        if os.path.isdir(p):
            for e in exts:
                files += sorted(glob.glob(os.path.join(p, "**", "*" + e), recursive=True))
        else:
            files += glob.glob(p)
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


# --------------------------------------------------------------------------- parsing


def parse_users(rows):
    users = []
    for r in rows:
        upn = clean(r.get("userprincipalname"))
        if not upn:
            continue
        limit = to_int(r.get("monthlycreditlimit"), 0)
        used = to_int(r.get("monthlycreditsused"), 0)
        users.append({
            "displayName": clean(r.get("displayname")) or upn,
            "upn": upn,
            "upnKey": upn.lower(),
            "limit": limit,
            "used": used,
            "pctUsed": round(used / limit * 100, 1) if limit > 0 else None,
            "licensed": clean(r.get("microsoft365copilotlicense")).lower() in ("yes", "true", "1"),
            "lastActivity": to_date(r.get("lastactivitydate")),
            "sessions": to_int(r.get("sessioncount"), 0),
        })
    return users


def parse_groups(rows):
    groups = []
    for r in rows:
        name = clean(r.get("displayname"))
        gid = clean(r.get("groupid"))
        if not name:
            name = "(No group - default / direct policy)" if gid.strip("0-") == "" else f"(Unnamed group {gid[:8]})"
        groups.append({
            "name": name,
            "groupId": gid,
            "totalUsers": to_int(r.get("totalusers"), 0),
            "used": to_int(r.get("monthlycreditsused"), 0),
            "membersUsed": to_int(r.get("membersthatusedcredits"), 0),
            "avgPerUserPerDay": to_float(r.get("avgcreditsperuserperday"), 0.0),
            "sessions": to_int(r.get("sessioncount"), 0),
            "lastActivity": to_date(r.get("lastactivitydate")),
        })
    return groups


def parse_services(rows):
    services = []
    for r in rows:
        name = clean(r.get("servicename"))
        if not name:
            continue
        services.append({
            "name": name,
            "activeUsers": to_int(r.get("activeusers"), 0),
            "used": to_int(r.get("monthlycreditsused"), 0),
            "prepaid": to_int(r.get("prepaidcreditsused"), 0),
            "payg": to_int(r.get("payasyougocreditsused"), 0),
            "lastActivity": to_date(r.get("lastactivitydate")),
        })
    return services


def parse_policies(rows):
    pols = []
    for r in rows:
        name = clean(r.get("spendingpolicy"))
        if not name:
            continue
        limit_raw = clean(r.get("currentspendinglimit"))
        limit_missing = limit_raw == ""
        unlimited = limit_raw.lower().startswith("no limit")
        limit = None if (unlimited or limit_missing) else to_int(limit_raw, 0)
        used = to_int(r.get("creditsused"), 0)
        rate = to_float(r.get("creditusagerate"), 0.0) if not (unlimited or limit_missing) else None
        if not unlimited and limit and rate == 0.0:
            rate = round(used / limit * 100, 1)
        pols.append({
            "name": name,
            "appliesTo": clean(r.get("appliesto")),
            "activeUsers": to_int(r.get("activeusers"), 0),
            "used": used,
            "limit": limit,
            "unlimited": unlimited,
            "limitMissing": limit_missing,
            "usageRate": rate,
            "billingMethod": clean(r.get("billingmethod")),
            "status": clean(r.get("policystatus")) or "Active",
        })
    return pols


def parse_cowork_usage(rows):
    out = []
    for r in rows:
        upn = clean(r.get("userprincipalname"))
        if not upn:
            continue
        out.append({
            "upn": upn,
            "upnKey": upn.lower(),
            "displayName": clean(r.get("displayname")) or upn,
            "totalTasks": to_int(r.get("totaltasks"), 0),
            "scheduledTasks": to_int(r.get("scheduledtasks"), 0),
            "userInitiatedTasks": to_int(r.get("userinitiatedtasks"), 0),
            "activeDays": to_int(r.get("activedays"), 0),
            "lastActivity": to_date(r.get("lastactivitydate")),
        })
    return out


def parse_org_rows(rows):
    """Org attributes from a CSV (Entra 'Download users' export or hand-made mapping)."""
    out = {}
    for r in rows:
        upn = clean(r.get("userprincipalname"))
        if not upn:
            continue
        out[upn.lower()] = {
            "upn": upn,
            "department": clean(r.get("department")) or "",
            "jobTitle": clean(r.get("jobtitle")) or "",
            "manager": clean(r.get("manager")) or clean(r.get("managerdisplayname")) or "",
            "managerUpn": clean(r.get("managerupn")) or clean(r.get("manageruserprincipalname")) or "",
            "country": clean(r.get("country")) or clean(r.get("usagelocation")) or "",
            "office": clean(r.get("officelocation")) or "",
            "costCenter": clean(r.get("costcenter")) or "",
        }
    return out


def parse_org_json(path):
    """Org attributes from Microsoft Graph JSON: a user object, a list, or {"value": [...]}."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        doc = json.load(fh)
    items = doc.get("value", [doc]) if isinstance(doc, dict) else doc
    out = {}
    for u in items:
        if not isinstance(u, dict):
            continue
        upn = clean(u.get("userPrincipalName") or u.get("mail") or "")
        if not upn:
            continue
        mgr = u.get("manager") or {}
        out[upn.lower()] = {
            "upn": upn,
            "department": clean(u.get("department") or ""),
            "jobTitle": clean(u.get("jobTitle") or ""),
            "manager": clean(mgr.get("displayName") or ""),
            "managerUpn": clean(mgr.get("userPrincipalName") or ""),
            "country": clean(u.get("country") or u.get("usageLocation") or ""),
            "office": clean(u.get("officeLocation") or ""),
            "costCenter": clean(u.get("costCenter") or ""),
        }
        # Graph returns mail alias too - index it so display-email UPNs in exports still match
        mail = clean(u.get("mail") or "")
        if mail and mail.lower() != upn.lower():
            out[mail.lower()] = out[upn.lower()]
    return out


def load_org(paths):
    org = {}
    for p in collect_inputs(paths, exts=(".csv", ".json")):
        if p.lower().endswith(".json"):
            org.update(parse_org_json(p))
        else:
            header, rows = read_csv(p)
            if detect_type([norm_key(x) for x in header]) == "org":
                org.update(parse_org_rows(rows))
    return org


def rollup(users, key_fn, label_unknown, near_pct=80):
    """Aggregate user rows by an org attribute."""
    agg = {}
    for u in users:
        k = key_fn(u) or label_unknown
        a = agg.setdefault(k, {"name": k, "users": 0, "consuming": 0, "used": 0, "tasks": 0, "sessions": 0,
                               "nearOrOver": 0, "topUser": None, "members": []})
        a["users"] += 1
        a["consuming"] += 1 if u["used"] > 0 else 0
        a["used"] += u["used"]
        a["tasks"] += u.get("tasks") or 0
        a["sessions"] += u["sessions"]
        if u["pctUsed"] is not None and u["pctUsed"] >= near_pct:
            a["nearOrOver"] += 1
        if a["topUser"] is None or u["used"] > a["topUser"]["used"]:
            a["topUser"] = u
        a["members"].append(u["upn"])
    total = sum(a["used"] for a in agg.values()) or 1
    rows = []
    for a in agg.values():
        rows.append({**a, "share": round(a["used"] / total * 100, 1),
                     "avgPerUser": round(a["used"] / a["users"]) if a["users"] else 0,
                     "creditsPerTask": round(a["used"] / a["tasks"]) if a["tasks"] else None,
                     "topUser": a["topUser"]["displayName"] if a["topUser"] else "", "members": len(a["members"])})
    rows.sort(key=lambda r: -r["used"])
    return rows


# --------------------------------------------------------------------------- analysis


def pct(a, b):
    return round(a / b * 100, 1) if b else None


def md_escape(value):
    s = clean(value).replace("\r", " ").replace("\n", " ")
    s = html.escape(s, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>])", r"\\\1", s)


_PSEUDONYM_SECRET = os.urandom(32)  # per-run secret; never written to any output


def pseudonym(prefix, key, width=10):
    """Stable within one report run, unlinkable across runs and not brute-forceable without the secret."""
    digest = hmac.new(_PSEUDONYM_SECRET, key.lower().encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix} {digest[:width]}"


def anonymize_data(data):
    """Replace every personal identifier before analysis so JSON, HTML and Markdown are all masked.
    Pseudonyms are keyed HMACs with a random per-run secret: consistent inside this report, not
    reproducible from a directory listing, and different on every run."""
    for u in data.get("users", []):
        u["displayName"] = pseudonym("User", u["upnKey"])
        u["upn"] = pseudonym("user", u["upnKey"]).replace(" ", "") + "@hidden"
    for x in data.get("cowork_usage", []):
        x["displayName"] = pseudonym("User", x["upnKey"])
        x["upn"] = pseudonym("user", x["upnKey"]).replace(" ", "") + "@hidden"
    for g in data.get("groups", []):
        g["_rawName"] = g.get("name", "")
        if g.get("name"):
            g["name"] = pseudonym("Group", g["name"], 8)
        if g.get("groupId"):
            g["groupId"] = pseudonym("group", g["groupId"], 8).replace(" ", "")
    for p in data.get("policies", []):
        p["_rawName"] = p.get("name", "")
        p["_rawAppliesTo"] = p.get("appliesTo", "")
        p["_rawBillingMethod"] = p.get("billingMethod", "")
        p["tenantWide"] = p["_rawAppliesTo"].lower().startswith("all users")
        if p.get("name"):
            p["name"] = pseudonym("Policy", p["name"], 8)
        if p.get("appliesTo"):
            p["appliesTo"] = pseudonym("Scope", p["appliesTo"], 8)
        if p.get("billingMethod"):
            p["billingMethod"] = pseudonym("Billing", p["billingMethod"], 8)
    seen_org = set()
    for k, o in (data.get("org") or {}).items():
        if id(o) in seen_org:
            continue
        seen_org.add(id(o))
        manager_key = o.get("managerUpn") or o.get("manager") or ""
        user_key = o.get("upn") or k
        o["manager"] = pseudonym("Manager", manager_key, 8) if manager_key else ""
        o["managerUpn"] = pseudonym("manager", manager_key, 8).replace(" ", "") + "@hidden" if manager_key else ""
        o["upn"] = pseudonym("user", user_key).replace(" ", "") + "@hidden"
        for field, prefix in (("department", "Department"), ("jobTitle", "Job"), ("country", "Location"),
                              ("office", "Office"), ("costCenter", "CostCenter")):
            if o.get(field):
                o[field] = pseudonym(prefix, o[field], 8)
    return data


def analyze(data, args, as_of):
    if args.anonymize:
        data = anonymize_data(data)
    users = data.get("users", [])
    groups = data.get("groups", [])
    services = data.get("services", [])
    policies = data.get("policies", [])
    usage = data.get("cowork_usage", [])
    notes = []      # data-quality / caveats
    recs = []       # recommendations (evidence-backed)

    # ---- totals -----------------------------------------------------------
    svc_total = sum(s["used"] for s in services)
    user_total = sum(u["used"] for u in users)
    total = svc_total or user_total
    prepaid = sum(s["prepaid"] for s in services)
    payg = sum(s["payg"] for s in services)
    rate_basis = "default PAYG list rate" if args.rate == 0.01 else "configured PAYG rate"
    prepaid_basis = "default prepaid rate" if args.prepaid_rate == 0.008 else "configured prepaid rate"
    if services and users and abs(svc_total - user_total) > max(50, 0.02 * max(svc_total, 1)):
        notes.append(
            f"Users export totals {user_total:,} credits vs {svc_total:,} in the services export "
            f"({pct(user_total, svc_total)}%). Exports are point-in-time snapshots taken at different moments, "
            "and per-user rows only show usage under each user's CURRENT policy.")

    split_valid = bool(services) and (prepaid + payg) > 0 and abs((prepaid + payg) - svc_total) <= max(5, 0.01 * svc_total)
    list_cost = total * args.rate
    if split_valid:
        est_cost = payg * args.rate + prepaid * args.prepaid_rate
        cost_basis = f"blended: pay-as-you-go at {rate_basis}, prepaid at {prepaid_basis}"
    else:
        est_cost = list_cost
        cost_basis = f"{rate_basis} on all credits (prepaid / pay-as-you-go split not available)"
        if services:
            notes.append("Prepaid vs pay-as-you-go split missing or inconsistent in the services export; the estimated "
                         f"cost falls back to {rate_basis} on all credits.")

    # ---- period & forecast ------------------------------------------------
    dates = [u["lastActivity"] for u in users if u["lastActivity"]] + \
            [x["lastActivity"] for x in usage if x["lastActivity"]]
    first_act = min(dates) if dates else None
    last_act = max(dates) if dates else None
    # The Consumption exports carry "Monthly credits used" - a current-billing-month snapshot - so the
    # default is a monthly projection. --period ytd is only valid when the export really is cumulative
    # (e.g. a YTD filter in the admin center) and then uses the calendar year, not the first activity.
    period_mode = "monthly" if args.period == "auto" else args.period
    forecast = {"mode": period_mode}
    if period_mode == "monthly":
        start = as_of.replace(day=1)
        nxt = (start + dt.timedelta(days=32)).replace(day=1)
        days_in = (nxt - start).days
        elapsed = max(1, (as_of - start).days + 1)
        daily = total / elapsed
        forecast.update({
            "periodStart": start.isoformat(), "periodEnd": (nxt - dt.timedelta(days=1)).isoformat(),
            "daysElapsed": elapsed, "daysInPeriod": days_in,
            "dailyRunRate": round(daily), "projectedPeriodTotal": round(daily * days_in),
            "projectedCost": round(daily * days_in * args.rate, 2),
        })
    else:
        # explicit year-to-date view: calendar-year start to the export date
        start = dt.date(as_of.year, 1, 1)
        elapsed_days = max(1, (as_of - start).days + 1)
        months = elapsed_days / 30.44
        daily = total / elapsed_days
        forecast.update({
            "periodStart": start.isoformat(), "periodEnd": as_of.isoformat(),
            "daysElapsed": elapsed_days, "monthsElapsed": round(months, 2),
            "dailyRunRate": round(daily), "monthlyRunRate": round(daily * 30.44),
            "annualisedCredits": round(daily * 365), "annualisedCost": round(daily * 365 * args.rate, 2),
        })
        notes.append(f"Year-to-date mode (--period ytd): run-rates assume the credit figures are cumulative from "
                     f"{start.isoformat()} to {as_of.isoformat()}. Use this only for exports taken with a YTD filter.")
    if first_act and last_act and (last_act - first_act).days > 40 and period_mode == "monthly":
        notes.append("User last-activity dates span more than 40 days while credit figures are monthly snapshots; the "
                     "projection covers the current billing month only. Re-run with --period ytd if the export was "
                     "taken with a year-to-date filter.")
    # ---- users -------------------------------------------------------------
    users_sorted = sorted(users, key=lambda u: -u["used"])
    consuming = [u for u in users if u["used"] > 0]
    n_users = len(users)
    top10 = users_sorted[:10]
    top10_share = pct(sum(u["used"] for u in top10), user_total)
    k20 = math.ceil(len(consuming) / 5) if consuming else 0
    top20pct_share = pct(sum(u["used"] for u in users_sorted[:k20]), user_total)
    near = [u for u in users if u["pctUsed"] is not None and args.near_limit * 100 <= u["pctUsed"] < 100]
    over = [u for u in users if u["pctUsed"] is not None and u["pctUsed"] >= 100]
    unlicensed = [u for u in users if not u["licensed"] and u["used"] > 0]
    dormant = [u for u in consuming if u["lastActivity"] and (as_of - u["lastActivity"]).days > args.dormant_days]
    limit_tiers = defaultdict(lambda: {"users": 0, "used": 0})
    for u in users:
        t = limit_tiers[u["limit"]]
        t["users"] += 1
        t["used"] += u["used"]
    tiers = [{"limit": k, "users": v["users"], "used": v["used"],
              "avgUsed": round(v["used"] / v["users"]) if v["users"] else 0,
              "avgPctOfLimit": pct(v["used"] / v["users"], k) if (k and v["users"]) else None}
             for k, v in sorted(limit_tiers.items(), key=lambda kv: -(kv[0] or 0))]
    def median(vals):
        vals = sorted(vals)
        n = len(vals)
        if not n:
            return 0
        return vals[n // 2] if n % 2 else round((vals[n // 2 - 1] + vals[n // 2]) / 2)
    median_used = median(u["used"] for u in consuming)

    if over:
        notes.append(f"{len(over)} user(s) show usage above 100% of their current limit. This normally means the limit "
                     "was lowered, or the user moved policy, mid-period - the Consumption view shows the CURRENT limit "
                     "against ALL credits used this period. Usage above a per-user soft limit is not billed and is not "
                     "shown as consumed.")
    if unlicensed:
        notes.append(f"{len(unlicensed)} consuming user(s) have no Microsoft 365 Copilot licence flag - verify their "
                     "entitlement; Cowork access normally requires the licence.")

    # ---- cowork usage join -------------------------------------------------
    usage_by = {x["upnKey"]: x for x in usage}
    user_keys = {u["upnKey"] for u in users}
    joined, tasks_total = [], sum(x["totalTasks"] for x in usage)
    sched_total = sum(x["scheduledTasks"] for x in usage)
    matched = 0
    for u in users:
        x = usage_by.get(u["upnKey"])
        if x:
            matched += 1
            u["tasks"] = x["totalTasks"]
            u["scheduledTasks"] = x["scheduledTasks"]
            u["activeDays"] = x["activeDays"]
            u["creditsPerTask"] = round(u["used"] / x["totalTasks"]) if x["totalTasks"] else None
            joined.append(u)
    task_joined = [u for u in joined if u["tasks"] > 0]
    tasks_matched = sum(u["tasks"] for u in task_joined)
    credits_matched = sum(u["used"] for u in task_joined)
    credits_per_task = round(credits_matched / tasks_matched) if tasks_matched else None
    usage_only = [x for x in usage if x["upnKey"] not in user_keys]
    credits_only = [u for u in users if u["upnKey"] not in usage_by and usage]
    if usage and users:
        notes.append(f"Matched {matched} of {n_users} consuming users to the Cowork usage export; "
                     f"{len(usage_only)} Cowork users have tasks but no credit row (activity before metering, or a "
                     f"different snapshot window) and {len(credits_only)} credit rows have no task row.")
    scheduled_share = pct(sched_total, tasks_total)
    heavy_sched = [x for x in usage if x["totalTasks"] >= 5 and x["scheduledTasks"] / x["totalTasks"] >= 0.5]

    # ---- org enrichment (Graph / directory) ---------------------------------
    org = data.get("org") or {}
    enriched = 0
    for u in users:
        o = org.get(u["upnKey"])
        if o:
            enriched += 1
        u["department"] = (o or {}).get("department", "")
        u["manager"] = (o or {}).get("manager", "")
        u["managerUpn"] = (o or {}).get("managerUpn", "")
        u["jobTitle"] = (o or {}).get("jobTitle", "")
        u["country"] = (o or {}).get("country", "")
        u["costCenter"] = (o or {}).get("costCenter", "")
    unknown_dept = "(Unknown - not in directory)"
    near_pct = args.near_limit * 100
    consuming_for_rollup = [u for u in users if u["used"] > 0]
    departments = rollup(consuming_for_rollup, lambda u: u.get("department"), unknown_dept, near_pct) if org else []
    # key managers by UPN (two managers can share a display name); label with the display name
    mgr_label = {}
    for u in consuming_for_rollup:
        k = (u.get("managerUpn") or u.get("manager") or "").lower()
        if k:
            mgr_label.setdefault(k, u.get("manager") or u.get("managerUpn"))
    managers = rollup(consuming_for_rollup, lambda u: (u.get("managerUpn") or u.get("manager") or "").lower(), "(No manager found)", near_pct) if org else []
    for m in managers:
        m["managerUpn"] = m["name"] if "@" in m["name"] else ""
        m["name"] = mgr_label.get(m["name"], m["name"])
    countries = rollup(consuming_for_rollup, lambda u: u.get("country"), "(Unknown)", near_pct) if org and any(u.get("country") for u in users) else []
    if org:
        notes.append(f"Directory enrichment: {enriched} of {n_users} consuming users matched to department/manager data "
                     f"({pct(enriched, n_users)}%). Unmatched users are grouped under '{unknown_dept}'.")
    elif users:
        notes.append("No directory data supplied (--org): department and manager views are unavailable. Collect it with "
                     "Microsoft Graph (/users?$expand=manager) or an Entra user export and re-run.")

    # ---- groups --------------------------------------------------------------
    groups_sorted = sorted(groups, key=lambda g: -g["used"])
    group_total = sum(g["used"] for g in groups)
    for g in groups:
        g["activationRate"] = pct(g["membersUsed"], g["totalUsers"]) if g["totalUsers"] else None
        g["share"] = pct(g["used"], group_total)
    group_name_counts = Counter(g.get("name") for g in groups)
    dup_names = [n for n, c in group_name_counts.items() if n and c > 1]
    if groups and services and group_total > svc_total * 1.05:
        notes.append(f"Group credits sum to {group_total:,} vs {svc_total:,} total - users belong to several groups, "
                     "so group figures overlap and must not be added together.")
    if dup_names:
        notes.append("Groups with the same display name but different IDs: " + ", ".join(sorted(dup_names)) +
                     ". Shown separately; consider renaming for clarity.")
    unassigned = [g for g in groups if (g.get("_rawName") or g["name"]).startswith("(No group")]

    # ---- policies -------------------------------------------------------------
    pol_total = sum(p["used"] for p in policies)
    unlimited = [p for p in policies if p["unlimited"] and p["status"].lower() == "active"]
    active_pol_total = sum(p["used"] for p in policies if p["status"].lower() == "active")
    unlimited_share = pct(sum(p["used"] for p in unlimited), active_pol_total)
    near_pol = [p for p in policies if p["usageRate"] is not None and p["usageRate"] >= args.near_limit * 100
                and p["status"].lower() == "active"]
    idle_pol = [p for p in policies if p["used"] == 0 and p["status"].lower() == "active"]
    tenant_wide = [p for p in policies if p.get("tenantWide") or p["appliesTo"].lower().startswith("all users")]
    methods = sorted({p["billingMethod"] for p in policies if p["billingMethod"]})
    missing_limit = [p for p in policies if p.get("limitMissing")]
    if missing_limit:
        notes.append(f"{len(missing_limit)} spending policy row(s) have a blank current spending limit; they are treated as unknown, not unlimited.")

    # ---- recommendations (each with evidence) --------------------------------
    def rec(priority, title, evidence, action):
        recs.append({"priority": priority, "title": title, "evidence": evidence, "action": action})

    if unlimited:
        rec("High", "Cap the unlimited spending policies",
            f"{len(unlimited)} active policies have no monthly limit and carry {unlimited_share}% of policy-attributed "
            f"credits ({sum(p['used'] for p in unlimited):,}). "
            + ("All are billed pay-as-you-go, so exposure is uncapped." if all("pay-as-you-go" in (p.get("_rawBillingMethod") or p["billingMethod"]).lower() for p in unlimited)
               else "Billing methods: " + ", ".join(sorted({p["billingMethod"].split(" (")[0] or "unknown" for p in unlimited})) + "."),
            "Set a policy-level monthly limit at roughly 1.3x the observed run-rate for each policy, keep per-user limits, "
            "and add alert recipients at 80%. Limits stop spend; alerts only warn.")
    if near_pol:
        rec("High", "Policies approaching their limit",
            "; ".join(f"{p['name']} at {p['usageRate']}% of {p['limit']:,}" for p in near_pol),
            "Decide before the cap is hit: raise the limit for the group, or accept that users lose access until the 1st of "
            "next month. Users can request credits from inside Cowork; route those requests to the right approver.")
    if over or near:
        rec("Medium", "Users at or over their personal limit",
            f"{len(over)} users over 100% and {len(near)} users between {int(args.near_limit*100)}% and 100% of their "
            f"current limit. Top: " + ", ".join(f"{u['displayName']} ({u['pctUsed']}%)" for u in (over + near)[:5]),
            "Review whether these users sit in the right policy tier. If value is proven (high tasks, high active days) move "
            "them up a tier; if usage is exploratory, leave the soft limit - it does not interrupt running tasks.")
    if top20pct_share and top20pct_share >= 60:
        rec("Medium", "Consumption is concentrated in a few users",
            f"Top {k20} users ({pct(k20, len(consuming))}% of consuming users) account for {top20pct_share}% of credits; "
            f"top 10 = {top10_share}%. Median consuming user: {median_used:,} credits.",
            "Interview the heavy users - they are your best evidence of value AND your biggest cost driver. Turn their "
            "repeatable tasks into shared skills/apps so the whole group benefits at lower marginal credits.")
    if split_valid and services and prepaid and payg:
        rec("Medium", "Prepaid vs pay-as-you-go mix",
            f"{pct(prepaid, svc_total)}% of credits came from prepaid capacity, {pct(payg, svc_total)}% from pay-as-you-go "
            f"({payg:,} credits ~ {args.currency} {payg*args.rate:,.2f} at {rate_basis}).",
            "If the pay-as-you-go tail is steady month over month, size additional capacity packs or a Copilot Credit "
            "pre-purchase plan (P3) to cover the floor of usage - prepaid rates are discounted; keep PAYG for the peak.")
    elif split_valid and services and payg and not prepaid:
        rec("Medium", "Everything is billed pay-as-you-go",
            f"{payg:,} credits (~{args.currency} {payg*args.rate:,.2f}) at {rate_basis} with no prepaid capacity in use.",
            "Once 2-3 months of steady usage exist, compare against capacity packs / P3 pre-purchase; steady usage is "
            "cheaper prepaid, and MACC-eligible when billed through the right Azure subscription.")
    if credits_per_task:
        hi = [u for u in joined if u.get("creditsPerTask") and u["creditsPerTask"] > 3 * credits_per_task and u["tasks"] >= 3]
        rec("Low", "Credits per task is the efficiency KPI to track",
            f"Blended {credits_per_task:,} credits per Cowork task across the {tasks_matched:,} tasks of the {matched} users "
            f"present in both exports (of {tasks_total:,} tasks in the usage export). "
            + (f"{len(hi)} users run at more than 3x that average (e.g. " + ", ".join(f"{u['displayName']} {u['creditsPerTask']:,}" for u in hi[:3]) + ")." if hi else "No extreme outliers."),
            "Publish the blended figure monthly. Coach heavy-per-task users on scoping prompts, using included Copilot Chat "
            "for single-output asks, and checking /cost inside Cowork before long-running tasks.")
    if heavy_sched:
        rec("Low", "Scheduled tasks drive part of the bill",
            f"{scheduled_share}% of all Cowork tasks are scheduled; {len(heavy_sched)} users run mostly scheduled tasks "
            f"(e.g. " + ", ".join(f"{x['displayName']} {x['scheduledTasks']}/{x['totalTasks']}" for x in heavy_sched[:3]) + ").",
            "Audit recurring schedules quarterly - stale automations keep burning credits with no reader.")
    if idle_pol:
        rec("Low", "Idle spending policies",
            ", ".join(f"{p['name']} ({p['appliesTo']}, limit {p['limit'] if p['limit'] is not None else 'none'})" for p in idle_pol),
            "Remove or pause policies with zero usage to keep the configuration auditable; a tenant-wide idle policy with a "
            "limit can still grant access you did not intend.")
    if dormant:
        rec("Low", "Dormant consumers",
            f"{len(dormant)} users have not used credits in over {args.dormant_days} days but consumed {sum(u['used'] for u in dormant):,} credits earlier.",
            "Not a cost problem today, but a value problem: re-engage with enablement or reclaim their policy slot.")
    if departments:
        known = [d for d in departments if d["name"] != unknown_dept]
        if known and known[0]["share"] >= 50:
            d = known[0]
            rec("Medium", f"One department drives the spend: {d['name']}",
                f"{d['name']} accounts for {d['share']}% of credits ({d['used']:,}) from {d['consuming']} consuming users; "
                f"top user {d['topUser']}.",
                "Give this department its own spending policy and security group so its budget, limits and alerts are explicit, "
                "and use the figure for showback/chargeback.")
        if len(known) >= 3:
            spread = sorted(known, key=lambda d: -(d["avgPerUser"]))
            rec("Low", "Departments differ widely in credits per user",
                "; ".join(f"{d['name']} {d['avgPerUser']:,}/user" for d in spread[:3]) + " vs " +
                "; ".join(f"{d['name']} {d['avgPerUser']:,}/user" for d in spread[-2:]),
                "Pair the high-intensity departments with the low ones for enablement - the use cases that consume most are "
                "usually the ones worth spreading, and per-user tiers should follow department intensity.")
    if managers:
        hot = [m for m in managers if m["nearOrOver"] >= 2 and not m["name"].startswith("(")]
        if hot:
            rec("Medium", "Managers with several team members near or over their limit",
                "; ".join(f"{m['name']}: {m['nearOrOver']} of {m['users']} users, {m['used']:,} credits" for m in hot[:4]),
                "Send each manager their team's view and ask them to confirm which users should move up a tier - managers, "
                "not admins, know whether the work justifies the credits.")
    if unassigned:
        rec("Low", "Consumption outside any named group",
            f"{unassigned[0]['used']:,} credits from {unassigned[0]['membersUsed']} users are attributed to no group "
            "(default policy / direct assignment).",
            "Move these users into a named security group so chargeback and limits are explicit.")

    prio = {"High": 0, "Medium": 1, "Low": 2}
    recs.sort(key=lambda r: prio[r["priority"]])

    def ser(o):
        if isinstance(o, (dt.date, dt.datetime)):
            return o.isoformat()
        raise TypeError

    def strip_keys(obj):
        """Remove internal join keys so the JSON never carries a raw identifier when --anonymize is on."""
        if isinstance(obj, dict):
            return {k: strip_keys(v) for k, v in obj.items() if k != "upnKey" and not k.startswith("_raw")}
        if isinstance(obj, list):
            return [strip_keys(x) for x in obj]
        return obj

    result = {
        "meta": {
            "title": "Anonymized Cowork & Work IQ Consumption Report" if args.anonymize else args.report_title,
            "asOf": as_of.isoformat(), "currency": args.currency,
            "paygRate": args.rate, "prepaidRate": args.prepaid_rate,
            "paygRateBasis": rate_basis, "prepaidRateBasis": prepaid_basis,
            "inputs": {k: ("<redacted>" if args.anonymize else v) for k, v in data.get("_files", {}).items()},
            "anonymized": bool(args.anonymize), "nearLimitThreshold": round(args.near_limit * 100),
            "generatedBy": "cowork-consumption-advisor/analyze_consumption.py",
        },
        "headline": {
            "totalCredits": total, "prepaidCredits": prepaid, "paygCredits": payg,
            "prepaidShare": pct(prepaid, svc_total) if split_valid else None,
            "listCost": round(list_cost, 2), "estimatedCost": round(est_cost, 2), "costBasis": cost_basis,
            "splitAvailable": split_valid,
            "activeUsers": len(consuming) if users else (services[0]["activeUsers"] if len(services) == 1 else sum(s["activeUsers"] for s in services)),
            "activeUsersBasis": ("distinct consuming users (Users export)" if users else
                                 ("service active users" if len(services) == 1 else
                                  "sum of per-service active users - NOT de-duplicated across services")),
            "consumingUsers": len(consuming), "creditsPerActiveUser": round(user_total / len(consuming)) if consuming else None,
            "medianCreditsPerUser": median_used, "creditsPerTask": credits_per_task,
            "totalTasks": tasks_total, "scheduledTaskShare": scheduled_share,
            "matchedTasks": tasks_matched, "matchedTaskUsers": matched,
            "firstActivity": first_act, "lastActivity": last_act,
        },
        "forecast": forecast,
        "services": services,
        "policies": {"rows": policies, "total": pol_total, "activeTotal": active_pol_total,
                 "unlimitedCount": len(unlimited), "unlimitedShare": unlimited_share,
                     "nearLimit": [p["name"] for p in near_pol], "idle": [p["name"] for p in idle_pol],
                     "tenantWide": [p["name"] for p in tenant_wide], "billingMethods": methods},
        "groups": {"rows": groups_sorted, "sumOfGroups": group_total, "duplicateNames": dup_names},
        "users": {
            "count": n_users, "total": user_total, "top10": top10, "top10Share": top10_share,
            "top20pctShare": top20pct_share, "top20pctCount": k20,
            "nearLimit": near, "overLimit": over, "unlicensed": unlicensed, "dormant": dormant,
            "limitTiers": tiers, "all": users_sorted,
        },
        "org": {"provided": bool(org), "enrichedUsers": enriched, "coverage": pct(enriched, n_users),
                "departments": departments, "managers": managers, "countries": countries},
        "coworkUsage": {"rows": usage, "totalTasks": tasks_total, "scheduledTasks": sched_total,
                        "matchedUsers": matched, "usageOnly": usage_only, "creditsOnly": [u["upn"] for u in credits_only],
                        "heavyScheduled": heavy_sched},
        "recommendations": recs,
        "dataQuality": notes,
    }
    return strip_keys(json.loads(json.dumps(result, default=ser)))


# --------------------------------------------------------------------------- rendering

CSS = """
:root{--b:#0f6cbd;--bg:#f5f6f8;--card:#fff;--t:#1b1b1f;--m:#616161;--line:#e5e7eb;--ok:#107c10;--warn:#835b00;--bad:#a80000;--teal:#0b8a8a;--orange:#f7a600;--purple:#7a3e9d;--red:#c43e1c}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif;color:var(--t);background:var(--bg)}
header{background:linear-gradient(120deg,#0f3d6e,#0f6cbd);color:#fff;padding:28px 32px}header h1{margin:0 0 6px;font-size:24px}header p{margin:0;opacity:.9}
nav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);padding:8px 32px;display:flex;gap:18px;flex-wrap:wrap;z-index:5}nav a{color:var(--b);text-decoration:none;font-weight:600}
main{padding:24px 32px;max-width:1400px;margin:auto}section{margin-bottom:34px}h2{font-size:19px;margin:0 0 12px;border-left:4px solid var(--b);padding-left:10px}h4{margin:0 0 6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}.kpi .k,.kpi .l{color:var(--m);font-size:12px;text-transform:uppercase;letter-spacing:.4px}.kpi .v{font-size:26px;font-weight:700;margin:4px 0}.kpi .s{color:var(--m);font-size:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}.grid2>*{min-width:0}.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.stack{display:flex;flex-direction:column;gap:10px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}.bar-row{grid-template-columns:1fr}.bar-val{text-align:left}}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:13px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{background:#eef3f9;cursor:pointer;position:sticky;top:42px;user-select:none}th:hover,th:focus{background:#dfe8f3;outline:2px solid transparent}tbody tr:hover{background:#f8fafc}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.tw{overflow:auto;border:1px solid var(--line);border-radius:10px;max-height:620px;max-width:100%}.tw table{border:0}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#eee}.pill.ok,.pill.Low{background:#dff6dd;color:var(--ok)}.pill.warn,.pill.Medium{background:#fff4ce;color:var(--warn)}.pill.bad,.pill.High{background:#fde7e9;color:var(--bad)}.pill.muted-b{background:#eee;color:#555}
.bars{display:flex;flex-direction:column;gap:6px}.bar-row{display:grid;grid-template-columns:200px 1fr 170px;align-items:center;gap:8px}.bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{background:#eef0f3;border-radius:4px;height:16px}.bar-fill{height:16px;border-radius:4px;background:var(--b)}.bar-fill.warn{background:var(--orange)}.bar-fill.bad{background:var(--bad)}.bar-fill.ok{background:var(--ok)}.bar-val{font-variant-numeric:tabular-nums}
.muted,.note{color:var(--m);font-size:12px}.ring{display:flex;align-items:center;gap:20px}.legend{display:flex;flex-direction:column;gap:6px}.legend span{display:block}.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.rec{display:flex;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:10px}.rec-n{flex:0 0 30px;height:30px;border-radius:50%;background:var(--b);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}.rec p{margin:4px 0}.rec h4{font-size:14px}
.tabs{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}.tabs button{border:1px solid var(--line);background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer;font:inherit}.tabs button.on{background:var(--b);color:#fff;border-color:var(--b)}.hide{display:none}.search,.filter{padding:6px 10px;border:1px solid var(--line);border-radius:6px;margin-bottom:8px;width:min(320px,100%)}
footer,.foot{color:var(--m);font-size:12px;padding:20px 32px;border-top:1px solid var(--line)}
@media print{nav,.tabs,.search,.filter{display:none}.tw{max-height:none;overflow:visible}th{position:static}body{background:#fff}}
"""

JS = r"""
function sortTable(th){const t=th.closest('table'),i=[...th.parentNode.children].indexOf(th),tb=t.tBodies[0],rows=[...tb.rows];const num=th.classList.contains('num');const dir=th.dataset.dir==='asc'?'desc':'asc';th.dataset.dir=dir;th.setAttribute('aria-sort',dir==='asc'?'ascending':'descending');rows.sort((a,b)=>{let x=a.cells[i].dataset.v??a.cells[i].innerText,y=b.cells[i].dataset.v??b.cells[i].innerText;if(num){const n=v=>parseFloat(String(v).replace(/[^0-9.\-]/g,''))||0;x=n(x);y=n(y);return dir==='asc'?x-y:y-x}return dir==='asc'?x.localeCompare(y):y.localeCompare(x)});rows.forEach(r=>tb.appendChild(r))}
function filterTable(inp,id){const q=inp.value.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none')}
function tab(btn,id){const p=btn.closest('.card');p.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');p.querySelectorAll('.pane').forEach(x=>x.classList.add('hide'));p.querySelector('#'+id).classList.remove('hide')}
document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('th[onclick^="sortTable"]').forEach(th=>{th.tabIndex=0;th.setAttribute('role','button');th.setAttribute('aria-sort','none');th.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();sortTable(th)}})}))
"""


def fmt(n, dec=0):
    if n is None:
        return "-"
    return f"{n:,.{dec}f}"


def money(v, cur):
    return "-" if v is None else f"{html.escape(cur)} {v:,.2f}"


def bar_rows(items, key, label, total=None, color=None, valfmt=None, limit_key=None):
    out = []
    mx = max((i[key] for i in items), default=0) or 1
    for i in items:
        v = i[key]
        w = min(100, v / mx * 100)
        cls = color(i) if color else ""
        val = valfmt(i) if valfmt else (f"{fmt(v)}" + (f" ({fmt(v/total*100,1)}%)" if total else ""))
        out.append(f'<div class="bar-row"><div class="bar-label" title="{html.escape(str(i[label]))}">{html.escape(str(i[label]))}</div>'
                   f'<div class="bar-track"><div class="bar-fill {cls}" style="width:{w:.1f}%"></div></div><div class="bar-val">{val}</div></div>')
    return f'<div class="bars">{"".join(out)}</div>'


def donut(parts, size=120):
    total = sum(v for _, v, _ in parts) or 1
    r, cx, cy = 42, size / 2, size / 2
    circ = 2 * 3.14159 * r
    off = 0
    segs = [f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="transparent" stroke="#e5e7eb" stroke-width="16"></circle>']
    for name, v, col in parts:
        d = v / total * circ
        segs.append(f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="transparent" stroke="{col}" stroke-width="16" '
                    f'stroke-dasharray="{d:.2f} {circ-d:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"><title>{html.escape(name)}: {v:,}</title></circle>')
        off += d
    center = round(parts[0][1] / total * 100) if parts else 0
    segs.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="14" font-weight="700" fill="#111">{center}%</text>')
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(segs)}</svg>'


def render_html(res, anonymize=False):
    h, f, cur = res["headline"], res["forecast"], res["meta"]["currency"]
    rate = res["meta"]["paygRate"]
    near_pct = res["meta"]["nearLimitThreshold"]

    def name(u):
        return u["displayName"]

    def upn(u):
        return u["upn"]

    # KPIs
    monthly_credits = f.get("projectedPeriodTotal") if f["mode"] == "monthly" else f.get("monthlyRunRate")
    annual_credits = round(monthly_credits * 12) if f["mode"] == "monthly" and monthly_credits is not None else f.get("annualisedCredits")
    annual_cost = round(annual_credits * rate, 2) if annual_credits is not None else f.get("annualisedCost")
    kpis = [
        ("Credits used", fmt(h["totalCredits"]), f"{h.get('firstActivity') or f.get('periodStart')} to {h.get('lastActivity') or f.get('periodEnd')}"),
        ("Prepaid share", f"{fmt(h['prepaidShare'],0)}%" if h["prepaidShare"] is not None else "-", f"{fmt(h['prepaidCredits'])} prepaid; {fmt(h['paygCredits'])} pay-as-you-go" if h["prepaidShare"] is not None else "prepaid / PAYG split not provided"),
        ("Est. cost", money(h["estimatedCost"], cur), (f"list {money(h['listCost'], cur)} @ {rate}/credit" if h["splitAvailable"] else f"{res['meta']['paygRateBasis']} @ {rate}/credit - no split")),
        ("Active users", fmt(h["activeUsers"]), f"median {fmt(h['medianCreditsPerUser'])} credits/user" if res["users"]["count"] else h["activeUsersBasis"]),
        ("Credits / active user", fmt(h["creditsPerActiveUser"]), "mean across consuming users"),
        ("Credits / Cowork task", fmt(h["creditsPerTask"]), f"{fmt(h['matchedTaskUsers'])} matched users, {fmt(h['matchedTasks'])} tasks" if h["totalTasks"] else "Cowork usage export not provided"),
        ("Monthly run-rate", fmt(monthly_credits), f"~{money(f.get('projectedCost') if f['mode'] == 'monthly' else f.get('monthlyRunRate', 0) * rate, cur)}/month at {res['meta']['paygRateBasis']}"),
        ("Annualised run-rate", fmt(annual_credits), f"~{money(annual_cost, cur)}/year at {res['meta']['paygRateBasis']}"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="k">{html.escape(str(l))}</div><div class="v">{html.escape(str(v))}</div><div class="s">{html.escape(str(s))}</div></div>' for l, v, s in kpis)

    # Services
    svc = res["services"]
    if svc:
        svc_rows = "".join(f"<tr><td>{html.escape(s['name'])}</td><td class='num'>{fmt(s['activeUsers'])}</td><td class='num'>{fmt(s['used'])}</td>"
                           f"<td class='num'>{fmt(s['prepaid'])}</td><td class='num'>{fmt(s['payg'])}</td><td>{s['lastActivity'] or '-'}</td></tr>" for s in svc)
        known = {"copilot cowork", "cowork", "work iq api", "workiq api"}
        missing = [n for n in ("Copilot Cowork", "Work IQ API") if n.lower() not in {s["name"].lower() for s in svc}]
        if h["splitAvailable"]:
            parts = [("Prepaid", sum(s["prepaid"] for s in svc), "#0f6cbd"), ("Pay-as-you-go", sum(s["payg"] for s in svc), "#f7a600")]
            split_html = f"""<div class="ring">{donut(parts, 150)}<div class="legend"><span><i style="background:#0f6cbd"></i>Prepaid: {fmt(parts[0][1])}</span><span><i style="background:#f7a600"></i>Pay-as-you-go: {fmt(parts[1][1])}</span>
        </div></div>"""
        else:
            split_html = "<p class='note'>Prepaid vs pay-as-you-go split unavailable or inconsistent; costs fall back to the configured PAYG rate.</p>"
        service_note = f"{'No consumption recorded for: ' + html.escape(', '.join(missing)) + '. ' if missing else ''}Prepaid credits come from capacity packs; pay-as-you-go includes pre-purchase plan (P3) credits."
        svc_table_html = f"""<div class="tw" style="border:0"><table><thead><tr><th onclick="sortTable(this)">Service</th><th class="num" onclick="sortTable(this)">Active users</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Prepaid</th><th class="num" onclick="sortTable(this)">Pay-as-you-go</th><th>Last activity</th></tr></thead><tbody>{svc_rows}</tbody></table></div><p class="muted">{service_note}</p>"""
    else:
        split_html = "<p class='note'>Agents & services export not provided - service split unavailable.</p>"
        svc_table_html = "<p class='note'>Agents & services export not provided.</p>"

    U = res["users"]
    tier_rows = "".join(f"<tr><td class='num'>{fmt(t['limit']) if t['limit'] else 'none'}</td><td class='num'>{t['users']}</td><td class='num'>{fmt(t['used'])}</td><td class='num'>{fmt(t['avgUsed'])}</td><td class='num'>{'-' if t['avgPctOfLimit'] is None else fmt(t['avgPctOfLimit'],0)+'%'}</td></tr>" for t in U["limitTiers"])

    # Policies
    P = res["policies"]
    if P["rows"]:
        def pcolor(p):
            if p["unlimited"]:
                return "warn"
            if p["usageRate"] is not None and p["usageRate"] >= near_pct:
                return "bad"
            return ""
        def policy_flag(p):
            if p["unlimited"]:
                return '<span class="pill warn">Unlimited</span>'
            if p["usageRate"] is not None and p["usageRate"] >= near_pct:
                return '<span class="pill bad">Near limit</span>'
            if p["used"] == 0:
                return '<span class="pill muted-b">Idle</span>'
            return '<span class="pill ok">OK</span>'
        prow = "".join(f"<tr><td>{html.escape(p['name'])} {'<span class=pill>tenant-wide</span>' if p.get('tenantWide') else ''}</td><td>{html.escape(p['appliesTo'].replace('Group: ',''))}</td>"
                   f"<td class='num'>{fmt(p['activeUsers'])}</td><td class='num'>{fmt(p['used'])}</td><td class='num' data-v='{p['limit'] or 0}'>{'No limit' if p['unlimited'] else ('Unknown' if p.get('limitMissing') else fmt(p['limit']))}</td>"
                       f"<td class='num' data-v='{p['usageRate'] or 0}'>{'-' if p['usageRate'] is None else fmt(p['usageRate'],0)+'%'}</td><td>{html.escape(p['billingMethod'].split(' (')[0])}</td><td>{html.escape(p['status'])}</td><td>{policy_flag(p)}</td></tr>" for p in P["rows"])
        near_labels = html.escape(', '.join(P['nearLimit']) or 'none')
        idle_labels = html.escape(', '.join(P['idle']) or 'none')
        pol_html = f"""<div class="tw"><table><thead><tr><th onclick="sortTable(this)">Policy</th><th onclick="sortTable(this)">Applies to</th><th class="num" onclick="sortTable(this)">Active users</th><th class="num" onclick="sortTable(this)">Credits used</th><th class="num" onclick="sortTable(this)">Limit</th><th class="num" onclick="sortTable(this)">Usage rate</th><th onclick="sortTable(this)">Billing method</th><th onclick="sortTable(this)">Status</th><th onclick="sortTable(this)">Flag</th></tr></thead><tbody>{prow}</tbody></table></div>
        <p class="muted">{P['unlimitedCount']} active policies without a limit carry {fmt(P['unlimitedShare'],1)}% of active policy-attributed credits. Near limit: {near_labels}. Idle: {idle_labels}. Only a <b>policy-level</b> limit hard-stops usage; per-user limits are soft.</p>
        <div class="card" style="margin-top:12px"><h4>Per-user limit tiers</h4><div class="tw" style="border:0"><table><thead><tr><th class="num" onclick="sortTable(this)">Monthly limit</th><th class="num" onclick="sortTable(this)">Users</th><th class="num" onclick="sortTable(this)">Credits used</th><th class="num" onclick="sortTable(this)">Avg / user</th><th class="num" onclick="sortTable(this)">Avg % of limit</th></tr></thead><tbody>{tier_rows}</tbody></table></div></div>"""
    else:
        pol_html = "<p class='note'>Spending policies export not provided.</p>"

    # Groups
    G = res["groups"]
    if G["rows"]:
        grow = "".join(f"<tr><td>{html.escape(g['name'])}</td><td class='num'>{fmt(g['totalUsers']) if g['totalUsers'] else '-'}</td><td class='num'>{fmt(g['membersUsed'])}</td>"
                       f"<td class='num' data-v='{g['activationRate'] or 0}'>{'-' if g['activationRate'] is None else fmt(g['activationRate'],0)+'%'}</td><td class='num'>{fmt(g['used'])}</td><td class='num'>{fmt(g['avgPerUserPerDay'],0)}</td><td class='num'>{fmt(g['sessions'])}</td><td>{g['lastActivity'] or '-'}</td></tr>" for g in G["rows"])
        concentration_html = f"""<p>Top 10 users account for <b>{fmt(U['top10Share'],0)}%</b> of user credits; the top 20% of users ({U['top20pctCount']}) account for <b>{fmt(U['top20pctShare'],0)}%</b>.</p>{bar_rows(U['top10'], 'used', 'displayName', total=U['total'] or None, color=lambda u: 'bad' if (u.get('pctUsed') or 0) >= 100 else ('warn' if (u.get('pctUsed') or 0) >= near_pct else ''))}"""
        grp_html = f"""<div class="grid2"><div class="card"><h4>Credits by group</h4>{bar_rows(G['rows'][:10], 'used', 'name', valfmt=lambda g: f"{fmt(g['used'])} <span class='muted'>{g['membersUsed']} consumers</span>")}</div>
        <div class="card"><h4>Concentration</h4>{concentration_html}</div></div>
        <div class="tw" style="margin-top:12px"><table><thead><tr><th onclick="sortTable(this)">Group</th><th class="num" onclick="sortTable(this)">Total users</th><th class="num" onclick="sortTable(this)">Members that used credits</th><th class="num" onclick="sortTable(this)">Activation rate</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Avg / user / day</th><th class="num" onclick="sortTable(this)">Sessions</th><th onclick="sortTable(this)">Last activity</th></tr></thead><tbody>{grow}</tbody></table></div>
        <p class="muted">Groups overlap - a user in several groups is counted in each. Never add group rows together.</p>"""
    else:
        grp_html = "<p class='note'>Groups export not provided.</p>"

    # Users
    def ucolor(u):
        if u["pctUsed"] is None:
            return ""
        return "bad" if u["pctUsed"] >= 100 else ("warn" if u["pctUsed"] >= near_pct else "")
    def names_for(rows, limit=12):
        names = [html.escape(name(u)) for u in rows[:limit]]
        suffix = f" and {len(rows) - limit} more" if len(rows) > limit else ""
        return ", ".join(names) + suffix if rows else "None"
    def user_flags(u):
        flags = []
        if u in U["overLimit"]:
            flags.append('<span class="pill bad">Over limit</span>')
        elif u in U["nearLimit"]:
            flags.append('<span class="pill warn">Near limit</span>')
        if u in U["dormant"]:
            flags.append('<span class="pill muted-b">Dormant</span>')
        if u in U["unlicensed"]:
            flags.append('<span class="pill warn">Unlicensed</span>')
        return " ".join(flags)
    urows = "".join(
        f"<tr><td>{html.escape(name(u))}</td><td>{html.escape(u.get('department') or '-')}</td><td>{html.escape(u.get('manager') or '-')}</td><td class='num' data-v='{u['used']}'>{fmt(u['used'])}</td><td class='num' data-v='{u['limit'] or 0}'>{fmt(u['limit'])}</td>"
        f"<td class='num' data-v='{u['pctUsed'] or 0}'>{'-' if u['pctUsed'] is None else fmt(u['pctUsed'],1)+'%'}</td><td class='num' data-v='{u.get('share') or 0}'>{fmt(u.get('share'),1)}%</td><td class='num' data-v='{u.get('tasks') or 0}'>{fmt(u.get('tasks'))}</td>"
        f"<td class='num' data-v='{u.get('creditsPerTask') or 0}'>{fmt(u.get('creditsPerTask'))}</td><td class='num' data-v='{u['sessions']}'>{fmt(u['sessions'])}</td><td>{u['lastActivity'] or '-'}</td><td>{user_flags(u)}</td></tr>" for u in U["all"])
    users_html = f"""<div class="grid4"><div class="card"><h4>Over 100% of limit ({len(U['overLimit'])})</h4><p>{names_for(U['overLimit'])}</p></div>
    <div class="card"><h4>Near limit &ge; {near_pct}% ({len(U['nearLimit'])})</h4><p>{names_for(U['nearLimit'])}</p></div>
    <div class="card"><h4>Dormant &gt; 30 days ({len(U['dormant'])})</h4><p>{names_for(U['dormant'])}</p></div>
    <div class="card"><h4>Unlicensed consumers ({len(U['unlicensed'])})</h4><p>{names_for(U['unlicensed'])}</p></div></div>
    <input class="filter" placeholder="Filter users, departments, managers..." oninput="filterTable(this,'utab')" style="margin-top:12px">
    <div class="tw"><table id="utab"><thead><tr><th onclick="sortTable(this)">User</th><th onclick="sortTable(this)">Department</th><th onclick="sortTable(this)">Manager</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Limit</th><th class="num" onclick="sortTable(this)">% of limit</th><th class="num" onclick="sortTable(this)">Share</th><th class="num" onclick="sortTable(this)">Cowork tasks</th><th class="num" onclick="sortTable(this)">Credits / task</th><th class="num" onclick="sortTable(this)">Sessions</th><th onclick="sortTable(this)">Last activity</th><th onclick="sortTable(this)">Flags</th></tr></thead><tbody>{urows}</tbody></table></div>
    <p class="muted">Cowork tasks come from the Cowork usage report and include pre-metering activity; credits per task is indicative.</p>"""

    # Departments & managers
    O = res["org"]

    def org_table(rows, first_label, extra_cols=""):
        tr = "".join(
            f"<tr><td>{html.escape(r['name'])}</td><td class='num'>{r['users']}</td><td class='num'>{r['consuming']}</td><td class='num'>{fmt(r['used'])}</td>"
            f"<td class='num' data-v='{r['share']}'>{fmt(r['share'],1)}%</td><td class='num'>{fmt(r['avgPerUser'])}</td><td class='num'>{fmt(r['tasks']) if r['tasks'] else '-'}</td>"
            f"<td class='num'>{fmt(r['creditsPerTask'])}</td><td class='num'>{r['nearOrOver']}</td><td>{html.escape(r['topUser'])}</td></tr>" for r in rows)
        return (f"<div class=\"tw\"><table><thead><tr><th onclick=\"sortTable(this)\">{first_label}</th><th class='num' onclick=\"sortTable(this)\">Users</th><th class='num' onclick=\"sortTable(this)\">Consuming</th>"
                f"<th class='num' onclick=\"sortTable(this)\">Credits</th><th class='num' onclick=\"sortTable(this)\">Share</th><th class='num' onclick=\"sortTable(this)\">Avg / user</th><th class='num' onclick=\"sortTable(this)\">Tasks</th>"
            f"<th class='num' onclick=\"sortTable(this)\">Credits / task</th><th class='num' onclick=\"sortTable(this)\">&ge;{near_pct}% of limit</th><th onclick=\"sortTable(this)\">Top user</th></tr></thead><tbody>{tr}</tbody></table></div>")

    if O["provided"]:
        def dcolor(r):
            return "warn" if r["name"].startswith("(") else ""
        dept_rows = O["departments"]
        mgr_rows = O["managers"]
        org_intro = f"<p class=\"muted\">Department, job title and manager come from Microsoft Graph (read-only). Coverage: {O['enrichedUsers']} of {res['users']['count']} users ({fmt(O['coverage'],0)}%). This is a spend-control view, not a performance ranking.</p>"
        dept_html = bar_rows(dept_rows[:10], 'used', 'name', total=res['users']['total'] or None, color=dcolor)
        mgr_html = bar_rows(mgr_rows[:10], 'used', 'name', total=res['users']['total'] or None, color=dcolor)
        country_html = ""
        if O["countries"]:
            country_html = f"""<div class="card" style="margin-top:16px"><h4>Countries <span class="muted">usage location</span></h4>{bar_rows(O['countries'][:12], 'used', 'name', total=res['users']['total'] or None)}</div>"""
        org_cards = (f'{org_intro}<div class="grid2"><div class="card"><h4>Credits by department</h4>{dept_html}</div>'
                     f'<div class="card"><h4>Credits by manager</h4>{mgr_html}</div></div>'
                     f'<h4 style="margin-top:16px">Department detail</h4>{org_table(dept_rows, "Department")}'
                     f'<h4 style="margin-top:16px">Manager accountability view</h4>{org_table(mgr_rows, "Manager")}{country_html}')
    else:
        org_cards = ('<div class="card"><p class="note">No directory data was supplied. '
                     'Provide Microsoft Graph user data (<code>/users?$select=department,jobTitle,usageLocation&amp;$expand=manager</code>) or an Entra user export with '
                     '<code>--org</code> to add per-department and per-manager reporting.</p></div>')

    # Recommendations
    rec_html = "".join(f'<div class="rec"><div class="rec-n">{i}</div><div><h4>{html.escape(r["title"])}</h4>'
                       f'<p><b>Evidence:</b> {html.escape(r["evidence"])}</p><p><b>Action:</b> {html.escape(r["action"])}</p></div></div>'
                       for i, r in enumerate(res["recommendations"], 1)) or "<p class='muted'>No recommendations triggered.</p>"

    # Forecast card
    if f["mode"] == "monthly":
        fc_html = (f"<p>Billing month <b>{f['periodStart']}</b> to <b>{f['periodEnd']}</b>: {fmt(h['totalCredits'])} credits in {f['daysElapsed']} of {f['daysInPeriod']} days "
                   f"= <b>{fmt(f['dailyRunRate'])}/day</b>. Straight-line projection: <b>{fmt(f['projectedPeriodTotal'])}</b> credits (~{money(f['projectedCost'], cur)} at {html.escape(res['meta']['paygRateBasis'])}).</p>")
    else:
        fc_html = (f"<p>Accumulated view from <b>{f['periodStart']}</b> to <b>{f['periodEnd']}</b> ({f['monthsElapsed']} months): "
                   f"<b>{fmt(f['dailyRunRate'])}/day</b>, <b>{fmt(f['monthlyRunRate'])}/month</b>, annualised <b>{fmt(f['annualisedCredits'])}</b> credits "
                   f"(~{money(f['annualisedCost'], cur)} at {html.escape(res['meta']['paygRateBasis'])}).</p>")
    fc_html += "<p class='note'>Run-rates are straight-line on observed data and assume no policy changes. Use them for sizing capacity packs, not as an invoice.</p>"
    fc_html += f"<p class='note'>Credits-per-task uses the {fmt(h.get('matchedTaskUsers'))} users present in both the consumption and usage exports ({fmt(h.get('matchedTasks'))} of {fmt(h.get('totalTasks'))} tasks).</p>" if h.get("matchedTasks") else ""

    dq = "".join(f"<li>{html.escape(n)}</li>" for n in res["dataQuality"])
    inputs = "".join(f"<li>{html.escape(k)}: {html.escape(os.path.basename(v))}</li>" for k, v in res["meta"]["inputs"].items())

    headline_note = (f"Run-rates are straight-line on observed data and assume no policy changes. Costs use {html.escape(res['meta']['paygRateBasis'])} of {cur} {rate}/pay-as-you-go credit and {html.escape(res['meta']['prepaidRateBasis'])} of {cur} {res['meta']['prepaidRate']}/prepaid credit. The Microsoft invoice on the Azure subscription named in the billing method is the record of truth.")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(res['meta']['title'])}</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style></head><body>
<header><h1>{html.escape(res['meta']['title'])}</h1><p>Copilot Credits consumption report &middot; data as of {res['meta']['asOf']} &middot; source: Microsoft 365 admin center exports &middot; reporting only</p></header>
<nav><a href="#headline">Headline</a><a href="#services">Services</a><a href="#policies">Spending policies</a><a href="#org">Departments &amp; managers</a><a href="#groups">Groups</a><a href="#users">Users</a><a href="#recs">Recommendations</a><a href="#dq">Data quality</a></nav>
<main>
<section id="headline"><h2>Headline</h2><div class="kpis">{kpi_html}</div><p class="muted" style="margin-top:10px">{headline_note}</p></section>
<section id="services"><h2>Service breakdown</h2><div class="grid2"><div class="card"><h4>Prepaid vs pay-as-you-go</h4>{split_html}</div><div class="card"><h4>By service</h4>{svc_table_html}</div></div><div class="card" style="margin-top:12px"><h4>Forecast &amp; run-rate</h4>{fc_html}</div></section>
<section id="policies"><h2>Spending-limit analysis</h2>{pol_html}</section>
<section id="org"><h2>Departments &amp; managers</h2>{org_cards}</section>
<section id="groups"><h2>Groups</h2>{grp_html}</section>
<section id="users"><h2>Users</h2>{users_html}</section>
<section id="recs"><h2>Recommendations</h2>{rec_html}<p class="muted">This report only recommends. Policy, limit and billing-method changes are made in Microsoft 365 admin center &gt; Copilot &gt; Cost management.</p></section>
<section id="dq"><h2>Data quality</h2><div class="card"><ul>{dq}<li>Exports are point-in-time snapshots; the live dashboard refreshes every 2 hours and may differ.</li><li>Usage above a per-user soft limit completes the task, is not billed, and is not shown as consumed credits.</li><li>The Microsoft invoice (Azure subscription named in the billing method) is the record of truth; costs here use {html.escape(res['meta']['paygRateBasis'])} {cur} {rate}/credit for pay-as-you-go and {html.escape(res['meta']['prepaidRateBasis'])} {cur} {res['meta']['prepaidRate']}/credit for prepaid.</li></ul><p class="muted">Inputs:</p><ul class="muted">{inputs}</ul></div></section>
</main>
<footer>Generated by the Cowork &amp; Work IQ Consumption Advisor skill. Self-contained file - no external scripts, safe to email or store in SharePoint.</footer>
<script>{JS}</script></body></html>"""


def render_md(res):
    h, f, cur = res["headline"], res["forecast"], res["meta"]["currency"]
    lines = [f"# {md_escape(res['meta']['title'])}", f"*As of {res['meta']['asOf']} - Microsoft 365 admin center exports*", "",
             "## Headline", f"- **Copilot Credits used:** {fmt(h['totalCredits'])}" + (f" ({fmt(h['prepaidShare'],1)}% prepaid)" if h['prepaidShare'] is not None else ""),
             f"- **Estimated cost:** {money(h['estimatedCost'], cur)} (list {money(h['listCost'], cur)}; {md_escape(h['costBasis'])})",
             f"- **Active users:** {fmt(h['activeUsers'])} - {fmt(h['creditsPerActiveUser'])} credits per active user, median {fmt(h['medianCreditsPerUser'])}"]
    if h["creditsPerTask"]:
        lines.append(f"- **Credits per task:** {fmt(h['creditsPerTask'])} over {fmt(h['matchedTasks'])} tasks of users in both exports ({fmt(h['totalTasks'])} Cowork tasks in total, {fmt(h['scheduledTaskShare'],1)}% scheduled)")
    if f["mode"] == "monthly":
        lines.append(f"- **Forecast:** {fmt(f['projectedPeriodTotal'])} credits by {f['periodEnd']} (~{money(f['projectedCost'], cur)} at {md_escape(res['meta']['paygRateBasis'])})")
    else:
        lines.append(f"- **Run-rate:** {fmt(f['monthlyRunRate'])} credits/month, annualised {fmt(f['annualisedCredits'])} (~{money(f['annualisedCost'], cur)} at {md_escape(res['meta']['paygRateBasis'])})")
    P = res["policies"]
    if P["rows"]:
        lines += ["", "## Spending limits", f"- {P['unlimitedCount']} active policies without a limit carry {fmt(P['unlimitedShare'],1)}% of active policy-attributed credits",
                  f"- Near limit: {md_escape(', '.join(P['nearLimit']) or 'none')}; idle: {md_escape(', '.join(P['idle']) or 'none')}"]
    O = res["org"]
    if O["provided"]:
        lines += ["", f"## Departments ({fmt(O['coverage'],0)}% of users matched)"]
        for d in O["departments"][:8]:
            lines.append(f"- {md_escape(d['name'])}: {fmt(d['used'])} credits ({d['share']}%), {d['users']} users, {fmt(d['avgPerUser'])} per user, {d['nearOrOver']} near/over limit")
        lines += ["", "## Managers"]
        for m in O["managers"][:8]:
            lines.append(f"- {md_escape(m['name'])}: {fmt(m['used'])} credits ({m['share']}%), {m['users']} users, {m['nearOrOver']} near/over limit")
    U = res["users"]
    lines += ["", "## Users", f"- Top 10 users = {fmt(U['top10Share'],1)}% of credits; {len(U['overLimit'])} over limit, {len(U['nearLimit'])} near limit, {len(U['dormant'])} dormant"]
    lines += ["", "## Recommendations"]
    for r in res["recommendations"]:
        lines.append(f"- **[{md_escape(r['priority'])}] {md_escape(r['title'])}** - {md_escape(r['evidence'])} -> {md_escape(r['action'])}")
    if res["dataQuality"]:
        lines += ["", "## Data quality"] + [f"- {md_escape(n)}" for n in res["dataQuality"]]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", nargs="+", required=True, help="CSV files, globs, or folders")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--org", nargs="*", default=[], help="directory data: Graph user JSON files/folders and/or org CSV (UPN, Department, Manager...)")
    ap.add_argument("--rate", type=float, default=0.01, help="pay-as-you-go list price per credit (default 0.01)")
    ap.add_argument("--prepaid-rate", type=float, default=0.008, help="effective prepaid price per credit (default 0.008 = 200/25,000 pack)")
    ap.add_argument("--currency", default="USD", help="ISO 4217 code, e.g. USD, EUR, CHF")
    ap.add_argument("--period", choices=["auto", "monthly", "ytd"], default="auto")
    ap.add_argument("--as-of", help="report date YYYY-MM-DD (default: latest date in the exports, else today)")
    ap.add_argument("--near-limit", type=float, default=0.8)
    ap.add_argument("--dormant-days", type=int, default=30)
    ap.add_argument("--tenant-name", help="tenant/company name to show in non-anonymized report titles")
    ap.add_argument("--title", default="Cowork & Work IQ Consumption Report")
    ap.add_argument("--anonymize", action="store_true",
                    help="replace user and manager names/UPNs with stable pseudonyms in ALL outputs (HTML, JSON, Markdown)")
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[A-Za-z]{3}", args.currency):
        print("ERROR: --currency must be a 3-letter ISO 4217 code (e.g. USD, EUR)", file=sys.stderr)
        return 2
    if not (math.isfinite(args.rate) and args.rate >= 0 and math.isfinite(args.prepaid_rate) and args.prepaid_rate >= 0):
        print("ERROR: --rate and --prepaid-rate must be finite non-negative numbers", file=sys.stderr)
        return 2
    args.currency = args.currency.upper()
    default_title = ap.get_default("title")
    if args.tenant_name and args.title == default_title:
        args.report_title = f"{clean(args.tenant_name)} - Cowork & Work IQ consumption"
    else:
        args.report_title = args.title
    files = collect_inputs(args.input, exts=(".csv", ".json"))
    json_files = [f for f in files if f.lower().endswith(".json")]
    files = [f for f in files if not f.lower().endswith(".json")]
    if not files:
        print("ERROR: no CSV files found", file=sys.stderr)
        return 2
    data, detected = {"_files": {}}, []
    for fpath in files:
        header, rows = read_csv(fpath)
        t = detect_type([norm_key(x) for x in header])
        if t == "org":
            continue  # merged below
        if not t:
            shown_name = "<redacted>" if args.anonymize else os.path.basename(fpath)
            shown_header = "<redacted>" if args.anonymize else header[:6]
            print(f"skip (unrecognised columns): {shown_name} -> {shown_header}", file=sys.stderr)
            continue
        if t in data:
            print(f"warning: second {t} export ignored: {os.path.basename(fpath)}", file=sys.stderr)
            continue
        parser = {"users": parse_users, "groups": parse_groups, "services": parse_services,
                  "policies": parse_policies, "cowork_usage": parse_cowork_usage}[t]
        data[t] = parser(rows)
        data["_files"][t] = fpath
        detected.append(f"{t}: {os.path.basename(fpath)} ({len(data[t])} rows)")
    # org data may also sit among the --input CSVs (Entra export); merge with --org
    org = load_org(args.org) if args.org else {}
    for jf in json_files:  # Graph user JSON dropped next to the exports
        try:
            org.update(parse_org_json(jf))
        except (ValueError, AttributeError):
            print(f"skip (not Graph user JSON): {os.path.basename(jf)}", file=sys.stderr)
    for fpath in files:
        header, rows = read_csv(fpath)
        if detect_type([norm_key(x) for x in header]) == "org":
            org.update(parse_org_rows(rows))
    if org:
        data["org"] = org
        detected.append(f"org: {len(org)} directory records")
    if "users" not in data and "services" not in data:
        print("ERROR: need at least the Consumption > Users or Agents & services export", file=sys.stderr)
        return 2

    if args.as_of:
        as_of = dt.date.fromisoformat(args.as_of)
    else:
        # snapshot date: explicit --as-of > unambiguous export-file timestamp > today. Never activity dates.
        cands = []
        for fpath in files:
            m = re.search(r"(\d{1,2})_(\d{1,2})_(\d{4})", os.path.basename(fpath)) or re.search(r"(\d{4})-(\d{2})-(\d{2})", os.path.basename(fpath))
            if m:
                g = m.groups()
                try:
                    cands.append(dt.date(int(g[2]), int(g[0]), int(g[1])) if len(g[0]) <= 2 and len(g[2]) == 4 else dt.date(int(g[0]), int(g[1]), int(g[2])))
                except ValueError:
                    pass
        as_of = max(cands) if cands else dt.date.today()
        if not cands:
            print("note: no --as-of and no export timestamp in file names - using today's date as the snapshot date", file=sys.stderr)

    res = analyze(data, args, as_of)
    shown_detected = ["<redacted>" for _ in detected] if args.anonymize else detected
    res["meta"]["detected"] = shown_detected
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "consumption-analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    with open(os.path.join(args.out, "consumption-report.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(res, anonymize=args.anonymize))
    with open(os.path.join(args.out, "consumption-summary.md"), "w", encoding="utf-8") as fh:
        fh.write(render_md(res))
    print("\n".join(shown_detected))
    print(f"as-of {as_of}; total credits {res['headline']['totalCredits']:,}; {len(res['recommendations'])} recommendations; "
          f"{len(res['dataQuality'])} data-quality notes")
    print(f"written: {args.out}/consumption-report.html, consumption-analysis.json, consumption-summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
