#!/usr/bin/env python3
"""
Deterministic cost and capacity model.

Arithmetic, not estimation. The LLM interprets the output; this computes it.

The value of this model is in the *ratio* between options and the break-even
point, not the absolute figures. Rates change; the break-even shape does not.
Every output carries a sensitivity band and the rate-card date, because a
confidently wrong cost number discredits the entire report.

Usage:
    python cost_model.py --volume 40000 --analysis analysis.json --out cost.json
    python cost_model.py --volume 40000 --generative-ratio 0.6 --out cost.json
    python cost_model.py --volume 40000 --analysis analysis.json \
        --collision-severity high --out cost.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RATE_CARD_DATE = "2026-07"
SENSITIVITY = 0.40

# ---- Copilot Studio relative consumption weights (see references/rate-card.md)
W_CLASSIC = 1.0
W_GENERATIVE = 10.0
W_ORCHESTRATION = 12.0
W_ACTION = 6.0

# ---- Conversation shape defaults
DEFAULT_TURNS = 4
BASE_ESCALATION = 0.08
COLLISION_ESCALATION = {"none": 0.0, "low": 0.02, "medium": 0.06, "high": 0.10}
RETRY_TURNS_ON_MISROUTE = 3

# ---- Foundry token defaults (per turn)
TOK_SYSTEM = 500
TOK_CONTEXT = 2000
TOK_HISTORY = 1500
TOK_COMPLETION = 400

# ---- Placeholder unit costs. REPLACE with verified current pricing.
#      Present as relative scaffolding, never as a quote.
CREDIT_UNIT_COST = 0.01          # cost per weighted credit unit
FOUNDRY_INPUT_PER_1K = 0.0025
FOUNDRY_OUTPUT_PER_1K = 0.010
SEARCH_FIXED_MONTHLY = 250.0     # standing cost — does not scale with volume
HOSTING_FIXED_MONTHLY = 150.0
SUPPORTING_UPLIFT = 0.15


def band(value: float) -> Dict[str, float]:
    return {
        "point": round(value, 2),
        "low": round(value * (1 - SENSITIVITY), 2),
        "high": round(value * (1 + SENSITIVITY), 2),
    }


DEFAULT_RATE_CARD = Path(__file__).resolve().parent.parent / "references" / "rate-card.json"


def load_rate_card(path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Load the external rate card. Missing/broken file → None (built-in defaults)."""
    p = Path(path) if path else DEFAULT_RATE_CARD
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — degrade to built-in defaults, never crash on cost
        return None


