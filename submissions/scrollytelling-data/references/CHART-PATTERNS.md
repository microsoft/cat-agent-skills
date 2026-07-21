# Chart Patterns Reference — Conditional Chart Types

This file covers chart types and combinations that only apply to **some** datasets — a geo column, a real two-variable correlation, or a bar+overlay pairing. Universal chart guidance (bar charts, stat cards, counters) stays in `SKILL.md`; only read this file when the data shape at hand actually calls for one of the sections below.

## Contents
- Combining Traces (Bar + Scatter/Line Overlay) — label collisions
- Geography: Don't Assume USA — Detect It From the Data
- Combining a Bar Trace with a Second Y-Axis Overlay (`yaxis2`)
- Scatter / Bubble Charts (entity-on-two-axes) — Log Ticks and Label Crowding

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
