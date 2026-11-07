#!/usr/bin/env python3
"""intent_classify - deterministic intent classification (rtl.customer-service-order-support.v1, #1.1).

v1.1: word-boundary keyword matching (no substring hits such as 'track' in 'contract'),
curly-apostrophe / whitespace normalisation, explicit input checks instead of bare asserts.
Run from the skill folder (skills/inquiry-intake); inquiry.json is built in the session
working folder from the user's own chat/email/call notes:
  python scripts/intent_classify.py --inquiry <session>/inquiry.json \
      --config config/service-config.json --out <session>/classified.json
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone

ENGINE = "engine:intent_classify"
ENGINE_VERSION = "intent_classify/1.1"
CONTRACT = "rtl.customer-service-order-support.v1"


def fail(msg: str) -> int:
    print(f"intent_classify: ERROR - {msg}", file=sys.stderr)
    return 2


def normalise(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text).strip()


def keyword_hits(text: str, keywords) -> int:
    hits = 0
    for kw in keywords:
        pattern = r"(?<!\w)" + re.escape(normalise(kw)) + r"(?!\w)"
        if re.search(pattern, text):
            hits += 1
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inquiry", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        with open(a.inquiry, encoding="utf-8") as f:
            p = json.load(f)
        with open(a.config, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return fail(f"cannot read inputs: {e}")
    if p.get("contract_version") != CONTRACT:
        return fail(f"contract_version must be {CONTRACT}, got {p.get('contract_version')!r}")
    inquiry = p.get("inquiry")
    if not isinstance(inquiry, dict) or not isinstance(inquiry.get("text"), str):
        return fail("inquiry.text (string) is required - the customer's words stay verbatim")
    taxonomy = cfg.get("intent_taxonomy")
    floor = cfg.get("confidence_floor")
    if not isinstance(taxonomy, dict) or not isinstance(floor, (int, float)):
        return fail("config needs intent_taxonomy (object) and confidence_floor (number)")

    text = normalise(inquiry["text"])
    hits = [(cat, keyword_hits(text, kws)) for cat, kws in taxonomy.items()]
    hits = [(c, n) for c, n in hits if n > 0]
    hits.sort(key=lambda t: -t[1])
    # DNR outranks generic WISMO when both match (#2.1 is the safety-relevant path)
    if any(c == "delivered_not_received" for c, _ in hits):
        cat, conf = "delivered_not_received", 0.9
    elif hits:
        cat = hits[0][0]
        conf = 0.9 if len(hits) == 1 or hits[0][1] > hits[1][1] else 0.7
    else:
        cat, conf = "unclassified", 0.3
    p["intent"] = {"category": cat, "confidence": conf, "source": ENGINE,
                   "citation": "intent taxonomy (config/service-config.json)"}
    if conf < floor:
        p.setdefault("escalations", []).append(
            f"intent confidence {conf} < {floor} - handoff, not a guessed answer (service-rules.md #1.1)")
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)
    print(f"intent_classify: {cat} (conf {conf}) -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
