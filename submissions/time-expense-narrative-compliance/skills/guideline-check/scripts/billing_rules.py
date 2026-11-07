#!/usr/bin/env python3
"""billing_rules - the deterministic code-map and billing-guideline rules (one rule set, three engines).

- code_map.py builds every entry's code_mapping with code_mapping() (task-phase-codes.md).
- guideline_check.py runs govern(). It recomputes every entry's code mapping and holds an entry whose
  supplied mapping disagrees (client-billing-guidelines.md #13.1), then applies #1-#9 and #11.
- Each stage's whole derivation is one function here (code_stage, govern_stage; signal_policy.draft_stage for
  narrative-draft) that the engine runs. code_map.py, guideline_check.py and exception_report.py each re-run
  every upstream stage on the activity packet (rederive) and refuse a carried document that differs from the
  result in any engine-owned field, provenance included (check_rederived, #13.8).
- exception_report.py then runs reconcile_governed(): govern() again under the report's own signal policy, so a
  narrower report-time policy that excludes evidence the entries were governed on is refused (#13.2), and prints
  only the re-derived flag detail and citations (rendered_flags).

Constants mirror references/task-phase-codes.md and references/client-billing-guidelines.md section
by section. The model reports these results; it never decides, suppresses or downgrades them.

This file ships as identical copies next to code_map.py, guideline_check.py and exception_report.py; the
test-data check test-data/professional-services/time-expense-narrative-compliance/<version>/tests/check_shared_copies.py
(not shipped in the package) fails when the copies drift.
"""
import os
import re
import sys
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signal_policy  # noqa: E402  (shared copy shipped next to each engine)

CODE_MAP_ENGINE = "engine:code_map"
GUIDELINE_ENGINE = "engine:guideline_check"
MAPPING_CITATION = "client-billing-guidelines.md #13.1"
RECONCILE_CITATION = "client-billing-guidelines.md #13.2"

# --- Code mapping (task-phase-codes.md) ----------------------------------------------------

DIRECT_MATCH_CONFIDENCE = 0.92  # task-phase-codes.md #5.1
KEYWORD_MATCH_CONFIDENCE = 0.78  # task-phase-codes.md #5.2
UNKNOWN_CONFIDENCE = 0.40  # task-phase-codes.md #5.3
CODE_MISMATCH_REVIEW_CONFIDENCE = 0.80  # client-billing-guidelines.md #4.2
UNMAPPED = ("UNMAPPED", "UNMAPPED", "Unknown or conflicting activity", "task-phase-codes.md #5.3")

CLASS_MAP = {
    "client_meeting": ("DL", "DL300", "Client meeting or working session", "task-phase-codes.md #3.1"),
    "document_analysis": ("AN", "AN200", "Document analysis tied to a client deliverable", "task-phase-codes.md #2.1"),
    "research": ("AN", "AN220", "Research or options analysis", "task-phase-codes.md #2.2"),
    "deliverable_drafting": ("DL", "DL320", "Drafting or finalizing a client deliverable", "task-phase-codes.md #3.2"),
    "internal_admin": ("NB", "NB900", "Internal non-billable administration", "task-phase-codes.md #4.1"),
    "billing_hygiene": ("BH", "BH910", "Pre-bill and WIP hygiene", "task-phase-codes.md #4.2"),
}
NON_BILLABLE_PHASES = ("NB", "BH")  # task-phase-codes.md #4
KEYWORDS = [
    ("meeting", CLASS_MAP["client_meeting"]),
    ("workshop", CLASS_MAP["client_meeting"]),
    ("analy", CLASS_MAP["document_analysis"]),
    ("research", CLASS_MAP["research"]),
    ("draft", CLASS_MAP["deliverable_drafting"]),
    ("staffing", CLASS_MAP["internal_admin"]),
]
# Activity classes compare in canonical form (signal_policy.canon_id): "Internal_Admin" or "internal-admin" is the
# internal_admin class, never an unknown class that would turn a non-billable reject into a hold (A13).
CLASS_KEYS = {signal_policy.canon_id(k): k for k in CLASS_MAP}


def known_class(value):
    """The CLASS_MAP key a (possibly variant-spelled) activity class names, or None."""
    return CLASS_KEYS.get(signal_policy.canon_id(value))


def signal_mapping(signal):
    """Map one linked signal to a code tuple, or None when its class is unknown.

    A signal explicitly marked non-billable that would otherwise map to a billable code maps to
    NB900 (#4.1); billing_hygiene keeps BH910 (#4.2).
    """
    mapping = CLASS_MAP.get(known_class(signal.get("activity_class")))
    if signal.get("billable_signal") is False and (mapping is None or mapping[0] not in NON_BILLABLE_PHASES):
        return CLASS_MAP["internal_admin"]
    return mapping


def draft_hits(draft_text, entry, linked):
    """Hits for a main draft narrative: alone, and with the entry's notes and linked activity text (#11.1)."""
    return signal_policy.screen(draft_text, signal_policy.entry_texts(
        {"narrative": draft_text, "notes": entry.get("notes")}, linked))


def usable_narratives(entry, linked):
    """(draft narrative, entry narrative, draft withheld, own withheld) the rules may read (D19, #11.2).

    The draft narrative is unusable when it is the withheld marker or trips with the entry's notes or linked text
    (guideline_check withholds it); the entry's own narrative when signal_policy.field_withheld() finds it is
    withheld text in its record (linked signals that are flagged themselves are left out, since their text is
    withheld on its own). An unusable narrative is "" and infers no code, credits no element, matches no term and
    is compared with no other narrative. A withheld draft over an empty timesheet narrative leaves the entry with
    no narrative of its own, which the rules still report (minimum detail); a withheld own narrative is not text
    the rules can judge, so with no usable draft the entry is held instead."""
    draft = entry.get("draft") if isinstance(entry.get("draft"), dict) else {}
    draft_text = draft.get("narrative").strip() if isinstance(draft.get("narrative"), str) else ""
    own = entry.get("narrative").strip() if isinstance(entry.get("narrative"), str) else ""
    draft_withheld = own_withheld = False
    if draft_text and (signal_policy.is_withheld(draft_text) or draft_hits(draft_text, entry, linked)):
        draft_text, draft_withheld = "", True
    clean = [a for a in linked if not signal_policy.signal_flagged(a)]
    if own and signal_policy.field_withheld(signal_policy.entry_texts(entry, clean), "narrative"):
        own, own_withheld = "", True
    return draft_text, own, draft_withheld, own_withheld


