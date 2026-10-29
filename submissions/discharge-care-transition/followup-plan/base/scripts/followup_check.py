#!/usr/bin/env python3
"""followup_check - deterministic completeness check for the follow-up checklist and pending results
(hls.discharge-care-transition.v1). Required fields, allowed owners and the follow-up window all come from
config/followup-rules.json. Mirrors base/references/discharge-rules.md #10-#11."""
import argparse, json, sys
from datetime import date, datetime, timezone

CONTRACT = "hls.discharge-care-transition.v1"
ENGINE = "engine:followup_check"
RULE_OWNED = "discharge-rules.md #10"
RULE_WINDOW = "discharge-rules.md #11"


def iso(d):
    try:
        return date.fromisoformat(str(d))
    except (TypeError, ValueError):
        return None


def check(rec, label, fields, cfg, gaps, discharge):
    subject = str(rec.get("item") or rec.get("result") or label)
    for f in fields:
        if not rec.get(f):
            gaps.append({"subject": subject, "type": "missing_field",
                         "detail": f"{label} '{subject}' has no {f}", "citation": RULE_OWNED})
    owner = rec.get("owner")
    if owner and owner not in cfg["allowed_owners"]:
        gaps.append({"subject": subject, "type": "owner_not_allowed",
                     "detail": f"{label} '{subject}' owner '{owner}' is not one of {cfg['allowed_owners']}",
                     "citation": RULE_OWNED})
    due, dc = iso(rec.get("due_date")), iso(discharge)
    if rec.get("due_date") and due is None:           # 1.0.3: an unreadable date never passes the window check
        gaps.append({"subject": subject, "type": "due_date_unverifiable",
                     "detail": f"{label} '{subject}' due_date {rec.get('due_date')!r} is not an ISO date "
                               f"(YYYY-MM-DD), so the follow-up window cannot be verified", "citation": RULE_WINDOW})
    if due and dc:
        days = (due - dc).days
        if days < 0 or days > cfg["max_days_to_first_followup"]:
            gaps.append({"subject": subject, "type": "due_date_out_of_window",
                         "detail": f"{label} '{subject}' due {due} is {days} days from discharge {dc}; window is "
                                   f"0-{cfg['max_days_to_first_followup']} days", "citation": RULE_WINDOW})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8"))
    version = p.get("contract_version") if isinstance(p, dict) else None
    if version != CONTRACT:                           # 1.0.3: readable input error instead of a bare traceback
        found = "is missing" if version is None else f"is {version!r}"
        print(f"followup_check: input error - contract_version {found}; expected {CONTRACT!r}. "
              f"No followup_report was written; correct the payload and re-run.", file=sys.stderr)
        return 2
    cfg = json.load(open(a.config, encoding="utf-8"))
    esc, gaps = list(p.get("escalations", [])), []
    discharge = p.get("encounter", {}).get("discharge_date")

    items = p.get("followup_checklist", [])
    pending = p.get("pending_results", [])
    for rec in items:
        check(rec, "follow-up item", cfg["required_item_fields"], cfg, gaps, discharge)
    for rec in pending:
        check(rec, "pending result", cfg["required_pending_result_fields"], cfg, gaps, discharge)
    # 1.0.1: every pending result and referral order must be carried onto the checklist (rule #10) -
    # matched on its documenting source_note, so an order can never silently fall off the action list.
    tracked = {str(r.get("source_note")) for r in items if r.get("source_note")}
    for label, recs in (("pending result", pending), ("referral order", p.get("referral_orders", []))):
        for rec in recs:
            if rec.get("source_note") and str(rec["source_note"]) not in tracked:
                subject = str(rec.get("item") or rec.get("result") or label)
                gaps.append({"subject": subject, "type": "untracked_order",
                             "detail": f"{label} '{subject}' ({rec['source_note']}) has no matching follow-up "
                                       f"checklist item", "citation": RULE_OWNED})
    if (items or pending) and iso(discharge) is None:   # 1.0.3: no usable discharge date - window unverifiable
        gaps.append({"subject": "encounter.discharge_date", "type": "due_date_unverifiable",
                     "detail": f"encounter discharge_date {discharge!r} is missing or not an ISO date (YYYY-MM-DD), "
                               f"so no follow-up due date can be checked against the window", "citation": RULE_WINDOW})
    if not items:
        gaps.append({"subject": "followup_checklist", "type": "missing_field",
                     "detail": "no follow-up item was produced for this discharge", "citation": RULE_OWNED})

    gaps.sort(key=lambda g: (g["subject"], g["type"], g["detail"]))
    complete = len(gaps) == 0
    p["followup_report"] = {"items_checked": len(items), "pending_results_checked": len(pending),
                            "referral_orders_checked": len(p.get("referral_orders", [])),
                            "gaps": gaps, "complete": complete,
                            "citation": RULE_OWNED, "config": "config/followup-rules.json", "source": ENGINE}
    for g in gaps:
        esc.append(f"follow-up plan gap: {g['detail']} ({g['citation']}) - route to the care-coordination team "
                   f"rather than discharging the item unowned")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("followup_check/1.2")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"followup_check: items={len(items)} pending={len(pending)} gaps={len(gaps)} complete={complete} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
