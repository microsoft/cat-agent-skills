#!/usr/bin/env python3
"""gate_check - deterministic quality-gate compliance engine."""
import copy
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import assertion_rules as rules  # noqa: E402  byte-identical copy of the assertion-map skill's canonical assertion_rules.py
import steering_guard as sg  # noqa: E402  vendored shared detector; never edit (tests/check_shared_copies.py pins its SHA-256)

ENGINE = "engine:gate_check"
ENGINE_VERSION = "1.0.9"
LEDGER_TAG = f"gate_check/{ENGINE_VERSION}"
CONTRACT_VERSION = "ps.deliverable-review-quality-gate.v1"
RELIANCE_RESTRICTION_REQUIRED_FOR_THIRD_PARTY = True  # quality-gate-criteria.md #2.2
DISCLAIMER_TYPES = {"general_advice", "reliance_restriction"}  # quality-gate-criteria.md #2.4: anything else holds
CONFIDENTIALITY_MARK_REQUIRED = True  # quality-gate-criteria.md #4.1
CLIENT_DATA_CLEAN_VALUE = "ok"  # quality-gate-criteria.md #4.3: the only clean client_data_handling value
LEGAL_MARK_DEFECT_BLOCKS = True  # quality-gate-criteria.md #5.2
BRAND_CHECK_STATUSES = {"pass", "fail"}  # quality-gate-criteria.md #5.3: anything else is "not verified" and holds
LICENSED_ATTRIBUTION_REQUIRED = True  # quality-gate-criteria.md #6.1
LICENSE_STATUS_KNOWN = "known"  # quality-gate-criteria.md #6.3: closed enum known/unknown; anything else is unknown
PRIOR_FIX_MUST_LAND = True  # quality-gate-criteria.md #7.1-#7.2
EMBEDDED_INSTRUCTION_HOLD = True  # quality-gate-criteria.md #8.1-#8.3
MAX_G8_HITS = 5
RELEASE_BLOCKER = "release_blocker"  # severity-rules.md #1.1
MUST_FIX = "must_fix"  # severity-rules.md #1.2
ADVISORY = "advisory"  # severity-rules.md #1.3
SEVERITY_RANK = {ADVISORY: 1, MUST_FIX: 2, RELEASE_BLOCKER: 3}
VALID_SEVERITIES = set(SEVERITY_RANK)
# quality-gate-criteria.md #8.4: finding-ID prefixes and source tags only the engines may emit.
SR_ENGINE = "engine:severity_rank"
GATES = {"G1": "Evidence support and substantiation", "G2": "Required disclaimer, limitation and reliance language", "G3": "Scope-of-work alignment", "G4": "Confidentiality marking and client-data handling", "G5": "Brand and formatting standards", "G6": "Third-party and licensed content attribution", "G7": "Prior-findings closure", "G8": "Data-as-data and embedded-instruction handling"}
# Recipient classification (quality-gate-criteria.md #2.5): client-only requires a positive client-name match.
EXTERNAL_RECIPIENT_PATTERN = re.compile(r"\b(?:" + "|".join((
    r"counsel", r"lawyers?", r"solicitors?", r"attorneys?", r"law firms?", r"lenders?", r"lending", r"banks?", r"bankers?",
    r"financiers?", r"creditors?", r"bondholders?", r"noteholders?", r"investors?", r"shareholders?", r"private equity",
    r"regulators?", r"regulatory", r"auditors?", r"external audit", r"buyers?", r"bidders?", r"acquirers?", r"purchasers?",
    r"vendors?", r"suppliers?", r"insurers?", r"underwriters?", r"rating agenc(?:y|ies)", r"trustees?", r"brokers?",
    r"arrangers?", r"counterpart(?:y|ies)", r"consultants?", r"advisers?", r"advisors?", r"outside", r"external",
    r"third party", r"third parties", r"independent", r"public", r"press", r"media", r"government",
)) + r")\b")
CLIENT_ROLE_PHRASES = ("general counsel", "in house counsel", "in house legal", "internal audit", "audit committee")
CLIENT_ROLE_WORDS = {
    "s", "the", "of", "and", "&", "for", "management", "manager", "managers", "board", "directors", "director",
    "executive", "executives", "leadership", "committee", "steering", "sponsor", "sponsors", "team", "teams", "office",
    "pmo", "programme", "program", "project", "cfo", "ceo", "coo", "cio", "cto", "cro", "chro", "chief", "officer",
    "officers", "finance", "operations", "procurement", "hr", "people", "it", "technology", "digital", "strategy", "legal",
    "risk", "compliance", "head", "heads", "function", "department", "division", "unit", "owner", "owners", "staff",
    "members", "chair", "president", "vp", "vice", "senior", "group",
}
INTERNAL_RECIPIENTS = {"engagement team", "engagement partner", "engagement manager", "reviewing partner", "engagement quality reviewer", "qrm"}
AMBIGUOUS_RECIPIENT_TERMS = ("tbd", "to be confirmed", "external parties", "third parties", "stakeholders", "interested parties", "advisors", "advisers", "allowed users", "distribution list")

# Look-alike folding and the canonical comparison forms live in assertion_rules (quality-gate-criteria.md #8.11).
CONFUSABLE_MAP = rules.CONFUSABLE_MAP
CONFUSABLES = rules.CONFUSABLES
# G8 embedded-instruction screening and withholding (quality-gate-criteria.md #8.1-#8.7) is shared by every stage and
# lives in assertion_rules (byte-identical in both skills); these names are kept for callers and tests.
STEERING_HOOKS = rules.STEERING_HOOKS
OVERSIZE = rules.OVERSIZE
PRIMARY_SECTIONS = rules.PRIMARY_SECTIONS
UNSCANNED_KEYS = rules.UNSCANNED_KEYS
AGGREGATE_LABEL = rules.AGGREGATE_LABEL
screen_text = rules.screen_text
screen_fields = rules.screen_fields
suspicious_instruction = rules.suspicious_instruction
safe_token = rules.safe_token
iter_strings = rules.iter_strings
collect_scan_text = rules.collect_scan_text
assertion_fields = rules.assertion_fields
instruction_hits = rules.instruction_hits

InputError = rules.InputError

def load_json(path):
    return rules.load_json_file(path, "mapped input")

validate_generated_at = rules.validate_generated_at

def require_contract(payload):
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise InputError(f"expected contract {CONTRACT_VERSION}, got {rules.describe(payload.get('contract_version'))}")
    if not isinstance(payload.get("deliverable"), dict):
        raise InputError("missing required object: deliverable")
    for key in ("assertions", "assertion_mappings", "findings", "escalations"):
        if key in payload and not isinstance(payload[key], list):
            raise InputError(f"{key} must be an array")
    if "assertion_mappings" not in payload:
        raise InputError("assertion_mappings missing: run assertion_map.py first; gate_check runs on assertion_map output only")
    if payload.get("criteria") is not None and not isinstance(payload["criteria"], dict):
        raise InputError("criteria must be an object when supplied (absent or null means the criteria register was not loaded)")
    for index, entry in enumerate(payload.get("escalations", [])):
        if not isinstance(entry, (str, dict)):
            raise InputError(f"escalations[{index}] must be a string or object, got {rules.describe(entry)}")
    rules.validate_assertions(payload.get("assertions"))

def normalize_text(value):
    """Comparison form of a name or label: rules.canonical_name (one canonical function, quality-gate-criteria.md #8.11)."""
    return rules.canonical_name(value)

def loc(section, page, paragraph, label):
    return {"section": section, "page": page, "paragraph": paragraph, "label": label}

def unplaced(section, label):
    """Register- or field-level location: no page or paragraph applies, so none is invented."""
    return {"section": section, "page": None, "paragraph": None, "label": label}

def engine_finding(finding_id, gate_id, severity, title, detail, location, criteria_section, confidence, citation):
    """One gate_check finding, every field set by the engine."""
    if severity not in VALID_SEVERITIES:
        raise InputError(f"an engine finding has an unknown severity ({rules.describe(severity)})")
    return {"finding_id": finding_id, "gate_id": gate_id, "severity": severity, "title": title, "detail": detail, "location": location, "criteria_section": criteria_section, "confidence": confidence, "source": ENGINE, "citation": citation}

