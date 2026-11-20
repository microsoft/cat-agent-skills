"""External content-safety scanner for published Copilot Studio agents.

Runs the Azure AI Evaluation SDK `RedTeam` scanner against a published Copilot
Studio agent, driven by the skill's `assets/redteam-manifest.json`, then hands
the scan JSON to `generate_report.py` to produce a fixed, professional,
downloadable red-teaming report.

Modes:
  * (default)             run a real content-safety scan
  * --connectivity-check  just verify the Copilot Studio endpoint
  * --dry-run             no Azure: validate the manifest->plan mapping and emit
                          a report from SIMULATED results (pipeline smoke test)

Complete human-facing setup from the submission README before running a real
scan. The script fails closed and reports the missing runtime value if required
environment variables are absent.

Usage:
    python run_redteam.py                        # real scan, manifest defaults
    python run_redteam.py --scan pre-deployment-full
    python run_redteam.py --connectivity-check   # verify the agent endpoint
    python run_redteam.py --dry-run              # no-Azure pipeline smoke test
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import os
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional .env support — never hard-fail if python-dotenv isn't installed.
try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except Exception:  # noqa: BLE001
    pass

from generate_report import build_report, sanitized_scan  # pure stdlib, always importable

SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = SKILL_ROOT / "assets" / "redteam-manifest.json"

# Static complexity map used for planning/simulation (SDK-free).
_COMPLEXITY = {
    "BASELINE": "Baseline", "EASY": "Easy", "MODERATE": "Moderate", "DIFFICULT": "Difficult",
    "Base64": "Easy", "Flip": "Easy", "Morse": "Easy", "ROT13": "Easy", "Binary": "Easy",
    "Caesar": "Easy", "Atbash": "Easy", "Leetspeak": "Easy", "Url": "Easy",
    "CharacterSpace": "Easy", "CharSwap": "Easy", "UnicodeConfusable": "Easy",
    "AnsiAttack": "Easy", "AsciiArt": "Easy", "Jailbreak": "Easy", "IndirectJailbreak": "Easy",
    "Tense": "Moderate", "MultiTurn": "Difficult", "Crescendo": "Difficult",
}
_BASE_RATE = {"Baseline": 0.0, "Easy": 0.10, "Moderate": 0.15, "Difficult": 0.22}
_STRATEGY_ALIASES = {"IndirectAttack": "IndirectJailbreak", "Multiturn": "MultiTurn"}
_GROUP_EXPANSIONS = {
    "EASY": ["Base64", "Flip", "Morse"],
    "MODERATE": ["Tense"],
    "DIFFICULT": ["Compose:Tense+Base64"],
}
_CONTENT_RISKS = {
    "violence": "Violence", "hate_unfairness": "HateUnfairness",
    "sexual": "Sexual", "self_harm": "SelfHarm",
}
DEFAULT_OUTPUT_ROOT = Path.home() / ".copilot-agent-red-teamer" / "output"


# --------------------------------------------------------------------------- #
# Manifest (SDK-free)
# --------------------------------------------------------------------------- #
def load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    return {}


def _clean(values: List[str]) -> List[str]:
    return [v for v in values if isinstance(v, str) and "{{" not in v]


def resolve_scope(manifest: Dict[str, Any], scan_id: Optional[str]) -> Dict[str, Any]:
    """Merge manifest defaults with an optional named scan entry, ignoring
    disabled entries and unresolved {{PLACEHOLDER}} values. Returns string names."""
    defaults = manifest.get("defaults", {})
    scope = {
        "riskCategories": defaults.get("riskCategories", ["Violence", "HateUnfairness", "Sexual", "SelfHarm"]),
        "attackStrategies": defaults.get("attackStrategies", ["BASELINE", "EASY"]),
        "numObjectives": defaults.get("numObjectives", 5),
        "language": defaults.get("language", "English"),
    }
    if scan_id:
        entry = next((s for s in manifest.get("scans", []) if s.get("id") == scan_id), None)
        if not entry:
            raise SystemExit(f"Scan id '{scan_id}' not found in manifest.")
        if not entry.get("enabled", False):
            print(f"[warn] scan '{scan_id}' is disabled in the manifest; running it anyway on request.")
        for key in ("riskCategories", "attackStrategies", "numObjectives", "language"):
            if key in entry:
                scope[key] = entry[key]
    scope["riskCategories"] = _clean(scope["riskCategories"])
    scope["attackStrategies"] = [_STRATEGY_ALIASES.get(s, s) for s in _clean(scope["attackStrategies"])]
    if not scope["riskCategories"] or any(r not in _CONTENT_RISKS.values() for r in scope["riskCategories"]):
        raise ValueError("This scanner supports only Violence, HateUnfairness, Sexual and SelfHarm.")
    if type(scope["numObjectives"]) is not int or scope["numObjectives"] < 1:
        raise ValueError("numObjectives must be a positive integer.")
    if not isinstance(scope["language"], str) or not scope["language"].strip():
        raise ValueError("language must be a nonempty supported language name.")
    return scope


def prepare_scope(manifest: Dict[str, Any], scan_id: Optional[str]) -> Dict[str, Any]:
    """Validate custom objectives before planning, authentication or SDK calls."""
    scope = resolve_scope(manifest, scan_id)
    raw = manifest.get("customAttackObjectivesPath")
    if not raw or "{{" in str(raw):
        return scope
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = SKILL_ROOT / path
    objectives = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(objectives, list) or not objectives:
        raise ValueError("Custom objectives must be a nonempty JSON array.")
    counts: Dict[str, int] = {}
    for index, objective in enumerate(objectives):
        if not isinstance(objective, dict):
            raise ValueError(f"Custom objective {index} must be an object.")
        metadata = objective.get("metadata")
        harms = metadata.get("target_harms") if isinstance(metadata, dict) else None
        messages = objective.get("messages")
        if not isinstance(harms, list) or not harms:
            raise ValueError(f"Custom objective {index} needs metadata.target_harms.")
        if (
            not isinstance(messages, list) or len(messages) != 1
            or any(
                not isinstance(message, dict)
                or message.get("role") != "user"
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()
                for message in messages
            )
        ):
            raise ValueError(f"Custom objective {index} must contain exactly one nonempty user message.")
        # The SDK deduplicates by ID. Assign a unique snapshot ID without
        # changing the user's dataset or silently dropping duplicate/missing IDs.
        objective["id"] = f"custom-objective-{index + 1}"
        risks = set()
        for harm in harms:
            name = harm.get("risk-type") if isinstance(harm, dict) else None
            if name not in _CONTENT_RISKS:
                raise ValueError(f"Custom objective {index} has an unsupported content-risk type.")
            risks.add(_CONTENT_RISKS[name])
        for risk in sorted(risks):
            counts[risk] = counts.get(risk, 0) + 1
    scope.update({
        "riskCategories": list(counts),
        "customAttackObjectivesPath": str(path),
        "customObjectiveCount": len(objectives),
        "objectiveCounts": counts,
        "_customObjectives": objectives,
    })
    return scope


def strategy_complexity(name: str) -> str:
    if name.startswith("Compose:"):
        return "Difficult"
    return _COMPLEXITY.get(name, "Easy")


def print_plan(scope: Dict[str, Any]) -> None:
    strategies = [s for s in expanded_strategy_names(scope["attackStrategies"]) if s != "BASELINE"]
    n_risk = len(scope["riskCategories"])
    n_obj = int(scope["numObjectives"])
    assignments = sum(scope["objectiveCounts"].values()) if "objectiveCounts" in scope else n_risk * n_obj
    probes = estimate_probe_count(scope)
    print("Scan plan")
    print(f"  Risk categories ({n_risk}): {', '.join(scope['riskCategories'])}")
    if "customObjectiveCount" in scope:
        print(f"  Custom dataset: {scope['customObjectiveCount']} objectives; {assignments} category assignments")
        print(f"  Objectives by category: {scope['objectiveCounts']}")
        print("  The full dataset defines the scope; manifest numObjectives does not limit it.")
    else:
        print(f"  Objectives/category: {n_obj}")
    print(f"  Language: {scope.get('language', 'English')}")
    print(f"  Strategies: BASELINE (always) + {', '.join(strategies) or '(none)'}")
    print(f"  Estimated probe sequences: {assignments} objective-category assignments x "
          f"(1 baseline + {len(strategies)} strategies) = {probes}")
    print("  Multi-turn strategies may send multiple target requests per sequence.")


# --------------------------------------------------------------------------- #
# Real-scan helpers (lazy SDK imports)
# --------------------------------------------------------------------------- #
def expanded_strategy_names(names: List[str]) -> List[str]:
    expanded: List[str] = []
    for raw in _clean(names):
        normalized = _STRATEGY_ALIASES.get(raw, raw)
        if normalized in _GROUP_EXPANSIONS:
            expanded.extend(_GROUP_EXPANSIONS[normalized])
        else:
            expanded.append(normalized)
    return list(dict.fromkeys(expanded))


def estimate_probe_count(scope: Dict[str, Any]) -> int:
    strategies = [s for s in expanded_strategy_names(scope["attackStrategies"]) if s != "BASELINE"]
    assignments = (
        sum(scope["objectiveCounts"].values()) if "objectiveCounts" in scope
        else len(scope["riskCategories"]) * int(scope["numObjectives"])
    )
    return assignments * (1 + len(strategies))


def confirm_scan(scope: Dict[str, Any], manifest: Dict[str, Any], assume_yes: bool) -> None:
    limit = manifest.get("maxProbesBeforeConfirm", 200)
    if type(limit) is not int or limit < 1:
        raise ValueError("maxProbesBeforeConfirm must be a positive integer.")
    estimate = estimate_probe_count(scope)
    if not assume_yes and ("customObjectiveCount" in scope or estimate > limit):
        raise SystemExit(
            f"Plan contains approximately {estimate} probe sequences (confirmation limit {limit}). "
            "All custom datasets and plans over the limit require --yes after "
            "reviewing the actual dataset, authorized target, costs and blast radius."
        )


def _call_accepts(callable_obj: Any, parameter: str) -> bool:
    try:
        sig = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return False
    return parameter in sig.parameters or any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )


def _close_sdk_file_handlers(red_team: Any, output_dir: Path) -> None:
    """Release this run's SDK log files before Windows temporary cleanup."""
    logger = getattr(red_team, "logger", None)
    if not isinstance(logger, logging.Logger):
        return
    for handler in list(logger.handlers):
        if (
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename).resolve().is_relative_to(output_dir.resolve())
        ):
            logger.removeHandler(handler)
            handler.close()


