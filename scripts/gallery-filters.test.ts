import assert from "node:assert/strict";
import { test } from "node:test";
import {
  copyGalleryFilters, countFacet, galleryFilterParams, matchesFilters, parseGalleryFilters,
  type FilterableSubmission, type GalleryFilters,
} from "../src/lib/gallery-filters";
import { PLATFORMS } from "../src/lib/skills";
import { authorKey } from "../src/lib/badges";

const filters: GalleryFilters = {
  query: "", platforms: new Set(), type: "", tags: new Set(), authors: new Set(),
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

test("fixed platforms retain the existing vocabulary and order", () => {
  assert.deepEqual(PLATFORMS, ["Cowork", "Copilot Studio", "Scout"]);
});

for (let mask = 0; mask < 1 << PLATFORMS.length; mask++) {
  const platforms = new Set(PLATFORMS.filter((_, index) => mask & (1 << index)));
  test(`platform subset ${mask} matches a union without duplicates and round-trips`, () => {
    const selected = { ...filters, platforms };
    const expected = items.filter((item) => !platforms.size || [...platforms].some((platform) => item.platforms.includes(platform)));
    const matched = items.filter((item) => matchesFilters(item, selected));
    assert.deepEqual(matched, expected);
    assert.equal(new Set(matched).size, matched.length);
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(selected)), selected);
  });
}

test("platforms, tags and contributors OR within facets and AND across facets", () => {
  const selected: GalleryFilters = {
    query: "NEGOTIATION",
    platforms: new Set(["Scout", "Cowork"]), type: "skill",
    tags: new Set(["missing", "BATNA"]),
    authors: new Set(["missing", "ada-example"]),
  };
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [submission]);
  for (const changed of [
    { platforms: new Set(["Scout"]) }, { type: "plugin" }, { tags: new Set(["reports"]) },
    { authors: new Set(["bea"]) }, { query: "absent" },
  ]) {
    assert.equal(matchesFilters(submission, { ...selected, ...changed }), false);
  }
});

test("legacy singleton and comma-separated platform URLs retain type and other filters", () => {
  for (const platform of ["Copilot Studio", "Cowork,Scout", "Cowork,Copilot Studio,Scout"]) {
    const params = new URLSearchParams(`platform=${encodeURIComponent(platform)}&type=skill&tag=BATNA&author=Ada-Example`);
    const parsed = parseGalleryFilters(params);
    assert.deepEqual([...parsed.platforms], platform.split(","));
    assert.equal(parsed.type, "skill");
    assert.deepEqual([...parsed.tags], ["BATNA"]);
    assert.deepEqual([...parsed.authors], ["ada-example"]);
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
  }
});

test("query parsing trims and deduplicates selections without changing tag case", () => {
  const parsed = parseGalleryFilters(new URLSearchParams({
    platform: " Cowork,Scout,Cowork, ", tag: "BATNA, ZOPA, BATNA, ",
    author: "ADA-EXAMPLE, ada-example, ", q: "NEGOTIATION",
  }));
  assert.deepEqual([...parsed.platforms], ["Cowork", "Scout"]);
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
    ...filters, query: "reports", platforms: new Set(["Scout"]),
    type: "skill", tags: new Set(["reports"]), authors: new Set(["cy"]),
  });
  const original = galleryFilterParams(applied).toString();
  const draft = copyGalleryFilters(applied);
  draft.tags.clear();
  draft.authors.add("bea");
  draft.platforms.add("Cowork");
  draft.type = "automation";
  assert.equal(galleryFilterParams(applied).toString(), original);
  const committed = copyGalleryFilters(draft);
  draft.tags.add("business");
  assert.equal(committed.tags.size, 0);
  assert.deepEqual([...committed.platforms], ["Scout", "Cowork"]);
});

test("clearing extra draft filters retains platforms and search", () => {
  const draft = copyGalleryFilters({
    ...filters, query: "reports", platforms: new Set(["Cowork", "Scout"]),
    type: "plugin", tags: new Set(["reports"]), authors: new Set(["bea"]),
  });
  draft.type = "";
  draft.tags.clear();
  draft.authors.clear();
  assert.equal(draft.query, "reports");
  assert.deepEqual([...draft.platforms], ["Cowork", "Scout"]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, draft)), [items[1], items[2], items[3]]);
});

test("facet counts respect platform union, query and other facets, counting each item once", () => {
  const selected = { ...filters, platforms: new Set(["Cowork", "Scout"]), query: "report" };
  assert.deepEqual(countFacet(items, selected, "tags"), new Map([["reports", 3], ["business", 1]]));
  assert.deepEqual(countFacet(items, selected, "authors"), new Map([["bea", 2], ["cy", 1]]));
  assert.deepEqual(countFacet(items, selected, "type"), new Map([["automation", 1], ["plugin", 1], ["skill", 1]]));
  const refined = { ...selected, type: "plugin", tags: new Set(["business"]), authors: new Set(["bea"]) };
  assert.deepEqual(countFacet(items, refined, "tags"), new Map([["reports", 1], ["business", 1]]));
  assert.deepEqual(countFacet(items, refined, "authors"), new Map([["bea", 1]]));
  assert.deepEqual(countFacet([{ ...submission, tags: ["BATNA", "BATNA"] }], filters, "tags"), new Map([["BATNA", 1]]));
});

test("empty filters show the full catalog and serialize without query parameters", () => {
  assert.deepEqual(parseGalleryFilters(new URLSearchParams()), filters);
  assert.equal(galleryFilterParams(filters).toString(), "");
  assert.equal(items.filter((item) => matchesFilters(item, filters)).length, items.length);
});

test("unknown selections produce explicit no-results state rather than silently widening filters", () => {
  for (const params of ["platform=Unknown", "type=unknown", "tag=unknown", "author=unknown", "q=not-a-result"]) {
    assert.equal(items.filter((item) => matchesFilters(item, parseGalleryFilters(new URLSearchParams(params)))).length, 0);
  }
});
