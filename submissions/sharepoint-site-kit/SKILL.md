---
name: sharepoint-site-kit
description: |
  Sets up a SharePoint team site for a program and builds a branded HTML landing page for its Site Pages library. Three parts: library setup (workstream folders, Lead column, Workstreams view), page builder (static HTML, live list-backed HTML or a standard page, styled from a PowerPoint brand template, with optional filterable list view sections from the same site; the first page becomes the site's home page) and upkeep (fix links after folder renames). Use when the user asks to "set up a SharePoint site for my program", "build an HTML page for SharePoint", "make a landing page for this site", "make the page our home page", "add a list view of <list> to the page" or "we renamed a folder, update the site page". Do NOT use for Word or PowerPoint documents, standalone HTML not meant for SharePoint, list data reports or charts, or permissions and governance work.
license: MIT
compatibility: Needs SharePoint access through the agent's SharePoint tools or Microsoft Graph (Sites.ReadWrite.All for folders and pages), a browser tool for click-tests and Make homepage, and Python 3 with lxml and Pillow. Playwright for Python is optional for the visual check.
metadata:
  category: productivity
  icon: Globe
  version: "1.3.0"
---

# SharePoint Site Kit

## Overview

Turns a program's source document (plan, deck, charter) into a working SharePoint team site: one folder per workstream with a lead and description, and a branded landing page in the Site Pages library that links to each folder. Afterwards it keeps the page in step with the library. The three parts work alone or together:

1. **Library setup:** workstream folders, a "0 Program" folder that sorts first, a Lead person column, the built-in Description column, a "Workstreams" view, and the source document copied into "0 Program".
2. **Page builder:** a branded, self-contained page in one of three modes: (a) static showcase HTML, (b) live list-backed HTML, (c) standard modern page (.aspx) as the fallback. The layout and motion follow the kit's design language (see 2.2a); colors and fonts come from a PowerPoint template, else the site's brand kit, else a neutral default. On request, any HTML page (new or existing) can also hold one or more **list view sections**: items from a list on the same site, with search, filters generated from the list's columns, and a cards or table layout (2.5). The first page the kit builds on a site becomes the site's home page through SharePoint's **Make homepage** command, after it is published (2.8).
3. **Upkeep:** re-check folder names and links after renames or additions, fix only what changed, flag folders without a card, refresh leads and descriptions, regenerate the link allowlist on live pages.

## When to Use

- "Set up a SharePoint site for my program" or "create folders for each workstream from this plan"
- "Build an HTML page for SharePoint", "make a landing page for this site", "use this brand deck for the page"
- "Build a gallery page backed by a list"
- "Make the new page our site's home page", "set this page as the homepage"
- "Add a list view of <list> to the page", "show the <list> list on the site page with filters", "pull items from a list on this site into the page", "can the page show our Resources list with filters?"
- "The folder links on my site page are broken", "we renamed a folder, update the site page"

## When NOT to Use

- Word, PowerPoint or PDF documents: use the document skills.
- Standalone HTML that will not live in SharePoint: use the general HTML or page skill.
- Reports, charts or analysis over SharePoint list data: use a data or reporting skill. A list view section shows and filters items; it does not count, chart or summarize them.
- A list on another site than the page: the list view mechanism binds to the page's own site. Offer a link card or a static snapshot instead.
- Site permissions, sharing, retention, sensitivity labels or other governance work.
- Creating the site itself when the user has not asked for it (site creation is a separate, approval-worthy action).

## Quick Start

```
User: "Set up our SharePoint site for the program in this deck and build a landing page with our brand template."
1. Intake: ask the five intake questions in one message (mode first).
2. Part 1: show the folder plan, create folders and columns after the user confirms, copy the source deck into "0 Program".
3. Part 2: publish probe, extract brand, draft content with 2-3 headline options, choose the hero style and motif, build <Page-Name>.html.
4. Quality gate: visual_check.py at 1440 and 390 px, light and dark; fix and repeat; click-test links.
5. Upload <Page-Name>.html once, get approval, publish it.
6. First page on the site: Make homepage on the published page, load the site root to confirm, hand over the manual-steps checklist.

User: "Can the page also show our Resources list with filters?"
1. Resolve "Resources" among the site's visible lists (ask if several match); read its columns and items.
2. build_list_view.py proposes title, description, link, people, date, filters and table columns; confirm with the user.
3. Build into the page, regenerate the allowlist and snapshot, run the script probe if the page was static.
4. Quality gate with sample data, one upload, verify live rows, filters, table toggle and shared URLs on the site.
```

## Intake interview

Ask these in ONE message before any work. Never assume the mode.

| # | Question | Default if the user has no preference |
|---|---|---|
| 1 | **Page mode:** (a) static showcase HTML page, (b) live HTML page that renders a SharePoint list, or (c) standard SharePoint page (.aspx)? HTML pages render in the Site Pages library; they do not download. | (a) static |
| 2 | Site URL (or "create the folders in which site?") | none; required |
| 3 | Source document or deck for the program (workstreams, leads, purpose) | none; for upkeep only, the existing page |
| 4 | Brand input: a PowerPoint template or brand deck (.potx/.pptx)? Optionally an image for the hero background, or to take the colors from | the site's brand kit, else neutral; motif `orbs` |
| 5 | Sibling sites or pages this one must look different from | none |
| 6 | **First page only:** "This will become your site's home page. Your current home page (for example Home.aspx) is kept, not deleted, and can be restored. OK, or keep the current home page?" | yes, make it the home page |

Ask question 6 only when the kit has built no page on this site before, or the site still opens its default `Home.aspx`. Record the current home page file name (read it from the site root URL in the browser, or the `WelcomePage` value of the root folder) so it can be restored. Later pages do not become the home page unless the user asks.

Also settle: the page name, which parts to run (1, 2, 3 or all), and for live mode the list name.

**Page name.** Name the HTML file after the program, in title case with hyphens, for example `AI-FinOps-Cowork-Workshop.html` or `CAPE-Cowork-Activation.html`. The file name shows in Site Pages and in the browser tab, so it must read well. Never add `-preview`, `-draft` or `-v1` to it. Write `<Page-Name>` below for this name.


**List view intake** (when the user asks for a list on the page, in the same message as above or on its own):

| # | Question | Default |
|---|---|---|
| L1 | Which list? (name as shown on the site) | none; resolve on the page's site (2.5 step 1) |
| L2 | Layout: cards or table? Both stay available through the toggle. | cards |
| L3 | Which columns to filter on, and any columns that must never show (internal notes, personal data)? | the generated proposal (2.5 step 3); no sensitive columns assumed |
| L4 | Which page, and where on it? | the page being built, after the workstreams; for an existing page, before the footer |

## Tool map

Use the SharePoint tools you have; [references/graph-api.md](references/graph-api.md) lists the Graph call behind each one and the pinned payloads.

| Need | Tool (Cowork names in parentheses) |
|---|---|
| Find a list by name for a list view | `ListLists` (skip hidden lists and document libraries), then `ListListColumns` and `ListListItems` |
| Resolve site, drives, lists | site lookup (`GetSite`, `ListSiteDrives`, `GetDefaultDrive`, `ListLists`) |
| Folders and files | `GetDriveChildren`, `CreateFolder`, `UploadFileContent`, `ReadFileContent` |
| Columns and list items | `ListListColumns`, `GetListSchema`, `UpdateListSchema`, `ListListItems`, `UpdateListItem` |
| Brand kit | `GetBrandKits`, `GetBrandKit` |
| Anything else in Graph | a Graph call tool (`CallGraph`) |
| Click-tests, UI-only steps, screenshots | browser tool (`browser_actions`) |
| Make homepage (2.8) | browser tool; else SharePoint REST (`_api/web/rootfolder`) if a REST-capable connection exists; Graph v1.0 has no endpoint for this |
| Scripts in this skill | Bash with Python |

## Part 1: Library setup

1. **Read the source.** Extract program name, purpose, workstreams, shared or supporting streams, leads and one-line descriptions. Mark anything not stated as unknown; never invent a lead.
2. **Sanitize names.** `python scripts/build_folder_links.py sanitize "<name>" ...` removes characters SharePoint rejects (`" * : < > ? / \ |`, trailing dots, reserved names). Report every rename.
3. **Show the plan** as a table (folder, lead, description) including "0 Program" (the leading "0 " sorts it first). Shared streams can use a verb prefix ("Decide - Insights Dashboard"). Wait for the user's confirmation before writing anything.
4. **Create folders** in the site's default Documents library with conflict behavior "fail"; report folders that already exist instead of overwriting.
5. **Columns.** Add a single-value person column "Lead" if missing. Use the library's built-in Description column (internal name usually `_ExtendedDescription`; confirm in the column list). Write descriptions and leads to each folder item. If a person's site user ID is not available, leave the Lead empty and add it to the manual steps.
6. **View.** Create a "Workstreams" view with Name, Lead, Description, Modified, sorted by Name. Views have no Graph endpoint: use the schema tool if it supports views, else the browser, else give the manual step (library > view menu > Edit current view, choose columns, Save view as "Workstreams").
7. **Copy the source document** into "0 Program". Confirm the copy landed by listing the folder.
8. Report: folders created, renamed, already there; columns added; view status; what remains manual.

## Part 2: Page builder

### 2.1 Publish probe (once per site, before building)

HTML pages can be blocked by tenant-wide settings, and uploads can fail to overwrite. Find out early:

1. Find Site Pages: `lists/Site Pages/items?$expand=driveItem` (the name `SitePages` returns 404, and the library is hidden from plain list listings). Note existing `.html` pages and their names.
2. Upload a tiny static file `<Page-Name>-probe.html` (one style element, one heading, no scripts).
   **Live pages and list views need scripts.** In that case also upload `<Page-Name>-probe-script.html`: one heading reading "Scripts blocked" and one inline script that changes it to "Scripts run", plus a `ka-livedata-manifest` entry for the target list and a line that prints whether `window.__LD_RESULTS__` holds that list's `spItemUrl`. Record both results.
3. Open it in the browser and try **Publish page** (or ask the user to). Record: renders, publishes, or "Could not publish your page... unexpected error".
4. Upload the probe again under the same name. Record whether overwrite works.
5. Decide:
   - **Publishes, overwrite works:** iterate on `<Page-Name>.html` itself. Review happens on the unpublished upload; publishing is the go-live step.
   - **Publishes, no overwrite:** one upload per approval round. The first round uses `<Page-Name>.html`; later rounds add a round number (`<Page-Name>-2.html`, `<Page-Name>-3.html`). Track every superseded name as a leftover.
   - **Blocked:** stop uploading. Build and check the page locally, then deliver the file with the supported path: **Pages > Create or upload > Upload HTML page**, then **Publish page**. Add an admin note: the Microsoft 365 baseline security settings "Block creation and editing of classic SharePoint pages" and "Don't allow new custom scripts" (Microsoft 365 admin center: Settings > Org settings > Security and privacy) can block HTML pages; the admin decides. Never try to work around a policy. Offer mode (c) as an alternative.
6. Script probe: scripts do not run, so live pages and list views cannot work here; use the static snapshot fallback (2.5 step 8b) and tell the user why. Scripts run but live data is not injected: the saved copy inside the page (2.5 step 8a) works, but it does not update by itself.
7. Add `<Page-Name>-probe.html` (and `<Page-Name>-probe-script.html`) to the leftovers list. The agent cannot delete files.

Skip the probe for mode (c), and in upkeep when the site already has a published HTML page that was uploaded the same way. Run the script probe when adding the first list view to a page that had no scripts, even if the static probe passed before.

### 2.2 Brand

1. **PowerPoint template given:** `python scripts/extract_brand.py brand.potx --css-out brand.css --json-out brand.json --logo-out logo.png`. It reads the theme colors (dk1, lt1, dk2, lt2, accent1-6, hlink), fonts, master gradients and the largest master or layout image, builds light and dark tokens, checks WCAG AA for every text and background pair, and adjusts lightness where a pair fails. Exit 3 means a pair still fails: fix by hand.
2. **No template:** read the site's brand kit, write its colors to a palette JSON (mapping in [references/graph-api.md](references/graph-api.md)) and run `extract_brand.py --palette kit.json --css-out brand.css --json-out brand.json`.
3. **Neither:** `extract_brand.py --neutral --css-out brand.css --json-out brand.json`. If the user supplied an image and wants the page colors to come from it, run `python scripts/prepare_hero_image.py image.jpg --css-out hero-img.css --palette-out image-palette.json`, then `extract_brand.py --palette image-palette.json --css-out brand.css --json-out brand.json`. With a template, the template colors win.
4. Confirm the logo candidate is a logo and not a background photo before using it.
5. **Sibling sites:** pages share the design language in 2.2a. Tell siblings apart with the other hero style (`wash` or `deep`), a different motif and a different lead accent. Say what you changed and why.
6. Brand fonts render only where installed; the stacks fall back to Segoe UI and system fonts. Never link external font files.

### 2.2a Design language (look and feel)

Every HTML page follows one design family, modeled on the layout of the AI FinOps for Cowork workshop and CAPE Cowork Activation site pages, but with generic decoration. The template carries it; the brand tokens only recolor it. Do not fall back to a plain layout.

- **Hero, two styles.** `hero wash` (default): a light gradient wash in the lead accent, a glass badge eyebrow, a large light-weight h1 with an italic accent phrase, an optional audience row and an optional right column of two or three glass "problem" cards. `hero deep`: a dark brand band with radial glows, a bold white h1 with a gradient-text accent and stat bars. Pick `deep` when a sibling uses `wash`, or when the brand template is dark-led.
- **Hero motif, one per page,** set with a class on the hero: `motif-orbs` (default, soft blurred glows), `motif-arcs` (thin concentric rings from one corner), `motif-grid` (dot grid fading in toward the right) or `motif-image` (an image the user supplied, prepared with `prepare_hero_image.py` and set as `style="--hero-img:url(...)"`, faded away from the text side; in `deep` it sits under a dark scrim). All motifs use the theme colors.
- **No logo look-alikes.** Never draw decoration that resembles a product or company logo: no skewed or slanted rounded parallelograms, no overlapping tilted tiles, no rainbow product gradients, no logo files or logo screenshots as backgrounds. Card glows, icons and the brand mark are circles or soft radial light.
- **Top bar** with the program name and a pure CSS light/dark switch (a checkbox, no script). It overrides the OS setting both ways.
- **Sticky section nav** of pill links under the hero, one per section kept on the page.
- **Executive summary card** that overlaps the hero edge, with a vertical "Executive summary" tag.
- **Section headers:** an eyebrow with a short gradient chip, then a light-weight h2 (40 px) and one sentence of intro on the right.
- **Color rotation:** add `rot` to a grid and its cards cycle through the six theme accents (`--c1` to `--c6`) for top borders, number chips, pills, glows and avatars.
- **Cards:** 22 to 28 px corner radius, soft two-layer shadow, lift on hover, a soft round corner glow on workstream and kit cards, arrow icons that slide on hover.
- **Closing feedback band:** a wide rounded gradient band with a soft round glow, headline, one sentence and one button.
- **Motion:** staggered rise on hero items and the summary only, slow drift on the orb glows; all motion stops under `prefers-reduced-motion`.
- **Extra sections** available from the references: outcomes grid with a before/after shift, journey milestones, kit tickets and a note callout. Use them only when the source has the content.

### 2.3 Content

1. Executive summary (three to five sentences) at the top: what the program does, for whom, what this site holds, what to open first.
2. Headline: derived from the source documents (what the program does, not how the team is organized). Offer 2 or 3 alternatives and let the user pick.
3. Outcome-led h2 per section, short eyebrow labels, one sentence of intro at most.
4. Leads only from the library's Lead column; empty shows "Lead to be confirmed".
5. Round durations up to 5, 10, 15, 20, 30, 45 or 60 minutes.
6. American English, no em dashes, no filler words.

Pick sections from [references/sections.md](references/sections.md): hero, section nav, executive summary, at a glance, program documents, workstream cards, dark band for shared streams, role lanes, timeline, rhythm, principles, team, feedback, footer, and list view (on request, 2.5).

### 2.4 Build

- **(a) Static:** start from `assets/static-page-template.html`. Replace the brand block with `extract_brand.py --from-css brand.css --inject <file>` (the block written in 2.2), or rerun 2.2 with the same source plus `--inject <file>`. Set the hero classes (`wash` or `deep`, plus one `motif-*`). Fill placeholders, repeat blocks, delete unused optional sections and their nav links. Build every folder link with `python scripts/build_folder_links.py links --site <site URL> --names "<folder>" ...` (library view URL with the `id=` folder path; a plain folder URL lands at the library root). Every link gets `target="_top" rel="noopener noreferrer"`. Pure CSS: one style element, no scripts, unless the user adds a list view (2.5).
- **(b) Live list:** start from `assets/live-list-template.html` and read [references/live-list-pattern.md](references/live-list-pattern.md) first. The mechanism was inferred from a working page and has no public documentation. Fill site URL, list ID and label in both the manifest and `site-page-config` (they must match exactly), edit `COLUMN_MAP` (the `build_list_view.py` proposal in 2.5 step 3 gives the column names), then run `python scripts/allowlist_from_list.py --items items.json --page <Page-Name>.html [--snapshot]`. After upload, verify on the site that live data renders; if `__LD_RESULTS__` is absent, fall back to the snapshot, else to a static snapshot page (mode a) and tell the user it will not update by itself.
- **(c) Standard page:** create the page with the pinned Graph beta `sitePage` payload in [references/graph-api.md](references/graph-api.md) (text web parts with basic HTML; styles are stripped). Beta is not supported for production use: say so, and publish only after approval.
- Save the working copy locally as `<Page-Name>.html`. Never embed tokens, keys, internal photos or personal data the audience should not see.

### 2.5 List view sections (on request)

Use when the user asks for "a list view of <list>" on a page, or to pull items from a list on the site into the page. Works on a new static or live page and on an existing page. Read [references/live-list-pattern.md](references/live-list-pattern.md) ("List view sections") first; the mechanism is inferred, not documented.

1. **Resolve the list on the page's site.** List the site's lists; skip hidden lists and document libraries unless the user asked for a library. Match the name case-insensitively. Several matches: show them and ask which. None: show the visible lists and ask. A list on another site: say this mechanism cannot read it and offer a link card or a static snapshot.
2. **Read the schema and a sample.** Get the list's columns (JSON with `name`, `displayName`, `hidden`, `readOnly` and the type facets) and up to 200 items. Ask which columns must never show; pass them to `--sensitive`.
3. **Propose the view.** `python scripts/build_list_view.py --columns columns.json --items items.json --label "<list name>" [--sensitive <col> ...]` prints the mapping (title, description, link, people, date), the ranked filters (top 3 in the bar, the rest under "More filters"), sort options, table columns and what it left out. Show the two tables to the user and take changes (`--filters`, `--primary`, `--layout`, `--exclude`). Default to the proposal when the user has no preference.
4. **Build.** Same command with `--web-url <site URL> --list-id <list id> --key <short key> --noun <singular,plural> --eyebrow ... --h2 ... --intro ... --into <Page-Name>.html`. It adds the CSS once, merges the manifest entry, inserts the section (static template marker, else end of main), and adds the allowlist and the one runtime script once. For an existing page, download it first and build into the local copy. One run per list; several list views per page are fine (one manifest entry per list, keyed by `spItemUrl`).
5. **Allowlist and snapshot.** `python scripts/allowlist_from_list.py --items <list1>.json [<list2>.json] --view <key1> [<key2>] --page <Page-Name>.html --snapshot`. Pass every list view on the page in one run. The snapshot keeps only the columns the view maps, never sensitive ones.
6. **Say what changed.** A static page with a list view now needs scripts: tell the user, and run the script probe (2.1) if it has not passed on this site.
7. **Verify.** Locally: `visual_check.py <page> --sample-data <key>=rows.json` (every list view must reach `data-state="ready"`). On the site, after upload: live rows render with no "saved copy" note; one bar filter, one "More filters" filter, search, the table toggle and a column sort work; the copied URL reopens the same view; item links open; the allowlist link count matches the list.
8. **Fallbacks, in order.** (a) Live data not injected but scripts run: the section shows its snapshot with "Showing a saved copy of the list from <date>." and tell the user it updates only when the agent reruns step 5. (b) Scripts blocked: `build_list_view.py ... --static-snapshot --into <page>` replaces the section with a static, dated table or cards ("Saved copy of the <list> list from <date>. It does not update by itself."); when no live list view is left it removes the runtime, so the page is script-free again. (c) HTML pages blocked: mode (c) with a List web part the user adds (manual step).

### 2.6 Quality gate (required before any upload the user will see)

1. `python scripts/visual_check.py <Page-Name>.html --out shots/ [--sample-data rows.json | <key>=rows.json ...] [--list-links]`. It screenshots 1440 px and 390 px in light and dark mode and checks overflow, contrast, placeholders, folder-link form, alt text, binding (gallery and every list view) and allowlist.
2. If Playwright is missing (exit 2), do the same pass with the browser tool: both widths, both color schemes, full-page screenshots.
3. Look at every screenshot for alignment (card rows, footers), cut-off text and low contrast on gradients. Check the design language too: the motif visible but not reducing headline contrast, nothing that looks like a logo, summary card overlapping the hero edge, rotating card colors, the light/dark switch flipping the whole page.
4. Fix, then repeat until clean. Batch all fixes before the next upload.
5. After upload, click-test every link in the browser: folder links must open the folder itself.

### 2.7 Upload, approve, go live

1. Upload once as `<Page-Name>.html` and leave it unpublished (if overwrite failed in the probe, later rounds use `<Page-Name>-2.html` and so on).
2. Show the user the page link and screenshots. Make the requested changes locally, run the gate again, upload once more.
3. Only after the user approves, publish the approved upload (or ask the user to click **Publish page**). If the approved file carries a round number, tell the user they can rename it to `<Page-Name>.html` after deleting the older round. If the probe showed publishing blocked, the user uploads it with **Pages > Create or upload > Upload HTML page** and publishes it.
4. First page on the site and the user did not opt out: make it the home page (2.8) only after it is published.
5. List every superseded round and the probe files for the user to delete.

### 2.8 Make it the home page (first page only)

Run after the live page is published, never on an unpublished upload: a home page that is not published can show visitors a draft or an access error. Needs site owner or edit rights on the site.

1. **Record the old home page** (from intake, for example `Home.aspx`). It stays in Site Pages; nothing is deleted.
2. **Set it, in this order of preference:**
   a. **Browser tool:** open Site Pages (`<site>/SitePages/Forms/ByAuthor.aspx`, or the All Pages view), select the published `<Page-Name>.html`, open **...** (More), choose **Make homepage**, confirm.
   b. **No browser, SharePoint REST connection available** (the agent usually lacks one): `POST <site>/_api/web/rootfolder` with headers `X-HTTP-Method: MERGE`, `IF-MATCH: *`, `Content-Type: application/json;odata=verbose`, body `{"__metadata":{"type":"SP.Folder"},"WelcomePage":"SitePages/<Page-Name>.html"}`. Graph v1.0 has no endpoint for the welcome page ([references/graph-api.md](references/graph-api.md)).
   c. **Neither:** give the user the manual clicks: Site Pages library > select the page > ... (More) > Make homepage.
3. **Verify:** load the site root URL (`<site>/`) in the browser and check that the new page loads, styled, with working links. Ask the user to check from a visitor account if they can.
4. **UNVERIFIED:** whether **Make homepage** is offered for `.html` pages in Site Pages, and whether it works on a draft. If the command is missing, greyed out, or the site root does not load the page: keep the old home page as home, add a prominent link or hero button to the HTML page on it (manual step: edit the home page > add a Button or Quick links web part), and tell the user.
5. **Restore:** to go back, run **Make homepage** on the old page (for example `Home.aspx`).

### 2.9 Site icon (optional)

`python scripts/make_site_icon.py --brand brand.json --out site-icon [--initials XY] [--motif orbs|arcs|grid]` draws the page's hero motif in the page palette, padded for SharePoint's round crop, at 512 and 256 px. Do not use generic logos, stars or stock symbols. Setting it is manual: Settings (gear) > Change the look > Header > Site logo > Change.

## Part 3: Upkeep

1. Download the current page (or use the local copy) and list the library's top-level folders.
2. `python scripts/build_folder_links.py check --site <site URL> --page page.html --folders children.json`. It reports links that work, broken links, likely renames and folders with no card.
3. For a rename that is a new word (for example Kickstarter to Activate) the script lists candidates; ask the user which folder each old link moved to, then rerun with `--rename OLD=NEW --fix-out page.fixed.html`. Only changed links are touched. Ask whether the card title should change too.
4. For each unlinked folder, ask for the lead and a one-line description (or read them from the Lead and Description columns), then add a card.
5. Refresh leads and descriptions from the library columns; keep "Lead to be confirmed" where the column is empty.
6. Live pages and list views: rerun `allowlist_from_list.py` against current list items (all list views in one run, with `--snapshot` to refresh the saved copies). If the list gained or renamed columns, rerun `build_list_view.py` with the same key; it replaces the section and keeps its snapshot.
7. Run the quality gate, upload once, click-test, list leftovers.
8. **Home page replaced by a new version:** when overwrite fails, each new version gets a numbered file name, so the home page still points at the old file. After the new version is published, run **Make homepage** (2.8) on the new file and verify the site root loads it; list the old file as a leftover only after that check passes.

## Decision points

| Situation | Decision |
|---|---|
| Mode not stated | Ask. Never default silently to .aspx. |
| Probe shows publishing blocked | Deliver the file plus the Upload HTML page path and the admin note; offer mode (c). |
| Overwrite fails | One upload per approval round, `<Page-Name>-2.html` and up, leftovers listed. |
| Sibling page uses the same hero style | Switch to the other hero style, motif and lead accent. |
| Live data missing on the site | Snapshot in page, else static snapshot page or section, else mode (c). |
| User asks for a list on the page | List view section (2.5); resolve the list on the page's site; ask if several match. |
| List view requested on a script-free page | Say the page will need scripts; run the script probe first. |
| List is on another site | Out of scope for list views: link card or static snapshot. |
| Column may hold internal or personal data | Ask; pass it to `--sensitive` so it never shows or enters a snapshot. |
| First page on the site | Confirm at intake that it becomes the home page; record the old home page; Make homepage only after publishing (2.8). |
| Later pages | Not the home page unless the user asks. |
| Lead unknown | "Lead to be confirmed"; ask the user. |
| Folder name invalid | Sanitize, report the rename. |
| Folder already exists | Keep it, report it, do not overwrite. |
| Brand pair fails AA after adjustment | Fix the token by hand; never ship a failing pair. |

## Failure handling

| Error or symptom | Action |
|---|---|
| "Could not publish your page... unexpected error" | Treat as a tenant setting block (2.1 step 5). Do not retry with tricks. |
| `SitePages` returns 404 | Use the display name `Site Pages`, URL-encoded. |
| Folder link opens the library root | Rebuild with `build_folder_links.py links`. |
| Card link broken after a rename | Part 3. |
| View creation not possible through tools | Browser, else manual step. |
| Person column write fails | Leave empty, add to manual steps. |
| Graph beta page call fails or changes shape | Report the error and the payload used; offer static HTML delivery. |
| Page renders unstyled in SharePoint | Check for more than one style element or stripped markup; static pages must be self-contained. |
| List view shows "This list couldn't be loaded" | Check the console: binding mismatch (manifest entry vs `lv-config.source`, often the label after a list rename): rebuild with the current list name; no live data and no snapshot: rerun step 5 with `--snapshot`. |
| Only one of several list views loads on the site | Multi-entry manifests are unverified: keep one live list view per page, snapshot the others. |
| Make homepage missing or greyed out for the `.html` page | Unverified for HTML pages: keep the old home page as home, add a prominent link or hero button to the HTML page, tell the user. |
| Make homepage denied, or REST call returns 403 | Needs site owner or edit rights: give the manual step to a site owner. |
| Publishing blocked, so the page stays a draft | Do not make a draft the home page. The user uploads it with Pages > Create or upload > Upload HTML page and publishes it; then Make homepage. Else keep the old home page and link to the HTML page. |
| Site root still loads the old page | Recheck in a private window (caching); else repeat 2.8 step 2, then the fallback in step 4. |
| `build_list_view.py` exits 2 "no Title column" | Pick the title column with the user; the list may be a library or custom-titled list. |

## Manual-steps checklist (hand to the user at the end)

- [ ] Delete superseded rounds and the probe files in Site Pages: (list them by name)
- [ ] Publish the page if the agent could not: Pages > the page > Publish page
- [ ] If HTML pages are blocked: Pages > Create or upload > Upload HTML page, then Publish page; or ask the admin to review the baseline security settings named above
- [ ] Home page (first page only), if the agent could not set it: Site Pages > select `<Page-Name>.html` > ... (More) > Make homepage; then open the site root to check. To restore the old one: Make homepage on it (for example Home.aspx)
- [ ] Site logo: Settings (gear) > Change the look > Header > Site logo > Change (use `site-icon-512.png`)
- [ ] Folder colors: right-click the folder > Folder color
- [ ] Fill empty Lead values (library > Edit in grid view)
- [ ] Create the "Workstreams" view if the agent could not
- [ ] Live pages and list views: ask the agent to rerun the allowlist step whenever list links change
- [ ] Delete `<Page-Name>-probe-script.html` if the script probe ran

## Output

End with a short report: what was created or changed (folders, columns, view, page names and links, home page set or not, and the old home page to restore), the quality gate result (screenshots, issues fixed), the headline options or choice, the manual-steps checklist, and open questions. Keep it under about 25 lines plus the checklist.

## Guardrails

- Confirm the folder plan before creating folders, and get approval of the uploaded page before publishing it or replacing a live page.
- Never send email or Teams messages, change permissions or sharing, or delete anything. Changing the home page keeps the old home page in Site Pages.
- Make a page the home page only after it is published, and only the first page unless the user asks.
- Never work around a tenant policy or security setting; name it and hand the decision to the admin.
- Never invent leads, dates, numbers or links; mark unknowns.
- Never imitate a product or company logo in page decoration or the site icon; never use a logo as a hero image.
- Never embed secrets, access tokens, internal profile photos or data the page audience should not see; keep tenant URLs, list IDs and names out of anything meant for reuse.
- List views read only lists on the page's own site, never write to a list, and never show or snapshot columns the user marked sensitive.
- Batch changes; one upload per approval round under the stable `<Page-Name>.html`. Never name a page file `-preview`.
- Click-test every link and run the quality gate before calling a page done.

## Files in this skill

- [references/sections.md](references/sections.md): design language, section library, tokens, writing and accessibility rules
- [references/live-list-pattern.md](references/live-list-pattern.md): live list mechanism, column mapping, verification, fallbacks
- [references/graph-api.md](references/graph-api.md): Graph calls, pinned standard-page payload, brand kit mapping
- [references/lessons-learned.md](references/lessons-learned.md): the lessons behind these rules
- [references/worked-example.md](references/worked-example.md): anonymized end-to-end example
- `assets/sections.css`, `assets/static-page-template.html`, `assets/live-list-template.html`, `assets/list-view-block.html` (list view section: CSS, manifest entry, section, allowlist, runtime)
- [scripts/extract_brand.py](scripts/extract_brand.py), [scripts/prepare_hero_image.py](scripts/prepare_hero_image.py), [scripts/build_folder_links.py](scripts/build_folder_links.py), [scripts/allowlist_from_list.py](scripts/allowlist_from_list.py), [scripts/build_list_view.py](scripts/build_list_view.py), [scripts/visual_check.py](scripts/visual_check.py), [scripts/make_site_icon.py](scripts/make_site_icon.py)