def apply_rate_card(card: Dict[str, Any], region: Optional[str]) -> Tuple[str, List[str]]:
    """Override module rate globals from the card. Returns (region_used, notes)."""
    global CREDIT_UNIT_COST, W_CLASSIC, W_GENERATIVE, W_ORCHESTRATION, W_ACTION
    global FOUNDRY_INPUT_PER_1K, FOUNDRY_OUTPUT_PER_1K, SEARCH_FIXED_MONTHLY
    global HOSTING_FIXED_MONTHLY, SUPPORTING_UPLIFT
    global TOK_SYSTEM, TOK_CONTEXT, TOK_HISTORY, TOK_COMPLETION
    global DEFAULT_TURNS, BASE_ESCALATION, COLLISION_ESCALATION, RETRY_TURNS_ON_MISROUTE
    global RATE_CARD_DATE, SENSITIVITY

    notes: List[str] = []
    RATE_CARD_DATE = card.get("rate_card_date", RATE_CARD_DATE)
    SENSITIVITY = card.get("sensitivity", SENSITIVITY)

    cs = card.get("copilot_studio", {})
    CREDIT_UNIT_COST = cs.get("credit_unit_cost", CREDIT_UNIT_COST)
    w = cs.get("weights", {})
    W_CLASSIC = w.get("classic", W_CLASSIC)
    W_GENERATIVE = w.get("generative", W_GENERATIVE)
    W_ORCHESTRATION = w.get("orchestration", W_ORCHESTRATION)
    W_ACTION = w.get("action", W_ACTION)

    fd = card.get("foundry", {})
    SUPPORTING_UPLIFT = fd.get("supporting_uplift", SUPPORTING_UPLIFT)
    tok = fd.get("tokens", {})
    TOK_SYSTEM = tok.get("system", TOK_SYSTEM)
    TOK_CONTEXT = tok.get("context", TOK_CONTEXT)
    TOK_HISTORY = tok.get("history", TOK_HISTORY)
    TOK_COMPLETION = tok.get("completion", TOK_COMPLETION)

    regions = fd.get("regions", {})
    region_used = region or fd.get("default_region") or "default"
    if regions and region_used not in regions:
        fallback = fd.get("default_region") if fd.get("default_region") in regions else next(iter(regions))
        notes.append(f"region '{region_used}' not in rate card; used '{fallback}'")
        region_used = fallback
    rr = regions.get(region_used, {})
    FOUNDRY_INPUT_PER_1K = rr.get("input_per_1k", FOUNDRY_INPUT_PER_1K)
    FOUNDRY_OUTPUT_PER_1K = rr.get("output_per_1k", FOUNDRY_OUTPUT_PER_1K)
    SEARCH_FIXED_MONTHLY = rr.get("search_fixed_monthly", SEARCH_FIXED_MONTHLY)
    HOSTING_FIXED_MONTHLY = rr.get("hosting_fixed_monthly", HOSTING_FIXED_MONTHLY)

    conv = card.get("conversation_defaults", {})
    DEFAULT_TURNS = conv.get("turns", DEFAULT_TURNS)
    BASE_ESCALATION = conv.get("base_escalation", BASE_ESCALATION)
    COLLISION_ESCALATION = conv.get("collision_escalation", COLLISION_ESCALATION)
    RETRY_TURNS_ON_MISROUTE = conv.get("retry_turns_on_misroute", RETRY_TURNS_ON_MISROUTE)
    return region_used, notes


def copilot_studio_cost(
    volume: int,
    turns: float,
    generative_ratio: float,
    action_ratio: float,
    escalation_rate: float,
    orchestration_mode: str,
) -> Dict[str, Any]:
    """Weighted-credit consumption for Copilot Studio."""
    base_turns = volume * turns

    gen_turns = base_turns * generative_ratio
    classic_turns = base_turns * (1 - generative_ratio)
    action_turns = base_turns * action_ratio

    gen_weight = W_ORCHESTRATION if orchestration_mode == "generative" else W_GENERATIVE

    # Misroute retry burn: extra generative turns before escalation
    misroute_conversations = volume * max(0.0, escalation_rate - BASE_ESCALATION)
    retry_turns = misroute_conversations * RETRY_TURNS_ON_MISROUTE

    units_generative = gen_turns * gen_weight
    units_classic = classic_turns * W_CLASSIC
    units_action = action_turns * W_ACTION
    units_retry = retry_turns * gen_weight

    total_units = units_generative + units_classic + units_action + units_retry
    total_cost = total_units * CREDIT_UNIT_COST

    drivers = [
        {"driver": "Generative answers", "units": round(units_generative),
         "share": _share(units_generative, total_units)},
        {"driver": "Retry burn from misroutes", "units": round(units_retry),
         "share": _share(units_retry, total_units)},
        {"driver": "Agent actions", "units": round(units_action),
         "share": _share(units_action, total_units)},
        {"driver": "Classic responses", "units": round(units_classic),
         "share": _share(units_classic, total_units)},
    ]
    drivers = [d for d in drivers if d["units"] > 0]
    drivers.sort(key=lambda d: d["units"], reverse=True)

    return {
        "monthly_units": round(total_units),
        "monthly_cost": band(total_cost),
        "cost_per_conversation": round(total_cost / volume, 4) if volume else 0.0,
        "assumptions": {
            "turns_per_conversation": turns,
            "generative_ratio": generative_ratio,
            "action_ratio": action_ratio,
            "escalation_rate": round(escalation_rate, 3),
            "orchestration_mode": orchestration_mode,
            "retry_turns_per_misroute": RETRY_TURNS_ON_MISROUTE,
        },
        "top_drivers": drivers[:3],
        "note": "Weighted-unit model. Replace unit cost with verified current pricing.",
    }


def _share(part: float, whole: float) -> str:
    return f"{round(100 * part / whole)}%" if whole else "0%"


