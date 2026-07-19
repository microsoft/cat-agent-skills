import { getCollection } from "astro:content";
import { getRating } from "./ratings";
import type { BadgeSkill } from "./badges";

/**
 * The badge-relevant view of the skills collection, used by every build-time
 * surface that resolves badges (the contributors page, the poster page, and the
 * OG-image endpoint). The client-side reveal reads the same fields off
 * `/skills.json`, so all four stay in lockstep as long as they map identically.
 */
export async function loadBadgeSkills(): Promise<BadgeSkill[]> {
  const skills = await getCollection("skills");
  return skills.map((s) => ({
    slug: s.id,
    name: s.data.name,
    author: s.data.author,
    authorGithub: s.data.authorGithub ?? null,
    featured: s.data.featured,
    rating: getRating(s.id),
    createdAt: s.data.createdAt ?? null,
    platforms: s.data.platforms,
  }));
}