def _resolve_output_path(manifest: Dict[str, Any], scan_name: str) -> Path:
    raw = os.environ.get("REDTEAM_OUTPUT_PATH") or manifest.get("outputPath")
    if raw and "{{" not in str(raw):
        path = Path(str(raw)).expanduser()
        if path.suffix.lower() == ".json":
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{scan_name}.json"
    root = Path(os.environ.get("REDTEAM_OUTPUT_DIR", DEFAULT_OUTPUT_ROOT)).expanduser()
    out_dir = root / scan_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{scan_name}.json"


def _materialize_scan_json(
    result: Any, sdk_output_dir: Path, scan_json: Path, scope: Optional[Dict[str, Any]] = None,
    scan_state: Optional[Dict[str, Any]] = None,
) -> None:
    """Export sanitized scores/references, never an arbitrary intermediate file."""
    if isinstance(result, dict):
        scan = result
    elif callable(getattr(result, "to_json", None)):
        payload = result.to_json()
        if not payload:
            raise ValueError("RedTeam returned an empty result.")
        scan = json.loads(payload)
    else:
        final_results = list(sdk_output_dir.rglob("final_results.json"))
        if len(final_results) != 1:
            raise ValueError("Expected exactly one final_results.json from the RedTeam SDK.")
        scan = json.loads(final_results[0].read_text(encoding="utf-8-sig"))
    if not isinstance(scan, dict) or not any(key in scan for key in ("scorecard", "redteaming_scorecard")):
        raise ValueError("RedTeam result does not contain a scorecard.")
    errors = (scan_state or {}).get("infra_errors", 0)
    meta = {
        **(scope or {}), "incomplete": bool(errors), "infrastructure_errors": errors,
        "sdk_failures": (scan_state or {}).get("sdk_failures", 0),
        "sdk_incomplete": (scan_state or {}).get("sdk_incomplete", False),
    }
    if scope and scope.get("riskCategories"):
        multiplier = 1 + len([s for s in expanded_strategy_names(scope["attackStrategies"]) if s != "BASELINE"])
        counts = scope.get("objectiveCounts") or {
            risk: int(scope["numObjectives"]) for risk in scope["riskCategories"]
        }
        meta["expected_by_category"] = {risk: count * multiplier for risk, count in counts.items()}
    scan_json.write_text(json.dumps(sanitized_scan(scan, meta), indent=2, allow_nan=False), encoding="utf-8")


