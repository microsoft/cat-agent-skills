---
name: regulation-monitor
description: Use when the user asks to set up, run, or check a scheduled regulation, law, or regulatory-guidance monitor or tracker — triggers include "set up a regulation tracker for X", "monitor [regulation] for me", "run my regulation monitor", "what changed on [regulation] this week", or an unattended scheduler invoking a saved profile. On first invocation walk interactive setup (topics, jurisdictions, cadence, delivery), auto-discover the top authoritative sources per topic, and STOP for user confirmation before any monitoring. On subsequent runs visit only the locked source list plus user seeds, classify items, flag team-relevant ones via a WorkIQ-derived keyword match, and render a self-contained HTML dashboard with client-side sortable columns. Do NOT use for one-off legal research, reading a single document, computing compliance liability or filing position, or non-regulatory news monitoring.
---

# Regulation Monitor

## Source discipline

This skill is deliberately **bounded and confirmed**. It does not run
open-ended web searches every run. Instead, at setup:

1. Run a small **discovery pass** to identify the top 5 authoritative
   sources per watch topic (regulators, official trackers, reputable
   trade press).
2. **Present the shortlist to the user and stop.** No monitoring runs
   until the user has confirmed the list.
3. The user can swap/remove any of the 5, lower the target, and supply
   their own **seed sources** on top.
4. The confirmed list is **locked into the profile config**.

Every subsequent run visits **only** those sources. A tightly-bounded
fallback web search (at most one query per topic, capped result count,
allowlist-filtered) is used only when a locked source is silent for a
topic in the window.

## Instructions

### Step 0 — First-run setup (only if no config exists)

If `config.json` for the requested profile does not exist, walk the user
through setup:

1. **Profile name** — kebab-case slug, e.g. `pillar-ii`.
2. **Watch topics** — 2 to 8 topics. For each: display name plus 3–8
   keywords the sweeps should look for.
3. **Jurisdictions** — countries, regions, states, sectors, or `global`.
4. **Cadence** — daily, weekly (default), biweekly, monthly.
5. **Window** — days to look back per run (default: matches cadence).
6. **Delivery target** — user's own email (default), a Teams chat, a Loop
   page, or "inline only".

### Step 1 — Auto-discover authoritative sources, then STOP for confirmation

**This is an interactive checkpoint. Run a small discovery pass to
identify candidate sources, then present them and stop. Do not start
the monitoring sweep (Step 5) until the user has explicitly confirmed
the source list.**

For each watch topic the user configured, propose up to **5 authoritative
sources** (default target 5; use fewer if the user asks or if the domain
has fewer canonical sources).

Preference order (pick the strongest 5 that exist for the topic):

1. The primary regulator / issuing body's official page for the topic.
   Examples: OECD's Pillar Two page, the European Commission's page for
   the AI Act, HHS OCR for HIPAA, EDPB for GDPR, ISSB for sustainability
   disclosure.
2. Government official journals and legislative trackers for the
   jurisdictions in scope. Examples: Federal Register, EUR-Lex, UK
   legislation.gov.uk, state legislature bill pages.
3. The relevant multilateral, standard-setting, or specialist body's
   page for the topic. Examples: OECD, UN, BIS, ISO, NIST (AI RMF,
   cyber), WHO/EMA (health), ILO (labor), FSB (financial stability).
4. A reputable public tracker or think tank whose focus matches the
   domain. Examples: Tax Foundation and MTC/NCSL for tax; IAPP and
   Future of Privacy Forum for privacy; Stanford HAI, Brookings AI, and
   the Ada Lovelace Institute for AI; ISSB and EFRAG for sustainability;
   SHRM and EPI for labor; KFF for healthcare policy.
5. Public alert pages from major professional-services or specialist
   firms that cover the domain (public URLs only, never subscriber
   content). Examples: KPMG / EY / PwC / Deloitte / BDO insight pages
   for tax and financial regulation; DLA Piper, Hogan Lovells, Wilson
   Sonsini, Cooley for tech / privacy / AI; Ropes & Gray for healthcare;
   Littler and Ogletree Deakins for labor.

Match the mix to the domain — do not force tax-style sources onto a
non-tax topic.