def foundry_cost(volume: int, turns: float, context_tokens: int) -> Dict[str, Any]:
    """Token-based variable cost plus standing fixed cost."""
    input_tokens = TOK_SYSTEM + context_tokens + TOK_HISTORY
    output_tokens = TOK_COMPLETION
    total_turns = volume * turns

    in_cost = (total_turns * input_tokens / 1000) * FOUNDRY_INPUT_PER_1K
    out_cost = (total_turns * output_tokens / 1000) * FOUNDRY_OUTPUT_PER_1K
    variable = in_cost + out_cost

    fixed = SEARCH_FIXED_MONTHLY + HOSTING_FIXED_MONTHLY
    supporting = (variable + fixed) * SUPPORTING_UPLIFT
    total = variable + fixed + supporting

    return {
        "monthly_cost": band(total),
        "fixed_monthly": round(fixed + supporting, 2),
        "variable_monthly": round(variable, 2),
        "cost_per_conversation": round(variable / volume, 4) if volume else 0.0,
        "tokens_per_turn": input_tokens + output_tokens,
        "assumptions": {
            "system_tokens": TOK_SYSTEM,
            "retrieved_context_tokens": context_tokens,
            "history_tokens": TOK_HISTORY,
            "completion_tokens": TOK_COMPLETION,
            "turns_per_conversation": turns,
            "supporting_uplift": SUPPORTING_UPLIFT,
        },
        "note": (
            "Azure AI Search is a standing cost independent of volume. At low "
            "volume it can exceed model inference cost entirely."
        ),
    }


def break_even(cs: Dict[str, Any], fd: Dict[str, Any], volume: int) -> Dict[str, Any]:
    cs_per = cs["cost_per_conversation"]
    fd_per = fd["cost_per_conversation"]
    fixed = fd["fixed_monthly"]

    if cs_per <= fd_per:
        return {
            "break_even_conversations": None,
            "interpretation": (
                "Foundry's per-conversation cost is not lower than Copilot Studio's "
                "under these assumptions. Cost does not favour migration at any volume."
            ),
            "cost_is_decisive": False,
        }

    be = fixed / (cs_per - fd_per)
    ratio = volume / be if be else 0

    if 0.5 <= ratio <= 1.5:
        interp = (
            f"Current volume ({volume:,}) is within the indifference band around "
            f"break-even (~{round(be):,}). Cost should not drive this decision — "
            f"decide on capability grounds."
        )
        decisive = False
    elif ratio > 1.5:
        interp = (
            f"Current volume ({volume:,}) is ~{ratio:.1f}x break-even (~{round(be):,}). "
            f"Foundry is cheaper at this volume, but cost alone does not justify "
            f"migration without a capability ceiling (COST-03)."
        )
        decisive = True
    else:
        interp = (
            f"Current volume ({volume:,}) is well below break-even (~{round(be):,}). "
            f"Copilot Studio is cheaper — fixed costs dominate at this scale."
        )
        decisive = True

    return {
        "break_even_conversations": round(be),
        "current_volume": volume,
        "ratio_to_break_even": round(ratio, 2),
        "interpretation": interp,
        "cost_is_decisive": decisive,
    }


