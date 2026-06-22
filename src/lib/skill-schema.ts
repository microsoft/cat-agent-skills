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
  description: z.string(),
  // Agent platform(s) the skill targets: Cowork, Copilot Studio, and/or Scout.
  platforms: z.array(z.enum(PLATFORMS)).nonempty(),
  tags: z.array(z.string()).nonempty(),
  author: z.string().optional(),
  version: z.string().optional(),
  createdAt: z.coerce.date().optional(),
  updatedAt: z.coerce.date().optional(),
  // Path (relative to /public) of a bundled .zip of scripts, when the skill
  // ships executable scripts alongside its instructions.
  bundle: z.string().optional(),
  // Optional override for the auto-generated cover color (any CSS color).
  coverColor: z.string().optional(),
  featured: z.boolean().default(false),
});

export type SkillFrontmatter = z.infer<typeof skillSchema>;
