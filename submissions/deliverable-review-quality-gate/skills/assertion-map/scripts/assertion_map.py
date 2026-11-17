#!/usr/bin/env python3
"""assertion_map - deterministic assertion-to-evidence support engine."""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import assertion_rules as rules  # noqa: E402  shared byte-identical with gate-check (tests/check_shared_copies.py)

ENGINE = rules.AM_ENGINE
ENGINE_VERSION = rules.AM_ENGINE_VERSION
CONTRACT_VERSION = rules.CONTRACT_VERSION
InputError = rules.InputError


def load_json(path):
    return rules.load_json_file(path, "review input")


validate_generated_at = rules.validate_generated_at


def require_contract(payload):
    rules.require_review_input(payload)


def main():
    parser = rules.EngineArgumentParser(prog="assertion_map.py", description="Map assertions to evidence support deterministically.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    try:
        generated_at = validate_generated_at(args.generated_at)
        payload = load_json(args.input)
        payload, mappings = rules.assertion_map_stage(payload, generated_at)
        rules.write_json_atomic(args.out, payload, "mapped output")
        unsupported = sum(1 for item in mappings if item["support_status"] == "unsupported")
        limited = sum(1 for item in mappings if item["support_status"] == "limited")
        print(f"assertion_map: {len(mappings)} assertion(s), {unsupported} unsupported, {limited} limited -> mapped output written")
        return 0
    except InputError as exc:
        print(f"assertion_map input error: {exc}", file=sys.stderr)
        return 1
    except RecursionError:
        print("assertion_map input error: input is nested too deeply to process safely", file=sys.stderr)
        return 1
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        print(f"assertion_map input error: malformed input ({type(exc).__name__}; details withheld because they may quote untrusted text)", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
