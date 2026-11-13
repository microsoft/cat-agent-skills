import assert from "node:assert/strict";
import test from "node:test";
import { computeStats, directoryAuthors, resolveBadges, type BadgeSkill } from "../src/lib/badges";
import { contributorAvatar } from "../src/lib/contributor-avatar";
import { CATEGORIES, CATEGORY_COLORS, CATEGORY_ICON_PATHS, CATEGORY_LABELS } from "../src/lib/categories";
import { skillSchema } from "../src/lib/skill-schema";

const team = "Microsoft";

test("every category has a label, color, icon, and schema support", () => {
  assert.equal(new Set(CATEGORIES).size, 13);
  for (const category of CATEGORIES) {
    assert.ok(CATEGORY_LABELS[category]);
    assert.match(CATEGORY_COLORS[category], /^#[0-9a-f]{6}$/i);
    assert.ok(CATEGORY_ICON_PATHS[category]);
    assert.equal(skillSchema.parse({
      name: "Example", description: "Example", platforms: ["Cowork"],
      category, tags: ["example"], author: team,
    }).category, category);
  }
});

test("team directory entry aggregates all nineteen submissions without fabricating a login or badge", () => {
  const skills: BadgeSkill[] = Array.from({ length: 19 }, (_, index) => ({
    slug: `team-${index}`, name: `Team ${index}`, author: team,
    authorGithub: null, featured: false, createdAt: "2026-10-31",
  }));
  skills.push({ slug: "ada", name: "Ada's skill", author: "Ada", authorGithub: "ADA" });
  const authors = directoryAuthors(skills);
  assert.equal(authors.length, 2);
  assert.equal(authors[0].key, "microsoft");
  assert.equal(authors[0].login, "");
  assert.equal(authors[0].displayName, team);
  assert.equal(authors[0].skillCount, 19);
  assert.equal(authors[0].skills.length, 19);
  assert.equal(authors[1].key, "ada");
  assert.equal(computeStats("ada", skills).skillCount, 1);
  assert.equal(computeStats("microsoft", skills).skillCount, 0);
  assert.deepEqual(resolveBadges("microsoft", skills), []);
});

test("avatars come from GitHub logins and otherwise fall back to initials", () => {
  assert.equal(contributorAvatar(null, team), null);
  assert.equal(contributorAvatar("microsoft", team), "/microsoft.svg");
  assert.equal(contributorAvatar("@Microsoft", team), "/microsoft.svg");
  assert.equal(contributorAvatar("@Ada", "Ada"), "https://github.com/ada.png?size=96");
  assert.equal(contributorAvatar(undefined, "Another team"), null);
});
