#!/usr/bin/env python3
"""criteria_engine - deterministic payer-policy criteria checklist + cited evidence match
(hls.prior-auth-assist.v1). Never renders a determination in EITHER direction - prior-auth-rules.md #2.
Constants below mirror base/references/prior-auth-rules.md line for line."""
import argparse, json, re, sys
from datetime import datetime, timezone

ENGINE = "engine:criteria_engine"
ENGINE_VERSION = "criteria_engine/1.3"
RULES = "prior-auth-rules.md"
CONTRACT = "hls.prior-auth-assist.v1"
# #2 - the only three determination states this engine can emit
DET_CLEAN, DET_GAPS, DET_OOS = "packet_assembled_clean", "packet_assembled_gaps", "out_of_scope"
# #2a - phrasing-independent determination-request tokens, symmetric across both directions.
# Matched on word boundaries after hyphens and underscores are read as spaces ("green-light" = "green light").
# Denial phrases that CONTAIN an approval token ("not medically necessary", "disapprove") are matched first and
# removed from the probe so they are never read as an approval request.
APPROVE_TOKENS = ("approve", "approves", "approving", "approval", "approved",
                  "preapprove", "preapproved", "preapproval",
                  "authorise", "authorize", "authorised", "authorized", "authorises", "authorizes",
                  "authorising", "authorizing",
                  "certify", "certifies", "certified", "certifying",
                  "medically necessary", "cleared", "clear for scheduling",
                  "okay to schedule", "ok to schedule", "okayed",
                  "green light", "green lights", "green lighted", "green lighting", "green lit",
                  "greenlight", "greenlights", "greenlighted", "greenlighting", "greenlit",
                  "sign off", "signs off", "signed off", "signing off", "signoff")
DENY_TOKENS = ("not medically necessary", "disapprove", "disapproved", "disapproves", "disapproving", "disapproval",
               "not covered", "deny", "denies", "denying", "denial", "denials", "denied",
               "reject", "rejects", "rejected", "rejecting", "rejection",
               "refuse coverage", "refused coverage", "refusing coverage", "non-covered", "adverse determination",
               "turn it down", "turned it down", "turning it down", "decline", "declines", "declined", "declining")
INTENT_FIELDS = ("request_mode", "request_text", "request_note", "instruction", "asks")
# #3 - why a criterion is a gap
REASON_NO_EVIDENCE, REASON_UNCITED = "no_evidence", "evidence_uncited"
# #4 - a flag counts as met only with all three citation fields present and non-empty
CITATION_FIELDS = ("source_note", "note_date", "quote")
# #5 / #6 - draft-first packet. packet.action_level is the level of the packet ARTEFACT (an L1 draft for
# human review, the plugin ceiling) - not the level of the skill that ran the engine (criteria-extract is L0).
PACKET_STATUS, PACKET_SUBMITTED, PACKET_ACTION_LEVEL = "draft", False, "L1"
# #7 - escalation routing roles (contacts are customer-configured in config/escalation-contacts.json)
ROLE_PAYER_RELATIONS, ROLE_COORDINATOR = "payer-relations contact", "prior-auth coordinator"
CONTACTS_FILE = "config/escalation-contacts.json"
# #1 - request fields required before any lookup, and the request fields whose clause is compared to the library
REQUIRED_REQUEST_FIELDS = ("service", "payer")
CLAUSE_FIELDS = ("clause", "order_clause")


def _norm(text):
    return re.sub(r"[-_]", " ", text.lower())


def _tok(token):
    return r"(?<![a-z])" + re.escape(_norm(token)) + r"(?![a-z])"


def _has(token, text):
    return re.search(_tok(token), text) is not None


def requested_direction(request):
    """#2a: which determination direction was asked for, however phrased. None = no determination asked."""
    probe = _norm(" ".join(str(request.get(k, "")) for k in INTENT_FIELDS))
    deny = False
    for t in DENY_TOKENS:
        if _has(t, probe):
            deny = True
            probe = re.sub(_tok(t), " ", probe)
    approve = any(_has(t, probe) for t in APPROVE_TOKENS)
    return ("approval_and_denial" if approve and deny else
            "approval" if approve else "denial" if deny else None)


def _same_payer(a, b):
    """#1: payer names compared case-insensitively, surrounding whitespace ignored."""
    return isinstance(a, str) and isinstance(b, str) and a.strip().casefold() == b.strip().casefold()


