import { CATEGORY_LABELS, isCategory, type Category } from "./categories";

export interface FilterableSubmission {
  name: string;
  description: string;
  tags: readonly string[];
  platforms: readonly string[];
  type: string;
  category: Category;
  builtByMicrosoft: boolean;
  authorName: string;
  authorLogin: string;
  authorKey: string;
}

export interface GalleryFilters {
  query: string;
  categories: ReadonlySet<Category>;
  platform: string;
  type: string;
  tags: ReadonlySet<string>;
  authors: ReadonlySet<string>;
}

export function copyGalleryFilters(filters: GalleryFilters) {
  return { ...filters, categories: new Set(filters.categories), tags: new Set(filters.tags), authors: new Set(filters.authors) };
}

export function parseGalleryFilters(params: URLSearchParams): GalleryFilters {
  const selections = (key: string) => new Set(
    (params.get(key) ?? "").split(",").map((value) => value.trim()).filter(Boolean),
  );
  return {
    query: (params.get("q") ?? "").toLowerCase(),
    categories: new Set([...selections("category")].filter(isCategory)),
    platform: params.get("platform") ?? "",
    type: params.get("type") ?? "",
    tags: selections("tag"),
    authors: new Set([...selections("author")].map((value) => value.toLowerCase())),
  };
}

export function galleryFilterParams(filters: GalleryFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.categories.size) params.set("category", [...filters.categories].join(","));
  if (filters.platform) params.set("platform", filters.platform);
  if (filters.type) params.set("type", filters.type);
  if (filters.tags.size) params.set("tag", [...filters.tags].join(","));
  if (filters.authors.size) params.set("author", [...filters.authors].join(","));
  return params;
}

export function matchesFilters(item: FilterableSubmission, filters: GalleryFilters): boolean {
  const text = [
    item.name, item.description, ...item.tags, item.authorName, item.authorLogin,
    CATEGORY_LABELS[item.category],
    item.type, `${item.type}s`,
    item.builtByMicrosoft ? "Built by Microsoft" : "Built by the community",
  ].join(" ").toLowerCase();
  return (
    (!filters.query || text.includes(filters.query.trim().toLowerCase())) &&
    (!filters.categories.size || filters.categories.has(item.category)) &&
    (!filters.platform || item.platforms.includes(filters.platform)) &&
    (!filters.type || item.type === filters.type) &&
    (!filters.tags.size || item.tags.some((tag) => filters.tags.has(tag))) &&
    (!filters.authors.size || filters.authors.has(item.authorKey))
  );
}

export function countPlatforms(
  items: Iterable<FilterableSubmission>,
  filters: GalleryFilters,
): Map<string, number> {
  const counts = new Map<string, number>();
  const otherFilters = { ...filters, platform: "" };
  for (const item of items) {
    if (!matchesFilters(item, otherFilters)) continue;
    for (const platform of new Set(item.platforms)) {
      counts.set(platform, (counts.get(platform) ?? 0) + 1);
    }
  }
  return counts;
}

export function partitionSubmissions<T extends { data: { builtByMicrosoft?: boolean } }>(items: readonly T[]) {
  return {
    microsoft: items.filter((item) => item.data.builtByMicrosoft === true),
    community: items.filter((item) => item.data.builtByMicrosoft !== true),
  };
}
