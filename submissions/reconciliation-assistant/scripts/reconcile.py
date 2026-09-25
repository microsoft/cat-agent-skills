#!/usr/bin/env python3
"""Config-driven reconciliation for code-capable hosts (Cowork, Scout).

Reads two datasets described by a JSON config (see assets/config.example.json),
runs a tiered match (exact -> difference -> similarity -> grouped -> unmatched),
proves the control totals tie out, and writes an .xlsx report.

This is a reference implementation the agent adapts to the actual column names
and file paths in play. It has no hidden behaviour: every rule here mirrors
SKILL.md and references/methodology.md.

Usage:
    python reconcile.py --config config.json --source-a A.xlsx --source-b B.csv --out reconciliation.xlsx

Dependencies: pandas, openpyxl. (difflib is stdlib and used for similarity.)
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher

import pandas as pd


# ----------------------------- loading -----------------------------

def load_table(path, sheet=None):
    lower = path.lower()
    if lower.endswith((".xlsx", ".xlsm")):
        # sheet may be a name or an index; None loads the first sheet. openpyxl is the declared
        # dependency and reads .xlsx/.xlsm. Legacy .xls needs the separate `xlrd` engine, which is
        # NOT a declared dependency, so we do not advertise .xls here - re-save such files as .xlsx.
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    if lower.endswith(".tsv"):
        return pd.read_csv(path, sep="\t")
    return pd.read_csv(path)


def _is_missing(value):
    """True for any pandas/NumPy missing scalar (None, float nan, pd.NA, pd.NaT). Using
    isinstance(value, float) alone misses pd.NA/pd.NaT (common in nullable-dtype or date columns),
    which would otherwise fall through to str() and become literal keys like "<NA>"/"NaT" or be
    treated as real amounts. pd.isna raises/return arrays for list-like input, so guard with a
    scalar check and swallow the non-scalar case."""
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(result) if isinstance(result, bool) or getattr(result, "ndim", 0) == 0 else False


def default_label(path, sheet=None):
    """A human label for a source: file name, plus a sheet qualifier when reconciling tabs. A
    named sheet is appended by name; a numeric sheet index is appended as "sheet N" so two tabs of
    the SAME workbook selected by index (e.g. 0 and 1) still get DISTINCT labels instead of
    collapsing to the bare file name (which would make the two sides ambiguous in the report)."""
    import os
    base = os.path.splitext(os.path.basename(path))[0]
    if isinstance(sheet, int):
        return f"{base} — sheet {sheet}"
    if sheet is not None:
        return f"{base} — {sheet}"
    return base


def normalize_amount(value, norm):
    """Return a float from a possibly messy amount cell, or None. The result is quantized to the
    cent (2 decimals) so that "exact to the cent" matching is deterministic and immune to binary
    floating-point noise - two cells that should be equal (e.g. both "1250.00") can otherwise parse
    to minutely different floats and, with a zero tolerance, be pushed to "Matched (with
    difference)". Quantizing here means the matcher, the per-key model and the workbook all compare
    the same cent-rounded values (the workbook already rounds to 2 dp when classifying)."""
    if _is_missing(value):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    s = str(value).strip()
    if not s:
        return None
    negative = False
    # Parentheses denote a negative in accounting notation. Detect them BEFORE stripping currency
    # symbols so a wrapped value like "$(50.00)", "USD (50.00)" or "(50.00)-" - where a currency
    # symbol or sign sits outside the parentheses, so the string does not literally start with "(" -
    # is still recognised as negative instead of parsing to a positive number.
    if norm.get("parenthesesMeanNegative", True) and "(" in s and ")" in s and s.index("(") < s.rindex(")"):
        negative = True
        s = s.replace("(", "").replace(")", "")
    if norm.get("stripCurrencySymbols", True):
        s = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
    s = s.replace(",", "")
    try:
        amt = float(s)
    except ValueError:
        return None
    # Use -abs() rather than -amt so a value that ALSO carries an inner minus sign (e.g.
    # "(-50.00)") isn't double-negated back to positive: the parentheses are authoritative for the
    # sign, magnitude comes from the parsed number.
    return round(-abs(amt) if negative else amt, 2)


def apply_sign(amount, convention):
    if amount is None:
        return None
    if convention == "flip":
        return -amount
    return amount


_MULTISPACE = re.compile(r" {2,}")


def norm_key(value, norm):
    # Canonicalize a key component. Integer-valued floats (e.g. 7100.0 that pandas produced
    # because another row was blank) are rendered as "7100" so a Python key matches what Excel
    # writes when it concatenates the same numeric cell - keeping all three outputs in step.
    if _is_missing(value):
        s = ""
    elif isinstance(value, float) and value.is_integer():
        s = str(int(value))
    else:
        s = str(value)
    if norm.get("trimWhitespace", True):
        # Mirror Excel TRIM(): strip leading/trailing spaces AND collapse internal runs of spaces
        # to a single space. If we only did .strip(), a component like "ACME  CORP" would stay
        # distinct in the Python union while Excel's TRIM in the Matching Key formula collapses it
        # to "ACME CORP" - the two would then disagree and SUMIF/COUNTIF could double-count.
        s = _MULTISPACE.sub(" ", s).strip(" ")
    if norm.get("caseInsensitiveKeys", True):
        s = s.lower()
    return s


# One delimiter for every key builder - the Python matcher (build_key), the Excel helper
# (_xl_key_formula), the workbook union (keystr) and the HTML path (kstr) - so the three outputs
# group keys identically. A delimiter-only string can never stand in for a real key because
# join_key_parts collapses an all-empty key to "".
KEY_DELIM = " | "

# Escape sequence applied to every key COMPONENT before it is joined, both in Python
# (_escape_key_component) and in Excel (_xl_escape_component via nested SUBSTITUTE), with the exact
# same order. It does two jobs at once:
#   1. Injectivity: the join delimiter contains "|", so a raw "|" inside a component would make
#      composite keys ambiguous - ['a | b','c'] and ['a','b | c'] would both build "a | b | c".
#      Escaping "|" removes that collision.
#   2. Wildcard safety: Excel treats *, ?, ~ as wildcards/escapes inside SUMIF/COUNTIF criteria, so
#      a key value containing one of them would aggregate unrelated rows. Escaping them means the
#      stored Matching Key (and therefore every SUMIF/COUNTIF criterion built from it) contains no
#      raw wildcard character.
# "^" is the escape introducer (escaped first as "^^" so the mapping stays reversible/injective);
# it is not an Excel wildcard. Components with none of ^ | * ? ~ (e.g. ordinary account codes,
# company names, periods) pass through unchanged.
_KEY_ESCAPES = (("^", "^^"), ("|", "^p"), ("*", "^a"), ("?", "^q"), ("~", "^t"))


def _escape_key_component(part):
    for raw, rep in _KEY_ESCAPES:
        part = part.replace(raw, rep)
    return part


def join_key_parts(parts):
    """Join normalized key components with the shared delimiter, collapsing an all-empty key to
    "" so keyless rows are treated as keyless everywhere (matcher, workbook, HTML) instead of
    grouping under a delimiter-only string. Each component is escaped first (see _KEY_ESCAPES) so
    the join is injective and the resulting key carries no Excel wildcard characters."""
    return KEY_DELIM.join(_escape_key_component(p) for p in parts) if any(parts) else ""


def build_key(row, key_cols, norm):
    # Exact/similarity tiers treat a "" key as keyless (see the `_key != ""` guard and the
    # similarity empty-key check), so join_key_parts collapsing all-empty parts to "" is what
    # keeps that protection intact.
    return join_key_parts([norm_key(row.get(c), norm) for c in key_cols])


# A row whose key components are ALL blank has no usable key. The record matcher treats such a row
# as non-matchable (its own one-sided break). The per-key views (workbook SUMIF/COUNTIF and the
# HTML aggregation) would otherwise group every keyless row under the single empty key "" and could
# "reconcile" them purely on netted totals. To keep those views faithful to the matcher, each
# keyless row is given a stable, unique placeholder key derived from a per-side scope plus its row
# position, so keyless rows are never aggregated together. The prefix cannot collide with a real
# key (real keys are TRIM/LOWER'd values joined by KEY_DELIM) and contains no Excel wildcard chars.
_KEYLESS_PREFIX = "(no key \u00b7 "


def keyless_token(scope, position):
    return f"{_KEYLESS_PREFIX}{scope} #{position})"


def is_keyless_token(s):
    return isinstance(s, str) and s.startswith(_KEYLESS_PREFIX)


def similarity(a, b):
    return SequenceMatcher(None, str(a), str(b)).ratio()


# Difference-type labels that indicate a per-key row needs review even though the netted amounts
# might look clean. Defined once so the Python per-key model, the HTML dashboard and the Excel
# formulas all emit and count the identical string (the Dashboard "by type" pivot binds by COUNTIF
# on these labels).
DT_DUPLICATE = "Duplicate key (review)"
DT_MISSING_AMOUNT = "Missing amount (review)"


def within_tolerance(x, y, abs_tol, pct_tol):
    if x is None or y is None:
        return False
    diff = abs(x - y)
    if diff <= abs_tol:
        return True
    if pct_tol > 0 and max(abs(x), abs(y)) > 0:
        return (diff / max(abs(x), abs(y))) * 100.0 <= pct_tol
    return False


def effective_tolerances(matching):
    """Resolve the amount-match tolerances honoring matching.amountMatch. In 'exact' mode the
    amounts must agree exactly (to the cent for 2-dp currency data), so BOTH tolerances are 0
    regardless of any amountToleranceAbsolute/Percent left in the config; 'tolerance' mode (or an
    unset amountMatch) uses the configured absolute/percent values (default 0.01 / 0)."""
    if matching.get("amountMatch") == "exact":
        return 0.0, 0.0
    return matching.get("amountToleranceAbsolute", 0.01), matching.get("amountTolerancePercent", 0.0)


def _distinct_currencies(df, currency_col):
    """Distinct, normalized (upper/trim) non-blank currency codes present in a source column."""
    out = []
    seen = set()
    for v in df[currency_col].tolist():
        if _is_missing(v):
            continue
        s = str(v).strip().upper()
        if s and s not in seen:
            seen.add(s); out.append(s)
    return out


def check_currency(df_a, df_b, config):
    """Enforce the currency-safety guard (SKILL.md Step 2): reconciling across currencies is
    meaningless, so refuse it rather than netting incomparable amounts. Each source may name a
    `currencyColumn`; `normalization.expectedCurrency` may name the one currency the reconciliation
    is expected to be in. The guard raises ValueError when:
      - a source's currency column carries a code other than expectedCurrency, or
      - the two sources expose different currencies, or
      - a single source mixes multiple currencies.
    When neither source exposes a currency column the guard cannot run and is skipped (the caller
    is trusted to have confirmed single-currency inputs, per the SOP). Returns the resolved
    currency (or None) for reporting."""
    norm = config.get("normalization", {})
    expected = norm.get("expectedCurrency")
    expected_n = str(expected).strip().upper() if expected else None
    found = {}
    for side, df in (("a", df_a), ("b", df_b)):
        col = config["sources"][side].get("currencyColumn")
        if not col:
            continue
        if col not in df.columns:
            raise ValueError(f"Source '{config['sources'][side]['label']}' names currencyColumn "
                             f"'{col}' but it is not present. Available: {list(df.columns)}")
        curs = _distinct_currencies(df, col)
        found[side] = curs
        if len(curs) > 1:
            raise ValueError(f"Source '{config['sources'][side]['label']}' mixes multiple currencies "
                             f"{curs}. Reconcile one currency at a time, or supply a conversion rate.")
        if expected_n and curs and curs[0] != expected_n:
            raise ValueError(f"Source '{config['sources'][side]['label']}' is in {curs[0]}, not the "
                             f"expected {expected_n}. Never reconcile across currencies without an "
                             "explicit user-supplied rate.")
    codes = {c[0] for c in found.values() if c}
    if len(codes) > 1:
        raise ValueError(f"The two sources are in different currencies {sorted(codes)}. A "
                         "cross-currency difference is meaningless; supply a conversion rate first.")
    return (expected_n or (next(iter(codes)) if codes else None))


def align_key_columns(config):
    """If matching.keyMap pairs A's key columns to differently-named B columns, reorder
    sources.b.keyColumns to match sources.a.keyColumns element-wise, so every positional
    (a_keys[i] <-> b_keys[i]) assumption downstream (key building, timing, report field
    mapping) holds. No-op when keyMap is absent or does not cover every A key column."""
    m = config.get("matching", {})
    key_map = m.get("keyMap")
    if not key_map:
        return
    a_keys = config["sources"]["a"]["keyColumns"]
    mapping = {}
    for pair in key_map:
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            mapping[pair[0]] = pair[1]
    if a_keys and all(k in mapping for k in a_keys):
        config["sources"]["b"]["keyColumns"] = [mapping[k] for k in a_keys]


# ----------------------------- matching -----------------------------

def reconcile(df_a, df_b, config):
    src = config["sources"]
    m = config["matching"]
    norm = config.get("normalization", {})
    abs_tol, pct_tol = effective_tolerances(m)

    a_keys = src["a"]["keyColumns"]
    b_keys = src["b"]["keyColumns"]
    a_amt_col = src["a"]["amountColumn"]
    b_amt_col = src["b"]["amountColumn"]

    # Timing detection: identify the "period" component of the key, if configured.
    # timingKeyColumn names a column in source A's keyColumns; the same position in
    # b_keys is treated as B's period column (keyMap keeps the two aligned).
    timing_col = m.get("timingKeyColumn")
    enable_timing = m.get("enableTimingDetection", True) and timing_col is not None
    a_timing_idx = a_keys.index(timing_col) if (enable_timing and timing_col in a_keys) else None
    # Disable timing unless the period column is present in A's key AND the aligned B key has a
    # column at the same position (guards against an IndexError / wrong reduced key when B's
    # keyColumns are shorter or were not aligned to A via keyMap), AND there is at least one
    # non-timing key column - otherwise the reduced key collapses to "" and unrelated rows would
    # be paired as "timing" purely on amount.
    if enable_timing and (a_timing_idx is None or a_timing_idx >= len(b_keys) or len(a_keys) <= 1):
        enable_timing = False

    def reduced_key(row, keys, norm):
        # key with the timing component removed, so "same record, different period" collapses
        return join_key_parts([norm_key(row.get(c), norm) for i, c in enumerate(keys) if i != a_timing_idx])

    a = df_a.to_dict("records")
    b = df_b.to_dict("records")
    for i, r in enumerate(a):
        r["_idx"] = i
        r["_key"] = build_key(r, a_keys, norm)
        r["_amt"] = apply_sign(normalize_amount(r.get(a_amt_col), norm), src["a"].get("signConvention", "asIs"))
        if enable_timing:
            r["_rkey"] = reduced_key(r, a_keys, norm)
            r["_tval"] = norm_key(r.get(a_keys[a_timing_idx]), norm)
    for j, r in enumerate(b):
        r["_idx"] = j
        r["_key"] = build_key(r, b_keys, norm)
        r["_amt"] = apply_sign(normalize_amount(r.get(b_amt_col), norm), src["b"].get("signConvention", "asIs"))
        if enable_timing:
            r["_rkey"] = reduced_key(r, b_keys, norm)
            r["_tval"] = norm_key(r.get(b_keys[a_timing_idx]), norm)

    total_a = sum(r["_amt"] for r in a if r["_amt"] is not None)
    total_b = sum(r["_amt"] for r in b if r["_amt"] is not None)

    b_by_key = {}
    for r in b:
        b_by_key.setdefault(r["_key"], []).append(r)

    # Per-side multiplicity of each real (non-empty) key. When a key occurs more than once on either
    # side the one-to-one correspondence is ambiguous (which A row pairs with which B row?), so those
    # exact-key pairings are surfaced as "Probable (Needs Review)" rather than silently reported as
    # Matched on a nearest-amount guess (the per-key workbook/HTML flag the same keys - see the
    # "Duplicate key" difftype).
    a_key_counts, b_key_counts = {}, {}
    for r in a:
        if r["_key"] != "":
            a_key_counts[r["_key"]] = a_key_counts.get(r["_key"], 0) + 1
    for r in b:
        if r["_key"] != "":
            b_key_counts[r["_key"]] = b_key_counts.get(r["_key"], 0) + 1

    results = []
    used_b = set()

    # Tier 1 + 2: exact key
    for ra in a:
        candidates = [r for r in b_by_key.get(ra["_key"], []) if r["_idx"] not in used_b and ra["_key"] != ""]
        if not candidates:
            continue
        candidates.sort(key=lambda r: abs((r["_amt"] or 0) - (ra["_amt"] or 0)))
        rb = candidates[0]
        used_b.add(rb["_idx"])
        ra["_matched"] = True
        duplicate_key = a_key_counts.get(ra["_key"], 0) > 1 or b_key_counts.get(ra["_key"], 0) > 1
        # The signed difference is always the real A-less-B amount (a blank amount counts as 0 for
        # the tie-out identity). It is never forced to zero: a within-tolerance "Matched" pair can
        # still carry a small real variance under a configured tolerance, and dropping it would make
        # the global tie-out fail to close (tie_out sums these differences).
        diff = (ra["_amt"] or 0) - (rb["_amt"] or 0)
        if ra["_amt"] is None or rb["_amt"] is None:
            # Key matches on both sides but an amount is blank/unparseable. Do not silently
            # invent a clean variance; flag for review.
            status = "Probable (Needs Review)"
            evidence = "exact key; amount missing on one side - verify before treating as matched"
        elif duplicate_key:
            # Ambiguous 1:1 correspondence; the amounts may still net, but a human must confirm the
            # pairing. Keep the real difference so the tie-out identity still balances.
            status = "Probable (Needs Review)"
            evidence = "exact key; duplicate key on one or both sides - 1:1 pairing is ambiguous, verify"
        elif within_tolerance(ra["_amt"], rb["_amt"], abs_tol, pct_tol):
            status = "Matched"
            evidence = "exact key"
        else:
            status = "Matched (with difference)"
            evidence = "exact key"
        results.append({"status": status, "a_idx": ra["_idx"], "b_idx": rb["_idx"],
                        "key": ra["_key"], "amount_a": ra["_amt"], "amount_b": rb["_amt"],
                        "difference": diff, "evidence": evidence})

    unmatched_a = [r for r in a if not r.get("_matched")]
    unmatched_b = [r for r in b if r["_idx"] not in used_b]

    # Tier 3: similarity (candidate matching for records with no shared key). Requires BOTH date
    # columns to be configured: the method pairs on amount + date proximity + name similarity, so
    # without dates the two remaining signals (amount within tolerance + name) would fabricate
    # "Probable" pairs on common round amounts. When dates aren't configured the tier is skipped
    # (documented in references/methodology.md and SKILL.md).
    date_a = src["a"].get("dateColumn")
    date_b = src["b"].get("dateColumn")
    if m.get("enableSimilarityMatching", True) and date_a and date_b:
        window = m.get("dateWindowDays", 3)
        sim_thr = m.get("similarityThreshold", 0.9)
        still_a = []
        for ra in unmatched_a:
            # Never pair on an empty key/description - SequenceMatcher on two empty strings
            # returns 1.0 and would fabricate a "Probable" match from amount/date alone.
            if not str(ra["_key"]).strip():
                still_a.append(ra)
                continue
            best = None
            for rb in unmatched_b:
                if rb["_idx"] in used_b or not str(rb["_key"]).strip():
                    continue
                if not within_tolerance(ra["_amt"], rb["_amt"], abs_tol, pct_tol):
                    continue
                da, db = ra.get(date_a), rb.get(date_b)
                try:
                    delta_days = abs((pd.to_datetime(da) - pd.to_datetime(db)).total_seconds()) / 86400.0
                except Exception:
                    # A date could not be parsed: the proximity rule cannot be satisfied, so this
                    # pair is not eligible for similarity.
                    continue
                if delta_days > window:
                    continue
                sim = similarity(ra["_key"], rb["_key"])
                if sim >= sim_thr and (best is None or sim > best[1]):
                    best = (rb, sim)
            if best:
                rb, sim = best
                used_b.add(rb["_idx"])
                results.append({"status": "Probable (Needs Review)", "a_idx": ra["_idx"], "b_idx": rb["_idx"],
                                "key": ra["_key"], "amount_a": ra["_amt"], "amount_b": rb["_amt"],
                                "difference": (ra["_amt"] or 0) - (rb["_amt"] or 0),
                                "evidence": f"similarity: amount+date, name similarity {sim:.2f}"})
            else:
                still_a.append(ra)
        unmatched_a = still_a
        unmatched_b = [r for r in unmatched_b if r["_idx"] not in used_b]

    # Tier 4: grouped (split / partial) matches. One record on one side equals the sum of
    # several on the other within tolerance (e.g. one invoice settled by three payments).
    # Bounded for safety: enumeration is skipped when the opposite pool is too large, and
    # combinations are capped at groupedMaxMembers. Grouped pairs go to Needs Review with
    # every member listed - a split is legitimate but a human should confirm it.
    if m.get("enableGrouped", True):
        from itertools import combinations
        max_members = max(2, int(m.get("groupedMaxMembers", 6)))
        POOL_CAP = 30  # skip enumeration if the many-side pool exceeds this (keeps it fast)
        grouped_a, grouped_b = set(), set()

        def _find_combo(target, pool, exclude):
            # Keyless rows (empty key) are non-matchable by design, so they never participate as
            # combo members either (mirrors the exact/similarity tiers).
            avail = [r for r in pool if r["_idx"] not in exclude and r["_amt"] is not None and r["_key"] != ""]
            if len(avail) > POOL_CAP:
                return None
            # A split is same-sign as its target, so drop opposite-sign candidates and any
            # single item already larger (by magnitude) than the target - this prunes the
            # search space sharply before enumerating combinations.
            if target >= 0:
                avail = [r for r in avail if 0 <= r["_amt"] <= target + abs_tol]
            else:
                avail = [r for r in avail if target - abs_tol <= r["_amt"] <= 0]
            # Search smaller (nearest-magnitude-first) combinations first, with an attempt cap
            # so a pathological pool can't blow up the run.
            avail.sort(key=lambda r: abs(r["_amt"]), reverse=True)
            attempts = 0
            ATTEMPT_CAP = 50000
            for size in range(2, max_members + 1):
                for combo in combinations(avail, size):
                    attempts += 1
                    if attempts > ATTEMPT_CAP:
                        return None
                    s = sum(c["_amt"] for c in combo)
                    if within_tolerance(target, s, abs_tol, pct_tol):
                        return combo
            return None

        # One A record ↔ many B records.
        for ra in unmatched_a:
            if ra["_amt"] is None or ra["_key"] == "":
                continue
            combo = _find_combo(ra["_amt"], unmatched_b, used_b | grouped_b)
            if combo:
                grouped_a.add(ra["_idx"])
                for c in combo:
                    grouped_b.add(c["_idx"]); used_b.add(c["_idx"])
                s = sum(c["_amt"] for c in combo)
                members = ", ".join(str(c["_key"]) for c in combo)
                results.append({"status": "Grouped (Needs Review)", "a_idx": ra["_idx"], "b_idx": None,
                                "key": ra["_key"], "amount_a": ra["_amt"], "amount_b": s,
                                "difference": (ra["_amt"] or 0) - s,
                                "evidence": f"grouped: {len(combo)} {src['b'].get('label','B')} rows ({members}) sum to {s:,.2f}"})

        # One B record ↔ many A records (using A rows not already grouped above).
        pool_a = [r for r in unmatched_a if r["_idx"] not in grouped_a]
        for rb in unmatched_b:
            if rb["_idx"] in grouped_b or rb["_amt"] is None or rb["_key"] == "":
                continue
            combo = _find_combo(rb["_amt"], pool_a, grouped_a)
            if combo:
                grouped_b.add(rb["_idx"])
                for c in combo:
                    grouped_a.add(c["_idx"])
                s = sum(c["_amt"] for c in combo)
                members = ", ".join(str(c["_key"]) for c in combo)
                results.append({"status": "Grouped (Needs Review)", "a_idx": None, "b_idx": rb["_idx"],
                                "key": rb["_key"], "amount_a": s, "amount_b": rb["_amt"],
                                "difference": s - (rb["_amt"] or 0),
                                "evidence": f"grouped: {len(combo)} {src['a'].get('label','A')} rows ({members}) sum to {s:,.2f}"})

        unmatched_a = [r for r in unmatched_a if r["_idx"] not in grouped_a]
        unmatched_b = [r for r in unmatched_b if r["_idx"] not in grouped_b]

    # Tier 4b: timing differences. Among the still-unmatched records, detect the classic
    # "same item posted to a different period" case: an A record and a B record sharing the
    # reduced key (identity minus the period) and the same amount, but a different period.
    # We ANNOTATE both lines (so they remain visible as one-sided breaks and count toward the
    # variance the way an accountant expects) rather than collapsing them - the note preserves
    # the timing insight for the reviewer.
    if enable_timing:
        b_pool = {}
        for rb in unmatched_b:
            if not rb.get("_rkey"):
                continue  # all non-period components blank: no identity to match a timing pair on
            b_pool.setdefault(rb["_rkey"], []).append(rb)
        b_noted = set()
        for ra in unmatched_a:
            if not ra.get("_rkey"):
                continue
            for rb in b_pool.get(ra["_rkey"], []):
                if rb["_idx"] in b_noted or rb["_tval"] == ra["_tval"]:
                    continue
                if within_tolerance(ra["_amt"], rb["_amt"], abs_tol, pct_tol):
                    ra["_timing_note"] = f"Possible timing difference - same amount in {rb['_tval']}"
                    rb["_timing_note"] = f"Possible timing difference - same amount in {ra['_tval']}"
                    b_noted.add(rb["_idx"])
                    break

    # Tier 5: whatever remains as genuine one-sided breaks.
    for ra in unmatched_a:
        results.append({"status": "Unmatched (A)", "a_idx": ra["_idx"], "b_idx": None,
                        "key": ra["_key"], "amount_a": ra["_amt"], "amount_b": None,
                        "difference": None, "evidence": ra.get("_timing_note", "")})
    for rb in unmatched_b:
        results.append({"status": "Unmatched (B)", "a_idx": None, "b_idx": rb["_idx"],
                        "key": rb["_key"], "amount_a": None, "amount_b": rb["_amt"],
                        "difference": None, "evidence": rb.get("_timing_note", "")})

    return results, total_a, total_b


def tie_out(results, total_a, total_b, abs_tol):
    # The identity: (total A - total B) must equal the sum of every line's net contribution.
    # For a matched (including within-tolerance), matched-with-difference, probable, or grouped
    # pairing that is the recorded difference (A less B, with a blank amount counting as 0); for a
    # one-sided item it is the present amount. "Matched" is included because a within-tolerance pair
    # can carry a small real variance that still has to be explained for the identity to close - it
    # is exactly 0 for an exact-mode match, so this never changes exact-mode results.
    explained = 0.0
    for r in results:
        st = r["status"]
        d = r.get("difference")
        if st in ("Matched", "Matched (with difference)", "Probable (Needs Review)",
                  "Grouped (Needs Review)") and d is not None:
            explained += d
        elif st == "Unmatched (A)" and r.get("amount_a") is not None:
            explained += r["amount_a"]
        elif st == "Unmatched (B)" and r.get("amount_b") is not None:
            explained -= r["amount_b"]
    left = total_a - total_b
    residual = left - explained
    # Amounts are quantized to cents, so evaluate the identity at cent precision: rounding the
    # residual to 2dp removes binary floating-point accumulation noise without masking a genuine
    # one-cent break (which the old "floor the threshold at 0.01" logic incorrectly accepted in
    # exact mode). A configured absolute tolerance is still honored; in exact mode (abs_tol 0) only
    # an exact cent-level match ties out.
    closed = abs(round(residual, 2)) <= abs_tol
    return {"total_a": total_a, "total_b": total_b, "net_difference": left,
            "explained": explained, "residual": residual, "tied_out": closed}


# ----------------------------- output -----------------------------

# Report palette (formula-driven workbook): blue headers, accounting number format.
HDR_FILL = "2E5C8A"         # blue - table header fills (white text)
HDR_FONT = "FFFFFF"         # white header text
SEC_C = "2E5C8A"            # blue - section labels / title text
SUB_C = "595959"            # gray - subtitles / basis-of-preparation line
BODY_C = "404040"           # near-black body text
NARR_C = "3B3B3B"           # headlines narrative text
MK_C = "808080"             # gray - matching-key helper column
REPORT_FONT = "Cambria"     # v15 uses Cambria throughout
# Consistent number format used for every amount throughout the workbook:
# 2 decimals, negatives in parentheses (e.g. 1,234.00 / (1,234.00) / 0.00). No currency symbol.
ACCT2 = '#,##0.00;(#,##0.00)'
CNT_FMT = '#,##0'
PCT_FMT = '0.0%'
ZEBRA_BG = "F2F7FC"         # very light blue - alternating rows
OPEN_FONT, OPEN_BG = "8C1D18", "F7E3E1"   # Open Item - red text on soft red
REC_FONT, REC_BG = "1F3864", "EAF1F8"     # Reconciled - navy text on soft blue
def _build_narrative_perkey(rows, config):
    """Headline narrative computed from the per-key reconciliation rows - the same model the
    Reconciliation sheet and the HTML dashboard use - so the headline counts can never disagree
    with the sheet totals. Returns plain-text lines (no currency symbols); shared verbatim by the
    Excel Dashboard and the HTML dashboard."""
    la = config["sources"]["a"].get("label", "Source A")
    lb = config["sources"]["b"].get("label", "Source B")
    out = config.get("output", {})
    group_by = out.get("groupBy", [])
    gb0 = group_by[0] if group_by else "company"
    gb1 = group_by[1] if len(group_by) > 1 else "period"

    total = len(rows)
    reconciled = sum(1 for r in rows if r["status"] == "Reconciled")
    open_rows = [r for r in rows if r["status"] == "Open Item"]
    opn = len(open_rows)
    net = round(sum(r["diff"] for r in rows), 2)
    gross = round(sum(abs(r["diff"]) for r in rows), 2)
    rate = (reconciled / total * 100) if total else 0

    # Per-account rollup (for the biggest driver) and root-cause tallies over open items.
    acct = {}
    acct_order = []
    for r in rows:
        a = r["account"]
        if a not in acct:
            acct[a] = {"name": r["name"], "a": 0.0, "b": 0.0}
            acct_order.append(a)
        acct[a]["a"] += r["amt_a"]
        acct[a]["b"] += r["amt_b"]

    def rc(name):
        c = sum(1 for r in open_rows if r["rootcause"] == name)
        v = round(sum(abs(r["diff"]) for r in open_rows if r["rootcause"] == name), 2)
        return c, v

    m_c, m_v = rc("Measurement")
    t_c, t_v = rc("Timing")
    s_c, s_v = rc("Scope / mapping")
    timing_net = round(sum(r["diff"] for r in open_rows if r["rootcause"] == "Timing"), 2)

    lines = [
        f"{total} keys reconciled across the {gb0.lower()} and {gb1.lower()} dimensions: "
        f"{reconciled} reconciled and {opn} open, a {rate:.1f}% match rate.",
        f"Net difference is {_num(net)} ({la} less {lb}); ignoring sign the differences total {_num(gross)}.",
    ]
    if acct_order:
        biggest = max(acct_order, key=lambda a: abs(acct[a]["a"] - acct[a]["b"]))
        big_diff = acct[biggest]["a"] - acct[biggest]["b"]
        lines.append(f"Largest account driver: {acct[biggest]['name']} at {_num(big_diff)}.")
    lines.append(
        f"Root causes: {m_c} measurement ({_num(m_v)}), {t_c} timing ({_num(t_v)}) "
        f"and {s_c} scope or mapping ({_num(s_v)}).")
    if t_c and timing_net == 0:
        lines.append("Timing items net to 0.00 across the periods and should clear without adjustment.")
    return lines


def _CL(n):
    from openpyxl.utils import get_column_letter
    return get_column_letter(n)


def _src_meta(df, src_cfg, config):
    """Column geometry for a source tab: header names, key/amount letters, the appended
    Matching Key helper column, and the A1-style ranges used by the reconciliation formulas."""
    cols = list(df.columns)
    n = len(df)
    amt = src_cfg["amountColumn"]
    keys = src_cfg["keyColumns"]
    amt_letter = _CL(cols.index(amt) + 1)
    key_letters = [_CL(cols.index(k) + 1) for k in keys]
    mk_letter = _CL(len(cols) + 1)          # Matching Key helper appended after the data
    # Data occupies rows 2..(n+1). Clamp to a minimum of 2 so that, when a source has no data
    # rows, the helper/amount ranges are the single (blank) cell $2:$2 rather than the inverted
    # $2:$1 - which Excel would mis-handle in SUM/COUNTIF and in the reconciliation formulas.
    last = max(n + 1, 2)
    return {
        "cols": cols, "n": n, "amt_letter": amt_letter, "key_letters": key_letters,
        "mk_letter": mk_letter, "last": last, "keys": keys,
    }


def _neutralize(v):
    """Defuse spreadsheet formula/injection: a text value whose first non-whitespace character is
    = + - @ could be executed as a formula when the workbook is opened. Since all source data is
    untrusted, force such strings to literal text with a leading apostrophe. The check ignores
    leading whitespace (Excel does too: `  =1+1` still evaluates), while the original value is
    preserved after the apostrophe. Numbers are unaffected."""
    if isinstance(v, str) and v.lstrip()[:1] in ("=", "+", "-", "@"):
        return "'" + v
    return v


def _xl_sheet_ref(sheet, a1):
    """A sheet-qualified reference (e.g. 'Sheet Name'!$A$1) with the sheet name safely quoted -
    embedded apostrophes are doubled, so a label/path-derived sheet name like "O'Brien" produces a
    valid formula instead of a broken one. Used everywhere a source-tab range/cell is referenced."""
    return "'" + str(sheet).replace("'", "''") + "'!" + a1


def _xl_str_literal(s):
    """An Excel string literal ("...") with any embedded double-quote doubled, so a user-derived
    label can neither break the formula nor be used to inject by escaping the string."""
    return '"' + str(s).replace('"', '""') + '"'


def _xl_within_tolerance(diff_ref, a_ref, b_ref, abs_tol, pct_tol):
    """Excel boolean expression mirroring within_tolerance(): the amounts agree when the absolute
    difference is within abs_tol OR (when a percentage tolerance is set) within pct_tol of the
    larger magnitude. The absolute test rounds to the cent first so binary SUM noise never masks or
    invents a break. In exact mode (abs_tol=pct_tol=0) this reduces to ABS(ROUND(diff,2))<=0, i.e.
    exact cent equality - identical to the old ROUND(diff,2)=0 test, so exact-mode output is
    unchanged while configured tolerances are now honored (matching the Python matcher/HTML)."""
    absok = f"ABS(ROUND({diff_ref},2))<={abs_tol}"
    if pct_tol and pct_tol > 0:
        denom = f"MAX(ABS({a_ref}),ABS({b_ref}))"
        return f"OR({absok},AND({denom}>0,ABS({diff_ref})/{denom}*100<={pct_tol}))"
    return absok


def _xl_key_formula(cell_refs, norm):
    """Excel formula that concatenates key cell references into a Matching Key, mirroring
    join_key_parts()/norm_key(): each component is wrapped in TRIM() when trimWhitespace is on and
    LOWER() when caseInsensitiveKeys is on, the components are joined by the shared KEY_DELIM, and
    an all-empty key collapses to "" (via an IF over the delimiter-free concatenation) exactly as
    the Python builder does. The source-tab helper and the Reconciliation sheet both call this with
    identical settings so their SUMIF/COUNTIF keys line up. LOWER/TRIM also coerce numbers to text
    the same way (integer-valued cells render without a trailing .0)."""
    trim = norm.get("trimWhitespace", True)
    lower = norm.get("caseInsensitiveKeys", True)

    def wrap(ref):
        expr = ref
        if trim:
            expr = f"TRIM({expr})"
        if lower:
            expr = f"LOWER({expr})"
        # Escape each component identically to _escape_key_component (same order: "^" first), so the
        # Excel Matching Key is injective across the delimiter and carries no raw wildcard character.
        for raw, rep in _KEY_ESCAPES:
            expr = f'SUBSTITUTE({expr},"{raw}","{rep}")'
        return expr

    parts = [wrap(r) for r in cell_refs]
    if not parts:
        return '=""'
    bare = "&".join(parts)                       # components with no delimiter, for the empty test
    joined = ('&"' + KEY_DELIM + '"&').join(parts)
    return f'=IF({bare}="","",{joined})'


def _safe_sheet_name(name, taken):
    """A valid, unique Excel sheet name: strip the reserved characters : \\ / ? * [ ] (plus ~,
    which is a wildcard-escape in SUMIF/COUNTIF criteria and would break a keyless row's literal
    Matching Key that embeds the sheet name), cap at 31 chars, and de-duplicate with a numeric
    suffix (truncating to keep room for it)."""
    import re
    n = re.sub(r"[:\\/?*\[\]~]", " ", str(name)).strip() or "Sheet"
    n = n[:31]
    base, i = n, 2
    while n.lower() in taken:
        suffix = f" ({i})"
        n = base[:31 - len(suffix)].rstrip() + suffix
        i += 1
    taken.add(n.lower())
    return n


def _write_source_tab(ws, df, meta, sheet_title, sign="asIs", norm=None):
    """Write a source ledger plus a Matching Key helper column, styled with a blue header. The
    amount column is written sign-normalized (so signConvention flows through the workbook's
    SUMIF totals); text cells are neutralized against formula injection; the helper column joins
    the key cells so the reconciliation SUMIF/COUNTIFs bind."""
    from openpyxl.styles import Font, PatternFill, Alignment

    norm = norm or {}
    # Shared font objects assigned by reference (openpyxl de-duplicates styles), so every cell is
    # styled as it is created - no second whole-sheet pass over this potentially huge tab.
    f_body = Font(name=REPORT_FONT)
    f_text = Font(name="Arial", size=10)
    f_hdr = Font(name=REPORT_FONT, bold=True, color=HDR_FONT)
    f_mk = Font(name=REPORT_FONT, color=MK_C)
    # Shared alignments too (re-creating an Alignment per cell is a measurable cost at scale and
    # bloats openpyxl's style table).
    a_left = Alignment(horizontal="left")
    a_ctr_v = Alignment(horizontal="center", vertical="center")
    hdr_fill = PatternFill("solid", fgColor=HDR_FILL)
    cols = meta["cols"]
    # Header row. Column names are user-derived, so neutralize against formula injection.
    for c, name in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=c, value=_neutralize(str(name)))
        cell.fill = hdr_fill
        cell.font = f_hdr
        cell.alignment = a_ctr_v
    mk_c = len(cols) + 1
    hc = ws.cell(row=1, column=mk_c, value="Matching Key")
    hc.fill = hdr_fill
    hc.font = f_hdr
    hc.alignment = a_ctr_v

    # Data rows. v15 convention: numeric non-amount cells use Cambria left-aligned (General
    # format renders integer keys cleanly); free-text cells (e.g. Account Name, Period) use
    # Arial 10; the amount uses the shared money format. The Matching Key helper is a gray formula.
    amt_letter = meta["amt_letter"]
    text_cols = {name for name in cols if not pd.api.types.is_numeric_dtype(df[name])}
    # Iterate plain dicts (one to_dict up front) rather than df.iterrows(), which allocates a fresh
    # pandas Series per row - a meaningful cost when writing tens of thousands of rows.
    for r, row in enumerate(df.to_dict("records"), start=2):
        for c, name in enumerate(cols, start=1):
            v = row[name]
            if pd.isna(v):
                v = None
            if _CL(c) == amt_letter:
                # Sign-normalized numeric value drives the workbook's SUMIF totals.
                cell = ws.cell(row=r, column=c, value=apply_sign(normalize_amount(v, norm), sign))
                cell.number_format = ACCT2
                cell.font = f_body
            elif name in text_cols:
                cell = ws.cell(row=r, column=c, value=_neutralize(v))
                cell.font = f_text
            else:
                cell = ws.cell(row=r, column=c, value=v)
                cell.alignment = a_left
                cell.font = f_body
        # Matching Key. A row with all key components blank gets a unique placeholder so keyless
        # rows are never aggregated together by the reconciliation SUMIF/COUNTIF; otherwise the
        # normalized concatenation of the key cells (TRIM/LOWER, all-empty collapses to "").
        if not any(norm_key(row[k], norm) for k in meta["keys"]):
            mkc = ws.cell(row=r, column=mk_c, value=keyless_token(sheet_title, r))
        else:
            refs = [f"${kl}{r}" for kl in meta["key_letters"]]
            mkc = ws.cell(row=r, column=mk_c, value=_xl_key_formula(refs, norm))
        mkc.font = f_mk

    # Column widths: vectorized string-length over a bounded sample (avoids an O(rows*cols)
    # Python loop; the widest of the first 200 rows is a fine proxy for display width).
    sample = df.head(200)
    for c, name in enumerate(cols, start=1):
        try:
            body_max = int(sample[name].astype(str).str.len().max() or 0)
        except Exception:
            body_max = 0
        width = min(max(max(len(str(name)), body_max) + 2, 10), 40)
        ws.column_dimensions[_CL(c)].width = width
    ws.column_dimensions[_CL(mk_c)].width = 26
    ws.freeze_panes = "A2"


def _col_to_idx(letter):
    from openpyxl.utils import column_index_from_string
    return column_index_from_string(letter) - 1


def _write_reconciliation(ws, df_a, df_b, config, meta_a, meta_b, sa, sb):
    """The formula-driven reconciliation: one row per union key, every number a live formula
    over the two source tabs. Returns the layout info the dashboard needs to reference it."""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.formatting.rule import FormulaRule, CellIsRule

    # Shared fonts assigned by reference, so every cell on this (potentially large) sheet is styled
    # as it is created - no second whole-sheet styling pass.
    f_body = Font(name=REPORT_FONT)
    f_text = Font(name="Arial", size=10)
    f_hdr = Font(name=REPORT_FONT, bold=True, color=HDR_FONT)
    f_mk = Font(name=REPORT_FONT, color=MK_C)
    f_key = Font(name=REPORT_FONT, color=BODY_C)
    f_bold = Font(name=REPORT_FONT, bold=True)
    # Shared alignments (avoid re-creating one per cell across a large sheet).
    a_left = Alignment(horizontal="left")
    a_center = Alignment(horizontal="center")

    la = config["sources"]["a"]["label"]
    lb = config["sources"]["b"]["label"]
    a_keys = config["sources"]["a"]["keyColumns"]
    b_keys = config["sources"]["b"]["keyColumns"]
    out = config.get("output", {})
    renames = out.get("columnRenames", {})
    norm = config.get("normalization", {})
    amt_a = config["sources"]["a"]["amountColumn"]
    timing_col = config["matching"].get("timingKeyColumn")

    # Descriptive columns = every source-A column except the amount column.
    desc_cols = [c for c in meta_a["cols"] if c != amt_a]
    D = len(desc_cols)
    # Recon column letters.
    desc_letter = {name: _CL(2 + i) for i, name in enumerate(desc_cols)}
    L_amt_a = _CL(2 + D)
    L_amt_b = _CL(3 + D)
    L_diff = _CL(4 + D)
    L_lines_a = _CL(5 + D)
    L_lines_b = _CL(6 + D)
    L_status = _CL(7 + D)
    L_dtype = _CL(8 + D)
    L_root = _CL(9 + D)
    L_action = _CL(10 + D)
    ncols = 10 + D

    # Union of keys: one row per UNIQUE key - the first-seen source-A row for each A key (in
    # order), then the first-seen source-B row for each B key not already present in A. This
    # mirrors compute_reconciliation()'s union exactly, so the SUMIF/COUNTIF-per-key sheet agrees
    # with the HTML dashboard and a key duplicated within a source is never double-counted. Uses
    # norm_key per component so the union matches the Python matcher and the Excel TRIM/LOWER
    # helper (integer-valued cells canonicalize identically).
    # Precompute each source as a list of plain dicts ONCE, so per-row lookups below are O(1) dict
    # access instead of df.iloc[i] (which allocates a fresh pandas Series on every access - an
    # O(rows x keys) cost on large reconciliations).
    a_recs = df_a.to_dict("records")
    b_recs = df_b.to_dict("records")

    def keystr(recs, keys, i, scope):
        k = join_key_parts([norm_key(recs[i].get(c), norm) for c in keys])
        return k if k else keyless_token(scope, i + 2)
    a_keyset = set()
    recon_rows = []
    row_keys = []
    for i in range(meta_a["n"]):
        k = keystr(a_recs, a_keys, i, sa)
        if k not in a_keyset:
            a_keyset.add(k)
            recon_rows.append(("a", i + 2)); row_keys.append(k)
    b_keyset = set()
    for j in range(meta_b["n"]):
        k = keystr(b_recs, b_keys, j, sb)
        if k not in a_keyset and k not in b_keyset:
            b_keyset.add(k)
            recon_rows.append(("b", j + 2)); row_keys.append(k)
    n_lines = len(recon_rows)
    r_first = 5
    # Clamp so an empty union (both sources have no data rows) yields the single row $5:$5 instead
    # of the inverted $5:$4, which would break every range-based formula and the conditional
    # formatting. Row 5 is then left blank and every SUM/COUNT over it evaluates to 0.
    r_last = max(r_first + n_lines - 1, r_first)
    r_total = r_last + 1
    r_ctrl = r_total + 1

    # Titles.
    t = ws.cell(row=1, column=1, value=f"Reconciliation detail — {la} vs {lb}")
    t.font = Font(name=REPORT_FONT, bold=True, size=16, color=SEC_C)
    st = ws.cell(row=2, column=1,
                 value=f"One row per matching key. Difference = {la} less {lb}. "
                       "Basis of preparation is on the Dashboard.")
    st.font = Font(name=REPORT_FONT, color=SUB_C)

    # Header row (row 4).
    headers = (["Matching Key"] + [renames.get(c, c) for c in desc_cols] +
               [f"Amount — {la}", f"Amount — {lb}", "Difference",
                f"Lines in {la}", f"Lines in {lb}", "Status",
                "Difference Type", "Root Cause", "Action Needed"])
    hdr_fill = PatternFill("solid", fgColor=HDR_FILL)
    thin = Side(style="thin", color=HDR_FILL)
    hborder = Border(left=thin, right=thin, top=thin, bottom=thin)
    for c, name in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=c, value=_neutralize(name))
        cell.fill = hdr_fill
        cell.font = f_hdr
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = hborder

    # Which recon letters correspond to the key columns (for the Matching Key join) and to
    # the non-timing key columns (for the timing COUNTIFS in Root Cause).
    key_recon_letters = [desc_letter[k] for k in a_keys if k in desc_letter]
    nontiming_keys = [k for k in a_keys if k != timing_col and k in desc_letter]
    # Timing root cause only makes sense when timing detection is enabled AND at least one
    # non-timing key column exists to group offsetting entries by; otherwise every one-sided break
    # would be grouped together and mislabelled "Timing" (mirrors the reconcile()/HTML guard).
    timing_on = (config["matching"].get("enableTimingDetection", True)
                 and timing_col is not None and len(nontiming_keys) >= 1)
    # Hidden helper column holding the NORMALIZED reduced key (the non-timing key components,
    # TRIM/LOWER'd exactly like the Matching Key). The Root Cause timing COUNTIFS groups offsetting
    # entries by this normalized identity - matching the Python matcher and the HTML - instead of
    # the raw display columns, which ignore trimWhitespace / caseInsensitiveKeys.
    L_rk = _CL(ncols + 1)
    nontiming_recon_letters = [desc_letter[k] for k in nontiming_keys]
    if timing_on:
        hc = ws.cell(row=4, column=ncols + 1, value="Reduced Key (helper)")
        hc.fill = hdr_fill
        hc.font = f_hdr
        ws.column_dimensions[L_rk].hidden = True

    mk_a = _xl_sheet_ref(sa, f"${meta_a['mk_letter']}$2:${meta_a['mk_letter']}${meta_a['last']}")
    amt_a_rng = _xl_sheet_ref(sa, f"${meta_a['amt_letter']}$2:${meta_a['amt_letter']}${meta_a['last']}")
    mk_b = _xl_sheet_ref(sb, f"${meta_b['mk_letter']}$2:${meta_b['mk_letter']}${meta_b['last']}")
    amt_b_rng = _xl_sheet_ref(sb, f"${meta_b['amt_letter']}$2:${meta_b['amt_letter']}${meta_b['last']}")

    b_cols = list(df_b.columns)
    keymap = dict(zip(a_keys, b_keys))
    text_desc = {name for name in desc_cols if not pd.api.types.is_numeric_dtype(df_a[name])}
    # Excel string literals for the source labels, embedded in the Difference Type / Root Cause
    # formulas. Built once with any double-quote in the label doubled so a label like `AB"C` can't
    # break the formula string (or inject). The runtime value Excel produces is the plain
    # "Missing in <label>", which matches the same plain string written as the Dashboard pivot
    # labels, so the COUNTIF/COUNTIFS still bind.
    miss_a = _xl_str_literal(f"Missing in {la}")
    miss_b = _xl_str_literal(f"Missing in {lb}")
    # Effective tolerances (0/0 in exact mode) and the review-difftype literals, so the Difference
    # Type / Root Cause formulas honor the configured tolerance and flag duplicate keys and missing
    # amounts with the SAME labels the Python per-key model and HTML emit.
    abs_tol, pct_tol = effective_tolerances(config["matching"])
    dup_lit = _xl_str_literal(DT_DUPLICATE)
    miss_amt_lit = _xl_str_literal(DT_MISSING_AMOUNT)
    # Precompute constant column geometry ONCE (letters/indices don't change per row), so the hot
    # loop below is O(1) dict lookups instead of repeated list.index() scans (which made it
    # O(rows * cols^2) on wide/large reconciliations).
    desc_col_idx = {name: 2 + i for i, name in enumerate(desc_cols)}
    a_src_letter = {name: _CL(meta_a["cols"].index(name) + 1) for name in desc_cols}
    b_src_letter = {bname: _CL(i + 1) for i, bname in enumerate(b_cols)}

    for idx, (side, srow) in enumerate(recon_rows):
        r = r_first + idx
        # Matching Key. Keyless rows carry a unique placeholder (written literally, matching the
        # source-tab helper) so they are never aggregated together; keyed rows rebuild the key by
        # formula, normalized identically to the source-tab helper so SUMIF/COUNTIF align.
        if is_keyless_token(row_keys[idx]):
            ws.cell(row=r, column=1, value=row_keys[idx]).font = f_key
        else:
            refs = [f"${kl}{r}" for kl in key_recon_letters]
            ws.cell(row=r, column=1, value=_xl_key_formula(refs, norm)).font = f_key
        # Timing root cause applies to this row only when timing is on AND its non-timing (reduced)
        # key is genuinely non-blank; keyless / blank-reduced rows are excluded so they are never
        # grouped and mislabelled "Timing" (mirrors reconcile() and the HTML per-key model).
        if timing_on:
            if side == "a":
                reduced = [norm_key(a_recs[srow - 2].get(k), norm) for k in nontiming_keys]
            else:
                reduced = [norm_key(b_recs[srow - 2].get(keymap.get(k, k)), norm) for k in nontiming_keys]
            row_timing = any(reduced)
        else:
            row_timing = False
        # Descriptive columns pulled from the source row by reference. Numeric key columns are
        # left-aligned Cambria; free-text columns (Account Name, Period) use Arial 10 (v15 style).
        for name in desc_cols:
            col_idx = desc_col_idx[name]
            if side == "a":
                ref = "=" + _xl_sheet_ref(sa, f"${a_src_letter[name]}{srow}")
            else:
                bname = keymap.get(name, name)
                bl = b_src_letter.get(bname)
                ref = "=" + _xl_sheet_ref(sb, f"${bl}{srow}") if bl is not None else None
            if ref is not None:
                cell = ws.cell(row=r, column=col_idx, value=ref)
                if name in text_desc:
                    cell.font = f_text
                else:
                    cell.font = f_body
                    cell.alignment = a_left
        # Amounts, difference, line counts.
        c_aa = ws.cell(row=r, column=2 + D, value=f"=SUMIF({mk_a},$A{r},{amt_a_rng})")
        c_aa.number_format = ACCT2; c_aa.font = f_body
        c_bb = ws.cell(row=r, column=3 + D, value=f"=SUMIF({mk_b},$A{r},{amt_b_rng})")
        c_bb.number_format = ACCT2; c_bb.font = f_body
        c_df = ws.cell(row=r, column=4 + D, value=f"={L_amt_a}{r}-{L_amt_b}{r}")
        c_df.number_format = ACCT2; c_df.font = f_body
        ca = ws.cell(row=r, column=5 + D, value=f"=COUNTIF({mk_a},$A{r})")
        cb = ws.cell(row=r, column=6 + D, value=f"=COUNTIF({mk_b},$A{r})")
        ca.alignment = cb.alignment = a_center
        ca.font = cb.font = f_body
        # Status / Difference Type / Root Cause / Action Needed (left-aligned text, v15 style).
        c_st = ws.cell(row=r, column=7 + D, value=f'=IF({L_dtype}{r}="None","Reconciled","Open Item")')
        c_st.alignment = a_left; c_st.font = f_body
        # Difference Type, in priority order: one-sided (missing in a source) -> a present key with a
        # blank/unparseable amount (review) -> a duplicate key on either side (ambiguous 1:1, review)
        # -> amounts agree within the configured tolerance ("None") -> otherwise "Amount mismatch".
        # The missing-amount test counts blank amount cells for this key (COUNTIFS ...,""); the
        # tolerance test honors amountMatch/tolerances instead of raw equality. These mirror the
        # Python per-key model so the workbook and HTML never disagree.
        missing_a = f'COUNTIFS({mk_a},$A{r},{amt_a_rng},"")'
        missing_b = f'COUNTIFS({mk_b},$A{r},{amt_b_rng},"")'
        within = _xl_within_tolerance(f"{L_diff}{r}", f"{L_amt_a}{r}", f"{L_amt_b}{r}", abs_tol, pct_tol)
        c_dt = ws.cell(row=r, column=8 + D,
                       value=(f'=IF({L_lines_a}{r}=0,{miss_a},'
                              f'IF({L_lines_b}{r}=0,{miss_b},'
                              f'IF(OR({missing_a}>0,{missing_b}>0),{miss_amt_lit},'
                              f'IF(OR({L_lines_a}{r}>1,{L_lines_b}{r}>1),{dup_lit},'
                              f'IF({within},"None","Amount mismatch")))))'))
        c_dt.alignment = a_left; c_dt.font = f_body
        # Root Cause: measurement (amount mismatch); duplicate/missing-amount rows are scope/mapping
        # (a review item, never timing); timing only when this row has an OFFSETTING one-sided break
        # of the opposite side sharing the reduced key AND an equal-magnitude amount (the SUMPRODUCT
        # amount test - diff+diff nets to ~0 - prevents two same-account rows with different balances
        # from being mislabelled "Timing"); otherwise scope / mapping.
        if timing_on:
            rk_refs = [f"${kl}{r}" for kl in nontiming_recon_letters]
            ws.cell(row=r, column=ncols + 1, value=_xl_key_formula(rk_refs, norm)).font = f_mk
        if row_timing:
            opp = f'IF({L_dtype}{r}={miss_b},{miss_a},{miss_b})'
            # Offsetting amount test, mirroring within_tolerance(this_amt, other_amt, abs_tol,
            # pct_tol). For a one-sided break the row's Difference equals its present amount, so the
            # two offsetting breaks agree when |other_diff + this_diff| is within abs_tol OR (when a
            # percentage tolerance is set) within pct_tol% of the larger magnitude. Dropping the
            # percent branch would let the workbook and the Python/HTML model disagree under a
            # configured amountTolerancePercent.
            offset = f'${L_diff}$5:${L_diff}${r_last}+{L_diff}{r}'
            amt_ok = f'ABS({offset})<={abs_tol}'
            if pct_tol and pct_tol > 0:
                # Element-wise larger magnitude of the two offsetting diffs. MAX() would collapse the
                # whole array to one scalar inside SUMPRODUCT, so build the per-element max as
                # (ar>sc)*ar+(ar<=sc)*sc. The percent test uses multiplication (no division) so a
                # zero denominator can't error - a genuine zero offset already passes the abs test.
                ar = f'ABS(${L_diff}$5:${L_diff}${r_last})'
                sc = f'ABS({L_diff}{r})'
                denom = f'(({ar}>{sc})*{ar}+({ar}<={sc})*{sc})'
                amt_ok = f'((ABS({offset})<={abs_tol})+(ABS({offset})<={pct_tol}/100*{denom}))'
            timing_test = (f'SUMPRODUCT((${L_rk}$5:${L_rk}${r_last}=${L_rk}{r})*'
                           f'(${L_dtype}$5:${L_dtype}${r_last}={opp})*'
                           f'({amt_ok}))>0')
            root = (f'=IF({L_status}{r}="Reconciled","—",'
                    f'IF({L_dtype}{r}="Amount mismatch","Measurement",'
                    f'IF(OR({L_dtype}{r}={dup_lit},{L_dtype}{r}={miss_amt_lit}),"Scope / mapping",'
                    f'IF({timing_test},"Timing","Scope / mapping"))))')
        else:
            root = (f'=IF({L_status}{r}="Reconciled","—",'
                    f'IF({L_dtype}{r}="Amount mismatch","Measurement","Scope / mapping"))')
        c_rt = ws.cell(row=r, column=9 + D, value=root)
        c_rt.alignment = a_left; c_rt.font = f_body
        c_ac = ws.cell(row=r, column=10 + D,
                       value=(f'=IF({L_root}{r}="Measurement","Obtain supporting detail and correct the misstated balance",'
                              f'IF({L_root}{r}="Timing","Confirm cut-off; the offsetting entry sits in the adjacent period",'
                              f'IF({L_root}{r}="Scope / mapping","Confirm the account is intentionally excluded, or post the missing entry",'
                              f'"No action — line agrees")))'))
        c_ac.font = f_body

    # Totals row + control row.
    tot_lbl = ws.cell(row=r_total, column=4, value="Total"); tot_lbl.font = f_bold
    for L in (L_amt_a, L_amt_b, L_diff):
        cc = ws.cell(row=r_total, column=_col_to_idx(L) + 1, value=f"=SUM({L}{r_first}:{L}{r_last})")
        cc.font = f_bold; cc.number_format = ACCT2
    top = Side(style="thin", color=HDR_FILL)
    for c in range(1, ncols + 1):
        ws.cell(row=r_total, column=c).border = Border(top=top, bottom=top)
    cl = ws.cell(row=r_ctrl, column=4,
                 value="Control — net difference ties to the independent ledger totals (must be nil)")
    cl.font = Font(name=REPORT_FONT, color=SUB_C)
    # A real check, not a tautology: the reconciliation's net difference (sum of the per-key
    # Difference column) must equal the difference of the two *independent* source-tab totals
    # (SUM over each source's amount column). If a key were dropped from the union or a range were
    # misaligned, the per-key total would stop matching the raw source total and this reads non-nil.
    ctrl_cell = ws.cell(row=r_ctrl, column=_col_to_idx(L_diff) + 1,
                        value=f"={L_diff}{r_total}-(SUM({amt_a_rng})-SUM({amt_b_rng}))")
    ctrl_cell.number_format = ACCT2
    ctrl_cell.font = f_bold

    # Column widths (aligned to v15).
    ws.column_dimensions["A"].width = 26
    for name in desc_cols:
        Lc = desc_letter[name]
        if name == out.get("accountNameColumn"):
            w = 22
        elif name == out.get("accountColumn"):
            w = 14
        else:
            w = 10
        ws.column_dimensions[Lc].width = w
    ws.column_dimensions[L_amt_a].width = 16
    ws.column_dimensions[L_amt_b].width = 16
    ws.column_dimensions[L_diff].width = 14
    ws.column_dimensions[L_lines_a].width = 9
    ws.column_dimensions[L_lines_b].width = 9
    ws.column_dimensions[L_status].width = 12
    ws.column_dimensions[L_dtype].width = 19
    ws.column_dimensions[L_root].width = 16
    ws.column_dimensions[L_action].width = 52

    ws.freeze_panes = f"{L_amt_a}5"

    # Zebra banding + status colouring (conditional formatting, so it survives edits).
    rng = f"A{r_first}:{L_action}{r_last}"
    zebra = PatternFill(start_color=ZEBRA_BG, end_color=ZEBRA_BG, fill_type="solid")
    ws.conditional_formatting.add(rng, FormulaRule(formula=["MOD(ROW(),2)=1"], fill=zebra))
    srng = f"{L_status}{r_first}:{L_status}{r_last}"
    ws.conditional_formatting.add(srng, CellIsRule(
        operator="equal", formula=['"Open Item"'],
        fill=PatternFill(start_color=OPEN_BG, end_color=OPEN_BG, fill_type="solid"),
        font=Font(color=OPEN_FONT)))
    ws.conditional_formatting.add(srng, CellIsRule(
        operator="equal", formula=['"Reconciled"'],
        fill=PatternFill(start_color=REC_BG, end_color=REC_BG, fill_type="solid"),
        font=Font(color=REC_FONT)))

    return {
        "r_first": r_first, "r_last": r_last, "r_total": r_total, "r_ctrl": r_ctrl,
        "desc_letter": desc_letter, "D": D,
        "L_amt_a": L_amt_a, "L_amt_b": L_amt_b, "L_diff": L_diff,
        "L_lines_a": L_lines_a, "L_lines_b": L_lines_b, "L_status": L_status,
        "L_dtype": L_dtype, "L_root": L_root, "recon_rows": recon_rows,
    }


def _write_dashboard(ws, info, config, df_a, df_b, meta_a, meta_b, sa, sb, narrative, src_name):
    from openpyxl.styles import Font, PatternFill, Alignment

    # Shared fonts (assigned by reference) so the Dashboard is styled as it is built - there is no
    # separate whole-workbook font pass over any sheet.
    f_bold = Font(name=REPORT_FONT, bold=True)
    f_body = Font(name=REPORT_FONT)
    f_sec = Font(name=REPORT_FONT, bold=True, size=12, color=SEC_C)
    f_hdr = Font(name=REPORT_FONT, bold=True, color=HDR_FONT)
    f_arial = Font(name="Arial", size=10)
    la = config["sources"]["a"]["label"]
    lb = config["sources"]["b"]["label"]
    out = config.get("output", {})
    acct_col = out.get("accountColumn")
    name_col = out.get("accountNameColumn")
    renames = out.get("columnRenames", {})
    # Display headers derive from the configured column names (via columnRenames) so the
    # pivots read correctly in any domain - "Vendor ID" for a WHT run, "Account Number" for GL.
    acct_hdr = renames.get(acct_col, acct_col) if acct_col else "Account"
    name_hdr = renames.get(name_col, name_col) if name_col else "Name"
    group_by = [g for g in out.get("groupBy", []) if g in config["sources"]["a"]["keyColumns"]]
    # Precompute each source as plain dicts once, so the account / company-period pivots below do
    # O(1) dict access per union row instead of df.iloc[srow-2] (a fresh pandas Series each time).
    a_recs = df_a.to_dict("records")
    b_recs = df_b.to_dict("records")
    a_cols = set(df_a.columns)
    b_cols_set = set(df_b.columns)
    # A->B column map (positionally aligned by align_key_columns / keyMap), so any A-side key name
    # read from the B frame is translated to B's own column name - otherwise a keyMap that renames
    # columns (e.g. A "Account No." -> B "GLAccount") makes df_b[A-name] a KeyError and silently
    # drops B-origin rows from the pivots.
    keymap_ab = dict(zip(config["sources"]["a"]["keyColumns"], config["sources"]["b"]["keyColumns"]))
    dl = info["desc_letter"]
    rf, rl = info["r_first"], info["r_last"]
    RB = dl.get(group_by[0]) if group_by else "B"
    RE = dl.get(group_by[1]) if len(group_by) > 1 else None
    RC = dl.get(acct_col) if acct_col else None
    Fa, Fb, Fd = info["L_amt_a"], info["L_amt_b"], info["L_diff"]
    Kst, Ldt, Mrc = info["L_status"], info["L_dtype"], info["L_root"]
    rtot = info["r_total"]
    rctrl = info["r_ctrl"]

    def R(col):  # a Reconciliation range for a whole-column data span
        return f"Reconciliation!${col}${rf}:${col}${rl}"

    hdr_fill = PatternFill("solid", fgColor=HDR_FILL)

    def section(row, col, text):
        c = ws.cell(row=row, column=col, value=text)
        c.font = f_sec

    def header(row, col, text):
        # Header text can include user-derived column names (via columnRenames); neutralize so a
        # column literally named e.g. "=cmd" can't execute when the workbook opens.
        c = ws.cell(row=row, column=col, value=_neutralize(text))
        c.fill = hdr_fill
        c.font = f_hdr
        c.alignment = Alignment(horizontal="center", vertical="center")

    def txt(cell):  # v15 renders row labels / text data in Arial 10
        cell.font = f_arial
        return cell

    # Title + basis of preparation.
    t = ws.cell(row=1, column=1, value=f"Reconciliation Dashboard — {la} vs {lb}")
    t.font = Font(name=REPORT_FONT, bold=True, size=18, color=SEC_C)
    basis_bits = []
    for g in group_by:
        if g == group_by[0]:
            # Distinct group values from the two columns directly (vectorized), instead of an
            # O(rows) df.iloc[i][g] Series allocation per row. The B column may be named differently
            # under keyMap, so translate g through the A->B map and guard when it's absent.
            gb = keymap_ab.get(g, g)
            vals = {str(v) for v in df_a[g].tolist()} if g in a_cols else set()
            if gb in b_cols_set:
                vals |= {str(v) for v in df_b[gb].tolist()}
            basis_bits.append(f"{g} " + ", ".join(sorted(vals)))
    basis_bits.append(f"Difference = {la} less {lb}")
    if src_name:
        basis_bits.append(f"Source: {src_name}")
    b2 = ws.cell(row=2, column=1, value=_neutralize(" | ".join(basis_bits)))
    b2.font = Font(name=REPORT_FONT, color=SUB_C)

    # ---- Control panel (rows 5-11) ----
    section(5, 1, "Control panel — every control must read OK before sign-off")
    for j, h in enumerate(["Control", "Result", "Expected", "Status"]):
        header(6, 1 + j, h)
    a_mk = _xl_sheet_ref(sa, f"${meta_a['mk_letter']}$2:${meta_a['mk_letter']}${meta_a['last']}")
    b_mk = _xl_sheet_ref(sb, f"${meta_b['mk_letter']}$2:${meta_b['mk_letter']}${meta_b['last']}")
    a_amt = _xl_sheet_ref(sa, f"${meta_a['amt_letter']}$2:${meta_a['amt_letter']}${meta_a['last']}")
    b_amt = _xl_sheet_ref(sb, f"${meta_b['amt_letter']}$2:${meta_b['amt_letter']}${meta_b['last']}")
    controls = [
        ("Every key in either ledger appears once",
         f"=COUNTA(Reconciliation!$A${rf}:$A${rl})",
         # Unique keys in A, plus unique keys in B that are absent from A - matching the union
         # (which de-duplicates each source), rather than counting raw rows. The 1/COUNTIF pattern
         # collapses repeats of the same key to a single count; keyless rows each carry a distinct
         # placeholder so they count once apiece. Each term drops to 0 when its source has no data
         # rows, so the helper range never inverts to include a blank cell (which would #DIV/0!).
         ("=" + (f"SUMPRODUCT(1/COUNTIF({a_mk},{a_mk}))" if meta_a["n"] else "0")
          + "+" + (f"SUMPRODUCT((COUNTIF({a_mk},{b_mk})=0)/COUNTIF({b_mk},{b_mk}))"
                   if meta_b["n"] else "0")),
         "count"),
        (f"Amount — {la} agrees to the {la} tab",
         f"=Reconciliation!${Fa}${rtot}", f"=SUM({a_amt})", "acct"),
        (f"Amount — {lb} agrees to the {lb} tab",
         f"=Reconciliation!${Fb}${rtot}", f"=SUM({b_amt})", "acct"),
        ("Total difference proves to the two ledger totals",
         f"=Reconciliation!${Fd}${rctrl}", "0", "acct"),
        ("Reconciled plus open items equal total lines",
         f'=COUNTIF({R(Kst)},"Reconciled")+COUNTIF({R(Kst)},"Open Item")',
         f"=COUNTA(Reconciliation!$A${rf}:$A${rl})", "count"),
    ]
    for i, (label, result, expected, kind) in enumerate(controls):
        row = 7 + i
        txt(ws.cell(row=row, column=1, value=label))
        rc = ws.cell(row=row, column=2, value=result)
        ec = ws.cell(row=row, column=3, value=expected)
        rc.alignment = ec.alignment = Alignment(horizontal="right")
        rc.font = ec.font = f_body
        fmt = ACCT2 if kind == "acct" else CNT_FMT
        rc.number_format = ec.number_format = fmt
        sc = ws.cell(row=row, column=4,
                     value=(f'=IF(ROUND(B{row}-C{row},2)=0,"OK","CHECK")' if kind == "acct"
                            else f'=IF(B{row}=C{row},"OK","CHECK")'))
        sc.alignment = Alignment(horizontal="center")
        sc.font = f_body

    # Right side of the control band: open items by difference type.
    section(6, 8, "Open items by difference type")
    header(7, 8, "Difference type"); header(7, 9, "Count"); header(7, 10, "Value, ignoring sign")
    dtypes = ["Amount mismatch", f"Missing in {la}", f"Missing in {lb}", DT_DUPLICATE, DT_MISSING_AMOUNT]
    for i, dt in enumerate(dtypes):
        row = 8 + i
        txt(ws.cell(row=row, column=8, value=dt))
        cc9 = ws.cell(row=row, column=9, value=f"=COUNTIF({R(Ldt)},$H{row})")
        cc9.alignment = Alignment(horizontal="right"); cc9.font = f_body
        vc = ws.cell(row=row, column=10,
                     value=f"=SUMPRODUCT(({R(Ldt)}=$H{row})*ABS({R(Fd)}))")
        vc.number_format = ACCT2; vc.font = f_body
    trow = 8 + len(dtypes)
    ws.cell(row=trow, column=8, value="Total").font = f_bold
    ws.cell(row=trow, column=9, value=f"=SUM(I8:I{trow-1})").font = f_bold
    tc = ws.cell(row=trow, column=10, value=f"=SUM(J8:J{trow-1})")
    tc.font = f_bold; tc.number_format = ACCT2

    # ---- Reconciliation summary (rows 13-19) + open items by root cause ----
    section(13, 1, "Reconciliation summary")
    summ = [
        ("Total lines", f"=COUNTA(Reconciliation!$A${rf}:$A${rl})", CNT_FMT),
        ("Reconciled", f'=COUNTIF({R(Kst)},"Reconciled")', CNT_FMT),
        ("Open items", f'=COUNTIF({R(Kst)},"Open Item")', CNT_FMT),
        ("Match rate", "=IF(B14=0,0,B15/B14)", PCT_FMT),
        (f"Net difference ({la} less {lb})", f"=SUM({R(Fd)})", ACCT2),
        ("Gross difference, ignoring sign", f"=SUMPRODUCT(ABS({R(Fd)}))", ACCT2),
    ]
    for i, (label, formula, fmt) in enumerate(summ):
        row = 14 + i
        txt(ws.cell(row=row, column=1, value=label))
        vc = ws.cell(row=row, column=2, value=formula)
        vc.font = f_bold; vc.alignment = Alignment(horizontal="right")
        vc.number_format = fmt

    # Open items by root cause — placed two rows below the (now variable-length) by-type total so
    # the two right-column tables never overlap regardless of how many difference types are listed.
    rc_sec = trow + 2
    section(rc_sec, 8, "Open items by root cause")
    header(rc_sec + 1, 8, "Root cause"); header(rc_sec + 1, 9, "Count"); header(rc_sec + 1, 10, "Value, ignoring sign")
    roots = ["Measurement", "Timing", "Scope / mapping"]
    for i, rt in enumerate(roots):
        row = rc_sec + 2 + i
        txt(ws.cell(row=row, column=8, value=rt))
        cc9 = ws.cell(row=row, column=9, value=f"=COUNTIF({R(Mrc)},$H{row})")
        cc9.alignment = Alignment(horizontal="right"); cc9.font = f_body
        vc = ws.cell(row=row, column=10, value=f"=SUMPRODUCT(({R(Mrc)}=$H{row})*ABS({R(Fd)}))")
        vc.number_format = ACCT2; vc.font = f_body
    rtrow = rc_sec + 2 + len(roots)
    ws.cell(row=rtrow, column=8, value="Total").font = f_bold
    ws.cell(row=rtrow, column=9, value=f"=SUM(I{rc_sec + 2}:I{rtrow-1})").font = f_bold
    vc = ws.cell(row=rtrow, column=10, value=f"=SUM(J{rc_sec + 2}:J{rtrow-1})")
    vc.font = f_bold; vc.number_format = ACCT2

    # ---- Difference by account (rows 21+) ----
    # Build the unique account list first; only draw the section when the account column is
    # configured, resolvable to a Reconciliation column (RC), and actually present in the data.
    # Otherwise the SUMIF ranges would reference a "$None$" column and an empty list would build a
    # reversed SUM() range (e.g. SUM(C23:C22)).
    accounts = []
    if acct_col and RC:
        seen = set()
        for side, srow in info["recon_rows"]:
            if side == "a":
                rec = a_recs[srow - 2]
                acct = rec.get(acct_col) if acct_col in a_cols else None
                nm = rec.get(name_col) if (name_col and name_col in a_cols) else ""
            else:
                bacct = keymap_ab.get(acct_col, acct_col)
                rec = b_recs[srow - 2]
                acct = rec.get(bacct) if bacct in b_cols_set else None
                nm = rec.get(name_col) if (name_col and name_col in b_cols_set) else ""
            if acct is not None and acct not in seen:
                seen.add(acct); accounts.append((acct, nm))
    acc_start = 23
    acc_tot = 22  # baseline row if the account section is not drawn (keeps the later blocks below)
    if accounts:
        section(21, 1, "Difference by account")
        for j, h in enumerate([acct_hdr, name_hdr, f"Amount \u2014 {la}", f"Amount \u2014 {lb}", "Difference"]):
            header(22, 1 + j, h)
        for i, (acct, nm) in enumerate(accounts):
            row = acc_start + i
            ac = ws.cell(row=row, column=1, value=_neutralize(acct))
            ac.alignment = Alignment(horizontal="left"); ac.font = f_body
            txt(ws.cell(row=row, column=2, value=_neutralize(nm)))
            c3 = ws.cell(row=row, column=3, value=f"=SUMIF({R(RC)},$A{row},{R(Fa)})")
            c3.number_format = ACCT2; c3.font = f_body
            c4 = ws.cell(row=row, column=4, value=f"=SUMIF({R(RC)},$A{row},{R(Fb)})")
            c4.number_format = ACCT2; c4.font = f_body
            c5 = ws.cell(row=row, column=5, value=f"=C{row}-D{row}")
            c5.number_format = ACCT2; c5.font = f_body
        acc_tot = acc_start + len(accounts)
        ws.cell(row=acc_tot, column=2, value="Total").font = f_bold
        for col, base in ((3, "C"), (4, "D"), (5, "E")):
            cc = ws.cell(row=acc_tot, column=col, value=f"=SUM({base}{acc_start}:{base}{acc_tot-1})")
            cc.font = f_bold; cc.number_format = ACCT2

    # Difference by company and period (right side; aligned one row lower than the left block,
    # matching v15 - section on row 22, sub-headers on row 23, data from row 24). Only drawn when
    # both group dimensions resolve AND at least one (company, period) combo exists, so the totals
    # never build a reversed SUM() range.
    if RB and RE:
        combos = []
        seenc = set()
        for side, srow in info["recon_rows"]:
            if side == "a":
                rec = a_recs[srow - 2]
                gcomp, gper = group_by[0], group_by[1]
                cols_set = a_cols
            else:
                rec = b_recs[srow - 2]
                # Translate the A-side group names to B's column names (keyMap may rename them).
                gcomp, gper = keymap_ab.get(group_by[0], group_by[0]), keymap_ab.get(group_by[1], group_by[1])
                cols_set = b_cols_set
            comp = rec.get(gcomp) if gcomp in cols_set else None
            per = rec.get(gper) if gper in cols_set else None
            key = (comp, per)
            if comp is not None and per is not None and key not in seenc:
                seenc.add(key); combos.append((comp, per))
        if combos:
            comp_hdr = renames.get(group_by[0], group_by[0])
            per_hdr = renames.get(group_by[1], group_by[1])
            section(22, 8, f"Difference by {comp_hdr.lower()} and {per_hdr.lower()}")
            for j, h in enumerate([comp_hdr, per_hdr, f"Amount \u2014 {la}", f"Amount \u2014 {lb}",
                                   "Difference", "Open items"]):
                header(23, 8 + j, h)
            cp_start = 24
            for i, (comp, per) in enumerate(combos):
                row = cp_start + i
                cc8 = ws.cell(row=row, column=8, value=_neutralize(comp))
                cc8.alignment = Alignment(horizontal="left"); cc8.font = f_body
                txt(ws.cell(row=row, column=9, value=_neutralize(per)))
                c10 = ws.cell(row=row, column=10,
                              value=f"=SUMIFS({R(Fa)},{R(RB)},$H{row},{R(RE)},$I{row})")
                c10.number_format = ACCT2; c10.font = f_body
                c11 = ws.cell(row=row, column=11,
                              value=f"=SUMIFS({R(Fb)},{R(RB)},$H{row},{R(RE)},$I{row})")
                c11.number_format = ACCT2; c11.font = f_body
                c12 = ws.cell(row=row, column=12, value=f"=J{row}-K{row}")
                c12.number_format = ACCT2; c12.font = f_body
                mc = ws.cell(row=row, column=13,
                             value=f'=COUNTIFS({R(RB)},$H{row},{R(RE)},$I{row},{R(Kst)},"Open Item")')
                mc.number_format = CNT_FMT
                mc.alignment = Alignment(horizontal="center"); mc.font = f_body
            cp_tot = cp_start + len(combos)
            ws.cell(row=cp_tot, column=9, value="Total").font = f_bold
            for col, base in ((10, "J"), (11, "K")):
                cc = ws.cell(row=cp_tot, column=col, value=f"=SUM({base}{cp_start}:{base}{cp_tot-1})")
                cc.font = f_bold; cc.number_format = ACCT2
            for col, base in ((12, "L"), (13, "M")):
                cc = ws.cell(row=cp_tot, column=col, value=f"=SUM({base}{cp_start}:{base}{cp_tot-1})")
                cc.font = f_bold
            acc_tot = max(acc_tot, cp_tot)

    # ---- Headlines (driver narrative; Calibri, matching v15) ----
    h_row = acc_tot + 2
    section(h_row, 1, "Headlines")
    narr_rows = []
    for i, line in enumerate(narrative):
        row = h_row + 1 + i
        narr_rows.append(row)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
        cell = ws.cell(row=row, column=1, value=line)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.font = Font(name="Calibri", color=NARR_C)
        import math
        ws.row_dimensions[row].height = max(15, 15 * math.ceil((len(line) + 3) / 130))

    # Widths.
    for col, w in {"A": 42, "B": 60, "C": 18, "D": 22, "E": 14, "F": 18, "G": 3,
                   "H": 31, "I": 8, "J": 20, "K": 14, "L": 14, "M": 9}.items():
        ws.column_dimensions[col].width = w
    return narr_rows


def control_total_tieout(df_a, df_b, config):
    """Control-total tie-out (SKILL.md Step 3b): one side is a control figure (or a short list of
    control-account balances), the other is the detail that should sum to it. This is NOT a
    line-by-line match - it proves the detail SUMS to the control and reports the variance.

    controlTotal.controlSide names the control source ("a"/"b"); the other source is the detail.
    controlTotal.controlAmountColumn is the control balance column; the detail amount is the detail
    source's amountColumn. When controlGroupColumn (on the control side) and detailGroupColumn (on
    the detail side) are both set, each control-account balance is tied to its detail group
    individually and orphans on either side are reported."""
    ct = config.get("controlTotal", {})
    norm = config.get("normalization", {})
    control_side = ct.get("controlSide", "a")
    if control_side not in ("a", "b"):
        raise ValueError("controlTotal.controlSide must be 'a' or 'b'.")
    detail_side = "b" if control_side == "a" else "a"
    df_c = df_a if control_side == "a" else df_b
    df_d = df_a if detail_side == "a" else df_b
    csrc, dsrc = config["sources"][control_side], config["sources"][detail_side]
    clabel, dlabel = csrc.get("label", "Control"), dsrc.get("label", "Detail")
    c_amt_col = ct.get("controlAmountColumn") or csrc["amountColumn"]
    d_amt_col = dsrc["amountColumn"]
    c_sign = csrc.get("signConvention", "asIs")
    d_sign = dsrc.get("signConvention", "asIs")
    for col, df, lab in ((c_amt_col, df_c, clabel), (d_amt_col, df_d, dlabel)):
        if col not in df.columns:
            raise ValueError(f"Source '{lab}' is missing the amount column '{col}'. "
                             f"Available: {list(df.columns)}")

    def amt_or_missing(v, sign):
        a = apply_sign(normalize_amount(v, norm), sign)
        return (a, False) if a is not None else (0.0, True)

    abs_tol, pct_tol = effective_tolerances(config.get("matching", {}))

    def is_tied(control, detail):
        # Honor BOTH tolerances exactly like the record-to-record matcher: within abs_tol OR (when a
        # percentage tolerance is set) within pct_tol% of the larger magnitude. In exact mode
        # (0,0) this is exact-cent equality.
        return within_tolerance(control, detail, abs_tol, pct_tol)

    cgroup, dgroup = ct.get("controlGroupColumn"), ct.get("detailGroupColumn")
    rows = []
    detail_rows = []            # every detail record with its group + amount (Detail section)
    orphans_control, orphans_detail = [], []
    missing_control = missing_detail = 0
    if cgroup and dgroup:
        if cgroup not in df_c.columns:
            raise ValueError(f"Control source '{clabel}' is missing controlGroupColumn '{cgroup}'.")
        if dgroup not in df_d.columns:
            raise ValueError(f"Detail source '{dlabel}' is missing detailGroupColumn '{dgroup}'.")
        # Sum each side by normalized group key, tracking blank/unparseable amounts per group so a
        # tie is never reported over invalid rows without a diagnostic.
        c_by, d_by = {}, {}
        c_disp, d_disp = {}, {}
        for rec in df_c.to_dict("records"):
            gk = norm_key(rec.get(cgroup), norm)
            amt, miss = amt_or_missing(rec.get(c_amt_col), c_sign)
            e = c_by.setdefault(gk, {"sum": 0.0, "miss": 0}); e["sum"] = round(e["sum"] + amt, 2); e["miss"] += miss
            missing_control += miss
            c_disp.setdefault(gk, rec.get(cgroup))
        for rec in df_d.to_dict("records"):
            gk = norm_key(rec.get(dgroup), norm)
            amt, miss = amt_or_missing(rec.get(d_amt_col), d_sign)
            e = d_by.setdefault(gk, {"sum": 0.0, "miss": 0}); e["sum"] = round(e["sum"] + amt, 2); e["miss"] += miss
            missing_detail += miss
            d_disp.setdefault(gk, rec.get(dgroup))
            detail_rows.append({"group": rec.get(dgroup), "amount": amt, "missing": bool(miss)})
        for gk in list(c_by):
            control = c_by[gk]["sum"]
            detail = d_by.get(gk, {"sum": 0.0})["sum"]
            var = round(control - detail, 2)
            grp_miss = c_by[gk]["miss"] + d_by.get(gk, {"miss": 0})["miss"]
            if gk not in d_by:
                orphans_control.append((c_disp[gk], control))
            # A group with a blank/unparseable amount is never reported tied - the sum is unreliable.
            rows.append({"group": c_disp[gk], "control": control, "detail": detail, "variance": var,
                         "missing": grp_miss, "tied": grp_miss == 0 and is_tied(control, detail)})
        for gk in d_by:
            if gk not in c_by:
                orphans_detail.append((d_disp[gk], d_by[gk]["sum"]))
                grp_miss = d_by[gk]["miss"]
                rows.append({"group": d_disp[gk], "control": 0.0, "detail": d_by[gk]["sum"],
                             "variance": round(-d_by[gk]["sum"], 2), "missing": grp_miss,
                             "tied": grp_miss == 0 and is_tied(0.0, d_by[gk]["sum"])})
    else:
        control = detail = 0.0
        for v in df_c[c_amt_col].tolist():
            amt, miss = amt_or_missing(v, c_sign); control = round(control + amt, 2); missing_control += miss
        for rec in df_d.to_dict("records"):
            amt, miss = amt_or_missing(rec.get(d_amt_col), d_sign); detail = round(detail + amt, 2); missing_detail += miss
            detail_rows.append({"group": "(all)", "amount": amt, "missing": bool(miss)})
        grp_miss = missing_control + missing_detail
        rows.append({"group": "(all)", "control": control, "detail": detail,
                     "variance": round(control - detail, 2), "missing": grp_miss,
                     "tied": grp_miss == 0 and is_tied(control, detail)})

    control_total = round(sum(r["control"] for r in rows), 2)
    detail_total = round(sum(r["detail"] for r in rows), 2)
    variance = round(control_total - detail_total, 2)
    total_missing = missing_control + missing_detail
    return {"mode": "control-total", "control_label": clabel, "detail_label": dlabel,
            "grouped": bool(cgroup and dgroup), "rows": rows, "detail_rows": detail_rows,
            "control_total": control_total, "detail_total": detail_total,
            "variance": variance, "tied_out": total_missing == 0 and is_tied(control_total, detail_total),
            "orphans_control": orphans_control, "orphans_detail": orphans_detail,
            "missing_control": missing_control, "missing_detail": missing_detail}


def write_control_total_report(result, config, out_path):
    """Write the control-total tie-out to a styled .xlsx: a per-group table (control, detail,
    variance, tied) and a total row that proves whether the detail sums to the control."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Control-Total Tie-Out"
    clabel, dlabel = result["control_label"], result["detail_label"]
    f_title = Font(name=REPORT_FONT, bold=True, size=16, color=SEC_C)
    f_hdr = Font(name=REPORT_FONT, bold=True, color=HDR_FONT)
    f_body = Font(name=REPORT_FONT)
    f_bold = Font(name=REPORT_FONT, bold=True)
    hdr_fill = PatternFill("solid", fgColor=HDR_FILL)
    right = Alignment(horizontal="right")

    ws.cell(row=1, column=1, value=f"Control-total tie-out — {dlabel} against {clabel}").font = f_title
    ws.cell(row=2, column=1,
            value=("Proves the detail sums to the control figure. Variance = control less detail; "
                   "a control reconciles when its variance is within tolerance.")).font = Font(name=REPORT_FONT, color=SUB_C)
    grouped = result["grouped"]
    ghdr = "Control account" if grouped else "Scope"
    headers = [ghdr, f"Control ({clabel})", f"Detail sum ({dlabel})", "Variance", "Tied?", "Note"]
    for c, name in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=c, value=name)
        cell.fill = hdr_fill; cell.font = f_hdr
        cell.alignment = Alignment(horizontal="center")
    r = 5
    for row in result["rows"]:
        ws.cell(row=r, column=1, value=_neutralize(row["group"])).font = f_body
        for c, key in ((2, "control"), (3, "detail"), (4, "variance")):
            cell = ws.cell(row=r, column=c, value=row[key])
            cell.number_format = ACCT2; cell.font = f_body; cell.alignment = right
        tc = ws.cell(row=r, column=5, value="Tied" if row["tied"] else "NOT TIED")
        tc.font = f_body; tc.alignment = Alignment(horizontal="center")
        # Flag groups that carry a blank/unparseable amount so a reviewer sees why an untied group
        # cannot be trusted rather than seeing a silent 0.
        if row.get("missing"):
            note = f'{row["missing"]} blank/unparseable amount row(s) — verify'
            ws.cell(row=r, column=6, value=note).font = f_body
        r += 1
    ws.cell(row=r, column=1, value="Total").font = f_bold
    for c, key in ((2, "control_total"), (3, "detail_total"), (4, "variance")):
        cell = ws.cell(row=r, column=c, value=result[key])
        cell.number_format = ACCT2; cell.font = f_bold; cell.alignment = right
    tc = ws.cell(row=r, column=5, value="Tied" if result["tied_out"] else "NOT TIED")
    tc.font = f_bold; tc.alignment = Alignment(horizontal="center")
    tot_missing = result.get("missing_control", 0) + result.get("missing_detail", 0)
    if tot_missing:
        ws.cell(row=r, column=6,
                value=f'{tot_missing} blank/unparseable amount row(s) across sources — tie-out not trustworthy until resolved').font = f_bold
    r += 2

    # Orphans section: control accounts with no detail, and detail groups with no control account -
    # each is a real finding (a mis-coded entry or a control that should be empty and is not).
    if result["orphans_control"] or result["orphans_detail"]:
        ws.cell(row=r, column=1, value="Orphans (no counterpart)").font = Font(name=REPORT_FONT, bold=True, size=13, color=SEC_C)
        r += 1
        for c, name in enumerate(["Side", ghdr, "Amount"], start=1):
            cell = ws.cell(row=r, column=c, value=name); cell.fill = hdr_fill; cell.font = f_hdr
            cell.alignment = Alignment(horizontal="center")
        r += 1
        for grp, amt in result["orphans_control"]:
            ws.cell(row=r, column=1, value=f"Control with no {dlabel}").font = f_body
            ws.cell(row=r, column=2, value=_neutralize(grp)).font = f_body
            ac = ws.cell(row=r, column=3, value=amt); ac.number_format = ACCT2; ac.font = f_body; ac.alignment = right
            r += 1
        for grp, amt in result["orphans_detail"]:
            ws.cell(row=r, column=1, value=f"{dlabel} with no control").font = f_body
            ws.cell(row=r, column=2, value=_neutralize(grp)).font = f_body
            ac = ws.cell(row=r, column=3, value=amt); ac.number_format = ACCT2; ac.font = f_body; ac.alignment = right
            r += 1
        r += 1

    # Detail section: the detail rows that make up each control sum, so a reviewer can see the
    # composition behind a variance (grouped by control account when a group column is set).
    detail_rows = result.get("detail_rows", [])
    if detail_rows:
        ws.cell(row=r, column=1, value=f"Detail — {dlabel}").font = Font(name=REPORT_FONT, bold=True, size=13, color=SEC_C)
        r += 1
        det_hdr = ([ghdr, "Amount", "Note"] if grouped else ["Amount", "Note"])
        for c, name in enumerate(det_hdr, start=1):
            cell = ws.cell(row=r, column=c, value=name); cell.fill = hdr_fill; cell.font = f_hdr
            cell.alignment = Alignment(horizontal="center")
        r += 1
        for d in detail_rows:
            col = 1
            if grouped:
                ws.cell(row=r, column=col, value=_neutralize(d["group"])).font = f_body; col += 1
            ac = ws.cell(row=r, column=col, value=d["amount"]); ac.number_format = ACCT2
            ac.font = f_body; ac.alignment = right; col += 1
            if d["missing"]:
                ws.cell(row=r, column=col, value="blank/unparseable amount").font = f_body
            r += 1

    for col, w in {"A": 34, "B": 22, "C": 20, "D": 16, "E": 12, "F": 46}.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A5"
    wb.save(out_path)


