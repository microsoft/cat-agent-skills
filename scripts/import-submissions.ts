/**
 * Import skill submissions into the site content.
 *
 * Every skill is contributed through the `submissions/` folder as a self-
 * contained submission — either an uncompressed folder or its zipped
 * equivalent — with the SAME shape:
 *
 *   submissions/<slug>/        (or submissions/<slug>.zip containing the same)
 *   ├── skill.md       The canonical Agent Skills file: frontmatter with
 *   │                  `name` + `description` (the AGENT-facing description the
 *   │                  model reads to decide when to invoke the skill) followed
 *   │                  by the instructions body.
 *   ├── metadata.json  (or metadata.yaml) Catalog metadata for THIS gallery:
 *   │                  `description` (the human catalog/gallery summary),
 *   │                  `platforms`, `tags`, `author`, `authorUrl`, `version`…
 *   └── scripts/       Optional helper files, packaged into a download bundle.
 *
 * The two descriptions are deliberately separate:
 *   - skill.md frontmatter `description`  → `agentDescription` (what the agent reads)
 *   - metadata.json `description`         → `description`      (what the gallery shows)
 *
 * For every submission this script validates the merged metadata against the
 * shared schema (HARD FAIL on error), then generates the canonical
 * `src/content/skills/<slug>.md` (which authors never edit by hand). Submissions
 * with extra files also get a deterministic `public/bundles/<slug>.zip`, with
 * `bundle:` injected into the frontmatter.
 *
 * Usage:
 *   tsx scripts/import-submissions.ts            # import everything
 *   tsx scripts/import-submissions.ts --check    # validate only, write nothing
 */
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { basename, join, posix, relative, sep } from "node:path";
import AdmZip from "adm-zip";
import matter from "gray-matter";
import { validateSkillData } from "./validate-skill.ts";

const ROOT = join(import.meta.dirname, "..");
const SUBMISSIONS_DIR = join(ROOT, "submissions");
const CONTENT_DIR = join(ROOT, "src", "content", "skills");
const BUNDLES_DIR = join(ROOT, "public", "bundles");

const INSTRUCTIONS_NAME = "skill.md";
const METADATA_NAMES = ["metadata.json", "metadata.yaml", "metadata.yml"];
// Fixed timestamp so generated bundle zips are byte-for-byte reproducible.
// adm-zip encodes the DOS time from the Date's *local* components, so this must
// be built from local components (not a UTC instant) to stay identical across
// timezones (e.g. a contributor's machine vs. CI running in UTC).
const FIXED_ZIP_DATE = new Date(2000, 0, 1, 0, 0, 0);
// Order in which frontmatter keys are emitted for generated content files.
const FIELD_ORDER = [
  "name",
  "description",
  "agentDescription",
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
/** A file inside a submission, with a forward-slash relative path. */
type SubFile = { path: string; data: Buffer };
/** A loaded submission (folder or zip), before parsing/validation. */
type Submission = {
  slug: string;
  label: string;
  skillMd?: string;
  metaName?: string;
  metaText?: string;
  scripts: SubFile[];
};

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

/** Write a deterministic zip from the given files. */
function writeBundle(files: SubFile[], outPath: string): void {
  const out = new AdmZip();
  for (const file of [...files].sort((a, b) => a.path.localeCompare(b.path))) {
    out.addFile(file.path, file.data);
  }
  for (const entry of out.getEntries()) entry.header.time = FIXED_ZIP_DATE;
  out.writeZip(outPath);
}

/** Only write when content differs, so unchanged submissions create no diff. */
function writeIfChanged(path: string, content: string): void {
  if (existsSync(path) && readFileSync(path, "utf8") === content) return;
  writeFileSync(path, content, "utf8");
}

/** Recursively list every file under `dir`, with forward-slash relative paths. */
function listFiles(dir: string, baseDir = dir): SubFile[] {
  const out: SubFile[] = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...listFiles(full, baseDir));
    } else {
      out.push({ path: relative(baseDir, full).split(sep).join("/"), data: readFileSync(full) });
    }
  }
  return out;
}

/** Split a submission's files into skill.md, metadata.*, and bundled scripts. */
function classify(slug: string, label: string, files: SubFile[]): Submission {
  const sub: Submission = { slug, label, scripts: [] };
  // Prefer the shallowest skill.md / metadata.* if duplicated in subfolders.
  const byDepth = (a: SubFile, b: SubFile) =>
    a.path.split("/").length - b.path.split("/").length;
  const sorted = [...files].sort(byDepth);
  for (const file of sorted) {
    const base = posix.basename(file.path).toLowerCase();
    if (base === INSTRUCTIONS_NAME && sub.skillMd === undefined) {
      sub.skillMd = file.data.toString("utf8");
    } else if (METADATA_NAMES.includes(base) && sub.metaText === undefined) {
      sub.metaName = base;
      sub.metaText = file.data.toString("utf8");
    } else {
      sub.scripts.push(file);
    }
  }
  return sub;
}

