import { test, type TestContext } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import AdmZip from "adm-zip";
import matter from "gray-matter";
import {
  buildContent,
  loadSubmission,
  preparePlugin,
  targetsCopilotStudio,
  writeBundle,
  type SkillPayloadFile,
} from "./import-submissions.ts";
import { validatePluginFiles } from "./validate-plugin.ts";

const catalog = {
  name: "Example plugin",
  description: "Two related skills in one package.",
  author: "Example author",
  tags: ["plugin"],
  platforms: ["Copilot Studio", "Scout"],
  category: "manufacturing",
  builtByMicrosoft: true,
};

function png(width: number, height: number): Buffer {
  // Only the PNG signature/IHDR dimensions are consumed by the package validator.
  const data = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(data);
  data.write("IHDR", 12, "ascii");
  data.writeUInt32BE(width, 16);
  data.writeUInt32BE(height, 20);
  return data;
}

function pluginFiles(): SkillPayloadFile[] {
  const manifest = {
    manifestVersion: "devPreview",
    id: "12345678-1234-1234-1234-123456789abc",
    name: { short: "Manifest name" },
    description: { short: "Manifest summary", full: "Manifest overview." },
    icons: { color: "color.png", outline: "outline.png" },
    agentSkills: [{ folder: "./skills/first/" }, { folder: "skills/second" }],
    agentConnectors: [{ id: "mcp", displayName: "MCP connector", description: "Search relevant records." }],
  };
  return [
    { path: "manifest.json", data: Buffer.from(JSON.stringify(manifest)) },
    { path: "color.png", data: png(192, 192) },
    { path: "outline.png", data: png(32, 32) },
    { path: "skills/first/SKILL.md", data: Buffer.from("---\nname: first\ndescription: First agent trigger.\n---\nRun first.\n") },
    { path: "skills/first/references/example.json", data: Buffer.from('{"sample":true}\n') },
    { path: "skills/first/references/README.md", data: Buffer.from("Runtime reference, not a gallery sidecar.\n") },
    { path: "skills/second/SKILL.md", data: Buffer.from("---\nname: second\ndescription: Second agent trigger.\n---\nRun second.\n") },
    { path: "skills/second/scripts/run.py", data: Buffer.from("print('example')\n") },
  ];
}

function put(dir: string, path: string, data: string | Buffer): void {
  mkdirSync(dirname(join(dir, path)), { recursive: true });
  writeFileSync(join(dir, path), data);
}

function fixture(t: TestContext, slug = "example-plugin", files = pluginFiles()): string {
  const root = join(process.cwd(), `.plugin-import-test-${randomUUID()}`);
  const dir = join(root, slug);
  mkdirSync(dir, { recursive: true });
  t.after(() => rmSync(root, { recursive: true, force: true }));
  put(dir, "metadata.json", JSON.stringify(catalog));
  for (const file of files) put(dir, file.path, file.data);
  return dir;
}

