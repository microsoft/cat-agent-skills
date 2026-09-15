import { test } from "node:test";
import assert from "node:assert/strict";
import { CATEGORIES, CATEGORY_LABELS, isCategory } from "../src/lib/categories.ts";
import { categorySubmissions, countPlatforms, matchesFilters, partitionSubmissions, type FilterableSubmission, type GalleryFilters } from "../src/lib/gallery-filters.ts";
import { skillSchema } from "../src/lib/skill-schema.ts";

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
  query: "", category: "", platform: "", type: "",
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

test("category collections include every matching submission and keep publisher sections separate", () => {
  const items = CATEGORIES.flatMap((category) =>
    ["skill", "plugin", "automation"].flatMap((type) =>
      [true, false, undefined].map((builtByMicrosoft) => ({
        data: { category, type, builtByMicrosoft },
      })),
    ),
  );
  for (const category of CATEGORIES) {
    const { microsoft, community } = categorySubmissions(items, category);
    assert.equal(microsoft.length, 3);
    assert.equal(community.length, 6);
    assert.deepEqual(
      new Set([...microsoft, ...community]),
      new Set(items.filter((item) => item.data.category === category)),
    );
  }
});

test("category collections support a missing publisher and completely empty categories", () => {
  const microsoft = { data: { category: "manufacturing" as const, builtByMicrosoft: true } };
  const community = { data: { category: "productivity" as const } };
  const items = Object.freeze([microsoft, community]);
  assert.deepEqual(categorySubmissions(items, "manufacturing"), { microsoft: [microsoft], community: [] });
  assert.deepEqual(categorySubmissions(items, "productivity"), { microsoft: [], community: [community] });
  assert.deepEqual(categorySubmissions(items, "retail-cpg"), { microsoft: [], community: [] });
  for (const category of CATEGORIES) {
    assert.deepEqual(categorySubmissions([], category), { microsoft: [], community: [] });
  }
});

test("shared filters match both sections identically", () => {
  const items = [true, false].map((builtByMicrosoft) => ({
    ...submission, builtByMicrosoft, data: { builtByMicrosoft },
  }));
  for (const section of Object.values(partitionSubmissions(items))) {
    assert.equal(section.filter((item) => matchesFilters(item, filters)).length, 1);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, category: "manufacturing" })).length, 1);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, category: "retail-cpg" })).length, 0);
    assert.equal(section.filter((item) => matchesFilters(item, { ...filters, platform: "Scout" })).length, 0);
  }
});

test("filters AND facets and OR selections within tags and contributors", () => {
  const selected: GalleryFilters = {
    ...filters, category: "manufacturing", platform: "Cowork", type: "plugin",
    tags: new Set(["not-present", "quality"]),
    authors: new Set(["not-present", "sravaniseethi"]),
    query: "NONCONFORMANCE",
  };
  assert.ok(matchesFilters(submission, selected));
  for (const changed of [
    { category: "productivity" as const },
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

test("platform counts honor each other filter facet", () => {
  const cases: Array<{ selected: Partial<GalleryFilters>; expected: Array<[string, number]> }> = [
    { selected: { query: "WRITING" }, expected: [["Cowork", 1], ["Copilot Studio", 1]] },
    { selected: { query: "Microsoft" }, expected: [["Cowork", 1]] },
    { selected: { category: "manufacturing" }, expected: [["Cowork", 1], ["Scout", 1]] },
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
    query: "inspection", category: "manufacturing", platform: "Copilot Studio", type: "plugin",
    tags: new Set(["absent", "quality"]), authors: new Set(["absent", "sravaniseethi"]),
  };
  assert.equal(platformSubmissions.filter((item) => matchesFilters(item, selected)).length, 0);
  assert.deepEqual(countPlatforms(platformSubmissions, selected), new Map([["Cowork", 1]]));
});

test("platform counts handle empty collections and no matches", () => {
  assert.deepEqual(countPlatforms([], filters), new Map());
  assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, query: "not present" }), new Map());
  assert.deepEqual(countPlatforms(platformSubmissions, { ...filters, category: "retail-cpg" }), new Map());
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
