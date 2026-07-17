import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { skillSchema } from "./lib/skill-schema";

const skills = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/skills" }),
  schema: skillSchema,
});

// Optional human-facing "overview" for an entry, generated from a
// submission's README.md. Keyed by the same slug as its skill so the detail page
// can look it up. Plain markdown — any frontmatter is ignored.
const guides = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/guides" }),
  schema: z.object({}).passthrough(),
});

export const collections = { skills, guides };
