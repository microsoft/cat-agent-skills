#!/usr/bin/env python3
"""shortage_impact_map - deterministic shortage-to-impact mapping engine
(mfg.supplier-disruption.v1).

Reads the structured disruption intake (the short/delayed part, the revised delivery date, the ERP
supply position and the BOM/where-used open orders) and explodes the shortage to the affected
products, production lines and open orders: per-order quantity and date at risk, a status
(covered / covered_by_incoming / at_risk / line_down / late_shipment), and a rolled-up impact
summary (worst severity + first-impact date). Emits the {impact_map, impact_summary} hop of the
contract and a preliminary next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this and
quotes its output; it never decides the impact itself.

Rules encoded here mirror references/impact-mapping-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:shortage_impact_map"
SEV_ORDER = ["none", "low", "medium", "high", "critical"]


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


def _worse(a, b):
    return a if SEV_ORDER.index(a) >= SEV_ORDER.index(b) else b


def map_impact(payload):
    supply = payload.get("supply", {}) or {}
    on_hand = _num(supply.get("on_hand", 0))
    safety = _num(supply.get("safety_stock", 0))
    revised = _parse_date(payload.get("revised_date"))
    orders = list((payload.get("retrieved", {}) or {}).get("open_orders", []) or [])

    # --- Sec 3: sort by need_by, walk and net against usable on-hand ---
    orders_sorted = sorted(orders, key=lambda o: (o.get("need_by") or "9999-99-99"))
    usable = on_hand
    running = 0.0
    demand_before_revised = 0.0
    items = []
    first_impact = None
    products, impacted_orders, sales_orders = set(), 0, 0
    total_risk = 0.0
    worst = "none"

    for o in orders_sorted:
        demand = _num(o.get("finished_qty", o.get("qty", 0))) * _num(o.get("per_unit", 1) or 1)
        need = _parse_date(o.get("need_by"))
        otype = (o.get("order_type") or "production").lower()
        running += demand
        arrives_in_time = bool(revised and need and need >= revised)
        if not arrives_in_time:
            demand_before_revised += demand
        covered_by_stock = running <= usable

        if covered_by_stock:                                   # #3.1 / #4.1
            status, sev, qty_risk = "covered", "none", 0.0
        elif arrives_in_time:                                  # #3.2 / #4.2
            status, sev, qty_risk = "covered_by_incoming", "low", 0.0
        else:
            qty_risk = max(0.0, min(demand, running - usable))
            if otype == "sales":                               # #3.3 / #4.5
                status, sev = "late_shipment", "critical"
            elif bool(o.get("high_runner")):                   # #3.4 / #4.4
                status, sev = "line_down", "high"
            else:                                              # #3.5 / #4.3
                status, sev = "at_risk", "medium"
            if need and (first_impact is None or need < first_impact):
                first_impact = need

        if status not in ("covered",):
            products.add(o.get("product", ""))
        if status not in ("covered", "covered_by_incoming"):
            impacted_orders += 1
            total_risk += qty_risk
            if otype == "sales":
                sales_orders += 1
        worst = _worse(worst, sev)

        items.append({
            "order_id": o.get("order_id", ""),
            "order_type": otype,
            "product": o.get("product", ""),
            "line": o.get("line", ""),
            "customer": o.get("customer", ""),
            "need_by": o.get("need_by", ""),
            "qty_at_risk": round(qty_risk, 3),
            "status": status,
            "severity": sev,
            "source": ENGINE,
            "citation": "impact-mapping-rules.md #3, #4",
        })

    # --- Sec 2: below-safety-stock flag (on-hand vs demand due before the late PO lands) ---
    below_safety = (usable - demand_before_revised) < safety

    complete = bool(orders) and payload.get("revised_date") and supply.get("on_hand") is not None
    confidence = 0.92 if complete else 0.70

    summary = {
        "worst_severity": worst,
        "first_impact_date": first_impact.date().isoformat() if first_impact else None,
        "affected_products": len([p for p in products if p]),
        "affected_orders": impacted_orders,
        "affected_sales_orders": sales_orders,
        "total_qty_at_risk": round(total_risk, 3),
        "below_safety_stock": bool(below_safety),
        "confidence": confidence,
        "source": ENGINE,
        "citation": "impact-mapping-rules.md #5, #6, #7",
    }
    return items, summary, complete


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True, help="disruption-intake.json (structured contract input)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.intake, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.supplier-disruption.v1", "wrong contract version"

    items, summary, complete = map_impact(payload)
    escalations = list(payload.get("escalations", []))

    # --- governance (impact-mapping-rules.md #7) ---
    if not complete:
        escalations.append(
            "MRP position incomplete (open orders, on-hand or revised date missing/ambiguous); confirm "
            "the netting in the ERP before committing a mitigation (impact-mapping-rules.md #7.2).")
    if summary["below_safety_stock"]:
        escalations.append(
            "Projected balance dips below safety stock: stock-out risk even where no single order is "
            "formally short (impact-mapping-rules.md #2).")

    # --- preliminary next-best action (mitigation_recommend finalizes it) ---
    sev = summary["worst_severity"]
    if sev in ("none", "low"):
        nba = ("Buffer / incoming PO covers demand through the revised date. Align the schedule and "
               "monitor; no expedite required.")
    else:
        nba = (f"Shortage maps to {summary['affected_orders']} order(s) at risk "
               f"(worst {sev}, first impact {summary['first_impact_date']}). Choose a mitigation "
               f"(expedite / substitute / reschedule) in mitigation-recommend.")

    payload["impact_map"] = items
    payload["impact_summary"] = summary
    payload["next_best_action"] = nba
    payload["escalations"] = escalations

    _finish(payload, a.out)
    print(f"shortage_impact_map: worst={sev}, first_impact={summary['first_impact_date']}, "
          f"orders_at_risk={summary['affected_orders']}, qty_at_risk={summary['total_qty_at_risk']} "
          f"-> {a.out}")
    return 0


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "shortage_impact_map/1.0" not in prov["engines"]:
        prov["engines"].append("shortage_impact_map/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
