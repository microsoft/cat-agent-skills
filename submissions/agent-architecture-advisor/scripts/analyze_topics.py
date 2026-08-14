#!/usr/bin/env python3
"""
Deterministic analysis of a normalised agent model.

Produces measurements, not opinions. Everything here is reproducible and
checkable, which is what lets downstream findings carry `high` confidence.
The LLM does classification and judgment; this script does measurement.

Analyses:
  1. Trigger phrase collision matrix   → CFG-01
  2. Orchestration graph               → DSN-03, CFG-03
  3. Configuration completeness        → CFG-02..CFG-08
  4. Topic complexity                  → DSN-02
  5. Variable lifecycle                → DSN-05
  6. Grounding coverage                → CFG-06, COST-04

Similarity uses token-level Jaccard plus a normalised-sequence ratio, with no
external dependencies. This is intentionally conservative: it catches lexical
overlap reliably, which is the dominant cause of real trigger collisions. It
will not catch purely semantic collisions ("cancel my order" vs "I don't want
this anymore"). Where embeddings are available, prefer them — but a
dependency-free default means the analysis always runs.

Usage:
    python analyze_topics.py normalized.json --out analysis.json
    python analyze_topics.py normalized.json --out analysis.json --threshold 0.70
"""

import argparse
import itertools
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

DEFAULT_THRESHOLD = 0.75
REPORT_FLOOR = 0.70          # report pairs at or above this, flag above threshold
MONOLITH_NODE_COUNT = 25     # DSN-02

STOPWORDS = {
    "a", "an", "the", "i", "my", "me", "you", "your", "to", "for", "of", "in",
    "on", "at", "is", "are", "am", "do", "does", "did", "can", "could", "would",
    "please", "want", "need", "how", "what", "where", "when", "help", "with",
    "it", "this", "that", "and", "or", "be", "have", "has", "get", "got",
}

# Action verbs that commonly head a user request. Used to separate the
# *action* from the *object* in a trigger phrase.
#
# Why this matters: "cancel my order" and "change my order" share their object
# but differ in action. Pure lexical similarity scores this low (they share one
# token), yet it is the single highest-risk collision shape in real agents —
# the classifier sees near-identical phrasing around the same entity and routes
# on the weaker signal. Treating same-object/different-action as a structural
# risk catches what token overlap alone misses.
ACTION_VERBS = {
    "cancel", "change", "modify", "update", "edit", "amend", "revise",
    "delete", "remove", "add", "create", "make", "start", "stop", "pause",
    "resume", "return", "refund", "exchange", "replace", "track", "check",
    "find", "search", "view", "show", "book", "reserve", "schedule",
    "reschedule", "confirm", "approve", "reject", "submit", "send",
    "upgrade", "downgrade", "renew", "extend", "transfer", "move",
}


def normalise(phrase: str) -> str:
    p = phrase.lower().strip()
    p = re.sub(r"[^\w\s]", " ", p)
    return re.sub(r"\s+", " ", p).strip()


def tokens(phrase: str) -> Set[str]:
    return {t for t in normalise(phrase).split() if t and t not in STOPWORDS}


def split_action_object(phrase: str) -> Tuple[Set[str], Set[str]]:
    """Separate content tokens into (actions, objects)."""
    content = tokens(phrase)
    actions = content & ACTION_VERBS
    return actions, content - actions


def structural_risk(a: str, b: str) -> Tuple[float, str]:
    """Detect same-object/different-action collisions.

    Returns (risk, reason). Risk is a similarity floor applied when the
    structural pattern is present, independent of token overlap.
    """
    act_a, obj_a = split_action_object(a)
    act_b, obj_b = split_action_object(b)

    if not obj_a or not obj_b:
        return 0.0, ""

    obj_overlap = len(obj_a & obj_b) / max(len(obj_a | obj_b), 1)

    # Same object, both have actions, actions differ → high collision risk
    if obj_overlap >= 0.5 and act_a and act_b and not (act_a & act_b):
        return 0.82, (
            f"same object ({', '.join(sorted(obj_a & obj_b))}) with differing "
            f"actions ({', '.join(sorted(act_a))} vs {', '.join(sorted(act_b))})"
        )

    # Identical object set, one phrase has no explicit action → ambiguous
    if obj_overlap >= 0.8 and (not act_a or not act_b):
        return 0.76, (
            f"same object ({', '.join(sorted(obj_a & obj_b))}) with no "
            f"distinguishing action in one phrase"
        )

    return 0.0, ""


