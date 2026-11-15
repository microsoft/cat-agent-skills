import assert from "node:assert/strict";
import { test } from "node:test";
import {
  copyGalleryFilters, countFacet, FORMAT_LABELS, galleryFilterParams, matchesFilters, parseGalleryFilters, sameGalleryFilters,
  type FilterableSubmission, type GalleryFilters,
} from "../src/lib/gallery-filters";
import { PLATFORMS } from "../src/lib/skills";
import { authorKey } from "../src/lib/badges";
import { CATEGORIES } from "../src/lib/categories";

const filters: GalleryFilters = {
  query: "", platforms: new Set(), categories: new Set(), types: new Set(), tags: new Set(), authors: new Set(),
};

for (const field of ["platforms", "categories", "types", "tags", "authors"] as const) {
  for (const clear of [false, true]) {
    test(`${field} ${clear ? "clear/reselect" : "off/on"} is a semantic no-op without changing selection order`, () => {
      const applied = copyGalleryFilters(parseGalleryFilters(new URLSearchParams(
        "q=skill&platform=Cowork,Scout&category=manufacturing,retail-cpg&type=skill,automation&tag=BATNA,ZOPA&author=ada,bea",
      )));
      const before = galleryFilterParams(applied).toString();
      const draft = copyGalleryFilters(applied);
      const [first, second] = [...draft[field]];
      if (clear) {
        draft[field].clear();
        draft[field].add(second);
      } else {
        draft[field].delete(first);
      }
      draft[field].add(first);
      assert.notDeepEqual([...draft[field]], [...applied[field]]);
      assert.equal(sameGalleryFilters(applied, draft), true);
      assert.equal(sameGalleryFilters(draft, applied), true);
      assert.equal(galleryFilterParams(applied).toString(), before);
    });
  }

  test(`${field} additions, removals and equal-size replacements are genuine changes`, () => {
    const applied = { ...filters, [field]: new Set(["first", "second"]) };
    for (const values of [["first"], ["first", "second", "third"], ["first", "third"], []]) {
      const draft = { ...applied, [field]: new Set(values) };
      assert.equal(sameGalleryFilters(applied, draft), false);
      assert.equal(sameGalleryFilters(draft, applied), false);
    }
  });
}

test("semantic filter equality compares query and products and accepts independent empty drafts", () => {
  assert.equal(sameGalleryFilters(filters, copyGalleryFilters(filters)), true);
  assert.equal(sameGalleryFilters(filters, { ...filters, query: "skill" }), false);
  assert.equal(sameGalleryFilters(filters, { ...filters, platforms: new Set(["Cowork"]) }), false);
});

const submission: FilterableSubmission = {
  name: "Negotiation coach",
  description: "Prepare a negotiation strategy",
  tags: ["BATNA", "ZOPA", "business"],
  platforms: ["Cowork", "Copilot Studio"],
  type: "skill",
  category: "productivity",
  builtByMicrosoft: false,
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
const platformSelections = Array.from({ length: 1 << PLATFORMS.length }, (_, mask) =>
  new Set(PLATFORMS.filter((_, bit) => mask & (1 << bit))),
);
const combinations = Array.from({ length: 7 }, (_, index) =>
  PLATFORMS.filter((_, bit) => (index + 1) & (1 << bit)),
).flatMap((platforms) => formats.map((type) => ({ ...submission, platforms, type })));

test("platform and format choices retain the existing vocabulary and order", () => {
  assert.deepEqual(PLATFORMS, ["Cowork", "Copilot Studio", "Scout"]);
  assert.deepEqual(Object.entries(FORMAT_LABELS), [
    ["skill", "Skills"], ["plugin", "Plugins"], ["automation", "Automations"],
  ]);
});

for (const platforms of platformSelections) {
  for (let mask = 0; mask < 8; mask++) {
    const types = new Set(formats.filter((_, index) => mask & (1 << index)));
    test(`products ${[...platforms].join(" or ") || "All"} and format subset ${mask} match exactly`, () => {
      const selected = { ...filters, platforms, types };
      const expected = combinations.filter((item) =>
        (!platforms.size || [...platforms].some((platform) => item.platforms.includes(platform))) &&
        (!types.size || types.has(item.type)),
      );
      const matched = combinations.filter((item) => matchesFilters(item, selected));
      assert.deepEqual(matched, expected);
      assert.equal(new Set(matched).size, matched.length);
      assert.equal(matched.length, (platforms.size ? 8 - 2 ** (3 - platforms.size) : 7) * (types.size || 3));
      assert.deepEqual(parseGalleryFilters(galleryFilterParams(selected)), selected);
    });
  }
}

test("an empty group is unrestricted while selections in the other group still filter", () => {
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platforms: new Set(["Cowork"]),
  })), [items[0], items[2]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, types: new Set(["skill"]),
  })), [items[0], items[3]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platforms: new Set(["Cowork"]), types: new Set(["skill"]),
  })), [items[0]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, platforms: new Set(["Scout"]), types: new Set(["automation"]),
  })), [items[1]]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, types: new Set(["plugin", "automation"]),
  })), [items[1], items[2]]);
});