WITHHELD_MAPPING_NOTE = ("the narrative is withheld as embedded_instruction and is not read to infer a code "
                         "(client-billing-guidelines.md #11.2)")
# Sweep A (QA round 14): a flag detail composed from several supplied values (activity classes, IDs, a submitted
# code) shows them only when they are clean read together (signal_policy.composed_hits); otherwise it gives counts
# and one of these notes, and govern holds the entry (COMPOSED_REASON).
COMPOSED_CLASSES_NOTE = (f"activity class names {signal_policy.COMPOSED_WITHHELD_NOTE} "
                         f"({signal_policy.INJECTION_CITATION})")
COMPOSED_IDS_NOTE = f"IDs {signal_policy.COMPOSED_WITHHELD_NOTE} ({signal_policy.INJECTION_CITATION})"
COMPOSED_REASON = ("supplied values the engine would join into a flag detail or review reason read as an "
                   "instruction together; the detail gives counts only")


def choose_mapping(entry, linked):
    """Return (mapping tuple, confidence, basis).

    Every linked signal is mapped first; more than one target code (non-billable codes included)
    is a conflict and returns UNMAPPED at 0.40 (#5.3). There is no non-billable short-circuit.
    Linked signals that all map to one code except for some unknown classes are partly mapped
    (UNMAPPED at 0.40, basis partially_mapped_activity_classes); none mapping is unknown_activity_class.
    Keyword inference reads only usable (screened, non-withheld) narratives (D19).
    """
    if linked:
        mappings = [signal_mapping(a) for a in linked]
        known = [m for m in mappings if m is not None]
        codes = {m[1] for m in known}
        if len(codes) > 1:
            return UNMAPPED, UNKNOWN_CONFIDENCE, "conflicting_activity_classes"
        if len(known) == len(mappings) and len(codes) == 1:
            return known[0], DIRECT_MATCH_CONFIDENCE, "direct_activity_class"
        if known:
            return UNMAPPED, UNKNOWN_CONFIDENCE, "partially_mapped_activity_classes"
        return UNMAPPED, UNKNOWN_CONFIDENCE, "unknown_activity_class"
    draft_text, own, _, _ = usable_narratives(entry, linked)
    text = signal_policy.canon_text(" ".join([draft_text, own]))
    for token, mapping in KEYWORDS:
        if token in text:
            return mapping, KEYWORD_MATCH_CONFIDENCE, "keyword_inference"
    return UNMAPPED, UNKNOWN_CONFIDENCE, "unmapped"


def code_mapping(entry, linked):
    """The code_mapping object code_map.py writes for one entry (and guideline_check.py recomputes)."""
    (phase, task, label, citation), confidence, basis = choose_mapping(entry, linked)
    submitted_task = entry.get("submitted_task_code")
    submitted_phase = entry.get("submitted_phase_code")
    flags = []
    if task == "UNMAPPED":
        pairs = sorted({f"{signal_policy.redact(a.get('activity_class'))}->{(signal_mapping(a) or ('?', '?'))[1]}"
                        for a in linked})
        mapped = sorted({f"{signal_policy.redact(a.get('activity_class'))}->{signal_mapping(a)[1]}"
                         for a in linked if signal_mapping(a) is not None})
        unknown = sum(signal_mapping(a) is None for a in linked)
        partly = (f"{unknown} of {len(linked)} linked signals have an activity class with no code; the others map to "
                  "{}; no code is recommended")
        if basis == "conflicting_activity_classes":
            detail = "linked signals point to different codes (" + ", ".join(pairs) + "); no code is recommended"
        elif basis == "partially_mapped_activity_classes":
            # The class->code pairs that did map are listed, so the detail never denies a mapping it shows (F02).
            detail = partly.format(", ".join(mapped))
        else:
            detail = "no activity class or keyword maps to a code"
        if basis == "unmapped" and any(usable_narratives(entry, linked)[2:]):
            detail = f"{WITHHELD_MAPPING_NOTE}; no activity class maps to a code"
        if submitted_task:
            detail += f"; submitted {submitted_task} cannot be confirmed"
        submitted = [submitted_task] if isinstance(submitted_task, str) else []
        if basis == "conflicting_activity_classes" and signal_policy.composed_hits(pairs + submitted, detail):
            # QA round 14: the class names and the submitted code read as an instruction together - counted only.
            detail = (f"linked signals point to {len({p.rsplit('->', 1)[1] for p in pairs})} different codes; "
                      f"{COMPOSED_CLASSES_NOTE}; no code is recommended"
                      + ("; the submitted task code cannot be confirmed" if submitted_task else ""))
        elif basis == "partially_mapped_activity_classes" and signal_policy.composed_hits(mapped + submitted, detail):
            detail = (partly.format(f"one code ({COMPOSED_CLASSES_NOTE})")
                      + ("; the submitted task code cannot be confirmed" if submitted_task else ""))
        flags.append({
            "flag": "unmapped_code",
            "detail": detail,
            "severity": "hold_for_review",
            "source": CODE_MAP_ENGINE,
            "confidence": confidence,
            "citations": ["task-phase-codes.md #5.3", "client-billing-guidelines.md #4.1"],
        })
    elif (submitted_task and submitted_task != task) or (submitted_phase and submitted_phase != phase):
        # Either code can be wrong: a matching task code under the wrong phase is still a mismatch (#4.1).
        detail = (f"submitted {submitted_task} does not match recommended {task}" if submitted_task and submitted_task != task
                  else f"submitted phase {submitted_phase} does not match recommended phase {phase} for {task}")
        flags.append({
            "flag": "submitted_code_mismatch",
            "detail": detail,
            "severity": "needs_review" if confidence >= CODE_MISMATCH_REVIEW_CONFIDENCE else "hold_for_review",
            "source": CODE_MAP_ENGINE,
            "confidence": confidence,
            "citations": [citation, "client-billing-guidelines.md #4.1", "client-billing-guidelines.md #4.2"],
        })
    return {
        "recommended_phase_code": phase,
        "recommended_task_code": task,
        "recommended_label": label,
        "submitted_phase_code": submitted_phase,
        "submitted_task_code": submitted_task,
        "basis": basis,
        "flags": flags,
        "confidence": confidence,
        "source": CODE_MAP_ENGINE,
        "citations": [citation],
    }


# --- Billing guidelines (client-billing-guidelines.md) -------------------------------------

