#!/usr/bin/env python3
"""policy_resolve - deterministic policy + promotion resolution (rtl.store-associate-assist.v1).
Rules mirror references/assist-rules.md. Promo eligibility = window AND cluster AND SKU (#2.1).

v1.0.2 changes
- Clause ranking (#1): an exclusion clause (determination_hint == "excluded") outranks the general
  clause ONLY when one of its own distinguishing topics matched the question - a topic that no
  non-exclusion clause hit also lists. A generic hit never promotes an exclusion.
- Confidence floor (#4.1) is live: 0.9 single clause / exclusion won on a distinguishing topic,
  0.8 general clause chosen while an exclusion clause was hit only on shared wording,
  0.7 (< floor) when hits span more than one policy family - shift-lead escalation.
- No `assert`: contract checks fail with an explicit message (exit 2) so `python -O` cannot skip them.
- Missing / invalid question.asked_on or store_context.cluster: promo check is marked unchecked with
  the reason and an escalation; clause resolution still runs.
- Promo citation lists every promo the SKU appears on, not just the last one.

v1.0.5 changes (authorised logic fixes)
- Raincheck gate (#2.3): a clause with "requires_out_of_stock" / "requires_promo_active" (PRC-3.3) resolves only
  when the question states the item is out of stock AND promo_check shows the promo live for the asked date and
  the store's cluster. Promo not live -> "no_alternative_promo_not_eligible" (no clause, no alternative; an
  escalation is added when the store's cluster is not on the promo). Item in stock -> "no_alternative_in_stock".
  Stock or promo status unknown -> "escalate_stock_unknown" / "escalate_promo_unknown", confidence 0.6 (< floor).
- Return gate (#1.4): a clause with "requires_receipt" / "categories" (RET-2.1) resolves only when the question
  states a receipt AND names an item from one of the clause's categories. Otherwise the engine routes to a library
  clause marked "applies_when": "no_receipt" / "category_not_covered" if one exists, else escalates to the shift
  lead at confidence 0.6 ("escalate_receipt_missing", "escalate_receipt_unknown", "escalate_category_not_covered").
  "eligible" is never output without a receipt.
- Signal phrases (receipt yes/no, in/out of stock) are configuration: policy library key "_signals". Library keys
  starting with "_" are not clauses. Built-in defaults apply when "_signals" is absent.
- Missing-cluster message now asks for the store master export from the user's files.

v1.0.6 changes - superseded by 1.0.7 (phrase lists for receipt / stock / purchase date removed).

v1.0.7 changes (design change: structured facts from question-intake)
- Receipt, stock and purchase date are read ONLY from question.facts, written by question-intake:
  receipt in_hand | not_in_hand | unclear, stock_at_this_store in_stock | out_of_stock | unclear,
  purchase_date YYYY-MM-DD | null, evidence {receipt, stock, purchase_date} verbatim words. No text parsing.
- Missing or invalid facts -> contract error (exit 2), never a default.
- RET-2.1 eligible needs receipt in_hand AND a covered category (item terms, unchanged) AND purchase_date inside
  windows_days. purchase_date null -> confirm_purchase_date (0.6); outside -> not_eligible_outside_window (0.9);
  not_in_hand -> receiptless clause if configured, else escalate_receipt_missing (0.6); unclear ->
  escalate_receipt_unknown (0.6).
- PRC-3.3 needs stock out_of_stock AND the promo live (unchanged gate order); in_stock -> no_alternative_in_stock;
  unclear -> escalate_stock_unknown (0.6).
- Clause ranking, promo test and the missing-cluster message are unchanged.
"""
import argparse, json, re, sys
from datetime import datetime, timezone, date

ENGINE = "engine:policy_resolve"
ENGINE_VERSION = "policy_resolve/1.0.7"
CONTRACT = "rtl.store-associate-assist.v1"
CONFIDENCE_FLOOR = 0.75  # assist-rules.md #4.1
GATED_CONFIDENCE = 0.6  # below the floor: a clause requirement could not be confirmed (#1.4, #2.3, #4.1)
RECEIPT = ("in_hand", "not_in_hand", "unclear")          # question.facts.receipt (#1.4)
STOCK = ("in_stock", "out_of_stock", "unclear")           # question.facts.stock_at_this_store (#2.3)
APOSTROPHES = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201b": "'", "\u02bc": "'", "\u00b4": "'", "`": "'",
                             "\u201c": '"', "\u201d": '"', "\u201e": '"'})


def normalise(text):
    """#1.4 / #2.3 matching runs on: straight apostrophes and quotes, lower case, single spaces."""
    return re.sub(r"\s+", " ", text.translate(APOSTROPHES).lower()).strip()


def fail(msg):
    print(f"policy_resolve: {msg}", file=sys.stderr)
    sys.exit(2)


