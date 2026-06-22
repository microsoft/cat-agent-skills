/**
 * Import skill submission zips into the site content.
 *
 * For each `submissions/<slug>.zip` this script:
 *   1. Unzips it in memory.
 *   2. Locates the front-page `SKILL.md` (the skill instructions + metadata).
 *   3. Validates the frontmatter against the shared schema (HARD FAIL on error).
 *   4. Writes `src/content/skills/<slug>.md`.
 *   5. Re-zips any remaining files (scripts) into `public/bundles/<slug>.zip`
 *      and injects `bundle: bundles/<slug>.zip` into the frontmatter.
 *
 * Usage:
 *   tsx scripts/import-submissions.ts            # import everything
 *   tsx scripts/import-submissions.ts --check    # validate only, write nothing
 *
 * Slug = the zip filename without its extension (matches the existing rule
 * where a content filename maps directly to the URL slug).
 */
import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import AdmZip from "adm-zip";
import { validateSkillSource } from "./validate-skill.ts";

const ROOT = join(import.meta.dirname, "..");
const SUBMISSIONS_DIR = join(ROOT, "submissions");
const CONTENT_DIR = join(ROOT, "src", "content", "skills");
const BUNDLES_DIR = join(ROOT, "public", "bundles");
const FRONT_PAGE = "skill.md";

const checkOnly = process.argv.includes("--check");

type ImportProblem = { zip: string; problems: string[] };

/** Find the front-page SKILL.md entry, preferring the shallowest path. */
function findFrontPage(zip: AdmZip): AdmZip.IZipEntry | undefined {
  const candidates = zip
    .getEntries()
    .filter(
      (e) => !e.isDirectory && basename(e.entryName).toLowerCase() === FRONT_PAGE,
    )
    .sort((a, b) => a.entryName.split("/").length - b.entryName.split("/").length);
  return candidates[0];
}

/** Inject a `bundle:` line into a frontmatter block if not already present. */
function injectBundle(source: string, bundlePath: string): string {
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return source; // validation will have already failed
  if (/^bundle\s*:/m.test(match[1])) return source; // author set it explicitly
  const newBlock = `---\n${match[1]}\nbundle: ${bundlePath}\n---`;
  return source.replace(match[0], newBlock);
}

function importZip(zipPath: string): ImportProblem | null {
  const slug = basename(zipPath).replace(/\.zip$/i, "");
  const label = `submissions/${basename(zipPath)}`;
  const zip = new AdmZip(zipPath);

  const frontEntry = findFrontPage(zip);
  if (!frontEntry) {
    return {
      zip: label,
      problems: [
        `no front-page \`SKILL.md\` found at the zip root (required for every submission)`,
      ],
    };
  }

  let source = zip.readAsText(frontEntry);

  // Validate metadata first — hard fail before writing anything.
  const result = validateSkillSource(source, label);
  if (!result.ok) {
    return { zip: label, problems: result.problems };
  }

  // Everything that is not the front page becomes the downloadable bundle.
  const scriptEntries = zip
    .getEntries()
    .filter((e) => !e.isDirectory && e.entryName !== frontEntry.entryName);

  const hasBundle = scriptEntries.length > 0;
  if (hasBundle) {
    source = injectBundle(source, `bundles/${slug}.zip`);
  }

  if (checkOnly) return null;

  // Write the content markdown.
  mkdirSync(CONTENT_DIR, { recursive: true });
  writeFileSync(join(CONTENT_DIR, `${slug}.md`), source, "utf8");

  // Build the bundle zip from the leftover files.
  if (hasBundle) {
    mkdirSync(BUNDLES_DIR, { recursive: true });
    const out = new AdmZip();
    for (const entry of scriptEntries) {
      out.addFile(entry.entryName, entry.getData());
    }
    out.writeZip(join(BUNDLES_DIR, `${slug}.zip`));
  }

  console.log(
    `\u2713 ${label} \u2192 src/content/skills/${slug}.md` +
      (hasBundle ? ` (+ public/bundles/${slug}.zip)` : ""),
  );
  return null;
}

function main() {
  if (!existsSync(SUBMISSIONS_DIR)) {
    console.log("No submissions/ directory \u2014 nothing to import.");
    return;
  }

  const zips = readdirSync(SUBMISSIONS_DIR)
    .filter((f) => f.toLowerCase().endsWith(".zip"))
    .map((f) => join(SUBMISSIONS_DIR, f));

  if (zips.length === 0) {
    console.log("No submission zips found in submissions/.");
    return;
  }

  const problems: ImportProblem[] = [];
  for (const zip of zips) {
    const problem = importZip(zip);
    if (problem) problems.push(problem);
  }

  if (problems.length > 0) {
    console.error(`\n\u2717 ${problems.length} submission(s) failed validation:\n`);
    for (const p of problems) {
      console.error(`  ${p.zip}:`);
      for (const msg of p.problems) console.error(`    \u2022 ${msg}`);
    }
    console.error(
      "\nEvery submission needs a front-page SKILL.md with valid metadata " +
        "(name, description, platforms, tags). Fix the items above and retry.",
    );
    process.exit(1);
  }

  console.log(
    checkOnly
      ? `\nAll ${zips.length} submission(s) passed validation (check-only, nothing written).`
      : `\nImported ${zips.length} submission(s).`,
  );
}

main();