MIN_NARRATIVE_WORDS = 12  # client-billing-guidelines.md #1.1
BLOCK_BILLING_HOURS = 2.0  # client-billing-guidelines.md #2.1 / #2.2
BLOCK_BILLING_CLASS_LIMIT = 1  # client-billing-guidelines.md #2.1
RELATED_CLASS_LIMIT = 2  # client-billing-guidelines.md #2.2
PROHIBITED_TERMS = ("attention to", "various matters", "miscellaneous", "work on file", "general follow up")  # #3.1
VAGUE_PHRASES = ("review and revise", "work on", "handle", "follow up", "touch base")  # #3.2
# #3.2 matches each vague phrase in its inflected forms too ("worked on", "handling", "followed up"); the flag detail
# names the base phrase.
VAGUE_FORMS = {
    "review and revise": r"review(?:s|ed|ing)?\sand\srevis(?:e|es|ed|ing)",
    "work on": r"work(?:s|ed|ing)?\son",
    "handle": r"handl(?:e|es|ed|ing)",
    "follow up": r"follow(?:s|ed|ing)?\sup",
    "touch base": r"touch(?:es|ed|ing)?\sbase",
}
VAGUE_RES = {phrase: re.compile(r"\b" + VAGUE_FORMS[phrase] + r"\b") for phrase in VAGUE_PHRASES}
NON_BILLABLE_CLASSES = signal_policy.NON_BILLABLE_CLASSES  # client-billing-guidelines.md #5.1
NON_BILLABLE_TASK_CODES = ("NB900", "BH910")  # task-phase-codes.md #4.1 / #4.2
ROUNDING_INCREMENT = Decimal("0.1")  # client-billing-guidelines.md #6.1
EVIDENCE_OVERRUN_HOURS = 0.2  # client-billing-guidelines.md #6.2
NEAR_DUPLICATE_RATIO = 0.92  # client-billing-guidelines.md #7.1
MISSING_TIME_MIN_HOURS = 0.5  # client-billing-guidelines.md #8.1
CONFIDENCE_FLOOR = 0.75  # client-billing-guidelines.md #9.1
SUBJECT_COVERAGE = 0.5  # share of a subject's content words the narrative must contain
SEVERITY_ORDER = {"compliant": 0, "needs_review": 1, "hold_for_review": 2, "reject": 3}

STOPWORDS = {"a", "an", "and", "the", "of", "for", "to", "with", "on", "in", "at", "by", "from", "or", "re", "via"}
# #1.2 "actor's work": the narrative must lead with the timekeeper's own work verb.
ACTION_VERBS = {
    "advised", "analyzed", "analysed", "assessed", "attended", "briefed", "called", "compiled", "conferred",
    "confirmed", "coordinated", "corresponded", "designed", "developed", "discussed", "documented", "drafted",
    "edited", "evaluated", "facilitated", "finalized", "identified", "interviewed", "led", "mapped", "met",
    "modeled", "negotiated", "planned", "prepared", "presented", "reconciled", "researched", "revised",
    "reviewed", "scoped", "summarized", "tested", "updated", "validated", "wrote",
}
# #1.2 "client-facing purpose": an explicit purpose clause.
PURPOSE_VERBS = signal_policy.PURPOSE_VERBS
PURPOSE_RE = re.compile(r"\b(?:to|so that we can|in order to)\s+(?:" + "|".join(PURPOSE_VERBS) + r")\b")
EMBEDDED_DEFAULT = ("narrative or linked activity text addresses the reviewer/engine, steers the verdict, "
                    "suppresses or overrides the review, claims an approval or waiver, asks for forwarding, mixes "
                    "scripts in one word, or carries an e-mail address or URL")
TEXT_WITHHELD_REASON = ("the narrative is withheld, so no narrative rule (detail, required elements, terms, phrases, "
                        "duplicates) or code inference was run on it (client-billing-guidelines.md #11.2)")


def normalize(text):
    # Canonical text first (NFKC, format characters, casefold): a fullwidth or zero-width-split prohibited term or
    # vague phrase is the same term, never erased by the ASCII filter below (A13).
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", signal_policy.canon_text(text or ""))).strip()


def tokens(text):
    return normalize(text).split()


def content_tokens(text):
    return {t for t in tokens(text) if t not in STOPWORDS}


def word_count(text):
    return len([w for w in re.split(r"\s+", (text or "").strip()) if w])


def rounded_to_increment(value):
    try:
        return (Decimal(str(value)) % ROUNDING_INCREMENT) == 0
    except InvalidOperation:
        return False


def similarity(a, b):
    """Max of character-sequence ratio and token Jaccard on normalized text."""
    ratio = SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return round(max(ratio, jaccard), 3)


def add_flag(flags, flag, severity, detail, citations, confidence=0.95):
    flags.append({
        "flag": flag,
        "severity": severity,
        "detail": detail,
        "source": GUIDELINE_ENGINE,
        "confidence": confidence,
        "citations": citations,
    })


def required_elements(entry, narrative, linked):
    """#1.2 checks on the narrative text itself. Returns {element: bool}.

    The subject is credited only against the entry's own linked signals; with nothing linked the
    subject cannot be evidenced (no fall-back to every signal in the packet). A flagged signal's
    subject and deliverable are withheld text and credit nothing (D19).
    """
    toks = tokens(narrative)
    narrative_tokens = set(toks)
    first = toks[0] if toks else ""
    actor = bool(entry.get("person")) and first in ACTION_VERBS
    subject = False
    for signal in linked:
        if signal_policy.signal_flagged(signal):
            continue
        for text in (signal.get("subject"), signal.get("deliverable")):
            wanted = content_tokens(text)
            if wanted and len(wanted & narrative_tokens) / len(wanted) >= SUBJECT_COVERAGE:
                subject = True
    normalized = normalize(narrative)
    purpose = bool(PURPOSE_RE.search(normalized))
    if not purpose:
        for signal in linked:
            recorded = normalize(signal.get("purpose"))
            if signal_policy.signal_flagged(signal) or not recorded:
                continue
            if signal_policy.purpose_prefix(recorded) == "regarding":
                variants = {recorded, normalize(signal_policy.noun_purpose(signal["purpose"]))}
                if any(re.search(r"\bregarding\s+" + re.escape(value) + r"\b", normalized) for value in variants):
                    purpose = True
                    break
            if signal_policy.purpose_repeats_subject(signal):
                # An omitted purpose is evidenced only by the complete grounded clause, never by an unrelated title.
                clause, _ = signal_policy.clause(entry, signal)
                parts = [normalize(part) for part in re.split(r";(?:\s+and)?\s*", narrative)]
                if normalize(clause) in parts:
                    purpose = True
                    break
    return {"actor": actor, "subject": subject, "purpose": purpose}


