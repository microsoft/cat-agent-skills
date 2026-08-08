---
name: rich-html-presentation
description: >-
  Use this skill whenever the user asks to create, build, or revise a
  self-contained HTML or web slide presentation, browser slideshow,
  keynote-style deck, arrow-key-navigable presentation, or a deck matching a
  previous HTML presentation. Use it before authoring the HTML so the shared
  design system, channel-specific delivery, and verification steps are applied.
  Do not use it for PowerPoint (.pptx), static documents, or data dashboards.
---

## Instructions

### Step 1 — Gather the content first
If the deck is grounded in the user's world (a meeting/transcript, documents, a project, a product), retrieve it with the right tools (`SearchM365`, `ListCalendarView` + meeting-transcript tools, `ReadFileContent`, `web_search`) before authoring. Use clearly-marked placeholders (e.g. `[Add Q3 number]`) for anything you can't find — never invent names, numbers, quotes, or dates.

### Step 2 — Start from the template
Read `references/template.html` and `references/components.md` from this skill folder. The template is the source of truth for the design system. **Copy its `<style>` block and all five `<script>` blocks verbatim** — do not restyle or rewrite the navigation/theme engine. Only the slide content, `<title>`, and `.brand` label change.

**The engine ships as five separate small scripts on purpose. Never merge them into one, and never make one depend on a variable from another** — see "Preview-surface constraints" below. (The fifth is the optional speaker-notes tray; delete it wholesale if the deck has no notes.)

### Step 2a — Preview-surface constraints (why the engine looks the way it does)
Decks get shared, and most recipients open them in an **embedded preview** — the Teams file-preview pane, Outlook's reading pane, a SharePoint preview — not a real browser tab. Those hosts rewrite the document before rendering, and they impose three limits that are easy to violate by accident:

1. **Inline scripts over ~2000 characters are silently never executed.** (The Teams preview injects its own guard carrying `LIMIT=2000`.) Keep every `<script>` under **~1700 characters** to leave headroom.
2. **Each inline script is wrapped, so top-level `const`/`let` does not reach a shared global scope.** A `const` declared in one block is invisible to the next.
3. **Each inline script may get its own global object.** Even an explicit `window.myThing = {}` in one block can be `undefined` in the next. There is no reliable cross-block channel.

So every block must be **self-contained**: re-read what you need from the DOM, and if one block must trigger another, dispatch a DOM event rather than calling a function. The template's swipe handler does exactly this — it dispatches an `ArrowRight`/`ArrowLeft` `keydown` instead of calling the navigation code.

These failures are **silent and deceptive**: CSS still applies, so the deck looks styled and intentional while navigation is dead. That is why the template hardcodes the real slide total into the counter — a deck stuck on slide 1 reading `01 / 12` reports "navigation is broken", whereas `01 / 01` looks like a deliberate one-slide deck and gets shipped that way.

These limits are **observed behavior, not documented vendor contract** — they may change. Treat them as the reason for the structure, and re-verify with the checks in Step 5 rather than assuming.

### Step 3 — Structure the deck
- One idea per slide; pace ~1.5–2 minutes per slide (state the slide count against the target length).
- Typical arc: title → context/why → 4–8 concept slides → any "options/comparison" slide → a numbered feature/asset run → a call-to-action step list → a timeline/closing with links.
- Compose each slide from the catalog (`.card` grids, `.callout`, `.chips`, `.steps`, the animated `.tf` spine timeline by default (static `.timeline` only as a deliberate quiet fallback), `.bars` bar chart for any numbers/ranking/comparison, `.flow-panel`/`.loop`, `.asset-num`, `.plat` color columns). Reuse the CSS variables and `cN` accent classes so both themes stay correct — avoid hard-coded light-on-dark hex.
- **Use the full visual portfolio.** Aim for variety — don't build a deck of near-identical card grids. Across a typical deck reach for a spread of distinct components: a spine timeline, a bar chart wherever there are figures to compare, a color-accented `.plat` slide, a `.callout` for the one line to remember, a numbered `.asset-num` run, and `.steps` for a call to action. If the content contains any quantities (sales, counts, growth, rankings), render at least one `.bars` chart rather than listing the numbers as text — the user should not have to ask for a chart. Vary the layout from slide to slide so no two consecutive slides look the same.
- First slide keeps `class="slide title-slide active"`; every other slide is `class="slide"`. **Set `<span id="tot">` to the real slide count** — the nav script sets it too, but hardcoding the truth means a deck whose script was blocked reports broken navigation instead of pretending to be a one-slide deck.
- **Keep slides short enough to fit a short viewport.** A preview pane is roughly `1200×672` — much shorter than a browser window, and shorter still when the notes tray reserves space. The template's height media queries shrink the type scale, but they can't rescue a slide with eight dense cards. Prefer 4–6 cards; if a slide needs more, split it. A slide that fills the full height will collide with the fixed brand label at the top or the counter and nav at the bottom.

### Step 3a — Speaker notes (optional)
The template ships a collapsible notes tray. Author a slide's notes as a `<div class="spk">…</div>` **inside** its `<section class="slide">`; they never render on the slide itself, and the tray shows the note for whichever slide is active.

- **N** toggles the tray, **Esc** collapses it, and a **Hide** link on the collapsed bar removes it from the screen entirely for presenting (**N** brings it back).
- Add notes when the user asks for them, or when the deck will be presented by someone who wasn't in the room. Write what the presenter should *say* and watch for — not a re-reading of the slide.
- **If a deck carries no notes, delete the tray** — its markup, its CSS block, and its script block. An empty tray is worse than no tray.
- **Notes are not private.** They ship inside the same file and are one "view source" away. Never put anything in them you wouldn't hand to the recipient. For a deck going outside your organization, strip the `.spk` blocks from the file rather than relying on the tray being collapsed.

