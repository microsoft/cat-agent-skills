# Worked example: Contoso Activation Program

Anonymized. Every name, URL and person below is fictional (Contoso is a Microsoft sample company name).

## Intake answers

| Question | Answer |
|---|---|
| Page mode | Static showcase HTML page |
| Site URL | `https://contoso.sharepoint.com/sites/ContosoActivation` |
| Source document | `Activation Program Plan.pptx` (12 slides, one per workstream plus overview) |
| Brand input | `Contoso Brand 2026.potx` |
| Sibling sites to stay distinct from | `https://contoso.sharepoint.com/sites/ContosoAdoptionHub` (blue hero, round shapes) |
| Page name | `Contoso-Activation-Program` |
| Home page | First page the kit builds on this site, so it becomes the home page. The user agreed. Current home page recorded: `Home.aspx` (kept, not deleted). |

## Part 1: Library setup

Plan shown to the user before any write:

| Folder | Lead (from plan) | Description |
|---|---|---|
| 0 Program | (none) | Plan, charter and shared decks |
| Activate | Avery Chen | Five plays that take customers from switched on to paying back |
| Adopt | Jordan Patel | Champion network and adoption campaigns for each customer |
| Expand | Lead to be confirmed | Finds the next team or region ready for rollout |
| Enable | Sam Rivera | Partner and field readiness: training, labs, certification |
| Measure | Riley Morgan | Usage and value scorecards per customer |
| Govern | Casey Brooks | Controls, cost guardrails and policy templates |
| Decide - Insights Dashboard | Taylor Nguyen | Signals that recommend the next-best play per customer |
| Deliver - Delivery at Scale | Morgan Lee | Repeatable delivery kits and scheduling |
| Learn - Feedback Loop | Jamie Ortiz | Turns delivery feedback into play updates |

Notes from this step:
- The selected default drive's root `webUrl` ended in `/Shared%20Documents`, so its recorded URL name was `Shared Documents`. Both folder-link generation and upkeep passed `--library "Shared Documents"` explicitly; a localized library would use its own resolved URL name instead.
- The plan named one stream "Plan/Build"; it was sanitized to "Plan - Build" and then merged into Activate at the user's request. The rename was reported.
- "Expand" had no named lead in the plan, so the Lead column stays empty and the page shows "Lead to be confirmed".
- Lead column: person, single value. Description: the library's built-in Description column.
- View "Workstreams": Name, Lead, Description, Modified; sorted by Name, so "0 Program" is first.
- `Activation Program Plan.pptx` copied into `0 Program`.

## Part 2: Page

**Brand.** `extract_brand.py "Contoso Brand 2026.potx"` found accent1 `#00A3AD`, accent2 `#F2C14E`, dk2 `#003B49`, fonts Georgia / Verdana, one master gradient, and a 400 x 160 logo. Two token adjustments for AA (`--muted`, `--accent-ink` darkened). The sibling site uses a light `wash` hero with soft orbs, so this page uses the teal `deep` hero with the `arcs` motif.