def withhold_draft(draft, hits):
    """#11.2: replace a flagged draft narrative with the neutral marker; the entry is held separately."""
    draft["narrative"] = signal_policy.WITHHELD_TEXT
    draft["status"] = "needs_review_embedded_instruction"
    draft["needs_review"] = True
    draft["word_count"] = 0
    draft["review_reasons"] = list(draft.get("review_reasons") or []) + [
        signal_policy.hold_reason(hits, "draft narrative flagged as embedded_instruction by guideline_check")
        + "; withheld from the governed output and never followed (client-billing-guidelines.md #11.1, #11.2)"]
    draft["citations"] = sorted(set(list(draft.get("citations") or [])
                                    + [signal_policy.INJECTION_CITATION, signal_policy.WITHHOLD_CITATION]))


def withhold_texts(item):
    """#11.2 for review reasons and citations. When the reasons trip, each reason that trips is replaced by the
    withheld marker (every reason when only their join trips); citations keep only safe ones, and only plain
    source-row or reference citations when the reasons and citations trip together."""
    reasons = [r for r in item.get("review_reasons") or [] if isinstance(r, str)]
    if reasons and signal_policy.embedded_instruction(signal_policy.draft_records({"review_reasons": reasons})[0]):
        single = [signal_policy.embedded_instruction(r) for r in reasons]
        if not any(single):
            single = [True] * len(reasons)
        item["review_reasons"] = [signal_policy.WITHHELD_TEXT if bad else r for r, bad in zip(reasons, single)]
    flagged = signal_policy.embedded_instruction(signal_policy.draft_records(
        {"review_reasons": reasons, "citations": item.get("citations")})[0])
    item["citations"] = signal_policy.safe_citations(item.get("citations") or [], flagged)[0]


def missing_time_item(activity):
    """One #8.1 missing-time item; flagged text is withheld (#11.2)."""
    hits = signal_policy.screen(signal_policy.signal_texts(activity))
    flagged = activity.get("embedded_instruction") is True or bool(hits)
    citations, _ = signal_policy.safe_citations(activity.get("citations", []), flagged)
    item = {
        "activity_id": activity["activity_id"],
        "person": activity.get("person"),
        "date": activity.get("date"),
        "activity_class": signal_policy.redact(activity.get("activity_class")),
        "duration_hours": activity.get("duration_hours"),
        "subject": signal_policy.WITHHELD_TEXT if flagged else activity.get("subject"),
        "finding": "engagement activity has no matching time entry",
        "source": GUIDELINE_ENGINE,
        "confidence": activity.get("confidence", 0.9),
        "citations": [c for c in citations
                      if c not in (signal_policy.POLICY_CITATION, signal_policy.INJECTION_CITATION)]
        + ["client-billing-guidelines.md #8.1"],
    }
    if flagged:
        item["embedded_instruction"] = True
        item["finding"] += "; " + signal_policy.hold_reason(hits, "activity text flagged as embedded_instruction") + "; withheld"
        item["citations"] += [signal_policy.INJECTION_CITATION, signal_policy.WITHHOLD_CITATION]
    return item


SPLIT_MISSING_REASON = ("activity text flagged as embedded_instruction when read with the neighbouring missing-time "
                        "items (text split across items that are listed side by side)")


def _rendered_row(item):
    """A missing-time item's values as the report's table prints them, in order (D22): ID, person, date, hours,
    subject and each citation."""
    values = [item.get("activity_id"), item.get("person"), item.get("date"), item.get("duration_hours"),
              item.get("subject")] + list(item.get("citations") or [])
    return [v if isinstance(v, str) else (None if v is None else str(v)) for v in values]


def withhold_missing_runs(items, activities=None):
    """#11.1 / #11.2 across items: missing-time items are listed side by side, so an instruction split across
    neighbouring items is screened joined (the detector's run screen) - their subjects alone, and every run of the
    values the rows print, in reading order, that crosses from one item to the next, IDs and citations included
    (D22) - and each item in a tripping run is withheld and held like a flagged one. 1.0.6: an item withheld on its
    own drops out of those screens, so the supplied subjects and activity classes (activities, the signals in item
    order) are also read for split partners (signal_policy.split_partners_seq), and the clean half of an instruction
    split across a withheld item and its neighbour is withheld too; a run too long to join is held as oversize."""
    texts = [None if item.get("embedded_instruction") else item.get("subject") for item in items]
    bad = set(signal_policy._tripping_seq(texts))
    # QA round 14: the items' activity classes are a column too (listed side by side in missing_time_report).
    classes = signal_policy._tripping_seq([None if item.get("embedded_instruction") else item.get("activity_class")
                                           for item in items])
    bad |= classes
    sources = activities if isinstance(activities, list) and len(activities) == len(items) else items
    flagged = {i for i, item in enumerate(items) if item.get("embedded_instruction")}
    subjects, over = signal_policy.split_partners_seq([s.get("subject") for s in sources], flagged)
    split_classes, over_classes = signal_policy.split_partners_seq([s.get("activity_class") for s in sources])
    bad |= subjects | split_classes
    classes = set(classes) | split_classes
    over |= over_classes
    originals = [[(i, v) for v in _rendered_row(dict(item, subject=sources[i].get("subject")))]
                 for i, item in enumerate(items)]
    bad |= signal_policy.crossing_runs([[(i, v) for v in _rendered_row(item)] for i, item in enumerate(items)],
                                       originals)
    for i in sorted(bad):
        item = items[i]
        if i in classes:
            item["activity_class"] = signal_policy.WITHHELD_TEXT
        if item.get("embedded_instruction"):
            continue  # already withheld and held (missing_time_item)
        item["subject"] = signal_policy.WITHHELD_TEXT
        item["embedded_instruction"] = True
        reason = signal_policy.OVERSIZE_REASON if i in over else SPLIT_MISSING_REASON
        item["finding"] += "; " + reason + "; withheld"
        item["citations"] = signal_policy.safe_citations(item["citations"], True)[0] + [
            signal_policy.INJECTION_CITATION, signal_policy.WITHHOLD_CITATION]


