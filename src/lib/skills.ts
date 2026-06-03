/**
 * Shared helpers for the skills gallery: deterministic cover styling and
 * small utilities reused across pages, endpoints, and the client island.
 */

/** The agent platforms a skill can target. */
export const PLATFORMS = ["Cowork", "Copilot Studio", "Scout"] as const;
export type Platform = (typeof PLATFORMS)[number];

/** Brand accent color used for each platform's badge. */
export const PLATFORM_COLORS: Record<Platform, string> = {
  Cowork: "#7c3aed",
  "Copilot Studio": "#2563eb",
  Scout: "#0d9488",
};

const COVER_PALETTE: Array<[string, string]> = [
  ["#3461ff", "#7a3cff"],
  ["#ff5f6d", "#ffc371"],
  ["#11998e", "#38ef7d"],
  ["#8e2de2", "#4a00e0"],
  ["#f7971e", "#ffd200"],
  ["#00b4db", "#0083b0"],
  ["#fc466b", "#3f5efb"],
  ["#e96443", "#904e95"],
  ["#1d976c", "#93f9b9"],
  ["#4776e6", "#8e54e9"],
  ["#ff512f", "#dd2476"],
  ["#2193b0", "#6dd5ed"],
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
  tags: string[];
  author?: string;
  version?: string;
  hasBundle: boolean;
  featured: boolean;
  gradient: string;
  initials: string;
};
