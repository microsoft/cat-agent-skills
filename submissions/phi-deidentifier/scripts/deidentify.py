#!/usr/bin/env python3
"""
PHI De-identifier — HIPAA Safe Harbor / Limited Data Set redaction engine.

Deterministic, offline, standard-library only. Detects the 18 HIPAA Safe Harbor
identifiers (structured ones via regex; names/places via optional NER), replaces
each with a consistent pseudonym token, and emits an audit manifest describing
what was removed and what still needs human review.

Usage:
    python deidentify.py INPUT.txt                     # -> INPUT.deid.txt + INPUT.manifest.json
    python deidentify.py INPUT.txt --mode limited      # Limited Data Set (keeps dates + city/state/zip)
    python deidentify.py --text "John Doe, SSN 123-45-6789"
    python deidentify.py INPUT.txt --map crosswalk.json   # ALSO write reversible token->value map (SENSITIVE)
    python deidentify.py INPUT.txt --json                 # print machine-readable result to stdout

Exit codes: 0 = success, 2 = usage error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# HHS-restricted 3-digit ZIP prefixes: population < 20,000, must become 000.   #
# (Per HIPAA Safe Harbor guidance.)                                            #
# --------------------------------------------------------------------------- #
RESTRICTED_ZIP3 = {
    "036", "059", "063", "102", "203", "556", "692", "790",
    "821", "823", "830", "831", "878", "879", "884", "890", "893",
}

# Category priority: higher wins when spans overlap (structured beats heuristic).
PRIORITY = {
    "SSN": 100, "MRN": 95, "EMAIL": 92, "URL": 90, "IP": 88, "FAX": 86,
    "PHONE": 85, "VIN": 80, "DEVICE_ID": 78, "LICENSE": 76, "ACCOUNT": 74,
    "DATE": 60, "AGE": 58, "STREET": 55, "ZIP": 50, "ORG": 48, "GEO": 40, "NAME": 20,
    "TIME": 59,
}

US_STATES = (
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN "
    "MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA "
    "WV WI WY"
).split()
_STATE_ALT = "|".join(US_STATES)
_STREET_SUFFIX = ("Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|"
                  "Dr|Way|Court|Ct|Place|Pl|Terrace|Ter|Circle|Cir|Highway|"
                  "Hwy|Parkway|Pkwy|Square|Sq|Trail|Trl")
# Street address line: number + 1-4 capitalised words + a street suffix.
STREET_RE = re.compile(
    rf"\b\d{{1,6}}[ \t]+(?:[A-Z][a-zA-Z.'\-]*[ \t]+){{1,4}}(?:{_STREET_SUFFIX})\b\.?")
# City + state, anchored by a following ZIP or a comma (keeps precision high).
CITY_STATE_ZIP_RE = re.compile(
    rf"\b([A-Z][a-zA-Z.'\-]+(?:[ \t][A-Z][a-zA-Z.'\-]+){{0,2}})[ \t]+({_STATE_ALT})\b(?=[ \t]+\d{{5}})")
CITY_STATE_COMMA_RE = re.compile(
    rf"\b([A-Z][a-zA-Z.'\-]+(?:[ \t][A-Z][a-zA-Z.'\-]+){{0,2}})[ \t]*,[ \t]*({_STATE_ALT})\b")
# Two-letter state codes that are ALSO clinical credentials. "Dr. Jane A. Smith,
# MD" must not be mistaken for "City, State" (MD=Maryland, PA=Pennsylvania,
# DC=District of Columbia, DO=osteopath). Guarded by a person-name signal below.
_CREDENTIAL_STATES = {"MD", "DO", "PA", "DC"}
_TITLE_BEFORE_RE = re.compile(r"(?:Dr|Dra|Mr|Mrs|Ms|Mx|Prof|Rev|Doctor|Nurse)\.?[ \t]+$")
_EMBEDDED_INITIAL_RE = re.compile(r"\b[A-Z]\.")


@dataclass
class Span:
    start: int
    end: int
    label: str
    value: str
    detector: str  # "regex" | "ner" | "heuristic" | "lexicon" | "model" | "field" | "unknown"
    confidence: str = "high"  # high | review
    flag_only: bool = False  # flagged for human review but NOT auto-redacted


@dataclass
class Result:
    text: str
    spans: list = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    crosswalk: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Regex detectors for the structured Safe Harbor identifiers.                  #
# --------------------------------------------------------------------------- #
_MONTHS = (r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
           r"[a-z]*")

REGEX_DETECTORS = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("URL", re.compile(r"\bhttps?://[^\s<>\"')]+", re.I)),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    # SSN — dashed, spaced, or labelled (the label form also catches 9 straight
    # digits, e.g. "SSN 123456789"). A bare, unlabelled 9-digit run is NOT
    # force-matched here (too many false positives); it surfaces instead via the
    # long-number review net below.
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("SSN", re.compile(r"\b\d{3}[ \t]\d{2}[ \t]\d{4}\b")),
    ("SSN", re.compile(r"\b(?:SSN|Social\s+Security(?:\s+(?:No\.?|Number|#))?)\s*[:#]?\s*(\d{3}[- \t]?\d{2}[- \t]?\d{4})\b", re.I)),
    # MRN: labeled medical record number OR "MRN" token followed by digits.
    ("MRN", re.compile(r"\b(?:MRN|Medical\s+Record\s+(?:No\.?|Number|#))\s*[:#]?\s*([A-Z0-9\-]{4,})\b", re.I)),
    ("FAX", re.compile(r"\bfax\s*[:#]?\s*(\+?\d[\d\-().\s]{7,}\d)\b", re.I)),
    # Phone: (a) the strict US shape (area code + separators), (b) any number
    # with a leading + country code, and (c) a number that follows a phone label
    # (catches run-together 10-digit and international formats the strict pattern
    # misses). Whitespace is limited to spaces/tabs so a match never spans lines.
    ("PHONE", re.compile(r"(?<!\d)(?:\+?1[\s.\-]?)?(?:\(\d{3}\)|\d{3})[\s.\-]\d{3}[\s.\-]\d{4}(?!\d)")),
    ("PHONE", re.compile(r"(?<!\w)\+\d[\d().\-\t ]{6,}\d(?!\w)")),
    ("PHONE", re.compile(r"\b(?:phone|tel|telephone|mobile|cell|call|contact)\s*(?:no\.?|number|#)?\s*[:#]?\s*(\+?\d[\d().\-\t ]{6,}\d)", re.I)),
    ("TIME", re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b")),
    ("VIN", re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")),
    # Device / serial / certificate / license numbers when explicitly labeled.
    # A digit is required in the captured value so plain words (e.g. a name after
    # "Member:") are not mistaken for an identifier code.
    ("DEVICE_ID", re.compile(r"\b(?:serial|device|implant)\s*(?:no\.?|number|#|id)?\s*[:#]?\s*((?=[A-Z0-9\-]*\d)[A-Z0-9\-]{5,})\b", re.I)),
    ("LICENSE", re.compile(r"\b(?:license|licence|cert(?:ificate)?|DEA|NPI)\s*(?:no\.?|number|#)?\s*[:#]?\s*((?=[A-Z0-9\-]*\d)[A-Z0-9\-]{5,})\b", re.I)),
    ("ACCOUNT", re.compile(r"\b(?:account|acct|beneficiary|policy|member)\s*(?:no\.?|number|#|id)?\s*[:#]?\s*((?=[A-Z0-9\-]*\d)[A-Z0-9\-]{5,})\b", re.I)),
    # Prefixed identifier codes (member/account/case/auth numbers) that appear
    # without a clean label or with filler words, e.g. "Acc# ACC-7781233",
    # "member ID is MEM-4459087", "Case: SP-24-00891". 2-6 leading capitals,
    # optional 2+ digit segments, ending in a >=4 digit run (so "COVID-19" is
    # NOT matched but multi-part case numbers are captured in full).
    ("ACCOUNT", re.compile(r"\b[A-Z]{2,6}-(?:\d{2,}-)*\d{4,}\b")),
    # Employer / organization name when tied to the individual by an employment
    # context word. Employer names are a Safe Harbor "name" identifier. Keywords
    # are matched case-sensitively so the captured org phrase stays capital-anchored
    # (a lone capitalized proper-noun run of 1-5 tokens).
    ("ORG", re.compile(r"\b(?:[Ee]mployer|[Ee]mployed\s+by|[Ww]orks?\s+(?:at|for))(?:\s+is)?\s*:?\s+([A-Z][\w&'\-]*(?:\s+[A-Z][\w&'\-]*){0,4})")),
    # Dates: numeric and long-form. Year captured where present.
    ("DATE", re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b")),
    ("DATE", re.compile(rf"\b{_MONTHS}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I)),
    ("DATE", re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTHS}\.?,?\s+(\d{{4}})\b", re.I)),
    # Ages 90+ (Safe Harbor: aggregate everything over 89).
    ("AGE", re.compile(r"\b(\d{2,3})\s*(?:-|\s)?(?:year|yr|y)s?(?:[\s\-]?old)?\b", re.I)),
    ("AGE", re.compile(r"\bage[d]?\s*[:#]?\s*(\d{2,3})\b", re.I)),
    # ZIP (5 or ZIP+4).
    ("ZIP", re.compile(r"\b(\d{5})(?:-\d{4})?\b")),
]

TITLE_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Miss|Dr|Prof|Rev|Sir|Dame|Fr|Capt|Lt|Sgt)\.?[ \t]+"
    r"([A-Z](?:\.|[a-zA-Z'\-]+)(?:[ \t][A-Z](?:\.|[a-zA-Z'\-]+)){0,3})"
)
# Labelled fields REQUIRE a colon/hash separator so role words that merely sit
# next to each other ("Referring physician") are not mistaken for names.
# Single-space word joins so a name never bleeds across a column gap or newline.
LABELED_NAME_RE = re.compile(
    r"\b(?:patient|name|physician|provider|doctor|nurse|guardian|"
    r"emergency\s+contact|next\s+of\s+kin|referring(?:\s+physician)?)[ \t]*[:#][ \t]*"
    r"((?:(?:Mr|Mrs|Ms|Miss|Dr|Prof|Rev)\.?[ \t]+)?"
    r"[A-Z](?:\.|[a-zA-Z'\-]+)(?:[ \t][A-Z](?:\.|[a-zA-Z'\-]+)){0,3})",
    re.I,
)
# Role / title tokens that must never survive as a "name" on their own.
NAME_STOPWORDS = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "rev", "sir", "dame", "fr",
    "capt", "lt", "sgt", "patient", "name", "physician", "provider",
    "doctor", "nurse", "guardian", "contact", "emergency", "referring",
    "next", "kin", "of",
}
_LEADING_TITLE_RE = re.compile(
    r"^(?:(?:Mr|Mrs|Ms|Miss|Dr|Prof|Rev|Sir|Dame|Fr|Capt|Lt|Sgt)\.?[ \t]+)+")


def _clean_name(value: str, start: int) -> tuple[str, int] | None:
    """Strip leading titles and reject role-word-only captures."""
    m = _LEADING_TITLE_RE.match(value)
    if m:
        start += m.end()
        value = value[m.end():]
    value = value.strip()
    if not value:
        return None
    tokens = [t for t in re.split(r"\s+", value)]
    if all(t.lower().strip(".,") in NAME_STOPWORDS for t in tokens):
        return None
    return value, start


def _year_of(m: re.Match) -> str | None:
    for g in reversed(m.groups() or ()):
        if g and re.fullmatch(r"\d{4}", g):
            return g
        if g and re.fullmatch(r"\d{2}", g):
            n = int(g)
            return ("19" if n > 30 else "20") + g
    return None


def find_regex_spans(text: str) -> list:
    spans = []
    for label, rx in REGEX_DETECTORS:
        for m in rx.finditer(text):
            # Use the captured group when the detector has one (value lives there).
            if m.groups():
                gi = 1
                start, end = m.start(gi), m.end(gi)
                value = m.group(gi)
            else:
                start, end, value = m.start(), m.end(), m.group(0)

            if label == "AGE":
                try:
                    if int(value) <= 89:
                        continue  # ages <=89 are permitted
                except ValueError:
                    continue
                spans.append(Span(start, end, "AGE", value, "regex"))
            elif label == "DATE":
                spans.append(Span(m.start(), m.end(), "DATE",
                                  m.group(0), "regex"))
                spans[-1].value = m.group(0)
                spans[-1].confidence = "high"
                spans[-1].year = _year_of(m)  # type: ignore[attr-defined]
            elif label == "ZIP":
                spans.append(Span(m.start(1), m.end(1), "ZIP", value, "regex"))
            else:
                spans.append(Span(start, end, label, value, "regex"))
    return spans


def find_geo_spans(text: str) -> list:
    """Street addresses (removed in every mode) and city/state (kept in LDS)."""
    spans = []
    for m in STREET_RE.finditer(text):
        spans.append(Span(m.start(), m.end(), "STREET", m.group(0), "regex"))
    # Redact the CITY (a subdivision smaller than a state) but leave the state
    # itself, which HIPAA Safe Harbor permits to be retained.
    for m in CITY_STATE_ZIP_RE.finditer(text):
        spans.append(Span(m.start(1), m.end(1), "GEO",
                          text[m.start(1):m.end(1)], "regex"))
    for m in CITY_STATE_COMMA_RE.finditer(text):
        city = text[m.start(1):m.end(1)]
        before = text[max(0, m.start(1) - 8):m.start(1)]
        if m.group(2).upper() in _CREDENTIAL_STATES and \
           (_TITLE_BEFORE_RE.search(before) or _EMBEDDED_INITIAL_RE.search(city)):
            continue  # a physician credential ("… Smith, MD"), not City, State
        spans.append(Span(m.start(1), m.end(1), "GEO", city, "regex"))
    return spans


def _load_name_lexicon() -> set:
    """Bundled offline gazetteer of common given names / surnames / nicknames."""
    path = Path(__file__).resolve().parent.parent / "assets" / "name_lexicon.txt"
    names = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                names.add(line.lower())
    except Exception:
        pass
    return names


_NAME_LEXICON = _load_name_lexicon()
_CAP_WORD_RE = re.compile(r"\b[A-Z][a-z]+\b")


def find_name_spans(text: str) -> list:
    spans = []

    # (a) High-precision: names after a title or in a labelled field.
    for rx in (TITLE_RE, LABELED_NAME_RE):
        for m in rx.finditer(text):
            cleaned = _clean_name(m.group(1), m.start(1))
            if cleaned is None:
                continue
            value, start = cleaned
            spans.append(Span(start, start + len(value), "NAME", value,
                              "heuristic", confidence="review"))

    # (b) Offline lexicon: catches BARE names in free prose with no title/label.
    #     Fully local, no network or extra packages — works in locked sandboxes.
    if _NAME_LEXICON:
        for m in _CAP_WORD_RE.finditer(text):
            if m.group(0).lower() in _NAME_LEXICON:
                spans.append(Span(m.start(), m.end(), "NAME", m.group(0),
                                  "lexicon", confidence="review"))

    # (c) Optional bonus: high-quality NER ONLY if the runtime already provides
    #     spaCy. Never assume it can be installed — many agent sandboxes block
    #     pip and network. Its absence changes nothing about steps (a)/(b).
    try:
        import spacy  # type: ignore
        nlp = spacy.load("en_core_web_sm")
        for ent in nlp(text).ents:
            if ent.label_ == "PERSON":
                spans.append(Span(ent.start_char, ent.end_char, "NAME",
                                  ent.text, "ner"))
            elif ent.label_ in ("GPE", "LOC", "FAC"):
                spans.append(Span(ent.start_char, ent.end_char, "GEO",
                                  ent.text, "ner"))
    except Exception:
        pass

    return spans


def resolve_overlaps(spans: list) -> list:
    def pr(s):
        return -1 if s.flag_only else PRIORITY.get(s.label, 0)
    spans = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    kept: list = []
    for s in spans:
        conflict = False
        for k in kept:
            if s.start < k.end and k.start < s.end:  # overlap
                if pr(s) > pr(k):
                    kept.remove(k)
                else:
                    conflict = True
                break
        if not conflict:
            kept.append(s)
    return sorted(kept, key=lambda s: s.start)


# Identifiers dropped entirely in a Limited Data Set (dates + geo are allowed).
LDS_KEEP = {"DATE", "AGE", "ZIP", "GEO", "TIME"}


def _hash(value: str, salt: str) -> str:
    h = hashlib.sha256((salt + "\x00" + value.strip().lower()).encode()).hexdigest()
    return "sha256:" + h[:16]


# --------------------------------------------------------------------------- #
# STAGE 2 bridge — accept name/place candidates found by the agent (the model  #
# recall pass) and turn every occurrence into a redacting span. In a locked    #
# sandbox the script cannot call an LLM, so the agent runs the recall and      #
# feeds its findings back in here. Detector = "model".                         #
# --------------------------------------------------------------------------- #
def add_model_spans(text: str, names=None, places=None, orgs=None) -> list:
    spans = []
    # names/places are Safe Harbor identifiers -> redact. orgs (facility/employer
    # names) are NOT individual identifiers -> FLAG for review, never auto-redact
    # (prevents clobbering clinical terms like "Neurology" in "Lakeside Neurology").
    for values, label, flag in ((names, "NAME", False), (places, "GEO", False),
                                (orgs, "ORG", True)):
        for raw in (values or []):
            v = (raw or "").strip()
            if len(v) < 2:
                continue
            for m in re.finditer(r"(?<!\w)" + re.escape(v) + r"(?!\w)", text):
                spans.append(Span(m.start(), m.end(), label, v, "model",
                                  confidence="review", flag_only=flag))
    return spans


# --------------------------------------------------------------------------- #
# STAGE 4 safety net — flag UNKNOWN capitalised word-pairs ("Rafael Alcaraz")  #
# that neither the lexicon nor the model claimed, so a silent miss becomes a   #
# review item instead of a leak. By default these are FLAGGED, not redacted.   #
# --------------------------------------------------------------------------- #
_COMMON_CAP = {
    "the", "a", "an", "and", "or", "but", "if", "then", "this", "that", "these",
    "those", "he", "she", "they", "we", "you", "his", "her", "their", "our",
    "your", "it", "there", "here", "when", "where", "which", "who", "will",
    "patient", "discussed", "reviewed", "recommend", "recommended", "follow",
    "following", "seen", "continue", "continues", "continued", "start",
    "started", "stop", "stopped", "plan", "note", "history", "exam",
    "assessment", "diagnosis", "impression", "labs", "lab", "results", "result",
    "no", "yes", "none", "normal", "stable", "denies", "reports", "per", "with",
    "without", "daily", "weekly", "monthly", "morning", "evening", "night",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    "diabetes", "hypertension", "cardiology", "endocrinology", "oncology",
    "neurology", "radiology", "pathology", "pediatrics", "psychiatry",
    "emergency", "department", "hospital", "clinic", "unit", "room", "floor",
    "metformin", "insulin", "aspirin", "lisinopril", "atorvastatin",
    "type", "stage", "grade", "left", "right", "chest", "blood", "pressure",
    "heart", "rate", "temperature", "weight", "height", "medical", "record",
    "chief", "complaint", "present", "illness", "social", "family", "surgical",
    "current", "medications", "allergies", "vitals", "physical", "discharge",
    "admission", "referral", "summary", "report", "final", "primary",
    "secondary", "chronic", "acute", "mild", "moderate", "severe", "next",
    "prior", "recent", "new", "old", "care", "team", "service", "provider",
    "attending", "resident", "consult", "reason", "date", "time",
}
_CAP_TOKEN = r"[A-Z][a-zA-Z'\u2019\-]+"
_CAP_PAIR_RE = re.compile(rf"\b({_CAP_TOKEN})[ \t]+({_CAP_TOKEN})\b")


def find_unknown_cap_spans(text: str) -> list:
    """Consecutive capitalised words that read like a full name but were not
    otherwise detected. High-signal, low-noise heuristic for the review net."""
    spans = []
    for m in _CAP_PAIR_RE.finditer(text):
        w1, w2 = m.group(1).lower(), m.group(2).lower()
        if w1 in _COMMON_CAP or w2 in _COMMON_CAP:
            continue
        if w1 in NAME_STOPWORDS or w2 in NAME_STOPWORDS:
            continue
        spans.append(Span(m.start(), m.end(), "NAME", m.group(0), "unknown",
                          confidence="review", flag_only=True))
    return spans


# Long bare digit runs (>=7) that carried no label the detectors could anchor
# on — e.g. an unlabelled account / record / SSN / device or phone number.
_LONG_NUM_RE = re.compile(r"(?<!\w)\d{7,}(?!\w)")


def find_unknown_number_spans(text: str) -> list:
    """Long unlabelled digit sequences that look like an identifier but weren't
    matched by any structured detector. Flagged for human review so a silent
    miss becomes a review item instead of a leak; never auto-redacted (a bare
    number can be a legitimate non-PHI value, so a human confirms)."""
    return [Span(m.start(), m.end(), "NUM", m.group(0), "unknown-number",
                 confidence="review", flag_only=True)
            for m in _LONG_NUM_RE.finditer(text)]


def _all_spans(text, model=None, flag_unknown=False, redact_unknown=False):
    """Gather every candidate span for a free-text segment (all stages)."""
    spans = find_regex_spans(text) + find_geo_spans(text) + find_name_spans(text)
    if model:
        spans += add_model_spans(text, model.get("names"), model.get("places"),
                                 model.get("orgs"))
    real = resolve_overlaps(spans)

    if flag_unknown or redact_unknown:
        occupied = [(s.start, s.end) for s in real]

        def _free(u):
            return not any(u.start < e and st < u.end for st, e in occupied)

        for u in find_unknown_cap_spans(text):
            if not _free(u):
                continue
            if redact_unknown:
                u.flag_only = False
            real.append(u)
        # Long unlabelled numbers are always flagged-only (redact_unknown is
        # name-specific): surface them for review without corrupting real data.
        for u in find_unknown_number_spans(text):
            if _free(u):
                real.append(u)
    return real


def _apply_mode(spans, mode):
    if mode != "limited":
        return spans
    # Limited Data Set keeps dates/age/zip/city-state but still removes names,
    # street, and direct contact identifiers.
    return [s for s in spans if s.label not in LDS_KEEP or s.flag_only]


# Field-name -> forced identifier label, for STAGE 0/1 structured records.
def _field_label(key: str):
    k = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).replace("_", " ").replace("-", " ").lower()
    if re.search(r"\b(street|address|addr|line1|line2|line 1|line 2)\b", k):
        return "STREET"
    if re.search(r"\b(zip|postal|postcode)\b", k):
        return "ZIP"
    if re.search(r"\b(email|e mail)\b", k):
        return "EMAIL"
    if re.search(r"\b(fax)\b", k):
        return "FAX"
    if re.search(r"\b(phone|mobile|cell|tel|telephone)\b", k):
        return "PHONE"
    if re.search(r"\b(ssn|social security)\b", k):
        return "SSN"
    if re.search(r"\b(mrn|medical record|record no|record number)\b", k):
        return "MRN"
    if re.search(r"\b(dob|birth ?date|date of birth)\b", k):
        return "DATE"
    if re.search(r"\b(city|county|town)\b", k):
        return "GEO"
    if re.search(r"\b(state|province)\b", k):
        return None  # state may be retained under Safe Harbor — do not redact
    if re.search(r"\b(employer|workplace|work place|company name|works? at)\b", k):
        return "ORG"  # employer/workplace tied to an individual is an identifier
    if re.search(r"\b(hospital|facility|org|organization|organisation|company)\b", k):
        return None  # facility/org names are not Safe Harbor individual identifiers
    if re.search(r"\b(name|patient|member|subscriber|guardian|provider|"
                 r"physician|doctor|nurse|kin|referring|caregiver|attending)\b", k) \
            and not re.search(r"\b(id|number|no|code)\b", k):
        return "NAME"
    return None


class _Redactor:
    """Holds tokenisation state so tokens stay consistent across many text
    segments (needed for structured records) and runs the guard + manifest."""

    def __init__(self, mode: str, salt: str):
        self.mode = mode
        self.salt = salt
        self.counters: dict = {}
        self.token_for: dict = {}
        self.crosswalk: dict = {}
        self.summary: dict = {}
        self.review: list = []
        self.released: list = []          # redacted output parts (for the guard)
        self.sensitive: dict = {}         # label -> {originals that must vanish}
        self.detectors: set = set()

    def _norm(self, label, value):
        v = re.sub(r"\s+", " ", value.strip())
        return v.lower() if label in ("NAME", "EMAIL", "GEO") else v

    def _token_of(self, s: Span) -> str:
        if s.label == "DATE" and self.mode != "limited":
            yr = getattr(s, "year", None)
            return f"[DATE:{yr}]" if yr else "[DATE]"
        if s.label == "AGE":
            return "[AGE:90+]"
        if s.label == "TIME":
            return "[TIME]"
        if s.label == "ZIP":
            z3 = s.value[:3]
            return "[ZIP:000]" if z3 in RESTRICTED_ZIP3 else f"[ZIP:{z3}XX]"
        key = (s.label, self._norm(s.label, s.value))
        if key not in self.token_for:
            self.counters[s.label] = self.counters.get(s.label, 0) + 1
            self.token_for[key] = f"[{s.label}-{self.counters[s.label]}]"
        return self.token_for[key]

    def apply(self, text: str, spans: list) -> str:
        redacting = sorted((s for s in spans if not s.flag_only), key=lambda s: s.start)
        out, cursor = [], 0
        for s in redacting:
            if s.start < cursor:      # overlap guard after cross-stage merges
                continue
            out.append(text[cursor:s.start])
            tok = self._token_of(s)
            out.append(tok)
            cursor = s.end
            self.summary[s.label] = self.summary.get(s.label, 0) + 1
            self.crosswalk.setdefault(tok, s.value)
            self.detectors.add(s.detector)
            if s.label not in ("DATE", "AGE", "ZIP", "TIME"):
                self.sensitive.setdefault(s.label, set()).add(s.value.strip())
            if s.confidence == "review":
                self.review.append({
                    "token": tok, "label": s.label, "detector": s.detector,
                    "value_hash": _hash(s.value, self.salt),
                    "reason": ("model/name recall match — verify no PHI missed "
                               "or over-redacted")})
        out.append(text[cursor:])
        red = "".join(out)
        for s in (s for s in spans if s.flag_only):     # flagged, not redacted
            self.detectors.add(s.detector)
            if s.detector == "unknown-number":
                reason = ("unlabelled long digit run — confirm whether it is an "
                          "identifier (account / record / SSN / device / phone) "
                          "to redact")
            elif s.label == "ORG":
                reason = ("organisation / facility name candidate — not an "
                          "individual identifier; confirm before sharing")
            else:
                reason = ("unrecognised capitalised name-like text was NOT "
                          "auto-redacted — a human must confirm/redact it")
            self.review.append({
                "token": None, "label": s.label, "detector": s.detector,
                "value_hash": _hash(s.value, self.salt),
                "reason": reason})
        self.released.append(red)
        return red

    def guard(self) -> dict:
        released = "\n".join(self.released)
        leaks = []
        for label, vals in self.sensitive.items():
            for v in vals:
                if not v.strip():
                    continue
                if re.search(r"(?<!\w)" + re.escape(v.strip()) + r"(?!\w)",
                             released, re.I):
                    leaks.append({"label": label, "value_hash": _hash(v, self.salt)})
        return {"verified": not leaks,
                "originals_checked": sum(len(v) for v in self.sensitive.values()),
                "leaks": leaks}

    def manifest(self) -> dict:
        return {
            "tool": "phi-deidentifier",
            "mode": "HIPAA Limited Data Set" if self.mode == "limited"
                    else "HIPAA Safe Harbor",
            "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "summary": {**{k: self.summary[k] for k in sorted(self.summary)},
                        "total": sum(self.summary.values())},
            "redactions": [
                {"token": tok, "label": tok.split(":")[0].strip("[]").split("-")[0],
                 "value_hash": _hash(orig, self.salt)}
                for tok, orig in self.crosswalk.items()],
            "needs_human_review": self.review,
            "guard": self.guard(),
            "notes": _notes(self.detectors),
        }


def redact(text: str, mode: str, salt: str, model=None,
           flag_unknown: bool = True, redact_unknown: bool = False) -> Result:
    spans = _apply_mode(_all_spans(text, model, flag_unknown, redact_unknown), mode)
    r = _Redactor(mode, salt)
    red = r.apply(text, spans)
    return Result(red, spans, r.manifest(), r.crosswalk)


def redact_record(record: dict, mode: str, salt: str, model=None,
                  flag_unknown: bool = True, redact_unknown: bool = False) -> Result:
    """STAGE 0/1 — de-identify a structured record. Fields whose NAME the schema
    identifies as PHI-bearing are redacted by field map (no guessing); every
    string value also runs the free-text pipeline to catch embedded IDs."""
    r = _Redactor(mode, salt)
    out = {}
    for key, val in record.items():
        if not isinstance(val, str) or not val.strip():
            out[key] = val
            continue
        forced = _field_label(key)
        if forced in ("NAME", "STREET", "ORG") or \
           (forced == "GEO" and mode != "limited"):
            spans = [Span(0, len(val), forced, val, "field", confidence="review")]
        elif forced in ("EMAIL", "PHONE", "FAX", "SSN", "MRN", "ZIP", "DATE", "GEO"):
            spans = _apply_mode(_all_spans(val, model, flag_unknown, redact_unknown), mode)
            if not any(not s.flag_only for s in spans):   # field says PHI; force it
                keep = mode != "limited" or forced not in LDS_KEEP
                if keep:
                    sp = Span(0, len(val), forced, val, "field")
                    if forced == "DATE":
                        sp.year = _year_of_str(val)  # type: ignore[attr-defined]
                    spans = [sp]
        else:
            spans = _apply_mode(_all_spans(val, model, flag_unknown, redact_unknown), mode)
        out[key] = r.apply(val, spans)
    return Result(json.dumps(out, indent=2, ensure_ascii=False), [], r.manifest(),
                  r.crosswalk)


def _year_of_str(value: str):
    m = re.search(r"\b(\d{4})\b", value)
    if m:
        return m.group(1)
    m = re.search(r"\b\d{1,2}[/\-]\d{1,2}[/\-](\d{2})\b", value)
    if m:
        n = int(m.group(1))
        return ("19" if n > 30 else "20") + m.group(1)
    return None


def _notes(detectors) -> list:
    used_ner = "ner" in detectors
    used_model = "model" in detectors
    used_field = "field" in detectors
    used_unknown = "unknown" in detectors
    used_unknown_num = "unknown-number" in detectors
    notes = [
        "Structured identifiers (SSN, MRN, phone, fax, email, URL, IP, dates, "
        "ZIP, street/city-state, account/license/device numbers) are matched "
        "deterministically by regex — the reproducible, auditable core.",
        "Ages <=89 are retained; 90+ is aggregated to '90+' per Safe Harbor.",
        "ZIP is truncated to its first 3 digits; restricted low-population "
        "prefixes are zeroed to 000.",
    ]
    if used_field:
        notes.append(
            "Structured record: fields the schema marks as PHI-bearing "
            "(patient/provider name, address, city/state) were redacted by "
            "field map — no guessing required.")
    notes.append(
        "Names in free text are found by (a) title/label patterns, (b) a bundled "
        "offline lexicon (assets/name_lexicon.txt), and (c) a model/agent recall "
        "pass whose findings are passed in as candidates" +
        (" — used in this run." if used_model else " (none supplied this run).") +
        (" spaCy NER was present and also applied." if used_ner else ""))
    if used_unknown:
        notes.append(
            "Unrecognised capitalised name-like text was FLAGGED under "
            "needs_human_review but NOT auto-redacted, so silent misses surface "
            "for a human instead of leaking.")
    if used_unknown_num:
        notes.append(
            "Long unlabelled digit sequences (>=7 digits) that resemble an "
            "account / record / SSN / device or phone number were FLAGGED under "
            "needs_human_review but NOT auto-redacted — confirm whether each is "
            "an identifier to remove.")
    notes.append(
        "A qualified human must review before release. This tool does not, on "
        "its own, satisfy the Safe Harbor 'no actual knowledge' clause "
        "(45 CFR 164.514(b)(2)(ii)) and does not perform Expert Determination. "
        "Extend assets/name_lexicon.txt for your population/locale.")
    return notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="HIPAA Safe Harbor PHI de-identifier.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("input", nargs="?", help="Path to a UTF-8 text or JSON file.")
    src.add_argument("--text", help="Inline text to de-identify.")
    ap.add_argument("--mode", choices=["safe-harbor", "limited"],
                    default="safe-harbor")
    ap.add_argument("--format", choices=["auto", "text", "record"], default="auto",
                    help="Treat input as free text or a structured JSON record.")
    ap.add_argument("--salt", default="phi-deid",
                    help="Salt for value hashes in the manifest.")
    ap.add_argument("--names", help="Comma-separated person names the model/agent "
                    "recall pass found (STAGE 2).")
    ap.add_argument("--names-file", dest="names_file",
                    help="JSON file with {\"names\":[...], \"places\":[...], "
                         "\"orgs\":[...]} from the model recall pass.")
    ap.add_argument("--flag-unknown-names", dest="flag_unknown",
                    action="store_true", default=True,
                    help="Flag (not redact) unknown capitalised name-like text "
                         "for review [default].")
    ap.add_argument("--no-flag-unknown-names", dest="flag_unknown",
                    action="store_false")
    ap.add_argument("--redact-unknown-names", dest="redact_unknown",
                    action="store_true",
                    help="Aggressively REDACT unknown capitalised name-like text.")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 3 if the guard finds any original value surviving.")
    ap.add_argument("-o", "--out", help="Output path for redacted text.")
    ap.add_argument("--manifest", help="Output path for the audit manifest JSON.")
    ap.add_argument("--map", dest="mapfile",
                    help="ALSO write a reversible token->value crosswalk "
                         "(SENSITIVE — re-identifying; store securely).")
    ap.add_argument("--json", action="store_true",
                    help="Print {redacted, manifest} to stdout as JSON.")
    args = ap.parse_args(argv)
    mode = "limited" if args.mode == "limited" else "safe-harbor"

    # STAGE 2 candidates from the model/agent recall pass.
    model = {"names": [], "places": [], "orgs": []}
    if args.names:
        model["names"] += [n.strip() for n in args.names.split(",") if n.strip()]
    if args.names_file:
        try:
            data = json.loads(Path(args.names_file).read_text(encoding="utf-8"))
            for k in ("names", "places", "orgs"):
                model[k] += list(data.get(k, []) or [])
        except Exception as e:
            print(f"error: could not read names-file: {e}", file=sys.stderr)
            return 2
    model = model if any(model.values()) else None

    if args.text is not None:
        raw, stem = args.text, None
    else:
        p = Path(args.input)
        if not p.is_file():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 2
        raw = p.read_text(encoding="utf-8", errors="replace")
        stem = p

    is_record = args.format == "record" or (
        args.format == "auto" and stem is not None
        and stem.suffix.lower() == ".json")
    if is_record:
        try:
            record = json.loads(raw)
        except Exception as e:
            print(f"error: input is not valid JSON: {e}", file=sys.stderr)
            return 2
        res = redact_record(record, mode, args.salt, model,
                            args.flag_unknown, args.redact_unknown)
    else:
        res = redact(raw, mode, args.salt, model,
                     args.flag_unknown, args.redact_unknown)

    if args.json:
        print(json.dumps({"redacted": res.text, "manifest": res.manifest},
                         indent=2))
        guard = res.manifest.get("guard", {})
        return 3 if (args.strict and not guard.get("verified", True)) else 0

    out_path = Path(args.out) if args.out else (
        stem.with_suffix(".deid.txt") if stem else None)
    man_path = Path(args.manifest) if args.manifest else (
        stem.with_suffix(".manifest.json") if stem else None)

    if out_path:
        out_path.write_text(res.text, encoding="utf-8")
        print(f"redacted -> {out_path}")
    else:
        print(res.text)
    if man_path:
        man_path.write_text(json.dumps(res.manifest, indent=2), encoding="utf-8")
        print(f"manifest -> {man_path}")
    if args.mapfile:
        Path(args.mapfile).write_text(json.dumps(res.crosswalk, indent=2),
                                      encoding="utf-8")
        print(f"crosswalk (SENSITIVE) -> {args.mapfile}")

    s = res.manifest["summary"]
    print(f"redacted {s['total']} identifier(s): "
          + ", ".join(f"{k}={v}" for k, v in s.items() if k != "total"))
    review = res.manifest["needs_human_review"]
    if review:
        print(f"WARNING: {len(review)} span(s) need human review.")
    guard = res.manifest.get("guard", {})
    if guard.get("verified"):
        print(f"GUARD: OK — 0 of {guard.get('originals_checked', 0)} original "
              f"identifiers survive in the released text.")
    else:
        print(f"GUARD: FAIL — {len(guard.get('leaks', []))} original "
              f"identifier(s) still present in the output.")
        if args.strict:
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
