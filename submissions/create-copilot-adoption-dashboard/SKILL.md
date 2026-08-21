---
name: create-copilot-adoption-dashboard
description: |
  Turns the four Microsoft admin center (MAC) Copilot activity exports into a
  populated, single-file HTML adoption dashboard using the Copilot Adoption
  Analysis framework (Pillars A–E and the KPI scorecard). Triggered by the
  `create-copilot-adoption-dashboard` command. Use when the user asks to
  "create a Copilot adoption dashboard", "populate the adoption dashboard
  template", "build my MAC report dashboard", "generate a Copilot usage
  dashboard", "turn my Copilot exports into a dashboard", or "make an adoption
  at-a-glance report". It first explains the process, then collects a company
  name (required) and logo (optional) plus the four CSV exports (Copilot usage,
  Agents per-user, Agents per-agent, Copilot Chat), computes the real metrics,
  and replaces every template placeholder with the customer's data. Do NOT use
  for a plain HTML page or a one-off chart with no MAC data — use the html or
  render-ui skill instead. Do NOT use to query a Power BI report — use the
  powerbi skill instead.
cowork:
  category: analysis
  icon: DataBarVertical
---

## Overview

This skill builds a **Microsoft 365 Copilot adoption dashboard** by feeding four
MAC report exports through the *Copilot Adoption Analysis* framework and
injecting the computed results into a bundled single-file HTML template. The
output is one self-contained `.html` file (no libraries, no network) branded
with the customer's name and logo, carrying only real data — every template
placeholder, sample number, and template label is replaced. Every KPI tile and
panel carries an `i` definition button, the segment donut, Top surfaces and
Agent usage share charts reveal the underlying **user counts on hover**, and a
**Recommended next steps** section below the charts turns the measured values
into the framework's enablement plays — split into KPI-triggered plays and
ongoing training/awareness focus. The framework logic
(pillars, thresholds, KPI formulas, and the data contract) lives in
[references/adoption-framework.md](references/adoption-framework.md); the
computation and injection are done by
[scripts/build_dashboard.py](scripts/build_dashboard.py).

## When to Use

- The user wants their four Copilot MAC exports turned into a populated dashboard.
- The user runs the `create-copilot-adoption-dashboard` command.
- The user asks to populate or brand the adoption dashboard template with real data.

## When NOT to Use

- A generic HTML page, report, or single chart with no MAC data — use the **html** or **render-ui** skill instead.
- Reading numbers from a Power BI report or semantic model — use the **powerbi** skill instead.
- Summarizing a meeting or email thread — use **meeting-intel** or the Outlook tools instead.
- Evaluating individual users' performance — decline; this skill reports aggregate adoption only.

## Quick Start

```
User: /create-copilot-adoption-dashboard
1. Explain the process (below) and list the four reports needed.
2. Ask for company name (required) + logo (optional); find the 4 CSVs in input/.
3. Inspect each CSV's headers and map it to a report (--usage / --agents-user /
   --agents-agent / --chat).
4. Run scripts/build_dashboard.py to compute the metrics and write the HTML to working/.
5. Review the KPI summary, publish to output/ with host-CopyArtifact, confirm with Glob.
```

## Core Instructions

### Phase 1 — Explain the process (always do this first)

Tell the user, in a few plain lines, how this works:

> This builds your Copilot adoption dashboard from four exports you pull from the
> Microsoft 365 admin center Copilot reports: **(1) Copilot usage** (per licensed
> user), **(2) Agents – per user**, **(3) Agents – per agent**, and **(4) Copilot
> Chat** (includes unlicensed users). I'll compute license activation, the
> habitual-user and agent-adoption rates, user segments (Champion → Never), top
> app surfaces, per-agent usage share, and the unlicensed-Chat conversion funnel,
> then drop them into a branded, single-file dashboard. The reporting window is
> taken from the **Report Period** column in your export (the admin center
> default is 28 days), so the dashboard always states the period your data
> actually covers. I just need your **company name** (required), an optional
> **logo**, and the **four CSV files**.

### Phase 2 — Collect inputs

1. **Company name + logo:** if not already given, ask with `core-AskUserQuestion`
   (company name is required; logo is optional — a PNG/JPG/SVG file). Do not ask
   for anything a lookup can answer.