def add_finding(findings, finding_id, gate_id, severity, title, detail, location, criteria_section, confidence, citation):
    add_built_finding(findings, engine_finding(finding_id, gate_id, severity, title, detail, location, criteria_section, confidence, citation))

def add_built_finding(findings, finding):
    finding_id, severity = finding["finding_id"], finding["severity"]
    for index, existing in enumerate(findings):
        if rules.canonical_id(existing.get("finding_id", "")) == rules.canonical_id(finding_id):
            # De-duplication may raise severity but never lowers it (quality-gate-criteria.md #8.4).
            if SEVERITY_RANK[severity] > SEVERITY_RANK.get(existing.get("severity"), 0):
                findings[index] = finding
            return
    findings.append(finding)

def validate_upstream_finding(item, index):
    if not isinstance(item, dict):
        raise InputError(f"findings[{index}] must be an object")
    label = f"findings[{index}]"
    rules.require_text(item, "finding_id", label)
    if item.get("severity") not in VALID_SEVERITIES:
        raise InputError(f"{label}: unknown severity ({rules.describe(item.get('severity'))}); severity must be one of {', '.join(sorted(VALID_SEVERITIES))}")
    if item.get("gate_id") not in GATES:
        raise InputError(f"{label}: gate_id must be one of {', '.join(GATES)}, got {rules.describe(item.get('gate_id'))}")
    for key in ("title", "detail", "criteria_section", "source", "citation"):
        rules.require_text(item, key, label, required=False, allow_blank=True)
    rules.require_confidence(item, label)
    rules.validate_location(item.get("location"), label, required=False)

def expected_assertion_outputs(payload, evidence_set):
    """Recompute assertion_map output from the carried assertions and evidence index. A null or absent index links
    nothing, so every claim is recomputed as unsupported: carried mappings and AM- findings are never trusted unverified,
    and the G1 register-missing blocker also holds (quality-gate-criteria.md #8.16)."""
    evidence_by_id = rules.evidence_index(evidence_set if evidence_set is not None else [])
    subject = rules.review_subject(payload)
    mappings, findings, escalations = [], {}, []
    for assertion in payload["assertions"]:
        mapping, finding, escalation = rules.map_assertion(assertion, evidence_by_id, subject)
        mappings.append(mapping)
        if finding:
            findings[finding["finding_id"]] = finding
            escalations.append(escalation)
    return {"mappings": mappings, "findings": findings, "escalations": escalations}

def genuine_am_finding(item, expected_am):
    """True when an AM- finding is exactly what assertion_map emits for the current assertions and evidence
    (`expected_am`, keyed by finding ID), exactly assertion_map's fixed spoof hold (rules.am_spoof_finding), or exactly
    one of its fixed foreign-entry holds (rules.am_foreign_hold_for), each of which can only hold the run
    (quality-gate-criteria.md #8.4, #8.15)."""
    if rules.is_am_spoof_id(item.get("finding_id")):
        return item == rules.am_spoof_finding()
    foreign_hold = rules.am_foreign_hold_for(item.get("finding_id"))
    if foreign_hold is not None:
        return item == foreign_hold
    return expected_am is not None and expected_am.get(item.get("finding_id")) == item

def screen_upstream_findings(upstream, expected, raw_upstream=None):
    """Keep legitimate upstream findings; drop any engine-owned finding that engine recomputation does not reproduce.

    An engine-owned finding stands only when the engine's own recomputation reproduces it exactly. An AM- finding is kept
    only when it is byte-for-byte what assertion_map emits for the current assertions and evidence (`expected`), or
    assertion_map's fixed spoof hold (genuine_am_finding); of two copies sharing an ID only the genuine one stands. A GC-
    finding is returned in `claimed` and checked at the end of the run against what gate_check computes
    (`check_claimed_findings`), so re-running gate_check on its own output reproduces it. SR- findings cannot precede
    severity_rank, and any other finding carrying an engine source tag is spoofed; a self-declared source tag proves
    nothing. Ownership is read from `raw_upstream` (the same findings before withholding), so a flagged ID such as
    `GC-<instruction>` is both withheld and still engine-owned, and compared in canonical form (rules.engine_id_owner,
    rules.canonical_tag), so `gc_G8-x` or `Engine :gate_check` cannot pass as a reviewer finding. Returns (kept,
    spoofed labels, claimed (label, finding) pairs) (quality-gate-criteria.md #8.4, #8.11)."""
    kept, spoofed, claimed = [], [], []
    expected_am = expected["findings"] if expected else None
    raw_upstream = upstream if raw_upstream is None else raw_upstream
    for index, item in enumerate(upstream):
        validate_upstream_finding(item, index)
        raw = raw_upstream[index] if index < len(raw_upstream) and isinstance(raw_upstream[index], dict) else item
        owner = rules.engine_id_owner(raw.get("finding_id"))
        source = rules.canonical_tag(raw.get("source")) or ""
        label = safe_token(item["finding_id"], f"findings[{index}]")
        if owner == ENGINE:
            claimed.append((label, item))
            continue
        if (owner is not None and owner != rules.AM_ENGINE) or source in (rules.canonical_tag(ENGINE), rules.canonical_tag(SR_ENGINE)):
            spoofed.append(label)
            continue
        if owner == rules.AM_ENGINE:
            if not genuine_am_finding(item, expected_am):
                spoofed.append(label)
            elif not any(rules.canonical_id(kept_item["finding_id"]) == rules.canonical_id(item["finding_id"]) for kept_item in kept):
                kept.append(item)
            continue
        if rules.is_engine_tag(raw.get("source")):
            spoofed.append(label)
            continue
        duplicate = next((i for i, kept_item in enumerate(kept) if rules.canonical_id(kept_item["finding_id"]) == rules.canonical_id(item["finding_id"])), None)
        if duplicate is None:
            kept.append(item)
        elif SEVERITY_RANK[item["severity"]] > SEVERITY_RANK[kept[duplicate]["severity"]]:
            kept[duplicate] = item
    return kept, spoofed, claimed

def check_claimed_findings(claimed, findings):
    """Labels of upstream GC- findings that this run's computation does not reproduce exactly (same ID and every field
    equal). A reproduced claim is already present as the engine's own finding; any other is spoofed (#8.4)."""
    computed = {rules.canonical_id(item["finding_id"]): item for item in findings}
    return [label for label, item in claimed if computed.get(rules.canonical_id(item["finding_id"])) != item]

def claim_finding_id(findings, owners, base, owner):
    """A finding ID unique to one register entry, required-language item or assertion (quality-gate-criteria.md #8.4).

    `base` comes from safe_token, which falls back to a fixed or indexed label for long, unsafe or flagged values, so
    two distinct items could otherwise share an ID and add_finding would merge them. The same owner always gets the
    same ID; a different owner, or an ID already used by another finding, gets the first free `-2`, `-3`, ... suffix.
    IDs are compared in canonical form, so two findings never differ only in case or separators (#8.11)."""
    taken = {rules.canonical_id(item["finding_id"]) for item in findings}
    candidate, suffix = base, 2
    while owners.get(rules.canonical_id(candidate), owner if rules.canonical_id(candidate) not in taken else None) != owner:
        candidate = f"{base}-{suffix}"
        suffix += 1
    owners[rules.canonical_id(candidate)] = owner
    return candidate

