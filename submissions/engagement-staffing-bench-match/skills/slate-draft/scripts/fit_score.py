#!/usr/bin/env python3
"""fit_score - deterministic candidate fit scoring (ps.engagement-staffing-bench-match.v1).

Reads role requirements and bench candidates as JSON and writes JSON. No network, no model
calls, no side effects beyond the requested output file. The model quotes this output; it
never recomputes scores or utilisation figures.

``score(roles_payload, bench_payload)`` is the pure engine (no file I/O); later engines import it
to re-derive this stage (independence-eligibility-rules.md #9.8). Inputs are validated in full
before anything is scored; any malformed input is one ``error:`` line naming a field path, exit 2,
and no output file.
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from input_guard import (
    ArgumentParser,
    InputError,
    check_confidence,
    check_date,
    check_id,
    engagement_id_key,
    check_name,
    check_pct,
    check_timestamp,
    duplicate_keys,
    field,
    has_marker,
    id_key,
    is_num,
    load_json,
    need,
    run,
    text_list,
    write_json,
)
from safety_text import ScreeningLog, is_suspect, safe_citation, safe_text, same_client, sanitize_free_text

ENGINE = "engine:fit_score"
ENGINE_VERSION = "fit_score/1.1.14"
CONTRACT = "ps.engagement-staffing-bench-match.v1"
DEFAULT_DURATION_WEEKS = 52

WEIGHT_SKILLS = 0.40          # fit-scoring-rubric.md #1.1
WEIGHT_SENIORITY = 0.15       # fit-scoring-rubric.md #1.2
WEIGHT_AVAILABILITY = 0.20    # fit-scoring-rubric.md #1.3
WEIGHT_LOCATION_LANGUAGE = 0.10  # fit-scoring-rubric.md #1.4
WEIGHT_RATE = 0.10            # fit-scoring-rubric.md #1.5
WEIGHT_CONTINUITY = 0.05      # fit-scoring-rubric.md #1.6

REQUIRED_SKILL_WEIGHT = 0.70  # fit-scoring-rubric.md #2.1
PREFERRED_SKILL_WEIGHT = 0.20 # fit-scoring-rubric.md #2.2
CERT_WEIGHT = 0.10            # fit-scoring-rubric.md #2.3

SENIORITY_BANDS = ["associate", "consultant", "senior consultant", "manager", "senior manager", "director", "partner"]

# Sources a raw roles.json / bench.json record may carry; engine:* stamps belong to engine output only.
RAW_SOURCES = (
    "skill:role-intake",
    "connector:resource-management-system",
    "connector:conflicts-register",
)
# Members only an engine writes; a raw input carrying one is refused (rule 9.8).
ENGINE_OWNED = ("scored_roles", "ranked_roles", "governed_roles", "gaps")
POLICIES = {
    "fit-scoring-rubric.md": "1.1.5",
    "independence-eligibility-rules.md": "1.1.5",
}


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


def normalize_candidate_id(value):
    return id_key(value) or ""


# ---------------------------------------------------------------------------------------------
# Input validation (A1/A2/A5a/A6/A7/A12/A13/A17/A21/B4/C5/D17/D20/D25; rules 9.7, 9.8, 9.9).
# Messages name field paths only; values and file paths are never echoed.
# ---------------------------------------------------------------------------------------------
def _ident(value, path):
    check_id(value, path)
    need(not is_suspect(value), f"{path} carries instruction-like text (rule 9.7)")
    return value


def _opt_text(obj, key, where):
    return field(obj, key, "str", where, required=key in obj)


def _opt_list(obj, key, where):
    return text_list(obj, key, where, required=key in obj)


def _provenance_fields(obj, where):
    source = field(obj, "source", "str", where)
    need(source in RAW_SOURCES, f"{where}.source is not a recognised source for this input (rule 9.9)")
    check_confidence(field(obj, "confidence", "num", where), f"{where}.confidence")
    citation = field(obj, "citation", "str", where)
    need(citation.strip(), f"{where}.citation must not be blank (citations are required provenance)")


def _validate_engagement(document):
    engagement = field(document, "engagement", "obj", "")
    need(engagement, "engagement must not be empty")
    _ident(field(engagement, "engagement_id", "str", "engagement"), "engagement.engagement_id")
    check_name(field(engagement, "client_name", "str", "engagement"), "engagement.client_name")
    affiliates = _opt_list(engagement, "affiliates", "engagement")
    for index, affiliate in enumerate(affiliates or []):
        check_name(affiliate, f"engagement.affiliates[{index}]")
    for key in ("practice", "stage"):
        _opt_text(engagement, key, "engagement")
    _provenance_fields(engagement, "engagement")
    return engagement


def _validate_header(document, wrong_contract):
    need(document.get("contract_version") == CONTRACT, f"{wrong_contract} (contract_version)")
    for key in ENGINE_OWNED:
        need(key not in document,
             f"{key} is engine-owned and not valid in a raw input; supply role-intake or bench output (rule 9.8)")
    _opt_list(document, "escalations", "")
    provenance = field(document, "provenance", "obj", "", required="provenance" in document)
    if provenance is not None:
        if "generated_at" in provenance:
            check_timestamp(provenance["generated_at"], "provenance.generated_at")
        _opt_list(provenance, "engines", "provenance")
        _opt_text(provenance, "demo_scenario", "provenance")
        policies = field(provenance, "policies", "obj", "provenance", required="policies" in provenance)
        for key, value in (policies or {}).items():
            need(isinstance(value, str), "provenance.policies values must be strings")
    return provenance or {}


def _validate_role(role, where):
    need(isinstance(role, dict), f"{where} must be an object")
    _ident(field(role, "role_id", "str", where), f"{where}.role_id")
    check_name(field(role, "title", "str", where), f"{where}.title")
    check_date(field(role, "start_date", "str", where), f"{where}.start_date")
    allocation = check_pct(field(role, "allocation_pct", "num", where), f"{where}.allocation_pct")
    need(allocation > 0, f"{where}.allocation_pct must be greater than 0")
    text_list(role, "required_skills", where)
    for key in ("preferred_skills", "required_certifications", "required_languages"):
        _opt_list(role, key, where)
    for key in ("seniority", "location", "industry_context"):
        _opt_text(role, key, where)
    field(role, "remote_ok", "bool", where, required="remote_ok" in role)
    band = field(role, "rate_band", "obj", where)
    low = field(band, "min", "num", f"{where}.rate_band")
    high = field(band, "max", "num", f"{where}.rate_band")
    need(0 <= low <= high, f"{where}.rate_band must satisfy 0 <= min <= max")
    _opt_text(band, "currency", f"{where}.rate_band")
    _provenance_fields(role, where)


def _validate_blocks(candidate, key, where):
    blocks = field(candidate, key, "list", where)
    for index, block in enumerate(blocks):
        path = f"{where}.{key}[{index}]"
        need(isinstance(block, dict), f"{path} must be an object")
        check_pct(field(block, "allocation_pct", "num", path), f"{path}.allocation_pct")
        # A missing or unparseable date keeps the conservative path (fit-scoring-rubric.md #4.1).
        for date_key in ("start", "end"):
            field(block, date_key, "str", path, required=False)
        _opt_text(block, "citation", path)


def _validate_candidate(candidate, where):
    need(isinstance(candidate, dict), f"{where} must be an object")
    _ident(field(candidate, "candidate_id", "str", where), f"{where}.candidate_id")
    check_name(field(candidate, "name", "str", where), f"{where}.name")
    text_list(candidate, "skills", where)
    for key in ("certifications", "industry_experience", "languages"):
        _opt_list(candidate, key, where)
    for key in ("seniority", "location"):
        _opt_text(candidate, key, where)
    if candidate.get("rate") is not None:
        need(is_num(candidate["rate"]), f"{where}.rate must be a number")
        need(candidate["rate"] >= 0, f"{where}.rate must not be negative")
    check_pct(field(candidate, "current_allocation_pct", "num", where), f"{where}.current_allocation_pct")
    if "target_utilization_pct" in candidate:
        check_pct(field(candidate, "target_utilization_pct", "num", where),
                  f"{where}.target_utilization_pct")
    for key in ("approved_leave", "soft_bookings"):
        _validate_blocks(candidate, key, where)
    _provenance_fields(candidate, where)


def _labelled(label, check, *args):
    try:
        return check(*args)
    except InputError as error:
        raise InputError(f"{label}: {error}") from None


def _validate_roles_document(roles_payload):
    provenance = _validate_header(roles_payload, "wrong roles contract")
    engagement = _validate_engagement(roles_payload)
    roles = field(roles_payload, "roles", "list", "")
    need(roles, "roles must not be empty")
    for index, role in enumerate(roles):
        _validate_role(role, f"roles[{index}]")
    need(not duplicate_keys([role["role_id"] for role in roles]),
         "roles repeat a role_id after canonical folding (rule 9.7)")
    return engagement, provenance


def _validate_bench_document(bench_payload):
    provenance = _validate_header(bench_payload, "wrong bench contract")
    engagement = _validate_engagement(bench_payload)
    field(bench_payload, "roles", "list", "", required="roles" in bench_payload)
    candidates = field(bench_payload, "bench_candidates", "list", "")
    for index, candidate in enumerate(candidates):
        _validate_candidate(candidate, f"bench_candidates[{index}]")
    need(not duplicate_keys([candidate["candidate_id"] for candidate in candidates]),
         "bench_candidates repeat a candidate_id after canonical folding (rule 9.7)")
    return engagement, provenance


def validate_inputs(roles_payload, bench_payload):
    """Refuse malformed roles.json / bench.json before anything is screened or scored."""
    need(isinstance(roles_payload, dict), "roles.json: top level must be a JSON object")
    need(isinstance(bench_payload, dict), "bench.json: top level must be a JSON object")
    roles_engagement, roles_provenance = _labelled("roles.json", _validate_roles_document, roles_payload)
    bench_engagement, bench_provenance = _labelled("bench.json", _validate_bench_document, bench_payload)
    need(
        same_client(roles_engagement["client_name"], bench_engagement["client_name"])
        and engagement_id_key(roles_engagement["engagement_id"]) == engagement_id_key(bench_engagement["engagement_id"]),
        "bench.json: engagement does not match roles.json engagement (client_name, engagement_id)",
    )
    need("generated_at" in roles_provenance or "generated_at" in bench_provenance,
         "provenance.generated_at is required in roles.json or bench.json")


# ---------------------------------------------------------------------------------------------
# Scoring helpers. Redacted marker values never count as evidence (D19).
# ---------------------------------------------------------------------------------------------
def _usable(values):
    return [value for value in values or [] if not has_marker(value)]


def duration_window(role):
    raw = role.get("duration_weeks")
    if raw is None or raw == "":
        return DEFAULT_DURATION_WEEKS, True, [
            f"duration_weeks missing - availability counted over a "
            f"{DEFAULT_DURATION_WEEKS}-week window; confirm duration"
        ]
    if is_num(raw) and raw == int(raw) and raw >= 1:
        return int(raw), False, []
    return DEFAULT_DURATION_WEEKS, True, [
        f"duration_weeks is not a whole number of weeks of at least 1 - availability counted over a "
        f"{DEFAULT_DURATION_WEEKS}-week window; confirm duration"
    ]


def percent_value(value, default, label, warnings):
    if is_num(value):
        return float(value)
    warnings.append(f"{label} is missing or invalid; used conservative {default}%")
    return float(default)


def overlap_pct(blocks, start, weeks):
    role_start = date.fromisoformat(start)
    role_end = role_start + timedelta(weeks=weeks) - timedelta(days=1)
    role_days = (role_end - role_start).days + 1
    weighted_total = 0.0
    warnings = []
    for index, block in enumerate(blocks or []):
        if not isinstance(block, dict):
            warnings.append(f"availability block {index + 1} is malformed; treated as full-role")
            weighted_total += 100.0
            continue
        allocation = percent_value(
            block.get("allocation_pct", 100),
            100,
            f"availability block {index + 1} allocation_pct",
            warnings,
        )
        raw_start = block.get("start")
        raw_end = block.get("end")
        if raw_start in (None, ""):
            warnings.append(
                f"availability block {index + 1} without start date treated as starting at role start"
            )
            block_start = role_start
        else:
            try:
                block_start = date.fromisoformat(str(raw_start))
            except ValueError:
                warnings.append(
                    f"availability block {index + 1} has invalid start date; treated as starting at role start"
                )
                block_start = role_start
        if raw_end in (None, ""):
            warnings.append(
                f"availability block {index + 1} without end date treated as open-ended"
            )
            block_end = role_end
        else:
            try:
                block_end = date.fromisoformat(str(raw_end))
            except ValueError:
                warnings.append(
                    f"availability block {index + 1} has invalid end date; treated as open-ended"
                )
                block_end = role_end
        if block_end < block_start:
            warnings.append(
                f"availability block {index + 1} ends before it starts; treated as full-role"
            )
            block_start, block_end = role_start, role_end
        overlap_start = max(block_start, role_start)
        overlap_end = min(block_end, role_end)
        if overlap_start <= overlap_end:
            overlap_days = (overlap_end - overlap_start).days + 1
            weighted_total += allocation * overlap_days / role_days
    return min(weighted_total, 100.0), warnings


def coverage(required, actual):
    if not required:
        return 1.0
    actual_set = {x.lower() for x in _usable(actual)}
    return len([x for x in required if x.lower() in actual_set]) / len(required)


def matched_requirements(required, actual):
    actual_set = {str(value).casefold() for value in _usable(actual)}
    seen = set()
    matches = []
    for requirement in required or []:
        normalized = str(requirement).casefold()
        if normalized in actual_set and normalized not in seen:
            seen.add(normalized)
            matches.append(requirement)
    return sorted(matches)


def skill_score(role, cand):
    required = coverage(role.get("required_skills", []), cand.get("skills", []))
    preferred = coverage(role.get("preferred_skills", []), cand.get("skills", []))
    certs = coverage(role.get("required_certifications", []), cand.get("certifications", []))
    return required * REQUIRED_SKILL_WEIGHT + preferred * PREFERRED_SKILL_WEIGHT + certs * CERT_WEIGHT


def _band_index(level):
    return SENIORITY_BANDS.index("" if has_marker(level) else (level or "").lower())


def seniority_score(role_level, cand_level):
    try:
        diff = abs(_band_index(role_level) - _band_index(cand_level))
    except ValueError:
        return 0.0
    if diff == 0:
        return 1.0      # fit-scoring-rubric.md #3.1
    if diff == 1:
        return 0.75     # fit-scoring-rubric.md #3.2
    if diff == 2:
        return 0.40     # fit-scoring-rubric.md #3.3
    return 0.0          # fit-scoring-rubric.md #3.4


def availability_context(role, cand):
    weeks, duration_assumed, warnings = duration_window(role)
    leave, leave_warnings = overlap_pct(
        cand.get("approved_leave", []),
        role["start_date"],
        weeks,
    )
    soft, soft_warnings = overlap_pct(
        cand.get("soft_bookings", []),
        role["start_date"],
        weeks,
    )
    warnings.extend(f"approved leave: {warning}" for warning in leave_warnings)
    warnings.extend(f"soft booking: {warning}" for warning in soft_warnings)
    current = percent_value(
        cand.get("current_allocation_pct", 0),
        100,
        "current_allocation_pct",
        warnings,
    )
    requested = percent_value(
        role.get("allocation_pct"),
        100,
        "requested allocation_pct",
        warnings,
    )
    effective = max(0.0, 100.0 - current - leave - soft)  # fit-scoring-rubric.md #4.1,#4.2
    component = min(effective / requested, 1.0) if requested else 0.0
    return {
        "duration_weeks_used": weeks,
        "duration_assumed": duration_assumed,
        "current_allocation_pct": round(current, 1),
        "approved_leave_overlap_pct": round(leave, 1),
        "soft_booking_overlap_pct": round(soft, 1),
        "effective_available_pct": round(effective, 1),
        "requested_allocation_pct": round(requested, 1),
        "utilization_after_staffing_pct": round(current + requested, 1),  # fit-scoring-rubric.md #4.3
        "component_score": round(component, 3),
        "evidence_complete": not warnings,
        "calculation_warnings": warnings,
    }


def normalize_location(value):
    if has_marker(value):
        return ""
    city = str(value or "").split(",", 1)[0]
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", city.casefold()).split())


def location_language_score(role, cand):
    role_location = normalize_location(role.get("location"))
    candidate_location = normalize_location(cand.get("location"))
    location = 1.0 if role.get("remote_ok") is True or (
        role_location and role_location == candidate_location
    ) else 0.0
    language = coverage(role.get("required_languages", []), cand.get("languages", []))
    return location * 0.60 + language * 0.40  # fit-scoring-rubric.md #5.1,#5.2


def rate_score(role, cand):
    band = role.get("rate_band", {})
    if cand.get("rate") in (None, ""):
        return 0.0
    rate = float(cand["rate"])
    min_rate = float(band.get("min", 0))
    max_rate = float(band.get("max", 0))
    if min_rate <= rate <= max_rate:
        return 1.0      # fit-scoring-rubric.md #6.1
    if rate < min_rate:
        return 0.90     # fit-scoring-rubric.md #6.4
    if max_rate and rate <= max_rate * 1.10:
        return 0.60     # fit-scoring-rubric.md #6.2
    return 0.20         # fit-scoring-rubric.md #6.3


def rate_rule(role, cand):
    band = role.get("rate_band", {})
    if cand.get("rate") in (None, ""):
        return "fit-scoring-rubric.md #6.5"
    rate = float(cand["rate"])
    min_rate = float(band.get("min", 0))
    max_rate = float(band.get("max", 0))
    if min_rate <= rate <= max_rate:
        return "fit-scoring-rubric.md #6.1"
    if rate < min_rate:
        return "fit-scoring-rubric.md #6.4"
    if max_rate and rate <= max_rate * 1.10:
        return "fit-scoring-rubric.md #6.2"
    return "fit-scoring-rubric.md #6.3"


def seniority_rule(role_level, cand_level):
    try:
        diff = abs(_band_index(role_level) - _band_index(cand_level))
    except ValueError:
        return "fit-scoring-rubric.md #3.4"
    return {
        0: "fit-scoring-rubric.md #3.1",
        1: "fit-scoring-rubric.md #3.2",
        2: "fit-scoring-rubric.md #3.3",
    }.get(diff, "fit-scoring-rubric.md #3.4")


GENERIC_INDUSTRY_WORDS = frozenset({
    "company", "firm", "industry", "operation", "provider", "sector", "service",
})
INDUSTRY_STOP_WORDS = frozenset({"and", "of", "the"})
PARTIAL_INDUSTRY_CAP = 10       # role/candidate pairs named in one partial-match escalation


def _singular(word):
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _industry_tokens(text):
    """Industry words in order: '&' read as 'and', stop words dropped, simple plurals folded."""
    words = re.findall(r"[^\W_]+", text.casefold().replace("&", " and "))
    return [_singular(word) for word in words if word not in INDUSTRY_STOP_WORDS]


def _industry_key(tokens):
    return frozenset(tokens), "".join(tokens)


def _same_industry(left, right):
    # Equal word sets, or the same letters once spaces go ("health care" and "healthcare").
    return bool(left[1]) and (left[0] == right[0] or left[1] == right[1])


def _role_industry(role):
    practice = role.get("industry_context", "")
    if not isinstance(practice, str) or has_marker(practice):
        return [], []
    tokens = _industry_tokens(practice)
    return tokens, [token for token in tokens if token not in GENERIC_INDUSTRY_WORDS]


def industry_match(role, cand):
    """fit-scoring-rubric.md #1.6. Returns ("full", ()) when, ignoring generic qualifier words,
    the role's industry words equal a bench industry's ("healthcare provider" matches
    "healthcare"); ("partial", shared words) when they only share a word ("retail banking" and
    "retail"); otherwise (None, ()). A role worded only in generic words ("services") matches
    only the same generic words and is never a partial match."""
    tokens, core = _role_industry(role)
    if not tokens:
        return None, ()
    generic_only = not core
    practice = _industry_key(tokens if generic_only else core)
    shared = set()
    for industry in _usable(cand.get("industry_experience", [])):
        bench = _industry_tokens(industry)
        if not generic_only:
            bench = [token for token in bench if token not in GENERIC_INDUSTRY_WORDS]
        words = _industry_key(bench)
        if _same_industry(practice, words):
            return "full", ()
        if not generic_only:
            shared |= practice[0] & words[0]
    return ("partial", tuple(sorted(shared))) if shared else (None, ())


def industry_escalation(role, candidates):
    """The role-level rubric #1.6 escalation for one role, or None. Pure, so slate_validate can
    re-derive it from validated.json and recognise the engine's own industry note exactly."""
    partial_pairs = []
    any_full = False
    for cand in candidates:
        match, shared = industry_match(role, cand)
        if match == "full":
            any_full = True
        elif match == "partial":
            partial_pairs.append(f"{role['role_id']}/{cand['candidate_id']} shares '{' '.join(shared)}'")
    practice_tokens, practice_core = _role_industry(role)
    partial = ""
    if partial_pairs:
        listed = partial_pairs[:PARTIAL_INDUSTRY_CAP]
        more = len(partial_pairs) - len(listed)
        partial = ("partial industry match (fit-scoring-rubric.md #1.6 continuity scored 0; confirm): "
                   + "; ".join(listed) + (f"; and {more} more" if more else ""))
    if practice_tokens and not any_full:
        if not practice_core:
            return (f"{role['role_id']}: industry_context has only generic words and matched no "
                    "candidate's industry_experience - fit-scoring-rubric.md #1.6 continuity scored 0 for every "
                    "candidate; confirm the industry wording")
        if partial:
            return (f"{role['role_id']}: no full industry match - industry_context fully matched no "
                    f"candidate's industry_experience; {partial}")
        return (f"{role['role_id']}: industry_context matched no candidate's industry_experience - "
                "fit-scoring-rubric.md #1.6 continuity scored 0 for every candidate; confirm the industry wording")
    if partial:
        return f"{role['role_id']}: {partial}"
    return None


