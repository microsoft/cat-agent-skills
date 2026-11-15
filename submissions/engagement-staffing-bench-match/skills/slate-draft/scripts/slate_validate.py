#!/usr/bin/env python3
"""slate_validate - deterministic secondary safety check and slate-draft renderer.

``validate(governed_payload)`` is the pure engine (no file I/O) and ``render_draft(validated)``
renders the slate-draft skeleton from its result (A23). The CLI never trusts a supplied
governed.json: it re-derives the governed document from roles.json, bench.json and constraints.json
with the vendored fit_score, slate_rank and constraint_check engines and refuses any difference
(independence-eligibility-rules.md #9.8) before validating the re-derived document, then writes
validated.json and slate-draft.md together (both files or neither).

``validate()`` is also safe on a hand-built document: it checks every field it relies on, refuses a
document whose derived lists (recommendations, gaps, top-candidate refusals) do not re-derive from
its own slates, refuses engine markers that no escalation accounts for (#9.6, #9.8), re-applies the
register row rules and the fit-score floor to every recommendation, and withholds any recommended
candidate that carries held text or that an open escalation names. Error messages name field paths
only, never values.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import constraint_check
import fit_score
from input_guard import (
    ArgumentParser,
    InputError,
    canonical,
    check_confidence,
    check_date,
    check_id,
    engagement_id_key,
    check_name,
    duplicate_keys,
    field,
    has_marker,
    id_key,
    is_num,
    is_reserved_label,
    load_json,
    mentions_id,
    need,
    run,
    same_document,
    text_list,
)
from safety_text import (
    ENGINE_MARKER,
    HOLD_REASONS,
    HOLD_RULE,
    OVERSIZE_REASON,
    ScreeningLog,
    is_engine_marker,
    is_suspect,
    list_run_indices,
    record_hits,
    sanitize_free_text,
)

CONTRACT = "ps.engagement-staffing-bench-match.v1"
ENGINE = "engine:slate_validate"
ENGINE_VERSION = "slate_validate/1.1.14"
SAFE_DISPOSITIONS = {"clear", "resolved", "non_material", "not_applicable"}
BLOCKING_TYPES = {
    "financial_interest",
    "ethical_wall",
    "adverse_matter",
    "prior_client_role",
    "prior_assurance_role",
}
MIN_RECOMMENDABLE_SCORE = 70.0
VERDICTS = {"eligible", "needs_review", "ineligible"}
RECOMMENDATION_STATUSES = {"recommended", "not_recommended", "below_score_floor"}
AVAILABILITY_TYPES = {"availability", "availability_evidence"}
COVERAGE_TYPE = "conflicts_register_coverage"
# Rows constraint_check writes itself (not register rows); they are never rebuilt as register input.
ENGINE_ROW_TYPES = AVAILABILITY_TYPES | {COVERAGE_TYPE, "source_screening"}
# Constraint types the draft may name as a conflict category; anything else shows as "unrecognised".
CATEGORY_TYPES = set(constraint_check.KNOWN_TYPES) | ENGINE_ROW_TYPES
REGISTER_FIELDS = (
    "type", "client_name", "status", "material", "role_type", "process", "end_date",
    "resolved_date", "source", "confidence", "citation",
)
DISPOSITION_RANK = {
    "clear": 0, "resolved": 0, "non_material": 0, "not_applicable": 0,
    "needs_review": 1, "ineligible": 2,
}
RULES = "independence-eligibility-rules.md"
RULE_ROWS = f"{RULES} #9.1"
RULE_COVERAGE = f"{RULES} #9.4"
RULE_MALFORMED_ROW = f"{RULES} #9.9"
RULE_VERDICT = f"{RULES} #1.2"
RULE_FLOOR = "fit-scoring-rubric.md #7.2"
TEXT_HOLD_PROBLEM = (
    "instruction-like, mixed-script or format-character text was found in the source record"
)
MARKER_HOLD_PROBLEM = "source text held for review is present in the candidate record"
COMPOSED_HOLD_PROBLEM = "recommendation evidence withheld for review"
ESCALATION_HOLD_PROBLEM = "an open escalation names this candidate"
FOREIGN_RULE = constraint_check.FOREIGN_RULE
FOREIGN_REASON = constraint_check.FOREIGN_REASON
UNVERIFIED_REASON = constraint_check.UNVERIFIED_REASON
UNVERIFIED_RULE = constraint_check.UNVERIFIED_RULE
DRAFT_BANNER = (
    "DRAFT - HUMAN REVIEW REQUIRED",
    "DRAFT - pending partner approval and independence/resource-management review",
)
WITHHELD_CELL = f"withheld ({HOLD_RULE})"
MISSING_CELL = "not in validated.json"
_RULE_SECTION = re.compile(
    r"(?:(?:fit-scoring-rubric|independence-eligibility-rules)\.md|rubric) #\d+\.\d+(?:[-,]#\d+\.\d+)*"
)
_ROLE_SCOPE = re.compile(r"([^\s:]+):")
# Field names that may appear in an error path; any other member name prints as <member> (D17).
KNOWN_KEYS = {
    "contract_version", "engagement", "engagement_id", "client_name", "affiliates", "source",
    "confidence", "citation", "roles", "role_id", "title", "start_date", "allocation_pct",
    "required_skills", "escalations", "provenance", "engines", "bench_candidates", "scored_roles",
    "ranked_roles", "governed_roles", "role_title", "candidate_slate", "recommended_candidates",
    "top_provisional_candidate_refused", "candidate_id", "candidate_name", "fit_score",
    "component_scores", "component_citations", "availability_context", "provisional_rank",
    "rank_source", "rank_citation", "constraints_considered", "eligibility", "verdict",
    "recommendation_status", "blocking_rule", "reasons", "final_eligible_rank", "screening_holds",
    "type", "status", "material", "role_type", "process", "end_date", "resolved_date",
    "applies_to_engagement", "disposition", "reason", "gaps", "gap_statement", "candidate_scores",
}
_ESCALATION_KINDS = (
    (": instruction-like text redacted; review source record", "instruction"),
    (f": {OVERSIZE_REASON}", "oversize"),
    (f": already-redacted marker text withheld; review source record ({HOLD_RULE})", "marker"),
    (": instruction-like member name withheld; review source record", "key"),
)
_MARKER_KINDS = {"instruction-like": "instruction", "oversize": "oversize", "already-redacted": "marker"}
_MARKER_PARTS = re.compile(
    r"\[FLAGGED: (instruction-like|oversize|already-redacted) source (citation|text|key) "
    r"(?:redacted|withheld); sha256=[0-9a-f]{12}\]"
)
_HOLD_LINE = re.compile(r"(.+): (" + "|".join(re.escape(text) for text in HOLD_REASONS.values())
                        + r") \(" + re.escape(HOLD_RULE) + r"\)")
_PATH_TOKEN = re.compile(r"\[(\d+)\]|\.?([^.\[\]]+)")
_MISSING = object()


def merge_unique(*groups):
    merged = []
    seen = set()
    for group in groups:
        for item in group or []:
            text = str(item)
            if text not in seen:
                seen.add(text)
                merged.append(text)
    return merged


def normalize_entity_name(name):
    return constraint_check.normalize_entity_name(name)


def entity_names_match(left, right):
    return constraint_check.entity_names_match(left, right)


def matches_engagement(item, engagement):
    """True/False/None: does a register row's entity match the client or a declared affiliate."""
    record_name = item.get("client_name")
    if not isinstance(record_name, str) or not record_name.strip():
        return None
    affiliates = engagement.get("affiliates", [])
    if isinstance(affiliates, str):
        affiliates = [affiliates]
    if not isinstance(affiliates, list):
        affiliates = []
    comparisons = [
        entity_names_match(record_name, target)
        for target in [engagement.get("client_name"), *affiliates]
        if isinstance(target, str) and constraint_check.entity_matchable(target)
    ]
    if any(value is True for value in comparisons):
        return True
    # A name that only partly matches the client or an affiliate (a whole-word part of it, or it of
    # the entity) is never another client's: it cannot be verified either way (rule 9.9).
    return None if not comparisons or any(value is None for value in comparisons) else False