def reconcile_assertion_outputs(payload, expected, kept, escalations):
    """Restore assertion_map output that was removed or altered upstream. Returns the assertion IDs that differed.

    The carried mappings are compared with the recomputed ones item by item, every key and ID included, never by
    count: each recomputed mapping must be carried exactly, and the carried list must equal the recomputed list, so
    an extra, repeated or reordered entry, or a one-field edit to an ID, is restored and held (quality-gate-criteria.md
    #8.19). Mappings are matched by canonical assertion ID (rules.key_of), so a variant spelling is a difference."""
    if expected is None:
        return []
    provided = {}
    for item in payload["assertion_mappings"]:
        key = rules.key_of(item.get("assertion_id")) if isinstance(item, dict) else None
        if key is not None:
            provided.setdefault(key, item)
    altered = [m["assertion_id"] for m in expected["mappings"] if provided.get(rules.key_of(m["assertion_id"])) != m]
    if payload["assertion_mappings"] != expected["mappings"] and not altered:
        altered.append("assertion_mappings")
    payload["assertion_mappings"] = expected["mappings"]
    present = {rules.canonical_id(item["finding_id"]) for item in kept}
    for finding_id, finding in expected["findings"].items():
        if rules.canonical_id(finding_id) not in present:
            kept.append(finding)
            altered.append(finding["finding_id"][len("AM-"):])
    for escalation in expected["escalations"]:
        if escalation not in escalations:
            escalations.append(escalation)
    return [safe_token(item, "assertion") for item in dict.fromkeys(altered)]

def highest_for_gate(findings, gate_id):
    gated = [item for item in findings if item.get("gate_id") == gate_id]
    return "none" if not gated else max((item["severity"] for item in gated), key=lambda sev: SEVERITY_RANK[sev])

def recipients_of(deliverable):
    recipients = deliverable.get("intended_recipients")
    return recipients if isinstance(recipients, list) else []

def recipient_words(value):
    return " ".join(re.sub(r"[^a-z0-9&]+", " ", normalize_text(value)).split())

def contains_phrase(text, phrase):
    return bool(phrase) and re.search(r"(?:^|\s)" + re.escape(phrase) + r"(?=\s|$)", text) is not None

def strip_role_phrases(text):
    for phrase in CLIENT_ROLE_PHRASES:
        text = re.sub(r"(?:^|\s)" + re.escape(phrase) + r"(?=\s|$)", " ", text)
    return " ".join(text.split())

def has_external_vocabulary(text):
    return EXTERNAL_RECIPIENT_PATTERN.search(strip_role_phrases(text)) is not None

def client_identity_entries(deliverable):
    """Yield (label, raw value, normalised phrase) for client_name and every client_aliases entry. A withheld name or
    alias never identifies the client (quality-gate-criteria.md #8.13)."""
    entries = []
    if isinstance(deliverable.get("client_name"), str):
        entries.append(("client_name", deliverable["client_name"], recipient_words(deliverable["client_name"])))
    for index, alias in enumerate(string_list(deliverable, "client_aliases", "deliverable.client_aliases")):
        entries.append((f"client_aliases[{index}]", alias, recipient_words(alias)))
    return [entry for entry in entries if len(entry[2]) >= 3 and not rules.contains_withheld(entry[1])]

def client_identities(deliverable):
    """Client names usable for positive matching. A name or alias containing external-party vocabulary is never
    trusted (quality-gate-criteria.md #2.5): it could otherwise relabel a lender or counsel as the client."""
    return [phrase for _, _, phrase in client_identity_entries(deliverable) if not has_external_vocabulary(phrase)]

def invalid_client_identities(deliverable):
    """Field paths (never the text) of the client name and aliases that carry external-party vocabulary (#2.5, #8.9)."""
    return [f"deliverable.{label}" for label, value, phrase in client_identity_entries(deliverable) if has_external_vocabulary(phrase)]

def classify_recipient(recipient, identities):
    """Return client, internal, external or unclassified (quality-gate-criteria.md #2.5).

    External-party vocabulary is checked first, on the full recipient text (only the engine's fixed client-role
    phrases such as "general counsel" are exempt); a client name or alias never neutralises it. A recipient is
    client-only only when it positively names a trusted client identity and every remaining word is a client role
    word. Anything else is unclassified; nothing is inferred from the absence of a keyword. A recipient the
    embedded-instruction screen withheld (quality-gate-criteria.md #8.7) cannot be read or confirmed, and look-alike
    characters may hide external vocabulary, so it is treated as external."""
    if rules.contains_withheld(recipient):
        return "external"
    text = recipient_words(recipient)
    if text in INTERNAL_RECIPIENTS:
        return "internal"
    if has_external_vocabulary(text):
        return "external"
    matched = False
    for phrase in sorted(identities, key=len, reverse=True):
        if contains_phrase(text, phrase):
            matched = True
            text = re.sub(r"(?:^|\s)" + re.escape(phrase) + r"(?=\s|$)", " ", text)
    text = strip_role_phrases(text)
    if matched and all(word in CLIENT_ROLE_WORDS for word in text.split()):
        return "client"
    return "unclassified"

def recipient_classes(deliverable):
    """Recipients by class, each named by its field path, never its text: a recipient names a party (#2.5, #8.9)."""
    identities = client_identities(deliverable)
    classes = {"client": [], "internal": [], "external": [], "unclassified": []}
    for index, recipient in enumerate(recipients_of(deliverable)):
        if recipient.strip():
            classes[classify_recipient(recipient, identities)].append(f"deliverable.intended_recipients[{index}]")
    return classes

def is_third_party_context(deliverable):
    return deliverable.get("third_party_recipient_named") is True or bool(recipient_classes(deliverable)["external"])

def recipient_list_problem(deliverable):
    recipients = deliverable.get("intended_recipients")
    if recipients is None:
        return "recipient list is missing"
    if not recipients:
        return "recipient list is empty"
    if any(not item.strip() for item in recipients):
        return "recipient list contains a blank entry"
    joined = " | ".join(rules.canonical_name(item) for item in recipients if not rules.contains_withheld(item))
    if any(rules.canonical_name(term) in joined for term in AMBIGUOUS_RECIPIENT_TERMS):
        return "recipient list is ambiguous"
    return None

def string_list(container, key, label):
    """Optional list of strings: absent or null -> [], wrong type -> InputError."""
    value = container.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError(f"{label} must be an array when present")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise InputError(f"{label}[{index}] must be a string, got {rules.describe(item)}")
    return value

def validate_deliverable(deliverable):
    """Type-check every deliverable field a gate reads. Wrong JSON types are input errors; enum values are judged by the gates."""
    if deliverable.get("intended_recipients") is not None:
        string_list(deliverable, "intended_recipients", "deliverable.intended_recipients")
    # Required: the declared flag is cross-checked against the classified recipients (quality-gate-criteria.md #2.5).
    rules.require_boolean(deliverable, "third_party_recipient_named", "deliverable")
    for key in ("required_disclaimer_type", "confidentiality_marking", "client_data_handling", "client_name"):
        rules.require_text(deliverable, key, "deliverable", required=False, allow_blank=True)
    for key in ("present_disclaimer_types", "present_language", "client_aliases"):
        string_list(deliverable, key, f"deliverable.{key}")

def require_unique_ids(items, label, id_key):
    rules.require_unique_ids(items, label, id_key)

def require_entry_basics(item, label, id_key):
    if not isinstance(item, dict):
        raise InputError(f"{label} must be an object")
    rules.require_text(item, id_key, label)
    for key in ("title", "detail", "citation", "source"):
        rules.require_text(item, key, label, required=False, allow_blank=True)
    rules.require_confidence(item, label)
    rules.validate_location(item.get("location"), label, required=False)

def validate_brand_checks(items):
    for index, item in enumerate(items):
        label = f"deliverable.brand_checks[{index}]"
        require_entry_basics(item, label, "check_id")
        rules.require_text(item, "status", label, required=False, allow_blank=True)
        rules.require_boolean(item, "legal_or_release_control", label)
    require_unique_ids(items, "deliverable.brand_checks", "check_id")

def validate_licensed_content(items):
    for index, item in enumerate(items):
        label = f"deliverable.licensed_content[{index}]"
        require_entry_basics(item, label, "content_id")
        rules.require_boolean(item, "attribution_present", label)
        rules.require_text(item, "license_status", label, required=False, allow_blank=True)
    require_unique_ids(items, "deliverable.licensed_content", "content_id")

def validate_prior_findings(items):
    for index, item in enumerate(items):
        label = f"prior_findings[{index}]"
        require_entry_basics(item, label, "finding_id")
        rules.require_boolean(item, "claimed_closed", label)
        rules.require_boolean(item, "document_fix_present", label)
    require_unique_ids(items, "prior_findings", "finding_id")