def check_contract(p):
    """Light structural check mirroring contracts/rtl.store-associate-assist.v1.json (no jsonschema dep)."""
    if p.get("contract_version") != CONTRACT:
        fail(f"contract_version must be '{CONTRACT}' (got {p.get('contract_version')!r})")
    q = p.get("question")
    if not isinstance(q, dict) or not isinstance(q.get("text"), str) or not q["text"].strip():
        fail("question.text (non-empty string) is required")
    if q.get("compare_skus") is not None and not isinstance(q["compare_skus"], list):
        fail("question.compare_skus must be an array")
    sc = p.get("store_context")
    if sc is not None and not isinstance(sc, dict):
        fail("store_context must be an object")
    check_facts(q)


def check_facts(q):
    """question.facts is written by question-intake; the engine never defaults it (#1.4, #2.3)."""
    f = q.get("facts")
    if not isinstance(f, dict):
        fail("question.facts (object: receipt, stock_at_this_store, purchase_date, evidence) is required - "
             "re-run question-intake; the engine does not read receipt, stock or purchase date from the text")
    if f.get("receipt") not in RECEIPT:
        fail(f"question.facts.receipt must be one of {list(RECEIPT)} (got {f.get('receipt')!r})")
    if f.get("stock_at_this_store") not in STOCK:
        fail(f"question.facts.stock_at_this_store must be one of {list(STOCK)} (got {f.get('stock_at_this_store')!r})")
    if "purchase_date" not in f:
        fail("question.facts.purchase_date is required (YYYY-MM-DD or null)")
    if f["purchase_date"] is not None:
        try:
            date.fromisoformat(f["purchase_date"])
        except (TypeError, ValueError):
            fail(f"question.facts.purchase_date must be YYYY-MM-DD or null (got {f['purchase_date']!r})")
    ev = f.get("evidence")
    if not isinstance(ev, dict):
        fail("question.facts.evidence (object) is required")
    for key, set_ in (("receipt", f["receipt"] != "unclear"), ("stock", f["stock_at_this_store"] != "unclear"),
                      ("purchase_date", f["purchase_date"] is not None)):
        if set_ and not (isinstance(ev.get(key), str) and ev[key].strip()):
            fail(f"question.facts.evidence.{key} (verbatim words) is required when that fact is not unclear/null")


def parse_asked_on(q):
    v = q.get("asked_on")
    if not isinstance(v, str):
        return None, "question.asked_on missing"
    try:
        return date.fromisoformat(v), None
    except ValueError:
        return None, f"question.asked_on {v!r} is not an ISO date (YYYY-MM-DD)"


def resolve_clause(qtext, lib):
    """Returns (key, clause, confidence, note) or (None, None, 0.0, note) when out of scope."""
    hits = []
    for k, v in lib.items():
        if k.startswith("_"):
            continue
        matched = [t for t in v["topics"] if t in qtext]
        if matched:
            hits.append((k, v, matched))
    if not hits:
        return None, None, 0.0, "no matching clause"
    families = {k.split(".")[0] for k, _, _ in hits}
    general = [(k, v, m) for k, v, m in hits if v["determination_hint"] != "excluded"]
    exclusions = [(k, v, m) for k, v, m in hits if v["determination_hint"] == "excluded"]
    # An exclusion outranks only on a DISTINGUISHING topic: one not listed by any general clause hit.
    general_topics = {t for _, v, _ in general for t in v["topics"]}
    promoted = [(k, v, m) for k, v, m in exclusions if any(t not in general_topics for t in m)]
    if promoted:
        k, v, m = promoted[0]
        conf = 0.9 if len(families) == 1 else 0.7
        return k, v, conf, f"exclusion {v['clause']} outranks on distinguishing topic(s) {m}"
    if general:
        k, v, m = general[0]
        if len(families) > 1:
            conf = 0.7
            note = f"question spans policy families {sorted(families)} - answered {v['clause']} first"
        elif exclusions:
            conf = 0.8
            note = f"{v['clause']} chosen; exclusion hit only on shared wording, no distinguishing topic"
        else:
            conf = 0.9
            note = f"single clause {v['clause']} matched on {m}"
        return k, v, conf, note
    # only exclusions hit, none on a distinguishing topic (config error: exclusion lists only shared topics)
    k, v, m = exclusions[0]
    return k, v, 0.7, f"exclusion {v['clause']} hit without a distinguishing topic - review config"


def phrase_spans(text, phrase):
    return [(m.start(), m.end()) for m in re.finditer(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text)]


def routed(lib, when):
    for k, v in lib.items():
        if not k.startswith("_") and v.get("applies_when") == when:
            return k, v
    return None, None


