import { test } from "node:test";
import assert from "node:assert/strict";
import { CATEGORIES, CATEGORY_COLORS, CATEGORY_ICON_PATHS, CATEGORY_LABELS, isCategory } from "../src/lib/categories.ts";
import { copyGalleryFilters, countPlatforms, galleryFilterParams, matchesFilters, parseGalleryFilters, partitionSubmissions, type FilterableSubmission, type GalleryFilters } from "../src/lib/gallery-filters.ts";
import { skillSchema } from "../src/lib/skill-schema.ts";
import { authorKey } from "../src/lib/badges.ts";

const submission: FilterableSubmission = {
  name: "Quality Inspection",
  description: "Draft a nonconformance report",
  tags: ["quality", "inspection"],
  platforms: ["Cowork"],
  type: "plugin",
  category: "manufacturing",
  builtByMicrosoft: true,
  authorName: "Industry Templates",
  authorLogin: "sravaniseethi",
  authorKey: "sravaniseethi",
};
const filters: GalleryFilters = {
  query: "", categories: new Set(), platform: "", type: "",
  tags: new Set(), authors: new Set(),
};
const metadata = {
  name: "Example", description: "Example submission", platforms: ["Cowork"],
  tags: ["quality"], author: "Author",
};
const platformSubmissions: readonly FilterableSubmission[] = [
  submission,
  {
    name: "Writing helper",
    description: "Draft clear text",
    tags: ["writing"],
    platforms: ["Cowork", "Copilot Studio", "Cowork"],
    type: "skill",
    category: "productivity",
    builtByMicrosoft: false,
    authorName: "Community Author",
    authorLogin: "community-author",
    authorKey: "community-author",
  },
  {
    name: "Report monitor",
    description: "Monitor report updates",
    tags: ["quality", "automation"],
    platforms: ["Scout"],
    type: "automation",
    category: "manufacturing",
    builtByMicrosoft: false,
    authorName: "Community Author",
    authorLogin: "community-author",
    authorKey: "community-author",
  },
];

test("categories are a closed stable vocabulary with labels", () => {
  assert.equal(CATEGORIES.length, 4);
  for (const category of CATEGORIES) {
    assert.ok(isCategory(category));
    assert.ok(CATEGORY_LABELS[category]);
    assert.equal(skillSchema.parse({ ...metadata, category }).category, category);
  }
  assert.equal(isCategory("quality"), false);
  assert.equal(isCategory(""), false);
  assert.equal(skillSchema.safeParse({ ...metadata, category: "quality" }).success, false);
});