/** Validate + generate one classified submission. */
function processSubmission(sub: Submission): ImportProblem | null {
  const { slug, label } = sub;
  if (sub.skillMd === undefined) {
    return { source: label, problems: [`no \`skill.md\` found`] };
  }
  if (sub.metaText === undefined) {
    return {
      source: label,
      problems: [`no metadata file found (expected ${METADATA_NAMES.join(" / ")})`],
    };
  }

  // skill.md → name + agent-facing description (its own frontmatter) + body.
  const parsed = matter(sub.skillMd);
  const skillFm = parsed.data as Record<string, unknown>;

  // metadata.* → catalog metadata for this gallery.
  let catalog: Record<string, unknown>;
  try {
    catalog = parseMetadataFile(sub.metaName!, sub.metaText);
  } catch (err) {
    return { source: label, problems: [`could not parse ${sub.metaName}: ${(err as Error).message}`] };
  }

  const problems: string[] = [];
  const slugName = skillFm.name as string | undefined;
  if (!slugName) {
    problems.push("`name` is required in skill.md frontmatter (must be a slug)");
  } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slugName)) {
    problems.push(
      `\`name\` in skill.md must be a slug (lowercase letters, numbers, and ` +
        `hyphens) \u2014 got "${slugName}"`,
    );
  } else if (slugName !== slug) {
    problems.push(
      `\`name\` in skill.md ("${slugName}") must match the submission ` +
        `folder/zip name ("${slug}")`,
    );
  }
  const agentDescription = skillFm.description as string | undefined;
  if (!agentDescription) {
    problems.push("`description` (agent-facing) is required in skill.md frontmatter");
  }
  if (!catalog.name) {
    problems.push("`name` (display name) is required in the metadata file");
  }
  if (!catalog.description) {
    problems.push("`description` (catalog) is required in the metadata file");
  }
  if (problems.length) return { source: label, problems };

  // Merge into the canonical frontmatter. The gallery `name` is the human display
  // name from metadata; the slug (skill.md `name`) is the file id used for the
  // route and the downloadable skill.md. The agent description gets its own key.
  const { name: displayName, description: catalogDescription, ...catalogRest } = catalog;
  const meta: Record<string, unknown> = {
    name: displayName,
    description: catalogDescription,
    agentDescription,
    ...catalogRest,
  };

  const hasBundle = sub.scripts.length > 0;
  if (hasBundle) meta.bundle = `bundles/${slug}.zip`;

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, parsed.content));
    if (hasBundle) {
      mkdirSync(BUNDLES_DIR, { recursive: true });
      writeBundle(sub.scripts, join(BUNDLES_DIR, `${slug}.zip`));
    }
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md` +
        (hasBundle ? ` (+ public/bundles/${slug}.zip)` : ""),
    );
  }
  return null;
}

/** Load a `submissions/<slug>/` folder. */
function loadFolder(dir: string): Submission {
  const slug = basename(dir);
  return classify(slug, `submissions/${slug}/`, listFiles(dir));
}

/** Load a `submissions/<slug>.zip`. */
function loadZip(zipPath: string): Submission {
  const slug = basename(zipPath).replace(/\.zip$/i, "");
  const files = new AdmZip(zipPath)
    .getEntries()
    .filter((e) => !e.isDirectory)
    .map((e) => ({ path: e.entryName.split("\\").join("/"), data: e.getData() }));
  return classify(slug, `submissions/${basename(zipPath)}`, files);
}

function main() {
  if (!existsSync(SUBMISSIONS_DIR)) {
    console.log("No submissions/ directory \u2014 nothing to import.");
    return;
  }

  const submissions: Submission[] = [];
  for (const name of readdirSync(SUBMISSIONS_DIR)) {
    if (name.startsWith(".") || name.startsWith("_")) continue; // _template, etc.
    const full = join(SUBMISSIONS_DIR, name);
    if (statSync(full).isDirectory()) {
      submissions.push(loadFolder(full));
    } else if (name.toLowerCase().endsWith(".zip")) {
      submissions.push(loadZip(full));
    }
  }

  if (submissions.length === 0) {
    console.log("No submissions found in submissions/.");
    return;
  }

  const problems: ImportProblem[] = [];
  for (const sub of submissions) {
    const p = processSubmission(sub);
    if (p) problems.push(p);
  }

  if (problems.length > 0) {
    console.error(`\n\u2717 ${problems.length} submission(s) failed validation:\n`);
    for (const p of problems) {
      console.error(`  ${p.source}:`);
      for (const msg of p.problems) console.error(`    \u2022 ${msg}`);
    }
    console.error(
      "\nEach submission needs skill.md (frontmatter `name` + agent-facing " +
        "`description`, then instructions) and a metadata file with a catalog " +
        "`description`, `platforms`, and `tags`. Fix the items above and retry.",
    );
    process.exit(1);
  }

  console.log(
    checkOnly
      ? `\nAll ${submissions.length} submission(s) passed validation (check-only, nothing written).`
      : `\nImported ${submissions.length} submission(s).`,
  );
}

main();