def entry_location(item, section, label):
    return item.get("location") or unplaced(section, label)

def register(container, key, label):
    """Return the register list, or None when it was not loaded (absent or null). Missing is not empty."""
    if not isinstance(container, dict) or container.get(key) is None:
        return None
    if not isinstance(container[key], list):
        raise InputError(f"{label} must be an array when supplied (absent or null means the register was not loaded)")
    return container[key]

def find_prior_location(payload, *terms):
    """The location of the first prior finding whose readable text names every term; withheld text is not read (#8.13)."""
    priors = payload.get("prior_findings")
    folded_terms = tuple(rules.canonical_name(term) for term in terms)
    subject = rules.review_subject(payload)
    for prior in priors if isinstance(priors, list) else []:
        # An excluded prior finding (withheld ID, or another engagement or deliverable) is never a basis, not even for a
        # location (#8.13, #8.15, #8.17).
        if not isinstance(prior, dict) or not isinstance(prior.get("location"), dict) or excluded_entry(prior, subject, "finding_id"):
            continue
        location = prior["location"]
        values = (prior.get("finding_id", ""), prior.get("detail", ""), prior.get("citation", ""), location.get("section", ""), location.get("label", ""))
        haystack = rules.canonical_name(" ".join(value for value in values if isinstance(value, str) and not rules.contains_withheld(value)))
        if all(term in haystack for term in folded_terms):
            return location
    return None

def disclaimer_location(payload):
    return (
        find_prior_location(payload, "disclaimer")
        or find_prior_location(payload, "reliance")
        or unplaced("Disclaimer", "Disclaimer block (page not supplied in the review input)")
    )

def item_location(items, index):
    if isinstance(items, list) and index < len(items) and isinstance(items[index], dict) and isinstance(items[index].get("location"), dict):
        return items[index]["location"]
    return None

def location_for_scan_path(payload, path):
    deliverable = payload.get("deliverable") or {}
    indexed = (
        (r"^\$\.assertions\[(\d+)\]", payload.get("assertions")),
        (r"^\$\.prior_findings\[(\d+)\]", payload.get("prior_findings")),
        (r"^\$\.assertion_mappings\[(\d+)\]", payload.get("assertion_mappings")),
        (r"^\$\.findings\[(\d+)\]", payload.get("findings")),
        (r"^\$\.deliverable\.brand_checks\[(\d+)\]", deliverable.get("brand_checks")),
        (r"^\$\.deliverable\.licensed_content\[(\d+)\]", deliverable.get("licensed_content")),
    )
    for pattern, items in indexed:
        match = re.match(pattern, path)
        if match:
            found = item_location(items, int(match.group(1)))
            if found:
                return found
            break
    match = re.match(r"^\$\.evidence_set\[(\d+)\]", path)
    if match:
        return unplaced("Evidence index", f"Evidence item {int(match.group(1)) + 1} (evidence_set[{match.group(1)}])")
    if path.startswith("$.deliverable"):
        return disclaimer_location(payload) if "disclaimer" in path or "language" in path else unplaced("Deliverable metadata", "Deliverable field")
    if path.startswith("$.criteria"):
        return unplaced("Criteria register", "Criteria extract field")
    return unplaced("Review input", "Supplied field outside the deliverable body")

def check_missing_registers(payload, deliverable, findings, escalations):
    criteria = payload.get("criteria")
    registers = (
        (criteria, "criteria_sections", "criteria.criteria_sections", "GC-G1-criteria-register-missing", "G1", RELEASE_BLOCKER, "Criteria register is missing", "The applicable criteria list is absent or null, so the gate cannot be treated as having no findings.", "Criteria register", "quality-gate-criteria.md #1-#8; severity-rules.md #1.1", "quality-gate-criteria.md #1-#8; severity-rules.md #1.1"),
        (payload, "evidence_set", "evidence_set", "GC-G1-evidence-index-missing", "G1", RELEASE_BLOCKER, "Evidence index is missing", "The evidence index is absent or null, so assertions cannot be treated as supported.", "Evidence index", "quality-gate-criteria.md #1.1", "quality-gate-criteria.md #1.1; severity-rules.md #1.1"),
        (deliverable, "client_data_handling", None, "GC-G4-client-data-register-missing", "G4", RELEASE_BLOCKER, "Client-data handling register is missing", "Client data handling is absent or null; missing is not the same as a clean data-handling assessment.", "Client-data handling register", "quality-gate-criteria.md #4.2-#4.3", "quality-gate-criteria.md #4.2-#4.3; severity-rules.md #1.1"),
        (deliverable, "brand_checks", "deliverable.brand_checks", "GC-G5-brand-register-missing", "G5", MUST_FIX, "Brand-check register is missing", "Brand and release-control checks are absent or null; missing is not the same as no brand findings.", "Brand-check register", "quality-gate-criteria.md #5.1-#5.2", "quality-gate-criteria.md #5.1-#5.2; severity-rules.md #1.2"),
        (deliverable, "licensed_content", "deliverable.licensed_content", "GC-G6-licensed-content-register-missing", "G6", MUST_FIX, "Licensed-content register is missing", "Licensed and third-party content checks are absent or null; missing is not the same as no licensed-content findings.", "Licensed-content register", "quality-gate-criteria.md #6.1-#6.2", "quality-gate-criteria.md #6.1-#6.2; severity-rules.md #1.2"),
        (payload, "prior_findings", "prior_findings", "GC-G7-prior-findings-register-missing", "G7", MUST_FIX, "Prior-findings register is missing", "Prior-review closure cannot be verified when the prior-findings register is absent or null.", "Prior findings register", "quality-gate-criteria.md #7.1-#7.2", "quality-gate-criteria.md #7.1-#7.2; severity-rules.md #1.2"),
        (deliverable, "required_language", "deliverable.required_language", "GC-G2-required-language-register-missing", "G2", RELEASE_BLOCKER, "Required-language register is missing", "The required-language list is absent or null; missing is not the same as explicitly empty.", "Required-language register", "quality-gate-criteria.md #2.1-#2.3", "quality-gate-criteria.md #2.1-#2.3; severity-rules.md #1.1"),
    )
    loaded = {}
    for container, key, label, finding_id, gate_id, severity, title, detail, section, criteria_section, citation in registers:
        value = container.get(key) if isinstance(container, dict) else None
        if value is None:
            add_finding(findings, finding_id, gate_id, severity, title, detail, unplaced(section, "Register not supplied (absent or null)"), criteria_section, 0.99, citation)
            escalations.append(f"{gate_id}: {section.lower()} not supplied (absent or null) - {severity}; hold for reviewing partner/QRM, missing is not empty ({criteria_section})")
        elif label:
            loaded[key] = register(container, key, label)
    return loaded

def check_client_data_value(deliverable, findings, escalations):
    value = deliverable.get("client_data_handling")
    if value is None or value == CLIENT_DATA_CLEAN_VALUE:
        return
    if value == "attention":
        severity, title, detail = MUST_FIX, "Client-data handling needs attention", "The client-data register records `attention`; only `ok` is clean, so the extract must be corrected or confirmed before release."
    elif value == "breach":
        severity, title, detail = RELEASE_BLOCKER, "Client-data handling breach recorded", "The client-data register records `breach`."
    elif value == "unknown":
        severity, title, detail = RELEASE_BLOCKER, "Client-data handling cannot be confirmed", "The client-data register records `unknown`; safe handling cannot be confirmed."
    else:
        severity, title, detail = RELEASE_BLOCKER, "Client-data handling value is not recognised", "client_data_handling is blank or not one of ok, attention, breach or unknown; an unrecognised value is never treated as clean."
    add_finding(findings, "GC-G4-client-data", "G4", severity, title, detail, unplaced("Client-data handling register", "client_data_handling"), "quality-gate-criteria.md #4.2-#4.3", 0.95, "quality-gate-criteria.md #4.2-#4.3")
    shown = value if value in {"attention", "breach", "unknown"} else "blank/unrecognised"
    escalations.append(f"G4: client_data_handling is {shown}, not ok - {severity}; hold for reviewing partner/QRM (quality-gate-criteria.md #4.2-#4.3)")