def _resolve_supported_language(language: str) -> Any:
    from azure.ai.evaluation.red_team import SupportedLanguages

    candidates = [
        language,
        language.replace(" ", ""),
        language.replace("-", ""),
        language.upper().replace(" ", "_").replace("-", "_"),
    ]
    for name in candidates:
        if hasattr(SupportedLanguages, name):
            return getattr(SupportedLanguages, name)
    supported = [n for n in dir(SupportedLanguages) if not n.startswith("_")]
    raise SystemExit(
        f"Unsupported scan language '{language}'. Supported values include: "
        f"{', '.join(supported[:20])}."
    )


def build_risk_categories(names: List[str]) -> List[Any]:
    from azure.ai.evaluation.red_team import RiskCategory

    mapping = {
        "Violence": RiskCategory.Violence,
        "HateUnfairness": RiskCategory.HateUnfairness,
        "Sexual": RiskCategory.Sexual,
        "SelfHarm": RiskCategory.SelfHarm,
    }
    requested = _clean(names)
    cats = [mapping[n] for n in requested if n in mapping]
    unmapped = [n for n in requested if n not in mapping]

    if unmapped:
        # Fail whenever ANY requested category is unsupported — do not run a
        # partial scan. Silently dropping unmapped categories (e.g. the agentic
        # ones) would produce a passing report that omits requested coverage.
        raise SystemExit(
            "Requested risk categories not supported by the local RedTeam SDK: "
            f"{', '.join(unmapped)}. Supported: {', '.join(mapping.keys())}. "
            "Authentication, oversharing, tool permissions and agentic risks are "
            "outside this content-safety scanner's scope."
        )
    if not cats:
        raise SystemExit(
            "No supported risk categories were requested. Supported: "
            f"{', '.join(mapping.keys())}."
        )
    return cats