def return_gate(k, v, conf, qtext, lib, today, facts):
    """#1.4: a receipt-and-category clause resolves eligible only with facts.receipt in_hand, a covered category and
    facts.purchase_date inside that category's window. Returns (k, v, det, conf, note, in_scope, extra_conditions)."""
    receipt = facts["receipt"] if v.get("requires_receipt") else "in_hand"
    cats = v.get("categories") or {}
    covered = [c for c, terms in cats.items() if any(phrase_spans(qtext, t) for t in terms)] if cats else ["any"]
    if receipt != "in_hand":
        rk, rv = routed(lib, "no_receipt") if receipt == "not_in_hand" else (None, None)
        if rk:
            return rk, rv, rv["determination_hint"], conf, f"receipt not in hand - routed to {rv['clause']}", True, []
        det = "escalate_receipt_missing" if receipt == "not_in_hand" else "escalate_receipt_unknown"
        why = ("receipt not in hand - " if receipt == "not_in_hand" else "receipt status unclear - ask the associate; ") + \
              f"{v['clause']} requires a receipt and the library has no receiptless clause"
        return None, v, det, min(conf, GATED_CONFIDENCE), why, True, []
    if not covered:
        rk, rv = routed(lib, "category_not_covered")
        if rk:
            return rk, rv, rv["determination_hint"], conf, f"category not covered by {v['clause']} - routed to {rv['clause']}", True, []
        return None, v, "escalate_category_not_covered", min(conf, GATED_CONFIDENCE), \
            f"item category not stated or not covered by {v['clause']} (covers {sorted(cats)})", False, []
    windows = v.get("windows_days") or {}
    known = [windows[c] for c in covered if c in windows]
    if not known:
        return k, v, v["determination_hint"], conf, None, True, []
    days, cat = min(known), [c for c in covered if windows.get(c) == min(known)][0]
    pdate = date.fromisoformat(facts["purchase_date"]) if facts["purchase_date"] else None
    age = (today - pdate).days if (pdate and today) else None
    if age is not None and 0 <= age <= days:
        return k, v, v["determination_hint"], conf, None, True, []
    if age is not None and age > days:
        return k, v, "not_eligible_outside_window", conf, f"purchased {age} days before the asked date, outside the {days}-day {cat} window", True, \
            [f"Purchased {pdate} ({age} days before {today}): outside the {days}-day {cat} return window - not eligible under {v['clause']} (#1.4)"]
    why = "purchase date not recorded" if pdate is None else f"purchase date {pdate} cannot be checked against asked date {today}"
    return k, v, "confirm_purchase_date", min(conf, GATED_CONFIDENCE), f"{why} - confirm the receipt date before any return", True, \
        [f"Eligible only if within {days} days of purchase ({cat}) - confirm the receipt date (#1.4)"]