def write_report(results, config, out_path, df_a, df_b, src_name=None):
    import openpyxl

    if df_a is None or df_b is None:
        raise ValueError("write_report requires both source frames df_a and df_b "
                         "(they drive the per-key model, source metadata, and tabs).")

    la = config["sources"]["a"].get("label", "Source A")
    lb = config["sources"]["b"].get("label", "Source B")

    res_df = pd.DataFrame(results)
    counts = res_df["status"].value_counts().to_dict() if not res_df.empty else {}
    # The Dashboard headlines are built from the per-key reconciliation model (compute_reconciliation) -
    # the same model that drives the Reconciliation sheet's formulas and the HTML dashboard - so the
    # narrative counts can never disagree with the sheet totals. (The tiered `results`/`counts` are a
    # record-level view returned for the caller's console summary, not the per-key artifact.)
    perkey_rows, _, _ = compute_reconciliation(df_a, df_b, config)
    narrative = _build_narrative_perkey(perkey_rows, config)

    meta_a = _src_meta(df_a, config["sources"]["a"], config)
    meta_b = _src_meta(df_b, config["sources"]["b"], config)
    norm = config.get("normalization", {})
    sign_a = config["sources"]["a"].get("signConvention", "asIs")
    sign_b = config["sources"]["b"].get("signConvention", "asIs")

    wb = openpyxl.Workbook()
    ws_dash = wb.active
    ws_dash.title = "Dashboard"
    ws_recon = wb.create_sheet("Reconciliation")
    # Excel sheet names: <=31 chars, no : \ / ? * [ ], and unique. Sanitize both labels.
    taken = {"dashboard", "reconciliation"}
    sa = _safe_sheet_name(la, taken)
    sb = _safe_sheet_name(lb, taken)
    ws_sa = wb.create_sheet(sa)
    ws_sb = wb.create_sheet(sb)

    _write_source_tab(ws_sa, df_a, meta_a, sa, sign=sign_a, norm=norm)
    _write_source_tab(ws_sb, df_b, meta_b, sb, sign=sign_b, norm=norm)
    info = _write_reconciliation(ws_recon, df_a, df_b, config, meta_a, meta_b, sa, sb)
    _write_dashboard(ws_dash, info, config, df_a, df_b, meta_a, meta_b, sa, sb, narrative, src_name)

    # Candidate matches (Needs Review): the tiered matcher's Probable (similarity / duplicate /
    # missing-amount) and Grouped (one-to-many split) pairings. The per-key Reconciliation sheet is
    # an exact-key model and cannot represent a fuzzy or one-to-many pairing as a formula, so those
    # rows would otherwise appear only as separate one-sided breaks. Listing them here (built from
    # the `results` this function is passed) preserves the evidence and review state instead of
    # discarding it, and points the reviewer at the underlying breaks to confirm.
    candidates = [r for r in results if r["status"] in ("Probable (Needs Review)", "Grouped (Needs Review)")]
    if candidates:
        _write_candidate_matches(wb.create_sheet("Candidate Matches"), candidates, la, lb)

    # Fonts are applied as each cell is created (shared Font objects in the writers above), so there
    # is no whole-workbook styling pass - important for large reconciliations.
    wb.save(out_path)
    return counts


