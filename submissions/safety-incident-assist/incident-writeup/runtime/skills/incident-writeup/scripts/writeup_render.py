#!/usr/bin/env python3
"""Validate all terminal hops and render one local Markdown draft to --out only."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from safety_common import load, diagnostic
from safety_terminal import render_markdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if Path(args.packet).resolve() == Path(args.out).resolve():
        raise ValueError('Input packet cannot be overwritten by the Markdown draft')
    rendered = render_markdown(load(args.packet))
    # No output is opened until schema AND recomputation AND render succeed.
    Path(args.out).write_text(rendered, encoding='utf-8')
    print('writeup_render: validated local DRAFT; HUMAN REVIEW REQUIRED; no operational actions.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print('VALIDATION ERROR: ' + diagnostic(exc), file=sys.stderr)
        sys.exit(2)
