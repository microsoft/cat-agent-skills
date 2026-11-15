#!/usr/bin/env python3
"""deadline_engine - deterministic appeal deadline, coding-integrity guard and queue ranking
(hls.denials-appeals-response.v1). Constants mirror base/references/denials-rules.md #1-#6."""
import argparse, json, re, sys
from datetime import datetime, timezone, date, timedelta

ENGINE = "engine:deadline_engine"
RULE_DEADLINE = "denials-rules.md #1"  # deadline = denial_date + config.payers[payer].appeal_window_days
RULE_CODING = "denials-rules.md #2"    # cited chart note+date required before a recode is honoured
RULE_QUEUE = "denials-rules.md #3"     # rank by (deadline asc, recoverable_value desc) - never by ease
RULE_NO_DROP = "denials-rules.md #4"   # a refused recode never de-queues the denial
RULE_DRAFT_ONLY = "denials-rules.md #5"  # drafts and calculates only - nothing is submitted
RULE_URGENT = "denials-rules.md #6"    # urgent when days_remaining <= config.urgent_threshold_days
RULE_EXPIRED = "denials-rules.md #7"   # days_remaining < 0 is an expired state, escalated, never dropped
CODE_RE = re.compile(r"\b([0-9]{4}[0-9A-Z]|[A-Z][0-9]{4})\b")  # CPT / HCPCS token


def payer_key(name):
    """Payer names are matched case- and whitespace-insensitively: 'CONTOSO HEALTH PLAN' == 'Contoso Health Plan'."""
    return " ".join(str(name or "").split()).casefold()


def window(payers, payer):
    """RULE_DEADLINE lookup. An exact key wins; otherwise the case-insensitive match. Never a default window."""
    cfg = payers.get(payer) if isinstance(payer, str) else None
    if cfg is None:
        want = payer_key(payer)
        matches = [v for k, v in payers.items() if payer_key(k) == want]
        cfg = matches[0] if len(matches) == 1 else None
    return cfg if isinstance(cfg, dict) else None


# Every escalation the engine itself writes starts with one of these templates. On a re-run they are
# recomputed from scratch (so a stale day count from an earlier run never lingers next to the new one);
# escalations written by other skills or people are carried forward untouched.
ENGINE_ESCALATION_RE = re.compile(
    r"^(contract as_of \S+ differs from today "
    r"|no appeal-window configuration for payer '"
    r"|coding_request to recode to '"
    r"|denial stays in the appeal queue on the original code after the refused recode "
    r"|appeal deadline \S+ (for '.*' passed \d+ day\(s\) ago - expired;|is -?\d+ day\(s\) away - urgent queue priority)"
    r"|queued claim '.*' has no appeal-window configuration for payer ')")


def add_once(esc, msg):
    """Append an escalation only if the identical text is not already on the contract, so re-running the
    engine on its own output never duplicates escalations."""
    if msg not in esc:
        esc.append(msg)


class MissingDenialDate(Exception):
    """RULE_DEADLINE: a configured window still needs a denial_date; the engine stops cleanly, never assumes one."""


def due(denial_date, cfg, claim_id=None):
    if not denial_date:
        raise MissingDenialDate(
            f"denial_date is missing for claim '{claim_id}' - no appeal deadline can be computed and none is assumed "
            f"({RULE_DEADLINE}); set it from the denial document (835 DTM*405) or, if the candidate dates conflict, "
            f"escalate for human decision")
    return (date.fromisoformat(denial_date) + timedelta(days=cfg["appeal_window_days"])).isoformat()


def norm_code(code):
    """Reduce '99215 (higher E/M level)' to '99215' so a descriptive label never defeats an exact-code match."""
    m = CODE_RE.search(str(code or "").upper())
    return m.group(1) if m else str(code or "").strip().upper()


def cited(evidence, code):
    """RULE_CODING: a specific note + date citing the requested code, not a bare boolean."""
    want = norm_code(code)
    for c in evidence.get("citations", []):
        if norm_code(c.get("supports_code")) == want and c.get("note") and c.get("date"):
            return c
    return None


