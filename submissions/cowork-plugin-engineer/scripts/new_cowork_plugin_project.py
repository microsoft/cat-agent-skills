#!/usr/bin/env python3
"""Scaffold a validated Microsoft Copilot Cowork plugin project."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path

from cowork_plugin_utils import (
    CoworkPluginError,
    SKILL_NAME_PATTERN,
    print_result,
    read_json,
    validate_https,
    write_json,
)


def create_project(
    project_path: str | Path,
    *,
    plugin_name: str,
    short_description: str,
    full_description: str,
    developer_name: str,
    website_url: str,
    privacy_url: str,
    terms_of_use_url: str,
    skill_names: list[str],
    skill_descriptions: list[str],
    color_icon_path: str | Path,
    outline_icon_path: str | Path,
    dry_run: bool = False,
) -> dict[str, object]:
    required_text = (
        (plugin_name, "Plugin name"),
        (short_description, "Short description"),
        (full_description, "Full description"),
        (developer_name, "Developer name"),
    )
    for value, label in required_text:
        if not value.strip():
            raise CoworkPluginError(f"{label} must not be empty.")
    if len(skill_names) != len(skill_descriptions):
        raise CoworkPluginError(
            "Skill names and skill descriptions must have the same number "
            "of values."
        )
    if not skill_names:
        raise CoworkPluginError("At least one skill is required.")
    if len(skill_names) > 20:
        raise CoworkPluginError("Cowork supports at most 20 registered skills.")
    normalized_names: set[str] = set()
    for name in skill_names:
        if not SKILL_NAME_PATTERN.fullmatch(name):
            raise CoworkPluginError(
                f"Skill name must be lowercase kebab-case: {name}"
            )
        if name.casefold() in normalized_names:
            raise CoworkPluginError(f"Duplicate skill name: {name}")
        normalized_names.add(name.casefold())
    if any(not description.strip() for description in skill_descriptions):
        raise CoworkPluginError("Skill descriptions must not be empty.")
    for value, label in (
        (website_url, "website URL"),
        (privacy_url, "privacy URL"),
        (terms_of_use_url, "terms-of-use URL"),
    ):
        validate_https(value, f"Developer {label}")

    project = Path(project_path).expanduser().resolve(strict=False)
    if project.exists():
        raise CoworkPluginError(f"Project path already exists: {project}")
    color_icon = Path(color_icon_path).expanduser().resolve(strict=True)
    outline_icon = Path(outline_icon_path).expanduser().resolve(strict=True)
    if not color_icon.is_file() or not outline_icon.is_file():
        raise CoworkPluginError("Color and outline icon paths must be files.")

    template_path = (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "manifest.v1.28.template.json"
    )
    manifest = read_json(template_path, "manifest template")
    manifest_id = str(uuid.uuid4())
    manifest["id"] = manifest_id
    manifest["developer"] = {
        "name": developer_name,
        "websiteUrl": website_url,
        "privacyUrl": privacy_url,
        "termsOfUseUrl": terms_of_use_url,
    }
    manifest["name"] = {
        "short": plugin_name,
        "full": f"{plugin_name} for Copilot Cowork",
    }
    manifest["description"] = {
        "short": short_description,
        "full": full_description,
    }
    manifest["agentSkills"] = [
        {"folder": f"./skills/{name}"} for name in skill_names
    ]

    if not dry_run:
        app_package = project / "appPackage"
        app_package.mkdir(parents=True)
        shutil.copyfile(color_icon, app_package / "color.png")
        shutil.copyfile(outline_icon, app_package / "outline.png")
        write_json(app_package / "manifest.json", manifest)
        for name, description in zip(
            skill_names, skill_descriptions, strict=True
        ):
            skill_folder = app_package / "skills" / name
            skill_folder.mkdir(parents=True)
            quoted_description = json.dumps(description, ensure_ascii=False)
            (skill_folder / "SKILL.md").write_text(
                "---\n"
                f"name: {json.dumps(name)}\n"
                f"description: {quoted_description}\n"
                "---\n\n"
                f"# {name}\n\n"
                "Define the focused workflow, activation boundaries, required "
                "inputs, and output\nformat for this skill. Move detailed "
                "material into references/.\n",
                encoding="utf-8",
                newline="\n",
            )
        (project / "m365agents.yml").write_text(
            "version: v1.11\nenvironmentFolderPath: ./env\n",
            encoding="utf-8",
            newline="\n",
        )
        (project / "env").mkdir()
    return {
        "project_path": str(project),
        "manifest_id": manifest_id,
        "skills": len(skill_names),
        "status": "Previewed" if dry_run else "Created",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--plugin-name", required=True)
    parser.add_argument("--short-description", required=True)
    parser.add_argument("--full-description", required=True)
    parser.add_argument("--developer-name", required=True)
    parser.add_argument("--website-url", required=True)
    parser.add_argument("--privacy-url", required=True)
    parser.add_argument("--terms-of-use-url", required=True)
    parser.add_argument("--skill-name", action="append", required=True)
    parser.add_argument("--skill-description", action="append", required=True)
    parser.add_argument("--color-icon-path", required=True)
    parser.add_argument("--outline-icon-path", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print_result(
            create_project(
                args.project_path,
                plugin_name=args.plugin_name,
                short_description=args.short_description,
                full_description=args.full_description,
                developer_name=args.developer_name,
                website_url=args.website_url,
                privacy_url=args.privacy_url,
                terms_of_use_url=args.terms_of_use_url,
                skill_names=args.skill_name,
                skill_descriptions=args.skill_description,
                color_icon_path=args.color_icon_path,
                outline_icon_path=args.outline_icon_path,
                dry_run=args.dry_run,
            )
        )
        return 0
    except (CoworkPluginError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
