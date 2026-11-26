#!/usr/bin/env python3
"""guideline_check - deterministic billing-guideline compliance engine (Govern, step 4 of 5).

The rules live in the shared billing_rules.py (identical copies next to code_map.py and
exception_report.py), whose constants mirror references/client-billing-guidelines.md section by
section. The model reports these flags; it never decides, suppresses or downgrades compliance verdicts.

v1.0.6 rules (billing_rules.govern):
- Signals from disabled or unknown sources are dropped first (signal_policy.py, #10.1); an
  entry that linked one gets a hold_for_review flag and the signal never counts as evidence.
- Rows outside the recorded timekeeper scope are withheld before any check (#12.1). A recorded team view
  must be confirmed by the raw engagement letter and exports (--raw-dir) or the packet is refused; with
  --raw-dir, and always for a team view, the activity packet must equal activity_pull re-run on them.
- #13.1 every entry's code mapping is recomputed from the code-map rules; a supplied code_mapping
  that disagrees (a forged recommendation, cleared flags) is discarded, the recomputed mapping and
  its flags are used, and the entry gets a code_mapping_mismatch hold.
- #1.1 under 12 words = reject. #1.2 actor's work / subject / purpose are checked on the
  narrative text itself for every entry (1 missing = needs_review, 2+ = reject).
- #2.1 >2.0 h with more than one class = reject; #2.2 <=2.0 h may combine at most two classes,
  and only with an explicit subject and purpose.
- #3.2 a vague phrase is reject unless the narrative states a specific subject AND purpose.
- #1.2 the subject is credited only against the entry's own linked signals (no fall-back to
  every packet signal).
- #6.2 evidence counts only linked activity on the entry's own date; off-date links are flagged.
  An entry over 0.2 h with NO linked evidence gets a no_linked_evidence hold (never compliant).
- #11.1 embedded_instruction hold (shared steering_guard detector via signal_policy.py) on the
  narrative, notes, main draft, suggested rewrites and linked signal text (citations included),
  alone and joined across fields.
- #11.2 flagged text is withheld: a flagged main draft narrative, suggested rewrite or missing-time
  subject is replaced by the neutral withheld marker before output.
- #7.1 near-duplicate = SequenceMatcher ratio or token Jaccard >= 0.92 against earlier
  narratives for the same meeting.
- #13.8 the coded packet must equal narrative-draft and code-map re-run on the activity packet
  (--activity) in every engine-owned field, provenance included, or nothing is written.
"""
import datetime
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import billing_rules  # noqa: E402  (shared rules, identical copies next to code_map.py and exception_report.py)
import signal_policy  # noqa: E402  (shared copy shipped next to each engine)

ENGINE = billing_rules.GUIDELINE_ENGINE
ENGINE_VERSION = "guideline_check/1.0.13"
CONTRACT = "ps.time-expense-narrative-compliance.v1"
# Narrative fields are data. The tripwire is shared by every engine (signal_policy.py, #11.1).
embedded_instruction = signal_policy.embedded_instruction


class InputError(ValueError):
    pass


def generated_at(override):
    if override:
        if not signal_policy.contract_check.valid_timestamp(override):
            raise InputError(f"--generated-at must be an ISO-8601 timestamp with seconds and an offset (for example 2026-09-23T00:00:00Z), got a string of {len(override)} character(s)")
        return override
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_packet(path):
    payload = signal_policy.read_json(path, InputError, "coded input")
    if not isinstance(payload, dict):
        raise InputError("input is not a JSON object")
    if payload.get("contract_version") != CONTRACT:
        raise InputError(f"expected a {CONTRACT} object (contract_version must be the contract constant)")
    signal_policy.validate_packet(payload, "coded")
    return payload


def main():
    ap = signal_policy.ArgumentParser(description="Govern time-entry narratives against client billing guidelines.")
    ap.add_argument("--coded", required=True, help="Input coded contract JSON")
    ap.add_argument("--activity", required=True, help="The activity packet the coded packet was derived from (activity_pull's output); "
                    "the coded packet must equal its re-derivation from it (client-billing-guidelines.md #13.8)")
    ap.add_argument("--out", required=True, help="Output governed contract JSON")
    ap.add_argument("--raw-dir", help=signal_policy.RAW_DIR_HELP)
    ap.add_argument("--signal-config", help="Additional signal policy JSON; it can only narrow the plugin's config/signal-sources.json, which is always applied (most restrictive wins)")
    ap.add_argument("--generated-at", help="Fixed ISO-8601 UTC timestamp for reproducible golden files")
    args = ap.parse_args()

    try:
        stamp = generated_at(args.generated_at)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        coded = load_packet(args.coded)
        activity = signal_policy.load_activity_root(args.activity, InputError, raw_dir=args.raw_dir)
        # #13.8: the whole coded packet must equal narrative-draft and code-map re-run on the activity packet.
        out = deepcopy(billing_rules.check_rederived(coded, activity, "coded", script_dir))
        rejected = billing_rules.govern_stage(out, stamp, config_path=args.signal_config, script_dir=script_dir,
                                              version=ENGINE_VERSION)
    except (InputError, signal_policy.PolicyError) as exc:
        sys.exit(f"guideline_check: {signal_policy.error_text(exc)}")

    exception_list = out["exception_list"]
    missing_time = out["missing_time_report"]
    excluded = out.get("provenance", {}).get("excluded_signals", [])
    try:
        signal_policy.write_output(args.out, signal_policy.dump_json(out))
    except (OSError, ValueError) as exc:  # ValueError covers NaN in dump_json and UnicodeEncodeError
        sys.exit(f"guideline_check: cannot write output: {signal_policy.error_text(exc)}")
    print(f"guideline_check: {len(out['time_entries'])} entries, {len(exception_list)} exception(s), "
          f"{len(missing_time)} missing-time item(s), {len(excluded)} excluded signal(s), "
          f"{rejected} supplied code mapping(s) rejected -> governed packet written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
