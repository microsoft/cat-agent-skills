/**
 * Import skill submissions into the site content.
 *
 * Everything is contributed through the `submissions/` folder, as either:
 *
 *   submissions/<slug>.md   A single markdown file with metadata in its
 *                           frontmatter (best for instruction-only skills).
 *
 *   submissions/<slug>.zip  A bundle containing:
 *                             - skill.md       the instructions (no frontmatter
 *                                              needed),
 *                             - metadata.json  OR metadata.yaml — all metadata,
 *                                              kept OUT of the instructions file,
 *                             - optional scripts / other files (bundled).
 *
 * For every submission this script validates the metadata against the shared
 * schema (HARD FAIL on error), then generates the canonical
 * `src/content/skills/<slug>.md` (which authors never edit by hand). Zip
 * submissions with extra files also get a deterministic
 * `public/bundles/<slug>.zip`, with `bundle:` injected into the frontmatter.
 *
 * Usage:
 *   tsx scripts/import-submissions.ts            # import everything
 *   tsx scripts/import-submissions.ts --check    # validate only, write nothing
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import AdmZip from "adm-zip";
import matter from "gray-matter";
import { validateSkillData } from "./validate-skill.ts";

const ROOT = join(import.meta.dirname, "..");
const SUBMISSIONS_DIR = join(ROOT, "submissions");
const CONTENT_DIR = join(ROOT, "src", "content", "skills");
const BUNDLES_DIR = join(ROOT, "public", "bundles");

const INSTRUCTIONS_NAME = "skill.md";
const METADATA_NAMES = ["metadata.json", "metadata.yaml", "metadata.yml"];
// Fixed timestamp so generated bundle zips are byte-for-byte reproducible
// (otherwise every CI run re-commits an identical-but-different-bytes zip).
const FIXED_ZIP_DATE = new Date("2000-01-01T00:00:00Z");
// Order in which frontmatter keys are emitted for generated content files.
const FIELD_ORDER = [
  "name",
  "description",
  "platforms",
  "tags",
  "author",
  "authorUrl",
  "version",
  "createdAt",
  "updatedAt",
  "coverColor",
  "featured",
  "bundle",
];

const checkOnly = process.argv.includes("--check");

type ImportProblem = { source: string; problems: string[] };

function quote(value: string): string {
  return /[:#\[\]{},'"]|^\s|\s$/.test(value) ? JSON.stringify(value) : value;
}

function formatScalar(value: unknown): string {
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  if (typeof value === "boolean" || typeof value === "number") return String(value);
  return quote(String(value));
}

/** Serialize a metadata object into a deterministic YAML frontmatter block. */
function serializeFrontmatter(meta: Record<string, unknown>): string {
  const keys = [
    ...FIELD_ORDER.filter((k) => k in meta),
    ...Object.keys(meta).filter((k) => !FIELD_ORDER.includes(k)),
  ];
  const lines = ["---"];
  for (const key of keys) {
    const value = meta[key];
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      lines.push(`${key}: [${value.map((v) => formatScalar(v)).join(", ")}]`);
    } else {
      lines.push(`${key}: ${formatScalar(value)}`);
    }
  }
  lines.push("---", "");
  return lines.join("\n");
}

/** Build a content markdown file from metadata + an instructions body. */
function buildContent(meta: Record<string, unknown>, body: string): string {
  return serializeFrontmatter(meta) + body.replace(/^\s+/, "");
}

/** Parse a metadata file (JSON or YAML) into a plain object. */
function parseMetadataFile(name: string, text: string): Record<string, unknown> {
  if (name.toLowerCase().endsWith(".json")) return JSON.parse(text);
  // Reuse gray-matter's YAML engine by wrapping the text as frontmatter.
  return matter(`---\n${text}\n---\n`).data;
}

/** Find a zip entry by base name (case-insensitive), preferring the shallowest. */
function findEntry(zip: AdmZip, names: string[]): AdmZip.IZipEntry | undefined {
  return zip
    .getEntries()
    .filter(
      (e) => !e.isDirectory && names.includes(basename(e.entryName).toLowerCase()),
    )
    .sort((a, b) => a.entryName.split("/").length - b.entryName.split("/").length)[0];
}

/** Write a deterministic zip from the given entries. */
function writeBundle(entries: AdmZip.IZipEntry[], outPath: string): void {
  const out = new AdmZip();
  for (const entry of [...entries].sort((a, b) => a.entryName.localeCompare(b.entryName))) {
    out.addFile(entry.entryName, entry.getData());
  }
  for (const entry of out.getEntries()) entry.header.time = FIXED_ZIP_DATE;
  out.writeZip(outPath);
}