def _write_candidate_matches(ws, candidates, la, lb):
    """List the tiered matcher's Probable/Grouped candidate pairings with their evidence, so the
    similarity/duplicate/grouped work is surfaced for review rather than discarded."""
    from openpyxl.styles import Font, PatternFill, Alignment
    f_title = Font(name=REPORT_FONT, bold=True, size=14, color=SEC_C)
    f_hdr = Font(name=REPORT_FONT, bold=True, color=HDR_FONT)
    f_body = Font(name=REPORT_FONT)
    hdr_fill = PatternFill("solid", fgColor=HDR_FILL)
    right = Alignment(horizontal="right")
    ws.cell(row=1, column=1, value="Candidate matches — Needs Review").font = f_title
    ws.cell(row=2, column=1, value=("Similarity, duplicate-key and grouped (one-to-many) pairings the "
            "matcher proposes. Each is a suggestion for a human to confirm, not a posted match.")
            ).font = Font(name=REPORT_FONT, color=SUB_C)
    headers = ["Type", "Key", f"Amount — {la}", f"Amount — {lb}", "Difference", "Evidence"]
    for c, name in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=c, value=name)
        cell.fill = hdr_fill; cell.font = f_hdr; cell.alignment = Alignment(horizontal="center")
    r = 5
    for cand in candidates:
        ws.cell(row=r, column=1, value=_neutralize(cand["status"])).font = f_body
        ws.cell(row=r, column=2, value=_neutralize(str(cand.get("key", "")))).font = f_body
        for c, key in ((3, "amount_a"), (4, "amount_b"), (5, "difference")):
            v = cand.get(key)
            cell = ws.cell(row=r, column=c, value=v)
            cell.number_format = ACCT2; cell.font = f_body; cell.alignment = right
        ws.cell(row=r, column=6, value=_neutralize(str(cand.get("evidence", "")))).font = f_body
        r += 1
    for col, w in {"A": 22, "B": 30, "C": 16, "D": 16, "E": 14, "F": 60}.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A5"



