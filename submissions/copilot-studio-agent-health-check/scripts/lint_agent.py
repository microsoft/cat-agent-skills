#!/usr/bin/env python3
"""
Copilot Studio Agent Health Check — deterministic structural checks.

Reads a normalised agent model (from ingest_agent.py) and emits a findings list.
Every finding is a structural fact about the artifact, decidable from the export
alone and true regardless of what ships in the platform next quarter. That
durability is the whole point: a trigger collision is a trigger collision
forever, so this linter does not go stale the way capability or pricing advice does.

Findings carry a tier, a severity, evidence, and a one-line fix:
  - tier "correctness" — will cause a user-visible failure or broken behaviour
  - tier "hygiene"     — maintainability / clarity; safe to defer

The linter never recommends platform strategy, cost changes, or migration. It
reports defects; it does not advise.

Rules:
  L-COLLISION   trigger-phrase collision (same object, different action; or lexical)
  L-UNREACHABLE topic with no trigger and no inbound edge
  L-CYCLE       two topics that call each other (hygiene)
  L-NOFALLBACK  no system fallback topic
  L-NOESCALATE  no human escalation path
  L-NOCORRECT   slot-filling topic with no interruption/correction path
  L-NOWELCOME   no conversation-start guidance (hygiene)
  L-VARUNSET    variable read but never set (empty-response risk)
  L-VARDEAD     variable set but never read (dead assignment) (hygiene)
  L-MONOLITH    oversized topic (hygiene)

Usage:
    python lint_agent.py normalized.json --out findings.json
    python lint_agent.py normalized.json --out findings.json --threshold 0.70
    python lint_agent.py normalized.json --format text
"""

import argparse
import itertools
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

DEFAULT_THRESHOLD = 0.75
REPORT_FLOOR = 0.70
MONOLITH_NODE_COUNT = 25

# normalized.json schema_version values this linter version knows how to read.
# ingest_agent.py and lint_agent.py version independently (e.g. shared across a
# team, or run from different checkouts), so a mismatch is reported as a
# caveat rather than silently misreading fields the schema may have changed.
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

STOPWORDS = {
    "a", "an", "the", "i", "my", "me", "you", "your", "to", "for", "of", "in",
    "on", "at", "is", "are", "am", "do", "does", "did", "can", "could", "would",
    "please", "want", "need", "how", "what", "where", "when", "help", "with",
    "it", "this", "that", "and", "or", "be", "have", "has", "get", "got",
}

# Action verbs that commonly head a user request. Used to separate the action
# from the object in a trigger phrase, so "cancel my order" and "change my
# order" (same object, different action) are caught — the single highest-risk
# collision shape, which pure lexical similarity scores too low to flag.
ACTION_VERBS = {
    "cancel", "change", "modify", "update", "edit", "amend", "revise",
    "delete", "remove", "add", "create", "make", "start", "stop", "pause",
    "resume", "return", "refund", "exchange", "replace", "track", "check",
    "find", "search", "view", "show", "book", "reserve", "schedule",
    "reschedule", "confirm", "approve", "reject", "submit", "send",
    "upgrade", "downgrade", "renew", "extend", "transfer", "move",
}


# --------------------------------------------------------------------------
# Similarity
# --------------------------------------------------------------------------

def normalise(phrase: str) -> str:
    p = phrase.lower().strip()
    p = re.sub(r"[^\w\s]", " ", p)
    return re.sub(r"\s+", " ", p).strip()


def tokens(phrase: str) -> Set[str]:
    return {t for t in normalise(phrase).split() if t and t not in STOPWORDS}


def split_action_object(phrase: str) -> Tuple[Set[str], Set[str]]:
    content = tokens(phrase)
    actions = content & ACTION_VERBS
    return actions, content - actions


def structural_risk(a: str, b: str) -> Tuple[float, str]:
    act_a, obj_a = split_action_object(a)
    act_b, obj_b = split_action_object(b)
    if not obj_a or not obj_b:
        return 0.0, ""
    obj_overlap = len(obj_a & obj_b) / max(len(obj_a | obj_b), 1)
    if obj_overlap >= 0.5 and act_a and act_b and not (act_a & act_b):
        return 0.82, (
            f"same object ({', '.join(sorted(obj_a & obj_b))}) with differing "
            f"actions ({', '.join(sorted(act_a))} vs {', '.join(sorted(act_b))})"
        )
    if obj_overlap >= 0.8 and (not act_a or not act_b):
        return 0.76, (
            f"same object ({', '.join(sorted(obj_a & obj_b))}) with no "
            f"distinguishing action in one phrase"
        )
    return 0.0, ""


def similarity_explained(a: str, b: str) -> Tuple[float, str]:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0, ""
    jaccard = len(ta & tb) / len(ta | tb)
    seq = SequenceMatcher(None, normalise(a), normalise(b)).ratio()
    lexical = 0.6 * jaccard + 0.4 * seq
    struct, reason = structural_risk(a, b)
    if struct > lexical:
        return round(struct, 3), reason
    shared = ", ".join(sorted(ta & tb)) or "none"
    return round(lexical, 3), f"lexical overlap (shared terms: {shared})"


# --------------------------------------------------------------------------
# Finding helper
# --------------------------------------------------------------------------

def finding(rule: str, tier: str, severity: str, title: str,
            evidence: str, fix: str, confidence: str = "high",
            file: Optional[str] = None, line: Optional[int] = None) -> Dict[str, Any]:
    return {
        "rule": rule,
        "tier": tier,               # correctness | hygiene
        "severity": severity,       # high | medium | low
        "title": title,
        "evidence": evidence,
        "fix": fix,
        "confidence": confidence,
        "file": file,               # optional: populated when the parser located the source
        "line": line,               # optional: only when cheaply determinable from raw text
    }


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_collisions(topics: List[Dict], threshold: float) -> List[Dict]:
    out: List[Dict] = []
    considered = [t for t in topics if t.get("trigger_phrases") and not t.get("is_system_topic")]
    for t1, t2 in itertools.combinations(considered, 2):
        best = (0.0, None, None, "")
        for p1 in t1["trigger_phrases"]:
            for p2 in t2["trigger_phrases"]:
                s, reason = similarity_explained(p1, p2)
                if s > best[0]:
                    best = (s, p1, p2, reason)
        score, pa, pb, reason = best
        if score >= threshold:
            out.append(finding(
                "L-COLLISION", "correctness", "high",
                f"Trigger collision: '{t1['name']}' vs '{t2['name']}'",
                f"score {score:.2f} — \"{pa}\" vs \"{pb}\" ({reason})",
                "Consolidate into one topic with a disambiguation slot, or "
                "differentiate the trigger phrases. Near-duplicate topics usually "
                "should be a single topic.",
            ))
        elif score >= REPORT_FLOOR:
            out.append(finding(
                "L-COLLISION", "correctness", "medium",
                f"Near-collision: '{t1['name']}' vs '{t2['name']}'",
                f"score {score:.2f} — \"{pa}\" vs \"{pb}\" ({reason})",
                "Review these phrases; they are close enough to risk occasional "
                "misrouting. Differentiate if the topics are distinct.",
            ))
    return out


