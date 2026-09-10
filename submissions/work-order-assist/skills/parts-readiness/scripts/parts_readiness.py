#!/usr/bin/env python3
"""parts_readiness - deterministic parts-readiness engine (mfg.work-order-assist.v1).

Reads the contract produced by similar_work (required parts + parts catalog + any superseding-fix
recommendation) and computes a per-part line status and an overall work-order readiness against
storeroom stock and the supersession table. Emits the {parts_readiness} hop and finalizes the
next_best_action for the write-up.

Deterministic: no LLM, no network, no randomness. Rules mirror
references/parts-readiness-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:parts_readiness"

# overall status precedence, worst-case first (parts-readiness-rules.md #4)
STATUS_RANK = {"BLOCKED": 4, "PARTIAL": 3, "READY_WITH_SUBSTITUTION": 2, "READY": 1}


def line_for(rp, catalog, sf_active, sf_supersedes, sf_recommended, escalations, asset_class):
    pn = rp["part_no"]
    qty = float(rp.get("qty", 1))
    crit = (rp.get("criticality") or "standard").lower()
    row = catalog.get(pn)
    found = row is not None
    on_hand = float(row.get("on_hand", 0)) if row else 0.0
    lead = row.get("lead_time_days") if row else None
    superseded_by = (row.get("superseded_by") if row else None) or None
    # superseding-fix override (parts-readiness-rules.md #2.2)
    if sf_active and sf_supersedes == pn and sf_recommended:
        superseded_by = superseded_by or sf_recommended

    note = ""
    effective = pn
    line_status = None

    if superseded_by:
        repl = catalog.get(superseded_by)
        repl_on_hand = float(repl.get("on_hand", 0)) if repl else 0.0
        note = f"{pn} superseded by {superseded_by} (parts-readiness-rules.md #2.1)."
        if repl_on_hand >= qty and on_hand < qty:
            line_status = "SUPERSEDED_AVAILABLE"; effective = superseded_by
            escalations.append(
                f"SOP references superseded part {pn}; order the replacement {superseded_by} "
                f"(in stock) and flag the SOP for update (parts-readiness-rules.md #2.2, #2.3).")
        elif on_hand >= qty:
            line_status = "IN_STOCK"
            note += f" Original {pn} still in stock; prefer {superseded_by} on next order."
        else:
            line_status = "BLOCKED" if crit == "critical" else "OUT"
            escalations.append(
                f"Part {pn} out of stock and its replacement {superseded_by} is not in stock; "
                f"expedite procurement (parts-readiness-rules.md #3.1).")
    else:
        if on_hand >= qty:
            line_status = "IN_STOCK"
        elif on_hand > 0:
            line_status = "SHORT"
        else:
            line_status = "BLOCKED" if crit == "critical" else "OUT"

    # critical-part escalations (parts-readiness-rules.md #3)
    if line_status == "BLOCKED":
        escalations.append(
            f"Critical part {pn} is out of stock with no substitute; do not schedule the job until "
            f"it lands (parts-readiness-rules.md #3.1).")
    elif line_status == "SHORT" and crit == "critical":
        escalations.append(
            f"Critical part {pn} is short (have {on_hand:g}, need {qty:g}); reserve/expedite before "
            f"scheduling (parts-readiness-rules.md #3.2).")
    if line_status in ("SHORT", "OUT", "BLOCKED") and asset_class == "A":
        escalations.append(
            f"Class-A asset with a parts shortage on {pn}; notify the planner and storeroom lead "
            f"(parts-readiness-rules.md #3.3).")

    if not found:
        note = (note + " Part not found in catalog; confirm the part number.").strip()

    return {
        "part_no": pn,
        "description": rp.get("description", row.get("description", "") if row else ""),
        "required_qty": qty,
        "on_hand": on_hand,
        "line_status": line_status,
        "effective_part": effective,
        "lead_time_days": lead,
        "note": note,
        "citation": f"parts-catalog.csv {pn}; parts-readiness-rules.md #1",
    }, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--similar", required=True, help="output of similar_work (contract)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.similar, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.work-order-assist.v1", "wrong contract version"

    required = payload.get("required_parts", []) or []
    catalog = {c["part_no"]: c for c in payload.get("parts_catalog", []) or []}
    asset_class = (payload.get("asset_criticality") or "").upper()
    sf = payload.get("superseding_fix", {}) or {}
    sf_active = bool(sf.get("active"))
    sf_supersedes = sf.get("supersedes_part")
    sf_recommended = sf.get("recommended_part")
    escalations = list(payload.get("escalations", []))

    lines, all_found = [], True
    for rp in required:
        line, found = line_for(rp, catalog, sf_active, sf_supersedes, sf_recommended,
                               escalations, asset_class)
        lines.append(line)
        all_found = all_found and found

    # overall status (parts-readiness-rules.md #4)
    if lines:
        worst = max(
            (STATUS_RANK.get(_fold(l["line_status"]), 1) for l in lines), default=1)
        status = next(k for k, v in STATUS_RANK.items() if v == worst)
    else:
        status = "READY"

    blockers = [f"{l['part_no']} ({l['line_status']})" for l in lines
                if l["line_status"] in ("BLOCKED", "OUT", "SHORT")]

    parts_readiness = {
        "status": status,
        "lines": lines,
        "blockers": blockers,
        "confidence": 0.9 if all_found else 0.7,
        "source": ENGINE,
        "citation": "parts-readiness-rules.md #1-#4; parts-catalog.csv",
    }
    payload["parts_readiness"] = parts_readiness

    # --- finalize next_best_action ---
    if status == "BLOCKED":
        payload["next_best_action"] = (
            "Do NOT schedule yet: expedite " + ", ".join(blockers) +
            " before this work order can be executed.")
    elif sf_active and any(l["line_status"] == "SUPERSEDED_AVAILABLE" for l in lines):
        payload["next_best_action"] = (
            f"Install {sf_recommended} (supersedes {sf_supersedes}) per fix note "
            f"{sf.get('from_fix_note')} - the replacement is in stock; do NOT re-fit "
            f"{sf_supersedes}." +
            (" Open an RCA on the recurring failure." if payload.get("history", {}).get("repeat_promotion") else ""))
    elif status == "PARTIAL":
        payload["next_best_action"] = (
            (payload.get("next_best_action", "") + " ").strip() +
            " Reserve/expedite short parts (" + ", ".join(blockers) + ") before scheduling.")
    # READY / READY_WITH_SUBSTITUTION with no superseding fix: keep similar_work's action.

    payload["escalations"] = escalations

    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "parts_readiness/1.0" not in prov["engines"]:
        prov["engines"].append("parts_readiness/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    json.dump(payload, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"parts_readiness: {status}, {len(lines)} line(s), blockers={len(blockers)} -> {a.out}")
    return 0


def _fold(ls):
    # map line statuses to the overall-status vocabulary for precedence
    return {"IN_STOCK": "READY", "SUPERSEDED_AVAILABLE": "READY_WITH_SUBSTITUTION",
            "SHORT": "PARTIAL", "OUT": "PARTIAL", "BLOCKED": "BLOCKED"}.get(ls, "READY")


if __name__ == "__main__":
    sys.exit(main())