**Headline options** (from the plan's overview slide, offered to the user):
1. "Activation that pays back, for every Contoso customer." (chosen)
2. "From switched on to paying back in 90 days."
3. "Six plays. One path to value."

**Outcome-led h2s:**
- Purpose: "Turn every license into measurable value."
- Documents: "Start with the plan."
- Workstreams: "Six workstreams. One activation plan."
- Shared streams (dark band): "Serving all six workstreams."
- Rhythm: "Weekly sync, monthly review, quarterly reset."
- Principles: "How we work."

**Executive summary:** "The Contoso Activation Program helps customer teams get value from the licenses they already own. Six workstreams each own one part of the journey, and three shared streams supply data, delivery kits and feedback. This site holds the plan, each workstream's folder and the meeting rhythm. New here? Open the program plan first."

**Folder link** for Activate (from `build_folder_links.py links --site https://contoso.sharepoint.com/sites/ContosoActivation --library "Shared Documents" --names Activate`):
`https://contoso.sharepoint.com/sites/ContosoActivation/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FContosoActivation%2FShared%20Documents%2FActivate`

**Workstream card markup:**
```html
<a class="ws" href="https://contoso.sharepoint.com/sites/ContosoActivation/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FContosoActivation%2FShared%20Documents%2FActivate" target="_top" rel="noopener noreferrer" data-folder="Activate"><span class="num">01</span><h3>Activate</h3><p>Five plays that take customers from switched on to paying back.</p><div class="wsf"><span class="ld"><em>Lead</em>Avery Chen</span><span class="open">Open folder ...</span></div></a>
```

**Publish probe:** `Contoso-Activation-Program-probe.html` uploaded, rendered, published. Overwrite of the same name failed, so the plan became: one upload per approval round, `Contoso-Activation-Program.html` first, then `Contoso-Activation-Program-2.html`, leftovers listed.

**Quality gate:** `visual_check.py` at 1440 and 390 px, light and dark. Round 1: the stats row overflowed at 390 px and the muted text on the dark band failed contrast. Both fixed; round 2 clean. All 13 links click-tested.

**Handover:** round 2 (`Contoso-Activation-Program-2.html`) approved and published.

**Home page.** Only after `Contoso-Activation-Program-2.html` was published: in the browser, Site Pages (`/SitePages/Forms/ByAuthor.aspx`) > select `Contoso-Activation-Program-2.html` > ... (More) > Make homepage > confirm. Then `https://contoso.sharepoint.com/sites/ContosoActivation/` loaded the new page, styled, with working folder links. `Home.aspx` stays in Site Pages; to restore it, Make homepage on `Home.aspx`. (Had Make homepage been missing for the `.html` page, the plan was to keep `Home.aspx` as home and add a hero button linking to `Contoso-Activation-Program-2.html`.)

Manual steps sent to the user: delete `Contoso-Activation-Program-probe.html` and `Contoso-Activation-Program.html` (round 1); set the site logo from `site-icon-512.png`; set folder colors; fill the Lead for Expand.

## Part 2b: Adding a "Resources" list view, one week later

The user asked: "Can the page also pull in the Resources list from the site, with filters?"

**Resolve the list.** The site's visible lists (hidden lists and document libraries skipped) held "Resources" and "Resources archive". Both matched "Resources", so the agent asked; the user chose "Resources".

**Schema and sample.** 24 columns, 38 items. The user said the "Internal notes" column must never show, so it went to `--sensitive`. The tool expanded Owners into approved display names under `Owners`, rather than returning only `OwnersLookupId`. Before the allowlist/snapshot command, the agent confirmed that these 38 items were the complete export with no continuation token left; a larger list would need every remaining page fetched and combined first. Separately, the list owner explicitly approved all 38 rows for the page's identified audience; column approval and the agent's read access were not treated as publication permission.

**Proposal** (`build_list_view.py --columns columns.json --items items.json --label Resources --sensitive InternalNotes`), shown to the user:

| Role | Column |
|---|---|
| Title | Title |
| Description | ResourceDescription (multi-line text) |
| Link | ResourceLink (hyperlink) |
| People | Owners (person, multi) |
| Date | PublishedOn ("Published") |

| # | Filter | Kind | Where |
|---|---|---|---|
| 1 | Type | single select (choice, 4 values) | bar |
| 2 | Audience | multi-select (multi-choice, 4 values) | bar |
| 3 | Phase | single select (choice, 3 values) | bar |
| 4 | Featured | toggle "Only featured" (yes/no) | More filters |
| 5 | Owners | multi-select (person) | More filters |

Not used: Internal notes (sensitive); Content Type, Attachments, Version, Image Tags, Retention label, Created By, Modified By (system); two hidden columns; Region (one value in the sample). Sort: newest, oldest, title A to Z. Table columns: Title, Type, Audience, Owners, Published.

The user kept the proposal and the cards layout.

**Build.**
```bash
python scripts/build_list_view.py --columns columns.json --items items.json --label Resources \
  --sensitive InternalNotes --web-url https://contoso.sharepoint.com/sites/ContosoActivation \
  --list-id <Resources list id> --key resources --noun resource,resources \
  --eyebrow Resources --h2 "Everything you need to get started." \
  --intro "Guides, templates and recordings, kept current by the program team." --into Contoso-Activation-Program-3.html
python scripts/allowlist_from_list.py --items items.json --publication-approved --view resources --page Contoso-Activation-Program-3.html --snapshot
```
The section went in after the workstreams. The page was static, so the agent told the user it now needs scripts and ran the script probe: `Contoso-Activation-Program-probe-script.html` showed "Scripts run" and the Resources rows were injected.

**Quality gate.** `visual_check.py Contoso-Activation-Program-3.html --sample-data resources=rows.json` at 1440 and 390 px, light and dark: the list view reached `data-state="ready"`; at 390 px the table toggle hides and cards show. One fix: a long choice value wrapped badly in the table, shortened in the list by the user.

**On the site.** Live rows rendered (no "saved copy" note). Checked: Type = Guide, Audience = Partners, "Only featured" from More filters, search "checklist" with highlight, Table and a sort on Published, and the shared link `?resources-type=Guide&resources-layout=table` reopened the same view. 31 links in the allowlist matched the list's 31 linked items.

**Fallback plan given to the user.** If live data stops loading, the page shows the saved copy from the build date; if scripts get blocked, `--static-snapshot` turns the section into a dated static list.

## Part 3: Upkeep, three weeks later

The user renamed `Activate` to `Activate and Onboard` and added a folder `Champions`.

`build_folder_links.py check` reported: Activate link broken, possible rename to "Activate and Onboard" or "Champions"; "Champions" unlinked. The user confirmed the rename; the rerun with `--rename "Activate=Activate and Onboard" --fix-out` changed one link and flagged that the card title still read "Activate". The user gave a lead and a description for Champions, the card was added, and the page went through the quality gate before a single upload.

Overwrite fails on this site, so the new version went up as `Contoso-Activation-Program-3.html`. After the user published it, the agent ran Make homepage on `Contoso-Activation-Program-3.html`, loaded the site root to confirm, and only then listed `Contoso-Activation-Program-2.html` as a leftover to delete.