def _word(value):
    return value.strip().casefold() if isinstance(value, str) else ""


def _constraint_problems(candidate, engagement=None):
    """(problem, rule) pairs for a candidate's carried constraint rows (rules 9.1, 9.4, 9.9)."""
    engagement = engagement if isinstance(engagement, dict) else {}
    considered = candidate.get("constraints_considered") if isinstance(candidate, dict) else None
    if not considered or not isinstance(considered, list):
        return [("constraints_considered[] is missing", RULE_COVERAGE)]
    problems = []
    rows = [item for item in considered if isinstance(item, dict)]
    if not [item for item in rows if _word(item.get("type")) not in AVAILABILITY_TYPES]:
        problems.append(("no conflicts-register record considered", RULE_COVERAGE))
    for index, item in enumerate(considered):
        if not isinstance(item, dict):
            problems.append((f"constraints_considered[{index}] is not an object", RULE_MALFORMED_ROW))
            continue
        kind = _word(item.get("type"))
        disposition = _word(item.get("disposition"))
        reason = item.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = kind or "unexplained constraint"
        applies = item.get("applies_to_engagement")
        if applies is not True and applies is not False:
            problems.append((
                f"constraints_considered[{index}].applies_to_engagement is not true or false",
                RULE_MALFORMED_ROW,
            ))
        if applies is not False and disposition not in SAFE_DISPOSITIONS:
            problems.append((reason, RULE_ROWS))
        if kind == COVERAGE_TYPE:
            problems.append((reason, RULE_COVERAGE))
        if kind in BLOCKING_TYPES and disposition == "clear":
            problems.append((f"{kind} cannot be dispositioned as clear", RULE_ROWS))
        if disposition == "not_applicable":
            matched = matches_engagement(item, engagement)
            if matched is True:
                problems.append((
                    f"{kind or 'conflict'} marked not_applicable but matches client or affiliate",
                    RULE_ROWS,
                ))
            elif matched is None:
                problems.append((
                    f"{kind or 'conflict'} marked not_applicable cannot be independently verified",
                    RULE_ROWS,
                ))
    return _unique_pairs(problems)


def _unique_pairs(pairs):
    seen, unique = set(), []
    for text, rule in pairs:
        if text not in seen:
            seen.add(text)
            unique.append((text, rule))
    return unique


def unexplained_constraints(candidate, engagement=None):
    return [text for text, _ in _constraint_problems(candidate, engagement)]


def _rederived_row_problems(candidate, role, engagement):
    """Re-apply constraint_check's row rules to the carried register rows (B5/A23)."""
    considered = candidate["constraints_considered"]
    carried = [item for item in considered if _word(item.get("type")) not in ENGINE_ROW_TYPES]
    rows = []
    for item in carried:
        raw = {"candidate_id": candidate["candidate_id"]}
        raw.update({key: item[key] for key in REGISTER_FIELDS if key in item})
        rows.append(raw)
    constraints = {
        "engagement": engagement,
        "roles": [{"role_id": role["role_id"], "start_date": role["start_date"]}],
        "constraints": rows,
    }
    role_view = {"role_id": role["role_id"], "title": role["title"], "start_date": role["start_date"]}
    try:
        verdict, reasons, citations, derived = constraint_check.verdict_for(
            role_view, candidate, constraints
        )
        if verdict == "ineligible":
            _, rule = constraint_check.blocking_reason(reasons, citations)
        else:
            _, rule = constraint_check.review_reason(reasons, citations)
    except Exception:  # any failure to re-apply the rules is itself a reason to withhold
        return [("constraint rows cannot be re-evaluated under the independence rules", RULE_ROWS)], False
    rule = rule if isinstance(rule, str) and not has_marker(rule) and len(rule) < 80 else RULE_ROWS
    derived_register = [item for item in derived if _word(item.get("type")) not in ENGINE_ROW_TYPES]
    problems = []
    if len(derived_register) != len(carried):
        problems.append(("constraint rows do not re-derive under the independence rules", rule))
    else:
        for index, (mine, theirs) in enumerate(zip(derived_register, carried)):
            derived_rank = DISPOSITION_RANK.get(mine.get("disposition"), 2)
            carried_rank = DISPOSITION_RANK.get(_word(theirs.get("disposition")), 0)
            if derived_rank > carried_rank:
                problems.append((
                    f"register row {index + 1} re-derives as {mine.get('disposition')} "
                    "under the independence rules",
                    rule,
                ))
    stricter = verdict != "eligible"
    return problems + ([(f"constraint evidence re-derives as {verdict}", rule)] if stricter else []), stricter


# --- path helpers (paths are rebuilt from the document, never echoed from input text) ---

def _parse_path(path):
    tokens, position = [], 0
    while position < len(path):
        match = _PATH_TOKEN.match(path, position)
        if not match or match.end() == position:
            return None
        tokens.append(int(match.group(1)) if match.group(1) is not None else match.group(2))
        position = match.end()
    return tokens


def _path_text(tokens):
    text = ""
    for token in tokens:
        text += f"[{token}]" if isinstance(token, int) else (f".{token}" if text else token)
    return text


def _safe_path(tokens):
    return _path_text([
        token if isinstance(token, int) or token in KNOWN_KEYS else "<member>" for token in tokens
    ])


def _context(node, context):
    """(role key, candidate key) of the nearest enclosing role and candidate records."""
    if isinstance(node, dict):
        role_key, candidate_key = context
        if "role_id" in node and id_key(node.get("role_id")):
            role_key = id_key(node.get("role_id"))
        if "candidate_id" in node and id_key(node.get("candidate_id")):
            candidate_key = id_key(node.get("candidate_id"))
        return role_key, candidate_key
    return context


def _resolve(document, tokens):
    node, context = document, _context(document, (None, None))
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(node, list) or not 0 <= token < len(node):
                return _MISSING, context
            node = node[token]
        else:
            if not isinstance(node, dict) or token not in node:
                return _MISSING, context
            node = node[token]
        context = _context(node, context)
    return node, context


def _walk(node, tokens, context):
    context = _context(node, context)
    if isinstance(node, dict):
        for key, value in node.items():
            yield "key", key, tokens + [key], context
            yield from _walk(value, tokens + [key], context)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, tokens + [index], context)
    elif isinstance(node, str):
        yield "value", node, tokens, context


def _escalation_index(escalations):
    index = []
    for escalation in escalations:
        for suffix, kind in _ESCALATION_KINDS:
            if escalation.endswith(suffix):
                path = escalation[: -len(suffix)]
                index.append((path.split(".", 1)[1] if "." in path else path, kind))
                break
    return index


def _compatible(origin, here):
    return not (origin[1] and here[1] and origin[1] != here[1])


def _held(scopes, role_key, candidate_key):
    for held_role, held_candidate in scopes:
        if held_candidate is None and held_role is not None and held_role == role_key:
            return True
        if held_candidate is not None and held_candidate == candidate_key and held_role in (None, role_key):
            return True
    return False


