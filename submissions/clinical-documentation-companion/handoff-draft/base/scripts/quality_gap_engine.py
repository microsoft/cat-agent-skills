#!/usr/bin/env python3
"""quality_gap_engine - deterministic quality-measure gap check, override refusal and claim-evidence check
(hls.clinical-documentation-companion.v1, plugin 1.0.3). Constants mirror base/references/clinical-doc-rules.md #1-#7.

1.0.3 changes: an override term that is negated in its own clause ("don't mark anything as met") or that names a
non-status object ("mark it final") is not override wording (#2; cue words and window in config); override terms may
carry a {measure} placeholder that matches the measure's name or aliases ("count {measure}", "treat {measure} as");
a refused request to move a documented (met) measure no longer says the fact "is not documented".

1.0.2 changes: an override detected in the live chat wording (`messages`) is logged with detected_via "messages"
(was "request_text"), one refusal per wording source; an unsigned-note halt also writes the contract `halt` record,
and needs no `encounter` block (the contract makes `encounter` optional for an unsigned-note halt).

1.0.1 changes: whole-word/phrase matching of requester wording (no 'mark' inside 'benchmark'); requester words
logged in full (no 160-char cut); a gap/unsupported flag also carries the note's own citation (note_citation);
code-change and handoff-omission requests are detected, refused and escalated (#7); the live chat message can be
passed in `messages`; bad input exits 2 with a readable error instead of a traceback; note age is recorded in
provenance so a stale note can be flagged."""
import argparse, json, re, sys
from datetime import date, datetime, timezone

ENGINE = "engine:quality_gap_engine"
R1 = "clinical-doc-rules.md #1"   # met only from a documented, cited fact
R2 = "clinical-doc-rules.md #2"   # override requests refused, whatever form they arrive in
R3 = "clinical-doc-rules.md #3"   # downstream artefacts are drafts
R4 = "clinical-doc-rules.md #4"   # claim elements supported only by a cited note fact
R5 = "clinical-doc-rules.md #5"   # the run only proceeds against a signed note
R6 = "clinical-doc-rules.md #6"   # refusals escalate by name to the configured routee
R7 = "clinical-doc-rules.md #7"   # code-change and open-item omission requests are refused and escalated
CONTRACT = "hls.clinical-documentation-companion.v1"


class InputError(Exception):
    pass


def cited(note_facts, key):
    """(documented, citation, asserted, raw_citation) - an uncited assertion is never documented (#1)."""
    v = note_facts.get(key)
    if isinstance(v, dict):
        c = v.get("citation") or {}
        ok = bool(isinstance(c, dict) and c.get("source") and c.get("locator"))
        return bool(v.get("value")) and ok, (c if ok else None), bool(v.get("value")), (c if ok else None)
    return False, None, bool(v), None


def routee(policy, kind):
    r = policy.get("routees", {}).get(kind) or {}
    vals = [str(r.get(k, "")) for k in ("name", "role", "contact")]
    if not r or any(not v or v.startswith("[TO CONFIGURE") for v in vals):
        # never pretend an escalation reached someone: an unconfigured routee is reported as NOT ROUTED
        return (f"NOT ROUTED - routees.{kind} is not configured in config/escalation-policy.json; "
                f"the plugin owner must configure it (refusal still logged)")
    return f"{vals[0]} ({vals[1]}, {vals[2]})"


def names_of(m):
    return [m["name"].lower()] + [a.lower() for a in m.get("aliases", [])]


def has_phrase(text, phrase):
    """Whole-word / whole-phrase match, case-insensitive (fixes substring false positives)."""
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])", text) is not None


CLAUSE_BREAK = re.compile(r"[.;:!?,()\"]|\s[-\u2013\u2014]\s|\bbut\b")
WORDS = re.compile(r"[a-z0-9']+")


def term_regex(term, mine):
    """Whole-word / whole-phrase regex for one config term. '{measure}' stands for one of this measure's names or
    aliases, optionally preceded by up to two words ("the diabetic") and followed by one ("measure")."""
    parts = [re.escape(x) for x in term.lower().split("{measure}")]
    alt = "|".join(re.escape(n) for n in sorted(mine, key=len, reverse=True))
    body = (r"(?:[a-z0-9'-]+\s+){0,2}(?:" + alt + r")(?:\s+[a-z0-9'-]+)?").join(parts)
    return re.compile(r"(?<![a-z0-9])" + body + r"(?![a-z0-9])")