test("unpacked manifest is detected before Scout JSON and derives protected inventories", (t) => {
  const dir = fixture(t);
  put(dir, "README.md", "# Human overview\n");
  put(dir, "metadata.json", JSON.stringify({
    ...catalog,
    type: "automation",
    bundle: "bundles/other.zip",
    pluginSkills: [{ name: "forged" }],
    pluginConnectors: [{ id: "forged" }],
  }));
  const sub = loadSubmission(dir);
  assert.equal(sub.kind, "plugin");
  assert.equal(sub.loadProblems, undefined);
  assert.equal(sub.readmeMd, "# Human overview\n");
  assert.equal(sub.automationJson, undefined);
  const prepared = preparePlugin(sub);
  assert.ok(!("problem" in prepared), JSON.stringify(prepared));
  assert.equal(prepared.meta.type, "plugin");
  assert.equal(prepared.meta.bundle, "bundles/example-plugin.zip");
  assert.deepEqual(prepared.meta.platforms, ["Cowork"]);
  assert.equal(targetsCopilotStudio(prepared.meta), false);
  assert.equal(prepared.meta.category, "manufacturing");
  assert.equal(prepared.meta.builtByMicrosoft, true);
  assert.deepEqual(prepared.meta.pluginSkills, [
    { folder: "skills/first", name: "first", description: "First agent trigger." },
    { folder: "skills/second", name: "second", description: "Second agent trigger." },
  ]);
  assert.deepEqual(prepared.meta.pluginConnectors, [
    { id: "mcp", displayName: "MCP connector", description: "Search relevant records." },
  ]);
  assert.equal(prepared.body, "Manifest overview.\n");
  assert.doesNotMatch(prepared.body, /## (Skills|Connectors|Install)/);
  const generated = matter(buildContent(prepared.meta, prepared.body));
  assert.deepEqual(generated.data.pluginSkills, prepared.meta.pluginSkills);
  assert.deepEqual(generated.data.pluginConnectors, prepared.meta.pluginConnectors);
});

test("plugin packages preserve resources, strip sidecars, and bundle deterministically", (t) => {
  const dir = fixture(t);
  put(dir, "README.md", "Human overview only.");
  put(dir, "skills/first/metadata.yaml", "name: stray sidecar");
  const sub = loadSubmission(dir);
  const prepared = preparePlugin(sub);
  assert.ok(!("problem" in prepared), JSON.stringify(prepared));
  assert.deepEqual(prepared.files.map((f) => f.path).sort(), pluginFiles().map((f) => f.path).sort());
  const firstZip = join(dirname(dir), "first.zip");
  const secondZip = join(dirname(dir), "second.zip");
  writeBundle(prepared.files, firstZip);
  writeBundle([...prepared.files].reverse(), secondZip);
  assert.deepEqual(readFileSync(firstZip), readFileSync(secondZip));
  const entries = new AdmZip(firstZip).getEntries().filter((e) => !e.isDirectory);
  assert.equal(entries.length, pluginFiles().length);
  for (const file of pluginFiles()) {
    const entry = entries.find((e) => e.entryName === file.path);
    assert.ok(entry, file.path);
    assert.deepEqual(entry.getData(), file.data);
  }
});

test("manifest metadata fallback and connector-only plugins remain supported", (t) => {
  const files = pluginFiles();
  const manifest = JSON.parse(files[0].data.toString());
  delete manifest.agentSkills;
  files[0].data = Buffer.from(JSON.stringify(manifest));
  const dir = fixture(t, "connector-only", files.filter((f) => !f.path.startsWith("skills/")));
  put(dir, "metadata.json", JSON.stringify({ tags: ["plugin"], author: "Author" }));
  const prepared = preparePlugin(loadSubmission(dir));
  assert.ok(!("problem" in prepared), JSON.stringify(prepared));
  assert.equal(prepared.meta.name, "Manifest name");
  assert.equal(prepared.meta.description, "Manifest summary");
  assert.deepEqual(prepared.meta.pluginSkills, []);
  assert.equal((prepared.meta.pluginConnectors as unknown[]).length, 1);
});

test("unpacked plugin rejects root skill, ZIP, installer, and automation payloads", (t) => {
  for (const path of ["SKILL.md", "other.zip", "INSTALL.md", "automation.json"]) {
    const dir = fixture(t);
    put(dir, path, "{}");
    const sub = loadSubmission(dir);
    assert.ok(sub.loadProblems?.length, path);
    assert.ok("problem" in preparePlugin(sub), path);
  }
});

test("legacy plugin ZIPs reject duplicate root manifests independently of filesystem casing", (t) => {
  const dir = fixture(t, "powerpoint-deck-designer", []);
  const files = pluginFiles();
  writeBundle([...files, { path: "MANIFEST.JSON", data: files[0].data }], join(dir, "plugin.zip"));
  assert.ok(loadSubmission(dir).loadProblems?.some((p) => p.includes("multiple root manifest")));
});

test("invalid plugin manifests fail validation rather than becoming automations or throwing", (t) => {
  for (const source of ["{", "null", "[]", '"text"', "{}"]) {
    const dir = fixture(t);
    put(dir, "manifest.json", source);
    const sub = loadSubmission(dir);
    assert.equal(sub.kind, "plugin");
    assert.ok("problem" in preparePlugin(sub));
  }
  const files = pluginFiles();
  const manifest = JSON.parse(files[0].data.toString());
  manifest.description.full = 123;
  manifest.agentConnectors = {};
  files[0].data = Buffer.from(JSON.stringify(manifest));
  const result = validatePluginFiles(files, "invalid-plugin");
  assert.equal(result.ok, false);
  assert.ok(result.problems.some((p) => p.includes("description.full")));
  assert.ok(result.problems.some((p) => p.includes("agentConnectors")));
});

test("missing icons or skill resources are rejected by the existing plugin validator", (t) => {
  for (const missing of ["color.png", "outline.png", "skills/first/SKILL.md"]) {
    const dir = fixture(t, "incomplete-plugin", pluginFiles().filter((f) => f.path !== missing));
    const result = preparePlugin(loadSubmission(dir));
    assert.ok("problem" in result, missing);
    assert.ok(result.problem.problems.some((p) => /icon|SKILL.md/.test(p)), missing);
  }
});

test("plugin metadata must be an object and retains strict catalog validation", (t) => {
  for (const value of [null, [], "text", { ...catalog, builtByMicrosoft: "false" }, { ...catalog, category: "unknown" }]) {
    const dir = fixture(t);
    put(dir, "metadata.json", JSON.stringify(value));
    assert.ok("problem" in preparePlugin(loadSubmission(dir)), JSON.stringify(value));
  }
});

test("new plugin ZIPs stay forbidden while grandfathered plugin ZIPs use the same pipeline", (t) => {
  for (const [slug, allowed] of [["new-plugin", false], ["powerpoint-deck-designer", true]] as const) {
    const dir = fixture(t, slug, []);
    writeBundle([
      ...pluginFiles(),
      { path: "README.md", data: Buffer.from("Legacy human overview.\n") },
      { path: "metadata.json", data: Buffer.from('{"name":"must not ship"}') },
    ], join(dir, "plugin.zip"));
    const sub = loadSubmission(dir);
    if (!allowed) {
      assert.ok(sub.loadProblems?.some((p) => p.includes("no longer accepted")));
      continue;
    }
    assert.equal(sub.kind, "plugin");
    assert.equal(sub.loadProblems, undefined);
    assert.equal(sub.readmeMd, "Legacy human overview.\n");
    const prepared = preparePlugin(sub);
    assert.ok(!("problem" in prepared), JSON.stringify(prepared));
    assert.equal(prepared.files.length, pluginFiles().length);
  }
});

test("legacy skills and Scout automations retain their detection paths", (t) => {
  const skill = fixture(t, "plain-skill", [
    { path: "SKILL.md", data: Buffer.from("---\nname: plain-skill\ndescription: Trigger\n---\nRun.\n") },
    { path: "references/data.json", data: Buffer.from("{}") },
  ]);
  const loadedSkill = loadSubmission(skill);
  assert.equal(loadedSkill.kind, "skill");
  assert.equal(loadedSkill.loadProblems, undefined);
  assert.match(loadedSkill.skillMd!, /plain-skill/);
  assert.deepEqual(loadedSkill.bundleFiles.map((f) => f.path), ["references/data.json"]);

  const automation = fixture(t, "plain-automation", [
    { path: "automation.json", data: Buffer.from('{"name":"Automation"}') },
  ]);
  assert.equal(loadSubmission(automation).kind, "automation");
  put(automation, "second.json", "{}");
  assert.ok(loadSubmission(automation).loadProblems?.some((p) => p.includes("2 automation")));

  const legacy = fixture(t, "phi-deidentifier", []);
  writeBundle(loadedSkill.bundleFiles.concat([
    { path: "SKILL.md", data: Buffer.from(loadedSkill.skillMd!) },
  ]), join(legacy, "skill.zip"));
  assert.equal(loadSubmission(legacy).kind, "skill");
  assert.equal(loadSubmission(legacy).loadProblems, undefined);
});

// These content submissions arrive in a dependent change, after generic support.
for (const [slug, category, contract] of [
  ["maintenance-triage", "manufacturing", "skills/fault-intake/contracts/mfg.maintenance-triage.v1.json"],
  ["store-associate-assist", "retail-cpg", "skills/question-intake/contracts/rtl.store-associate-assist.v1.json"],
] as const) {
  const dir = join(process.cwd(), "submissions", slug);
  test(`converted ${slug} retains its complete multi-skill package`, {
    skip: !existsSync(join(dir, "manifest.json")),
  }, (t) => {
    const sub = loadSubmission(dir);
    const prepared = preparePlugin(sub);
    assert.ok(!("problem" in prepared), JSON.stringify(prepared));
    assert.equal(sub.kind, "plugin");
    assert.ok(sub.readmeMd?.length);
    assert.equal(prepared.meta.category, category);
    assert.equal(prepared.meta.builtByMicrosoft, true);
    assert.equal((prepared.meta.pluginSkills as unknown[]).length, 5);
    assert.deepEqual(prepared.meta.pluginConnectors, []);
    assert.ok(prepared.files.some((f) => f.path === contract));
    assert.equal(targetsCopilotStudio(prepared.meta), false);
    const outputDir = fixture(t, "bundle-output", []);
    const bundlePath = join(outputDir, "package.zip");
    writeBundle(prepared.files, bundlePath);
    const zip = new AdmZip(bundlePath);
    assert.equal(zip.getEntries().length, prepared.files.length);
    for (const file of prepared.files) {
      assert.deepEqual(zip.getEntry(file.path)?.getData(), file.data, file.path);
    }
    assert.equal(zip.getEntry("metadata.json"), null);
    assert.equal(zip.getEntry("README.md"), null);
  });
}