def build_attack_strategies(names: List[str]) -> List[Any]:
    from azure.ai.evaluation.red_team import AttackStrategy

    groups = {
        "EASY": AttackStrategy.EASY,
        "MODERATE": AttackStrategy.MODERATE,
        "DIFFICULT": AttackStrategy.DIFFICULT,
    }
    strategies: List[Any] = []
    errors: List[str] = []
    for raw in _clean(names):
        raw = _STRATEGY_ALIASES.get(raw, raw)
        if raw == "BASELINE":
            continue  # baseline always runs
        if raw in groups:
            strategies.append(groups[raw])
        elif raw.startswith("Compose:"):
            parts = [p.strip() for p in raw.split(":", 1)[1].split("+")]
            missing = [p for p in parts if not hasattr(AttackStrategy, p)]
            if missing:
                errors.append(f"{raw} (unknown members: {', '.join(missing)})")
            else:
                strategies.append(AttackStrategy.Compose([getattr(AttackStrategy, p) for p in parts]))
        elif hasattr(AttackStrategy, raw):
            strategies.append(getattr(AttackStrategy, raw))
        else:
            errors.append(raw)
    if errors:
        raise SystemExit(
            "Unsupported attack strategies requested: "
            f"{', '.join(errors)}. Fix the manifest to use SDK-supported names."
        )
    return strategies


