# Institutional Knowledge Archivist

When a long-tenured leader leaves, the org rarely loses the *what* — project
trackers and docs survive. It loses the ***why***: the decision rationale, the
rejected alternatives, the stakeholder history, and the unwritten rules that
lived only in that person's head.

This skill turns a departing senior leader's **Microsoft 365 signals** — emails,
Teams chats, meetings, and SharePoint/OneDrive contributions — into a
structured, interlinked **institutional-knowledge archive** a successor (or an
AI assistant) can read on day one and ground on for years.

It runs as a **guided, multi-session sprint** rather than a one-shot dump. You
curate and answer clarifying questions; the agent does all the writing.

## Before you start

- **A connected Microsoft 365 account** for the leader (or a delegate working on
  their behalf). The skill reads mail, Teams chats, calendar/meetings, and
  recent files via the agent's `m365_*` tools.
- **Time**: plan a ~1-week sprint across **5–6 sessions of 60–90 minutes**.
  Session 1 does discovery; later sessions go deep, then assemble.
- Optional: a document skill installed if you want to export the final archive
  to `.docx`/`.pdf`.

Nothing leaves the M365 trust boundary — the archive is written to the user's own
`Documents/` folder. HR, compensation, performance, and health content is
automatically out of scope.

## How to use it

Invoke it in plain language, e.g.:

- *"Help me build an institutional knowledge archive for our departing VP."*
- *"Capture Doug's decision history before he retires next month."*
- *"Start the institutional-knowledge skill."*

The skill then walks you through **five gated phases**, confirming with you
before advancing each one:

1. **Discovery** — a complete inventory of the leader's projects, initiatives,
   recurring forums, and workstreams across their whole tenure. You validate the
   significance ratings.
2. **Deep extraction** — per high-significance project: *decision archaeology*
   (what was decided, when, by whom, why, what was rejected, how reversible),
   problem→solution→lesson mapping, key relationships, and successor guidance.
3. **Cross-cutting themes** — leadership principles, org-navigation guidance,
   domain expertise, and historical context synthesized across projects.
4. **Gap questionnaire** — the questions only the leader can answer, generated
   from everything the signals *couldn't* reveal. The leader fills these in
   offline.
5. **Final assembly** — a single, leader-approved archive document.

It's **resumable and idempotent**: every session reads a `manifest.md` and picks
up where the last one stopped, and re-ingesting the same source merges rather
than duplicates.

## Good to know

- **The highest-value step is the clarifying-question loop.** After each project
  deep-dive the agent asks you 2–3 targeted questions ("you and X exchanged 40
  emails about Y but never wrote down the decision — what did you land on and
  why?"). That's where tacit knowledge gets captured — don't skip it.
- **Breadth before polish.** Early passes bias toward capturing raw signal; if
  you run out of time, raw breadth beats a half-polished narrow archive.
- **Privacy is on you at share time.** The archive includes private 1:1 and email
  signal by design (it's the leader's own data). The agent flags sensitive
  sections with `[Review Required]` / `[Confidential]`, but the leader should
  review `relationships.md`, `historical-context.md`, and the "Successor
  guidance" sections line-by-line before sharing with anyone.
- **Tool names may vary by host.** The instructions reference `m365_*` tool
  names; if your Cowork/Scout environment exposes M365 under different names, the
  workflow is identical — just map the tool names.

## What you end up with

```
institutional-knowledge/
├── phase-1-inventory.md   ← project & initiative catalog
├── projects/<slug>.md     ← one decision-rich deep-dive per project
├── decisions.md           ← cross-project decision archaeology
├── relationships.md       ← stakeholder roster + how to work with each
├── themes.md              ← leadership principles & operating style
├── domain-knowledge.md    ← technical/industry/regulatory knowledge
├── org-navigation.md      ← "how to get things done here"
├── historical-context.md  ← origin stories, past failures, unwritten rules
├── gap-questionnaire.md   ← what only the leader can answer
├── final-archive.md       ← the assembled, approved document
└── raw/                   ← faithful per-source extracts (audit trail)
```
