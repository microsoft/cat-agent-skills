# Regulation Monitor

Configure this skill once for a regulation you care about, then let it run on a
schedule and drop a fresh dashboard into your inbox.

## What it does

Turns a saved **watch profile** — topics, jurisdictions, source list, cadence —
into a repeatable regulatory sweep. On each run the skill visits only the
sources you locked into the profile at setup: the top authoritative sources
the skill proposed for each topic, plus any seed URLs you added on top. It
classifies each new item (topic, jurisdiction, stage, date), flags items that
match your team's function-area keywords using a light WorkIQ-derived profile,
and produces a self-contained HTML dashboard.

It is a **monitoring** tool. It reports what regulators, legislatures, and
courts are doing. It never files, calculates liability, or gives a legal
opinion.

## When to use it

- You want a recurring digest of regulatory changes in a defined area (tax,
  privacy, AI, healthcare, ESG, labor, competition, anything domain-specific).
- You already know roughly what to watch (topic + jurisdictions) and want a
  bounded, predictable sweep rather than an open-ended search every week.
- You want the same view for the same profile every week so you can diff week
  over week.

## When not to use it

- One-off legal or regulatory research → use a research skill.
- Reading a single document you already have → use `docx` / `pptx`.
- Computing a compliance liability or filing position → out of scope. Escalate
  to a human.

## Setup walkthrough

First time you invoke the skill for a new regulation, it walks you through a
short interactive setup:

1. **Profile name**, e.g. `pillar-ii`, `eu-ai-act`, `hipaa-sec-2`.
2. **Watch topics** — 2 to 8 topics, each with a display name and a handful
   of keywords the sweep will look for.
3. **Jurisdictions** — countries, regions, sectors, or `global`.
4. **Cadence** — daily, weekly (default), biweekly, monthly.
5. **Window** — days to look back per run (default matches cadence).
6. **Delivery target** — your own email (default), a Teams chat, a Loop page,
   or inline only.

The skill then does a small **discovery pass** to propose the top 5
authoritative sources per topic (regulator page → official journal →
multilateral body → reputable tracker → firm public alert). It **stops for
your confirmation** — you can swap any of the 5, lower the target, or add
your own seed URLs — before starting any monitoring.

After you confirm, the skill captures a light org profile from WorkIQ
(`workiq_get_my_profile`, `workiq_get_my_manager`, `workiq_get_relevant_people`)
and proposes 5–15 function-area keywords for the team-relevance flag. You edit
and confirm those too.

Everything is written to `config.json` next to the dashboard output. Every
subsequent run reads it and visits only the confirmed source list.

## Scheduling

The core skill has no schedule of its own — it just runs. Wire it to your
platform's scheduler:

### Scout

Create a Scout automation:

```
name: Regulation Monitor — <profile-name>
schedule: every Monday at 8am
prompt: |
  Run the regulation-monitor skill for profile "<profile-name>".
  Load the profile's config.json, sweep the window since the last run,
  build the dashboard, and email the digest to the user per the
  delivery block. Always send the dashboard, including on quiet weeks —
  topics with no items are reported explicitly as "No significant
  developments this period" and the empty-state view is intentional.
teamsNotify: auto
```

Scout keeps the recurrence and invokes the skill.

### Cowork

Create a recurring Cowork task with the same prompt above, task name
`Regulation Monitor — <profile-name>`, recurrence matching the profile's
cadence.

### What the schedule should not do

- **Do not reconfigure the profile from the schedule.** Setup is an interactive
  step. If the profile is missing or stale, the scheduled run should send a
  short heads-up and stop, not silently rebuild.
- **Do not add external email recipients from the schedule.** The pre-authorized
  recipient is you (the user). Any other recipient requires an interactive
  confirmation.
- **Do not chain the monitor into downstream action.** This skill monitors; it
  does not take a filing position or trigger a workflow. Keep the scheduled
  job single-purpose.

## Output

- **Dashboard**: `output/regulation-dashboard.html` — KPI tiles,
  client-side sortable color-coded table (click any column header to sort
  by date, topic, jurisdiction, stage, title, or source), team-relevant
  badges, per-row source links (URL scheme sanitized — only
  `http`/`https`/`mailto` are rendered), and a "Quiet this period" section
  listing every watch topic that produced zero items as
  **"No significant developments this period"**.
- **Items JSON**: `working/regulation-items.json` — raw items from this run.
- **Inline summary**: ≤12 lines — window, item counts by topic, top team-
  relevant items. Quiet topics are reported explicitly, not padded.

## Tips

- Keep watch topics narrow. "Pillar Two" as one topic gives you a coherent
  weekly digest. "International tax" gives you noise.
- The domain-agnostic reputable-source allowlist for fallback search lives in
  `references/sources-and-taxonomy.md`. Extend it via
  `domain_allowlist_extensions` in the config if your domain needs sources
  outside the defaults.
- Tune `runtime_budget` in the config if you find the sweep is too aggressive
  (lower `max_items`) or too silent (raise `max_fallback_searches`).