def check_orchestration(topics: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    names = {t["name"] for t in topics}
    inbound: Dict[str, List[str]] = {n: [] for n in names}
    for t in topics:
        for target in t.get("calls_topics", []):
            for n in names:
                if target.lower() in n.lower().replace(" ", ""):
                    inbound[n].append(t["name"])

    for t in topics:
        if (not t.get("trigger_phrases") and not inbound.get(t["name"])
                and not t.get("is_system_topic")):
            out.append(finding(
                "L-UNREACHABLE", "correctness", "high",
                f"Unreachable topic: '{t['name']}'",
                "no trigger phrases and no inbound edge from any other topic",
                "Add trigger phrases, route to it from another topic, or remove it "
                "if it is dead work.",
            ))

    # Note: a "dead-end" check (topic that never routes onward) was considered
    # and deliberately dropped. Almost every leaf topic legitimately ends the
    # conversation, so it fires on nearly all topics and drowns real findings.
    # A linter that cries wolf on every topic trains users to ignore it.

    seen_pairs = set()
    for t in topics:
        for target in t.get("calls_topics", []):
            for other in topics:
                if target.lower() in other["name"].lower().replace(" ", ""):
                    back = [c.lower() for c in other.get("calls_topics", [])]
                    if any(t["name"].lower().replace(" ", "") in b for b in back):
                        pair = tuple(sorted([t["name"], other["name"]]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            out.append(finding(
                                "L-CYCLE", "hygiene", "medium",
                                f"Topics call each other: '{pair[0]}' <-> '{pair[1]}'",
                                "mutual BeginDialog references",
                                "Check for an unintended loop. If intentional, ensure "
                                "there is a guaranteed exit condition.",
                            ))
    return out


def check_configuration(model: Dict[str, Any]) -> List[Dict]:
    out: List[Dict] = []
    cfg = model.get("configuration", {})
    topics = model.get("topics", [])

    if cfg.get("fallback_configured") is False:
        out.append(finding(
            "L-NOFALLBACK", "correctness", "high",
            "No fallback topic",
            "no system fallback topic detected",
            "Add a fallback topic so unmatched input gets a recovery path instead "
            "of a dead end.",
        ))

    if cfg.get("escalation_configured") is False:
        out.append(finding(
            "L-NOESCALATE", "correctness", "high",
            "No escalation path",
            "no human handoff topic detected",
            "Add a human-handoff path so failed conversations have an exit.",
        ))

    slot_no_interrupt = [
        t["name"] for t in topics
        if t.get("has_slot_filling") and not t.get("has_interruption_handling")
        and not t.get("is_system_topic")
    ]
    if slot_no_interrupt:
        shown = ", ".join(slot_no_interrupt[:5])
        out.append(finding(
            "L-NOCORRECT", "correctness", "high",
            "Slot-filling with no correction path",
            f"{len(slot_no_interrupt)} topic(s) collect input without an "
            f"interruption/correction branch: {shown}",
            "Allow interruption on these topics so a user can correct themselves "
            "('no, I meant...') without being stuck in the slot.",
        ))

    if cfg.get("welcome_message") is False:
        out.append(finding(
            "L-NOWELCOME", "hygiene", "low",
            "No conversation-start guidance",
            "no welcome/greeting topic detected",
            "Add a welcome message disclosing what the agent can do — it improves "
            "containment rate.",
        ))

    return out


def check_variables(model: Dict[str, Any]) -> List[Dict]:
    out: List[Dict] = []
    for v in model.get("variables", []):
        # Variables used only inside platform system topics (Multiple Topics
        # Matched, On Error, Goodbye, etc.) are managed by Copilot Studio, not
        # the maker. Flagging them is noise the user cannot act on.
        if v.get("only_system"):
            continue
        if v.get("read_in") and not v.get("set_in"):
            out.append(finding(
                "L-VARUNSET", "correctness", "high",
                f"Variable read but never set: '{v['name']}'",
                f"read in: {', '.join(v['read_in'][:5])}",
                "Set this variable before it is read, or the agent will render an "
                "empty value to the user.",
            ))
        if v.get("set_in") and not v.get("read_in"):
            out.append(finding(
                "L-VARDEAD", "hygiene", "low",
                f"Variable set but never read: '{v['name']}'",
                f"set in: {', '.join(v['set_in'][:5])}",
                "Remove the dead assignment, or use the value — it is currently "
                "computed and discarded.",
            ))
    return out


def check_complexity(topics: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for t in topics:
        if t.get("node_count", 0) > MONOLITH_NODE_COUNT:
            out.append(finding(
                "L-MONOLITH", "hygiene", "low",
                f"Oversized topic: '{t['name']}'",
                f"{t['node_count']} nodes (threshold {MONOLITH_NODE_COUNT})",
                "Consider decomposing into smaller topics or extracting shared "
                "sub-topics for maintainability.",
            ))
    return out


def check_power_fx(topics: List[Dict]) -> List[Dict]:
    """PFX-SAFETY: Power Fx '=' expressions checked two ways.

    1. Function names outside the known-common set: advisory-leaning by design
       (low severity, low confidence) -- the known set is a common-function
       heuristic, not an exhaustive or verified reference for every function
       Copilot Studio supports, so a miss is a prompt to double-check, never
       an assertion that the function is unsupported.
    2. Unbalanced brackets/quotes: deterministic syntax validation, reported
       at higher confidence since an imbalance is a verifiable fact regardless
       of which functions are considered supported.
    """
    out: List[Dict] = []
    for t in topics:
        unknown = t.get("power_fx_unknown_functions", [])
        if unknown:
            shown = ", ".join(f"`{f}`" for f in unknown[:8])
            out.append(finding(
                "PFX-SAFETY", "hygiene", "low",
                f"Power Fx expression uses an unrecognised function: '{t['name']}'",
                f"{len(unknown)} function name(s) in '=' expressions do not match "
                f"the known-common Power Fx set: {shown}",
                "Confirm each function is actually supported in Copilot Studio's "
                "Power Fx subset (this is a common-function heuristic, not an "
                "exhaustive reference) — an unsupported function fails silently "
                "at runtime.",
                confidence="low",
                file=t.get("source_file"),
            ))
        for issue in t.get("power_fx_syntax_issues", []):
            out.append(finding(
                "PFX-SAFETY", "correctness", "medium",
                f"Power Fx expression has {issue['issue']}: '{t['name']}'",
                f"a '=' expression has {issue['issue']}",
                "Fix the expression's brackets/quotes — an unbalanced Power Fx "
                "expression fails to parse at runtime.",
                confidence="medium",
                file=t.get("source_file"),
                line=issue.get("line"),
            ))
    return out


def check_dialog_deadends(topics: List[Dict]) -> List[Dict]:
    """A ConditionGroup where some branches redirect/end cleanly and at least
    one just stops — a likely-forgotten branch that inflates "Abandoned"
    session metrics. Deliberately narrower than "every branch needs an
    explicit exit": almost every topic legitimately ends a branch with a
    plain message, so flagging that universally would drown real findings —
    see the dead-end note in check_orchestration, where exactly that broader
    check was tried and rejected for this reason."""
    out: List[Dict] = []
    for t in topics:
        if t.get("is_system_topic"):
            continue
        groups = t.get("unterminated_branch_groups", [])
        if groups:
            worst = max(groups, key=lambda g: g["unterminated"])
            out.append(finding(
                "DIALOG-DEADEND", "correctness", "medium",
                f"Inconsistent branch exits: '{t['name']}'",
                f"{len(groups)} condition group(s) have at least one branch that "
                f"redirects/ends cleanly and at least one that does not, e.g. "
                f"'{worst['group']}' ({worst['unterminated']} of {worst['branches']} "
                f"branch(es) unterminated)",
                "Give every branch in the group the same kind of clean exit "
                "(EndDialog/RedirectDialog/BeginDialog/ReplaceDialog/"
                "CancelAllDialogs, or an explicit conversationOutcome), so a "
                "forgotten branch does not silently abandon the session.",
                confidence="medium",
                file=t.get("source_file"),
            ))
    return out


MIN_MODEL_DESCRIPTION_CHARS = 15
MIN_CLASSIC_TRIGGER_PHRASES = 5

# Advisory-only length thresholds (judgement calls, not defects): a single
# instruction block or skill this long risks diluting instruction-following
# and adds meaningfully to per-turn token cost.
LARGE_INSTRUCTIONS_CHARS = 12000
LARGE_ALWAYS_LOADED_TOKENS = 8000
LARGE_SKILL_INSTRUCTIONS_CHARS = 4000


def check_orchestration_quality(model: Dict[str, Any]) -> List[Dict]:
    """Routing-quality checks that depend on which orchestration mode is
    active: generative actions need a clear modelDescription to route on;
    classic trigger-phrase matching needs enough paraphrases to route on."""
    out: List[Dict] = []
    generative = model.get("agent", {}).get("generative_actions_enabled")
    if generative is None:
        return out  # unknown — do not guess which branch applies

    if generative:
        for t in model.get("tools", []):
            chars = t.get("model_description_chars", 0)
            if not t.get("model_description_present") or chars < MIN_MODEL_DESCRIPTION_CHARS:
                detail = "absent" if not t.get("model_description_present") else f"{chars} chars"
                out.append(finding(
                    "TRG-QUALITY", "correctness", "medium",
                    f"Action has a thin or missing model description: '{t['name']}'",
                    f"modelDescription is {detail} "
                    f"(threshold {MIN_MODEL_DESCRIPTION_CHARS})",
                    "Write a clear modelDescription stating what this action is for "
                    "and when not to use it (e.g. 'Use for X. Do NOT use for Y.'), so "
                    "the generative orchestrator can route to it reliably.",
                    file=t.get("source_file"),
                ))
    else:
        for t in model.get("topics", []):
            if t.get("is_system_topic"):
                continue
            phrases = set(t.get("trigger_phrases", []))
            if phrases and len(phrases) < MIN_CLASSIC_TRIGGER_PHRASES:
                out.append(finding(
                    "TRG-QUALITY", "hygiene", "low",
                    f"Few trigger phrases for classic routing: '{t['name']}'",
                    f"{len(phrases)} distinct trigger phrase(s) "
                    f"(Microsoft recommends at least {MIN_CLASSIC_TRIGGER_PHRASES})",
                    "Add more paraphrases of how a user would actually ask for "
                    "this, so classic trigger-phrase matching has enough signal "
                    "to route correctly.",
                    confidence="medium",
                    file=t.get("source_file"),
                ))
    return out


def check_odata_quoting(model: Dict[str, Any]) -> List[Dict]:
    """Inconsistent quoting of $-prefixed OData-style connector parameters
    within the same component — a common cause of silent runtime failures
    calling SharePoint/OData-backed connectors. Cannot assert a single
    universal "correct" form without the specific connector's documentation,
    so this flags the inconsistency for the maker to confirm, not which side
    is wrong."""
    out: List[Dict] = []
    for t in model.get("topics", []):
        for issue in t.get("odata_quote_issues", []):
            out.append(finding(
                "ODATA-QUOTE", "hygiene", "low",
                f"Inconsistent OData parameter quoting: '{t['name']}'",
                f"`{issue['param']}` appears with mixed quoting styles in this "
                f"topic: {issue['styles']}",
                "Use one consistent quoting convention for this parameter "
                "throughout the topic, matching what the connector actually "
                "requires — mixed quoting is a common cause of a filter that "
                "silently returns nothing.",
                confidence="low",
                file=t.get("source_file"),
            ))
    for tool in model.get("tools", []):
        for issue in tool.get("odata_quote_issues", []):
            out.append(finding(
                "ODATA-QUOTE", "hygiene", "low",
                f"Inconsistent OData parameter quoting: '{tool['name']}'",
                f"`{issue['param']}` appears with mixed quoting styles in this "
                f"action: {issue['styles']}",
                "Use one consistent quoting convention for this parameter, "
                "matching what the connector actually requires.",
                confidence="low",
                file=tool.get("source_file"),
            ))
    return out


_SECURITY_VAR_KEYWORDS = {
    "token", "key", "secret", "password", "pat", "api", "auth",
    "credential", "credentials",
}


def _tokenize_identifier(name: str) -> List[str]:
    """Split camelCase/PascalCase/snake_case into lowercase word tokens, so a
    keyword match requires a whole-word hit (e.g. "Patient" -> ["patient"],
    never "pat") rather than a raw, false-positive-prone substring search."""
    s = re.sub(r"[_\-.]+", " ", name)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return [tok.lower() for tok in s.split() if tok]


def check_variable_ai_leak(model: Dict[str, Any]) -> List[Dict]:
    """A variable whose name suggests it holds a secret (token/key/password/
    etc.) is a structural risk in any agent with a generative core: the value
    can flow through conversation state into what an LLM orchestrator reasons
    over. Flagged on the variable's existence alone — not on a speculative
    AI-visibility property this export may or may not carry, since that
    field's exact schema is not verified."""
    out: List[Dict] = []
    topic_files = {t["name"]: t.get("source_file") for t in model.get("topics", [])}
    for v in model.get("variables", []):
        if v.get("only_system"):
            continue
        hit = set(_tokenize_identifier(v["name"])) & _SECURITY_VAR_KEYWORDS
        if hit:
            set_in = v.get("set_in", [])
            out.append(finding(
                "SEC-AI-LEAK", "correctness", "high",
                f"Variable name suggests sensitive data: '{v['name']}'",
                f"variable name matches security keyword(s) {sorted(hit)}; "
                f"set in: {', '.join(set_in[:5]) or 'unknown'}",
                "Do not carry secrets/tokens/credentials in a Topic-scoped "
                "variable that can flow into conversation state or a generative "
                "orchestrator's context. Migrate to a connection reference or an "
                "environment-level secret store, and confirm this value is never "
                "exposed to the AI/model context.",
                file=topic_files.get(set_in[0]) if set_in else None,
            ))
    return out


def check_guardrail_gate(topics: List[Dict]) -> List[Dict]:
    """GUARDRAIL-GATE: flags any use of the OnOutgoingMessage system trigger,
    which does not do anything as a maker-facing trigger in Copilot Studio's
    conversational runtime. A focused, high-accuracy check on the trigger's
    mere presence -- it does not attempt to also verify confirmation gating
    on mutating actions, which needs a broader, less mechanical analysis than
    a single trigger-kind match can support."""
    out: List[Dict] = []
    for t in topics:
        if t.get("has_on_outgoing_message_trigger"):
            out.append(finding(
                "GUARDRAIL-GATE", "hygiene", "low",
                f"Non-functional trigger used: '{t['name']}'",
                "topic references the OnOutgoingMessage system trigger",
                "Remove the OnOutgoingMessage trigger; it does not fire as a "
                "maker-facing trigger and any logic behind it will not run.",
                confidence="medium",
                file=t.get("source_file"),
            ))
    return out


MIN_CONNECTED_AGENT_DESC_CHARS = 30


def check_connected_agents(model: Dict[str, Any]) -> List[Dict]:
    """CONNECTED-AGENTS: a connected/child agent needs enough description for
    the orchestrator to hand off to it reliably, and (for a native AgentDialog
    specifically) the OnToolSelected trigger its own beginDialog is expected to
    carry -- observed directly in a real export as the mechanism a parent
    orchestrator uses to select it, not a separate topic-level marker."""
    out: List[Dict] = []
    for c in model.get("connected_agents", []):
        chars = c.get("instruction_chars", 0)
        if chars < MIN_CONNECTED_AGENT_DESC_CHARS:
            out.append(finding(
                "CONNECTED-AGENTS", "correctness", "medium",
                f"Connected agent has a thin description: '{c['name']}'",
                f"description is {chars} chars "
                f"(threshold {MIN_CONNECTED_AGENT_DESC_CHARS})",
                "Write a clearer description of what this connected agent "
                "handles, so the parent orchestrator can hand off to it "
                "reliably instead of guessing.",
                file=c.get("source_file"),
            ))
        if c.get("source_kind") == "AgentDialog" and not c.get("has_on_tool_selected_trigger"):
            out.append(finding(
                "CONNECTED-AGENTS", "correctness", "medium",
                f"Connected agent missing its OnToolSelected trigger: '{c['name']}'",
                "this AgentDialog component's beginDialog is not OnToolSelected",
                "Map this connected agent's beginDialog to the OnToolSelected "
                "trigger, or the parent orchestrator cannot select it and the "
                "handoff silently drops.",
                confidence="medium",
                file=c.get("source_file"),
            ))
    return out


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIER_ORDER = {"correctness": 0, "hygiene": 1}


# --------------------------------------------------------------------------
# Agentic checks (new-experience InlineAgentSkill agents)
# --------------------------------------------------------------------------

MIN_DESC_CHARS = 30
MIN_INSTRUCTION_CHARS = 20


def _desc_similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    seq = SequenceMatcher(None, normalise(a), normalise(b)).ratio()
    return 0.6 * jaccard + 0.4 * seq


def check_skill_descriptions(skills: List[Dict], threshold: float) -> List[Dict]:
    """Two skills whose descriptions overlap enough that the LLM router cannot
    reliably choose between them — the agentic analogue of a trigger collision."""
    out: List[Dict] = []
    described = [s for s in skills if s.get("description")]
    for s1, s2 in itertools.combinations(described, 2):
        score = _desc_similarity(s1["description"], s2["description"])
        if score >= threshold:
            out.append(finding(
                "A-DESC-COLLISION", "correctness", "high",
                f"Skill descriptions overlap: '{s1['name']}' vs '{s2['name']}'",
                f"description similarity {score:.2f} — the router may not reliably "
                f"distinguish these two skills",
                "Sharpen each description to state what makes this skill distinct "
                "(different object, action, or trigger condition), so the model can "
                "route to the right one.",
            ))
    return out


def check_skill_quality(skills: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for s in skills:
        desc = s.get("description", "")
        if not desc:
            out.append(finding(
                "A-NODESC", "correctness", "high",
                f"Skill has no description: '{s['name']}'",
                "no description found in the skill frontmatter",
                "Add a description. In the agentic experience the model selects a "
                "skill by its description; with none, it cannot be routed to reliably.",
            ))
        elif len(desc) < MIN_DESC_CHARS:
            out.append(finding(
                "A-WEAKDESC", "correctness", "medium",
                f"Skill description too thin: '{s['name']}'",
                f"description is {len(desc)} chars: \"{desc}\"",
                "Expand the description to clearly state when this skill should be "
                "used, so the router can select it against the others.",
            ))
        if not s.get("instructions") or len(s.get("instructions", "")) < MIN_INSTRUCTION_CHARS:
            out.append(finding(
                "A-NOINSTRUCTION", "correctness", "high",
                f"Skill has little or no instructions: '{s['name']}'",
                f"instructions section is {len(s.get('instructions',''))} chars",
                "Add instructions describing what the skill should do when activated. "
                "An empty skill will be selected but then have no defined behaviour.",
            ))
    return out


# Verbs in instructions that imply the skill acts on data/systems and therefore
# needs at least one tool to actually do anything.
ACTION_INSTRUCTION_VERBS = (
    "read", "write", "update", "create", "delete", "search", "find", "fetch",
    "retrieve", "query", "call", "invoke", "post", "send", "modify", "look up",
)
# Language that signals a description states *when* to route to the skill.
USE_WHEN_MARKERS = (
    "use when", "use this when", "when the user", "when the buyer", "when someone",
    "for when", "triggered when", "use for", "handles", "call this when",
)


def check_skill_semantics(model: Dict[str, Any]) -> List[Dict]:
    """Deeper structural checks on agent skills.

    Still structural (decidable from the export, no semantic judgement of whether
    the prose is 'good') — but catches shapes that break routing or execution:
    a skill that acts on data but wires no tool, a description with no routing
    condition, and duplicate skill names.
    """
    out: List[Dict] = []
    skills = model.get("skills", [])

    # A-DUP-NAME — two skills with the same name
    seen: Dict[str, int] = {}
    for s in skills:
        seen[s["name"]] = seen.get(s["name"], 0) + 1
    for name, count in seen.items():
        if count > 1:
            out.append(finding(
                "A-DUP-NAME", "correctness", "high",
                f"Duplicate skill name: '{name}'",
                f"{count} skills share the name '{name}'",
                "Give each skill a unique name; duplicate names make routing and "
                "maintenance ambiguous.",
            ))

    for s in skills:
        desc = s.get("description", "")
        instr = (s.get("instructions") or "").lower()
        tools = s.get("referenced_tools", [])

        # A-NOTOOLS — instructions act on data but no tool is listed
        if instr and not tools:
            if any(v in instr for v in ACTION_INSTRUCTION_VERBS):
                out.append(finding(
                    "A-NOTOOLS", "correctness", "medium",
                    f"Skill acts on data but lists no tools: '{s['name']}'",
                    "instructions describe reading/updating/searching data, but the "
                    "skill's Tools section is empty",
                    "List the tools this skill needs (e.g. a data or action tool). "
                    "Without them the model is instructed to act but has nothing to "
                    "act with.",
                    confidence="medium",
                ))

        # A-VAGUE-DESC — description present and long enough, but states no
        # routing condition, so the router has no signal for *when* to pick it.
        if desc and len(desc) >= MIN_DESC_CHARS:
            low = desc.lower()
            if not any(mk in low for mk in USE_WHEN_MARKERS):
                out.append(finding(
                    "A-VAGUE-DESC", "hygiene", "low",
                    f"Description states no routing condition: '{s['name']}'",
                    "the description does not say *when* to use the skill "
                    "(no 'use when…', 'when the user…', 'handles…' language)",
                    "Add a 'use when…' clause so the router can tell this skill "
                    "apart from the others by its trigger condition, not just its topic.",
                ))
    return out


# Built-in platform tools follow a stable verb_noun connector-operation naming
# scheme (data_find_entities, api_invoke_action, search_knowledge, ...). Rather
# than hardcode a prefix list that goes stale when the platform adds a family,
# recognise the *shape*: a known operation verb followed by an underscore. This
# is durable because the naming convention is the durable thing, not the
# specific set of prefixes shipped this quarter.
BUILTIN_TOOL_VERBS = frozenset({
    "data", "api", "search", "http", "power", "flow", "connector",
    "knowledge", "get", "list", "create", "update", "delete", "find",
    "invoke", "run", "call", "query", "fetch", "send",
})


def _is_builtin_tool(name: str) -> bool:
    """A tool reference that is a platform built-in (needs no wired component).

    True when the name looks like verb_noun with a known operation verb head,
    e.g. data_find_entities, api_invoke_action, search_knowledge_sources.
    """
    low = name.strip().lower()
    head = re.split(r"[_\-\s]", low, 1)[0]
    return "_" in low and head in BUILTIN_TOOL_VERBS


def check_tool_references(model: Dict[str, Any]) -> List[Dict]:
    """A skill that references a custom tool which is not wired into the agent.

    Only *custom* tools are flagged. Built-in platform tools are excluded by
    naming shape, not a fixed prefix list. The finding is low-severity by design:
    tool wiring can live outside the exported components (environment-level
    connections), so a linter should surface the possibility without asserting a
    definite break — a false 'unwired tool' alarm costs more credibility than it
    is worth.
    """
    out: List[Dict] = []
    wired = set()
    for t in model.get("tools", []):
        nm = t.get("name", "")
        wired.add(nm.lower())
        wired.add(re.sub(r"[^a-z0-9]", "", nm.lower()))
    for s in model.get("skills", []):
        for ref in s.get("referenced_tools", []):
            r = ref.strip()
            if not r:
                continue
            if _is_builtin_tool(r):
                continue  # platform built-in, no wiring needed
            low = r.lower()
            simple = re.sub(r"[^a-z0-9]", "", low)
            if not simple:
                continue
            # Tolerate a reference written as a shorthand of a longer wired
            # name (simple in w), but do NOT accept the reverse (w in simple):
            # that direction would treat any unwired tool whose name merely
            # extends a wired one (e.g. an unwired `UpdateOrderTool` next to a
            # wired `OrderTool`) as already wired, hiding a genuine A-TOOLREF.
            if low in wired or simple in wired or any(
                simple and simple in w for w in wired
            ):
                continue
            out.append(finding(
                "A-TOOLREF", "correctness", "low",
                f"Skill may reference an unwired tool: '{s['name']}' -> `{r}`",
                f"the skill lists tool `{r}`, which does not match any tool "
                f"component in the export (it may be an environment-level "
                f"connection defined outside this solution)",
                "Confirm the tool is wired into the agent, or correct the tool "
                "name in the skill's Tools section.",
                confidence="medium",
            ))
    return out


def check_components(model: Dict[str, Any]) -> List[Dict]:
    """Structural checks across the whole agent: tools, instructions, memory,
    knowledge, and evaluation. All decidable from the export; no judgement of
    prose quality (those go in the advisory section)."""
    out: List[Dict] = []
    tools = model.get("tools", [])
    skills = model.get("skills", [])
    instr = model.get("instructions", {})
    evalsets = model.get("evaluation_sets", [])

    # Build the set of tool operations the agent actually exposes.
    exposed = set()
    for t in tools:
        exposed.add(re.sub(r"[^a-z0-9]", "", t["name"].lower()))
        for op in t.get("allowed_tools", []):
            exposed.add(re.sub(r"[^a-z0-9]", "", op.lower()))

    for t in tools:
        if t.get("kind") == "McpTool" and not t.get("allowed_tools"):
            out.append(finding(
                "C-TOOL-EMPTY", "correctness", "medium",
                f"MCP tool exposes no operations: '{t['name']}'",
                "the McpTool component has an empty allowedTools list",
                "Add the operations this MCP tool should expose, or remove the "
                "tool if it is unused.",
            ))
        if t.get("kind") == "McpTool" and not t.get("connection_reference"):
            out.append(finding(
                "C-TOOL-NOCONN", "correctness", "medium",
                f"MCP tool has no connection reference: '{t['name']}'",
                "no connectionReference is set, so the tool cannot authenticate at runtime",
                "Bind a connection reference to this tool before publishing.",
                confidence="medium",
            ))

    if instr.get("present"):
        exposed_list = sorted(exposed)
        for ref in instr.get("referenced_tools", []):
            simple = re.sub(r"[^a-z0-9]", "", ref.lower())
            if not simple or simple in exposed:
                continue
            # Tolerate shorthand: instructions often write "data_create/update/
            # delete_entities", from which we extract "data_create". If the
            # reference is a prefix of any exposed operation, it is that op in
            # shorthand, not a missing tool.
            if any(op.startswith(simple) or simple.startswith(op) for op in exposed_list):
                continue
            head = re.split(r"[_\-]", ref.lower(), 1)[0]
            if not _is_builtin_tool(ref) and head not in BUILTIN_TOOL_VERBS:
                continue
            out.append(finding(
                "C-INSTR-TOOLREF", "hygiene", "low",
                f"Main instructions reference an unwired tool: `{ref}`",
                f"the agent instructions mention `{ref}`, which looks like a tool "
                f"call but is not among the wired tools or MCP operations",
                "Confirm the tool is wired, or update the instruction so it "
                "does not tell the model to call a tool that isn't available.",
                confidence="medium",
            ))

    if skills and instr.get("present") is False:
        out.append(finding(
            "C-INSTR-MISSING", "correctness", "medium",
            "No main agent instructions",
            "the agent has skills but no top-level instructions were found",
            "Add main instructions (the always-loaded system prompt) that define "
            "the agent's role and any global rules; skills alone leave gate/scope "
            "behaviour undefined.",
        ))

    for ev in evalsets:
        if ev.get("grader_count", 0) == 0:
            out.append(finding(
                "C-EVAL-NOGRADER", "hygiene", "low",
                f"Evaluation set has no grader: '{ev['name']}'",
                "the EvaluationSet defines no graders, so its cases cannot be scored",
                "Add a grader (e.g. a quality grader) so the set produces pass/fail "
                "results, or remove the empty set.",
            ))

    if skills and not evalsets and not model.get("agent", {}).get("evaluation_case_count"):
        out.append(finding(
            "C-EVAL-NONE", "hygiene", "low",
            "No evaluation coverage",
            "the agent defines skills but ships no evaluation sets or test cases",
            "Add an evaluation set with representative cases so routing and "
            "behaviour can be regression-tested before publishing.",
        ))

    # Connected (child) agents and their contracts.
    connected = model.get("connected_agents", [])
    contracts = model.get("contracts", [])
    for c in contracts:
        if c.get("valid_json") is False:
            out.append(finding(
                "C-CONTRACT-INVALID", "correctness", "medium",
                f"Contract is not valid JSON: '{c['name']}'",
                f"the contract file {c.get('source_file', c['name'])} does not parse "
                f"as JSON, so the request/result shape between agents is undefined",
                "Fix the JSON so the contract between the orchestrator and the "
                "connected agent is well-formed.",
            ))
    if connected and not contracts:
        out.append(finding(
            "C-CONN-NOCONTRACT", "hygiene", "low",
            "Connected agent with no contract",
            f"{len(connected)} connected agent(s) are defined but no request/result "
            f"contract was found",
            "Add the request/result contract the orchestrator and connected agent "
            "exchange, so the hand-off shape is explicit and testable.",
        ))

    return out


# Mutating operation shapes: if any wired tool exposes one of these, the agent
# can change state and therefore needs a confirmation gate in its instructions.
_MUTATING_OP_MARKERS = ("create", "update", "delete", "write", "post", "invoke_action",
                        "cancel", "confirm", "modify", "remove", "set_")


def _agent_has_mutating_tool(model: Dict[str, Any]) -> bool:
    for t in model.get("tools", []):
        name = t.get("name", "").lower()
        ops = [o.lower() for o in t.get("allowed_tools", [])]
        blob = name + " " + " ".join(ops)
        if any(mk in blob for mk in _MUTATING_OP_MARKERS):
            return True
    for s in model.get("skills", []):
        for rt in s.get("referenced_tools", []):
            if any(mk in rt.lower() for mk in _MUTATING_OP_MARKERS):
                return True
    # A hybrid/modernized agent's mutating capability can live entirely in a
    # connected execution agent, with no McpTool/WorkflowTool/skill in this
    # export to carry the signal otherwise.
    for c in model.get("connected_agents", []):
        if c.get("references_mutating_ops"):
            return True
    return False


def check_guardrails_and_quality(model: Dict[str, Any]) -> List[Dict]:
    """Hard, defect-level checks for guardrail presence and instruction/skill
    quality.

    These are evidence-based on the *structural absence* of a control a script
    can be sure about — not a judgement of how well prose is written. They fire
    only when a required control is entirely absent, to keep false positives low
    even at defect severity:

      - G-NOCONFIRM: the agent can mutate state (a wired tool exposes a
        create/update/delete/action op) but its instructions contain no
        confirmation/approval gate of any kind.
      - G-NOGROUNDING: the agent has instructions but no grounding rule
        (no 'do not fabricate/invent/guess', no 'answer only from…'), so nothing
        structurally discourages hallucination.
      - Q-NOOUTPUT: instructions define no output/format constraint at all.
      - Q-NOSCOPE: instructions state no scope limit / prohibition ('do not…',
        'never…', 'only…') — the agent is given capability with no stated bounds.
      - Q-SKILL-NOSTRUCTURE: a skill's instructions are present but contain no
        step/format/prohibition structure a router-selected skill needs.

    NOTE: these are guardrail *presence* checks, not a security red-team or a
    sufficiency audit (that is the scope of the guardrails/red-team skills). They
    can be turned back to advisory with --guardrails-advisory.
    """
    out: List[Dict] = []
    instr = model.get("instructions", {})
    sig = instr.get("signals", {}) if isinstance(instr.get("signals"), dict) else {}
    has_instr = bool(instr.get("present"))

    if has_instr:
        if _agent_has_mutating_tool(model) and not sig.get("has_confirmation_gate"):
            out.append(finding(
                "G-NOCONFIRM", "correctness", "high",
                "Agent can change state but instructions define no confirmation gate",
                "a wired tool exposes a create/update/delete/action operation, but "
                "the main instructions contain no confirmation or approval step "
                "(no 'confirm', 'approve', 'are you sure', 'ask before…')",
                "Add an explicit confirmation gate before any mutating operation, so "
                "the agent cannot write, delete, or run an action without the user "
                "approving the exact change first.",
            ))
        if not sig.get("has_grounding_rule"):
            out.append(finding(
                "G-NOGROUNDING", "correctness", "high",
                "Instructions contain no grounding / anti-fabrication rule",
                "the main instructions include no rule discouraging fabrication "
                "(no 'do not invent/guess/fabricate', no 'answer only from…'), so "
                "nothing in the prompt structurally constrains the model against "
                "making up values",
                "Add a grounding rule — e.g. answer only from tool/knowledge results, "
                "and say when something is unknown rather than inventing it.",
            ))
        if not sig.get("has_output_constraint"):
            out.append(finding(
                "Q-NOOUTPUT", "correctness", "medium",
                "Instructions define no output or format constraint",
                "the instructions state no output shape, format, or presentation "
                "rule, leaving reply structure entirely to the model",
                "Specify the expected output format (message shape, table layout, "
                "what to never expose) so replies are consistent and predictable.",
            ))
        if not sig.get("has_scope_limits"):
            out.append(finding(
                "Q-NOSCOPE", "correctness", "medium",
                "Instructions state no scope limits or prohibitions",
                "the instructions contain no 'do not / never / only' bounds, so the "
                "agent is given capability with no stated limits",
                "Add explicit scope limits (what the agent must not do, what is out "
                "of scope) so behaviour is bounded.",
            ))

    # Per-skill instruction quality: a skill with instructions but no structure
    # (no steps, no format, no prohibition) is thin guidance for a selected skill.
    # Consolidated into ONE finding listing the affected skills, rather than one
    # per skill, so the report is not flooded with near-identical notes.
    thin_skills = []
    for s in model.get("skills", []):
        s_sig = s.get("signals", {}) if isinstance(s.get("signals"), dict) else {}
        instr_len = len(s.get("instructions") or "")
        if instr_len >= 20 and not (
            s_sig.get("has_output_constraint") or s_sig.get("has_scope_limits")
        ):
            thin_skills.append(s["name"])
    if thin_skills:
        listed = ", ".join(f"'{n}'" for n in thin_skills)
        out.append(finding(
            "Q-SKILL-NOSTRUCTURE", "hygiene", "low",
            f"{len(thin_skills)} skill(s) have instructions with no output/scope structure",
            f"these skills have instructions but no output-format rule and no "
            f"prohibition/scope bound, so their behaviour when selected is loosely "
            f"specified: {listed}",
            "Add at least an output-format expectation or an explicit boundary to "
            "each skill's instructions so its behaviour is well-defined. (Skills "
            "often inherit format rules from the main instructions — confirm that "
            "is intended rather than an omission.)",
            confidence="medium",
        ))

    # Per-skill grounding language: the main instructions' grounding rule (if
    # any) does not necessarily apply once a specific skill's own instructions
    # take over — a skill with no anti-fabrication language of its own is a
    # structural gap, not a judgement of whether its prose is well-written.
    ungrounded_skills = []
    for s in model.get("skills", []):
        s_sig = s.get("signals", {}) if isinstance(s.get("signals"), dict) else {}
        instr_len = len(s.get("instructions") or "")
        if instr_len >= MIN_INSTRUCTION_CHARS and not s_sig.get("has_grounding_rule"):
            ungrounded_skills.append(s["name"])
    if ungrounded_skills:
        listed = ", ".join(f"'{n}'" for n in ungrounded_skills)
        out.append(finding(
            "Q-SKILL-NOGROUNDING", "hygiene", "low",
            f"{len(ungrounded_skills)} skill(s) have instructions with no grounding rule of their own",
            f"these skills' own instructions contain no anti-fabrication/grounding "
            f"language (no 'do not invent/guess', 'answer only from…'), independent "
            f"of whatever the main instructions state: {listed}",
            "Confirm the main instructions' grounding rule is meant to carry over once "
            "this skill is selected, or add the rule to the skill itself — this is a "
            "structural absence check, not a judgement that the skill will hallucinate.",
            confidence="medium",
        ))
    return out


def _estimate_tokens(chars: int) -> int:
    """Rough, dependency-free estimate (~4 characters/token, the commonly-cited
    rule of thumb for English text). Derived only from already-collected
    character counts, never raw text. Not an exact tokenizer count — actual
    usage depends on the specific model's tokenizer."""
    return max(0, round(chars / 4))


def build_skill_review(skills: List[Dict], tools: List[Dict]) -> List[Dict]:
    """Per-skill inventory and assessment, produced even when there are no
    findings. Reports structure and length, never the description/instruction
    text itself, so business-sensitive prompt content is not reproduced.

    For each skill: description length, whether it states a routing condition,
    tool count split into built-in vs custom, instruction length, and its
    closest sibling by description similarity (the separation margin).
    """
    review: List[Dict] = []
    described = [s for s in skills if s.get("description")]

    for s in skills:
        desc = s.get("description", "")
        low = desc.lower()
        tools_ref = s.get("referenced_tools", [])
        builtin = [t for t in tools_ref if _is_builtin_tool(t)]
        custom = [t for t in tools_ref if not _is_builtin_tool(t)]

        # closest sibling by description similarity
        closest_name, closest_score = None, 0.0
        if desc:
            for other in described:
                if other is s:
                    continue
                sc = _desc_similarity(desc, other["description"])
                if sc > closest_score:
                    closest_name, closest_score = other["name"], sc

        review.append({
            "name": s["name"],
            "description_chars": len(desc),
            "description_tokens": _estimate_tokens(len(desc)),
            "states_routing_condition": bool(desc) and any(mk in low for mk in USE_WHEN_MARKERS),
            "instruction_chars": len(s.get("instructions") or ""),
            "instruction_tokens": _estimate_tokens(len(s.get("instructions") or "")),
            "tools_builtin": builtin,
            "tools_custom": custom,
            "closest_sibling": closest_name,
            "closest_similarity": round(closest_score, 2),
        })
    return review


def build_token_budget(model: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Rough token estimate for what's in context, computed purely from
    character counts already collected elsewhere (never raw text):
    main instructions + every skill's description (loaded for routing) make
    up what's always in the orchestrator's own context each turn; the largest
    single skill's instructions add a worst-case selected turn. Connected
    agents run in their own separate context (a different delegated call, not
    appended to the orchestrator's), so their tokens are reported alongside
    rather than folded into "always loaded" — but included in the combined
    export-wide total, so they are not silently invisible either.
    Returns None when there is nothing to estimate from.
    """
    instr = model.get("instructions", {})
    instr_chars = instr.get("length", 0) if instr.get("present") else 0
    skills = model.get("skills", [])
    connected = model.get("connected_agents", [])
    if not instr_chars and not skills and not connected:
        return None

    instr_tokens = _estimate_tokens(instr_chars)
    desc_tokens = [_estimate_tokens(len(s.get("description") or "")) for s in skills]
    instr_tokens_per_skill = [_estimate_tokens(len(s.get("instructions") or "")) for s in skills]
    total_desc_tokens = sum(desc_tokens)
    largest_skill_instr_tokens = max(instr_tokens_per_skill, default=0)
    always_loaded = instr_tokens + total_desc_tokens

    connected_tokens = [_estimate_tokens(c.get("instruction_chars", 0)) for c in connected]
    connected_tokens_total = sum(connected_tokens)

    return {
        "instructions_tokens": instr_tokens,
        "skills_count": len(skills),
        "skill_descriptions_tokens_total": total_desc_tokens,
        "largest_skill_instructions_tokens": largest_skill_instr_tokens,
        "always_loaded_tokens": always_loaded,
        "worst_case_turn_tokens": always_loaded + largest_skill_instr_tokens,
        "connected_agents_count": len(connected),
        "connected_agents_tokens_total": connected_tokens_total,
        "combined_export_tokens": (
            always_loaded + largest_skill_instr_tokens + connected_tokens_total
        ),
    }


def build_guardrail_summary(model: Dict[str, Any]) -> Dict[str, Any]:
    """A present/absent summary of the guardrail and instruction-quality signals,
    for ANY experience (classic, agentic, hybrid). This renders whether or not
    anything was flagged, so a clean agent still shows that the controls were
    checked and found present — rather than the check being invisible.

    Signals come from the agent's main instructions (wherever they live —
    configuration.json for agentic, parent-agent/instructions.md for modernized
    classic/hybrid), so this is experience-agnostic.
    """
    instr = model.get("instructions", {})
    if not instr.get("present"):
        return {"present": False}
    sig = instr.get("signals", {}) if isinstance(instr.get("signals"), dict) else {}
    mutating = _agent_has_mutating_tool(model)
    return {
        "present": True,
        "source_file": instr.get("source_file"),
        "rows": [
            {"control": "Confirmation / approval gate",
             "ok": bool(sig.get("has_confirmation_gate")),
             "note": "required — agent can change state" if mutating else "no mutating tool detected"},
            {"control": "Grounding / anti-fabrication rule",
             "ok": bool(sig.get("has_grounding_rule")),
             "note": "guards against invented values"},
            {"control": "Output / format constraint",
             "ok": bool(sig.get("has_output_constraint")),
             "note": "keeps replies consistent"},
            {"control": "Scope limits / prohibitions",
             "ok": bool(sig.get("has_scope_limits")),
             "note": "bounds what the agent may do"},
        ],
    }


def build_advisory(model: Dict[str, Any], token_budget: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """Clearly-labelled, non-durable, semantic observations. These are NOT
    structural findings — they are judgement calls a maker may reasonably
    disagree with, kept separate so the deterministic findings stay trustworthy.
    """
    notes: List[Dict] = []
    instr = model.get("instructions", {})
    mem = model.get("memory", {})
    kn = model.get("knowledge", {})
    skills = model.get("skills", [])
    topics = model.get("topics", [])

    # All analyzed topics are platform system topics — the classic checks ran
    # but had no maker-authored topic to evaluate, so a clean result reflects
    # an absence of custom topics, not a verified-clean topic graph.
    if topics and not skills and all(t.get("is_system_topic") for t in topics):
        notes.append({
            "topic": "Topics",
            "note": f"All {len(topics)} topic(s) in this export are platform-managed system "
                    "topics (Greeting, Fallback, Escalate, and so on) — there are no "
                    "maker-authored classic topics. The classic checks ran but had nothing "
                    "maker-written to evaluate; look to the generative core (main "
                    "instructions, connected agents, tools) for where this agent's real "
                    "behaviour and risk actually live.",
        })

    # Very long single instruction block — advisory, not a defect.
    if instr.get("present") and instr.get("length", 0) > LARGE_INSTRUCTIONS_CHARS:
        tokens_note = f" (~{_estimate_tokens(instr['length']):,} tokens)"
        notes.append({
            "topic": "Instructions",
            "note": f"The main instructions are large ({instr['length']:,} characters"
                    f"{tokens_note}). Long always-loaded prompts raise per-turn token cost "
                    "and can dilute instruction-following. Consider moving operation-specific "
                    "detail into the relevant skills, keeping only global gates and shared "
                    "rules in the main instructions.",
        })

    # Overall token budget — the combined picture across main instructions,
    # skill descriptions, and connected agents, which the per-component check
    # above cannot see on its own (e.g. many modest skill descriptions adding
    # up, even if no single one is individually "large").
    if token_budget and token_budget.get("always_loaded_tokens", 0) > LARGE_ALWAYS_LOADED_TOKENS:
        notes.append({
            "topic": "Token budget",
            "note": f"The always-loaded token estimate is "
                    f"~{token_budget['always_loaded_tokens']:,} tokens (main instructions plus "
                    f"every skill description), before any skill is even selected. This is "
                    "paid on every single turn regardless of what the user asks; consider "
                    "shortening skill descriptions to routing-relevant text only, and moving "
                    "anything else into the skill's own instructions.",
        })

    # Oversized individual skill instructions — advisory, not a defect: a very
    # long single-skill prompt can dilute instruction-following once that
    # skill is selected, the same concern as the main-instructions check above.
    oversized_skills = [
        s["name"] for s in skills
        if len(s.get("instructions") or "") > LARGE_SKILL_INSTRUCTIONS_CHARS
    ]
    if oversized_skills:
        listed = ", ".join(f"'{n}'" for n in oversized_skills)
        notes.append({
            "topic": "Skill instructions",
            "note": f"{len(oversized_skills)} skill(s) have instructions over "
                    f"{LARGE_SKILL_INSTRUCTIONS_CHARS:,} characters (~"
                    f"{_estimate_tokens(LARGE_SKILL_INSTRUCTIONS_CHARS):,}+ tokens): {listed}. "
                    "A long single-skill prompt can dilute instruction-following once that "
                    "skill is selected; consider splitting it into more focused skills.",
        })

    # Memory enabled — remind about retention/privacy, not a defect.
    if mem.get("enabled") is True:
        notes.append({
            "topic": "Memory",
            "note": "Memory is enabled. Confirm a retention/TTL policy is set and that "
                    "sensitive fields are excluded from what memory stores, so the agent "
                    "does not retain regulated data longer than intended.",
        })

    # Web search / knowledge off with no knowledge sources — capability note.
    if kn.get("web_search_enabled") is False and kn.get("source_count", 0) == 0:
        notes.append({
            "topic": "Knowledge",
            "note": "Web search is off and no knowledge sources are configured, so the "
                    "agent answers only from its instructions, tools, and model. That is a "
                    "valid design for a transactional agent; flagged only so it is a "
                    "deliberate choice.",
        })

    return notes


# Known internal model-series codes -> human-readable display name. Only
# confirmed mappings go here; an unrecognised code is shown verbatim (raw
# code, e.g. "Sonnet52") rather than guessed at, so a wrong label is never
# fabricated for a model series this hasn't been told about yet.
MODEL_SERIES_DISPLAY_NAMES = {
    "Sonnet46": "Claude Sonnet 4.6",
}


def _model_display_name(series: Optional[str]) -> Optional[str]:
    if not series:
        return series
    return MODEL_SERIES_DISPLAY_NAMES.get(series, series)


def build_component_inventory(model: Dict[str, Any]) -> Dict[str, Any]:
    """A structured inventory of every component type, for the report — so the
    report accounts for ALL parts of the agent, not just topics/skills."""
    agent = model.get("agent", {})
    return {
        "agent_name": agent.get("name"),
        "model": _model_display_name(agent.get("model")),
        "mode": agent.get("orchestration_mode"),
        "topics": len(model.get("topics", [])),
        "skills": len(model.get("skills", [])),
        "tools": [
            {
                "name": t["name"],
                "kind": t.get("kind"),
                "operations": len(t.get("allowed_tools", [])),
                "connected": bool(t.get("connection_reference")) if t.get("kind") == "McpTool" else None,
                "inputs": t.get("input_count", 0) if t.get("kind") == "WorkflowTool" else None,
            }
            for t in model.get("tools", [])
        ],
        "instructions": {
            "present": model.get("instructions", {}).get("present"),
            "length": model.get("instructions", {}).get("length", 0),
            "source_file": model.get("instructions", {}).get("source_file"),
        },
        "memory_enabled": model.get("memory", {}).get("enabled"),
        "web_search_enabled": model.get("knowledge", {}).get("web_search_enabled"),
        "knowledge_sources": len(model.get("knowledge_sources", []))
                             or model.get("knowledge", {}).get("source_count", 0),
        "evaluation_sets": len(model.get("evaluation_sets", [])),
        "evaluation_cases": agent.get("evaluation_case_count", 0),
        "connected_agents": len(model.get("connected_agents", [])),
        "contracts": len(model.get("contracts", [])),
    }


def lint(model: Dict[str, Any], threshold: float,
         guardrails_advisory: bool = True) -> Dict[str, Any]:
    topics = model.get("topics", [])
    skills = model.get("skills", [])
    findings: List[Dict] = []
    advisory_extra: List[Dict] = []
    # Classic / topic-based checks
    findings += check_collisions(topics, threshold)
    findings += check_orchestration(topics)
    findings += check_configuration(model)
    findings += check_variables(model)
    findings += check_complexity(topics)
    findings += check_power_fx(topics)
    findings += check_dialog_deadends(topics)
    findings += check_orchestration_quality(model)
    findings += check_odata_quoting(model)
    findings += check_variable_ai_leak(model)
    findings += check_guardrail_gate(topics)
    findings += check_connected_agents(model)
    # Agentic / skill-based checks
    findings += check_skill_descriptions(skills, threshold)
    findings += check_skill_quality(skills)
    findings += check_skill_semantics(model)
    findings += check_tool_references(model)
    # Whole-agent component checks (tools, instructions, memory, knowledge, eval)
    findings += check_components(model)
    guardrail_findings = check_guardrails_and_quality(model)
    if guardrails_advisory:
        # Downgrade to advisory notes rather than defects.
        for f in guardrail_findings:
            advisory_extra.append({
                "topic": f["rule"],
                "note": f"{f['title']} — {f['evidence']}. {f['fix']}",
            })
    else:
        findings += guardrail_findings

    findings.sort(key=lambda f: (TIER_ORDER[f["tier"]], SEVERITY_ORDER[f["severity"]]))

    confidence = "high" if model.get("parse_report", {}).get("complete") else "medium"
    if not topics and not skills:
        confidence = "low"

    correctness = [f for f in findings if f["tier"] == "correctness"]
    hygiene = [f for f in findings if f["tier"] == "hygiene"]
    token_budget = build_token_budget(model)
    advisory = build_advisory(model, token_budget) + advisory_extra

    schema_version = model.get("schema_version")
    schema_warning = None
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        schema_warning = (
            f"normalized.json has schema_version '{schema_version}', which this "
            f"linter version does not recognise (supports "
            f"{', '.join(sorted(SUPPORTED_SCHEMA_VERSIONS))}). Findings below may be "
            "incomplete or based on misread fields; re-run ingest_agent.py from the "
            "same linter version/checkout as lint_agent.py."
        )

    return {
        "schema_version": "1.0",
        "schema_warning": schema_warning,
        "agent_name": model.get("agent", {}).get("name"),
        "orchestration_mode": model.get("agent", {}).get("orchestration_mode"),
        "lint_confidence": confidence,
        "collision_sensitivity": threshold,
        "analyzed": {
            "topics": len(topics),
            "skills": len(skills),
            "tools": len(model.get("tools", [])),
        },
        "component_inventory": build_component_inventory(model),
        "guardrail_summary": build_guardrail_summary(model),
        "connected_agents": model.get("connected_agents", []),
        "knowledge_sources": model.get("knowledge_sources", []),
        "skill_review": build_skill_review(skills, model.get("tools", [])),
        "token_budget": token_budget,
        "advisory": advisory,
        "summary": {
            "total": len(findings),
            "correctness": len(correctness),
            "hygiene": len(hygiene),
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "advisory": len(advisory),
            "clean": len(findings) == 0,
        },
        "findings": findings,
        "note": (
            "Structural lint plus a clearly-separated advisory section. Structural "
            "findings are deterministic and decidable from the export. Advisory notes "
            "are judgement calls, not defects. Skill and instruction text is assessed "
            "by structure and length only — never reproduced in this report. This is a "
            "static structural review: it checks for the *presence* of grounding/"
            "confirmation/output/scope language and reports prompt-size token estimates; "
            "it does not judge whether that language is well-written, does not predict "
            "whether the agent will hallucinate, and does not test runtime behaviour or "
            "resistance to adversarial prompts."
        ),
    }


def print_text(result: Dict[str, Any]) -> None:
    s = result["summary"]
    a = result.get("analyzed", {})
    mode = result.get("orchestration_mode") or "unknown"
    sens = result.get("collision_sensitivity")
    if result.get("schema_warning"):
        print(f"WARNING: {result['schema_warning']}")
    print(f"Lint: {result.get('agent_name') or '(unnamed)'}  "
          f"[mode: {mode} | confidence: {result['lint_confidence']}]")
    print(f"  analyzed: {a.get('topics', 0)} topic(s), {a.get('skills', 0)} skill(s), "
          f"{a.get('tools', 0)} tool(s)")
    # Name the checks that were applicable, so a clean result visibly shows its
    # work rather than reading as "nothing was looked at".
    ran = []
    if a.get("topics", 0):
        ran.append("trigger-collision, orchestration, config, variable-lifecycle")
    if a.get("skills", 0):
        ran.append("skill-description-collision, description/instruction quality, tool-refs")
    if ran:
        print(f"  checks run: {'; '.join(ran)}")
    if sens is not None:
        print(f"  collision sensitivity: {sens} (lower with --threshold to catch weaker overlaps)")
    if s["clean"]:
        print("  No structural issues found.")
        return
    print(f"  {s['total']} finding(s): {s['correctness']} correctness, "
          f"{s['hygiene']} hygiene ({s['high']} high-severity)")
    print()
    last_tier = None
    for f in result["findings"]:
        if f["tier"] != last_tier:
            print(f"── {f['tier'].upper()} ──")
            last_tier = f["tier"]
        print(f"  [{f['severity']:6}] {f['rule']:12} {f['title']}")
        if f.get("file"):
            loc = f["file"] + (f":{f['line']}" if f.get("line") else "")
            print(f"           at:       {loc}")
        print(f"           evidence: {f['evidence']}")
        print(f"           fix:      {f['fix']}")
        print()


def render_markdown(result: Dict[str, Any]) -> str:
    """Render the lint result as a self-contained markdown report."""
    a = result.get("analyzed", {})
    s = result["summary"]
    mode = result.get("orchestration_mode") or "unknown"
    name = result.get("agent_name") or "(unnamed agent)"
    sens = result.get("collision_sensitivity")
    lines: List[str] = []

    lines.append(f"# Copilot Studio Agent Lint Report")
    lines.append("")
    if result.get("schema_warning"):
        lines.append(f"> [!WARNING]")
        lines.append(f"> {result['schema_warning']}")
        lines.append("")
    lines.append(f"**Agent:** {name}  ")
    lines.append(f"**Mode:** {mode}  ")
    lines.append(f"**Confidence:** {result['lint_confidence']}  ")
    lines.append(f"**Analyzed:** {a.get('topics',0)} topic(s), {a.get('skills',0)} "
                 f"skill(s), {a.get('tools',0)} tool(s)  ")
    if sens is not None:
        lines.append(f"**Collision sensitivity:** {sens} "
                     f"(lower with `--threshold` to catch weaker overlaps)  ")
    lines.append("")

    # Summary line
    if s["clean"]:
        lines.append("## Result: No structural issues found")
        lines.append("")
        lines.append("The applicable structural checks ran and found nothing to flag. "
                     "On a well-built agent this is the expected result.")
    else:
        lines.append("## Result")
        lines.append("")
        lines.append(f"**{s['total']} finding(s)** — {s['correctness']} correctness, "
                     f"{s['hygiene']} hygiene ({s['high']} high-severity).")
    lines.append("")

    # Findings
    if not s["clean"]:
        for tier in ("correctness", "hygiene"):
            group = [f for f in result["findings"] if f["tier"] == tier]
            if not group:
                continue
            lines.append(f"### {tier.capitalize()} findings")
            lines.append("")
            for f in group:
                lines.append(f"#### `{f['rule']}` · {f['severity'].upper()} · {f['title']}")
                lines.append("")
                if f.get("file"):
                    loc = f["file"] + (f":{f['line']}" if f.get("line") else "")
                    lines.append(f"- **Location:** `{loc}`")
                lines.append(f"- **Evidence:** {f['evidence']}")
                lines.append(f"- **Fix:** {f['fix']}")
                lines.append("")

    # Component inventory — accounts for every part of the agent
    inv = result.get("component_inventory")
    if inv:
        lines.append("## Component inventory")
        lines.append("")
        lines.append("| Component | Present | Detail |")
        lines.append("|---|:---:|---|")
        lines.append(f"| Model | {'yes' if inv.get('model') else '—'} | {inv.get('model') or 'not specified'} |")
        lines.append(f"| Topics | {inv.get('topics',0)} | classic dialog topics |")
        if inv.get("skills", 0) or inv.get("mode") in ("agentic", "hybrid"):
            lines.append(f"| Skills | {inv.get('skills',0)} | agentic InlineAgentSkills |")
        instr = inv.get("instructions", {})
        instr_detail = f"{instr.get('length',0):,} chars" if instr.get("present") else "none found"
        if instr.get("present"):
            instr_detail += f" (~{_estimate_tokens(instr.get('length', 0)):,} tokens)"
        if instr.get("source_file"):
            instr_detail += f" ({instr['source_file']})"
        lines.append(f"| Main instructions | {'yes' if instr.get('present') else 'no'} | {instr_detail} |")
        mem = inv.get("memory_enabled")
        lines.append(f"| Memory | {'on' if mem else ('off' if mem is False else '—')} | "
                     f"{'enabled' if mem else ('disabled' if mem is False else 'not specified')} |")
        ws = inv.get("web_search_enabled")
        lines.append(f"| Web search | {'on' if ws else ('off' if ws is False else '—')} | "
                     f"{inv.get('knowledge_sources',0)} knowledge source(s) |")
        lines.append(f"| Evaluation | {inv.get('evaluation_sets',0)} set(s) | "
                     f"{inv.get('evaluation_cases',0)} test case(s) |")
        if inv.get("connected_agents", 0):
            lines.append(f"| Connected agents | {inv.get('connected_agents',0)} | "
                         f"child execution agent(s) |")
        if inv.get("contracts", 0):
            lines.append(f"| Contracts | {inv.get('contracts',0)} | request/result schema(s) |")
        lines.append("")
        # tools detail
        tools = inv.get("tools", [])
        if tools:
            lines.append("**Tools**")
            lines.append("")
            lines.append("| Tool | Kind | Operations / Inputs | Connected |")
            lines.append("|---|---|---:|:---:|")
            for t in tools:
                if t["kind"] == "McpTool":
                    detail = f"{t['operations']} ops"
                    conn = "yes" if t.get("connected") else "**no**"
                elif t["kind"] == "WorkflowTool":
                    detail = f"{t.get('inputs',0)} inputs"
                    conn = "—"
                else:
                    detail = "—"; conn = "—"
                lines.append(f"| {t['name']} | {t['kind']} | {detail} | {conn} |")
            lines.append("")

    # Guardrail & instruction-quality summary — shown for ANY experience, so a
    # clean agent still shows the controls were checked.
    gs = result.get("guardrail_summary", {})
    if gs.get("present"):
        lines.append("## Guardrail & instruction-quality checks")
        lines.append("")
        src = f" (from {gs['source_file']})" if gs.get("source_file") else ""
        lines.append(f"Presence of key controls in the agent's main instructions{src}. "
                     "These are structural presence checks, reported as advisory — not a "
                     "security audit of whether a control is sufficient.")
        lines.append("")
        lines.append("| Control | Present | Why it matters |")
        lines.append("|---|:---:|---|")
        for r in gs.get("rows", []):
            mark = "yes" if r["ok"] else "**no**"
            lines.append(f"| {r['control']} | {mark} | {r['note']} |")
        lines.append("")
    elif gs.get("present") is False:
        lines.append("## Guardrail & instruction-quality checks")
        lines.append("")
        lines.append("No main agent instructions were found, so guardrail-presence "
                     "checks could not be applied. If this agent should have "
                     "always-loaded instructions, that absence is itself worth "
                     "confirming.")
        lines.append("")

    # Connected agents (modernized / multi-agent)
    ca = result.get("connected_agents", [])
    if ca:
        lines.append("## Connected agents")
        lines.append("")
        lines.append("Child/execution agents this agent delegates to. Lengths and tool "
                     "references only — instruction text is not reproduced.")
        lines.append("")
        lines.append("| Agent | Instruction chars | Referenced tools |")
        lines.append("|---|---:|---|")
        for c in ca:
            tools = ", ".join(f"`{t}`" for t in c.get("referenced_tools", [])) or "—"
            lines.append(f"| {c['name']} | {c.get('instruction_chars',0):,} | {tools} |")
        lines.append("")

    # Knowledge sources
    ks = result.get("knowledge_sources", [])
    if ks:
        lines.append("## Knowledge sources")
        lines.append("")
        lines.append("| Source | Kind | Detail |")
        lines.append("|---|---|---|")
        for k in ks:
            lines.append(f"| {k.get('name','—')} | {k.get('source_kind','—')} | {k.get('detail','—')} |")
        lines.append("")

    # Per-skill review (agentic)
    sr = result.get("skill_review", [])
    if sr:
        lines.append("## Skill review")
        lines.append("")
        lines.append("Per-skill inventory and separation margin. Lengths and structure "
                     "only — description and instruction text are never reproduced.")
        lines.append("")
        lines.append("| Skill | Desc chars | ~Tokens | Routing condition | Instr chars | ~Tokens | "
                     "Built-in tools | Custom tools | Closest sibling | Similarity |")
        lines.append("|---|---:|---:|:---:|---:|---:|---:|---|---|---:|")
        for r in sr:
            cond = "yes" if r["states_routing_condition"] else "**no**"
            custom = ", ".join(f"`{t}`" for t in r["tools_custom"]) or "—"
            sib = r["closest_sibling"] or "—"
            lines.append(
                f"| {r['name']} | {r['description_chars']} | ~{r['description_tokens']} | {cond} | "
                f"{r['instruction_chars']} | ~{r['instruction_tokens']} | {len(r['tools_builtin'])} | {custom} | "
                f"{sib} | {r['closest_similarity']:.2f} |"
            )
        lines.append("")
        # Separation summary
        sims = [r["closest_similarity"] for r in sr if r.get("closest_sibling")]
        if sims:
            hi = max(sims)
            lines.append(f"**Separation margin:** the closest any two skill descriptions "
                         f"come is **{hi:.2f}** (flag line is {sens}). "
                         f"{'Well separated — routing is unambiguous.' if hi < (sens or 0.75) else 'Close pair present — see findings.'}")
            lines.append("")

    # Token budget — rough, dependency-free estimate from lengths already
    # collected elsewhere (chars/4); never computed from raw text.
    tb = result.get("token_budget")
    if tb:
        lines.append("## Token budget (estimated)")
        lines.append("")
        lines.append("Rough estimate only (~4 characters/token, a common rule of thumb for "
                     "English text) — not an exact tokenizer count, and actual usage depends "
                     "on the specific model. Computed from lengths already collected "
                     "elsewhere, never from the underlying text.")
        lines.append("")
        lines.append("| Component | ~Tokens |")
        lines.append("|---|---:|")
        lines.append(f"| Main instructions | {tb['instructions_tokens']:,} |")
        if tb["skills_count"]:
            lines.append(f"| All {tb['skills_count']} skill description(s) (always loaded for routing) "
                         f"| {tb['skill_descriptions_tokens_total']:,} |")
            lines.append(f"| **Always loaded each turn** | **{tb['always_loaded_tokens']:,}** |")
            lines.append(f"| + largest single skill's instructions, once selected "
                         f"| {tb['largest_skill_instructions_tokens']:,} |")
            lines.append(f"| **Worst-case single turn** | **{tb['worst_case_turn_tokens']:,}** |")
        else:
            lines.append(f"| **Always loaded each turn** | **{tb['always_loaded_tokens']:,}** |")
        if tb["connected_agents_count"]:
            lines.append(f"| {tb['connected_agents_count']} connected agent(s)' instructions "
                         f"(separate context, not appended to the above) "
                         f"| {tb['connected_agents_tokens_total']:,} |")
            lines.append(f"| **Combined, across every component in this export** "
                         f"| **{tb['combined_export_tokens']:,}** |")
        lines.append("")
        if tb["always_loaded_tokens"] > LARGE_ALWAYS_LOADED_TOKENS:
            lines.append(f"**Status:** ~{tb['always_loaded_tokens']:,} tokens always loaded "
                         f"exceeds the {LARGE_ALWAYS_LOADED_TOKENS:,}-token advisory threshold "
                         f"— see the Token budget advisory note below.")
        else:
            lines.append(f"**Status:** ~{tb['always_loaded_tokens']:,} tokens always loaded is "
                         f"within the {LARGE_ALWAYS_LOADED_TOKENS:,}-token advisory threshold; "
                         f"not flagged.")
        lines.append("")

    # Advisory (semantic, non-durable — clearly separated from findings)
    adv = result.get("advisory", [])
    if adv:
        lines.append("## Advisory notes")
        lines.append("")
        lines.append("*These are judgement calls, not structural defects. They may not "
                     "apply to your design — treat them as prompts to confirm a choice was "
                     "deliberate, not as required fixes.*")
        lines.append("")
        for n in adv:
            lines.append(f"- **{n['topic']}:** {n['note']}")
        lines.append("")

    lines.append("---")
    lines.append(f"*{result.get('note','')}*")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    # Redirecting/piping stdout on Windows can force a non-UTF-8 console
    # codepage, which would otherwise crash on the em-dash/box-drawing
    # characters below with the report already written to --out.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Lint a normalised Copilot Studio agent model.")
    ap.add_argument("normalized", help="Path to normalized.json from ingest_agent.py")
    ap.add_argument("--out", default="lint-report.md",
                    help="Output path (default lint-report.md)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help=f"Collision similarity threshold (default {DEFAULT_THRESHOLD})")
    ap.add_argument("--format", choices=["md", "json", "text"], default="md",
                    help="Report format (default md)")
    ap.add_argument("--guardrails-strict", action="store_true",
                    help="Report guardrail/quality checks as hard findings instead "
                         "of advisory notes. Off by default: these are presence "
                         "proxies, so they are advisory unless you opt in.")
    args = ap.parse_args()

    p = Path(args.normalized)
    if not p.exists():
        print(f"error: {p} not found", file=sys.stderr)
        return 2

    model = json.loads(p.read_text(encoding="utf-8"))
    result = lint(model, args.threshold,
                  guardrails_advisory=not args.guardrails_strict)

    if args.format == "json":
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
    elif args.format == "text":
        # text goes to stdout; still write markdown to --out for the file artifact
        print_text(result)
        Path(args.out).write_text(render_markdown(result), encoding="utf-8")
    else:  # md (default)
        md = render_markdown(result)
        Path(args.out).write_text(md, encoding="utf-8")
        print_text(result)  # concise console summary

    print(f"\nWritten to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
