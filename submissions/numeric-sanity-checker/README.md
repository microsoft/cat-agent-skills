# Numeric Sanity Checker

Catches the three arithmetic mistakes that show up constantly in generated
reports: a budget breakdown whose parts don't actually sum to the stated
total, a percentage distribution that doesn't sum to 100, and a percent-change
figure that's actually just the point difference between two percentages
mislabeled as a percent change.

## How it works

`scripts/check_numbers.py` takes a small JSON list of checks and verifies
each one exactly: sum a list of parts against a claimed total, sum a list of
percentages against an expected whole, or recompute a percent-change figure
from its two source values. Rounding tolerance is built in so normal
report-rounding doesn't get flagged as an error.

## Usage

```bash
python scripts/check_numbers.py checks.json
echo '[{"type": "sum", "parts": [10,20,30], "claimed_total": 61}]' | python scripts/check_numbers.py -
```

No dependencies beyond the Python standard library.

## Why percent change specifically

Going from 20% to 25% is a 5 percentage-point increase, but a 25% relative
increase, and mixing the two up is one of the most common numeric errors in
generated business writing. This skill's checker computes the actual formula,
`(new - old) / old * 100`, and flags a claimed figure that doesn't match it.

## Limits

This verifies arithmetic consistency between numbers already given, not
whether the underlying source numbers are correct. Garbage inputs that are
internally consistent will still pass.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