def _check_markers(document):
    """D21/B6: every engine marker and screening hold must be bound to its own escalation.

    Returns the (role, candidate) scopes under governed_roles that carry bound held text.
    """
    escalations = document["escalations"]
    index = _escalation_index(escalations)
    held = set()
    unresolved_origin = {}
    pigeonholed = {}
    for kind_of_item, text, tokens, context in _walk(
        {key: value for key, value in document.items() if key != "escalations"}, [], (None, None)
    ):
        where = _safe_path(tokens)
        in_slate = bool(tokens) and tokens[0] == "governed_roles"
        if kind_of_item == "key":
            if not has_marker(text):
                continue
            need(
                _MARKER_PARTS.fullmatch(text) is not None and any(
                    f".{text}: instruction-like member name withheld; review source record" in escalation
                    for escalation in escalations
                ),
                f"{where} member name carries a marker with no matching escalation "
                f"({HOLD_RULE}; rule 9.8)",
            )
            if in_slate:
                held.add(context)
            continue
        if not has_marker(text):
            continue
        need(is_engine_marker(text),
             f"{where} carries marker text that is not in engine form ({HOLD_RULE}; rule 9.8)")
        here = _path_text(tokens)
        for match in _MARKER_PARTS.finditer(text):
            marker = match.group(0)
            kind = "key" if match.group(2) == "key" else _MARKER_KINDS[match.group(1)]
            bound = kind == "key" and any(
                f".{marker}: instruction-like member name withheld; review source record" in escalation
                for escalation in escalations
            )
            for origin_path, origin_kind in ([] if bound else index):
                if origin_kind != kind:
                    continue
                if origin_path == here:
                    bound = True
                    break
                origin_tokens = _parse_path(origin_path)
                if not origin_tokens:
                    continue
                value, origin_context = _resolve(document, origin_tokens)
                if value is _MISSING:
                    if origin_tokens[0] == "constraints":
                        unresolved_origin.setdefault(kind, set()).add(origin_path)
                    continue
                if isinstance(value, str) and marker in value and _compatible(origin_context, context):
                    bound = True
                    break
            if not bound:
                # Register rows are not carried in governed.json: a marker from a constraints row
                # binds only to a distinct constraints escalation of the same kind.
                pigeonholed.setdefault(kind, set()).add(marker)
                need(
                    context[1] is not None and len(pigeonholed[kind]) <= len(unresolved_origin.get(kind, ())),
                    f"{where} carries an engine marker with no matching escalation "
                    f"({HOLD_RULE}; rule 9.8)",
                )
            if in_slate:
                held.add(context)
    return held, index


def _check_holds(candidate, where, index, context, held):
    holds = candidate.get("screening_holds")
    if holds is None:
        return
    need(isinstance(holds, list), f"{where}.screening_holds must be an array")
    paths = {path for path, _ in index}
    for position, line in enumerate(holds):
        match = _HOLD_LINE.fullmatch(line) if isinstance(line, str) else None
        need(match is not None and match.group(1) in paths,
             f"{where}.screening_holds[{position}] is not bound to a matching escalation "
             f"({HOLD_RULE}; rule 9.8)")
    if holds:
        held.add(context)


# --- structure (A1/A2/A7, A21/D25) ---

def _name(value, path):
    if isinstance(value, str) and re.fullmatch(ENGINE_MARKER, value.strip()):
        return value
    return check_name(value, path)


def _no_duplicates(values, where):
    need(not duplicate_keys(values), f"{where} has duplicate IDs (independence-eligibility-rules.md #9.7)")


def _check_engagement(document):
    engagement = field(document, "engagement", "obj", "")
    need(engagement, "engagement must not be empty")
    check_id(field(engagement, "engagement_id", "str", "engagement"), "engagement.engagement_id")
    _name(field(engagement, "client_name", "str", "engagement"), "engagement.client_name")
    for position, affiliate in enumerate(field(engagement, "affiliates", "list", "engagement")):
        _name(affiliate, f"engagement.affiliates[{position}]")
    field(engagement, "source", "str", "engagement")
    check_confidence(field(engagement, "confidence", "num", "engagement"), "engagement.confidence")
    field(engagement, "citation", "str", "engagement")
    return engagement


def _check_roles(document):
    roles = field(document, "roles", "list", "")
    need(roles, "roles must not be empty")
    by_key = {}
    for position, role in enumerate(roles):
        where = f"roles[{position}]"
        need(isinstance(role, dict), f"{where} must be an object")
        check_id(field(role, "role_id", "str", where), f"{where}.role_id")
        _name(field(role, "title", "str", where), f"{where}.title")
        check_date(field(role, "start_date", "str", where), f"{where}.start_date")
        field(role, "allocation_pct", "num", where)
        field(role, "required_skills", "list", where)
        field(role, "source", "str", where)
        check_confidence(field(role, "confidence", "num", where), f"{where}.confidence")
        field(role, "citation", "str", where)
        by_key[id_key(role["role_id"])] = role
    _no_duplicates([role["role_id"] for role in roles], "roles")
    return by_key


def _check_candidate(candidate, where):
    need(isinstance(candidate, dict), f"{where} must be an object")
    check_id(field(candidate, "candidate_id", "str", where), f"{where}.candidate_id")
    _name(field(candidate, "candidate_name", "str", where), f"{where}.candidate_name")
    field(candidate, "fit_score", "num", where)
    for key in ("component_scores", "component_citations", "availability_context"):
        field(candidate, key, "obj", where)
    context = candidate["availability_context"]
    for flag in ("evidence_complete", "duration_assumed"):
        if flag in context:
            need(context[flag] is True or context[flag] is False,
                 f"{where}.availability_context.{flag} must be true or false")
    field(candidate, "source", "str", where)
    check_confidence(field(candidate, "confidence", "num", where), f"{where}.confidence")
    field(candidate, "citation", "str", where)
    field(candidate, "provisional_rank", "int", where)
    field(candidate, "rank_source", "str", where)
    field(candidate, "rank_citation", "str", where)
    field(candidate, "final_eligible_rank", "int", where, required=False)
    considered = field(candidate, "constraints_considered", "list", where)
    for position, row in enumerate(considered):
        need(isinstance(row, dict), f"{where}.constraints_considered[{position}] must be an object")
        if "material" in row:
            need(row["material"] is None or isinstance(row["material"], bool),
                 f"{where}.constraints_considered[{position}].material must be true, false or null")
    eligibility = field(candidate, "eligibility", "obj", where)
    path = f"{where}.eligibility"
    need(field(eligibility, "verdict", "str", path) in VERDICTS,
         f"{path}.verdict must be eligible, needs_review or ineligible")
    need(field(eligibility, "recommendation_status", "str", path) in RECOMMENDATION_STATUSES,
         f"{path}.recommendation_status must be recommended, not_recommended or below_score_floor")
    need("blocking_rule" in eligibility, f"{path}.blocking_rule is required")
    field(eligibility, "blocking_rule", "str", path, nullable=True)
    text_list(eligibility, "reasons", path)
    field(eligibility, "source", "str", path)
    check_confidence(field(eligibility, "confidence", "num", path), f"{path}.confidence")
    field(eligibility, "citation", "str", path)
    need("secondary_validation" not in candidate,
         f"{where}.secondary_validation is validator output and must not be supplied")


def _check_structure(document):
    need(isinstance(document, dict) and document.get("contract_version") == CONTRACT,
         "wrong governed contract (contract_version)")
    engagement = _check_engagement(document)
    roles = _check_roles(document)
    text_list(document, "escalations", "")
    provenance = field(document, "provenance", "obj", "")
    text_list(provenance, "engines", "provenance", required=False)
    governed_roles = field(document, "governed_roles", "list", "")
    for position, role in enumerate(governed_roles):
        where = f"governed_roles[{position}]"
        need(isinstance(role, dict), f"{where} must be an object")
        role_id = check_id(field(role, "role_id", "str", where), f"{where}.role_id")
        need(id_key(role_id) in roles, f"{where}.role_id is not one of the roles (rule 9.8)")
        title = _name(field(role, "role_title", "str", where), f"{where}.role_title")
        need(title == roles[id_key(role_id)]["title"],
             f"{where}.role_title does not match its role (rule 9.8)")
        field(role, "top_provisional_candidate_refused", "bool", where)
        field(role, "source", "str", where)
        check_confidence(field(role, "confidence", "num", where), f"{where}.confidence")
        field(role, "citation", "str", where)
        need("top_provisional_candidate_withheld" not in role,
             f"{where}.top_provisional_candidate_withheld is validator output and must not be supplied")
        slate = field(role, "candidate_slate", "list", where)
        for index, candidate in enumerate(slate):
            _check_candidate(candidate, f"{where}.candidate_slate[{index}]")
        _no_duplicates([candidate["candidate_id"] for candidate in slate], f"{where}.candidate_slate")
        recommended = field(role, "recommended_candidates", "list", where)
        for index, candidate in enumerate(recommended):
            _check_candidate(candidate, f"{where}.recommended_candidates[{index}]")
        _no_duplicates([candidate["candidate_id"] for candidate in recommended],
                       f"{where}.recommended_candidates")
    _no_duplicates([role["role_id"] for role in governed_roles], "governed_roles")
    need({id_key(role["role_id"]) for role in governed_roles} == set(roles),
         "governed_roles does not cover every role (rule 9.8)")
    gaps = field(document, "gaps", "list", "")
    for position, gap in enumerate(gaps):
        where = f"gaps[{position}]"
        need(isinstance(gap, dict), f"{where} must be an object")
        check_id(field(gap, "role_id", "str", where), f"{where}.role_id")
        _name(field(gap, "role_title", "str", where), f"{where}.role_title")
        for key in ("gap_statement", "source", "citation"):
            field(gap, key, "str", where)
        field(gap, "confidence", "num", where)
    return engagement, roles