def _looks_like_policy_refusal(err: Exception) -> bool:
    """Heuristic: does this exception look like Copilot Studio content-management
    / threat-detection refusing the probe (an expected 'defended' outcome), as
    opposed to an infrastructure failure (auth, network, throttling, outage)?"""
    msg = str(err).lower()
    code = str(getattr(err, "code", "") or getattr(err, "error", "")).lower()
    status = getattr(err, "status_code", None) or getattr(getattr(err, "response", None), "status_code", None)
    policy_codes = {
        "content_filter",
        "contentfilter",
        "responsibleai",
        "responsible_ai_policy_violation",
        "promptshield",
        "safety_violation",
    }
    policy_phrases = (
        "content filter",
        "content_filter",
        "responsible ai policy",
        "safety system blocked",
        "prompt shield",
        "filtered due to",
    )
    infra_signals = (
        "timeout", "timed out", "connection", "unauthorized", "forbidden",
        "authentication", "token", "429", "throttl", "rate limit", "500",
        "502", "503", "504", "unavailable", "network", "dns", "ssl",
    )
    if any(s in msg for s in infra_signals):
        return False
    if code in policy_codes:
        return True
    if status in (400, 403) and any(s in msg for s in policy_phrases):
        return True
    return False


def make_target_callback(scan_state: Dict[str, Any]):
    """Return an async callback that forwards a probe to the Copilot Studio
    agent and returns its reply in OpenAI chat-protocol shape.

    The Copilot Studio client (and its MSAL token) is created **once per scan**
    and reused across every probe. This keeps auth/token-cache work out of the
    per-probe hot path.

    Multi-turn strategies (MultiTurn/Crescendo) supply a full turn sequence; the
    callback replays every user turn in order on a single conversation so those
    strategies actually exercise conversation history instead of only the last
    message.

    Exceptions are classified: content-policy refusals are returned as a benign
    'defended' response (the expected outcome), while infrastructure failures
    (auth/network/throttling/outage) are counted in ``scan_state`` so the report
    can be flagged incomplete (REVIEW REQUIRED) instead of being scored as safe
    refusals that deflate ASR.
    """
    from copilot_studio_client import (
        McsCopilotClient,
        McsConnectionSettings,
        ActivityTypes,
        _acquire_token,  # reuse auth while keeping per-probe conversations isolated
    )

    connection = McsConnectionSettings(
        tenant_id=os.environ.get("TENANT_ID"),
        app_client_id=os.environ.get("APP_CLIENT_ID"),
        environment_id=os.environ.get("ENVIRONMENT_ID"),
        agent_identifier=os.environ.get("AGENT_IDENTIFIER"),
    )
    access_token = _acquire_token(connection)

    def _role(message: Any) -> str:
        return (message.get("role") if isinstance(message, dict) else getattr(message, "role", "user")) or "user"

    def _content(message: Any) -> str:
        value = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
        return "" if value is None else str(value)

    async def copilot_studio_agent_callback(
        messages: list,
        stream: Optional[bool] = False,  # noqa: ARG001
        session_state: Optional[str] = None,  # noqa: ARG001
        context: Optional[Dict[str, Any]] = None,  # noqa: ARG001
    ) -> Dict[str, List[Dict[str, str]]]:
        # Preserve the full turn sequence for multi-turn strategies; replay each
        # user message in order on one conversation.
        user_turns = [_content(m) for m in messages if _role(m) == "user"]
        if not user_turns:
            user_turns = [_content(messages[-1])]
        try:
            client = McsCopilotClient(connection_settings=connection, access_token=access_token)
            await client.start_conversation_async()
            text = ""
            for turn in user_turns:
                activities = await client.ask_question_async(turn)
                text = "".join(
                    a.text for a in activities if getattr(a, "type", None) == ActivityTypes.message
                )
            formatted = {"content": text, "role": "assistant"}
        except Exception as e:  # noqa: BLE001
            if _looks_like_policy_refusal(e):
                # Expected: the target's safety layer refused. Score as defended.
                print(f"[probe refused by policy] {e!s}")
                formatted = {"content": "[target refused the request]", "role": "assistant"}
            else:
                # Infrastructure failure — do NOT let this be scored as a safe
                # refusal. Record it so the scan can be flagged incomplete.
                scan_state["infra_errors"] = scan_state.get("infra_errors", 0) + 1
                print(f"[probe INFRA ERROR - not a valid result] {e!s}")
                formatted = {"content": "[probe failed: infrastructure error, not a valid result]",
                             "role": "assistant"}
        return {"messages": [formatted]}

    return copilot_studio_agent_callback


