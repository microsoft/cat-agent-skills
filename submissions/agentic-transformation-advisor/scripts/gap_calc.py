#!/usr/bin/env python3
"""Compute per-pillar maturity gaps, scale-breaker and weakest pillar.

Input JSON (see assets/example-input-contoso.json):
{
  "organization": "Contoso",
  "scope": "Customer Service",
  "current": {"ai_strategy": 200, "business_strategy": 200,
              "governance_security": 300, "technology_data": 200,
              "organization_culture": null},
  "patterns": ["employee_ai_enablement", "external_engagement"],
  "target_source": "summary"            # optional: summary | deep-dive | custom
  "custom_targets": {"pattern_key": {"pillar": 300 or [200, 300]}}  # when custom
}

Targets come from Microsoft Learn (verified 2026-11-24):
  summary   -> https://learn.microsoft.com/en-us/agents/adoption-patterns/choose-pattern
  deep-dive -> the per-pattern pages under /agents/adoption-patterns/

Gaps are counted in levels (100 points = one level). A range target is kept
as [min, max]: gap_to_min drives the readiness verdict, gap_to_max drives the
scale-breaker. Unknown (null) current levels are reported, never treated as 0.
No overall or average score is produced, by design.
"""
import argparse
import json
import sys

PILLARS = [
    ("ai_strategy", "AI strategy and experience"),
    ("business_strategy", "Business strategy"),
    ("governance_security", "Governance and security"),
    ("technology_data", "Technology and data"),
    ("organization_culture", "Organization and culture"),
]
PILLAR_KEYS = [p[0] for p in PILLARS]
PILLAR_NAMES = dict(PILLARS)

PATTERNS = {
    "employee_ai_enablement": {
        "name": "Employee AI enablement", "mode": "Assist",
        "named_scale_breaker": "organization_culture",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-employee-ai-enablement",
    },
    "business_expert_empowerment": {
        "name": "Business expert empowerment", "mode": "Assist",
        "named_scale_breaker": "technology_data",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-business-expert-empowerment",
    },
    "workplace_it_services": {
        "name": "Workplace and IT services", "mode": "Execute",
        "named_scale_breaker": "business_strategy",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-workplace-it-services",
    },
    "core_business_process": {
        "name": "Core business process transformation", "mode": "Execute",
        "named_scale_breaker": "business_strategy",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-core-business-process",
    },
    "external_engagement": {
        "name": "External engagement", "mode": "Execute",
        "named_scale_breaker": "governance_security",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-external-engagement",
    },
    "ai_first_capabilities": {
        "name": "AI-first capabilities", "mode": "Execute",
        "named_scale_breaker": "technology_data",
        "url": "https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-ai-first-capabilities",
    },
}

# Order: ai_strategy, business_strategy, governance_security, technology_data, organization_culture
SUMMARY_TARGETS = {
    "employee_ai_enablement": [200, [200, 300], 200, [200, 300], 300],
    "business_expert_empowerment": [200, 200, 300, 300, 300],
    "workplace_it_services": [[300, 400], 400, 400, 300, [200, 300]],
    "core_business_process": [500, 500, 400, 400, 400],
    "external_engagement": [[300, 400], 400, 500, 400, 200],
    "ai_first_capabilities": [500, 500, 500, 500, 500],
}
# Deep-dive pages; "400 or higher" is recorded as 400.
DEEP_DIVE_TARGETS = {
    "employee_ai_enablement": [200, 200, 200, 200, 300],
    "business_expert_empowerment": [200, 200, 300, 300, 300],
    "workplace_it_services": [400, 400, 400, 300, 300],
    "core_business_process": [500, 500, 400, 400, 400],
    "external_engagement": [400, 400, 500, 400, 400],
    "ai_first_capabilities": [500, 500, 500, 500, 500],
}
SOURCE_URL = {
    "summary": "https://learn.microsoft.com/en-us/agents/adoption-patterns/choose-pattern",
    "deep-dive": "per-pattern pages under https://learn.microsoft.com/en-us/agents/adoption-patterns/",
    "custom": "user-supplied targets",
}
VALID_LEVELS = {100, 200, 300, 400, 500}


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def norm_range(value, where):
    if isinstance(value, list):
        if len(value) != 2:
            fail(f"{where}: a range must be [min, max]")
        lo, hi = value
    else:
        lo = hi = value
    for v in (lo, hi):
        if v not in VALID_LEVELS:
            fail(f"{where}: {v} is not a level (100, 200, 300, 400, 500)")
    if lo > hi:
        fail(f"{where}: min {lo} is above max {hi}")
    return lo, hi