# ----------------------------- HTML dashboard -----------------------------

def compute_reconciliation(df_a, df_b, config):
    """Compute the same per-key reconciliation the Excel derives by formula, as Python values
    (for the HTML dashboard). One row per unique union key with amounts, status, difference type
    and root cause, so the HTML always agrees with the workbook."""
    la = config["sources"]["a"].get("label", "Source A")
    lb = config["sources"]["b"].get("label", "Source B")
    a_keys = config["sources"]["a"]["keyColumns"]
    b_keys = config["sources"]["b"]["keyColumns"]
    amt_a_col = config["sources"]["a"]["amountColumn"]
    amt_b_col = config["sources"]["b"]["amountColumn"]
    out = config.get("output", {})
    acct_col = out.get("accountColumn")
    name_col = out.get("accountNameColumn")
    group_by = out.get("groupBy", [])
    timing_col = config["matching"].get("timingKeyColumn")
    keymap_ab = dict(zip(a_keys, b_keys))

    def kstr(row, keys):
        # Canonical key: identical to build_key() (norm_key per component, shared KEY_DELIM,
        # all-empty collapses to "") so the HTML groups keys the same way as the matcher and the
        # workbook.
        return join_key_parts([norm_key(row.get(k), norm) for k in keys])

    norm = config.get("normalization", {})
    sign_a = config["sources"]["a"].get("signConvention", "asIs")
    sign_b = config["sources"]["b"].get("signConvention", "asIs")

    def amt_a(v):
        return apply_sign(normalize_amount(v, norm), sign_a)

    def amt_b(v):
        return apply_sign(normalize_amount(v, norm), sign_b)

    abs_tol, pct_tol = effective_tolerances(config["matching"])

    # Aggregate each source by canonical (normalized) key string. Keyless rows (all key parts
    # blank) get a unique per-row placeholder so they are never merged together - matching the
    # workbook helper and the record matcher, which treat an empty key as non-matchable. "miss"
    # counts rows whose amount was blank/unparseable so a key carrying an invalid amount is flagged
    # for review rather than silently treated as 0 (which could turn a blank-vs-zero into
    # "Reconciled").
    a_recs, b_recs = df_a.to_dict("records"), df_b.to_dict("records")
    a_agg, b_agg = {}, {}
    a_first, b_first = {}, {}
    order = []
    for i, rec in enumerate(a_recs):
        kl = kstr(rec, a_keys) or keyless_token("A " + la, i + 2)
        if kl not in a_agg:
            a_agg[kl] = {"sum": 0.0, "n": 0, "miss": 0}; a_first[kl] = rec
            order.append(kl)
        v = amt_a(rec[amt_a_col])
        if v is None:
            a_agg[kl]["miss"] += 1
        else:
            a_agg[kl]["sum"] += v
        a_agg[kl]["n"] += 1
    for j, rec in enumerate(b_recs):
        kl = kstr(rec, b_keys) or keyless_token("B " + lb, j + 2)
        if kl not in b_agg:
            b_agg[kl] = {"sum": 0.0, "n": 0, "miss": 0}; b_first[kl] = rec
        v = amt_b(rec[amt_b_col])
        if v is None:
            b_agg[kl]["miss"] += 1
        else:
            b_agg[kl]["sum"] += v
        b_agg[kl]["n"] += 1
    for kl in b_agg:
        if kl not in a_agg:
            order.append(kl)

    def field(kl, col, bcol=None):
        if kl in a_first and col in a_first[kl]:
            return a_first[kl][col]
        if kl in b_first:
            bc = bcol or keymap_ab.get(col, col)
            if bc in b_first[kl]:
                return b_first[kl][bc]
        return ""

    rows = []
    for kl in order:
        aa = a_agg.get(kl, {"sum": 0.0, "n": 0, "miss": 0})
        bb = b_agg.get(kl, {"sum": 0.0, "n": 0, "miss": 0})
        diff = round(aa["sum"] - bb["sum"], 2)
        if aa["n"] == 0:
            dtype = f"Missing in {la}"
        elif bb["n"] == 0:
            dtype = f"Missing in {lb}"
        elif aa["miss"] or bb["miss"]:
            # A key present on both sides but with a blank/unparseable amount somewhere: the netted
            # figure is unreliable, so surface it for review instead of calling it reconciled.
            dtype = DT_MISSING_AMOUNT
        elif aa["n"] > 1 or bb["n"] > 1:
            # Duplicate key on one or both sides: the one-to-one correspondence is ambiguous even
            # when the totals happen to net, so it must be reviewed rather than shown as Reconciled.
            dtype = DT_DUPLICATE
        elif within_tolerance(aa["sum"], bb["sum"], abs_tol, pct_tol):
            # Honor the configured tolerance (0/0 in exact mode) instead of testing raw equality, so
            # the HTML agrees with the matcher: a within-tolerance pair is reconciled.
            dtype = "None"
        else:
            dtype = "Amount mismatch"
        status = "Reconciled" if dtype == "None" else "Open Item"
        rows.append({
            "key": kl,
            "company": field(kl, group_by[0]) if group_by else "",
            "account": field(kl, acct_col) if acct_col else "",
            "name": field(kl, name_col) if name_col else "",
            "period": field(kl, timing_col) if timing_col else (field(kl, group_by[1]) if len(group_by) > 1 else ""),
            "amt_a": aa["sum"], "amt_b": bb["sum"], "diff": diff,
            "lines_a": aa["n"], "lines_b": bb["n"], "status": status, "difftype": dtype,
        })

    # Root cause (needs the whole population to spot an offsetting timing entry). Timing only
    # applies when timing detection is enabled AND there is at least one non-timing key column to
    # group offsetting entries by, and only for a row whose non-timing (reduced) key is not all
    # blank - otherwise unrelated one-sided breaks would be mislabelled "Timing" (mirrors the
    # reconcile() and Excel-root-cause guards so the platforms don't diverge).
    nontiming = [k for k in a_keys if k != timing_col]
    timing_on = (config["matching"].get("enableTimingDetection", True)
                 and timing_col is not None and len(nontiming) >= 1)
    grp = {}
    for r in rows:
        gk = tuple(norm_key(field(r["key"], k), norm) for k in nontiming)
        grp.setdefault(gk, []).append(r)
    for r in rows:
        if r["status"] == "Reconciled":
            r["rootcause"] = "—"
        elif r["difftype"] == "Amount mismatch":
            r["rootcause"] = "Measurement"
        elif r["difftype"] in (DT_DUPLICATE, DT_MISSING_AMOUNT):
            r["rootcause"] = "Scope / mapping"
        else:
            # Group offsetting entries by the NORMALIZED reduced key (norm_key per non-timing
            # component), so the timing classification matches the matcher and the workbook helper
            # even when non-timing key parts differ only by whitespace/case. norm_key also collapses
            # NaN/blank components to "" (str(NaN) would be the truthy "nan"), so keyless /
            # blank-reduced rows are correctly excluded from timing. A genuine timing pair must be an
            # OFFSETTING one-sided break (opposite Missing-in side) whose amount equals this row's
            # amount within tolerance - not merely any opposite break sharing the reduced key - so
            # two same-account rows with DIFFERENT balances are not mislabelled "Timing".
            gk = tuple(norm_key(field(r["key"], k), norm) for k in nontiming)
            opp = f"Missing in {la}" if r["difftype"] == f"Missing in {lb}" else f"Missing in {lb}"
            this_amt = r["amt_a"] if r["difftype"] == f"Missing in {lb}" else r["amt_b"]
            reduced_nonempty = any(gk)
            has_offset = (timing_on and reduced_nonempty and any(
                o["difftype"] == opp
                and within_tolerance(this_amt, (o["amt_a"] if opp == f"Missing in {lb}" else o["amt_b"]), abs_tol, pct_tol)
                for o in grp.get(gk, [])))
            r["rootcause"] = "Timing" if has_offset else "Scope / mapping"
    return rows, la, lb


