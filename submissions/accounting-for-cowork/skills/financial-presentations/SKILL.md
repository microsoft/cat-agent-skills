---
name: financial-presentations
description: "Structures accounting presentations that turn detailed data into a clear, decision-ready narrative. Supports quarterly financial reviews, monthly close summaries, strategic budget reviews, AP/AR process documentation, department workload updates, reconciliation-review packs, variance and aging analyses, and audit or transaction-support decks. Builds an executive summary, logical storyline, concise commentary, useful charts or bridges, supporting appendix views, decisions required, owners, and next actions. Use for any accounting or finance slide deliverable, including board, leadership, quarterly review, planning, close-status, process, investment, audit, or team-meeting presentations."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'SlideText'
  argument-hint: '<deck-type> [period]'
---

# Financial Report

**Important**: This skill assists with structuring finance presentations but does not provide financial advice. All financial content should be reviewed by qualified financial professionals before distribution.

Deck structures, slide-by-slide guidance, and formatting principles for the core finance presentation deliverables: quarterly / board financial-review decks, investment-committee and deal recommendation decks, AP/AR process-documentation decks, and department meeting decks. **Whenever a finance deliverable is a slide deck (.pptx), read this skill first** — before building slides — and apply the finance-specific discipline below, not just generic slide craft.

This skill covers presentation *structure and assembly*. The analytical content comes from the work behind the deck: statements and key metrics from `financial-statements`, reconciliation status from `reconciliation`, and variance narratives, waterfalls and close status from the variance analysis and close tracker the user provides. Do not recompute analysis here — pull it in and format it for an audience.

**Read [Financial Reporting Standards](references/financial-reporting-standards.md) before you build**: the deck's figures follow its reporting conventions, and any workbook behind the deck goes through its checklist.

## General Slide Principles for Finance Decks

1. **One message per slide.** The slide title states the takeaway ("OpEx grew 8%, driven by headcount"), not the topic ("OpEx Analysis").
2. **Lead with the conclusion.** Executives read slide 1-2 and skim the rest. The executive summary must stand alone.
3. **Numbers need comparisons.** Never show a figure without its reference point — budget, prior period, or prior year.
4. **Color discipline.** Favorable = green, unfavorable = red, consistently. Don't decorate; signal.
5. **Tables for lookup, charts for trends.** A 12-month trend is a line chart; a 5-item variance ranking is a table or waterfall.
6. **Push detail to appendix.** Anything needed only if someone asks goes in back-up slides, not the main flow.
7. **End every deck with actions.** Decisions needed, owners, and dates — a deck that ends in data leaves the meeting without outcomes.

## Finance-Specific Discipline

Generic slide craft (above) is necessary but not sufficient. These are the disciplines that separate a *finance* deck from a merely good-looking one — and the ones a reviewer will fail you on:

1. **Every number ties to a source.** Each figure must trace to the underlying workpaper, model, or filing — the deck must not introduce numbers that don't reconcile to the analysis it summarizes. Where a slide mixes reported and modeled figures, mark which are **disclosed** (from the financials/filing, with source) vs **derived** (estimated/analyst-built, with basis). A number on a slide that doesn't tie to the workpaper is the deck equivalent of a plug.
2. **Every variance carries its driver *and* its implication.** Don't stop at "OpEx +8%." State the driver ("driven by 12 net new hires") and the forward implication ("annualizes to +$4M; continuing, not one-time"). A variance without a cause and an outlook is a data point, not analysis.
3. **Allocate slide space by materiality.** Rank items by size; the main flow goes to the material ones — a $2K variance does not earn the same slide as a $2M one. Immaterial detail goes to the appendix. Reuse the materiality thresholds the reconciliation/variance workpapers already applied; don't invent new ones for the deck.

### Choosing the finance chart

