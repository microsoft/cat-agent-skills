# Live list-backed HTML page

> **Status: inferred, not documented.** This mechanism was read from a working HTML page in the Site Pages library of a SharePoint site. No public documentation for it was found. Verify it on the target site every time (step "Verify on the target site" below) and fall back to a snapshot or static page when it does not work.

Two ways to use it:
- **Live page (mode b):** the whole page is a gallery of one list. Template: `assets/live-list-template.html`.
- **List view section (any page):** one or more list views dropped into a static, live or existing page on request ("add a list view of Resources"). Block: `assets/list-view-block.html`; builder: `scripts/build_list_view.py`. See "List view sections" below.

Allowlist and snapshot tool for both: `scripts/allowlist_from_list.py`.

## Row and audience publication approval

Before embedding any list rows, titles, values or URLs, identify the page audience and obtain explicit approval to republish either the complete current export or specific row IDs. Item-level permissions do not travel with copied HTML; delegated caller access, approval of columns and approval of the page layout are not row approval. This gate applies equally to galleries, list sections, hidden allowlists and static fallbacks.

Retrieve every continuation page, then export only the approved rows and columns. Use `--publication-approved` only to attest that every supplied row is approved for the identified audience. If a list has no row approval, supply `[]` for that view with `--snapshot` to clear its old saved data and shared allowlist contribution, or omit its static section. A refresh without `--snapshot` clears old snapshots so earlier approval cannot linger. Verify live injection uses the reader's authorized context; never preload an unapproved privileged payload.

## How it works

1. **Theme bootstrap.** A small script in `<head>` sets `data-theme="light|dark"` on `<html>` from a `?theme=` URL parameter, else from `prefers-color-scheme`. A toggle button flips it.
2. **Manifest.** The page declares the list it reads:
   ```html
   <script type="application/json" class="ka-livedata-manifest">
   [{"kind":"list","spItemUrl":"list:<webUrl>/<listId>","webUrl":"<webUrl>","listId":"<listId>","label":"<list display name>"}]
   </script>
   ```
   Keep the class name `ka-livedata-manifest` exactly; it appears to be what the viewer looks for.
3. **Page config.** `<script type="application/json" id="site-page-config">` holds `schemaVersion`, `mode` (`preview` or `production`), `siteUrl`, `page` (`slug`, `file`, `title`, `expectedUniqueId`; `slug` is the page name and `file` is `<Page-Name>.html`) and `publicationSource`, an exact copy of the manifest entry.
4. **Injection.** When the SharePoint HTML viewer opens the page, it injects `window.__LD_RESULTS__`, an object keyed by `spItemUrl`. Each value has `format: "rows"` and `content`, a JSON string `{"headers":[...],"rows":[[...],...]}`. Headers are column internal names in the observed page; the template also accepts display names.
5. **Binding check.** The script finds the manifest entry whose `spItemUrl` equals `publicationSource.spItemUrl` and compares `kind`, `spItemUrl`, `webUrl`, `listId` and `label`. Any difference: the page refuses to render and shows the error state ("binding is invalid" in the console).
6. **Decode.** Columns are found by candidate names (`COLUMN_MAP`). `ID` and `Title` are required. The decoder skips rows without a valid positive integer ID, de-duplicates IDs, turns HTML rich text into plain text, reads person fields as JSON arrays of `{LookupValue}` / `{Title}` or as `;`-separated text, reads hyperlink fields as `<a href>`, `{"Url":...}` or `"url, description"`, and accepts only `https:` links without credentials.
7. **Render.** Cards with search (with match highlight), select filters per mapped column, an optional internal/external scope toggle, sort, item count, empty state ("Nothing matches...") and error state. State is mirrored to the query string (`?q=`, `?category=`, `?scope=internal`) so filtered views can be shared. `#item-<ID>` and `postMessage({anchor:"item-<ID>"})` scroll to one card.
8. **Link allowlist.** The viewer only lets a link open when the same address appears statically in the page. A hidden `<nav id="link-allowlist" hidden>` between `<!-- link-allowlist:start -->` and `<!-- link-allowlist:end -->` holds a static copy of every link in the list. Links that are not in it go through the link helper: `window.open` in a new tab, else a popover with "Copy link" and the right-click instruction.

**The allowlist goes stale.** Regenerate it every time list items are added or their links change:
```bash
python scripts/allowlist_from_list.py --items approved-items.json --publication-approved --columns ID Title AssetLink AssetDescription Owners PublishedOn Category Topic InternalOnly --page <Page-Name>.html
```
The column names above are an example, not a default approval. Confirm the actual audience-approved set from `COLUMN_MAP`; `--columns` is required for gallery inputs and limits both links and snapshot fields. Fetch all continuation pages before generating either output, not just the proposal sample. Inputs with an outstanding `@odata.nextLink` are rejected.