def similarity(a: str, b: str) -> float:
    """Blend Jaccard over content tokens with sequence ratio.

    Jaccard alone over-scores short phrases sharing one content word;
    sequence ratio alone over-scores phrases with similar shape but different
    meaning. The blend is more stable than either. Structural risk then raises
    the floor for same-object/different-action pairs, which lexical measures
    systematically under-score.
    """
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    seq = SequenceMatcher(None, normalise(a), normalise(b)).ratio()
    lexical = 0.6 * jaccard + 0.4 * seq
    struct, _ = structural_risk(a, b)
    return round(max(lexical, struct), 3)


def similarity_explained(a: str, b: str) -> Tuple[float, str]:
    """similarity() plus the reason, for evidence in the findings register."""
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
# 1. Trigger collision matrix (CFG-01)
# --------------------------------------------------------------------------

def collision_matrix(topics: List[Dict], threshold: float) -> Dict[str, Any]:
    pairs: List[Dict[str, Any]] = []
    considered = [t for t in topics if t.get("trigger_phrases") and not t.get("is_system_topic")]

    for t1, t2 in itertools.combinations(considered, 2):
        best = (0.0, None, None, "")
        for p1 in t1["trigger_phrases"]:
            for p2 in t2["trigger_phrases"]:
                s, reason = similarity_explained(p1, p2)
                if s > best[0]:
                    best = (s, p1, p2, reason)
        if best[0] >= REPORT_FLOOR:
            pairs.append({
                "topic_a": t1["name"],
                "topic_b": t2["name"],
                "score": best[0],
                "phrase_a": best[1],
                "phrase_b": best[2],
                "reason": best[3],
                "exceeds_threshold": best[0] >= threshold,
                "severity": "high" if best[0] >= threshold else "medium",
            })

    pairs.sort(key=lambda x: x["score"], reverse=True)
    flagged = [p for p in pairs if p["exceeds_threshold"]]

    return {
        "threshold": threshold,
        "report_floor": REPORT_FLOOR,
        "topics_considered": len(considered),
        "pairs_flagged": len(flagged),
        "pairs_near_threshold": len(pairs) - len(flagged),
        "collisions": pairs,
        "method": "max(0.6*jaccard + 0.4*sequence_ratio, structural_risk)",
        "limitation": (
            "Lexical similarity only. Semantically equivalent phrases with no "
            "shared vocabulary will not be detected."
        ),
    }


# --------------------------------------------------------------------------
# 2. Orchestration graph (DSN-03, CFG-03)
# --------------------------------------------------------------------------

