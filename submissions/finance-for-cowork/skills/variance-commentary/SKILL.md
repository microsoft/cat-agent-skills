---
name: "variance-commentary"
description: >-
  Drafts crisp variance commentary for actuals versus plan, forecast, prior
  year, or prior quarter. Captures metric, segment, period, comparison basis,
  magnitude, and drivers, then produces a three-part block — headline, drivers,
  forward look — for each segment in scope, and searches recent email and chat
  for grounding when drivers aren't supplied. Use when the user asks to "write
  the variance commentary", "explain why we missed plan", "draft the actuals vs
  forecast narrative", "why is revenue up versus last year", or "write
  commentary for the variance slides". Do NOT use for computing the variance in
  a model (do the spreadsheet work first), general stakeholder emails, or
  forecast changes not tied to actuals.
metadata:
  icon: DocumentFlowchart
---

# Variance Commentary

Produces exec-ready variance narrative: short, fact-anchored blocks that drop straight into review
slides, a controller email, or board prep.

## When NOT to Use

- **Computing the variance or decomposing drivers in a model** → spreadsheet or BI work first
- **General stakeholder emails not anchored to a variance** → outside this skill's scope
- **Operational or headcount narratives** with no financial comparison → write directly
- **Forecast-change rationale** not tied to an actuals comparison → write directly

## Related Skills

Hand off rather than overlap:

- Prep for the review where the variance is presented — use forecast-review-prep instead.
- Anticipating questions on the variance — use stakeholder-qa-prep instead.
- Broad stakeholder messaging — outside this skill's scope.
- Recurring deliverables emails — use quarterly-workback instead.

## Workflow

### 1. Capture the inputs

From the user's message or recent context, establish:

- **Metric** — whatever the business actually tracks (revenue, bookings, margin, operating
  expense, cash, units, backlog)
- **Segment or business** — the reporting unit in scope
- **Period** — the fiscal period, in the user's own fiscal convention
- **Comparison basis** — versus plan, forecast, prior year, or prior quarter
- **Magnitude** — both the absolute variance and the percentage
- **Known drivers** — what the user already attributes it to

Ask only for what's genuinely missing, and ask once. Multiple segments in one request produce one
block per segment.

**Do not assume a fiscal calendar.** If the period is ambiguous ("Q3"), confirm the convention
rather than guessing between calendar and fiscal years.

### 2. Ground the drivers when thin

If the user supplied no drivers or only one, run `m365_search-SearchM365` with
`sources=["email","teams"]` on the metric, period, and segment over the last 30 days. Surface what
you find. **If search comes back empty, the block says "Driver TBD pending review" — never invent
a plausible cause.**

### 3. Draft the three-part block

- **Headline** — one line stating what happened, with the number and the comparison
- **Drivers** — 2-3 sub-bullets naming what moved it, with amounts where known
- **Forward look** — one line on the implication for next period or the risk to monitor

**Style rules (blocking):**

- Past tense for what happened, present for current state, future used sparingly
- No hedging — state the fact or flag the gap; "appears to" and "seems to" are banned
- Numbers with a consistent unit and one decimal; percentages to one decimal
- Never "significant" or "material" without a number attached
- Active voice with concrete verbs — landed, accelerated, slipped, recovered, decelerated

### 4. Roll up if multi-segment

With two or more blocks, offer to combine them into a single review-ready paragraph: one headline
summarizing the roll-up, drivers grouped, one forward look.

## Output Format

Inline markdown by default. **Never write a file unless the user asks for one** — this output is
usually pasted into something else.

## When Things Fail

- **Search returns nothing** — the block ships with "Driver TBD pending review". Never substitute a plausible cause.
- **The user's magnitude and the retrieved data disagree** — surface both and ask which is authoritative.
- **Period convention is ambiguous** — stop and confirm rather than assuming a calendar or fiscal year.
- **Only a percentage or only an absolute is available** — state the one you have and mark the other as not supplied; do not back-compute from an assumed base.
- **A tool errors** — retry once, then draft from what the user supplied and disclose the gap.

### Example output

```text
Headline
  Revenue landed at $42.1M, $1.8M / 4.5% above plan for the quarter.

Drivers
  - Enterprise renewals closed early, pulling ~$1.1M into the period
  - Services attach ran 210bps above plan on the same deal base
  - Partially offset by $0.4M of churn in the mid-market segment

Forward look
  The renewal pull-forward borrows from next quarter; treat the $1.1M as
  timing rather than run-rate when setting the Q4 baseline.
```

## Guardrails

- **Never invent a driver or a number.** Unknown drivers are written as "Driver TBD pending
  review." A fabricated cause in variance commentary propagates into board materials.
- **Flag variances that cross a materiality threshold** so the user can decide on escalation. Use
  the user's threshold if they have one; otherwise flag anything past 5% and say which threshold
  you applied.
- If retrieved context contradicts the user's stated driver, surface the contradiction rather than
  silently overriding or silently accepting it.
- Attribute outcomes to business drivers, never to individuals' performance.
- Never write a file or send anything without being asked; this output is normally pasted elsewhere.
- State the materiality threshold you applied whenever you flag or decline to flag a variance.
- Keep units and fiscal labels exactly as the user uses them — do not convert or relabel periods.
