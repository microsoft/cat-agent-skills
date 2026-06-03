import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

export async function getStaticPaths() {
  const skills = await getCollection("skills");
  return skills.map((skill) => ({ params: { slug: skill.id }, props: { skill } }));
}

function quote(value: string): string {
  return /[:#\[\]{},'"]/.test(value) ? JSON.stringify(value) : value;
}

export const GET: APIRoute = ({ props }) => {
  const { skill } = props as { skill: Awaited<ReturnType<typeof getCollection>>[number] };
  const d = skill.data as Record<string, unknown>;

  const lines: string[] = ["---"];
  lines.push(`name: ${quote(String(d.name))}`);
  lines.push(`description: ${quote(String(d.description))}`);
  if (Array.isArray(d.platforms) && d.platforms.length) {
    lines.push(`platforms: [${(d.platforms as string[]).map(quote).join(", ")}]`);
  }
  if (Array.isArray(d.tags) && d.tags.length) {
    lines.push(`tags: [${(d.tags as string[]).map(quote).join(", ")}]`);
  }
  if (d.author) lines.push(`author: ${quote(String(d.author))}`);
  if (d.version) lines.push(`version: ${quote(String(d.version))}`);
  if (d.bundle) lines.push(`bundle: ${quote(String(d.bundle))}`);
  lines.push("---", "");

  const frontmatter = lines.join("\n");
  const body = skill.body ?? "";

  return new Response(frontmatter + body, {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${skill.id}.md"`,
    },
  });
};