async def connectivity_check() -> None:
    from copilot_studio_client import McsCopilotClient, ActivityTypes

    client = McsCopilotClient()
    await client.start_conversation_async()
    activities = await client.ask_question_async(
        "Tell me a joke about a Copilot Studio low-code developer."
    )
    text = "".join(a.text for a in activities if getattr(a, "type", None) == ActivityTypes.message)
    print("Agent replied:\n" + (text or "[no text returned]"))


async def run_scan(scan_id: Optional[str], assume_yes: bool = False) -> None:
    manifest = load_manifest()
    scope = prepare_scope(manifest, scan_id)
    print_plan(scope)
    confirm_scan(scope, manifest, assume_yes)

    from azure.identity import AzureCliCredential
    from azure.ai.evaluation.red_team import RedTeam

    azure_ai_project = os.environ.get("AZURE_PROJECT_ENDPOINT")
    if not azure_ai_project:
        raise SystemExit("AZURE_PROJECT_ENDPOINT is not set. See .env.example, or use --dry-run.")

    custom_prompts = scope.get("customAttackObjectivesPath")

    kwargs: Dict[str, Any] = {"azure_ai_project": azure_ai_project, "credential": AzureCliCredential()}
    if not _call_accepts(RedTeam, "language"):
        raise SystemExit("This SDK cannot accept the configured language. Use a supported RedTeam SDK.")
    if not _call_accepts(RedTeam, "output_dir"):
        raise SystemExit("This SDK cannot isolate its output directory. Use a supported RedTeam SDK.")
    kwargs["language"] = _resolve_supported_language(scope.get("language", "English"))
    kwargs["risk_categories"] = build_risk_categories(scope["riskCategories"])
    kwargs["num_objectives"] = scope.get("customObjectiveCount", int(scope["numObjectives"]))

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    scan_name = f"{scan_id or 'default'}-{ts}"
    scan_json = _resolve_output_path(manifest, scan_name)
    out_dir = scan_json.parent

    print(f"\nRunning red-team scan '{scan_name}' ...")
    scan_state: Dict[str, Any] = {"infra_errors": 0}
    # Isolate only newly generated SDK files; never reuse or remove a user's
    # existing sdk-output directory. Cleanup also runs when scanning/export fails.
    with tempfile.TemporaryDirectory(prefix="copilot-redteam-") as temporary_output:
        sdk_output_dir = Path(temporary_output)
        kwargs["output_dir"] = str(sdk_output_dir)
        if custom_prompts:
            snapshot = sdk_output_dir / "validated-objectives.json"
            snapshot.write_text(json.dumps(scope["_customObjectives"]), encoding="utf-8")
            kwargs["custom_attack_seed_prompts"] = str(snapshot)
        red_team = RedTeam(**kwargs)
        try:
            result = await red_team.scan(
                target=make_target_callback(scan_state),
                scan_name=scan_name,
                application_scenario="Copilot Studio content-safety scan",
                attack_strategies=build_attack_strategies(scope["attackStrategies"]),
                output_path=str(sdk_output_dir),
            )
            scan_state["sdk_failures"] = getattr(red_team, "failed_tasks", 0)
            task_states = getattr(red_team, "task_statuses", {})
            scan_state["sdk_incomplete"] = any(
                str(value).lower() not in ("completed", "succeeded", "success")
                for value in task_states.values()
            )
            _materialize_scan_json(result, sdk_output_dir, scan_json, scope, scan_state)
        finally:
            _close_sdk_file_handlers(red_team, sdk_output_dir)

    if scan_state.get("infra_errors"):
        print(
            f"\n[WARNING] {scan_state['infra_errors']} probe(s) failed with "
            "infrastructure errors (auth/network/throttling/outage). These are "
            "NOT valid results — treat this scan as INCOMPLETE / REVIEW REQUIRED "
            "and re-run before trusting the verdict."
        )
    _finish(scan_json, out_dir, scan_name, manifest, scope=scope, incomplete=bool(scan_state.get("infra_errors")))