def status(days_remaining, urgent_threshold):
    """RULE_URGENT / RULE_EXPIRED: open, urgent, expired - or unconfigured when no window exists."""
    if days_remaining is None:
        return "unconfigured"
    if days_remaining < 0:
        return "expired"
    return "urgent" if days_remaining <= urgent_threshold else "open"


def clock_escalation(claim_id, deadline, days_remaining, urgent_threshold):
    st = status(days_remaining, urgent_threshold)
    if st == "expired":
        return (f"appeal deadline {deadline} for '{claim_id}' passed {-days_remaining} day(s) ago - expired; "
                f"escalate for human decision, claim stays queued ({RULE_EXPIRED}, {RULE_NO_DROP})")
    if st == "urgent":
        return f"appeal deadline {deadline} is {days_remaining} day(s) away - urgent queue priority"
    return None


def rank_queue(queue, payers, today, urgent_threshold, unconfigured_claim=None):
    """RULE_QUEUE: deadline ascending, then recoverable_value descending. Ease is never an input.
    unconfigured_claim is the primary denial's claim_id when the denial's payer has no window (RULE_DEADLINE): its own
    queue row is unconfigured too, even if the queue spells the payer differently, so one claim never gets a deadline
    the denial itself does not have."""
    rows = []
    for item in queue:
        own = unconfigured_claim is not None and item.get("claim_id") == unconfigured_claim
        cfg = None if own else window(payers, item.get("payer"))
        dl = due(item.get("denial_date"), cfg, item.get("claim_id")) if cfg else None
        rows.append({"claim_id": item.get("claim_id"), "payer": item.get("payer"), "deadline": dl,
                     "days_remaining": (date.fromisoformat(dl) - today).days if dl else None,
                     "recoverable_value": float(item.get("recoverable_value", 0.0)),
                     "rank_basis": RULE_QUEUE})
        rows[-1]["deadline_status"] = status(rows[-1]["days_remaining"], urgent_threshold)
    rows.sort(key=lambda r: (r["deadline"] is None, r["deadline"] or "", -r["recoverable_value"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def main():
    try:
        return run()
    except MissingDenialDate as e:
        print(f"deadline_engine: error: {e}", file=sys.stderr)
        return 1


def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--payers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--today", help="ISO date to count from (reproduces a demo scenario snapshot only); default is the real current date")
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8"))
    cfg_file = json.load(open(a.payers, encoding="utf-8"))
    payers = cfg_file["payers"]
    urgent_threshold = cfg_file["urgent_threshold_days"]
    assert p["contract_version"] == "hls.denials-appeals-response.v1"
    esc = []
    for prior in p.get("escalations", []) or []:
        # Re-running on a contract that already carries this engine's escalations must not duplicate them:
        # engine-written lines are dropped and recomputed below; everything else is kept once, in order.
        if isinstance(prior, str) and ENGINE_ESCALATION_RE.match(prior):
            continue
        add_once(esc, prior)

    denial = p["denial"]
    payer_cfg = window(payers, denial["payer"])
    # RULE_DEADLINE: days_remaining is relative to TODAY - the real current date unless --today pins it to
    # reproduce a demo snapshot. denial.as_of is the contract snapshot date and never stands in for today.
    today = date.fromisoformat(a.today) if a.today else datetime.now(timezone.utc).date()
    as_of = denial.get("as_of")
    if as_of and date.fromisoformat(as_of) != today:
        add_once(esc, f"contract as_of {as_of} differs from today {today.isoformat()} - every day count is "
                   f"computed as of {today.isoformat()} ({RULE_DEADLINE})")
    policy_basis = [c.get("clause_id") for c in p.get("policy_citations", []) if c.get("clause_id")]

    if payer_cfg is None:
        deadline_result = {"deadline": None, "days_remaining": None, "deadline_status": "unconfigured",
                           "coding_decision": "n/a",
                           "coding_evidence_basis": None, "policy_basis": policy_basis,
                           "action_level": "L0", "source": ENGINE}
        add_once(esc, f"no appeal-window configuration for payer '{denial['payer']}' - escalate to payer-relations")
    else:
        deadline = due(denial.get("denial_date"), payer_cfg, denial.get("claim_id"))
        days_remaining = (date.fromisoformat(deadline) - today).days
        coding_decision, basis = "not_requested", None
        cr = p.get("coding_request")
        chart_evidence = p.get("chart_evidence", {}) or {}
        if cr:
            code = cr.get("requested_code")
            citation = cited(chart_evidence, code)
            flagged = chart_evidence.get("supports_requested_code", False) is True
            if citation and flagged:
                coding_decision = "supported_by_chart"
                basis = f"{citation['note']} ({citation['date']})"
            else:
                coding_decision = "refused_evidence_gap"
                why = ("chart does not support it" if not flagged else
                       "no cited chart note and date supports it - a supports_requested_code flag is not evidence")
                add_once(esc,
                    f"coding_request to recode to '{code}' refused - {why} "
                    f"({RULE_CODING}); reported as an evidence gap for human decision, never auto-applied")
                add_once(esc, f"denial stays in the appeal queue on the original code after the refused recode ({RULE_NO_DROP})")
        deadline_result = {"deadline": deadline, "days_remaining": days_remaining,
                           "deadline_status": status(days_remaining, urgent_threshold),
                           "coding_decision": coding_decision, "coding_evidence_basis": basis,
                           "policy_basis": policy_basis, "action_level": "L0", "source": ENGINE}
        msg = clock_escalation(denial.get("claim_id"), deadline, days_remaining, urgent_threshold)
        if msg:
            add_once(esc, msg)

    queue = p.get("queue")
    if queue:
        p["queue_ranked"] = rank_queue(queue, payers, today, urgent_threshold,
                                       unconfigured_claim=denial.get("claim_id") if payer_cfg is None else None)
        for r in p["queue_ranked"]:
            if r["deadline"] is not None and r["claim_id"] != denial.get("claim_id"):
                # RULE_URGENT / RULE_EXPIRED apply to EVERY queued claim, not only the primary denial.
                msg = clock_escalation(r["claim_id"], r["deadline"], r["days_remaining"], urgent_threshold)
                if msg:
                    add_once(esc, msg.replace("urgent queue priority", f"urgent queue priority for '{r['claim_id']}'"))
            if r["deadline"] is None:
                named = denial.get("payer") if payer_cfg is None and r["claim_id"] == denial.get("claim_id") else r["payer"]
                add_once(esc, f"queued claim '{r['claim_id']}' has no appeal-window configuration for payer "
                           f"'{named}' - ranked last and escalated to payer-relations, never dropped ({RULE_QUEUE})")

    p["deadline_result"] = deadline_result
    p["escalations"] = esc
    prov = p.setdefault("provenance", {})
    engines = list(dict.fromkeys(prov.get("engines", [])))  # a re-run never stacks duplicate engine entries
    if "deadline_engine/1.0.3" not in engines:
        engines.append("deadline_engine/1.0.3")
    prov["engines"] = engines
    prov["rules"] = [RULE_DEADLINE, RULE_CODING, RULE_QUEUE, RULE_NO_DROP, RULE_DRAFT_ONLY, RULE_URGENT, RULE_EXPIRED]
    prov["computed_as_of"] = today.isoformat()
    prov["citations"] = policy_basis + [f"{c.get('note')} ({c.get('date')})"
                                        for c in p.get("chart_evidence", {}).get("citations", [])]
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    dr = p["deadline_result"]
    print(f"deadline_engine: deadline={dr['deadline']} days_remaining={dr['days_remaining']} "
          f"status={dr['deadline_status']} as_of={today.isoformat()} "
          f"coding={dr['coding_decision']} queued={len(p.get('queue_ranked', []))} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