## Column mapping guide

Edit only the `COLUMN_MAP` object in the template:

```js
const COLUMN_MAP = {
  id: ["ID"],
  title: ["Title", "LinkTitle"],
  description: ["AssetDescription", "Description"],  // rich text is flattened
  url: ["AssetLink", "Link", "URL"],                  // hyperlink or text
  people: ["Owners", "Owner"],                        // person or text
  date: ["PublishedOn", "Modified", "Created"],
  internal: ["InternalOnly"],                         // optional yes/no; drives the scope toggle
  filters: [
    { key: "category", label: "Category", columns: ["Category"], multi: false },
    { key: "topic", label: "Topic", columns: ["Topic"], multi: true },  // multi-choice
  ],
};
```

How to fill it:
1. Read the list's columns (column listing tool or `GET /sites/{site-id}/lists/{list-id}/columns`). Note each column's internal `name` and `displayName`.
2. Put the internal name first, the display name second. Internal names encode spaces as `_x0020_` (for example `Skill_x0020_Level`).
3. Use `multi: true` for multi-choice, multi-lookup and managed metadata columns.
4. If there is no yes/no column for scope, list public hosts in `EXTERNAL_HOSTS`; links on those hosts count as external. Leave both empty to hide the toggle.
5. Keep `filters` to three or fewer in the live gallery. For more filters, or a generated mapping, use a list view section instead: it builds the "More filters" panel itself.
6. Require person/lookup display values under the mapped names. Raw Graph `<Name>LookupId` fields are not display values: resolve them through authorized tools or request an expanded payload before proposal, snapshot or browser use. Exclude the column explicitly if resolution is unavailable; never substitute an ID for a name. Verify the live viewer supplies expanded values too.

## List view sections

A list view is a self-contained section that renders one list from the SAME site as the page. Any page can hold several.

### Resolve the list
1. Look up the lists on the page's site (list lookup tool, or `GET /sites/{site-id}/lists`, see graph-api.md). Skip hidden lists and document libraries unless the user asked for a library.
2. Match the name the user gave against `displayName` (case-insensitive, then "contains"). One match: use it. Several: show them (name, item count if known, URL) and ask which. None: list the visible lists and ask.
3. A list on another site is out of scope for this mechanism: say so and offer a link card or a static snapshot instead.

### Generate the view from the schema
```bash
python scripts/build_list_view.py --columns columns.json --items items.json --label "<list display name>" [--sensitive <col> ...]
```
`columns.json` is the column listing (`name`, `displayName`, `hidden`, `readOnly`, type facets); `items.json` is optional sample items (Graph items with fields, the rows shape, or plain dicts). The script prints the proposal as two short tables:

- Roles: Title; description = first multi-line text column; link = first hyperlink column; people = first person column; date = a dateTime column whose name suggests published, due, release or event, else Modified.
- Filters, ranked: choice and managed metadata (multi-select when the column allows several values), yes/no (an "Only ..." toggle), person (multi-select), lookup. With sample items, columns with one distinct value or more than 25 are skipped. The first 3 show in the bar; the rest go to "More filters".
- Sort: newest first, oldest first (when there is a date), title A to Z. Table columns: title, the first two filters, people, date.
- Never used: hidden columns, system columns (ContentType, Attachments, _UIVersionString, compliance, media and Teams metadata such as image tags, Created By, Modified By) and every column passed to `--sensitive` or `--exclude`.

Confirm the proposal with the user (or take their changes: `--filters A B C` sets filters in order, `--primary N` sets how many show in the bar, `--layout table` sets the default layout).

### Build and insert
```bash
python scripts/build_list_view.py --columns columns.json --items items.json --label "Resources" \
  --web-url <site URL> --list-id <list GUID> --key resources --layout cards --noun resource,resources \
  --eyebrow Resources --h2 "<outcome-led h2>" --intro "<one sentence>" --into <Page-Name>.html
python scripts/allowlist_from_list.py --items approved-resources.json [approved-events.json] --publication-approved --view resources [events] \
  --page <Page-Name>.html --snapshot
```
`--into` adds, once per page, the list view CSS to the single style element, the hidden link allowlist and the runtime script; adds or merges the manifest entry; and inserts the section at `<!-- list-view:insert -->` (static template), else at the end of `<main>`. Running it again with the same key replaces that section and keeps its snapshot only if the source, mapped columns, filters and sensitive-column configuration are unchanged; otherwise the snapshot is cleared. Regenerate saved data before upload.

Fetch complete exports before selecting row-approved inputs for the refresh command, following every continuation page and resolving person/lookup IDs to approved display values. Pass every live list view on the page in one run: it rewrites the shared allowlist from approved rows, takes links only from the columns each view maps, and writes each snapshot with the mapped columns only. If the page also has a live gallery, include it with the reserved `@gallery` key and its audience-approved rows and columns:

