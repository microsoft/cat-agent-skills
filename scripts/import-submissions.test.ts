/**
 * Unit tests for the shared catalog-merge policy used by every submission
 * processor (`buildMeta` + `CATALOG_PASSTHROUGH`). These lock in the invariant
 * that derived/canonical frontmatter always wins over the metadata sidecar and
 * that undocumented catalog keys are dropped — the bug class that a per-field
 * spot fix would leave open.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import matter from "gray-matter";
import { skillSchema } from "../src/lib/skill-schema.ts";
import { validateSkillData } from "./validate-skill.ts";
import {
  buildContent,
  buildMeta,
  CATALOG_PASSTHROUGH,
  targetsCopilotStudio,
  writeCopilotStudioSkill,
} from "./import-submissions.ts";

test("derived fields always win over same-named catalog keys", () => {
  const meta = buildMeta(
    {
      name: "Display Name",
      description: "catalog summary",
      agentDescription: "agent-facing trigger",
      platforms: ["Cowork"],
      type: "plugin",
      bundle: "bundles/x.zip",
      pluginSkills: [{ folder: "skills/x", name: "x", description: "From the skill" }],
      pluginConnectors: [{ id: "actual-connector" }],
    },
    {
      name: "SIDECAR NAME",
      description: "SIDECAR DESC",
      agentDescription: "SIDECAR AGENT DESC",
      platforms: ["Scout"],
      type: "automation",
      bundle: "bundles/EVIL.zip",
      pluginSkills: [{ name: "FAKE" }],
      pluginConnectors: [{ id: "fake-connector" }],
    },
  );
  assert.equal(meta.name, "Display Name");
  assert.equal(meta.description, "catalog summary");
  assert.equal(meta.agentDescription, "agent-facing trigger");
  assert.deepEqual(meta.platforms, ["Cowork"]);
  assert.equal(meta.type, "plugin");
  assert.equal(meta.bundle, "bundles/x.zip");
  assert.deepEqual(meta.pluginSkills, [{ folder: "skills/x", name: "x", description: "From the skill" }]);
  assert.deepEqual(meta.pluginConnectors, [{ id: "actual-connector" }]);
});

test("a metadata sidecar cannot override the SKILL.md agentDescription (the #140 regression)", () => {
  const meta = buildMeta(
    { name: "N", description: "D", agentDescription: "FROM SKILL.md" },
    {
      agentDescription: "FROM metadata.json",
      platforms: ["Cowork"],
      tags: ["t"],
      author: "A",
    },
  );
  assert.equal(meta.agentDescription, "FROM SKILL.md");
});

test("only allowlisted catalog fields pass through; everything else is dropped", () => {
  const catalog: Record<string, unknown> = {
    // canonical fields the importer owns — must not pass through:
    name: "n",
    description: "d",
    type: "automation",
    // allowlisted, human-authored:
    platforms: ["Cowork"],
    category: "manufacturing",
    builtByMicrosoft: true,
    tags: ["a", "b"],
    author: "Ada",
    authorUrl: "https://github.com/ada",
    authorGithub: "ada",
    version: "1.2.3",
    createdAt: "2024-01-01",
    updatedAt: "2024-02-01",
    coverColor: "#fff",
    featured: true,
    // undocumented noise that must be dropped:
    slug: "n",
    license: "MIT",
    runtime: "python>=3.10",
    entrypoint: "scripts/x.py",
    dependencies: ["a"],
    capabilities: ["b"],
    evil: "leak",
    pluginSkills: [{ name: "FAKE" }],
    pluginConnectors: [{ id: "fake-connector" }],
  };
  const meta = buildMeta({ name: "N", description: "D" }, catalog);

  for (const key of CATALOG_PASSTHROUGH) {
    assert.ok(key in meta, `expected allowlisted "${key}" to pass through`);
  }
  for (const key of [
    "slug",
    "license",
    "runtime",
    "entrypoint",
    "dependencies",
    "capabilities",
    "evil",
    "pluginSkills",
    "pluginConnectors",
    // `type` is derived, not passthrough: a catalog-only `type` is dropped so a
    // skill can't self-declare its type (the schema defaults it instead).
    "type",
  ]) {
    assert.ok(!(key in meta), `expected non-allowlisted "${key}" to be dropped`);
  }
});

test("undefined derived values are skipped so no empty keys are emitted", () => {
  const meta = buildMeta(
    { name: "N", description: "D", agentDescription: undefined, bundle: undefined },
    { platforms: ["Cowork"], tags: ["t"], author: "A" },
  );
  assert.ok(!("agentDescription" in meta));
  assert.ok(!("bundle" in meta));
});

test("undefined catalog values are skipped", () => {
  const meta = buildMeta(
    { name: "N", description: "D" },
    { platforms: ["Cowork"], tags: undefined },
  );
  assert.ok(!("tags" in meta));
});

test("CATALOG_PASSTHROUGH never lists a canonical/derived field", () => {
  for (const forbidden of ["name", "description", "agentDescription", "type", "bundle", "pluginSkills", "pluginConnectors"]) {
    assert.ok(
      !(CATALOG_PASSTHROUGH as readonly string[]).includes(forbidden),
      `"${forbidden}" must never be in the passthrough allowlist`,
    );
  }
});

test("Copilot Studio feed includes only skills declaring that platform", () => {
  assert.equal(targetsCopilotStudio({ platforms: ["Copilot Studio"] }), true);
  assert.equal(targetsCopilotStudio({ platforms: ["Cowork", "Copilot Studio"] }), true);
  assert.equal(targetsCopilotStudio({ platforms: ["Cowork", "Scout"] }), false);
  assert.equal(targetsCopilotStudio({ platforms: "Copilot Studio" }), false);
});

test("Copilot Studio export preserves canonical skill and nested resource paths", () => {
  const output = join(process.cwd(), `.copilot-studio-skills-test-${randomUUID()}`);
  mkdirSync(output);
  try {
    writeCopilotStudioSkill(output, "sample-skill", "---\nname: sample-skill\n---\n", [
      { path: "scripts/lib/helper.py", data: Buffer.from("print('ok')\n") },
    ]);

    assert.equal(
      readFileSync(join(output, "sample-skill", "SKILL.md"), "utf8"),
      "---\nname: sample-skill\n---\n",
    );
    assert.equal(
      readFileSync(join(output, "sample-skill", "scripts", "lib", "helper.py"), "utf8"),
      "print('ok')\n",
    );
  } finally {
    rmSync(output, { recursive: true, force: true });
  }
});

test("Copilot Studio export rejects resource path traversal", () => {
  const output = join(process.cwd(), `.copilot-studio-skills-test-${randomUUID()}`);
  mkdirSync(output);
  try {
    assert.throws(
      () =>
        writeCopilotStudioSkill(output, "sample-skill", "# Skill\n", [
          { path: "../outside.txt", data: Buffer.from("unsafe") },
        ]),
      /unsafe skill resource path/,
    );
  } finally {
    rmSync(output, { recursive: true, force: true });
  }
});

test("new catalog fields and structured plugin inventories round-trip through frontmatter", () => {
  const meta = buildMeta(
    {
      name: "Plugin",
      description: "A plugin",
      type: "plugin",
      pluginSkills: [
        { folder: "skills/example", name: "example", description: 'Use "quoted": values\nwith [brackets].' },
      ],
      pluginConnectors: [{ id: "mcp", description: "true", displayName: "MCP: connector" }],
    },
    {
      platforms: ["Cowork"],
      tags: ["plugin"],
      author: "Ada",
      category: "retail-cpg",
      builtByMicrosoft: true,
    },
  );
  const source = buildContent(meta, "\nOverview\n");
  const parsed = matter(source).data;
  assert.deepEqual(parsed, meta);
  assert.equal(skillSchema.parse(parsed).builtByMicrosoft, true);
  assert.deepEqual(skillSchema.parse(parsed).pluginSkills, meta.pluginSkills);
  assert.deepEqual(skillSchema.parse(parsed).pluginConnectors, meta.pluginConnectors);
  assert.equal(source, buildContent(meta, "\nOverview\n"));
});

test("catalog validation rejects invalid category and non-boolean Microsoft flags", () => {
  const catalog = { platforms: ["Cowork"], tags: ["plugin"], author: "Ada" };
  const derived = { name: "Plugin", description: "A plugin" };
  for (const builtByMicrosoft of ["false", "true", 0, 1, null, [], {}]) {
    const meta = buildMeta(derived, { ...catalog, builtByMicrosoft });
    const result = validateSkillData(meta, "test");
    assert.equal(result.ok, false, `must reject ${JSON.stringify(builtByMicrosoft)}`);
    assert.ok(result.problems.some((p) => p.startsWith("builtByMicrosoft:")));
  }
  for (const builtByMicrosoft of [true, false, undefined]) {
    const meta = buildMeta(derived, { ...catalog, builtByMicrosoft });
    assert.equal(validateSkillData(meta, "test").ok, true);
    assert.equal(skillSchema.parse(meta).builtByMicrosoft, builtByMicrosoft ?? false);
  }
  const invalid = buildMeta(derived, { ...catalog, category: "unknown-industry" });
  assert.equal(validateSkillData(invalid, "test").ok, false);
  assert.equal(skillSchema.parse(buildMeta(derived, catalog)).category, "productivity");
});
