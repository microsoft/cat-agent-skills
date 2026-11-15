#!/usr/bin/env python3
"""code_map - deterministic phase/task mapping for time-entry narratives (step 3 of 5).

The rules live in the shared billing_rules.py (identical copies next to guideline_check.py and
exception_report.py), whose constants mirror references/task-phase-codes.md and
references/client-billing-guidelines.md. guideline_check.py recomputes the same mapping and holds
an entry whose supplied code_mapping disagrees (client-billing-guidelines.md #13.1).

v1.0.6 rules:
- Signals from disabled or unknown sources are dropped first (signal_policy.py, #10.1), and rows
  outside the recorded timekeeper scope are withheld (#12.1). A recorded team view must be confirmed
  by the raw engagement letter and exports (--raw-dir) or the packet is refused; with --raw-dir, and
  always for a team view, the activity packet must equal activity_pull re-run on those exports.
- Activity-class text that trips the embedded-instruction tripwire is never echoed in a flag (#11.2).
- Linked signals whose activity classes point to more than one task code are CONFLICTING:
  they map to UNMAPPED at 0.40 and are held for review (task-phase-codes.md #5.3). The engine
  never majority-votes a code. Every linked signal is mapped BEFORE any non-billable decision,
  so a client meeting plus an internal call is a conflict, not NB900 (#4.1 vs #3.1).
- A non-billable signal maps to NB900 (#4.1) unless its class is billing_hygiene -> BH910 (#4.2).
- The drafted packet must equal narrative-draft re-run on the activity packet (--activity) in every
  engine-owned field, provenance included, or nothing is written (#13.8).
"""
import datetime
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import billing_rules  # noqa: E402  (shared rules, identical copies next to guideline_check.py and exception_report.py)
import signal_policy  # noqa: E402  (shared copy shipped next to each engine)

ENGINE = billing_rules.CODE_MAP_ENGINE
ENGINE_VERSION = "code_map/1.0.13"
CONTRACT = "ps.time-expense-narrative-compliance.v1"


class InputError(ValueError):
    pass


def generated_at(override):
    if override:
        if not signal_policy.contract_check.valid_timestamp(override):
            raise InputError(f"--generated-at must be an ISO-8601 timestamp with seconds and an offset (for example 2026-09-23T00:00:00Z), got a string of {len(override)} character(s)")
        return override
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_packet(path):
    payload = signal_policy.read_json(path, InputError, "drafted input")
    if not isinstance(payload, dict):
        raise InputError("input is not a JSON object")
    if payload.get("contract_version") != CONTRACT:
        raise InputError(f"expected a {CONTRACT} object (contract_version must be the contract constant)")
    signal_policy.validate_packet(payload, "drafted")
    return payload


def main():
    ap = signal_policy.ArgumentParser(description="Map drafted time entries to phase/task codes.")
    ap.add_argument("--drafted", required=True, help="Input drafted contract JSON")
    ap.add_argument("--activity", required=True, help="The activity packet the drafted packet was drafted from (activity_pull's output); "
                    "the drafted packet must equal its re-derivation from it (client-billing-guidelines.md #13.8)")
    ap.add_argument("--out", required=True, help="Output coded contract JSON")
    ap.add_argument("--raw-dir", help=signal_policy.RAW_DIR_HELP)
    ap.add_argument("--signal-config", help="Additional signal policy JSON; it can only narrow the plugin's config/signal-sources.json, which is always applied (most restrictive wins)")
    ap.add_argument("--generated-at", help="Fixed ISO-8601 UTC timestamp for reproducible golden files")
    args = ap.parse_args()

    try:
        stamp = generated_at(args.generated_at)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        drafted = load_packet(args.drafted)
        activity = signal_policy.load_activity_root(args.activity, InputError, raw_dir=args.raw_dir)
        # #13.8: the whole drafted packet must equal narrative-draft re-run on the activity packet.
        out = deepcopy(billing_rules.check_rederived(drafted, activity, "drafted", script_dir))
        billing_rules.code_stage(out, stamp, config_path=args.signal_config, script_dir=script_dir,
                                 version=ENGINE_VERSION)
    except (InputError, signal_policy.PolicyError) as exc:
        sys.exit(f"code_map: {signal_policy.error_text(exc)}")

    mappings = [entry["code_mapping"] for entry in out["time_entries"]]
    held = sum(m["recommended_task_code"] == "UNMAPPED" for m in mappings)
    mismatches = sum(any(f["flag"] == "submitted_code_mismatch" for f in m["flags"]) for m in mappings)
    try:
        signal_policy.write_output(args.out, signal_policy.dump_json(out))
    except (OSError, ValueError) as exc:  # ValueError covers NaN in dump_json and UnicodeEncodeError
        sys.exit(f"code_map: cannot write output: {signal_policy.error_text(exc)}")
    print(f"code_map: {len(out['time_entries'])} entries, {mismatches} submitted-code mismatch(es), "
          f"{held} unmapped/held -> coded packet written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
