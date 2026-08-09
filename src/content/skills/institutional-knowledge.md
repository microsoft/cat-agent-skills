---
name: Institutional Knowledge Archivist
description: "Preserve a departing senior leader's institutional knowledge — decisions, rationale, relationships, and tribal knowledge — by mining their M365 signals into a structured, multi-phase archive a successor can ground on."
agentDescription: "Extract and preserve a departing senior leader's institutional knowledge — projects, decisions, rationale, relationships, tribal knowledge — into a structured, multi-phase archive built from M365 signals (emails, Teams, meetings, SharePoint/OneDrive). Resumable across multiple sessions. Use when the user asks to \"build an institutional knowledge archive\", \"preserve institutional knowledge\", \"capture a departing leader's knowledge\", \"run a knowledge extraction for an executive handoff\", \"document a leadership transition before someone retires\", or otherwise to capture/preserve a specific leader's decision history and expertise before they leave. Do not trigger on incidental mentions of someone retiring, leaving, or being out of office."
platforms: [Cowork, Scout]
tags: [knowledge, handoff, leadership, m365, offboarding, documentation, productivity]
author: Srinivas Varukala
authorUrl: "https://github.com/svarukala"
authorGithub: svarukala
version: 1.0.1
createdAt: 2026-07-26
updatedAt: 2026-07-28
---
# /institutional-knowledge — Executive Knowledge Preservation

**Intent.** Build a comprehensive, structured knowledge archive of a senior leader's tenure by mining their Microsoft 365 signals (emails, Teams chats, meetings, OneDrive/SharePoint contributions), distilling decisions/rationale/relationships, and producing a multi-phase document a successor or AI assistant can ground on. Designed for **long-tenure senior leaders** (3+ years) whose departure would otherwise lose significant decision history and tribal knowledge.

This skill is **resumable**. Each invocation reads `manifest.md` and continues where the last session stopped. Plan for a 1-week sprint across multiple sessions.

---

## 0. Core operating principles

1. **The leader curates; you produce.** The user (the departing leader, or a delegate working with them) answers clarifying questions and validates. You write everything.
2. **Decision archaeology is the highest-value output.** Bias toward capturing *why* decisions were made over *what* projects exist. Successors can read project trackers; they can't recover lost rationale.
3. **Multi-phase, gated progression.** Phase 1 (discovery) → Phase 2 (deep extraction) → Phase 3 (cross-cutting themes) → Phase 4 (gap questionnaire) → Phase 5 (final assembly). Confirm with the user before advancing phases.
4. **Idempotent ingest.** Every signal is keyed by `(source_id, item_id)` or `(source_id, date)`. Re-running merges, never duplicates.
5. **Capture before polish.** Get raw signals down across all phases before refining. If time runs short, raw breadth beats polished narrowness.
6. **Privacy.** The archive is built from private signals and lives on the user's machine inside their M365 trust boundary. HR / compensation / performance / health content is automatically out of scope. The leader alone decides what to share with the org or successor.

---

## 1. First-run bootstrap

Default archive path: `$env:USERPROFILE\Documents\institutional-knowledge` on Windows/PowerShell hosts, `~/Documents/institutional-knowledge` elsewhere. Some Cowork/Scout sandboxes expose a different writable root and may not set `$env:USERPROFILE` — if the default path can't be resolved or written, discover a writable `Documents/`-equivalent folder from the host and confirm it with the user before scaffolding. Detection: an `AGENTS.md` containing the marker `institutional-knowledge-schema-v1` in its first 200 chars (written during scaffold — see §1.4).

**If no archive exists, run bootstrap.**

### 1.1 Confirm parameters (one at a time — never silently default)

- **a) Archive location.** Default as above; allow override.
- **b) Leader's name, title, tenure dates.** "Doug Smith — VP of Platform Engineering — Jan 2020 to present, last day June 30 2026."
- **c) Tenure horizon.** Default: full tenure. Confirm start year. Senior leaders' early-tenure decisions often anchor current state — do not truncate without reason.
- **d) Audience for the archive.** Successor (named, if known) / leadership team / future AI assistant grounding / all of the above. Affects tone of final document.
- **e) Explicit out-of-scope.** Any project, vendor, or topic the leader does not want captured. Always-excluded: HR matters, compensation, performance reviews, health.
- **f) Sessions available.** How many work sessions before the last day. Calibrates Section 1.5 plan.
- **g) Delegate?** Is the user the leader themselves, or a delegate (chief of staff, EA, successor) operating on their behalf? Affects how clarifying questions are framed.