test("search, tags and contributors AND-narrow all 64 product/format combinations", () => {
  for (const platforms of platformSelections) {
    for (let mask = 0; mask < 8; mask++) {
      const types = new Set(formats.filter((_, index) => mask & (1 << index)));
      for (const narrowing of [
        { query: "report" },
        { tags: new Set(["reports"]) },
        { tags: new Set(["reports", "business"]) },
        { tags: new Set(["missing", "reports"]) },
        { authors: new Set(["bea"]) },
        { authors: new Set(["missing"]) },
        { authors: new Set(["bea", "cy"]) },
        { query: "report", tags: new Set(["reports", "business"]), authors: new Set(["bea"]) },
      ]) {
        const expected = items.filter((item) => (!platforms.size || [...platforms].some((platform) => item.platforms.includes(platform))) &&
          (!types.size || types.has(item.type)) &&
          (!narrowing.query || item.name.toLowerCase().includes(narrowing.query)) &&
          (!narrowing.tags || [...narrowing.tags].every((tag) => item.tags.includes(tag))) &&
          (!narrowing.authors || [...narrowing.authors].every((author) => author === item.authorKey)));
        assert.deepEqual(items.filter((item) => matchesFilters(item, {
          ...filters, platforms, types, ...narrowing,
        })), expected, `${[...platforms].join(" or ") || "All"} / subset ${mask}`);
      }
    }
  }
});

test("tags and contributors require every selected value", () => {
  const selected: GalleryFilters = {
    query: "NEGOTIATION",
    categories: new Set(),
    platforms: new Set(["Cowork"]), types: new Set(["skill"]),
    tags: new Set(["BATNA", "ZOPA"]),
    authors: new Set(["ada-example"]),
  };
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [submission]);
  for (const changed of [
    { platforms: new Set(["Scout"]), types: new Set(["plugin"]) }, { tags: new Set(["BATNA", "missing"]) },
    { authors: new Set(["ada-example", "bea"]) }, { query: "absent" },
  ] satisfies Partial<GalleryFilters>[]) {
    assert.equal(matchesFilters(submission, { ...selected, ...changed }), false);
  }
});

test("adding tags never widens matches and tag counts reflect the existing intersection", () => {
  const tags = ["BATNA", "ZOPA", "business", "reports", "missing"];
  for (let mask = 0; mask < 1 << tags.length; mask++) {
    const selected = { ...filters, tags: new Set(tags.filter((_, bit) => mask & (1 << bit))) };
    const before = items.filter((item) => matchesFilters(item, selected));
    const counts = countFacet(items, selected, "tags");
    for (const tag of tags) {
      const narrowed = { ...selected, tags: new Set([...selected.tags, tag]) };
      const after = items.filter((item) => matchesFilters(item, narrowed));
      assert.deepEqual(after, before.filter((item) => item.tags.includes(tag)));
      assert.equal(counts.get(tag) ?? 0, after.length);
    }
  }
  assert.deepEqual(items.filter((item) => matchesFilters(item, {
    ...filters, tags: new Set(["BATNA", "ZOPA"]),
  })), [submission]);
  assert.equal(items.filter((item) => matchesFilters(item, {
    ...filters, tags: new Set(["BATNA", "reports"]),
  })).length, 0);
});

