/**
 * Shared helpers for the skills gallery: deterministic cover styling and
 * small utilities reused across pages, endpoints, and the client island.
 */

/** The agent platforms a skill can target. */
export const PLATFORMS = ["Cowork", "Copilot Studio", "Scout"] as const;
export type Platform = (typeof PLATFORMS)[number];

/**
 * A submission is a single cross-platform Agent Skill, a Cowork plugin (an M365
 * app package bundling one or more skills + optional connectors), or a Scout
 * automation (a scheduled `.json` of ordered prompt steps, Scout-only).
 */
export type SkillType = "skill" | "plugin" | "automation";

/** Brand accent color used for each platform's badge (CAT palette). */
export const PLATFORM_COLORS: Record<Platform, string> = {
  Cowork: "#7f39fb",
  "Copilot Studio": "#0078d4",
  Scout: "#0d9488",
};

/**
 * Cover gradient pairs drawn from the CAT brand spectrum
 * (blue -> purple -> pink -> orange). Calm enough to read well against both
 * light and dark backgrounds.
 */
const COVER_PALETTE: Array<[string, string]> = [
  ["#0078d4", "#5b8def"],
  ["#5b8def", "#7f39fb"],
  ["#7f39fb", "#c26cf3"],
  ["#c26cf3", "#d83b73"],
  ["#d83b73", "#ff8c00"],
  ["#0078d4", "#7f39fb"],
  ["#3aa0ff", "#5b8def"],
  ["#7f39fb", "#d83b73"],
  ["#0d9488", "#5b8def"],
  ["#c26cf3", "#5b8def"],
  ["#d83b73", "#c26cf3"],
  ["#0078d4", "#0d9488"],
];

/** Stable hash for a string (FNV-1a style, good enough for theming). */
function hash(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Deterministic gradient for a skill, derived from its slug. */
export function coverGradient(slug: string, override?: string): string {
  if (override) {
    return `linear-gradient(135deg, ${override} 0%, ${override} 100%)`;
  }
  const [from, to] = COVER_PALETTE[hash(slug) % COVER_PALETTE.length];
  const angle = 110 + (hash(slug + "angle") % 60);
  return `linear-gradient(${angle}deg, ${from} 0%, ${to} 100%)`;
}

/** Up to two-letter initials used as a watermark on covers. */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "AI";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

export function formatDate(date?: Date): string | undefined {
  if (!date) return undefined;
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export type SkillSummary = {
  slug: string;
  name: string;
  description: string;
  platforms: Platform[];
  type: SkillType;
  tags: string[];
  author?: string;
  authorGithub?: string | null;
  createdAt?: string | null;
  version?: string;
  hasBundle: boolean;
  featured: boolean;
  rating: number;
  gradient: string;
  initials: string;
};
