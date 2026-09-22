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

export function isCategory(value: string): value is Category {
  return CATEGORIES.some((category) => category === value);
}