**How to find them:** for each topic, do a short bounded discovery
pass — one to three focused web searches against the reputable-domain
allowlist in `references/sources-and-taxonomy.md` — just enough to
identify canonical topic pages (not the regulator's home page). This
discovery pass is separate from the monitoring sweep and must be small.

**Present them and STOP.** Show the shortlist to the user and wait
before doing anything else:

> "Before I start monitoring, here are the 5 authoritative sources I'd
> watch for **Pillar II**:
>   1. OECD — Pillar Two: <url>
>   2. European Commission — Pillar Two implementation: <url>
>   3. HMRC — Multinational Top-up Tax: <url>
>   4. Tax Foundation — Global minimum tax tracker: <url>
>   5. KPMG — BEPS 2.0 tracker: <url>
>
> Want me to swap any out? And do you have any of your own sources
> (regulator pages, internal trackers, subscription-free trade alerts,
> etc.) you want me to add on top of these?"

**Wait for the user's reply.** The user may:

- Approve as-is → proceed.
- Ask to swap or remove one of the 5 → re-run discovery for that slot
  with the constraint they gave.
- Add their own seed URLs → append them to `seed_sources_by_topic`
  under the appropriate topic key. Seed sources are **not** counted
  against the "top 5" — a topic can end up with 5 auto-discovered plus
  N user seeds. A seed that spans multiple topics is added under each
  relevant topic key.
- Ask you to lower the target from 5 → honor it.

**Do not skip this confirmation, even on a re-setup.** If the user
later adds a topic, repeat this checkpoint for the new topic before
touching the sweep.

### Step 2 — Capture the WorkIQ org profile (setup)

Derive a light org profile from WorkIQ and show it for confirmation:

- `workiq_get_my_profile` → job title, department, office
- `workiq_get_my_manager` → manager and their department (context only)
- `workiq_get_relevant_people` (limit 10) → likely function-area
  collaborators

Propose a `function_area_keywords` list (5–15 words: department name and
variants, the user's job function, key collaborator team names, obvious
topic proxies). The user edits and confirms.

If WorkIQ is unavailable on the current platform, ask the user for
`function_area_keywords` manually. The rest of the skill works unchanged.

### Step 3 — Save the profile

Write `config.json`:

```json
{
  "profile_name": "pillar-ii",
  "watch_topics": [
    { "key": "pillar-two", "name": "OECD Pillar II / GloBE",
      "keywords": ["Pillar Two", "GloBE", "global minimum tax",
                   "IIR", "UTPR", "QDMTT", "DMTT", "top-up tax"] }
  ],
  "jurisdictions": ["global"],
  "sources_by_topic": {
    "pillar-two": [
      { "name": "OECD — Pillar Two",
        "url": "https://www.oecd.org/tax/beps/pillar-two-model-rules-in-a-nutshell.pdf",
        "kind": "regulator" }
    ]
  },
  "seed_sources_by_topic": {},
  "cadence": "weekly",
  "window_days": 7,
  "runtime_budget": {
    "max_items": 40,
    "max_fallback_searches": 2,
    "max_fetches_per_source": 2
  },
  "delivery": { "type": "email", "to": ["me@example.com"] },
  "workiq_context": {
    "captured_at": "2026-07-23T11:00:00Z",
    "department": "Global Tax Policy",
    "job_title": "Director, International Tax",
    "function_area_keywords": ["Pillar Two", "GloBE", "international tax",
                               "transfer pricing", "top-up tax"],
    "collaborator_teams": ["Transfer Pricing", "Tax Controversy"]
  },
  "last_run_at": null
}
```

### Step 4 — Load config and scope the sweep (every run)

- Read `config.json` for the profile.
- Resolve the window: from `last_run_at` (if set) to now, else the past
  `window_days`.
- Restate the scope back to the user in one line so they can interrupt
  if it looks wrong (interactive runs only).

### Step 5 — Sweep the locked source list (bounded)

Sweep proceeds in this order and stops when the budget is met:

1. **Every source in `sources_by_topic[topic]` and
   `seed_sources_by_topic[topic]` for each topic.** `web_fetch` each URL.
   Extract items dated within the window.
   - Cap `max_fetches_per_source` (default 2). If a source's index page
     links to individual items, follow at most that many per source.
2. **Bounded fallback search** only for topics where every locked source
   (auto-discovered + user seeds) returned zero items in the window. At
   most one `web_search` per topic, at most `max_fallback_searches`
   total across the run (default 2). Filter results by the reputable-
   domain allowlist. Discard non-matching results.
3. **Stop when `max_items` is reached** (default 40). Prefer regulator
   sources > tracker sources > firm alerts when trimming.

Runtime budget defaults, all configurable in `config.runtime_budget`:

- `max_items`: 40 — total items recorded per run.
- `max_fallback_searches`: 2 — `web_search` calls per run.
- `max_fetches_per_source`: 2 — items followed from one source's index.

Rules that always apply:

- Validate every date against the window; drop out-of-window items.
- Never bypass a paywall; skip subscriber-only content.
- Deduplicate items with the same title + jurisdiction, keeping the
  more authoritative source (regulator > tracker > firm alert).

### Step 6 — Classify each item

Record, for every item:

- **topic** — one of the profile's watch-topic keys.
- **jurisdiction** — from the profile's list, or `global` /
  `local: <name>`.
- **stage** — `proposed` / `in-consultation` / `passed` /
  `regulatory-guidance` / `in-force` / `litigation` / `withdrawn`.
- **date** — ISO date the source is dated or the action took place.
- **title** — the source's short title, verbatim.
- **summary** — 1–2 sentences in the skill's own words.
- **source_name** — publisher's short name.
- **source_url** — canonical public URL actually retrieved
  (http/https/mailto only; other schemes are dropped at render time).

Stage inference guidance is in `references/sources-and-taxonomy.md`.

### Step 7 — Flag team relevance (WorkIQ-derived)

For each item, set `relevant_to_your_team` to `true` if any
`workiq_context.function_area_keywords` phrase appears (case-insensitive)
in the item's title, summary, or matched topic keywords. Otherwise
`false`.

This is a soft highlight, not an impact rubric. The dashboard uses it
to sort and badge; the skill never says "this affects your business" —
that is a human judgment.

### Step 8 — Build the dashboard

1. Write items to `working/regulation-items.json`.
2. Run the bundled generator:
   ```
   python scripts/build_dashboard.py \
     --config config.json \
     --items working/regulation-items.json \
     --output output/regulation-dashboard.html
   ```
3. Verify the file was written before telling the user it is ready.

The dashboard is a single self-contained HTML file — KPI tiles (total
items, count per topic, team-relevant count), a table color-coded by
stage with **client-side sortable columns** (click any column header, or
focus and press Enter/Space, to sort), a team-relevant badge on flagged
rows, and every row linking to its primary source.

### Step 9 — Deliver and update last-run

- **Inline**: a short summary — window covered, item counts by topic,
  the top team-relevant items (title, jurisdiction, stage, date). If a
  topic produced no items, say **"No significant developments this
  period"** for that topic. Do not pad, do not speculate.
- **Scheduled runs**: send per the profile's delivery block. If `type`
  is `email`, send the HTML dashboard as an attachment to the addresses
  in `to`. The pre-authorized recipient is the user themselves. Any
  additional recipient requires explicit user confirmation on an
  interactive run and is never added on an unattended run.
- **Update the config** with `last_run_at = <now-ISO>`.

## Guardrails

- **Never fabricate** a bill number, date, quote, or enactment status.
  If a fact cannot be confirmed from a retrieved public source, mark it
  `[unverified]` in the summary. Report gaps honestly.
- **No speculation, rumors, or unofficial sources.** Do not include
  items sourced from anonymous leaks, social-media speculation,
  unattributed drafts, or "reportedly" / "expected to" claims without a
  named official source. If an item cannot be tied to a specific
  document or announcement from a source on the profile's locked list
  (or the reputable-domain allowlist for fallback search), drop it.
  Better silence than noise.
- **Report empty categories explicitly.** If a topic produced no items
  in the window, say **"No significant developments this period"** for
  that topic in both the inline summary and the dashboard. Do not pad
  with low-signal filler.
- **Public sources only.** Never bypass a paywall or reproduce
  paywalled or copyrighted text. Summarize in the skill's own words and
  link the source.
- **Locked source list.** The sweep only visits URLs in the profile's
  `sources_by_topic` and `seed_sources_by_topic`. That list is set at
  interactive setup with explicit user confirmation — the skill cannot
  start the monitoring sweep until the user has approved the sources.
  Fallback search is bounded by `runtime_budget.max_fallback_searches`
  and filtered by the reputable-domain allowlist. Do not add new
  sources on an unattended run — that requires interactive re-setup.
- **Monitoring, not advice.** The skill never states a filing position,
  a legal conclusion, or a business impact. `relevant_to_your_team` is
  a soft keyword-match highlight.
- **Confirm before external sends.** Emailing anyone other than the
  user requires explicit confirmation on an interactive run; unattended
  runs never add recipients.
- **Confidentiality and sensitivity.** If a retrieved source carries a
  confidentiality label or sensitivity marking (for example
  "Confidential", "Internal Only", "Restricted", or an enterprise
  information-protection label), or contains unreleased figures,
  customer or partner identifiers, or names that aren't public yet,
  drop it — this skill uses public sources only. Never add PII,
  customer identifiers, or non-public attribution to the dashboard
  beyond the function-area keywords the user confirmed at setup.
- **Cover exactly the requested topics** — no more, no fewer.
- **Do not reproduce third-party copyrighted text** verbatim; paraphrase
  in the skill's own words.
- **Verify delivery.** Confirm the dashboard file exists before
  reporting success. If the delivery block failed, report the failure.
- **Cite by exact source name** and validate every date against the
  requested window.

## References

- `references/sources-and-taxonomy.md` — reputable-domain allowlist,
  item classification taxonomy, stage-inference rules, and per-topic
  search-query templates.
- `scripts/build_dashboard.py` — self-contained dashboard generator
  (Python standard library only; embeds a small vanilla-JS sorter for
  the items table).