test("single-product and multi-product URLs round-trip with multi-format and other filters", () => {
  for (const platforms of platformSelections) {
    for (const type of ["skill", "plugin,automation", "skill,plugin,automation"]) {
      const params = new URLSearchParams(`platform=${encodeURIComponent([...platforms].join(","))}&type=${type}&tag=BATNA&author=Ada-Example`);
      const parsed = parseGalleryFilters(params);
      assert.deepEqual(parsed.platforms, platforms);
      assert.deepEqual([...parsed.types], type.split(","));
      assert.deepEqual([...parsed.tags], ["BATNA"]);
      assert.deepEqual([...parsed.authors], ["ada-example"]);
      assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
    }
  }
  const legacy = parseGalleryFilters(new URLSearchParams("type=skill"));
  assert.deepEqual([...legacy.types], ["skill"]);
  assert.equal(legacy.platforms.size, 0);
  assert.equal(galleryFilterParams(legacy).toString(), "type=skill");
});

test("platform unions retain all valid choices without changing formats", () => {
  for (const [legacy, platforms] of [
    ["Cowork,Scout", ["Cowork", "Scout"]],
    ["Scout,Cowork", ["Scout", "Cowork"]],
    ["Unknown, Copilot Studio,Scout,Copilot Studio", ["Copilot Studio", "Scout"]],
    [" Cowork, Scout, Cowork, ", ["Cowork", "Scout"]],
    ["Cowork,Copilot Studio,Scout", ["Cowork", "Copilot Studio", "Scout"]],
    ["Scout,Unknown,Cowork,Scout,Copilot Studio", ["Scout", "Cowork", "Copilot Studio"]],
    ["Unknown", []],
    [" ,Unknown, ", []],
    ["", []],
  ] as const) {
    const parsed = parseGalleryFilters(new URLSearchParams({
      platform: legacy, type: "automation,plugin,skill", q: "REPORT",
      tag: "BATNA,ZOPA", author: "Ada-Example", sort: "updated",
    }));
    assert.deepEqual([...parsed.platforms], platforms, legacy);
    assert.equal(galleryFilterParams(parsed).get("platform"), platforms.join(",") || null);
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
  assert.deepEqual([...parsed.platforms], ["Cowork", "Scout"]);
  assert.deepEqual([...parsed.types], ["skill", "plugin"]);
  assert.deepEqual([...parsed.tags], ["BATNA", "ZOPA"]);
  assert.deepEqual([...parsed.authors], ["ada-example"]);
  assert.equal(parsed.query, "negotiation");
  assert.ok(matchesFilters(submission, parsed));
});

test("contributor CSV preserves every distinct value, including unknown contributors", () => {
  for (const [csv, authors] of [
    ["", []], [" , , ", []], ["Ada-Example", ["ada-example"]],
    [" , Bea,cy,BEA", ["bea", "cy"]], ["unknown,ada-example", ["unknown", "ada-example"]],
    ["CY,bea", ["cy", "bea"]],
  ] as const) {
    const parsed = parseGalleryFilters(new URLSearchParams({
      author: csv, platform: "Scout", type: "skill,automation", tag: "BATNA,ZOPA", q: "REPORT",
    }));
    assert.deepEqual([...parsed.authors], authors);
    assert.deepEqual([...parsed.platforms], ["Scout"]);
    assert.deepEqual([...parsed.types], ["skill", "automation"]);
    assert.deepEqual([...parsed.tags], ["BATNA", "ZOPA"]);
    assert.equal(parsed.query, "report");
    assert.equal(galleryFilterParams(parsed).get("author"), authors.join(",") || null);
    assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
  }
  assert.equal(items.filter((item) => matchesFilters(item, parseGalleryFilters(
    new URLSearchParams("author=unknown,ada-example"),
  ))).length, 0);
});

test("removing contributors recovers from an empty intersection without clearing other filters", () => {
  const selected = copyGalleryFilters({
    ...filters, platforms: new Set(["Scout"]), types: new Set(["skill", "automation"]),
    tags: new Set(["reports"]), query: "report", authors: new Set(["bea"]),
  });
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [items[1]]);
  assert.deepEqual(countFacet(items, selected, "authors"), new Map([["bea", 1]]));
  selected.authors.add("cy");
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), []);
  assert.deepEqual(countFacet(items, selected, "authors"), new Map());
  selected.authors.delete("bea");
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [items[3]]);
  selected.authors.clear();
  assert.deepEqual(items.filter((item) => matchesFilters(item, selected)), [items[1], items[3]]);
  assert.deepEqual([...selected.platforms], ["Scout"]);
  assert.deepEqual([...selected.types], ["skill", "automation"]);
  assert.deepEqual([...selected.tags], ["reports"]);
  assert.equal(selected.query, "report");
});

