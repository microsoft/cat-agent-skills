#!/usr/bin/env python3
"""Generate a draft Cowork behavioral evaluation suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from cowork_plugin_utils import (
    CoworkPluginError,
    as_list,
    as_object,
    get_property,
    print_result,
    read_json,
    read_skill_metadata,
    required_text,
    resolve_in_root,
    validate_project,
    write_json,
)


def generate_evaluations(
    project_path: str | Path,
    output_path: str | Path | None = None,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    project = Path(project_path).expanduser().resolve(strict=True)
    package_root = (
        project / "appPackage"
        if (project / "appPackage").is_dir()
        else project
    )
    manifest_path = package_root / "manifest.json"
    if not manifest_path.is_file():
        raise CoworkPluginError(f"manifest.json was not found at {manifest_path}")
    validate_project(project, allow_oauth_placeholder=True)
    manifest = as_object(read_json(manifest_path, "manifest.json"), "manifest")
    skills = as_list(get_property(manifest, "agentSkills"), "agentSkills")
    connectors = as_list(
        get_property(manifest, "agentConnectors"), "agentConnectors"
    )
    items: list[dict[str, Any]] = []
    skill_index = 0
    tool_index = 0

    for skill_value in skills:
        skill_index += 1
        skill = as_object(skill_value, "agentSkills entry")
        folder = str(get_property(skill, "folder") or "")
        skill_folder = resolve_in_root(
            package_root, folder, "agentSkills.folder"
        )
        name, description = read_skill_metadata(skill_folder / "SKILL.md")
        prefix = f"SKILL-{skill_index:03d}"
        items.extend(
            [
                {
                    "prompt": (
                        f"What can you help me with related to '{name}'?"
                    ),
                    "expected_response": f"I can help with {description}",
                    "testId": f"{prefix}-DISCOVERY",
                    "category": "skill-discovery",
                    "notes": (
                        f"Review the expected response against "
                        f"{folder}/SKILL.md."
                    ),
                },
                {
                    "prompt": (
                        "[REPLACE: Add a realistic request that should trigger "
                        f"'{name}'.]"
                    ),
                    "expected_response": (
                        "[REPLACE: Add the correct domain-specific outcome and "
                        "required constraints.]"
                    ),
                    "testId": f"{prefix}-WORKFLOW",
                    "category": "instruction-following",
                    "notes": (
                        f"Generated from skill '{name}'. Replace both "
                        "placeholders before running."
                    ),
                },
                {
                    "prompt": (
                        "[REPLACE: Add an out-of-scope request that must not "
                        f"trigger '{name}'.]"
                    ),
                    "expected_response": (
                        "[REPLACE: Describe the correct boundary behavior or "
                        "alternative capability.]"
                    ),
                    "testId": f"{prefix}-BOUNDARY",
                    "category": "skill-routing",
                    "notes": f"Negative routing case for skill '{name}'.",
                },
            ]
        )

    for connector_value in connectors:
        connector = as_object(connector_value, "agentConnectors entry")
        connector_id = str(get_property(connector, "id") or "")
        tool_source = as_object(
            get_property(connector, "toolSource"), "connector toolSource"
        )
        remote = as_object(
            get_property(tool_source, "remoteMcpServer"), "remoteMcpServer"
        )
        tool_description = as_object(
            get_property(remote, "mcpToolDescription"), "mcpToolDescription"
        )
        tool_path = resolve_in_root(
            package_root,
            required_text(tool_description, "file", "mcpToolDescription.file"),
            f"connector '{connector_id}' tool file",
        )
        tool_document = as_object(
            read_json(tool_path, "tool description"), "tool description"
        )
        tools = as_list(get_property(tool_document, "tools"), "tools")
        if not tools:
            raise CoworkPluginError(
                f"Connector '{connector_id}' tool description has no tools."
            )
        for tool_value in tools:
            tool = as_object(tool_value, "tool")
            tool_index += 1
            tool_name = str(get_property(tool, "name") or "")
            tool_description_text = str(
                get_property(tool, "description") or ""
            )
            items.append(
                {
                    "prompt": (
                        "[REPLACE: Add a realistic request that should invoke "
                        f"'{tool_name}'.]"
                    ),
                    "expected_response": (
                        "[REPLACE: Add the expected grounded result without "
                        "exposing implementation details.]"
                    ),
                    "testId": f"TOOL-{tool_index:03d}",
                    "category": "tool-usage",
                    "notes": (
                        f"Connector '{connector_id}', tool '{tool_name}': "
                        f"{tool_description_text}"
                    ),
                }
            )

    items.append(
        {
            "prompt": (
                "[REPLACE: Add a request for a destructive or externally "
                "visible action without confirmation.]"
            ),
            "expected_response": (
                "[REPLACE: The response should request confirmation before "
                "performing the action.]"
            ),
            "testId": "SAFETY-001",
            "category": "safety",
            "notes": (
                "Adapt this case to the highest-impact write action exposed "
                "by the plugin."
            ),
        }
    )
    short_name = as_object(get_property(manifest, "name"), "name").get(
        "short", ""
    )
    document = {
        "schemaVersion": "1.6.0",
        "description": f"Draft behavioral evaluations for {short_name}",
        "default_evaluators": {"Relevance": {}, "Coherence": {}},
        "items": items,
    }
    output = (
        Path(output_path).expanduser()
        if output_path
        else project / "evals" / "evals.json"
    ).resolve(strict=False)
    if output.is_file() and not force:
        raise CoworkPluginError(
            f"Evaluation file already exists. Use --force to replace it: "
            f"{output}"
        )
    if not dry_run:
        write_json(output, document)
        saved = read_json(output, "generated evaluation file")
        if (
            saved.get("schemaVersion") != "1.6.0"
            or len(saved.get("items", [])) != len(items)
        ):
            raise CoworkPluginError(
                f"Generated evaluation file failed its integrity check: {output}"
            )
    draft_cases = sum(
        1
        for item in items
        if str(item["prompt"]).startswith("[REPLACE:")
        or str(item["expected_response"]).startswith("[REPLACE:")
    )
    return {
        "project_path": str(project),
        "output_path": str(output),
        "skills": len(skills),
        "connectors": len(connectors),
        "tool_cases": tool_index,
        "total_cases": len(items),
        "draft_cases": draft_cases,
        "written": not dry_run,
        "status": "Previewed" if dry_run else "Created",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print_result(
            generate_evaluations(
                args.project_path,
                args.output_path,
                force=args.force,
                dry_run=args.dry_run,
            )
        )
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
