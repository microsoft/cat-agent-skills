/**
 * Read-side helper for skill download counts.
 *
 * `src/data/downloads.json` is a static, committed snapshot of all-time download
 * counts keyed by skill slug. Unlike ratings (fetched from GitHub Discussions),
 * downloads cannot be read from the Microsoft Clarity Data Export API — the
 * `skill_download` Smart Event is not exposed as an API dimension — so the file
 * is maintained out-of-band (seeded from a Clarity dashboard CSV export and
 * refreshed by overwriting this file). The site simply bakes the numbers in at
 * build time, exactly like `ratings.ts` does for reaction counts.
 */
import downloads from "../data/downloads.json";

const counts = downloads as Record<string, number>;

/** All-time download count for a skill slug (0 when unknown). */
export function getDownloads(slug: string): number {
  const n = counts[slug];
  return typeof n === "number" && Number.isFinite(n) && n > 0 ? n : 0;
}
