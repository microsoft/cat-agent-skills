#!/usr/bin/env python3
"""
Copilot Credit forecast engine for standard-harness Microsoft Copilot Studio agents.

Reads a JSON model of an agent's design and expected volumes, and produces a
three-scenario credit and cost forecast, a ranked list of cost hotspots, a
sensitivity analysis, and a purchasing-model comparison.

This engine does not model agents powered by the GitHub Copilot harness. That
harness uses a separate usage-based model covering build, test, evaluation, and
runtime activity.

Usage:
    python3 forecast.py config.json
    python3 forecast.py config.json --json out.json
    python3 forecast.py --schema        # print an annotated example config

Standard library only. No network access. Reads nothing but the config file.

RATES: verified against Microsoft Learn "Copilot Credits billing rates" on
2026-08-24. Re-verify before publishing a forecast and update RATES_VERIFIED_ON.
https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-messages-management
"""

import argparse
import json
import sys
from copy import deepcopy

RATES_VERIFIED_ON = "2026-08-24"
SUPPORTED_HARNESS = "standard"

# Credits per single execution of the feature.
RATES = {
    "classic_answer": 1.0,
    "generative_answer": 2.0,
    "agent_action": 5.0,
    "tenant_graph_grounding": 10.0,
    "agent_flow_action": 0.13,        # 13 credits per 100 flow actions
    "ai_tool_basic": 0.1,             # 1 credit per 10 responses
    "ai_tool_standard": 1.5,          # 15 credits per 10 responses
    "ai_tool_premium": 10.0,          # 100 credits per 10 responses
    "content_processing_page": 8.0,   # per page
    "reasoning_per_1k_tokens": 10.0,  # premium AI tools rate, charged ON TOP
}

VOICE_RATES_PER_MINUTE = {
    "classic": 10.0,
    "genai": 35.0,
    "premium_genai": 75.0,
}

BASE_TYPES = ("classic_answer", "generative_answer", "agent_action")


# --------------------------------------------------------------------------
# Credit model
# --------------------------------------------------------------------------

def require_supported_harness(cfg):
    """Reject configs for harnesses this feature-rate model does not support."""
    harness = cfg.get("harness")
    if harness != SUPPORTED_HARNESS:
        supplied = "missing" if harness is None else repr(harness)
        raise ValueError(
            f"config harness is {supplied}; expected '{SUPPORTED_HARNESS}'. "
            "GitHub Copilot harness agents require a separate range-based model."
        )

def path_credits(path):
    """Credits consumed by one execution of a conversation path.

    Features stack within a single interaction: a generative answer that also
    grounds on the tenant graph costs 2 + 10 = 12, not 10.
    """
    ptype = path.get("type", "generative_answer")
    if ptype not in BASE_TYPES and ptype != "none":
        raise ValueError(
            f"path '{path.get('name')}': unknown type '{ptype}' "
            f"(expected one of {BASE_TYPES + ('none',)})"
        )

    breakdown = {}

    if ptype in BASE_TYPES:
        n = float(path.get("executions_per_turn", 1))
        breakdown[ptype] = RATES[ptype] * n

    if path.get("tenant_graph_grounding"):
        breakdown["tenant_graph_grounding"] = RATES["tenant_graph_grounding"]

    flow_actions = float(path.get("flow_actions", 0))
    if flow_actions:
        breakdown["agent_flow_action"] = RATES["agent_flow_action"] * flow_actions

    tier = path.get("ai_tool_tier")            # basic | standard | premium
    if tier:
        key = f"ai_tool_{tier}"
        if key not in RATES:
            raise ValueError(f"path '{path.get('name')}': unknown ai_tool_tier '{tier}'")
        breakdown[key] = RATES[key] * float(path.get("ai_tool_responses", 1))

    pages = float(path.get("content_pages", 0))
    if pages:
        breakdown["content_processing_page"] = RATES["content_processing_page"] * pages

    tokens = float(path.get("reasoning_tokens", 0))
    if tokens:
        breakdown["reasoning"] = RATES["reasoning_per_1k_tokens"] * (tokens / 1000.0)

    return sum(breakdown.values()), breakdown


def apply_overrides(path, scenario):
    """Merge a path's per-scenario overrides, e.g. {"worst": {"tenant_graph_grounding": true}}."""
    out = deepcopy(path)
    out.pop("scenarios", None)
    override = (path.get("scenarios") or {}).get(scenario)
    if override:
        out.update(override)
    return out