### 1.2 Gather identity & relationships

In parallel (retry transient failures once before marking blocked):

- `m365_get_my_profile` *(required — abort if it fails twice)*
- `m365_get_my_manager`
- `m365_get_my_direct_reports`
- `m365_get_relevant_people` *(limit 25, used to seed the relationship map)*

### 1.3 Discover sources → write `manifest.md`

Best-effort; record any failures in `log.md` under "Discovery limitations" and continue.

- **Mail folders** — `m365_list_mail_folders(limit: 20)`. **Always pass `limit` explicitly.** Note custom folders (`Leadership`, `Board`, `Strategy`, `Decisions`, project-named folders). Skip personal folders (`H1B*`, `Immig*`, `PTO*`, `Personal`, `H1Renewal`).
- **Active Teams chats** — `m365_list_chats(limit: 50)`. Do not pass `orderBy`. Tag each `1:1` / `group` / `meeting`.
- **Teams memberships** — `m365_list_teams` + `m365_list_channels`. Often fails on `teams_auth_required` — mark blocked and continue; `m365_list_chats` already covers most active conversation.
- **Recurring meetings** — `m365_list_events` over the last 180-365 days; cluster by subject prefix to detect recurrence.
- **Authored documents** — `m365_get_recent_files(limit: 50)` first; fall back to `m365_list_files(limit: 50)` if it fails. Do not rely on `m365_search_files(query: '*')` — unreliable.
- **Targeted email scoping** — `m365_search_emails` works for specific names/keywords but fails on broad queries. Use only during per-project deep dives in Phase 2.

Each source becomes a row in `manifest.md` with status `pending` / `in_progress` / `done` / `skipped` / `blocked`.

### 1.4 Scaffold the archive

Create the layout (Section 2) and seed files: `AGENTS.md`, `index.md`, `log.md`, `manifest.md`, `phase-1-inventory.md`, `relationships.md`, `decisions.md`. Other files are created on first need.

**`AGENTS.md` must begin with the detection marker so future sessions can recognize this archive (see §1).** Write the literal string `institutional-knowledge-schema-v1` within the first 200 characters of `AGENTS.md` — the recommended first line is an HTML comment so it renders invisibly:

```markdown
<!-- institutional-knowledge-schema-v1 -->
# Institutional Knowledge Archive — <Leader name>
<!-- schema + conventions for this archive; do not delete the marker above -->
```

Do not scaffold `AGENTS.md` without this marker: resumability (§11 "continue") depends on it.

### 1.5 Propose phase plan

Map phases to remaining sessions:

| Session | Phase focus |
|---|---|
| 1 | Bootstrap + Phase 1 discovery (full project/initiative inventory) |
| 2–3 | Phase 2 deep-dive on High-significance projects |
| 4 | Phase 2 continues + Phase 3 cross-cutting themes |
| 5 | Phase 4 gap questionnaire → leader answers offline |
| 6 | Phase 5 final assembly + review |

Adjust to actual available sessions. Compress by dropping Medium/Low-significance Phase 2 deep-dives first.

---

## 2. Directory layout

```
institutional-knowledge/
├── AGENTS.md                    # schema, customized for this leader
├── index.md                     # catalog: every page, one-line summary, last-updated
├── log.md                       # append-only timeline
├── manifest.md                  # discovered sources + ingest status
├── phase-1-inventory.md         # project & initiative catalog (Phase 1 output)
├── projects/                    # one page per significant project (Phase 2)
│   └── <slug>.md
├── decisions.md                 # cross-project decision log
├── relationships.md             # people, stakeholders, engagement guidance
├── themes.md                    # cross-cutting principles, operating style (Phase 3)
├── domain-knowledge.md          # technical/industry/regulatory knowledge
├── org-navigation.md            # "how to get things done here"
├── historical-context.md        # origin stories, past failures, unwritten rules
├── gap-questionnaire.md         # Phase 4 questions for the leader
├── gap-answers.md               # leader's responses (input by user)
├── final-archive.md             # Phase 5 assembled document
└── raw/                         # immutable per-source extracts
    ├── email-<folder>/YYYY-MM.md
    ├── chat-<slug>/YYYY-MM.md
    ├── meeting-<series-slug>/YYYY-MM-DD.md
    └── sharepoint-<site-slug>/index.md
```