test("every category has a distinct team-managed icon and color", () => {
  assert.deepEqual(Object.keys(CATEGORY_ICON_PATHS), [...CATEGORIES]);
  assert.deepEqual(Object.keys(CATEGORY_COLORS), [...CATEGORIES]);
  assert.equal(new Set(Object.values(CATEGORY_ICON_PATHS)).size, CATEGORIES.length);
  assert.equal(new Set(Object.values(CATEGORY_COLORS)).size, CATEGORIES.length);
  for (const category of CATEGORIES) {
    assert.match(CATEGORY_ICON_PATHS[category], /^[Mm]/);
    assert.match(CATEGORY_COLORS[category], /^#[0-9a-f]{6}$/i);
  }
});

test("omitted metadata preserves existing community submissions", () => {
  const parsed = skillSchema.parse(metadata);
  assert.equal(parsed.category, "productivity");
  assert.equal(parsed.builtByMicrosoft, false);
});

test("Microsoft membership requires an actual boolean", () => {
  for (const flag of [false, true]) {
    assert.equal(skillSchema.parse({ ...metadata, builtByMicrosoft: flag }).builtByMicrosoft, flag);
  }
  for (const flag of ["true", "false", 1, 0, null]) {
    assert.equal(skillSchema.safeParse({ ...metadata, builtByMicrosoft: flag }).success, false);
  }
});

test("every submission type partitions by metadata alone, without duplication", () => {
  const items = ["skill", "plugin", "automation"].flatMap((type) =>
    [true, false, undefined].map((builtByMicrosoft) => ({
      data: { type, builtByMicrosoft, author: "Microsoft", featured: true },
    })),
  );
  const { microsoft, community } = partitionSubmissions(items);
  assert.equal(microsoft.length, 3);
  assert.equal(community.length, 6);
  assert.equal(new Set([...microsoft, ...community]).size, items.length);
  assert.ok(microsoft.every((item) => item.data.builtByMicrosoft === true));
  assert.ok(community.every((item) => !item.data.builtByMicrosoft));
});

test("category filters include both publishers and every submission format", () => {
  const items = CATEGORIES.flatMap((category) =>
    ["skill", "plugin", "automation"].flatMap((type) =>
      [true, false].map((builtByMicrosoft) => ({
        ...submission, category, type, builtByMicrosoft, data: { builtByMicrosoft },
      })),
    ),
  );
  for (const category of CATEGORIES) {
    const matched = items.filter((item) => matchesFilters(item, { ...filters, categories: new Set([category]) }));
    const { microsoft, community } = partitionSubmissions(matched);
    assert.equal(microsoft.length, 3);
    assert.equal(community.length, 3);
    assert.deepEqual(
      new Set([...microsoft, ...community]),
      new Set(items.filter((item) => item.category === category)),
    );
  }
});

test("every category combination matches the union without duplicating submissions", () => {
  const items = CATEGORIES.flatMap((category) =>
    ["skill", "plugin", "automation"].flatMap((type) =>
      [true, false].map((builtByMicrosoft) => ({ ...submission, category, type, builtByMicrosoft })),
    ),
  );
  for (let mask = 0; mask < 1 << CATEGORIES.length; mask++) {
    const categories = new Set(CATEGORIES.filter((_, index) => mask & (1 << index)));
    const matched = items.filter((item) => matchesFilters(item, { ...filters, categories }));
    assert.equal(matched.length, (categories.size || CATEGORIES.length) * 6);
    assert.equal(new Set(matched).size, matched.length);
    assert.equal(matched.filter((item) => item.builtByMicrosoft).length, matched.length / 2);
    for (const item of matched) assert.ok(!categories.size || categories.has(item.category));
  }
});

test("category filtering supports no Microsoft, no community, or no matching submissions", () => {
  const microsoft = { ...submission, data: { builtByMicrosoft: true } };
  const community = { ...submission, category: "productivity" as const, builtByMicrosoft: false, data: { builtByMicrosoft: false } };
  const items = Object.freeze([microsoft, community]);
  const byCategory = (category: typeof CATEGORIES[number]) =>
    partitionSubmissions(items.filter((item) => matchesFilters(item, { ...filters, categories: new Set([category]) })));
  assert.deepEqual(byCategory("manufacturing"), { microsoft: [microsoft], community: [] });
  assert.deepEqual(byCategory("productivity"), { microsoft: [], community: [community] });
  assert.deepEqual(byCategory("retail-cpg"), { microsoft: [], community: [] });
  for (const category of CATEGORIES) {
    assert.equal(matchesFilters(submission, { ...filters, categories: new Set([category]), query: "no such submission" }), false);
  }
});

test("shared filters match both sections identically", () => {
  const items = [true, false].map((builtByMicrosoft) => ({
    ...submission, builtByMicrosoft, data: { builtByMicrosoft },
  }));
  for (const section of Object.values(partitionSubmissions(items))) {
    assert.equal(section.filter((item) => matchesFilters(item, filters)).length, 1);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, categories: new Set(["manufacturing"]) })).length, 1);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, categories: new Set(["retail-cpg"]) })).length, 0);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, platform: "Scout" })).length, 0);
  }
});