def population_credits(pop, scenario, turns_key):
    """Credits per month for one population, plus a per-path breakdown."""
    turns = pop.get("turns_per_session", {})
    turns_per_session = float(turns.get(turns_key, turns.get("p50", 4)))

    mau = float(pop["monthly_active_users"]) * float(
        pop.get("scenario_user_multiplier", {}).get(scenario, 1.0)
    )
    sessions = mau * float(pop["sessions_per_user_per_month"])

    shares = sum(float(p.get("share_of_turns", 0)) for p in pop.get("paths", []))
    if pop.get("paths") and abs(shares - 1.0) > 0.02:
        print(
            f"  ! warning: path shares for '{pop['name']}' sum to {shares:.2f}, not 1.00",
            file=sys.stderr,
        )

    per_path = {}
    feature_totals = {}

    for raw in pop.get("paths", []):
        p = apply_overrides(raw, scenario)
        per_exec, breakdown = path_credits(p)
        turns_on_path = sessions * turns_per_session * float(p.get("share_of_turns", 0))
        per_path[p["name"]] = per_exec * turns_on_path
        for feature, credits in breakdown.items():
            feature_totals[feature] = feature_totals.get(feature, 0.0) + credits * turns_on_path

    # Once-per-session costs: greeting, auth, initial grounding.
    for raw in pop.get("per_session_fixed", []):
        p = apply_overrides(raw, scenario)
        per_exec, breakdown = path_credits(p)
        count = sessions * float(p.get("count", 1))
        name = f"{p['name']} (per session)"
        per_path[name] = per_exec * count
        for feature, credits in breakdown.items():
            feature_totals[feature] = feature_totals.get(feature, 0.0) + credits * count

    # Voice bills per minute and includes core agent activity for that minute.
    voice = pop.get("voice")
    if voice:
        rate = VOICE_RATES_PER_MINUTE[voice["tier"]]
        minutes = sessions * float(voice["minutes_per_session"])
        per_path[f"voice ({voice['tier']})"] = rate * minutes
        feature_totals["voice"] = feature_totals.get("voice", 0.0) + rate * minutes

    total = sum(per_path.values())

    # Zero-rating applies only to employee-facing traffic from users
    # authenticated with a Microsoft 365 Copilot identity.
    share = float(pop.get("m365_copilot_licensed_share", 0.0))
    if not pop.get("employee_facing", True):
        share = 0.0
    billable = total * (1.0 - share)

    return {
        "population": pop["name"],
        "sessions": sessions,
        "turns_per_session": turns_per_session,
        "credits": total,
        "billable_credits": billable,
        "zero_rated_share": share,
        "per_path": per_path,
        "per_feature": feature_totals,
    }


def run_scenario(cfg, scenario, turns_key):
    parts = [population_credits(p, scenario, turns_key) for p in cfg["populations"]]
    total = sum(p["credits"] for p in parts)
    billable = sum(p["billable_credits"] for p in parts)

    per_path, per_feature = {}, {}
    for p in parts:
        for k, v in p["per_path"].items():
            per_path[f"{p['population']} / {k}"] = per_path.get(f"{p['population']} / {k}", 0.0) + v
        for k, v in p["per_feature"].items():
            per_feature[k] = per_feature.get(k, 0.0) + v

    return {
        "scenario": scenario,
        "credits": total,
        "billable_credits": billable,
        "sessions": sum(p["sessions"] for p in parts),
        "populations": parts,
        "per_path": per_path,
        "per_feature": per_feature,
    }


SCENARIOS = [("base", "p50"), ("peak", "p90"), ("worst", "p90")]


# --------------------------------------------------------------------------
# Purchasing, sensitivity
# --------------------------------------------------------------------------

def purchasing(cfg, billable_credits):
    """Compare purchasing motions. Returns [] unless the user supplied prices.

    Never invent a price per credit: it varies by agreement, region and date.
    """
    pur = cfg.get("purchasing") or {}
    cur = pur.get("currency", "")
    rows = []

    payg = pur.get("payg_price_per_credit")
    if payg:
        rows.append({
            "model": "Pay-as-you-go",
            "monthly_cost": billable_credits * float(payg),
            "note": "no commitment, highest unit rate",
        })

    pack = pur.get("prepaid_pack")
    if pack:
        import math
        packs = math.ceil(billable_credits / float(pack["credits"])) if billable_credits else 0
        cost = packs * float(pack["price"])
        util = billable_credits / (packs * float(pack["credits"])) if packs else 0.0
        rows.append({
            "model": "Prepaid Copilot Credit packs",
            "monthly_cost": cost,
            "note": f"{packs} pack(s), {util:.0%} utilization — unused credits do not roll over",
        })

    commit = pur.get("commit_price_per_credit")
    if commit:
        rows.append({
            "model": "Credit Commit Units (1-year)",
            "monthly_cost": billable_credits * float(commit),
            "note": "lowest unit rate, needs a defensible annual forecast",
        })

    for r in rows:
        r["currency"] = cur
    return rows


