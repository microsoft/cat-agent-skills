---
name: AI Demo Assistant
description: "Turns a customer name, line of business, and personas into a ready-to-seed Microsoft 365 Copilot demo — fictional Word/PowerPoint/Excel example files plus a full delivery and provisioning plan, with optional one-click seeding to OneDrive and Teams."
agentDescription: "Builds a scenario-driven content pack for a Microsoft 365 Copilot customer demo. From a customer name, line of business, and target personas, it proposes demo scenarios for operator approval, then generates fictional Word/PowerPoint/Excel example files plus an AI Demo Delivery Plan (persona roster with tenant-account mapping, email and Teams chat scripts, calendar meetings with agendas, a meeting transcript, and app-tagged Copilot prompt workflows grounded in the generated content). After approval it can OPTIONALLY seed the Office files into a customer-named OneDrive folder and optionally post the Teams chat scripts live; email, calendar, and recordings are drafted for manual loading. Use when the user asks to \"set up a Copilot demo\", \"build demo content for a customer\", \"seed a demo tenant\", \"create a demo delivery plan\", \"fill a demo tenant with realistic content\", or \"generate demo scenarios and sample files\". Do NOT use for sending real email, booking real calendar events, or production-tenant data.\n"
platforms: [Cowork]
tags: [demo, copilot, microsoft-365, sales-enablement, content, productivity]
author: Doak Moore
authorGithub: adilei
version: 1.0.0
---
# AI Demo Assistant

Turns a customer name + line of business + target personas into a polished,
scenario-driven **content pack** for a Microsoft 365 Copilot demo: example
files plus a written delivery/provisioning plan. After operator approval, it can
**optionally seed the generated Office files into a customer-named OneDrive
folder** and **optionally post the Teams chat scripts live** — both gated on
explicit confirmation. Everything else (email threads, calendar invites, meeting
transcripts) is drafted for a human to load.

## What can and can't be auto-seeded

| Asset | Auto-seed? | How |
|-------|-----------|-----|
| Word / PowerPoint / Excel files | **Yes** | Create a customer-named OneDrive folder and upload the files (Phase 3). |
| Teams chat messages | **Optional, with constraints** | Posts live via Graph; see Phase 4 caveats (timestamped now; one account posts only as itself). |
| Email threads | No | Drafted as scripts for manual paste/seed. Do not auto-send. |
| Calendar meetings | No | Drafted as scripts with agendas for manual creation. Do not auto-book. |
| Meeting **recordings / transcripts** | **No — not possible via any API** | Generate a transcript/script; to get a real recording, a person reads it aloud in a recorded Teams meeting. See Phase 4. |

The hard limits exist because Graph has no endpoint to backdate messages or to
inject a recording/transcript — those are produced only by a live recorded
meeting. Never claim a recording was seeded.

## When NOT to Use

- Sending real email, booking real calendar events, or writing to a **production
  tenant**. This skill targets demo tenants and the operator's own OneDrive with
  fictional content only.
- Real customer data or PII. All generated content is fictional dummy data.
- Generic single-file asks ("make a deck", "write an email") with no demo
  framing — use the docx/pptx/xlsx skills directly.

## Inputs (collect before building)