test("filters AND facets and OR selections within categories, tags, and contributors", () => {
  const selected: GalleryFilters = {
    ...filters, categories: new Set(["retail-cpg", "manufacturing"]), platform: "Cowork", type: "plugin",
    tags: new Set(["not-present", "quality"]),
    authors: new Set(["not-present", "sravaniseethi"]),
    query: "NONCONFORMANCE",
  };
  assert.ok(matchesFilters(submission, selected));
  for (const changed of [
    { categories: new Set(["productivity" as const]) },
    { type: "skill" },
    { platform: "Scout" },
    { tags: new Set(["absent"]) },
    { authors: new Set(["absent"]) },
    { query: "unrelated" },
  ]) {
    assert.equal(matchesFilters(submission, { ...selected, ...changed }), false);
  }
});

test("search includes category, author name/login, tags, name and description", () => {
  for (const query of [" Manufacturing ", "industry templates", "SravaniSeethi", "inspection", "Quality", "nonconformance"]) {
    assert.ok(matchesFilters(submission, { ...filters, query }), query);
  }
});

test("search includes publisher labels without changing author attribution", () => {
  const community = { ...submission, builtByMicrosoft: false };
  for (const query of [" Microsoft ", "BUILT BY MICROSOFT"]) {
    assert.ok(matchesFilters(submission, { ...filters, query }), query);
    assert.equal(matchesFilters(community, { ...filters, query }), false, query);
  }
  for (const query of ["community", " Built by the COMMUNITY "]) {
    assert.ok(matchesFilters(community, { ...filters, query }), query);
    assert.equal(matchesFilters(submission, { ...filters, query }), false, query);
  }
  const microsoftAuthor = { ...community, authorName: "Microsoft", authorLogin: "microsoft" };
  assert.ok(matchesFilters(microsoftAuthor, { ...filters, query: "Microsoft" }));
  assert.equal(matchesFilters(microsoftAuthor, { ...filters, query: "built by microsoft" }), false);
  assert.ok(matchesFilters(microsoftAuthor, { ...filters, query: "community" }));
});

test("search includes singular and plural formats for both publishers", () => {
  const types = ["skill", "plugin", "automation"];
  for (const type of types) {
    for (const builtByMicrosoft of [true, false]) {
      const item = { ...submission, type, builtByMicrosoft };
      for (const query of [type, `${type}s`, ` ${type.toUpperCase()}S `]) {
        assert.ok(matchesFilters(item, { ...filters, query }), `${type}: ${query}`);
      }
      for (const other of types.filter((value) => value !== type)) {
        assert.equal(matchesFilters(item, { ...filters, query: other }), false, `${type}: ${other}`);
      }
    }
  }
});

test("platform counts combine publishers and count each submission once per platform", () => {
  assert.deepEqual(countPlatforms(platformSubmissions, filters), new Map([
    ["Cowork", 2], ["Copilot Studio", 1], ["Scout", 1],
  ]));
});

test("platform counts ignore only the active platform", () => {
  const expected = countPlatforms(platformSubmissions, filters);
  for (const platform of ["Cowork", "Copilot Studio", "Scout"]) {
    assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, platform }), expected);
  }
});

test("platform counts use the category union while other facets still narrow it", () => {
  const selected: GalleryFilters = {
    ...filters, categories: new Set(["manufacturing", "productivity"]), platform: "Scout",
  };
  assert.deepEqual(countPlatforms(platformSubmissions, selected), new Map([
    ["Cowork", 2], ["Copilot Studio", 1], ["Scout", 1],
  ]));
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, selected)).length, 1);
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, { ...selected, type: "skill" })).length, 0);
  assert.deepEqual(countPlatforms(platformSubmissions, { ...selected, type: "skill" }), new Map([
    ["Cowork", 1], ["Copilot Studio", 1],
  ]));
  assert.deepEqual(countPlatforms(platformSubmissions, { ...selected, tags: new Set(["quality"]) }), new Map([
    ["Cowork", 1], ["Scout", 1],
  ]));
});

