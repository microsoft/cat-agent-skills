/**
 * Single source of truth for the skill frontmatter schema.
 *
 * Imported by both the Astro content collection (`src/content.config.ts`) and
 * the standalone CI validator (`scripts/validate-skill.mjs`) so that the rules
 * enforced at build time and at submission time can never drift apart.
 */
import { z } from "astro/zod";
import { PLATFORMS } from "./skills";

/** Zod schema for a skill's frontmatter metadata. */
export const skillSchema = z.object({
  name: z.string(),
  // Catalog/gallery summary shown to humans on the card, search, and the top of
  // the detail page. Comes from metadata.json.
  description: z.string(),
  // The agent-facing description the model reads to decide when to invoke the
  // skill. Comes from the `description` in SKILL.md's own frontmatter (the
  // canonical Agent Skills format). Optional so older catalog-only skills still
  // validate.
  agentDescription: z.string().optional(),
  // Agent platform(s) the skill targets: Cowork, Copilot Studio, and/or Scout.
  platforms: z.array(z.enum(PLATFORMS)).nonempty(),
  tags: z.array(z.string()).nonempty(),
  author: z.string().optional(),
  // Optional URL to the author's website / profile, shown as a link on the
  // skill page when an `author` is also present.
  authorUrl: z.string().url().optional(),
  version: z.string().optional(),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
  // Path (relative to /public) of a bundled .zip of the skill's files, when the
  // skill ships more than its SKILL.md (scripts, references, assets).
  bundle: z.string().optional(),
  // Optional override for the auto-generated cover color (any CSS color).
  coverColor: z.string().optional(),
  featured: z.boolean().default(false),
});

export type SkillFrontmatter = z.infer<typeof skillSchema>;
