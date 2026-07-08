# Skill ratings

Skills can be rated with a 👍 by anyone with a GitHub account. The gallery is a
**static site on GitHub Pages** (no server, no database), so ratings are stored
where they naturally belong — on GitHub — and read at build time.

## How it works

```
GitHub Discussions (category "Skill Ratings")
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

## One-time setup (maintainers)

The voting widget stays hidden until giscus is configured (`RATINGS_ENABLED` in
[`src/lib/ratings-config.ts`](../src/lib/ratings-config.ts) is `false` until then).

1. **Enable Discussions** on the repository (Settings → General → Features).
2. **Create a Discussion category** named `Skill Ratings` (any format works;
   "Announcements" keeps the list tidy since only maintainers open threads, but
   giscus can also auto-create discussions on first vote).
3. **Install the giscus GitHub App** on the repo: <https://github.com/apps/giscus>.
4. On <https://giscus.app>, enter the repo and pick the `Skill Ratings` category.
   Copy the generated **Repository ID** and **Category ID**.
5. Paste them into [`src/lib/ratings-config.ts`](../src/lib/ratings-config.ts)
   (`GISCUS_REPO_ID`, `GISCUS_CATEGORY_ID`) **or** provide them at build time as
   the env vars `PUBLIC_GISCUS_REPO_ID` and `PUBLIC_GISCUS_CATEGORY_ID`. These are
   public client IDs (giscus ships them in the browser bundle) — safe to commit.

That's it. On the next deploy the widget appears and `scripts/fetch-ratings.ts`
starts populating counts.

## Refreshing counts

- The deploy workflow runs `npm run ratings:fetch` before every build.
- A daily `schedule` cron in `.github/workflows/deploy.yml` rebuilds the site so
  counts stay current without a code push.
- To refresh on demand, run the **Deploy to GitHub Pages** workflow via
  *workflow_dispatch*, or locally:

  ```bash
  GITHUB_TOKEN=$(gh auth token) npm run ratings:fetch
  ```