| Input | Required | Example |
|-------|----------|---------|
| Customer name | Yes | "Contoso Manufacturing" |
| Line of business (LOB) | Yes | "Field Service Operations" |
| Target personas / roles | Yes | "Service Dispatcher, Field Tech, Ops Director" |
| Segment / size | Optional (default: Enterprise) | "SMB", "Public Sector" |
| Region / language / tone | Optional (default: US English, professional) | "UK English, formal" |
| # of scenarios | Optional (default: propose 3–5) | "4" |
| Demo tenant domain | Optional (default: placeholder `{tenant-domain}`) | "M365x84272.onmicrosoft.com" |
| **OneDrive seeding target** | Optional (default: operator's own OneDrive) | "seed to my OneDrive" / a specific account |
| **Teams seeding** | Optional (default: scripts only, no live post) | "post the chats too" |

If customer, LOB, or personas are missing, ask **one** concise question to fill
the gaps. Do not over-interview — reasonable defaults cover everything else.
Seeding target and Teams seeding are only needed at Phase 3/4; don't block the
build on them.

## Workflow

### Phase 1 — Propose scenarios (confirmation gate)

1. From the LOB + personas, infer **3–5 realistic, high-impact Copilot
   scenarios** that map to a day-in-the-life of the named personas. Each scenario
   should show Copilot saving time across Outlook, Teams, and Office.
2. Present the proposed scenarios as a short numbered list — each with a one-line
   title, the persona it serves, and the Copilot "wow moment" it demonstrates.
3. **Stop and ask the operator to approve, edit, or swap scenarios** before
   building anything. Do not generate files until scenarios are confirmed.
4. **Pre-approval exception:** if the operator supplied their own scenario list
   (or explicitly said "just build it") in the initial request, treat that as
   approval — restate the scenario set in one line and proceed to Phase 2. The
   gate exists to prevent wasted builds, not to force a redundant round trip.

### Phase 2 — Build the content pack (after approval)

For the approved scenario set, generate every asset below. Use the customer name,
LOB, and personas throughout so content feels native. Save all deliverables to
the standard output directory for the current environment (the designated
`output/` folder).

**Before generating any Office file, read the relevant skill's SKILL.md
(docx / pptx / xlsx) and follow it** — these skills encode the validation and
rendering steps that keep files from arriving corrupted or ugly.

**Persona roster (build first — everything else references it).**
Create a small cast of fictional characters: name, title, which scenarios they
appear in, and a mapping column for the demo tenant account the operator will
use to seed as them (use real demo-tenant aliases if the operator provided a
tenant domain, otherwise `{firstname}@{tenant-domain}` placeholders the operator
can find-and-replace). Reuse this exact cast — same spellings, same titles —
across every email thread, chat script, meeting invite, and document byline.
Inconsistent names across artifacts are the fastest way to make a demo feel
fake and to confuse the person seeding the tenant.

**File naming and cross-reference consistency.**
Name every generated file with the pattern `S<NN>_<ScenarioShortName>_<DocType>.<ext>`
(e.g., `S01_EscalationTriage_ServiceReport.docx`). Any filename mentioned in an
email script, chat script, agenda, pre-read list, or the manifest must exactly
match a generated file — a plan that references files that don't exist (or are
named differently) breaks the operator's seeding run.

**A. Office example files (dummy data, clearly fictional)**
Name each file per the convention above and give it **real, specific content** so
the manifest descriptions (item 9) and the prompt workflows (item 8) have
something concrete to point at:
- **Word**: a representative document per scenario where it fits (e.g.,
  `S01_EscalationTriage_ServiceReport.docx` — a field service report with named
  sections such as Incident Summary, Root-Cause Analysis, Parts Replaced,
  Customer Impact, Recommended Follow-up). Target 2–4 pages — enough substance
  for Copilot to summarize impressively, no more.
- **PowerPoint**: a customer-branded-style deck (e.g., `S02_QBR_Deck.pptx` — a
  QBR with an SLA scorecard, a ticket-volume trend slide, a cost summary, and a
  roadmap). Target 8–12 slides, each with a clear, descriptive title.
- **Excel**: a data workbook with believable dummy rows and **named sheets and
  columns** (e.g., `S01_EscalationTriage_TicketLog.xlsx` — a "Tickets" sheet with
  TicketID, OpenedDate, Site, Priority, Status, AssignedTech, AgeDays, Resolution
  columns). Target 30–80 rows — enough for Copilot to find real patterns, small
  enough to stay readable.
- Compute any totals/percentages with a code tool before embedding them; never
  hand-calculate numbers in a file.

These size targets exist because example files only need to be rich enough to
make the live prompts land; oversized assets slow the build and add nothing to
the demo.

