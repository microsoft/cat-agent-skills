#!/usr/bin/env python3
"""Safely inspect and validate an untrusted Cowork plugin ZIP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cowork_plugin_utils import (
    ATK_VERSION,
    CoworkPluginError,
    inspect_zip,
    print_result,
    run_atk,
    temporary_workspace,
    validate_project,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-path", required=True)
    parser.add_argument("--atk-version", default=ATK_VERSION)
    parser.add_argument("--allow-oauth-placeholder", action="store_true")
    parser.add_argument("--skip-toolkit-validation", action="store_true")
    parser.add_argument("--max-entries", type=int, default=1000)
    parser.add_argument(
        "--max-extracted-bytes", type=int, default=250 * 1024 * 1024
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        package = Path(args.package_path).expanduser().resolve(strict=True)
        with temporary_workspace(".cowork-plugin-validation-") as workspace:
            extraction_root = Path(workspace) / "package"
            entries, extracted_bytes = inspect_zip(
                package,
                extraction_root,
                max_entries=args.max_entries,
                max_extracted_bytes=args.max_extracted_bytes,
            )
            validation = validate_project(
                extraction_root,
                allow_oauth_placeholder=args.allow_oauth_placeholder,
                package_root_only=True,
            )
            if not args.skip_toolkit_validation:
                run_atk(
                    ["validate", "--package-file", str(package)],
                    args.atk_version,
                )
            print_result(
                {
                    "package_path": str(package),
                    "entries": entries,
                    "uncompressed_bytes": extracted_bytes,
                    "manifest_version": validation.manifest_version,
                    "version": validation.version,
                    "skills": validation.skills,
                    "connectors": validation.connectors,
                    "toolkit_validated": not args.skip_toolkit_validation,
                    "atk_version": (
                        None
                        if args.skip_toolkit_validation
                        else args.atk_version
                    ),
                    "status": "Passed",
                }
            )
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
