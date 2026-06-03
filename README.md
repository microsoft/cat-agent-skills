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
  `?q=`/`?tag=`/`?platform=` URLs.
- **Skill detail pages** rendering the instructions, metadata, and downloads.
- **Downloads**: the skill as a `.md` file, plus an optional `.zip` script
  bundle when a skill ships executable helpers.

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

Skills live in `src/content/skills/` as Markdown files. To add one, open a PR
that adds `src/content/skills/<your-skill>.md`. See
[`docs/authoring-skills.md`](docs/authoring-skills.md) for the full frontmatter
spec and how to bundle scripts in a `.zip`.

Minimal example:

```markdown
---
name: My Great Skill
description: One-line summary shown on the card and detail page.
platforms: [Cowork, Copilot Studio, Scout]
tags: [productivity, automation]
author: Your Name
version: 1.0.0
---

You are the **My Great Skill** skill. Write the agent instructions here as
Markdown — this body becomes the "Instructions" section on the detail page.
```

> `platforms` is required and must be one or more of `Cowork`, `Copilot Studio`,
> `Scout`. PRs run a build check that validates every skill against the schema.

## 📁 Project structure

```
src/
  components/      SkillCard, SkillCover (the branded "screenshot")
  content/skills/  one Markdown file per skill (the content)
  layouts/         base page layout
  lib/             cover theming + small helpers
  pages/
    index.astro          home gallery (search + filter + infinite scroll)
    skills/[slug].astro  skill detail page
    skills/[slug].md.ts  raw Markdown download endpoint
    tags/[tag].astro     per-tag listing
    skills.json.ts       metadata endpoint
public/
  bundles/         downloadable .zip script bundles
.github/workflows/ ci.yml (PR build check) + deploy.yml (Pages deploy)
```

## 🚢 Deployment

Pull requests run `.github/workflows/ci.yml`, which builds the site (and thereby
validates every skill against the content schema). Pushing to `main` triggers
`.github/workflows/deploy.yml`, which builds and publishes the site to GitHub
Pages at `https://microsoft.github.io/cat-agent-skills/`. Enable Pages in the
repo settings with the **GitHub Actions** source.

## License

[MIT](LICENSE)
