# Reconciliation Standards

> Reference file of the `reconciliation` skill. Read it before you build any reconciliation or supporting workpaper, and finish with its "Final pass — re-verify the delivered file".

**Important**: This skill assists with finance workflows but does not provide financial advice. All workpapers should be reviewed by a qualified professional before sign-off.

These are **checks to apply to your own deliverable** — a few things that must be true whatever the reconciliation type (GL-to-subledger, bank, intercompany, lease, debt, trial-balance). They are *not* a template, a required tab structure, or a treatment to adopt. Build the deliverable the way the task calls for, then make sure it passes these. A simpler workpaper that reconciles and is sourced beats an elaborate one that doesn't; don't add structure or complexity the task didn't ask for.

## Workbook implementation before applying these checks

For an Excel workbook, load `xlsx` first if it is offered in this conversation, and prefer its workflow over improvised file manipulation. This skill supplies accounting methodology; it does not supply or replace workbook implementation and validation guidance. If `xlsx` is not offered, proceed with the workbook tools this conversation does provide.

## The checks

0. **It matches the requested structure exactly.** Before applying any other check, lock the required file count, tab count, exact names and order, and template layout. Do not add supplemental `Requirements`, `README`, cover, controls, source, notes, memo, index, dashboard, or copied-input tabs unless explicitly requested or already present. Keep verification artifacts internal. "Audit-ready" and "reusable" are quality standards, not permission to enlarge the deliverable.

1. **It reconciles within threshold, and shows the difference.** Compute the difference between the two sides with a live formula and show it. Conclude "reconciled" when that difference is within the materiality threshold set for the account — thresholds are tight for cash/bank and looser for estimate-heavy accounts (e.g., accruals); it does not have to be exactly zero. A difference over threshold, or any difference left unexplained, means the account is not reconciled.

2. **It ties to the official ledger.** Show the GL / control balance from the official books (the figure that ties to the ERP) next to your built-up detail, and show the difference between them — e.g., AP subledger 1,234 vs GL 1,232: show both and the $2 difference, reconciled under a $100 threshold. Don't present detail that only looks tidy on its own.

3. **Live formulas, never typed-in answers.** Totals computed by formula so the math is checkable and updates when inputs change. If a figure links to an external workbook, name that source workbook.

4. **Completeness — cover the whole population.** Work the entire dataset, not a sample or a convenient subset; if something is excluded, state exactly what and why.

5. **Accuracy — source every material figure, and fake none.** For each figure at or above the account's materiality threshold, mark it official (disclosed — with source and date) or estimated (derived — with basis). Never present a guess as disclosed; if the authoritative source wasn't provided, build a clearly-labeled estimate rather than leaving the page blank.

6. **Document inputs, methodology, exceptions, and conclusion.** A short reviewer note stating the source of the inputs, the methodology used, exceptions above threshold (or "none"), and a definitive conclusion (reconciled / reconciled with $X within threshold / not reconciled). Also: when reconciling related accounts together, cross-check that the relationship is reasonable (e.g., AR vs revenue given the payment terms) and flag anomalies; for each exception, propose the most-likely cause (a missing GL entry, a suspect subledger item, a timing difference); and use correct accounting terms and generally accepted abbreviations, citing accounting references or comparable peer disclosures where a methodology is developed. State any convention that drives the math in words next to the calculation — day-count (e.g. 30/360 vs actual/365), the current-vs-long-term split, effective-interest vs straight-line — and cite the governing guidance at paragraph level (e.g. ASC 835-30, ASC 842) beside the driving variable, not as a bare standard number in a header.

## Keep visible (however you lay it out)

- The tie: the difference computed by formula and visible on the face of the work.
- Provenance: a source / disclosed-vs-derived marker where figures mix sources.
- If — and only if — you build a rollforward, make it **period-by-period across the full horizon** — one row per period, each period's opening equal to the prior period's ending by formula (not a single YTD or annual line, unless a coarser view is what was asked for) — give each movement driver its own formula-driven column (additions, modifications/remeasurements, terminations/disposals, payments, amortization/depreciation), and tie both ends (opening to prior TB, closing to current TB). If the task specifies an exact layout, match it exactly instead.

## Final pass — re-verify the delivered file

The checks above are asserted against **what was actually produced**, not what you intended to build. After writing the file(s), re-open the delivered output and verify:

- **The structure lock passes first** — exact file count, tab count, names, order, and protected template layout match the request. Delete any unrequested scaffolding rather than defending it as useful or audit-ready.
- **Everything explicitly requested exists under its requested name** — every file (count and type), tab/sheet/slide, section, and column the request named. A consolidated substitute, a renamed tab, or requested files merged into one fails; "don't add unrequested structure" is never license to drop or rename structure the task *did* ask for (a consolidated view may be an extra tab, never a replacement). No headers-only tabs: every required schedule has populated data rows.
- **Every check/tie/difference cell recomputes and passes from the delivered cells** — per-tab and subsidiary checks included, not just the top-level tie. A residual bridged by a hardcoded balancing figure, an open-exceptions bucket, or an unsupported FX/"other" line is a plug, not a reconciliation. Never deliver a check cell reading "should be zero" beside a material non-zero value, an impossible figure (a negative current liability, a balance that never reaches its required endpoint), or any #REF/#NAME/#### error.
- **Rollforwards chain** — each period's opening equals the prior ending by formula and both ends tie (per "Keep visible").
- **Derived amounts and scope are honest** — each reconstructed balance is its own labeled line, and the reviewer note quantifies the total derived amount, the method, and a definitive verdict. When reconciling to a public filing, show related disclosed amounts *outside* the reconciled balance (e.g., commitments not yet commenced) as explicit scoped-out lines with their dollar amounts, and never mark a tie "Pass" against a line the filing does not separately present — state the presentation limitation instead.

Fix what fails and re-verify. If a difference genuinely cannot tie, conclude "not reconciled" with the most-likely cause — never paper over it — and make sure every assumption or open question you relied on is stated, naming the specific items (IDs, periods, amounts), in both the final reply and the deliverable itself.

## What this is NOT

It is not a template, and it does not tell you how to structure tabs or which accounting treatment to use — the type-specific mechanics live in this skill's `SKILL.md`, and you apply the treatment the task calls for. Don't impose a formal multi-tab structure, control-check scaffolding, or a prescribed treatment the task doesn't need; that overhead can leave a workpaper looking incomplete or apply the wrong method. Let your own correct approach stand — these checks only catch what it might miss.