def excluded_entry(item, subject, id_key):
    """True when a register entry is excluded from every decision: its ID was withheld by the embedded-instruction
    screen (#8.13), or it names another engagement or deliverable (#8.15). Every section that reads the entry uses this
    one predicate (#8.17)."""
    return rules.contains_withheld(item.get(id_key)) or bool(rules.foreign_subject(item, subject))

def foreign_entry_hold(findings, escalations, owners, item, subject, index, gate_id, kind, register_name, register_key, section, id_key):
    """Hold an excluded register entry instead of judging it: one whose ID the embedded-instruction screen withheld
    (#8.13) or that names another engagement or deliverable (#8.15). It is never a basis for its gate, so a pass, an
    attribution or a closure it records counts for nothing. A foreign entry is named by position only (its finding ID,
    location, detail and escalation): assertion_map has already replaced it by its stand-in, and no supplied ID, title,
    detail or location of it is shown, even one that looks like a valid identifier. Returns True when held."""
    fallback = f"{REGISTER_PATHS[register_key][1]}-{index + 1}"
    owner = (register_key, index)
    if rules.contains_withheld(item.get(id_key)):
        entry_id = safe_token(item[id_key], fallback)
        finding_id = claim_finding_id(findings, owners, f"GC-{gate_id}-{entry_id}", owner)
        location = entry_location(item, register_name, f"{REGISTER_PATHS[register_key][2]} {entry_id}")
        add_finding(findings, finding_id, gate_id, RELEASE_BLOCKER, f"{kind} identifier was withheld", f"{kind} {entry_id} has an identifier the embedded-instruction screen withheld, so the entry cannot be verified and is not used as a basis for this gate; the reviewing partner/QRM must confirm or remove it before release.", location, f"{section}; quality-gate-criteria.md #8.13", 0.97, f"{section}; quality-gate-criteria.md #8.13, #8.17; severity-rules.md #1.1")
        escalations.append(f"{gate_id}: {kind.lower()} {entry_id} has a withheld identifier and is not used - release blocker; hold for reviewing partner/QRM (quality-gate-criteria.md #8.13)")
        return True
    fields = rules.foreign_subject(item, subject)
    if not fields:
        return False
    named = " and ".join(fields)
    where = f"{kind} {index + 1} ({REGISTER_PATHS[register_key][0]}[{index}])"
    finding_id = claim_finding_id(findings, owners, f"GC-{gate_id}-{fallback}", owner)
    add_finding(findings, finding_id, gate_id, RELEASE_BLOCKER, f"{kind} belongs to another engagement or deliverable", f"{where} gives a {named} that differs from this review's (or cannot be verified), so it is not used as a basis for this gate and its identifier and contents are not shown; the reviewing partner/QRM must confirm or remove it before release.", unplaced(register_name, where), f"{section}; quality-gate-criteria.md #8.15", 0.97, f"{section}; quality-gate-criteria.md #8.15; severity-rules.md #1.1")
    escalations.append(f"{gate_id}: {where[0].lower()}{where[1:]} names another engagement or deliverable ({named}) - release blocker; hold for reviewing partner/QRM (quality-gate-criteria.md #8.15)")
    return True

# Each register a foreign entry can sit in: its field path, the positional slug of its finding IDs and the label of a
# withheld-ID entry's register location.
REGISTER_PATHS = {"brand_checks": ("deliverable.brand_checks", "brand-check", "Brand check"), "licensed_content": ("deliverable.licensed_content", "licensed-content", "Licensed content"), "prior_findings": ("prior_findings", "prior-finding", "Prior finding")}

def placeholder_hits(payload, raw, expected, own_escalations, hits):
    """A G8 hit for each withheld placeholder in a position gate_check does not recompute (a reviewer finding, a carried
    escalation no engine derived, provenance or another note) unless this run already holds that exact path
    (quality-gate-criteria.md #8.18). Engine findings are recomputed or removed as spoofs, and engine escalations are
    re-derived, so their placeholders are bound by recomputation. A hold on another path never binds one."""
    raw_findings = raw.get("findings") if isinstance(raw.get("findings"), list) else []

    def engine_finding(index, item):
        source = raw_findings[index] if index < len(raw_findings) and isinstance(raw_findings[index], dict) else item
        return rules.engine_id_owner(source.get("finding_id")) is not None or rules.is_engine_tag(source.get("source"))

    derived = list(expected["escalations"]) + list(own_escalations)
    held = {path for path, _ in hits}
    paths = rules.placeholder_paths(payload, engine_finding, lambda entry: entry in derived)
    return rules.unbound_placeholder_hits(paths, lambda path: path in held)

SPOOF_ID = "GC-G8-engine-id-spoof"

def spoof_finding(spoofed_count, altered_count):
    """gate_check's fixed spoof hold; only the two counts vary (severity_rank rebuilds it to compare every field)."""
    parts = []
    if spoofed_count:
        parts.append(f"{spoofed_count} upstream finding(s) used an engine-owned finding ID or engine source tag without matching engine recomputation and were ignored")
    if altered_count:
        parts.append(f"assertion_map output for {altered_count} assertion(s) was missing or did not match recomputation and was restored")
    return engine_finding(SPOOF_ID, "G8", RELEASE_BLOCKER, "Upstream engine output is spoofed or altered", "; ".join(parts) + ". Engine findings are recomputed and cannot be replaced, removed or downgraded by input data.", unplaced("Upstream findings", "findings[] / assertion_mappings supplied with the review input"), "quality-gate-criteria.md #8.1; quality-gate-criteria.md #8.4", 0.99, "quality-gate-criteria.md #8.1, #8.4; severity-rules.md #1.1")

def g8_hit_finding(hit_index, path, hit_reason, payload):
    """gate_check's G8 hold for one embedded-instruction hit; severity_rank rebuilds it to compare every field."""
    if hit_reason == OVERSIZE:
        return engine_finding(f"GC-G8-embedded-instruction-{hit_index}", "G8", RELEASE_BLOCKER, "Field too long to screen for embedded instructions", f"Untrusted field {path} is too long to screen for embedded instructions (over {sg.MAX_TOTAL_CHARS:,} characters, raw or after Unicode normalisation, on its own or in the rendered review packet), so it was not screened in full; it must be held for human review.", location_for_scan_path(payload, path), "quality-gate-criteria.md #8.6", 0.99, "quality-gate-criteria.md #8.1, #8.6; severity-rules.md #1.1")
    return engine_finding(f"GC-G8-embedded-instruction-{hit_index}", "G8", RELEASE_BLOCKER, "Embedded instruction or forwarding request found in deliverable data", f"Untrusted field {path} contains instruction-like, forwarding or look-alike-character text; it must be treated as data and held for human review.", location_for_scan_path(payload, path), "quality-gate-criteria.md #8.1-#8.3", 0.99, "quality-gate-criteria.md #8.1-#8.3; severity-rules.md #1.1")

def add_spoof_hold(findings, escalations, spoofed, altered):
    """One G8 release blocker and escalations for spoofed engine findings and restored assertion_map output (#8.4)."""
    if not (spoofed or altered):
        return
    add_built_finding(findings, spoof_finding(len(spoofed), len(altered)))
    if spoofed:
        escalations.append(f"G8: upstream finding(s) {', '.join(spoofed)} reused engine-owned IDs or source tags without matching engine recomputation and were ignored - hold for reviewing partner/QRM (quality-gate-criteria.md #8.4)")
    if altered:
        escalations.append(f"G8: assertion_map output for {', '.join(altered)} was missing or altered upstream and was restored from recomputation - hold for reviewing partner/QRM (quality-gate-criteria.md #8.4)")

