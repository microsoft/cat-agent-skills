# CAT Agent Skills

A community gallery of **skills for AI agents** — reusable instruction sets (and
optional script bundles) you can drop into **Cowork**, **Copilot Studio**, and
**Scout** agents. The site is inspired by [pcf.gallery](https://pcf.gallery/):
an infinitely scrolling, searchable, filterable grid of skills, each with its
own detail page and downloads.

Built with [Astro](https://astro.build/) + [Tailwind CSS](https://tailwindcss.com/),
deployed as a static site to GitHub Pages.

## ✨ Features

- **A Built by Microsoft preview row above the community gallery**, with a
  **View more** link beside the heading, wrapping underneath on narrow screens.
  It includes the matching count and no arrow, and opens the Microsoft-only
  collection. Both galleries use the same product,
  category, search and extra filters; collection/back links preserve selections
  and sorting. Collection and detail pages use matching **Back to gallery**
  arrow links. The preview uses the community grid's responsive card widths
  and the same page background. It is ordered by category, then title (A-Z),
  independently of the community sort selection.
  The catalog includes 20 industry plugins (10 Manufacturing and 10 Retail & CPG)
  from [industry-templates at pinned commit e4a0ab3](https://github.com/SravaniSeethi/industry-templates/tree/e4a0ab3d1eaa2b40e4c1d5c4b346a9566f25c682),
  with original source and license notices retained.
- **Infinite-scroll galleries** with compact, consistently sized cards,
  category icons and quiet category labels for Microsoft submissions, and auto-generated monograms for
  community submissions (no image assets to maintain).
  Featured stars appear only on community cards.
- **Multi-select products** in one horizontal row: Copilot Studio, Cowork,
  and Scout pills. Products match **any selected value** (OR), then intersect
  with categories and other filters (AND). Clicking an active product removes
  it; no products selected means all products, with no separate Any control.
  Each product and category has a keyboard tab stop; Space or Enter toggles it.
  Selected filters use the same theme-aware accent as the contribution and
  filter-apply actions, with a tinted fill, colored text, and a visible outline.
- **Multi-select categories** alongside products: Manufacturing, Retail & CPG,
  Productivity and Agent development. Categories match **any selected value**
  (OR), then intersect with the product and other filters (AND). Selecting an
  active category removes it; no categories selected means all categories.
- **Client-side search** and a **Filters dialog** for Format, Tags, and
  Contributor. Format offers multi-select Skills, Plugins, and Automations:
  any selected format matches (OR), and must also match a chosen product
  (AND). Cowork + Skills shows only Cowork skills. No selected formats is
  unrestricted; there is no All formats control.
  Tags and Contributor require **every selected value** (AND), so adding a
  choice cannot widen results; option counts reflect adding that choice to the
  current intersection. Empty selections are unrestricted, with no All
  contributors control. Current submissions have one contributor each, so
  selecting two distinct contributors intentionally returns no results; this
  does not add multi-contributor metadata support. Selections remain removable
  even at zero results.
  Platform pills apply immediately; dialog changes apply only
  with **Show results**. Closing the dialog discards its draft. Applied
  formats, tags, and contributors appear as removable pills before platforms in
  the same scrolling row, with each choice counted in the Filters badge.
  Clear extra filters clears draft formats/tags/contributors, keeping the
  product selection, categories, search, and sort. Applying the same selections after
  toggling them off/on or clearing/reselecting preserves their existing order,
  URL, revealed cards, and scroll.
- **Shareable filters** using `?q=`, `?platform=`, `?category=`, `?type=`, `?tag=`, and `?author=`.
  `category` accepts one slug or a comma-separated union. `platform` remains
  the product query key and accepts one name or a comma-separated union; it is
  omitted when no products are selected. `type` still accepts single values
  or comma-separated selections, including all three formats.
  Platform values are trimmed, deduplicated, and restricted to valid names,
  retaining every valid selection, including an explicit selection of all
  three products. No valid values means unrestricted products.
  The URL is normalized to those visible product choices without changing other
  parameters. Format values remain lowercase (`skill`, `plugin`, `automation`). Search,
  tags, and contributors AND-narrow the platform/format results. Every selected
  tag and contributor is required. The `author` key preserves all supplied
  comma-separated values, trimmed, lowercased, and deduplicated; it is never
  truncated to one contributor. Unknown contributors remain explicit no-match
  restrictions with individual removable chips. Existing
  single-platform and single-format links still work. Tag case is preserved;
  search is case-insensitive.
- **Sort** by Featured, Top rated, Most downloaded, Name, Newest, or Recently
  updated. Samples stay last; browser Back/Forward restores filters, revealed
  cards, and scroll position per history entry, including separate visits to
  the same filter URL. Reload and returning from a detail page preserve the
  current entry's position too. Debounced search replaces the current entry
  without changing its identity or unrelated history state, and saves the
  updated results' position rather than the pre-search position.
- **Skill detail pages** rendering the instructions, metadata, and downloads.
- **Skill ratings**: 👍 a skill with your GitHub account (via GitHub
  Discussions); the gallery bakes in the counts and offers a "Top rated" sort.
  See [`docs/ratings.md`](docs/ratings.md).
- **Downloads**: the skill as a `SKILL.md` file, plus an optional `.zip` bundle
  when a skill ships files beyond its `SKILL.md`.
- **More than skills**: also hosts **Cowork plugins** (M365 `.zip` packages) and
  **Scout automations** (scheduled `.json` exports) and **Scout automation
  installers** (a `.zip` with an `INSTALL.md` + JSON config that sets the
  automation up), each with its own format label, filter, and verbatim download.

## 🚀 Local development

Use Node.js 22.19 or newer to satisfy the locked website dependencies.

```bash
npm ci
npm run import:submissions # generate the local catalog and bundles; do not commit them
npm run dev      # start the dev server (http://localhost:4321/cat-agent-skills)
npm run build    # production build into ./dist
npm run preview  # preview the production build locally
```

> The site is configured with a `base` path of `/cat-agent-skills`
> for GitHub Pages, so local URLs include that prefix.

Run the focused gallery checks with
`node --import tsx --test scripts/gallery-filters.test.ts scripts/gallery-sort.test.ts`.
These checks and the site build do not execute submission runtimes.

## 🧩 Adding a skill

Add **one submission to the [`submissions/`](submissions/) folder** and open a
PR — you never edit `src/content/skills/` by hand. CI validates the metadata and
generates the published page (and any download bundle) for you. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

Every submission is a `submissions/<slug>/` folder with a `metadata.json` sidecar
plus one skill payload — an **unpacked** `SKILL.md` (+ optional dirs):

```
submissions/<slug>/
├── metadata.json  # OR metadata.yaml — catalog details (sidecar, not bundled)
├── README.md      # OPTIONAL human-facing note (not bundled) — shown on the page
└── an unpacked skill:
    ├── SKILL.md    # name + agent description + instructions
    ├── scripts/    # optional executable code
    ├── references/ # optional docs
    └── assets/     # optional templates / data files
```

A skill carries **two** descriptions: the **agent** description in `SKILL.md`
frontmatter (what the model reads to decide when to invoke), and the **catalog**
description in `metadata.json` (the friendly one-liner shown in the gallery). An optional **`README.md`** adds a third, human-only voice: it never ships to the
agent and, when present, **becomes the main content** on the detail page — the
author's overview, setup, and usage — with the exact `SKILL.md` still offered as
the download.

`submissions/my-great-skill/SKILL.md`:

```markdown
---
name: my-great-skill
description: Use this skill whenever the user… (the agent-facing trigger).
---

Write the agent instructions here as Markdown — this body becomes the
"Instructions" section on the detail page.
```

`submissions/my-great-skill/metadata.json`:

```json
{
  "name": "My Great Skill",
  "description": "One-line catalog summary shown on the card and detail page.",
  "platforms": ["Cowork", "Copilot Studio", "Scout"],
  "tags": ["productivity", "automation"],
  "author": "Your Name",
  "authorUrl": "https://example.com",
  "version": "1.0.0"
}
```

> `name`, `description`, `platforms`, and `tags` are required (`platforms` must be
> one or more of `Cowork`, `Copilot Studio`, `Scout`). PRs run a build check that
> validates every skill against the schema.

> Besides single skills, you can submit a **Scout automation** (a `.json` export,
> Scout-only). It drops into `submissions/<slug>/` the same way and is
> auto-detected by its payload. You can also submit an **unpacked Cowork plugin**
> (a root `manifest.json` with its icons and skills/connectors).
> (Scout automation installers were `.zip` packages and are **no longer
> accepted** — `.zip` payloads have been retired; existing ones stay published.) See
> [`submissions/README.md`](submissions/README.md) for the details.

## Add Copilot Studio skills from GitHub

In Copilot Studio, choose **Add skill** > **From GitHub** and paste this public
folder URL:

`https://github.com/microsoft/cat-agent-skills/tree/copilot-studio-skills`

The dedicated branch is generated from submissions on `main` whose `platforms`
include `Copilot Studio`. Its root contains only unpacked canonical skills with
a root `SKILL.md` and their resources; gallery metadata and root human-facing
READMEs are excluded.

## 📁 Project structure

```
src/
  components/      GalleryBrowser, GalleryFilters, SubmissionItem, SkillCard, SkillCover
  content/skills/  generated skill pages (produced from submissions/ — do not edit by hand)
  layouts/         base page layout
  lib/             gallery controller, filtering, sorting, cover theming + small helpers
  data/            ratings.json (build-time 👍 snapshot; see docs/ratings.md)
  pages/
    index.astro          home gallery (search + filter + sort + infinite scroll)
    skills/[slug].astro  skill detail page (instructions, download, ratings)
    skills/[slug].md.ts  raw Markdown download endpoint
    tags/[tag].astro     legacy tag URLs redirect to the filtered home gallery
    skills.json.ts       metadata endpoint
public/
  bundles/         downloadable .zip skill bundles
submissions/       drop-in skill submissions (folders imported by CI)
scripts/           import-submissions + validate-skill + fetch-ratings
.github/workflows/ ci.yml (PR build check) + deploy.yml (Pages deploy + ratings)
```

## 🚢 Deployment

Pull requests run `.github/workflows/ci.yml`, which builds the site (and thereby
validates every skill against the content schema). Pushing to `main` triggers
`.github/workflows/deploy.yml`, which builds and publishes the site to GitHub
Pages at `https://microsoft.github.io/cat-agent-skills/`. Enable Pages in the
repo settings with the **GitHub Actions** source.

Before each build, `deploy.yml` runs `npm run ratings:fetch` to snapshot 👍
counts from GitHub Discussions, and a daily `schedule` cron refreshes them
without a code push. See [`docs/ratings.md`](docs/ratings.md) for the one-time
giscus/Discussions setup.

## 🆘 Support

CAT Agent Skills is an **example implementation**. The underlying Microsoft
features (Power Apps, Power Automate, Dataverse, Copilot Studio, etc.) are fully
supported, but the skills themselves are provided as-is. See
[`SUPPORT.md`](SUPPORT.md) for how to file issues and get help.

## License

[MIT](LICENSE)