def orchestration_graph(topics: List[Dict]) -> Dict[str, Any]:
    def _norm(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", name.lower())

    names = {t["name"] for t in topics}
    norm_to_name = {_norm(n): n for n in names}
    inbound: Dict[str, List[str]] = {n: [] for n in names}

    # Redirect edges are unreliable across export vintages. When none parsed,
    # dead-end/cycle/reachability signals are meaningless — suppress them rather
    # than flag every leaf topic as a false positive.
    edges_parsed = any(t.get("calls_topics") for t in topics)

    for t in topics:
        for target in t.get("calls_topics", []):
            match = norm_to_name.get(_norm(target))
            if match:
                inbound[match].append(t["name"])

    unreachable = [
        t["name"] for t in topics
        if edges_parsed
        and not t.get("trigger_phrases")
        and not inbound.get(t["name"])
        and not t.get("is_system_topic")
    ] if edges_parsed else []

    # Real dead end: collects user input but has no downstream action to consume it.
    dead_ends = [
        t["name"] for t in topics
        if t.get("has_slot_filling")
        and not t.get("calls_topics")
        and not t.get("tools_invoked")
        and not t.get("is_system_topic")
    ] if edges_parsed else []

    cycles = []
    if edges_parsed:
        for t in topics:
            for target in t.get("calls_topics", []):
                other_name = norm_to_name.get(_norm(target))
                other = next((o for o in topics if o["name"] == other_name), None)
                if not other:
                    continue
                back = {_norm(c) for c in other.get("calls_topics", [])}
                if _norm(t["name"]) in back:
                    pair = tuple(sorted([t["name"], other["name"]]))
                    if pair not in [tuple(sorted(c)) for c in cycles]:
                        cycles.append(list(pair))

    return {
        "topic_count": len(topics),
        "edges_parsed": edges_parsed,
        "unreachable_topics": unreachable,
        "dead_end_topics": dead_ends,
        "potential_cycles": cycles,
        "inbound_edges": {k: v for k, v in inbound.items() if v},
        "note": None if edges_parsed else (
            "No topic redirects were parseable from this export; reachability, "
            "dead-end, and cycle detection were skipped to avoid false positives. "
            "Confirm routing with the user."
        ),
    }


# --------------------------------------------------------------------------
# 3. Configuration completeness (CFG-02..CFG-08)
# --------------------------------------------------------------------------

def configuration_checks(model: Dict[str, Any]) -> Dict[str, Any]:
    cfg = model.get("configuration", {})
    topics = model.get("topics", [])
    checks: List[Dict[str, Any]] = []

    def add(rule: str, name: str, ok: Any, detail: str, severity: str) -> None:
        checks.append({
            "rule": rule,
            "check": name,
            "passed": ok,
            "detail": detail,
            "severity": severity if ok is False else None,
            "confidence": "high" if ok is not None else "low",
        })

    add("CFG-02", "fallback_configured", cfg.get("fallback_configured"),
        "System fallback topic present" if cfg.get("fallback_configured")
        else "No fallback topic detected — unmatched input has no recovery path",
        "high")

    add("CFG-03", "escalation_configured", cfg.get("escalation_configured"),
        "Escalation path present" if cfg.get("escalation_configured")
        else "No human handoff detected — failed conversations have no exit",
        "high")

    add("CFG-08", "welcome_message", cfg.get("welcome_message"),
        "Conversation start guidance present" if cfg.get("welcome_message")
        else "No welcome/capability disclosure — affects containment rate",
        "low")

    add("CFG-05", "content_moderation", cfg.get("content_moderation"),
        f"Moderation: {cfg.get('content_moderation')}" if cfg.get("content_moderation")
        else "Content moderation level not detected in export",
        "medium")

    # CFG-04: slot filling without interruption handling
    slot_no_interrupt = [
        t["name"] for t in topics
        if t.get("has_slot_filling") and not t.get("has_interruption_handling")
    ]
    add("CFG-04", "mid_conversation_correction",
        len(slot_no_interrupt) == 0,
        f"{len(slot_no_interrupt)} topic(s) collect input without a correction path: "
        f"{', '.join(slot_no_interrupt[:5])}" if slot_no_interrupt
        else "Slot-filling topics allow interruption",
        "high")

    # CFG-06: grounding enabled with no bound source
    grounded_no_source = [
        t["name"] for t in topics
        if t.get("grounding_enabled") and not t.get("knowledge_sources")
        and not model.get("knowledge_sources")
    ]
    add("CFG-06", "knowledge_source_binding",
        len(grounded_no_source) == 0,
        f"{len(grounded_no_source)} topic(s) have grounding enabled with no source bound"
        if grounded_no_source else "Knowledge bindings consistent",
        "high")

    # Session timeout is frequently absent from exports entirely. Absence is
    # a parsing gap, not a misconfiguration — report as unknown so the CONFIG
    # rule does not fire on missing data.
    add("CFG-07", "session_timeout",
        True if cfg.get("session_timeout_minutes") else None,
        f"Timeout: {cfg.get('session_timeout_minutes')} min"
        if cfg.get("session_timeout_minutes")
        else "Session timeout not present in export — confirm with the user",
        "medium")

    failed = [c for c in checks if c["passed"] is False]
    unknown = [c for c in checks if c["passed"] is None]

    return {
        "checks": checks,
        "failed_count": len(failed),
        "unknown_count": len(unknown),
        "note": (
            "Checks returning null could not be determined from the export and "
            "should be confirmed with the user rather than reported as findings."
        ),
    }


# --------------------------------------------------------------------------
# 4. Topic complexity (DSN-02)
# --------------------------------------------------------------------------

def complexity_analysis(topics: List[Dict]) -> Dict[str, Any]:
    monoliths = [
        {"name": t["name"], "node_count": t["node_count"]}
        for t in topics
        if t.get("node_count", 0) > MONOLITH_NODE_COUNT
    ]
    monoliths.sort(key=lambda x: x["node_count"], reverse=True)
    counts = [t.get("node_count", 0) for t in topics] or [0]
    return {
        "monolith_threshold": MONOLITH_NODE_COUNT,
        "monolithic_topics": monoliths,
        "median_node_count": sorted(counts)[len(counts) // 2],
        "max_node_count": max(counts),
    }


# --------------------------------------------------------------------------
# 5. Variable lifecycle (DSN-05)
# --------------------------------------------------------------------------

def variable_lifecycle(model: Dict[str, Any]) -> Dict[str, Any]:
    read_without_set, set_without_read, scope_leaks = [], [], []
    for v in model.get("variables", []):
        set_in = set(v.get("set_in", []))
        read_in = set(v.get("read_in", []))
        if read_in and not set_in:
            read_without_set.append({"name": v["name"], "read_in": v["read_in"]})
        if set_in and not read_in:
            set_without_read.append({"name": v["name"], "set_in": v["set_in"]})
        # Topic.X is topic-scoped in Copilot Studio; reads from topics that never set it are scope leaks.
        cross = read_in - set_in
        if set_in and cross:
            scope_leaks.append({
                "name": v["name"],
                "set_in": sorted(set_in),
                "read_in_without_local_set": sorted(cross),
            })
    return {
        "read_without_set": read_without_set,   # user-visible empty responses
        "set_without_read": set_without_read,   # dead assignments
        "scope_leaks": scope_leaks,             # Topic.X read outside the topic that set it
        "total_variables": len(model.get("variables", [])),
    }


# --------------------------------------------------------------------------
# 6. Grounding coverage (CFG-06, COST-04)
# --------------------------------------------------------------------------

def grounding_coverage(model: Dict[str, Any]) -> Dict[str, Any]:
    topics = model.get("topics", [])
    generative = [t for t in topics if t.get("is_generative")]
    grounded = [t for t in topics if t.get("grounding_enabled")]

    # COST-04: grounding on topics that look deterministic
    action_words = ("reset", "cancel", "confirm", "submit", "greeting", "goodbye",
                    "transfer", "escalate", "start", "sign")
    over_grounded = [
        t["name"] for t in grounded
        if any(w in t["name"].lower() for w in action_words)
    ]

    return {
        "total_topics": len(topics),
        "generative_topics": len(generative),
        "grounded_topics": len(grounded),
        "generative_ratio": round(len(generative) / len(topics), 3) if topics else 0.0,
        "knowledge_sources_configured": len(model.get("knowledge_sources", [])),
        "possible_over_grounding": over_grounded,
    }


# --------------------------------------------------------------------------
# Entry
# --------------------------------------------------------------------------

def analyze(model: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    topics = model.get("topics", [])
    result = {
        "schema_version": "1.0",
        "agent_name": model.get("agent", {}).get("name"),
        "platform": model.get("agent", {}).get("platform"),
        "orchestration_mode": model.get("agent", {}).get("orchestration_mode"),
        "analysis_confidence": "high" if model.get("parse_report", {}).get("complete") else "medium",
        "trigger_collisions": collision_matrix(topics, threshold),
        "orchestration": orchestration_graph(topics),
        "configuration": configuration_checks(model),
        "complexity": complexity_analysis(topics),
        "variables": variable_lifecycle(model),
        "grounding": grounding_coverage(model),
    }

    if not topics:
        result["analysis_confidence"] = "low"
        result["warning"] = (
            "No topics available. Topic-level analyses are empty — this reflects "
            "the export, not the agent. Use self-report mode for these areas."
        )
    return result


def print_summary(a: Dict[str, Any]) -> None:
    print(f"Analysis: {a.get('agent_name') or '(unnamed)'} [{a.get('platform')}]")
    print(f"  confidence: {a['analysis_confidence']}")
    tc = a["trigger_collisions"]
    print(f"  trigger collisions: {tc['pairs_flagged']} flagged "
          f"(+{tc['pairs_near_threshold']} near threshold)")
    for c in tc["collisions"][:3]:
        mark = "!" if c["exceeds_threshold"] else "~"
        print(f"    {mark} {c['score']:.2f}  {c['topic_a']} <-> {c['topic_b']}")
        print(f"         \"{c['phrase_a']}\" vs \"{c['phrase_b']}\"")
    o = a["orchestration"]
    print(f"  unreachable topics: {len(o['unreachable_topics'])}")
    print(f"  config checks failed: {a['configuration']['failed_count']} "
          f"(unknown: {a['configuration']['unknown_count']})")
    print(f"  monolithic topics: {len(a['complexity']['monolithic_topics'])}")
    print(f"  read-without-set variables: {len(a['variables']['read_without_set'])}")
    g = a["grounding"]
    print(f"  generative ratio: {g['generative_ratio']:.0%}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyse a normalised agent model.")
    ap.add_argument("normalized", help="Path to normalized.json from ingest_agent.py")
    ap.add_argument("--out", default="analysis.json")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help=f"Collision similarity threshold (default {DEFAULT_THRESHOLD})")
    args = ap.parse_args()

    p = Path(args.normalized)
    if not p.exists():
        print(f"error: {p} not found", file=sys.stderr)
        return 2

    model = json.loads(p.read_text(encoding="utf-8"))
    result = analyze(model, args.threshold)
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print_summary(result)
    print(f"\nWritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
