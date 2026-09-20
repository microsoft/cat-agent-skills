#!/usr/bin/env python3
"""
Ingest a Copilot Studio agent export into normalised JSON for structural linting.

Scope: Copilot Studio only. Extracts exactly what the linter's structural checks
need — topics, trigger phrases, node counts, orchestration edges, variable
lifecycle, and configuration presence. No cost, model, or platform-fit fields:
those are out of scope for a linter and would tie it to the platform's pricing
and feature cadence, which is precisely what a structural linter must not depend on.

Handles:
  - Copilot Studio solution .zip
  - A directory of exported topic YAML
  - A single agent/topic YAML file

Degrades gracefully: reports what it could not read rather than guessing, because
every downstream finding inherits the ingestion's errors.

Usage:
    python ingest_agent.py <path> --out normalized.json
    python ingest_agent.py <path> --out normalized.json --verbose
"""

import argparse
import html
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

SCHEMA_VERSION = "1.0"


def _unescape(text: str) -> str:
    """Normalise text pulled from exports: decode HTML entities (&amp; etc.)
    and CRLF line endings, so downstream matching is not thrown off by encoding
    artifacts in the export."""
    if not text:
        return ""
    return html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")


# Guardrail / quality signals detected from instruction text. These are booleans
# only — the instruction TEXT is never stored, preserving the privacy guarantee.
# Each signal is a durable structural fact ("does the prompt contain a
# confirmation gate / a grounding rule / an output-format rule"), not a judgement
# of how well it is written.
_GROUNDING_MARKERS = (
    "do not fabricate", "don't fabricate", "never fabricate", "do not invent",
    "don't invent", "never invent", "do not guess", "never guess", "no guess",
    "only from", "based only on", "grounded", "do not hallucinate",
    "never hallucinate", "if you don't know", "if unknown", "cite", "citation",
    "from the knowledge source", "from the provided",
)
_CONFIRM_MARKERS = (
    "confirm", "confirmation", "approve", "approval", "are you sure",
    "before you", "require explicit", "ask before", "double-check", "verify with",
)
# Mirrors lint_agent.py's _MUTATING_OP_MARKERS: used only to set a boolean signal
# on connected agents (never to store their text), since ingest is the only place
# their raw content is available.
_MUTATING_MARKERS = (
    "create", "update", "delete", "write", "post", "invoke_action",
    "cancel", "confirm", "modify", "remove", "set_",
)
_OUTPUT_MARKERS = (
    "format", "output", "respond with", "reply with", "return only", "json",
    "one message", "exactly one", "table", "markdown", "structure your",
    "do not expose", "never expose", "layout",
)
_SCOPE_MARKERS = (
    "do not", "don't", "never", "must not", "only ", "not allowed", "refuse",
    "out of scope", "decline", "you cannot", "you can not",
)


def _instruction_signals(text: str) -> Dict[str, bool]:
    low = text.lower()
    return {
        "has_grounding_rule": any(m in low for m in _GROUNDING_MARKERS),
        "has_confirmation_gate": any(m in low for m in _CONFIRM_MARKERS),
        "has_output_constraint": any(m in low for m in _OUTPUT_MARKERS),
        "has_scope_limits": any(m in low for m in _SCOPE_MARKERS),
    }
YAML_EXTS = (".yaml", ".yml")
BOT_FILE_HINTS = ("botcomponent", "bot_", "/bots/", "dialog", "topic")


def empty_model() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {"path": None, "format": None, "parsed_files": []},
        "agent": {
            "name": None,
            "orchestration_mode": None,  # classic | generative | agentic | hybrid | unknown
            "model": None,               # e.g. Sonnet46
            "generative_actions_enabled": None,  # settings.GenerativeActionsEnabled
        },
        "topics": [],
        "skills": [],           # InlineAgentSkill components (new agentic experience)
        "tools": [],            # McpTool / WorkflowTool / action tool bindings
        "knowledge_sources": [],
        "connected_agents": [],  # connected/child execution agents (markdown or component)
        "contracts": [],         # request/result JSON schemas between agents
        "evaluation_sets": [],  # EvaluationSet components (+ their test-case counts)
        "instructions": {       # agent-level main instructions (system prompt)
            "present": None,
            "length": 0,
            "referenced_tools": [],
            "signals": {},       # guardrail/quality booleans (text never stored)
        },
        "memory": {
            "enabled": None,     # from configuration.json enableMemory
        },
        "knowledge": {
            "web_search_enabled": None,
            "source_count": 0,
        },
        "configuration": {
            "fallback_configured": None,
            "escalation_configured": None,
            "welcome_message": None,
            "session_timeout_minutes": None,
        },
        "variables": [],
        "parse_report": {
            "complete": False,
            "warnings": [],
            "unreadable": [],
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
        "source_file": None,
        "power_fx_unknown_functions": [],   # names only, never the expression text
        "power_fx_syntax_issues": [],       # [{"issue":, "line":}] -- bracket/quote imbalance only
        "unterminated_branch_groups": [],   # ConditionGroup branches with an inconsistent exit
        "has_on_outgoing_message_trigger": False,  # non-functional system trigger, per spec
        "odata_quote_issues": [],           # inconsistent quoting of $-prefixed params
    }


# --------------------------------------------------------------------------
# Format detection
# --------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    if path.is_dir():
        # A botcomponents/ folder (possibly nested) means the modern solution
        # layout, where each topic's YAML lives in botcomponents/<comp>/data
        # with its name in the sibling botcomponent.xml. This is the shape used
        # by current Copilot Studio exports (classic, hybrid, and agentic).
        if list(path.rglob("botcomponents")):
            return "botcomponents_dir"
        return "directory"
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return "solution_zip"
    if suffix in YAML_EXTS:
        return "agent_yaml"
    return "unknown"


def _name_from_botcomponent_xml(xml_path: Path) -> str:
    """Pull a topic/skill display name from a botcomponent.xml sibling.

    Prefers <name>, then <n> (some exports use it), then the topic.X suffix of
    the schemaname. The data file itself often has no display name, so this is
    the reliable source.
    """
    try:
        text = xml_path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return xml_path.parent.name
    for tag in ("name", "n"):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.S)
        if m and m.group(1).strip():
            return m.group(1).strip()
    m = re.search(r'schemaname="[^"]*\.(?:topic|skill|action|tool)\.([^"]+)"', text)
    if m:
        return m.group(1).strip()
    return xml_path.parent.name