def live_term(policy, t, m):
    """False when the matched override term is negated, or names a non-status object, within its own clause (#2):
    "don't mark anything as met" and "mark it final" are not requests to change a measure status."""
    window = int(policy.get("override_context_window_words", 3))
    start = max([b.end() for b in CLAUSE_BREAK.finditer(t, 0, m.start())] or [0])
    nxt = CLAUSE_BREAK.search(t, m.end())
    before = WORDS.findall(t[start:m.start()])
    after = WORDS.findall(t[m.end():nxt.start() if nxt else len(t)])[:window]
    for cue in policy.get("override_negation_terms", []):
        cw = WORDS.findall(cue.lower())
        for i in range(len(before) - len(cw) + 1):
            if cw and before[i:i + len(cw)] == cw and len(before) - i - len(cw) <= window:
                return False
    non_status = {w.lower() for w in policy.get("override_non_status_terms", [])}
    return not any(w in non_status for w in after)


def request_texts(policy, payload, with_source=False):
    """Requester wording from every configured field. with_source=True yields (detected_via, text) pairs:
    words from the live chat `messages` field are labelled "messages", every other field "request_text"."""
    out = []
    for field in policy.get("request_text_fields", []):
        val = payload.get(field)
        via = "messages" if field == "messages" else "request_text"
        for s in (val if isinstance(val, list) else [val]):
            if s:
                t = re.sub(r"\s+", " ", str(s)).strip()
                out.append((via, t) if with_source else t)
    return out


def text_override(policy, payload, mid, measures):
    """Deterministic scan of requester wording for override intent (#2). Vague wording is not a loophole: an
    intent term that names no measure at all counts against every measure that is currently a gap.
    A negated term or one naming a non-status object does not count (live_term).
    Returns [(detected_via, words)] - at most one hit per source ("request_text", "messages"), first match wins."""
    mine = names_of(measures[mid])
    terms = [term_regex(x, mine) for x in policy.get("override_intent_terms", [])]
    others = [n for k, v in measures.items() if k != mid for n in names_of(v)]
    hits = {}
    for via, s in request_texts(policy, payload, with_source=True):
        if via in hits:
            continue
        t = s.lower().replace("\u2019", "'")
        if not any(live_term(policy, t, m) for rx in terms for m in rx.finditer(t)):
            continue
        if any(n in t for n in mine) or not any(n in t for n in others):
            hits[via] = s
    return list(hits.items())


def text_hits(policy, payload, key):
    terms = policy.get(key, [])
    return [s for s in request_texts(policy, payload) if any(has_phrase(s.lower(), x) for x in terms)]


def finish(p, esc, out, note_age):
    p["escalations"] = list(dict.fromkeys(esc))   # 1.0.3: re-running on an updated contract never duplicates entries
    prov = p.setdefault("provenance", {})
    engines = prov.setdefault("engines", [])
    if "quality_gap_engine/1.3" not in engines:
        engines.append("quality_gap_engine/1.3")
    prov["rules"] = "base/references/clinical-doc-rules.md #1-#7"
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prov["note_age_days"] = note_age
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=2)
    q = p["quality_gap_result"]
    print(f"quality_gap_engine: met={len(q['met'])} gaps={len(q['gaps'])} "
          f"refused={len(q['override_attempts_refused'])} omissions_refused={len(q['omission_requests_refused'])} "
          f"halted={q.get('halted')} note_age_days={note_age} -> {out}")
    return 0