Naming: lowercase kebab-case. Dates: `YYYY-MM-DD` or `YYYY-MM`.

---

## 3. Phase 1 — Project & Initiative Discovery

**Objective.** Build a comprehensive catalog of every significant project, initiative, recurring forum, or workstream the leader owned or materially shaped.

### 3.1 Search strategy

Across all M365 sources, identify:
- Projects where the leader was owner / lead / primary decision-maker
- Recurring meeting series they organized or regularly attended as required
- Email threads with significant decision content (length > 5 messages, leadership participants)
- Documents they authored or were primary contributor to
- Channels / chats they created or are most active in

### 3.2 Time slicing

Break the tenure into eras and analyze each:
- **Early tenure** (Year 1–2): foundational work, what they inherited, first initiatives
- **Growth period** (Year 3–4): major initiatives, scope expansion, key hires
- **Recent / current** (last 2 years): current state, in-flight work, near-term commitments

### 3.3 Categorization

For each project, tag with one or more:
- Product / Engineering
- Strategic Planning / OKRs
- Team / Org Leadership (hiring, reorgs, performance culture)
- Cross-functional Initiatives
- Technical / Architecture Decisions
- Vendor / Partner Relationships
- Business Development / Customer
- Regulatory / Compliance

### 3.4 Output → `phase-1-inventory.md`

```markdown
# Phase 1 — Project & Initiative Inventory

## <Project name>
- **Period:** <start> – <end or "active">
- **Category:** <one or more from §3.3>
- **Role:** owner / lead / key contributor / advisor
- **Key collaborators:** [[relationships.md#name]], ...
- **Data sources found:** N emails, M Teams threads, K meetings, J documents
- **Significance:** High / Medium / Low
- **Why this rating:** one sentence
```

After Phase 1 is complete, **present the full inventory to the user, ask them to validate significance ratings and flag anything missing, then confirm before starting Phase 2.**

---

## 4. Phase 2 — Deep Knowledge Extraction (per project)

For each High-significance project (then Medium if time allows), produce `projects/<slug>.md`.

### 4.1 Decision archaeology

Search for signal phrases in emails/chats/meeting notes:
- "We decided to…" / "After discussing, we're going with…"
- "The recommendation is…" / "Leadership approved…"
- "We're not going to pursue X because…"
- "The tradeoff is…" / "The risk is…"
- "<Leader's first name> recommended…" / "Based on <leader>'s input…"
- "Reversing course…" / "We tried X and it didn't work…"

For each decision, capture: **what was decided, when, by whom, why, what alternatives were rejected and why, reversibility (easy / hard / one-way door), and source link.**

### 4.2 Problem-solution mapping

- Obstacles encountered → approach taken → outcome → lesson
- Failed approaches and why they failed (these are *especially* valuable — successors will be tempted to retry)
- Workarounds still in place

### 4.3 Relationships & context

- Stakeholders who had to be aligned
- Cross-team dependencies
- External factors (market, regulatory, vendor situations, org changes) that shaped the work

### 4.4 Lessons & insights

- What worked well (replicate)
- What the leader would do differently with hindsight
- Tribal knowledge — "everyone knows but nothing is written down"
- Advice for the person taking this over

### 4.5 Artifacts

- Key documents (specs, designs, proposals, decks) — with SharePoint/OneDrive links
- Reference email threads (subject, date range, participants)
- Meeting recordings/transcripts where critical
- Tools and systems where the work lives

### 4.6 Output template → `projects/<slug>.md`

