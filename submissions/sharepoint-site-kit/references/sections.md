# Section library

Every section reads only CSS custom properties, so a new brand changes the tokens block and nothing else. All sections are in `assets/sections.css`; `assets/static-page-template.html` has the markup for each one with `{{PLACEHOLDER}}` slots and `repeat:start` / `repeat:end` markers.

## Tokens

| Token | Use |
|---|---|
| `--ground`, `--ground2` | Page background and alternate background |
| `--card` | Card surfaces |
| `--ink` | Headings and strong text |
| `--body` | Body text |
| `--muted` | Secondary text (checked for AA on ground, ground2 and card) |
| `--line` | Hairlines and card borders |
| `--accent`, `--accent2`, `--accent3` | Brand accents for shapes, rules and markers (decorative) |
| `--accent-ink` | Accent used as text or link color (checked for AA) |
| `--pale` | Tinted surface for pills and the featured document card |
| `--navy` | Deep color for the hero and the dark band |
| `--band-ink`, `--band-muted` | Text on `--navy` |
| `--on-accent` | Text on a solid accent fill |
| `--grad` | Brand gradient (rules, hero heading accent, avatars) |
| `--shadow` | Card shadow |
| `--fd`, `--ft` | Display and text font stacks |

Dark mode: the same tokens are redefined inside `@media (prefers-color-scheme:dark)` (static pages) and under `:root[data-theme="dark"]` (live pages, set by the theme bootstrap script). `scripts/extract_brand.py` writes both.

## Writing rules for every section

- Headlines (h2) are outcome-led: say what the reader gets or what the program achieves ("Six workstreams. One activation plan."), not the format ("Our workstreams").
- Derive the hero headline from the program's own source documents: what the program does for its audience, not how the team is organized. Offer the user 2 or 3 alternatives.
- Every section gets a short eyebrow label (`.kick`) above the h2 and at most one sentence of intro.
- American English. No em dashes. No filler words ("genuinely", "honestly", "really", "truly", "simply").
- Durations round up to 5, 10, 15, 20, 30, 45 or 60 minutes.
- Never invent a lead, date or number. Use "Lead to be confirmed" (`.ld.tbc`) or leave the item out.

## The sections

### 1. Hero (`header.hero`)
Program name as eyebrow, h1 with an accent span (gradient text), one lead sentence, up to two buttons, up to three stats. The two skewed shapes (`.shape.s1`, `.s2`) carry the brand motif; the site icon reuses the same motif. Keep the h1 under about 60 characters.

### 2. Executive summary (`.summary`)
Required at the top of every page. Three to five sentences: what the program does, for whom, what this site holds, and the one thing a first-time visitor should open. Sits over the hero edge on desktop, stacks on mobile.

### 3. At a glance / purpose (`.glance`)
Two to four cards with a pill label, a title and two sentences. Use for "what this site is for", phases, or goals.

### 4. Program documents (`.docs`)
One featured document (`.doc.feat`, the plan or charter) plus two to five links. Each card names the document type (Plan, Deck, Tracker). Links go to the file in the "0 Program" folder.

### 5. Workstream cards (`.grid > a.ws`)
One card per workstream folder: two-digit number, name, one-line description, Lead, "Open folder". The whole card is the link (folder link from `build_folder_links.py`, `target="_top"`). Add `data-folder="<exact folder name>"` so upkeep can match cards to folders. Lead comes from the library's Lead column; when empty use `<span class="ld tbc"><em>Lead</em>Lead to be confirmed</span>`.

### 6. Dark band for shared or supporting streams (`.band > .sub`)
Streams that serve all workstreams (data, delivery, learning). Each card has a verb chip (`.verb`, for example Decide, Deliver, Learn), a name, a line of text and a folder link. Use once per page.

### 7. Role lanes (`ul.lanes > li.lane`)
Three to six roles with two to four tasks each. Lane colors rotate through the accents. Good for workshops and RACI-style overviews.

### 8. Timeline / run of show (`ol.timeline > li.slot`)
Time, title, one line, duration pill. Durations follow the rounding rule. Stacks to one column on mobile.

### 9. Rhythm (`ol.rhythm > li.step`)
Meeting cadence: meeting name, cadence (Weekly, Monthly), purpose. Three steps fit one row on desktop.

### 10. Principles (`ol.princ`)
Four to eight numbered principles, each a bold lead phrase plus one sentence.

### 11. Team (`ul.people`)
Initials avatars by default. Only use photos the user supplies for this purpose; never pull internal profile photos into a page.

### 12. Feedback / call to action (`.ask`)
One headline, one sentence, one button (form, channel, or mail link the user supplies).

### 13. Footer (`.foot`)
Program name and "Last updated" date.

### 14. List view (`section.lv[data-list-view]`)
Items from a list on the SAME site as the page, with search, filters and a cards/table toggle. Use it when the user asks for "a list view of <list>" on any page, static or live, new or existing. Block: `assets/list-view-block.html` (parts: css, manifest entry, section, allowlist, runtime). Build and insert it with `scripts/build_list_view.py --into <page>`; never paste the parts by hand.

- **One section per list.** Each has its own `lv-config` (generated from the list schema) and `lv-snapshot`, and one entry in the page's `ka-livedata-manifest`, keyed by `spItemUrl`. Several list views on one page share one runtime script, one CSS block and one link allowlist.
- **Script-dependent.** A static page with a list view is no longer script-free: it carries one runtime script plus JSON blocks. The publish probe must confirm that scripts run (SKILL.md 2.1).
- **Layouts.** Cards (default) and a compact table with sortable column headers (`aria-sort`), a sticky header and a scrollable region; under 640 px the table renders as cards and the toggle hides.
- **Tools.** Search with match highlight; up to three filters in the bar (choice and managed metadata as select or multi-select, yes/no as an "Only ..." toggle, person, lookup); the rest in a "More filters" panel; active-filter chips with "Clear all"; sort (newest, oldest, title); result count in an `aria-live` region.
- **States.** Loading, ready, saved copy ("Showing a saved copy of the list from <date>."), empty ("The list has no items yet."), no match ("Nothing matches...") and error ("This list couldn't be loaded...").
- **Shareable.** Filters, search, sort and layout are mirrored to the query string with the section key as prefix (`?resources-type=Guide&resources-layout=table`); `#<key>-item-<ID>` scrolls to one item.
- **Pills.** Choice values get colored pills; colors rotate through `--accent`, `--accent2`, `--accent3`, `--navy` and two mixes, in the order of the column's choices, as tints with `--ink` text so they stay AA in light and dark.
- **Writing.** Outcome-led h2 and a short eyebrow like every section ("Everything you need to get started."). The list's own item text is shown as is.

## Accessibility and layout checklist

- One h1 per page; h2 per section with `aria-labelledby`; cards use h3.
- Decorative SVGs and shapes carry `aria-hidden="true"`; images carry `alt` (empty for decorative).
- Focus outline is visible on links, buttons and inputs (`:focus-visible`).
- Text pairs meet WCAG AA (4.5:1, or 3:1 for 24 px and larger). `extract_brand.py` adjusts tokens; `visual_check.py` verifies the rendered page.
- Breakpoints: 980 px (three columns to two) and 640 px (one column, 20 px side padding).
- `prefers-reduced-motion` turns off transitions.
- Static mode: one `<style>` element, no `<script>`, no external CSS or fonts. Exception: list view sections add their JSON blocks and one runtime script (`list-view-runtime`).
- List views: native controls only (select, checkbox, buttons), visible focus, table caption and `scope` on headers, result count in `aria-live="polite"`.