### Step 4 — Detect the channel, then write the file
First determine which delivery surface is available — the tools differ by host, so pick the matching path:

- **Cowork / artifact-capable hosts** (a `CreateArtifact` / `EditArtifact` / `CopyArtifact` tool exists): create the deck with **CreateArtifact** (`surface="output"`, a `.html` path), passing the full HTML as `content`; use **EditArtifact** for later tweaks. `output/` is read-only to the Write tool — the artifact tools are the write path. For a big rebuild, build in `working/` then publish with **CopyArtifact**.
- **Copilot Studio and other hosts without artifact tools** (only a file-return / attachment mechanism is available): write the full HTML to the host's file-output location (commonly a bash-writable dir such as `/app/created/` — check the host's file conventions rather than assuming a path), then **return it as a downloadable attachment on the same turn**. Do not "edit in place" and report done: on these hosts an in-place edit from a previous turn is NOT retrievable by the user — every delivery must be a fresh file attached to the current response.

If unsure which surface you're on, probe for the artifact tools first and fall back to plain file return. Resolve the write path once, up front — don't burn turns retrying sandbox paths.

### Step 4a — Version file names on every edit (non-artifact hosts)
On hosts where you re-attach the file each turn (Copilot Studio), the single most common failure is reusing the same file name and/or editing in place — the user then gets a stale file or nothing. **Every time you deliver a change, emit a brand-new incrementing name**: `<topic>-v1.html`, `<topic>-v2.html`, `<topic>-v3.html`, … Never say "updated in place"; always attach the new file and tell the user which version is current. On artifact hosts (Cowork) only, keep a stable name and edit in place with EditArtifact.

### Step 5 — Verify delivery
Confirm the `.html` file actually reached the user before claiming done:
- Artifact hosts: run `Glob output/**/*` and confirm the `.html` is present.
- Non-artifact hosts: confirm the file is attached to the current turn's response.
If missing, re-create/re-attach — never report success unverified.

### Step 5a — Verify it survives a preview pane
Before saying it's ready, check the finished HTML against the constraints in Step 2a. These are cheap text checks — do them on the file you actually produced.

> **Strip HTML *and* CSS comments before counting anything.** The `<head>` comment and a comment inside `<style>` both quote the literal strings `<script>`, `<section class="slide">` and `<div class="spk">` as documentation. A regex that only strips `<!-- … -->` will report a phantom script block, an inflated slide count, or a phantom speaker note. This has produced a wrong answer on every one of those three counts — strip `/* … */` too, every time.

1. **Every `<script>` under ~1700 characters**, measured on the file as written. CRLF line endings add ~1 byte per line, so a block that measures 1500 with LF reads ~1560 with CRLF. If a real block is over, split it into smaller self-contained blocks — never leave a single large engine script.
2. **No cross-block state.** No block may read a variable or `window.*` property that a different block created.
3. **Counter total matches the real slide count** in the markup, not `01`.
4. **`justify-content:safe center`** is still on `.slide` (with the plain `center` fallback declared before it), and the two `@media (max-height: …)` blocks are present.

If you can render the file, load it at **1200×672** and check two different things:

- **Overflow** — no slide has `scrollHeight > clientHeight`.
- **Chrome collision** — the fixed `.brand` (top-left), `.counter` (bottom-left) and `.nav` (bottom-right) float *above* the slide, so a slide can pass the overflow check and still have its first or last line sitting underneath them. Compare the bounding box of the slide's first and last visible content against those three. Measure the text, not the block: `.content` children are full-width, so a naive box-intersection test reports a collision on almost every slide.

Report the slide count and that the preview checks passed.

## Output
- A single self-contained `.html` file (inline CSS + JS, no external dependencies), delivered on the host's output surface — `output/` on artifact hosts, an attached file on Copilot Studio and similar.
- Dark theme by default, follows the OS setting on load, with a working light/dark toggle.
- Navigation: ← / → (also PageUp/Down, Space), Home/End, on-screen ‹ ›, F fullscreen, T theme, touch swipe.
- Optional speaker-notes tray: N toggles, Esc collapses, and a Hide link removes the bar for presenting.
- Tell the user the filename, the slide count, and the controls.

## Guardrails
- **Never fabricate facts** — look up the user's real data first; use visible `[placeholders]` for gaps.
- **Preserve the design system** — keep the template `<style>` and all five `<script>` blocks intact so every deck matches; don't hand-roll a different look.
- **Never consolidate the engine scripts** — they are split so embedded previews (Teams, Outlook, SharePoint) will execute them, and each is self-contained because those hosts may isolate every script's global scope. Merging them, or introducing a shared global between them, silently kills navigation for anyone who opens the deck in a preview pane.
- **Self-contained only** — inline everything; no CDN links or external image URLs (embed or omit). This keeps the deck portable and offline-safe.
- **Verify before claiming done** — confirm the file reached the user (artifact present in `output/`, or file attached to this turn) before saying it's ready.
- **Match the delivery to the channel** — use artifact tools on Cowork; on Copilot Studio and other attachment-only hosts, return the file on the current turn and increment the file name (`-v2`, `-v3`, …) on every edit so the user always gets the fresh version.
- **Right tool for the format** — redirect `.pptx` requests to a PowerPoint/pptx workflow, and static document requests (memos/reports) to a document-writing workflow (e.g., Markdown/HTML document), rather than forcing them into this presentation template.
- **Accessibility** — keep readable contrast in both themes and don't remove the keyboard navigation.
