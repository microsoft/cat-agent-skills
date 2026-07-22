# Chart Patterns & Build Helpers Reference

This file has two kinds of content:

- **Conditional chart types** (first) — combinations that only apply to **some** datasets: a geo column, a real two-variable correlation, or a bar+overlay pairing. Read these only when the data shape at hand calls for one.
- **Shared build helpers** (second) — the base layout object and helper functions used on **most** stories when writing the HTML in Phase 4 (`renderCategoryBar`, `renderDonut`, the low-variance fix, and the counter / leaderboard / record-card animation code). Open this file before writing chart or animation code and build through these helpers.

## Contents
**Conditional chart types**
- Combining Traces (Bar + Scatter/Line Overlay) — label collisions
- Geography: Don't Assume USA — Detect It From the Data
- Combining a Bar Trace with a Second Y-Axis Overlay (`yaxis2`)
- Scatter / Bubble Charts (entity-on-two-axes) — Log Ticks and Label Crowding

**Shared build helpers (Phase 4)**
- Base layout object (`BG` / `CFG`) — used by every chart
- Horizontal Bar Charts (`renderCategoryBar`) — get the axes right
- Donut / Pie Charts (`renderDonut`) — label on the slice, no legend
- Low-Variance Rankings — when every value looks the same
- Scroll-Triggered Counter — two-observer pattern
- Leaderboard Rows / Record Cards — staggered reveals

---

## Combining Traces (Bar + Scatter/Line Overlay) — Keep Labels on Opposite Sides

Whenever two traces share the same x-position (e.g. a bar trace with a scatter/line trace overlaid on the same or a secondary axis), their data labels can render at the same pixel and collide — most commonly a bar's `textposition:'outside'` label and a scatter marker's `textposition:'top center'` label both landing just above the bar top. This is a general hazard of any dual-trace chart, not a one-off styling mistake in a single chapter.

**Rule: never leave both traces' labels pointing the same direction.** When combining a bar trace with a scatter/line overlay on the same axis, assign labels to opposite sides — e.g. bar labels `'inside'` (or `'outside'` only if the scatter trace's labels are pushed to `'bottom center'`), and scatter/marker labels on the side away from the bar top. Pick whichever pairing keeps the two label sets in different vertical space for the actual data at hand, rather than hardcoding one specific combination.

## Geography: Don't Assume USA — Detect It From the Data

The geo column could hold US state codes, full country names, ISO codes, or something else entirely — never hardcode `locationmode:'USA-states'` as the default. Instead, inspect the actual values and branch:

- **2-letter codes matching US state abbreviations** (e.g. `CA`, `TX`, `NY`) → `locationmode:'USA-states'`, `geo:{scope:'usa'}`
- **Full US state names** (e.g. `Alabama`, `California`) → **convert to two-letter postal codes first** (a fixed `{'Alabama':'AL', ...}` lookup), then `locationmode:'USA-states'`, `geo:{scope:'usa'}`. Plotly won't match full state names directly, so the map comes up empty if you skip the conversion.
- **Full country names** (e.g. `France`, `Japan`) → `locationmode:'country names'`, `geo:{scope:'world', projection:{type:'natural earth'}}`
- **3-letter ISO codes** (e.g. `FRA`, `JPN`) → `locationmode:'ISO-3'`, `geo:{scope:'world'}` (more reliable matching than country names, which can have spelling/alias mismatches)