def _parse_agent_config(root: Path, model: Dict[str, Any]) -> None:
    """Read agent-level config from bot.xml and configuration.json.

    Extracts: agent display name, model series, whether memory is enabled,
    whether web search / knowledge is on, and the main agent instructions
    (system prompt) with any tool names it references. Only lengths and
    references are kept from the instructions — never the prompt text.
    """
    # bot.xml -> agent name, model hint
    for botxml in root.rglob("bots/*/bot.xml"):
        try:
            text = botxml.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        m = re.search(r"<name>(.*?)</name>", text, re.S)
        if m and not model["agent"]["name"]:
            model["agent"]["name"] = m.group(1).strip()
        model["source"]["parsed_files"].append(str(botxml))
        break

    # configuration.json -> instructions, memory, model, web search
    for cfg in root.rglob("bots/*/configuration.json"):
        try:
            data = json.loads(cfg.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001
            model["parse_report"]["unreadable"].append(f"{cfg.name}: {exc}")
            continue
        model["source"]["parsed_files"].append(str(cfg))
        settings = data.get("settings", {}) if isinstance(data.get("settings"), dict) else {}
        agent_settings = data.get("agentSettings", {}) if isinstance(data.get("agentSettings"), dict) else {}

        # orchestration mode signal: generative (LLM-routed) actions vs classic
        # trigger-phrase routing. Verified field, seen in a real hybrid export.
        if "GenerativeActionsEnabled" in settings:
            model["agent"]["generative_actions_enabled"] = bool(settings["GenerativeActionsEnabled"])

        # memory
        if "enableMemory" in data:
            model["memory"]["enabled"] = bool(data["enableMemory"])
        elif "enableMemory" in agent_settings:
            model["memory"]["enabled"] = bool(agent_settings["enableMemory"])

        # web search / knowledge
        web = data.get("web") or agent_settings.get("web")
        if isinstance(web, dict) and "enableWebSearch" in web:
            model["knowledge"]["web_search_enabled"] = bool(web["enableWebSearch"])

        # model series
        modelcfg = agent_settings.get("model") if isinstance(agent_settings.get("model"), dict) else {}
        if isinstance(modelcfg.get("series"), str):
            model["agent"]["model"] = modelcfg["series"]

        # main instructions (system prompt) — length + tool references only
        instr = agent_settings.get("instructions") if isinstance(agent_settings.get("instructions"), dict) else {}
        segs = instr.get("segments") if isinstance(instr.get("segments"), list) else []
        instr_text = ""
        for seg in segs:
            if isinstance(seg, dict) and isinstance(seg.get("value"), str):
                instr_text += seg["value"] + "\n"
        instr_text = _unescape(instr_text)
        if instr_text.strip():
            model["instructions"]["present"] = True
            model["instructions"]["length"] = len(instr_text)
            # Reset in case a GptComponentMetadata component (parsed earlier
            # in this same ingest pass) had already set a source_file: this
            # branch's content wins, so its stale label must not linger.
            model["instructions"]["source_file"] = None
            model["instructions"]["signals"] = _instruction_signals(instr_text)
            # Expand slash-shorthand the way makers write it: a common style is
            # "data_create/update/delete_entities" meaning three tools —
            # data_create_entities, data_update_entities, data_delete_entities.
            # Without expansion the regex below would pull the bare middle token
            # "update_entities" / "delete_entities" and flag them as unwired,
            # which is a false positive. Rewrite each such run into its full
            # member names first.
            def _expand(m: "re.Match") -> str:
                prefix, first, rest, suffix = m.group(1), m.group(2), m.group(3), m.group(4)
                parts = [first] + [p for p in rest.split("/") if p]
                return " ".join(f"{prefix}_{p}_{suffix}" for p in parts)
            expanded = re.sub(
                r"\b([a-z]+)_([a-z]+)((?:/[a-z]+)+)_([a-z]+)\b", _expand, instr_text
            )
            # tool names referenced in the instructions (best-effort: backticked
            # tokens that look like tool identifiers, plus verb_noun tokens)
            refs = set(re.findall(r"`([A-Za-z0-9_]{3,})`", expanded))
            refs |= set(re.findall(r"\b([a-z]+_[a-z_]+)\b", expanded))
            model["instructions"]["referenced_tools"] = sorted(
                r for r in refs if "_" in r or r[:1].isupper()
            )[:40]
        elif not model["instructions"].get("present"):
            # Don't clobber a source already claimed earlier in ingest (e.g. a
            # GptComponentMetadata component) just because config.json itself
            # carries no agentSettings.instructions.
            model["instructions"]["present"] = False
        break


def parse_modernization_layer(root: Path, model: Dict[str, Any], verbose: bool) -> None:
    """Read the modernization/orchestration layer some exports ship alongside
    the solution: markdown parent/orchestrator instructions, connected (child)
    execution agents, and the request/result contracts between them.

    These files are how a hybrid/modernized agent expresses its instructions and
    its multi-agent wiring, so skipping them made the linter report 'no
    instructions' on an agent that clearly has them. Only structure and length
    are recorded; the instruction text itself is never stored.
    """
    # Markdown instructions (parent-agent/instructions.md, */instructions.md).
    # Only adopt these as the agent's main instructions if config gave us none.
    if not model["instructions"].get("present"):
        for md in sorted(root.rglob("*instructions.md")) + sorted(root.rglob("parent-agent/*.md")):
            try:
                text = _unescape(md.read_text(encoding="utf-8", errors="replace"))
            except Exception:  # noqa: BLE001
                continue
            if text.strip():
                model["instructions"]["present"] = True
                model["instructions"]["length"] = len(text)
                model["instructions"]["source_file"] = md.name
                model["instructions"]["signals"] = _instruction_signals(text)
                refs = set(re.findall(r"`([A-Za-z0-9_]{3,})`", text))
                refs |= set(re.findall(r"\b([a-z]+_[a-z_]+)\b", text))
                model["instructions"]["referenced_tools"] = sorted(
                    r for r in refs if "_" in r or r[:1].isupper()
                )[:40]
                model["source"]["parsed_files"].append(str(md))
                break

    # Connected / child execution agents. kind: AgentDialog (parsed earlier, in
    # the botcomponents pass) is the primary source of truth per the ingestion
    # spec; a connected-agents/*.md file is treated as supplementary
    # documentation for the same agent(s), not a second one, whenever at least
    # one native AgentDialog was already found. There is no reliable shared
    # identifier to match a specific .md file to a specific AgentDialog
    # component (observed real names differ, e.g. "Agent" vs "Dynamics 365 PO
    # Execution Agent" for what is plausibly the same child agent), so this
    # treats "any native AgentDialog present" as sufficient to skip the
    # markdown files entirely, rather than risk double-counting one real
    # connected agent as two.
    has_native_agent_dialog = any(
        c.get("source_kind") == "AgentDialog" for c in model["connected_agents"]
    )
    seen_conn = {c["name"] for c in model["connected_agents"]}
    for md in sorted(root.rglob("connected-agents/*.md")):
        if has_native_agent_dialog:
            break
        try:
            text = _unescape(md.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            continue
        title = None
        tm = re.search(r"^#\s+(.+)$", text, re.M)
        if tm:
            title = tm.group(1).strip()
        name = title or md.stem
        if name in seen_conn:
            continue
        seen_conn.add(name)
        refs = sorted(set(re.findall(r"`([A-Za-z0-9_]{3,})`", text)))
        model["connected_agents"].append({
            "name": name,
            "source_file": md.name,
            "source_kind": "markdown",
            "instruction_chars": len(text),
            # Accept snake_case or PascalCase tool names, matching every other
            # tool-reference extractor in this file (a PascalCase-only name like
            # `BillingTool` was previously dropped because it has no underscore).
            "referenced_tools": [r for r in refs if "_" in r or r[:1].isupper()][:20],
            # Boolean only (never the text): lets the guardrail check recognise
            # mutating capability that lives entirely in a connected agent, with
            # no McpTool/WorkflowTool/skill in this export to carry the signal.
            "references_mutating_ops": any(m in text.lower() for m in _MUTATING_MARKERS),
        })
        model["source"]["parsed_files"].append(str(md))
        if verbose:
            print(f"[ingest] connected agent: {name} ({len(text)} chars)", file=sys.stderr)

    # Contracts (request/result schemas between agents).
    seen_contract = {c["name"] for c in model["contracts"]}
    for sch in sorted(root.rglob("contracts/*.json")):
        name = sch.stem
        if name in seen_contract:
            continue
        seen_contract.add(name)
        valid = None
        try:
            json.loads(sch.read_text(encoding="utf-8", errors="replace"))
            valid = True
        except Exception:  # noqa: BLE001
            valid = False
        model["contracts"].append({"name": name, "source_file": sch.name, "valid_json": valid})
        model["source"]["parsed_files"].append(str(sch))


def ingest_botcomponents_dir(root: Path, model: Dict[str, Any], verbose: bool) -> None:
    """Walk botcomponents/<component>/data files.

    Routes each component by its `kind`:
      - AdaptiveDialog        -> topic (classic structural checks)
      - InlineAgentSkill      -> skill (agentic checks: description, tools, instructions)
      - McpTool / WorkflowTool -> tool binding (referenced by skills)
    Other kinds (GptComponentMetadata, evaluation cases, dialogs) are counted and
    reported but not linted — the checks do not apply to them, and pretending
    otherwise would fabricate findings.
    """
    model["source"]["format"] = "copilot_studio_botcomponents"
    data_files = sorted(root.rglob("botcomponents/*/data"))
    other_kinds: Dict[str, int] = {}

    for data_path in data_files:
        try:
            text = data_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            model["parse_report"]["unreadable"].append(f"{data_path}: {exc}")
            continue

        stripped = text.lstrip()
        km = re.match(r"kind:\s*(\w+)", stripped)
        kind = km.group(1) if km else ""
        xml_sib = data_path.parent / "botcomponent.xml"
        name = _name_from_botcomponent_xml(xml_sib) if xml_sib.exists() else data_path.parent.name
        try:
            rel_source = str(data_path.relative_to(root))
        except ValueError:
            rel_source = str(data_path)

        if kind == "AdaptiveDialog":
            model["source"]["parsed_files"].append(str(data_path))
            parse_topic_yaml(text, name, model, verbose, forced_name=name, source_file=rel_source)
        elif kind == "InlineAgentSkill":
            model["source"]["parsed_files"].append(str(data_path))
            parse_inline_skill(text, name, model, verbose)
        elif kind in ("McpTool", "WorkflowTool", "TaskDialog"):
            model["source"]["parsed_files"].append(str(data_path))
            parse_tool(text, name, kind, model, source_file=rel_source)
        elif kind == "EvaluationSet":
            model["source"]["parsed_files"].append(str(data_path))
            parse_evaluation_set(text, name, model)
        elif kind == "KnowledgeSourceConfiguration":
            model["source"]["parsed_files"].append(str(data_path))
            parse_knowledge_source(text, name, model)
        elif kind == "AgentDialog":
            model["source"]["parsed_files"].append(str(data_path))
            parse_agent_dialog(text, name, model, source_file=rel_source)
        elif kind == "MultiTurnEvaluationCase":
            other_kinds[kind] = other_kinds.get(kind, 0) + 1  # counted as test cases
        elif kind == "GptComponentMetadata":
            model["source"]["parsed_files"].append(str(data_path))
            parse_gpt_component(text, name, model)
        else:
            if kind:
                other_kinds[kind] = other_kinds.get(kind, 0) + 1

    # Agent-level config (instructions, memory, model, web/knowledge) lives in
    # bot.xml + configuration.json, not in botcomponents. Read them too.
    _parse_agent_config(root, model)

    # Modernization/orchestration layer (markdown instructions, connected agents,
    # contracts) — present in hybrid/modernized exports, outside botcomponents.
    parse_modernization_layer(root, model, verbose)

    # Attach test-case count to evaluation reporting rather than dismissing it.
    tc = other_kinds.pop("MultiTurnEvaluationCase", 0)
    if tc:
        model["agent"]["evaluation_case_count"] = tc

    if other_kinds:
        model["agent"]["other_components"] = other_kinds
        summary = ", ".join(f"{k}x{v}" for k, v in sorted(other_kinds.items()))
        model["parse_report"]["warnings"].append(
            f"Additional component kinds present and recorded: {summary}."
        )


def parse_inline_skill(text: str, comp_name: str, model: Dict[str, Any], verbose: bool) -> None:
    """Extract an InlineAgentSkill: name, description, referenced tools, instructions.

    The skill's payload is usually a markdown document inside a `content:` block,
    with YAML frontmatter (name, description) and markdown sections (## Tools,
    ## Instructions). In the agentic experience the LLM routes to a skill by its
    *description*, so description quality is the new analogue of trigger phrases.

    This parser is defensive about export-format variance: the description may
    live in the frontmatter OR as a top-level YAML field; section headers vary
    (Tool/Tools/Available Tools, Instruction/Instructions); tool names may be in
    backticks or plain list items; and text may carry HTML entities and CRLF.
    None of these should change whether a real defect is found.
    """
    skill = {
        "name": comp_name,
        "description": "",
        "instructions": "",
        "referenced_tools": [],
        "content_present": False,
    }

    data = load_yaml(text, model, comp_name)

    # 1) Locate the markdown content.
    content = ""
    top_description = ""
    if isinstance(data, dict):
        if isinstance(data.get("content"), str):
            content = data["content"]
        # Description / instructions may also be direct fields on the component.
        for k in ("description", "summary"):
            if isinstance(data.get(k), str) and data[k].strip():
                top_description = data[k].strip()
                break
        if isinstance(data.get("instructions"), str) and data["instructions"].strip():
            skill["instructions"] = data["instructions"].strip()
        if isinstance(data.get("displayName"), str) and data["displayName"].strip():
            skill["name"] = data["displayName"].strip()
    if not content:
        m = re.search(r"content:\s*\|?[-+]?\s*\n(.*)", text, re.S)
        if m:
            content = m.group(1)

    content = _unescape(content)
    skill["content_present"] = bool(content.strip())

    # 2) Frontmatter name/description (only a genuine leading --- ... --- block).
    fm = re.match(r"\s*---\s*\n(.*?)\n\s*---\s*(?:\n|$)", content, re.S)
    if fm:
        block = fm.group(1)
        nm = re.search(r"^\s*name:\s*(.+)$", block, re.M)
        if nm:
            skill["name"] = nm.group(1).strip().strip("\"'")
        dm = re.search(r"^\s*description:\s*\|?-?\s*\n?(.*?)(?:\n\s*\w[\w\- ]*:\s|\Z)",
                       block, re.S | re.M)
        if dm and dm.group(1).strip():
            # A YAML double-quoted scalar is required whenever the value itself
            # contains ": " (e.g. "Use when...a PO: unit cost..."), so strip a
            # matching pair of quotes the same way the name field above does.
            skill["description"] = re.sub(r"\s+", " ", dm.group(1)).strip().strip("\"'")

    # Fall back to a top-level description field if frontmatter had none.
    if not skill["description"] and top_description:
        skill["description"] = re.sub(r"\s+", " ", _unescape(top_description)).strip()

    # 3) Instructions section (header-name tolerant), if not already set.
    if not skill["instructions"]:
        im = re.search(r"^#{1,4}\s*Instructions?\s*\n(.*?)(?:\n#{1,4}\s|\Z)",
                       content, re.S | re.M | re.I)
        if im:
            skill["instructions"] = im.group(1).strip()

    # 4) Tools section (header-name tolerant): names in backticks, or leading
    #    list-item tokens if no backticks are used.
    tm = re.search(r"^#{1,4}\s*(?:Available\s+)?Tools?\s*\n(.*?)(?:\n#{1,4}\s|\Z)",
                   content, re.S | re.M | re.I)
    if tm:
        section = tm.group(1)
        refs = re.findall(r"`([^`]+?)`", section)
        if not refs:
            # plain list items: "- toolName (read)" -> toolName
            for line in section.splitlines():
                lm = re.match(r"\s*[-*]\s*([A-Za-z0-9_.\-]+)", line)
                if lm:
                    refs.append(lm.group(1))
        skill["referenced_tools"] = sorted({_unescape(r).strip() for r in refs if r.strip()})

    model["skills"].append(skill)
    skill["signals"] = _instruction_signals(skill.get("instructions", ""))
    if verbose:
        print(f"[ingest] skill: {skill['name']} "
              f"(desc {len(skill['description'])} chars, "
              f"{len(skill['referenced_tools'])} tools)", file=sys.stderr)


def parse_tool(text: str, comp_name: str, kind: str, model: Dict[str, Any],
               source_file: Optional[str] = None) -> None:
    """Record a tool binding (McpTool / WorkflowTool / TaskDialog) with its
    structural detail so skill tool-references can be checked for integrity and
    wiring completeness, and so TRG-QUALITY can assess its description."""
    tool = {
        "name": _unescape(comp_name).strip(),
        "kind": kind,
        "source_file": source_file,
        "allowed_tools": [],       # McpTool: the operations it exposes
        "connection_reference": None,
        "connector_id": None,
        "workflow_id": None,
        "input_count": 0,
        "model_description_present": False,   # never store the description text itself
        "model_description_chars": 0,
        "odata_quote_issues": [],
    }
    data = load_yaml(text, model, comp_name)
    if isinstance(data, dict):
        for key in ("name", "displayName", "toolName", "schemaName", "modelDisplayName"):
            if isinstance(data.get(key), str) and data[key].strip():
                tool["name"] = _unescape(data[key]).strip()
                break
        if isinstance(data.get("allowedTools"), list):
            tool["allowed_tools"] = [str(t).strip() for t in data["allowedTools"] if str(t).strip()]
        if isinstance(data.get("connectionReference"), str):
            tool["connection_reference"] = data["connectionReference"].strip()
        if isinstance(data.get("connectorId"), str):
            tool["connector_id"] = data["connectorId"].strip()
        if isinstance(data.get("workflowId"), str):
            tool["workflow_id"] = data["workflowId"].strip()
        if isinstance(data.get("toolInputs"), list):
            tool["input_count"] = len(data["toolInputs"])
        # TaskDialog (the action/connector component kind in real exports): the
        # description lives in a top-level modelDescription, and the connection
        # reference is nested under action.connectionReference rather than top-level.
        if kind == "TaskDialog":
            action = data.get("action") if isinstance(data.get("action"), dict) else {}
            if isinstance(action.get("connectionReference"), str):
                tool["connection_reference"] = action["connectionReference"].strip()
            desc = data.get("modelDescription")
            if isinstance(desc, str) and desc.strip():
                tool["model_description_present"] = True
                tool["model_description_chars"] = len(desc.strip())
    tool["odata_quote_issues"] = _scan_odata_quote_issues(text)
    model["tools"].append(tool)


def parse_agent_dialog(text: str, comp_name: str, model: Dict[str, Any],
                       source_file: Optional[str] = None) -> None:
    """Record a native AgentDialog component as a connected/child agent -- the
    primary source of truth for child agents (a connected-agents/*.md file
    describing the same agent is treated as supplementary documentation, not
    a second one; see the dedup step in parse_modernization_layer). Only
    length/signals/tool-refs are kept, never the description text.
    """
    data = load_yaml(text, model, comp_name)
    name = comp_name
    desc = ""
    has_on_tool_selected = False
    if isinstance(data, dict):
        if isinstance(data.get("displayName"), str) and data["displayName"].strip():
            name = data["displayName"].strip()
        begin = data.get("beginDialog") if isinstance(data.get("beginDialog"), dict) else {}
        has_on_tool_selected = str(begin.get("kind", "")) == "OnToolSelected"
        # modelDescription matches TaskDialog's shape and this rule's spec;
        # beginDialog.description is what a real export has actually shown.
        if isinstance(data.get("modelDescription"), str) and data["modelDescription"].strip():
            desc = data["modelDescription"]
        elif isinstance(begin.get("description"), str):
            desc = begin["description"]
    desc = _unescape(desc)
    if any(c["name"] == name and c.get("source_kind") == "AgentDialog"
           for c in model["connected_agents"]):
        return
    refs = set(re.findall(r"`([A-Za-z0-9_]{3,})`", desc))
    refs |= set(re.findall(r"\b([a-z]+_[a-z_]+)\b", desc))
    model["connected_agents"].append({
        "name": name,
        "source_file": source_file or comp_name,
        "source_kind": "AgentDialog",
        "instruction_chars": len(desc),
        "referenced_tools": sorted(r for r in refs if "_" in r or r[:1].isupper())[:20],
        "references_mutating_ops": any(m in desc.lower() for m in _MUTATING_MARKERS),
        "has_on_tool_selected_trigger": has_on_tool_selected,
    })


def parse_evaluation_set(text: str, comp_name: str, model: Dict[str, Any]) -> None:
    """Record an EvaluationSet and (structurally) whether it has graders."""
    ev = {"name": comp_name, "graders": [], "grader_count": 0}
    data = load_yaml(text, model, comp_name)
    if isinstance(data, dict) and isinstance(data.get("graders"), list):
        for g in data["graders"]:
            if isinstance(g, dict) and g.get("kind"):
                ev["graders"].append(str(g["kind"]))
        ev["grader_count"] = len(ev["graders"])
    model["evaluation_sets"].append(ev)


def parse_knowledge_source(text: str, comp_name: str, model: Dict[str, Any]) -> None:
    """Record a KnowledgeSourceConfiguration component with its source kind and
    a short detail (site, dataset, etc.) so the report can describe it."""
    ks = {"name": comp_name, "kind": "KnowledgeSourceConfiguration",
          "source_kind": None, "detail": None}
    data = load_yaml(text, model, comp_name)
    if isinstance(data, dict):
        src = data.get("source") if isinstance(data.get("source"), dict) else {}
        ks["source_kind"] = src.get("kind")
        for key in ("site", "url", "dataset", "connectionReference", "path"):
            if isinstance(src.get(key), str) and src[key].strip():
                ks["detail"] = src[key].strip()
                break
    else:
        km = re.search(r"kind:\s*(\w+)", text)
        sm = re.search(r"site:\s*(\S+)", text)
        if km:
            ks["source_kind"] = km.group(1)
        if sm:
            ks["detail"] = sm.group(1)
    model["knowledge_sources"].append(ks)
    model["knowledge"]["source_count"] = len(model["knowledge_sources"])


def parse_gpt_component(text: str, comp_name: str, model: Dict[str, Any]) -> None:
    """A GptComponentMetadata component can carry the agent's real generative
    system prompt directly in its own `instructions:` field. Some exports
    reference it from configuration.json via `gPTSettings.defaultSchemaName`
    instead of embedding `agentSettings.instructions` there, which otherwise
    leaves the agent looking like it has no main instructions at all.

    Adopted only if nothing has already claimed the main-instructions role
    (config.json's own agentSettings.instructions takes precedence if both
    exist). Only length/signals/tool-refs are kept, never the raw text.
    """
    if model["instructions"].get("present"):
        return
    data = load_yaml(text, model, comp_name)
    instr_text = None
    if isinstance(data, dict) and isinstance(data.get("instructions"), str):
        instr_text = data["instructions"]
    if instr_text is None:
        m = re.search(r'^\s*instructions:\s*"(.*)"\s*$', text, re.S | re.M)
        if m:
            instr_text = m.group(1)
    if not instr_text or not instr_text.strip():
        return
    instr_text = _unescape(instr_text)
    model["instructions"]["present"] = True
    model["instructions"]["length"] = len(instr_text)
    model["instructions"]["source_file"] = "GptComponentMetadata"
    model["instructions"]["signals"] = _instruction_signals(instr_text)
    refs = set(re.findall(r"`([A-Za-z0-9_]{3,})`", instr_text))
    refs |= set(re.findall(r"\b([a-z]+_[a-z_]+)\b", instr_text))
    model["instructions"]["referenced_tools"] = sorted(
        r for r in refs if "_" in r or r[:1].isupper()
    )[:40]


def load_yaml(text: str, model: Dict[str, Any], label: str) -> Optional[Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        model["parse_report"]["warnings"].append(
            f"PyYAML not available; used regex fallback for {label}. "
            "Install pyyaml for more reliable parsing."
        )
        return None
    try:
        return yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        model["parse_report"]["warnings"].append(f"YAML parse failed for {label}: {exc}")
        return None


# --------------------------------------------------------------------------
# Solution zip
# --------------------------------------------------------------------------

# An agent export is text/YAML/JSON, so a legitimate one is at most a few MB
# and at most a few thousand component files. These caps exist only to refuse
# a decompression-bomb upload before it exhausts memory/disk, not to bound
# real exports.
MAX_ZIP_ENTRIES = 5000
MAX_ZIP_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB


def _safe_extractall(zf: "zipfile.ZipFile", dest: Path, model: Dict[str, Any]) -> None:
    """Extract a zip while refusing entries that would escape the destination
    or a payload sized like a decompression bomb.

    The export is untrusted input, so a crafted archive could contain entries
    like '../../etc/x' (zip-slip) or absolute paths, or a small file that
    decompresses to an enormous size/entry count (zip bomb). Both are checked
    before any bytes are written; on either, extraction is refused and
    reported rather than left to exhaust memory or disk.
    """
    infos = zf.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        model["parse_report"]["unreadable"].append(
            f"archive has {len(infos)} entries, exceeding the {MAX_ZIP_ENTRIES} "
            "limit; refusing to extract (possible zip bomb)."
        )
        return
    total_uncompressed = sum(i.file_size for i in infos)
    if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
        model["parse_report"]["unreadable"].append(
            f"archive would decompress to {total_uncompressed:,} bytes, "
            f"exceeding the {MAX_ZIP_UNCOMPRESSED_BYTES:,} byte limit; "
            "refusing to extract (possible zip bomb)."
        )
        return

    dest_root = dest.resolve()
    for member in zf.namelist():
        # Reject absolute paths and any traversal that escapes dest.
        target = (dest_root / member).resolve()
        if not (target == dest_root or dest_root in target.parents):
            model["parse_report"]["warnings"].append(
                f"Skipped archive entry outside extraction root (possible "
                f"zip-slip): {member}"
            )
            continue
        if member.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as out:
            out.write(src.read())


def ingest_solution_zip(path: Path, model: Dict[str, Any], verbose: bool) -> None:
    model["source"]["format"] = "copilot_studio_solution_zip"
    try:
        zf = zipfile.ZipFile(path)
    except Exception as exc:  # noqa: BLE001
        model["parse_report"]["unreadable"].append(f"{path.name}: {exc}")
        return

    with zf:
        names = zf.namelist()
        if verbose:
            print(f"[ingest] {len(names)} entries in archive", file=sys.stderr)

        # Modern export: topics live in botcomponents/<comp>/data. Extract to a
        # temp dir and reuse the directory walker, which reads the data files
        # Any modern export extracts fully to a temp dir and is walked as a
        # directory. This uniformly covers botcomponents topics/skills, the
        # agent config (bot.xml, configuration.json), and the modernization
        # layer (parent-agent instructions, connected agents, contracts) —
        # regardless of whether the zip uses the botcomponents layout.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            _safe_extractall(zf, Path(td), model)
            tdp = Path(td)
            if list(tdp.rglob("botcomponents")):
                ingest_botcomponents_dir(tdp, model, verbose)
            else:
                # No botcomponents: read config + modernization, then any loose
                # topic YAML.
                _parse_agent_config(tdp, model)
                parse_modernization_layer(tdp, model, verbose)
                for child in sorted(tdp.rglob("*")):
                    if child.is_file() and child.suffix.lower() in YAML_EXTS:
                        try:
                            text = child.read_text(encoding="utf-8", errors="replace")
                        except Exception:  # noqa: BLE001
                            continue
                        model["source"]["parsed_files"].append(child.name)
                        parse_topic_yaml(text, child.name, model, verbose)
        model["source"]["format"] = "copilot_studio_solution_zip"
        return


# --------------------------------------------------------------------------
# Topic YAML
# --------------------------------------------------------------------------

def parse_topic_yaml(text: str, label: str, model: Dict[str, Any], verbose: bool,
                     forced_name: str = None, source_file: Optional[str] = None) -> None:
    data = load_yaml(text, model, label)
    if data is None:
        parse_topic_regex(text, label, model, forced_name=forced_name)
        return
    if not isinstance(data, dict):
        return

    name = forced_name or data.get("displayName") or data.get("name") or Path(label).stem
    topic = empty_topic(str(name))
    topic["is_system_topic"] = _looks_like_system_topic(str(name))
    topic["source_file"] = source_file

    begin = data.get("beginDialog", {}) if isinstance(data.get("beginDialog"), dict) else {}
    begin_intent = begin.get("intent", {}) if isinstance(begin.get("intent"), dict) else {}
    top_intent = data.get("intent", {}) if isinstance(data.get("intent"), dict) else {}
    top_trigger = data.get("trigger", {}) if isinstance(data.get("trigger"), dict) else {}
    phrase_sources = [
        data.get("triggerQueries"),
        top_trigger.get("triggerQueries"),
        begin.get("triggerQueries"),
        begin_intent.get("triggerQueries"),   # beginDialog.intent.triggerQueries (current export shape)
        top_intent.get("triggerQueries"),
    ]
    for ps in phrase_sources:
        if isinstance(ps, list):
            for p in ps:
                if isinstance(p, str) and p.strip():
                    topic["trigger_phrases"].append(p.strip())

    body = json.dumps(data)
    topic["node_count"] = _count_nodes(data)
    topic["is_generative"] = "generativeAnswers" in body or "GenerativeAnswers" in body
    topic["grounding_enabled"] = topic["is_generative"]
    topic["has_slot_filling"] = "Question" in body or "slotFilling" in body
    topic["has_interruption_handling"] = (
        "allowInterruption" in body or "interruption" in body.lower()
    )
    _extract_variables(body, topic)
    topic["calls_topics"] = sorted(set(re.findall(r"BeginDialog[\"']?\s*:\s*[\"']([\w\.]+)", body)))
    pfx = _scan_power_fx(text)
    topic["power_fx_unknown_functions"] = pfx["unknown_functions"]
    topic["power_fx_syntax_issues"] = pfx["syntax_issues"]
    topic["unterminated_branch_groups"] = _find_unterminated_branch_groups(data)
    topic["odata_quote_issues"] = _scan_odata_quote_issues(text)
    topic["has_on_outgoing_message_trigger"] = "OnOutgoingMessage" in body

    _merge_topic(model, topic)
    if verbose:
        print(f"[ingest] topic: {topic['name']} "
              f"({len(topic['trigger_phrases'])} phrases, {topic['node_count']} nodes)",
              file=sys.stderr)


def parse_topic_regex(text: str, label: str, model: Dict[str, Any],
                      forced_name: str = None) -> None:
    """Minimal fallback when YAML parsing is unavailable."""
    name_m = re.search(r"displayName:\s*(.+)", text)
    name = forced_name or (name_m.group(1).strip().strip("\"'") if name_m else Path(label).stem)
    topic = empty_topic(name)
    topic["is_system_topic"] = _looks_like_system_topic(name)

    block = re.search(r"triggerQueries:\s*((?:\s*-\s*.+\n?)+)", text)
    if block:
        for line in block.group(1).splitlines():
            p = line.strip().lstrip("-").strip().strip("\"'")
            if p:
                topic["trigger_phrases"].append(p)

    topic["node_count"] = len(re.findall(r"^\s*-\s*kind:", text, re.M))
    topic["is_generative"] = "GenerativeAnswers" in text
    topic["grounding_enabled"] = topic["is_generative"]
    topic["has_slot_filling"] = "kind: Question" in text
    topic["has_interruption_handling"] = "allowInterruption" in text
    _extract_variables(text, topic)

    _merge_topic(model, topic)


def _extract_variables(body: str, topic: Dict[str, Any]) -> None:
    """Extract set/read variables across both assignment syntaxes.

    Two assignment syntaxes appear in exports: inline Power Fx (Topic.X = ...)
    and node-based (variable: Topic.X). A variable is "read" if it appears
    anywhere other than as an assignment target — including brace interpolation
    {Topic.X}. Count total references against assignment references per name: a
    surplus means at least one genuine read. This avoids (a) a lookahead on \\w+
    inventing truncated phantom names, and (b) treating a set-and-echoed
    variable as a dead assignment.
    """
    inline_sets = re.findall(r"Topic\.(\w+)\s*=", body)
    node_sets = re.findall(r'"?variable"?\s*:\s*"?Topic\.(\w+)', body)
    topic["variables_set"] = sorted(set(inline_sets) | set(node_sets))

    total_refs = Counter(re.findall(r"Topic\.(\w+)", body))
    assign_refs = Counter(inline_sets) + Counter(node_sets)
    topic["variables_read"] = sorted({
        name for name, total in total_refs.items()
        if total > assign_refs.get(name, 0)
    })


def _looks_like_system_topic(name: str) -> bool:
    n = name.lower().replace(" ", "").replace("_", "")
    return any(k in n for k in (
        "fallback", "escalate", "escalation", "greeting", "goodbye",
        "startover", "endofconversation", "signin", "resetconversation",
        "multipletopicsmatched", "conversationstart", "onerror",
        "conversationalboosting", "thankyou", "signout",
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


# Known-common Power Fx functions, used only to decide whether an unusual
# token in a "=" expression deserves a closer look. NOT an exhaustive or
# verified list of every function Copilot Studio supports -- PFX-WHITELIST
# treats a miss as a low-confidence advisory signal, never an assertion that
# the function is unsupported.
KNOWN_POWER_FX_FUNCTIONS = {
    # Math
    "abs", "acos", "acot", "asin", "atan", "atan2", "cos", "cot", "degrees",
    "exp", "int", "ln", "log", "mod", "pi", "power", "radians", "rand",
    "randbetween", "round", "rounddown", "roundup", "sin", "sqrt", "sum",
    "tan", "trunc",
    # Text
    "char", "concat", "concatenate", "encodehtml", "encodeurl", "endswith",
    "find", "left", "len", "lower", "match", "matchall", "mid", "plaintext",
    "proper", "replace", "right", "search", "split", "startswith",
    "substitute", "text", "trim", "trimends", "unichar", "upper", "value",
    # Date/Time
    "date", "dateadd", "datediff", "datetime", "datetimevalue", "datevalue",
    "day", "edate", "eomonth", "hour", "istoday", "minute", "month", "now",
    "second", "time", "timevalue", "timezoneoffset", "today", "weekday",
    "weeknum", "year",
    # Logical
    "and", "coalesce", "if", "iferror", "isblank", "isblankorerror",
    "isempty", "iserror", "ismatch", "isnumeric", "istype", "not", "or",
    "switch",
    # Table
    "addcolumns", "column", "columnnames", "count", "counta", "countif",
    "countrows", "distinct", "dropcolumns", "filter", "first", "firstn",
    "forall", "index", "last", "lastn", "lookup", "patch", "refresh",
    "renamecolumns", "sequence", "showcolumns", "shuffle", "sort",
    "sortbycolumns", "summarize", "table",
    # Aggregate
    "average", "max", "min", "stdevp", "varp",
    # Type conversion
    "astype", "boolean", "dec2hex", "decimal", "float", "guid", "hex2dec",
    "json", "parsejson",
    # Other, incl. common ones a hand-picked whitelist tends to miss
    "blank", "colorfade", "colorvalue", "error", "language", "optionsetinfo",
    "rgba", "trace", "with", "collect", "clearcollect", "clear", "remove",
    "removeif", "updateif", "update", "set", "updatecontext", "navigate",
    "notify", "reset", "resetform", "validate", "submitform", "newform",
    "editform", "viewform", "back", "exit", "launch", "download", "print",
    "recordinfo", "revert", "savedata", "loaddata", "cleardata", "disable",
    "enable", "select", "setfocus", "assert", "user", "concurrent",
}


def _check_bracket_balance(expr: str) -> Optional[str]:
    """Check that (), {}, [] are balanced in a Power Fx expression, treating
    the contents of a '...' or "..." string literal as opaque so a bracket
    character inside a string argument is never misread as expression
    structure. Returns a short description of the first problem found, or
    None if balanced. Deterministic syntax validation only -- never a claim
    about whether a function name is supported."""
    pairs = {")": "(", "}": "{", "]": "["}
    opens = set(pairs.values())
    stack: List[str] = []
    quote: Optional[str] = None
    for ch in expr:
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return f"unmatched '{ch}'"
            stack.pop()
    if quote:
        return f"unterminated {quote} string"
    if stack:
        return f"unmatched '{stack[-1]}'"
    return None


# Matches a YAML "key: =expr" value, capturing the expression up to its
# closing quote if the value was quoted, or to end-of-line if it was bare --
# so a stray wrapper quote is never mistaken for part of the Power Fx string.
# Line-based (re.M): a "=" expression continued across multiple YAML lines
# (block-scalar style) is only scanned on its first line, a deliberate scope
# limit rather than a full YAML-aware Power Fx tokenizer.
_PFX_EXPR_RE = re.compile(r':\s*(["\'])?=((?:(?!\1).)*)\1?\s*$', re.M)


def _scan_power_fx(text: str) -> Dict[str, List[Any]]:
    """Scan '=' Power Fx expressions in the raw YAML source for (a) function
    names outside the known-common set and (b) unbalanced brackets/quotes.
    Names and issue labels only -- the expression text itself is never kept."""
    unknown: Set[str] = set()
    syntax_issues: List[Dict[str, Any]] = []
    for m in _PFX_EXPR_RE.finditer(text):
        expr = m.group(2)
        for fn in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", expr):
            if fn.lower() not in KNOWN_POWER_FX_FUNCTIONS:
                unknown.add(fn)
        issue = _check_bracket_balance(expr)
        if issue:
            syntax_issues.append({"issue": issue, "line": text[:m.start()].count("\n") + 1})
    return {"unknown_functions": sorted(unknown), "syntax_issues": syntax_issues}


# A branch (ConditionGroup condition, or its elseActions) is considered to
# cleanly exit if its last action is one of these dialog-exiting kinds, or
# carries an explicit conversationOutcome marker.
_TERMINATING_ACTION_KINDS = {
    "redirectdialog", "begindialog", "replacedialog", "enddialog",
    "cancelalldialogs",
}
_TERMINATING_OUTCOMES = {"resolvedconfirmed", "resolvedimplied"}


def _branch_terminates(actions: Any) -> bool:
    if not isinstance(actions, list) or not actions:
        return False
    last = actions[-1]
    if not isinstance(last, dict):
        return False
    if str(last.get("kind", "")).lower() in _TERMINATING_ACTION_KINDS:
        return True
    outcome = last.get("conversationOutcome")
    return isinstance(outcome, str) and outcome.lower() in _TERMINATING_OUTCOMES


def _find_unterminated_branch_groups(data: Any, path: str = "") -> List[Dict[str, Any]]:
    """Find ConditionGroup nodes whose branches disagree on how they exit --
    some redirect/end cleanly, at least one just stops. Deliberately does NOT
    flag a group where every branch ends the same way (including "just stops"):
    almost every topic legitimately ends a branch with a plain message, so
    flagging that universally drowns real findings in noise (see L-UNREACHABLE-
    adjacent design note in lint_agent.py's check_orchestration). Flagging only
    the inconsistent case targets the higher-confidence "forgot a branch" shape.
    """
    found: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        if str(data.get("kind", "")).lower() == "conditiongroup":
            conditions = data.get("conditions") if isinstance(data.get("conditions"), list) else []
            branches = [c.get("actions") for c in conditions if isinstance(c, dict)]
            if isinstance(data.get("elseActions"), list):
                branches.append(data["elseActions"])
            if len(branches) >= 2:
                terminated = [_branch_terminates(b) for b in branches]
                if any(terminated) and not all(terminated):
                    label = data.get("id") or path or "condition group"
                    found.append({
                        "group": str(label),
                        "branches": len(branches),
                        "unterminated": terminated.count(False),
                    })
        for k, v in data.items():
            found.extend(_find_unterminated_branch_groups(v, path=str(k)))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            found.extend(_find_unterminated_branch_groups(item, path=f"{path}[{i}]"))
    return found


# OData-style query parameters a connector action might expose.
_ODATA_PARAM_TOKEN_RE = re.compile(r"(['\"]?)(\$[A-Za-z]+)\1?")


def _scan_odata_quote_issues(text: str) -> List[Dict[str, str]]:
    """Flag inconsistent quoting of $-prefixed connector parameters within the
    same component -- e.g. some references doubly-quoted ('$filter' embedded
    inside the YAML string) and others bare. Cannot verify a single universal
    "correct" form without the specific connector's documentation, so this
    reports the inconsistency for the maker to confirm rather than asserting
    which side is wrong.
    """
    styles: Dict[str, Set[str]] = {}
    for m in re.finditer(r"(\"'?\$[A-Za-z]+'?\"|'\$[A-Za-z]+'|\$[A-Za-z]+)", text):
        token = m.group(0)
        param = re.search(r"\$[A-Za-z]+", token).group(0).lower()
        if token.count("'") >= 2 or (token.startswith("'") and token.endswith("'")):
            style = "double-quoted (embedded single-quotes)"
        elif "'" in token:
            style = "mixed"
        else:
            style = "bare"
        styles.setdefault(param, set()).add(style)
    return [
        {"param": param, "styles": ", ".join(sorted(seen))}
        for param, seen in sorted(styles.items())
        if len(seen) > 1
    ]


def _merge_topic(model: Dict[str, Any], topic: Dict[str, Any]) -> None:
    for existing in model["topics"]:
        if existing["name"] == topic["name"]:
            existing["trigger_phrases"] = sorted(
                set(existing["trigger_phrases"]) | set(topic["trigger_phrases"])
            )
            existing["node_count"] = max(existing["node_count"], topic["node_count"])
            existing["variables_set"] = sorted(
                set(existing["variables_set"]) | set(topic["variables_set"])
            )
            existing["variables_read"] = sorted(
                set(existing["variables_read"]) | set(topic["variables_read"])
            )
            existing["power_fx_unknown_functions"] = sorted(
                set(existing["power_fx_unknown_functions"]) | set(topic["power_fx_unknown_functions"])
            )
            existing["power_fx_syntax_issues"] = (
                existing["power_fx_syntax_issues"] + topic["power_fx_syntax_issues"]
            )
            existing["unterminated_branch_groups"] = (
                existing["unterminated_branch_groups"] + topic["unterminated_branch_groups"]
            )
            existing["odata_quote_issues"] = (
                existing["odata_quote_issues"] + topic["odata_quote_issues"]
            )
            existing["has_on_outgoing_message_trigger"] = (
                existing["has_on_outgoing_message_trigger"] or topic["has_on_outgoing_message_trigger"]
            )
            existing["source_file"] = existing["source_file"] or topic["source_file"]
            return
    model["topics"].append(topic)


# --------------------------------------------------------------------------
# Configuration derivation
# --------------------------------------------------------------------------

def derive_configuration(model: Dict[str, Any]) -> None:
    names = [t["name"].lower() for t in model["topics"]]
    joined = " ".join(names)

    if model["topics"]:
        model["configuration"]["fallback_configured"] = "fallback" in joined
        model["configuration"]["escalation_configured"] = (
            "escalate" in joined or "escalation" in joined
        )
        model["configuration"]["welcome_message"] = (
            "greeting" in joined or "conversationstart" in joined.replace(" ", "")
        )

    if model["agent"]["orchestration_mode"] is None:
        has_skills = bool(model["skills"])
        has_topics = bool(model["topics"])
        # A modernized generative core can show up with no InlineAgentSkill
        # components at all — as connected agents, request/result contracts, or
        # a GptComponentMetadata orchestrator component — so treat any of those
        # the same as "has_skills" for mode purposes (SKILL.md's "classic system
        # topics plus a generative core" hybrid shape).
        has_modernized_core = (
            bool(model["connected_agents"]) or bool(model["contracts"])
            or bool(model["agent"].get("other_components", {}).get("GptComponentMetadata"))
        )
        if (has_skills or has_modernized_core) and has_topics:
            model["agent"]["orchestration_mode"] = "hybrid"
        elif has_skills or has_modernized_core:
            model["agent"]["orchestration_mode"] = "agentic"
        elif has_topics:
            generative = sum(1 for t in model["topics"] if t.get("is_generative"))
            model["agent"]["orchestration_mode"] = (
                "generative" if generative > len(model["topics"]) / 3 else "classic"
            )

    seen: Dict[str, Dict[str, Any]] = {}
    for t in model["topics"]:
        sys = t.get("is_system_topic", False)
        for v in t["variables_set"]:
            e = seen.setdefault(v, {"name": v, "set_in": [], "read_in": [], "only_system": True})
            e["set_in"].append(t["name"])
            if not sys:
                e["only_system"] = False
        for v in t["variables_read"]:
            e = seen.setdefault(v, {"name": v, "set_in": [], "read_in": [], "only_system": True})
            e["read_in"].append(t["name"])
            if not sys:
                e["only_system"] = False
    model["variables"] = list(seen.values())

    parsed = len(model["source"]["parsed_files"])
    has_content = bool(model["topics"]) or bool(model["skills"])
    model["parse_report"]["complete"] = (
        parsed > 0 and has_content and not model["parse_report"]["unreadable"]
    )

    if not has_content:
        model["parse_report"]["warnings"].append(
            "No topics or agent skills were extracted. The export layout may differ "
            "from expected shapes, or the file may not be a Copilot Studio agent export."
        )


# --------------------------------------------------------------------------
# Entry
# --------------------------------------------------------------------------

def ingest(path: Path, verbose: bool) -> Dict[str, Any]:
    model = empty_model()
    model["source"]["path"] = str(path)
    fmt = detect_format(path)

    if fmt == "botcomponents_dir":
        ingest_botcomponents_dir(path, model, verbose)
    elif fmt == "solution_zip":
        ingest_solution_zip(path, model, verbose)
    elif fmt == "agent_yaml":
        text = path.read_text(encoding="utf-8", errors="replace")
        model["source"]["format"] = "copilot_studio_agent_yaml"
        model["source"]["parsed_files"].append(path.name)
        parse_topic_yaml(text, path.name, model, verbose, source_file=path.name)
    elif fmt == "directory":
        model["source"]["format"] = "directory"
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() in YAML_EXTS:
                sub = ingest(child, verbose)
                _merge_models(model, sub)
    else:
        model["parse_report"]["unreadable"].append(
            f"{path.name}: unrecognised format. Supported: .zip, .yaml, .yml, or a directory."
        )

    derive_configuration(model)
    return model


def _merge_models(base: Dict[str, Any], other: Dict[str, Any]) -> None:
    base["source"]["parsed_files"].extend(other["source"]["parsed_files"])
    for t in other["topics"]:
        _merge_topic(base, t)
    if other["agent"]["name"] and not base["agent"]["name"]:
        base["agent"]["name"] = other["agent"]["name"]
    base["parse_report"]["warnings"].extend(other["parse_report"]["warnings"])
    base["parse_report"]["unreadable"].extend(other["parse_report"]["unreadable"])


def main() -> int:
    # See lint_agent.py's main() for why this guards against a console
    # encoding crash when output is redirected/piped on Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Ingest a Copilot Studio agent export for linting.")
    ap.add_argument("path", help="Path to export (.zip, .yaml, .yml, or a directory)")
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
    print(f"  mode:     {model['agent'].get('orchestration_mode')}")
    print(f"  topics:   {len(model['topics'])}")
    print(f"  skills:   {len(model['skills'])}")
    print(f"  tools:    {len(model['tools'])}")
    print(f"  complete: {rep['complete']}")
    for w in rep["warnings"]:
        print(f"  WARNING: {w}")
    for u in rep["unreadable"]:
        print(f"  UNREADABLE: {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
