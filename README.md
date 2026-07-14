# CAT Agent Skills

A community gallery of **skills for AI agents** — reusable instruction sets (and
optional script bundles) you can drop into **Cowork**, **Copilot Studio**, and
**Scout** agents. The site is inspired by [pcf.gallery](https://pcf.gallery/):
an infinitely scrolling, searchable, filterable grid of skills, each with its
own detail page and downloads.

Built with [Astro](https://astro.build/) + [Tailwind CSS](https://tailwindcss.com/),
deployed as a static site to GitHub Pages.

## ✨ Features

- **Infinite-scroll gallery** with auto-generated branded covers (no image
  assets to maintain).
- **Platform filtering** across Cowork, Copilot Studio, and Scout.
- **Client-side search** and **tag filtering** with shareable
  `?q=`/`?tag=`/`?platform=`/`?sort=` URLs.
- **Sort** by Featured, Top rated, Name, or Newest.
- **Skill detail pages** rendering the instructions, metadata, and downloads.
- **Skill ratings**: 👍 a skill with your GitHub account (via GitHub
  Discussions); the gallery bakes in the counts and offers a "Top rated" sort.
  See [`docs/ratings.md`](docs/ratings.md).
- **Downloads**: the skill as a `SKILL.md` file, plus an optional `.zip` bundle
  when a skill ships files beyond its `SKILL.md`.
- **More than skills**: also hosts **Cowork plugins** (M365 `.zip` packages) and
  **Scout automations** (scheduled `.json` exports), each with its own badge,
  filter, and verbatim download.

## 🚀 Local development

```bash
npm install
npm run dev      # start the dev server (http://localhost:4321/cat-agent-skills)
npm run build    # production build into ./dist
npm run preview  # preview the production build locally
```

> The site is configured with a `base` path of `/cat-agent-skills`
> for GitHub Pages, so local URLs include that prefix.

## 🧩 Adding a skill

Add **one submission to the [`submissions/`](submissions/) folder** and open a
PR — you never edit `src/content/skills/` by hand. CI validates the metadata and
generates the published page (and any download bundle) for you. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

Every submission is a `submissions/<slug>/` folder with a `metadata.json` sidecar
plus one skill payload — an unpacked `SKILL.md` (+ optional dirs) or a `.zip`:

```
submissions/<slug>/
├── metadata.json  # OR metadata.yaml — catalog details (sidecar, not bundled)
└── EITHER an unpacked skill…       OR a pre-packaged bundle:
    ├── SKILL.md   # name + agent description + instructions   └── <name>.zip
    ├── scripts/   # optional executable code
    ├── references/# optional docs
    └── assets/    # optional templates / data files
```

A skill carries **two** descriptions: the **agent** description in `SKILL.md`
frontmatter (what the model reads to decide when to invoke), and the **catalog**
description in `metadata.json` (the friendly one-liner shown in the gallery).

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

> Besides single skills, you can submit a **Cowork plugin** (a `.zip` M365 app
> package, Cowork-only) or a **Scout automation** (a `.json` export, Scout-only).
> Both drop into `submissions/<slug>/` the same way and are auto-detected by their
> payload. See [`submissions/README.md`](submissions/README.md) for the details.

## 📁 Project structure

```
src/
  components/      SkillCard, SkillCover (the branded "screenshot")
  content/skills/  generated skill pages (produced from submissions/ — do not edit by hand)
  layouts/         base page layout
  lib/             cover theming + small helpers
  data/            ratings.json (build-time 👍 snapshot; see docs/ratings.md)
  pages/
    index.astro          home gallery (search + filter + sort + infinite scroll)
    skills/[slug].astro  skill detail page (instructions, download, ratings)
    skills/[slug].md.ts  raw Markdown download endpoint
    tags/[tag].astro     per-tag listing
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
