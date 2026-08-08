---
name: numeric-sanity-checker
description: >-
  Use this skill before presenting any report, summary, or answer containing
  calculated numbers, such as subtotals that should add to a total,
  percentages that should sum to 100, or a stated percent change between two
  figures, to catch arithmetic errors before they ship.
---

Verify the arithmetic actually holds before presenting numbers as correct.

## Instructions

1. This applies whenever a response includes: parts that are claimed to sum
   to a total (a budget breakdown, a category split), percentages that are
   claimed to sum to a whole (a distribution, a survey breakdown), or a
   percent-change figure derived from two values (growth, decline, a
   before/after comparison).

2. Before presenting the numbers, run the bundled checker when a Python
   environment is available:

   ```bash
   python scripts/check_numbers.py checks.json
   ```

   where `checks.json` is a list of check objects, one of:

   ```json
   {"type": "sum", "parts": [10, 20, 30], "claimed_total": 61}
   {"type": "percentages", "values": [40, 35, 26], "expected_total": 100}
   {"type": "percent_change", "old": 80, "new": 100, "claimed_pct": 20}
   ```

   It also reads from stdin. Without Python available, do the same three
   checks by hand: add the parts, add the percentages, and recompute percent
   change as `(new - old) / old * 100`, not the raw point difference between
   two percentages.

3. If a check fails, don't just flag it. Recompute the correct value and fix
   the number before presenting it, or if the discrepancy might mean the
   underlying data (not the arithmetic) is wrong, say so and ask rather than
   silently substituting a number.

4. A very common specific mistake worth naming: percent change is not the
   same as the point difference between two percentages. Going from 20% to
   25% is a 5 percentage-point increase, but a 25% relative increase. State
   which one is actually meant, and compute the one that's stated.

5. Rounding is expected and not itself an error. Percentages that sum to
   99.9 or 100.1 due to rounding are fine; the checker's default tolerance
   accounts for that. A sum that's off by a meaningful amount is the actual
   target.

## Guardrails

- Never present a subtotal, percentage breakdown, or percent-change figure
  without having verified the arithmetic, either through the script or by
  hand.
- Never silently adjust the underlying numbers to make the arithmetic work.
  If parts don't sum to a stated total, either the parts, the total, or one
  input is wrong; say which, don't quietly fudge one number to force
  agreement.
- Don't apply this as a broad fact-checking pass. It verifies arithmetic
  consistency between numbers already given, not whether the source numbers
  themselves are accurate.

## Tone

Quick and matter-of-fact. Fix the number and move on; no need to narrate a
successful check, only a failed one.