def _num(x):
    """Number cell, matching the Excel format: 2 decimals, parentheses for negatives,
    0.00 for zero. No currency symbol. Used for every value so the HTML reads consistently."""
    x = x or 0
    return f"({abs(x):,.2f})" if round(x, 2) < 0 else f"{x:,.2f}"


def build_html_dashboard(rows, config, src_name=None, df_a=None, df_b=None):
    import html as _h
    la = config["sources"]["a"].get("label", "Source A")
    lb = config["sources"]["b"].get("label", "Source B")
    out = config.get("output", {})
    group_by = out.get("groupBy", [])
    renames = out.get("columnRenames", {})
    acct_col = out.get("accountColumn")
    name_col = out.get("accountNameColumn")
    # Display headers derive from the configured column names so the pivots read correctly in
    # any domain (e.g. "Vendor ID" for a WHT run instead of a hardcoded "Account Number").
    acct_hdr = renames.get(acct_col, acct_col) if acct_col else "Account"
    name_hdr = renames.get(name_col, name_col) if name_col else "Name"
    comp_hdr = renames.get(group_by[0], group_by[0]) if group_by else "Company"
    per_hdr = renames.get(group_by[1], group_by[1]) if len(group_by) > 1 else "Period"

    total = len(rows)
    reconciled = sum(1 for r in rows if r["status"] == "Reconciled")
    open_rows = [r for r in rows if r["status"] == "Open Item"]
    opn = len(open_rows)
    net = round(sum(r["diff"] for r in rows), 2)
    gross = round(sum(abs(r["diff"]) for r in rows), 2)
    total_a = round(sum(r["amt_a"] for r in rows), 2)
    total_b = round(sum(r["amt_b"] for r in rows), 2)
    rate = (reconciled / total * 100) if total else 0

    # Independent source totals: summed directly from the raw records (a different code path from
    # the per-key aggregation), so the amount controls below are a real check - they would read
    # CHECK if the per-key aggregation dropped or double-counted a record - rather than comparing a
    # value to itself. Falls back to the per-key totals only if the raw frames weren't provided.
    nrm = config.get("normalization", {})
    amt_a_col = config["sources"]["a"]["amountColumn"]
    amt_b_col = config["sources"]["b"]["amountColumn"]
    sgn_a = config["sources"]["a"].get("signConvention", "asIs")
    sgn_b = config["sources"]["b"].get("signConvention", "asIs")
    # Materialize the raw records once (they feed both the independent totals control and the
    # independent unique-key control below); df.to_dict("records") is O(rows*cols) and would
    # otherwise be built twice per frame on large reconciliations.
    a_recs = df_a.to_dict("records") if df_a is not None else None
    b_recs = df_b.to_dict("records") if df_b is not None else None
    if df_a is not None and df_b is not None:
        ind_a = round(sum(apply_sign(normalize_amount(rec.get(amt_a_col), nrm), sgn_a) or 0.0
                          for rec in a_recs), 2)
        ind_b = round(sum(apply_sign(normalize_amount(rec.get(amt_b_col), nrm), sgn_b) or 0.0
                          for rec in b_recs), 2)
    else:
        ind_a, ind_b = total_a, total_b

    # Independent unique-key count, recomputed straight from the raw frames (a separate code path
    # from the `rows` aggregation), so the "every key appears once" control is a real check - it
    # reads CHECK if the aggregation dropped or duplicated a key - rather than comparing total to
    # itself. Mirrors the workbook's SUMPRODUCT(1/COUNTIF) control. Keyless rows get the same unique
    # placeholder scheme as compute_reconciliation so each counts once.
    a_keycols = config["sources"]["a"]["keyColumns"]
    b_keycols = config["sources"]["b"]["keyColumns"]
    if df_a is not None and df_b is not None:
        def _canon(rec, keys, scope, i):
            k = join_key_parts([norm_key(rec.get(c), nrm) for c in keys])
            return k if k else keyless_token(scope, i + 2)
        a_ky = {_canon(rec, a_keycols, "A " + la, i) for i, rec in enumerate(a_recs)}
        b_extra = {k for j, rec in enumerate(b_recs)
                   if (k := _canon(rec, b_keycols, "B " + lb, j)) not in a_ky}
        ind_total = len(a_ky) + len(b_extra)
    else:
        ind_total = total

    def agg_by(keyf):
        d = {}
        for r in open_rows:
            k = keyf(r); c, v = d.get(k, (0, 0.0)); d[k] = (c + 1, v + abs(r["diff"]))
        return d
    by_type = agg_by(lambda r: r["difftype"])
    by_root = agg_by(lambda r: r["rootcause"])

    # By account (all rows), by company/period (all rows) with open counts.
    acct = {}; acct_order = []
    for r in rows:
        a = r["account"]
        if a not in acct:
            acct[a] = {"name": r["name"], "a": 0.0, "b": 0.0}; acct_order.append(a)
        acct[a]["a"] += r["amt_a"]; acct[a]["b"] += r["amt_b"]
    cp = {}; cp_order = []
    for r in rows:
        k = (r["company"], r["period"])
        if k not in cp:
            cp[k] = {"a": 0.0, "b": 0.0, "open": 0}; cp_order.append(k)
        cp[k]["a"] += r["amt_a"]; cp[k]["b"] += r["amt_b"]
        if r["status"] == "Open Item":
            cp[k]["open"] += 1

    # (Headline aggregates now come from _build_narrative_perkey, shared with the Excel Dashboard.)

    def e(s):
        return _h.escape(str(s))

    def numcell(x, bar=None, maxabs=None):
        cls = "num neg" if (x or 0) < 0 else "num"
        s = _num(x)
        if bar and maxabs:
            w = min(100, abs(x) / maxabs * 100) if maxabs else 0
            return f'<td class="{cls} bar-cell">{s}<span class="bar" style="width:{w:.1f}%"></span></td>'
        return f'<td class="{cls}">{s}</td>'

    # ---- controls ----
    ctrls = [
        ("Every key in either ledger appears once", str(total), str(ind_total), total == ind_total),
        (f"Amount — {la} agrees to the {la} tab", _num(total_a), _num(ind_a), round(total_a - ind_a, 2) == 0),
        (f"Amount — {lb} agrees to the {lb} tab", _num(total_b), _num(ind_b), round(total_b - ind_b, 2) == 0),
        ("Total difference proves to the two ledger totals",
         _num(net), _num(round(ind_a - ind_b, 2)), round(net - (ind_a - ind_b), 2) == 0),
        ("Reconciled plus open items equal total lines", str(reconciled + opn), str(total), reconciled + opn == total),
    ]
    ctrl_html = "".join(
        f'<tr><td>{e(lbl)}</td><td class="num">{res}</td><td class="num">{exp}</td>'
        f'<td><span class="{"ok" if ok else "check"}">{"OK" if ok else "CHECK"}</span></td></tr>'
        for lbl, res, exp, ok in ctrls)

    # ---- type / root tables ----
    def kv_table(d, order):
        body = ""
        tc = tv = 0
        for k in order:
            if k in d:
                c, v = d[k]; tc += c; tv += v
                body += f'<tr><td>{e(k)}</td><td class="num">{c:,}</td><td class="num">{_num(v)}</td></tr>'
        body += f'<tr class="total"><td>Total</td><td class="num">{tc:,}</td><td class="num">{_num(tv)}</td></tr>'
        return body
    type_body = kv_table(by_type, ["Amount mismatch", f"Missing in {la}", f"Missing in {lb}",
                                   DT_DUPLICATE, DT_MISSING_AMOUNT])
    root_body = kv_table(by_root, ["Measurement", "Timing", "Scope / mapping"])

    # ---- account table ----
    maxacct = max((abs(acct[a]["a"] - acct[a]["b"]) for a in acct_order), default=1) or 1
    acct_body = ""
    for a in acct_order:
        d = acct[a]; diff = d["a"] - d["b"]
        acct_body += (f'<tr><td>{e(a)}</td><td>{e(d["name"])}</td>'
                      f'{numcell(d["a"])}{numcell(d["b"])}{numcell(diff, bar=True, maxabs=maxacct)}</tr>')
    acct_body += (f'<tr class="total"><td></td><td>Total</td>{numcell(total_a)}{numcell(total_b)}'
                  f'{numcell(round(total_a-total_b,2))}</tr>')

    # ---- company/period table ----
    maxcp = max((abs(cp[k]["a"] - cp[k]["b"]) for k in cp_order), default=1) or 1
    cp_body = ""
    cp_ta = cp_tb = cp_open = 0
    for k in cp_order:
        d = cp[k]; diff = d["a"] - d["b"]; cp_ta += d["a"]; cp_tb += d["b"]; cp_open += d["open"]
        cp_body += (f'<tr><td>{e(k[0])}</td><td>{e(k[1])}</td>'
                    f'{numcell(d["a"])}{numcell(d["b"])}{numcell(diff, bar=True, maxabs=maxcp)}'
                    f'<td class="num">{d["open"]}</td></tr>')
    cp_body += (f'<tr class="total"><td></td><td>Total</td>{numcell(cp_ta)}{numcell(cp_tb)}'
                f'{numcell(round(cp_ta-cp_tb,2))}<td class="num">{cp_open}</td></tr>')

    # ---- open-item detail (sorted by magnitude) ----
    det = sorted(open_rows, key=lambda r: abs(r["diff"]), reverse=True)
    det_body = ""
    for r in det:
        det_body += (f'<tr><td>{e(r["company"])}</td><td>{e(r["account"])}</td><td>{e(r["name"])}</td>'
                     f'<td>{e(r["period"])}</td>{numcell(r["amt_a"])}{numcell(r["amt_b"])}{numcell(r["diff"])}'
                     f'<td><span class="tag tag-open">Open Item</span></td>'
                     f'<td>{e(r["difftype"])}</td><td>{e(r["rootcause"])}</td></tr>')
    det_body += (f'<tr class="total"><td colspan="6">Total difference on open items</td>'
                 f'{numcell(round(sum(r["diff"] for r in open_rows),2))}<td colspan="3"></td></tr>')

    # ---- headlines ----
    gb0 = group_by[0] if group_by else "company"
    gb1 = group_by[1] if len(group_by) > 1 else "period"
    # Analytical headlines come from the shared per-key narrative builder, so the HTML and the
    # Excel Dashboard show identical wording over the same numbers. The controls line is
    # HTML-specific (the workbook evaluates its controls as live formulas instead).
    headlines = list(_build_narrative_perkey(rows, config))
    ok_ct = sum(1 for c in ctrls if c[3])
    headlines.append(f"All {ok_ct} of {len(ctrls)} controls currently read OK." if ok_ct == len(ctrls)
                     else f"{ok_ct} of {len(ctrls)} controls read OK — resolve the exceptions before sign-off.")
    head_html = "".join(f"<li>{e(h)}</li>" for h in headlines)

    companies = sorted({str(r["company"]) for r in rows if r["company"] != ""})
    periods = sorted({str(r["period"]) for r in rows if r["period"] != ""})
    # Build the sub-header from escaped pieces so user-derived labels/values can't inject markup.
    esc_comp = " and ".join(e(c) for c in companies)
    esc_per = " and ".join(e(p) for p in periods)
    sub = (f"{e(la)} vs {e(lb)} &nbsp;|&nbsp; {e(gb0)} " + esc_comp +
           f" &nbsp;|&nbsp; {e(gb1)} " + esc_per +
           f" &nbsp;|&nbsp; Difference = {e(la)} less {e(lb)}" +
           (f" &nbsp;|&nbsp; Source: {e(src_name)}" if src_name else ""))

    return _HTML_TEMPLATE.format(
        title=e(f"{la} vs {lb} Reconciliation Dashboard"),
        h1=e(f"{la} vs {lb} Reconciliation Dashboard"),
        sub=sub,
        ctrl=ctrl_html,
        k_total=total, k_rec=reconciled, k_rate=f"{rate:.1f}", k_open=opn,
        k_net=_num(net), k_net_cls=("value neg" if net < 0 else "value"),
        k_gross=_num(gross),
        type_body=type_body, root_body=root_body,
        la=e(la), lb=e(lb), acct_body=acct_body, cp_body=cp_body,
        acct_hdr=e(acct_hdr), name_hdr=e(name_hdr), comp_hdr=e(comp_hdr), per_hdr=e(per_hdr),
        cp_title=e(f"Difference by {comp_hdr.lower()} and {per_hdr.lower()}"),
        open_ct=opn, det_body=det_body, rec_ct=reconciled,
        head=head_html,
        footer=(f"Prepared from {e(src_name)}. " if src_name else "") + "Companion workbook with live formulas accompanies this dashboard.",
    )


