import type { APIRoute, GetStaticPaths } from "astro";
import { allAuthors, posterTiles, resolveBadges } from "../../../lib/badges";
import { loadBadgeSkills } from "../../../lib/badge-data";
import { renderBadgePng } from "../../../lib/badge-poster";

export const getStaticPaths: GetStaticPaths = async () => {
  const skills = await loadBadgeSkills();
  return allAuthors(skills).flatMap((stats) =>
    resolveBadges(stats.login, skills).map((resolved) => ({
      params: { login: stats.login, badge: resolved.badge.id },
      props: {
        login: stats.login,
        title: resolved.badge.title,
        image: resolved.badge.image,
        caption: resolved.caption,
        tiles: posterTiles(resolved.badge, resolved.stats),
      },
    })),
  );
};

function siteLabelFrom(site: URL | undefined): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  return `${site?.host ?? "microsoft.github.io"}${base}`;
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