def govern(out):
    """Apply the guideline rules to a coded packet in place (after scope and signal policy are enforced).

    Sets every entry's compliance, and the packet's missing_time_report, exception_list and
    prebill_summary. Returns the number of entries whose supplied code mapping was rejected.
    """
    signals = out["activity_signals"]
    by_id = signal_policy.signal_index(signals)
    # #11.3: a hold on packet metadata governs every entry, so it is known before any entry is gated (B6).
    packet_hold = signal_policy.packet_held(out)
    used_activity_ids = set()
    meeting_seen = {}
    rejected_mappings = 0

    for entry in out["time_entries"]:
        draft = entry.get("draft") or {}
        linked = signal_policy.linked_signals(entry, by_id)
        draft_text = draft.get("narrative").strip() if isinstance(draft.get("narrative"), str) else ""
        draft_found = []
        if draft_text and not signal_policy.is_withheld(draft_text):
            # The main draft alone, and with the entry's notes and linked activity text (split instructions).
            draft_found = draft_hits(draft_text, entry, linked)
        # #11.2: a withheld draft (flagged now, or already the marker) is never checked as text. Every rule runs
        # on the entry's own narrative instead, so exception_report's re-run reproduces every flag (#13.2).
        # D19: a narrative that is itself withheld text is read by no rule; with no usable narrative the text rules
        # (detail, elements, terms, phrases, duplicates) are not run and the entry is held instead.
        usable_draft, usable_own, draft_withheld, own_withheld = usable_narratives(entry, linked)
        narrative = usable_draft or usable_own
        any_withheld = draft_withheld or own_withheld
        text_withheld = own_withheld and not narrative
        narrative_norm = normalize(narrative)
        used_activity_ids.update(signal_policy._id_key(a["activity_id"]) for a in linked)
        # Distinct classes in canonical form (a variant spelling of one class is one class); first spelling shown.
        class_names = {}
        for a in linked:
            if a.get("activity_class"):
                class_names.setdefault(signal_policy.canon_id(a["activity_class"]), a["activity_class"])
        classes = sorted(class_names.values())
        duration = entry["duration_hours"]
        same_day = [a for a in linked if a.get("date") == entry.get("date")]
        off_date = [a for a in linked if a.get("date") != entry.get("date")]
        evidence_hours = round(sum(a.get("duration_hours", 0) for a in same_day), 2)
        all_date_hours = round(sum(a.get("duration_hours", 0) for a in linked), 2)
        # #13.1: the code mapping is recomputed from the rules (on the usable narratives only, as code_map.py
        # read them, D19); a supplied mapping that disagrees is discarded and the entry is held.
        mapping = code_mapping(entry, linked)
        mapping_rejected = entry.get("code_mapping") != mapping
        flags = []

        excluded_links = entry.get("excluded_activity_ids") or []
        if excluded_links:
            add_flag(flags, "disabled_source_signal", "hold_for_review",
                     f"linked signal(s) from a disabled or unresolvable source were excluded and not counted as evidence: "
                     f"{signal_policy.describe_excluded(excluded_links, out)}", [signal_policy.POLICY_CITATION], 0.99)

        cross = entry.get("cross_person_activity_ids") or []
        if cross:
            # Counted, never named: the other timekeeper and their activity stay out of this entry's output (#12.1).
            add_flag(flags, "cross_person_link", "hold_for_review",
                     f"{len(cross)} linked activit{'y is' if len(cross) == 1 else 'ies are'} recorded for another "
                     "timekeeper; not drafted from, mapped or counted as evidence", [signal_policy.CROSS_PERSON_CITATION],
                     0.99)

        wc = word_count(narrative)
        if wc < MIN_NARRATIVE_WORDS and not text_withheld:
            add_flag(flags, "minimum_detail", "reject", f"{wc} words < {MIN_NARRATIVE_WORDS} required words",
                     ["client-billing-guidelines.md #1.1"], 0.9)

        elements = required_elements(entry, narrative, linked)
        missing = [k for k in ("actor", "subject", "purpose") if not elements[k]]
        if text_withheld:
            pass  # D19: a withheld narrative is not checked for elements; the entry is held below
        elif len(missing) >= 2:
            add_flag(flags, "required_elements_missing", "reject", f"missing required elements: {', '.join(missing)}",
                     ["client-billing-guidelines.md #1.2"], 0.88)
        elif missing:
            add_flag(flags, "required_elements_missing", "needs_review", f"missing required element: {missing[0]}",
                     ["client-billing-guidelines.md #1.2"], 0.88)

        # QA round 14: the class names are joined into the detail only when they are clean read together - in the
        # detail's order with the detail's own words, and in link order (the class column of split_activities);
        # otherwise the detail counts them (COMPOSED_CLASSES_NOTE) and the entry is held below.
        link_classes = [a.get("activity_class") for a in linked if isinstance(a.get("activity_class"), str)]

        def class_detail(detail, neutral):
            if len(classes) > 1 and (signal_policy.composed_hits(classes, detail)
                                     or signal_policy.composed_hits(link_classes)):
                return neutral
            return detail

        if duration > BLOCK_BILLING_HOURS and len(classes) > BLOCK_BILLING_CLASS_LIMIT:
            add_flag(flags, "block_billing", "reject", class_detail(
                f"{duration} hours combines {len(classes)} activity classes: {', '.join(classes)}",
                f"{duration} hours combines {len(classes)} activity classes; {COMPOSED_CLASSES_NOTE}"),
                ["client-billing-guidelines.md #2.1"], 0.97)
        elif duration <= BLOCK_BILLING_HOURS and len(classes) > RELATED_CLASS_LIMIT:
            head = (f"{duration} hours combines {len(classes)} activity classes (at most {RELATED_CLASS_LIMIT} at <= "
                    f"{BLOCK_BILLING_HOURS} hours)")
            add_flag(flags, "block_billing", "reject",
                     class_detail(f"{head}: {', '.join(classes)}", f"{head}; {COMPOSED_CLASSES_NOTE}"),
                     ["client-billing-guidelines.md #2.2"], 0.95)
        elif (duration <= BLOCK_BILLING_HOURS and len(classes) == RELATED_CLASS_LIMIT and not text_withheld
              and not (elements["subject"] and elements["purpose"])):
            add_flag(flags, "block_billing", "needs_review", class_detail(
                f"{duration} hours combines {', '.join(classes)} without an explicit subject and purpose",
                f"{duration} hours combines {len(classes)} activity classes ({COMPOSED_CLASSES_NOTE}) without an "
                "explicit subject and purpose"), ["client-billing-guidelines.md #2.2"], 0.9)

        for term in PROHIBITED_TERMS:
            if term in narrative_norm:
                add_flag(flags, "prohibited_term", "reject", f"matched prohibited term '{term}'",
                         ["client-billing-guidelines.md #3.1", "client-billing-guidelines.md #3.3"], 0.99)
        cured = elements["subject"] and elements["purpose"]
        for phrase in VAGUE_PHRASES:
            if VAGUE_RES[phrase].search(narrative_norm):
                if cured:
                    add_flag(flags, "vague_phrase", "needs_review",
                             f"matched vague phrase '{phrase}' (cured by an explicit subject and purpose)",
                             ["client-billing-guidelines.md #3.2", "client-billing-guidelines.md #3.3"], 0.93)
                else:
                    add_flag(flags, "vague_phrase", "reject",
                             f"matched vague phrase '{phrase}' with no specific subject and purpose to cure it",
                             ["client-billing-guidelines.md #3.2", "client-billing-guidelines.md #3.3"], 0.93)

        rewrites = [r for r in draft.get("suggested_rewrites") or [] if isinstance(r, dict)]
        # QA round 14: the date-mismatch and duplicate-meeting details are composed from several supplied values (IDs
        # and dates), so they are built here, before the embedded_instruction gate, and added in their usual place.
        date_flags, meeting_flags = [], []
        if off_date:
            detail = (f"entry dated {entry.get('date')} links activity from another date: "
                      + ", ".join(f"{a['activity_id']} ({a.get('date')})" for a in off_date))
            if signal_policy.composed_hits([entry.get("date")] + [v for a in off_date
                                                                  for v in (a["activity_id"], a.get("date"))], detail):
                detail = (f"entry links {len(off_date)} activit{'y' if len(off_date) == 1 else 'ies'} from another "
                          f"date; activity {COMPOSED_IDS_NOTE}")
            add_flag(date_flags, "date_mismatch", "needs_review", detail, ["client-billing-guidelines.md #6.2"], 0.85)
        # Meetings are matched in canonical form (canon_id): a variant spelling of a meeting ID is the same meeting
        # and cannot escape the duplicate rule; the detail names the entry's own spelling.
        meeting_ids = {}
        for a in linked:
            # A21: a meeting ID that folds to nothing is no meeting: two blank IDs are never "the same meeting".
            if signal_policy.canon_id(a.get("meeting_id")):
                meeting_ids.setdefault(signal_policy.canon_id(a["meeting_id"]), a["meeting_id"])
        for meeting_key, meeting_id in sorted(meeting_ids.items()):
            if text_withheld:
                break  # D19: a withheld narrative is compared with no other narrative, and none with it
            prior = meeting_seen.setdefault(meeting_key, [])
            best = None
            for prior_id, prior_text in prior:
                score = similarity(prior_text, narrative_norm)
                if score >= NEAR_DUPLICATE_RATIO and (best is None or score > best[1]):
                    best = (prior_id, score)
            if best:
                detail = (f"near-duplicate meeting narrative for {meeting_id}: similarity {best[1]} >= "
                          f"{NEAR_DUPLICATE_RATIO} with {best[0]}")
                if signal_policy.composed_hits([meeting_id, best[0]], detail):
                    detail = (f"near-duplicate meeting narrative: similarity {best[1]} >= {NEAR_DUPLICATE_RATIO} "
                              f"with an earlier entry; meeting and entry {COMPOSED_IDS_NOTE}")
                add_flag(meeting_flags, "duplicate_meeting", "reject", detail, ["client-billing-guidelines.md #7.1"],
                         0.92)
            prior.append((entry["entry_id"], narrative_norm))
        # The draft's review reasons, citations and every rewrite are free text too (#11.1).
        records = signal_policy.draft_records(draft)
        record_hits = [signal_policy.screen(r) for r in records]
        # Any upstream marker or any field (or field aggregate) that trips holds the entry; never compliant.
        hits = signal_policy.screen(narrative, signal_policy.entry_texts(entry, linked),
                                    *[signal_policy.signal_texts(a) for a in linked]) + draft_found
        hits += [h for found in record_hits for h in found]
        reasons = list(draft.get("review_reasons") or []) + [x for r in rewrites for x in r.get("review_reasons") or []]
        marked = (any_withheld or entry.get("embedded_instruction") is True
                  or any(a.get("embedded_instruction") is True for a in linked)
                  or bool(signal_policy.split_activities(linked, entry.get("person")))
                  or any(r.get("status") == "withheld_embedded_instruction" for r in rewrites)
                  or signal_policy.WITHHELD_TEXT in reasons)
        # A detail or reason that counts supplied values instead of joining them (sweep A) holds the entry too.
        composed = any(isinstance(text, str) and signal_policy.COMPOSED_WITHHELD_NOTE in text
                       for text in [f.get("detail") for f in flags + mapping["flags"] + date_flags + meeting_flags]
                       + reasons)
        if marked or hits or packet_hold or composed:
            causes = ([signal_policy.hold_reason(hits, EMBEDDED_DEFAULT)] if marked or hits else []) \
                + ([COMPOSED_REASON] if composed else []) \
                + ([TEXT_WITHHELD_REASON] if text_withheld else []) \
                + ([signal_policy.PACKET_HOLD_REASON] if packet_hold else [])
            add_flag(flags, "embedded_instruction", "hold_for_review",
                     "; ".join(causes) + "; treated as data and not followed",
                     [signal_policy.INJECTION_CITATION] + ([signal_policy.METADATA_CITATION] if packet_hold else []),
                     0.95)
        if record_hits and record_hits[0]:
            withhold_texts(draft)
        if draft_found:
            withhold_draft(draft, draft_found)
        for rewrite, found in zip(rewrites, record_hits[1:]):
            if found:
                rewrite["narrative"] = signal_policy.WITHHELD_TEXT
                rewrite["status"] = "withheld_embedded_instruction"
                withhold_texts(rewrite)
                rewrite["citations"] = sorted(set(rewrite.get("citations", []) + [signal_policy.WITHHOLD_CITATION]))

        if mapping_rejected:
            rejected_mappings += 1
            add_flag(flags, "code_mapping_mismatch", "hold_for_review",
                     f"the supplied code_mapping does not match the code-map rules for this entry and its linked "
                     f"activity; it was discarded and the recomputed mapping ({mapping['recommended_task_code']}, "
                     f"{mapping['basis']}) and its flags are used", [MAPPING_CITATION, "client-billing-guidelines.md #4.1"],
                     0.99)
            entry["code_mapping"] = dict(mapping, supplied_mapping_rejected=True)
        task_code = mapping["recommended_task_code"]
        if any(signal_policy.class_in(c, NON_BILLABLE_CLASSES) for c in classes) or task_code in NON_BILLABLE_TASK_CODES:
            add_flag(flags, "non_billable_activity", "reject", "entry is linked to internal/non-billable activity",
                     ["client-billing-guidelines.md #5.1", "task-phase-codes.md #4.1"], 0.96)

        if not rounded_to_increment(duration):
            add_flag(flags, "rounding_increment", "needs_review", f"{duration} is not rounded to 0.1 hour",
                     ["client-billing-guidelines.md #6.1"], 0.91)
        flags.extend(date_flags)
        if not linked and duration > EVIDENCE_OVERRUN_HOURS:
            add_flag(flags, "no_linked_evidence", "hold_for_review",
                     f"{duration} billed hours has no linked activity evidence (0 hours); the #6.2 tolerance is "
                     f"{EVIDENCE_OVERRUN_HOURS} hours", ["client-billing-guidelines.md #6.2"], 0.9)
        elif linked and duration - evidence_hours > EVIDENCE_OVERRUN_HOURS:
            add_flag(flags, "evidence_overrun", "needs_review",
                     f"{duration} billed hours exceeds {evidence_hours} hours of same-date linked evidence "
                     f"({all_date_hours} hours across all linked dates) by more than {EVIDENCE_OVERRUN_HOURS}",
                     ["client-billing-guidelines.md #6.2"], 0.86)

        for map_flag in mapping["flags"]:
            flags.append(map_flag)
        flags.extend(meeting_flags)

        lowest_conf = min([f.get("confidence", 1.0) for f in flags]
                          + [draft.get("confidence", 1.0), mapping["confidence"]])
        if lowest_conf < CONFIDENCE_FLOOR:
            add_flag(flags, "confidence_floor", "hold_for_review", f"confidence {lowest_conf} below {CONFIDENCE_FLOOR}",
                     ["client-billing-guidelines.md #9.1"], lowest_conf)

        verdict = "compliant"
        for flag in flags:
            sev = flag.get("severity")
            # An unrecognised severity fails closed to hold_for_review, never to needs_review.
            if SEVERITY_ORDER.get(sev, SEVERITY_ORDER["hold_for_review"]) > SEVERITY_ORDER[verdict]:
                verdict = sev
        entry["compliance"] = {
            "verdict": verdict,
            "flags": flags,
            "required_elements": elements,
            "evidence_hours_same_date": evidence_hours,
            "confidence": round(lowest_conf if flags else 0.96, 2),
            "source": GUIDELINE_ENGINE,
            "citations": sorted({c for f in flags for c in f.get("citations", [])})
            or ["client-billing-guidelines.md #1.1", "client-billing-guidelines.md #1.2"],
        }

    missing_signals = [a for a in signals
                       if signal_policy._id_key(a["activity_id"]) not in used_activity_ids
                       and a.get("billable_signal") and a.get("duration_hours", 0) >= MISSING_TIME_MIN_HOURS]
    missing_time = [missing_time_item(a) for a in missing_signals]
    withhold_missing_runs(missing_time, missing_signals)
    exception_list = exception_items(out["time_entries"], missing_time)

    out["missing_time_report"] = missing_time
    out["exception_list"] = exception_list
    excluded = out.get("provenance", {}).get("excluded_signals", [])
    out["prebill_summary"] = {
        "period": out.get("period"),
        **summary_figures(out["time_entries"], missing_time),
        "exception_count": len(exception_list),
        "excluded_signal_ids": [e.get("activity_id") for e in excluded],
        "source": GUIDELINE_ENGINE,
        "confidence": 0.96,
        "citations": ["client-billing-guidelines.md #2.1", "client-billing-guidelines.md #3.1",
                      "client-billing-guidelines.md #8.1", "client-billing-guidelines.md #9.2",
                      "client-billing-guidelines.md #10.1"],
    }
    return rejected_mappings