def derive_from_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Pull measured inputs from analyze_topics.py output where available."""
    derived: Dict[str, Any] = {}
    g = analysis.get("grounding", {})
    if g.get("generative_ratio") is not None:
        derived["generative_ratio"] = g["generative_ratio"]

    mode = analysis.get("orchestration_mode")
    if mode:
        derived["orchestration_mode"] = mode

    tc = analysis.get("trigger_collisions", {})
    flagged = tc.get("pairs_flagged", 0)
    if flagged >= 3:
        derived["collision_severity"] = "high"
    elif flagged >= 1:
        derived["collision_severity"] = "medium"
    elif tc.get("pairs_near_threshold", 0) > 0:
        derived["collision_severity"] = "low"
    else:
        derived["collision_severity"] = "none"
    return derived


def main() -> int:
    ap = argparse.ArgumentParser(description="Model agent cost and break-even volume.")
    ap.add_argument("--volume", type=int, required=True,
                    help="Conversations per month")
    ap.add_argument("--analysis", help="analysis.json from analyze_topics.py")
    ap.add_argument("--turns", type=float, default=None)
    ap.add_argument("--generative-ratio", type=float, default=None)
    ap.add_argument("--action-ratio", type=float, default=0.15)
    ap.add_argument("--orchestration-mode", default=None,
                    choices=["classic", "generative"])
    ap.add_argument("--collision-severity", default=None,
                    choices=["none", "low", "medium", "high"])
    ap.add_argument("--context-tokens", type=int, default=None)
    ap.add_argument("--region", default=None,
                    help="Azure region for Foundry rates (see rate-card.json)")
    ap.add_argument("--rate-card", default=None,
                    help="Path to rate-card.json (default: references/rate-card.json)")
    ap.add_argument("--out", default="cost.json")
    args = ap.parse_args()

    card = load_rate_card(args.rate_card)
    region_used = args.region or "built-in defaults"
    rate_card_notes: List[str] = []
    if card:
        region_used, rate_card_notes = apply_rate_card(card, args.region)
        rate_card_source = str(Path(args.rate_card) if args.rate_card else DEFAULT_RATE_CARD)
    else:
        rate_card_source = "built-in defaults (rate-card.json not found)"
        rate_card_notes.append("rate-card.json not loaded; using built-in placeholder rates")

    turns = args.turns if args.turns is not None else DEFAULT_TURNS
    context_tokens = args.context_tokens if args.context_tokens is not None else TOK_CONTEXT

    derived: Dict[str, Any] = {}
    if args.analysis:
        p = Path(args.analysis)
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
        derived = derive_from_analysis(json.loads(p.read_text(encoding="utf-8")))

    gen_ratio = args.generative_ratio
    if gen_ratio is None:
        gen_ratio = derived.get("generative_ratio", 0.5)

    mode = args.orchestration_mode or derived.get("orchestration_mode") or "classic"
    severity = args.collision_severity or derived.get("collision_severity", "none")
    escalation = BASE_ESCALATION + COLLISION_ESCALATION.get(severity, 0.0)

    cs = copilot_studio_cost(
        args.volume, turns, gen_ratio, args.action_ratio, escalation, mode
    )
    fd = foundry_cost(args.volume, turns, context_tokens)
    be = break_even(cs, fd, args.volume)

    result = {
        "schema_version": "1.0",
        "rate_card_date": RATE_CARD_DATE,
        "rate_card_source": rate_card_source,
        "region": region_used,
        "sensitivity_band": f"±{int(SENSITIVITY * 100)}%",
        "inputs": {
            "volume_per_month": args.volume,
            "generative_ratio": gen_ratio,
            "generative_ratio_source": (
                "measured from analysis" if args.generative_ratio is None
                and "generative_ratio" in derived else "supplied or default"
            ),
            "orchestration_mode": mode,
            "collision_severity": severity,
            "escalation_rate": round(escalation, 3),
        },
        "copilot_studio": cs,
        "foundry": fd,
        "break_even": be,
        "notes": rate_card_notes,
        "verification_required": (
            "These figures use placeholder unit costs as a modelling scaffold. "
            "Verify against current Microsoft pricing before acting. The ratio "
            "and break-even shape are more reliable than absolute values."
        ),
    }

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Cost model  [rate card {RATE_CARD_DATE}, region {region_used}, ±{int(SENSITIVITY*100)}%]")
    print(f"  volume: {args.volume:,} conversations/month")
    print(f"  generative ratio: {gen_ratio:.0%}  mode: {mode}  "
          f"collisions: {severity}")
    print()
    print(f"  Copilot Studio: ~{cs['monthly_cost']['point']:,.0f} "
          f"({cs['monthly_cost']['low']:,.0f}–{cs['monthly_cost']['high']:,.0f})")
    for d in cs["top_drivers"]:
        print(f"      {d['share']:>4}  {d['driver']}")
    print(f"  Foundry:        ~{fd['monthly_cost']['point']:,.0f} "
          f"({fd['monthly_cost']['low']:,.0f}–{fd['monthly_cost']['high']:,.0f})")
    print(f"      fixed {fd['fixed_monthly']:,.0f} + variable {fd['variable_monthly']:,.0f}")
    print()
    print(f"  {be['interpretation']}")
    print(f"\nWritten to {args.out}")
    print("Verify current pricing before acting on these figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
