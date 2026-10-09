import assert from "node:assert/strict";
import { test } from "node:test";
import {
  copyGalleryFilters, countFacet, FORMAT_LABELS, galleryFilterParams, matchesFilters, parseGalleryFilters,
  type FilterableSubmission, type GalleryFilters,
} from "../src/lib/gallery-filters";
import { PLATFORMS } from "../src/lib/skills";
import { authorKey } from "../src/lib/badges";

const filters: GalleryFilters = {
  query: "", platform: "", types: new Set(), tags: new Set(), authors: new Set(),
};
const submission: FilterableSubmission = {
  name: "Negotiation coach",
  description: "Prepare a negotiation strategy",
  tags: ["BATNA", "ZOPA", "business"],
  platforms: ["Cowork", "Copilot Studio"],
  type: "skill",
  authorName: "Ada Example",
  authorLogin: "ada-example",
  authorKey: "ada-example",
};
const items: FilterableSubmission[] = [
  submission,
  { ...submission, name: "Daily reports", platforms: ["Scout"], type: "automation", tags: ["reports"], authorKey: "bea" },
  { ...submission, name: "Report plugin", platforms: ["Cowork"], type: "plugin", tags: ["reports", "business"], authorKey: "bea" },
  { ...submission, name: "Report writer", platforms: ["Copilot Studio", "Scout"], tags: ["reports"], authorKey: "cy" },
];

const formats = Object.keys(FORMAT_LABELS);
const combinations = Array.from({ length: 7 }, (_, index) =>
  PLATFORMS.filter((_, bit) => (index + 1) & (1 << bit)),
).flatMap((platforms) => formats.map((type) => ({ ...submission, platforms, type })));

test("fixed platforms and formats retain the existing vocabulary and order", () => {
  assert.deepEqual(PLATFORMS, ["Cowork", "Copilot Studio", "Scout"]);
  assert.deepEqual(Object.entries(FORMAT_LABELS), [
    ["skill", "Skills"], ["plugin", "Plugins"], ["automation", "Automations"],
  ]);
});

for (const platform of ["", ...PLATFORMS] as const) {
  for (let mask = 0; mask < 8; mask++) {
    const types = new Set(formats.filter((_, index) => mask & (1 << index)));
    test(`platform ${platform || "All"} and format subset ${mask} match exactly`, () => {
      const selected = { ...filters, platform, types };
      const expected = combinations.filter((item) =>
        (!platform || item.platforms.includes(platform)) && (!types.size || types.has(item.type)),
      );
      const matched = combinations.filter((item) => matchesFilters(item, selected));
      assert.deepEqual(matched, expected);
      assert.equal(new Set(matched).size, matched.length);
      assert.equal(matched.length, (platform ? 4 : 7) * (types.size || 3));
      assert.deepEqual(parseGalleryFilters(galleryFilterParams(selected)), selected);
    });
  }
}

test("an empty group is unrestricted while selections in the other group still filter", () => {
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platform: "Cowork",
  })), [items[0], items[2]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, types: new Set(["skill"]),
  })), [items[0], items[3]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platform: "Cowork", types: new Set(["skill"]),
  })), [items[0]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platform: "Scout", types: new Set(["automation"]),
  })), [items[1]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, types: new Set(["plugin", "automation"]),
  })), [items[1], items[2]]);
});

test("search, tags and contributors AND-narrow all 32 platform/format combinations", () => {
  for (const platform of ["", ...PLATFORMS] as const) {
    for (let mask = 0; mask < 8; mask++) {
      const types = new Set(formats.filter((_, index) => mask & (1 << index)));
      for (const narrowing of [
        { query: "report" },
        { tags: new Set(["missing", "reports"]) },
        { authors: new Set(["bea", "missing"]) },
        { query: "report", tags: new Set(["reports", "missing"]), authors: new Set(["bea", "cy"]) },
      ]) {
        const expected = items.filter((item) => (!platform || item.platforms.includes(platform)) &&
          (!types.size || types.has(item.type)) &&
          (!narrowing.query || item.name.toLowerCase().includes(narrowing.query)) &&
          (!narrowing.tags || item.tags.includes("reports")) &&
          (!narrowing.authors || narrowing.authors.has(item.authorKey)));
        assert.deepEqual(items.filter((item) => matchesFilters(item, {
          ...filters, platform, types, ...narrowing,
        })), expected, `${platform || "All"} / subset ${mask}`);
      }
    }
  }
});

