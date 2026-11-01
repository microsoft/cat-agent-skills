#!/usr/bin/env python3
"""eligibility_check + fraud_signal - deterministic eligibility (Govern) and fraud-signal
surfacing (rtl.returns-refund-case.v1). Constants mirror references/returns-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:eligibility_check"; FRAUD = "engine:fraud_signal"
CONFIDENCE_FLOOR = 0.75  # returns-rules.md #4.1
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True); ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.classified, encoding="utf-8")); cfg = json.load(open(a.config, encoding="utf-8"))
    assert p["contract_version"] == "rtl.returns-refund-case.v1"
    rq = p["return_request"]; order = p.get("order", {}); hist = p.get("customer_history", {})
    esc = list(p.get("escalations", [])); signals = []
    cat = rq["category"]; win = cfg["windows_days"].get(cat)
    missing = []
    det, clause, detail, rec, conf = "eligible", None, "", "refund", 0.95
    if rq.get("opened") and cat == "software_opened":
        det, clause, detail, rec = "ineligible", "RET-4.2", "opened software is non-returnable (#1.3)", "decline"
    elif win is None:
        det, rec, conf = "needs_evidence", "hold_for_review", 0.5; missing.append("category window undefined - confirm category")
    else:
        if not order:
            missing.append("order/receipt lookup")
        else:
            age = (date.fromisoformat(rq["requested_on"]) - date.fromisoformat(order["order_date"])).days
            if age > win:
                det, clause, rec = "ineligible", "RET-2.1", "decline"
                detail = f"{age} days since purchase > {win}-day {cat} window (#1.1)"
            else:
                clause, detail = "RET-2.1", f"{age} days <= {win}-day {cat} window (#1.1)"
        if not rq.get("has_receipt") and not order:
            if rq["value"] > cfg["receiptless_limit"]:
                det = "needs_evidence"; rec = "hold_for_review"
                missing.append(f"receipt or order lookup (value {rq['value']} > receiptless limit {cfg['receiptless_limit']}, #1.2)")
    if det == "needs_evidence" and not missing: missing.append("unspecified - review")
    # fraud signals (#3.x) - surfaced, never adjudicated
    if order and rq.get("unit_serial") and order.get("sold_serial") and rq["unit_serial"] != order["sold_serial"]:
        signals.append({"signal": "serial_mismatch", "detail": f"unit {rq['unit_serial']} != sold {order['sold_serial']} (#3.1)",
                        "source": FRAUD, "citation": "order line serial vs presented unit"})
    if hist.get("receiptless_returns_90d", 0) > cfg["receiptless_frequency_threshold_90d"] - 1 and not rq.get("has_receipt"):
        signals.append({"signal": "return_frequency", "detail": f"{hist['receiptless_returns_90d']} receiptless returns in 90d >= {cfg['receiptless_frequency_threshold_90d']} (#3.2)",
                        "source": FRAUD, "citation": "customer history extract"})
    if not rq.get("has_receipt") and rq["value"] > cfg["receiptless_limit"]:
        signals.append({"signal": "high_value_receiptless", "detail": f"value {rq['value']} > {cfg['receiptless_limit']} without receipt (#3.3)",
                        "source": FRAUD, "citation": "return request"})
    if signals:
        rec = "hold_for_review"
        esc.append(f"{len(signals)} fraud signal(s) surfaced - asset-protection review; recommendation held (returns-rules.md #4.2); signals are surfaced, not adjudicated")
    if conf < CONFIDENCE_FLOOR: rec = "hold_for_review"; esc.append(f"confidence {conf} < {CONFIDENCE_FLOOR} (#4.1)")
    p["eligibility"] = {"determination": det, "clause": clause, "detail": detail, "missing_evidence": missing,
                        "recommendation": rec, "confidence": conf, "source": ENGINE,
                        "citation": (f"policy clause {clause}; " if clause else "") + cfg["citation"]}
    p["fraud_signals"] = signals; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).extend(["eligibility_check/1.0", "fraud_signal/1.0"])
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"eligibility_check: {det} ({clause}) rec={rec} signals={len(signals)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
