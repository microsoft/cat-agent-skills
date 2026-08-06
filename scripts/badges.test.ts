import assert from "node:assert/strict";
import test from "node:test";
import {
  BADGES,
  computeStats,
  downloadLeaderLogins,
  posterTiles,
  resolveBadges,
  type BadgeSkill,
} from "../src/lib/badges";

const skill = (
  slug: string,
  authorGithub: string,
  downloads: number,
  extra: Partial<BadgeSkill> = {},
): BadgeSkill => ({
  slug,
  name: slug,
  authorGithub,
  downloads,
  ...extra,
});

test("aggregates contributor downloads across skills", () => {
  const stats = computeStats("Ada", [
    skill("one", "ada", 120),
    skill("two", "@ADA", 80),
    skill("other", "grace", 999),
  ]);
  assert.equal(stats.totalDownloads, 200);
  assert.equal(stats.avgDownloads, 100);
});

test("selects exactly three download leaders with deterministic ties", () => {
  const skills = [
    skill("a", "zeta", 50),
    skill("b", "alpha", 50),
    skill("c", "beta", 50),
    skill("d", "gamma", 49),
  ];
  assert.deepEqual([...downloadLeaderLogins(skills)], ["alpha", "beta", "zeta"]);
});

test("returns every earned badge instead of suppressing lower badges", () => {
  const skills = Array.from({ length: 5 }, (_, index) =>
    skill(`ada-${index}`, "ada", 100, {
      featured: index === 0,
      rating: 10,
    }),
  );
  const ids = resolveBadges("ada", skills).map(({ badge }) => badge.id);
  assert.deepEqual(ids, [
    "skill-factory",
    "teachers-pet",
    "shelf-clearer",
    "top-rated",
    "house-cat",
  ]);
});

test("Shelf Clearer evidence leads with downloads", () => {
  const stats = computeStats("ada", [skill("one", "ada", 1234)]);
  assert.deepEqual(posterTiles(BADGES["shelf-clearer"], stats)[0], {
    num: "1,234",
    label: "downloads",
  });
});
