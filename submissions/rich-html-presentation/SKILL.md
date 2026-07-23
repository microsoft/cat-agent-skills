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
Read `references/template.html` and `references/components.md` from this skill folder. The template is the source of truth for the design system. **Copy its `<style>` block and `<script>` block verbatim** — do not restyle or rewrite the navigation/theme engine. Only the slide content, `<title>`, and `.brand` label change.

### Step 3 — Structure the deck
- One idea per slide; pace ~1.5–2 minutes per slide (state the slide count against the target length).
- Typical arc: title → context/why → 4–8 concept slides → any "options/comparison" slide → a numbered feature/asset run → a call-to-action step list → a timeline/closing with links.
- Compose each slide from the catalog (`.card` grids, `.callout`, `.chips`, `.steps`, the animated `.tf` spine timeline by default (static `.timeline` only as a deliberate quiet fallback), `.bars` bar chart for any numbers/ranking/comparison, `.flow-panel`/`.loop`, `.asset-num`, `.plat` color columns). Reuse the CSS variables and `cN` accent classes so both themes stay correct — avoid hard-coded light-on-dark hex.
- **Use the full visual portfolio.** Aim for variety — don't build a deck of near-identical card grids. Across a typical deck reach for a spread of distinct components: a spine timeline, a bar chart wherever there are figures to compare, a color-accented `.plat` slide, a `.callout` for the one line to remember, a numbered `.asset-num` run, and `.steps` for a call to action. If the content contains any quantities (sales, counts, growth, rankings), render at least one `.bars` chart rather than listing the numbers as text — the user should not have to ask for a chart. Vary the layout from slide to slide so no two consecutive slides look the same.
- First slide keeps `class="slide title-slide active"`; every other slide is `class="slide"`. The counter total is computed automatically.

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

## Output
- A single self-contained `.html` file (inline CSS + JS, no external dependencies), delivered on the host's output surface — `output/` on artifact hosts, an attached file on Copilot Studio and similar.
- Dark theme by default, follows the OS setting on load, with a working light/dark toggle.
- Navigation: ← / → (also PageUp/Down, Space), Home/End, on-screen ‹ ›, F fullscreen, T theme, touch swipe.
- Tell the user the filename, the slide count, and the controls.

## Guardrails
- **Never fabricate facts** — look up the user's real data first; use visible `[placeholders]` for gaps.
- **Preserve the design system** — keep the template `<style>`/`<script>` intact so every deck matches; don't hand-roll a different look.
- **Self-contained only** — inline everything; no CDN links or external image URLs (embed or omit). This keeps the deck portable and offline-safe.
- **Verify before claiming done** — confirm the file reached the user (artifact present in `output/`, or file attached to this turn) before saying it's ready.
- **Match the delivery to the channel** — use artifact tools on Cowork; on Copilot Studio and other attachment-only hosts, return the file on the current turn and increment the file name (`-v2`, `-v3`, …) on every edit so the user always gets the fresh version.
- **Right tool for the format** — redirect `.pptx` requests to a PowerPoint/pptx workflow, and static document requests (memos/reports) to a document-writing workflow (e.g., Markdown/HTML document), rather than forcing them into this presentation template.
- **Accessibility** — keep readable contrast in both themes and don't remove the keyboard navigation.
