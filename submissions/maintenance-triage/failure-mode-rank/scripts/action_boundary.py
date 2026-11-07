"""Draft action boundary; diagnostic scores and priority are never changed."""
CONFIDENCE_FLOOR = 0.75  # failure-mode-library.md #4.1
BOUNDARY = (" No reset/restart, protective-device bypass, energized work or repair authorization. "
            "Qualified personnel must follow site isolation/LOTO and applicable OEM procedures.")
DIAGNOSIS_REQUIRED = ("DRAFT: Human diagnosis required; no single cause or corrective repair is selected "
                      "(failure-mode-library.md #4.1)." + BOUNDARY)
NOT_DIAGNOSED = ("DRAFT: Not diagnosed; applicable OEM/vendor and human diagnostic review required; "
                 "no corrective repair is selected (failure-mode-library.md #4.3)." + BOUNDARY)
ASSESSMENTS = {
    "bearing_degradation": "bearing replacement, lubrication and shaft alignment",
    "coupling_misalignment": "pump/motor coupling alignment and coupling-element condition",
    "motor_overload_electrical": "the cause of the overload trip using applicable OEM diagnostic evidence",
    "mechanical_seal_failure": "mechanical-seal replacement and shaft-sleeve condition",
    "impeller_cavitation": "suction/NPSH conditions and possible impeller cavitation erosion",
}


def apply_action_boundary(payload):
    ranked = payload.get("ranked_causes", [])
    if not ranked:
        payload["recommended_action"] = NOT_DIAGNOSED
        return
    low_top = ranked[0]["confidence"] < CONFIDENCE_FLOOR
    for cause in ranked:
        assessment = ASSESSMENTS.get(cause["failure_mode"])
        if low_top or cause["confidence"] < CONFIDENCE_FLOOR:
            cause["recommended_fix"] = DIAGNOSIS_REQUIRED
        elif assessment is None:
            cause["recommended_fix"] = NOT_DIAGNOSED
        else:
            cause["recommended_fix"] = (
                "DRAFT: Qualified human review of the candidate diagnosis and assessment of "
                + assessment + "; verify asset-model/manual applicability before any corrective work."
                + BOUNDARY)
    payload["recommended_action"] = ranked[0]["recommended_fix"]
