#!/usr/bin/env python3
"""mitigation_recommend - deterministic mitigation-choice & escalation engine
(mfg.supplier-disruption.v1).

Reads the mapped-impact contract (worst severity, first-impact date, quantity at risk) and the ERP
supply position (substitutes, alternate suppliers, lead time, single-source flag, supplier history),
then chooses the mitigation (expedite / substitute / reschedule), sets the urgency, builds the
cumulative owner-notification list, and raises the escalations. Emits the {mitigation, notifications}
hop of the contract and finalizes next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this and
quotes its output; it never chooses the mitigation or escalates itself.

Rules encoded here mirror references/mitigation-escalation-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:mitigation_recommend"
SEV_ORDER = ["none", "low", "medium", "high", "critical"]

URGENCY = {                                                    # mitigation-escalation-rules.md #2
    "none": "routine", "low": "routine", "medium": "elevated",
    "high": "urgent", "critical": "immediate",
}

# cumulative owner notifications by severity (mitigation-escalation-rules.md #4)
NOTIFY_BY_SEVERITY = {
    "none": [("Buyer", "Owns the PO", "mitigation-escalation-rules.md #4.1")],
    "low": [("Buyer", "Owns the PO", "mitigation-escalation-rules.md #4.1")],
    "medium": [("Production planner", "Schedule adjustment on the affected line", "mitigation-escalation-rules.md #4.2")],
    "high": [("Materials manager", "A line will stop; approve expedite/premium freight", "mitigation-escalation-rules.md #4.3")],
    "critical": [("Plant manager", "A customer order will ship late", "mitigation-escalation-rules.md #4.4")],
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00").split("T")[0])
    except ValueError:
        return None


def _ge(sev, floor):
    return SEV_ORDER.index(sev) >= SEV_ORDER.index(floor)


def recommend(payload):
    summary = payload.get("impact_summary", {}) or {}
    sev = summary.get("worst_severity", "none")
    risk = _num(summary.get("total_qty_at_risk", 0))
    supply = payload.get("supply", {}) or {}
    single_source = bool(supply.get("single_source"))

    subs = supply.get("substitutes", []) or []
    alts = supply.get("alternates", []) or []

    reported = _parse_date(payload.get("reported_at"))
    first_impact = _parse_date(summary.get("first_impact_date"))
    days_to_impact = (first_impact - reported).days if (reported and first_impact) else None

    # best approved substitute that covers the shortfall (#1.2)
    sub = next((s for s in subs if s.get("approved") and _num(s.get("available_qty", 0)) >= risk and risk > 0), None)
    # qualified alternate that can beat the first-impact date (#1.3)
    alt_in_time = next((x for x in alts
                        if x.get("qualified") and days_to_impact is not None
                        and _num(x.get("lead_time_days", 1e9)) <= days_to_impact), None)
    # any alternate to begin qualifying (#1.4)
    alt_any = alts[0] if alts else None

    substitute_part, alternate_supplier = {}, {}

    if not _ge(sev, "medium"):                                 # #1.1
        option = "reschedule"
        rationale = ("Buffer / incoming PO covers demand through the revised date "
                     "(mitigation-escalation-rules.md #1.1).")
        actions = ["Align the affected production/sales orders to the revised delivery date.",
                   "Monitor the PO; ask the supplier to confirm the revised date in writing."]
    elif sub is not None:                                      # #1.2
        option = "substitute"
        substitute_part = {"part_no": sub.get("part_no"), "approved": True,
                           "available_qty": _num(sub.get("available_qty", 0)),
                           "citation": sub.get("citation", "supply.substitutes")}
        rationale = (f"Approved substitute {sub.get('part_no')} covers the shortfall of {risk:g} "
                     f"(mitigation-escalation-rules.md #1.2).")
        actions = [f"Swap in approved substitute {sub.get('part_no')} for the shortfall ({risk:g}).",
                   "Confirm form/fit/function and update the affected work orders.",
                   "Hold the delayed PO balance to the revised date."]
    elif alt_in_time is not None:                              # #1.3
        option = "expedite"
        alternate_supplier = {"supplier": alt_in_time.get("supplier"),
                              "lead_time_days": _num(alt_in_time.get("lead_time_days", 0)),
                              "qualified": True,
                              "citation": alt_in_time.get("citation", "supply.alternates")}
        rationale = (f"Qualified alternate {alt_in_time.get('supplier')} can deliver within "
                     f"{int(_num(alt_in_time.get('lead_time_days',0)))} days, before the first-impact "
                     f"date (mitigation-escalation-rules.md #1.3).")
        actions = [f"Expedite {risk:g} of the part from qualified alternate {alt_in_time.get('supplier')}.",
                   "Confirm the expedite date beats the first-impact date; place the expedite PO.",
                   "Hold or cancel the shortfall on the delayed PO to avoid double supply."]
    else:                                                      # #1.4
        option = "expedite"
        if alt_any is not None:
            alternate_supplier = {"supplier": alt_any.get("supplier"),
                                  "lead_time_days": _num(alt_any.get("lead_time_days", 0)),
                                  "qualified": bool(alt_any.get("qualified")),
                                  "citation": alt_any.get("citation", "supply.alternates")}
        rationale = ("No approved substitute and no qualified alternate can beat the first-impact date; "
                     "expedite the current supplier and begin qualifying an alternate "
                     "(mitigation-escalation-rules.md #1.4).")
        actions = ["Request a partial shipment / premium (air) freight from the current supplier to hit "
                   "the first-impact date, or a firm recovery plan.",
                   "Begin qualifying an alternate supplier (second source).",
                   "Reschedule downstream orders as a fallback if the expedite cannot close the gap."]

    urgency = URGENCY.get(sev, "routine")
    complete = summary.get("confidence", 1.0) >= 0.80
    confidence = 0.9 if complete else 0.7

    mitigation = {
        "option": option, "urgency": urgency, "rationale": rationale, "actions": actions,
        "substitute_part": substitute_part, "alternate_supplier": alternate_supplier,
        "confidence": confidence, "source": ENGINE,
        "citation": "mitigation-escalation-rules.md #1, #2",
    }
    return mitigation, summary, sev


def _build_notifications(sev, summary, chronic):
    notifications, seen = [], set()

    def add(role, reason, cite):
        if role not in seen:
            seen.add(role)
            notifications.append({"role": role, "name": "(owner)", "reason": reason, "citation": cite})

    idx = SEV_ORDER.index(sev)
    for lvl in SEV_ORDER[:idx + 1]:
        for role, reason, cite in NOTIFY_BY_SEVERITY.get(lvl, []):
            add(role, reason, cite)
    if _num(summary.get("affected_sales_orders", 0)) > 0:      # #4.5
        add("Customer service / account manager", "A customer sales order is at risk of a late shipment",
            "mitigation-escalation-rules.md #4.5")
    if chronic:                                                # #4.6
        add("Supplier quality (SQM)", "Chronic late-delivery pattern: supplier performance review",
            "mitigation-escalation-rules.md #4.6")
    return notifications


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impact", required=True, help="output of shortage_impact_map")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.impact, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.supplier-disruption.v1", "wrong contract version"

    mitigation, summary, sev = recommend(payload)
    supply = payload.get("supply", {}) or {}
    single_source = bool(supply.get("single_source"))
    chronic = bool((payload.get("history", {}) or {}).get("chronic_pattern", False))
    escalations = list(payload.get("escalations", []))

    # --- escalation matrix (mitigation-escalation-rules.md #3) ---
    if sev == "medium":
        escalations.append("Production planner owns a schedule adjustment; buyer chases the PO "
                           "(mitigation-escalation-rules.md #3.1).")
    if sev == "high":
        escalations.append("Line-stopping shortage: escalate to the materials manager; approve "
                           "expedite / premium freight against downtime cost (mitigation-escalation-rules.md #3.2).")
    if sev == "critical":
        escalations.append("Customer order at risk of a late shipment: escalate to the materials "
                           "manager + plant manager and notify customer service/account before the "
                           "customer finds out (mitigation-escalation-rules.md #3.3).")
    if single_source and _ge_sev(sev, "high"):
        escalations.append("Single-source critical part with no buffer: open a second-source "
                           "qualification (mitigation-escalation-rules.md #3.4).")
    if chronic:
        escalations.append("Chronic late-delivery pattern from this supplier: open a supplier-"
                           "performance / SQM review; do not treat this as a one-off slip "
                           "(mitigation-escalation-rules.md #3.5).")
    if summary.get("confidence", 1.0) < 0.80:
        escalations.append("Impact confidence below 0.80: confirm the MRP position (on-hand, open "
                           "orders, revised date) before committing the mitigation "
                           "(mitigation-escalation-rules.md #3.7).")

    notifications = _build_notifications(sev, summary, chronic)

    # --- finalized next-best action (mitigation-escalation-rules.md #5) ---
    fi = summary.get("first_impact_date")
    risk = _num(summary.get("total_qty_at_risk", 0))
    if mitigation["option"] == "reschedule":
        nba = ("Buffer / incoming PO covers demand through the revised date. Align the schedule and "
               "monitor; no expedite required.")
    elif mitigation["option"] == "substitute":
        sp = mitigation["substitute_part"].get("part_no", "the substitute")
        nba = (f"Swap in approved substitute {sp} for the shortfall ({risk:g}); confirm form/fit/"
               f"function and update the work orders. Hold the delayed PO to the revised date.")
    else:
        who = (mitigation["alternate_supplier"].get("supplier") or "the current supplier")
        nba = (f"Expedite {risk:g} of the part ({who}) to hit the first-impact date ({fi}). "
               f"A customer order is at risk: notify account management and escalate per the matrix; "
               f"reschedule downstream orders as a fallback." if sev == "critical" else
               f"Expedite {risk:g} of the part ({who}) to hit the first-impact date ({fi}); escalate "
               f"per the matrix and reschedule downstream orders as a fallback.")

    payload["mitigation"] = mitigation
    payload["notifications"] = notifications
    payload["escalations"] = escalations
    payload["next_best_action"] = nba

    _finish(payload, a.out)
    print(f"mitigation_recommend: option={mitigation['option']}, urgency={mitigation['urgency']}, "
          f"notifications={len(notifications)}, escalations={len(escalations)} -> {a.out}")
    return 0


def _ge_sev(sev, floor):
    return SEV_ORDER.index(sev) >= SEV_ORDER.index(floor)


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "mitigation_recommend/1.0" not in prov["engines"]:
        prov["engines"].append("mitigation_recommend/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
