#!/usr/bin/env python3
"""constraint_check - deterministic staffing eligibility Govern engine.

``govern(ranked_payload, constraints_payload)`` is the pure engine (no file I/O). The CLI never
trusts a supplied ranked.json: it re-derives the ranked document from roles.json and bench.json with
the vendored fit_score and slate_rank engines and refuses any difference
(independence-eligibility-rules.md #9.8) before governing the re-derived document.

``govern`` validates both documents before anything is screened or evaluated: a malformed ranked
document or conflicts register is one clean input error that names a field path, never a value.
The ranked (role-intake) engagement is authoritative; constraints.json may add affiliates but never
move the client. Any screening hit on a candidate's bench, score or conflicts record holds the
candidate for review (#9.6); rules never read a withheld value. Rows for another client are
validated before they are scoped out (#9.9) and are emitted only by position and a fixed label.
"""
import functools
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import fit_score
import slate_rank
import steering_guard
from input_guard import (
    ArgumentParser,
    InputError,
    canonical,
    check_confidence,
    check_date,
    check_id,
    engagement_id_key,
    duplicate_keys,
    has_marker,
    id_key,
    is_num,
    is_reserved_label,
    load_json,
    need,
    run,
    same_document,
    write_json,
)
from safety_text import (
    ENTITY_DESIGNATORS,
    ENTITY_SUFFIXES,
    HOLD_RULE,
    ScreeningLog,
    entity_key,
    entity_keys,
    entity_matchable,
    entity_names_match,
    entity_readings,
    is_suspect,
    safe_citation,
    safe_text,
    same_client,
    sanitize_free_text,
)

ENGINE = "engine:constraint_check"
ENGINE_VERSION = "constraint_check/1.1.14"
CONTRACT = "ps.engagement-staffing-bench-match.v1"
RULES = "independence-eligibility-rules.md"
CONFIDENCE_FLOOR = 0.75       # independence-eligibility-rules.md #8.1
PRIOR_ROLE_COOLING_DAYS = 365 # independence-eligibility-rules.md #2.1
PRIOR_ROLE_REVIEW_DAYS = 730  # independence-eligibility-rules.md #2.2
DIVEST_REVIEW_DAYS = 30       # independence-eligibility-rules.md #3.2
ADVERSE_REVIEW_DAYS = 180     # independence-eligibility-rules.md #4.2
ASSURANCE_LOOKBACK_DAYS = 730 # independence-eligibility-rules.md #5.1
CAPACITY_REVIEW_BAND = 10.0   # independence-eligibility-rules.md #6.2
MIN_RECOMMENDABLE_SCORE = 70.0 # fit-scoring-rubric.md #7.2
ESCALATION_CAP = 25           # escalations kept per rule; the rest are counted in one summary line
KNOWN_TYPES = {
    "clear",
    "financial_interest",
    "prior_client_role",
    "ethical_wall",
    "adverse_matter",
    "prior_assurance_role",
}
RESOLVED_FI_STATUSES = {"divested", "resolved", "cleared"}
RESOLVED_STATUSES = {"closed", "resolved", "cleared", "inactive"}
CLEAR_STATUSES = {"clear", "cleared"}
FI_STATUSES = {"active"} | RESOLVED_FI_STATUSES
WALL_STATUSES = {"active"} | RESOLVED_STATUSES
DATED_STATUSES = {"active", "open", "closed", "resolved", "cleared", "inactive", "ended", "completed"}
ROLE_TYPES = {"employee", "officer", "board_member"}
# Register row members that are text when present (null reads as absent).
ROW_TEXT_FIELDS = (
    "type", "client_name", "status", "role_type", "process", "end_date", "resolved_date", "source", "citation",
)
# Members a rule reads. A screening hit on one of these means the row is not evaluated at all.
DECISION_FIELDS = {
    "candidate_id", "type", "client_name", "status", "material", "role_type", "process", "end_date",
    "resolved_date",
}
# The ranked slate members a governed slate row carries (B1); engine-owned members are never carried.
CARRIED_KEYS = (
    "candidate_id",
    "candidate_name",
    "fit_score",
    "component_scores",
    "component_citations",
    "availability_context",
    "matched_required_skills",
    "matched_preferred_skills",
    "source",
    "confidence",
    "citation",
    "screening_holds",
    "provisional_rank",
    "rank_source",
    "rank_citation",
)
FOREIGN_LABEL = "another client (name withheld)"
FOREIGN_RULE = "independence-eligibility-rules.md #9.11"
FOREIGN_VALUE = f"withheld: names another client ({FOREIGN_RULE})"
# Register text naming an entity a rule 9.9 review hold withholds (one that only partly matches the
# client or a declared affiliate) is replaced with this fixed text wherever it would be carried.
UNVERIFIED_VALUE = f"withheld: names an entity that cannot be matched reliably ({RULES} #9.9)"
FOREIGN_REASON = "candidate record names another client; values withheld"
UNVERIFIED_RULE = f"{RULES} #9.9"
UNVERIFIED_REASON = "candidate or register text names an entity that cannot be matched reliably; values withheld"
# Top-level record members never screened for another client's identity (the record key). Nested
# members are always screened, and ``screening_holds`` is screened by its input-derived path only.
FOREIGN_SKIP = {"candidate_id"}
HOLDS_KEY = "screening_holds"
_ENGINE_HOLD = re.compile(
    r"^(?P<path>[^:]+): (?:instruction-like text|oversize text|already-redacted marker text|"
    r"instruction-like member name) withheld \(independence-eligibility-rules\.md #9\.6\)$"
)
# Bound on the chains of values tried per record and other-client name (rule 9.11).
FOREIGN_CHAIN_BUDGET = 20000
PASSTHROUGH_SECTIONS = ("bench_candidates", "scored_roles", "ranked_roles")
REVIEW_FALLBACK = "conflicts, screening or availability evidence requires independence review"
_ENGINE_MARKER_DIGEST = re.compile(r"\[FLAGGED: [^\]]*sha256=([0-9a-f]{12})\]")
_ROW_HIT = re.compile(r"^constraints_input\.constraints\[(\d+)\](?:\.([^.\[]+))?")


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

def safe_cite(text):
    return safe_citation(text)

def screened(text, fallback):
    """Composed text is screened before it is written (D22); a hit keeps contract vocabulary only."""
    text = str(text)
    return fallback if is_suspect(text) or has_marker(text) else text

def days_between(start, end):
    return (date.fromisoformat(start) - date.fromisoformat(end)).days

def timing_phrase(days, past_tense="ended"):
    if days < 0:
        return f"extends {-days} days beyond role start"
    return f"{past_tense} {days} days before start"

def normalize_candidate_id(value):
    """One canonical candidate key (rule 9.5); blank or non-string IDs are '' and never match."""
    return id_key(value) or ""

def candidate_register_rows(constraints, candidate_id):
    """(register index, row) for every conflicts-register row of one candidate."""
    key = id_key(candidate_id)
    if key is None:
        return []
    rows = constraints.get("constraints") or []
    return [
        (index, item)
        for index, item in enumerate(rows if isinstance(rows, list) else [])
        if isinstance(item, dict) and id_key(item.get("candidate_id")) == key
    ]

def register_index(constraints):
    """id_key(candidate_id) -> [(register index, row)], built in one pass over the register."""
    rows = constraints.get("constraints") or []
    index = {}
    for position, item in enumerate(rows if isinstance(rows, list) else []):
        if isinstance(item, dict):
            key = id_key(item.get("candidate_id"))
            if key is not None:
                index.setdefault(key, []).append((position, item))
    return index

def candidate_constraints(constraints, candidate_id):
    return [item for _index, item in candidate_register_rows(constraints, candidate_id)]

def unknown_constraint_ids(constraints, candidate_ids):
    known = {id_key(candidate_id) for candidate_id in candidate_ids} - {None}
    return [
        item.get("candidate_id", "<blank>")
        for item in constraints.get("constraints", [])
        if id_key(item.get("candidate_id")) not in known
    ]

def unknown_constraint_rows(constraints, candidate_ids):
    """Register positions whose candidate_id is blank or names no ranked candidate (reported by position)."""
    known = {id_key(candidate_id) for candidate_id in candidate_ids} - {None}
    return [
        index
        for index, item in enumerate(constraints.get("constraints") or [])
        if not isinstance(item, dict) or id_key(item.get("candidate_id")) not in known
    ]

