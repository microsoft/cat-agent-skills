#!/usr/bin/env python3
"""Validate a Cowork plugin project and, optionally, its package."""

from __future__ import annotations

import argparse
import sys

from cowork_plugin_utils import CoworkPluginError, print_result, validate_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--package-path")
    parser.add_argument("--allow-oauth-placeholder", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = validate_project(
            args.project_path,
            package_path=args.package_path,
            allow_oauth_placeholder=args.allow_oauth_placeholder,
        )
        print_result(result.to_dict())
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