def load_targets(source, custom):
    if source == "summary":
        table = SUMMARY_TARGETS
    elif source == "deep-dive":
        table = DEEP_DIVE_TARGETS
    elif source == "custom":
        if not isinstance(custom, dict) or not custom:
            fail("target_source is custom but custom_targets is missing")
        out = {}
        for pkey, pillars in custom.items():
            out[pkey] = {k: norm_range(pillars[k], f"custom_targets.{pkey}.{k}")
                         for k in PILLAR_KEYS}
        return out
    else:
        fail(f"unknown target_source '{source}'")
    return {p: {k: norm_range(v, f"{p}.{k}") for k, v in zip(PILLAR_KEYS, vals)}
            for p, vals in table.items()}


def verdict(short_count):
    if short_count == 0:
        return "Meets or exceeds target: strong fit now. Proceed, deliver, then scale."
    if short_count <= 2:
        return ("One or two pillars short: clear scale-breaker. Close it first, "
                "or run a bounded pilot while closing it.")
    return ("Several pillars short: ambition is outrunning readiness. Consider a "
            "more accessible stepping-stone pattern.")


def analyze(profile_targets, current, named=None):
    rows, unknown = [], []
    for k in PILLAR_KEYS:
        lo, hi = profile_targets[k]
        cur = current.get(k)
        if cur is None:
            unknown.append(k)
            rows.append({"pillar": k, "pillar_name": PILLAR_NAMES[k], "current": None,
                         "target_min": lo, "target_max": hi,
                         "gap_to_min_levels": None, "gap_to_max_levels": None})
            continue
        rows.append({"pillar": k, "pillar_name": PILLAR_NAMES[k], "current": cur,
                     "target_min": lo, "target_max": hi,
                     "gap_to_min_levels": max(0, lo - cur) // 100,
                     "gap_to_max_levels": max(0, hi - cur) // 100})
    known = [r for r in rows if r["current"] is not None]
    short = [r for r in known if r["gap_to_min_levels"] > 0]
    sb = None
    if known:
        best = max(r["gap_to_max_levels"] for r in known)
        if best > 0:
            tied = [r for r in known if r["gap_to_max_levels"] == best]
            # tie-break: Learn-named scale-breaker first, then lowest current level
            named_set = named if isinstance(named, (set, frozenset)) else {named}
            tied.sort(key=lambda r: (r["pillar"] not in named_set, r["current"]))
            sb = {"pillar": tied[0]["pillar"], "pillar_name": tied[0]["pillar_name"],
                  "gap_levels": best,
                  "tied_with": [r["pillar_name"] for r in tied[1:]]}
    return {
        "rows": rows,
        "pillars_short_of_min": [r["pillar_name"] for r in short],
        "computed_scale_breaker": sb,
        "verdict": ("Readiness undetermined: collect evidence for unknown pillars before "
                    "deciding whether to proceed or scale.") if unknown else verdict(len(short)),
        "unknown_pillars": [PILLAR_NAMES[k] for k in unknown],
        "verdict_note": ("Verdict excludes unknown pillars; collect evidence before "
                         "relying on it.") if unknown else "",
    }


def run(data):
    current = data.get("current") or {}
    for k in PILLAR_KEYS:
        if k not in current:
            current[k] = None
        elif current[k] is not None and current[k] not in VALID_LEVELS:
            fail(f"current.{k} = {current[k]} is not a level (100-500 or null)")
    extra = set(current) - set(PILLAR_KEYS)
    if extra:
        fail(f"unknown pillar keys in current: {sorted(extra)}")
    selected = data.get("patterns") or []
    if not selected:
        fail("patterns list is empty")
    for p in selected:
        if p not in PATTERNS and data.get("target_source") != "custom":
            fail(f"unknown pattern '{p}'. Valid: {sorted(PATTERNS)}")
    source = data.get("target_source", "summary")
    targets = load_targets(source, data.get("custom_targets"))

    known = {k: v for k, v in current.items() if v is not None}
    weakest = None
    if len(known) == len(PILLAR_KEYS):
        low = min(known.values())
        weakest = {"level": low,
                   "pillars": [PILLAR_NAMES[k] for k in PILLAR_KEYS if known.get(k) == low]}

    per_pattern = {}
    for p in selected:
        if p not in targets:
            fail(f"no targets for pattern '{p}' in source '{source}'")
        meta = PATTERNS.get(p, {"name": p, "mode": "n/a", "named_scale_breaker": None, "url": ""})
        res = analyze(targets[p], current, meta["named_scale_breaker"])
        res.update({"pattern": p, "pattern_name": meta["name"], "mode": meta["mode"],
                    "learn_named_scale_breaker": PILLAR_NAMES.get(meta["named_scale_breaker"]),
                    "learn_url": meta["url"]})
        per_pattern[p] = res

    combined_targets = {k: (max(targets[p][k][0] for p in selected),
                            max(targets[p][k][1] for p in selected)) for k in PILLAR_KEYS}
    named_all = {PATTERNS[p]["named_scale_breaker"] for p in selected if p in PATTERNS}
    combined = analyze(combined_targets, current, named_all)
    if len(selected) > 3:
        combined["warning"] = ("More than three patterns selected. Learn recommends "
                               "capping at two or three.")

    return {
        "organization": data.get("organization"),
        "scope": data.get("scope"),
        "target_source": source,
        "target_source_url": SOURCE_URL[source],
        "current": current,
        "weakest_pillar": weakest,
        "per_pattern": per_pattern,
        "combined": combined,
        "note": "No overall maturity score is computed, by design (Learn: avoid a single score).",
    }


def fmt(v):
    return "Unknown" if v is None else str(v)


def to_markdown(r):
    out = [f"# Gap analysis: {r.get('organization') or ''} {r.get('scope') or ''}".rstrip(), "",
           f"Target source: {r['target_source']} ({r['target_source_url']})", ""]
    if r["weakest_pillar"]:
        w = r["weakest_pillar"]
        out.append(f"Weakest pillar (ceiling): {', '.join(w['pillars'])} at {w['level']}")
        out.append("")
    else:
        out += ["Weakest pillar (ceiling): undetermined until all pillars have evidence.", ""]

    def table(res):
        lines = ["| Pillar | Current | Target | Gap to min (levels) | Gap to target max (levels) |",
                 "|---|---|---|---|---|"]
        for row in res["rows"]:
            tgt = (str(row["target_min"]) if row["target_min"] == row["target_max"]
                   else f"{row['target_min']}-{row['target_max']}")
            lines.append(f"| {row['pillar_name']} | {fmt(row['current'])} | {tgt} | "
                         f"{fmt(row['gap_to_min_levels'])} | {fmt(row['gap_to_max_levels'])} |")
        return lines

    for res in r["per_pattern"].values():
        out += [f"## {res['pattern_name']} ({res['mode']})", ""] + table(res) + [""]
        out.append(f"- Learn-named scale-breaker: {res['learn_named_scale_breaker']}")
        sb = res["computed_scale_breaker"]
        out.append("- Computed scale-breaker: " + (
            f"{sb['pillar_name']} ({sb['gap_levels']} level(s) short)"
            + (f", tied with {', '.join(sb['tied_with'])}" if sb["tied_with"] else "")
            if sb else "none, all known pillars meet the target"))
        out.append(f"- Readiness verdict: {res['verdict']}")
        if res["unknown_pillars"]:
            out.append(f"- Unknown pillars: {', '.join(res['unknown_pillars'])}. {res['verdict_note']}")
        out.append(f"- Source: {res['learn_url']}")
        out.append("")
    c = r["combined"]
    out += ["## Combined profile (highest target per pillar across selected patterns)", ""]
    out += table(c) + [""]
    sb = c["computed_scale_breaker"]
    out.append("- Computed scale-breaker: " + (
        f"{sb['pillar_name']} ({sb['gap_levels']} level(s) short)"
        + (f", tied with {', '.join(sb['tied_with'])}" if sb["tied_with"] else "")
        if sb else "none"))
    out.append("- Tie-break: a pillar Learn names as a scale-breaker for a selected pattern "
               "comes first, then the lowest current level.")
    out.append(f"- Readiness verdict: {c['verdict']}")
    if c["unknown_pillars"]:
        out.append(f"- Unknown pillars: {', '.join(c['unknown_pillars'])}. {c['verdict_note']}")
    if c.get("warning"):
        out.append(f"- Warning: {c['warning']}")
    out += ["", r["note"], ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="profile JSON file")
    ap.add_argument("--json-output", help="write full result JSON here")
    ap.add_argument("--markdown", help="write a markdown gap table here")
    ap.add_argument("--target-source", choices=["summary", "deep-dive", "custom"],
                    help="override target_source in the input")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    if args.target_source:
        data["target_source"] = args.target_source
    result = run(data)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    md = to_markdown(result)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)


if __name__ == "__main__":
    main()
