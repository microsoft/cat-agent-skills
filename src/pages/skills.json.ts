import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { coverGradient, initials, type SkillSummary } from "../lib/skills";

export const GET: APIRoute = async () => {
  const skills = await getCollection("skills");

  const data: SkillSummary[] = skills
    .map((skill) => {
      const d = skill.data;
      return {
        slug: skill.id,
        name: d.name,
        description: d.description,
        platforms: d.platforms,
        tags: d.tags,
        author: d.author,
        version: d.version,
        hasBundle: Boolean(d.bundle),
        featured: d.featured,
        gradient: coverGradient(skill.id, d.coverColor),
        initials: initials(d.name),
      };
    })
    .sort((a, b) => {
      if (a.featured !== b.featured) return a.featured ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" },
  });
};