```markdown
---
slug: <slug>
title: <project name>
period: <start> – <end>
category: <tags>
role: <owner | lead | contributor | advisor>
significance: high | medium | low
status: active | wrapping-up | dormant | done | handed-off
last_activity: YYYY-MM-DD
source_count: N
---

# <Project name>

## Executive summary
2–3 sentences: what this was, why it mattered, current state.

## Key decisions

| Decision | Date | Rationale | Alternatives rejected | Participants | Reversibility | Source |
|---|---|---|---|---|---|---|

## Problems and solutions

### Problem: <description>
- **Context:** what was happening
- **Approach:** what was done
- **Outcome:** result
- **Lesson:** takeaway
- **Source:** raw/<source>/<date>.md

## Key relationships
- **<Stakeholder>:** nature of relationship, how to work with them effectively

## Critical insights
1. …
2. …

## Successor guidance
What the leader would tell the person taking this over. Direct quote where possible; paraphrase otherwise and mark `[paraphrased]`.

## Reference artifacts
- <Doc title>: <webUrl> — what it contains
- Email thread "<subject>": <date range> — <participants>
```

### 4.7 Clarifying-question loop

After each project deep-dive, **stop and ask the user 2–3 clarifying questions** to fill gaps the raw signals can't:
- "Project X went quiet in March. Was it (a) dormant, (b) finished, (c) handed off, (d) still active but slow?"
- "You and <name> exchanged 40 emails about <topic> but never reached a decision in writing. What did you ultimately decide and why?"
- "I see <vendor> in 20 threads but can't tell if the relationship is healthy. How would you characterize it?"

Write answers into the project page immediately, marking quotes vs. paraphrase. This is the highest-leverage step in the whole skill.

### 4.8 Budget guards

- ~500 emails per session pass before checkpoint
- ~5 chats per pass
- One project deep-dive per session typically; two if signals are concentrated

If a lane has more to ingest, mark `in_progress` in `manifest.md` with a next-offset note and stop. Tell the user "this project has N more sources; continue or switch?"

---

## 5. Phase 3 — Cross-Cutting Themes

After enough High-significance Phase 2 deep-dives, run synthesis across them.

### 5.1 Leadership principles & operating style → `themes.md`

- How does the leader approach decision-making? (consensus, decisive, data-driven, intuition, etc.)
- What frameworks/mental models recur in their writing? (e.g., "reversible vs. one-way doors", "disagree and commit", named frameworks they cite)
- How do they prioritize competing demands?
- How do they handle disagreement?
- Communication style across audiences (board, peers, reports, customers)

### 5.2 Organizational navigation → `org-navigation.md`

- Go-to people for specific needs ("for budget questions → X; for legal → Y")
- Political dynamics navigated
- How alignment gets built across teams here
- Watch-outs ("don't go to X before Y has heard it first")

### 5.3 Domain expertise → `domain-knowledge.md`

- Technical/industry knowledge uniquely held by the leader
- Critical vendor/partner relationships and their history
- Regulatory/compliance knowledge
- Customer/market context

### 5.4 Historical context → `historical-context.md`

- Origin stories of current processes, systems, team structures
- Past failures whose lessons inform current approaches
- "Unwritten rules" of the organization
- Founders'/predecessors' decisions still in force

---

## 6. Phase 4 — Gap Analysis & Questionnaire

Review all extracted content for:
- Topics mentioned but not fully explained
- Decisions captured without clear *why*
- Projects without documented outcomes
- Implicit knowledge — things hinted at but never stated
- Forward-looking items (upcoming decisions, planned changes, roadmap)

### 6.1 Output → `gap-questionnaire.md`

Structure for the leader to answer offline:

```markdown
# Gap Questionnaire for <Leader>

> Please answer in as much detail as you can. These are gaps only you can fill. This is your last chance to capture context that will otherwise be lost.

## Project-specific

### <Project name>
1. <question>
2. <question>

## Strategic & leadership
1. What are the top 3 things your successor absolutely must know?
2. What mistakes did you make that others should avoid?
3. What relationships are most critical to maintain, and why?
4. What is the biggest risk or opportunity the team should be aware of?
5. What would you do differently if starting over?
6. What unfinished business matters most?
7. What decisions are pending that someone will need to make soon?
8. What context would be lost if you walked out today without documenting it?

## Domain & technical
1. <gap>
2. <gap>

## Organizational & cultural
1. <gap>
2. <gap>
```