def write_html_report(rows, config, out_path, src_name=None, df_a=None, df_b=None):
    html = build_html_dashboard(rows, config, src_name, df_a=df_a, df_b=df_b)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{title}</title>
<style>
:root{{
  --bg:#f3f6fa; --surface:#ffffff; --ink:#1e2430; --muted:#5c6675;
  --line:#dae2ec; --rule:#e3eaf3;
  --brand:#2e5c8a; --brand-2:#5b9bd5; --brand-tint:#eaf1f8; --brand-band:#f2f7fc;
  --open-bg:#f7e3e1; --open-ink:#8c1d18;
  --rec-bg:#eaf1f8; --rec-ink:#1f3864;
  --neg:#b3261e; --radius:10px;
}}
@media (prefers-color-scheme: dark){{
  :root{{
    --bg:#11151b; --surface:#1a202a; --ink:#e7ecf4; --muted:#a2acbc;
    --line:#2b3340; --rule:#232b36;
    --brand:#7fb0e0; --brand-2:#4a7fb5; --brand-tint:#1d2836; --brand-band:#171e28;
    --open-bg:#3a201e; --open-ink:#f0a9a3; --rec-bg:#1d2a3c; --rec-ink:#9dc0e8; --neg:#ff8a80;
  }}
}}
*{{box-sizing:border-box;}}
body{{margin:0; padding:28px 22px 52px; background:var(--bg); color:var(--ink);
  font-family:Arial,"Segoe UI",Helvetica,sans-serif; font-size:14.5px; line-height:1.5;}}
