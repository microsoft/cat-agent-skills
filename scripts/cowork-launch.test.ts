import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { authorKey, computeStats, directoryAuthors, resolveBadges, type BadgeSkill } from "../src/lib/badges";
import { contributorAvatar } from "../src/lib/contributor-avatar";
import { CATEGORIES, CATEGORY_COLORS, CATEGORY_ICON_PATHS, CATEGORY_LABELS } from "../src/lib/categories";
import { skillSchema } from "../src/lib/skill-schema";
import { loadSubmission } from "./import-submissions";
import { validatePluginFiles } from "./validate-plugin";

const team = "Copilot Cowork team";
const plugins = [
  ["education-for-cowork", "education", 10],
  ["legal-for-cowork", "legal", 20],
  ["finance-for-cowork", "finance", 13],
  ["capital-markets-for-cowork", "capital-markets", 10],
  ["accounting-for-cowork", "accounting", 7],
] as const;
const sales = [
  "business-case-composer", "competitive-strategy", "customer-engagement-and-deal-risk-insights",
  "deal-catchup", "meeting-prep", "pipeline-prioritizer", "post-meeting-follow-up",
  "sales-progress-update", "stakeholder-and-decision-map",
];
const service = ["answer-research", "case-preparation-brief", "case-triage", "draft-customer-reply", "knowledge-harvest"];

test("every category has a label, color, icon, and schema support", () => {
  assert.equal(new Set(CATEGORIES).size, 11);
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

test("launch submissions are five complete plugins and fourteen individual Cowork skills", () => {
  const entries = [
    ...plugins.map(([slug, category]) => ({ slug, category, kind: "plugin" })),
    ...sales.map((slug) => ({ slug, category: "sales", kind: "skill" })),
    ...service.map((slug) => ({ slug, category: "service", kind: "skill" })),
  ];
  assert.equal(entries.length, 19);
  for (const { slug, category, kind } of entries) {
    const path = `submissions/${slug}`;
    const sub = loadSubmission(path);
    assert.ok(sub);
    assert.equal(sub.kind, kind, slug);
    assert.equal(sub.loadProblems?.length ?? 0, 0, slug);
    assert.ok(sub.readmeMd?.trim(), `${slug} needs a human-facing README`);
    assert.equal([...(sub.pluginFiles ?? []), ...sub.bundleFiles]
      .some((file) => file.path.toLowerCase() === "readme.md"), false, slug);
    const meta = skillSchema.parse(JSON.parse(readFileSync(`${path}/metadata.json`, "utf8")));
    assert.equal(meta.category, category);
    assert.equal(meta.builtByMicrosoft, true);
    assert.equal(meta.author, team);
    assert.deepEqual(meta.platforms, ["Cowork"]);
    assert.equal(meta.authorGithub, undefined);
    assert.equal(authorKey(meta.authorGithub, meta.author), "copilot-cowork-team");
    if (kind === "plugin") {
      const validated = validatePluginFiles(sub.pluginFiles ?? [], slug);
      assert.deepEqual(validated.problems, []);
      assert.equal(validated.skills.length, plugins.find(([name]) => name === slug)?.[2]);
    }
  }
  assert.match(readFileSync("submissions/accounting-for-cowork/README.md", "utf8"), /Frontier only/);
});

test("team directory entry aggregates all nineteen submissions without fabricating a login or badge", () => {
  const skills: BadgeSkill[] = Array.from({ length: 19 }, (_, index) => ({
    slug: `team-${index}`, name: `Team ${index}`, author: team,
    authorGithub: null, featured: false, createdAt: "2026-10-31",
  }));
  skills.push({ slug: "ada", name: "Ada's skill", author: "Ada", authorGithub: "ADA" });
  const authors = directoryAuthors(skills);
  assert.equal(authors.length, 2);
  assert.equal(authors[0].key, "copilot-cowork-team");
  assert.equal(authors[0].login, "");
  assert.equal(authors[0].displayName, team);
  assert.equal(authors[0].skillCount, 19);
  assert.equal(authors[0].skills.length, 19);
  assert.equal(authors[1].key, "ada");
  assert.equal(computeStats("ada", skills).skillCount, 1);
  assert.equal(computeStats("copilot-cowork-team", skills).skillCount, 0);
  assert.deepEqual(resolveBadges("copilot-cowork-team", skills), []);
});

test("avatars use the official local team logo without changing GitHub or initials fallbacks", () => {
  assert.equal(contributorAvatar(null, team), "/copilot.svg");
  assert.equal(contributorAvatar("", " COPILOT COWORK TEAM "), "/copilot.svg");
  assert.equal(contributorAvatar("@Ada", "Ada"), "https://github.com/ada.png?size=96");
  assert.equal(contributorAvatar("ada", team), "https://github.com/ada.png?size=96");
  assert.equal(contributorAvatar(undefined, "Another team"), null);
  const logo = readFileSync("public/copilot.svg", "utf8");
  assert.match(logo, /<svg/);
  assert.match(logo, /linearGradient/);
});
