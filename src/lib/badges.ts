/**
 * Contributor badge engine (framework-agnostic, pure).
 *
 * Given the public skills catalog (each skill carries `authorGithub`, `featured`,
 * `rating`, `createdAt`), this computes per-author stats and assigns exactly one
 * gently-snarky badge. Imported both server-side (the Authors directory) and
 * client-side (the "You" panel island), so it must not import anything Astro-
 * or Node-specific.
 *
 * The badge itself is not secret — contributions here are public — so "only to
 * them" is a UI choice enforced by the panel, not by this module.
 */

export type BadgeId =
  | "deep-cat"
  | "top-rated"
  | "shelf-clearer"
  | "skill-factory"
  | "teachers-pet"
  | "house-cat";

export interface BadgeMeta {
  id: BadgeId;
  title: string;
  /** Base filename in /public/badges (a `.png`, with a `.svg` placeholder fallback). */
  image: string;
  /** Plain, non-snarky line explaining how the badge is earned (shown in the reveal). */
  meaning: string;
  /** Snarky caption variants; one is chosen deterministically per login. */
  captions: string[];
}

export const BADGES: Record<BadgeId, BadgeMeta> = {
  "deep-cat": {
    id: "deep-cat",
    title: "Deep Cat",
    image: "deep-cat",
    meaning: "More than three Scout automations shipped.",
    captions: [
      "Certified bottom-dweller. The automations run themselves down here.",
      "More claws than paws at these depths.",
      "You went so deep the crabs started reporting to you.",
    ],
  },
  "top-rated": {
    id: "top-rated",
    title: "Crowd Favorite",
    image: "top-rated",
    meaning: "Top 3 by community upvotes.",
    captions: [
      "Certified crowd favorite. The crowd is fickle.",
      "Peer-reviewed by strangers with thumbs. Rigorous.",
      "Top-rated today. Don't get comfortable.",
    ],
  },
  "shelf-clearer": {
    id: "shelf-clearer",
    title: "Shelf Clearer",
    image: "shelf-clearer",
    meaning: "Top 3 contributors by all-time skill downloads.",
    captions: [
      "Nothing left but dust and a suspicious number of ZIP files.",
      "Your skills keep disappearing into other people's folders.",
      "Cleared the shelf. Restocking is somebody else's problem.",
    ],
  },
  "skill-factory": {
    id: "skill-factory",
    title: "The Skill Factory",
    image: "skill-factory",
    meaning: "Five or more skills shipped.",
    captions: [
      "Certified in Volume. The ratings are still loading.",
      "You've automated everything except stopping.",
      "Quantity is a strategy. Allegedly.",
    ],
  },
  "teachers-pet": {
    id: "teachers-pet",
    title: "Teacher's Pet",
    image: "teachers-pet",
    meaning: "Top 3 by featured skills.",
    captions: [
      "The homepage keeps picking you. Suspicious.",
      "Top three in featured. Teacher noticed.",
      "Certified homepage favorite. Don't let it go to your head.",
    ],
  },
  "house-cat": {
    id: "house-cat",
    title: "The House Cat",
    image: "house-cat",
    meaning: "Every contributor who ships.",
    captions: [
      "Achievement unlocked: you shipped.",
      "Level 1 cleared. Plenty of game left.",
      "The starter badge — everyone begins here.",
    ],
  },
};

/** Assignment order — first matching rule wins. */
export const BADGE_ORDER: BadgeId[] = [
  "deep-cat",
  "skill-factory",
  "teachers-pet",
  "shelf-clearer",
  "top-rated",
  "house-cat",
];

/** Minimal shape the engine needs from a skill (subset of SkillSummary). */
export interface BadgeSkill {
  slug: string;
  name?: string;
  author?: string | null;
  authorGithub?: string | null;
  featured?: boolean;
  rating?: number;
  downloads?: number;
  createdAt?: string | number | Date | null;
  platforms?: string[];
  type?: "skill" | "plugin" | "automation";
}

export interface ContributorStats {
  login: string;
  displayName: string;
  skillCount: number;
  featuredCount: number;
  automationCount: number;
  totalRating: number;
  avgRating: number;
  totalDownloads: number;
  avgDownloads: number;
  zeroRatedCount: number;
  platforms: string[];
  newestCreatedAtMs: number | null;
  skills: { slug: string; name: string; featured: boolean }[];
}

export interface BadgeContext {
  /** Logins that rank in the top-N by total community rating (👍). */
  ratingLeaders: Set<string>;
  /** Logins that rank in the top-N by featured-skill count. */
  featuredLeaders: Set<string>;
  /** Logins that rank in the top-N by all-time downloads. */
  downloadLeaders: Set<string>;
  /** A contributor needs strictly MORE Scout automations than this to earn "Deep Cat". */
  automationThreshold: number;
  factoryThreshold: number;
}

/** Bare, comparable GitHub login (lowercased, no leading `@`). */
export function normalizeLogin(login: string | null | undefined): string {
  return (login ?? "").trim().toLowerCase().replace(/^@/, "");
}

