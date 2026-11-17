#!/usr/bin/env python3
"""claim_check - deterministic claim / regulated-term validation (Govern engine,
rtl.product-content-enrichment.v1). Rules mirror references/enrichment-rules.md:
  #4.1 a claim ships only if the library approves it FOR THAT GTIN and market -
       approved claims of OTHER GTINs found in the copy are 'unapproved';
  #4.2 regulated terms are blocked without substantiation for the market;
  #4.3 blocked claims never appear in copy;
  #4.4 supplier romance terms (config romance_terms) are 'unapproved' unless the library approves them;
  #1.1 a record whose GTIN failed the GS1 check stays blocked - findings carry record_blocked.

Matching is by normalised substring (lower-case, punctuation/whitespace folded), so a
multi-word library claim such as "antibacterial coating" is recognised in the copy and
satisfies the regulated token "antibacterial" it contains (v1.0.2 fix)."""
import argparse, json, re, sys
from datetime import datetime, timezone
ENGINE = "engine:claim_check"


def norm(s):
    """Lower-case, fold punctuation and whitespace so 'Anti-bacterial  Coating!' == 'antibacterial coating'."""
    s = (s or "").lower().replace("-", "")
    s = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", s)      # keep '.' only inside numbers (99.9%)
    s = re.sub(r"[^a-z0-9%.]+", " ", s)
    return " " + re.sub(r"\s+", " ", s).strip() + " "


def contains(text_n, phrase):
    ph = norm(phrase).strip()
    return ph != "" and (" " + ph + " ") in text_n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True); ap.add_argument("--library", required=True)
    ap.add_argument("--market", default="US"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.scored, encoding="utf-8")); lib = json.load(open(a.library, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    esc = list(p.get("escalations", [])); findings = []
    approved = lib.get("approved", [])
    regulated = list(lib.get("regulated_terms", []))
    romance = list(lib.get("romance_terms", []))

    def library_hit(gtin, phrase):
        """Library entry for THIS gtin (or the batch brand scope) whose claim text contains the phrase."""
        for e in approved:
            scope_ok = e.get("gtin") == gtin or (e.get("brand") and e.get("brand") == p.get("brand"))
            if scope_ok and contains(norm(e["claim"]), phrase):
                return e
        return None

    for r in p["normalized"]:
        gtin = r["gtin"]; blocked_rec = not r.get("gtin_valid", True)
        copy_n = norm(r["attributes"].get("supplier_copy") or "")
        seen = set()

        def add(claim, verdict, detail, citation):
            key = (claim.lower(), verdict)
            if key in seen: return
            seen.add(key)
            f = {"gtin": gtin, "claim": claim, "verdict": verdict, "market": a.market, "detail": detail,
                 "source": ENGINE, "citation": citation}
            if blocked_rec: f["record_blocked"] = True
            findings.append(f)

        if blocked_rec:
            esc.append(f"GTIN {gtin}: record BLOCKED on invalid GS1 check digit - claims evaluated for the steward only, "
                       f"nothing from this record may be drafted (enrichment-rules.md #1.1)")
        # --- #4.2 regulated terms -------------------------------------------------------
        for term in regulated:
            if not contains(copy_n, term): continue
            hit = library_hit(gtin, term)
            if hit and a.market in hit.get("markets", []):
                add(hit["claim"], "approved",
                    f"substantiated: {hit['substantiation']} (library claim '{hit['claim']}' covers regulated term '{term}')",
                    f"claim library {hit['substantiation']} (#4.1)")
            else:
                why = (f"library claim '{hit['claim']}' is not cleared for market {a.market} (markets: {', '.join(hit.get('markets', []))})"
                       if hit else f"regulated term without substantiation for market {a.market}")
                add(term, "regulated_blocked", f"{why} - BLOCKED from copy (#4.2, #4.3)",
                    "config/claim-library.json regulated_terms")
                esc.append(f"GTIN {gtin}: regulated claim '{term}' BLOCKED - {why} (enrichment-rules.md #4.2)")
        # --- #4.1 non-regulated library claims: approved for THIS gtin, else unapproved ----------
        for e in approved:
            if not contains(copy_n, e["claim"]): continue
            if any(contains(norm(e["claim"]), t) for t in regulated): continue  # handled above
            if e.get("gtin") == gtin and a.market in e.get("markets", []):
                add(e["claim"], "approved", f"substantiated: {e['substantiation']}", f"claim library {e['substantiation']} (#4.1)")
            else:
                who = f"GTIN {e.get('gtin')}" if e.get("gtin") != gtin else f"market(s) {', '.join(e.get('markets', []))}"
                add(e["claim"], "unapproved",
                    f"claim is approved only for {who}, not for this GTIN in {a.market} - not usable in copy (#4.1)",
                    "config/claim-library.json approved (scope mismatch)")
                esc.append(f"GTIN {gtin}: claim '{e['claim']}' UNAPPROVED for this GTIN/market - approved only for {who} (enrichment-rules.md #4.1)")
        # --- #4.4 romance terms ---------------------------------------------------------------
        for term in romance:
            if not contains(copy_n, term): continue
            if any(contains(norm(term), t) for t in regulated): continue
            hit = library_hit(gtin, term)
            if hit and a.market in hit.get("markets", []):
                add(hit["claim"], "approved", f"substantiated: {hit['substantiation']}", f"claim library {hit['substantiation']} (#4.1)")
            else:
                add(term, "unapproved",
                    "supplier romance term with no library approval for this GTIN - dropped from copy, not a blocker (#4.4)",
                    "config/claim-library.json romance_terms")
    p["claim_findings"] = findings; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("claim_check/1.0.3")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    n = lambda v: sum(1 for f in findings if f["verdict"] == v)
    print(f"claim_check: {len(findings)} finding(s), approved={n('approved')}, unapproved={n('unapproved')}, "
          f"blocked={n('regulated_blocked')}, market={a.market} -> {a.out}")
    return 0


if __name__ == "__main__": sys.exit(main())
