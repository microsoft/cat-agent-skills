#!/usr/bin/env python3
"""consistency_check - deterministic cross-section consistency engine (hls.reg-submission-authoring.v1).
Constants mirror base/references/submission-rules.md #1-#6 line for line. Data lives in config/; the model
never calculates. Action level L0: reads the contract, reports findings, files nothing."""
import argparse, json, os, sys
from datetime import datetime, timezone

ENGINE = "engine:consistency_check"
CONTRACT = "hls.reg-submission-authoring.v1"
RULES = "submission-rules.md"
RULE_1 = "#1 cross-section numeric consistency"
RULE_2 = "#2 population definition discipline"
RULE_3 = "#3 draft-first, never filed"
RULE_4 = "#4 no unsourced assertion"
RULE_5 = "#5 every fact cites its grounding"
RULE_6 = "#6 required-section coverage gates assembly"
STATUS_CLEAN, STATUS_OPEN = "draft_clean", "draft_open_items"  # RULE_3: the only permitted states
ACTION_LEVEL = "L0"
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.normpath(os.path.join(HERE, "..", "..", "config"))


def finding(rule, kind, detail, section=None, field=None, **kw):
    f = {"rule": f"{RULES} {rule}", "type": kind, "section": section, "field": field, "detail": detail}
    f.update(kw)
    return f


def rounds_to(asserted, source):  # RULE_2 numeric_format: a rounded form of the source is not equal
    return (isinstance(asserted, (int, float)) and isinstance(source, (int, float))
            and not isinstance(asserted, bool) and not isinstance(source, bool)
            and asserted != source and any(round(source, d) == asserted for d in range(0, 4)))


def check_field(sec, field, cell, facts, style):
    """Findings for one asserted field. An unsourced or uncited assertion never passes silently."""
    if not isinstance(cell, dict) or "value" not in cell:
        return [finding(RULE_5, "uncited_assertion", f"'{field}' is asserted without a {{value, citation}} pair, "
                        "so its grounding cannot be verified", sec, field)]
    out, asserted, cite = [], cell["value"], cell.get("citation")
    fact = facts.get(field)
    if fact is None:  # RULE_4
        return [finding(RULE_4, "unsourced_assertion", f"'{field}' is asserted as {asserted!r} but has no entry in "
                        "source_facts - source it from the protocol/SAP/TLF set or drop it", sec, field,
                        asserted=asserted)]
    source = fact.get("value")
    if not cite:
        out.append(finding(RULE_5, "missing_citation", f"'{field}' is asserted without a citation; the source fact "
                           f"cites {fact.get('citation')!r}", sec, field))
    elif cite != fact.get("citation"):
        out.append(finding(RULE_5, "citation_mismatch", f"'{field}' cites {cite!r} but the source fact cites "
                           f"{fact.get('citation')!r}", sec, field))
    if asserted == source and type(asserted) is type(source):
        return out
    same_number = (asserted == source and not isinstance(asserted, bool) and not isinstance(source, bool)
                   and isinstance(asserted, (int, float)) and isinstance(source, (int, float)))
    if type(asserted) is not type(source) and (str(asserted) == str(source) or same_number):  # RULE_1 type message
        same = "same text, different JSON type" if str(asserted) == str(source) else "same number, different type"
        out.append(finding(RULE_1, "type_mismatch",
                           f"{field} asserted={asserted!r} ({type(asserted).__name__}) source={source!r} "
                           f"({type(source).__name__}) - {same}; re-carry the source value "
                           "verbatim", sec, field, asserted=asserted, source=source,
                           asserted_type=type(asserted).__name__, source_type=type(source).__name__))
        return out
    if style.get("population_terms_must_match_sap"):  # RULE_2
        for other in sorted(facts):
            if other != field and other.endswith("_n") and facts[other].get("value") == asserted:
                out.append(finding(RULE_2, "population_substitution", f"{field} asserted={asserted!r} is the value "
                                   f"of '{other}', not of '{field}' (source={source!r}) - these are distinct "
                                   "populations", sec, field, asserted=asserted, source=source, matched_field=other))
                return out
    if rounds_to(asserted, source):  # RULE_2 numeric_format
        out.append(finding(RULE_2, "rounding_violation", f"{field} asserted={asserted!r} is a rounded form of "
                           f"source={source!r}; style-guide numeric_format = {style.get('numeric_format')!r}",
                           sec, field, asserted=asserted, source=source))
        return out
    out.append(finding(RULE_1, "value_mismatch", f"{field} asserted={asserted!r} source={source!r}",
                       sec, field, asserted=asserted, source=source))
    return out