test("platform counts honor each other filter facet", () => {
  const cases: Array<{ selected: Partial<GalleryFilters>; expected: Array<[string, number]> }> = [
    { selected: { query: "WRITING" }, expected: [["Cowork", 1], ["Copilot Studio", 1]] },
    { selected: { query: "Microsoft" }, expected: [["Cowork", 1]] },
    { selected: { categories: new Set(["manufacturing"]) }, expected: [["Cowork", 1], ["Scout", 1]] },
    { selected: { type: "plugin" }, expected: [["Cowork", 1]] },
    { selected: { tags: new Set(["absent", "quality"]) }, expected: [["Cowork", 1], ["Scout", 1]] },
    {
      selected: { authors: new Set(["absent", "community-author"]) },
      expected: [["Cowork", 1], ["Copilot Studio", 1], ["Scout", 1]],
    },
  ];
  for (const { selected, expected } of cases) {
    assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, ...selected }), new Map(expected));
  }
});

test("platform counts preserve combined facets even when the selected platform has no results", () => {
  const selected: GalleryFilters = {
    query: "inspection", categories: new Set(["manufacturing"]), platform: "Copilot Studio", type: "plugin",
    tags: new Set(["absent", "quality"]), authors: new Set(["absent", "sravaniseethi"]),
  };
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, selected)).length, 0);
  assert.deepEqual(countPlatforms(platformSubmissions, selected), new Map([["Cowork", 1]]));
});

test("platform counts handle empty collections and no matches", () => {
  assert.deepEqual(countPlatforms([], filters), new Map());
  assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, query: "not present" }), new Map());
  assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, categories: new Set(["retail-cpg"]) }), new Map());
});

test("platform counts do not mutate filter state or submissions", () => {
  const immutableItems = Object.freeze(platformSubmissions.map((item) => Object.freeze({
    ...item,
    tags: Object.freeze([...item.tags]),
    platforms: Object.freeze([...item.platforms]),
  })));
  const selected: GalleryFilters = Object.freeze({
    ...filters, platform: "Scout",
    tags: new Set(["quality"]), authors: new Set(["sravaniseethi"]),
  });
  const originalItems = structuredClone(immutableItems);
  const originalFilters = structuredClone(selected);
  assert.deepEqual(countPlatforms(immutableItems, selected), new Map([["Cowork", 1]]));
  assert.deepEqual(immutableItems, originalItems);
  assert.deepEqual(selected, originalFilters);
});

test("empty results and cleared filters preserve the complete submission set", () => {
  assert.deepEqual(partitionSubmissions([]), { microsoft: [], community: [] });
  assert.equal(matchesFilters(submission, { ...filters, query: "no such submission" }), false);
  assert.ok(matchesFilters(submission, filters));
});

test("draft filter copies cannot mutate applied selections before commit", () => {
  const applied = copyGalleryFilters({
    ...filters, query: "quality", categories: new Set(["manufacturing"]), platform: "Cowork",
    tags: new Set(["quality"]), authors: new Set(["sravaniseethi"]),
  });
  const original = copyGalleryFilters(applied);
  const draft = copyGalleryFilters(applied);
  draft.platform = "Scout";
  draft.type = "automation";
  draft.tags.clear();
  draft.categories.add("retail-cpg");
  draft.authors.add("another-author");
  assert.deepEqual(applied, original);
  assert.notEqual(draft.tags, applied.tags);
  assert.notEqual(draft.categories, applied.categories);
  assert.notEqual(draft.authors, applied.authors);
  const committed = copyGalleryFilters(draft);
  draft.tags.add("later-edit");
  draft.categories.clear();
  assert.equal(committed.tags.has("later-edit"), false);
  assert.deepEqual(committed.categories, new Set(["manufacturing", "retail-cpg"]));
  assert.equal(committed.platform, "Scout");
  assert.deepEqual(copyGalleryFilters(applied), original, "discarding and reopening starts from applied state");
});

test("filter query round trips preserve every facet on either collection route", () => {
  const selected: GalleryFilters = {
    query: "quality & safety", categories: new Set(["manufacturing", "retail-cpg"]), platform: "Copilot Studio", type: "plugin",
    tags: new Set(["quality", "inspection"]), authors: new Set(["sravaniseethi", "another-author"]),
  };
  const query = galleryFilterParams(selected).toString();
  for (const path of ["/cat-agent-skills/", "/cat-agent-skills/built-by-microsoft/"]) {
    const url = new URL(`${path}?${query}`, "https://example.com");
    assert.deepEqual(parseGalleryFilters(url.searchParams), selected);
    assert.equal(url.pathname, path);
  }
  assert.equal(galleryFilterParams(filters).toString(), "");
});

