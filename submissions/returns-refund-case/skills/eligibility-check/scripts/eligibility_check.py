#!/usr/bin/env python3
"""eligibility_check + fraud_signal - deterministic eligibility (Govern) and fraud-signal
surfacing (rtl.returns-refund-case.v1). Constants mirror references/returns-rules.md.

v1.0.2 changes:
- No order record -> needs_evidence / hold_for_review with clause RET-1.2 cited, regardless of
  value or receipt flag (#1.2, #2.1, #2.2). The engine never emits eligible/refund with a null clause.
- #3.2 return-frequency signal fires when receiptless returns in 90d are STRICTLY greater than the
  configured threshold (rule text: "> config threshold").
- #3.4 wardrobing signal implemented: fashion category, worn flag, request within the last
  wardrobing_last_days of the window.
"""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:eligibility_check"; FRAUD = "engine:fraud_signal"
CONFIDENCE_FLOOR = 0.75  # returns-rules.md #4.1
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True); ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.classified, encoding="utf-8")); cfg = json.load(open(a.config, encoding="utf-8"))
    if p.get("contract_version") != "rtl.returns-refund-case.v1":
        raise SystemExit(f"contract_version mismatch: {p.get('contract_version')!r}")
    rq = p["return_request"]; order = p.get("order") or {}; hist = p.get("customer_history") or {}
    esc = list(p.get("escalations", [])); signals = []
    cat = rq["category"]; win = cfg["windows_days"].get(cat)
    limit = cfg["receiptless_limit"]; freq = cfg["receiptless_frequency_threshold_90d"]
    last_days = cfg.get("wardrobing_last_days", 3)
    missing = []; age = None
    det, clause, detail, rec, conf = "eligible", None, "", "refund", 0.95
    if rq.get("opened") and cat == "software_opened":
        det, clause, detail, rec = "ineligible", "RET-4.2", "opened software is non-returnable (#1.3)", "decline"
    elif win is None:
        det, clause, rec, conf = "needs_evidence", "RET-1.1", "hold_for_review", 0.5
        detail = f"no window configured for category {cat!r} (#1.1) - confirm category with the policy owner"
        missing.append("category window undefined - confirm category")
    elif not order.get("order_date"):
        # #1.2 / #2.2: the window cannot be tested without the order/receipt date; the case is not decided.
        det, clause, rec, conf = "needs_evidence", "RET-1.2", "hold_for_review", 0.6
        missing.append("order/receipt lookup (order date required to test the window, #1.1)")
        if rq.get("has_receipt"):
            detail = "receipt presented but no order record attached - order lookup required before determination (#1.2, #2.2)"
        elif rq["value"] > limit:
            detail = f"no receipt and no order; value {rq['value']} > receiptless limit {limit} - receipt or order lookup required (#1.2)"
        else:
            detail = f"no receipt and no order; value {rq['value']} <= receiptless limit {limit} - at most ID-verified store credit, a human decision (#1.2)"
            missing.append("ID verification if store credit is considered (#1.2)")
    else:
        request_date = date.fromisoformat(rq["requested_on"])
        order_date = date.fromisoformat(order["order_date"])
        age = (request_date - order_date).days
        if age < 0:
            det, clause, rec, conf = "needs_evidence", "RET-1.1", "hold_for_review", 0.5
            detail = "request date precedes order date (#1.1) - correct the case dates before determination"
            missing.append("valid request and order dates (#1.1)")
        elif age > win:
            det, clause, rec = "ineligible", "RET-2.1", "decline"
            detail = f"{age} days since purchase > {win}-day {cat} window (#1.1)"
        else:
            clause, detail = "RET-2.1", f"{age} days <= {win}-day {cat} window (#1.1)"
    if det == "needs_evidence" and not missing: missing.append("unspecified - review")
    # fraud signals (#3.x) - surfaced, never adjudicated
    if order and rq.get("unit_serial") and order.get("sold_serial") and rq["unit_serial"] != order["sold_serial"]:
        signals.append({"signal": "serial_mismatch", "detail": f"unit {rq['unit_serial']} != sold {order['sold_serial']} (#3.1)",
                        "source": FRAUD, "citation": "order line serial vs presented unit"})
    if not rq.get("has_receipt") and hist.get("receiptless_returns_90d", 0) > freq:
        signals.append({"signal": "return_frequency", "detail": f"{hist['receiptless_returns_90d']} receiptless returns in 90d > {freq} (#3.2)",
                        "source": FRAUD, "citation": "customer history extract"})
    if not rq.get("has_receipt") and rq["value"] > limit:
        signals.append({"signal": "high_value_receiptless", "detail": f"value {rq['value']} > {limit} without receipt (#3.3)",
                        "source": FRAUD, "citation": "return request"})
    if cat == "fashion" and rq.get("worn") and age is not None and win is not None and age >= win - last_days + 1 and age <= win:
        signals.append({"signal": "wardrobing_pattern", "detail": f"fashion item flagged worn, returned on day {age} of {win} (last {last_days} days of window, #3.4)",
                        "source": FRAUD, "citation": "return request condition flags vs order date"})
    if signals:
        rec = "hold_for_review"
        esc.append(f"{len(signals)} fraud signal(s) surfaced - asset-protection review; recommendation held (returns-rules.md #4.2); signals are surfaced, not adjudicated")
    if conf < CONFIDENCE_FLOOR:
        rec = "hold_for_review"; esc.append(f"confidence {conf} < {CONFIDENCE_FLOOR} (#4.1)")
    assert clause is not None, "engine invariant: every determination cites a clause (#2.1)"
    p["eligibility"] = {"determination": det, "clause": clause, "detail": detail, "missing_evidence": missing,
                        "recommendation": rec, "confidence": conf, "source": ENGINE,
                        "citation": f"policy clause {clause}; " + cfg["citation"]}
    p["fraud_signals"] = signals; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).extend(["eligibility_check/1.0.2", "fraud_signal/1.0.2"])
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"eligibility_check: {det} ({clause}) rec={rec} signals={len(signals)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
