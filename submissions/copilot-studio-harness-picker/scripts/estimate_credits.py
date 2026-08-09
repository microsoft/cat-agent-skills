#!/usr/bin/env python3
"""Estimate gross Copilot Credits from a dated, inspectable rate snapshot."""

from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RATES = SCRIPT_DIR.parent / "assets" / "credit-rates-2026-08.json"
COMPLEXITIES = ("light", "medium", "heavy")
GITHUB_SECTIONS = (
    ("authoring_sessions", "AI-assisted authoring", "authoring"),
    ("preview_evaluation_tasks", "Preview and evaluation", "task"),
    ("runtime_tasks", "Production runtime", "task"),
)


class InputError(ValueError):
    """Raised when workload input cannot be estimated safely."""


def decimal_value(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise InputError(f"{field} must be a non-negative number, not a boolean")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InputError(f"{field} must be a non-negative number") from exc
    if not number.is_finite() or number < 0:
        raise InputError(f"{field} must be a finite, non-negative number")
    return number


def load_json(path: str) -> dict[str, Any]:
    if path == "-":
        payload = json.load(sys.stdin)
    else:
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    return payload


def load_rates(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        rates = json.load(handle)
    if not isinstance(rates, dict):
        raise InputError("rates file must contain a JSON object")
    return rates


def money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.01')):,.2f}"


def number(value: Decimal | None) -> str:
    if value is None:
        return "open-ended"
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return f"{int(normalized):,}"
    return f"{normalized:,.4f}".rstrip("0").rstrip(".")


def required_units(credits: Decimal, unit_credits: Decimal, lower_exclusive: bool) -> int:
    if credits == 0:
        return 0
    quotient = credits / unit_credits
    if lower_exclusive and quotient == quotient.to_integral():
        return int(quotient) + 1
    return math.ceil(quotient)


def priced_p3_tier(raw_tier: dict[str, Any], payg_rate: Decimal) -> dict[str, Any]:
    credits = decimal_value(raw_tier["credits"], "P3 tier credits")
    discount = decimal_value(raw_tier["discount_percent"], "P3 tier discount")
    if discount > 100:
        raise InputError("P3 tier discount cannot exceed 100 percent")
    return {
        "credits": credits,
        "discount_percent": discount,
        "list_price": credits * payg_rate * (Decimal("1") - discount / Decimal("100")),
    }


def select_p3_tier(
    credits: Decimal,
    lower_exclusive: bool,
    tiers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if credits == 0:
        return None
    for tier in tiers:
        capacity = tier["credits"]
        if capacity > credits or (not lower_exclusive and capacity == credits):
            return tier
    return None


def price_scenarios(
    low: Decimal,
    high: Decimal | None,
    low_exclusive: bool,
    period: str,
    p3_annualization_factor: Decimal | None,
    rates: dict[str, Any],
) -> dict[str, Any]:
    pricing = rates["pricing"]
    payg_rate = decimal_value(pricing["pay_as_you_go_per_credit"], "PAYG rate")
    pack = pricing["capacity_pack"]
    pack_credits = decimal_value(pack["credits_per_month"], "pack credits")
    if pack_credits == 0:
        raise InputError("pack credits must be greater than zero")
    pack_price = decimal_value(pack["list_price_per_month"], "pack price")
    capacity_applicable = period.strip().lower() in {"month", "monthly", "one month", "1 month"}
    low_packs = required_units(low, pack_credits, low_exclusive) if capacity_applicable else None
    result: dict[str, Any] = {
        "pay_as_you_go": {
            "low": low * payg_rate,
            "high": None if high is None else high * payg_rate,
            "low_exclusive": low_exclusive,
            "rate_per_credit": payg_rate,
        },
        "capacity_pack": {
            "applicable": capacity_applicable,
            "low_packs": low_packs,
            "low_cost": None if low_packs is None else Decimal(low_packs) * pack_price,
            "high_packs": None,
            "high_cost": None,
            "credits_per_pack": pack_credits,
            "price_per_pack": pack_price,
            "billing_note": str(pack["billing_note"]),
        },
    }
    if capacity_applicable and high is not None:
        high_packs = required_units(high, pack_credits, False)
        result["capacity_pack"]["high_packs"] = high_packs
        result["capacity_pack"]["high_cost"] = Decimal(high_packs) * pack_price

    p3 = pricing["pre_purchase_plan"]
    raw_tiers = p3.get("tiers", [])
    if not isinstance(raw_tiers, list) or not raw_tiers:
        raise InputError("P3 tiers must be a non-empty list")
    tiers = sorted((priced_p3_tier(tier, payg_rate) for tier in raw_tiers), key=lambda tier: tier["credits"])
    p3_result: dict[str, Any] = {
        "annualization_factor": p3_annualization_factor,
        "annualized_low_credits": None,
        "annualized_high_credits": None,
        "low_exclusive": low_exclusive,
        "low_tier": None,
        "high_tier": None,
        "largest_listed_tier_credits": tiers[-1]["credits"],
        "term_months": p3["term_months"],
        "billing_note": str(p3["billing_note"]),
    }
    if p3_annualization_factor is not None:
        annualized_low = low * p3_annualization_factor
        annualized_high = None if high is None else high * p3_annualization_factor
        p3_result["annualized_low_credits"] = annualized_low
        p3_result["annualized_high_credits"] = annualized_high
        p3_result["low_tier"] = select_p3_tier(annualized_low, low_exclusive, tiers)
        if annualized_high is not None:
            p3_result["high_tier"] = select_p3_tier(annualized_high, False, tiers)
    result["pre_purchase_plan"] = p3_result
    return result


def estimate_standard(workload: dict[str, Any], rates: dict[str, Any]) -> dict[str, Any]:
    allowed = {"harness", "period", "activities", "p3_annualization_factor", "notes"}
    extra = sorted(set(workload) - allowed)
    if extra:
        raise InputError("unknown top-level fields for standard or copilot-chat: " + ", ".join(extra))
    activities = workload.get("activities", {})
    if not isinstance(activities, dict):
        raise InputError("activities must be a JSON object")
    unknown = sorted(set(activities) - set(rates["standard"]))
    if unknown:
        raise InputError("unknown activities: " + ", ".join(unknown))

    rows: list[dict[str, Any]] = []
    total = Decimal("0")
    for key, value in activities.items():
        volume = decimal_value(value, f"activities.{key}")
        rate = rates["standard"][key]
        credits = decimal_value(rate["credits"], f"rate.{key}.credits")
        per = decimal_value(rate["per"], f"rate.{key}.per")
        if per == 0:
            raise InputError(f"rate.{key}.per must be greater than zero")
        subtotal = volume * credits / per
        total += subtotal
        rows.append(
            {
                "key": key,
                "label": rate["label"],
                "volume": volume,
                "rate_credits": credits,
                "rate_per": per,
                "rate_unit": rate["unit"],
                "credits": subtotal,
            }
        )

    return {
        "kind": "fixed",
        "rows": rows,
        "low_credits": total,
        "high_credits": total,
        "low_exclusive": False,
        "open_upper": False,
        "assumptions": [],
    }


def heavy_upper(
    workload: dict[str, Any],
    rate_kind: str,
    minimum: Decimal,
    lower_inclusive: bool,
) -> Decimal | None:
    bounds = workload.get("heavy_upper_bounds", {})
    if bounds is None:
        bounds = {}
    if not isinstance(bounds, dict):
        raise InputError("heavy_upper_bounds must be a JSON object")
    key = "authoring_credits_per_session" if rate_kind == "authoring" else "task_credits_per_task"
    if key not in bounds:
        return None
    upper = decimal_value(bounds[key], f"heavy_upper_bounds.{key}")
    if upper < minimum or (not lower_inclusive and upper == minimum):
        relation = "below" if lower_inclusive else "at or below"
        raise InputError(f"heavy_upper_bounds.{key} cannot be {relation} the documented lower bound {number(minimum)}")
    return upper


def estimate_github(workload: dict[str, Any], rates: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    assumptions: list[str] = []
    low_total = Decimal("0")
    high_total = Decimal("0")
    open_upper = False
    low_exclusive = False

    allowed = {"harness", "period", "authoring_sessions", "preview_evaluation_tasks", "runtime_tasks", "heavy_upper_bounds", "p3_annualization_factor", "notes"}
    extra = sorted(set(workload) - allowed)
    if extra:
        raise InputError("unknown top-level fields for github-copilot: " + ", ".join(extra))

    for field, label, rate_kind in GITHUB_SECTIONS:
        distribution = workload.get(field, {})
        if not isinstance(distribution, dict):
            raise InputError(f"{field} must be a JSON object")
        invalid_complexities = sorted(set(distribution) - set(COMPLEXITIES))
        if invalid_complexities:
            raise InputError(f"unknown complexities in {field}: " + ", ".join(invalid_complexities))

        for complexity in COMPLEXITIES:
            volume = decimal_value(distribution.get(complexity, 0), f"{field}.{complexity}")
            if volume == 0:
                continue
            rate = rates["github_copilot"][rate_kind][complexity]
            minimum = decimal_value(rate["minimum"], f"rate.{rate_kind}.{complexity}.minimum")
            lower_inclusive = rate.get("lower_inclusive", True)
            if not isinstance(lower_inclusive, bool):
                raise InputError(f"rate.{rate_kind}.{complexity}.lower_inclusive must be a boolean")
            documented_maximum = rate["maximum"]
            maximum = None if documented_maximum is None else decimal_value(documented_maximum, f"rate.{rate_kind}.{complexity}.maximum")
            assumed_upper = False
            if maximum is None:
                maximum = heavy_upper(workload, rate_kind, minimum, lower_inclusive)
                assumed_upper = maximum is not None
                if assumed_upper:
                    assumption = f"{label} heavy upper bound: {number(maximum)} credits per {rate['unit']}"
                    if assumption not in assumptions:
                        assumptions.append(assumption)

            low = volume * minimum
            high = None if maximum is None else volume * maximum
            low_total += low
            if not lower_inclusive:
                low_exclusive = True
            if high is None:
                open_upper = True
            else:
                high_total += high
            rows.append(
                {
                    "field": field,
                    "label": label,
                    "complexity": complexity,
                    "volume": volume,
                    "minimum_rate": minimum,
                    "lower_inclusive": lower_inclusive,
                    "maximum_rate": maximum,
                    "assumed_upper": assumed_upper,
                    "unit": rate["unit"],
                    "guide": rate["guide"],
                    "low_credits": low,
                    "high_credits": high,
                }
            )

    return {
        "kind": "range",
        "rows": rows,
        "low_credits": low_total,
        "high_credits": None if open_upper else high_total,
        "low_exclusive": low_exclusive,
        "open_upper": open_upper,
        "assumptions": assumptions,
    }


def serializable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral() else float(value)
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serializable(item) for item in value]
    return value


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Copilot Credit planning estimate",
        "",
        f"- Harness: `{result['harness']}`",
        f"- Period: {result['period']}",
        f"- Rate snapshot checked: {result['rates_as_of']}",
        "- Scope: gross credits before licensing inclusions, tenant entitlements, or agreement adjustments",
        "",
        "## Calculation",
        "",
    ]
    estimate = result["estimate"]
    if estimate["kind"] == "fixed":
        lines.extend(["| Activity | Volume | Documented rate | Gross credits |", "|---|---:|---:|---:|"])
        for row in estimate["rows"]:
            rate = f"{number(row['rate_credits'])} / {number(row['rate_per'])} {row['rate_unit']}"
            lines.append(f"| {row['label']} | {number(row['volume'])} | {rate} | {number(row['credits'])} |")
    else:
        lines.extend(["| Stage | Complexity | Volume | Planning rate | Gross credit range |", "|---|---|---:|---:|---:|"])
        for row in estimate["rows"]:
            maximum = row["maximum_rate"]
            suffix = " (assumed upper)" if row["assumed_upper"] else ""
            rate_prefix = "" if row["lower_inclusive"] else ">"
            credit_prefix = "" if row["lower_inclusive"] else ">"
            if maximum is not None:
                separator = "–" if row["lower_inclusive"] else " to "
                rate_range = f"{rate_prefix}{number(row['minimum_rate'])}{separator}{number(maximum)}{suffix}"
                credit_range = f"{credit_prefix}{number(row['low_credits'])}{separator}{number(row['high_credits'])}"
            else:
                rate_range = f"{rate_prefix}{number(row['minimum_rate'])}" if rate_prefix else f"{number(row['minimum_rate'])}+"
                credit_range = f"{credit_prefix}{number(row['low_credits'])}" if credit_prefix else f"{number(row['low_credits'])}+"
            lines.append(f"| {row['label']} | {row['complexity'].title()} | {number(row['volume'])} | {rate_range} / {row['unit']} | {credit_range} |")

    high_text = number(estimate["high_credits"])
    if estimate["kind"] == "fixed":
        total_text = f"**Gross credits: {number(estimate['low_credits'])}**"
    elif estimate["high_credits"] is not None:
        lower = f">{number(estimate['low_credits'])}" if estimate["low_exclusive"] else number(estimate["low_credits"])
        total_text = f"**Gross credits: {lower} to {high_text}**"
    else:
        relation = "more than" if estimate["low_exclusive"] else "at least"
        total_text = f"**Gross credits: {relation} {number(estimate['low_credits'])}; upper bound is open**"
    lines.extend(
        [
            "",
            total_text,
            "",
            "## Counterfactual gross list-price scenarios",
            "",
            "These figures assume every gross credit is billable. They are not an expected invoice until licensing inclusions, entitlements, and agreement terms are applied.",
            "",
        ]
    )
    prices = result["prices"]
    payg = prices["pay_as_you_go"]
    payg_relation = "more than" if payg["low_exclusive"] else "at least"
    if payg["high"] is None:
        lines.append(f"- Pay as you go: {payg_relation} {money(payg['low'])}; upper cost is open at {money(payg['rate_per_credit'])} per credit.")
    else:
        low_text = f">{money(payg['low'])}" if payg["low_exclusive"] else money(payg["low"])
        lines.append(f"- Pay as you go: {low_text} to {money(payg['high'])} at {money(payg['rate_per_credit'])} per credit.")
    pack = prices["capacity_pack"]
    if not pack["applicable"]:
        lines.append("- Capacity packs: not sized because the workload period is not explicitly one month; normalize the workload to a representative month first.")
    elif pack["high_packs"] is None:
        lines.append(f"- Capacity packs: at least {pack['low_packs']} pack(s), or {money(pack['low_cost'])} per month at list price; the upper requirement is open.")
    else:
        lines.append(f"- Capacity packs: {pack['low_packs']}–{pack['high_packs']} pack(s), or {money(pack['low_cost'])}–{money(pack['high_cost'])} per month at list price.")
    lines.append(f"- Capacity note: {pack['billing_note']}")
    p3 = prices["pre_purchase_plan"]
    if p3["annualization_factor"] is None:
        lines.append("- Copilot Credit P3: not sized. Supply `p3_annualization_factor` only when the workload can credibly be annualized from stable pilot telemetry.")
    else:
        annual_low_prefix = ">" if p3["low_exclusive"] else ""
        annual_low = f"{annual_low_prefix}{number(p3['annualized_low_credits'])}"
        annual_high = p3["annualized_high_credits"]
        if annual_high is None:
            relation = "more than" if p3["low_exclusive"] else "at least"
            demand = f"{relation} {number(p3['annualized_low_credits'])}, with an open upper bound"
        else:
            demand = f"{annual_low} to {number(annual_high)}"
        low_tier = p3["low_tier"]
        high_tier = p3["high_tier"]
        if p3["annualized_low_credits"] == 0 and annual_high == 0:
            tier_text = "no listed tier because the estimated demand is zero"
        elif low_tier is None:
            tier_text = f"above the largest listed single tier of {number(p3['largest_listed_tier_credits'])} credits; obtain commercial sizing"
        elif annual_high is None:
            tier_text = f"at least the {number(low_tier['credits'])}-credit tier at {number(low_tier['discount_percent'])}% published discount ({money(low_tier['list_price'])} upfront list scenario); upper tier is unresolved"
        elif high_tier is None:
            tier_text = f"from the {number(low_tier['credits'])}-credit tier to above the largest listed single tier; obtain commercial sizing"
        elif low_tier["credits"] == high_tier["credits"]:
            tier_text = f"the {number(low_tier['credits'])}-credit tier at {number(low_tier['discount_percent'])}% published discount ({money(low_tier['list_price'])} upfront list scenario)"
        else:
            tier_text = f"the {number(low_tier['credits'])}- to {number(high_tier['credits'])}-credit tiers ({number(low_tier['discount_percent'])}%–{number(high_tier['discount_percent'])}% published discount)"
        lines.append(f"- Copilot Credit P3: annualized demand {demand}; sizing points to {tier_text}.")
    lines.append(f"- P3 note: {p3['billing_note']}")
    lines.append("- Procurement comparison: arithmetic only, not a commitment recommendation; validate stable pilot telemetry first.")

    lines.extend(["", "## Assumptions and exclusions", ""])
    if estimate["kind"] == "range":
        if estimate["assumptions"]:
            for assumption in estimate["assumptions"]:
                lines.append(f"- Planning assumption: {assumption}. This is not a Microsoft-documented cap.")
        else:
            lines.append("- No user-supplied heavy-case upper bound was applied.")
    else:
        lines.append("- Fixed activity-rate arithmetic was used; the activity volumes and their meter classification come from the input.")
    if prices["pre_purchase_plan"]["annualization_factor"] is not None:
        lines.append(f"- Planning assumption: the input period repeats {number(prices['pre_purchase_plan']['annualization_factor'])} time(s) across the P3 annual term.")
    lines.extend(
        [
            "- The workload volumes and complexity classifications come from the input, not Microsoft.",
            "- `agent_flow_actions` means Copilot Studio agent-flow actions, not Power Automate cloud-flow actions.",
            "- The estimate does not apply Microsoft 365 licensing inclusions, fair-use treatment, tenant entitlements, negotiated pricing, taxes, or currency conversion. P3 output is only a gross list-price sizing scenario.",
            "- It excludes Microsoft 365 seats, Azure resources, connectors, telephony, third-party systems, custom model hosting, implementation, and support.",
            "- Verify current rates and use metered pilot data before a financial commitment.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_result(workload: dict[str, Any], rates: dict[str, Any]) -> dict[str, Any]:
    harness = str(workload.get("harness", "")).strip().lower()
    if harness not in {"standard", "copilot-chat", "github-copilot"}:
        raise InputError("harness must be standard, copilot-chat, or github-copilot")
    period = str(workload.get("period", "month")).strip() or "month"
    raw_factor = workload.get("p3_annualization_factor")
    p3_annualization_factor = None if raw_factor is None else decimal_value(raw_factor, "p3_annualization_factor")
    if p3_annualization_factor is not None and p3_annualization_factor == 0:
        raise InputError("p3_annualization_factor must be greater than zero")
    estimate = estimate_github(workload, rates) if harness == "github-copilot" else estimate_standard(workload, rates)
    prices = price_scenarios(
        estimate["low_credits"],
        estimate["high_credits"],
        estimate["low_exclusive"],
        period,
        p3_annualization_factor,
        rates,
    )
    return {
        "harness": harness,
        "period": period,
        "rates_as_of": rates["as_of"],
        "currency": rates["currency"],
        "estimate": estimate,
        "prices": prices,
        "disclaimer": rates["disclaimer"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Workload JSON file, or - for standard input")
    parser.add_argument("--rates", type=Path, default=DEFAULT_RATES, help="Rate snapshot JSON")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        workload = load_json(args.input)
        rates = load_rates(args.rates)
        try:
            result = build_result(workload, rates)
        except KeyError as exc:
            raise InputError(f"rates file is missing required field: {exc.args[0]}") from exc
        except (AttributeError, TypeError) as exc:
            raise InputError(f"rates file has an invalid structure: {exc}") from exc
    except (InputError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(serializable(result), indent=2))
    else:
        print(render_markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
