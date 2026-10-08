export const CATEGORIES = [
  "manufacturing",
  "retail-cpg",
  "productivity",
  "agent-development",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<Category, string> = {
  manufacturing: "Manufacturing",
  "retail-cpg": "Retail & CPG",
  productivity: "Productivity",
  "agent-development": "Agent development",
};

export const CATEGORY_COLORS: Record<Category, string> = {
  manufacturing: "#0078d4",
  "retail-cpg": "#6366f1",
  productivity: "#0f8b8d",
  "agent-development": "#9254de",
};

export const CATEGORY_ICON_PATHS: Record<Category, string> = {
  manufacturing: "M3 21V10l6 3V9l6 4V3h4l2 18H3Zm4-4h1m4 0h1m4 0h1",
  "retail-cpg": "M3 10l2-6h14l2 6M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 13v8h14v-8M10 21v-6h4v6",
  productivity: "M9 5H6a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3M9 3h6v4H9V3Zm-1 12 3 3 5-6",
  "agent-development": "m7 8-4 4 4 4m10-8 4 4-4 4M14 4l-4 16",
};

export function isCategory(value: string): value is Category {
  return CATEGORIES.some((category) => category === value);
}