# --- identity (A19/C5) ---

def _same_identity(expected, carried, key):
    if not isinstance(expected, str) or not expected.strip() or not isinstance(carried, str):
        return True
    if re.fullmatch(ENGINE_MARKER, carried.strip()):
        digest = hashlib.sha256(expected.strip().encode("utf-8")).hexdigest()[:12]
        return f"sha256={digest}" in carried
    if key == "engagement_id":
        return engagement_id_key(expected) == engagement_id_key(carried)
    # Client names reconcile with the shared identity classifier every engine uses (rule 9.10).
    return constraint_check.same_client(expected, carried)


def _check_identity(document, engagement, intake_engagements):
    witnesses = [(label, value) for label, value in intake_engagements]
    witnesses.append(("provenance", document["provenance"]))
    witnesses.extend((f"roles[{position}]", role) for position, role in enumerate(document["roles"]))
    for label, witness in witnesses:
        if not isinstance(witness, dict):
            continue
        for key in ("engagement_id", "client_name"):
            need(_same_identity(witness.get(key), engagement[key], key),
                 f"engagement.{key} does not match the {label} engagement (rule 9.8)")
    client = engagement["client_name"]
    client_marked = has_marker(client)
    for position, role in enumerate(document["governed_roles"]):
        for slate in ("candidate_slate", "recommended_candidates"):
            for index, candidate in enumerate(role[slate]):
                for row_index, row in enumerate(candidate["constraints_considered"]):
                    name = row.get("client_name")
                    if not isinstance(name, str) or not name.strip() or has_marker(name) or is_suspect(name):
                        continue
                    where = f"governed_roles[{position}].{slate}[{index}].constraints_considered[{row_index}]"
                    if name == constraint_check.FOREIGN_LABEL and row.get("disposition") == "needs_review":
                        continue  # a malformed other-client row (#9.9): it can only hold the candidate
                    if _word(row.get("type")) == COVERAGE_TYPE:
                        need(client_marked or canonical(name) == canonical(client),
                             f"{where}.client_name names a different engagement client (rule 9.8)")
                    elif row.get("applies_to_engagement") is True and _word(row.get("type")) not in AVAILABILITY_TYPES:
                        need(matches_engagement(row, engagement) is not False,
                             f"{where} applies to an entity that is not the engagement client or a "
                             "declared affiliate (rule 9.8)")


# --- derived lists (A20/A22) ---

def _expected_gap(role):
    title = role["title"]
    return {
        "role_id": role["role_id"],
        "role_title": title,
        "gap_statement": (
            f"No eligible candidate meets the {constraint_check.MIN_RECOMMENDABLE_SCORE} fit-score floor "
            f"for {title}; do not pad the slate."
        ),
        "source": constraint_check.ENGINE,
        "confidence": 0.99,
        "citation": "fit-scoring-rubric.md #7.2; independence-eligibility-rules.md #7.2",
    }


def _check_derived(document, roles):
    expected_gaps = []
    for position, role in enumerate(document["governed_roles"]):
        where = f"governed_roles[{position}]"
        slate = role["candidate_slate"]
        need([candidate["provisional_rank"] for candidate in slate] == list(range(1, len(slate) + 1)),
             f"{where}.candidate_slate provisional ranks do not re-derive (rule 9.8)")
        recommended = [
            candidate for candidate in slate
            if candidate["eligibility"]["recommendation_status"] == "recommended"
        ]
        for index, candidate in enumerate(slate):
            if candidate["eligibility"]["recommendation_status"] == "recommended":
                continue
            need("final_eligible_rank" not in candidate,
                 f"{where}.candidate_slate[{index}].final_eligible_rank is set on a candidate that is "
                 "not recommended (rule 9.8)")
        need([candidate.get("final_eligible_rank") for candidate in recommended]
             == list(range(1, len(recommended) + 1)),
             f"{where} final eligible ranks do not re-derive (rule 9.8)")
        need(same_document(role["recommended_candidates"], recommended),
             f"{where}.recommended_candidates does not re-derive from its candidate_slate (rule 9.8)")
        refused = any(
            candidate["provisional_rank"] == 1 and candidate["eligibility"]["verdict"] == "ineligible"
            for candidate in slate
        )
        need(role["top_provisional_candidate_refused"] is refused,
             f"{where}.top_provisional_candidate_refused does not re-derive (rule 9.8)")
        if not recommended:
            expected_gaps.append(_expected_gap(roles[id_key(role["role_id"])]))
    need(same_document(document["gaps"], expected_gaps),
         "gaps does not re-derive from governed_roles (rule 9.8)")


# --- gating ---

def _recommendation_problems(candidate, role, engagement):
    problems = _constraint_problems(candidate, engagement)
    if candidate["eligibility"]["verdict"] != "eligible":
        problems.append((
            f"eligibility verdict is {candidate['eligibility']['verdict']}, not eligible", RULE_VERDICT
        ))
    fit_score = candidate["fit_score"]
    if fit_score < MIN_RECOMMENDABLE_SCORE:
        problems.append((
            f"fit_score {fit_score:g} is below the {MIN_RECOMMENDABLE_SCORE:g} recommendation floor",
            RULE_FLOOR,
        ))
    rederived, stricter = _rederived_row_problems(candidate, role, engagement)
    rows_only = [pair for pair in rederived if not pair[0].startswith("constraint evidence re-derives")]
    problems.extend(rows_only)
    if stricter and not problems:
        problems.extend(pair for pair in rederived if pair not in rows_only)
    return _unique_pairs(problems)


def _composed_is_suspect(parts, composed):
    texts = [text for text in parts if isinstance(text, str) and text.strip()]
    return is_suspect(composed) or bool(record_hits(texts))


def _withhold(candidate, role, role_index, index, problems, escalations, log):
    eligibility = candidate["eligibility"]
    texts = [text for text, _ in problems]
    name = candidate.get("candidate_name")
    composed = f"{role['role_id']}: secondary validation withheld {name} - " + "; ".join(texts)
    text_hold = any(rule == HOLD_RULE for _, rule in problems)
    if _composed_is_suspect([role["role_id"], name, *texts], composed):
        # D22: the values only trip when rendered together; withhold every contributing value.
        where = f"governed_input.governed_roles[{role_index}].candidate_slate[{index}]"
        candidate["candidate_name"] = sanitize_free_text(
            str(name), f"{where}.candidate_name", log, "candidate_name", force_redact=True
        )
        for row_index, row in enumerate(candidate.get("constraints_considered", [])):
            for key in ("reason", "type"):
                if isinstance(row.get(key), str) and _word(row[key]) in {_word(text) for text in texts}:
                    row[key] = sanitize_free_text(
                        row[key], f"{where}.constraints_considered[{row_index}].{key}", log,
                        key, force_redact=True,
                    )
        texts = [COMPOSED_HOLD_PROBLEM]
        problems = [(COMPOSED_HOLD_PROBLEM, HOLD_RULE)]
        text_hold = True
        composed = (
            f"governed_roles[{role_index}].candidate_slate[{index}]: secondary validation withheld - "
            f"{COMPOSED_HOLD_PROBLEM} ({HOLD_RULE})"
        )
    rules = merge_unique([rule for _, rule in problems], [RULE_VERDICT])
    candidate.pop("final_eligible_rank", None)
    if eligibility.get("verdict") != "ineligible":
        eligibility["verdict"] = "needs_review"
    eligibility["recommendation_status"] = "not_recommended"
    eligibility["blocking_rule"] = HOLD_RULE if text_hold else problems[0][1]
    eligibility["reasons"] = merge_unique(
        eligibility.get("reasons", []),
        ["secondary validation found inconsistent or unsafe recommendation evidence"],
        texts,
    )
    eligibility["citation"] = "; ".join(
        part for part in [str(eligibility.get("citation", "")).strip().rstrip(";").strip(), *rules] if part
    )
    candidate["secondary_validation"] = {
        "status": "withheld",
        "unresolved_constraints": texts,
        "source": ENGINE,
        "citation": "; ".join(rules),
    }
    escalations.append(composed)
    if candidate.get("provisional_rank") == 1:
        role["top_provisional_candidate_withheld"] = True


