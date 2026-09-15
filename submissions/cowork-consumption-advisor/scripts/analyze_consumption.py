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
        [--title "Contoso - Cowork consumption"] [--anonymize]
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
import os
import re
import sys
from collections import defaultdict

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
        unlimited = limit_raw.lower().startswith("no limit") or limit_raw == ""
        limit = None if unlimited else to_int(limit_raw, 0)
        used = to_int(r.get("creditsused"), 0)
        rate = to_float(r.get("creditusagerate"), 0.0) if not unlimited else None
        if not unlimited and limit and rate == 0.0:
            rate = round(used / limit * 100, 1)
        pols.append({
            "name": name,
            "appliesTo": clean(r.get("appliesto")),
            "activeUsers": to_int(r.get("activeusers"), 0),
            "used": used,
            "limit": limit,
            "unlimited": unlimited,
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
    for k, o in (data.get("org") or {}).items():
        mk = (o.get("managerUpn") or o.get("manager") or "")
        o["manager"] = pseudonym("Manager", mk, 8) if mk else ""
        o["managerUpn"] = pseudonym("manager", mk, 8).replace(" ", "") + "@hidden" if mk else ""
        o["upn"] = pseudonym("user", k).replace(" ", "") + "@hidden"
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
    if services and users and abs(svc_total - user_total) > max(50, 0.02 * max(svc_total, 1)):
        notes.append(
            f"Users export totals {user_total:,} credits vs {svc_total:,} in the services export "
            f"({pct(user_total, svc_total)}%). Exports are point-in-time snapshots taken at different moments, "
            "and per-user rows only show usage under each user's CURRENT policy.")

    split_valid = bool(services) and (prepaid + payg) > 0 and abs((prepaid + payg) - svc_total) <= max(5, 0.01 * svc_total)
    list_cost = total * args.rate
    if split_valid:
        est_cost = payg * args.rate + prepaid * args.prepaid_rate
        cost_basis = "blended: pay-as-you-go at list rate, prepaid at prepaid rate"
    else:
        est_cost = list_cost
        cost_basis = "list rate on all credits (prepaid / pay-as-you-go split not available)"
        if services:
            notes.append("Prepaid vs pay-as-you-go split missing or inconsistent in the services export; the estimated "
                         "cost falls back to list rate on all credits.")

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
    k20 = max(1, round(len(consuming) * 0.2))
    top20pct_share = pct(sum(u["used"] for u in users_sorted[:k20]), user_total)
    near = [u for u in users if u["pctUsed"] is not None and args.near_limit * 100 <= u["pctUsed"] < 100]
    over = [u for u in users if u["pctUsed"] is not None and u["pctUsed"] >= 100]
    unlicensed = [u for u in users if not u["licensed"] and u["used"] > 0]
    dormant = [u for u in users if u["lastActivity"] and (as_of - u["lastActivity"]).days > args.dormant_days]
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
    tasks_matched = sum(u["tasks"] for u in joined)
    credits_matched = sum(u["used"] for u in joined)
    credits_per_task = round(credits_matched / tasks_matched) if tasks_matched else None
    usage_only = [x for x in usage if x["upnKey"] not in {u["upnKey"] for u in users}]
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
    departments = rollup(users, lambda u: u.get("department"), unknown_dept, near_pct) if org else []
    # key managers by UPN (two managers can share a display name); label with the display name
    mgr_label = {}
    for u in users:
        k = (u.get("managerUpn") or u.get("manager") or "").lower()
        if k:
            mgr_label.setdefault(k, u.get("manager") or u.get("managerUpn"))
    managers = rollup(users, lambda u: (u.get("managerUpn") or u.get("manager") or "").lower(), "(No manager found)", near_pct) if org else []
    for m in managers:
        m["managerUpn"] = m["name"] if "@" in m["name"] else ""
        m["name"] = mgr_label.get(m["name"], m["name"])
    countries = rollup(users, lambda u: u.get("country"), "(Unknown)", near_pct) if org and any(u.get("country") for u in users) else []
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
    dup_names = [n for n, c in defaultdict(int, {g["name"]: sum(1 for h in groups if h["name"] == g["name"]) for g in groups}).items() if c > 1]
    if groups and services and group_total > svc_total * 1.05:
        notes.append(f"Group credits sum to {group_total:,} vs {svc_total:,} total - users belong to several groups, "
                     "so group figures overlap and must not be added together.")
    if dup_names:
        notes.append("Groups with the same display name but different IDs: " + ", ".join(sorted(dup_names)) +
                     ". Shown separately; consider renaming for clarity.")
    unassigned = [g for g in groups if g["name"].startswith("(No group")]

    # ---- policies -------------------------------------------------------------
    pol_total = sum(p["used"] for p in policies)
    unlimited = [p for p in policies if p["unlimited"] and p["status"].lower() == "active"]
    unlimited_share = pct(sum(p["used"] for p in unlimited), pol_total)
    near_pol = [p for p in policies if p["usageRate"] is not None and p["usageRate"] >= args.near_limit * 100
                and p["status"].lower() == "active"]
    idle_pol = [p for p in policies if p["used"] == 0 and p["status"].lower() == "active"]
    tenant_wide = [p for p in policies if p["appliesTo"].lower().startswith("all users")]
    methods = sorted({p["billingMethod"] for p in policies if p["billingMethod"]})

    # ---- recommendations (each with evidence) --------------------------------
    def rec(priority, title, evidence, action):
        recs.append({"priority": priority, "title": title, "evidence": evidence, "action": action})

    if unlimited:
        rec("High", "Cap the unlimited spending policies",
            f"{len(unlimited)} active policies have no monthly limit and carry {unlimited_share}% of policy-attributed "
            f"credits ({sum(p['used'] for p in unlimited):,}). "
            + ("All are billed pay-as-you-go, so exposure is uncapped." if all("pay-as-you-go" in p["billingMethod"].lower() for p in unlimited)
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
    if services and prepaid and payg:
        rec("Medium", "Prepaid vs pay-as-you-go mix",
            f"{pct(prepaid, svc_total)}% of credits came from prepaid capacity, {pct(payg, svc_total)}% from pay-as-you-go "
            f"({payg:,} credits ~ {args.currency} {payg*args.rate:,.0f} at list rate).",
            "If the pay-as-you-go tail is steady month over month, size additional capacity packs or a Copilot Credit "
            "pre-purchase plan (P3) to cover the floor of usage - prepaid rates are discounted; keep PAYG for the peak.")
    elif services and payg and not prepaid:
        rec("Medium", "Everything is billed pay-as-you-go",
            f"{payg:,} credits (~{args.currency} {payg*args.rate:,.0f}) at list rate with no prepaid capacity in use.",
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
            return {k: strip_keys(v) for k, v in obj.items() if k != "upnKey"}
        if isinstance(obj, list):
            return [strip_keys(x) for x in obj]
        return obj

    result = {
        "meta": {
            "title": args.title, "asOf": as_of.isoformat(), "currency": args.currency,
            "paygRate": args.rate, "prepaidRate": args.prepaid_rate,
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
        "policies": {"rows": policies, "total": pol_total, "unlimitedCount": len(unlimited), "unlimitedShare": unlimited_share,
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
:root{--bg:#f3f4f6;--card:#fff;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--brand:#0f6cbd;--brand2:#5b5fc7;--ok:#107c10;--warn:#c19c00;--bad:#c50f1f;--chip:#eef2ff}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:14px}
header{background:linear-gradient(120deg,var(--brand),var(--brand2));color:#fff;padding:28px 40px}header h1{margin:0 0 4px;font-size:26px;font-weight:600}header p{margin:0;opacity:.9}
main{max-width:1280px;margin:0 auto;padding:24px 40px 60px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:-46px 0 22px}
.kpi{background:var(--card);border-radius:12px;padding:16px 18px;box-shadow:0 2px 8px rgba(0,0,0,.06)}.kpi .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}.kpi .v{font-size:26px;font-weight:600;margin-top:4px}.kpi .s{color:var(--muted);font-size:12px;margin-top:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px}
.card{background:var(--card);border-radius:12px;padding:18px 20px;box-shadow:0 2px 8px rgba(0,0,0,.05)}.card h2{margin:0 0 12px;font-size:16px;font-weight:600}.card h2 small{color:var(--muted);font-weight:400;margin-left:8px}
.bar{display:grid;grid-template-columns:200px 1fr 90px;gap:10px;align-items:center;padding:5px 0;border-bottom:1px solid var(--line)}.bar:last-child{border-bottom:0}.bar .n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar .t{height:14px;background:#eef2f7;border-radius:7px;overflow:hidden}.bar .f{height:100%;background:var(--brand);border-radius:7px}.bar .f.warn{background:var(--warn)}.bar .f.bad{background:var(--bad)}.bar .f.ok{background:var(--ok)}.bar .val{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:7px 8px;text-align:left;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;cursor:pointer;user-select:none;white-space:nowrap}th:hover{color:var(--brand)}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:var(--chip);color:var(--brand2)}.pill.High{background:#fde7e9;color:var(--bad)}.pill.Medium{background:#fff4ce;color:#8a6d00}.pill.Low{background:#dff6dd;color:var(--ok)}
.rec{border-left:4px solid var(--brand);padding:10px 14px;margin:10px 0;background:#fafbfd;border-radius:0 8px 8px 0}.rec.High{border-color:var(--bad)}.rec.Medium{border-color:var(--warn)}.rec.Low{border-color:var(--ok)}.rec b{display:block;margin-bottom:4px}.rec .ev{color:var(--muted);font-size:13px}.rec .ac{margin-top:6px}
.tabs{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}.tabs button{border:1px solid var(--line);background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer;font:inherit}.tabs button.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.hide{display:none}.search{padding:7px 10px;border:1px solid var(--line);border-radius:8px;font:inherit;width:260px;margin-bottom:8px}
.note{color:var(--muted);font-size:12px}.foot{margin-top:28px;color:var(--muted);font-size:12px;line-height:1.6}
.ring{display:flex;align-items:center;gap:18px}.legend span{display:inline-block;margin-right:14px}.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
@media print{header{-webkit-print-color-adjust:exact}.tabs,.search{display:none}.hide{display:block!important}}
"""

JS = r"""
function sortTable(th){const t=th.closest('table'),i=[...th.parentNode.children].indexOf(th),tb=t.tBodies[0],rows=[...tb.rows];const num=th.classList.contains('num');const dir=th.dataset.dir==='asc'?'desc':'asc';th.dataset.dir=dir;rows.sort((a,b)=>{let x=a.cells[i].dataset.v??a.cells[i].innerText,y=b.cells[i].dataset.v??b.cells[i].innerText;if(num){const n=v=>parseFloat(String(v).replace(/[^0-9.\-]/g,''))||0;x=n(x);y=n(y);return dir==='asc'?x-y:y-x}return dir==='asc'?x.localeCompare(y):y.localeCompare(x)});rows.forEach(r=>tb.appendChild(r))}
function filterTable(inp,id){const q=inp.value.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none')}
function tab(btn,id){const p=btn.closest('.card');p.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');p.querySelectorAll('.pane').forEach(x=>x.classList.add('hide'));p.querySelector('#'+id).classList.remove('hide')}
"""


def fmt(n, dec=0):
    if n is None:
        return "-"
    return f"{n:,.{dec}f}"


def money(v, cur):
    return "-" if v is None else f"{html.escape(cur)} {v:,.0f}"


def bar_rows(items, key, label, total=None, color=None, valfmt=None, limit_key=None):
    out = []
    mx = max((i[key] for i in items), default=0) or 1
    for i in items:
        v = i[key]
        w = min(100, v / mx * 100)
        cls = color(i) if color else ""
        val = valfmt(i) if valfmt else (f"{fmt(v)}" + (f" ({fmt(v/total*100,1)}%)" if total else ""))
        out.append(f'<div class="bar"><div class="n" title="{html.escape(str(i[label]))}">{html.escape(str(i[label]))}</div>'
                   f'<div class="t"><div class="f {cls}" style="width:{w:.1f}%"></div></div><div class="val">{val}</div></div>')
    return "".join(out)


def donut(parts, size=120):
    total = sum(v for _, v, _ in parts) or 1
    r, cx, cy = 42, size / 2, size / 2
    circ = 2 * 3.14159 * r
    off, segs = 0, []
    for name, v, col in parts:
        d = v / total * circ
        segs.append(f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="transparent" stroke="{col}" stroke-width="16" '
                    f'stroke-dasharray="{d:.2f} {circ-d:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"><title>{html.escape(name)}: {v:,}</title></circle>')
        off += d
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
    fc_label = ("Projected month-end" if f["mode"] == "monthly" else "Monthly run-rate")
    fc_val = f.get("projectedPeriodTotal") if f["mode"] == "monthly" else f.get("monthlyRunRate")
    fc_sub = (f"{f['daysElapsed']}/{f['daysInPeriod']} days elapsed" if f["mode"] == "monthly"
              else f"~{money(f.get('annualisedCost'), cur)}/yr at list rate")
    kpis = [
        ("Copilot Credits used", fmt(h["totalCredits"]), f"{fmt(h['prepaidShare'],1)}% prepaid" if h["prepaidShare"] is not None else "prepaid / PAYG split not provided"),
        ("Est. cost", money(h["estimatedCost"], cur), (f"list {money(h['listCost'], cur)} @ {rate}/credit" if h["splitAvailable"] else f"list rate @ {rate}/credit - no split")),
        (fc_label, fmt(fc_val), fc_sub),
        ("Active users", fmt(h["activeUsers"]), f"median {fmt(h['medianCreditsPerUser'])} credits/user" if res["users"]["count"] else h["activeUsersBasis"]),
        ("Credits / active user", fmt(h["creditsPerActiveUser"]), "mean across consuming users"),
        ("Credits / task", fmt(h["creditsPerTask"]), f"over {fmt(h['matchedTasks'])} matched tasks ({fmt(h['totalTasks'])} total, {fmt(h['scheduledTaskShare'],1)}% scheduled)" if h["totalTasks"] else "Cowork usage export not provided"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s">{s}</div></div>' for l, v, s in kpis)

    # Services
    svc = res["services"]
    if svc:
        parts = [("Prepaid", sum(s["prepaid"] for s in svc), "#0f6cbd"), ("Pay-as-you-go", sum(s["payg"] for s in svc), "#5b5fc7")]
        svc_rows = "".join(f"<tr><td>{html.escape(s['name'])}</td><td class='num'>{fmt(s['activeUsers'])}</td><td class='num'>{fmt(s['used'])}</td>"
                           f"<td class='num'>{fmt(s['prepaid'])}</td><td class='num'>{fmt(s['payg'])}</td><td class='num'>{money(s['payg']*rate, cur)}</td><td>{s['lastActivity'] or '-'}</td></tr>" for s in svc)
        known = {"copilot cowork", "cowork", "work iq api", "workiq api"}
        missing = [n for n in ("Copilot Cowork", "Work IQ API") if n.lower() not in {s["name"].lower() for s in svc}]
        svc_html = f"""<div class="ring">{donut(parts)}<div class="legend"><span><i style="background:#0f6cbd"></i>Prepaid {fmt(parts[0][1])}</span><span><i style="background:#5b5fc7"></i>Pay-as-you-go {fmt(parts[1][1])}</span>
        <p class="note">{'No consumption recorded for: ' + ', '.join(missing) + '.' if missing else ''} Prepaid credits come from capacity packs; pay-as-you-go includes pre-purchase plan (P3) credits.</p></div></div>
        <table><thead><tr><th onclick="sortTable(this)">Service</th><th class="num" onclick="sortTable(this)">Active users</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Prepaid</th><th class="num" onclick="sortTable(this)">PAYG</th><th class="num" onclick="sortTable(this)">PAYG list cost</th><th>Last activity</th></tr></thead><tbody>{svc_rows}</tbody></table>"""
    else:
        svc_html = "<p class='note'>Agents & services export not provided - service split unavailable.</p>"

    # Policies
    P = res["policies"]
    if P["rows"]:
        def pcolor(p):
            if p["unlimited"]:
                return "warn"
            if p["usageRate"] is not None and p["usageRate"] >= near_pct:
                return "bad"
            return ""
        prow = "".join(f"<tr><td>{html.escape(p['name'])} {'<span class=pill>tenant-wide</span>' if p['appliesTo'].lower().startswith('all users') else ''}</td><td>{html.escape(p['appliesTo'].replace('Group: ',''))}</td>"
                       f"<td class='num'>{fmt(p['activeUsers'])}</td><td class='num'>{fmt(p['used'])}</td><td class='num' data-v='{p['limit'] or 0}'>{'No limit' if p['unlimited'] else fmt(p['limit'])}</td>"
                       f"<td class='num' data-v='{p['usageRate'] or 0}'>{'-' if p['usageRate'] is None else fmt(p['usageRate'],0)+'%'}</td><td>{html.escape(p['billingMethod'].split(' (')[0])}</td><td>{html.escape(p['status'])}</td></tr>" for p in P["rows"])
        pol_html = f"""<p class="note">{P['unlimitedCount']} active policies without a limit carry {fmt(P['unlimitedShare'],1)}% of policy-attributed credits. Near limit: {', '.join(P['nearLimit']) or 'none'}. Idle: {', '.join(P['idle']) or 'none'}.</p>
        {bar_rows(sorted(P['rows'], key=lambda p: -p['used']), 'used', 'name', total=P['total'] or None, color=pcolor)}
        <table style="margin-top:12px"><thead><tr><th onclick="sortTable(this)">Policy</th><th onclick="sortTable(this)">Applies to</th><th class="num" onclick="sortTable(this)">Active users</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Limit / month</th><th class="num" onclick="sortTable(this)">Used</th><th onclick="sortTable(this)">Billing</th><th onclick="sortTable(this)">Status</th></tr></thead><tbody>{prow}</tbody></table>"""
    else:
        pol_html = "<p class='note'>Spending policies export not provided.</p>"

    # Groups
    G = res["groups"]
    if G["rows"]:
        grow = "".join(f"<tr><td>{html.escape(g['name'])}</td><td class='num'>{fmt(g['totalUsers']) if g['totalUsers'] else '-'}</td><td class='num'>{fmt(g['membersUsed'])}</td>"
                       f"<td class='num' data-v='{g['activationRate'] or 0}'>{'-' if g['activationRate'] is None else fmt(g['activationRate'],0)+'%'}</td><td class='num'>{fmt(g['used'])}</td><td class='num'>{fmt(g['avgPerUserPerDay'],0)}</td><td class='num'>{fmt(g['sessions'])}</td><td>{g['lastActivity'] or '-'}</td></tr>" for g in G["rows"])
        grp_html = f"""<p class="note">Users can belong to several groups, so group totals overlap ({fmt(G['sumOfGroups'])} summed vs {fmt(h['totalCredits'])} actual). Activation = members that used credits / total members.</p>
        {bar_rows(G['rows'][:8], 'used', 'name')}
        <table style="margin-top:12px"><thead><tr><th onclick="sortTable(this)">Group</th><th class="num" onclick="sortTable(this)">Members</th><th class="num" onclick="sortTable(this)">Members used</th><th class="num" onclick="sortTable(this)">Activation</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Avg/user/day</th><th class="num" onclick="sortTable(this)">Sessions</th><th onclick="sortTable(this)">Last activity</th></tr></thead><tbody>{grow}</tbody></table>"""
    else:
        grp_html = "<p class='note'>Groups export not provided.</p>"

    # Users
    U = res["users"]

    def ucolor(u):
        if u["pctUsed"] is None:
            return ""
        return "bad" if u["pctUsed"] >= 100 else ("warn" if u["pctUsed"] >= near_pct else "")
    top_html = bar_rows(U["top10"], "used", "displayName", total=U["total"] or None, color=ucolor)
    tier_rows = "".join(f"<tr><td class='num'>{fmt(t['limit']) if t['limit'] else 'none'}</td><td class='num'>{t['users']}</td><td class='num'>{fmt(t['used'])}</td><td class='num'>{fmt(t['avgUsed'])}</td><td class='num'>{'-' if t['avgPctOfLimit'] is None else fmt(t['avgPctOfLimit'],0)+'%'}</td></tr>" for t in U["limitTiers"])
    urows = "".join(
        f"<tr><td>{html.escape(name(u))}</td><td class='note'>{html.escape(upn(u))}</td><td class='num'>{fmt(u['used'])}</td><td class='num'>{fmt(u['limit'])}</td>"
        f"<td class='num' data-v='{u['pctUsed'] or 0}'>{'-' if u['pctUsed'] is None else fmt(u['pctUsed'],0)+'%'}</td><td class='num'>{fmt(u.get('tasks'))}</td><td class='num'>{fmt(u.get('creditsPerTask'))}</td>"
        f"<td class='num'>{fmt(u['sessions'])}</td><td>{'Yes' if u['licensed'] else '<b>No</b>'}</td><td>{u['lastActivity'] or '-'}</td>"
        f"<td>{html.escape(u.get('department') or '-')}</td><td>{html.escape(u.get('manager') or '-')}</td></tr>" for u in U["all"])
    watch = (f"<b>{len(U['overLimit'])}</b> over limit &middot; <b>{len(U['nearLimit'])}</b> near limit (&ge;{near_pct}%) &middot; "
             f"<b>{len(U['dormant'])}</b> dormant &middot; <b>{len(U['unlicensed'])}</b> unlicensed consumers")
    users_html = f"""<p class="note">Top 10 users = {fmt(U['top10Share'],1)}% of credits; top {U['top20pctCount']} users (20% of consumers) = {fmt(U['top20pctShare'],1)}%. Watchlist: {watch}.</p>
    <div class="tabs"><button class="on" onclick="tab(this,'u-top')">Top consumers</button><button onclick="tab(this,'u-tiers')">Limit tiers</button><button onclick="tab(this,'u-all')">All users</button></div>
    <div id="u-top" class="pane">{top_html}</div>
    <div id="u-tiers" class="pane hide"><table><thead><tr><th class="num">Monthly limit</th><th class="num">Users</th><th class="num">Credits</th><th class="num">Avg per user</th><th class="num">Avg % of limit</th></tr></thead><tbody>{tier_rows}</tbody></table></div>
    <div id="u-all" class="pane hide"><input class="search" placeholder="Filter users..." oninput="filterTable(this,'utab')"><table id="utab"><thead><tr><th onclick="sortTable(this)">User</th><th onclick="sortTable(this)">UPN</th><th class="num" onclick="sortTable(this)">Credits</th><th class="num" onclick="sortTable(this)">Limit</th><th class="num" onclick="sortTable(this)">% used</th><th class="num" onclick="sortTable(this)">Tasks</th><th class="num" onclick="sortTable(this)">Credits/task</th><th class="num" onclick="sortTable(this)">Sessions</th><th onclick="sortTable(this)">Licence</th><th onclick="sortTable(this)">Last activity</th><th onclick="sortTable(this)">Department</th><th onclick="sortTable(this)">Manager</th></tr></thead><tbody>{urows}</tbody></table></div>"""

    # Departments & managers
    O = res["org"]

    def org_table(rows, first_label, extra_cols=""):
        tr = "".join(
            f"<tr><td>{html.escape(r['name'])}</td><td class='num'>{r['users']}</td><td class='num'>{r['consuming']}</td><td class='num'>{fmt(r['used'])}</td>"
            f"<td class='num' data-v='{r['share']}'>{fmt(r['share'],1)}%</td><td class='num'>{fmt(r['avgPerUser'])}</td><td class='num'>{fmt(r['tasks']) if r['tasks'] else '-'}</td>"
            f"<td class='num'>{fmt(r['creditsPerTask'])}</td><td class='num'>{r['nearOrOver']}</td><td>{html.escape(r['topUser'])}</td></tr>" for r in rows)
        return (f"<table><thead><tr><th onclick=\"sortTable(this)\">{first_label}</th><th class='num' onclick=\"sortTable(this)\">Users</th><th class='num' onclick=\"sortTable(this)\">Consuming</th>"
                f"<th class='num' onclick=\"sortTable(this)\">Credits</th><th class='num' onclick=\"sortTable(this)\">Share</th><th class='num' onclick=\"sortTable(this)\">Avg / user</th><th class='num' onclick=\"sortTable(this)\">Tasks</th>"
                f"<th class='num' onclick=\"sortTable(this)\">Credits / task</th><th class='num' onclick=\"sortTable(this)\">&ge;{near_pct}% of limit</th><th onclick=\"sortTable(this)\">Top user</th></tr></thead><tbody>{tr}</tbody></table>")

    if O["provided"]:
        def dcolor(r):
            return "warn" if r["name"].startswith("(") else ""
        dept_rows = O["departments"]
        mgr_rows = O["managers"]
        dept_html = f"""<p class="note">Directory coverage: {O['enrichedUsers']} of {res['users']['count']} consuming users matched ({fmt(O['coverage'],0)}%). Source: Microsoft Graph user profiles (department, manager) or an Entra user export.</p>
        {bar_rows(dept_rows[:10], 'used', 'name', total=res['users']['total'] or None, color=dcolor)}
        <div style="margin-top:12px">{org_table(dept_rows, 'Department')}</div>"""
        mgr_html = f"""<p class="note">Manager roll-up uses each user's direct manager from the directory. Send each manager their own row - they decide whether their team's usage justifies the credits.</p>
        {bar_rows(mgr_rows[:10], 'used', 'name', total=res['users']['total'] or None, color=dcolor)}
        <div style="margin-top:12px">{org_table(mgr_rows, 'Manager')}</div>"""
        country_html = ""
        if O["countries"]:
            country_html = f"""<div class="card" style="grid-column:1/-1"><h2>Countries <small>usage location</small></h2>{bar_rows(O['countries'][:12], 'used', 'name', total=res['users']['total'] or None)}</div>"""
        org_cards = (f'<div class="card" style="grid-column:1/-1"><h2>Departments <small>who is spending</small></h2>{dept_html}</div>'
                     f'<div class="card" style="grid-column:1/-1"><h2>Managers <small>accountability view</small></h2>{mgr_html}</div>{country_html}')
    else:
        org_cards = ('<div class="card" style="grid-column:1/-1"><h2>Departments &amp; managers</h2><p class="note">No directory data was supplied. '
                     'Provide Microsoft Graph user data (<code>/users?$select=department,jobTitle,usageLocation&amp;$expand=manager</code>) or an Entra user export with '
                     '<code>--org</code> to add per-department and per-manager reporting.</p></div>')

    # Recommendations
    rec_html = "".join(f'<div class="rec {r["priority"]}"><b><span class="pill {r["priority"]}">{r["priority"]}</span> {html.escape(r["title"])}</b>'
                       f'<div class="ev">Evidence: {html.escape(r["evidence"])}</div><div class="ac">{html.escape(r["action"])}</div></div>' for r in res["recommendations"]) or "<p class='note'>No recommendations triggered.</p>"

    # Forecast card
    if f["mode"] == "monthly":
        fc_html = (f"<p>Billing month <b>{f['periodStart']}</b> to <b>{f['periodEnd']}</b>: {fmt(h['totalCredits'])} credits in {f['daysElapsed']} of {f['daysInPeriod']} days "
                   f"= <b>{fmt(f['dailyRunRate'])}/day</b>. Straight-line projection: <b>{fmt(f['projectedPeriodTotal'])}</b> credits (~{money(f['projectedCost'], cur)} at list rate).</p>")
    else:
        fc_html = (f"<p>Accumulated view from <b>{f['periodStart']}</b> to <b>{f['periodEnd']}</b> ({f['monthsElapsed']} months): "
                   f"<b>{fmt(f['dailyRunRate'])}/day</b>, <b>{fmt(f['monthlyRunRate'])}/month</b>, annualised <b>{fmt(f['annualisedCredits'])}</b> credits "
                   f"(~{money(f['annualisedCost'], cur)} at list rate).</p>")
    fc_html += "<p class='note'>Run-rates are straight-line on observed data and assume no policy changes. Use them for sizing capacity packs, not as an invoice.</p>"
    fc_html += f"<p class='note'>Credits-per-task uses the {fmt(h.get('matchedTaskUsers'))} users present in both the consumption and usage exports ({fmt(h.get('matchedTasks'))} of {fmt(h.get('totalTasks'))} tasks).</p>" if h.get("matchedTasks") else ""

    dq = "".join(f"<li>{html.escape(n)}</li>" for n in res["dataQuality"])
    inputs = "".join(f"<li>{html.escape(k)}: {html.escape(os.path.basename(v))}</li>" for k, v in res["meta"]["inputs"].items())

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(res['meta']['title'])}</title><style>{CSS}</style></head><body>
<header><h1>{html.escape(res['meta']['title'])}</h1><p>Cowork &amp; Work IQ consumption &middot; as of {res['meta']['asOf']} &middot; source: Microsoft 365 admin center exports &middot; reporting only</p></header>
<main>
<div class="kpis">{kpi_html}</div>
<div class="grid">
<div class="card" style="grid-column:1/-1"><h2>Recommendations <small>evidence-backed, sorted by priority</small></h2>{rec_html}</div>
<div class="card"><h2>Service breakdown <small>prepaid vs pay-as-you-go</small></h2>{svc_html}</div>
<div class="card"><h2>Forecast &amp; run-rate</h2>{fc_html}</div>
<div class="card" style="grid-column:1/-1"><h2>Spending-limit analysis <small>policies</small></h2>{pol_html}</div>
{org_cards}
<div class="card" style="grid-column:1/-1"><h2>Groups</h2>{grp_html}</div>
<div class="card" style="grid-column:1/-1"><h2>Users</h2>{users_html}</div>
<div class="card" style="grid-column:1/-1"><h2>Data quality &amp; caveats</h2><ul>{dq}<li>Exports are point-in-time snapshots; the live dashboard refreshes every 2 hours and may differ.</li><li>Usage above a per-user soft limit completes the task, is not billed, and is not shown as consumed credits.</li><li>The Microsoft invoice (Azure subscription named in the billing method) is the record of truth; costs here use list rate {cur} {rate}/credit for pay-as-you-go and {cur} {res['meta']['prepaidRate']}/credit for prepaid.</li></ul>
<p class="note">Inputs:</p><ul class="note">{inputs}</ul></div>
</div>
<div class="foot">Generated by the Cowork &amp; Work IQ Consumption Advisor skill. Self-contained file - no external scripts, safe to email or store in SharePoint.</div>
</main><script>{JS}</script></body></html>"""


def render_md(res):
    h, f, cur = res["headline"], res["forecast"], res["meta"]["currency"]
    lines = [f"# {res['meta']['title']}", f"*As of {res['meta']['asOf']} - Microsoft 365 admin center exports*", "",
             "## Headline", f"- **Copilot Credits used:** {fmt(h['totalCredits'])}" + (f" ({fmt(h['prepaidShare'],1)}% prepaid)" if h['prepaidShare'] is not None else ""),
             f"- **Estimated cost:** {money(h['estimatedCost'], cur)} (list {money(h['listCost'], cur)}; {h['costBasis']})",
             f"- **Active users:** {fmt(h['activeUsers'])} - {fmt(h['creditsPerActiveUser'])} credits per active user, median {fmt(h['medianCreditsPerUser'])}"]
    if h["creditsPerTask"]:
        lines.append(f"- **Credits per task:** {fmt(h['creditsPerTask'])} over {fmt(h['matchedTasks'])} tasks of users in both exports ({fmt(h['totalTasks'])} Cowork tasks in total, {fmt(h['scheduledTaskShare'],1)}% scheduled)")
    if f["mode"] == "monthly":
        lines.append(f"- **Forecast:** {fmt(f['projectedPeriodTotal'])} credits by {f['periodEnd']} (~{money(f['projectedCost'], cur)})")
    else:
        lines.append(f"- **Run-rate:** {fmt(f['monthlyRunRate'])} credits/month, annualised {fmt(f['annualisedCredits'])} (~{money(f['annualisedCost'], cur)})")
    P = res["policies"]
    if P["rows"]:
        lines += ["", "## Spending limits", f"- {P['unlimitedCount']} active policies without a limit carry {fmt(P['unlimitedShare'],1)}% of credits",
                  f"- Near limit: {', '.join(P['nearLimit']) or 'none'}; idle: {', '.join(P['idle']) or 'none'}"]
    O = res["org"]
    if O["provided"]:
        lines += ["", f"## Departments ({fmt(O['coverage'],0)}% of users matched)"]
        for d in O["departments"][:8]:
            lines.append(f"- {d['name']}: {fmt(d['used'])} credits ({d['share']}%), {d['users']} users, {fmt(d['avgPerUser'])} per user, {d['nearOrOver']} near/over limit")
        lines += ["", "## Managers"]
        for m in O["managers"][:8]:
            lines.append(f"- {m['name']}: {fmt(m['used'])} credits ({m['share']}%), {m['users']} users, {m['nearOrOver']} near/over limit")
    U = res["users"]
    lines += ["", "## Users", f"- Top 10 users = {fmt(U['top10Share'],1)}% of credits; {len(U['overLimit'])} over limit, {len(U['nearLimit'])} near limit, {len(U['dormant'])} dormant"]
    lines += ["", "## Recommendations"]
    for r in res["recommendations"]:
        lines.append(f"- **[{r['priority']}] {r['title']}** - {r['evidence']} -> {r['action']}")
    if res["dataQuality"]:
        lines += ["", "## Data quality"] + [f"- {n}" for n in res["dataQuality"]]
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
    ap.add_argument("--title", default="Cowork & Work IQ Consumption Report")
    ap.add_argument("--anonymize", action="store_true",
                    help="replace user and manager names/UPNs with stable pseudonyms in ALL outputs (HTML, JSON, Markdown)")
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[A-Za-z]{3}", args.currency):
        print("ERROR: --currency must be a 3-letter ISO 4217 code (e.g. USD, EUR)", file=sys.stderr)
        return 2
    args.currency = args.currency.upper()
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
            print(f"skip (unrecognised columns): {os.path.basename(fpath)} -> {header[:6]}", file=sys.stderr)
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
    res["meta"]["detected"] = detected
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "consumption-analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    with open(os.path.join(args.out, "consumption-report.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(res, anonymize=args.anonymize))
    with open(os.path.join(args.out, "consumption-summary.md"), "w", encoding="utf-8") as fh:
        fh.write(render_md(res))
    print("\n".join(detected))
    print(f"as-of {as_of}; total credits {res['headline']['totalCredits']:,}; {len(res['recommendations'])} recommendations; "
          f"{len(res['dataQuality'])} data-quality notes")
    print(f"written: {args.out}/consumption-report.html, consumption-analysis.json, consumption-summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
