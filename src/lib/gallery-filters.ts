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
  platforms: ReadonlySet<string>;
  types: ReadonlySet<string>;
  tags: ReadonlySet<string>;
  authors: ReadonlySet<string>;
}

export function copyGalleryFilters(filters: GalleryFilters) {
  return {
    ...filters,
    platforms: new Set(filters.platforms),
    types: new Set(filters.types),
    tags: new Set(filters.tags),
    authors: new Set(filters.authors),
  };
}

export function parseGalleryFilters(params: URLSearchParams): GalleryFilters {
  const selections = (key: string) => new Set(
    (params.get(key) ?? "").split(",").map((value) => value.trim()).filter(Boolean),
  );
  return {
    query: (params.get("q") ?? "").toLowerCase(),
    platforms: selections("platform"),
    types: new Set([...selections("type")].map((value) => value.toLowerCase())),
    tags: selections("tag"),
    authors: new Set([...selections("author")].map((value) => value.toLowerCase())),
  };
}

export function galleryFilterParams(filters: GalleryFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.platforms.size) params.set("platform", [...filters.platforms].join(","));
  if (filters.types.size) params.set("type", [...filters.types].join(","));
  if (filters.tags.size) params.set("tag", [...filters.tags].join(","));
  if (filters.authors.size) params.set("author", [...filters.authors].join(","));
  return params;
}

export function matchesFilters(item: FilterableSubmission, filters: GalleryFilters): boolean {
  const text = [
    item.name, item.description, ...item.tags, item.authorName, item.authorLogin,
    item.type, `${item.type}s`,
  ].join(" ").toLowerCase();
  return (
    (!filters.query || text.includes(filters.query.trim().toLowerCase())) &&
    (!filters.platforms.size || item.platforms.some((platform) => filters.platforms.has(platform))) &&
    (!filters.types.size || filters.types.has(item.type)) &&
    (!filters.tags.size || item.tags.some((tag) => filters.tags.has(tag))) &&
    (!filters.authors.size || filters.authors.has(item.authorKey))
  );
}

/** Count each option against the other facets, including platform and format selections. */
export function countFacet(
  items: Iterable<FilterableSubmission>,
  filters: GalleryFilters,
  facet: "tags" | "authors",
): Map<string, number> {
  const counts = new Map<string, number>();
  const otherFilters = { ...filters, [facet]: new Set<string>() };
  for (const item of items) {
    if (!matchesFilters(item, otherFilters)) continue;
    const values = facet === "authors" ? [item.authorKey] : item.tags;
    for (const value of new Set(values)) {
      if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
    }
  }
  return counts;
}