def continuity_score(role, cand):
    return 1.0 if industry_match(role, cand)[0] == "full" else 0.0


# ---------------------------------------------------------------------------------------------
# Pure engine.
# ---------------------------------------------------------------------------------------------
def score(roles_payload, bench_payload):
    """Validate, screen and score; returns the scored document. No file I/O."""
    validate_inputs(roles_payload, bench_payload)
    safety_escalations = ScreeningLog()
    roles_payload = sanitize_free_text(roles_payload, "roles_input", safety_escalations)
    bench_payload = sanitize_free_text(bench_payload, "bench_input", safety_escalations)
    candidates = bench_payload["bench_candidates"]
    screening_holds = [
        safety_escalations.holds_under(f"bench_input.bench_candidates[{index}]")
        for index in range(len(candidates))
    ]
    for candidate in candidates:
        if candidate.get("rate") is None:
            safety_escalations.append(
                f"{candidate['candidate_id']}: rate missing - "
                "rate-band component scored 0; confirm rate before scoring is relied on"
            )
    scored_roles = []
    for role in roles_payload["roles"]:
        candidate_scores = []
        for cand, holds in zip(candidates, screening_holds):
            availability = availability_context(role, cand)
            for warning in availability["calculation_warnings"]:
                safety_escalations.append(f"{role['role_id']}/{cand['candidate_id']}: {warning}")

            components = {
                "skills": round(skill_score(role, cand), 3),
                "seniority": round(seniority_score(role.get("seniority"), cand.get("seniority")), 3),
                "availability": availability["component_score"],
                "location_language": round(location_language_score(role, cand), 3),
                "rate_band": round(rate_score(role, cand), 3),
                "continuity": round(continuity_score(role, cand), 3)
            }
            total = (
                components["skills"] * WEIGHT_SKILLS +
                components["seniority"] * WEIGHT_SENIORITY +
                components["availability"] * WEIGHT_AVAILABILITY +
                components["location_language"] * WEIGHT_LOCATION_LANGUAGE +
                components["rate_band"] * WEIGHT_RATE +
                components["continuity"] * WEIGHT_CONTINUITY
            )
            candidate_scores.append({
                "candidate_id": cand["candidate_id"],
                "candidate_name": cand["name"],
                "fit_score": round(total * 100, 1),
                "component_scores": components,
                "component_citations": {
                    "skills": "fit-scoring-rubric.md #1.1,#2.1,#2.2,#2.3",
                    "seniority": seniority_rule(role.get("seniority"), cand.get("seniority")),
                    "availability": "fit-scoring-rubric.md #1.3,#4.1,#4.2,#4.3",
                    "location_language": "fit-scoring-rubric.md #1.4,#5.1,#5.2",
                    "rate_band": rate_rule(role, cand),
                    "continuity": "fit-scoring-rubric.md #1.6",
                },
                "availability_context": availability,
                "matched_required_skills": matched_requirements(
                    role.get("required_skills", []), cand.get("skills", [])
                ),
                "matched_preferred_skills": matched_requirements(
                    role.get("preferred_skills", []), cand.get("skills", [])
                ),
                "source": ENGINE,
                "confidence": min(float(role["confidence"]), float(cand["confidence"]), 0.99),
                "citation": "fit-scoring-rubric.md #7.3; " + safe_citation(cand["citation"]),
                "screening_holds": list(holds),
            })
        industry_note = industry_escalation(role, candidates)
        if industry_note:
            safety_escalations.append(industry_note)
        scored_roles.append({
            "role_id": role["role_id"],
            "role_title": role["title"],
            "candidate_scores": candidate_scores,
            "source": ENGINE,
            "confidence": min(float(role["confidence"]), 0.99),
            "citation": safe_citation(role["citation"]),
        })

    out = dict(roles_payload)
    out["bench_candidates"] = candidates
    out["scored_roles"] = scored_roles
    out["escalations"] = merge_unique(
        roles_payload.get("escalations", []),
        bench_payload.get("escalations", []),
        safety_escalations,
    )
    provenance = dict(roles_payload.get("provenance", {}))
    for key, value in bench_payload.get("provenance", {}).items():
        provenance.setdefault(key, value)
    engines = merge_unique(
        roles_payload.get("provenance", {}).get("engines", []),
        bench_payload.get("provenance", {}).get("engines", []),
    )
    provenance["engines"] = [
        engine for engine in engines if not engine.startswith("fit_score/")
    ] + [ENGINE_VERSION]
    provenance["policies"] = dict(POLICIES)
    out["provenance"] = provenance
    return out


def _main(argv):
    parser = ArgumentParser(prog="fit_score.py", description="Deterministic candidate fit scoring.")
    parser.add_argument("--roles", required=True)
    parser.add_argument("--bench", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    roles_payload = load_json(args.roles, "roles.json")
    bench_payload = load_json(args.bench, "bench.json")
    out = score(roles_payload, bench_payload)
    write_json(args.out, out)
    print(f"fit_score: {len(out['scored_roles'])} role(s), "
          f"{len(out['bench_candidates'])} candidate(s) -> scored output written")
    return 0


def main(argv=None):
    """CLI entry point: one clean ``error:`` line and exit 2 on any input error, no output file."""
    return run(lambda: _main(argv))


if __name__ == "__main__":
    sys.exit(main())