def _rolled_up(values, key):
    """One value, or "multiple" when the values differ in canonical form (A22: "Morgan Lee" and "  morgan   lee  "
    are one person); the first spelling is shown."""
    return "multiple" if len({key(v) for v in values}) > 1 else values[0]


def exception_items(entries, missing_time):
    """The exception_list, built from the entries' compliance and the missing-time items (#13.2). guideline_check
    writes it and exception_report rebuilds it and compares it item by item (A22), so a changed ID, person, verdict
    or flag in one item is refused, never only counted."""
    items = []
    for entry in entries:
        compliance = entry.get("compliance") or {}
        flags = compliance.get("flags") or []
        if not flags:
            continue
        item = {
            "entry_id": entry.get("entry_id"),
            "person": entry.get("person"),
            "date": entry.get("date"),
            "duration_hours": entry.get("duration_hours"),
            "verdict": compliance.get("verdict"),
            "flags": [f.get("flag") for f in flags],
            "recommended_action": ("rewrite_or_remove_before_prebill" if compliance.get("verdict") == "reject"
                                   else "billing_coordinator_review"),
            "source": GUIDELINE_ENGINE,
            "confidence": compliance.get("confidence"),
            "citations": compliance.get("citations"),
        }
        if entry.get("excluded_activity_ids"):
            item["excluded_activity_ids"] = list(entry["excluded_activity_ids"])
        items.append(item)
    if missing_time:
        items.append({
            "entry_id": None,
            "person": _rolled_up([m.get("person") for m in missing_time], signal_policy.person_key),
            "date": _rolled_up([m.get("date") for m in missing_time], str),
            "duration_hours": round(sum(m["duration_hours"] for m in missing_time), 2),
            "verdict": "missing_time",
            "flags": ["missing_time"] + (["embedded_instruction"] if any(m.get("embedded_instruction")
                                                                         for m in missing_time) else []),
            "recommended_action": "review_activity_and_create_draft_entries_if_billable",
            "source": GUIDELINE_ENGINE,
            "confidence": min(m["confidence"] for m in missing_time),
            "citations": sorted({c for m in missing_time for c in m["citations"]}),
        })
    return items


