---
name: "regulation-monitor"
description: "Monitors user-specified regulations, laws, and regulatory guidance on a"
---

# Regulation Monitor

## Overview

Turns a saved "watch profile" — topics, jurisdictions, source list, cadence —
into a repeatable regulatory sweep. On each run the skill visits only the
sources locked into the profile at setup: the top authoritative sources the
skill proposed for each watch topic plus any seed sources the user added.
It classifies each new item, flags items likely relevant to the user's team
using a light org profile derived once from WorkIQ, and produces a
self-contained HTML dashboard with sortable columns.

It is a **monitoring** tool. It reports what regulators, legislatures, and
courts are doing. It never files, calculates liability, or gives a legal
opinion.

## Source discipline

This skill is deliberately **bounded and confirmed**. It does not run
open-ended web searches every run — those get expensive, unpredictable, and
prone to noise. Instead, at setup:

1. The skill runs a small **discovery pass** to identify the top 5
   authoritative sources per watch topic (regulators, official trackers,
   reputable trade press).
2. **The skill presents that shortlist to the user and stops.** No
   monitoring runs until the user has confirmed the list.
3. The user can swap/remove any of the 5, lower the target, and can supply
   their own **seed sources** on top.
4. The confirmed list is **locked into the profile config**.

Every subsequent run visits **only** those sources. A tightly-bounded
fallback web search (at most one query per topic, capped result count,
allowlist-filtered) is used only when a locked source is silent for a
topic in the window. See "Runtime budget" below.

## When to Use

- On-demand: "run my regulation monitor", "what changed on the EU AI Act
  this week"
- Setup: "set up a regulation tracker for [topics]", "monitor [X]
  regulations for me"
- Scheduled: unattended runs invoked by an external scheduler (Scout
  automation, Cowork scheduled task, etc.) — see the submission's
  README.md for platform-specific templates

## When NOT to Use

- One-off legal or regulatory research → use `deep-research`
- Reading a single document the user has already given you → use `docx` /
  `pptx`
- Computing a compliance liability, filing position, or legal conclusion →
  out of scope; escalate to a human
- Non-regulatory news monitoring → use `deep-research` or a news skill

## Quick Start

```
User: "Set up a regulation monitor for OECD Pillar II across all jurisdictions"
1. Capture profile name, watch topics, jurisdictions, cadence, delivery.
2. Discovery pass: propose up to 5 authoritative sources per watch topic.
3. STOP — show the shortlist to the user and ask two things: which to swap
   out, and whether they want to add their own seed sources.
4. Wait for confirmation. Do not do any monitoring until the user approves.
5. Derive a light org profile from WorkIQ (function-area keywords) and show
   it for confirmation.
6. Lock all of this into config.json.
7. Do the first sweep now that the user has approved the source list.
```

## Core Instructions

### Step 0 — First-run setup (only if no config exists)

If `config.json` for the requested profile does not exist, walk the user
through setup:

1. **Profile name** — kebab-case slug, e.g. `pillar-ii`.
2. **Watch topics** — 2 to 8 topics. For each: display name plus 3–8
   keywords/phrases the sweeps should look for.
3. **Jurisdictions** — countries, regions, states, sectors, or `global`.
4. **Cadence** — daily, weekly (default), biweekly, monthly.
5. **Window** — days to look back per run (default: matches cadence).
6. **Delivery target** — user's own email (default), a Teams chat, a Loop
   page, or "inline only".

### Step 1 — Auto-discover authoritative sources, then STOP for confirmation

**This is an interactive checkpoint. The skill runs a small discovery pass
to identify candidate sources, then presents them and stops. Do not start
the monitoring sweep (Step 5) until the user has explicitly confirmed the
source list.**

For each watch topic the user configured, propose up to **5 authoritative
sources** (default target is 5; use fewer if the user asks or if the domain
genuinely has fewer canonical sources):

- **Preference order** (in this order — pick the strongest 5 that exist for
  the topic):
  1. The primary regulator / issuing body's official page for the topic.
     Examples: OECD's Pillar Two page, the European Commission's page for
     the AI Act, HHS OCR for HIPAA, EDPB for GDPR, ISSB for sustainability
     disclosure.
  2. Government official journals and legislative trackers for the
     jurisdictions in scope. Examples: Federal Register, EUR-Lex, UK
     legislation.gov.uk, state legislature bill pages.
  3. The relevant multilateral, standard-setting, or specialist body's page
     for the topic. Examples: OECD, UN, BIS, ISO, NIST (AI RMF, cyber),
     WHO/EMA (health), ILO (labor), FSB (financial stability).
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

  Pick the mix that fits the domain. A tax profile will lean on OECD +
  regulators + Tax Foundation + big-four alerts. A privacy profile will
  lean on EDPB + national DPAs + IAPP + tech-privacy firm alerts. A health
  profile will lean on HHS/FDA + WHO/EMA + KFF + healthcare firm alerts.
  Do not force tax-style sources onto a non-tax topic.

