#!/usr/bin/env python3
"""
rank_column_matches.py — offline ranking helper for the lab-column-mapper skill.

Given a mystery source column (name + optional sample values + optional lab ID)
and a canonical schema JSON file, this script ranks the canonical columns by
how likely they are to be the correct destination — using nothing but the
Python standard library.

It's not a replacement for Azure AI Search's semantic ranker. It's a
lightweight sanity check for makers so they can iterate on their
`column_description` values before wiring up the real index.

Usage:
    python rank_column_matches.py \\
        --source-column "PT_MRN" \\
        --source-samples "MRN-hash-abc,MRN-hash-def" \\
        --canonical-schema canonical_schema.json \\
        --lab-id LAB-QUEST-001 \\
        --top 5

Canonical schema JSON format:
    [
        {
            "canonical_column_name": "patient_mrn",
            "column_description": "Unique medical record number identifying the patient at this health system.",
            "data_type": "nvarchar",
            "clinical_domain": "lab-observations",
            "loinc_code": null,
            "synonyms": ["mrn", "medical record number", "patient number"],
            "previously_mapped_from_labs": ["LAB-QUEST-001", "LAB-LABCORP-001"],
            "example_source_names": ["PT_MRN", "medical_record_number", "pat_id"]
        },
        ...
    ]

Scoring formula (weighted sum, all in [0, 1]):
    0.35 * name_similarity      (source name vs canonical name + synonyms + examples)
    0.40 * description_overlap  (source name/samples token overlap with description)
    0.10 * sample_shape_bonus   (bonus if sample values look like the data type)
    0.15 * lab_history_bonus    (bonus if this canonical was previously mapped from this lab)
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path


# ------------------------------ scoring pieces ------------------------------ #

def tokenize(text: str) -> list[str]:
    """Split a string into lowercase word tokens, tolerant of snake_case,
    camelCase, and separators like _ - . / ."""
    if not text:
        return []
    # Insert spaces between camelCase transitions, then split on non-word chars.
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    parts = re.split(r"[\W_]+", spaced.lower())
    return [p for p in parts if p]


def name_similarity(source_name: str, candidate_names: list[str]) -> float:
    """Return the best fuzzy-match ratio between the source column name and
    any of the candidate names (canonical name + synonyms + example source
    names)."""
    if not candidate_names:
        return 0.0
    src = source_name.lower()
    best = 0.0
    for name in candidate_names:
        if not name:
            continue
        ratio = difflib.SequenceMatcher(None, src, name.lower()).ratio()
        if ratio > best:
            best = ratio
        # Also compare the tokenized forms — helps `PT_MRN` match `patient_mrn`.
        token_ratio = difflib.SequenceMatcher(
            None, " ".join(tokenize(source_name)), " ".join(tokenize(name))
        ).ratio()
        if token_ratio > best:
            best = token_ratio
    return best


def description_overlap(source_tokens: set[str], description: str) -> float:
    """Return the fraction of source tokens that appear in the description,
    scaled by the description's specificity (short descriptions with a high
    match count score higher than long descriptions with the same count)."""
    if not description or not source_tokens:
        return 0.0
    desc_tokens = set(tokenize(description))
    if not desc_tokens:
        return 0.0
    overlap = source_tokens & desc_tokens
    if not overlap:
        return 0.0
    coverage = len(overlap) / len(source_tokens)
    specificity = min(1.0, len(overlap) / max(3.0, len(desc_tokens) ** 0.5))
    return (coverage + specificity) / 2.0


def sample_shape_bonus(samples: list[str], data_type: str) -> float:
    """Give a small bonus when the sample values look like the target data
    type — e.g., ISO dates for datetime2, digits + decimal for decimal."""
    if not samples or not data_type:
        return 0.0

    data_type = data_type.lower()
    hits = 0

    date_pat = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}([ T]\d{1,2}:\d{2})?")
    decimal_pat = re.compile(r"^-?\d+(\.\d+)?$")
    int_pat = re.compile(r"^-?\d+$")

    for s in samples:
        s = (s or "").strip()
        if not s:
            continue
        if "datetime" in data_type or data_type in {"date", "datetime2"}:
            if date_pat.match(s):
                hits += 1
        elif "decimal" in data_type or "float" in data_type or "numeric" in data_type:
            if decimal_pat.match(s):
                hits += 1
        elif "int" in data_type:
            if int_pat.match(s):
                hits += 1
        else:  # string-ish
            if not decimal_pat.match(s) and not date_pat.match(s):
                hits += 1

    return hits / len(samples) if samples else 0.0


def lab_history_bonus(lab_id: str, previously_mapped_from_labs: list[str]) -> float:
    """1.0 if this lab has previously been mapped to this canonical column."""
    if not lab_id or not previously_mapped_from_labs:
        return 0.0
    return 1.0 if lab_id in previously_mapped_from_labs else 0.0


def score_candidate(
    source_column: str,
    source_samples: list[str],
    source_tokens: set[str],
    lab_id: str,
    candidate: dict,
) -> tuple[float, dict]:
    """Return (weighted score in [0, 1], breakdown dict) for a single candidate."""
    candidate_names = [
        candidate.get("canonical_column_name", ""),
        *(candidate.get("synonyms") or []),
        *(candidate.get("example_source_names") or []),
    ]

    n_sim = name_similarity(source_column, candidate_names)
    d_ovl = description_overlap(source_tokens, candidate.get("column_description", ""))
    s_bonus = sample_shape_bonus(source_samples, candidate.get("data_type", ""))
    l_bonus = lab_history_bonus(lab_id, candidate.get("previously_mapped_from_labs") or [])

    weighted = (
        0.35 * n_sim
        + 0.40 * d_ovl
        + 0.10 * s_bonus
        + 0.15 * l_bonus
    )
    return weighted, {
        "name_similarity": round(n_sim, 3),
        "description_overlap": round(d_ovl, 3),
        "sample_shape_bonus": round(s_bonus, 3),
        "lab_history_bonus": round(l_bonus, 3),
    }


# --------------------------------- CLI --------------------------------- #

def load_schema(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Canonical schema JSON must be a list of column objects.")
    return data


def parse_samples(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank canonical destination columns for an unknown source column."
    )
    parser.add_argument("--source-column", required=True,
                        help="The mystery column name (e.g., 'PT_MRN').")
    parser.add_argument("--source-samples", default="",
                        help="Comma-separated de-identified sample values (optional).")
    parser.add_argument("--source-description", default="",
                        help="Human description of the source column, if the lab publishes one (optional).")
    parser.add_argument("--canonical-schema", required=True, type=Path,
                        help="Path to canonical schema JSON.")
    parser.add_argument("--lab-id", default="",
                        help="Sending lab ID (used for the lab-history bonus).")
    parser.add_argument("--top", type=int, default=5,
                        help="How many top candidates to print. Default 5.")
    args = parser.parse_args()

    if not args.canonical_schema.exists():
        print(f"error: canonical schema not found: {args.canonical_schema}",
              file=sys.stderr)
        return 2

    try:
        schema = load_schema(args.canonical_schema)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: could not parse canonical schema: {exc}", file=sys.stderr)
        return 2

    samples = parse_samples(args.source_samples)
    source_tokens = set(
        tokenize(args.source_column) + tokenize(args.source_description)
    )

    ranked = []
    for candidate in schema:
        score, breakdown = score_candidate(
            args.source_column, samples, source_tokens, args.lab_id, candidate
        )
        ranked.append((score, breakdown, candidate))

    ranked.sort(key=lambda t: t[0], reverse=True)
    top = ranked[: args.top]

    print(f"\nSource column: {args.source_column}")
    if args.lab_id:
        print(f"Lab ID:        {args.lab_id}")
    if samples:
        print(f"Samples:       {samples}")
    print(f"Ranked {min(args.top, len(ranked))} of {len(ranked)} canonical columns:\n")

    for rank, (score, breakdown, candidate) in enumerate(top, start=1):
        print(f"  {rank}. {candidate.get('canonical_column_name', '<unnamed>'):32s} "
              f"score={score:.3f}")
        loinc = candidate.get("loinc_code")
        if loinc:
            print(f"     loinc: {loinc}")
        desc = candidate.get("column_description", "")
        if desc:
            print(f"     desc:  {desc[:80]}{'…' if len(desc) > 80 else ''}")
        parts = ", ".join(f"{k}={v}" for k, v in breakdown.items())
        print(f"     parts: {parts}\n")

    if not top:
        print("  (no candidates in the schema)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
