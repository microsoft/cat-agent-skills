#!/usr/bin/env python3
"""med_reconcile - deterministic medication reconciliation diff engine
(hls.discharge-care-transition.v1). Constants mirror base/references/discharge-rules.md line for line."""
import argparse, json, sys
from datetime import datetime, timezone

CONTRACT = "hls.discharge-care-transition.v1"
ENGINE = "engine:med_reconcile"
RULE = {                                              # discrepancy type -> numbered rule
    "unresolved_stop_reappeared": "discharge-rules.md #1",
    "missing_from_discharge": "discharge-rules.md #4",
    "stopped_med_undocumented": "discharge-rules.md #5",
    "unordered_addition": "discharge-rules.md #6",
    "dose_mismatch": "discharge-rules.md #7",
    "change_to_absent_med": "discharge-rules.md #8",
    "change_provenance_missing": "discharge-rules.md #9",
}
STOP_STATUSES = {"stopped", "discontinued", "held"}   # rule #5
KNOWN_ACTIONS = {"start", "stop", "change"}          # contract enum for inpatient_change.action
CITED = ("source_note", "documented_date")            # rule #9


def cite(rec):
    return {k: rec.get(k) for k in CITED}


def flag(out, drug, dtype, detail, rec=None):
    d = {"drug": drug, "type": dtype, "detail": detail, "citation": RULE[dtype]}
    d.update(cite(rec or {}))
    out.append(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8"))
    version = p.get("contract_version") if isinstance(p, dict) else None
    if version != CONTRACT:                           # 1.0.3: readable input error instead of a bare traceback
        found = "is missing" if version is None else f"is {version!r}"
        print(f"med_reconcile: input error - contract_version {found}; expected {CONTRACT!r}. "
              f"No reconciliation_report was written; correct the payload and re-run.", file=sys.stderr)
        return 2
    esc, disc, unrecognised = list(p.get("escalations", [])), [], []

    admission = {m["drug"]: dict(m) for m in p.get("admission_meds", [])}
    expected, stopped = dict(admission), {}
    for c in p.get("inpatient_changes", []):
        drug = c["drug"]
        action = c.get("action")
        if action not in KNOWN_ACTIONS:               # 1.0.1: never silently ignore an action the engine cannot apply
            unrecognised.append({"drug": drug, "action": action, **cite(c)})
            continue
        if not all(c.get(k) for k in CITED):          # rule #9
            flag(disc, drug, "change_provenance_missing",
                 f"inpatient {c.get('action')} of {drug} has no documenting note and date", c)
        if action == "stop":
            expected.pop(drug, None)
            stopped[drug] = c
        elif action == "start":
            stopped.pop(drug, None)                   # 1.0.3: a later documented restart supersedes the stop
            expected[drug] = {"drug": drug, "dose": c.get("dose"), "status": "active",
                              "reason": c.get("reason"), **cite(c)}
        elif action == "change":
            if drug in expected:
                expected[drug] = {"drug": drug, "dose": c.get("dose"), "status": "active",
                                  "reason": c.get("reason"), **cite(c)}
            else:                                     # rule #8 - never silently ignored
                flag(disc, drug, "change_to_absent_med",
                     f"documented change of {drug} to {c.get('dose')} names a medication that is not on the "
                     f"expected discharge list (never on admission, or already stopped)", c)

    draft = {m["drug"]: dict(m) for m in p.get("draft_discharge_meds", [])}
    for drug, dm in draft.items():
        if drug in stopped:                           # rule #1
            if str(dm.get("status", "active")).lower() not in STOP_STATUSES:
                flag(disc, drug, "unresolved_stop_reappeared",
                     f"{drug} was stopped in-house but reappears in the discharge draft without a new order",
                     stopped[drug])
            elif not str(dm.get("reason") or "").strip():   # rule #5 (1.0.3) - a stop status alone is not documented
                flag(disc, drug, "stopped_med_undocumented",
                     f"{drug} was stopped in-house ({stopped[drug].get('reason')}) and is listed as "
                     f"{dm.get('status')} on the discharge draft without the stop reason", stopped[drug])
        elif drug not in expected:                    # rule #6
            flag(disc, drug, "unordered_addition",
                 f"{drug} {dm.get('dose')} appears on the discharge draft but was on neither the admission list "
                 f"nor an inpatient start order", dm)
    for drug, em in sorted(expected.items()):
        if drug not in draft:                         # rule #4
            flag(disc, drug, "missing_from_discharge",
                 f"{drug} is expected on discharge (active) but is absent from the draft", em)
        elif str(draft[drug].get("status", "active")).lower() in STOP_STATUSES:   # rule #4 (1.0.1)
            flag(disc, drug, "missing_from_discharge",
                 f"{drug} is expected on discharge (active) but the draft lists it as "
                 f"{draft[drug].get('status')} with no inpatient stop order", em)
        elif draft[drug].get("dose") != em.get("dose"):   # rule #7
            flag(disc, drug, "dose_mismatch",
                 f"{drug} draft dose {draft[drug].get('dose')} != expected {em.get('dose')}", em)
    for drug, c in sorted(stopped.items()):
        if drug not in draft:                         # rule #5 - hiding it is not resolving it
            flag(disc, drug, "stopped_med_undocumented",
                 f"{drug} was stopped in-house ({c.get('reason')}) and has been dropped from the discharge draft "
                 f"entirely instead of being listed as stopped", c)

    disc.sort(key=lambda d: (d["drug"], d["type"]))
    clean = len(disc) == 0 and not unrecognised
    p["reconciliation_report"] = {
        "expected_discharge_meds": [expected[k] for k in sorted(expected)],
        # 1.0.3: documented in-house stops, so the summary can show what was discontinued and why
        "stopped_meds": [{"drug": d, "status": "stopped", "reason": c.get("reason"), **cite(c)}
                         for d, c in sorted(stopped.items())],
        "discrepancies": disc, "clean": clean, "source": ENGINE}
    if unrecognised:                                  # only emitted when present, so clean goldens are unchanged
        p["reconciliation_report"]["unrecognised_actions"] = unrecognised
        for u in unrecognised:
            esc.append(f"medication reconciliation input error: inpatient change of {u['drug']} has action "
                       f"{u['action']!r}, which is not one of start/stop/change - the engine cannot apply it, so the "
                       f"reconciliation is not clean until a clinician corrects the record")
    for d in disc:
        esc.append(f"medication reconciliation discrepancy: {d['detail']} ({d['citation']}) - "
                   f"clinician resolution required before summary-draft finalises")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("med_reconcile/1.3")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"med_reconcile: expected={len(expected)} discrepancies={len(disc)} clean={clean} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