test("tags and contributors retain internal OR but cannot widen fixed group matches", () => {
  const selected: GalleryFilters = {
    query: "NEGOTIATION",
    platform: "Cowork", types: new Set(["skill"]),
    tags: new Set(["missing", "BATNA"]),
    authors: new Set(["missing", "ada-example"]),
  };
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [submission]);
  for (const changed of [
    { platform: "Scout", types: new Set(["plugin"]) }, { tags: new Set(["reports"]) },
    { authors: new Set(["bea"]) }, { query: "absent" },
  ] satisfies Partial<GalleryFilters>[]) {
    assert.equal(matchesFilters(submission, { ...selected, ...changed }), false);
  }
});

test("single-platform and multi-format URLs round-trip with other filters", () => {
  for (const platform of ["", ...PLATFORMS]) {
    for (const type of ["skill", "plugin,automation", "skill,plugin,automation"]) {
      const params = new URLSearchParams(`platform=${encodeURIComponent(platform)}&type=${type}&tag=BATNA&author=Ada-Example`);
      const parsed = parseGalleryFilters(params);
      assert.equal(parsed.platform, platform);
      assert.deepEqual([...parsed.types], type.split(","));
      assert.deepEqual([...parsed.tags], ["BATNA"]);
      assert.deepEqual([...parsed.authors], ["ada-example"]);
      assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
    }
  }
  const legacy = parseGalleryFilters(new URLSearchParams("type=skill"));
  assert.deepEqual([...legacy.types], ["skill"]);
  assert.equal(legacy.platform, "");
  assert.equal(galleryFilterParams(legacy).toString(), "type=skill");
});

test("legacy platform unions normalize to All or the first valid choice without changing formats", () => {
  for (const [legacy, platform] of [
    ["Cowork,Scout", "Cowork"],
    ["Scout,Cowork", "Scout"],
    ["Unknown, Copilot Studio,Scout,Copilot Studio", "Copilot Studio"],
    [" Cowork, Scout, Cowork, ", "Cowork"],
    ["Cowork,Copilot Studio,Scout", ""],
    ["Scout,Unknown,Cowork,Scout,Copilot Studio", ""],
    ["Unknown", ""],
    [" ,Unknown, ", ""],
    ["", ""],
  ]) {
    const parsed = parseGalleryFilters(new URLSearchParams({
      platform: legacy, type: "automation,plugin,skill", q: "REPORT",
      tag: "BATNA,ZOPA", author: "Ada-Example", sort: "updated",
    }));
    assert.equal(parsed.platform, platform, legacy);
    assert.equal(galleryFilterParams(parsed).get("platform"), platform || null);
    assert.deepEqual([...parsed.types], ["automation", "plugin", "skill"]);
    assert.equal(parsed.query, "report");
    assert.deepEqual([...parsed.tags], ["BATNA", "ZOPA"]);
    assert.deepEqual([...parsed.authors], ["ada-example"]);
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
  }
});

test("query parsing trims and deduplicates selections without changing tag case", () => {
  const parsed = parseGalleryFilters(new URLSearchParams({
    platform: " Cowork,Scout,Cowork, ", type: " Skill,plugin,SKILL, ", tag: "BATNA, ZOPA, BATNA, ",
    author: "ADA-EXAMPLE, ada-example, ", q: "NEGOTIATION",
  }));
  assert.equal(parsed.platform, "Cowork");
  assert.deepEqual([...parsed.types], ["skill", "plugin"]);
  assert.deepEqual([...parsed.tags], ["BATNA", "ZOPA"]);
  assert.deepEqual([...parsed.authors], ["ada-example"]);
  assert.equal(parsed.query, "negotiation");
  assert.ok(matchesFilters(submission, parsed));
});

test("encoded tag and contributor gallery links round-trip under the Pages base", () => {
  for (const tag of ["BATNA", "ZOPA", "R&D / planning", "résumé", "C++"]) {
    const href = `/cat-agent-skills/?tag=${encodeURIComponent(tag)}`;
    const parsed = parseGalleryFilters(new URL(href, "https://example.test").searchParams);
    assert.deepEqual([...parsed.tags], [tag]);
    assert.ok(matchesFilters({ ...submission, tags: [tag] }, parsed));
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
  }
  for (const [login, name] of [["Ada-Example", "Ada Example"], [undefined, "Renée O'Neil & Co."]] as const) {
    const key = authorKey(login, name);
    const href = `/cat-agent-skills/?author=${encodeURIComponent(key)}`;
    const parsed = parseGalleryFilters(new URL(href, "https://example.test").searchParams);
    assert.deepEqual([...parsed.authors], [key]);
    assert.ok(matchesFilters({ ...submission, authorKey: key }, parsed));
  }
});

