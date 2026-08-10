/**
 * Unit tests for the shared catalog-merge policy used by every submission
 * processor (`buildMeta` + `CATALOG_PASSTHROUGH`). These lock in the invariant
 * that derived/canonical frontmatter always wins over the metadata sidecar and
 * that undocumented catalog keys are dropped — the bug class that a per-field
 * spot fix would leave open.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildMeta, CATALOG_PASSTHROUGH } from "./import-submissions.ts";

test("derived fields always win over same-named catalog keys", () => {
  const meta = buildMeta(
    {
      name: "Display Name",
      description: "catalog summary",
      agentDescription: "agent-facing trigger",
      platforms: ["Cowork"],
      type: "plugin",
      bundle: "bundles/x.zip",
    },
    {
      name: "SIDECAR NAME",
      description: "SIDECAR DESC",
      agentDescription: "SIDECAR AGENT DESC",
      platforms: ["Scout"],
      type: "automation",
      bundle: "bundles/EVIL.zip",
    },
  );
  assert.equal(meta.name, "Display Name");
  assert.equal(meta.description, "catalog summary");
  assert.equal(meta.agentDescription, "agent-facing trigger");
  assert.deepEqual(meta.platforms, ["Cowork"]);
  assert.equal(meta.type, "plugin");
  assert.equal(meta.bundle, "bundles/x.zip");
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
  for (const forbidden of ["name", "description", "agentDescription", "type", "bundle"]) {
    assert.ok(
      !(CATALOG_PASSTHROUGH as readonly string[]).includes(forbidden),
      `"${forbidden}" must never be in the passthrough allowlist`,
    );
  }
});
