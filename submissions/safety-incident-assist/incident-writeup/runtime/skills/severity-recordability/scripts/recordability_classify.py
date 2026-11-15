#!/usr/bin/env python3
"""recordability_classify - deterministic OSHA severity & recordability engine
(mfg.safety-incident-assist.v2), EHS-review candidate.

Reads the structured incident intake (incident type, injury nature/body part, treatment given,
outcome, days away) and drafts severity, near-miss and recording recommendations
(with a supported OSHA 300 column). Reporting and timing remain review-required. Emits the
{classification} hop of the contract and a preliminary next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this
and quotes its output; it never decides recordability itself.

Rules encoded here mirror references/osha-recordability-rules.md by section number.
"""
import argparse, sys
import copy
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from safety_common import load, validate, history_match, governance, finish, diagnostic
from safety_reconcile import reconciliation_issues

ENGINE = "engine:recordability_classify"

FIRST_AID = {"none", "first_aid"}                       # osha-recordability-rules.md #2.1
MED = {"medical_treatment", "hospitalization"}          # #2.2, #2.3
REPORTABLE = {"fatality", "in_patient_hospitalization", "amputation", "loss_of_eye"}


def classify(payload):
    validate(payload)
    inj = payload.get("injury", {}) or {}
    itype = payload.get("incident_type")
    treatment = inj.get("treatment_given")
    outcome = inj.get("outcome")
    days_away = inj.get("days_away")
    diagnosis = inj.get("significant_diagnosis")
    significant = diagnosis in {"fracture", "cracked_bone", "punctured_eardrum",
                               "cancer", "chronic_irreversible_disease"}
    verified_diagnosis = (significant and inj.get("diagnosed_by") == "physician_or_plhcp"
                          and bool(inj.get("diagnosis_citation")))
    issues = []
    if itype is None:
        issues.append("Incident type missing.")
    app = payload.get("applicability", {})
    applicable = (all(app.get(k) is True for k in ("work_related", "new_case", "recordkeeping_covered"))
                  and app.get("jurisdiction") == "federal_osha" and bool(app.get("citation")))
    if not applicable:
        issues.append("Recording applicability not established by cited EHS evidence (scope/new case/work-relatedness).")
    if not inj.get("citation"):
        issues.append("Treatment/outcome evidence citation missing; completeness is not confidence.")
    if treatment is None or outcome is None or days_away is None:
        issues.append("Treatment, outcome or days-away facts missing.")
    if significant and not verified_diagnosis:
        issues.append("Significant diagnosis lacks physician/PLHCP attribution and citation.")
    if outcome == "days_away" and days_away == 0:
        issues.append("Days-away outcome contradicts zero days; confirm clinician recommendation/count.")

    # --- 1. near-miss vs injury ---
    has_injury = bool(inj.get("body_part", "").strip() or inj.get("nature", "").strip()) or treatment in MED \
        or treatment == "first_aid" or outcome not in ("none", None) or bool(days_away) \
        or significant or inj.get("loss_of_consciousness") is True
    contradiction = itype in ("near_miss", "property", "environmental") and has_injury
    if contradiction:
        issues.append("Non-injury incident type contradicts injury evidence; do not treat as near miss.")
    absence = (inj.get("absence_confirmed") is True and bool(inj.get("citation"))
               and treatment == "none" and outcome == "none" and days_away == 0
               and inj.get("loss_of_consciousness") is False and diagnosis == "none"
               and inj.get("other_recording_criteria_reviewed") is True and not has_injury)
    if itype == "near_miss" and not absence and not contradiction:
        issues.append("Cited explicit absence of injury is not established; near-miss status undetermined.")
    near_miss = (None if contradiction or not itype else
                 (True if absence else None) if itype == "near_miss" else False)
    if inj.get("absence_confirmed") is True and has_injury:
        issues.append("Claimed absence contradicts structured injury/treatment evidence; reconcile sources.")
    # No medical/day inference: contradictions only add review, including explicit
    # intake conflicts that are not recognizable by a bounded lexical check.
    narrative_issues = reconciliation_issues(payload, blank_detail=not (
        inj.get("body_part", "").strip() or inj.get("nature", "").strip()))
    issues.extend(narrative_issues)
    if narrative_issues and (itype in ("near_miss", "property", "environmental")
                             or payload.get("source_conflicts")):
        near_miss = None

    # --- 4. reportability (1904.39) ---
    severe = outcome in REPORTABLE or treatment == "hospitalization"
    # The legacy intake cannot establish every 1904.39 applicability/awareness fact.
    # Keep the clock explicitly blocked rather than guessing from occurrence time.
    reportable = {"value": None, "status": "review_required",
                  "type": outcome if outcome in REPORTABLE else "undetermined",
                  "deadline_hours": None, "authority": "OSHA (1904.39)",
                  "reason": "Reporting applicability and complete event/awareness timing require EHS review; no deadline asserted.",
                  "citation": "osha-recordability-rules.md #4"}

    # --- 3. recordability + OSHA 300 column ---
    recordable_val = None
    column = ""
    reason = ""
    positive = outcome == "fatality" or (days_away is not None and days_away > 0) \
        or outcome in ("days_away", "restricted_duty", "job_transfer") \
        or treatment == "medical_treatment" or inj.get("loss_of_consciousness") is True or verified_diagnosis
    negative_screen = (inj.get("loss_of_consciousness") is False and diagnosis == "none"
                       and inj.get("other_recording_criteria_reviewed") is True)
    if issues:
        reason = "REVIEW REQUIRED: " + " ".join(issues)
    elif positive:
        recordable_val = True
        if outcome == "fatality":
            column, reason = "G", "Work-related fatality (osha-recordability-rules.md #3.1)."
        elif outcome == "days_away" or days_away > 0:
            column = "H"
            reason = (f"Days away from work ({days_away} day(s)) "
                      f"(osha-recordability-rules.md #3.2).")
        elif outcome in ("restricted_duty", "job_transfer"):
            column, reason = "I", "Job transfer or work restriction (osha-recordability-rules.md #3.3)."
        else:
            column, reason = "J", "Medical treatment, loss of consciousness or verified significant diagnosis (1904.7)."
    elif treatment in FIRST_AID and outcome == "none" and days_away == 0 and negative_screen:
        recordable_val, reason = False, "No recording criterion supported by the cited complete negative screen; draft EHS review."
    else:
        issues.append("Negative screen incomplete or severe outcome requires clinical clarification; no nonrecordable default.")
        reason = "REVIEW REQUIRED: " + issues[-1]
    if payload.get("prior_determination", {}).get("recordable") is True and recordable_val is False:
        issues.append("Prior positive recording determination is not superseded without verified EHS review.")
        recordable_val, column, reason = None, "", "REVIEW REQUIRED: " + issues[-1]

    recordable = {"value": recordable_val, "reason": reason, "osha_300_column": column,
                  "status": "draft_determination" if recordable_val is not None else "review_required",
                  "citation": "osha-recordability-rules.md #3"}

    # --- 5. severity ---
    if severe:
        severity = "critical"
    elif (days_away is not None and days_away > 0) or outcome == "days_away":
        severity = "high"
    elif recordable_val is True:
        severity = "medium"
    else:
        severity = "review_required" if recordable_val is None else "low"

    # --- 6. confidence ---
    complete = not issues
    confidence = None

    return {
        "severity": severity,
        "near_miss": near_miss,
        "recordable": recordable,
        "reportable": reportable,
        "confidence": confidence,
        "confidence_basis": "not_estimated",
        "review_reasons": issues,
        "status": "draft_review_required",
        "source": ENGINE,
        "citation": "osha-recordability-rules.md #3, #4, #5",
    }, complete


