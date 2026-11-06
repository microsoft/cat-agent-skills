#!/usr/bin/env python3
"""readability_check - deterministic plain-language check for patient_instructions
(hls.discharge-care-transition.v1). Every threshold, term and section comes from
config/readability-rules.json; nothing is hard-coded. Mirrors base/references/discharge-rules.md #3."""
import argparse, json, re, sys
from datetime import datetime, timezone

CONTRACT = "hls.discharge-care-transition.v1"
ENGINE = "engine:readability_check"
RULE = "discharge-rules.md #3"
VOWELS = "aeiouy"
# 1.0.2: the clinician marker patient-instructions writes when a required section has no cited order. A section
# whose only content is this marker has not been written, so it counts as MISSING (discharge-rules.md #3).
MARKER = re.compile(r"\[\s*CLINICIAN TO COMPLETE\b[^\]]*\]", re.I)


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n, prev = 0, False
    for ch in w:
        v = ch in VOWELS
        n += v and not prev
        prev = v
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def jargon_pattern(term):
    """1.0.3: a lower-case word term also matches its inflected forms (-s, -es, -ed, -ing; a final silent e is
    dropped), so 'titrate' catches 'titrated'. Abbreviations (any capital or digit, e.g. NPO, q4h) match exactly."""
    body = re.escape(term)
    if term.isalpha() and term.islower():
        stem = term[:-1] if term.endswith("e") else term
        body = rf"(?:{re.escape(term)}|{re.escape(stem)}(?:s|es|ed|ing))"
    return rf"(?<![A-Za-z]){body}(?![A-Za-z])"


def sentences(text):
    body = "\n".join(l for l in text.splitlines() if not l.strip().endswith(":"))
    return [s.strip() for s in re.split(r"[.!?]+|\n", body) if s.strip()]


def _heading(line, names):
    """Return (section, inline_content) if line is a heading for one of names, else None."""
    for name in names:
        m = re.match(rf"^\s*(?:#+\s*)?(?:\*\*)?{re.escape(name)}(?:\*\*)?\s*:?\s*(?:\*\*)?\s*(.*)$", line, re.I)
        if m:
            return name, m.group(1)
    return None


def section_status(text, required):
    """1.0.2: (missing, marker_only). A required section is MISSING when it is absent, or when it appears as a
    heading and every occurrence holds nothing but the [CLINICIAN TO COMPLETE: ...] marker (or nothing at all).
    A section named only inside a sentence (no heading line) keeps the pre-1.0.2 substring behaviour."""
    lines = text.splitlines()
    content = {}                                        # section -> list of content strings, one per occurrence
    cur = None
    for line in lines:
        h = _heading(line, required)
        if h:
            cur = h[0]
            content.setdefault(cur, []).append(h[1])
            continue
        if line.strip().endswith(":") and not MARKER.search(line):
            cur = None                                  # an unconfigured heading ends the current section
            continue
        if cur:
            content[cur][-1] += "\n" + line
    missing, marker_only = [], []
    for name in required:
        if name in content:
            real = [c for c in content[name] if re.sub(r"[\s\-*\u2022.:]+", "", MARKER.sub("", c))]
            if not real:
                missing.append(name)
                if any(MARKER.search(c) for c in content[name]):
                    marker_only.append(name)
        elif name.lower() not in text.lower():
            missing.append(name)
    return missing, marker_only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8"))
    version = p.get("contract_version") if isinstance(p, dict) else None
    if version != CONTRACT:                           # 1.0.3: readable input error instead of a bare traceback
        found = "is missing" if version is None else f"is {version!r}"
        print(f"readability_check: input error - contract_version {found}; expected {CONTRACT!r}. "
              f"No readability_report was written; correct the payload and re-run.", file=sys.stderr)
        return 2
    cfg = json.load(open(a.config, encoding="utf-8"))
    text = p.get("patient_instructions") or ""
    esc = list(p.get("escalations", []))

    sents = sentences(text)
    words = [w for s in sents for w in s.split()]
    syl = sum(syllables(w) for w in words)
    grade = (round(0.39 * (len(words) / len(sents)) + 11.8 * (syl / len(words)) - 15.59, 2)
             if sents and words else None)
    long_sentences = [{"sentence": s, "words": len(s.split())} for s in sents
                      if len(s.split()) > cfg["max_sentence_words"]]
    jargon = [{"term": t, "plain_language": plain, "citation": RULE}
              for t, plain in sorted(cfg.get("banned_jargon", {}).items())
              if cfg.get("avoid_jargon", True) and re.search(jargon_pattern(t), text, re.I)]
    missing, marker_only = section_status(text, cfg.get("required_sections", []))

    passed = bool(text) and grade is not None and grade <= cfg["max_grade_level"] \
        and not long_sentences and not jargon and not missing
    p["readability_report"] = {
        "metric": cfg["metric"], "grade_level": grade, "max_grade_level": cfg["max_grade_level"],
        "target_reading_level": cfg["target_reading_level"], "max_sentence_words": cfg["max_sentence_words"],
        "long_sentences": long_sentences, "jargon_hits": jargon, "missing_sections": missing,
        "passed": passed, "citation": RULE, "config": "config/readability-rules.json", "source": ENGINE}
    if not passed:
        why = []
        if not text:
            why.append("no patient_instructions draft was supplied")
        if grade is not None and grade > cfg["max_grade_level"]:
            why.append(f"{cfg['metric']}={grade} exceeds max_grade_level {cfg['max_grade_level']}")
        for s in long_sentences:
            why.append(f"sentence of {s['words']} words exceeds max_sentence_words {cfg['max_sentence_words']}")
        for j in jargon:
            why.append(f"jargon '{j['term']}' (say: {j['plain_language']})")
        if missing:
            why.append("missing required sections: " + ", ".join(missing))
        if marker_only:
            why.append("sections holding only the [CLINICIAN TO COMPLETE] marker count as missing: " +
                       ", ".join(marker_only))
        esc.append(f"patient instructions failed the readability check ({RULE}): " + "; ".join(why) +
                   " - revise and re-run before the packet goes to the patient")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("readability_check/1.1")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"readability_check: grade={grade} jargon={len(jargon)} long={len(long_sentences)} "
          f"missing={len(missing)} passed={passed} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
