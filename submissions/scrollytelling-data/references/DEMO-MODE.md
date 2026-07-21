# DEMO DATA ONLY

# Demo Mode & Reference Implementation

Read this only when the user asks for a **demo**, an **example**, or "show me what this does" **without uploading a dataset of their own**. For a real upload, ignore this file and run the normal five-phase workflow on their file.

## The bundled sample dataset

`/app/skills/scrollytelling-data/assets/demo-agent-data.xlsx` — a US-states demo dataset, a multi-sheet workbook chosen because it exercises the map, regional, ranking, and correlation chapters at once:

- **`State Data`** (51 rows, incl. a `State`=`Total` rollup row) — geo + measure columns (State, Region, Demo Revenue ($), Demo Accounts).
- **`State Symbols`** (50 rows) — a lookup sheet (State, State Bird, State Flower, Year Admitted to Union, Demo Tourism Score) that joins to State Data by State, so the demo also shows the multi-sheet SQLite-join path (Phase 3).

It has US geography, a four-region grouping (South/West/Northeast/Midwest), rankings, and a two-variable (revenue vs. accounts, or revenue vs. tourism score) correlation — enough to fill hero → stats → big US map → regional breakdown → rankings → scatter → closing → epilogue. There's no date column, so it has no time trend.

**Three must-dos for this dataset:** (1) drop the `State`=`Total` rollup row before aggregating — left in, it dominates the map and every ranking; (2) show the states choropleth **large** — full-width and ~560–640px tall — converting full state names to two-letter postal codes for `locationmode:'USA-states'`; (3) **surface the `State Symbols` data** — don't let the bird/flower columns go unused. For roughly the **top 10 states** (by demo revenue), name each state's **State Bird** and **State Flower** somewhere in the story — e.g. as a captioned detail on the rankings/hall-of-fame chapter, in the map hover text, or a small annotated list beneath the top-10 ranking. It doesn't need to cover all 50; the top 10 is enough to make the joined lookup sheet visibly pay off (and demonstrates the multi-sheet SQLite join producing real narrative content, not just numbers).

## How to run a demo

Build the story from this sample exactly as you would for a real upload — inspect, find the story, prepare the JSON, build the HTML, deliver (Phases 1–5 in `SKILL.md`). Two differences from a real run:

- **Skip the upload/preprocessor gate.** The sample isn't under `/app/uploads/`, so read the path directly instead of running `analyzing-xlsx/preprocess.py` first.
- **Name the output** per the File Naming Convention (`demo-agent-data-story-<YYYY-MM-DD>.html`) and write it to `/app/created/`.

You still make every editorial decision (chapter selection, order, narrative copy) — a demo should look like a real, hand-authored story, not a template dump.

**Keep the tone positive and sensitive to every state.** These are real home states, so no state should be framed as the "best," "worst," "winner," "loser," "bottom," or "falling behind." Present differences as scale or character, not merit — a smaller market has "room to grow," a state's bird/flower/tourism gives it its own charm. Even where a ranking or choropleth necessarily orders states, write copy that honors the whole set rather than crowning one and diminishing the rest.

## `scripts/build_story.py` — a complete worked reference

`scripts/build_story.py` (runtime path `/app/skills/scrollytelling-data/scripts/build_story.py`) is a full, end-to-end example generator: it loads a workbook, joins multiple sheets in SQLite, detects schema (entity / metric / time / geo / category), runs the standard aggregations, and assembles a complete Dark-Fire scrollytelling page.

**Use it as a reference, not as the thing you ship — and never run it as a shortcut for the demo.** Building the demo means authoring your own story exactly like a real upload (Phases 1–5). Do **not** execute `build_story.py` to produce the deliverable; its templated output is only a code example to read. Read `build_story.py` when you want a concrete, known-good example of how a piece fits together end to end — especially the parts that are fiddly to get right from prose alone:

- The `<head>`/`<body>` assembly with **Plotly loaded synchronously in `<head>`** so it's guaranteed defined before any chart dispatch fires (call `Plotly.newPlot` directly — no async poller).
- The single **`renderSection(id)`** function driven by *both* the `IntersectionObserver` **and** a 2.5s safety-net timeout, so charts and counters still appear if the observer never fires. Dispatch is keyed on the **section** id (`ch-map`, `ch-cat`, ...), not the chart-div id.
- The two isolated `IntersectionObserver`s (reveal vs. single-shot counter) and the lazy per-section chart dispatch with a `rendered` guard.
- The `renderCategoryBar()` / `renderScatterBubble()` / `buildHall()` helpers and the shared `BG` / `CFG` layout objects, plus the `js_esc()` label-escaping and the `node --check` pass after writing the file.
- Stat-card layout (`.s-card` / `.s-card-wide`) without the `margin:auto` / greedy-`flex` pitfalls.