def confidence_value(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def materiality_value(item):
    """Only a JSON true or false records materiality (A5a); anything else is not recorded."""
    value = item.get("material")
    return value if isinstance(value, bool) else None

def _text(item, key):
    value = item.get(key)
    return value if isinstance(value, str) else ""

def _valid_date(value):
    if not isinstance(value, str) or len(value) != 10:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True

def normalize_entity_name(name):
    """Entity names compare in one canonical form: NFKC, format characters removed, confusables and
    diacritics folded, case-folded, separators and punctuation as spaces, then only the trailing run
    of corporate designators and a leading "the" dropped, never a designator inside the name or a
    trailing "the", so "Company Partners" stays "company partners" while "Partners Inc." is
    "partners", and "Orchard Ridge Clinics The" keeps its "the"."""
    return entity_key(name)

def _affiliates(engagement):
    affiliates = engagement.get("affiliates", [])
    if isinstance(affiliates, str):
        return [affiliates]
    return affiliates if isinstance(affiliates, list) else []

def applies_to_client(item, engagement):
    """True when the row names the client or a declared affiliate, False when it names another
    entity, None when that cannot be decided reliably. Withheld or blank names are never matched."""
    raw_name = item.get("client_name")
    if not isinstance(raw_name, str) or not raw_name.strip() or is_suspect(raw_name) or has_marker(raw_name):
        return None
    comparisons = [entity_names_match(raw_name, entity) for entity in [engagement.get("client_name"), *_affiliates(engagement)]]
    if any(value is True for value in comparisons):
        return True
    return None if not comparisons or any(value is None for value in comparisons) else False

def ambiguous_row(item, engagement):
    """A readable, unreserved row name that only partly matches the client or a declared affiliate
    (rule 9.9): applies_to_client cannot decide it although the engagement client is matchable."""
    raw_name = item.get("client_name")
    if (not isinstance(raw_name, str) or not raw_name.strip() or is_reserved_label(raw_name)
            or is_suspect(raw_name) or has_marker(raw_name) or shape_problems(item)):
        return False
    if not entity_matchable(engagement.get("client_name")) or not entity_matchable(raw_name):
        return False
    return applies_to_client(item, engagement) is None

def engagement_keys(engagement):
    """Every canonical form of the client's and each declared affiliate's name."""
    if not isinstance(engagement, dict):
        return ()
    return tuple(key for name in [engagement.get("client_name"), *_affiliates(engagement)] for key in entity_keys(name))

def unverified_names(names, engagement):
    """Identities withheld under rule 9.9, screened like other clients' names (rule 9.11) but with
    their own fixed text, and never matched inside the client's or an affiliate's own name (each of
    them is part of, or contains, one of those names)."""
    return ForeignNames(names, allowed=engagement_keys(engagement), value=UNVERIFIED_VALUE)

def ambiguous_names(constraints, engagement):
    """Rule 9.9: the identities of the register rows held because their entity only partly matches
    the client or a declared affiliate, harvested from the raw register. Any carried value naming
    one (alone or read with the candidate's other values) is withheld and holds the candidate."""
    names = set()
    for item in constraints.get("constraints") or []:
        if isinstance(item, dict) and ambiguous_row(item, engagement):
            names.update(entity_keys(item.get("client_name")))
    return unverified_names(names, engagement)

def screened_identities(raw_constraints, engagement):
    """The register identities screened out of every output, classified once with one precedence:
    the client or a declared affiliate (either reading of a name matches) > an entity that cannot be
    matched reliably (rule 9.9) > another client (rule 9.11). Returns (foreign, ambiguous); a form
    held under rule 9.9 is never also screened as another client's, and an occurrence of the client's
    own name (in either reading) is never screened as either."""
    ambiguous = ambiguous_names(raw_constraints, engagement)
    return _foreign_names(raw_constraints, engagement).without(ambiguous), ambiguous


def unverified_text(text, ambiguous):
    """True for register text (not engine text) that names an identity withheld under rule 9.9."""
    return isinstance(text, str) and not _engine_value(text) and _names_foreign(text, ambiguous)

def same_entity(left, right):
    """One engagement client (rule 9.10), decided by the shared identity classifier (same_client():
    any reading of either name is the entity), as every engine reconciles client names."""
    return same_client(left, right)

def engagement_entity_label(item, engagement):
    name = str(item.get("client_name") or "").strip()
    if not name:
        return "client or declared affiliate"
    if entity_names_match(name, engagement.get("client_name")) is True:
        return f"client '{name}'"
    return f"declared affiliate '{name}'"

def engagement_unsafe(engagement):
    """True when the client or an affiliate name was withheld by screening or is unreadable."""
    names = [engagement.get("client_name"), *_affiliates(engagement)]
    return any(
        not isinstance(name, str) or has_marker(name) or is_suspect(name)
        for name in names
        if name not in (None, "")
    )

def merge_engagement(payload, constraints, escalations):
    """The ranked (role-intake) engagement is authoritative (A18/C1). constraints.json only fills
    members the ranked engagement lacks and adds affiliates; a different client or engagement ID
    is refused, never merged."""
    ranked = payload.get("engagement") or {}
    constrained = constraints.get("engagement") or {}
    if not isinstance(ranked, dict) or not isinstance(constrained, dict):
        sys.exit("engagement context must be an object")
    for key, label in (("client_name", "client_name"), ("engagement_id", "engagement_id")):
        mine, theirs = ranked.get(key), constrained.get(key)
        if mine in (None, "") or theirs in (None, ""):
            continue
        same = (
            same_entity(mine, theirs)
            if key == "client_name"
            else engagement_id_key(mine) is not None and engagement_id_key(mine) == engagement_id_key(theirs)
        )
        if not same:
            sys.exit(
                f"constraints.json: engagement.{label} does not match the ranked (role-intake) engagement; "
                "the ranked engagement is authoritative (rule 9.10)"
            )
    merged = dict(ranked)
    for key, value in constrained.items():
        if value in (None, "", []) or key == "affiliates":
            continue
        if merged.get(key) in (None, ""):
            merged[key] = value
    ranked_affiliates = _affiliates(ranked)
    constrained_affiliates = _affiliates(constrained)
    merged["affiliates"] = merge_unique(ranked_affiliates, constrained_affiliates)
    if ranked_affiliates and not constrained_affiliates:
        escalations.append(
            "engagement affiliates restored from ranked role-intake context; "
            "bench-query must propagate the engagement block unchanged"
        )
    if not str(merged.get("client_name") or "").strip():
        sys.exit("engagement.client_name is required for fail-closed conflict governance")
    if not entity_matchable(merged["client_name"]):
        escalations.append(
            "engagement.client_name cannot be normalized to a matchable entity; "
            "all candidates require independence review"
        )
    payload["engagement"] = merged
    constraints["engagement"] = merged
    return merged

def elevate(current, proposed):
    priority = {"eligible": 0, "needs_review": 1, "ineligible": 2}
    return proposed if priority[proposed] > priority[current] else current

def considered_item(item, applies, disposition, reason, default_source="connector:conflicts-register"):
    return {
        "type": _text(item, "type"),
        "client_name": _text(item, "client_name"),
        "status": _text(item, "status"),
        "material": materiality_value(item),
        "role_type": carried_role_type(_text(item, "role_type")),
        "process": _text(item, "process"),
        "end_date": _text(item, "end_date"),
        "resolved_date": _text(item, "resolved_date"),
        "applies_to_engagement": applies,
        "disposition": disposition,
        "reason": reason,
        "source": _text(item, "source") or default_source,
        "confidence": confidence_value(item.get("confidence", 1.0)),
        "citation": safe_cite(_text(item, "citation") or "conflicts record"),
    }

def _row_label(index):
    return f"conflicts register row {index + 1}"

def held_item(item, index, reason, rule, default_source):
    """A register row that is not evaluated: no supplied value is repeated, only position and rule."""
    kind = _text(item, "type").strip().casefold()
    return {
        "type": kind if kind in KNOWN_TYPES else "",
        "client_name": "",
        "status": "",
        "material": None,
        "role_type": "",
        "process": "",
        "end_date": "",
        "resolved_date": "",
        "applies_to_engagement": True,
        "disposition": "needs_review",
        "reason": reason,
        "source": default_source,
        "confidence": confidence_value(item.get("confidence", 1.0)),
        "citation": f"{_row_label(index)} ({RULES} {rule})",
    }

def foreign_item(item, index, disposition, reason, default_source):
    """A row for another client: kept by position and a fixed label only (#9.9)."""
    kind = _text(item, "type").strip().casefold()
    status = _text(item, "status").strip().casefold()
    role_type = normalize_role_type(item.get("role_type")) if isinstance(item.get("role_type"), str) else ""
    # Only fixed vocabulary is kept, so slate_validate can re-check a valid row without its free text.
    return {
        "type": kind if kind in KNOWN_TYPES else "",
        "client_name": FOREIGN_LABEL,
        "status": status if status in CLEAR_STATUSES | FI_STATUSES | WALL_STATUSES | DATED_STATUSES else "",
        "material": materiality_value(item),
        "role_type": role_type if role_type in ROLE_TYPES else "",
        "process": "withheld" if _text(item, "process").strip() else "",
        "end_date": _text(item, "end_date") if _valid_date(item.get("end_date")) else "",
        "resolved_date": _text(item, "resolved_date") if _valid_date(item.get("resolved_date")) else "",
        "applies_to_engagement": disposition != "not_applicable",
        "disposition": disposition,
        "reason": reason,
        "source": default_source,
        "confidence": confidence_value(item.get("confidence", 1.0)),
        "citation": f"{_row_label(index)} for another client; name and citation withheld ({RULES} #9.9)",
    }

def shape_problems(item):
    """Row members of the wrong JSON type (direct callers; govern() refuses these as input errors)."""
    return [key for key in ROW_TEXT_FIELDS if item.get(key) is not None and not isinstance(item.get(key), str)]

def foreign_row_problems(item):
    """A24/#9.9: a row for another client is validated before it is scoped out."""
    kind = _text(item, "type").strip().casefold()
    status = _text(item, "status").strip().casefold()
    if kind not in KNOWN_TYPES:
        return True
    for key in ("end_date", "resolved_date"):
        if item.get(key) not in (None, "") and not _valid_date(item.get(key)):
            return True
    if kind == "clear":
        return status not in CLEAR_STATUSES
    if kind == "financial_interest":
        material = item.get("material")
        if status not in FI_STATUSES or not (material is None or isinstance(material, bool)):
            return True
        return status == "divested" and not _valid_date(item.get("resolved_date"))
    if kind == "ethical_wall":
        return status not in WALL_STATUSES
    if status not in DATED_STATUSES:
        return True
    if kind == "prior_client_role":
        return not _valid_date(item.get("end_date")) or normalize_role_type(item.get("role_type")) not in ROLE_TYPES
    if kind == "prior_assurance_role":
        return not _valid_date(item.get("end_date")) or not _text(item, "process").strip()
    return not _valid_date(item.get("end_date"))

def normalize_role_type(value):
    normalized = re.sub(r"[\s-]+", "_", str(value or "").strip().casefold())
    aliases = {
        "board_member": "board_member",
        "board_director": "board_member",
        "director": "board_member",
    }
    return aliases.get(normalized, normalized)

def carried_role_type(value):
    """The role_type a register entry carries: the canonical type when the value is recognised (an
    alias such as "board director" is never repeated), otherwise the supplied text."""
    text = value if isinstance(value, str) else ""
    canonical_type = normalize_role_type(text)
    return canonical_type if canonical_type in ROLE_TYPES else text

def safe_days_between(start, end):
    try:
        return days_between(start, end)
    except (TypeError, ValueError):
        return None

def _role_start(role, constraints):
    key = id_key(role.get("role_id"))
    for item in constraints.get("roles") or []:
        if isinstance(item, dict) and key is not None and id_key(item.get("role_id")) == key and item.get("start_date"):
            return item.get("start_date")
    return role.get("start_date")


class _Verdict:
    def __init__(self):
        self.verdict = "eligible"
        self.reasons = []
        self.citations = []
        self.considered = []

    def add(self, level, reason, citation, item=None):
        reason = screened(reason, REVIEW_FALLBACK)
        if level != "eligible":
            self.verdict = elevate(self.verdict, level)
        self.reasons.append(reason)
        self.citations.append(citation)
        if item is not None:
            item["reason"] = reason
            self.considered.append(item)


def verdict_for(role, row, constraints, held_rows=None, foreign_hold=False, register_rows=None, ambiguous=None,
                unverified_hold=False):
    """Evaluate one ranked candidate against the register. ``held_rows`` maps a register index to the
    set of member names a screening hit withheld (``None`` member: the row itself). ``foreign_hold``
    marks a candidate record that named another client (rule 9.11). ``register_rows`` are the
    candidate's (index, row) pairs when the caller already has them. ``ambiguous`` are the identities
    withheld under rule 9.9 (ambiguous_names(); computed from ``constraints`` when not given);
    ``unverified_hold`` holds the candidate because a carried value named one of them."""
    held_rows = held_rows or {}
    acc = _Verdict()
    start = _role_start(role, constraints)
    if not start:
        raise ValueError(f"no start_date for role {role.get('role_id', '<unknown>')}")
    engagement = constraints.get("engagement") or {}
    rows = candidate_register_rows(constraints, row.get("candidate_id")) if register_rows is None else register_rows
    default_source = constraints.get("source") if isinstance(constraints.get("source"), str) else ""
    default_source = default_source or "connector:conflicts-register"
    if ambiguous is None:
        ambiguous = ambiguous_names(constraints, engagement)
    # Rule 9.9: register text naming a withheld identity is never carried, held rows included.
    if unverified_text(default_source, ambiguous):
        default_source = UNVERIFIED_VALUE
    default_citation = constraints.get("citation") or "conflicts register"
    default_citation = UNVERIFIED_VALUE if unverified_text(default_citation, ambiguous) else safe_cite(default_citation)

    confidence_values = [
        confidence_value(row.get("confidence", 1.0)),
        confidence_value(constraints.get("confidence", 1.0)),
        confidence_value(engagement.get("confidence", 1.0)),
        *[confidence_value(item.get("confidence", 1.0)) for _index, item in rows],
    ]
    lowest_confidence = min(confidence_values)
    if lowest_confidence < CONFIDENCE_FLOOR:
        acc.add("needs_review", f"evidence confidence {lowest_confidence} below {CONFIDENCE_FLOOR}", f"{RULES} #8.1")

    if not entity_matchable(engagement.get("client_name")):
        acc.add("needs_review", "engagement client name cannot be matched reliably", f"{RULES} #9.2")
    if engagement_unsafe(engagement):
        acc.add("needs_review", "engagement client or affiliate name was withheld by source screening",
                f"{RULES} #9.2,#9.6")

    if not rows:
        reason = "no conflicts-register record for candidate - clearance cannot be inferred"
        acc.add("needs_review", reason, f"{RULES} #9.4", {
            "type": "conflicts_register_coverage",
            "client_name": engagement.get("client_name", ""),
            "status": "",
            "material": None,
            "role_type": "",
            "process": "",
            "end_date": "",
            "resolved_date": "",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": reason,
            "source": default_source,
            "confidence": confidence_value(constraints.get("confidence", 0.0)),
            "citation": default_citation,
        })

    for index, item in rows:
        cite = _text(item, "citation") or "conflicts record"
        cite = UNVERIFIED_VALUE if unverified_text(cite, ambiguous) else safe_cite(cite)
        if index in held_rows:
            fields = held_rows[index]
            reason = "conflicts-register record carries text withheld by source screening"
            acc.add("needs_review", reason, f"{HOLD_RULE}; {_row_label(index)}", {
                "type": "source_screening",
                "applies_to_engagement": True,
                "disposition": "needs_review",
                "reason": reason,
                "citation": f"{_row_label(index)} ({HOLD_RULE})",
            })
            if None in fields or fields & DECISION_FIELDS:
                continue
        if shape_problems(item):
            reason = "conflicts record has a member of the wrong type"
            acc.add("needs_review", reason, f"{RULES} #9.1; {_row_label(index)}",
                    held_item(item, index, reason, "#9.1", default_source))
            continue
        name = _text(item, "client_name")
        if not name.strip():
            reason = "conflicts record does not name the client or affiliate it covers"
            acc.add("needs_review", reason, f"{RULES} #9.1,#9.2; {_row_label(index)}",
                    held_item(item, index, reason, "#9.1,#9.2", default_source))
            continue
        if is_reserved_label(name):
            reason = "conflicts record names an entity with a reserved label form"
            acc.add("needs_review", reason, f"{RULES} #9.7; {_row_label(index)}",
                    held_item(item, index, reason, "#9.7", default_source))
            continue
        applies = applies_to_client(item, engagement)
        if applies is False:
            if foreign_row_problems(item):
                reason = "conflicts-register row for another client is malformed - independence review required"
                acc.add("needs_review", reason, f"{RULES} #9.1,#9.9; {_row_label(index)}",
                        foreign_item(item, index, "needs_review", reason, default_source))
            else:
                acc.considered.append(foreign_item(
                    item, index, "not_applicable",
                    "recorded entity does not match the client or a declared affiliate", default_source,
                ))
            continue
        if applies is None:
            # Rule 9.9: an entity that cannot be matched to the client or a declared affiliate, or
            # that only partly matches one (a whole-word part of it, or it of the entity), is neither
            # the engagement's nor plainly another client's: held by position, nothing repeated.
            reason = "conflict entity cannot be matched reliably to the client or declared affiliates"
            acc.add("needs_review", reason, f"{RULES} #9.2,#9.9; {_row_label(index)}",
                    held_item(item, index, reason, "#9.2,#9.9", default_source))
            continue
        _evaluate_row(acc, role, item, start, engagement, cite, default_source)

    _evaluate_availability(acc, row)

    holds = row.get("screening_holds")
    if isinstance(holds, list) and holds:
        reason = "bench or score record carries text withheld by source screening"
        acc.add("needs_review", reason, HOLD_RULE, {
            "type": "source_screening",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": reason,
            "citation": HOLD_RULE,
        })

    if foreign_hold:
        acc.add("needs_review", FOREIGN_REASON, FOREIGN_RULE, {
            "type": "source_screening",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": FOREIGN_REASON,
            "citation": FOREIGN_RULE,
        })
    if unverified_hold:
        acc.add("needs_review", UNVERIFIED_REASON, UNVERIFIED_RULE, {
            "type": "source_screening",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": UNVERIFIED_REASON,
            "citation": UNVERIFIED_RULE,
        })

    if not acc.reasons:
        acc.reasons.append("no blocking independence, conflict or availability constraint found")
        acc.citations.append(f"{RULES} #1.1")

    return acc.verdict, acc.reasons, acc.citations, acc.considered


def _status_check(acc, item, status, cite, default_source, mark):
    """Dated rows decide on dates, but the status must be present and recognised (A5, rule 9.1): an
    absent, blank or null status is missing, never clearance. Runs after the date rule (whose
    considered items start at ``mark``): a block stands; a settled outcome is replaced by review."""
    if status not in DATED_STATUSES:
        added = acc.considered[mark:]
        if any(entry.get("disposition") == "ineligible" for entry in added):
            return
        acc.considered[mark:] = [entry for entry in added if entry.get("disposition") == "needs_review"]
        reason = "conflicts record status is missing or not recognised"
        acc.add("needs_review", reason, f"{RULES} #9.1; " + cite,
                considered_item(item, True, "needs_review", reason, default_source))


def status_problem(item):
    """True when a register row's status is missing (absent, blank or null) or not recognised for its
    type (rule 9.1). Rows of an unrecognised type are reported by type instead."""
    kind = _text(item, "type").strip().casefold()
    status = _text(item, "status").strip().casefold()
    if kind == "clear":
        return status not in CLEAR_STATUSES
    if kind == "financial_interest":
        return status not in FI_STATUSES
    if kind == "ethical_wall":
        return status not in WALL_STATUSES
    return kind in KNOWN_TYPES and status not in DATED_STATUSES


def _evaluate_row(acc, role, item, start, engagement, cite, default_source):
    kind = _text(item, "type").strip().casefold()
    status = _text(item, "status").strip().casefold()
    materiality = materiality_value(item)

    def review(reason, rules):
        acc.add("needs_review", reason, f"{RULES} {rules}; " + cite,
                considered_item(item, True, "needs_review", reason, default_source))

    def block(reason, rules):
        acc.add("ineligible", reason, f"{RULES} {rules}; " + cite,
                considered_item(item, True, "ineligible", reason, default_source))

    def settle(disposition, reason):
        acc.considered.append(considered_item(item, True, disposition, reason, default_source))

    if kind not in KNOWN_TYPES:
        review("unrecognised conflicts record type - route to independence review", "#1.1,#8.1,#9.1")
    elif kind == "clear":
        if status in CLEAR_STATUSES:
            settle("clear", "conflicts register marks candidate clear")
        else:
            review("clear record status is missing or not recognised", "#9.1")
    elif kind == "financial_interest":
        if status not in RESOLVED_FI_STATUSES and materiality is None:
            review("financial interest materiality not recorded as true or false", "#3.1,#8.1,#9.1")
        elif status not in RESOLVED_FI_STATUSES and materiality:
            block("unresolved material financial interest in " + engagement_entity_label(item, engagement), "#3.1")
        elif status == "divested":
            resolved = item.get("resolved_date")
            if not resolved:
                review("divested financial interest has no resolved_date", "#3.2,#8.1")
            else:
                days = safe_days_between(start, resolved)
                if days is None:
                    review("divested financial interest has an invalid resolved_date", "#3.2,#9.1")
                elif days <= DIVEST_REVIEW_DAYS:
                    review(f"material interest divestment {timing_phrase(days, 'completed')}", "#3.2")
                else:
                    settle("resolved", "divestment completed outside the review window")
        elif status in RESOLVED_FI_STATUSES:
            settle("resolved", "financial interest is resolved or explicitly non-material")
        elif status == "active":
            settle("non_material", "financial interest is resolved or explicitly non-material")
        else:
            review("financial interest status is missing or not recognised", "#9.1,#9.3")
    elif kind == "prior_client_role":
        mark = len(acc.considered)
        role_type = normalize_role_type(item.get("role_type"))
        if not item.get("end_date") or not role_type:
            review("prior client role is missing role_type or end_date", "#2.2,#8.1")
        else:
            days = safe_days_between(start, item["end_date"])
            if days is None:
                review("prior client role has an invalid end_date", "#2.2,#9.1")
            elif role_type in ROLE_TYPES and days <= PRIOR_ROLE_COOLING_DAYS:
                block(f"prior {role_type} role at client {timing_phrase(days)}", "#2.1")
            elif days <= PRIOR_ROLE_REVIEW_DAYS:
                review(f"prior client role {timing_phrase(days)}", "#2.2")
            else:
                settle("resolved", "prior role falls outside the review window")
        _status_check(acc, item, status, cite, default_source, mark)
    elif kind == "ethical_wall":
        if status == "active":
            block("active ethical wall involving client", "#4.1")
        elif status in RESOLVED_STATUSES:
            settle("resolved", "ethical wall is recorded as resolved")
        else:
            review("ethical wall status is missing or not recognised", "#4.1,#8.1,#9.1")
    elif kind == "adverse_matter":
        mark = len(acc.considered)
        if not item.get("end_date"):
            review("adverse matter has no end_date", "#4.2,#8.1")
        else:
            days = safe_days_between(start, item["end_date"])
            if days is None:
                review("adverse matter has an invalid end_date", "#4.2,#9.1")
            elif days < 0:
                block("adverse matter remains active at role start", "#4.1")
            elif days <= ADVERSE_REVIEW_DAYS:
                review(f"adverse matter support {timing_phrase(days)}", "#4.2")
            else:
                settle("resolved", "adverse matter falls outside the review window")
        _status_check(acc, item, status, cite, default_source, mark)
    elif kind == "prior_assurance_role":
        mark = len(acc.considered)
        process = _text(item, "process").strip()
        if not process or not item.get("end_date"):
            review("prior assurance role process or end_date is missing or ambiguous", "#5.2")
        else:
            days = safe_days_between(start, item["end_date"])
            same_process = normalize_entity_name(process) in normalize_entity_name(role.get("title", ""))
            if days is None:
                review("prior assurance role has an invalid end_date", "#5.2,#9.1")
            elif days <= ASSURANCE_LOOKBACK_DAYS and same_process:
                block(f"prior assurance role over same process {timing_phrase(days)}", "#5.1")
            elif days <= ASSURANCE_LOOKBACK_DAYS:
                review(
                    f"prior assurance role over '{process}' {timing_phrase(days)}; "
                    "overlap with role scope not determinable",
                    "#5.2",
                )
            else:
                settle("resolved", "prior assurance role falls outside the lookback window")
        _status_check(acc, item, status, cite, default_source, mark)


def _evaluate_availability(acc, row):
    availability = row.get("availability_context")
    if not isinstance(availability, dict):
        availability = {}
    effective = confidence_value(availability.get("effective_available_pct"), None)
    requested = confidence_value(availability.get("requested_allocation_pct"), None)
    warnings = availability.get("calculation_warnings", [])
    row_cite = safe_cite(row.get("citation") or "fit score record")
    if availability.get("evidence_complete") is not True or warnings:
        reason = "availability evidence is incomplete or uses a conservative assumption"
        acc.add("needs_review", reason, f"{RULES} #6.3,#8.1", {
            "type": "availability_evidence",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": reason,
            "source": row.get("source", "engine:fit_score"),
            "confidence": confidence_value(row.get("confidence", 0.0)),
            "citation": f"{RULES} #6.3,#8.1",
        })
    if effective is None or requested is None:
        reason = "availability calculation is missing effective or requested capacity"
        acc.add("needs_review", reason, f"{RULES} #6.3,#9.1", {
            "type": "availability",
            "applies_to_engagement": True,
            "disposition": "needs_review",
            "reason": reason,
            "citation": row_cite,
        })
    elif effective < requested:
        gap = requested - effective
        if gap > CAPACITY_REVIEW_BAND:
            reason = f"effective available capacity {effective}% is below requested allocation {requested}%"
            acc.add("ineligible", reason, f"{RULES} #6.1; " + row_cite, {
                "type": "availability",
                "applies_to_engagement": True,
                "disposition": "ineligible",
                "reason": reason,
                "citation": row_cite,
            })
        else:
            reason = f"effective capacity {effective}% is within {CAPACITY_REVIEW_BAND} points of requested {requested}%"
            acc.add("needs_review", reason, f"{RULES} #6.2; " + row_cite, {
                "type": "availability",
                "applies_to_engagement": True,
                "disposition": "needs_review",
                "reason": reason,
                "citation": row_cite,
            })
    else:
        acc.considered.append({
            "type": "availability",
            "applies_to_engagement": True,
            "disposition": "clear",
            "reason": "effective available capacity meets requested allocation",
            "citation": row_cite,
        })


def blocking_reason(reasons, citations):
    blocking_rules = ("#2.1", "#3.1", "#4.1", "#5.1", "#6.1")
    for reason, citation in zip(reasons, citations):
        if any(rule in citation.split(";", 1)[0] for rule in blocking_rules):
            return reason, citation.split(";", 1)[0]
    return reasons[0], citations[0].split(";", 1)[0]

def review_reason(reasons, citations):
    review_rules = (
        "#9.6",
        "#9.7",
        "#9.11",
        "#2.2",
        "#3.2",
        "#4.2",
        "#5.2",
        "#6.2",
        "#6.3",
        "#9.1",
        "#9.2",
        "#9.9",
        "#9.4",
        "#8.1",
    )
    for rule in review_rules:
        for reason, citation in zip(reasons, citations):
            if rule in citation.split(";", 1)[0]:
                return reason, citation.split(";", 1)[0]
    return reasons[0], citations[0].split(";", 1)[0]


# ---------------------------------------------------------------------------------------------
# Input validation (A1/A2/A7/A12/A18/A21/C1/C5/D17/D20/D23/D25; rules 9.5, 9.7, 9.8).
# Messages name field paths only; values and file paths are never echoed.
# ---------------------------------------------------------------------------------------------
def _join(where, key):
    return f"{where} {key}" if where.endswith(":") else f"{where}.{key}"

def _obj(value, path):
    need(isinstance(value, dict), f"{path} must be an object")
    return value

def _list(value, path):
    need(value is not None, f"{path} must not be null")
    need(isinstance(value, list), f"{path} must be an array")
    return value

def _member(obj, key, where, required=True):
    if key not in obj:
        need(not required, f"{_join(where, key)} is required")
        return None
    return obj[key]

def _opt_text(obj, key, where):
    value = obj.get(key)
    need(value is None or isinstance(value, str), f"{_join(where, key)} must be a string")
    return value

def _ident(value, path):
    check_id(value, path)
    need(not is_suspect(value), f"{path} carries instruction-like text (rule 9.7)")
    return value

def _label(value, path, markers_ok=False):
    """A name: a non-blank string that is not a reserved label (an engine marker only when allowed)."""
    need(isinstance(value, str) and value.strip(), f"{path} must be a non-blank string")
    need(not is_reserved_label(value) or (markers_ok and has_marker(value)), f"{path} uses a reserved label form")
    return value

def _escalation_items(document, where, objects_ok):
    if "escalations" not in document:
        return
    items = _list(document["escalations"], _join(where, "escalations"))
    for index, item in enumerate(items):
        need(isinstance(item, str) or (objects_ok and isinstance(item, dict)),
             f"{_join(where, 'escalations')}[{index}] must be a string" + (" or an object" if objects_ok else ""))

def validate_ranked(ranked):
    label = "ranked.json"
    need(isinstance(ranked, dict) and ranked.get("contract_version") == CONTRACT,
         f"{label}: wrong ranked contract (contract_version)")
    engagement = _obj(_member(ranked, "engagement", f"{label}:"), f"{label}: engagement")
    _label(_member(engagement, "client_name", f"{label}: engagement"), f"{label}: engagement.client_name", True)
    if engagement.get("engagement_id") is not None:
        _ident(engagement["engagement_id"], f"{label}: engagement.engagement_id")
    if "affiliates" in engagement:
        for index, affiliate in enumerate(_list(engagement["affiliates"], f"{label}: engagement.affiliates")):
            _label(affiliate, f"{label}: engagement.affiliates[{index}]", True)
    if "confidence" in engagement:
        check_confidence(engagement["confidence"], f"{label}: engagement.confidence")
    roles = _list(_member(ranked, "roles", f"{label}:"), f"{label}: roles")
    need(roles, f"{label}: roles must not be empty")
    for index, role in enumerate(roles):
        where = f"{label}: roles[{index}]"
        _obj(role, where)
        _ident(_member(role, "role_id", where), f"{where}.role_id")
        _label(_member(role, "title", where), f"{where}.title", True)
        check_date(_member(role, "start_date", where), f"{where}.start_date")
    need(not duplicate_keys([role["role_id"] for role in roles]),
         f"{label}: roles repeat a role_id after canonical folding (rule 9.7)")
    role_keys = {id_key(role["role_id"]) for role in roles}
    ranked_roles = _list(_member(ranked, "ranked_roles", f"{label}:"), f"{label}: ranked_roles")
    for r_index, ranked_role in enumerate(ranked_roles):
        where = f"{label}: ranked_roles[{r_index}]"
        _obj(ranked_role, where)
        role_id = _ident(_member(ranked_role, "role_id", where), f"{where}.role_id")
        need(id_key(role_id) in role_keys, f"{where}.role_id is missing from roles")
        _label(_member(ranked_role, "role_title", where), f"{where}.role_title", True)
        slate = _list(_member(ranked_role, "candidate_slate", where), f"{where}.candidate_slate")
        for c_index, candidate in enumerate(slate):
            path = f"{where}.candidate_slate[{c_index}]"
            _obj(candidate, path)
            _ident(_member(candidate, "candidate_id", path), f"{path}.candidate_id")
            _label(_member(candidate, "candidate_name", path), f"{path}.candidate_name", True)
            need(is_num(_member(candidate, "fit_score", path)), f"{path}.fit_score must be a number")
            rank = _member(candidate, "provisional_rank", path)
            need(isinstance(rank, int) and not isinstance(rank, bool) and rank >= 1,
                 f"{path}.provisional_rank must be a positive integer")
            check_confidence(_member(candidate, "confidence", path), f"{path}.confidence")
            if "availability_context" in candidate:
                _obj(candidate["availability_context"], f"{path}.availability_context")
            if "screening_holds" in candidate:
                for h_index, hold in enumerate(_list(candidate["screening_holds"], f"{path}.screening_holds")):
                    need(isinstance(hold, str), f"{path}.screening_holds[{h_index}] must be a string")
            for key in ("source", "citation"):
                _opt_text(candidate, key, path)
        need(not duplicate_keys([candidate["candidate_id"] for candidate in slate]),
             f"{where}.candidate_slate repeats a candidate_id after canonical folding (rule 9.7)")
    need(not duplicate_keys([ranked_role["role_id"] for ranked_role in ranked_roles]),
         f"{label}: ranked_roles repeat a role_id after canonical folding (rule 9.7)")
    _escalation_items(ranked, f"{label}:", objects_ok=False)
    if "provenance" in ranked:
        provenance = _obj(ranked["provenance"], f"{label}: provenance")
        if "engines" in provenance:
            for index, engine in enumerate(_list(provenance["engines"], f"{label}: provenance.engines")):
                need(isinstance(engine, str), f"{label}: provenance.engines[{index}] must be a string")

def validate_constraints(constraints, ranked):
    label = "constraints.json"
    need(isinstance(constraints, dict) and constraints.get("contract_version") == CONTRACT,
         f"{label}: wrong constraints contract (contract_version)")
    ranked_engagement = ranked["engagement"]
    if "engagement" in constraints:
        engagement = _obj(constraints["engagement"], f"{label}: engagement")
        client = _opt_text(engagement, "client_name", f"{label}: engagement")
        if client not in (None, ""):
            _label(client, f"{label}: engagement.client_name")
            need(
                same_entity(client, ranked_engagement["client_name"]),
                f"{label}: engagement.client_name does not match the ranked (role-intake) engagement; "
                "the ranked engagement is authoritative (rule 9.10)",
            )
        engagement_id = engagement.get("engagement_id")
        if engagement_id not in (None, ""):
            _ident(engagement_id, f"{label}: engagement.engagement_id")
            need(engagement_id_key(engagement_id) == engagement_id_key(ranked_engagement.get("engagement_id")),
                 f"{label}: engagement.engagement_id does not match the ranked (role-intake) engagement; "
                 "the ranked engagement is authoritative (rule 9.10)")
        if "affiliates" in engagement:
            for index, affiliate in enumerate(_list(engagement["affiliates"], f"{label}: engagement.affiliates")):
                _label(affiliate, f"{label}: engagement.affiliates[{index}]")
        if engagement.get("confidence") is not None:
            check_confidence(engagement["confidence"], f"{label}: engagement.confidence")
        for key in ("source", "citation"):
            _opt_text(engagement, key, f"{label}: engagement")
    ranked_starts = {id_key(role["role_id"]): role["start_date"] for role in ranked["roles"]}
    if "roles" in constraints:
        roles = _list(constraints["roles"], f"{label}: roles")
        for index, role in enumerate(roles):
            where = f"{label}: roles[{index}]"
            _obj(role, where)
            role_id = _ident(_member(role, "role_id", where), f"{where}.role_id")
            if role.get("start_date") is not None:
                check_date(role["start_date"], f"{where}.start_date")
                expected = ranked_starts.get(id_key(role_id))
                need(expected is None or expected == role["start_date"],
                     f"{where}.start_date does not match the ranked role start_date (rule 9.10)")
        need(not duplicate_keys([role["role_id"] for role in roles]),
             f"{label}: roles repeat a role_id after canonical folding (rule 9.7)")
    register = _member(constraints, "constraints", f"{label}:")
    need(register is not None, f"{label}: constraints must not be null (an absent register is never clearance)")
    need(isinstance(register, list), f"{label}: constraints must be an array of register rows")
    for index, item in enumerate(register):
        where = f"{label}: constraints[{index}]"
        _obj(item, where)
        _ident(_member(item, "candidate_id", where), f"{where}.candidate_id")
        for key in ROW_TEXT_FIELDS:
            _opt_text(item, key, where)
        if item.get("confidence") is not None:
            check_confidence(item["confidence"], f"{where}.confidence")
    if constraints.get("confidence") is not None:
        check_confidence(constraints["confidence"], f"{label}: confidence")
    for key in ("source", "citation"):
        _opt_text(constraints, key, f"{label}:")
    _escalation_items(constraints, f"{label}:", objects_ok=True)


# ---------------------------------------------------------------------------------------------
# Escalations (A8, B3, D17, D22)
# ---------------------------------------------------------------------------------------------
_HEAD_KEYS = ("id", "escalation_id", "rule", "code")
_BODY_KEYS = ("message", "reason", "text", "summary", "detail")


def normalise_escalation(item, index):
    """A string, or an object rendered as ``head: body`` from its known members (A8). Unknown
    members are never dumped; an object with no readable message is reported by position."""
    if isinstance(item, str):
        return item.strip(), None
    head = next((item[key].strip() for key in _HEAD_KEYS if isinstance(item.get(key), str) and item[key].strip()), "")
    body = next((item[key].strip() for key in _BODY_KEYS if isinstance(item.get(key), str) and item[key].strip()), "")
    if not body:
        return f"constraints escalations[{index}]: escalation object has no readable message; review source record", head or None
    return (f"{head}: {body}" if head else body), head or None


class _Escalations:
    """Escalations in order, de-duplicated, capped per rule key with one summary line each (A8)."""

    def __init__(self):
        self.items = []

    def add(self, text, rule=None):
        self.items.append((str(text), rule))

    def extend(self, texts):
        for text in texts:
            self.add(text)

    def render(self):
        counts, kept, dropped, seen = {}, [], {}, set()
        for text, rule in self.items:
            if text in seen or not text:
                continue
            seen.add(text)
            if rule is not None:
                counts[rule] = counts.get(rule, 0) + 1
                if counts[rule] > ESCALATION_CAP:
                    dropped[rule] = dropped.get(rule, 0) + 1
                    continue
            kept.append(text)
        for rule, count in dropped.items():
            kept.append(
                f"{count} further escalation(s) under {screened(rule, 'one rule')} not listed (cap {ESCALATION_CAP}); "
                "see each candidate's eligibility record"
            )
        return kept


def _seed_engine_markers(log, value, path):
    """B3: text an upstream engine already redacted (the marker carries its digest) is not escalated
    again when the same text arrives at the same field of constraints.json."""
    if isinstance(value, dict):
        for key, item in value.items():
            _seed_engine_markers(log, item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _seed_engine_markers(log, item, f"{path}[{index}]")
    elif isinstance(value, str):
        for match in _ENGINE_MARKER_DIGEST.finditer(value):
            log.keys.add((path, match.group(1)))


def _held_rows(log):
    """Register index -> member names a screening hit withheld (None: the row or a member name)."""
    held = {}
    for path, _kind in log.hits:
        match = _ROW_HIT.match(path)
        if match:
            held.setdefault(int(match.group(1)), set()).add(match.group(2))
    return held


class ForeignNames(frozenset):
    """Normalised names withheld from every output: other clients' names (rule 9.11) or, with
    ``value=UNVERIFIED_VALUE``, identities held under rule 9.9. Each name is filed under its rarest
    token, so a text is compared only with the names filed under one of its own tokens, and each
    distinct text is screened once per document (the result is cached). ``allowed`` are names an
    occurrence never counts inside (the client's and affiliates' own names); ``value`` is the fixed
    text a withheld value becomes."""

    def __new__(cls, names=(), allowed=(), value=FOREIGN_VALUE):
        self = super().__new__(cls, (name for name in names if isinstance(name, str) and name.split()))
        parts = [tuple(name.split()) for name in self]
        frequency = Counter(token for words in parts for token in set(words))
        self.filed = {}
        for words in parts:
            self.filed.setdefault(min(words, key=lambda token: (frequency[token], token)), []).append(words)
        self.allowed = tuple(dict.fromkeys(
            tuple(name.split()) for name in allowed if isinstance(name, str) and name.split()))
        self.value = value
        self.hits = {}
        return self

    def without(self, names):
        """The same set without ``names`` (same allowed names and fixed text)."""
        return ForeignNames(set(self) - set(names), allowed=[" ".join(name) for name in self.allowed],
                            value=self.value)


def _as_foreign(foreign):
    return foreign if isinstance(foreign, ForeignNames) else ForeignNames(foreign or ())


@functools.lru_cache(maxsize=1 << 16)
def _screen_forms(text, allowed):
    """The readings of ``text`` screened for withheld names, as ``(words, spans, masks)``: see
    entity_readings() (format characters removed, and read as a word boundary, so neither
    "Orchard\u200bClinics" nor "Orch\u200bard Clinics" escapes a name). ``masks`` are the ranges of
    every occurrence of an ``allowed`` name (the client's or a declared affiliate's) in either
    reading: an occurrence classified as the client is the client in both readings, and neither
    reading of it is screened as another entity."""
    readings = entity_readings(text)
    masks = []
    for words, spans in readings:
        for part in allowed:
            size = len(part)
            for start in range(len(words) - size + 1):
                if words[start:start + size] == part:
                    masks.append((spans[start][0], spans[start + size - 1][1]))
    masks = tuple(dict.fromkeys(masks))
    return tuple((words, spans, masks) for words, spans in readings)


def _text_variants(text, allowed=()):
    return _screen_forms(text, tuple(allowed)) if isinstance(text, str) else ()


def _covered(masks, first, end):
    return any(low <= first and end <= high for low, high in masks)


def _occurs(form, name):
    """True when the token tuple ``name`` appears in the reading ``form`` as whole consecutive
    tokens, other than wholly inside an occurrence of the client's own name (in either reading)."""
    words, spans, masks = form
    width = len(name)
    if not width or width > len(words):
        return False
    first = name[0]
    return any(words[index:index + width] == name
               and not (masks and _covered(masks, spans[index][0], spans[index + width - 1][1]))
               for index in range(len(words) - width + 1) if words[index] == first)


def _units(form):
    """The parts of a reading a split name is assembled from: the whole reading, or the runs
    between occurrences of the client's own name (so the client's name, wherever it is carried and
    in either reading, never spells part of another name)."""
    words, spans, masks = form
    if not masks:
        return [words] if words else []
    units, current = [], []
    for word, (first, end) in zip(words, spans):
        if _covered(masks, first, end):
            if current:
                units.append(tuple(current))
            current = []
        else:
            current.append(word)
    if current:
        units.append(tuple(current))
    return units


def _names_in(form, foreign):
    """True when the reading ``form`` holds a whole withheld name (cached per name set)."""
    hit = foreign.hits.get(form)
    if hit is None:
        hit = foreign.hits[form] = any(
            _occurs(form, name) for token in set(form[0]) for name in foreign.filed.get(token, ()))
    return hit


def _foreign_names(raw_constraints, engagement):
    """A16/D12: the other-client names in the raw register, harvested before anything is screened."""
    names = set()
    for item in raw_constraints.get("constraints") or []:
        name = item.get("client_name") if isinstance(item, dict) else None
        if isinstance(name, str) and name.strip() and applies_to_client(item, engagement) is False:
            names.update(entity_keys(name))
    return ForeignNames(names, allowed=engagement_keys(engagement))


def _names_foreign(text, foreign):
    if not foreign or not isinstance(text, str):
        return False
    foreign = _as_foreign(foreign)
    return any(_names_in(form, foreign) for form in _text_variants(text, foreign.allowed))


# Top-level members of a candidate record whose names are engine vocabulary; every other member
# name is screened like a value.
_ENGINE_MEMBERS = set(CARRIED_KEYS) | {"constraints_considered", "eligibility", "final_eligible_rank"}
# The shape the engines give the structured members, as (member name -> type check). Member names
# inside one of these are exempt from screening only when the whole member has exactly this shape:
# the engine's member names, each with exactly the type the engine emits. Anything else, such as a
# raw bench record carrying a member with an engine name, is screened as untrusted passthrough,
# member names included. Values are always screened.
_COMPONENTS = ("skills", "seniority", "availability", "location_language", "rate_band", "continuity")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _string(value):
    return isinstance(value, str)


def _string_or_none(value):
    return value is None or isinstance(value, str)


def _boolean(value):
    return isinstance(value, bool)


def _boolean_or_none(value):
    return value is None or isinstance(value, bool)


def _strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


_ELIGIBILITY_SHAPE = {
    "verdict": _string, "recommendation_status": _string, "blocking_rule": _string_or_none,
    "reasons": _strings, "source": _string, "confidence": _number, "citation": _string,
}
_CONSIDERED_SHAPE = {
    "type": _string, "client_name": _string, "status": _string, "material": _boolean_or_none,
    "role_type": _string, "process": _string, "end_date": _string, "resolved_date": _string,
    "applies_to_engagement": _boolean, "disposition": _string, "reason": _string, "source": _string,
    "confidence": _number, "citation": _string,
}
# Every register-row entry the engine emits carries at least these members.
_CONSIDERED_REQUIRED = {"type", "applies_to_engagement", "disposition", "reason", "citation"}


def _exact(value, shape, required):
    return (isinstance(value, dict) and required <= set(value) <= set(shape)
            and all(shape[key](item) for key, item in value.items()))


def _engine_shaped(key, value):
    """True when the record member ``key`` has exactly the shape its engine gives it (every member
    name known and every value of exactly the type the engine emits for that name)."""
    if key == "component_scores":
        return _exact(value, dict.fromkeys(_COMPONENTS, _number), set(_COMPONENTS))
    if key == "component_citations":
        return _exact(value, dict.fromkeys(_COMPONENTS, _string), set(_COMPONENTS))
    if key == "eligibility":
        return _exact(value, _ELIGIBILITY_SHAPE, set(_ELIGIBILITY_SHAPE))
    if key == "constraints_considered":
        return isinstance(value, list) and all(
            _exact(item, _CONSIDERED_SHAPE, _CONSIDERED_REQUIRED) for item in value)
    return False


def _foreign_hit(text, foreign, contributors):
    if not isinstance(text, str) or _engine_value(text):
        return False
    if _names_foreign(text, foreign):
        return True
    if not contributors:
        return False
    allowed = getattr(foreign, "allowed", ())
    return any(_occurs(form, tuple(part.split()))
               for form in _text_variants(text, allowed) for part in contributors)


def _withhold_value(value, foreign, contributors, screen_keys):
    if isinstance(value, str):
        return (foreign.value, 1) if _foreign_hit(value, foreign, contributors) else (value, 0)
    if isinstance(value, dict):
        out, hits = {}, 0
        for key, item in value.items():
            if screen_keys and _foreign_hit(key, foreign, contributors):
                hits += 1
                key = foreign.value
                number = 2
                while key in out or key in value:
                    key = f"{foreign.value} [{number}]"
                    number += 1
            out[key], count = _withhold_value(item, foreign, contributors, screen_keys)
            hits += count
        return out, hits
    if isinstance(value, list):
        out, hits = [], 0
        for item in value:
            new, count = _withhold_value(item, foreign, contributors, screen_keys)
            out.append(new)
            hits += count
        return out, hits
    return value, 0


def _withhold_holds(value, foreign, contributors):
    """Rule 9.11 for a record's ``screening_holds``: an engine hold line is screened by its path (the
    only part an input can shape); anything else, a raw input value included, is screened whole."""
    foreign = _as_foreign(foreign)
    if isinstance(value, list):
        out, hits = [], 0
        for item in value:
            match = _ENGINE_HOLD.match(item) if isinstance(item, str) else None
            if match and not _foreign_hit(match.group("path"), foreign, contributors):
                out.append(item)
                continue
            if match:
                out.append(foreign.value)
                hits += 1
                continue
            new, count = _withhold_value(item, foreign, contributors, True)
            out.append(new)
            hits += count
        return out, hits
    return _withhold_value(value, foreign, contributors, True)


def withhold_record(record, foreign, skip=FOREIGN_SKIP, contributors=()):
    """Rule 9.11 for one candidate record: top-level members in ``skip`` are kept as they are; every
    other member is screened at every depth (member names included, apart from engine vocabulary),
    and ``screening_holds`` by the input-derived path of each engine hold line."""
    foreign = _as_foreign(foreign)
    out, hits = {}, 0
    for key, item in record.items():
        if key in skip:
            out[key] = item
            continue
        if key not in _ENGINE_MEMBERS and _foreign_hit(key, foreign, contributors):
            hits += 1
            key = foreign.value
            number = 2
            while key in out or key in record:
                key = f"{foreign.value} [{number}]"
                number += 1
        if key == HOLDS_KEY:
            out[key], count = _withhold_holds(item, foreign, contributors)
        else:
            out[key], count = _withhold_value(item, foreign, contributors, not _engine_shaped(key, item))
        hits += count
    return out, hits


def withhold_foreign(value, foreign, skip=frozenset(), contributors=()):
    """A16/D12/D24 (rule 9.11): every string under ``value`` that names another client, or contains
    one of the normalised ``contributors`` (values that name another client only when read together),
    becomes the neutral FOREIGN_VALUE. Returns (new value, number of strings withheld). With ``skip``,
    ``value`` is one candidate record and withhold_record() applies (``skip`` holds top-level members
    only; nested members are always screened). The input is never mutated."""
    foreign = _as_foreign(foreign)
    if isinstance(value, dict) and skip:
        return withhold_record(value, foreign, skip, contributors)
    return _withhold_value(value, foreign, contributors, False)


def _value_texts(value, screen_keys):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            if screen_keys and isinstance(key, str):
                yield key
            yield from _value_texts(item, screen_keys)
    elif isinstance(value, list):
        for item in value:
            yield from _value_texts(item, screen_keys)


def _record_texts(record, skip):
    """Every text of one candidate record that withhold_record() screens, in record order."""
    for key, item in record.items():
        if key in skip:
            continue
        if key not in _ENGINE_MEMBERS and isinstance(key, str):
            yield key
        if key == HOLDS_KEY and isinstance(item, list):
            for hold in item:
                match = _ENGINE_HOLD.match(hold) if isinstance(hold, str) else None
                if match:
                    yield match.group("path")
                else:
                    yield from _value_texts(hold, True)
        else:
            yield from _value_texts(item, not _engine_shaped(key, item))


def _split_name_contributors(texts, name):
    """The texts that spell the withheld ``name`` (a token tuple) only when two or more of them
    are read together in some order: the first ends with the name's opening words, any middle text
    is exactly the next words, and the last starts with the closing words. ``texts`` keeps every
    occurrence, so a name that repeats a word ("Echo Echo Consulting") can use two equal values;
    each occurrence is used at most once. Equal texts are interchangeable, so only the first unused
    occurrence of each is tried. Bounded search; when the budget runs out, every text that could
    take part is returned (fail closed)."""
    size = len(name)
    counts = {}
    for text in texts:
        counts[text] = counts.get(text, 0) + 1
    starts, middles, ends_at = [], {}, {}
    for text in counts:
        for cut in range(1, min(len(text), size - 1) + 1):
            if text[-cut:] == name[:cut]:
                starts.append((cut, text))
        if len(text) < size - 1:
            for at in range(1, size - len(text)):
                if text == name[at:at + len(text)]:
                    middles.setdefault(at, []).append((at + len(text), text))
        for at in range(1, size):
            if text[:size - at] == name[at:]:
                ends_at.setdefault(at, []).append(text)
    found, budget = set(), [FOREIGN_CHAIN_BUDGET]

    def walk(position, used):
        budget[0] -= 1
        if budget[0] < 0:
            return
        for text in ends_at.get(position, ()):
            if used.get(text, 0) < counts[text]:
                found.update(used)
                found.add(text)
        for after, text in middles.get(position, ()):
            if used.get(text, 0) < counts[text]:
                walk(after, {**used, text: used.get(text, 0) + 1})

    for cut, text in starts:
        walk(cut, {text: 1})
    if budget[0] < 0:
        return {text for _cut, text in starts} | {
            text for group in ends_at.values() for text in group} | {
            text for group in middles.values() for _after, text in group}
    return found


def _own_forms(own):
    if isinstance(own, str):
        own = (own,)
    return {tuple(key.split()) for key in own or () if isinstance(key, str)}


def contributors_of(texts, foreign):
    """Rule 9.11 (and rule 9.9, for identities held as unverified) over one candidate's collection of
    input-derived texts: the normalised texts that name a withheld name, alone or when two or more
    of them are read together in some order (a name split across fields, list items or register
    values). Each text is read in both format-character forms (see _text_variants()). A name is
    searched for only when the collection's tokens include every token of it (as often as the name
    repeats it), so the cost grows with the collection, not with the number of names. A text that
    only shares a word with a name never counts on its own, and a text that is exactly one of the
    engine's fixed texts never counts at all. An occurrence inside one of the set's ``allowed``
    names (the client's own name) never counts, and those names never take part in a split. An
    entry may be ``(text, own)``: a row's own identity (``own`` its canonical forms), screened
    against every other name (alone and with the rest of the collection) but never against itself."""
    foreign = _as_foreign(foreign)
    if not foreign:
        return set()
    allowed = foreign.allowed
    entries = []
    for entry in texts:
        text, own = entry if isinstance(entry, tuple) else (entry, None)
        if _engine_value(text):
            continue
        own = _own_forms(own)
        for form in _text_variants(text, allowed):
            if form[0]:
                entries.append((form, own))
    found, rest = set(), []
    for form, own in entries:
        if any(name not in own and _occurs(form, name)
               for token in set(form[0]) for name in foreign.filed.get(token, ())):
            found.add(form[0])
        else:
            rest.extend((unit, own) for unit in _units(form))  # every occurrence
    counts = Counter(token for unit, _own in rest for token in unit)
    for token in counts:
        for name in foreign.filed.get(token, ()):
            if len(name) > 1 and all(counts[part] >= need for part, need in Counter(name).items()):
                found.update(_split_name_contributors([unit for unit, own in rest if name not in own], name))
    return {" ".join(tokens) for tokens in found}


def collection_keys(texts, foreign):
    """Every normalised form contributors_of() can return for ``texts`` (whole texts and units)."""
    allowed = _as_foreign(foreign).allowed
    keys = set()
    for entry in texts:
        text = entry[0] if isinstance(entry, tuple) else entry
        for form in _text_variants(text, allowed):
            keys.add(" ".join(form[0]))
            keys.update(" ".join(unit) for unit in _units(form))
    return keys


def foreign_contributors(record, foreign, skip=FOREIGN_SKIP, extra=()):
    """Rule 9.11 for one candidate record (and ``extra`` input-derived texts read with it): see
    contributors_of()."""
    return contributors_of([*_record_texts(record, skip), *extra], foreign)


_VOCABULARY = {
    "type": KNOWN_TYPES,
    "status": CLEAR_STATUSES | FI_STATUSES | WALL_STATUSES | DATED_STATUSES | RESOLVED_STATUSES,
}


def _vocabulary_value(key, value):
    """True for a value that is exactly the canonical vocabulary the engine emits for ``key``."""
    if not isinstance(value, str):
        return False
    if key == "role_type":
        return value in ROLE_TYPES
    return value in _VOCABULARY.get(key, ())


def _default_source_used(item, engagement, held):
    """True when verdict_for() writes the register's own source into this row's entry: a held or
    another client's row always carries it, an evaluated row only when it has no source of its own;
    a row withheld by source screening carries no source at all."""
    if held is not None and (None in held or held & DECISION_FIELDS):
        return False
    name = _text(item, "client_name")
    if shape_problems(item) or not name.strip() or is_reserved_label(name):
        return True
    if applies_to_client(item, engagement) is not True:
        return True
    return not _text(item, "source")


def verdict_sources(constraints, register_rows, held_rows=None):
    """The input-derived texts of a candidate's register rows (rule 9.11), read from the raw rows
    before any entry replaces them: every member name and every string of every row, whether or not
    it applies to this engagement, except the candidate_id and values that are exactly fixed
    vocabulary or one of the engine's fixed texts. The client_name of a row for another client, or
    of a row whose entity cannot be matched reliably (rule 9.9), is that row's own identity: it comes
    back as ``(name, identity forms)`` so it is screened against every other withheld name but never
    its own. The register's own source counts only when some
    row's entry falls back to it, and the register's citation only for a candidate with no row.
    Engine-composed text is never candidate content."""
    engagement = constraints.get("engagement") or {}
    held_rows = held_rows or {}
    texts, default_used = [], not register_rows
    for index, item in register_rows:
        own_row = applies_to_client(item, engagement) is False or ambiguous_row(item, engagement)
        default_used = default_used or _default_source_used(item, engagement, held_rows.get(index))
        for key, value in item.items():
            if key == "candidate_id":
                continue
            if own_row and key == "client_name":
                texts.append((value, entity_keys(value)))
                continue
            if isinstance(key, str) and key not in _CONSIDERED_SHAPE:
                texts.append(key)
            if key == "role_type" and isinstance(value, str):
                value = carried_role_type(value)  # the form the entry carries
            if not _vocabulary_value(key, value) and not _engine_value(value):
                texts.extend(_value_texts(value, True))
    for key, used in (("source", default_used), ("citation", not register_rows)):
        value = constraints.get(key)
        if used and isinstance(value, str) and not _engine_value(value):
            texts.append(value)
    return texts


# Entry types the engine itself emits in constraints_considered (not register rows).
_ENGINE_ENTRY_TYPES = {"source_screening", "availability", "availability_evidence", "conflicts_register_coverage"}
# Entry types built from the bench record (already screened with it) or from fixed text only.
_RECORD_ENTRY_TYPES = {"source_screening", "availability", "availability_evidence"}
# Members of a register entry that carry input text; every other member is engine-composed.
_INPUT_MEMBERS = ("client_name", "status", "role_type", "process", "end_date", "resolved_date", "source", "citation")
# Fixed text and defaults the engine itself writes into those members.
_ENGINE_TEXTS = {
    FOREIGN_LABEL, FOREIGN_VALUE, FOREIGN_REASON, FOREIGN_RULE, UNVERIFIED_VALUE, UNVERIFIED_REASON,
    UNVERIFIED_RULE, "withheld", "conflicts record",
    "conflicts register", "connector:conflicts-register",
    f"conflicts register citation withheld: names another client ({RULES} #9.9)",
}
_ENGINE_ROW_TEXT = re.compile(
    r"conflicts register row \d+(?: for another client; name and citation withheld)? "
    r"\(independence-eligibility-rules\.md #\d+\.\d+(?:,#\d+\.\d+)*\)")


def _engine_text(value):
    return value in _ENGINE_TEXTS or _ENGINE_ROW_TEXT.fullmatch(value) is not None


@functools.lru_cache(maxsize=4096)
def _fixed_key(text):
    """Canonical folding for comparing a value with the engine's fixed texts: confusables, case and
    punctuation folded, every word kept (corporate suffixes too, so "Register LLC" is not "register")."""
    return " ".join(re.sub(r"[\W_]+", " ", steering_guard.normalize(canonical(text))).split())


_ENGINE_KEYS = frozenset(key for key in map(_fixed_key, _ENGINE_TEXTS) if key)


def _engine_value(value):
    """True for an input value that is exactly one of the engine's fixed texts (after canonical
    folding): such a value is the engine's own vocabulary, never candidate-sourced content."""
    return isinstance(value, str) and (_engine_text(value) or _fixed_key(value) in _ENGINE_KEYS)


def _own_identity(item, foreign):
    """For another client's entry in a hand-built governed document (not applicable, client_name
    itself an established foreign identity), that identity (its canonical forms); otherwise None. Only that client_name
    is the engine's representation of the entry; every other member is screened as usual."""
    name = item.get("client_name")
    if item.get("applies_to_engagement") is False and isinstance(name, str) and name != FOREIGN_LABEL:
        keys = tuple(key for key in entity_keys(name) if key in foreign)
        if keys:
            return keys
    return None


def _untrusted_member(key, value):
    """A member outside the engine's register-entry shape, or of a type the engine never emits."""
    return key not in _CONSIDERED_SHAPE or not _CONSIDERED_SHAPE[key](value)


def _input_member(item, key, value, own=None):
    """True for a constraints_considered member that carries register input text (not fixed
    vocabulary, engine text, an entry built from the bench record, or the client_name that is
    another client's entry's own identity)."""
    return (isinstance(value, str) and bool(value.strip()) and key in _INPUT_MEMBERS
            and not (key == "client_name" and own is not None)
            and item.get("type") not in _RECORD_ENTRY_TYPES
            and not _vocabulary_value(key, value) and not _engine_value(value))


def _member_texts(key, value):
    """Every text of an untrusted member: its name and every nested name and value."""
    return ([key] if isinstance(key, str) else []) + list(_value_texts(value, True))


def considered_texts(items, foreign=frozenset()):
    """The register input text a constraints_considered list carries (rule 9.11), in order."""
    if not isinstance(items, list):
        return []
    texts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        own = _own_identity(item, foreign)
        for key, value in item.items():
            if _untrusted_member(key, value):
                texts.extend(_member_texts(key, value))
            elif key == "client_name" and own is not None:
                texts.append((value, own))
            elif _input_member(item, key, value, own):
                texts.append(value)
    return texts


def withhold_considered(items, foreign, contributors=(), held=False):
    """Rule 9.11 for a constraints_considered list: register input text naming another client (or
    holding a contributing value) is withheld and counted. For a ``held`` candidate, engine-composed
    text holding a contributing value is withheld too; dispositions, fixed vocabulary, engine entry
    types and engine text are always kept. A member outside the engine's entry shape is screened and
    never carried; a known member of the wrong type is screened and withheld on a hit. Another
    client's entry is screened like any other, except that its client_name is not matched against its
    own identity. Returns (new list, number of input values withheld)."""
    if not isinstance(items, list):
        return items, 0
    foreign = _as_foreign(foreign)
    out, hits = [], 0
    for item in items:
        if not isinstance(item, dict):
            out.append(item)
            continue
        own = _own_identity(item, foreign)
        entry = {}
        for key, value in item.items():
            if _untrusted_member(key, value):
                hit = any(_foreign_hit(text, foreign, contributors) for text in _member_texts(key, value))
                hits += hit
                if key not in _CONSIDERED_SHAPE:
                    continue
                if hit:
                    value = foreign.value
            elif key == "client_name" and own is not None:
                others = foreign.without(own)
                if _foreign_hit(value, others, contributors):
                    value = foreign.value
                    hits += 1
            elif _input_member(item, key, value, own):
                if _foreign_hit(value, foreign, contributors):
                    value = foreign.value
                    hits += 1
            elif (held and isinstance(value, str) and key not in ("type", "disposition")
                    and not _vocabulary_value(key, value) and not _engine_value(value)
                    and _foreign_hit(value, foreign, contributors)):
                value = foreign.value
            entry[key] = value
        out.append(entry)
    return out, hits


def candidate_records(document):
    """Every candidate record carried in the bench, scored and ranked sections of ``document``."""
    for record in document.get("bench_candidates") or []:
        yield record
    for section, member in (("scored_roles", "candidate_scores"), ("ranked_roles", "candidate_slate")):
        for role in document.get(section) or []:
            if isinstance(role, dict):
                yield from role.get(member) or []


def foreign_candidates(records, foreign, skip=FOREIGN_SKIP, extra_contributors=None):
    """id_key(candidate_id) -> contributing normalised values, for each candidate with any record that
    names another client (rule 9.11). ``extra_contributors(record)`` gives further input-derived texts
    read with that record as one collection (the candidate's register text)."""
    foreign = _as_foreign(foreign)
    found = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        key = id_key(record.get("candidate_id"))
        contributors = foreign_contributors(record, foreign, skip,
                                            extra_contributors(record) if extra_contributors else ())
        if key is not None and contributors:
            found.setdefault(key, set()).update(contributors)
    return found


def _withhold_records(records, foreign, flagged):
    if not isinstance(records, list):
        return withhold_foreign(records, foreign)[0]
    out = []
    for record in records:
        if isinstance(record, dict):
            contributors = flagged.get(id_key(record.get("candidate_id")), ())
            out.append(withhold_record(record, foreign, FOREIGN_SKIP, contributors)[0])
        else:
            out.append(withhold_foreign(record, foreign)[0])
    return out


def withhold_foreign_sections(payload, foreign, flagged=None):
    """Rule 9.11: the candidate records carried through unchanged (bench, scored and ranked sections)
    are screened the same way, so a value naming another client never reaches any output. ``flagged``
    is the foreign_candidates() map; every contributing value of a flagged candidate is withheld."""
    foreign = _as_foreign(foreign)
    flagged = flagged if flagged is not None else foreign_candidates(candidate_records(payload), foreign)
    if "bench_candidates" in payload:
        payload["bench_candidates"] = _withhold_records(payload["bench_candidates"], foreign, flagged)
    for section, member in (("scored_roles", "candidate_scores"), ("ranked_roles", "candidate_slate")):
        if section not in payload:
            continue
        roles = payload[section]
        if not isinstance(roles, list):
            payload[section] = withhold_foreign(roles, foreign)[0]
            continue
        screened_roles = []
        for role in roles:
            if not isinstance(role, dict):
                screened_roles.append(withhold_foreign(role, foreign)[0])
                continue
            screened_roles.append({
                key: _withhold_records(item, foreign, flagged) if key == member
                else withhold_foreign(item, foreign)[0]
                for key, item in role.items()
            })
        payload[section] = screened_roles
    return payload


def govern(ranked_payload, constraints_payload):
    """Apply the independence and eligibility rules; returns the governed document. No file I/O.

    The inputs are never mutated. ``ranked_payload`` is expected to be a document this plugin's
    engines produced (the CLI passes the re-derived one), so whole engine markers in it are kept.
    Both documents are validated first; any malformed member is an InputError naming its path.
    """
    validate_ranked(ranked_payload)
    validate_constraints(constraints_payload, ranked_payload)

    target_engagement = dict(ranked_payload["engagement"])
    if isinstance(constraints_payload.get("engagement"), dict):
        target_engagement["affiliates"] = merge_unique(
            _affiliates(ranked_payload["engagement"]), _affiliates(constraints_payload["engagement"]))
    foreign, ambiguous = screened_identities(constraints_payload, target_engagement)

    log = ScreeningLog()
    _seed_engine_markers(log, ranked_payload, "")
    payload = sanitize_free_text(ranked_payload, "ranked_input", log, engine_markers_ok=True)
    constraints = sanitize_free_text(constraints_payload, "constraints_input", log)

    escalations = _Escalations()
    escalations.extend(payload.get("escalations", []))
    for index, item in enumerate(constraints.get("escalations", [])):
        text, head = normalise_escalation(item, index)
        if _names_foreign(text, foreign):
            text = f"constraints escalations[{index}]: escalation names another client; withheld ({RULES} #9.9)"
        escalations.add(text, head)
    escalations.extend(log)
    merge_notes = []
    try:
        merge_engagement(payload, constraints, merge_notes)
    except SystemExit as error:
        raise InputError(str(error.code)) from None
    escalations.extend(merge_notes)
    if any(unverified_text(constraints_payload.get(key), ambiguous) for key in ("source", "citation")):
        escalations.add(
            f"conflicts register source or citation names an entity that cannot be matched reliably; "
            f"withheld ({RULES} #9.9)", f"{RULES} #9.9")

    held_rows = _held_rows(log)
    row_holds = {index: log.holds_under(f"constraints_input.constraints[{index}]") for index in held_rows}
    register = constraints["constraints"]
    if not register:
        escalations.add(
            f"conflicts register supplied no rows - every candidate requires independence review ({RULES} #9.4)")

    roles_by_key = {id_key(role["role_id"]): role for role in payload["roles"]}
    ranked_ids = [
        candidate["candidate_id"]
        for ranked_role in payload["ranked_roles"]
        for candidate in ranked_role["candidate_slate"]
    ]
    for index in unknown_constraint_rows(constraints, ranked_ids):
        escalations.add(
            f"constraints[{index}]: conflicts-register row names a candidate_id that is not on the ranked slate "
            f"- check candidate ID mapping ({RULES} #9.5)",
            f"{RULES} #9.5",
        )
    # Rule 9.11 reads one collection per candidate: the values of each of its records together with
    # the register text its verdict can carry, so a name split between them is still found.
    rows_by_key = register_index(constraints)
    register_texts = {}
    for ranked_role in payload["ranked_roles"]:
        for candidate in ranked_role["candidate_slate"]:
            key = id_key(candidate["candidate_id"])
            if key not in register_texts:
                register_texts[key] = verdict_sources(constraints, rows_by_key.get(key, []), held_rows)
    flagged = foreign_candidates(
        candidate_records(payload), foreign,
        extra_contributors=lambda record: register_texts.get(id_key(record.get("candidate_id")), ()))
    # Rule 9.9: identities held as unverified are searched for in the same collections.
    unverified = foreign_candidates(
        candidate_records(payload), ambiguous,
        extra_contributors=lambda record: register_texts.get(id_key(record.get("candidate_id")), ()))
    missing_reported = set()
    governed_roles = []
    gaps = []

    for r_index, ranked_role in enumerate(payload["ranked_roles"]):
        role = roles_by_key[id_key(ranked_role["role_id"])]
        role_id = role["role_id"]
        governed = []
        top_refused = False
        for c_index, row in enumerate(ranked_role["candidate_slate"]):
            register_rows = rows_by_key.get(id_key(row["candidate_id"]), [])
            candidate_held = {index: held_rows[index] for index, _item in register_rows if index in held_rows}
            ranked_holds = log.holds_under(f"ranked_input.ranked_roles[{r_index}].candidate_slate[{c_index}]")
            # Rule 9.11: a carried candidate value naming another client is withheld before any rule
            # or message reads it, and the candidate is held for review. Hold lines are screened too.
            flagged_values = flagged.get(id_key(row["candidate_id"]), ())
            row, foreign_hits = withhold_foreign(row, foreign, FOREIGN_SKIP, flagged_values)
            ranked_holds, hold_hits = _withhold_holds(ranked_holds, foreign, flagged_values)
            register_holds, register_hits = _withhold_holds(
                merge_unique(*[row_holds[index] for index in candidate_held]), foreign, flagged_values)
            foreign_hits += hold_hits + register_hits + bool(flagged_values)
            unverified_values = unverified.get(id_key(row["candidate_id"]), ())
            row, unverified_hits = withhold_foreign(row, ambiguous, FOREIGN_SKIP, unverified_values)
            ranked_holds, hold_hits = _withhold_holds(ranked_holds, ambiguous, unverified_values)
            register_holds, register_hits = _withhold_holds(register_holds, ambiguous, unverified_values)
            unverified_hits += hold_hits + register_hits + bool(unverified_values)
            holds = merge_unique(row.get("screening_holds") or [], ranked_holds)

            foreign_held = bool(foreign_hits)
            unverified_held = bool(unverified_hits)
            verdict_row = dict(row, screening_holds=holds)
            result = verdict_for(role, verdict_row, constraints, candidate_held, foreign_hold=foreign_held,
                                 register_rows=register_rows, ambiguous=ambiguous, unverified_hold=unverified_held)
            for item in result[3]:
                if "client_name" in item and item.get("applies_to_engagement") is not False \
                        and _names_foreign(item.get("citation"), foreign):
                    item["citation"] = f"conflicts register citation withheld: names another client ({RULES} #9.9)"
            verdict, reasons, citations, considered = result
            # Only register input text reaches the verdict (bench values were withheld above); engine
            # vocabulary and engine text never count.
            sources = register_texts.get(id_key(row["candidate_id"]), ())
            for names, values in ((foreign, flagged_values), (ambiguous, unverified_values)):
                register_contributors = set(values) & collection_keys(sources, names)
                if register_contributors:
                    reasons = [text if _engine_text(text) else withhold_foreign(text, names, contributors=register_contributors)[0]
                               for text in reasons]
                    citations = [text if _engine_text(text) else withhold_foreign(text, names, contributors=register_contributors)[0]
                                 for text in citations]
                considered = withhold_considered(considered, names, register_contributors, held=bool(register_contributors))[0]
            if unverified_held:
                escalations.add(
                    f"{role_id}: {row['candidate_id']} - {UNVERIFIED_REASON}; independence review required "
                    f"({UNVERIFIED_RULE})",
                    UNVERIFIED_RULE,
                )
            if foreign_held:
                escalations.add(
                    f"{role_id}: {row['candidate_id']} - {FOREIGN_REASON}; independence review required "
                    f"({FOREIGN_RULE})",
                    FOREIGN_RULE,
                )
            for index, item in register_rows:
                if index in candidate_held:
                    continue
                applies = applies_to_client(item, constraints.get("engagement") or {})
                if ambiguous_row(item, constraints.get("engagement") or {}):
                    escalations.add(
                        f"{row['candidate_id']}: {_row_label(index)} entity cannot be matched reliably to the "
                        f"client or a declared affiliate - independence review required ({RULES} #9.9)",
                        f"{RULES} #9.9",
                    )
                elif status_problem(item) and applies is not False:
                    escalations.add(
                        f"{row['candidate_id']}: {_row_label(index)} status is missing or not recognised "
                        f"- independence review required ({RULES} #9.1)",
                        f"{RULES} #9.1",
                    )
                elif applies is False and foreign_row_problems(item):
                    escalations.add(
                        f"{row['candidate_id']}: {_row_label(index)} for another client is malformed "
                        f"- independence review required ({RULES} #9.9)",
                        f"{RULES} #9.9",
                    )
            fit = float(row["fit_score"])
            recommendation_status = "not_recommended"
            if verdict == "eligible" and fit >= MIN_RECOMMENDABLE_SCORE:
                recommendation_status = "recommended"
            elif verdict == "eligible":
                recommendation_status = "below_score_floor"
            top = row["provisional_rank"] == 1
            if verdict == "ineligible":
                reason, blocking_rule = blocking_reason(reasons, citations)
                if top:
                    top_refused = True
                    fallback = (f"{role_id}: refused top provisional candidate at provisional rank 1 "
                                f"({blocking_rule}; {RULES} #7.1)")
                    escalations.add(fallback if foreign_held else screened(
                        f"{role_id}: refused top provisional candidate {row['candidate_name']} - {reason} "
                        f"({blocking_rule}; {RULES} #7.1)",
                        fallback,
                    ))
            elif verdict == "needs_review":
                reason, blocking_rule = review_reason(reasons, citations)
                if top:
                    fallback = (f"{role_id}: withheld top provisional candidate at provisional rank 1 "
                                f"({blocking_rule}; {RULES} #1.2)")
                    escalations.add(fallback if foreign_held else screened(
                        f"{role_id}: withheld top provisional candidate {row['candidate_name']} "
                        f"- {reason} ({blocking_rule}; {RULES} #1.2)",
                        fallback,
                    ))
            else:
                blocking_rule = None
            key = id_key(row["candidate_id"])
            if not register_rows and key not in missing_reported:
                missing_reported.add(key)
                escalations.add(
                    f"{row['candidate_id']}: no conflicts-register row - clearance cannot be inferred; "
                    f"independence review required ({RULES} #9.4)",
                    f"{RULES} #9.4",
                )
            citation = "; ".join(citations)
            if is_suspect(citation):
                citation = "; ".join(item.split(";", 1)[0] for item in citations)
            out = {key: row[key] for key in row if key in CARRIED_KEYS}
            all_holds = merge_unique(holds, register_holds)
            if all_holds or "screening_holds" in row:
                out["screening_holds"] = all_holds
            out["constraints_considered"] = considered
            out["eligibility"] = {
                "verdict": verdict,
                "recommendation_status": recommendation_status,
                "blocking_rule": blocking_rule,
                "reasons": reasons,
                "source": ENGINE,
                "confidence": min(float(row["confidence"]), 0.99),
                "citation": citation,
            }
            governed.append(out)

        eligible = [c for c in governed if c["eligibility"]["recommendation_status"] == "recommended"]
        for i, candidate in enumerate(eligible, start=1):
            candidate["final_eligible_rank"] = i
        title = screened(role["title"], "this role")
        if not eligible:
            gaps.append({
                "role_id": role_id,
                "role_title": role["title"],
                "gap_statement": f"No eligible candidate meets the {MIN_RECOMMENDABLE_SCORE} fit-score floor for {title}; do not pad the slate.",
                "source": ENGINE,
                "confidence": 0.99,
                "citation": f"fit-scoring-rubric.md #7.2; {RULES} #7.2",
            })
            escalations.add(f"{role_id}: gap statement issued - no eligible candidate above score floor ({RULES} #7.2)")

        governed_roles.append({
            "role_id": ranked_role["role_id"],
            "role_title": ranked_role["role_title"],
            "top_provisional_candidate_refused": top_refused,
            "candidate_slate": governed,
            "recommended_candidates": eligible,
            "source": ENGINE,
            "confidence": 0.99,
            "citation": f"{RULES} #1.1-#8.1",
        })

    withhold_foreign_sections(payload, foreign, flagged)
    withhold_foreign_sections(payload, ambiguous, unverified)
    payload["governed_roles"] = governed_roles
    payload["gaps"] = gaps
    rendered = []
    for text in escalations.render():
        if _names_foreign(text, foreign):
            text = f"escalation withheld: names another client ({FOREIGN_RULE})"
        elif _names_foreign(text, ambiguous):
            text = f"escalation withheld: names an entity that cannot be matched reliably ({UNVERIFIED_RULE})"
        if text not in rendered:
            rendered.append(text)
    payload["escalations"] = rendered
    provenance = payload.setdefault("provenance", {})
    engines = [
        engine for engine in provenance.get("engines", [])
        if not engine.startswith("constraint_check/")
    ]
    provenance["engines"] = merge_unique(engines, [ENGINE_VERSION])
    return payload


def rederive_ranked(roles_payload, bench_payload):
    """The ranked document the plugin's own engines derive from roles.json and bench.json."""
    return slate_rank.rank(fit_score.score(roles_payload, bench_payload))


def _main(argv):
    parser = ArgumentParser(prog="constraint_check.py", description="Deterministic eligibility governance.")
    parser.add_argument("--roles", required=True)
    parser.add_argument("--bench", required=True)
    parser.add_argument("--ranked", required=True)
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    roles_payload = load_json(args.roles, "roles.json")
    bench_payload = load_json(args.bench, "bench.json")
    ranked_payload = load_json(args.ranked, "ranked.json")
    constraints_payload = load_json(args.constraints, "constraints.json")
    need(ranked_payload.get("contract_version") == CONTRACT,
         "ranked.json: wrong ranked contract (contract_version)")
    need(constraints_payload.get("contract_version") == CONTRACT,
         "constraints.json: wrong constraints contract (contract_version)")
    expected = rederive_ranked(roles_payload, bench_payload)
    need(same_document(ranked_payload, expected),
         "ranked.json does not re-derive from roles.json and bench.json (rule 9.8); re-run fit-score")
    try:
        payload = govern(expected, constraints_payload)
    except SystemExit as error:
        if isinstance(error.code, str):
            raise InputError(error.code) from None
        raise
    write_json(args.out, payload)
    governed_roles = payload["governed_roles"]
    refused = sum(1 for r in governed_roles if r["top_provisional_candidate_refused"])
    print(f"constraint_check: {len(governed_roles)} role(s), {refused} top-candidate refusal(s), "
          f"{len(payload['gaps'])} gap(s) -> governed output written")
    return 0


def main(argv=None):
    """CLI entry point: one clean ``error:`` line and exit 2 on any input error, no output file."""
    return run(lambda: _main(argv))


if __name__ == "__main__":
    sys.exit(main())