test("tag deep links preserve metadata spelling and URL-encode special characters", () => {
  for (const tag of ["BATNA", "ZOPA", "research & planning", "C++"]) {
    const url = new URL(`/?tag=${encodeURIComponent(tag)}`, "https://example.com");
    const selected = parseGalleryFilters(url.searchParams);
    const item = { ...submission, tags: [tag] };
    assert.deepEqual(selected.tags, new Set([tag]));
    assert.ok(matchesFilters(item, selected));
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(selected)), selected);
    assert.ok(matchesFilters(item, { ...filters, query: tag.toLowerCase() }));
  }
});

test("contributor deep links match normalized GitHub and display-name fallback keys", () => {
  for (const [login, name, expectedKey] of [
    ["SravaniSeethi", "Industry Templates", "sravaniseethi"],
    [undefined, "Marco Zama", "marco-zama"],
  ]) {
    const key = authorKey(login, name);
    assert.equal(key, expectedKey);
    const url = new URL(`/?author=${encodeURIComponent(key)}`, "https://example.com");
    const selected = parseGalleryFilters(url.searchParams);
    assert.deepEqual(selected.authors, new Set([key]));
    assert.ok(matchesFilters({ ...submission, authorKey: key }, selected));
    assert.equal(matchesFilters({ ...submission, authorKey: "someone-else" }, selected), false);
  }
});

test("category URLs accept legacy single values and normalized comma-separated selections", () => {
  const legacy = parseGalleryFilters(new URLSearchParams("category=manufacturing"));
  assert.deepEqual(legacy.categories, new Set(["manufacturing"]));
  assert.equal(galleryFilterParams(legacy).toString(), "category=manufacturing");
  const multiple = copyGalleryFilters(parseGalleryFilters(new URLSearchParams(
    "category=manufacturing,unknown,,retail-cpg,manufacturing,%20productivity%20",
  )));
  assert.deepEqual(multiple.categories, new Set(["manufacturing", "retail-cpg", "productivity"]));
  multiple.categories.delete("manufacturing");
  assert.equal(galleryFilterParams(multiple).get("category"), "retail-cpg,productivity");
  multiple.categories.clear();
  assert.equal(galleryFilterParams(multiple).has("category"), false);
});

test("filter parsing preserves existing URL semantics and never selects a publisher by search", () => {
  const parsed = parseGalleryFilters(new URLSearchParams("q=Microsoft&category=unknown&platform=Scout&type=skill&tag=quality,,inspection,quality&author=SomeAuthor,OTHER"));
  assert.equal(parsed.query, "microsoft");
  assert.deepEqual(parsed.categories, new Set());
  assert.equal(parsed.platform, "Scout");
  assert.equal(parsed.type, "skill");
  assert.deepEqual(parsed.tags, new Set(["quality", "inspection"]));
  assert.deepEqual(parsed.authors, new Set(["someauthor", "other"]));
  assert.deepEqual(parseGalleryFilters(new URLSearchParams()), filters);
});

test("draft result and platform counts use the complete current publisher scope", () => {
  const microsoft = platformSubmissions.filter((item) => item.builtByMicrosoft);
  const draft = copyGalleryFilters(filters);
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, draft)).length, 3);
  assert.equal(microsoft.filter((item) => matchesFilters(item, draft)).length, 1);
  draft.platform = "Copilot Studio";
  assert.equal(microsoft.filter((item) => matchesFilters(item, draft)).length, 0);
  assert.deepEqual(countPlatforms(microsoft, draft), new Map([["Cowork", 1]]));
  draft.categories.add("productivity");
  assert.deepEqual(countPlatforms(microsoft, draft), new Map());
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, draft)).length, 1);
});