def _gap_statement(role):
    statement = (
        f"No candidate is safe to recommend at or above the {MIN_RECOMMENDABLE_SCORE} fit-score floor "
        f"for {role.get('role_title')}; do not pad the slate."
    )
    if _composed_is_suspect([role.get("role_title"), statement], statement):
        statement = (
            f"No candidate is safe to recommend at or above the {MIN_RECOMMENDABLE_SCORE} fit-score "
            f"floor for role {role.get('role_id')}; do not pad the slate."
        )
    return statement


def _hit_scopes(document, log):
    scopes = set()
    for path, _ in log.hits:
        tokens = _parse_path(path.split(".", 1)[1]) if "." in path else []
        _, context = _resolve(document, tokens or [])
        if context != (None, None):
            scopes.add(context if tokens and tokens[0] == "governed_roles" or context[1] is None
                       else (None, context[1]))
    return scopes


# --- A10: a recommendation never coexists with an open escalation that names the candidate ---

def _is_screening_escalation(escalation):
    return any(escalation.endswith(suffix) for suffix, _ in _ESCALATION_KINDS)


def _names_candidate(escalation, candidate):
    """A10: the escalation names this candidate by ID in canonical form (rule 9.5; whitespace or any
    dash between the ID's parts) or by its whole display name."""
    if mentions_id(escalation, candidate["candidate_id"]):
        return True
    text = canonical(escalation)
    name = candidate["candidate_name"]
    if not isinstance(name, str) or has_marker(name):
        return False
    folded = canonical(name)
    return bool(folded) and re.search(rf"(?<!\w){re.escape(folded)}(?!\w)", text) is not None


def _named_by_escalation(escalations, role, role_keys, candidate):
    """True when an open escalation outside screening paths names this candidate. An escalation
    scoped to another role (``<role_id>: ...``) does not apply to this role's slate."""
    own = id_key(role["role_id"])
    for escalation in escalations:
        if not isinstance(escalation, str) or _is_screening_escalation(escalation):
            continue
        scope = _ROLE_SCOPE.match(escalation)
        scope_key = id_key(scope.group(1)) if scope else None
        if scope_key in role_keys and scope_key != own:
            continue
        if _names_candidate(escalation, candidate):
            return True
    return False


def _governed_foreign(document, engagement):
    """Other-client names a hand-built governed document still carries in its not_applicable rows."""
    names = set()
    for role in document["governed_roles"]:
        for slate in ("candidate_slate", "recommended_candidates"):
            for candidate in role[slate]:
                for item in candidate["constraints_considered"]:
                    name = item.get("client_name")
                    if (item.get("applies_to_engagement") is False and isinstance(name, str)
                            and name != constraint_check.FOREIGN_LABEL
                            and matches_engagement(item, engagement) is False):
                        names.update(constraint_check.entity_keys(name))
    return names


def _withhold_foreign_escalations(escalations, foreign, unverified=()):
    out = []
    for text in escalations:
        if constraint_check._names_foreign(text, foreign):
            text = f"escalation withheld: names another client ({FOREIGN_RULE})"
        elif constraint_check._names_foreign(text, unverified):
            text = f"escalation withheld: names an entity that cannot be matched reliably ({UNVERIFIED_RULE})"
        if text not in out:
            out.append(text)
    return out


def _withhold_names(payload, names, reason, rule, escalations):
    """Rule 9.11 (other clients' names) or rule 9.9 (identities held as unverified, ``names`` built
    by unverified_names()): screens the candidate's own values, in its slate rows and in every
    carried bench, scored and ranked record. A slate row's register entries are read with its values
    as one collection, by their register input text only (engine vocabulary and engine text never
    count). Every contributing value is withheld; returns the (role, slate position) pairs held."""
    held = set()
    skip = constraint_check.FOREIGN_SKIP | {"constraints_considered"}
    flagged = constraint_check.foreign_candidates(constraint_check.candidate_records(payload), names)
    slate_rows = [candidate for role in payload["governed_roles"] for candidate in role["candidate_slate"]]
    for key, values in constraint_check.foreign_candidates(
            slate_rows, names, skip,
            extra_contributors=lambda record: constraint_check.considered_texts(
                record.get("constraints_considered"), names)).items():
        flagged.setdefault(key, set()).update(values)
    for role_index, role in enumerate(payload["governed_roles"]):
        for index, candidate in enumerate(role["candidate_slate"]):
            values = flagged.get(id_key(candidate["candidate_id"]), ())
            scrubbed, hits = constraint_check.withhold_foreign(candidate, names, skip, values)
            scrubbed["constraints_considered"], considered_hits = constraint_check.withhold_considered(
                scrubbed["constraints_considered"], names, values, held=bool(hits or values))
            hits += considered_hits
            if hits or values:
                candidate.clear()
                candidate.update(scrubbed)
                held.add((role_index, index))
                escalations.append(
                    f"governed_roles[{role_index}].candidate_slate[{index}]: {reason}; "
                    f"independence review required ({rule})"
                )
    constraint_check.withhold_foreign_sections(payload, names, flagged)
    return held


