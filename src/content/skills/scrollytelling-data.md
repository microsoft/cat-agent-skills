---
name: Scrollytelling Data
description: Turns data into a scroll-driven HTML story.
agentDescription: "Turns an uploaded dataset (.xlsx, .csv, .json, or PDF tables) into a self-contained, scroll-driven HTML data story with animated Plotly charts, counting stat cards, and narrative chapters. Use when the user asks for a data story, scrollytelling report, or an interactive narrative write-up of a dataset. If the user asks for a demo or example with no dataset of their own, build the story from the bundled sample workbook at assets/Basketball_Demo_Data.xlsx."
platforms: [Copilot Studio]
tags: [data, visualization, storytelling, reporting]
author: AndrewHessMSFT
authorUrl: "https://github.com/AndrewHessMSFT"
authorGithub: AndrewHessMSFT
version: 1.0.0
createdAt: 2026-07-21
updatedAt: 2026-07-21
bundle: bundles/scrollytelling-data.zip
---
# Skill: Data Scrollytelling — Interactive HTML Story from Any Dataset

A workflow for turning any uploaded dataset into a self-contained, scroll-driven HTML data story — no server, no install, just open in a browser. Charts animate in on scroll, stats count up, and the page tells a narrative from the data automatically.

---

## What This Skill Produces

A single `.html` file that:
- Opens in any browser with zero setup
- Tells the data's story chapter by chapter as the user scrolls
- Renders interactive Plotly.js charts (map, bar, scatter, heatmap, line, pie/donut)
- Animates stat counters, shame lists, and card reveals on scroll via IntersectionObserver
- Includes a fixed progress bar and chapter indicator
- Is a single self-contained HTML file — Plotly.js loads from a CDN at view time

---

## How to Talk to the User While Working

The internal workflow uses technical steps (SQL, JSON, HTML, Plotly), but **never expose that vocabulary in chat messages to the user**. Narrate progress the way a friendly analyst would explain it to a non-technical stakeholder — plain language, short sentences, and a sprinkle of emoji to keep it warm. Never say "SQL," "JSON," "HTML," "Plotly," "dataframe," "aggregation," or similar implementation terms in a user-facing message.

**Don't send one message per phase and go quiet — send one per meaningful sub-step.** Phase 1 (inspect) and Phase 3 (aggregations) are the slowest parts and can easily run 30–60+ seconds with no output, which feels stalled. Break each phase into several small checkpoint messages as the work actually happens, so the user sees steady progress instead of a long silence.

**Don't number the checkpoints.** Skip any `(Step X/Y)` counter — lead each message with its emoji and a short, plain-language title instead. The emoji and wording already convey momentum; a running count just invites off-by-one errors and false precision about how much is left.

**Phase 1 — Inspect:**
- 👀 "Taking a first look at your data..."
- 📐 "Found `<N>` rows and `<N>` columns — checking what each one means..."
- 🏷️ "Spotted your key categories: `<examples>`..."
- 📅 "Nice, there's a time column too — that unlocks a trend chapter..." *(skip if no time column)*

**Phase 3 — Crunching the numbers:**
- 🔢 "Counting up the totals..."
- 🏆 "Ranking your top performers — your #1 is `<top entity>`..."
- 📊 "Seeing how big the gap is from first to last..."
- 🥧 "Breaking things down by category..."
- 📈 "Mapping out the trend over time..." *(skip if no time column)*
- 🗺️ "Plotting things out by location..." *(skip if no geo column)*
- 🧮 "Double-checking everything adds up..."

**Phase 4 — Building the story:**
- ✍️ "Writing the story chapters..."
- 🔍 "Calling out the standout finding: `<insight>`..."
- 🎨 "Styling it up and wiring in the charts..."
- 🛠️ "Putting all the pieces together..."

**Delivery:**
- ✅ "Your story is ready! Take a look 👇"

The bullets above are an illustrative full run (time + geo). Drop any that don't apply to the dataset (no time column → skip the trend/📈 lines; no geo → skip the 🗺️ line), and split a slow phase into more checkpoints when it helps — just don't attach step numbers to any of them.