def summary_figures(entries, missing_time):
    """The prebill_summary figures derived from the line items (#13.2)."""
    counts = {}
    for entry in entries:
        verdict = entry.get("compliance", {}).get("verdict", "unknown")
        counts[verdict] = counts.get(verdict, 0) + 1
    return {
        "total_entries": len(entries),
        "total_hours": round(sum(e.get("duration_hours", 0) for e in entries), 2),
        "verdict_counts": dict(sorted(counts.items())),
        "missing_time_hours": round(sum(m["duration_hours"] for m in missing_time), 2),
    }


def excluded_ids(packet):
    """The excluded signal IDs, derived from provenance.excluded_signals (#10.1)."""
    return [e.get("activity_id") for e in (packet.get("provenance") or {}).get("excluded_signals", [])]


def rendered_flags(recorded, rederived):
    """The flags exception_report prints for one entry (#13.2): the re-run's flags with their re-derived detail
    and citations. check_rederived has already refused any recorded flag that differs from the re-derivation (#13.8),
    so nothing carried is kept; supplied detail and citation text is never printed."""
    return [{"flag": f["flag"], "severity": f["severity"], "detail": f.get("detail", ""),
             "citations": list(f.get("citations", []))} for f in rederived]


# The sections a report-time signal policy could change by excluding evidence (#13.2).
REPORT_POLICY_SECTIONS = ("activity_signals", "time_entries", "missing_time_report", "exception_list", "prebill_summary")


