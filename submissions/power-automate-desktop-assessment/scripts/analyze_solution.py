from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Iterator
import xml.etree.ElementTree as ET


GUID_SUFFIX = re.compile(
    r"-[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)
API_ID_PATTERN = re.compile(
    r"/providers/Microsoft\.PowerApps/apis/([^/\"\\]+)",
    re.IGNORECASE,
)
SENSITIVE_KEY_PATTERNS = {
    "password": re.compile(r"password", re.IGNORECASE),
    "secret": re.compile(r"secret", re.IGNORECASE),
    "token": re.compile(r"token", re.IGNORECASE),
    "credential": re.compile(r"credential", re.IGNORECASE),
    "authorization": re.compile(r"authorization|bearer", re.IGNORECASE),
    "key": re.compile(
        r"(^|[-_])(api|access|private|client)?[-_]?key($|[-_])",
        re.IGNORECASE,
    ),
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8-sig") as stream:
        return json.load(stream)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def get_definition(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    properties = data.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    definition = properties.get("definition") or data.get("definition") or {}
    return definition if isinstance(definition, dict) else {}


def friendly_name(filename: str) -> str:
    stem = Path(filename).stem
    stem = GUID_SUFFIX.sub("", stem)
    return re.sub(r"[-_]+", " ", stem).strip()


def walk_actions(
    actions: object,
    *,
    prefix: str = "",
    foreach_depth: int = 0,
) -> Iterator[dict[str, object]]:
    if not isinstance(actions, dict):
        return

    for name, raw_action in actions.items():
        if not isinstance(raw_action, dict):
            continue

        action_type = str(raw_action.get("type") or "Unknown")
        current_path = f"{prefix}/{name}" if prefix else str(name)
        current_depth = foreach_depth + int(action_type.lower() == "foreach")
        yield {
            "path": current_path,
            "name": str(name),
            "type": action_type,
            "foreachDepth": current_depth,
            "runAfter": raw_action.get("runAfter")
            if isinstance(raw_action.get("runAfter"), dict)
            else {},
            "inputs": raw_action.get("inputs"),
            "raw": raw_action,
        }

        yield from walk_actions(
            raw_action.get("actions"),
            prefix=current_path,
            foreach_depth=current_depth,
        )

        else_block = raw_action.get("else")
        if isinstance(else_block, dict):
            yield from walk_actions(
                else_block.get("actions"),
                prefix=f"{current_path}/else",
                foreach_depth=current_depth,
            )

        cases = raw_action.get("cases")
        if isinstance(cases, dict):
            for case_name, case_value in cases.items():
                if isinstance(case_value, dict):
                    yield from walk_actions(
                        case_value.get("actions"),
                        prefix=f"{current_path}/case:{case_name}",
                        foreach_depth=current_depth,
                    )

        default_block = raw_action.get("default")
        if isinstance(default_block, dict):
            yield from walk_actions(
                default_block.get("actions"),
                prefix=f"{current_path}/default",
                foreach_depth=current_depth,
            )


def sensitive_keyword_classes(node: object) -> list[str]:
    matches: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                for keyword_class, pattern in SENSITIVE_KEY_PATTERNS.items():
                    if pattern.search(key_text):
                        matches.add(keyword_class)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(node)
    return sorted(matches)


def connector_names(data: object, definition: dict[str, object]) -> list[str]:
    connectors: set[str] = set()

    if isinstance(data, dict):
        properties = data.get("properties")
        if isinstance(properties, dict):
            references = properties.get("connectionReferences")
            if isinstance(references, dict):
                for reference in references.values():
                    if not isinstance(reference, dict):
                        continue
                    api = reference.get("api")
                    if isinstance(api, dict) and api.get("name"):
                        connectors.add(str(api["name"]))

    serialized = json.dumps(definition, ensure_ascii=False)
    connectors.update(API_ID_PATTERN.findall(serialized))
    return sorted(connectors)


def has_non_success_run_after(action: dict[str, object]) -> bool:
    run_after = action["runAfter"]
    if not isinstance(run_after, dict):
        return False
    for statuses in run_after.values():
        values = statuses if isinstance(statuses, list) else [statuses]
        if any(str(status).lower() != "succeeded" for status in values):
            return True
    return False


def has_retry_policy(action: dict[str, object]) -> bool:
    raw = action["raw"]
    if not isinstance(raw, dict):
        return False
    if isinstance(raw.get("retryPolicy"), dict):
        return True
    inputs = raw.get("inputs")
    if isinstance(inputs, dict) and isinstance(inputs.get("retryPolicy"), dict):
        return True
    runtime = raw.get("runtimeConfiguration")
    return isinstance(runtime, dict) and isinstance(runtime.get("retryPolicy"), dict)


def is_http_like(action: dict[str, object]) -> bool:
    action_type = str(action["type"]).lower()
    if action_type == "http":
        return True
    inputs = action["inputs"]
    if not isinstance(inputs, dict):
        return False
    host = inputs.get("host")
    if isinstance(host, dict):
        operation = str(host.get("operationId") or "")
        api_id = str(host.get("apiId") or "")
        return "http" in operation.lower() or "webcontents" in api_id.lower()
    return "uri" in inputs and "method" in inputs


def is_child_or_desktop_reference(action: dict[str, object]) -> bool:
    if str(action["type"]).lower() == "workflow":
        return True
    inputs = action["inputs"]
    if not isinstance(inputs, dict):
        return False
    host = inputs.get("host")
    if isinstance(host, dict) and "uiflow" in str(host.get("apiId") or "").lower():
        return True
    return False


def read_solution(root: Path) -> dict[str, object]:
    path = root / "solution.xml"
    if not path.is_file():
        raise FileNotFoundError(f"Required solution.xml not found under {root}")

    document = ET.parse(path).getroot()
    publisher = document.find(".//Publisher")
    missing_dependencies = document.findall(
        ".//MissingDependencies/MissingDependency"
    )
    return {
        "uniqueName": document.findtext(".//UniqueName") or "",
        "version": document.findtext(".//Version") or "",
        "managed": document.findtext(".//Managed") or "",
        "publisher": publisher.findtext("UniqueName")
        if publisher is not None
        else "",
        "rootComponentCount": len(document.findall(".//RootComponents/RootComponent")),
        "missingDependencyCount": len(missing_dependencies),
    }


def read_customizations(root: Path) -> dict[str, object]:
    path = root / "customizations.xml"
    if not path.is_file():
        return {
            "present": False,
            "file": "customizations.xml",
            "size": 0,
            "componentCounts": {},
        }

    document = ET.parse(path).getroot()
    element_counts = Counter(
        element.tag.rsplit("}", 1)[-1].casefold()
        for element in document.iter()
    )
    tracked_components = {
        "Entity": "entity",
        "Workflow": "workflow",
        "Role": "role",
        "OptionSet": "optionset",
        "WebResource": "webresource",
        "EntityRelationship": "entityrelationship",
    }
    return {
        "present": True,
        "file": "customizations.xml",
        "size": path.stat().st_size,
        "rootElement": document.tag.rsplit("}", 1)[-1],
        "componentCounts": {
            label: element_counts[normalized_name]
            for label, normalized_name in tracked_components.items()
            if element_counts[normalized_name]
        },
    }


def read_environment_variables(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    env_root = root / "environmentvariabledefinitions"
    if not env_root.is_dir():
        return result

    for path in sorted(env_root.rglob("environmentvariabledefinition.xml")):
        definition = ET.parse(path).getroot()
        label = definition.find("./displayname/label")
        default_value = definition.find("defaultvalue")
        result.append(
            {
                "file": path.relative_to(root).as_posix(),
                "schemaName": definition.attrib.get("schemaname")
                or path.parent.name,
                "displayName": label.attrib.get("description", "")
                if label is not None
                else "",
                "type": definition.findtext("type") or "",
                "secretStore": definition.findtext("secretstore") or "",
                "required": definition.findtext("isrequired") or "",
                "defaultValuePresent": default_value is not None
                and bool((default_value.text or "").strip()),
            }
        )
    return result


def read_desktop_binaries(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    binary_root = root / "desktopflowbinaries"
    if not binary_root.is_dir():
        return result

    for path in sorted(binary_root.rglob("*.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object in {path}")

        modules = data.get("ModuleReferences")
        screens = data.get("Screens")
        images = data.get("Images")
        connectors = data.get("ConnectorReferences")
        result.append(
            {
                "file": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "kind": path.name.split("_", 1)[0],
                "keys": sorted(str(key) for key in data),
                "moduleNames": sorted(
                    str(item.get("Name"))
                    for item in modules
                    if isinstance(item, dict) and item.get("Name")
                )
                if isinstance(modules, list)
                else [],
                "connectorCount": len(connectors)
                if isinstance(connectors, list)
                else 0,
                "screenCount": len(screens) if isinstance(screens, list) else 0,
                "imageCount": len(images) if isinstance(images, list) else 0,
            }
        )
    return result


def read_workflows(
    root: Path,
) -> tuple[list[dict[str, object]], Counter[str], Counter[str]]:
    result: list[dict[str, object]] = []
    connector_counts: Counter[str] = Counter()
    action_type_counts: Counter[str] = Counter()
    workflow_root = root / "Workflows"
    if not workflow_root.is_dir():
        return result, connector_counts, action_type_counts

    for path in sorted(workflow_root.rglob("*.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object in {path}")

        properties = data.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        definition = get_definition(data)
        actions = list(walk_actions(definition.get("actions")))
        triggers = definition.get("triggers")
        if not isinstance(triggers, dict):
            triggers = {}

        action_types = Counter(str(action["type"]) for action in actions)
        action_type_counts.update(action_types)
        connectors = connector_names(data, definition)
        connector_counts.update(connectors)

        non_success = [
            action for action in actions if has_non_success_run_after(action)
        ]
        retry_actions = [action for action in actions if has_retry_policy(action)]
        http_like = [action for action in actions if is_http_like(action)]
        child_or_desktop = [
            action for action in actions if is_child_or_desktop_reference(action)
        ]
        waits = [
            action
            for action in actions
            if str(action["type"]).lower() in {"wait", "until"}
            or re.search(r"\b(wait|delay|espera)\b", str(action["name"]), re.I)
        ]

        relative_file = path.relative_to(root).as_posix()
        result.append(
            {
                "file": relative_file,
                "name": str(
                    properties.get("displayName")
                    or properties.get("name")
                    or data.get("name")
                    or friendly_name(path.name)
                ),
                "state": str(
                    properties.get("state") or properties.get("flowState") or ""
                ),
                "triggers": len(triggers),
                "actions": len(actions),
                "foreach": action_types.get("Foreach", 0),
                "maxForeachDepth": max(
                    (int(action["foreachDepth"]) for action in actions),
                    default=0,
                ),
                "scopes": action_types.get("Scope", 0),
                "variables": sum(
                    action_types.get(action_type, 0)
                    for action_type in (
                        "InitializeVariable",
                        "SetVariable",
                        "AppendToArrayVariable",
                        "AppendToStringVariable",
                        "IncrementVariable",
                        "DecrementVariable",
                    )
                ),
                "compose": action_types.get("Compose", 0),
                "condition": action_types.get("If", 0),
                "switch": action_types.get("Switch", 0),
                "httpLike": len(http_like),
                "terminate": action_types.get("Terminate", 0),
                "runAfterNonSuccess": len(non_success),
                "retryPolicy": len(retry_actions),
                "desktopOrChildRefs": len(child_or_desktop),
                "waitOrDelay": len(waits),
                "connectors": connectors,
                "types": dict(sorted(action_types.items())),
                "sensitiveKeywordClasses": sensitive_keyword_classes(definition),
                "runAfterSamples": [
                    str(action["path"]) for action in non_success[:5]
                ],
            }
        )

    return result, connector_counts, action_type_counts


def analyze_solution(root: Path) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Extracted solution directory not found: {root}")

    workflows, connectors, action_types = read_workflows(root)
    environment_variables = read_environment_variables(root)
    desktop_binaries = read_desktop_binaries(root)
    return {
        "schemaVersion": 1,
        "solution": read_solution(root),
        "customizations": read_customizations(root),
        "environmentVariables": environment_variables,
        "desktopBinaries": desktop_binaries,
        "workflows": workflows,
        "connectors": dict(sorted(connectors.items())),
        "actionTypes": dict(sorted(action_types.items())),
        "totals": {
            "workflowCount": len(workflows),
            "totalActions": sum(int(item["actions"]) for item in workflows),
            "environmentVariableCount": len(environment_variables),
            "desktopBinaryJsonCount": len(desktop_binaries),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate static metrics for an extracted Power Platform solution."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    metrics = analyze_solution(args.root)
    write_json(args.output, metrics)
    print(
        json.dumps(
            {
                "metricsPath": str(args.output.resolve()),
                "workflowCount": metrics["totals"]["workflowCount"],
                "totalActions": metrics["totals"]["totalActions"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
