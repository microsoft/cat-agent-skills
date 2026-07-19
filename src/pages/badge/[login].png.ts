import type { APIRoute, GetStaticPaths } from "astro";
import { allAuthors, resolveBadge, posterTiles } from "../../lib/badges";
import { loadBadgeSkills } from "../../lib/badge-data";
import { renderBadgePng } from "../../lib/badge-poster";

export const getStaticPaths: GetStaticPaths = async () => {
  const skills = await loadBadgeSkills();
  return allAuthors(skills)
    .map((stats) => {
      const resolved = resolveBadge(stats.login, skills);
      if (!resolved) return null;
      return {
        params: { login: stats.login },
        props: {
          login: stats.login,
          title: resolved.badge.title,
          image: resolved.badge.image,
          caption: resolved.caption,
          tiles: posterTiles(resolved.badge, resolved.stats),
        },
      };
    })
    .filter((p): p is NonNullable<typeof p> => p !== null);
};

function siteLabelFrom(site: URL | undefined): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  const host = site?.host ?? "microsoft.github.io";
  return `${host}${base}`;
}

export const GET: APIRoute = async ({ props, site }) => {
  const png = await renderBadgePng({
    login: props.login,
    title: props.title,
    image: props.image,
    caption: props.caption,
    tiles: props.tiles,
    siteLabel: siteLabelFrom(site),
  });
  return new Response(new Uint8Array(png), {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=86400",
    },
  });
};