def sensitivity(cfg, base_total):
    """Which assumptions actually move the answer. +/-25% on each, one at a time."""
    out = []
    for label, mutate in (
        ("turns per session", _mut_turns),
        ("monthly active users", _mut_mau),
        ("M365 Copilot licence share", _mut_share),
    ):
        for delta in (-0.25, 0.25):
            c = mutate(deepcopy(cfg), delta)
            total = run_scenario(c, "base", "p50")["billable_credits"]
            change = (total - base_total) / base_total if base_total else 0.0
            out.append({"assumption": label, "input_delta": delta, "output_delta": change})
    out.sort(key=lambda r: -abs(r["output_delta"]))
    return out


def _mut_turns(cfg, d):
    for p in cfg["populations"]:
        for k in ("p50", "p90"):
            if k in p.get("turns_per_session", {}):
                p["turns_per_session"][k] *= (1 + d)
    return cfg


def _mut_mau(cfg, d):
    for p in cfg["populations"]:
        p["monthly_active_users"] *= (1 + d)
    return cfg


def _mut_share(cfg, d):
    for p in cfg["populations"]:
        s = p.get("m365_copilot_licensed_share", 0.0)
        p["m365_copilot_licensed_share"] = max(0.0, min(1.0, s * (1 + d)))
    return cfg


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def n(x, dp=0):
    return f"{x:,.{dp}f}"


def report(cfg, results, lines):
    w = lines.append
    w(f"# Standard-harness Copilot Credit forecast — {cfg.get('agent', 'unnamed agent')}")
    w("")
    w(f"Rates verified on **{RATES_VERIFIED_ON}**. Re-verify before circulating.")
    w("")

    w("## Monthly forecast")
    w("")
    w("| Scenario | Sessions | Credits | Billable credits | Credits / session |")
    w("|---|---:|---:|---:|---:|")
    for r in results:
        cps = r["credits"] / r["sessions"] if r["sessions"] else 0
        w(f"| {r['scenario']} | {n(r['sessions'])} | {n(r['credits'])} "
          f"| {n(r['billable_credits'])} | {cps:.1f} |")
    w("")

    base = results[0]
    w("## Cost hotspots (base scenario)")
    w("")
    w("| Rank | Path | Credits / month | Share |")
    w("|---:|---|---:|---:|")
    ranked = sorted(base["per_path"].items(), key=lambda kv: -kv[1])
    for i, (name, credits) in enumerate(ranked[:8], 1):
        share = credits / base["credits"] if base["credits"] else 0
        w(f"| {i} | {name} | {n(credits)} | {share:.1%} |")
    w("")

    w("## Consumption by billed feature (base scenario)")
    w("")
    w("| Feature | Credits / month | Share |")
    w("|---|---:|---:|")
    for feature, credits in sorted(base["per_feature"].items(), key=lambda kv: -kv[1]):
        share = credits / base["credits"] if base["credits"] else 0
        w(f"| {feature} | {n(credits)} | {share:.1%} |")
    w("")

    zero_rated = base["credits"] - base["billable_credits"]
    if zero_rated > 0:
        w(f"Zero-rating for Microsoft 365 Copilot licensed users removes "
          f"**{n(zero_rated)} credits/month** ({zero_rated / base['credits']:.0%} of gross "
          f"consumption). Raising licensed coverage or moving employee-facing traffic to "
          f"authenticated M365 Copilot identities is usually the largest single lever.")
        w("")

    priced = [(r, purchasing(cfg, r["billable_credits"])) for r in results]
    if any(rows for _, rows in priced):
        for r, rows in priced:
            w(f"## Purchasing comparison — {r['scenario']} scenario")
            w("")
            w("| Model | Monthly cost | Note |")
            w("|---|---:|---|")
            for row in rows:
                w(f"| {row['model']} | {row['currency']} {n(row['monthly_cost'], 2)} "
                  f"| {row['note']} |")
            w("")
    else:
        w("## Purchasing comparison")
        w("")
        w("Not computed: no prices supplied. Ask the user for their effective price per "
          "credit (pay-as-you-go, prepaid pack, and Credit Commit Unit rates) and re-run. "
          "**Never convert credits to currency from memory** — the rate varies by "
          "agreement, region and date.")
        w("")

    w("## Sensitivity (base scenario, one assumption at a time)")
    w("")
    w("| Assumption | Input change | Billable credit change |")
    w("|---|---:|---:|")
    for row in sensitivity(cfg, base["billable_credits"]):
        w(f"| {row['assumption']} | {row['input_delta']:+.0%} | {row['output_delta']:+.1%} |")
    w("")
    w("The assumption at the top of that table is the one to replace with real telemetry "
      "first. Re-baseline the whole model after two weeks of production traffic.")
    w("")

    out_of_model = cfg.get("out_of_model_costs") or []
    if out_of_model:
        w("## Out of model")
        w("")
        w("Priced separately, not included in any figure above:")
        w("")
        for item in out_of_model:
            w(f"- {item}")
        w("")

    assumptions = cfg.get("assumptions") or []
    if assumptions:
        w("## Stated assumptions")
        w("")
        for a in assumptions:
            w(f"- {a}")
        w("")

    return lines