def reconcile_governed(packet, script_dir=None, engine="engine:unknown", config_path=None):
    """The report-time signal policy check, run after check_rederived has matched the whole governed document with
    its re-derivation from the activity packet (#13.8). Returns (problems, rerun); no problems = consistent (#13.2).

    The report's own effective policy (config_path, the report's --signal-config) is applied to a copy, starting from
    drafts re-derived from each entry's evidence (#13.5), and the guideline rules are re-run. A narrower report-time
    policy that excludes evidence an entry was governed on changes a line item or an exclusion record and is refused,
    never rendered as a compliant entry built on excluded evidence; a policy that excludes nothing changes nothing.
    Every other field was already compared whole by check_rederived, so nothing else is reconciled field by field
    here. Messages name sections only, never supplied text.
    """
    rerun = deepcopy(packet)
    signal_policy.derive_drafts(rerun)
    signal_policy.filter_packet(rerun, config_path=config_path, script_dir=script_dir, engine=engine)
    govern(rerun)
    problems = [f"{key} changes when the report's signal policy is applied" for key in REPORT_POLICY_SECTIONS
                if signal_policy.document_differences({key: packet.get(key)}, {key: rerun.get(key)})]
    for key in ("excluded_signals", "excluded_entries"):
        if signal_policy.document_differences({key: (packet.get("provenance") or {}).get(key)},
                                              {key: (rerun.get("provenance") or {}).get(key)}):
            problems.append(f"provenance.{key} changes when the report's signal policy is applied")
    return problems, rerun


# --- Stage derivations and whole-document re-derivation (client-billing-guidelines.md #13.8) ---------------------

def code_stage(packet, stamp, config_path=None, script_dir=None, extra_sources=None,
               version=signal_policy.STAGE_VERSIONS["coded"]):
    """code-map's whole derivation, in place: timekeeper scope (#12.1), signal policy (#10.1), every entry's code
    mapping, provenance. code_map.py and every later stage's re-derivation run this one function."""
    signal_policy.enforce_timekeeper_scope(packet, engine=CODE_MAP_ENGINE)
    signal_policy.filter_packet(packet, config_path=config_path, script_dir=script_dir, engine=CODE_MAP_ENGINE,
                                extra_sources=extra_sources)
    by_id = signal_policy.signal_index(packet["activity_signals"])
    for entry in packet["time_entries"]:
        entry["code_mapping"] = code_mapping(entry, signal_policy.linked_signals(entry, by_id))
    return signal_policy.finish_stage(packet, version, stamp)


def govern_stage(packet, stamp, config_path=None, script_dir=None, extra_sources=None,
                 version=signal_policy.STAGE_VERSIONS["governed"]):
    """guideline-check's whole derivation, in place: timekeeper scope (#12.1), signal policy (#10.1), govern(),
    provenance. Returns govern()'s count of rejected supplied mappings. guideline_check.py and exception_report.py's
    re-derivation run this one function."""
    signal_policy.enforce_timekeeper_scope(packet, engine=GUIDELINE_ENGINE)
    signal_policy.filter_packet(packet, config_path=config_path, script_dir=script_dir, engine=GUIDELINE_ENGINE,
                                extra_sources=extra_sources)
    rejected = govern(packet)
    signal_policy.finish_stage(packet, version, stamp)
    return rejected


UPSTREAM_STAGES = (("drafted", signal_policy.draft_stage), ("coded", code_stage), ("governed", govern_stage))


def rederive(activity, carried, stage, script_dir=None):
    """The document the engines write at `stage` (drafted, coded or governed) from this activity packet: every stage
    up to it re-run in order, each with the run parameters the carried document records (its timestamp and each
    stage's additional signal policy, signal_policy.stage_policy). The stage is fixed by the engine asking, never by
    the carried provenance.engines list."""
    stamp = (carried.get("provenance") or {}).get("generated_at")
    packet = deepcopy(activity)
    for name, run_stage in UPSTREAM_STAGES:
        run_stage(packet, stamp, script_dir=script_dir,
                  extra_sources=signal_policy.stage_policy(carried, name, writer=name == stage))
        if name == stage:
            return packet
    raise ValueError("unknown stage")


def check_rederived(carried, activity, stage, script_dir=None):
    """Refuse a carried document that differs from its re-derivation from the activity packet in any field outside
    signal_policy.NOT_ENGINE_OWNED - missing, extra or changed, provenance included (#13.8). Returns the re-derived
    document. The message counts the differing top-level sections and names no value, field or path."""
    want = rederive(activity, carried, stage, script_dir)
    differ = signal_policy.document_differences(want, carried)
    if differ:
        raise signal_policy.SchemaError(
            f"invalid input: the {stage} packet does not equal its re-derivation from the activity packet "
            f"({differ} top-level section(s) differ; every engine-owned field and section, provenance included, is "
            f"re-derived by re-running the earlier stages and compared whole, {signal_policy.REDERIVE_CITATION}) - no "
            "output was written; re-run the chain from narrative_draft.py on the same activity packet")
    return want