.wrap{{max-width:1180px; margin-inline:auto;}}
header.page-head{{margin-block-end:24px;}}
h1{{font-size:1.7rem; margin:0 0 4px; color:var(--brand); letter-spacing:-.2px;}}
.sub{{color:var(--muted); font-size:.86rem; margin:0 0 12px;}}
.accent{{height:5px; background:var(--brand-2); border-radius:3px;}}
h2{{font-size:.95rem; text-transform:uppercase; letter-spacing:.7px; color:var(--brand); margin:30px 0 10px;}}
section{{break-inside:avoid;}}
.card{{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:16px 18px;}}
.grid2{{display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:16px;}}
.input-row{{display:flex; align-items:center; gap:12px; flex-wrap:wrap;}}
.input-row .label{{font-weight:bold;}}
.input-row .val{{font-weight:bold; color:#0000ff; background:var(--brand-tint);
  border:1px solid var(--brand-2); border-radius:5px; padding:3px 12px; font-variant-numeric:tabular-nums;}}
@media (prefers-color-scheme: dark){{ .input-row .val{{color:#8fb8ff;}} }}
.input-row .note{{color:var(--muted); font-size:.82rem; font-style:italic;}}
.kpis{{display:grid; grid-template-columns:repeat(auto-fit,minmax(165px,1fr)); gap:12px;}}
.kpi{{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:12px 14px;}}
.kpi .label{{font-size:.74rem; text-transform:uppercase; letter-spacing:.5px; color:var(--muted);}}
.kpi .value{{font-size:1.5rem; font-weight:bold; margin-block-start:3px; font-variant-numeric:tabular-nums;}}
.kpi .foot{{font-size:.76rem; color:var(--muted);}}
.value.neg{{color:var(--neg);}}
table{{width:100%; border-collapse:collapse; font-size:.85rem;}}
th,td{{padding:7px 9px; text-align:start; border-block-end:1px solid var(--rule);}}
th{{background:var(--brand); color:#fff; font-weight:bold; font-size:.75rem; text-transform:uppercase; letter-spacing:.4px;}}
td.num,th.num{{text-align:end; font-variant-numeric:tabular-nums;}}
tbody tr:nth-child(odd){{background:var(--brand-band);}}
tr.total td{{font-weight:bold; background:transparent; border-block-start:2px solid var(--brand); border-block-end:2px solid var(--brand);}}
.neg{{color:var(--neg);}}
.tag{{display:inline-block; padding:2px 9px; border-radius:4px; font-size:.75rem; white-space:nowrap;}}
.tag-open{{background:var(--open-bg); color:var(--open-ink);}}
.tag-rec{{background:var(--rec-bg); color:var(--rec-ink);}}
.ok{{background:var(--rec-bg); color:var(--rec-ink); font-weight:bold; padding:2px 9px; border-radius:4px;}}
.check{{background:var(--open-bg); color:var(--open-ink); font-weight:bold; padding:2px 9px; border-radius:4px;}}
.bar-cell{{position:relative;}}
.bar{{display:block; height:4px; background:var(--brand-2); border-radius:2px; margin-block-start:3px; margin-inline-start:auto;}}
.notes dt{{font-weight:bold; margin-block-start:8px;}}
.notes dd{{margin:0; color:var(--muted); font-size:.86rem;}}
.headlines{{margin:0; padding-inline-start:18px;}}
.headlines li{{margin-block-end:5px;}}
footer{{margin-block-start:30px; padding-block-start:10px; border-block-start:1px solid var(--line); font-size:.78rem; color:var(--muted);}}
@media print{{
  body{{background:#fff; padding:0; font-size:10.5pt;}}
  .card,.kpi{{border-color:#ccc;}} h2{{margin-block-start:16px;}}
  thead{{display:table-header-group;}}
  tbody tr:nth-child(odd){{background:#f4f7fb !important; -webkit-print-color-adjust:exact; print-color-adjust:exact;}}
  th{{background:#2e5c8a !important; -webkit-print-color-adjust:exact; print-color-adjust:exact;}}
}}
</style>
</head>
<body>
<div class="wrap">
<header class="page-head">
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>
  <div class="accent"></div>
</header>

<section><div class="card input-row">
  <span class="label">Reconciliation basis</span>
  <span class="val">{la} less {lb}</span>
  <span class="note">Every matching key present in either ledger is compared once; differences are classified below.</span>
</div></section>

<section>
  <h2>Control panel — every control must read OK before sign-off</h2>
  <div class="card"><table>
    <thead><tr><th>Control</th><th class="num">Result</th><th class="num">Expected</th><th>Status</th></tr></thead>
    <tbody>{ctrl}</tbody>
  </table></div>
</section>

<section>
  <h2>Reconciliation summary</h2>
  <div class="kpis">
    <div class="kpi"><div class="label">Total lines</div><div class="value">{k_total}</div><div class="foot">Unique matching keys</div></div>
    <div class="kpi"><div class="label">Reconciled</div><div class="value">{k_rec}</div><div class="foot">{k_rate}% match rate</div></div>
    <div class="kpi"><div class="label">Open items</div><div class="value">{k_open}</div><div class="foot">Require follow-up</div></div>
    <div class="kpi"><div class="label">Net difference</div><div class="{k_net_cls}">{k_net}</div><div class="foot">{la} less {lb}</div></div>
    <div class="kpi"><div class="label">Gross, ignoring sign</div><div class="value">{k_gross}</div><div class="foot">Sum of absolute differences</div></div>
  </div>
</section>

<div class="grid2">
  <section><h2>Open items by difference type</h2><div class="card"><table>
    <thead><tr><th>Difference type</th><th class="num">Count</th><th class="num">Value, ignoring sign</th></tr></thead>
    <tbody>{type_body}</tbody></table></div></section>
  <section><h2>Open items by root cause</h2><div class="card"><table>
    <thead><tr><th>Root cause</th><th class="num">Count</th><th class="num">Value, ignoring sign</th></tr></thead>
    <tbody>{root_body}</tbody></table></div></section>
</div>

<section>
  <h2>Difference by account</h2>
  <div class="card"><table>
    <thead><tr><th>{acct_hdr}</th><th>{name_hdr}</th><th class="num">Amount — {la}</th><th class="num">Amount — {lb}</th><th class="num">Difference</th></tr></thead>
    <tbody>{acct_body}</tbody></table></div>
</section>

<section>
  <h2>{cp_title}</h2>
  <div class="card"><table>
    <thead><tr><th>{comp_hdr}</th><th>{per_hdr}</th><th class="num">Amount — {la}</th><th class="num">Amount — {lb}</th><th class="num">Difference</th><th class="num">Open items</th></tr></thead>
    <tbody>{cp_body}</tbody></table></div>
</section>

<section>
  <h2>Reconciliation detail — {open_ct} open items</h2>
  <div class="card"><table>
    <thead><tr><th>{comp_hdr}</th><th>{acct_hdr}</th><th>{name_hdr}</th><th>{per_hdr}</th><th class="num">Amount — {la}</th><th class="num">Amount — {lb}</th><th class="num">Difference</th><th>Status</th><th>Difference Type</th><th>Root Cause</th></tr></thead>
    <tbody>{det_body}</tbody></table>
    <p class="sub" style="margin:10px 0 0">The remaining {rec_ct} lines are <span class="tag tag-rec">Reconciled</span> and are listed in full on the Reconciliation tab of the workbook.</p>
  </div>
</section>

<section><h2>Headlines</h2><div class="card"><ul class="headlines">{head}</ul></div></section>

<footer>{footer}</footer>
</div>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="Config-driven two-source reconciliation.")
    p.add_argument("--config", required=True)
    p.add_argument("--source-a", required=True)
    p.add_argument("--source-b", required=True)
    p.add_argument("--sheet-a", default=None, help="Sheet name/index for source A (for workbook tabs)")
    p.add_argument("--sheet-b", default=None, help="Sheet name/index for source B (for workbook tabs)")
    p.add_argument("--out", default="reconciliation.xlsx")
    p.add_argument("--html", default=None,
                   help="Also write the styled HTML dashboard to this path (or set output.emitHtml in config).")
    args = p.parse_args()
    import os

    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    # Resolve sheet selectors: CLI overrides config; config `sheet` under each source is honored.
    sheet_a = args.sheet_a if args.sheet_a is not None else config["sources"]["a"].get("sheet")
    sheet_b = args.sheet_b if args.sheet_b is not None else config["sources"]["b"].get("sheet")
    # A digit-only selector (e.g. --sheet-a 0) is a sheet index, not a sheet literally named "0".
    def _parse_sheet(s):
        if isinstance(s, str) and s.strip().lstrip("-").isdigit():
            return int(s.strip())
        return s
    sheet_a, sheet_b = _parse_sheet(sheet_a), _parse_sheet(sheet_b)

    df_a = load_table(args.source_a, sheet_a)
    df_b = load_table(args.source_b, sheet_b)

    # Fill in human labels from file/tab names when the config didn't set an explicit label.
    # This is what keeps the report free of generic "A"/"B" wording.
    if not config["sources"]["a"].get("label"):
        config["sources"]["a"]["label"] = default_label(args.source_a, sheet_a)
    if not config["sources"]["b"].get("label"):
        config["sources"]["b"]["label"] = default_label(args.source_b, sheet_b)
    # If both sources are the same file reconciled across two tabs, make sure the labels
    # are distinct by including the sheet name.
    if (args.source_a == args.source_b and sheet_a is not None and sheet_b is not None
            and config["sources"]["a"]["label"] == config["sources"]["b"]["label"]):
        config["sources"]["a"]["label"] = default_label(args.source_a, sheet_a)
        config["sources"]["b"]["label"] = default_label(args.source_b, sheet_b)

    # Align B's key columns to A's per matching.keyMap so differently-named keys reconcile.
    align_key_columns(config)

    la = config["sources"]["a"]["label"]
    lb = config["sources"]["b"]["label"]

    # Dispatch on reconciliation mode. Record-to-record (default) runs the tiered matcher; the
    # control-total mode proves the detail sums to a control figure (SKILL.md Step 3b) and is now
    # produced by the script rather than refused.
    mode = config.get("matching", {}).get("reconciliationMode", "recordToRecord")
    control_modes = {"controltotal", "control-total", "controltotaltieout"}
    if isinstance(mode, str) and mode.strip().lower() in control_modes:
        # Currency safety applies to every mode.
        try:
            check_currency(df_a, df_b, config)
            ct_result = control_total_tieout(df_a, df_b, config)
        except ValueError as e:
            sys.exit(f"Control-total tie-out failed: {e}")
        write_control_total_report(ct_result, config, args.out)
        print(f"Control-total tie-out written to {args.out}")
        print(f"Control ({ct_result['control_label']}) = {ct_result['control_total']:.2f} | "
              f"Detail ({ct_result['detail_label']}) = {ct_result['detail_total']:.2f} | "
              f"variance = {ct_result['variance']:.2f}")
        print(f"Tied out: {'YES' if ct_result['tied_out'] else 'NO'}")
        tot_missing = ct_result.get("missing_control", 0) + ct_result.get("missing_detail", 0)
        if tot_missing:
            print(f"  WARNING: {tot_missing} blank/unparseable amount row(s) - tie-out not trustworthy until resolved")
        if ct_result["grouped"]:
            not_tied = [r for r in ct_result["rows"] if not r["tied"]]
            print(f"  Control groups: {len(ct_result['rows'])} ({len(not_tied)} not tied)")
            if ct_result["orphans_detail"]:
                print(f"  Detail groups with no control: {len(ct_result['orphans_detail'])}")
            if ct_result["orphans_control"]:
                print(f"  Control groups with no detail: {len(ct_result['orphans_control'])}")
        return
    if mode and mode != "recordToRecord":
        sys.exit(f"reconciliationMode '{mode}' is not recognized. Use 'recordToRecord' for the "
                 "tiered line-by-line match, or a control-total mode "
                 "('controlTotal') to prove a detail list sums to a control figure.")

    # Confirm configured columns exist before matching (keys, amount, and any optional date or
    # currency column - a misspelled dateColumn would otherwise make the similarity tier silently
    # skip candidates instead of matching, and a misspelled currencyColumn would skip the guard).
    for side, df in (("a", df_a), ("b", df_b)):
        s = config["sources"][side]
        needed = list(s["keyColumns"]) + [s["amountColumn"]]
        for opt in ("dateColumn", "currencyColumn"):
            if s.get(opt):
                needed.append(s[opt])
        missing = [c for c in needed if c not in df.columns]
        if missing:
            sys.exit(f"Source '{s['label']}' is missing configured column(s): {missing}. "
                     f"Available: {list(df.columns)}")

    # Currency safety: never reconcile across currencies (SKILL.md Step 2). Refuse with a clear
    # message rather than netting incomparable amounts.
    try:
        check_currency(df_a, df_b, config)
    except ValueError as e:
        sys.exit(f"Currency check failed: {e}")

    results, total_a, total_b = reconcile(df_a, df_b, config)
    summary = tie_out(results, total_a, total_b, effective_tolerances(config["matching"])[0])
    counts = write_report(results, config, args.out, df_a=df_a, df_b=df_b,
                          src_name=os.path.basename(args.source_a))

    print(f"Reconciliation written to {args.out}")

    # Optional HTML dashboard (same data, styled template). Driven by --html or output.emitHtml.
    html_path = args.html
    if html_path is None and config.get("output", {}).get("emitHtml"):
        html_path = os.path.splitext(args.out)[0] + ".html"
    if html_path:
        rows, _, _ = compute_reconciliation(df_a, df_b, config)
        write_html_report(rows, config, html_path, src_name=os.path.basename(args.source_a),
                          df_a=df_a, df_b=df_b)
        print(f"HTML dashboard written to {html_path}")

    print(f"Control total {la} = {total_a:.2f} | {lb} = {total_b:.2f} | net = {summary['net_difference']:.2f}")
    print(f"Tied out: {'YES' if summary['tied_out'] else 'NO (residual %.2f)' % summary['residual']}")
    for status, n in counts.items():
        print(f"  {status}: {n}")


if __name__ == "__main__":
    main()