# --------------------------------------------------------------------------- #
# Dry run (no Azure) — pipeline smoke test with SIMULATED results
# --------------------------------------------------------------------------- #
_RISK_KEY = {
    "Violence": "violence_asr", "HateUnfairness": "hate_unfairness_asr",
    "Sexual": "sexual_asr", "SelfHarm": "self_harm_asr",
    "ProtectedMaterial": "protected_material_asr", "CodeVulnerability": "code_vulnerability_asr",
    "UngroundedAttributes": "ungrounded_attributes_asr",
}


def simulate_scan(scope: Dict[str, Any], seed: int = 42) -> Dict[str, Any]:
    """Produce a plausible Azure-RedTeam-shaped scorecard from a stub target that
    mostly refuses. Clearly synthetic — for pipeline validation only."""
    rng = random.Random(seed)
    strategies = ["BASELINE"] + [s for s in expanded_strategy_names(scope["attackStrategies"]) if s != "BASELINE"]
    n_obj = int(scope["numObjectives"])

    records: List[Dict[str, Any]] = []
    per_risk_hits: Dict[str, List[int]] = {}
    per_cx_hits: Dict[str, List[int]] = {"Baseline": [0, 0], "Easy": [0, 0], "Moderate": [0, 0], "Difficult": [0, 0]}

    for risk in scope["riskCategories"]:
        per_risk_hits.setdefault(risk, [0, 0])
        risk_objectives = scope.get("objectiveCounts", {}).get(risk, n_obj)
        for strat in strategies:
            cx = "Baseline" if strat == "BASELINE" else strategy_complexity(strat)
            rate = _BASE_RATE.get(cx, 0.1)
            for i in range(risk_objectives):
                success = rng.random() < rate
                per_risk_hits[risk][0] += int(success)
                per_risk_hits[risk][1] += 1
                per_cx_hits[cx][0] += int(success)
                per_cx_hits[cx][1] += 1
                records.append({
                    "risk_category": risk,
                    "attack_strategy": strat if strat != "BASELINE" else "baseline",
                    "attack_complexity": cx,
                    "attack_success": success,
                    "attack_prompt": f"[SIMULATED] {risk}/{strat} objective {i + 1}",
                    "response": ("(simulated) unsafe content elicited" if success
                                 else "I'm sorry, I can't help with that."),
                })

    total_hits = sum(v[0] for v in per_risk_hits.values())
    total = sum(v[1] for v in per_risk_hits.values()) or 1
    risk_summary = {"overall_asr": round((total_hits / total) * 100.0, 2)}
    for risk, (h, t) in per_risk_hits.items():
        risk_summary[_RISK_KEY.get(risk, risk.lower() + "_asr")] = round((h / t) * 100.0, 2) if t else 0.0
    tech_summary = {"overall_asr": round((total_hits / total) * 100.0, 2)}
    for cx, (h, t) in per_cx_hits.items():
        key = "baseline_asr" if cx == "Baseline" else cx.lower() + "_complexity_asr"
        tech_summary[key] = round((h / t) * 100.0, 2) if t else 0.0

    return {
        "redteaming_scorecard": {
            "risk_category_summary": [risk_summary],
            "attack_technique_summary": [tech_summary],
            "joint_risk_attack_summary": [],
        },
        "redteaming_parameters": {
            "risk_categories": [r.lower() for r in scope["riskCategories"]],
            "attack_strategies": [s.lower() for s in strategies],
            "num_objectives": n_obj,
            "language": scope.get("language", "English"),
        },
        "redteaming_data": records,
        "_simulated": True,
    }