def evaluate(payload, hit_sink=None, rendered_check=True):
    """Apply every gate to a mapped payload (assertion_map output) and return it with findings, escalations and
    gate_results set. No file I/O and no provenance stamp; severity_rank calls it to re-derive the engine findings
    from the mapped input that gate-checked.json carries (severity-rules.md #3.7).

    With rendered_check, the result is screened as the review packet renders it (rules.rendered_screen on the ranked
    order): when values within a row, across rows or across blocks trip only together, the input text behind them is
    withheld with split markers, and when the packet would be too long to screen whole, the input text behind its
    longest lines is withheld with oversize markers (rules.oversize_sources); the gates are then evaluated again from
    the original input, until nothing composes and the packet fits (quality-gate-criteria.md #8.22). Each round
    withholds at least one more value, so it ends. severity_rank's re-derivation of a carried gate run turns it off: the
    withheld text arrives there as markers, which hold the same way."""
    original = copy.deepcopy(payload) if rendered_check else None
    rendered, oversize = frozenset(), frozenset()
    while True:
        sink = []
        result = evaluate_once(payload, sink, rendered, oversize)
        if not rendered_check:
            break
        groups, too_long = rules.rendered_screen(result, rules.rank_order(result["findings"]))
        found = rules.rendered_sources(original, groups)
        longest = rules.oversize_sources(original, too_long, rendered | oversize | found)
        if found <= rendered and longest <= oversize:
            break
        rendered, oversize = rendered | found, oversize | longest
        payload.clear()
        payload.update(copy.deepcopy(original))
    if hit_sink is not None:
        hit_sink.extend(sink)
    return result


