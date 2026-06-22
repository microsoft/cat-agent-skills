/**
 * Validate a skill's frontmatter against the shared Zod schema.
 *
 * Usage:
 *   tsx scripts/validate-skill.ts <file.md> [more.md ...]
 *
 * Exits non-zero and prints an itemized list of problems if any file fails.
 * Used both locally (`npm run validate:skills`) and by the import pipeline so
 * the rules can never drift from the Astro build-time content schema.
 */
import { readFileSync } from "node:fs";
import { basename } from "node:path";
import matter from "gray-matter";
import { skillSchema } from "../src/lib/skill-schema.ts";

/** Result of validating a single markdown source. */
export type ValidationResult = {
  /** Human-readable label (file path) for messages. */
  label: string;
  ok: boolean;
  /** Itemized, human-readable problems (empty when ok). */
  problems: string[];
};

/**
 * Validate a raw markdown string (frontmatter + body) for one skill.
 * Returns ok=true or an itemized problem list on failure.
 */
export function validateSkillSource(
  source: string,
  label: string,
): ValidationResult {
  let data: Record<string, unknown>;
  try {
    data = matter(source).data;
  } catch (err) {
    return {
      label,
      ok: false,
      problems: [`could not parse frontmatter: ${(err as Error).message}`],
    };
  }

  if (!data || Object.keys(data).length === 0) {
    return {
      label,
      ok: false,
      problems: ["no YAML frontmatter found (expected a `---` block at the top)"],
    };
  }

  const result = skillSchema.safeParse(data);
  if (result.success) return { label, ok: true, problems: [] };

  const problems = result.error.issues.map((issue) => {
    const field = issue.path.length ? issue.path.join(".") : "(root)";
    return `${field}: ${issue.message}`;
  });
  return { label, ok: false, problems };
}

/** Validate a markdown file on disk. */
export function validateSkillFile(path: string): ValidationResult {
  const source = readFileSync(path, "utf8");
  return validateSkillSource(source, path);
}

function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error("usage: tsx scripts/validate-skill.ts <file.md> [more.md ...]");
    process.exit(2);
  }

  let failures = 0;
  for (const file of files) {
    const result = validateSkillFile(file);
    if (result.ok) {
      console.log(`\u2713 ${basename(file)} \u2014 metadata OK`);
    } else {
      failures++;
      console.error(`\u2717 ${file} \u2014 invalid metadata:`);
      for (const p of result.problems) console.error(`    \u2022 ${p}`);
    }
  }

  if (failures > 0) {
    console.error(
      `\n${failures} skill(s) failed metadata validation. ` +
        `Fix the fields above and try again.`,
    );
    process.exit(1);
  }
  console.log(`\nAll ${files.length} skill(s) passed metadata validation.`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
