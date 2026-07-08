/**
 * Read-side helper for skill ratings.
 *
 * `src/data/ratings.json` is a build-time snapshot of 👍 counts keyed by skill
 * slug, produced by `scripts/fetch-ratings.ts`. It is committed as `{}` so the
 * site builds with all-zero ratings when no snapshot has been fetched (local
 * dev, forks, or a repo without the giscus/Discussions setup).
 */
import ratings from "../data/ratings.json";

const counts = ratings as Record<string, number>;

/** 👍 count for a skill slug (0 when unknown). */
export function getRating(slug: string): number {
  const n = counts[slug];
  return typeof n === "number" && Number.isFinite(n) && n > 0 ? n : 0;
}
