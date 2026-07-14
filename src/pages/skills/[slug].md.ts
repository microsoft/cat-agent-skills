import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

export async function getStaticPaths() {
  const skills = await getCollection("skills");
  // Plugins ship as an M365 .zip package and automations ship as a Scout .json,
  // not a single SKILL.md, so neither exposes a `.md` download route.
  return skills
    .filter((skill) => skill.data.type !== "plugin" && skill.data.type !== "automation")
    .map((skill) => ({ params: { slug: skill.id }, props: { skill } }));
}

function quote(value: string): string {
  return /[:#\[\]{},'"]/.test(value) ? JSON.stringify(value) : value;
}

export const GET: APIRoute = ({ props }) => {
  const { skill } = props as { skill: Awaited<ReturnType<typeof getCollection>>[number] };
  const d = skill.data as Record<string, unknown>;

  const lines: string[] = ["---"];
  // Copilot Studio / Agent Skills expect a slug-style identifier for `name`
  // (the display name lives in the gallery's catalog metadata).
  lines.push(`name: ${quote(skill.id)}`);
  // The downloadable file is the canonical Agent Skills artifact `SKILL.md`: it
  // carries only `name` + the agent-facing `description` (catalog metadata stays
  // on the gallery page). Fall back to the catalog summary if no agent description.
  lines.push(`description: ${quote(String(d.agentDescription ?? d.description))}`);
  lines.push("---", "");

  const frontmatter = lines.join("\n");
  const body = skill.body ?? "";

  return new Response(frontmatter + body, {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="SKILL.md"`,
    },
  });
};
