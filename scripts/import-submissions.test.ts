/**
 * Unit tests for the shared catalog-merge policy used by every submission
 * processor (`buildMeta` + `CATALOG_PASSTHROUGH`). These lock in the invariant
 * that derived/canonical frontmatter always wins over the metadata sidecar and
 * that undocumented catalog keys are dropped — the bug class that a per-field
 * spot fix would leave open.
 */
import { test, type TestContext } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import {
  buildMeta,
  CATALOG_PASSTHROUGH,
  loadSubmission,
  targetsCopilotStudio,
  writeCopilotStudioSkill,
} from "./import-submissions.ts";
import { validatePluginFiles } from "./validate-plugin.ts";

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

test("Copilot Studio feed includes only skills declaring that platform", () => {
  assert.equal(targetsCopilotStudio({ platforms: ["Copilot Studio"] }), true);
  assert.equal(targetsCopilotStudio({ platforms: ["Cowork", "Copilot Studio"] }), true);
  assert.equal(targetsCopilotStudio({ platforms: ["Cowork", "Scout"] }), false);
  assert.equal(targetsCopilotStudio({ platforms: "Copilot Studio" }), false);
});

test("Copilot Studio export preserves canonical skill and nested resource paths", () => {
  const output = mkdtempSync(join(tmpdir(), "copilot-studio-skills-"));
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
  const output = mkdtempSync(join(tmpdir(), "copilot-studio-skills-"));
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

function submissionFixture(t: TestContext, files: Record<string, string | Buffer>): string {
  const dir = mkdtempSync(join(tmpdir(), "submission-routing-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  for (const [path, contents] of Object.entries(files)) {
    const full = join(dir, path);
    mkdirSync(dirname(full), { recursive: true });
    writeFileSync(full, contents);
  }
  return dir;
}

function pngHeader(width: number, height: number): Buffer {
  const data = Buffer.alloc(24);
  Buffer.from("89504e470d0a1a0a0000000d49484452", "hex").copy(data);
  data.writeUInt32BE(width, 16);
  data.writeUInt32BE(height, 20);
  return data;
}

const pluginManifest = {
  manifestVersion: "devPreview",
  id: "4e34d725-5a50-5fff-a8b1-ac68968bbabd",
  name: { short: "Test Plugin" },
  description: { short: "A plugin for importer tests." },
  icons: { color: "color.png", outline: "outline.png" },
  agentSkills: [{ folder: "./skills/sample-skill" }],
};
const pluginFixture = {
  "manifest.json": JSON.stringify(pluginManifest),
  "color.png": pngHeader(192, 192),
  "outline.png": pngHeader(32, 32),
  "metadata.json": JSON.stringify({
    name: "Test Plugin",
    description: "Catalog description",
    platforms: ["Cowork"],
    tags: ["testing"],
    author: "Test Author",
  }),
  "README.md": "# Human overview\n",
  "skills/sample-skill/SKILL.md":
    "---\nname: sample-skill\ndescription: Use for importer tests.\n---\nRun the task.\n",
};

test("unpacked plugins route to plugin validation and exclude only root sidecars", (t) => {
  const files: Record<string, string | Buffer> = {
    ...pluginFixture,
    "metadata.yaml": "name: Alternative metadata\n",
    "metadata.yml": "name: Alternative metadata\n",
    "skills/sample-skill/README.md": "# Runtime reference\n",
    "skills/sample-skill/assets/metadata.json": '{"runtime":true}',
    "shared/config.json": '{"policy":"test"}',
    ".claude-plugin/plugin.json": '{"name":"sample-plugin"}',
  };
  const sub = loadSubmission(submissionFixture(t, files));
  assert.equal(sub.kind, "plugin");
  assert.equal(sub.loadProblems, undefined);
  assert.equal(sub.skillMd, undefined);
  assert.equal(sub.automationJson, undefined);
  assert.equal(sub.metaText, pluginFixture["metadata.json"]);
  assert.equal(sub.readmeMd, pluginFixture["README.md"]);
  assert.ok(sub.pluginFiles);
  const expectedPaths = Object.keys(files).filter(
    (path) => !["metadata.json", "metadata.yaml", "metadata.yml", "README.md"].includes(path),
  );
  assert.deepEqual(sub.pluginFiles.map((file) => file.path).sort(), expectedPaths.sort());
  for (const file of sub.pluginFiles) {
    const expected = files[file.path];
    assert.deepEqual(file.data, typeof expected === "string" ? Buffer.from(expected) : expected);
  }
  const validation = validatePluginFiles(sub.pluginFiles, sub.label);
  assert.equal(validation.ok, true, validation.problems.join("\n"));
  assert.deepEqual(validation.skills.map((skill) => skill.name), ["sample-skill"]);
});

test("plugin detection and root sidecar removal are case-insensitive", (t) => {
  const { "manifest.json": manifest, "metadata.json": metadata, "README.md": readme, ...rest } =
    pluginFixture;
  const sub = loadSubmission(submissionFixture(t, {
    ...rest,
    "MANIFEST.JSON": manifest,
    "METADATA.JSON": metadata,
    "readme.md": readme,
  }));
  assert.equal(sub.kind, "plugin");
  assert.equal(sub.metaText, metadata);
  assert.equal(sub.readmeMd, readme);
  assert.ok(sub.pluginFiles);
  assert.ok(sub.pluginFiles.some((file) => file.path === "MANIFEST.JSON"));
  assert.ok(!sub.pluginFiles.some((file) => /^(metadata\.json|readme\.md)$/i.test(file.path)));
  const validation = validatePluginFiles(sub.pluginFiles, sub.label);
  assert.equal(validation.ok, true, validation.problems.join("\n"));
});

test("connector-only plugins need neither a root skill nor a README", (t) => {
  const { agentSkills, ...manifest } = pluginManifest;
  const sub = loadSubmission(submissionFixture(t, {
    "manifest.json": JSON.stringify({
      ...manifest,
      agentConnectors: [{ id: "sample-connector", displayName: "Sample connector" }],
    }),
    "metadata.json": pluginFixture["metadata.json"],
    "color.png": pluginFixture["color.png"],
    "outline.png": pluginFixture["outline.png"],
  }));
  assert.equal(sub.kind, "plugin");
  assert.equal(sub.readmeMd, undefined);
  assert.ok(sub.pluginFiles);
  const validation = validatePluginFiles(sub.pluginFiles, sub.label);
  assert.equal(validation.ok, true, validation.problems.join("\n"));
  assert.equal(validation.skills.length, 0);
  assert.equal(validation.connectors[0]?.id, "sample-connector");
});

test("invalid unpacked plugins report plugin errors, not automation errors", (t) => {
  const sub = loadSubmission(submissionFixture(t, {
    ...pluginFixture,
    "manifest.json": "{invalid json",
  }));
  assert.equal(sub.kind, "plugin");
  assert.ok(sub.pluginFiles);
  const validation = validatePluginFiles(sub.pluginFiles, sub.label);
  assert.equal(validation.ok, false);
  assert.match(validation.problems.join("\n"), /manifest.json is not valid JSON/);
});

test("ordinary skills keep root SKILL.md precedence over JSON resources", (t) => {
  const sub = loadSubmission(submissionFixture(t, {
    "SKILL.md": pluginFixture["skills/sample-skill/SKILL.md"],
    "manifest.json": '{"resource":true}',
    "metadata.json": pluginFixture["metadata.json"],
  }));
  assert.equal(sub.kind, "skill");
  assert.equal(sub.skillMd, pluginFixture["skills/sample-skill/SKILL.md"]);
  assert.deepEqual(sub.bundleFiles.map((file) => file.path), ["manifest.json"]);
  assert.equal(sub.pluginFiles, undefined);
});

test("Scout JSON and nested manifest resources keep automation routing", (t) => {
  const automation = '{"name":"Example","steps":[],"schedule":{"type":"single"}}';
  const sub = loadSubmission(submissionFixture(t, {
    "example.json": automation,
    "metadata.json": pluginFixture["metadata.json"],
    "assets/manifest.json": JSON.stringify(pluginManifest),
  }));
  assert.equal(sub.kind, "automation");
  assert.equal(sub.automationJson, automation);
  assert.equal(sub.loadProblems, undefined);
});

test("unpacked plugin support does not bypass the new ZIP payload ban", (t) => {
  const sub = loadSubmission(submissionFixture(t, {
    ...pluginFixture,
    "plugin.zip": Buffer.from("not opened: new ZIPs are rejected"),
  }));
  assert.match(sub.loadProblems?.join("\n") ?? "", /zip.*payloads are no longer accepted/);
  assert.equal(sub.pluginFiles, undefined);
});
