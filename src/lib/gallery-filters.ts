import { PLATFORMS, type Platform } from "./skills";

export const FORMAT_LABELS: Readonly<Record<string, string>> = {
  skill: "Skills", plugin: "Plugins", automation: "Automations",
};

export interface FilterableSubmission {
  name: string;
  description: string;
  tags: readonly string[];
  platforms: readonly string[];
  type: string;
  authorName: string;
  authorLogin: string;
  authorKey: string;
}

export interface GalleryFilters {
  query: string;
  platform: Platform | "";
  types: ReadonlySet<string>;
  tags: ReadonlySet<string>;
  author: string;
}

export function copyGalleryFilters(filters: GalleryFilters) {
  return {
    ...filters,
    types: new Set(filters.types),
    tags: new Set(filters.tags),
  };
}

export function parseGalleryFilters(params: URLSearchParams): GalleryFilters {
  const selections = (key: string) => new Set(
    (params.get(key) ?? "").split(",").map((value) => value.trim()).filter(Boolean),
  );
  const platforms = [...selections("platform")].filter((value): value is Platform =>
    PLATFORMS.some((platform) => platform === value),
  );
  return {
    query: (params.get("q") ?? "").toLowerCase(),
    // Legacy unions covering every platform remain unrestricted; partial unions use the first valid choice.
    platform: platforms.length === PLATFORMS.length ? "" : platforms[0] ?? "",
    types: new Set([...selections("type")].map((value) => value.toLowerCase())),
    tags: selections("tag"),
    author: [...selections("author")][0]?.toLowerCase() ?? "",
  };
}

export function galleryFilterParams(filters: GalleryFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.platform) params.set("platform", filters.platform);
  if (filters.types.size) params.set("type", [...filters.types].join(","));
  if (filters.tags.size) params.set("tag", [...filters.tags].join(","));
  if (filters.author) params.set("author", filters.author);
  return params;
}

export function matchesFilters(item: FilterableSubmission, filters: GalleryFilters): boolean {
  const text = [
    item.name, item.description, ...item.tags, item.authorName, item.authorLogin,
    item.type, `${item.type}s`,
  ].join(" ").toLowerCase();
  return (
    (!filters.query || text.includes(filters.query.trim().toLowerCase())) &&
    (!filters.platform || item.platforms.includes(filters.platform)) &&
    (!filters.types.size || filters.types.has(item.type)) &&
    [...filters.tags].every((tag) => item.tags.includes(tag)) &&
    (!filters.author || filters.author === item.authorKey)
  );
}

/** Tag counts include selected tags so adding another tag can only narrow the results. */
export function countFacet(
  items: Iterable<FilterableSubmission>,
  filters: GalleryFilters,
  facet: "types" | "tags" | "authors",
): Map<string, number> {
  const counts = new Map<string, number>();
  const otherFilters = facet === "tags" ? filters
    : facet === "authors" ? { ...filters, author: "" } : { ...filters, types: new Set<string>() };
  for (const item of items) {
    if (!matchesFilters(item, otherFilters)) continue;
    const values = facet === "types" ? [item.type] : facet === "authors" ? [item.authorKey] : item.tags;
    for (const value of new Set(values)) {
      if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
    }
  }
  return counts;
}
