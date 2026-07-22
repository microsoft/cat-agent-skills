# Component Catalog

Every component below is already styled in `template.html`. Build slides by composing these — do not invent new CSS unless a slide genuinely needs it. Keep the `<style>` and `<script>` blocks verbatim.

## Slide shell
```html
<section class="slide">
  <div class="content"> … slide content … </div>
</section>
```
- First slide only: `class="slide title-slide active"`. All others: `class="slide"`.
- Direct children of `.content` fade up in sequence (stagger delays for the first 6 children). Keep ~2–6 top-level children per slide.

## Text
- `.eyebrow` — small uppercase gradient kicker above the headline.
- `h1` — title-slide headline. `h2` — section headline. Wrap 1–3 words in `<span class="grad">…</span>` for a gradient highlight.
- `.subtitle` — one-line subtitle under an `h1`.
- `.lead` — large muted body / takeaway line. `p.small` — fine print.
- `<strong>` and `<em>` are theme-aware (resolve to the ink color).

## Grids & cards
- `.grid` + one of `.g2 .g3 .g4 .g5` (columns; collapse responsively).
- `.card` — bordered panel; `h3` + `p`. Optional `.ic` icon chip (use a unicode glyph: ◇ ⚙ ✦ ≡ ⧉ ⇉ ▦ ✓) or `.num-badge` (1,2,3…).
- Tinted "highlight" card: add inline `style="background:linear-gradient(120deg,rgba(59,130,246,.09),rgba(236,72,153,.09));border-color:rgba(236,72,153,.28)"`.

## Stat row
- `.stat-num` (add `.g` for gradient text) inside a `.card`, with an `h3` label + `p`.

## Callout (one key sentence)
```html
<div class="callout"><span class="tag">Label</span><p>The sentence to remember.</p></div>
```

## Chips (compact list)
```html
<div class="chips"><span class="chip"><b>Term</b> — gloss</span> …</div>
```

## Two-panel comparison + process/loop diagram
- `.grid.g2` of two `.flow-panel`s (each has a `.ph` uppercase label). Tint the "after" panel with `style="border-color:rgba(139,92,246,.35)"` and its `.ph` with `style="color:var(--violet)"`.
- Inside a panel: `.loop` containing `.node` (`.n-t` title + `.n-d` detail) separated by `<span class="arrow">→</span>`.

## Multi-column color-accented comparison ("platform" slide)
- `.grid.g5.plat`. Each column: `<div class="card cN"><span class="kick cN">KICKER</span><h3>Title</h3><p>…</p></div>` where `N` is 1–5.
- `c1`=green `c2`=cyan `c3`=purple `c4`=pink `c5`=orange (border-top + kicker color; auto-darkened in light theme).

## Numbered feature / asset slide
```html
<div class="asset-head"><span class="asset-num">1</span><h2 style="margin:0">Name</h2></div>
<p class="lead">What it is.</p>
<div class="asset-do"><span class="tick">▶</span><span><b>What to do:</b> the action.</span></div>
<a class="link" href="…">short-url</a>
```

## Step list / call to action
- `.steps` of `.step` rows (`.s-n` number + `.s-t` text). Make the final row `.step.go` with `.s-t.grad` for the big ask.

## Timelines (spine is the default)
- **Spine timeline (default)** — `.tf`, the horizontal animated variant. Reach for this first for any timeline slide. The gradient line self-draws, dots pop in sequentially with pulsing glow rings, and cards lift on hover; it replays each time the slide is (re)entered. Use up to 6 `.tf-item`s (stagger delays are wired for six); collapses to 2-col then 1-col on small screens. Snippet below.
- **Static timeline (fallback)** — `.timeline` of `.tl` cards (`.when` mono label + `h3` + `p`). A calm 3-column grid. Use only when you deliberately want a quiet, un-animated look (e.g. a closing "legacy" recap that shouldn't compete with the hero timeline), or when a slide has more than 6 moments.

## Bar chart
CSS-only horizontal bars that grow from zero on slide entry — no libraries. Use for any "by the numbers" / ranking / comparison of quantities (sales, revenue, adoption, scores). Set each `.bar-fill` width as a percentage of the largest value, and put the real figure as the fill text. Always ground the numbers in a real source; label the unit.
```html
<div class="bars">
  <div class="bar-row">
    <div class="bar-lbl">Greatest Hits <span>1981</span></div>
    <div class="bar-track"><div class="bar-fill" style="width:100%">25.0M</div></div>
  </div>
  <div class="bar-row">
    <div class="bar-lbl">Made in Heaven <span>1995</span></div>
    <div class="bar-track"><div class="bar-fill" style="width:80%">20.0M</div></div>
  </div>
  <!-- more .bar-row … widths relative to the top value -->
</div>
```
```html
<div class="tf">
  <div class="tf-line"></div>
  <div class="tf-row">
    <div class="tf-item">
      <div class="tf-dot"></div>
      <div class="tf-year">1946</div>
      <div class="tf-card"><h3>Zanzibar</h3><p>Born Farrokh Bulsara.</p></div>
    </div>
    <!-- repeat .tf-item up to 6 times -->
  </div>
</div>
```

## Links
- `.link` — monospace pill anchor (auto arrow prefix). Group several in `.recap` for a resources footer.

## Chrome (do not remove)
`.bg-glow` (ambient), `.progress` (top bar), `.brand` (top-left label — edit its text), `.counter` (auto), `.nav` (‹ ›), `.theme-btn` (☀/☾). The slide count is computed from the number of `.slide` elements.

## Theme
Dark by default; follows the OS `prefers-color-scheme` on load; toggled via the top-right button or `T`. Everything reads from CSS variables (`--bg --ink --muted --line --card --grad --blue --violet --pink`), so custom colors should reuse those variables (or the `cN` accent classes) to stay theme-correct. Avoid hard-coded light-on-dark hex in inline styles.
