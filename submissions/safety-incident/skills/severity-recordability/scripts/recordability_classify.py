#!/usr/bin/env python3
"""recordability_classify - deterministic OSHA severity & recordability engine
(mfg.safety-incident-assist.v1).

Reads the structured incident intake (incident type, injury nature/body part, treatment given,
outcome, days away) and classifies the incident: severity tier, near-miss flag, OSHA recordability
(with the OSHA 300 column) and reportability (with the 1904.39 regulatory clock). Emits the
{classification} hop of the contract and a preliminary next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this
and quotes its output; it never decides recordability itself.

Rules encoded here mirror references/osha-recordability-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:recordability_classify"

FIRST_AID = {"none", "first_aid"}                       # osha-recordability-rules.md #2.1
MED = {"medical_treatment", "hospitalization"}          # #2.2, #2.3
REPORTABLE = {                                          # #4
    "fatality": ("fatality", 8),
    "in_patient_hospitalization": ("in_patient_hospitalization", 24),
    "amputation": ("amputation", 24),
    "loss_of_eye": ("loss_of_eye", 24),
}


def classify(payload):
    inj = payload.get("injury", {}) or {}
    itype = (payload.get("incident_type") or "").lower()
    treatment = (inj.get("treatment_given") or "none").lower()
    outcome = (inj.get("outcome") or "none").lower()
    days_away = int(inj.get("days_away") or 0)

    # --- 1. near-miss vs injury ---
    has_injury = bool(inj.get("body_part") or inj.get("nature")) or treatment in MED \
        or outcome not in ("none", "")
    near_miss = (itype == "near_miss") or (not has_injury and itype in ("near_miss", "property", "environmental", ""))
    if has_injury and treatment in MED:
        near_miss = False

    # --- 4. reportability (1904.39) ---
    if outcome in REPORTABLE:
        rtype, hours = REPORTABLE[outcome]
        reportable = {"value": True, "type": rtype, "deadline_hours": hours,
                      "authority": "OSHA (1904.39)",
                      "citation": "osha-recordability-rules.md #4"}
    else:
        reportable = {"value": False, "type": "none", "deadline_hours": None,
                      "authority": "", "citation": "osha-recordability-rules.md #4.5"}

    # --- 3. recordability + OSHA 300 column ---
    recordable_val = False
    column = ""
    reason = ""
    if near_miss:
        recordable_val, column, reason = False, "", "Near miss: no injury/illness (osha-recordability-rules.md #1.1, #3.5)."
    elif treatment in FIRST_AID and outcome == "none":
        recordable_val, column, reason = False, "", "First-aid only, no days away/restriction (osha-recordability-rules.md #2.1, #3.5)."
    else:
        recordable_val = True
        if outcome == "fatality":
            column, reason = "G", "Work-related fatality (osha-recordability-rules.md #3.1)."
        elif outcome in ("in_patient_hospitalization", "amputation", "loss_of_eye") or days_away > 0:
            column = "H"
            reason = (f"Days away from work ({days_away} day(s)) / severe outcome "
                      f"(osha-recordability-rules.md #3.2).")
        elif outcome in ("restricted_duty", "job_transfer"):
            column, reason = "I", "Job transfer or work restriction (osha-recordability-rules.md #3.3)."
        else:
            column, reason = "J", "Medical treatment beyond first aid (osha-recordability-rules.md #2.2, #3.4)."

    recordable = {"value": recordable_val, "reason": reason, "osha_300_column": column,
                  "citation": "osha-recordability-rules.md #3"}

    # --- 5. severity ---
    if reportable["value"]:
        severity = "critical"
    elif recordable_val and (outcome == "days_away" or days_away > 0):
        severity = "high"
    elif recordable_val:
        severity = "medium"
    else:
        severity = "low"

    # --- 6. confidence ---
    complete = bool(inj.get("treatment_given")) and bool(inj.get("outcome")) if not near_miss else True
    confidence = 0.92 if complete else 0.75

    return {
        "severity": severity,
        "near_miss": bool(near_miss),
        "recordable": recordable,
        "reportable": reportable,
        "confidence": confidence,
        "source": ENGINE,
        "citation": "osha-recordability-rules.md #3, #4, #5",
    }, complete


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True, help="incident-intake.json (structured contract input)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.intake, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.safety-incident-assist.v1", "wrong contract version"

    cls, complete = classify(payload)
    escalations = list(payload.get("escalations", []))

    # --- governance escalations (osha-recordability-rules.md #6) ---
    if not complete:
        escalations.append(
            "Incident record incomplete (treatment/outcome missing or ambiguous); confirm with the "
            "treating clinician before finalizing the classification (osha-recordability-rules.md #6.2).")

    # --- preliminary next-best action (routing-notify finalizes it) ---
    col = cls["recordable"]["osha_300_column"]
    if cls["reportable"]["value"]:
        nba = (f"Do NOT classify as first-aid. Record on the OSHA 300 (column {col}). File the OSHA "
               f"report within {int(cls['reportable']['deadline_hours'])} hours "
               f"({cls['reportable']['type']}, 1904.39).")
    elif cls["recordable"]["value"]:
        nba = (f"Record on the OSHA 300 (column {col}); complete the investigation and RCA per policy.")
    else:
        nba = ("Log as first-aid/near-miss (not OSHA recordable); investigate as a leading indicator "
               "and feed any control back into the JHA.")

    payload["classification"] = cls
    payload["next_best_action"] = nba
    payload["escalations"] = escalations

    _finish(payload, a.out)
    print(f"recordability_classify: severity={cls['severity']}, near_miss={cls['near_miss']}, "
          f"recordable={cls['recordable']['value']}(col {col or '-'}), "
          f"reportable={cls['reportable']['value']} -> {a.out}")
    return 0


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "recordability_classify/1.0" not in prov["engines"]:
        prov["engines"].append("recordability_classify/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