test("contributor intersections and option counts narrow monotonically without inventing co-attribution", () => {
  const authors = ["ada-example", "bea", "cy", "unknown"];
  for (const platforms of platformSelections) {
    for (let mask = 0; mask < 1 << authors.length; mask++) {
      const selected = { ...filters, platforms, authors: new Set(authors.filter((_, bit) => mask & (1 << bit))) };
      const before = items.filter((item) => matchesFilters(item, selected));
      const counts = countFacet(items, selected, "authors");
      if (selected.authors.size > 1) assert.equal(before.length, 0);
      for (const author of authors) {
        const narrowed = { ...selected, authors: new Set([...selected.authors, author]) };
        const after = items.filter((item) => matchesFilters(item, narrowed));
        assert.deepEqual(after, before.filter((item) => item.authorKey === author));
        assert.equal(counts.get(author) ?? 0, after.length);
      }
    }
  }
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
    types: new Set(["skill"]), tags: new Set(["reports"]), authors: new Set(["cy"]),
  });
  const original = galleryFilterParams(applied).toString();
  const draft = copyGalleryFilters(applied);
  draft.tags.clear();
  draft.authors.add("bea");
  draft.platforms.delete("Scout");
  draft.platforms.add("Cowork");
  draft.types.add("automation");
  assert.equal(galleryFilterParams(applied).toString(), original);
  assert.deepEqual([...applied.authors], ["cy"]);
  const committed = copyGalleryFilters(draft);
  draft.tags.add("business");
  assert.equal(committed.tags.size, 0);
  assert.deepEqual([...committed.platforms], ["Cowork"]);
  assert.deepEqual([...applied.platforms], ["Scout"]);
  draft.platforms.clear();
  assert.deepEqual([...committed.platforms], ["Cowork"]);
  assert.deepEqual([...committed.authors], ["cy", "bea"]);
  assert.deepEqual([...committed.types], ["skill", "automation"]);
  draft.types.clear();
  assert.equal(committed.types.size, 2);
  draft.authors.clear();
  assert.equal(committed.authors.size, 2);
});

test("clearing extra draft filters clears formats, tags and authors but retains the product union and search", () => {
  const draft = copyGalleryFilters({
    ...filters, query: "report", platforms: new Set(["Cowork", "Scout"]),
    types: new Set(["automation"]), tags: new Set(["reports"]), authors: new Set(["bea", "cy"]),
  });
  draft.types.clear();
  draft.tags.clear();
  draft.authors.clear();
  assert.equal(draft.query, "report");
  assert.deepEqual([...draft.platforms], ["Cowork", "Scout"]);
  assert.equal(draft.types.size, 0);
  assert.deepEqual(items.filter((item) => matchesFilters(item, draft)), [items[1], items[2], items[3]]);
});

test("removing one applied format preserves remaining formats and all other filters", () => {
  const applied = copyGalleryFilters({
    ...filters, platforms: new Set(["Scout"]), query: "report", types: new Set(formats),
    tags: new Set(["reports"]), authors: new Set(["bea"]),
  });
  applied.types.delete("skill");
  assert.deepEqual([...applied.types], ["plugin", "automation"]);
  assert.deepEqual([...applied.platforms], ["Scout"]);
  assert.equal(applied.query, "report");
  assert.deepEqual([...applied.tags], ["reports"]);
  assert.deepEqual([...applied.authors], ["bea"]);
  assert.deepEqual(items.filter((item) => matchesFilters(item, applied)), [items[1]]);
  assert.deepEqual(parseGalleryFilters(galleryFilterParams(applied)), applied);
});

test("format counts omit only the format facet, respecting platform, search, tags and contributors", () => {
  const selected: GalleryFilters = {
    ...filters, platforms: new Set(["Scout"]), types: new Set(["plugin"]), query: "report",
    tags: new Set(["reports"]), authors: new Set(),
  };
  assert.deepEqual(countFacet(items, selected, "types"), new Map([["automation", 1], ["skill", 1]]));
  assert.deepEqual(countFacet(items, { ...selected, authors: new Set(["cy"]) }, "types"), new Map([["skill", 1]]));
  assert.deepEqual(countFacet(items, { ...selected, authors: new Set(["cy", "bea"]) }, "types"), new Map());
  assert.deepEqual(countFacet(items, { ...selected, tags: new Set(["business"]) }, "types"), new Map());
  assert.deepEqual(countFacet(items, { ...selected, query: "missing" }, "types"), new Map());
});