def validate(governed_payload, intake_engagements=(), foreign_names=(), withheld_names=()):
    """Secondary safety check of a governed document; returns the validated document. No file I/O.

    The input is never mutated. ``intake_engagements`` is an optional sequence of
    (label, engagement object) pairs from the raw inputs; any identity mismatch is refused (C5).
    ``foreign_names`` are canonical other-client names harvested from constraints.json; any carried
    candidate value naming one is withheld and the candidate is held for review (rule 9.11).
    ``withheld_names`` are the identities of register rows held under rule 9.9 (an entity that only
    partly matches the client); a carried register source or citation naming one is withheld and the
    candidate is held for review.
    """
    try:
        engagement, roles = _check_structure(governed_payload)
        _check_identity(governed_payload, engagement, intake_engagements)
        _check_derived(governed_payload, roles)
        held, index = _check_markers(governed_payload)
        for position, role in enumerate(governed_payload["governed_roles"]):
            for slate in ("candidate_slate", "recommended_candidates"):
                for number, candidate in enumerate(role[slate]):
                    _check_holds(candidate, f"governed_roles[{position}].{slate}[{number}]", index,
                                 (id_key(role["role_id"]), id_key(candidate["candidate_id"])), held)
    except InputError as error:
        raise InputError(f"governed.json: {error}") from None

    log = ScreeningLog()
    payload = sanitize_free_text(governed_payload, "governed_input", log, engine_markers_ok=True)
    hit_scopes = _hit_scopes(governed_payload, log)
    held |= hit_scopes
    escalations = merge_unique(payload["escalations"], log)
    # One classification per identity, as constraint-check makes it: the client's own name (either
    # reading) is never screened, and a form held under rule 9.9 is not also another client's.
    unverified = constraint_check.unverified_names(withheld_names, governed_payload["engagement"])
    foreign = constraint_check.ForeignNames(
        (set(foreign_names) | _governed_foreign(governed_payload, governed_payload["engagement"])) - set(unverified),
        allowed=constraint_check.engagement_keys(governed_payload["engagement"]))
    foreign_held = _withhold_names(payload, foreign, FOREIGN_REASON, FOREIGN_RULE, escalations)
    unverified_held = _withhold_names(payload, unverified, UNVERIFIED_REASON, UNVERIFIED_RULE, escalations)
    escalations = _withhold_foreign_escalations(escalations, foreign, unverified)
    open_escalations = list(governed_payload["escalations"])
    role_keys = {id_key(role["role_id"]) for role in governed_payload["governed_roles"]}
    gaps = list(payload["gaps"])
    existing_gap_roles = {id_key(gap.get("role_id")) for gap in gaps}

    for role_index, role in enumerate(payload["governed_roles"]):
        original = governed_payload["governed_roles"][role_index]
        role_key = id_key(original["role_id"])
        role_record = roles[role_key]
        recommended = []
        for index, candidate in enumerate(role["candidate_slate"]):
            if candidate["eligibility"]["recommendation_status"] != "recommended":
                continue
            candidate_key = id_key(original["candidate_slate"][index]["candidate_id"])
            problems = _recommendation_problems(candidate, role_record, payload["engagement"])
            if _held(held, role_key, candidate_key):
                problems.append(
                    (TEXT_HOLD_PROBLEM, HOLD_RULE) if _held(hit_scopes, role_key, candidate_key)
                    else (MARKER_HOLD_PROBLEM, HOLD_RULE)
                )
                new_holds = log.holds_under(f"governed_input.governed_roles[{role_index}].candidate_slate[{index}]")
                if new_holds:
                    candidate["screening_holds"] = merge_unique(candidate.get("screening_holds", []), new_holds)
            if _named_by_escalation(open_escalations, original, role_keys, original["candidate_slate"][index]):
                problems.append((ESCALATION_HOLD_PROBLEM, RULE_VERDICT))
            if (role_index, index) in foreign_held:
                problems.append((FOREIGN_REASON, FOREIGN_RULE))
            if (role_index, index) in unverified_held:
                problems.append((UNVERIFIED_REASON, UNVERIFIED_RULE))
            problems = _unique_pairs(problems)
            if problems:
                _withhold(candidate, role, role_index, index, problems, escalations, log)
            else:
                candidate["secondary_validation"] = {
                    "status": "passed",
                    "source": ENGINE,
                    "citation": "independence-eligibility-rules.md #1.2,#9.1",
                }
                recommended.append(candidate)

        for rank, candidate in enumerate(recommended, start=1):
            candidate["final_eligible_rank"] = rank
        role["recommended_candidates"] = recommended

        if not recommended and role_key not in existing_gap_roles:
            gaps.append({
                "role_id": role.get("role_id"),
                "role_title": role.get("role_title"),
                "gap_statement": _gap_statement(role),
                "source": ENGINE,
                "confidence": 0.99,
                "citation": (
                    "fit-scoring-rubric.md #7.2; "
                    "independence-eligibility-rules.md #1.2,#7.2,#9.1"
                ),
            })
            existing_gap_roles.add(role_key)

    payload["gaps"] = gaps
    payload["escalations"] = _withhold_foreign_escalations(merge_unique(escalations, log), foreign)
    provenance = payload["provenance"]
    engines = [
        engine for engine in provenance.get("engines", [])
        if not engine.startswith("slate_validate/")
    ]
    provenance["engines"] = merge_unique(engines, [ENGINE_VERSION])
    return payload


# --- A23: the final rendering step; the slate draft is rendered from validated.json, never by hand ---

def _check_validated(document):
    need(isinstance(document, dict) and document.get("contract_version") == CONTRACT,
         "wrong validated contract (contract_version)")
    text_list(document, "escalations", "")
    for position, role in enumerate(field(document, "governed_roles", "list", "")):
        where = f"governed_roles[{position}]"
        need(isinstance(role, dict), f"{where} must be an object")
        check_id(field(role, "role_id", "str", where), f"{where}.role_id")
        field(role, "role_title", "str", where)
        for slate in ("candidate_slate", "recommended_candidates"):
            for index, candidate in enumerate(field(role, slate, "list", where)):
                path = f"{where}.{slate}[{index}]"
                need(isinstance(candidate, dict), f"{path} must be an object")
                check_id(field(candidate, "candidate_id", "str", path), f"{path}.candidate_id")
                field(candidate, "candidate_name", "str", path)
                field(candidate, "fit_score", "num", path)
                field(candidate, "provisional_rank", "int", path, required=False)
                field(candidate, "final_eligible_rank", "int", path, required=False)
                for key in ("component_scores", "component_citations", "availability_context",
                            "secondary_validation"):
                    field(candidate, key, "obj", path, required=False)
                eligibility = field(candidate, "eligibility", "obj", path)
                need(field(eligibility, "verdict", "str", f"{path}.eligibility") in VERDICTS,
                     f"{path}.eligibility.verdict must be eligible, needs_review or ineligible")
                need(field(eligibility, "recommendation_status", "str", f"{path}.eligibility")
                     in RECOMMENDATION_STATUSES,
                     f"{path}.eligibility.recommendation_status must be recommended, not_recommended "
                     "or below_score_floor")
                field(eligibility, "blocking_rule", "str", f"{path}.eligibility", required=False)
                field(eligibility, "citation", "str", f"{path}.eligibility", required=False)
        for index, candidate in enumerate(role["recommended_candidates"]):
            need(candidate["eligibility"]["recommendation_status"] == "recommended"
                 and candidate["eligibility"]["verdict"] == "eligible",
                 f"{where}.recommended_candidates[{index}] is not an eligible recommendation (rule 9.8)")
    for position, gap in enumerate(field(document, "gaps", "list", "")):
        where = f"gaps[{position}]"
        need(isinstance(gap, dict), f"{where} must be an object")
        check_id(field(gap, "role_id", "str", where), f"{where}.role_id")
        field(gap, "gap_statement", "str", where)


def _cell(text):
    text = " ".join(str(text).split())
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _shown(text):
    """A display value; a placeholder, reserved label or instruction-like text is never repeated."""
    if (not isinstance(text, str) or not text.strip() or has_marker(text) or is_reserved_label(text)
            or is_suspect(text)):
        return WITHHELD_CELL
    return _cell(text)


def _number(value):
    return json.dumps(value) if is_num(value) else MISSING_CELL


def _rule_sections(*texts):
    sections = []
    for text in texts:
        if not isinstance(text, str):
            continue
        for part in text.split(";"):
            part = part.strip()
            if _RULE_SECTION.fullmatch(part) and part not in sections:
                sections.append(part)
    return sections


def _candidate_cell(candidate):
    return f"{_cell(candidate['candidate_id'])} {_shown(candidate['candidate_name'])}"


def _rate_cell(candidate):
    score = (candidate.get("component_scores") or {}).get("rate_band")
    if not is_num(score):
        return MISSING_CELL
    rules = _rule_sections((candidate.get("component_citations") or {}).get("rate_band"))
    return f"rate-band component {_number(score)}" + (f" ({'; '.join(rules)})" if rules else "")


def _conflict_category(candidate):
    """Types of the applicable constraint records that are not safe; never a client name or reason."""
    categories = []
    for record in candidate.get("constraints_considered") or []:
        if (not isinstance(record, dict) or record.get("applies_to_engagement") is False
                or record.get("disposition") in SAFE_DISPOSITIONS):
            continue
        kind = record.get("type")
        category = kind if isinstance(kind, str) and kind in CATEGORY_TYPES else "unrecognised"
        if category not in categories:
            categories.append(category)
    return "; ".join(categories) or "none"


def _escalation_line(text):
    """An escalation as stored in validated.json; withheld unless it is clean or carries only engine markers."""
    if not isinstance(text, str) or not text.strip() or not is_engine_marker(text) or is_suspect(text):
        return WITHHELD_CELL
    rest = re.sub(ENGINE_MARKER, "", text).strip()
    if rest and is_reserved_label(rest):
        return WITHHELD_CELL
    return " ".join(text.split())


