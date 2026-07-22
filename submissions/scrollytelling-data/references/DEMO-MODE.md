# DEMO DATA ONLY

# Demo Mode & Reference Implementation

Read this only when the user asks for a **demo**, an **example**, or "show me what this does" **without uploading a dataset of their own**. For a real upload, ignore this file and run the normal five-phase workflow on their file.

## The bundled sample dataset

`/app/skills/scrollytelling-data/assets/Basketball_Demo_Data.xlsx` — a basketball demo dataset, a multi-sheet workbook chosen because it exercises joins, rankings, grouping, and correlation chapters at once:

- **`Players`** (~1000 rows) — core stats columns (`Player Name`, `Team`, `Position`, `Age`, `Points/Game`, `Rebounds/Game`, `Assists/Game`).
- **`Teams`** (~30 rows) — lookup columns (`Team`, `City`, `Conference`, `Division`, `Home Arena`, `Founded`) that join to Players by Team, so the demo also shows the multi-sheet SQLite-join path (Phase 3).

It supports strong basketball narratives: player rankings, position-based comparisons, team/conference summaries, and two-variable correlations (`Points/Game` vs assists or rebounds). There's no built-in date column, so it has no required time trend.

**Three must-dos for this dataset:** (1) load both sheets and JOIN on `Team`; (2) explicitly use team metadata (conference/division/city/arena/founded) in at least one chapter so the join visibly matters; (3) when this bundled basketball demo is the input, use pink + green accent tones for theme/chart accents (demo-only rule, not for user-uploaded datasets).

## How to run a demo

Build the story from this sample exactly as you would for a real upload — inspect, find the story, prepare the JSON, build the HTML, deliver (Phases 1–5 in `SKILL.md`). Two differences from a real run:

- **Skip the upload/preprocessor gate.** The sample isn't under `/app/uploads/`, so read the path directly instead of running `analyzing-xlsx/preprocess.py` first.
- **Name the output** per the File Naming Convention (`basketball-demo-data-story-<YYYY-MM-DD>.html`) and write it to `/app/created/`.
- **Set expectations in the handoff message.** Say clearly this story uses bundled **demo data**, and that stories built from the user's real uploaded data are usually more relevant and often better than the demo output.
- **Avoid repeating chart types in the demo.** Don't use the same primary chart type in back-to-back chapters, and cap bar-chart chapters at two unless the user explicitly asks for a bar-heavy output.

You still make every editorial decision (chapter selection, order, narrative copy) — a demo should look like a real, hand-authored story, not a template dump.

**Keep the tone competitive but respectful.** It's fine to highlight leaders and trailing groups in basketball stats, but avoid insulting or demeaning language about players/teams. Keep analysis energetic and constructive.

## `scripts/build_story.py` — a complete worked reference

`scripts/build_story.py` (runtime path `/app/skills/scrollytelling-data/scripts/build_story.py`) is a full, end-to-end example generator: it loads a workbook, performs a pragmatic cross-sheet merge in pandas when keys overlap, writes the joined result to SQLite for aggregations, detects schema (entity / metric / time / geo / category), and assembles a complete Dark-Fire scrollytelling page.

**Use it as a reference, not as the thing you ship — and never run it as a shortcut for the demo.** Building the demo means authoring your own story exactly like a real upload (Phases 1–5). Do **not** execute `build_story.py` to produce the deliverable; its templated output is only a code example to read. Read `build_story.py` when you want a concrete, known-good example of how a piece fits together end to end — especially the parts that are fiddly to get right from prose alone:

- The `<head>`/`<body>` assembly with **Plotly loaded synchronously in `<head>`** so it's guaranteed defined before any chart dispatch fires (call `Plotly.newPlot` directly — no async poller).
- The single **`renderSection(id)`** function driven by *both* the `IntersectionObserver` **and** a 2.5s safety-net timeout, so charts and counters still appear if the observer never fires. Dispatch is keyed on the **section** id (`ch-map`, `ch-cat`, ...), not the chart-div id.
- The two isolated `IntersectionObserver`s (reveal vs. single-shot counter) and the lazy per-section chart dispatch with a `rendered` guard.
- The `renderCategoryBar()` / `renderScatterBubble()` / `buildHall()` helpers and the shared `BG` / `CFG` layout objects, plus the `js_esc()` label-escaping and the `node --check` pass after writing the file.
- Stat-card layout (`.s-card` / `.s-card-wide`) without the `margin:auto` / greedy-`flex` pitfalls.