def evaluate_once(payload, hit_sink=None, rendered=frozenset(), oversize=frozenset()):
    """One evaluation of every gate (evaluate), with the `rendered` and `oversize` input values also withheld."""
    require_contract(payload)
    raw = copy.deepcopy(payload)
    # Every section and nested record is checked against the contract before any reader touches it, so a wrongly typed
    # section is a clean input error, never iterated or skipped (quality-gate-criteria.md #8.16).
    rules.validate_contract(raw, "gate_check")
    # Withhold flagged text before any computation, so every derived field, finding and output carries the numbered
    # marker instead of the text (quality-gate-criteria.md #8.7). The contract is still checked on the raw input.
    rules.withhold_untrusted(payload, rendered=rendered, oversize=oversize)
    # A record of another engagement or deliverable carries only its positional stand-in (#8.15); assertion_map has
    # already replaced it, so this is a no-op on its output and defence in depth on anything else.
    rules.sanitise_foreign_records(payload)
    # Hits are also taken before any upstream engine output is restored from recomputation, so a flagged field inside
    # a restored entry (for example a member name added to assertion_mappings[]) is still reported, not just dropped.
    screened_hits = instruction_hits(payload) if EMBEDDED_INSTRUCTION_HOLD else []
    deliverable = payload["deliverable"]
    validate_deliverable(deliverable)
    expected = expected_assertion_outputs(payload, payload.get("evidence_set"))
    escalations = list(payload.get("escalations", []))
    carried_escalations = len(escalations)
    findings, spoofed, claimed = screen_upstream_findings(payload.get("findings", []), expected, raw.get("findings", []))
    altered = reconcile_assertion_outputs(payload, expected, findings, escalations)
    owners = {}
    loaded = check_missing_registers(payload, deliverable, findings, escalations)
    brand_checks = loaded.get("brand_checks") or []
    licensed_content = loaded.get("licensed_content") or []
    prior_findings = loaded.get("prior_findings") or []
    required_language = loaded.get("required_language") or []
    for index, section in enumerate(loaded.get("criteria_sections") or []):
        if not isinstance(section, str) or not section.strip():
            raise InputError(f"criteria.criteria_sections[{index}] must be a non-blank string, got {rules.describe(section)}")
    for index, item in enumerate(required_language):
        if not isinstance(item, str):
            raise InputError(f"deliverable.required_language[{index}] must be a string, got {rules.describe(item)}")
    validate_brand_checks(brand_checks)
    validate_licensed_content(licensed_content)
    validate_prior_findings(prior_findings)
    recipient_problem = recipient_list_problem(deliverable)
    if recipient_problem:
        add_finding(findings, "GC-G2-recipient-ambiguity", "G2", RELEASE_BLOCKER, "Recipient list is missing or ambiguous", f"{recipient_problem}; reliance language cannot be confirmed until the allowed recipient set is explicit.", disclaimer_location(payload), "quality-gate-criteria.md #2.2", 0.98, "quality-gate-criteria.md #2.2; severity-rules.md #1.1")
        escalations.append(f"G2: {recipient_problem} - release blocker; reviewing partner/QRM must confirm the allowed recipients (quality-gate-criteria.md #2.2)")
    recipients = recipient_classes(deliverable)
    invalid_identities = invalid_client_identities(deliverable)
    if invalid_identities:
        names = ", ".join(invalid_identities)
        add_finding(findings, "GC-G2-client-identity-external", "G2", MUST_FIX, "Client name or alias contains external-party vocabulary", f"{names} contains external-party vocabulary (counsel, lender, bank, investor, regulator, auditor, buyer, outside or third party), so it is not trusted to identify the client; recipients naming it are treated as external.", disclaimer_location(payload), "quality-gate-criteria.md #2.5", 0.9, "quality-gate-criteria.md #2.5; severity-rules.md #1.2")
        escalations.append(f"G2: confirm client aliases {names} - contains external-party vocabulary and is not trusted as the client identity; reviewing partner/QRM must confirm the client name, aliases and recipients (quality-gate-criteria.md #2.5)")
    if recipients["external"] and deliverable["third_party_recipient_named"] is False:
        names = ", ".join(recipients["external"])
        withheld_note = " or were withheld by the embedded-instruction screen" if any(rules.contains_withheld(item) for item in recipients_of(deliverable)) else ""
        add_finding(findings, "GC-G2-recipient-third-party-conflict", "G2", RELEASE_BLOCKER, "External recipient conflicts with third_party_recipient_named=false", f"Recipient(s) {names} match external-party vocabulary (counsel, lender, investor, regulator, auditor, buyer, outside or third party){withheld_note} but third_party_recipient_named is false; the deliverable is treated as third-party and reliance-restriction language is required.", disclaimer_location(payload), "quality-gate-criteria.md #2.2; quality-gate-criteria.md #2.5", 0.97, "quality-gate-criteria.md #2.2, #2.5; severity-rules.md #1.1")
        escalations.append(f"G2: recipient(s) {names} look external but third_party_recipient_named is false - release blocker; reviewing partner/QRM must confirm the recipients and reliance terms (quality-gate-criteria.md #2.5)")
    if recipients["unclassified"] and not recipient_problem:
        names = ", ".join(recipients["unclassified"])
        reason = "no trusted deliverable.client_name or client_aliases entry is supplied, so no recipient can be positively matched to the client" if not client_identities(deliverable) else "they do not positively match the client named in deliverable.client_name/client_aliases or a defined internal role"
        add_finding(findings, "GC-G2-recipient-unconfirmed", "G2", MUST_FIX, "Recipients not confirmed as client-only", f"Recipient(s) {names} are unclassified: {reason}. An unmatched recipient is never assumed to be client-only.", disclaimer_location(payload), "quality-gate-criteria.md #2.5", 0.9, "quality-gate-criteria.md #2.5; severity-rules.md #1.2")
        escalations.append(f"G2: confirm recipients {names} - not positively matched to the client; must-fix until the reviewing partner/QRM confirms they are client-only (quality-gate-criteria.md #2.5)")
    # Names and labels are compared in canonical form (quality-gate-criteria.md #8.11); closed enums stay exact. A
    # withheld entry never satisfies a requirement, and a withheld requirement is always unmet (#8.13): every copy of
    # one flagged text carries the same marker, so markers must never be matched against each other.
    # A blank entry (blank after the fold) states nothing, so it never satisfies a requirement (#8.17).
    present_disclaimers = {rules.key_of(item) for item in string_list(deliverable, "present_disclaimer_types", "deliverable.present_disclaimer_types") if not rules.contains_withheld(item)} - {None}
    disclaimer_type = deliverable.get("required_disclaimer_type")
    third_party = is_third_party_context(deliverable)
    if disclaimer_type not in DISCLAIMER_TYPES:
        add_finding(findings, "GC-G2-disclaimer-type-unrecognised", "G2", RELEASE_BLOCKER, "Required disclaimer type is not determined", "required_disclaimer_type is absent, blank or not one of general_advice or reliance_restriction, so the required disclaimer cannot be confirmed; an unrecognised value is never treated as clean.", disclaimer_location(payload), "quality-gate-criteria.md #2.1-#2.2; quality-gate-criteria.md #2.4", 0.97, "quality-gate-criteria.md #2.1-#2.2, #2.4; severity-rules.md #1.1")
        escalations.append("G2: required_disclaimer_type is absent, blank or unrecognised - release blocker; reviewing partner/QRM must confirm the required disclaimer (quality-gate-criteria.md #2.4)")
    if third_party and RELIANCE_RESTRICTION_REQUIRED_FOR_THIRD_PARTY and disclaimer_type in DISCLAIMER_TYPES and disclaimer_type != "reliance_restriction":
        add_finding(findings, "GC-G2-required-disclaimer-wrong", "G2", RELEASE_BLOCKER, "Required disclaimer type is wrong for third-party context", "A third-party recipient or allowed user requires reliance-restriction language.", disclaimer_location(payload), "quality-gate-criteria.md #2.2", 0.98, "quality-gate-criteria.md #2.2; severity-rules.md #1.1")
    if (disclaimer_type == "reliance_restriction" or (third_party and RELIANCE_RESTRICTION_REQUIRED_FOR_THIRD_PARTY)) and "reliance restriction" not in present_disclaimers:
        if third_party:
            add_finding(findings, "GC-G2-reliance-language", "G2", RELEASE_BLOCKER, "Wrong disclaimer for third-party recipient", "A third-party recipient or allowed user is named but reliance-restriction language is absent; a general-advice disclaimer does not satisfy this gate.", disclaimer_location(payload), "quality-gate-criteria.md #2.2", 0.98, "quality-gate-criteria.md #2.2; severity-rules.md #1.1")
            escalations.append("G2: third-party recipient context and reliance-restriction language absent - release blocker (quality-gate-criteria.md #2.2)")
        else:
            add_finding(findings, "GC-G2-reliance-language", "G2", RELEASE_BLOCKER, "Required reliance-restriction disclaimer is absent", "required_disclaimer_type is reliance_restriction but reliance-restriction language is not in present_disclaimer_types.", disclaimer_location(payload), "quality-gate-criteria.md #2.2; quality-gate-criteria.md #2.4", 0.97, "quality-gate-criteria.md #2.2, #2.4; severity-rules.md #1.1")
            escalations.append("G2: required reliance-restriction disclaimer absent from the deliverable - release blocker (quality-gate-criteria.md #2.4)")
    if disclaimer_type == "general_advice" and "general advice" not in present_disclaimers:
        add_finding(findings, "GC-G2-general-advice-absent", "G2", MUST_FIX, "Required general-advice disclaimer is absent", "required_disclaimer_type is general_advice but general-advice language is not in present_disclaimer_types; a declared disclaimer requirement is only met when the disclaimer is present.", disclaimer_location(payload), "quality-gate-criteria.md #2.1; quality-gate-criteria.md #2.4", 0.95, "quality-gate-criteria.md #2.1, #2.4; severity-rules.md #1.2")
        escalations.append("G2: required general-advice disclaimer absent from the deliverable - must-fix; reviewing partner/QRM must confirm the disclaimer before release (quality-gate-criteria.md #2.4)")
    present_language = {rules.key_of(item) for item in string_list(deliverable, "present_language", "deliverable.present_language") if not rules.contains_withheld(item)} - {None}
    for index, required in enumerate(required_language):
        # A requirement blank after the fold names nothing a present entry could match, so it is never satisfied (#8.17).
        if rules.contains_withheld(required) or rules.key_of(required) not in present_language:
            severity = RELEASE_BLOCKER if rules.canonical_id(required) == "reliance restriction" else MUST_FIX
            token = safe_token(required, "")
            finding_id = claim_finding_id(findings, owners, f"GC-G2-missing-{token or f'language-{index + 1}'}", ("required_language", required))
            if token:
                title, detail = f"Missing required language: {token}", f"Required language `{token}` is not present in the deliverable."
            else:
                # An item that is not an identifier-shaped key is named by position only, never quoted; an item that is
                # exactly a withheld marker (engine text) also names that marker (#8.9).
                title = f"Missing required language: item {index + 1}"
                shown = f"; it is {required}" if rules.is_withheld(required) else ""
                detail = f"Required language item {index + 1} (deliverable.required_language[{index}]) is not present in the deliverable{shown}."
            add_finding(findings, finding_id, "G2", severity, title, detail, disclaimer_location(payload), "quality-gate-criteria.md #2.1-#2.3", 0.94, "quality-gate-criteria.md #2.1-#2.3")
    if CONFIDENTIALITY_MARK_REQUIRED and rules.canonical_id(deliverable.get("confidentiality_marking") or "") != "client confidential":
        add_finding(findings, "GC-G4-confidentiality", "G4", RELEASE_BLOCKER, "Missing client-confidential marking", "Required client-confidential marking is absent from cover/footer.", loc("Cover", 1, 1, "Confidentiality mark"), "quality-gate-criteria.md #4.1", 0.97, "quality-gate-criteria.md #4.1; severity-rules.md #1.1")
    check_client_data_value(deliverable, findings, escalations)
    subject = rules.review_subject(payload)
    for index, check in enumerate(brand_checks):
        if foreign_entry_hold(findings, escalations, owners, check, subject, index, "G5", "Brand check", "Brand-check register", "brand_checks", "quality-gate-criteria.md #5.1-#5.3", "check_id"):
            continue
        check_id = safe_token(check["check_id"], f"brand-check-{index + 1}")
        finding_id = claim_finding_id(findings, owners, f"GC-G5-{check_id}", ("brand_checks", index))
        location = entry_location(check, "Brand-check register", f"Brand check {check_id}")
        legal = check["legal_or_release_control"] and LEGAL_MARK_DEFECT_BLOCKS
        status_value = check.get("status")
        if status_value == "fail":
            add_finding(findings, finding_id, "G5", MUST_FIX if legal else ADVISORY, check.get("title") or "Brand or formatting defect", check.get("detail") or "Brand check failed", location, "quality-gate-criteria.md #5.1-#5.2", check.get("confidence", 0.9), check.get("citation") or "quality-gate-criteria.md #5.1-#5.2")
        elif status_value not in BRAND_CHECK_STATUSES:
            severity = RELEASE_BLOCKER if legal else MUST_FIX
            add_finding(findings, finding_id, "G5", severity, "Brand or release-control check not verified", f"Brand check {check_id} has {'an unrecognised status' if status_value else 'a blank or missing status'}; only pass or fail are recognised, so the check is treated as not verified{' for a legal, confidentiality or release-control mark' if legal else ''}.", location, "quality-gate-criteria.md #5.2-#5.3", 0.95, "quality-gate-criteria.md #5.2-#5.3")
            escalations.append(f"G5: brand check {check_id} status is not pass or fail - {severity}; hold for reviewing partner/QRM (quality-gate-criteria.md #5.3)")
    for index, item in enumerate(licensed_content):
        if foreign_entry_hold(findings, escalations, owners, item, subject, index, "G6", "Licensed-content entry", "Licensed-content register", "licensed_content", "quality-gate-criteria.md #6.1-#6.3", "content_id"):
            continue
        content_id = safe_token(item["content_id"], f"licensed-content-{index + 1}")
        license_known = item.get("license_status") == LICENSE_STATUS_KNOWN
        if LICENSED_ATTRIBUTION_REQUIRED and item["attribution_present"] is not True:
            severity = MUST_FIX if license_known else RELEASE_BLOCKER
            add_finding(findings, claim_finding_id(findings, owners, f"GC-G6-{content_id}", ("licensed_content", index)), "G6", severity, "Licensed content lacks attribution", item.get("detail") or "Third-party content requires attribution.", entry_location(item, "Licensed-content register", f"Licensed content {content_id}"), "quality-gate-criteria.md #6.1-#6.2", item.get("confidence", 0.93), item.get("citation") or "quality-gate-criteria.md #6.1-#6.2")
            if not license_known:
                escalations.append(f"G6: unattributed licensed content {content_id} with license_status not known (unknown, blank or unrecognised) - release blocker; hold for reviewing partner/QRM (quality-gate-criteria.md #6.2-#6.3)")
    for index, prior in enumerate(prior_findings):
        if foreign_entry_hold(findings, escalations, owners, prior, subject, index, "G7", "Prior finding", "Prior findings register", "prior_findings", "quality-gate-criteria.md #7.1-#7.2", "finding_id"):
            continue
        if prior["claimed_closed"] is True and prior["document_fix_present"] is not True and PRIOR_FIX_MUST_LAND:
            prior_id = safe_token(prior["finding_id"], f"prior-finding-{index + 1}")
            add_finding(findings, claim_finding_id(findings, owners, f"GC-G7-{prior_id}", ("prior_findings", index)), "G7", MUST_FIX, "Prior finding marked closed but fix is absent", prior.get("detail") or "Tracker closure is not supported by the current document.", entry_location(prior, "Prior findings register", f"Prior finding {prior_id}"), "quality-gate-criteria.md #7.1-#7.2", prior.get("confidence", 0.96), prior.get("citation") or "quality-gate-criteria.md #7.1-#7.2")
    for index, assertion in enumerate(payload["assertions"]):
        if assertion["scope_aligned"] is not True:
            assertion_id = safe_token(assertion["assertion_id"], f"assertion-{index + 1}")
            add_finding(findings, claim_finding_id(findings, owners, f"GC-G3-scope-{assertion_id}", ("scope", index)), "G3", RELEASE_BLOCKER, "Claim or recommendation falls outside signed scope", "Assertion is marked scope_aligned=false; claims and recommendations must stay inside the signed statement of work and documented evidence set.", assertion["location"], "quality-gate-criteria.md #3.1", assertion.get("confidence", 0.9), f"{assertion['citation']}; quality-gate-criteria.md #3.1; severity-rules.md #1.1")
    verified_am = {rules.key_of(item["finding_id"]) for item in findings if rules.engine_id_owner(item["finding_id"]) == rules.AM_ENGINE} - {None}
    for index, mapping in enumerate(payload["assertion_mappings"]):
        if mapping["support_status"] in {"unsupported", "limited"} and "#3.2" in mapping["criteria_section"]:
            # Only an AM finding that matched engine recomputation may stand in for the G3 limitation finding.
            if rules.key_of(mapping["assertion_id"]) is not None and rules.key_of(f"AM-{mapping['assertion_id']}") in verified_am:
                continue
            add_finding(findings, claim_finding_id(findings, owners, f"GC-G3-{safe_token(mapping['assertion_id'], f'assertion-{index + 1}')}", ("limitation", index)), "G3", MUST_FIX, "Scope or sample limitation missing at point of recommendation", mapping.get("rationale", "Recommendation requires limitation."), mapping["location"], "quality-gate-criteria.md #3.2", mapping.get("confidence", 0.8), mapping.get("citation", "quality-gate-criteria.md #3.2"))
    if EMBEDDED_INSTRUCTION_HOLD:
        hits = instruction_hits(payload)
        hits += [hit for hit in screened_hits if hit not in hits]
        hits += placeholder_hits(payload, raw, expected, escalations[carried_escalations:], hits)
        if hit_sink is not None:
            # Every hit path, listed or beyond MAX_G8_HITS, so severity_rank reconciles by path, never by count (#8.19).
            hit_sink.extend(path for path, _ in hits)
        for hit_index, (path, hit_reason) in enumerate(hits[:MAX_G8_HITS], start=1):
            add_built_finding(findings, g8_hit_finding(hit_index, path, hit_reason, payload))
            if hit_reason == OVERSIZE:
                escalations.append(f"G8: {path} is too long to screen for embedded instructions - hold for reviewing partner/QRM (quality-gate-criteria.md #8.6)")
                continue
            escalations.append(f"G8: embedded-instruction tripwire in {path} - hold for reviewing partner/QRM (quality-gate-criteria.md #8.1-#8.3)")
        if len(hits) > MAX_G8_HITS:
            escalations.append(f"G8: {len(hits) - MAX_G8_HITS} further embedded-instruction hit(s) not listed individually - hold for reviewing partner/QRM (quality-gate-criteria.md #8.1-#8.3)")
    spoofed += check_claimed_findings(claimed, findings)
    add_spoof_hold(findings, escalations, spoofed, altered)
    # Escalations already carried in the input are not repeated, so a re-run on gate_check's own output reproduces it.
    escalations = rules.unique_entries(escalations)
    gate_results = []
    for gate_id, name in GATES.items():
        highest = highest_for_gate(findings, gate_id)
        status = "no_engine_findings" if highest == "none" else "blocked" if highest == RELEASE_BLOCKER else "attention_required"
        gate_results.append({"gate_id": gate_id, "name": name, "status": status, "highest_severity": highest, "finding_count": sum(1 for item in findings if item.get("gate_id") == gate_id), "confidence": 0.95, "source": ENGINE, "citation": f"quality-gate-criteria.md #{gate_id[1]}"})
    provenance = payload.setdefault("provenance", {})
    if not isinstance(provenance, dict):
        raise InputError("provenance must be an object when present")
    payload["findings"], payload["gate_results"], payload["escalations"] = findings, gate_results, escalations
    return payload


