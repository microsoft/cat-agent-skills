#!/usr/bin/env python3
"""similar_work - deterministic similar-past-work ranking engine (mfg.work-order-assist.v1).

Reads the enriched work-order contract (current WO signals + required parts + retrieved prior
fixes + asset work-order history) and ranks the most similar past work orders. Applies the
recurring-failure rule and surfaces a superseding-fix recommendation. Emits the {similar_work}
and {superseding_fix} hops of the contract and a preliminary next_best_action.

Same input, same output, always: no LLM calls, no network, no randomness. The model invokes this
and quotes its output; it never re-ranks the prior work itself.

Rules encoded here mirror references/similar-work-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:similar_work"
CONFIDENCE_FLOOR = 0.75          # similar-work-rules.md #4.1
REPEAT_THRESHOLD = 3             # similar-work-rules.md #3.1

# similarity weights (similar-work-rules.md #2)
W_SAME_ASSET = 4
W_SAME_CLASS = 2
W_SAME_COMPONENT = 3
W_KEYWORD = 2
W_PART = 2


def score_prior(wo, cur_asset, cur_class, cur_comp, cur_kw, cur_parts):
    raw, matched, sigtypes = 0, [], set()
    same_asset = wo.get("asset_id", cur_asset) == cur_asset
    if same_asset:
        raw += W_SAME_ASSET; matched.append(f"asset:{cur_asset}"); sigtypes.add("asset")
    elif cur_class and wo.get("asset_class") == cur_class:
        raw += W_SAME_CLASS; matched.append(f"class:{cur_class}"); sigtypes.add("asset")
    if cur_comp and wo.get("component") == cur_comp:
        raw += W_SAME_COMPONENT; matched.append(f"component:{cur_comp}"); sigtypes.add("component")
    shared_kw = sorted(cur_kw & set(wo.get("keywords", [])))
    for k in shared_kw:
        raw += W_KEYWORD; matched.append(f"keyword:{k}")
    if shared_kw:
        sigtypes.add("keyword")
    shared_parts = sorted(cur_parts & set(wo.get("parts_used", [])))
    for p in shared_parts:
        raw += W_PART; matched.append(f"part:{p}")
    if shared_parts:
        sigtypes.add("parts")
    return raw, matched, sigtypes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True, help="wo-intake.json (enriched contract input)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.intake, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.work-order-assist.v1", "wrong contract version"

    cur_asset = payload.get("asset_id")
    cur_class = payload.get("asset_class")
    cur_comp = payload.get("component")
    cur_kw = {k["name"] for k in payload.get("issue_keywords", [])}
    cur_parts = {p["part_no"] for p in payload.get("required_parts", [])}
    default_parts = set(cur_parts)
    sop = payload.get("sop_ref", {}) or {}
    default_remedy = sop.get("default_remedy") or "the SOP default remedy"
    escalations = list(payload.get("escalations", []))

    prior = (payload.get("history", {}) or {}).get("prior_work_orders", []) or []

    scored = []
    for wo in prior:
        raw, matched, sigtypes = score_prior(wo, cur_asset, cur_class, cur_comp, cur_kw, cur_parts)
        if raw > 0:
            conf = min(0.97, round(0.60 + 0.06 * len(sigtypes), 2))
            scored.append({"wo": wo, "raw": raw, "matched": matched, "confidence": conf})

    total_raw = sum(s["raw"] for s in scored)
    for s in scored:
        s["similarity_score"] = round(s["raw"] / total_raw, 3) if total_raw else 0.0

    # --- recurring-failure detection (similar-work-rules.md #3.1) ---
    def used_default(wo):
        return bool(set(wo.get("parts_used", [])) & default_parts) if default_parts else False
    recurred_defaults = [wo for wo in prior
                         if used_default(wo) and wo.get("outcome") in ("recurred", "reopened")]
    repeat_promotion = len(recurred_defaults) >= REPEAT_THRESHOLD

    # sort: most similar first, then most recent, then wo_id
    scored.sort(key=lambda s: (-s["raw"], s["wo"].get("date", ""), s["wo"].get("wo_id", "")),
                reverse=False)
    scored.sort(key=lambda s: -s["raw"])

    similar = []
    for rank, s in enumerate(scored, start=1):
        wo = s["wo"]
        is_repeat = repeat_promotion and used_default(wo) and wo.get("outcome") in ("recurred", "reopened")
        similar.append({
            "rank": rank,
            "wo_id": wo.get("wo_id", "unknown"),
            "similarity_score": s["similarity_score"],
            "shared_signals": s["matched"],
            "outcome": wo.get("outcome", "unknown"),
            "recommended_fix": wo.get("action_taken", ""),
            "repeat_failure": bool(is_repeat),
            "confidence": s["confidence"],
            "source": ENGINE,
            "citation": f"{wo.get('citation', 'work-order-history')}; similar-work-rules.md #2",
        })

    # --- superseding-fix rule (similar-work-rules.md #3.3) ---
    fixes = (payload.get("retrieved", {}) or {}).get("prior_fixes", []) or []
    sf_note = next((f for f in fixes if f.get("recommended_change") and f.get("superseding_part")), None)
    if sf_note:
        superseding = {
            "active": True,
            "from_fix_note": sf_note.get("fix_note_id", ""),
            "supersedes_part": sf_note.get("supersedes_part", ""),
            "recommended_part": sf_note.get("superseding_part", ""),
            "rationale": sf_note.get("summary", ""),
            "confidence": 0.9,
            "source": ENGINE,
            "citation": f"{sf_note.get('citation', 'fix-note')}; similar-work-rules.md #3.3",
        }
    else:
        superseding = {"active": False, "source": ENGINE, "confidence": 0.0,
                       "citation": "similar-work-rules.md #3.3"}

    # --- escalations ---
    if repeat_promotion:
        escalations.append(
            f"Recurring failure: the SOP-default remedy recurred {len(recurred_defaults)} times on "
            f"{cur_asset} with the fault returning. Open a root-cause analysis before repeating it "
            f"(similar-work-rules.md #3.1, #4.3).")
    if not similar:
        escalations.append(
            f"No comparable prior work order found for {cur_asset}; proceed from the SOP and manual "
            f"alone and confirm with the planner (similar-work-rules.md #4.2).")
    elif similar[0]["confidence"] < CONFIDENCE_FLOOR:
        escalations.append(
            f"Closest prior work WO {similar[0]['wo_id']} confidence {similar[0]['confidence']} below "
            f"{CONFIDENCE_FLOOR} floor; confirm the comparable job manually (similar-work-rules.md #4.1).")

    # --- preliminary next-best action (parts-readiness finalizes it) ---
    if superseding["active"]:
        nba = (f"Install {superseding['recommended_part']} (supersedes "
               f"{superseding['supersedes_part']}) per fix note {superseding['from_fix_note']}; "
               f"do NOT repeat the SOP-default {superseding['supersedes_part']} replacement.")
        if repeat_promotion:
            nba += " Open an RCA on the recurring failure."
    elif repeat_promotion:
        nba = ("Do not simply repeat the recurring SOP-default remedy; escalate for a root-cause "
               "analysis and confirm the corrective action.")
    else:
        nba = f"Proceed per {sop.get('doc', 'the SOP')}: {default_remedy}"

    payload["similar_work"] = similar
    payload["superseding_fix"] = superseding
    payload["next_best_action"] = nba
    payload["escalations"] = escalations
    hist = payload.setdefault("history", {})
    hist["repeat_failures"] = len(recurred_defaults)
    hist["repeat_promotion"] = repeat_promotion

    _finish(payload, a.out)
    print(f"similar_work: {len(similar)} match(es), top={similar[0]['wo_id'] if similar else 'none'}, "
          f"repeat_promotion={repeat_promotion}, superseding={superseding['active']} -> {a.out}")
    return 0


def _finish(payload, out):
    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "similar_work/1.0" not in prov["engines"]:
        prov["engines"].append("similar_work/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(payload, open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