test("tags remain case-sensitive while search includes uppercase tags case-insensitively", () => {
  assert.ok(matchesFilters(submission, { ...filters, tags: new Set(["BATNA"]) }));
  assert.equal(matchesFilters(submission, { ...filters, tags: new Set(["batna"]) }), false);
  for (const query of ["batna", "ZOPA", " Negotiation ", "ADA EXAMPLE", "Ada-Example", "strategy", "skills"]) {
    assert.ok(matchesFilters(submission, { ...filters, query }), query);
  }
});

test("search recognizes every singular and plural format", () => {
  for (const type of ["skill", "plugin", "automation"]) {
    for (const query of [type, `${type}s`, ` ${type.toUpperCase()}S `]) {
      assert.ok(matchesFilters({ ...submission, type }, { ...filters, query }));
    }
  }
});

test("draft selections are independent from applied selections until copied back", () => {
  const applied = copyGalleryFilters({
    ...filters, query: "reports", platform: "Scout",
    types: new Set(["skill"]), tags: new Set(["reports"]), authors: new Set(["cy"]),
  });
  const original = galleryFilterParams(applied).toString();
  const draft = copyGalleryFilters(applied);
  draft.tags.clear();
  draft.authors.add("bea");
  draft.platform = "Cowork";
  draft.types.add("automation");
  assert.equal(galleryFilterParams(applied).toString(), original);
  const committed = copyGalleryFilters(draft);
  draft.tags.add("business");
  assert.equal(committed.tags.size, 0);
  assert.equal(committed.platform, "Cowork");
  assert.deepEqual([...committed.types], ["skill", "automation"]);
  draft.types.clear();
  assert.equal(committed.types.size, 2);
});

test("clearing extra draft filters retains platform, format selections and search", () => {
  const draft = copyGalleryFilters({
    ...filters, query: "report", platform: "Cowork",
    types: new Set(["plugin"]), tags: new Set(["reports"]), authors: new Set(["bea"]),
  });
  draft.tags.clear();
  draft.authors.clear();
  assert.equal(draft.query, "report");
  assert.equal(draft.platform, "Cowork");
  assert.deepEqual([...draft.types], ["plugin"]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, draft)), [items[2]]);
});

test("facet counts respect platform/formats, query and other facets, counting each item once", () => {
  const selected: GalleryFilters = { ...filters, platform: "Cowork", types: new Set(["skill", "plugin"]), query: "report" };
  assert.deepEqual(countFacet(items, selected, "tags"), new Map([["reports", 1], ["business", 1]]));
  assert.deepEqual(countFacet(items, selected, "authors"), new Map([["bea", 1]]));
  const refined = { ...selected, tags: new Set(["business"]), authors: new Set(["bea"]) };
  assert.deepEqual(countFacet(items, refined, "tags"), new Map([["reports", 1], ["business", 1]]));
  assert.deepEqual(countFacet(items, refined, "authors"), new Map([["bea", 1]]));
  assert.deepEqual(countFacet([{ ...submission, tags: ["BATNA", "BATNA"] }], filters, "tags"), new Map([["BATNA", 1]]));
});

test("empty filters show the full catalog and serialize without query parameters", () => {
  assert.deepEqual(parseGalleryFilters(new URLSearchParams()), filters);
  assert.equal(galleryFilterParams(filters).toString(), "");
  assert.equal(items.filter((item) => matchesFilters(item, filters)).length, items.length);
});

test("unknown platforms select All, while other unknown selections retain no-results behavior", () => {
  assert.deepEqual(parseGalleryFilters(new URLSearchParams("platform=Unknown")), filters);
  for (const params of ["type=unknown", "tag=unknown", "author=unknown", "q=not-a-result"]) {
    assert.equal(items.filter((item) => matchesFilters(item, parseGalleryFilters(new URLSearchParams(params)))).length, 0);
  }
});