**B. AI Demo Delivery Plan**
Default to a single Word doc (it's the operator- and customer-facing artifact);
use markdown only if the operator asks for a lighter/faster format. Contains the
provisioning recipe a human loads into the demo tenant:
1. **Persona roster** — the fictional cast with the tenant-account mapping table
   described above.
2. **Scenario overview** — the approved scenarios and their personas.
3. **Email thread scripts** — for each scenario: subject, fictional participants
   (from the roster), and full body text for a realistic 2–4 message thread,
   ready to paste/seed. Threads should carry real substance — context, a
   decision or two, and an open question — so that "summarize this thread"
   produces a genuinely impressive answer. Reference the generated files as
   attachments/pre-reads by exact filename.
4. **Teams chat scripts** — short, natural 1:1 and group chat exchanges per
   scenario, using roster names. Keep each line attributed to a roster persona so
   the optional live-post step (Phase 4) knows who would send what.
5. **Teams structure** — a single **reusable team** name + description, and one
   **channel per scenario** with its purpose, so the operator builds it once and
   reuses across demos.
6. **Calendar meetings** — per scenario: subject, attendees (from the roster),
   relative date/time placeholders, an agenda, and pre-read links pointing to
   the generated files by exact filename.
7. **Meeting transcript/script** — for the headline scenario (or each, if the
   operator asks), a realistic meeting transcript in speaker-attributed form
   (`Name: line`), 12–25 turns, covering context, a decision, and an action item
   so that "summarize the meeting and list action items" lands. This is the
   substitute for a recording — see Phase 4 for how it becomes a real recording.
8. **Sample prompt workflows** — for each scenario, an **ordered workflow** of the
   exact Copilot prompts the presenter runs, written so each step builds on the
   one before it into a day-in-the-life narrative (typically *catch up → analyze →
   draft → polish → share*). Present each workflow as a numbered sequence, and
   **tag every prompt with the specific Copilot app it runs in** so the presenter
   knows exactly where to click. Use these canonical app names:
   - **Microsoft 365 Copilot Chat** — the standalone, work-grounded chat (the
     Copilot app, Teams/Edge side panel, or m365.cloud.microsoft); best for
     cross-app "catch me up across everything" prompts.
   - **Copilot in Outlook** — summarize a thread, draft a reply, coaching tips.
   - **Copilot in Teams** — summarize a chat or channel; and **Copilot in Teams
     meetings** for live/after-meeting recap and action items.
   - **Copilot in Word** — draft, summarize, or rewrite a document.
   - **Copilot in Excel** — analyze data, surface trends, build formulas.
   - **Copilot in PowerPoint** — create or summarize a deck, or build one from a
     Word file.

   **Write every prompt with the CRAFT framework** so each one is a complete,
   copy-paste-ready Copilot prompt instead of a vague ask:
   - **C — Context:** the situation and constraints ("ahead of the Northwind QBR
     on Demo Day −2…").
   - **R — Role:** the persona Copilot should adopt ("act as a service operations
     analyst…").
   - **A — Action:** the specific task ("summarize the top three escalation
     risks…").
   - **F — Format:** the shape of the output ("as a 5-bullet list", "a two-column
     table", "an email under 150 words").
   - **T — Target audience:** who the output is for ("for the Ops Director"), which
     also sets the tone.

   **Name the grounding file(s) inline in the prompt whenever it sharpens the
   result** — e.g. *"In `S01_EscalationTriage_TicketLog.xlsx`, which open
   tickets…"* — in addition to the separate `→ grounds on:` note. Naming the file
   inside the prompt is what makes file-scoped prompts (Copilot in
   Excel/Word/PowerPoint) reliably attach to the right artifact live on stage.

   Format each step as `App — "exact prompt"` with a `→ grounds on:` note naming
   the artifact(s) it draws from. Example workflow:
   ```
   Scenario 1 — Escalation triage  (persona: Service Dispatcher)
   1. Microsoft 365 Copilot Chat — "Ahead of my morning triage, act as my operations
      assistant and catch me up on everything about the Northwind escalation from the
      last week. Give me a short bulleted brief — what happened, current status, and
      what needs my decision — in a concise, professional tone for a dispatcher."
        → grounds on: S01_EscalationTriage_EmailThread, S01_EscalationTriage_TeamsChat,
          S01_EscalationTriage_StandupTranscript
   2. Copilot in Outlook — "Act as a customer-facing service manager. Summarize the
      Northwind escalation email thread, then draft a reply proposing the Tuesday
      repair window, as a ready-to-send email under 150 words in a reassuring,
      professional tone for the customer."
        → grounds on: S01_EscalationTriage_EmailThread
   3. Copilot in Excel — "In S01_EscalationTriage_TicketLog.xlsx, act as a data
      analyst: find the open tickets tied to the Northwind site and calculate their
      average age in days. Present it as a small table sorted oldest-first, for the
      Ops Director."
        → grounds on: S01_EscalationTriage_TicketLog.xlsx
   4. Copilot in Word — "Using S01_EscalationTriage_ServiceReport.docx, act as a
      technical writer and turn this field service report into a 5-bullet executive
      summary in a crisp, outcome-focused tone for the Ops Director."
        → grounds on: S01_EscalationTriage_ServiceReport.docx
   5. Copilot in Teams — "Act as a meeting scribe. Recap the escalation stand-up and
      list the action items as a table with owner and due-date columns, in a clear,
      neutral tone for the team."
        → grounds on: S01_EscalationTriage_StandupTranscript
   ```
   **Every prompt must be answerable from content that exists in this pack** —
   before finalizing, walk each step back to the specific thread, chat, meeting,
   transcript, or file it draws on (note it inline as shown above) and strengthen
   the content if the answer would be thin. A prompt with nothing behind it is a
   live-demo failure waiting to happen.
9. **File manifest / seeding checklist** — a table of every generated file:
   exact file name, a **detailed description of the file's contents**, which
   scenario / prompt-workflow step it supports, and **where it gets seeded**
   (which mailbox, channel, calendar, or OneDrive/SharePoint location). The
   description must be specific enough that the operator knows exactly what each
   file holds without opening it — name the **Word** section headings and page
   count, the **PowerPoint** slide titles, and the **Excel** sheet/tab names with
   their column headers and row count. One-line "a budget spreadsheet"
   descriptions are not enough. Example rows:
   ```
   | File name | Contents (detailed) | Supports | Seed to |
   |-----------|---------------------|----------|---------|
   | S01_EscalationTriage_ServiceReport.docx | 3-page field service report. Sections: Incident Summary, Root-Cause Analysis, Parts Replaced, Customer Impact, Recommended Follow-up. ~20 fictional part/labor line items. | Scenario 1, prompt 4 | Dispatcher OneDrive → "Copilot Demo - Northwind" |
   | S01_EscalationTriage_TicketLog.xlsx | Single sheet "Tickets" (62 rows). Columns: TicketID, OpenedDate, Site, Priority, Status, AssignedTech, AgeDays, Resolution. Mix of open/closed across 4 sites. | Scenario 1, prompt 3 | Dispatcher OneDrive folder |
   | S02_QBR_Deck.pptx | 10-slide QBR deck. Slides: Title, Agenda, SLA Scorecard, Ticket-Volume Trend, Top 5 Escalations, Cost Summary, Roadmap, Risks, Asks, Next Steps. | Scenario 2, prompts 1–2 | Ops Director OneDrive folder |
   ```
   For files seeded in Phase 3, include the live OneDrive folder path/link once
   created. This table is the operator's load checklist.
10. **Seeding timing note** — instruct the operator to load content **24–72
    hours before the demo**. Copilot answers from the Microsoft Graph semantic
    index, and freshly seeded content often isn't surfaced for hours; seeding
    minutes before going on stage is the most common cause of dead demos. This
    applies to OneDrive-seeded files too — seed them on the same schedule.

11. **Appendix — Sample file contents** — close the Delivery Plan with an
    **appendix that walks through each generated sample file in detail**, one
    subsection per file. For every file give the exact file name, its type and size
    (page / slide / row count), and a structured description of what's inside: for
    **Word**, each section heading and what it covers; for **PowerPoint**, every
    slide title and the key point on it; for **Excel**, each sheet/tab name with its
    column headers and what the rows represent. Call out the two or three "hero"
    details in each file that the sample prompts (item 8) rely on, so a presenter
    reading only the appendix knows exactly what Copilot will find. This appendix is
    the narrative companion to the seeding-checklist table (item 9): the table says
    *where each file goes*, the appendix says *what's inside it*.

**Date convention:** use relative dates anchored to demo day ("Demo Day −5",
"Demo Day −2, 9:00 AM") in all scripts and meetings rather than hard-coded
calendar dates. This keeps the pack evergreen across runs and ensures
recency-based prompts ("summarize my recent emails about the escalation")
actually work when the operator seeds on schedule.

### Phase 3 — Seed files to OneDrive (optional, on request)

Run this when the operator asks to seed/upload the files to OneDrive (e.g.,
"seed the files to my OneDrive", "put these in OneDrive"). If they didn't ask,
skip this phase and leave files in `output/` for manual loading.

1. **Confirm the target.** Default to the operator's own OneDrive
   (`GetDefaultDrive`, no `site_id`). If they named a different account/drive,
   resolve it explicitly — never guess a drive. Confirm the destination in one
   line before writing.
2. **Create the customer folder.** Derive a folder name from the customer name,
   prefixed for tidiness: `Copilot Demo - {Customer}` (sanitize illegal
   characters `\ / : * ? " < > |`). Place it under a stable parent
   (`Copilot Demos/` at the OneDrive root — create the parent first if missing).
   Use `CreateFolder`. If a same-named folder already exists, reuse it rather
   than failing; tell the operator you're reusing it.
3. **Upload the generated Office files** from `output/` into that folder using
   the available OneDrive upload capability. Upload only the demo Office files
   and the Delivery Plan — not scratch/working files. If the runtime cannot
   upload a given binary file directly, place it into a customer-named subfolder
   of the synced workspace output and report that OneDrive-sync location instead;
   never silently drop a file.
4. **Verify and report.** List the destination folder (`GetDriveChildren`) and
   confirm every intended file is present. Give the operator the folder link and
   the list of seeded files. Update the manifest's "where it gets seeded" column
   with the live OneDrive path.

**Folder-per-customer is the rule** — one customer-named folder per demo so runs
don't collide and the operator can find/clean up a demo's assets in one place.

### Phase 4 — Optional Teams chats & meeting recording

**Teams chat seeding (optional, on explicit request).** Only post live if the
operator says to (e.g., "post the chats too"). Otherwise the chat **scripts** in
the Delivery Plan are the deliverable. Before posting, state these constraints in
one line so expectations are right:
- Messages are timestamped **now** — Graph cannot backdate them. Recency prompts
  work; "last Tuesday" framing in the script won't match the real timestamp.
- A signed-in account posts **only as itself**. A multi-persona chat looks real
  only if each persona's tenant account posts its own lines; from one account,
  all lines appear from that one user. Tell the operator which is happening.
- Use `PostMessage`/`PostChannelMessage` with resolved recipients. Do not
  fabricate chat IDs.

**Meeting recording — generate a transcript, not a recording.** There is **no
API to create or upload a Teams meeting recording or transcript** — they exist
only after a real recorded meeting. So:
- Deliver the **meeting transcript/script** from Phase 2 (item 7) as the
  seedable artifact (a text/VTT file Copilot-grounded prompts can draw on if the
  operator seeds it as a file).
- If a genuine recording is required, instruct the operator to start a Teams
  meeting with the persona accounts, **turn on recording**, read the transcript
  aloud, and stop — Teams then produces a real recording + transcript tied to the
  event. This is the only path to an actual recording; never imply one was
  generated programmatically.

### Phase 5 — Deliver

1. Run the **delivery gate**: list the output directory and verify that every
   file named in the manifest exists on disk, and that no script or agenda
   references a file that wasn't generated. If Phase 3 ran, also verify the
   OneDrive folder contains the seeded files.
2. Give the operator a short summary: scenarios built, files produced (by name),
   where the Delivery Plan lives, and — if seeded — the OneDrive folder link and
   what was posted to Teams. Note that content is fictional dummy data, that
   email/calendar/recordings are drafted for manual loading, and the seeding
   timing window (24–72h before demo).

## Guardrails

- **Scoped live seeding only.** The only live writes this skill performs are
  (a) creating a OneDrive folder and uploading the generated files (Phase 3), and
  (b) optionally posting Teams chat messages (Phase 4) — both only when the
  operator asks, and only with fictional content. **Never auto-send email, never
  auto-book calendar events, and never write to a production tenant.** If asked
  to do those, output the script and explain the operator loads it.
- **Confirm destination before writing.** Resolve and restate the target
  OneDrive/account in one line before creating folders or uploading. Never guess
  a drive or post to an unconfirmed chat/channel.
- **No backdating, no fake recordings.** Do not claim messages were backdated or
  that a meeting recording/transcript was seeded — neither is possible.
- **All data is fictional.** Use invented names, companies, numbers, and dates.
  Never use the operator's real colleagues, real customer PII, or real internal
  figures. Use the demo tenant domain (or `{tenant-domain}` placeholder) for all
  fictional email addresses — never real-looking public domains.
- **No fabricated real facts.** Dummy data is fine; do not assert real-world
  statistics, real people, or real quotes as fact.
- **Confirmation gate on scenarios.** Always get operator approval of the
  scenario list before building files (Phase 1 → Phase 2), unless pre-approved
  per the Phase 1 exception.
- **Numeric accuracy.** Compute any embedded totals/percentages with a code tool.
- **Internal consistency.** One persona roster, one filename convention, and
  every live prompt traceable to seeded content. Consistency is what makes the
  demo feel real.
- **Folder-per-customer.** Seed each demo into its own customer-named OneDrive
  folder so runs don't collide.
- **Reusable across runs.** Keep customer/LOB/persona/tenant-domain/seeding
  target as variables so the same flow works for any segment and LOB.