def load(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise InputError(f"{what} file not found: {path}")
    except json.JSONDecodeError as e:
        raise InputError(f"{what} file is not valid JSON ({path}): {e}")


def note_age_days(p):
    try:
        return (date.today() - date.fromisoformat(str((p.get("encounter") or {}).get("date", ""))[:10])).days
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--measures", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = load(a.question, "question")
    measures = load(a.measures, "measures")
    policy = load(a.policy, "policy")
    if p.get("contract_version") != CONTRACT:
        raise InputError(f"contract_version must be '{CONTRACT}', got {p.get('contract_version')!r}")
    esc = list(p.get("escalations", []))
    p["action_level"] = p.get("action_level") or policy.get("action_levels", {}).get("default", "L0")
    note_facts = p.get("note_facts", {}) or {}
    age = note_age_days(p)

    if not (p.get("note_signature") or {}).get("signed"):     # #5
        to = routee(policy, 'unsigned_note')
        esc.append(f"note is not signed - run halted before any computation ({R5}); escalated to {to} ({R6})")
        halt = p.get("halt") if isinstance(p.get("halt"), dict) else {}
        p["halt"] = {"halted": "unsigned_note",
                     "reason": halt.get("reason") or f"note is not signed - nothing computed or drafted ({R5})",
                     "skill": halt.get("skill") or ENGINE, "routee": to}
        p["quality_gap_result"] = {"measures_checked": 0, "met": [], "met_citations": {}, "gaps": [],
                                   "override_attempts_refused": [], "omission_requests_refused": [],
                                   "halted": "unsigned_note", "source": ENGINE}
        p["coding_rationale"] = None
        return finish(p, esc, a.out, age)

    requested = p.get("requested_measure_status") or {}
    met, met_cits, gaps, refused = [], {}, [], []
    for mid, m in measures.items():
        documented, cit, asserted, raw = cited(note_facts, m["required_fact_key"])
        status = "met" if documented else "gap"
        attempts = []
        if mid in requested and requested[mid] != status:
            attempts.append(("requested_measure_status", requested[mid], f"requested_measure_status.{mid}='{requested[mid]}'"))
        if asserted and not documented:
            attempts.append(("uncited_note_fact", "met", f"note_facts.{m['required_fact_key']} asserted true with no citation"))
        if status != "met":
            for via, words in text_override(policy, p, mid, measures):
                attempts.append((via, "met", words))
        if documented:   # reverse request on a met measure: the fact IS documented
            why = (f"'{m['required_fact_key']}' is documented with a citation in the signed note and a measure status "
                   f"is never set by request")
        else:
            why = f"'{m['required_fact_key']}' is not documented with a citation in the signed note"
        for via, req, ev in attempts:
            refused.append({"measure": mid, "requested": req, "actual": status, "detected_via": via,
                            "evidence": ev, "citation": R2})
            esc.append(f"override attempt on measure '{mid}' (requested '{req}', detected via {via}: {ev}) refused - "
                       f"{why} ({R2}); measure remains '{status}'; escalated to {routee(policy, 'override_refusal')} ({R6})")
        if status == "met":
            met.append(mid)
            met_cits[mid] = cit
        else:
            gaps.append({"measure": mid, "name": m["name"], "missing_fact": m["required_fact_key"], "citation": R1,
                         "note_citation": raw})

    omissions = []
    if gaps:                                                   # #7 - only meaningful when something is open
        for s in text_hits(policy, p, "omission_intent_terms"):
            omissions.append({"requested": "omit open item", "evidence": s, "citation": R7})
            esc.append(f"request to omit an open item from the handoff ({s}) refused - every gap stays an open item "
                       f"({R7}); escalated to {routee(policy, 'omission_refusal')} ({R6})")

    p["quality_gap_result"] = {"measures_checked": len(measures), "met": met, "met_citations": met_cits,
                               "gaps": gaps, "override_attempts_refused": refused,
                               "omission_requests_refused": omissions, "halted": None, "source": ENGINE}

    claim = p.get("claim") or None
    if claim:                                                  # #4
        supported, unsupported = [], []
        for e in claim.get("elements", []):
            documented, cit, _, raw = cited(note_facts, e.get("supported_by", ""))
            if documented:
                supported.append({"element": e["element"], "type": e["type"],
                                  "supported_by": e["supported_by"], "citation": cit})
            else:
                unsupported.append({"element": e["element"], "type": e["type"],
                                    "missing_fact": e.get("supported_by", ""), "citation": R4, "note_citation": raw})
                esc.append(f"claim element '{e['element']}' has no documented, cited support in the signed note "
                           f"({R4}); escalated to {routee(policy, 'unsupported_claim_element')} for documentation "
                           f"completion before submission ({R6})")
        changes = []
        for s in text_hits(policy, p, "code_change_intent_terms"):   # #7
            changes.append({"requested": "change/select/upgrade a code", "evidence": s, "citation": R7})
            esc.append(f"request to change, select or upgrade a claim code ({s}) refused - coding-rationale only "
                       f"rationalises codes already on the claim ({R7}); escalated to "
                       f"{routee(policy, 'code_change_refusal')} ({R6})")
        p["coding_rationale"] = {"status": "draft", "action_level": p["action_level"], "visit_level":
                                 claim.get("visit_level"), "supported": supported,
                                 "unsupported_flags": unsupported, "change_requests_refused": changes,
                                 "draft_citation": R3, "source": ENGINE}
    else:
        p["coding_rationale"] = {"status": "not_applicable", "reason": "no claim on the contract",
                                 "supported": [], "unsupported_flags": [], "change_requests_refused": [],
                                 "source": ENGINE}
    return finish(p, esc, a.out, age)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InputError as e:
        print(f"quality_gap_engine: input error - {e}", file=sys.stderr)
        sys.exit(2)
