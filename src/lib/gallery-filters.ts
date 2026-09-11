import { CATEGORY_LABELS, type Category } from "./categories";

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
  category: Category | "";
  platform: string;
  type: string;
  tags: ReadonlySet<string>;
  authors: ReadonlySet<string>;
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
    (!filters.category || item.category === filters.category) &&
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

export function categorySubmissions<T extends { data: { category: Category; builtByMicrosoft?: boolean } }>(
  items: readonly T[],
  category: Category,
) {
  return partitionSubmissions(items.filter((item) => item.data.category === category));
}