| Message | Chart |
|---------|-------|
| Budget→actual or PY→CY bridge | **Waterfall** (start, +/− drivers, end) |
| Trend over time (revenue, margin %) | **Line** (6–8 periods) |
| Ranked variances / contributions | **Horizontal bars**, favorable green / unfavorable red |
| Segment / entity comparison over time | **Small multiples** (shared axis, one panel per segment) |
| Sensitivity / risk range | **Tornado** (drivers ranked by swing) |
| Composition at a point | **Stacked / 100% bar** (avoid pie beyond ~4 slices) |

### Before you finish — reviewer self-check

- [ ] Every slide title states a takeaway, not a topic.
- [ ] Every number has a comparison (budget / prior period / prior year) **and** a traceable source.
- [ ] Disclosed vs. derived figures are distinguished wherever they mix.
- [ ] Each material variance names its driver and its forward implication.
- [ ] Charts match their message (bridge = waterfall, trend = line, sensitivity = tornado).
- [ ] Immaterial detail is in the appendix, not the main flow.
- [ ] The deck ends in decisions/actions with owners and dates — or, for a board/IC deck, *opens* with the ask.
- [ ] Status / testing / aging data presented on a slide sits in a **native table object** — reviewers extract tables programmatically; text boxes and shape grids don't count — sliced to exactly the scope requested (e.g., the current phase only, other phases separated out).
- [ ] Count sets are stated completely and explicitly — tested, passed, failed, **and** deficiencies — even when one is derivable from the others; every in-scope area with no rows in the source data is named as having none, and unquantified impacts are called out as unquantified. **Completeness applies within the requested scope only**: data from phases or periods the request excludes stays out of every slide and total, even "for context".
- [ ] Margins and segment figures state their **measurement basis**: whether one-time / non-recurring items are included or excluded, and any allocation-methodology caveat (e.g., revenue by customer-address geography vs. by operating segment); the deck closes by translating the numbers into the decision they support (capital-allocation or investment takeaway), with each segment covered in depth proportional to its size and role.
- [ ] An explicitly requested slide count or deliverable set is met exactly — a 10–12-slide ask gets 10–12 slides, one .pptx and nothing else unless another file is requested.
- [ ] Analytical slides state the **exact figures from the source tracker** — counts, rates, severity mixes, statuses, and target dates lifted from the rows, never qualitative paraphrase ("92.6% pass rate; 150 passed / 12 failed", not "most controls passed") — with per-group observation tables built one row per process/team/account from the tracker, and the source file cited by name on the slide or in source notes.
- [ ] An engagement / proposal deck includes the client's specific offerings and services (from the provided materials or verifiable public information, named specifically) and a fee section with the retainer/fee structure, at least one alternative fee option, and the stated rationale for the recommended one.
- [ ] A meeting invite or opener slide states the date **with its computed weekday** (verify the calendar — don't guess), an explicit time zone, the named attendees from the source roster, and the presenter/organizer. Use the concrete location or virtual join + dial-in from the source. If the source omits those details, ask the user; if clarification is unavailable, mark the location or join information as missing and requiring confirmation rather than inventing it or writing "TBD".

## Investment-Committee / Board / Deal Deck

A decision-forcing deck: recommend a capital allocation, investment, or transaction and secure an explicit approval. Unlike a review deck, it must **open and close with a specific ask**, not end in data.

### Deck Structure (8–14 slides)

| # | Slide | Content |
|---|-------|---------|
| 1 | Title | Proposal, sponsor, date, decision requested |
| 2 | Recommendation & the ask | The recommendation in one line, the specific approval/decision sought, and the amount — up front |
| 3 | Thesis | Why this, why now: the 2–3 reasons the proposal creates value |
| 4 | Financials | Historical + projected P&L / cash flows for the target or project, key assumptions stated on the slide |
| 5 | Valuation | Basis (DCF / trading multiples / precedents), resulting value or range, price vs. value |
| 6 | Returns | IRR, MOIC, payback, NPV — each against the hurdle rate; base case explicitly labeled |
| 7 | Sensitivities | Returns under downside / base / upside; the 2–3 variables that swing the outcome (tornado) |
| 8 | Risks & mitigants | Key risks, each with likelihood, impact, and a named mitigation/owner |
| 9 | Structure & terms | Deal / financing structure, key terms, conditions precedent |
| 10 | Alternatives considered | What else was evaluated and why this option wins |
| 11 | Decision & next steps | The ask restated, approvals needed, timeline, owners |
| 12+ | Appendix | Full model, diligence detail, comparable transactions |

**Rules:** state the ask on slide 2 (not slide 12); every projection names its assumptions; returns are always shown against the hurdle rate; and the base case is labeled so the committee doesn't read the upside as the plan.

## Quarterly Financial Review Deck

A leadership-facing deck summarizing quarter performance: results, variances, trends, and the discussion points that need leadership attention.

### Deck Structure (10-14 slides)

| # | Slide | Content | Source |
|---|-------|---------|--------|
| 1 | Title | Period, audience, date, presenter | — |
| 2 | Executive summary | 4-6 bullets: headline results vs budget/prior quarter, the one or two stories of the quarter, key actions needed | All sections |
| 3 | Financial scorecard | Table: revenue, gross margin, operating income, net income, cash — actual vs budget vs prior quarter with variance flags | `financial-statements` key metrics |
| 4 | P&L bridge | Waterfall from budget (or prior quarter) operating income to actual, 5-8 drivers | Variance analysis (waterfall) |
| 5-6 | Variance deep-dives | One slide per major variance: quantified driver decomposition + narrative + outlook (one-time vs continuing) | Variance analysis (narratives) |
| 7 | Revenue and margin trends | 6-8 quarter trend charts: revenue, gross margin %, operating margin % | `financial-statements` |
| 8 | Balance sheet highlights | Key balance movements: AR/DSO, AP/DPO, inventory, debt; working capital commentary | `financial-statements`, `reconciliation` aging |
| 9 | Cash flow commentary | Operating/investing/financing summary; free cash flow vs plan; cash runway if relevant | `financial-statements` cash flow |
| 10 | KPI trends | Business-specific KPIs with targets (pick 4-6, consistent quarter to quarter) | Org-specific |
| 11 | Risks and opportunities | Two columns: quantified downside risks and upside opportunities for next quarter, each with likelihood and owner | Management input |
| 12 | Management discussion points / actions | Decisions needed from leadership, each framed as a question with a recommendation | All sections |
| 13+ | Appendix | Full statements, detailed variance tables, reconciliation detail | Back-up |

### Management Discussion Point Prompts

For each financial area, the discussion points that typically warrant a slide bullet:

- **Revenue:** pipeline coverage for next quarter's target; pricing pressure observed; customer concentration changes
- **Margin:** input cost trends; mix shift between high/low margin lines; one-time items distorting the run rate
- **OpEx:** hiring pace vs plan; discretionary spend trajectory; commitments that step up next quarter
- **Working capital:** collections health (DSO trend); payment term changes; inventory build risk
- **Cash:** runway and covenant headroom; capex timing; financing needs on the horizon

## AP/AR Process Documentation Deck

A reference deck mapping the end-to-end accounts payable and accounts receivable workflows — stages, roles, systems, controls, and exception paths.

### Deck Structure (8-12 slides)

| # | Slide | Content |
|---|-------|---------|
| 1 | Title and purpose | What process, current as-of date, owner |
| 2 | Process overview | Both workflows on one page as high-level stage chains (see below) |
| 3-5 | AP workflow detail | One slide per phase group with swimlanes |
| 6-8 | AR workflow detail | One slide per phase group with swimlanes |
| 9 | Key controls summary | Control points mapped to process stages |
| 10 | Exception handling and escalation | Common failure points and their resolution paths |
| 11 | Systems and handoffs | Which system owns each stage; manual handoff points |
| 12 | Contacts and ownership | Role-to-stage responsibility matrix |

### AP Workflow Stages

```
Intake → Validation → Coding → Approval → Posting → Payment → Reconciliation
```

| Stage | Activities | Typical Role | Key Control |
|-------|-----------|--------------|-------------|
| Intake | Invoice receipt (email/EDI/portal), capture, indexing | AP clerk | All invoices logged with unique ID |
| Validation | Three-way match (PO, receipt, invoice); duplicate check | AP clerk / system | Match tolerance; duplicate detection |
| Coding | GL account, cost center, project assignment | AP clerk + requester | Coding review for non-PO invoices |
| Approval | Routing per authorization matrix | Budget owner | Approval limits enforced by system |
| Posting | Entry to AP subledger and GL | AP / system | Batch control totals |
| Payment | Payment run, method selection, remittance | Treasury / AP manager | Segregation: approver ≠ payer; positive pay |
| Reconciliation | AP subledger to GL; vendor statement recs | Accountant | Monthly reconciliation sign-off |

**Common failure points to call out:** invoices received outside the intake channel (lost), match exceptions aging without an owner, coding defaults applied incorrectly, duplicate payments from re-sent invoices, and approvals stuck with absent approvers.

### AR Workflow Stages

```
Order/Contract → Invoicing → Delivery → Collections → Cash Application → Reconciliation
```

| Stage | Activities | Typical Role | Key Control |
|-------|-----------|--------------|-------------|
| Order/Contract | Credit check, terms setup, order entry | Sales ops / credit | Credit limit enforcement |
| Invoicing | Invoice generation per contract/delivery terms | Billing | Pricing to contract; invoice completeness |
| Delivery | Performance/delivery evidence captured | Operations | Delivery confirmation before recognition |
| Collections | Dunning cadence, aging follow-up, dispute logging | Collections | Aging review; escalation thresholds |
| Cash Application | Match receipts to invoices; resolve unapplied cash | AR clerk | Unapplied cash aging; same-day application |
| Reconciliation | AR subledger to GL; reserve assessment | Accountant | Monthly reconciliation; allowance review |

**Common failure points to call out:** invoices issued before delivery evidence, disputes not logged (aging silently), unapplied cash masking true aging, and credit memos issued without approval.

### Swimlane Slide Guidance

- One lane per role (requester, AP/AR clerk, approver, treasury, system) — maximum 5 lanes per slide
- Flow left to right; decision diamonds only where the path genuinely branches (match exception, approval rejection, dispute)
- Mark control points with a distinct shield/check marker and number them; the controls summary slide indexes those numbers
- Mark system boundaries (ERP, banking portal, billing system) so manual handoffs are visible — handoffs are where processes break
- One phase group per slide; never compress an entire end-to-end flow onto a single readable slide

## Department Meeting Deck

A recurring (weekly/monthly) team meeting deck reviewing workload, close status, and upcoming priorities.

### Deck Structure (5-7 slides)

| # | Slide | Content |
|---|-------|---------|
| 1 | Status dashboard | Work completed vs in progress vs blocked, as counts with trend vs last meeting |
| 2 | Close / cycle progress | Close status by day vs calendar (on track / at risk / late by task group), open exceptions count and $ |
| 3 | Open exceptions and blockers | Top items by risk: what, owner, age, what's needed to unblock |
| 4 | Upcoming deadlines | Next cycle's key dates: close milestones, filings, audits, deliverables — flag anything with a capacity conflict |
| 5 | Capacity and staffing | Workload distribution, PTO/absence coverage, capacity risks for the coming period |
| 6 | Decisions needed | Items requiring leadership/supervisor decision, each with a recommendation and a deadline for deciding |
| 7 | Actions and owners | Carry-forward action log: what, who, when |

### Content Guidance

1. **Use the close status tracker as the data source** — the dashboard slide is a rollup of the task-level close tracker, not a separate status collected by survey.
2. **Show trend, not just state.** "12 open exceptions (down from 19)" reads differently than "12 open exceptions."
3. **Frame blockers as asks.** Every blocker names what is needed and from whom — otherwise the slide is a complaint, not an agenda item.
4. **Deadlines get owners before the meeting ends.** The deadline slide pairs each deliverable with a named owner; unassigned deadlines are the first decision needed.
5. **Keep the decisions slide honest.** If nothing needs deciding, drop the slide — don't manufacture decisions to fill it.
6. **Reuse the skeleton.** Same slide order every meeting; the team should know where to look for what. Update content, not structure.