EXAMPLE = {
    "harness": "standard",
    "agent": "HR Assistant",
    "assumptions": [
        "Turns per session estimated from comparable Q&A agents; replace after 2 weeks live.",
        "Licence share taken from the June entitlement report.",
    ],
    "out_of_model_costs": ["Workday API contract", "Azure Function hosting for the payslip tool"],
    "purchasing": {
        "currency": "EUR",
        "payg_price_per_credit": 0.01,
        "prepaid_pack": {"credits": 25000, "price": 200.0},
        "commit_price_per_credit": 0.0068,
    },
    "populations": [
        {
            "name": "Employees",
            "employee_facing": True,
            "monthly_active_users": 4000,
            "sessions_per_user_per_month": 3,
            "turns_per_session": {"p50": 4, "p90": 9},
            "m365_copilot_licensed_share": 0.35,
            "scenario_user_multiplier": {"peak": 1.3, "worst": 1.6},
            "per_session_fixed": [{"name": "greeting", "type": "classic_answer", "count": 1}],
            "paths": [
                {
                    "name": "policy Q&A",
                    "type": "generative_answer",
                    "share_of_turns": 0.45,
                    "scenarios": {"worst": {"tenant_graph_grounding": True}},
                },
                {"name": "menu / navigation", "type": "classic_answer", "share_of_turns": 0.2},
                {
                    "name": "cross-tenant people search",
                    "type": "generative_answer",
                    "share_of_turns": 0.15,
                    "tenant_graph_grounding": True,
                },
                {
                    "name": "leave request",
                    "type": "agent_action",
                    "share_of_turns": 0.12,
                    "executions_per_turn": 2,
                },
                {
                    "name": "payslip lookup flow",
                    "type": "agent_action",
                    "share_of_turns": 0.08,
                    "flow_actions": 40,
                },
            ],
        },
        {
            "name": "External candidates",
            "employee_facing": False,
            "monthly_active_users": 900,
            "sessions_per_user_per_month": 1.5,
            "turns_per_session": {"p50": 5, "p90": 11},
            "paths": [
                {"name": "job FAQ", "type": "generative_answer", "share_of_turns": 0.8},
                {"name": "handoff to recruiter", "type": "agent_action", "share_of_turns": 0.2},
            ],
        },
    ],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", nargs="?", help="path to the agent model JSON")
    ap.add_argument("--json", metavar="PATH", help="also write structured results here")
    ap.add_argument("--schema", action="store_true", help="print an example config and exit")
    args = ap.parse_args()

    if args.schema:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.config:
        ap.error("config is required (or use --schema)")

    with open(args.config) as fh:
        cfg = json.load(fh)

    try:
        require_supported_harness(cfg)
    except ValueError as exc:
        ap.error(str(exc))

    results = [run_scenario(cfg, s, t) for s, t in SCENARIOS]
    lines = report(cfg, results, [])
    print("\n".join(lines))

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"harness": SUPPORTED_HARNESS,
                       "rates_verified_on": RATES_VERIFIED_ON,
                       "rates": RATES,
                       "scenarios": results}, fh, indent=2)
        print(f"\n[structured results written to {args.json}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
