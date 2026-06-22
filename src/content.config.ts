import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { skillSchema } from "./lib/skill-schema";

const skills = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/skills" }),
  schema: skillSchema,
});

export const collections = { skills };