- **How to find them**: for each topic, do a short bounded discovery
  pass — one to three focused web searches against the reputable-domain
  allowlist in `references/sources-and-taxonomy.md` — just enough to
  identify the canonical topic pages (not the regulator's home page). This
  discovery pass is separate from the monitoring sweep and must be small.

- **Present them and STOP**. Show the proposed list to the user in a short
  message and wait for a reply before doing anything else:
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

- **Wait for the user's reply.** The user may:
  - Approve as-is → proceed.
  - Ask to swap or remove one of the 5 → re-run discovery for that slot
    with the constraint they gave you.
  - Add their own seed URLs → append them to `seed_sources_by_topic` under
    the appropriate topic key. Seed sources are **not** counted against the
    "top 5" — a topic can end up with 5 auto-discovered + N user seeds.
    A user seed that spans multiple topics should be added under each
    relevant topic key.
  - Ask you to lower the target from 5 (e.g., "just the two OECD pages
    are enough") → honor it.

- **Do not skip this confirmation, even on a re-setup.** If the user later
  says "add EU AI Act to my profile", repeat this checkpoint for the new
  topic before touching the sweep.

### Step 2 — Capture the WorkIQ org profile (setup)

Derive a light org profile from WorkIQ and show it for confirmation:

- `workiq_get_my_profile` → job title, department, office
- `workiq_get_my_manager` → manager and their department (context only)
- `workiq_get_relevant_people` (limit 10) → likely function-area
  collaborators

From those, propose a `function_area_keywords` list (5–15 words: department
name and variants, the user's job function, key collaborator team names,
obvious topic proxies). The user edits and confirms.

If WorkIQ is unavailable on the current platform, ask the user to provide
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
      { "name": "OECD — Pillar Two", "url": "https://www.oecd.org/tax/beps/pillar-two-model-rules-in-a-nutshell.pdf",
        "kind": "regulator" },
      { "name": "European Commission — Pillar Two",
        "url": "https://taxation-customs.ec.europa.eu/taxation/business-taxation/minimum-corporate-taxation_en",
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
- Restate the scope back to the user in one line so they can interrupt if it
  looks wrong (interactive runs only).

### Step 5 — Sweep the locked source list (bounded)

Sweep proceeds in this order and stops when the budget is met:

1. **Every source in `sources_by_topic[topic]` and
   `seed_sources_by_topic[topic]` for each topic.** `web_fetch` each URL.
   Extract items dated within the window.
   - Cap `max_fetches_per_source` (default 2). If a source's index page
     links to individual items, follow at most that many links per source.
2. **Bounded fallback search** only for topics where every locked source
   (auto-discovered + user seeds) returned zero items in the window. At
   most one `web_search` per topic, at most `max_fallback_searches` total
   across the run (default 2). Filter results by the reputable-domain
   allowlist. Discard non-matching results.
3. **Stop when `max_items` is reached** (default 40). Prefer regulator
   sources > tracker sources > firm alerts when trimming.

**Rules that always apply:**

- Validate every date against the window; drop out-of-window items.
- Never bypass a paywall; skip subscriber-only content.
- Deduplicate items with the same title + jurisdiction, keeping the more
  authoritative source (regulator > tracker > firm alert).

### Step 6 — Classify each item

Record, for every item:

- **topic** — one of the profile's watch-topic keys
- **jurisdiction** — from the profile's list, or `global` / `local: <name>`
- **stage** — `proposed` / `in-consultation` / `passed` /
  `regulatory-guidance` / `in-force` / `litigation` / `withdrawn`
- **date** — ISO date the source is dated or the action took place
- **title** — the source's short title, verbatim
- **summary** — 1–2 sentences in the skill's own words
- **source_name** — publisher's short name
- **source_url** — canonical public URL actually retrieved

Stage inference guidance is in `references/sources-and-taxonomy.md`.

### Step 7 — Flag team relevance (WorkIQ-derived)

For each item, set `relevant_to_your_team` to `true` if any
`workiq_context.function_area_keywords` phrase appears (case-insensitive) in
the item's title, summary, or matched topic keywords. Otherwise `false`.

This is a soft highlight, not an impact rubric. The dashboard uses it to
sort and badge; the skill never says "this affects your business" — that is
a human judgment.

### Step 8 — Build the dashboard

1. Write items to `working/regulation-items.json` (schema in the script
   header).
2. Run the bundled generator:
   ```
   python scripts/build_dashboard.py \
     --config config.json \
     --items working/regulation-items.json \
     --output output/regulation-dashboard.html
   ```
3. Verify the file was written before telling the user it is ready.

The dashboard is a single self-contained HTML file — KPI tiles (total items,
count per topic, team-relevant count), a table color-coded by stage with
**client-side sortable columns** (click any column header to sort), a
team-relevant badge on flagged rows, and every row linking to its primary
source.

### Step 9 — Deliver and update last-run

- **Inline**: a short summary — window covered, item counts by topic, the
  top team-relevant items (title, jurisdiction, stage, date).
- **Scheduled runs**: send per the profile's delivery block. If `type` is
  `email`, send the HTML dashboard as an attachment to the addresses in
  `to`. The pre-authorized recipient is the user themselves. Any additional
  recipient requires explicit user confirmation on an interactive run and
  is never added on an unattended run.
- **Update the config** with `last_run_at = <now-ISO>`.

## Runtime budget (defaults)

The `runtime_budget` block in the config caps every dimension of a run:

| Setting | Default | What it caps |
|---|---:|---|
| `max_items` | 40 | Total items recorded in one run |
| `max_fallback_searches` | 2 | `web_search` calls per run (only if a source was silent) |
| `max_fetches_per_source` | 2 | Individual items followed from one source's index |

These bounds keep the skill fast and predictable. Users can raise them for
big topics (e.g., Pillar II across 20 jurisdictions) or lower them for
narrow ones (e.g., one EU regulation).

## Output

- **Dashboard**: `output/regulation-dashboard.html` — KPI tiles, client-side
  sortable color-coded table, team-relevant badges, per-row source links
  (URL scheme sanitized — only `http`/`https`/`mailto` render).
- **Items JSON**: `working/regulation-items.json` — raw items from this run
  (useful for diffing or feeding downstream tools).
- **Inline summary**: ≤12 lines — window, item counts by topic, top team-
  relevant items. If a topic produced no items, say **"No significant
  developments this period"** for that topic — do not pad, do not speculate.

## Guardrails

- **Never fabricate** a bill number, date, quote, or enactment status. If a
  fact cannot be confirmed from a retrieved public source, mark it
  `[unverified]` in the summary. Report gaps honestly ("couldn't confirm X").
- **No speculation, rumors, or unofficial sources.** Do not include items
  that come from anonymous leaks, social-media speculation, unattributed
  drafts, or "reportedly" / "expected to" claims without a named official
  source. If an item cannot be tied to a specific document or announcement
  from a source on the profile's locked list (or the reputable-domain
  allowlist for fallback search), drop it. Better silence than noise.
- **Report empty categories explicitly.** If a topic produced no items in
  the window, say **"No significant developments this period"** for that
  topic in both the inline summary and the dashboard. Do not pad with
  low-signal filler.
- **Public sources only.** Never bypass a paywall or reproduce paywalled or
  copyrighted text. Summarize in the skill's own words and link the source.
- **Locked source list.** The sweep only visits URLs in the profile's
  `sources_by_topic` and `seed_sources_by_topic`. That list is set at
  interactive setup with an explicit user confirmation — the skill cannot
  start the monitoring sweep until the user has approved the sources.
  Fallback search at runtime is bounded by
  `runtime_budget.max_fallback_searches` and filtered by the reputable-
  domain allowlist. Do not add new sources on an unattended run — that
  requires interactive re-setup.
- **Monitoring, not advice.** The skill never states a filing position, a
  legal conclusion, or a business impact. `relevant_to_your_team` is a soft
  keyword-match highlight.
- **Confirm before external sends.** Emailing anyone other than the user
  requires explicit confirmation on an interactive run; unattended runs
  never add recipients.
- **Confidentiality and sensitivity.** If a retrieved source carries a
  confidentiality label or sensitivity marking (for example "Confidential",
  "Internal Only", "Restricted", or an enterprise information-protection
  label), or contains unreleased figures, customer or partner identifiers,
  or names that aren't public yet, drop it — this skill uses public
  sources only. Never add PII, customer identifiers, or non-public
  attribution to the dashboard beyond the function-area keywords the user
  confirmed at setup.
- **Cover exactly the requested topics** — no more, no fewer.
- **Do not reproduce third-party copyrighted text** verbatim; paraphrase
  in the skill's own words.
- **Verify delivery.** Confirm the dashboard file exists before reporting
  success. If the delivery block failed, report the failure — do not
  report success.
- **Cite by exact source name** and validate every date against the
  requested window.

## Scheduling

The core skill has no schedule of its own — it just runs. See the
submission's `README.md` (a human-facing sidecar; not bundled into the
agent's context) for platform-specific scheduling walkthroughs on Scout and
Cowork. Wire this skill to your platform's scheduler and it invokes the
skill on cadence.

## References

- `references/sources-and-taxonomy.md` — reputable-domain allowlist for
  fallback search, item classification taxonomy, stage-inference rules, and
  per-topic search-query templates.
- `scripts/build_dashboard.py` — self-contained dashboard generator
  (Python standard library only; embeds a small vanilla-JS sorter for
  the items table).