Present the questionnaire and **pause**. The leader fills in `gap-answers.md` (the user pastes their responses or types them in a session). Do not advance to Phase 5 until answers are in.

---

## 7. Phase 5 — Final Archive Assembly

Once Phase 4 answers are in:

### 7.1 Assemble `final-archive.md`

```markdown
# <Leader name> — Institutional Knowledge Archive
## <Title/Role> | Tenure: <start> – <end>

### Document purpose
This archive captures the institutional knowledge, decisions, insights, and guidance from <leader>'s <N> years leading <areas>. It is a reference for <audience> and may be used to ground AI assistants for retrieval.

---

## Table of contents
1. Executive summary
2. Project & initiative catalog
3. Detailed project knowledge
4. Cross-cutting themes & principles
5. Key relationships & stakeholders
6. Domain expertise & technical knowledge
7. Organizational navigation guide
8. Historical context
9. Lessons learned & advice
10. Appendix — reference artifacts

## 1. Executive summary
[written last, drafted by you, edited with the leader]

## 2. Project & initiative catalog
[summary table from phase-1-inventory.md with significance ratings]

## 3. Detailed project knowledge
[full Phase 2 deep-dives, ordered by significance then chronology]

## 4. Cross-cutting themes & principles
[from themes.md]

## 5. Key relationships & stakeholders
[from relationships.md, with engagement guidance from gap-answers.md merged in]

## 6. Domain expertise & technical knowledge
[from domain-knowledge.md]

## 7. Organizational navigation guide
[from org-navigation.md]

## 8. Historical context
[from historical-context.md]

## 9. Lessons learned & advice
[consolidated from Phase 2 successor-guidance sections + Phase 4 answers]

## 10. Appendix — reference artifacts
[catalog of documents, email threads, meetings — with locations and access notes]
```

### 7.2 Review loop

1. Present the assembled archive section by section.
2. The leader edits in their own voice — terse, candid, direct.
3. Iterate until they approve.
4. Optionally export to `.docx` or `.pdf` (use the doc skill if installed).

---

## 8. Ingest workflows (reused across phases)

### 8.1 Email ingest (monthly chunks)

For each month within the horizon, most-recent first:

1. Read `manifest.md` for last ingested month per folder.
2. `m365_list_emails(startDate, endDate, limit: 50, select: 'id,subject,from,toRecipients,receivedDateTime,bodyPreview,hasAttachments,conversationId')`. **Omit `folder` arg for Inbox**; use `folder: 'sentitems'` for Sent. Page until exhausted.
3. De-noise: marketing, calendar invites (handled in meeting pass), bot notifications, OOO replies, single-line acks.
4. Group by `conversationId`.
5. Write `raw/email-<folder>/YYYY-MM.md` — one file per month.
6. **Lift** signals upward:
   - Recurring correspondents → `relationships.md`
   - Project keywords → new or updated `projects/<slug>.md`
   - Decision phrases → `decisions.md` + the relevant project page
   - Unanswered asks → flag for Phase 4 questionnaire
7. Update `manifest.md` row; append to `log.md`.

### 8.2 Teams chat ingest