def classification_hop(payload):
    """Pure hop construction; history/governance recomputed from original input facts."""
    payload = copy.deepcopy(payload)
    cls, complete = classify(payload)
    escalations = list(payload.get("escalations", []))
    payload["history"] = history_match(payload)
    payload["governance"] = governance(payload, cls)
    for stale in ("routing", "writeup", "next_best_action"):
        payload.pop(stale, None)
    if payload["governance"]["downgrade_hold"]:
        escalations.append("HOLD: downgrade request or prior positive determination requires documented EHS-manager review; no approval verified.")
    if payload["history"]["status"] == "review_required":
        escalations.append("History REVIEW REQUIRED: " + payload["history"]["reason"])
    escalations.append("EHS REVIEW REQUIRED / COWORK RE-EVAL PENDING. Reporting deadline undetermined; urgent EHS assessment for severe events, do not wait for this plugin.")

    # --- governance escalations (osha-recordability-rules.md #6) ---
    if not complete:
        escalations.append(
            "Incident record incomplete (treatment/outcome missing or ambiguous); confirm with the "
            "treating clinician before finalizing the classification (osha-recordability-rules.md #6.2).")

    # --- preliminary next-best action (routing-notify finalizes it) ---
    col = cls["recordable"]["osha_300_column"]
    nba = ("DRAFT — EHS REVIEW REQUIRED. Review the cited recording determination and unresolved reporting "
           "applicability immediately for severe events; no reporting deadline asserted. No filing, notification or closure authorized.")

    payload["classification"] = cls
    payload["next_best_action"] = nba
    payload["escalations"] = list(dict.fromkeys(escalations))

    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    payload = classification_hop(load(a.intake))
    _finish(payload, a.out)
    cls = payload["classification"]
    print("recordability_classify: local DRAFT saved; HUMAN REVIEW REQUIRED; no official determination.")
    return 0


def _finish(payload, out):
    finish(payload, out, "recordability_classify")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"VALIDATION ERROR: {diagnostic(exc)}", file=sys.stderr)
        sys.exit(2)
