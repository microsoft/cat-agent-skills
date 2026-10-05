#!/usr/bin/env python3
"""Package and validate a Cowork plugin with Microsoft 365 Agents Toolkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cowork_plugin_utils import (
    ATK_VERSION,
    CoworkPluginError,
    print_result,
    run_atk,
    validate_project,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--output-path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        validation = validate_project(args.project_path)
        project = Path(validation.project_path)
        workflow = project / "m365agents.yml"
        if not workflow.is_file():
            raise CoworkPluginError(
                f"m365agents.yml is required for atk packaging: {workflow}"
            )
        manifest = Path(validation.manifest_path)
        output = (
            Path(args.output_path).expanduser()
            if args.output_path
            else manifest.parent / "build" / "appPackage.zip"
        ).resolve(strict=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        run_atk(
            [
                "package",
                "--manifest-file",
                str(manifest),
                "--output-package-file",
                str(output),
                "--output-folder",
                str(output.parent),
            ],
            excluded_roots=(project,),
        )
        run_atk(
            ["validate", "--package-file", str(output)],
            excluded_roots=(project,),
        )
        validate_project(project, package_path=output)
        print_result(
            {
                "project_path": str(project),
                "package_path": str(output),
                "bytes": output.stat().st_size,
                "atk_version": ATK_VERSION,
                "status": "Passed",
            }
        )
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
