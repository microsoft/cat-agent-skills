#!/usr/bin/env python3
"""
Ingest a Copilot Studio or Azure AI Foundry agent export into normalised JSON.

Handles:
  - Copilot Studio solution .zip (unpacked customizations.xml / bot definitions)
  - Copilot Studio agent YAML
  - Azure AI Foundry agent definition (JSON/YAML)
  - A directory containing any of the above

Design principle: degrade gracefully and report what could not be read. A partial
parse with honest gaps is far more useful than a confident wrong one, because every
downstream finding inherits the ingestion's errors.

Usage:
    python ingest_agent.py <path> --out normalized.json
    python ingest_agent.py <path> --out normalized.json --verbose
"""

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.0"


# --------------------------------------------------------------------------
# Normalised output shape
# --------------------------------------------------------------------------

def empty_model() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {"path": None, "format": None, "parsed_files": []},
        "agent": {
            "name": None,
            "platform": None,          # copilot_studio | foundry | unknown
            "orchestration_mode": None,  # classic | generative | unknown
            "description": None,
        },
        "topics": [],                  # see topic shape below
        "knowledge_sources": [],
        "tools": [],
        "variables": [],
        "configuration": {
            "fallback_configured": None,
            "escalation_configured": None,
            "content_moderation": None,
            "session_timeout_minutes": None,
            "welcome_message": None,
            "auth_model": None,
        },
        "foundry": {
            "model": None,
            "temperature": None,
            "index_bindings": [],
            "eval_configured": None,
        },
        "parse_report": {
            "complete": False,
            "warnings": [],
            "unreadable": [],
            "fields_not_in_export": [
                "scale.conversations_per_month",
                "scale.peak_concurrency",
                "scale.latency_p95_target_ms",
                "governance.data_residency",
                "governance.content_safety_tier",
                "governance.auditability",
                "governance.budget_monthly",
                "knowledge.volume_gb",
                "model_control.*",
            ],
        },
    }


def empty_topic(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "trigger_phrases": [],
        "node_count": 0,
        "is_generative": None,
        "grounding_enabled": None,
        "knowledge_sources": [],
        "calls_topics": [],
        "variables_set": [],
        "variables_read": [],
        "has_slot_filling": False,
        "has_interruption_handling": False,
        "is_system_topic": False,
        "tools_invoked": [],
        "has_transfer_action": False,
    }


# Real Copilot Studio action kind is SearchAndSummarizeContent; older/agentic vintages also emit GenerativeAnswers.
GENERATIVE_MARKERS = ("SearchAndSummarizeContent", "GenerativeAnswers", "generativeAnswers")
TRANSFER_MARKERS = ("TransferConversation", "EscalateToHuman")


def _has_marker(text: str, markers: tuple) -> bool:
    return any(m in text for m in markers)


# --------------------------------------------------------------------------
# Format detection
# --------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return "solution_zip"
    if suffix in (".yaml", ".yml"):
        return "agent_yaml"
    if suffix == ".json":
        return "json_definition"
    if suffix == ".xml":
        return "customizations_xml"
    return "unknown"


# --------------------------------------------------------------------------
# YAML loading (optional dependency)
# --------------------------------------------------------------------------