2. **The four CSVs:** find them with `Glob` on `input/**/*.csv`. If fewer than
   four are present, tell the user which report types are missing and proceed
   with the ones supplied (missing reports degrade to a pending panel — never
   invented data).

### Phase 3 — Map columns and compute

1. **Inspect headers** of each CSV (read the first two lines) and match each file
   to a report flag using the signatures in the reference: per-app **Loop/OneNote**
   columns → `--usage`; **agents-used** column → `--agents-user`; an **agent-name**
   row grain → `--agents-agent`; a **web-chat** surface / unlicensed users → `--chat`.
2. **Run the build** (from the skill directory) — write to `working/` first:
   ```
   python scripts/build_dashboard.py \
     --company "<Company>" [--logo input/<logo>] \
     --usage input/<usage>.csv --agents-user input/<agents_user>.csv \
     --agents-agent input/<agents_agent>.csv --chat input/<chat>.csv \
     --out working/<Company>_Copilot_Adoption_Dashboard.html
   ```
   **Omit `--period`** — the window comes from the export's **Report Period**
   column (MAC default 28 days). Pass `--period` only when the user explicitly
   asks for a different window, and `--report-date` only to override the
   export's Report Refresh Date.
3. **Read the JSON summary** the script prints. Check `periodDays` and
   `periodSource` — confirm the window matches the export the user supplied
   (e.g. `28` from the Report Period column) and mention it when you report back.
   If `warnings` names an unmapped column, write a small `--col-map` JSON (see
   the reference) and re-run — do not hand-edit numbers. Confirm
   `template_reference_check` is `clean`.

### Phase 4 — Review and deliver

1. Show the user a short **table** of the computed KPIs (activation, habitual,
   agent adoption, conversion), the **number of recommended next steps** the
   dashboard raised, plus the report date, the **reporting window and
   where it came from** (e.g. "28-day window, from the export's Report Period
   column"), and which sources were used, for a quick sanity check before delivery.
2. Publish the finished file to `output/` with
   `host-CopyArtifact(surface="output", source="working/<file>.html", destination="<file>.html")`,
   then confirm it exists with `Glob output/**/*`.
3. Tell the user the dashboard is ready and note any pending panels (missing sources).

## Output

- **Primary deliverable:** one self-contained `.html` dashboard in `output/`,
  named `<Company>_Copilot_Adoption_Dashboard.html`, opening directly in any browser.
- **Chat reply:** 3–5 lines — the KPI summary table, the report date/window, and
  a note of any missing source. Keep internal paths and tool names out of it.

## Guardrails

- **Never fabricate** a metric: every KPI, segment, and share is computed by the
  script from the exports. If a column can't be mapped, provide a `--col-map` and
  re-run; never type a number in by hand.
- **Always inspect headers before computing** — tenants name columns differently;
  confirm each file maps to the right report flag.
- **Never hard-code the reporting window.** It is read from the export's **Report
  Period** column (MAC default 28 days) and shown on the dashboard badge and
  footer; only pass `--period` when the user explicitly asks for a different
  window. If the script warns that reports disagree or that no Report Period
  column was found, tell the user which window was used and why.
- If a report is missing, leave its `sources` flag false so the panel renders as
  **pending** — do not guess or copy sample values as a fallback.
- Thresholds (segments, lead tiers, KPI targets) come from the framework and are
  tunable; if the user asks, adjust them in the reference, not by editing outputs.
- **Review before delivery:** show the KPI summary table and confirm the company
  name spelling before publishing the final file; keep the four exports in
  `working/` and deliver only the dashboard.
- **Recommendations are threshold-driven, never invented.** KPI-triggered cards
  appear only when a measured value trips its framework threshold, and each
  cites that number; the ongoing training/awareness cards are labelled as such
  because they are not threshold-driven. Do not add, reorder or soften cards by
  hand — if a threshold needs to change, change the template's `RECO_T` and say so.
- **Dormancy is not a recommendation trigger.** The framework treats it as a
  trend needing two reporting periods; this is a single-period view, so the
  Dormant segment is charted but never used to raise a play.
- This skill reports **aggregate** adoption only — never rank or evaluate
  individual users. Redirect performance questions to the user's manager or HR.
