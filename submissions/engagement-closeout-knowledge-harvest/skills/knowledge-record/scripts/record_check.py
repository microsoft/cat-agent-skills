#!/usr/bin/env python3
"""record_check - knowledge-record skeleton and draft check (knowledge-record skill).

Reads sanitize_check output and re-derives it in full (an edited or foreign payload is refused).
--skeleton-out writes the deterministic knowledge-record skeleton: every line is fixed by the
governed payload except the <<CONTEXT ...>> and <<LESSON ...>> slot lines the drafter fills.
--draft checks a filled draft: fixed lines must be unchanged, each slot must hold one line of
generalized prose, and no slot may carry an embedded instruction, a withheld marker, the client
identity or descriptor, a sector-and-region pair, a date, the headcount, a product, a named person,
held material, copied stage guidance or copied source wording (confidentiality-sanitisation-rules.md
#8.5). No network, no model calls, no side effects beyond --skeleton-out.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import closeout_core as core  # noqa: E402

MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december"
          "|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
DATE_PATTERNS = (
    re.compile(r"\b\d{4}-\d{1,2}(?:-\d{1,2})?\b"),
    re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"),
    re.compile(rf"\b(?:{MONTHS})\.?\s+(?:\d{{1,2}},?\s+)?\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b\d{{1,2}}\s+(?:{MONTHS})\.?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b(?:q[1-4]|h[12])\s*'?\d{2,4}\b", re.IGNORECASE),
)


def shingles(text, size):
    tokens = core.words(core.strip_placeholders(text))
    if len(tokens) < size:
        return set()
    return {" ".join(tokens[i:i + size]) for i in range(len(tokens) - size + 1)}


def phrase_in(phrase, text):
    """Whole-word canonical phrase match."""
    needle = " ".join(core.words(phrase))
    return bool(needle) and f" {needle} " in f" {' '.join(core.words(text))} "


SOURCE_SHINGLE = 6
# Single-word source values that carry no wording of their own (a register's status or filler).
STRUCTURAL_TOKENS = frozenset({
    "n/a", "na", "none", "nil", "tbc", "tbd", "yes", "no", "true", "false", "pending", "complete", "completed",
    "draft", "open", "closed", "unknown", "other", "various", "see", "above", "below",
})
_ID_TOKEN = re.compile(r"[A-Za-z0-9]+(?:[._:-][A-Za-z0-9]+)*")


def trivial_source(value):
    """A source value too short to carry wording: a single ID-shaped token or a structural word."""
    stripped = value.strip().strip(".").strip()
    if stripped.lower() in STRUCTURAL_TOKENS:
        return True
    tokens = core.words(core.strip_placeholders(value))
    if not tokens:
        return True
    if len(tokens) > 1 and not _ID_TOKEN.fullmatch(stripped):
        return False
    return bool(_ID_TOKEN.fullmatch(stripped)) and any(c.isdigit() for c in stripped)


def source_rules(values):
    """Adaptive copy rule (#8.5): a source value of SOURCE_SHINGLE words or more is matched by its
    6-word shingles; a shorter one by an exact normalised whole-phrase match."""
    shingle_set, phrases = set(), set()
    for value in values:
        if not value or not _live(value) or trivial_source(value):
            continue
        tokens = core.words(core.strip_placeholders(value))
        if len(tokens) >= SOURCE_SHINGLE:
            shingle_set |= shingles(value, SOURCE_SHINGLE)
        else:
            phrases.add(" ".join(tokens))
    return shingle_set, phrases


def _live(value):
    return value != core.WITHHELD


def draft_rules(doc):
    """Everything a slot may not carry, derived from the governed payload."""
    engagement = doc["engagement"]
    rules = {
        "identity": core.identity_terms(engagement["client_name"]),
        "descriptor": engagement["client_descriptor"] if _live(engagement["client_descriptor"]) else "",
        "sector": engagement.get("sector", "") if _live(engagement.get("sector", "")) else "",
        "region": engagement.get("region", "") if _live(engagement.get("region", "")) else "",
        "headcount": engagement.get("client_headcount"),
        "products": [p for p in engagement.get("third_party_products", []) if _live(p)],
        "people": sorted({p for item in doc["retrospective_inputs"] for p in item["named_people"] if _live(p)}),
    }
    released = {a["asset_id"] for a in doc["released_assets"]}
    held_ids = {a["asset_id"] for a in doc["held_assets"] if a["asset_id"] not in released}
    held_ids |= {f["target_id"] for f in doc["sanitisation_report"]["findings"]
                 if f["target_type"] in ("lesson", "screening")}
    rules["held_ids"] = {core.canon_id(i) for i in held_ids}
    rules["held_titles"] = [a["title"] for a in doc["candidate_assets"]
                            if a["asset_id"] in held_ids and _live(a["title"])]
    guidance = [doc["knowledge_record"]["engagement_context_guidance"]]
    guidance += [lesson["drafting_guidance"] for lesson in doc["knowledge_record"]["lessons"]]
    rules["guidance"] = set().union(*(shingles(g, 5) for g in guidance))
    source = [rules["descriptor"]]
    for item in doc["decision_log"]:
        source += [item["summary"], item["impact"]]
    source += [item["text"] for item in doc["retrospective_inputs"]]
    source += [a["description"] for a in doc["candidate_assets"]]
    source += [t["summary"] for t in doc["confidentiality_terms"]]
    rules["source"], rules["source_phrases"] = source_rules(source)
    return rules


def _held_title(filled, title):
    if len(core.words(title)) >= 3:
        return bool(shingles(filled, 3) & shingles(title, 3))
    return phrase_in(title, filled)


def slot_codes(filled, rules):
    if not filled.strip():
        return ["blank_slot"]
    codes = []
    tokens = set(core.words(filled))
    if core.WITHHELD in filled or "<<" in filled or ">>" in filled or core.marker_shaped(filled):
        codes.append("withheld_marker")
    if core.text_hits(filled):
        codes.append("embedded_instruction")
    if rules["identity"] and core.contains_identity(filled, rules["identity"]):
        codes.append("client_identity")
    descriptor = rules["descriptor"]
    if descriptor and (shingles(filled, 4) & shingles(descriptor, 4)
                       or (len(core.words(descriptor)) < 4 and phrase_in(descriptor, filled))):
        codes.append("client_descriptor")
    if rules["sector"] and rules["region"] and phrase_in(rules["sector"], filled) and phrase_in(rules["region"], filled):
        codes.append("sector_region")
    if any(p.search(filled) for p in DATE_PATTERNS):
        codes.append("go_live_date")
    headcount = rules["headcount"]
    if headcount is not None and (str(headcount) in tokens or f"{headcount:,}" in filled):
        codes.append("headcount")
    if any(phrase_in(p, filled) for p in rules["products"]):
        codes.append("third_party_product")
    if any(phrase_in(p, filled) for p in rules["people"]):
        codes.append("named_person")
    ids = {core.canon_id(t) for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]*", filled)}
    if ids & rules["held_ids"] or any(_held_title(filled, t) for t in rules["held_titles"]) or "withheld" in tokens:
        codes.append("held_item")
    if shingles(filled, 5) & rules["guidance"]:
        codes.append("stage_guidance")
    canon_filled = f" {' '.join(core.words(filled))} "
    if (shingles(filled, SOURCE_SHINGLE) & rules["source"]
            or any(f" {phrase} " in canon_filled for phrase in rules["source_phrases"])):
        codes.append("source_text")
    return codes


def check_draft(doc, text):
    """Return [(line number, [codes])] for every refused line; an empty list accepts the draft."""
    expected = core.skeleton(doc)
    lines = core._LINE_SPLIT.split(text)
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) != len(expected):
        return [(min(len(lines), len(expected)) + 1, ["line_count"])]
    rules = draft_rules(doc)
    refused, filled_lines = [], []
    for number, (line, (fixed, slot, _)) in enumerate(zip(lines, expected), start=1):
        if slot is None:
            filled_lines.append(None)
            if line != fixed:
                refused.append((number, ["fixed_line_changed"]))
            continue
        token = core.CONTEXT_SLOT if slot == "CONTEXT" else core.lesson_slot(slot)
        prefix, suffix = fixed.split(token)
        if not (line.startswith(prefix) and line.endswith(suffix) and len(line) >= len(prefix) + len(suffix)):
            filled_lines.append(None)
            refused.append((number, ["fixed_line_changed"]))
            continue
        filled = line[len(prefix):len(line) - len(suffix)]
        filled_lines.append(filled)
        codes = slot_codes(filled, rules)
        if codes:
            refused.append((number, codes))
    flagged = {n for n, _ in refused}
    for index in range(len(lines) - 1):
        if filled_lines[index] is None and filled_lines[index + 1] is None:
            continue
        if index + 1 in flagged or index + 2 in flagged:
            continue
        pair = (lines[index], lines[index + 1])
        if pair[0].strip() and pair[1].strip() and core.fields_hits(pair):
            target = index + 1 if filled_lines[index] is not None else index + 2
            refused.append((target, ["embedded_instruction"]))
            flagged.add(target)
    return sorted(refused)


def _body(argv):
    parser = argparse.ArgumentParser(description="Write or check the governed knowledge-record skeleton.")
    parser.add_argument("--input", required=True, help="sanitize_check output JSON")
    parser.add_argument("--skeleton-out", help="write the knowledge-record skeleton (Markdown) here")
    parser.add_argument("--draft", help="check this filled knowledge-record draft (Markdown)")
    args = parser.parse_args(argv)
    if not args.skeleton_out and not args.draft:
        parser.error("pass --skeleton-out, --draft or both")
    doc = core.load_json(args.input)
    core.verify(doc, 3)
    if args.skeleton_out:
        core.write_text(args.skeleton_out, core.skeleton_text(doc))
        slots = sum(1 for _, slot, _ in core.skeleton(doc) if slot)
        print(f"record_check: skeleton written with {slots} slot(s) to fill")
    if args.draft:
        refused = check_draft(doc, core.read_text(args.draft, "draft"))
        if refused:
            for number, codes in refused:
                print(f"record_check: draft refused: line {number}: {', '.join(codes)}", file=sys.stderr)
            return 1
        print("record_check: draft accepted; fixed lines unchanged and every slot passed the checks")
    return 0


def main(argv=None):
    return core.run("record_check", argv, _body)


if __name__ == "__main__":
    sys.exit(main())
