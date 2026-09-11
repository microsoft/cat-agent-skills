#!/usr/bin/env python3
"""Set a Cowork connector OAuth reference and optionally bump its version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cowork_plugin_utils import (
    CoworkPluginError,
    SEMVER_PATTERN,
    as_list,
    as_object,
    get_property,
    is_oauth_placeholder,
    print_result,
    read_json,
    write_json,
)


def set_oauth_reference(
    project_path: str | Path,
    connector_id: str,
    oauth_configuration_id: str,
    *,
    no_version_bump: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    if is_oauth_placeholder(oauth_configuration_id, connector_id):
        raise CoworkPluginError(
            "OAuth configuration ID appears to be a placeholder. Use the "
            "generated Teams Developer Portal OAuth client registration ID."
        )
    project = Path(project_path).expanduser().resolve(strict=True)
    manifest_path = project / "appPackage" / "manifest.json"
    if not manifest_path.is_file():
        manifest_path = project / "manifest.json"
    if not manifest_path.is_file():
        raise CoworkPluginError(
            f"manifest.json was not found under {project}"
        )
    manifest = as_object(read_json(manifest_path, "manifest.json"), "manifest")
    connectors = as_list(get_property(manifest, "agentConnectors"), "agentConnectors")
    matches = [
        as_object(connector, "agentConnectors entry")
        for connector in connectors
        if isinstance(connector, dict)
        and str(connector.get("id", "")).casefold() == connector_id.casefold()
    ]
    if len(matches) != 1:
        raise CoworkPluginError(
            f"Expected one connector with ID '{connector_id}'; found "
            f"{len(matches)}."
        )
    tool_source = as_object(
        get_property(matches[0], "toolSource"), "connector toolSource"
    )
    remote = as_object(
        get_property(tool_source, "remoteMcpServer"), "remoteMcpServer"
    )
    authorization = as_object(
        get_property(remote, "authorization"), "authorization"
    )
    if get_property(authorization, "type") != "OAuthPluginVault":
        raise CoworkPluginError(
            f"Connector '{connector_id}' does not use OAuthPluginVault."
        )
    version = get_property(manifest, "version")
    if not no_version_bump:
        match = SEMVER_PATTERN.fullmatch(version or "")
        if not match:
            raise CoworkPluginError(
                f"Manifest version is not semantic: {version}"
            )
        version = (
            f"{match.group(1)}.{match.group(2)}.{int(match.group(3)) + 1}"
        )
        manifest["version"] = version
    authorization["referenceId"] = oauth_configuration_id
    if not dry_run:
        write_json(manifest_path, manifest)
    return {
        "manifest_path": str(manifest_path),
        "connector_id": connector_id,
        "version": version,
        "updated": not dry_run,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--connector-id", required=True)
    parser.add_argument("--oauth-configuration-id", required=True)
    parser.add_argument("--no-version-bump", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print_result(
            set_oauth_reference(
                args.project_path,
                args.connector_id,
                args.oauth_configuration_id,
                no_version_bump=args.no_version_bump,
                dry_run=args.dry_run,
            )
        )
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