/** Only write when content differs, so unchanged submissions create no diff. */
function writeIfChanged(path: string, content: string): void {
  if (existsSync(path) && readFileSync(path, "utf8") === content) return;
  writeFileSync(path, content, "utf8");
}

/** Import a standalone `submissions/<slug>.md`. */
function importMarkdown(mdPath: string): ImportProblem | null {
  const slug = basename(mdPath).replace(/\.md$/i, "");
  const source = readFileSync(mdPath, "utf8");
  const label = `submissions/${basename(mdPath)}`;

  let data: Record<string, unknown>;
  try {
    data = matter(source).data;
  } catch (err) {
    return { source: label, problems: [`could not parse frontmatter: ${(err as Error).message}`] };
  }
  const result = validateSkillData(data, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), source);
    console.log(`\u2713 ${label} \u2192 src/content/skills/${slug}.md`);
  }
  return null;
}

/** Import a `submissions/<slug>.zip`. */
function importZip(zipPath: string): ImportProblem | null {
  const slug = basename(zipPath).replace(/\.zip$/i, "");
  const label = `submissions/${basename(zipPath)}`;
  const zip = new AdmZip(zipPath);

  const instructions = findEntry(zip, [INSTRUCTIONS_NAME]);
  if (!instructions) {
    return { source: label, problems: [`no \`skill.md\` found at the zip root`] };
  }

  const metaEntry = findEntry(zip, METADATA_NAMES);
  const parsed = matter(zip.readAsText(instructions));
  let meta: Record<string, unknown>;
  if (metaEntry) {
    try {
      meta = parseMetadataFile(metaEntry.entryName, zip.readAsText(metaEntry));
    } catch (err) {
      return {
        source: label,
        problems: [`could not parse ${basename(metaEntry.entryName)}: ${(err as Error).message}`],
      };
    }
  } else {
    // Back-compat: fall back to frontmatter inside skill.md.
    meta = parsed.data;
  }

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  const skip = new Set([instructions.entryName, metaEntry?.entryName].filter(Boolean) as string[]);
  const scriptEntries = zip.getEntries().filter((e) => !e.isDirectory && !skip.has(e.entryName));
  const hasBundle = scriptEntries.length > 0;
  if (hasBundle) meta = { ...meta, bundle: `bundles/${slug}.zip` };

  if (!checkOnly) {
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, parsed.content));
    if (hasBundle) {
      mkdirSync(BUNDLES_DIR, { recursive: true });
      writeBundle(scriptEntries, join(BUNDLES_DIR, `${slug}.zip`));
    }
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md` +
        (hasBundle ? ` (+ public/bundles/${slug}.zip)` : ""),
    );
  }
  return null;
}

function main() {
  if (!existsSync(SUBMISSIONS_DIR)) {
    console.log("No submissions/ directory \u2014 nothing to import.");
    return;
  }

  const files = readdirSync(SUBMISSIONS_DIR);
  const ignore = new Set(["readme.md", "skill.template.md"]);
  const mds = files.filter(
    (f) => f.toLowerCase().endsWith(".md") && !ignore.has(f.toLowerCase()),
  );
  const zips = files.filter((f) => f.toLowerCase().endsWith(".zip"));

  if (mds.length === 0 && zips.length === 0) {
    console.log("No submissions found in submissions/.");
    return;
  }

  const problems: ImportProblem[] = [];
  for (const f of mds) {
    const p = importMarkdown(join(SUBMISSIONS_DIR, f));
    if (p) problems.push(p);
  }
  for (const f of zips) {
    const p = importZip(join(SUBMISSIONS_DIR, f));
    if (p) problems.push(p);
  }

  if (problems.length > 0) {
    console.error(`\n\u2717 ${problems.length} submission(s) failed validation:\n`);
    for (const p of problems) {
      console.error(`  ${p.source}:`);
      for (const msg of p.problems) console.error(`    \u2022 ${msg}`);
    }
    console.error(
      "\nEvery submission needs valid metadata (name, description, platforms, " +
        "tags) \u2014 in the .md frontmatter, or in metadata.json/metadata.yaml " +
        "inside the zip. Fix the items above and retry.",
    );
    process.exit(1);
  }

  const total = mds.length + zips.length;
  console.log(
    checkOnly
      ? `\nAll ${total} submission(s) passed validation (check-only, nothing written).`
      : `\nImported ${total} submission(s).`,
  );
}

main();
