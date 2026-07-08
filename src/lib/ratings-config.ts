/**
 * Configuration for the GitHub-native skill rating feature.
 *
 * Ratings are 👍 reactions on a GitHub Discussion (one per skill). We use the
 * giscus widget for in-page voting and read the reaction counts at build time
 * via the GitHub GraphQL API (see `scripts/fetch-ratings.ts`).
 *
 * The `repoId` and `categoryId` values below are NOT secrets — giscus emits
 * them into the public client bundle. They are safe to commit. Fill them in
 * once the giscus GitHub App is installed on the repo (https://giscus.app):
 *
 *   1. Enable Discussions on the repository.
 *   2. Create a Discussion category (e.g. "Skill Ratings").
 *   3. Install the giscus app and paste the generated ids here (or set the
 *      matching PUBLIC_GISCUS_* env vars at build time).
 *
 * Until real ids are provided, `RATINGS_ENABLED` is false: the voting widget is
 * hidden and the gallery simply shows zero counts. Everything else still works.
 */

/** `owner/repo` that hosts the rating Discussions. */
export const GISCUS_REPO = import.meta.env.PUBLIC_GISCUS_REPO ?? "microsoft/cat-agent-skills";

/** giscus repository id (public client id, safe to commit). */
export const GISCUS_REPO_ID = import.meta.env.PUBLIC_GISCUS_REPO_ID ?? "R_kgDOSwZGlA";

/** Discussion category name that holds the rating discussions. */
export const GISCUS_CATEGORY = import.meta.env.PUBLIC_GISCUS_CATEGORY ?? "Announcements";

/** giscus category id (public client id, safe to commit). */
export const GISCUS_CATEGORY_ID = import.meta.env.PUBLIC_GISCUS_CATEGORY_ID ?? "DIC_kwDOSwZGlM4DAxet";

/**
 * The rating widget renders only when giscus has been fully configured. This
 * keeps local dev and un-provisioned deploys from showing a broken embed.
 */
export const RATINGS_ENABLED = Boolean(GISCUS_REPO_ID && GISCUS_CATEGORY_ID);