/**
 * Canonical key used to group and filter a person's skills across the gallery
 * (homepage `?author=` filter, detail-page byline, Contributors links).
 * Prefers the normalized GitHub login — stable and matching profile URLs — and
 * falls back to a slug of the display name for the few submissions with no
 * login, so every author is still browsable.
 */
export function authorKey(
  login: string | null | undefined,
  name: string | null | undefined,
): string {
  const l = normalizeLogin(login);
  if (l) return l;
  return (name ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function toMs(value: BadgeSkill["createdAt"]): number | null {
  if (value == null) return null;
  if (value instanceof Date) return value.getTime();
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

/** FNV-1a hash — deterministic caption selection per login. */
function hash(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Aggregate one author's contributions. `skillCount === 0` ⇒ not a contributor. */
export function computeStats(login: string, skills: BadgeSkill[]): ContributorStats {
  const norm = normalizeLogin(login);
  const mine =
    norm === ""
      ? []
      : skills.filter((s) => normalizeLogin(s.authorGithub) === norm);

  let featuredCount = 0;
  let automationCount = 0;
  let totalRating = 0;
  let totalDownloads = 0;
  let zeroRatedCount = 0;
  let newest: number | null = null;
  let displayName = "";
  const platforms = new Set<string>();
  const list: { slug: string; name: string; featured: boolean }[] = [];

  for (const s of mine) {
    if (s.featured) featuredCount++;
    if (s.type === "automation" && (s.platforms ?? []).includes("Scout"))
      automationCount++;
    const r = typeof s.rating === "number" && Number.isFinite(s.rating) ? s.rating : 0;
    totalRating += r;
    const d =
      typeof s.downloads === "number" && Number.isFinite(s.downloads)
        ? Math.max(0, s.downloads)
        : 0;
    totalDownloads += d;
    if (r <= 0) zeroRatedCount++;
    (s.platforms ?? []).forEach((p) => platforms.add(p));
    const ms = toMs(s.createdAt);
    if (ms != null) newest = newest == null ? ms : Math.max(newest, ms);
    if (!displayName && s.author) displayName = s.author;
    list.push({ slug: s.slug, name: s.name ?? s.slug, featured: !!s.featured });
  }

  const skillCount = mine.length;
  list.sort(
    (a, b) => Number(b.featured) - Number(a.featured) || a.name.localeCompare(b.name),
  );
  return {
    login: norm,
    displayName: displayName || login,
    skillCount,
    featuredCount,
    automationCount,
    totalRating,
    avgRating: skillCount ? totalRating / skillCount : 0,
    totalDownloads,
    avgDownloads: skillCount ? totalDownloads / skillCount : 0,
    zeroRatedCount,
    platforms: [...platforms],
    newestCreatedAtMs: newest,
    skills: list,
  };
}

/** Every author's stats, sorted as a "top contributors" list. */
export function allAuthors(skills: BadgeSkill[]): ContributorStats[] {
  const logins = new Set<string>();
  for (const s of skills) {
    const l = normalizeLogin(s.authorGithub);
    if (l) logins.add(l);
  }
  return [...logins]
    .map((l) => computeStats(l, skills))
    .sort(
      (a, b) =>
        b.skillCount - a.skillCount ||
        b.featuredCount - a.featuredCount ||
        a.login.localeCompare(b.login),
    );
}

/** Logins in the top-N by featured-skill count (featuredCount > 0 only). */
export function featuredLeaderLogins(skills: BadgeSkill[], topN = 3): Set<string> {
  const leaders = allAuthors(skills)
    .filter((a) => a.featuredCount > 0)
    .sort(
      (a, b) =>
        b.featuredCount - a.featuredCount ||
        b.skillCount - a.skillCount ||
        a.login.localeCompare(b.login),
    )
    .slice(0, topN);
  return new Set(leaders.map((a) => a.login));
}

/** Logins in the top-N by total community rating (totalRating > 0 only). */
export function ratingLeaderLogins(skills: BadgeSkill[], topN = 3): Set<string> {
  const leaders = allAuthors(skills)
    .filter((a) => a.totalRating > 0)
    .sort(
      (a, b) =>
        b.totalRating - a.totalRating ||
        b.avgRating - a.avgRating ||
        a.login.localeCompare(b.login),
    )
    .slice(0, topN);
  return new Set(leaders.map((a) => a.login));
}

/** Logins in the top-N by aggregate all-time downloads (totalDownloads > 0 only). */
export function downloadLeaderLogins(skills: BadgeSkill[], topN = 3): Set<string> {
  const leaders = allAuthors(skills)
    .filter((a) => a.totalDownloads > 0)
    .sort(
      (a, b) =>
        b.totalDownloads - a.totalDownloads ||
        b.avgDownloads - a.avgDownloads ||
        a.login.localeCompare(b.login),
    )
    .slice(0, topN);
  return new Set(leaders.map((a) => a.login));
}

/** Most recent contribution time across the whole gallery (ms). */
export function galleryNewestMs(skills: BadgeSkill[]): number | null {
  let newest: number | null = null;
  for (const s of skills) {
    const ms = toMs(s.createdAt);
    if (ms != null) newest = newest == null ? ms : Math.max(newest, ms);
  }
  return newest;
}

export function buildContext(skills: BadgeSkill[]): BadgeContext {
  return {
    ratingLeaders: ratingLeaderLogins(skills, 3),
    featuredLeaders: featuredLeaderLogins(skills, 3),
    downloadLeaders: downloadLeaderLogins(skills, 3),
    automationThreshold: 3,
    factoryThreshold: 5,
  };
}

/** Every badge earned by a contributor, in display order. */
export function earnedBadges(stats: ContributorStats, ctx: BadgeContext): BadgeMeta[] {
  const earned = new Set<BadgeId>(["house-cat"]);
  if (stats.automationCount > ctx.automationThreshold) earned.add("deep-cat");
  if (stats.skillCount >= ctx.factoryThreshold) earned.add("skill-factory");
  if (stats.featuredCount > 0 && ctx.featuredLeaders.has(stats.login))
    earned.add("teachers-pet");
  if (stats.totalDownloads > 0 && ctx.downloadLeaders.has(stats.login))
    earned.add("shelf-clearer");
  if (stats.totalRating > 0 && ctx.ratingLeaders.has(stats.login)) earned.add("top-rated");
  return BADGE_ORDER.filter((id) => earned.has(id)).map((id) => BADGES[id]);
}

/** The first badge shown for legacy single-badge surfaces. */
export function pickBadge(stats: ContributorStats, ctx: BadgeContext): BadgeMeta {
  return earnedBadges(stats, ctx)[0];
}

/** Deterministic snarky caption for a badge + login. */
export function captionFor(badge: BadgeMeta, login: string): string {
  if (badge.captions.length === 0) return "";
  return badge.captions[hash(login || badge.id) % badge.captions.length];
}

export interface ResolvedBadge {
  badge: BadgeMeta;
  caption: string;
  stats: ContributorStats;
}

/** One-shot: stats → every earned badge for a login. Empty when they have not contributed. */
export function resolveBadges(login: string, skills: BadgeSkill[]): ResolvedBadge[] {
  const stats = computeStats(login, skills);
  if (stats.skillCount === 0) return [];
  return earnedBadges(stats, buildContext(skills)).map((badge) => ({
    badge,
    caption: captionFor(badge, stats.login),
    stats,
  }));
}

/** Legacy single-badge resolver; returns the first badge on the contributor's shelf. */
export function resolveBadge(login: string, skills: BadgeSkill[]): ResolvedBadge | null {
  return resolveBadges(login, skills)[0] ?? null;
}

/** A single evidence tile: a big number/label pair under a revealed badge. */
export interface PosterTile {
  num: string;
  label: string;
}

const TILE_DATE_FMT = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

/** Format a timestamp as the compact "latest" tile value (UTC, so build + client agree). */
export function formatTileDate(ms: number | null): string | null {
  return ms ? TILE_DATE_FMT.format(new Date(ms)) : null;
}

/**
 * The evidence tiles for a revealed badge, ordered so each badge leads with the
 * stat that earned it (crowd favorites lead with votes, the factory with volume,
 * and so on). Capped at three so the row stays tidy. Single source of truth for
 * the on-site reveal, the poster page, and the composed OG image — so they never
 * drift.
 */
export function posterTiles(badge: BadgeMeta, stats: ContributorStats): PosterTile[] {
  const latest = formatTileDate(stats.newestCreatedAtMs);
  const t: Record<string, PosterTile | null> = {
    skills: {
      num: String(stats.skillCount),
      label: stats.skillCount === 1 ? "skill" : "skills",
    },
    automations:
      stats.automationCount > 0
        ? {
            num: String(stats.automationCount),
            label: stats.automationCount === 1 ? "automation" : "automations",
          }
        : null,
    featured:
      stats.featuredCount > 0
        ? { num: String(stats.featuredCount), label: "featured" }
        : null,
    votes:
      stats.totalRating > 0
        ? {
            num: String(stats.totalRating),
            label: stats.totalRating === 1 ? "upvote" : "upvotes",
          }
        : null,
    downloads:
      stats.totalDownloads > 0
        ? {
            num: stats.totalDownloads.toLocaleString("en-US"),
            label: stats.totalDownloads === 1 ? "download" : "downloads",
          }
        : null,
    platforms:
      stats.platforms.length > 0
        ? {
            num: String(stats.platforms.length),
            label: stats.platforms.length === 1 ? "platform" : "platforms",
          }
        : null,
    latest: latest ? { num: latest, label: "latest" } : null,
  };
  const order =
    badge.id === "shelf-clearer"
      ? [t.downloads, t.skills, t.latest]
      : badge.id === "top-rated"
      ? [t.votes, t.skills, t.featured]
      : badge.id === "teachers-pet"
        ? [t.featured, t.skills, t.latest]
        : badge.id === "skill-factory"
          ? [t.skills, t.featured, t.latest]
          : badge.id === "deep-cat"
            ? [t.automations, t.skills, t.latest]
            : [t.skills, t.platforms, t.latest];
  return order.filter((x): x is PosterTile => Boolean(x)).slice(0, 3);
}