1. `m365_list_chat_messages(chatId, top: 50, orderBy: 'createdDateTime desc')`. Page until older than horizon or last ingested ID. *(Note: `m365_list_chat_messages` accepts `orderBy`; the chat-**listing** tool `m365_list_chats` in §1.3 does not — don't pass `orderBy` there.)*
2. De-noise: system messages, reactions-only, join/leave.
3. Write `raw/chat-<slug>/YYYY-MM.md`. Lift to relationships/projects/decisions.

### 8.3 Meeting ingest

1. `m365_list_events(startDate, endDate, query: { orderBy: 'start/dateTime asc', select: 'subject,start,end,organizer,attendees,onlineMeeting,isAllDay,bodyPreview' })`.
2. Cluster by subject prefix → recurring series.
3. For each series: capture organizer, frequency, purpose, leader's role, attendee patterns.
4. If transcripts available (`m365_get_transcript` on the most recent instance via `onlineMeeting.joinUrl`), ingest latest 2-3 into `raw/meeting-<series-slug>/YYYY-MM-DD.md`.
5. One-off events with substantive body → record as `## Recent activity` entries in the relevant project page.

### 8.4 SharePoint / OneDrive ingest

1. `m365_get_recent_files(limit: 50)`; group by parent path (site/folder).
2. Write `raw/sharepoint-<site-slug>/index.md` with title, webUrl, lastModified, role (authored / co-authored / maintainer / editor).
3. Lift to project artifacts sections. **Do not download contents in bulk** — catalog + link is enough except when the leader explicitly wants a doc summarized.

---

## 9. Privacy & boundary rules

- Archive lives on the user's machine inside their M365 trust boundary. Never send outbound messages (email/Teams) referencing archive content during the build.
- 1:1 chats and private emails ARE in scope — this is the leader's own data, for their own knowledge-preservation use.
- HR, performance, compensation, health content is OUT of scope. If encountered, skip silently and note in `log.md` *without quoting*. **This exclusion is best-effort:** it relies on folder-name heuristics (§1.3) plus content judgment, not a guaranteed classifier — when a signal is ambiguous, err toward excluding it and flag borderline items with `[Review Required]` rather than silently including them.
- When the archive is eventually shared with successors or org leadership, the leader reviews `relationships.md`, `historical-context.md`, and the Phase 2 "Successor guidance" sections line-by-line — these are the most likely to contain content appropriate for the leader but not for broader distribution.
- Confidential vendor/partner content gets `[Confidential]` markers; sensitive personal observations get `[Review Required]`.

---

## 10. Quality, sensitivity, and provenance markers

- `[Inferred]` — derived from signals, not stated explicitly
- `[Uncertain]` — conflicting or weak evidence
- `[Not Found]` — looked for, didn't find
- `[Paraphrased]` — restating the leader's voice, not a direct quote
- `[Quote]` — verbatim from a source
- `[Review Required]` — sensitive; flag for leader review before sharing
- `[Confidential]` — vendor/partner/legal content, restricted distribution

Every Phase 2 decision and Phase 3 theme should carry source links to `raw/`.

---

## 11. Invocation patterns

- **First invocation / "start"** → bootstrap (Section 1).
- **"Continue" / "next"** → read `manifest.md` + last 10 `log.md` entries; resume the lane with status `in_progress` or propose the next `pending`.
- **"Phase 1" / "discovery"** → Section 3.
- **"Deep dive on <project>"** → Section 4 for that project.
- **"Themes" / "Phase 3"** → Section 5.
- **"Generate questionnaire" / "Phase 4"** → Section 6.
- **"Assemble final" / "Phase 5"** → Section 7 (requires `gap-answers.md` populated).
- **"What's left?"** → summarize `manifest.md` + phase progress.
- **"Ask me questions"** → clarifying-question pass against current gaps.

Each session, **start by reading `AGENTS.md`, `manifest.md`, the last 10 `log.md` entries, and `phase-1-inventory.md`** to recover state.

---

## 12. Definition of done

The archive is complete when:

- [ ] `phase-1-inventory.md` covers all significant projects/initiatives across the full tenure, with leader-validated significance ratings.
- [ ] Every High-significance project has a `projects/<slug>.md` with all 7 sections populated.
- [ ] `decisions.md` aggregates at least the top 20 cross-project decisions with rationale.
- [ ] `relationships.md` covers manager, all direct reports, top 25 collaborators, and key external stakeholders.
- [ ] `themes.md`, `org-navigation.md`, `domain-knowledge.md`, `historical-context.md` are non-empty.
- [ ] `gap-questionnaire.md` was sent, and `gap-answers.md` contains the leader's responses.
- [ ] `final-archive.md` is assembled and the leader has signed off.
- [ ] `index.md` reflects all pages; last `log.md` entry is a `final-review` pass with no open ⚠️ items.

If time runs out, prioritize: phase-1 inventory → top 5 High-significance project deep-dives → `gap-questionnaire.md` answered → final assembly. Cross-cutting themes (Phase 3) can be partially deferred — the project deep-dives already carry most of the value.
