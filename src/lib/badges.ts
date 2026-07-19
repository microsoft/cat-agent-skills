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
  | "top-rated"
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
  "top-rated",
  "skill-factory",
  "teachers-pet",
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
  createdAt?: string | number | Date | null;
  platforms?: string[];
}

export interface ContributorStats {
  login: string;
  displayName: string;
  skillCount: number;
  featuredCount: number;
  totalRating: number;
  avgRating: number;
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
  factoryThreshold: number;
}

/** Bare, comparable GitHub login (lowercased, no leading `@`). */
export function normalizeLogin(login: string | null | undefined): string {
  return (login ?? "").trim().toLowerCase().replace(/^@/, "");
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
  let totalRating = 0;
  let zeroRatedCount = 0;
  let newest: number | null = null;
  let displayName = "";
  const platforms = new Set<string>();
  const list: { slug: string; name: string; featured: boolean }[] = [];

  for (const s of mine) {
    if (s.featured) featuredCount++;
    const r = typeof s.rating === "number" && Number.isFinite(s.rating) ? s.rating : 0;
    totalRating += r;
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
    totalRating,
    avgRating: skillCount ? totalRating / skillCount : 0,
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
    factoryThreshold: 5,
  };
}

/** Assign a badge from stats. Ordered, first match wins. */
export function pickBadge(stats: ContributorStats, ctx: BadgeContext): BadgeMeta {
  if (stats.totalRating > 0 && ctx.ratingLeaders.has(stats.login))
    return BADGES["top-rated"];
  if (stats.skillCount >= ctx.factoryThreshold) return BADGES["skill-factory"];
  if (stats.featuredCount > 0 && ctx.featuredLeaders.has(stats.login))
    return BADGES["teachers-pet"];
  return BADGES["house-cat"];
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

/** One-shot: stats → badge → caption for a login. `null` if they've contributed nothing. */
export function resolveBadge(login: string, skills: BadgeSkill[]): ResolvedBadge | null {
  const stats = computeStats(login, skills);
  if (stats.skillCount === 0) return null;
  const badge = pickBadge(stats, buildContext(skills));
  return { badge, caption: captionFor(badge, stats.login), stats };
}