Detect this once (e.g. a simple regex/length check on the geo column's values during Phase 1 inspection or right before building the map trace) and pick the matching `locationmode`/`geo` config — the same `buildMap()` function should handle either case rather than having a separate function per geography type.

**Watch for a rollup/`Total` row.** Datasets often include a summary row (e.g. `State`=`Total`) that isn't a real location. Filter it out before mapping (and before ranking/aggregating) — it never matches a `locationmode` code and, if it slips into a value-based scale, its huge total anchors `zmax` and washes out every real region (see the dominance note below).

**Give the map room — size it large.** A choropleth is usually the hero of its chapter: make its div full-width and tall (≈560–640px) with `margin:{t:10,b:10,l:0,r:0}` so the states/countries read big and clear, rather than a cramped square beside the text.

**One dominant entity can wash out the whole color scale.** Choropleths default to a linear color scale from the data's min to max — if one country/state is an order of magnitude larger than everyone else (e.g. one giant producer/exporter), it anchors `zmax` and every other entity collapses into nearly the same faint color, hiding all the variation the map exists to show. Detect this from the data itself (e.g. `top value / second-highest value` is large) rather than assuming it per dataset, and when it's true, do one of:
- Switch to a **log color scale** (color the log of the value, with a `colorbar.tickvals`/`ticktext` that shows real units, not log units), or
- **Cap `zmax`** at a value below the true max (e.g. the 2nd- or 3rd-highest entity, or a percentile) so the rest of the map keeps visible contrast — call out in the chapter copy that the top entity is clipped/off-scale so the visual doesn't silently misrepresent it.

## Combining a Bar Trace with a Second Y-Axis Overlay (`yaxis2`)

Pairing a bar trace with a scatter/line trace on `yaxis2` (e.g. volume as bars + price as an overlaid line/markers) is common, but two details are easy to miss on a dark theme:

1. **Always set `yaxis2.tickfont`/`color` explicitly.** Plotly's default axis color assumes a light background; on `BG`'s dark `#111`/`#0d1526` panels, an unstyled `yaxis2` can render dark-on-dark and effectively disappear. Set it to match (or complement) the overlay trace's own marker/line color, the same way `xaxis2` already does elsewhere in this skill's charts.
2. **Check that `yaxis2`'s range doesn't collide with the bars.** Because `yaxis2` is a separate scale overlaid on the same plot area, an unconstrained auto-range can place the scatter markers directly on top of (or visually indistinguishable from) the bar tops. Compute the range from the actual overlay values (e.g. `[min * 0.9, max * 1.2]`) rather than leaving it on full auto, so the two traces occupy visually distinct vertical bands — and combine this with the label-side rule above ("Combining Traces") so neither the markers nor their labels land on the bars.

## Scatter / Bubble Charts (entity-on-two-axes) — Log Ticks and Label Crowding

Charts that plot every entity by two metrics (e.g. volume vs. price, count vs. rate), optionally sized/colored by a third and fourth variable, hit two recurring failure modes whenever one axis spans multiple orders of magnitude and many entities cluster at the low end:

1. **Confusing log-axis ticks.** Plotly's log-axis default draws a labeled tick at every `1`, `2`, `5` within each decade (`0.1, 2, 5, 1, 2, 5, 10, 2, 5, ...`). That's technically correct but reads as broken/non-monotonic to a viewer skimming left to right. Fix it generically by forcing one labeled tick per decade (`dtick: 1` on a `type:'log'` axis draws only the power-of-ten ticks: `0.1, 1, 10, 100`), regardless of what the data's actual min/max happen to be.
2. **Overlapping static labels.** When many entities sit close together (common at the low-volume/low-count end), printing every entity's name as a permanent text label produces unreadable overlapping text — and that crowding gets *worse*, not better, in exactly the region the chart is trying to highlight. Never decide by eye which labels to hide per dataset; compute it.

**Use one shared helper for every "entity on two numeric axes" scatter/bubble chart:**

```javascript
// Generic helper for ANY entity-vs-two-metrics scatter/bubble chart.
// entities: array of names, x/y: numeric arrays, opts.size/opts.color: optional per-entity arrays.
function renderScatterBubble(divId, entities, x, y, opts = {}) {
  if (entities.length !== x.length || entities.length !== y.length) {
    throw new Error(`${divId}: entities/x/y length mismatch (${entities.length}, ${x.length}, ${y.length})`);
  }

  const logX = opts.logX ?? (Math.max(...x) / Math.min(...x.filter(v => v > 0)) > 100);
  const logY = opts.logY ?? (Math.max(...y) / Math.min(...y.filter(v => v > 0)) > 100);

  // Normalize each point to 0-1 in (log-transformed, if applicable) coordinate space so
  // crowding is judged the same way the eye will actually see it on screen, not in raw units.
  const tx = v => logX ? Math.log10(v) : v;
  const ty = v => logY ? Math.log10(v) : v;
  const xs = x.map(tx), ys = y.map(ty);
  const xRange = Math.max(...xs) - Math.min(...xs) || 1;
  const yRange = Math.max(...ys) - Math.min(...ys) || 1;
  const nx = xs.map(v => (v - Math.min(...xs)) / xRange);
  const ny = ys.map(v => (v - Math.min(...ys)) / yRange);

  // Greedily label the largest markers first; skip a label if it would land within
  // minGap of an already-placed label. Everyone still gets the full name on hover.
  const sizes = opts.size || entities.map(() => 1);
  const order = entities.map((_, i) => i).sort((a, b) => sizes[b] - sizes[a]);
  const minGap = opts.labelMinGap ?? 0.06; // fraction of the plotted range; tune per density, not per dataset
  const placed = [];
  const showLabel = new Array(entities.length).fill(false);
  for (const i of order) {
    const collides = placed.some(j => Math.hypot(nx[i] - nx[j], ny[i] - ny[j]) < minGap);
    if (!collides) { showLabel[i] = true; placed.push(i); }
  }

  Plotly.newPlot(divId, [{
    type: 'scatter', mode: 'markers+text',
    x, y, text: entities.map((name, i) => showLabel[i] ? name : ''),
    textposition: 'top center', textfont: { color: '#aab', size: 10 },
    marker: {
      size: sizes, sizemode: 'area', sizeref: opts.size ? Math.max(...sizes) / 40**2 : undefined,
      color: opts.color, colorscale: opts.colorscale, showscale: !!opts.colorscale, opacity: .85,
      line: { width: 1, color: '#111' }
    },
    hovertemplate: entities.map((name, i) => `${name}: %{x}, %{y}<extra></extra>`)
  }], {
    ...BG,
    xaxis: { ...BG.xaxis, title: opts.xTitle || '', type: logX ? 'log' : '-', dtick: logX ? 1 : undefined },
    yaxis: { ...BG.yaxis, title: opts.yTitle || '', type: logY ? 'log' : '-', dtick: logY ? 1 : undefined },
    margin: { t: 20, b: 50, l: 60, r: 20 }
  }, CFG);
}

// Every chapter that plots entities on two metrics calls the SAME function:
// renderScatterBubble('exportChart', D.country, D.volume, D.price_per_kg, {size: D.volume, color: D.region_code, xTitle:'Export Volume', yTitle:'Avg Price per kg'});
```

Rules this helper enforces (for reference, if extending it):

1. **Log-ness is detected from the data's own dynamic range** (`max/min > 100`, or pass `opts.logX`/`opts.logY` explicitly) — never hardcode which axis is log for a given dataset.
2. **`dtick: 1` on any log axis** so labeled ticks land only on powers of ten, no matter what the underlying values are.
3. **Label placement is a greedy pack computed from normalized (and log-transformed, if applicable) coordinates** — largest markers get priority, and a label is only skipped if it would collide with one already placed. This scales to however many entities are crowded together, in whichever region of the chart that happens to be, for any dataset.
4. **Every entity keeps its name on hover** even when its static text label is suppressed, so no data is hidden — only the always-on label is decluttered.
5. **`minGap` is a tunable density knob, not a per-dataset cutoff** — widen it for very crowded charts, narrow it for sparse ones, but never hand-pick which specific entities get labels.

---

## Base Layout Object (`BG` / `CFG`)

Always use this base layout object for dark-theme consistency, and spread `...BG`
into every chart's layout:

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

## Horizontal Bar Charts (category-vs-value) — Get the Axes Right

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

## Donut / Pie Charts (share / composition) — Label On the Slice, No Legend

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

## Low-Variance Rankings — When Every Value Looks the Same

Before building any ranked bar list (leaderboards, top-N charts), **check the spread of the values**: `(max - min) / max`. If that spread is small (roughly under ~15–20%, e.g. CSAT scores of 3.98–4.08, or percentages like 94%–97%), a bar scaled from 0 → max will render every row as visually identical — the chart tells the reader nothing.

**Fix — pick one based on the chapter's purpose:**

1. **Zoom the axis / bar scale to the actual data range**, not 0. Compute `pct` as `(value - floor) / (ceil - floor) * 100` where `floor` is slightly below the min (e.g. min − 10% of range, or a meaningful baseline like a group average) and `ceil` is slightly above the max. This is the right default fix for the leaderboard bar rows.
2. **Show delta-from-baseline instead of the raw value.** If the story point is "these agents beat the average," plot `value − desk_average` as a diverging bar (positive bars extend right in `--fire`, negative in a muted gray) instead of the absolute score. This makes small-but-real differences visible and matches the narrative.
3. **Switch chart type** when a bar list still isn't informative even after zooming: a **dot/lollipop plot** on a zoomed axis, or a **table with a small sparkline/heatmap-tint per row** (color intensity instead of bar length), reads better than near-equal-length bars for tightly clustered rankings.
4. **Never leave a 0-based bar as the only visual** for a low-variance metric — always zoom, delta, or switch.

State the actual spread in the chapter copy too (e.g. "the gap between #1 and #10 is just 0.10 points on a 5-point scale") so the visual and the narrative agree on how tight the race is.

## Scroll-Triggered Counter

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

## Leaderboard Rows
Animated stagger: rows slide in from the left one by one, then value bars grow right.

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
function buildLeaderboard(){
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

## Record Cards
5 cards fly up from below, staggered:
```javascript
wrap.querySelectorAll('.i-card').forEach((c, i) => {
  setTimeout(() => c.classList.add('vis'), i * 110);
});
```