test("facet counts respect platform/formats, query and other facets, counting each item once", () => {
  const selected: GalleryFilters = { ...filters, platforms: new Set(["Cowork"]), types: new Set(["skill", "plugin"]), query: "report" };
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
  for (const params of ["category=unknown", "type=unknown", "tag=unknown", "author=unknown", "q=not-a-result"]) {
    assert.equal(items.filter((item) => matchesFilters(item, parseGalleryFilters(new URLSearchParams(params)))).length, 0);
  }
});

test("all category subsets use OR within categories and AND with every existing filter", () => {
  const catalog = CATEGORIES.flatMap((category) => items.map((item) => ({ ...item, category })));
  for (let mask = 0; mask < 1 << CATEGORIES.length; mask++) {
    const categories = new Set(CATEGORIES.filter((_, bit) => mask & (1 << bit)));
    for (const platforms of platformSelections) {
      for (const refinements of [
        {}, { types: new Set(["skill", "automation"]) },
        { tags: new Set(["reports", "business"]) }, { authors: new Set(["bea", "cy"]) },
        { query: "report", types: new Set(["plugin"]), tags: new Set(["business"]), authors: new Set(["bea"]) },
      ]) {
        const selected = { ...filters, platforms, categories, ...refinements };
        const withoutCategories = { ...selected, categories: new Set<string>() };
        const expected = catalog.filter((item) => (!categories.size || categories.has(item.category)) &&
          matchesFilters(item, withoutCategories));
        assert.deepEqual(catalog.filter((item) => matchesFilters(item, selected)), expected);
        assert.deepEqual(parseGalleryFilters(galleryFilterParams(selected)), selected);
        assert.equal(new Set(expected).size, expected.length);
      }
    }
  }
});

test("category URLs normalize case, preserve single-category links and deduplicate unions", () => {
  const parsed = parseGalleryFilters(new URLSearchParams("category=Manufacturing,retail-cpg,manufacturing&platform=Cowork&sort=updated"));
  assert.deepEqual([...parsed.categories], ["manufacturing", "retail-cpg"]);
  assert.deepEqual([...parsed.platforms], ["Cowork"]);
  assert.deepEqual(parseGalleryFilters(galleryFilterParams(parsed)), parsed);
  assert.deepEqual([...parseGalleryFilters(new URLSearchParams("category=manufacturing")).categories], ["manufacturing"]);
});

test("category drafts and extra-filter clearing leave the applied category union intact", () => {
  const applied = copyGalleryFilters({ ...filters, categories: new Set(["manufacturing", "retail-cpg"]) });
  const draft = copyGalleryFilters(applied);
  draft.categories.delete("manufacturing");
  assert.deepEqual([...applied.categories], ["manufacturing", "retail-cpg"]);
  assert.equal(sameGalleryFilters(applied, draft), false);
  draft.types.clear();
  draft.tags.clear();
  draft.authors.clear();
  assert.deepEqual([...draft.categories], ["retail-cpg"]);
});

test("Microsoft search and facet counts use the full selected category and product scope", () => {
  const industry = [
    { ...submission, category: "manufacturing", builtByMicrosoft: true, type: "plugin", platforms: ["Cowork"] },
    { ...submission, category: "retail-cpg", builtByMicrosoft: true, type: "plugin", platforms: ["Cowork"] },
    submission,
  ];
  const selected = { ...filters, query: "Microsoft", categories: new Set(["manufacturing", "retail-cpg"]) };
  assert.equal(industry.filter((item) => matchesFilters(item, selected)).length, 2);
  assert.deepEqual(countFacet(industry, selected, "types"), new Map([["plugin", 2]]));
  assert.equal(industry.filter((item) => matchesFilters(item, { ...selected, platforms: new Set(["Scout"]) })).length, 0);
  const union = { ...selected, platforms: new Set(["Cowork", "Scout"]) };
  assert.equal(industry.filter((item) => matchesFilters(item, union)).length, 2);
  assert.deepEqual(countFacet(industry, union, "types"), new Map([["plugin", 2]]));
  assert.deepEqual(countFacet(industry, { ...selected, categories: new Set(["manufacturing"]) }, "types"), new Map([["plugin", 1]]));
});
