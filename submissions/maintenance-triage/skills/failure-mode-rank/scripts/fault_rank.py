#!/usr/bin/env python3
"""fault_rank - deterministic failure-mode ranking engine (mfg.maintenance-triage.v1).

Reads the structured fault intake (symptoms + alarm codes + asset history) and ranks the
candidate failure modes from the failure-mode library, applying the repeat-failure
root-cause promotion rule. Emits the {ranked_causes} hop of the contract.

Same input, same output, always: no LLM calls, no network, no randomness. The model
invokes this and quotes its output; it never re-ranks causes itself.

Rules encoded here mirror references/failure-mode-library.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:fault_rank"
CONFIDENCE_FLOOR = 0.75          # failure-mode-library.md #4.1
AMBIGUITY_BAND = 0.08            # failure-mode-library.md #4.2
HISTORY_PROMOTION_BOOST = 0.20   # failure-mode-library.md #3.1
HISTORY_REPEAT_BOOST = 0.08      # failure-mode-library.md #3.2
REPEAT_THRESHOLD = 3             # failure-mode-library.md #3.1

# --- rules-as-data: failure-mode signatures (failure-mode-library.md #2) ---
# weights per matched signal; base is the starting confidence for the mode.
FAILURE_MODES = [
    {"failure_mode": "bearing_degradation", "lib": "failure-mode-library.md #2.1", "manual": "OEM Pump Manual CP-200 §6.3",
     "symptoms": {"high_vibration": 3, "bearing_temp_high": 3, "grinding_noise": 2}, "alarms": {"VIB-HH": 3, "TEMP-BRG-H": 3},
     "base": 0.58, "mechanical_root": True,
     "fix": "Replace pump bearings; verify lubrication and shaft alignment."},
    {"failure_mode": "coupling_misalignment", "lib": "failure-mode-library.md #2.2", "manual": "OEM Pump Manual CP-200 §5.2",
     "symptoms": {"high_vibration": 3, "overload_trip": 2, "bearing_temp_high": 1, "grinding_noise": 1}, "alarms": {"VIB-HH": 2, "OL-TRIP": 2},
     "base": 0.55, "mechanical_root": True,
     "fix": "Laser-align pump/motor coupling; inspect coupling element."},
    {"failure_mode": "motor_overload_electrical", "lib": "failure-mode-library.md #2.3", "manual": "OEM Pump Manual CP-200 §7.1",
     "symptoms": {"overload_trip": 3, "motor_hot": 2}, "alarms": {"OL-TRIP": 3},
     "base": 0.50, "symptomatic": True,
     "fix": "Reset overload relay; verify motor current draw and supply voltage."},
    {"failure_mode": "mechanical_seal_failure", "lib": "failure-mode-library.md #2.4", "manual": "OEM Pump Manual CP-200 §6.1",
     "symptoms": {"seal_leak": 3, "reduced_flow": 1}, "alarms": {"SEAL-LEAK": 3},
     "base": 0.55, "fix": "Replace mechanical seal; inspect shaft sleeve."},
    {"failure_mode": "impeller_cavitation", "lib": "failure-mode-library.md #2.5", "manual": "OEM Pump Manual CP-200 §6.4",
     "symptoms": {"reduced_flow": 3, "grinding_noise": 2, "high_vibration": 1, "low_suction_pressure": 2}, "alarms": {"FLOW-LO": 3, "SUCT-LO": 2},
     "base": 0.50, "fix": "Correct suction/NPSH condition; inspect impeller for cavitation erosion."},
]

MECHANICAL_SIGNALS = {"high_vibration", "bearing_temp_high"}
MECHANICAL_ALARMS = {"VIB-HH", "TEMP-BRG-H"}
SYMPTOMATIC_MODES = {"motor_overload_electrical", "overload_reset", "breaker_reset"}


def score_modes(observed_sym, observed_alm):
    scored = []
    for i, m in enumerate(FAILURE_MODES):
        matched, raw = [], 0
        for sym, w in m["symptoms"].items():
            if sym in observed_sym:
                raw += w; matched.append(f"symptom:{sym}")
        for alm, w in m["alarms"].items():
            if alm in observed_alm:
                raw += w; matched.append(f"alarm:{alm}")
        if raw > 0:
            conf = min(0.97, round(m["base"] + 0.06 * len(matched), 2))
            scored.append({"idx": i, "mode": m, "raw": raw, "matched": matched, "confidence": conf})
    return scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True, help="fault-intake.json (contract input)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.intake, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.maintenance-triage.v1", "wrong contract version"

    observed_sym = {s["name"] for s in payload.get("symptoms", [])}
    observed_alm = {c["code"] for c in payload.get("alarm_codes", [])}
    escalations = list(payload.get("escalations", []))

    scored = score_modes(observed_sym, observed_alm)

    if not scored:
        payload["ranked_causes"] = []
        escalations.append("No known failure-mode signal matched the reported symptoms/alarms; "
                           "route to OEM manual / vendor support (failure-mode-library.md #4.3).")
        payload["escalations"] = escalations
        payload.setdefault("history", {})["repeat_promotion"] = False
        _finish(payload, a.out); return 0

    total_raw = sum(s["raw"] for s in scored)
    for s in scored:
        s["match_score"] = round(s["raw"] / total_raw, 3) if total_raw else 0.0

    # --- repeat-failure inference (failure-mode-library.md #3) ---
    history = payload.get("history", {}) or {}
    prior = history.get("prior_work_orders", []) or []
    symptomatic_repeats = sum(1 for wo in prior if wo.get("failure_mode") in SYMPTOMATIC_MODES)
    mechanical_present = bool(observed_sym & MECHANICAL_SIGNALS) or bool(observed_alm & MECHANICAL_ALARMS)
    repeat_promotion = False
    promotion_note = None

    if symptomatic_repeats >= REPEAT_THRESHOLD and mechanical_present:
        # #3.1 promote the corroborated mechanical root cause to rank 1
        root = next((s for s in scored if s["mode"].get("mechanical_root")), None)
        if root is None:
            # mechanical alarm present but signature not scored: synthesize bearing_degradation
            m = FAILURE_MODES[0]
            root = {"idx": 0, "mode": m, "raw": 3, "matched": ["alarm:VIB-HH"],
                    "confidence": m["base"], "match_score": 0.0}
            scored.append(root)
        root["confidence"] = min(0.97, round(root["confidence"] + HISTORY_PROMOTION_BOOST, 2))
        root["promoted"] = True
        repeat_promotion = True
        promotion_note = (f"{symptomatic_repeats} symptomatic resets in {history.get('window_days','?')} days "
                          f"with mechanical signals present -> symptomatic fix is masking a root cause "
                          f"(failure-mode-library.md #3.1).")
        root.setdefault("matched", []).append("history:repeat-failure-pattern")
        escalations.append("Recurring failure pattern detected; route to reliability engineering for "
                           "root-cause analysis (failure-mode-library.md #3.3).")
    else:
        # #3.2 lighter corroboration
        counts = {}
        for wo in prior:
            counts[wo.get("failure_mode")] = counts.get(wo.get("failure_mode"), 0) + 1
        for s in scored:
            c = counts.get(s["mode"]["failure_mode"], 0)
            if c >= 2:
                s["confidence"] = min(0.97, round(s["confidence"] + HISTORY_REPEAT_BOOST, 2))
                s.setdefault("matched", []).append(f"history:{c}-prior-same-mode")

    # sort: promoted first, then confidence, then raw, then library order
    scored.sort(key=lambda s: (not s.get("promoted", False), -s["confidence"], -s["raw"], s["idx"]))

    ranked = []
    for rank, s in enumerate(scored, start=1):
        m = s["mode"]
        evidence = list(s["matched"])
        if s.get("promoted") and promotion_note:
            evidence.append(promotion_note)
        if m.get("symptomatic") and repeat_promotion:
            evidence.append("Recurred as a repeat symptomatic fix in history; treated as a symptom, "
                            "not the root cause (failure-mode-library.md #3.1).")
        ranked.append({
            "rank": rank,
            "failure_mode": m["failure_mode"],
            "match_score": s["match_score"],
            "evidence": evidence,
            "recommended_fix": m["fix"],
            "confidence": s["confidence"],
            "source": ENGINE,
            "citation": f"{m['lib']}; {m['manual']}",
        })

    top = ranked[0]
    # #4.1 confidence floor
    if top["confidence"] < CONFIDENCE_FLOOR:
        escalations.append(f"Top candidate '{top['failure_mode']}' confidence {top['confidence']} below "
                           f"{CONFIDENCE_FLOOR} floor; human diagnosis required (failure-mode-library.md #4.1).")
    # #4.2 ambiguity
    if len(ranked) >= 2 and not repeat_promotion:
        if abs(ranked[0]["match_score"] - ranked[1]["match_score"]) < AMBIGUITY_BAND:
            escalations.append(f"Differential diagnosis: {ranked[0]['failure_mode']} vs "
                               f"{ranked[1]['failure_mode']} within {AMBIGUITY_BAND} match; confirm with the "
                               f"check named in the OEM manual (failure-mode-library.md #4.2).")

    payload["ranked_causes"] = ranked
    payload["recommended_action"] = top["recommended_fix"]
    payload["escalations"] = escalations
    payload.setdefault("history", {})["repeat_promotion"] = repeat_promotion
    _finish(payload, a.out)
    print(f"fault_rank: {len(ranked)} candidate(s), top={top['failure_mode']} "
          f"(conf {top['confidence']}), repeat_promotion={repeat_promotion} -> {a.out}")
    return 0


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "fault_rank/1.0" not in prov["engines"]:
        prov["engines"].append("fault_rank/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