def raincheck_gate(k, v, conf, lib, pc, promo_flags, facts):
    """#2.3: raincheck only when facts.stock_at_this_store is out_of_stock AND the promo is live for the date and
    the store's cluster."""
    stock = facts["stock_at_this_store"]
    esc = []
    if v.get("requires_promo_active"):
        if not pc["checked"]:
            return None, "escalate_promo_unknown", min(conf, GATED_CONFIDENCE), \
                f"promo status could not be checked ({'; '.join(pc['reasons'])}) - no {v['clause']} until it is", [], \
                [f"{v['clause']} needs the advertised promo live at this store - promo not checked; no raincheck offered (#2.3)"]
        if not pc["eligible"]:
            if promo_flags.get("cluster_fail"):
                esc.append(f"store cluster not participating in {', '.join(promo_flags['cluster_fail'])} - no raincheck; "
                           f"a customer dispute about the advert is a manager decision (#2.3)")
            return None, "no_alternative_promo_not_eligible", conf, \
                f"promo not live for this date / store - {v['clause']} does not apply", esc, \
                [f"{v['clause']} applies only to an advertised promo item that is out of stock while the promo is live "
                 f"at this store; the promo is not (see promo_check) - no policy alternative (#2.3)"]
    if v.get("requires_out_of_stock"):
        if stock == "in_stock":
            return None, "no_alternative_in_stock", conf, f"item reported in stock - {v['clause']} does not apply", [], \
                [f"Item reported in stock - {v['clause']} covers advertised promo items that are out of stock only (#2.3)"]
        if stock == "unclear":
            return None, "escalate_stock_unknown", min(conf, GATED_CONFIDENCE), \
                "stock at this store unclear - ask the associate to check shelf and back room; no raincheck offered", [], \
                [f"{v['clause']} needs the item out of stock at this store; stock status unclear (#2.3)"]
    return v["clause"], v["determination_hint"], conf, None, [], [v["text"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True); ap.add_argument("--policies", required=True)
    ap.add_argument("--promos", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8")); lib = json.load(open(a.policies, encoding="utf-8"))
    promos = json.load(open(a.promos, encoding="utf-8"))
    check_contract(p)
    esc = list(p.get("escalations", []))
    qtext = normalise(p["question"]["text"])
    facts = p["question"]["facts"]

    # promo check (#2.1): window AND cluster AND SKU - computed first so the raincheck gate (#2.3) can read it
    promo_esc = []
    promo_flags = {"cluster_fail": []}
    sku = p["question"].get("sku")
    today, date_err = parse_asked_on(p["question"])
    cluster = (p.get("store_context") or {}).get("cluster")
    pc = {"checked": False, "eligible": False, "reasons": [], "source": ENGINE, "citation": "promo pack"}
    if not sku:
        pc["reasons"] = ["no SKU on the question - promo not checked"]
    elif date_err:
        pc["reasons"] = [f"{date_err} - promo window cannot be evaluated (#2.1)"]
        promo_esc.append(f"{date_err} - ask the associate for the date asked; promo eligibility not determined (#2.1)")
    elif not cluster:
        pc["reasons"] = ["store_context.cluster missing - promo cluster leg cannot be evaluated (#2.1)"]
        promo_esc.append("store cluster missing - the store master export from the user's files is missing or has no row "
                         "for this store; ask the user for the store master export; promo eligibility not determined (#2.1)")
    else:
        pc["checked"] = True
        citations = []
        for pr in promos:
            if sku in pr["skus"]:
                citations.append(pr["citation"])
                in_window = date.fromisoformat(pr["start"]) <= today <= date.fromisoformat(pr["end"])
                in_cluster = cluster in pr["clusters"]
                if in_window and in_cluster:
                    pc.update(eligible=True, promo_id=pr["promo_id"],
                              reasons=[f"{pr['name']}: window + cluster + SKU all match (#2.1)"])
                else:
                    if not in_window: pc["reasons"].append(f"{pr['promo_id']}: outside window {pr['start']}..{pr['end']} (today {today})")
                    if not in_cluster:
                        pc["reasons"].append(f"{pr['promo_id']}: store cluster '{cluster}' not in {pr['clusters']}")
                        promo_flags["cluster_fail"].append(pr["promo_id"])
        if citations:
            pc["citation"] = citations[0] if len(citations) == 1 else "; ".join(citations)
        if not pc["reasons"]:
            pc["reasons"] = ["SKU on no promo list"]

    k, v, conf, note = resolve_clause(qtext, lib)
    if k is None:
        p["policy_resolution"] = {"topic": p["question"].get("topic", "unknown"), "applicable_clause": None,
            "determination": "out_of_scope", "conditions": [], "in_scope": False, "confidence": 0.0,
            "source": ENGINE, "citation": "no matching clause (assist-rules.md #1.2)"}
        esc.append("question outside policy library scope - escalation drafted, no improvised policy (assist-rules.md #1.2)")
    else:
        clause, det, conditions, in_scope = v["clause"], v["determination_hint"], [v["text"]], True
        citation, gate_esc = f"policy clause {v['clause']}", []
        if v.get("requires_receipt") or v.get("categories"):
            gk, gv, det, conf, gnote, in_scope, extra = return_gate(k, v, conf, qtext, lib, today, facts)
            if gk == k:
                conditions += extra
                note = gnote or note
            if gk is None:
                clause, citation = None, f"policy clause {v['clause']} requirement not met (assist-rules.md #1.4)"
                note = gnote
            elif gk != k:
                k, clause, conditions, citation, note = gk, gv["clause"], [gv["text"]], f"policy clause {gv['clause']}", gnote
        elif v.get("requires_out_of_stock") or v.get("requires_promo_active"):
            clause, det, conf, gnote, gate_esc, conditions = raincheck_gate(k, v, conf, lib, pc, promo_flags, facts)
            if clause is None:
                citation = f"policy clause {v['clause']} not applicable (assist-rules.md #2.3)"
                note = gnote
        p["policy_resolution"] = {"topic": k, "applicable_clause": clause,
            "determination": det, "conditions": conditions, "in_scope": in_scope,
            "confidence": conf, "source": ENGINE, "citation": citation}
        if conf < CONFIDENCE_FLOOR:
            esc.append(f"resolution confidence {conf} < {CONFIDENCE_FLOOR} ({note}) - shift-lead escalation with the draft attached (assist-rules.md #4.1)")
        esc.extend(gate_esc)
    esc.extend(promo_esc)
    p["promo_check"] = pc; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    pr = p["policy_resolution"]
    print(f"policy_resolve: clause={pr['applicable_clause']} det={pr['determination']} conf={pr['confidence']} promo_eligible={pc['eligible']} -> {a.out}")
    return 0


if __name__ == "__main__": sys.exit(main())