_TOP_ESCALATION = re.compile(r"(?P<role>[^\s:]+): (?P<action>refused|withheld) top provisional candidate\b")
_SECONDARY_ESCALATION = re.compile(r"(?P<role>[^\s:]+): secondary validation withheld\b")
_INDUSTRY_ESCALATION = re.compile(
    r"(?P<role>[^\s:]+): (?:partial industry match\b|no full industry match\b|industry_context\b)"
)
# Fail-closed backstop for escalation prose that the structured data cannot place: financial-interest
# specifics and leave reasons (slate-draft Grounding) are never repeated in the draft.
_SENSITIVE_DETAIL = re.compile(
    r"\bfinancial[\s_-]*interests?\b|\bequity\b|\bshare(?:s|holding|holdings|holder|holders)\b|\bstock(?:s|holding)?\b"
    r"|\bdividends?\b|\bdivest\w*|\bmaternity\b|\bpaternity\b|\b(?:medical|parental|sick|bereavement|compassionate|"
    r"family|personal|disability|adoption|caregiver|carer'?s?|garden|unpaid|special|study)\s+leave\b",
    re.I,
)
# The shared words fit_score quotes in its own industry note come from free text, so numbers and
# leave words there are withheld too (matrix 2026-10-24-1127 blocker 3, N11). fit_score sorts the
# words, so any "leave" counts, not only "<reason> leave".
_SHARED_WORDS = re.compile(r" shares '([^']*)'")
_UNSAFE_SHARED_WORD = re.compile(r"\d|\bmaternit\w*|\bpaternit\w*|\bleaves?\b", re.I)


def _client_names(validated_payload):
    """Entity keys of the client, its declared affiliates and every client named by a constraint record."""
    engagement = validated_payload.get("engagement") or {}
    names = [engagement.get("client_name")]
    names += engagement.get("affiliates") if isinstance(engagement.get("affiliates"), list) else []
    for role in validated_payload["governed_roles"]:
        for slate in ("candidate_slate", "recommended_candidates"):
            for candidate in role.get(slate) or []:
                for record in candidate.get("constraints_considered") or []:
                    if isinstance(record, dict):
                        names.append(record.get("client_name"))
    keys = set()
    for name in names:
        if isinstance(name, str) and name.strip() and not has_marker(name) and name != constraint_check.FOREIGN_LABEL:
            keys.update(constraint_check.entity_keys(name))
    return keys


def _engine_industry_notes(validated_payload):
    """The rubric #1.6 industry notes fit_score emits for this payload, re-derived from the roles
    and bench candidates carried in validated.json; empty when they cannot be re-derived."""
    roles, candidates = validated_payload.get("roles"), validated_payload.get("bench_candidates")
    if not isinstance(roles, list) or not isinstance(candidates, list):
        return set()
    try:
        notes = {fit_score.industry_escalation(role, candidates) for role in roles}
    except (AttributeError, KeyError, TypeError, ValueError):
        return set()
    return {note for note in notes if isinstance(note, str) and _INDUSTRY_ESCALATION.match(note)}


def _conflict_escalation_lines(validated_payload):
    """The visible escalation lines. An escalation that carries conflict, financial-interest or leave
    detail shows only the role, action, candidate, conflict category and rule sections, rebuilt from
    the validated slate; one the slate cannot place is shown with category ``unrecognised`` and no
    detail (fail closed). An industry note is shown as stored only when it equals fit_score's
    re-derived note, names no client or affiliate and shares no number or leave word; any other
    industry note is withheld. Every other escalation is shown as stored (``_escalation_line``)."""
    roles = {id_key(role["role_id"]): role for role in validated_payload["governed_roles"]}
    clients = _client_names(validated_payload)

    def sensitive(text):
        return bool(_SENSITIVE_DETAIL.search(text)) or constraint_check._names_foreign(text, clients)

    def detail_free(candidate):
        return all(category in AVAILABILITY_TYPES or category == "none"
                   for category in _conflict_category(candidate).split("; "))

    def rules_tail(rules):
        rules = list(dict.fromkeys(rules))
        return f" ({'; '.join(rules)})" if rules else ""

    def withheld(text, prefix):
        return f"{prefix}escalation detail withheld - conflict category unrecognised" + rules_tail(
            _RULE_SECTION.findall(text))

    engine_notes = _engine_industry_notes(validated_payload)
    lines = []
    for text in validated_payload["escalations"]:
        shown = _escalation_line(text)
        if shown == WITHHELD_CELL:
            lines.append(shown)
            continue
        industry = _INDUSTRY_ESCALATION.match(shown)
        if industry:
            # Only fit_score's own re-derived note holds nothing but role and candidate IDs and industry
            # words, so only it skips the financial-interest screen (1.1.12 N9). A look-alike is withheld
            # (N10), and so is an engine note sharing a number or leave word (N11).
            if (text in engine_notes and not constraint_check._names_foreign(shown, clients)
                    and not any(_UNSAFE_SHARED_WORD.search(words) for words in _SHARED_WORDS.findall(shown))):
                lines.append(shown)
            else:
                role_id = industry.group("role")
                lines.append(withheld(shown, f"{_cell(role_id)}: " if id_key(role_id) in roles else ""))
            continue
        top, secondary = _TOP_ESCALATION.match(shown), _SECONDARY_ESCALATION.match(shown)
        match = top or secondary
        role = roles.get(id_key(match.group("role"))) if match else None
        if role is None:
            scope = _ROLE_SCOPE.match(shown)
            known = scope and (id_key(scope.group(1)) in roles or any(
                id_key(scope.group(1)) == id_key(candidate["candidate_id"])
                for item in roles.values() for candidate in item["candidate_slate"]))
            lines.append(withheld(shown, f"{_cell(scope.group(1))}: " if known else "") if sensitive(shown)
                         else shown)
            continue
        role_id = _cell(role["role_id"])
        if top:
            action = top.group("action")
            head = f"{role_id}: {action} top provisional candidate"
            slate = [candidate for candidate in role["candidate_slate"] if candidate.get("provisional_rank") == 1]
        else:
            head = f"{role_id}: secondary validation withheld"
            slate = [candidate for candidate in role["candidate_slate"]
                     if (candidate.get("secondary_validation") or {}).get("status") == "withheld"
                     and isinstance(candidate.get("candidate_name"), str)
                     and not has_marker(candidate["candidate_name"])
                     and _names_candidate(shown, candidate)]
        if len(slate) != 1:
            lines.append(f"{head} - conflict category unrecognised" + rules_tail(_RULE_SECTION.findall(shown)))
            continue
        candidate = slate[0]
        if detail_free(candidate) and not sensitive(shown):
            lines.append(shown)
            continue
        if top:
            rules = _rule_sections(candidate["eligibility"].get("blocking_rule"),
                                   f"{RULES} #7.1" if action == "refused" else RULE_VERDICT)
        else:
            rules = _rule_sections((candidate.get("secondary_validation") or {}).get("citation"))
        lines.append(f"{head} {_candidate_cell(candidate)} - conflict category "
                     f"{_conflict_category(candidate)}" + rules_tail(rules))
    return lines


