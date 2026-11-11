#!/usr/bin/env python3
"""Structural-only CLI for supplied draft inputs; not terminal semantic validation."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from safety_common import load, diagnostic
parser = argparse.ArgumentParser()
parser.add_argument('--intake', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
try:
    payload = load(args.intake)
    serialized = json.dumps(payload, indent=2, allow_nan=False) + '\n'
    Path(args.out).write_text(serialized, encoding='utf-8')
    print('structural load/validate: accepted local draft inputs; not an official determination.')
except (ValueError, TypeError, KeyError, OSError) as exc:
    print('VALIDATION ERROR: ' + diagnostic(exc), file=sys.stderr)
    sys.exit(2)