def gate_stage(mapped, generated_at=None):
    """gate_check's whole derivation on a mapped document, in place: evaluate, then record this engine after
    assertion_map in the ledger. severity_rank runs it to re-derive gate-checked.json (#8.21)."""
    payload = evaluate(mapped)
    rules.record_engine(payload, LEDGER_TAG, generated_at, prior=(rules.AM_LEDGER_TAG,))
    return payload


def rederive_mapped(review_input, stamp):
    """assertion_map's output re-derived from the review input with the carried run stamp (#8.21)."""
    return rules.assertion_map_stage(copy.deepcopy(review_input), stamp)[0]


def mapped_candidates(derived, stamp):
    """What gate_check accepts as --mapped: assertion_map's re-derived output, else (computed only when needed)
    gate_check's own output on it, so a re-run on gate-checked.json reproduces it."""
    yield derived
    try:
        yield gate_stage(copy.deepcopy(derived), stamp)
    except InputError:
        return


def authenticate(carried, input_path):
    """The mapped input must be exactly what assertion_map derives from the review input, every engine-owned field and
    the ledger included (or gate_check's own output, for an idempotent re-run): an edited deliverable identity,
    escalation, finding or provenance entry is refused, never carried (quality-gate-criteria.md #8.21)."""
    review_input = rules.load_json_file(input_path, "review input")
    stamp = rules.carried_stamp(carried)
    rules.require_rederived(carried, mapped_candidates(rederive_mapped(review_input, stamp), stamp), "gate_check")


def main():
    parser = rules.EngineArgumentParser(prog="gate_check.py", description="Apply quality-gate compliance checks deterministically.")
    parser.add_argument("--mapped", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    try:
        generated_at = validate_generated_at(args.generated_at)
        carried = load_json(args.mapped)
        original = copy.deepcopy(carried)
        payload = evaluate(carried)
        authenticate(original, args.input)
        findings, gate_results = payload["findings"], payload["gate_results"]
        rules.record_engine(payload, LEDGER_TAG, generated_at, prior=(rules.AM_LEDGER_TAG,))
        rules.write_json_atomic(args.out, payload, "gate-check output")
        blockers = sum(1 for item in findings if item["severity"] == RELEASE_BLOCKER)
        must_fix = sum(1 for item in findings if item["severity"] == MUST_FIX)
        advisory = sum(1 for item in findings if item["severity"] == ADVISORY)
        print(f"gate_check: {len(gate_results)} gate(s), blockers={blockers}, must_fix={must_fix}, advisory={advisory} -> gate-check output written")
        return 0
    except InputError as exc:
        print(f"gate_check input error: {exc}", file=sys.stderr)
        return 1
    except RecursionError:
        print("gate_check input error: input is nested too deeply to process safely", file=sys.stderr)
        return 1
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        print(f"gate_check input error: malformed input ({type(exc).__name__}; details withheld because they may quote untrusted text)", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