def render_draft(validated_payload):
    """Render the slate-draft skeleton (SKILL.md ``## Output format``) from a validated document.

    Pure: returns LF text. Only the engagement ID, engine figures, verdicts, conflict categories,
    record IDs, rule sections, the engine's gap statements and the escalations in validated.json
    (flagged text already replaced by its engine marker; conflict, financial-interest and leave
    detail replaced by the conflict category) are rendered, never a client name, free-text
    citation, reason or placeholder. The rendered lines are screened on their own and as
    adjacent runs (D22); a hit refuses the draft.
    """
    try:
        _check_validated(validated_payload)
    except InputError as error:
        raise InputError(f"validated.json: {error}") from None
    roles = validated_payload["governed_roles"]
    engagement_id = _cell(validated_payload["engagement"]["engagement_id"])
    lines = list(DRAFT_BANNER) + [f"# Staffing slate draft - {engagement_id}", "", "## Refusals"]

    refusals = []
    for role in roles:
        heading = f"{_cell(role['role_id'])} {_shown(role['role_title'])}"
        for candidate in role["candidate_slate"]:
            if candidate.get("provisional_rank") != 1:
                continue
            eligibility = candidate["eligibility"]
            rule = "; ".join(_rule_sections(eligibility.get("blocking_rule"))) or MISSING_CELL
            if eligibility["verdict"] == "ineligible":
                refusals.append(f"- {heading}: top provisional candidate {_candidate_cell(candidate)} "
                                f"refused - ineligible ({rule}; {RULES} #7.1)")
            elif eligibility["verdict"] == "needs_review":
                refusals.append(f"- {heading}: top provisional candidate {_candidate_cell(candidate)} "
                                f"withheld - needs_review ({rule}; {RULE_VERDICT})")
    lines += refusals or ["No refusals."]

    lines += ["", "## Recommended slate"]
    for role in roles:
        lines += ["", f"### {_cell(role['role_id'])} {_shown(role['role_title'])}"]
        if not role["recommended_candidates"]:
            lines.append("No candidate recommended for this role; see Gap statements.")
            continue
        lines += [
            "| Rank | Candidate | Fit score | Availability % | Utilisation after staffing % "
            "| Rate-band context | Citations |",
            "|---|---|---|---|---|---|---|",
        ]
        for candidate in role["recommended_candidates"]:
            context = candidate.get("availability_context") or {}
            citations = [_cell(role["role_id"]), _cell(candidate["candidate_id"])] + _rule_sections(
                candidate["eligibility"].get("citation"),
                (candidate.get("secondary_validation") or {}).get("citation"),
            )
            lines.append(
                f"| {_number(candidate.get('final_eligible_rank'))} | {_candidate_cell(candidate)} "
                f"| {_number(candidate['fit_score'])} | {_number(context.get('effective_available_pct'))} "
                f"| {_number(context.get('utilization_after_staffing_pct'))} | {_rate_cell(candidate)} "
                f"| {'; '.join(citations)} |"
            )

    lines += ["", "## Not recommended"]
    rows = []
    for role in roles:
        for candidate in role["candidate_slate"]:
            eligibility = candidate["eligibility"]
            status = eligibility["recommendation_status"]
            if status == "recommended":
                continue
            below = status == "below_score_floor"
            blocking = _rule_sections(eligibility.get("blocking_rule")) or ([RULE_FLOOR] if below else [])
            citation = _rule_sections(
                eligibility.get("citation"),
                (candidate.get("secondary_validation") or {}).get("citation"),
                RULE_FLOOR if below else None,
            )
            verdict = "below_score_floor" if below else _cell(eligibility["verdict"])
            rows.append(
                f"| {_cell(role['role_id'])} | {_candidate_cell(candidate)} | {verdict} "
                f"| {_conflict_category(candidate)} "
                f"| {'; '.join(blocking) or MISSING_CELL} | {'; '.join(citation) or MISSING_CELL} |"
            )
    if rows:
        lines += ["| Role | Candidate | Verdict | Conflict category | Blocking rule | Citation |",
                  "|---|---|---|---|---|---|"] + rows
    else:
        lines.append("No candidate is listed as not recommended.")

    lines += ["", "## Gap statements"]
    gaps = validated_payload["gaps"]
    if gaps:
        lines += [f"- {_cell(gap['role_id'])}: {_shown(gap['gap_statement'])}" for gap in gaps]
    else:
        lines.append("No staffing gaps identified.")

    lines += [
        "",
        "## Next steps",
        "- Partner approval and independence/resource-management review are required before any assignment.",
        "- A needs_review or ineligible verdict changes only through a corrected source record and an "
        "engine re-run.",
    ]
    if gaps:
        lines.append("- Route each gap to recruiting, subcontractor search, start-date negotiation or "
                     "scope adjustment; do not pad the slate.")
    escalations = validated_payload["escalations"]
    lines.append(f"- Escalations recorded in validated.json: {len(escalations)}.")
    lines += ["", "### Escalations"]
    lines += [f"- {line}" for line in _conflict_escalation_lines(validated_payload)] or ["No escalations recorded."]

    texts = [line for line in lines if line.strip()]
    need(not any(is_suspect(text) for text in texts) and not list_run_indices(texts),
         "slate-draft.md: the rendered draft trips the instruction screen "
         f"({HOLD_RULE}); review the source records")
    return "\n".join(lines) + "\n"


def write_outputs(json_path, payload, draft_path, draft_text):
    """Write validated.json and slate-draft.md atomically together: both files or neither."""
    items = (
        (json_path, json.dumps(payload, indent=2).encode("utf-8")),
        (draft_path, draft_text.encode("utf-8")),
    )
    temps = []
    try:
        for path, data in items:
            folder = os.path.dirname(os.path.abspath(path))
            handle, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=folder)
            temps.append(temp_path)
            with os.fdopen(handle, "wb") as out:
                out.write(data)
        os.replace(temps[0], json_path)
        try:
            os.replace(temps[1], draft_path)
        except OSError:
            os.remove(json_path)
            raise
    except OSError:
        raise InputError("output files could not be written; neither output was kept") from None
    finally:
        for temp_path in temps:
            if os.path.exists(temp_path):
                os.remove(temp_path)


SAFE_GOVERN_ERRORS = {
    "engagement context must be an object",
    "engagement.client_name is required for fail-closed conflict governance",
}


def rederive_governed(roles_payload, bench_payload, constraints_payload):
    """The governed document the plugin's own engines derive from the three raw inputs."""
    try:
        ranked = constraint_check.rederive_ranked(roles_payload, bench_payload)
        return constraint_check.govern(ranked, constraints_payload)
    except SystemExit as error:
        if isinstance(error.code, str) and error.code in SAFE_GOVERN_ERRORS:
            raise InputError(error.code) from None
        if isinstance(error.code, str):
            # Engine exit messages can quote input values; never echo them (D17).
            raise InputError(
                "roles.json, bench.json and constraints.json cannot be governed "
                "(independence-eligibility-rules.md #9.8); re-run constraint-check"
            ) from None
        raise


def _main(argv):
    parser = ArgumentParser(prog="slate_validate.py", description="Deterministic secondary slate validation.")
    parser.add_argument("--roles", required=True)
    parser.add_argument("--bench", required=True)
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--governed", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--draft-out", required=True)
    args = parser.parse_args(argv)
    need(os.path.normcase(os.path.abspath(args.out)) != os.path.normcase(os.path.abspath(args.draft_out)),
         "command line: --out and --draft-out must name different files")

    roles_payload = load_json(args.roles, "roles.json")
    bench_payload = load_json(args.bench, "bench.json")
    constraints_payload = load_json(args.constraints, "constraints.json")
    governed_payload = load_json(args.governed, "governed.json")
    need(isinstance(governed_payload, dict) and governed_payload.get("contract_version") == CONTRACT,
         "governed.json: wrong governed contract (contract_version)")
    need(isinstance(constraints_payload, dict) and constraints_payload.get("contract_version") == CONTRACT,
         "constraints.json: wrong constraints contract (contract_version)")
    expected = rederive_governed(roles_payload, bench_payload, constraints_payload)
    need(same_document(governed_payload, expected),
         "governed.json does not re-derive from roles.json, bench.json and constraints.json "
         "(rule 9.8); re-run constraint-check")
    intake = [
        (label, payload.get("engagement"))
        for label, payload in (
            ("roles.json", roles_payload),
            ("bench.json", bench_payload),
            ("constraints.json", constraints_payload),
        )
        if isinstance(payload, dict)
    ]
    foreign, withheld = constraint_check.screened_identities(constraints_payload, expected["engagement"])
    payload = validate(expected, intake, foreign, withheld)
    draft = render_draft(payload)
    write_outputs(args.out, payload, args.draft_out, draft)
    print(f"slate_validate: {len(payload['governed_roles'])} role(s) -> validated output and slate draft written")
    return 0


def main(argv=None):
    """CLI entry point: one clean ``error:`` line and exit 2 on any input error, no output file."""
    return run(lambda: _main(argv))


if __name__ == "__main__":
    sys.exit(main())