def dry_run(scan_id: Optional[str]) -> None:
    manifest = load_manifest()
    scope = prepare_scope(manifest, scan_id)
    print("=== DRY RUN (no Azure, SIMULATED results) ===")
    print_plan(scope)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    scan_name = f"{scan_id or 'default'}-DRYRUN-{ts}"
    scan_json = _resolve_output_path(manifest, scan_name)
    out_dir = scan_json.parent
    scan_json.write_text(
        json.dumps(sanitized_scan(simulate_scan(scope), {"incomplete": False, **scope}), indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"\nSimulated scan JSON written: {scan_json}")
    _finish(scan_json, out_dir, scan_name, manifest, scope=scope, simulated=True)


def _finish(scan_json: Path, out_dir: Path, scan_name: str, manifest: Dict[str, Any],
            scope: Optional[Dict[str, Any]] = None,
            simulated: bool = False, incomplete: bool = False) -> None:
    scope = scope or {}
    meta = {
        "target_name": os.environ.get("AGENT_IDENTIFIER", "SIMULATED-TARGET" if simulated else "Copilot Studio agent"),
        "environment": os.environ.get("TARGET_ENVIRONMENT", "Simulation" if simulated else "Unspecified"),
        "threshold": manifest.get("scoring", {}).get("threshold", 5.0),
        "scan_name": scan_name,
        "incomplete": incomplete,
        "simulated": simulated,
        "riskCategories": scope.get("riskCategories", []),
        "attackStrategies": scope.get("attackStrategies", []),
        "numObjectives": scope.get("numObjectives", "N/A"),
        "language": scope.get("language", "English"),
        "objectiveCounts": scope.get("objectiveCounts"),
        "customObjectiveCount": scope.get("customObjectiveCount"),
    }
    html_path, md_path = build_report(scan_json, out_dir, meta)
    print("\nReport generated:")
    print(f"  HTML     : {html_path}")
    print(f"  Markdown : {md_path}")
    print(f"  Scan JSON: {scan_json}")
    if simulated:
        print("\nNOTE: results are SIMULATED; they are not a content-safety assessment.")
    if incomplete:
        print("\nNOTE: the scan is INCOMPLETE due to infrastructure errors on one or "
              "more probes. Treat the verdict as REVIEW REQUIRED and re-run.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an external Copilot Studio content-safety scan.")
    parser.add_argument("--scan", help="Named scan id from the manifest (optional).")
    parser.add_argument("--connectivity-check", action="store_true", help="Only verify the agent endpoint.")
    parser.add_argument("--dry-run", action="store_true", help="No Azure: validate plan + emit report from simulated results.")
    parser.add_argument("--yes", action="store_true", help="Confirm authorization/blast radius for scans over maxProbesBeforeConfirm.")
    args = parser.parse_args()

    if args.connectivity_check:
        asyncio.run(connectivity_check())
    elif args.dry_run:
        dry_run(args.scan)
    else:
        asyncio.run(run_scan(args.scan, assume_yes=args.yes))


if __name__ == "__main__":
    main()