```bash
python scripts/allowlist_from_list.py --items approved-gallery.json approved-resources.json --publication-approved \
  --view @gallery resources --columns ID Title AssetLink AssetDescription Owners PublishedOn Category Topic \
  --page <Page-Name>.html --snapshot
```

In a combined refresh, `--columns` applies only to the gallery; each section uses its own mapped columns. Missing gallery or section inputs are rejected rather than silently dropping their links; supply `[]` for a list without row approval. Record retrieved/approved/omitted counts and require the snapshot row count to match the approved count, including approved items beyond the first page.

### How a list view binds
- The page's single `ka-livedata-manifest` array gets one entry per list. Each section's `lv-config.source` must match its entry exactly (`kind`, `spItemUrl`, `webUrl`, `listId`, `label`), or that section shows the error state. Other sections are unaffected.
- Rebuilding with changed shared metadata (for example a renamed list's label) is rejected before writing if a gallery or another section still has the old source config. Update all affected `publicationSource`/`source` configs together, then rebuild and verify every binding; do not update only the shared manifest.
- The runtime reads `window.__LD_RESULTS__[spItemUrl]`, else the section's `lv-snapshot`, else shows the error state.
- **Unverified:** the observed working page had one manifest entry and one list. That the viewer injects data for several entries in one manifest, and for a manifest on a page without `site-page-config`, is inferred from the array shape. Verify both on the target site; if only one list loads, keep one list view per page or fall back to a snapshot for the others.
- Adding a list view makes a static page script-dependent. The script probe (SKILL.md 2.1) must pass first.

## Verify on the target site

1. Fill the template, run the quality gate locally with sample data:
   `python scripts/visual_check.py <Page-Name>.html --mode live --sample-data rows.json`
   For list views pass one file per section: `--sample-data resources=resources-rows.json events=events-rows.json`.
2. Upload once as `<Page-Name>.html` (unpublished) to Site Pages and open it in the browser.
3. Check the gallery section, and every list view section: `data-state="ready"` with items and no "saved copy" note means live data works. A "saved copy" note means `__LD_RESULTS__` was not injected and the snapshot rendered. An error message means no live data and no snapshot, or a binding mismatch.
4. Click three item links: one in the allowlist (opens), one external, one SharePoint link.
5. List views: apply one filter from the bar and one from "More filters", search a word, switch to Table and sort a column, then copy the URL into a new tab and confirm the same view opens. Confirm the allowlist was regenerated after the last list change and contains exactly the unique links from the approved rows.

## Fallbacks, in order

1. **Snapshot inside the live page.** `allowlist_from_list.py --items approved-items.json --publication-approved --columns <audience-approved columns...> --page <Page-Name>.html --snapshot` writes the approved rows into `<script id="snapshot-data">`; the page renders them with a "saved copy from <date>" note when live data is missing. Needs scripts to be allowed. Do not snapshot columns or rows the page audience is not approved to see.
2. **Static snapshot page or section.** If scripts are blocked too, use only row-approved items selected after fetching all continuation pages, never the proposal sample. Build static cards or a table with a dated note ("Saved copy of the <list> list from <date>. It does not update by itself.") and tell the user the page will not update by itself. For a list view use `build_list_view.py ... --items approved-items.json --publication-approved --static-snapshot` to remove its runtime and JSON blocks when no other live consumer remains. Without row approval, omit the section or supply `[]`.
3. **Standard page.** If HTML pages cannot be published at all, use the standard modern page mode with a List web part added by the user (manual step) or a text web part with links.

When converting a section on a page that still has a live gallery or other live sections, supply their current approved inputs in the same builder command:

```bash
python scripts/build_list_view.py --columns columns.json --items empty.json --label Resources \
  --web-url <site URL> --list-id <Resources list GUID> --key resources --static-snapshot \
  --publication-approved --into <Page-Name>.html \
  --remaining-items approved-gallery.json approved-events.json --remaining-view @gallery events \
  --gallery-columns ID Title Link
```

Here `empty.json` contains `[]` because publication approval for Resources was withdrawn; the flag attests only to the nonempty remaining inputs. The builder converts Resources and rebuilds the remaining consumers' snapshots and shared allowlist in memory, then writes only after the full refresh succeeds. Missing inputs or approval abort without modifying the page or output files. This removes old hidden URLs while preserving currently approved links, including shared links still approved for another consumer. Omit the converted `resources` key from `--remaining-view` and every later standalone refresh. Without a remaining gallery, omit `@gallery` and `--gallery-columns`; without any live consumers, omit all three remaining-refresh options.
