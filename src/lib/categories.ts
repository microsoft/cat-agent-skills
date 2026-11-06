export const CATEGORIES = [
  "manufacturing",
  "retail-cpg",
  "productivity",
  "agent-development",
  "education",
  "legal",
  "sales",
  "service",
  "finance",
  "capital-markets",
  "accounting",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<Category, string> = {
  manufacturing: "Manufacturing",
  "retail-cpg": "Retail & CPG",
  productivity: "Productivity",
  "agent-development": "Agent development",
  education: "Education",
  legal: "Legal",
  sales: "Sales",
  service: "Service",
  finance: "Finance",
  "capital-markets": "Capital Markets",
  accounting: "Accounting",
};

export const CATEGORY_COLORS: Record<Category, string> = {
  manufacturing: "#0078d4",
  "retail-cpg": "#6366f1",
  productivity: "#0f8b8d",
  "agent-development": "#9254de",
  education: "#2563eb",
  legal: "#7c3aed",
  sales: "#b45309",
  service: "#0f766e",
  finance: "#047857",
  "capital-markets": "#4338ca",
  accounting: "#0369a1",
};

export const CATEGORY_ICON_PATHS: Record<Category, string> = {
  manufacturing: "M3 21V10l6 3V9l6 4V3h4l2 18H3Zm4-4h1m4 0h1m4 0h1",
  "retail-cpg": "M3 10l2-6h14l2 6M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 13v8h14v-8M10 21v-6h4v6",
  productivity: "M9 5H6a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3M9 3h6v4H9V3Zm-1 12 3 3 5-6",
  "agent-development": "m7 8-4 4 4 4m10-8 4 4-4 4M14 4l-4 16",
  education: "m2 9 10-5 10 5-10 5-10-5Zm4 2v6c4 3 8 3 12 0v-6M22 9v8",
  legal: "M12 3v18M5 21h14M4 7h16M6 7l-4 7h8L6 7Zm12 0-4 7h8l-4-7Z",
  sales: "M3 21V3m0 18h18M7 16l5-5 4 3 5-7m-5 0h5v5",
  service: "M4 14v-3a8 8 0 0 1 16 0v3M4 11H2v7h4v-7H4Zm16 0h2v7h-4v-7h2Zm0 7c0 3-3 3-6 3h-2",
  finance: "M12 3v18m5-14c-1-3-10-3-10 1s10 4 10 8-9 4-10 1",
  "capital-markets": "m3 10 9-7 9 7H3Zm2 3v5m5-5v5m4-5v5m5-5v5M3 21h18",
  accounting: "M6 3h12v18H6V3Zm3 3h6v4H9V6Zm0 8h1m4 0h1m-6 3h1m4 0h1",
};
