# Skill ratings

Skills can be rated with a 👍 by anyone with a GitHub account. The gallery is a
**static site on GitHub Pages** (no server, no database), so ratings are stored
where they naturally belong — on GitHub — and read at build time.

## How it works

```
GitHub Discussions (Announcements category)
    │   one discussion per skill; discussion title == skill slug
    │   the 👍 (THUMBS_UP) reaction count is the rating
    ▼
scripts/fetch-ratings.ts   (GraphQL, runs in CI with GITHUB_TOKEN)
    ▼
src/data/ratings.json      { "<slug>": <count> }   ← build-time snapshot
    ▼
Gallery cards + detail pages + "Top rated" sort on the homepage
```

- **Voting** happens live, in-page, via the [giscus](https://giscus.app) widget
  on each skill's detail page ("Rate & discuss this skill"). giscus maps the page
  to a GitHub Discussion using `mapping="specific"` with the skill **slug** as the
  term, so discussion titles are deterministic.
- **Sorting** uses the baked snapshot. The homepage "Top rated" option sorts by
  👍 count (ties broken by name). The count you see updates on the next deploy or
  the daily scheduled rebuild — it is not a live counter.
- **Graceful by default:** with no `GITHUB_TOKEN`, no Discussions, or on a fork,
  `ratings.json` stays `{}` and every skill simply shows `0`. Nothing breaks.

## Setup (already wired for this repo)

This repository is already configured: Discussions is enabled, giscus points at
the **Announcements** category, and the repo/category IDs are committed in
[`src/lib/ratings-config.ts`](../src/lib/ratings-config.ts) (they are public
giscus client IDs, safe to commit). The only remaining manual step is installing
the **giscus GitHub App** (below), after which voting is live.

We reuse the **Announcements** category because it is the giscus-recommended
type — only maintainers and the giscus app can open threads, so votes can
auto-create one discussion per skill without opening the door to spam. Skill
discussions are titled by slug; the welcome/announcement posts are ignored by
`fetch-ratings.ts` because their titles aren't slug-shaped.

**To install the app (one time):** open
<https://github.com/apps/giscus>, click **Install**, and select
`microsoft/cat-agent-skills`.

### Re-provisioning from scratch

If you ever need to point ratings at a different repo or category:

1. **Enable Discussions** (Settings → General → Features) and pick a category
   (an **Announcement**-type category is recommended).
2. **Install the giscus GitHub App**: <https://github.com/apps/giscus>.
3. Fetch the IDs with the API (no need to visit giscus.app):

   ```bash
   gh api graphql -f query='{ repository(owner:"microsoft", name:"cat-agent-skills"){ id discussionCategories(first:20){ nodes{ id name } } } }'
   ```

4. Put the repo id + category id (and matching category name) into
   [`src/lib/ratings-config.ts`](../src/lib/ratings-config.ts), or provide them
   at build time via `PUBLIC_GISCUS_REPO_ID` / `PUBLIC_GISCUS_CATEGORY_ID` /
   `PUBLIC_GISCUS_CATEGORY`. Keep the category name in sync with the
   `GISCUS_CATEGORY` default in `scripts/fetch-ratings.ts`.

## Refreshing counts

- The deploy workflow runs `npm run ratings:fetch` before every build.
- A daily `schedule` cron in `.github/workflows/deploy.yml` rebuilds the site so
  counts stay current without a code push.
- To refresh on demand, run the **Deploy to GitHub Pages** workflow via
  *workflow_dispatch*, or locally:

  ```bash
  GITHUB_TOKEN=$(gh auth token) npm run ratings:fetch
  ```