def is_cited(key, citations):
    """#4: source_note, note_date and quote must all be present and non-empty."""
    c = citations.get(key)
    if not isinstance(c, dict):
        return False
    return all(str(c.get(f, "")).strip() for f in CITATION_FIELDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8"))
    lib = json.load(open(a.policy, encoding="utf-8"))
    if p.get("contract_version") != CONTRACT:
        print(f"criteria_engine: contract_version must be {CONTRACT}, got {p.get('contract_version')!r}",
              file=sys.stderr)
        return 2
    req = p.get("request")
    if not isinstance(req, dict):
        print(f"criteria_engine: request must be an object with {', '.join(REQUIRED_REQUEST_FIELDS)} "
              f"({RULES} #1), got {req!r}", file=sys.stderr)
        return 2
    for f in REQUIRED_REQUEST_FIELDS:
        if not isinstance(req.get(f), str) or not req[f].strip():
            print(f"criteria_engine: request.{f} is required and must be a non-empty string ({RULES} #1), "
                  f"got {req.get(f)!r}; no checklist built", file=sys.stderr)
            return 2
    esc = list(p.get("escalations", []))

    service = req["service"]
    payer = req["payer"]
    policy = lib.get(service)
    evidence = p.get("patient_evidence", {})
    citations = p.get("evidence_citations", {})

    direction = requested_direction(req)
    if direction:
        article = "an" if direction[0] in "aeiou" else "a"
        esc.append(f"request asked for {article} {direction} determination - refused; the engine has no approval "
                   f"or denial state in either direction ({RULES} #2); the refusal is logged and the "
                   f"packet returned is whatever the evidence supports, unchanged by the request")

    if policy is not None and not _same_payer(payer, policy.get("payer")):
        esc.append(f"no policy found for service '{service}' and payer '{payer}' - the library entry for "
                   f"'{service}' belongs to payer '{policy.get('payer')}' (clause {policy['clause']}) and is not "
                   f"applied; determination {DET_OOS} ({RULES} #1, #2); escalation drafted, no improvised criteria; "
                   f"route to the {ROLE_PAYER_RELATIONS} ({CONTACTS_FILE}, {RULES} #7)")
        policy = None
    elif policy is None:
        esc.append(f"no policy found for service '{service}' - determination {DET_OOS} ({RULES} #2); "
                   f"escalation drafted, no improvised criteria; route to the {ROLE_PAYER_RELATIONS} "
                   f"({CONTACTS_FILE}, {RULES} #7)")
    if policy is None:
        p["criteria_result"] = {"clause": None, "criteria_checked": 0, "criteria_met": [], "gaps": [],
                                "determination": DET_OOS, "source": ENGINE}
    else:
        reported = set()
        for f in CLAUSE_FIELDS:
            asked = req.get(f)
            if asked and asked != policy["clause"] and asked not in reported:
                reported.add(asked)
                esc.append(f"request.{f} '{asked}' does not match the library clause '{policy['clause']}' for "
                           f"service '{service}' - checklist built on the library clause; confirm with the "
                           f"{ROLE_COORDINATOR} ({RULES} #1)")
        met, gaps = [], []
        for c in policy["criteria"]:
            key = c["evidence_key"]
            flag = evidence.get(key) is True
            if flag and is_cited(key, citations):
                met.append({"id": c["id"], "evidence_key": key, "citation": citations[key]})
            else:
                reason = REASON_UNCITED if flag else REASON_NO_EVIDENCE
                gaps.append({"id": c["id"], "text": c["text"], "evidence_key": key, "reason": reason,
                             "citation": f"policy clause {policy['clause']}"})
        p["criteria_result"] = {"clause": policy["clause"], "criteria_checked": len(policy["criteria"]),
                                "criteria_met": met, "gaps": gaps,
                                "determination": DET_CLEAN if not gaps else DET_GAPS, "source": ENGINE}
        for g in gaps:
            need = ("a cited source note, note date and verbatim quote" if g["reason"] == REASON_UNCITED
                    else f"evidence for '{g['evidence_key']}'")
            esc.append(f"unmet criterion '{g['id']}' ({g['text']}) - policy clause {policy['clause']}, "
                       f"reason {g['reason']}, needs {need} before the packet can be marked clean")

    cr = p["criteria_result"]
    p["packet"] = {"status": PACKET_STATUS, "submitted": PACKET_SUBMITTED, "action_level": PACKET_ACTION_LEVEL,
                   "determination": cr["determination"], "clause": cr["clause"],
                   "criteria_met_count": len(cr["criteria_met"]), "open_gaps": len(cr["gaps"]),
                   "refusal_logged": direction or "none",
                   "contents": ["criteria_checklist", "evidence_citations", "necessity_narrative", "gap_list"]}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"criteria_engine: clause={cr['clause']} det={cr['determination']} gaps={len(cr['gaps'])} "
          f"refusal={direction or 'none'} status={PACKET_STATUS} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