def load_yaml(text: str, model: Dict[str, Any], label: str) -> Optional[Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        model["parse_report"]["warnings"].append(
            f"PyYAML not available; could not parse {label}. "
            "Install pyyaml or supply a JSON export."
        )
        return None
    try:
        return yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        model["parse_report"]["warnings"].append(f"YAML parse failed for {label}: {exc}")
        return None


# --------------------------------------------------------------------------
# Copilot Studio: solution zip
# --------------------------------------------------------------------------

# Real Copilot Studio solutions ship as: solution.xml + bots/<schema>/{bot.xml,configuration.json}
# + botcomponents/<schema>.(topic|action|agent|gpt).<Name>/{botcomponent.xml, data}. The `data` file
# has no extension and carries the YAML topic body — filename hints, not suffix, drive the walk.
YAML_EXTS = (".yaml", ".yml")
COMPONENT_FOLDER_RE = re.compile(r"^[\w\-]+\.(topic|action|agent|gpt)\.(.+)$", re.I)


def _is_solution_layout(names: List[str]) -> bool:
    """Detect the Power Platform solution shape: presence of any botcomponents/ entry."""
    for n in names:
        low = n.lower().replace("\\", "/")
        if "botcomponents/" in low or low.startswith("botcomponents/"):
            return True
    return False


def parse_bot_xml(text: str, model: Dict[str, Any]) -> None:
    """Extract the friendly agent name from bots/<schema>/bot.xml (<name>...</name>)."""
    m = re.search(r"<name>(.*?)</name>", text, re.S | re.I)
    if m:
        model["agent"]["name"] = m.group(1).strip()


def parse_bot_configuration_json(text: str, model: Dict[str, Any], label: str) -> None:
    """Read bot-level settings (content moderation, recognizer kind) from configuration.json."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        model["parse_report"]["warnings"].append(
            f"configuration.json parse failed ({label}): {exc}"
        )
        return
    if not isinstance(data, dict):
        return
    ai = data.get("aISettings") if isinstance(data.get("aISettings"), dict) else {}
    cm = ai.get("contentModeration")
    if cm:
        model["configuration"]["content_moderation"] = cm
    recognizer = data.get("recognizer") if isinstance(data.get("recognizer"), dict) else {}
    kind = recognizer.get("$kind") or recognizer.get("kind")
    if isinstance(kind, str):
        model["agent"]["orchestration_mode"] = (
            "generative" if "generative" in kind.lower() else "classic"
        )


def _read_sidecar_name(loader, model: Dict[str, Any], label: str):
    """Return (display_name, description) from a botcomponent.xml sidecar, or (None, None)."""
    try:
        text = loader()
    except Exception as exc:  # noqa: BLE001
        model["parse_report"]["unreadable"].append(f"{label}: {exc}")
        return None, None
    model["source"]["parsed_files"].append(label)
    name_m = re.search(r"<name>(.*?)</name>", text, re.S | re.I)
    desc_m = re.search(r"<description>(.*?)</description>", text, re.S | re.I)
    return (
        name_m.group(1).strip() if name_m else None,
        desc_m.group(1).strip() if desc_m else None,
    )


def _ingest_solution_entries(
    entries: List[Any],
    model: Dict[str, Any],
    verbose: bool,
) -> None:
    """Solution-aware walker shared by zip and directory ingest.

    entries: list of (rel_path, text_loader). rel_path uses forward slashes.
    """
    component_folders: Dict[str, Dict[str, Any]] = {}

    for rel, loader in entries:
        norm = rel.replace("\\", "/")
        parts = norm.split("/")
        low = norm.lower()

        # botcomponents/<schema>.<kind>.<Name>/<file>
        if len(parts) >= 3 and parts[0].lower() == "botcomponents":
            folder = parts[1]
            filename = parts[-1]
            m = COMPONENT_FOLDER_RE.match(folder)
            if m:
                bucket = component_folders.setdefault(folder, {
                    "__kind": m.group(1).lower(),
                    "__tail": m.group(2),
                })
                bucket[filename.lower()] = loader
            continue

        # bots/<schema>/{bot.xml, configuration.json}
        if len(parts) >= 3 and parts[0].lower() == "bots":
            filename = parts[-1].lower()
            try:
                text = loader()
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"{rel}: {exc}")
                continue
            model["source"]["parsed_files"].append(rel)
            if filename == "bot.xml":
                parse_bot_xml(text, model)
            elif filename == "configuration.json":
                parse_bot_configuration_json(text, model, rel)
            continue

        if low.endswith("solution.xml"):
            try:
                text = loader()
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"{rel}: {exc}")
                continue
            model["source"]["parsed_files"].append(rel)
            # bot.xml is the source of truth for the friendly name; only fill from solution.xml if empty.
            m = re.search(r"<UniqueName>(.*?)</UniqueName>", text, re.S)
            if m and not model["agent"]["name"]:
                model["agent"]["name"] = m.group(1).strip()
            continue

        if low.endswith("customizations.xml"):
            try:
                text = loader()
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"{rel}: {exc}")
                continue
            model["source"]["parsed_files"].append(rel)
            parse_customizations(text, model)
            continue

    for folder, files in component_folders.items():
        kind = files["__kind"]
        tail = files["__tail"]
        data_loader = files.get("data")
        sidecar_loader = files.get("botcomponent.xml")
        sidecar_label = f"botcomponents/{folder}/botcomponent.xml"
        display_name, description = (None, None)
        if sidecar_loader is not None:
            display_name, description = _read_sidecar_name(sidecar_loader, model, sidecar_label)

        if kind == "topic":
            if data_loader is None:
                if display_name:
                    topic = empty_topic(display_name)
                    topic["is_system_topic"] = (
                        _looks_like_system_topic(tail) or _looks_like_system_topic(display_name)
                    )
                    _merge_topic(model, topic)
                continue
            try:
                body_text = data_loader()
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"botcomponents/{folder}/data: {exc}")
                continue
            data_label = f"botcomponents/{folder}/data"
            model["source"]["parsed_files"].append(data_label)
            before = len(model["topics"])
            parse_topic_yaml(body_text, data_label, model, verbose)
            if len(model["topics"]) > before:
                added = model["topics"][-1]
                # Sidecar has the friendly name (e.g. "Conversational boosting"); YAML rarely does.
                if display_name and added["name"] in ("data", Path(data_label).stem):
                    added["name"] = display_name
                if _looks_like_system_topic(tail):
                    added["is_system_topic"] = True
            continue

        if kind == "action":
            name = display_name or tail
            tool = {"name": name, "type": "connector_action", "description": description}
            if tool not in model["tools"]:
                model["tools"].append(tool)
            continue

        # agent/gpt components: record parsed sidecar; body isn't a topic.
        if data_loader is not None:
            try:
                data_loader()  # touch the loader so any read error is surfaced
                model["source"]["parsed_files"].append(f"botcomponents/{folder}/data")
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(
                    f"botcomponents/{folder}/data: {exc}"
                )


def ingest_solution_zip(path: Path, model: Dict[str, Any], verbose: bool) -> None:
    model["source"]["format"] = "copilot_studio_solution_zip"
    model["agent"]["platform"] = "copilot_studio"

    try:
        zf = zipfile.ZipFile(path)
    except Exception as exc:  # noqa: BLE001
        model["parse_report"]["unreadable"].append(f"{path.name}: {exc}")
        return

    with zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if verbose:
            print(f"[ingest] {len(names)} entries in archive", file=sys.stderr)

        if _is_solution_layout(names):
            entries = [(n, (lambda name=n: zf.read(name).decode("utf-8", errors="replace"))) for n in names]
            _ingest_solution_entries(entries, model, verbose)
            return

        # Loose YAML fallback for older / non-solution archives.
        for n in names:
            low = n.lower()
            if low.endswith("solution.xml"):
                try:
                    text = zf.read(n).decode("utf-8", errors="replace")
                    model["source"]["parsed_files"].append(n)
                    m = re.search(r"<UniqueName>(.*?)</UniqueName>", text, re.S)
                    if m and not model["agent"]["name"]:
                        model["agent"]["name"] = m.group(1).strip()
                except Exception as exc:  # noqa: BLE001
                    model["parse_report"]["unreadable"].append(f"{n}: {exc}")

        for n in [x for x in names if x.lower().endswith(YAML_EXTS)]:
            try:
                text = zf.read(n).decode("utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"{n}: {exc}")
                continue
            model["source"]["parsed_files"].append(n)
            parse_topic_yaml(text, n, model, verbose)

        for n in [x for x in names if x.lower().endswith("customizations.xml")]:
            try:
                text = zf.read(n).decode("utf-8", errors="replace")
                model["source"]["parsed_files"].append(n)
                parse_customizations(text, model)
            except Exception as exc:  # noqa: BLE001
                model["parse_report"]["unreadable"].append(f"{n}: {exc}")


def parse_customizations(text: str, model: Dict[str, Any]) -> None:
    """Extract what we can from customizations.xml without a full XML schema."""
    if model["agent"]["name"] is None:
        m = re.search(r"<botname>(.*?)</botname>", text, re.S | re.I)
        if m:
            model["agent"]["name"] = m.group(1).strip()

    # Knowledge source references
    for m in re.finditer(r"<knowledgesource[^>]*name=[\"'](.*?)[\"']", text, re.I):
        src = {"name": m.group(1), "type": "unknown", "scope": None}
        if src not in model["knowledge_sources"]:
            model["knowledge_sources"].append(src)


# --------------------------------------------------------------------------
# Copilot Studio: topic YAML
# --------------------------------------------------------------------------

def parse_topic_yaml(text: str, label: str, model: Dict[str, Any], verbose: bool) -> None:
    data = load_yaml(text, model, label)
    if data is None:
        # Regex fallback so a missing PyYAML does not zero out the analysis
        parse_topic_regex(text, label, model)
        return
    if not isinstance(data, dict):
        return

    name = (
        data.get("displayName")
        or data.get("name")
        or Path(label).stem
    )
    topic = empty_topic(str(name))
    topic["is_system_topic"] = _looks_like_system_topic(str(name))

    # Trigger phrases appear under several shapes across export vintages
    trigger = data.get("beginDialog", {}) if isinstance(data.get("beginDialog"), dict) else {}
    phrase_sources = [
        data.get("triggerQueries"),
        data.get("trigger", {}).get("triggerQueries") if isinstance(data.get("trigger"), dict) else None,
        trigger.get("triggerQueries"),
        data.get("intent", {}).get("triggerQueries") if isinstance(data.get("intent"), dict) else None,
    ]
    for ps in phrase_sources:
        if isinstance(ps, list):
            for p in ps:
                if isinstance(p, str) and p.strip():
                    topic["trigger_phrases"].append(p.strip())

    body = json.dumps(data)
    topic["node_count"] = _count_nodes(data)
    topic["is_generative"] = _has_marker(body, GENERATIVE_MARKERS)
    topic["grounding_enabled"] = topic["is_generative"]
    topic["has_slot_filling"] = "Question" in body or "slotFilling" in body
    topic["has_interruption_handling"] = (
        "allowInterruption" in body or "interruption" in body.lower()
    )
    topic["has_transfer_action"] = _has_marker(body, TRANSFER_MARKERS)
    # Sets come from slot-filling (variable: Topic.X), Power Fx assignment (Topic.X = ...), and Power Fx Set(Topic.X, ...).
    set_slot = re.findall(r'"variable"\s*:\s*"Topic\.(\w+)"', body)
    set_assign = re.findall(r"Topic\.(\w+)\s*=(?!=)", body)
    set_powerfx = re.findall(r"Set\s*\(\s*Topic\.(\w+)", body)
    topic["variables_set"] = sorted(set(set_slot) | set(set_assign) | set(set_powerfx))
    read_scan = re.sub(r'"variable"\s*:\s*"Topic\.\w+"', " ", body)
    read_scan = re.sub(r"Topic\.(\w+)\s*=(?!=)", " ", read_scan)
    read_scan = re.sub(r"Set\s*\(\s*Topic\.\w+", " ", read_scan)
    topic["variables_read"] = sorted(set(re.findall(r"Topic\.(\w+)", read_scan)))
    calls = set(re.findall(r"BeginDialog[\"']?\s*:\s*[\"']([\w\.]+)", body))
    # RedirectDialog and BeginDialog action shapes carry the target under a "dialog" field.
    calls.update(re.findall(r'"dialog"\s*:\s*"([^"]+)"', body))
    topic["calls_topics"] = sorted(calls)

    _merge_topic(model, topic)
    if verbose:
        print(f"[ingest] topic: {topic['name']} "
              f"({len(topic['trigger_phrases'])} phrases, {topic['node_count']} nodes)",
              file=sys.stderr)


def parse_topic_regex(text: str, label: str, model: Dict[str, Any]) -> None:
    """Minimal fallback when YAML parsing is unavailable."""
    name_m = re.search(r"displayName:\s*(.+)", text)
    name = name_m.group(1).strip().strip("\"'") if name_m else Path(label).stem
    topic = empty_topic(name)
    topic["is_system_topic"] = _looks_like_system_topic(name)

    block = re.search(r"triggerQueries:\s*((?:\s*-\s*.+\n?)+)", text)
    if block:
        for line in block.group(1).splitlines():
            p = line.strip().lstrip("-").strip().strip("\"'")
            if p:
                topic["trigger_phrases"].append(p)

    topic["node_count"] = len(re.findall(r"^\s*-\s*kind:", text, re.M))
    topic["is_generative"] = _has_marker(text, GENERATIVE_MARKERS)
    topic["grounding_enabled"] = topic["is_generative"]
    topic["has_slot_filling"] = "kind: Question" in text
    topic["has_interruption_handling"] = "allowInterruption" in text
    topic["has_transfer_action"] = _has_marker(text, TRANSFER_MARKERS)
    slot_sets = set(re.findall(r"variable:\s*Topic\.(\w+)", text))
    powerfx_sets = set(re.findall(r"Set\s*\(\s*Topic\.(\w+)", text))
    topic["variables_set"] = sorted(slot_sets | powerfx_sets)
    read_scan = re.sub(r"variable:\s*Topic\.\w+", " ", text)
    read_scan = re.sub(r"Set\s*\(\s*Topic\.\w+", " ", read_scan)
    topic["variables_read"] = sorted(set(re.findall(r"Topic\.(\w+)", read_scan)))
    topic["calls_topics"] = sorted(set(re.findall(r"dialog:\s*([\w\.]+)", text)))

    _merge_topic(model, topic)


def _looks_like_system_topic(name: str) -> bool:
    n = name.lower().replace(" ", "").replace("_", "")
    return any(k in n for k in (
        "fallback", "escalate", "escalation", "greeting", "goodbye",
        "startover", "endofconversation", "signin", "resetconversation",
        "multipletopicsmatched", "conversationstart", "onerror",
    ))


def _count_nodes(data: Any) -> int:
    count = 0
    if isinstance(data, dict):
        if "kind" in data:
            count += 1
        for v in data.values():
            count += _count_nodes(v)
    elif isinstance(data, list):
        for item in data:
            count += _count_nodes(item)
    return count


def _merge_topic(model: Dict[str, Any], topic: Dict[str, Any]) -> None:
    for existing in model["topics"]:
        if existing["name"] == topic["name"]:
            # Merge rather than duplicate — exports often split one topic
            existing["trigger_phrases"] = sorted(
                set(existing["trigger_phrases"]) | set(topic["trigger_phrases"])
            )
            existing["node_count"] = max(existing["node_count"], topic["node_count"])
            return
    model["topics"].append(topic)


# --------------------------------------------------------------------------
# Foundry agent definition
# --------------------------------------------------------------------------

def ingest_foundry(text: str, model: Dict[str, Any], label: str) -> None:
    model["source"]["format"] = "foundry_agent_definition"
    model["agent"]["platform"] = "foundry"

    data: Any = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = load_yaml(text, model, label)
    if not isinstance(data, dict):
        model["parse_report"]["unreadable"].append(label)
        return

    model["source"]["parsed_files"].append(label)
    model["agent"]["name"] = data.get("name") or data.get("id")
    model["agent"]["description"] = data.get("description")
    model["foundry"]["model"] = data.get("model") or data.get("model_deployment")
    model["foundry"]["temperature"] = data.get("temperature")
    model["foundry"]["eval_configured"] = bool(data.get("evaluation") or data.get("evaluators"))

    for tool in data.get("tools", []) or []:
        if isinstance(tool, dict):
            model["tools"].append({
                "name": tool.get("function", {}).get("name") or tool.get("name"),
                "type": tool.get("type"),
                "description": (tool.get("function", {}) or {}).get("description")
                               or tool.get("description"),
            })

    for res in (data.get("tool_resources") or {}).get("azure_ai_search", {}).get("indexes", []) or []:
        if isinstance(res, dict):
            model["foundry"]["index_bindings"].append(res.get("index_name"))


# --------------------------------------------------------------------------
# Configuration derivation
# --------------------------------------------------------------------------

def derive_configuration(model: Dict[str, Any]) -> None:
    """Infer config presence from parsed topics.

    Absence of evidence is recorded as False rather than None only where the
    export would reliably contain the item if configured — otherwise the
    downstream CONFIG rules would fire on a parsing gap rather than a real
    misconfiguration.
    """
    names = [t["name"].lower() for t in model["topics"]]
    joined = " ".join(names)

    if model["topics"]:
        model["configuration"]["fallback_configured"] = "fallback" in joined
        # Action-kind evidence is the source of truth; topic-name match stays as a lower-confidence fallback.
        model["configuration"]["escalation_configured"] = (
            any(t.get("has_transfer_action") for t in model["topics"])
            or "escalate" in joined
            or "escalation" in joined
        )
        model["configuration"]["welcome_message"] = (
            "greeting" in joined or "conversationstart" in joined.replace(" ", "")
        )

    if model["agent"]["orchestration_mode"] is None and model["topics"]:
        generative = sum(1 for t in model["topics"] if t.get("is_generative"))
        model["agent"]["orchestration_mode"] = (
            "generative" if generative > len(model["topics"]) / 3 else "classic"
        )

    # Aggregate variables
    seen = {}
    for t in model["topics"]:
        for v in t["variables_set"]:
            seen.setdefault(v, {"name": v, "set_in": [], "read_in": []})["set_in"].append(t["name"])
        for v in t["variables_read"]:
            seen.setdefault(v, {"name": v, "set_in": [], "read_in": []})["read_in"].append(t["name"])
    model["variables"] = list(seen.values())

    parsed = len(model["source"]["parsed_files"])
    model["parse_report"]["complete"] = (
        parsed > 0
        and bool(model["topics"] or model["foundry"]["model"])
        and not model["parse_report"]["unreadable"]
    )

    if not model["topics"] and model["agent"]["platform"] == "copilot_studio":
        model["parse_report"]["warnings"].append(
            "No topics were extracted. The export layout may differ from expected "
            "shapes. Fall back to self-report mode for topic-level findings."
        )


# --------------------------------------------------------------------------
# Entry
# --------------------------------------------------------------------------

def ingest(path: Path, verbose: bool) -> Dict[str, Any]:
    model = empty_model()
    model["source"]["path"] = str(path)
    fmt = detect_format(path)

    if fmt == "solution_zip":
        ingest_solution_zip(path, model, verbose)
    elif fmt == "agent_yaml":
        text = path.read_text(encoding="utf-8", errors="replace")

        # Heuristic: Foundry agent definitions often have top-level 'model'/'model_deployment' and 'tools'.
        # Prefer failing with an explicit warning over mis-parsing as a Copilot Studio topic.
        looks_like_foundry = (
            re.search(r"^\s*(model|model_deployment)\s*:", text, re.M)
            and re.search(r"^\s*tools\s*:", text, re.M)
        )

        if looks_like_foundry:
            ingest_foundry(text, model, path.name)
        else:
            model["source"]["format"] = "copilot_studio_agent_yaml"
            model["agent"]["platform"] = "copilot_studio"
            model["source"]["parsed_files"].append(path.name)
            parse_topic_yaml(text, path.name, model, verbose)
        text = path.read_text(encoding="utf-8", errors="replace")
        ingest_foundry(text, model, path.name)
    elif fmt == "customizations_xml":
        text = path.read_text(encoding="utf-8", errors="replace")
        model["source"]["format"] = "customizations_xml"
        model["agent"]["platform"] = "copilot_studio"
        model["source"]["parsed_files"].append(path.name)
        parse_customizations(text, model)
    elif fmt == "directory":
        # Prefer solution-aware walk when the layout matches (botcomponents/ present).
        all_files = [p for p in path.rglob("*") if p.is_file()]
        rels = [str(p.relative_to(path)).replace("\\", "/") for p in all_files]
        if _is_solution_layout(rels):
            model["source"]["format"] = "copilot_studio_solution_dir"
            model["agent"]["platform"] = "copilot_studio"
            entries = [
                (rel, (lambda fp=fp: fp.read_text(encoding="utf-8", errors="replace")))
                for fp, rel in zip(all_files, rels)
            ]
            _ingest_solution_entries(entries, model, verbose)
        else:
            model["source"]["format"] = "directory"
            for child in sorted(all_files):
                if child.suffix.lower() in (".yaml", ".yml", ".json", ".xml"):
                    sub = ingest(child, verbose)
                    _merge_models(model, sub)
    else:
        model["parse_report"]["unreadable"].append(
            f"{path.name}: unrecognised format. Supported: .zip, .yaml, .yml, .json, .xml"
        )

    derive_configuration(model)
    return model


def _merge_models(base: Dict[str, Any], other: Dict[str, Any]) -> None:
    base["source"]["parsed_files"].extend(other["source"]["parsed_files"])
    for t in other["topics"]:
        _merge_topic(base, t)
    for k in ("knowledge_sources", "tools"):
        for item in other[k]:
            if item not in base[k]:
                base[k].append(item)
    if other["agent"]["name"] and not base["agent"]["name"]:
        base["agent"]["name"] = other["agent"]["name"]
    if other["agent"]["platform"] and not base["agent"]["platform"]:
        base["agent"]["platform"] = other["agent"]["platform"]
    base["parse_report"]["warnings"].extend(other["parse_report"]["warnings"])
    base["parse_report"]["unreadable"].extend(other["parse_report"]["unreadable"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest an agent export into normalised JSON.")
    ap.add_argument("path", help="Path to export (.zip, .yaml, .json, .xml, or directory)")
    ap.add_argument("--out", default="normalized.json", help="Output JSON path")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"error: path not found: {p}", file=sys.stderr)
        return 2

    model = ingest(p, args.verbose)
    Path(args.out).write_text(json.dumps(model, indent=2), encoding="utf-8")

    rep = model["parse_report"]
    print(f"Parsed {len(model['source']['parsed_files'])} file(s) -> {args.out}")
    print(f"  platform: {model['agent']['platform']}")
    print(f"  topics:   {len(model['topics'])}")
    print(f"  tools:    {len(model['tools'])}")
    print(f"  complete: {rep['complete']}")
    for w in rep["warnings"]:
        print(f"  WARNING: {w}")
    for u in rep["unreadable"]:
        print(f"  UNREADABLE: {u}")
    if not rep["complete"]:
        print("  Note: parse incomplete — supplement with self-report for missing areas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