def reject(why):  # explicit check (not assert): survives python -O; exit 2 = escalate, no report written
    print(f"consistency_check: ERROR {why} - payload rejected; escalate, do not report clean", file=sys.stderr)
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--templates", default=os.path.join(CFG, "submission-templates.json"))
    ap.add_argument("--style", default=os.path.join(CFG, "style-guide.json"))
    a = ap.parse_args()
    try:  # a payload that is unreadable or off-contract is rejected loudly, never reported as clean
        p = json.load(open(a.question, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return reject(f"payload unreadable: {e}")
    if not isinstance(p, dict) or p.get("contract_version") != CONTRACT:
        got = p.get("contract_version") if isinstance(p, dict) else type(p).__name__
        return reject(f"contract_version {got!r} != {CONTRACT!r}")
    sub = p.get("submission")  # RULE_6: coverage cannot be gated without the contract's required submission_type
    if not isinstance(sub, dict) or not isinstance(sub.get("submission_type"), str):
        what = "has no submission block" if not isinstance(sub, dict) else "has no submission.submission_type"
        return reject(f"payload {what} (required by {CONTRACT})")
    templates = json.load(open(a.templates, encoding="utf-8"))
    style = json.load(open(a.style, encoding="utf-8"))
    facts = p.get("source_facts", {})
    sections = p.get("draft_sections", [])

    findings, checked = [], 0
    for field in sorted(facts):  # RULE_5: grounding is checked at the source too
        if not isinstance(facts[field], dict) or not facts[field].get("citation"):
            findings.append(finding(RULE_5, "uncited_source_fact", f"source_facts['{field}'] carries no citation "
                                    "naming its TLF table / SAP or protocol section", None, field))
    for sec in sections:
        for field, cell in sec.get("asserted", {}).items():
            checked += 1
            findings.extend(check_field(sec["section"], field, cell, facts, style))

    stype = sub["submission_type"]  # RULE_6: coverage comes from config
    template = templates.get(stype, {})
    required = template.get("required_sections", [])
    drafted = [s.get("section") for s in sections]
    missing = [s for s in required if s not in drafted]
    for s in missing:
        target = template.get("target", stype)
        target = target if target.endswith("structure") else f"{target} structure"
        findings.append(finding(RULE_6, "section_not_drafted", f"required section '{s}' of the "
                                f"{target} has not been drafted", s))
    if not required:
        findings.append(finding(RULE_6, "unknown_submission_type", f"submission_type {stype!r} has no template in "
                                "config/submission-templates.json - coverage cannot be gated"))

    clean = not findings
    prior_status = p.get("assembly_status")  # RULE_3: a filed/submitted input state is replaced, never silently
    p["consistency_report"] = {
        "checked": checked, "mismatches": findings, "clean": clean,
        "coverage": {"required": required, "drafted": drafted, "missing": missing},
        "rules": f"{RULES} #1-#6", "action_level": ACTION_LEVEL, "source": ENGINE,
    }
    p["assembly_status"] = STATUS_CLEAN if clean else STATUS_OPEN  # RULE_3
    p["action_level"] = ACTION_LEVEL
    esc = list(p.get("escalations", []))
    for f in findings:
        where = f" in '{f['section']}'" if f.get("section") else ""
        esc.append(f"{f['type']}{where}: {f['detail']} ({f['rule']}) - resolve before assembly")
    if prior_status is not None and prior_status not in (STATUS_CLEAN, STATUS_OPEN):
        esc.append(f"assembly_status_replaced: input assembly_status {prior_status!r} is not a draft state and was "
                   f"replaced by {p['assembly_status']!r}; nothing is filed or submitted ({RULES} {RULE_3}) - "
                   "confirm with the submission lead")
        print(f"consistency_check: WARNING input assembly_status {prior_status!r} replaced by "
              f"{p['assembly_status']!r} ({RULES} {RULE_3})", file=sys.stderr)
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("consistency_check/1.1")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"consistency_check: checked={checked} open_items={len(findings)} missing_sections={len(missing)} "
          f"status={p['assembly_status']} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