**Ranking and chapter-writing are where the user most wants to feel progress — so give each a beat or two beyond the headline, not one line and then silence.** Fold a concrete finding into the ranking update (the actual #1, or the size of the gap) and call out the standout insight while writing chapters, using real entity names and numbers (e.g. "🥇 Sales leads with 3,120 hours saved...") rather than generic placeholders. Aim for a couple of extra updates here — enough to feel alive, without an emoji on every micro-step.

Keep each line short — a few words plus one emoji — but favor *more, smaller* updates over fewer, longer silences. If a step is genuinely quick, it's fine to skip its checkpoint; if a step is slow (large file, many columns, many aggregations), split it into even more checkpoints rather than leaving the user waiting on one message.

Keep these updates to one short line each — they're a friendly heartbeat while work happens in the background, not a status log. Save the substance (the actual findings, chapter takeaways, etc.) for the final delivered story itself.

---

## Supported Input Formats

- `.xlsx` / `.xls` — via openpyxl / pandas
- `.csv` — via pandas
- `.json` — via json + pandas
- `.pdf` — extract tables via pdfplumber, then treat as tabular data
- Any tabular data with at least one numeric column and one categorical column

---

## Demo Mode — Build a Story with No Upload

This skill ships with a bundled sample workbook so you can produce a full, feature-complete story even when the user hasn't uploaded anything.

**When to use it:** If the user asks for a "demo", "example", "show me what this does", or otherwise wants to see the skill in action without providing their own file, use the bundled workbook as the input dataset:

```
scrollytelling-data/assets/Basketball_Demo_Data.xlsx
```

At runtime the full path is `/app/skills/scrollytelling-data/assets/Basketball_Demo_Data.xlsx`.

**What's in it:** A basketball demo dataset — a two-sheet workbook built to exercise joins, rankings, team breakdowns, and correlation chapters:
- **`Players`** (~1000 rows): `PlayerID`, `Player Name`, `Team`, `Position`, `Age`, `Points/Game`, `Rebounds/Game`, `Assists/Game`.
- **`Teams`** (~30 rows, lookup): `Team`, `City`, `Conference`, `Division`, `Home Arena`, `Founded` — joins to `Players` on `Team` (the sheet-to-sheet SQL JOIN from Phase 3).

**How to run a demo:**
1. Treat the bundled `.xlsx` above as the uploaded dataset and run the **full five-phase workflow** on it exactly as you would a user's file — no shortcuts.
2. Because the demo file lives in the skill folder (not `/app/uploads/`), the Phase 1 upload gate doesn't apply — read it directly. Running `preprocess.py` is optional here (fine for a consistent inspection step, but not required to unlock the file).
3. Load **both** sheets and JOIN them in SQL (Phase 3) so the story can combine player stats with team metadata (conference/division/city/arena/founded).
4. Prioritize chapters that fit this dataset: top scorers, team-level averages, position splits, conference/division comparisons, and correlation views (`Points/Game` vs `Assists/Game` or `Rebounds/Game`).
5. Use the default chart-selection rules; there is no built-in geo field and no required map chapter for this demo.
6. Narrate the friendly emoji checkpoints (no step numbers). There's no built-in time column, so skip time-trend chapters unless you derive a valid time dimension from the user prompt.
7. **Basketball demo color rule (demo-only):** when the input is this bundled basketball demo workbook, switch accents to pink + green tones for the page/theme and chart accents. Keep it constrained to that demo path only; for user-uploaded datasets, use the normal theme rules.
8. Name the output per the File Naming Convention (e.g. `basketball-demo-data-story-YYYY-MM-DD.html`).
9. In the delivery message, explicitly remind the user this run used bundled **demo data**, and set expectation that stories built from their real uploaded data are usually more relevant and often better than the demo output.
10. **Basketball demo anti-repeat rule (demo-only):** avoid repeated chart patterns. Do not place the same primary chart type in back-to-back chapters, and cap bar-chart chapters at two total unless the user explicitly asks for mostly bar charts.

**Tone — competitive but respectful.** It's fine to discuss leaders and lagging groups in basketball stats, but avoid insulting or demeaning language about players/teams. Keep the copy energetic and constructive.

If the user later uploads their own dataset, use that instead — the demo file is only a fallback when no dataset is provided.

---

## The Five-Phase Workflow

### Phase 1 — Inspect & Understand the Data

Always start here. Never skip.

```bash
python /app/skills/analyzing-xlsx/scripts/preprocess.py <file>
cat /app/workspace/_artifacts/<hash>/xlsx/1.0/metadata.json
```

**Sandbox file access — run the preprocessor first, every time.** In the Copilot Studio sandbox, uploaded files under `/app/uploads/` are gated: reading one directly with pandas/openpyxl (or `cd`-ing into `/app/uploads/` first) gets blocked before the preprocessing step has run. Always run `preprocess.py` against the uploaded file **before** any other tool touches it — that's what satisfies the gate and unlocks direct reads for the rest of the workflow. If a read gets blocked, the fix is to run the preprocessor, not to retry the same read or work around the block.

**Shell execution in this sandbox.** Some Python scripts in this environment need to be run through `/usr/local/bin/sandbox-exec` rather than invoked directly (e.g. `sandbox-exec python script.py <args>`). If a plain `python`/`python3` invocation fails or is blocked, retry it wrapped in `sandbox-exec` before assuming the script itself is broken.

Identify:
- Sheet names and row/column counts
- Which columns are **categorical** (names, types, states, categories)
- Which columns are **numeric** (costs, counts, scores, durations)
- Which column is the **primary entity** (the "who" or "what" — e.g. pit master, product, customer)
- Which column is the **primary metric** (the "how much" — e.g. damage cost, revenue, quantity)
- Whether there is a **time column** (enables timeline chart)
- Whether there is a **geography column** (state, country → enables map)
- If the file has **multiple sheets**, whether they relate via a shared key
  (e.g. a foreign-key-style ID column) — this determines whether they need
  to be joined in SQLite before aggregating (see Phase 3)

Run SQL via SQLite to compute:
- Total count of records
- Sum/avg of primary metric
- Top N entities by metric
- Distribution of categorical columns (outcomes, types, categories)
- Monthly/weekly/daily aggregation if time column exists
- Geographic aggregation if geo column exists

### Phase 2 — Find the Story

Before writing a single line of HTML, answer these questions from the data:

| Story Beat | Question to Answer |
|---|---|
| **The Scale** | How big is this? Total count, total value, biggest single number |
| **The Where** | Is there geography? Which location dominates? |
| **The Who** | Who are the top/bottom performers? Hall of fame or shame? |
| **The What** | Which category/type causes the most impact? |
| **The How** | Which method/tool/grill/channel performs best or worst? |
| **The When** | Is there a trend over time? Spike? Seasonal pattern? |
| **The Worst** | What are the top 5 most extreme individual records? |
| **The Verdict** | What is the one-line takeaway? |
| **The Fix** | Given the data, what does the reader need in a closing chapter — takeaways, recommendations, external context, a benchmark? |

Each answer becomes a **chapter**. Aim for 6–8 chapters. Too few = shallow. Too many = boring.

### Phase 3 — Prepare the Data as JSON

Extract all data needed for charts and inject it as a JavaScript constant in the HTML. This is what makes the file self-contained.

```python
import json, sqlite3, pandas as pd

# Load data
conn = sqlite3.connect(":memory:")

# Single-sheet / CSV / JSON: one dataframe, one table
df = pd.read_excel(path) # or pd.read_csv, etc.
df.to_sql("data", conn, index=False)

# Multi-sheet Excel: preferred live-workflow approach is to load EVERY sheet
# into its OWN table (named after the sheet), then JOIN them in SQL. This is
# how sheet-to-sheet relationships (e.g. a "transactions" sheet referencing a
# "customers" sheet by ID) are normally resolved. (A reference script may use
# a pragmatic pre-merge, but the runtime workflow should still favor SQL joins.)
sheets = pd.read_excel(path, sheet_name=None)  # dict of {sheet_name: df}
for sheet_name, sheet_df in sheets.items():
    sheet_df.to_sql(sheet_name, conn, index=False)
# Example: SELECT * FROM transactions JOIN customers USING (customer_id)

# Run all aggregations
summary = pd.read_sql_query("SELECT ...", conn)
monthly = pd.read_sql_query("SELECT ...", conn)
# etc.

# Serialize everything to one dict
data = {
    "total_count": int(...),
    "total_value": float(...),
    "top10_names": [...],
    "top10_values": [...],
    "monthly_x": [...],
    "monthly_y": [...],
    "categories": [...],
    "category_values": [...],
    "state_codes": [...],
    "state_values": [...],
    "worst_records": df_worst.to_dict(orient='records'),
}
with open("/app/workspace/story_data.json", "w") as f:
    json.dump(data, f)
```

Save to `/app/workspace/story_data.json`. Then build the HTML in a separate script that reads this file, so the two phases are independent and the HTML builder can be re-run without re-querying.

### Phase 4 — Build the HTML Story

Write the HTML to `/app/workspace/build_story.py` using the `create` tool, then run it with `python3`. Always write to a file — never use a heredoc with nested quotes.

**Default story scaffold (a starting point, not a fixed recipe):**

```
[HERO]          Full-screen dramatic title + subtitle + scroll cue
[STAT SPLASH]   Animated counting stat cards (5–6 key numbers)
[CHAPTER]       Geography / where (choropleth map)
[CHAPTER]       Method / tool / type (bar chart)
[CHAPTER]       Category / what (horizontal bar)
[CHAPTER]       Outcomes / distribution (pie or donut)
[CHAPTER]       Timeline / when (dual-axis line chart)
[DIVIDER]
[CHAPTER]       Hall of shame/fame — top N entities (animated rows + bars)
[DIVIDER]
[CHAPTER]       Worst/best 5 individual records (animated cards)
[DIVIDER]
[CHAPTER]       Closing chapter — takeaways, recommendations, news/context, or benchmark (AI decides which fits)
[EPILOGUE]      One-paragraph verdict + badge
```

This scaffold exists so you're never starting from a blank page, and the hero → stat splash → epilogue bookends are worth keeping almost always — they're what make the page feel like a complete story rather than a loose set of charts. **Everything in between is a decision, not a checklist:**

- **Order chapters by narrative strength for this specific dataset**, not by the list position above. If "the who" (top performers) is the most surprising finding, it can lead; geography doesn't have to go first just because it's listed first here.
- **Skip, merge, split, or reorder chapters freely.** No timeline data → drop that chapter. Two story beats are thin on their own but powerful together → combine them into one chapter with two charts. A single beat has enough depth for two angles → split it into two chapters.
- **Add chapters the scaffold doesn't mention** when the data reveals an angle worth its own beat (a correlation, an anomaly, a segment comparison) — the Phase 2 story-beat table is a prompt for thinking, not an exhaustive chapter list.
- **6–8 chapters is a rough guide, not a hard target** — let the data's actual depth decide the count.

Use your judgment the same way an editor would: the goal is the strongest possible narrative from *this* dataset, not a template filled in the same order every time.

**Chapter layout pattern (two-column):**

```html
<section class="chapter" id="ch1">
  <div class="c-inner">          <!-- text LEFT, chart RIGHT -->
    <div class="reveal">
      <div class="c-num">Chapter 01</div>
      <h2 class="c-head">Narrative <em>headline here.</em></h2>
      <p class="c-body">2–3 sentences. <strong>Bold the key insight.</strong></p>
    </div>
    <div class="chart-box reveal" style="transition-delay:.2s">
      <div id="cChart1" style="height:460px"></div>
    </div>
  </div>
</section>
```

Use `.c-inner.flip` to alternate text left/right between chapters for visual rhythm.
Use `.c-inner.full` for full-width chapters (timeline, hall of shame, worst records).

**Rendering contract — two rules that keep charts and counters from silently dying:**

1. **One `renderSection(id)` function, driven by both the observer and a safety-net.** Put all lazy chart/section rendering in a single named `renderSection(id)` function. Drive it from the `IntersectionObserver` **and** from a 2.5s `setTimeout` fallback. The observer alone is not enough — if it never fires (no scroll, reduced-motion, layout quirk), sections stay blank. The safety-net must do **all three** things the observers do — reveal, count, and render:

   ```javascript
   function renderSection(id) {
     if (rendered[id]) return; rendered[id] = true;
     if (id==='ch-map')  { /* Plotly.newPlot('mapChart', ...) */ }
     // ...one branch per section...
   }
   const sectionObs = new IntersectionObserver(es =>
     es.forEach(e => { if (e.isIntersecting) renderSection(e.target.id); }), {threshold:0.15});
   document.querySelectorAll('section[id]').forEach(s => sectionObs.observe(s));

   setTimeout(() => {                       // guaranteed fallback
     document.querySelectorAll('.reveal').forEach(el => el.classList.add('vis'));
     document.querySelectorAll('.num[data-target]').forEach(n => counter(n)); // counters too!
     document.querySelectorAll('section[id]').forEach(s => renderSection(s.id)); // charts too!
   }, 2500);
   ```

   **Dispatch on the SECTION id, not the chart-div id.** The observer watches `section[id]` elements, so `e.target.id` is the section's id (e.g. `ch-map`), *not* the inner chart div (`mapChart`). Match `renderSection` branches against the section ids or every branch silently no-ops.

2. **Syntax-check the generated JS with `node --check` before shipping.** One stray character — most commonly an unescaped apostrophe inside a single-quoted string (`'Chapter 06 · Who's Buying'`) — throws a `SyntaxError` that kills the *entire* `<script>` block, so *nothing* runs: blank charts and every counter frozen at 0. Escape apostrophes (`Who\'s`) and run `node --check` on the script before delivery. `scripts/build_story.py` does this automatically after writing the file.

### Phase 5 — Deliver

```python
with open("/app/created/<dataset-name>-story-YYYY-MM-DD.html", "w") as f:
    f.write(html)
```

Always write to `/app/created/` so it is returned as an attachment.

---

## Chart Selection Guide

This table is a **starting point for the most common data shapes** — use it to move fast, but override the pick whenever a different chart would reveal the specific story in front of you more clearly (e.g. a scatter instead of bars when the real story is a correlation, or small multiples instead of one crowded chart when comparing many categories at once).

| Data Shape | Common Choice | Plotly Type |
|---|---|---|
| Rankings (top N entities) | Vertical bar | `bar` |
| Rankings with long names | Horizontal bar | `bar` + `orientation:'h'` |
| Share / composition | Donut | `pie` + `hole:0.55`, `showlegend:false`, on-slice `label+percent` — **max one donut/pie per story** — see "Donut / Pie Charts" |
| Two variables per entity | Scatter / bubble | `renderScatterBubble()` — conditional pattern, see `references/CHART-PATTERNS.md` |
| Geographic (US states) | Choropleth | `choropleth` + `locationmode:'USA-states'` + `geo:{scope:'usa'}` — see `references/CHART-PATTERNS.md` |
| Geographic (world) | World map | `choropleth` + `locationmode:'country names'` (or `'ISO-3'`) + `geo:{scope:'world'}` — see `references/CHART-PATTERNS.md` |
| Two metrics over time | Dual-axis line | Two `scatter` traces + `yaxis2` — see `references/CHART-PATTERNS.md` |
| Category × category intensity | Heatmap | `heatmap` |
| Distribution of values | Box plot | `box` |
| Distribution shape | Histogram | `histogram` |
| Part-to-whole with many categories or a hierarchy | Treemap / sunburst | `treemap` / `sunburst` |
| Ordered stages / drop-off (e.g. Scoping → Piloting → Live) | Funnel | `funnel` |
| Composition across a few groups | 100% stacked bar | `bar` + `barnorm:'percent'` + `barmode:'stack'` |
| Cumulative build-up / running total | Waterfall | `waterfall` |
| Multi-attribute profile of a few entities | Radar | `scatterpolar` + `fill:'toself'` |
| Flow / transfer between categories | Sankey | `sankey` |
| Density across two numeric axes | Density heatmap | `histogram2dcontour` |

**Right chart for the data first, variety second — never "fancy for its own sake."** The chart type must always be driven by what the data is actually saying: a funnel only if the categories are real ordered stages, a treemap only for genuine part-to-whole/hierarchy, a radar only when comparing a few entities across several attributes, and so on. Never reach for a fancier chart just because it looks impressive — a forced treemap or sankey that doesn't match the data is worse than a plain bar. *Within* that constraint, aim for variety: don't render five bar charts in a row when some chapters would genuinely be clearer as a treemap, funnel, waterfall, or radar. So: pick the correct chart for each chapter's data, and let that naturally produce a mix of shapes rather than a wall of identical bars. The only hard caps are the composition ones (max one donut/pie). Keep every chart readable on the dark theme (spread `...BG`, set explicit label/tick colors) and render it through `renderSection(id)` with a real `height` on the div.

**Conditional chart types — read only when the data calls for them:** maps/choropleth, scatter/bubble correlations, and bar+overlay (`yaxis2`) combos each only apply to some datasets (a geo column, a real two-variable story, a dual-metric pairing). Their detailed rules, gotchas, and shared helper functions (including `renderScatterBubble()`) live in [`references/CHART-PATTERNS.md`](references/CHART-PATTERNS.md) — open that file as soon as Phase 1 inspection shows one of those data shapes is present, rather than loading it for every story.

### Horizontal Bar Charts (category-vs-value) — Get the Axes Right

Charts like "resolution time by priority" (Low/Medium/High/Critical vs. hours) are a classic failure point: it's easy to end up with vertical columns misaligned to the category axis, or a category silently missing its bar. This tends to happen because each chapter's chart is hand-written separately and one copy-paste drifts from the rest — the fix is to stop hand-writing bar traces per chapter and go through one shared helper instead.

**Use one shared JS function for every "category compared to a metric" bar chart, regardless of dataset or chapter.** Never write a bespoke `Plotly.newPlot` bar trace per chapter — call this helper so the rules below are enforced in one place instead of re-implemented (and potentially mis-implemented) each time:

```javascript
// Generic helper for ANY category-vs-metric bar chart (priority, category, channel, region, etc.)
// Call this the same way regardless of what the categories/metric actually represent.
function renderCategoryBar(divId, categories, values, opts = {}) {
  if (categories.length !== values.length) {
    throw new Error(`${divId}: categories/values length mismatch (${categories.length} vs ${values.length})`);
  }
  // Pair, then sort/order once from a single source of truth — never build x/y as two separately-derived arrays.
  const order = opts.categoryOrder;                 // optional fixed order, e.g. ['Critical','High','Medium','Low']
  const pairs = categories.map((c, i) => [c, values[i]]);
  if (order) pairs.sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]));
  else pairs.sort((a, b) => b[1] - a[1]);            // default: descending by value

  const cats = pairs.map(p => p[0]);
  const vals = pairs.map(p => p[1]);

  // Low-variance guard: zoom the axis instead of always starting at 0 (see "Low-Variance Rankings")
  const spread = (Math.max(...vals) - Math.min(...vals)) / Math.max(...vals);
  const floor  = spread < 0.15 ? Math.min(...vals) - (Math.max(...vals) - Math.min(...vals)) * 0.5 : 0;

  Plotly.newPlot(divId, [{
    type: 'bar', orientation: 'h', y: cats, x: vals,   // always horizontal: category on y, metric on x
    marker: { color: opts.color || '#ff6600', opacity: .9 },
    text: vals.map(v => opts.fmt ? opts.fmt(v) : v), textposition: 'outside', textfont: { color: '#aab' },
    hovertemplate: `%{y}: %{x}${opts.unit || ''}<extra></extra>`
  }], {
    ...BG,
    xaxis: { ...BG.xaxis, title: opts.xTitle || '', range: [floor, Math.max(...vals) * 1.15] },
    yaxis: { ...BG.yaxis, type: 'category', categoryorder: order ? 'array' : 'total ascending', categoryarray: order, automargin: true },
    margin: { t: 20, b: 50, l: 140, r: 60 }
  }, CFG);
}

// Every chapter that compares categories to a metric calls the SAME function:
// renderCategoryBar('priChart', D.pri_labels, D.pri_hrs, {categoryOrder:['Critical','High','Medium','Low'], unit:'h', xTitle:'Avg Resolution Hours'});
// renderCategoryBar('catChart', D.cat_names, D.cat_cnt, {unit:' tickets', xTitle:'Ticket Count'});
// renderCategoryBar('chanChart', D.chan_labels, D.chan_cnt, {unit:' tickets', xTitle:'Ticket Count'});
```

This is the actual fix for the class of bug we saw (a "Low" category with no visible bar): it wasn't a one-off mistake in a single chapter, it was the *lack of a shared pattern* — one chapter's bar trace was hand-typed slightly differently than the others. Centralizing it in `renderCategoryBar()` means every category-bar chapter — for any dataset, any column names — gets the length-check, orientation, ordering, and low-variance zoom for free, instead of relying on each chapter's author to remember the rules correctly by hand.

The specific rules this helper enforces (for reference, if extending it):

1. **`orientation:'h'`, category array on `y`, numeric array on `x`** — never the reverse.
2. **`x` and `y` are derived from one paired, sorted list** — never two separately-ordered arrays that can drift out of sync.
3. **Categories are never filtered independently of their values** — drop both together or not at all.
4. **`yaxis.categoryorder`/`categoryarray`** set explicitly so label order can't drift from bar order on re-render.
5. **Length is asserted (`categories.length === values.length`) before plotting**, failing loudly instead of silently rendering a phantom label with no bar.

### Donut / Pie Charts (share / composition) — Label On the Slice, No Legend

**Use a donut/pie at most once per story — never two.** A single composition chart is a nice change of pace among the bars and lines; a second one makes the story feel repetitive and dilutes its impact. If another column also tells a share/composition story, reach for a *different* shape rather than a second donut — pick whichever fits the data:

- **Treemap** (`type:'treemap'`) — great for a part-to-whole with many categories or a hierarchy (e.g. department → status), and it labels comfortably inside the tiles.
- **100% stacked bar** — a single full-width bar split into its shares; ideal for one composition, or a few side-by-side bars to compare composition *across* groups.
- **Stacked / grouped bar** — when the interesting story is the counts within each category, not just their fractions.
- **Funnel** (`type:'funnel'`) — when the categories form ordered stages (e.g. Scoping → Piloting → In Development → Live).
- **Vertical or horizontal bar** — a plain ranked bar is often the clearest, but don't treat it as the *only* fallback.

Match the chart to what the data is actually saying; the rule is just "not a second donut," not "always a bar."

A donut's slices are already labeled directly (name + percent on each slice), so **a legend is redundant — and worse, it collides**: Plotly places the legend to the right, where its entries overlap the slice labels and each other, producing tangled text like "In DevelopmentPiloting". Never render a donut with both on-slice labels and a legend.

**Use one shared helper for every donut, with the legend off:**

```javascript
// Generic donut for ANY category share/composition (status, type, segment, ...).
function renderDonut(divId, labels, values, opts = {}) {
  if (labels.length !== values.length)
    throw new Error(`${divId}: labels/values length mismatch (${labels.length} vs ${values.length})`);
  Plotly.newPlot(divId, [{
    type: 'pie', hole: 0.55,
    labels, values,
    sort: true, direction: 'clockwise',
    textinfo: 'label+percent',        // label the slice itself...
    textposition: 'inside',           // ...inside the ring
    insidetextorientation: 'horizontal',
    textfont: { color: '#fff', size: 12 },
    marker: { line: { color: '#111', width: 2 } },  // thin gap between slices
    hovertemplate: '%{label}: %{value} (%{percent})<extra></extra>'
  }], {
    ...BG,
    showlegend: false,                // ← the fix: no redundant, colliding legend
    margin: { t: 20, b: 20, l: 20, r: 20 }
  }, CFG);
}
```

Rules this enforces:
1. **`showlegend: false`** — the on-slice `label+percent` text is the only labeling; the legend is always off.
2. **`textposition: 'inside'` with `insidetextorientation: 'horizontal'`** — keeps labels on their slice and readable, never floating outside where they collide with neighbors.
3. **`sort: true`** so slices read largest-to-smallest.
4. If a slice is too thin for an inside label, **don't turn the legend back on** — merge tiny tail categories into an "Other" slice, or switch to a horizontal bar (`renderCategoryBar`) for many small categories.


### Low-Variance Rankings — When Every Value Looks the Same

Before building any ranked bar list (Hall of Shame/Fame, top-N charts), **check the spread of the values**: `(max - min) / max`. If that spread is small (roughly under ~15–20%, e.g. CSAT scores of 3.98–4.08, or percentages like 94%–97%), a bar scaled from 0 → max will render every row as visually identical — the chart tells the reader nothing.

**Fix — pick one based on the chapter's purpose:**

1. **Zoom the axis / bar scale to the actual data range**, not 0. Compute `pct` as `(value - floor) / (ceil - floor) * 100` where `floor` is slightly below the min (e.g. min − 10% of range, or a meaningful baseline like "desk average") and `ceil` is slightly above the max. This is the right default fix for the Hall of Shame/Fame bar rows.
2. **Show delta-from-baseline instead of the raw value.** If the story point is "these agents beat the average," plot `value − desk_average` as a diverging bar (positive bars extend right in `--fire`, negative in a muted gray) instead of the absolute score. This makes small-but-real differences visible and matches the narrative.
3. **Switch chart type** when a bar list still isn't informative even after zooming: a **dot/lollipop plot** on a zoomed axis, or a **table with a small sparkline/heatmap-tint per row** (color intensity instead of bar length), reads better than near-equal-length bars for tightly clustered rankings.
4. **Never leave a 0-based bar as the only visual** for a low-variance metric — always zoom, delta, or switch.

State the actual spread in the chapter copy too (e.g. "the gap between #1 and #10 is just 0.10 points on a 5-point scale") so the visual and the narrative agree on how tight the race is.

Always use this base layout object for dark theme consistency:
```javascript
const BG = {
  paper_bgcolor:'#111', plot_bgcolor:'#111',
  font:{color:'#bbb', size:11},
  margin:{t:16, b:52, l:58, r:18},
  xaxis:{gridcolor:'#1e1e1e', linecolor:'#2a2a2a'},
  yaxis:{gridcolor:'#1e1e1e', linecolor:'#2a2a2a'}
};
const CFG = {responsive:true, displayModeBar:false};
```

---

## Stat Card Rules

**Short numbers** (≤6 chars, e.g. `2,000`, `60`, `156`): use `.s-card` with `flex:1; min-width:220px`

**Long numbers** (≥7 chars, e.g. `$419,917`, `1,284,330`): use `.s-card-wide` — a standalone centered card on its own row with more horizontal space and larger font.

**Rule of thumb:** if the number has a `$` prefix AND is 6+ digits, give it `.s-card-wide`.

**`data-suffix`/`data-prefix` must be short and purely a unit** (e.g. `"M"`, `"%"`, `"B"`, `"h"`) — never embed prose, arrows, ranges, or multi-word labels in them (e.g. never `data-suffix="M tons"` or `data-suffix="→$4.17/kg"`). The 6-vs-7 char length check applies to the **full rendered string** — prefix + number + suffix combined — not just the numeric part alone, since that's what actually has to fit in the card.

**If a value isn't a clean countable integer or round decimal, don't force it into a counter.** A counter animates one number ticking up to a target — it can't meaningfully animate a range (`$3.61→$4.17/kg`) or a compound unit. When the raw stat is a range, ratio, or multi-part value, either display it as static (non-animated) text, or redesign it as something genuinely countable — e.g. replace "$3.61→$4.17/kg" with a "16% price increase" stat instead.

```html
<!-- Row 1: short numbers -->
<div class="stat-row">
  <div class="s-card reveal">...</div>
  <div class="s-card reveal">...</div>
  <div class="s-card reveal">...</div>
</div>
<!-- Row 2: large dollar amount gets its own wide card -->
<div class="stat-row">
  <div class="s-card-wide reveal">...</div>
</div>
```

---

## Animated Components

### Scroll-Triggered Counter
Add `data-target="12345"` and optionally `data-prefix="$"` to any `.num` element. A dedicated observer calls `counter(el)` automatically when its card scrolls into view.

```html
<div class="num" data-prefix="$" data-target="419917">$0</div>
```

**Never start counters from the same IntersectionObserver that drives generic `.reveal` transitions.** That observer fires for every reveal element on the page (chapter text, chart boxes, stat cards, ...) in the same batch — mixing counter starts into it means a stat card's counter can start (or get skipped) while the card is still mid-opacity-transition, so numbers race, stall, or never animate. This isn't a one-off card issue, it's a class of bug: any dataset with more than a couple of stat cards can reproduce it.

Use two independent, single-purpose observers instead — one for visual reveal, one for counters — and guard `counter()` so it can never fire twice for the same element:

```javascript
function counter(el) {
  if (el.dataset.counted) return;   // guard: fire at most once per element
  el.dataset.counted = '1';
  // ...existing animation logic...
}

// Visual reveal only — no counter logic here.
const revealObs = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('vis'); });
}, {threshold: 0.15});
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// Isolated counter observer: watches whichever container each .num[data-target] lives in
// (works for any number of stat cards anywhere on the page — nothing hardcoded to an id
// or count), uses a higher threshold so the card is substantially visible before its
// numbers start moving, and unobserves immediately so it can never double-trigger.
const counterObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.querySelectorAll('.num[data-target]').forEach(n => counter(n));
    counterObs.unobserve(e.target);
  });
}, {threshold: 0.3});
document.querySelectorAll('.num[data-target]').forEach(n => {
  counterObs.observe(n.closest('.reveal') || n);
});
```

### Hall of Shame / Fame Rows
Animated stagger: rows slide in from the left one by one, then damage bars grow right.

**Before computing `pct`, check variance first** (see "Low-Variance Rankings" above). If the top10 values are tightly clustered, scale from a zoomed floor instead of 0:

```javascript
const vals = D.top10_values;
const spread = (Math.max(...vals) - Math.min(...vals)) / Math.max(...vals);
// Zoom in when values are tightly clustered (e.g. CSAT 3.98-4.08)
const floor = spread < 0.15 ? Math.min(...vals) - (Math.max(...vals) - Math.min(...vals)) * 0.5 : 0;
const ceil = Math.max(...vals) * 1.02;
const pct = v => ((v - floor) / (ceil - floor)) * 100;
```

```javascript
function buildShame(){
  D.top10_names.forEach((name, i) => {
    const row = document.createElement('div');
    row.className = 's-row';
    row.style.transitionDelay = (i * .07) + 's';
    row.innerHTML = `...`; // use pct(D.top10_values[i]) for the bar width, not a raw 0-based ratio
    list.appendChild(row);
  });
  // Stagger visibility
  list.querySelectorAll('.s-row').forEach((r, i) => {
    setTimeout(() => {
      r.classList.add('vis');
      setTimeout(() => {
        r.querySelector('.s-bar').style.width = r.querySelector('.s-bar').dataset.pct + '%';
      }, 350);
    }, i * 90);
  });
}
```

### Incident / Record Cards
5 cards fly up from below, staggered:
```javascript
wrap.querySelectorAll('.i-card').forEach((c, i) => {
  setTimeout(() => c.classList.add('vis'), i * 110);
});
```

---

## The Closing Chapter — Decide What the Reader Needs, Don't Default to One Format

Every story needs a payoff beyond "here's what happened" — but *what kind* of payoff depends on the dataset and audience, not a fixed template. Add this as the second-to-last chapter, right before the epilogue, derived from **The Fix** story beat (Phase 2) — but "The Fix" is a prompt to figure out the right closing move, not a mandate that it's always a takeaways/action-item list.

**Decide which closing format actually serves this data. Common options:**

| Format | Use when... |
|---|---|
| **Key Takeaways** | The story's value is understanding — the reader mainly needs the 3–5 things worth remembering, no action implied (e.g. exploratory or descriptive data). |
| **Recommendations & Next Steps** | The data clearly implies operational actions the reader/organization can take (e.g. service desk staffing, agent coaching, process fixes). |
| **News & Context** *(requires web research)* | The topic benefits from grounding in current real-world events, industry trends, or external validation — e.g. market data, public health, policy topics — where showing "here's what's happening in the news around this" adds credibility or urgency the dataset alone can't. Only use this if the environment actually has web access; verify before committing to it rather than assuming it's available. |
| **Benchmark / How You Compare** | A credible public benchmark or industry average exists to compare the dataset against, and "are we ahead or behind" is the most useful closing frame. |

Pick one (or blend two, e.g. takeaways + one grounding external stat) based on what would actually be useful to *this* reader for *this* dataset — don't reach for "what to do about it" by default if the data is purely descriptive, and don't reach for takeaways if the data screams for action.

**Content rules (apply regardless of format chosen):**
- 3–5 items, each grounded in a specific number or finding already shown earlier in the story (don't introduce new *data-derived* claims here — external/news items are the one exception, and those must be clearly sourced)
- Keep each item to 1–2 sentences — this is a scannable list, not another narrative chapter
- End with a short closing line appropriate to the format (a "Next step" for recommendations, a one-line synthesis for takeaways, a source/date note for news items)

**Markup pattern (numbered cards, full-width — same structure works for any format, only the copy changes):**

```html
<section class="chapter" id="ch8">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">Chapter 08</div>
      <h2 class="c-head"><!-- headline matches the chosen format, e.g. "What to do <em>about it.</em>" or "What to <em>remember.</em>" or "What's happening <em>right now.</em>" --></h2>
      <p class="c-body">One sentence framing the closing format you chose.</p>
    </div>
    <div class="takeaway-grid">
      <div class="t-card reveal">
        <div class="t-index">01</div>
        <h3>Insight-driven headline</h3>
        <p>One sentence citing the specific number/finding (or, for the news format, the headline + source), plus why it matters.</p>
      </div>
      <!-- repeat for 3–5 cards total -->
    </div>
    <div class="next-steps reveal">
      <strong><!-- "Next step:" / "Bottom line:" / "As of <date>:" depending on format --></strong> One concrete closing line.
    </div>
  </div>
</section>
```

**If choosing "News & Context":** confirm web access works before committing the chapter to it (a quick test fetch, not an assumption), cite the source and date for each headline/stat pulled in, and keep the dataset's own findings as the throughline — external context should support the data's story, not replace it.

`.t-card` styling should match `.s-card` (dark card, `--fire` accent border-left, staggered reveal like `.i-card`). Number each card (`.t-index`) so it reads as a ranked action list, not a wall of text.

---

## Narrative Writing Guidelines

Good scrollytelling copy is short, punchy, and specific. Use this formula per chapter:

1. **Setup** (1 sentence): state the angle
2. **Specific finding** (1 sentence with a `<strong>` entity name): name the data winner/loser
3. **Implication or tension** (1 sentence): why does it matter, or what's surprising

**Good example:**
> Gas grills racked up the most incidents by volume — they're everywhere, and in the wrong hands, they're catastrophic. But **kamado grills?** When something goes wrong on a kamado, it goes *really* wrong — the highest average damage cost per incident of any grill type.

**Bad example (too vague):**
> There are many different types of grills. Some cost more than others. The data shows interesting patterns.

Make headlines dramatic. Use `<em>` (styled orange) for the key word:
```html
<h2 class="c-head">The weapon<br>of choice <em>matters.</em></h2>
```

The epilogue should echo the hero's opening claim and close the loop:
- Hero: *"America Has a BBQ Problem."*
- Epilogue: *"The data is clear. The smoke never lies."*

---

## Design System (Dark Fire Theme)

```css
:root {
  --fire: #ff6600;   /* primary accent — headlines, numbers, bars */
  --ember: #ff3300;  /* gradient end — buttons, glow */
  --text: #f0ede8;   /* body text */
  --muted: #999;     /* secondary text, labels */
}
/* Background layers */
body        { background: #0a0a0a }
.chapter    { background: #0a0a0a or #0d0d0d (alternate) }
.chart-box  { background: #111; border: 1px solid #1e1e1e }
.s-card     { background: #111; border: 1px solid #222 }
```

For a different theme (e.g. corporate blue, green sustainability), replace `--fire` and `--ember` and update the radial gradient in `#hero` and `#epilogue`.

---

## File Naming Convention

```
<dataset-name>-story-YYYY-MM-DD.html
```

Lowercase kebab-case dataset name, the word `story`, then the current date. Examples:
- `bbq-story-2025-07-21.html`
- `sales-data-story-2025-07-21.html`
- `hr-incidents-story-2024-11-03.html`

Always deliver to `/app/created/` so it is returned as an attachment.

---

## Gotchas

| Issue | Fix |
|---|---|
| Large numbers clipped in stat cards | Use `.s-card-wide` for any value ≥ 7 chars |
| Content looks tiny with wasted black space | Increase chart heights to 460–500px; use `clamp(2.2rem,4.5vw,4rem)` for headlines |
| Donut/pie legend overlaps the slice labels (tangled text like "In DevelopmentPiloting" on the right) | The slices are already labeled on-slice, so the legend is redundant and collides. Set `showlegend:false` and label slices with `textinfo:'label+percent'`, `textposition:'inside'` — see "Donut / Pie Charts" / `renderDonut()` |
| Charts not rendering | Each chart div needs an explicit `height` in its inline style; Plotly needs a sized container |
| Blank charts AND every stat counter stuck at 0 | A single JS `SyntaxError` (often an unescaped apostrophe in a single-quoted string, e.g. `'Who's Buying'`) kills the whole `<script>` so nothing runs. Escape apostrophes and run `node --check` on the generated JS before shipping — see Phase 4 "Rendering contract" |
| Only the first chart renders; later charts stay blank | The lazy-render `IntersectionObserver` reports the **section** id (`ch-map`), not the chart-div id (`mapChart`). Dispatch `renderSection` branches on the section id |
| Charts/counters never appear until the user scrolls (or never at all) | Rendering is observer-only with no fallback. Route all rendering through one `renderSection(id)` called from both the observer and a 2.5s safety-net timeout that also reveals and runs counters — see Phase 4 "Rendering contract" |
| Nested quotes break the Python heredoc | Always write HTML builder to a `.py` file with the `create` tool, then run it — never use heredocs with nested single quotes |
| Chapters render before scroll | Charts are only initialized inside `IntersectionObserver` callback with a `rendered` guard object — never call `Plotly.newPlot` at page load |
| Hall of shame bars jump on load | Set `width:0` in CSS; only transition to final width after `.vis` class is added via JS |
| Ranked bars all look the same length (e.g. CSAT 3.98–4.08) | Values are tightly clustered — a 0-based bar hides the difference. Zoom the scale to the actual range (or a meaningful floor like the desk average), or plot delta-from-baseline instead of raw value. See "Low-Variance Rankings" |
| A category (e.g. "Low") shows a label but no bar, or bars render as misaligned vertical columns instead of horizontal rows | `x`/`y` arrays are mismatched, misordered, or `orientation:'h'` is missing. Rebuild `x`/`y` from one ordered list of pairs and verify `trace.x.length === trace.y.length`. See "Horizontal Bar Charts" |
| File too large to send | Avoid embedding Plotly.js inline (3MB+); always use the CDN script tag |
| Stat counters stall, jump straight to final value, or never animate | Counter starts were mixed into the shared `.reveal` IntersectionObserver batch and raced against other reveal transitions. Use an isolated, single-shot counter observer with a `counted` guard, decoupled from `revealObs`. See "Scroll-Triggered Counter" |
| Scatter/bubble log axis shows confusing repeating ticks (`0.1, 2, 5, 1, 2, 5, 10...`) | Set `dtick: 1` on any log-type axis so labeled ticks land only on powers of ten. See `references/CHART-PATTERNS.md` |
| Scatter/bubble labels overlap into unreadable mush in a crowded region | Don't statically label every point — greedily label largest markers first, skip a label if it collides with one already placed, keep full name on hover. See `renderScatterBubble()` in `references/CHART-PATTERNS.md` |
| Stat card text overflows/wraps (e.g. "105M tons", "$3.61→$4.17/kg") | The 6-vs-7 char rule applies to the full rendered string (prefix+number+suffix), not just the number. Keep `data-suffix`/`data-prefix` to short units only — never prose, arrows, or ranges. If the value isn't a clean countable number, don't animate it; show static text or redesign the stat |
| Dual-trace label collision (e.g. a bar's `outside` label and a scatter/line's `top center` label overlap at the bar top) | A bar chart and a scatter/line trace share the same x-position with labels pointing the same direction. Assign labels to opposite sides (e.g. bar `'inside'`, scatter `'bottom center'`) so the two never share the same vertical space. See `references/CHART-PATTERNS.md` |
| `yaxis2` overlay is invisible or its markers sit on top of the bars | Dark-theme axes need `yaxis2.color`/`tickfont` set explicitly (unstyled defaults to a dark-on-dark color); compute `yaxis2.range` from the overlay's own values instead of full auto so it doesn't collide with the bar heights. See `references/CHART-PATTERNS.md` |
| One giant entity washes out all color variation on a choropleth (e.g. one huge producer/exporter makes every other country look the same faint shade) | Detect dominance from the data (top value vs. 2nd-highest) and switch to a log color scale, or cap `zmax` below the true max — call out the clipping in the chapter copy. See `references/CHART-PATTERNS.md` |
| File read is blocked before any aggregation runs | The Copilot Studio sandbox gates direct reads of `/app/uploads/` files until the preprocessor has run against them. Always run `preprocess.py` first — see Phase 1 |
| A plain `python`/`python3` script invocation fails or is blocked | Retry wrapped in `sandbox-exec` (e.g. `sandbox-exec python script.py <args>`) before assuming the script is broken — see Phase 1 |

---

## Quick-Start Checklist

- [ ] Inspect the data — identify entity, metric, time, geo columns
- [ ] Run SQL aggregations — top 10, totals, distributions, monthly, geo
- [ ] Serialize all chart data to `/app/workspace/story_data.json`
- [ ] Write `/app/workspace/build_story.py` using the `create` tool
- [ ] Run `python3 /app/workspace/build_story.py` — verify "Done! X chars written"
- [ ] Syntax-check the embedded JS with `node --check` (build_story.py does this automatically) — a single bad char blanks the whole page
- [ ] Closing chapter — pick the right format (takeaways / recommendations / news-context / benchmark) for this data, 3–5 items grounded in earlier findings
- [ ] Stat cards: short numbers → `.s-card`, large dollar amounts → `.s-card-wide`
- [ ] Chart heights: minimum 460px per chart div
- [ ] Headline font: `clamp(2.2rem, 4.5vw, 4rem)` minimum
- [ ] Output file → `/app/created/<dataset-name>-story-YYYY-MM-DD.html`
