import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { PLATFORMS } from "./lib/skills";

const skills = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/skills" }),
  schema: z.object({
    name: z.string(),
    description: z.string(),
    // Agent platform(s) the skill targets: Cowork, Copilot Studio, and/or Scout.
    platforms: z.array(z.enum(PLATFORMS)).nonempty(),
    tags: z.array(z.string()).default([]),
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
  }),
});

export const collections = { skills };
