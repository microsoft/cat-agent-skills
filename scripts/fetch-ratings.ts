/**
 * Fetch skill ratings (👍 reactions) from GitHub Discussions and write a
 * build-time snapshot to `src/data/ratings.json`.
 *
 * Each skill maps to one Discussion whose title is the skill slug (giscus
 * `mapping="specific"`, `term=slug`). The rating is the number of THUMBS_UP
 * reactions on that Discussion. The homepage uses this snapshot to sort skills
 * by rating; the live vote is reflected on the next build/scheduled rebuild.
 *
 * Usage:
 *   GITHUB_TOKEN=... npm run ratings:fetch
 *
 * Config (env, with sensible defaults):
 *   GITHUB_TOKEN            token with `read:discussion` / repo read scope
 *   GISCUS_REPO             owner/repo (default: microsoft/cat-agent-skills)
 *   GISCUS_CATEGORY         Discussion category name (default: "Skill Ratings")
 *
 * This script is intentionally NON-FATAL: any problem (missing token, network
 * error, Discussions disabled, category missing) results in an empty/unchanged
 * snapshot and a warning — never a failed build.
 */
import { writeFileSync, mkdirSync, existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = resolve(dirname(fileURLToPath(import.meta.url)), "../src/data/ratings.json");

const REPO = process.env.GISCUS_REPO ?? "microsoft/cat-agent-skills";
const CATEGORY = process.env.GISCUS_CATEGORY ?? "Announcements";
const TOKEN = process.env.GITHUB_TOKEN ?? process.env.GH_TOKEN ?? "";

/** Skill slugs: 1-64 chars, lowercase alnum + single hyphens (agentskills spec). */
const SLUG_RE = /^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$/;

type Ratings = Record<string, number>;

function warn(msg: string): void {
  console.warn(`[fetch-ratings] ${msg}`);
}

/** Write the snapshot without clobbering an existing one when we found nothing. */
function persist(ratings: Ratings, { allowEmpty }: { allowEmpty: boolean }): void {
  mkdirSync(dirname(OUT), { recursive: true });
  if (Object.keys(ratings).length === 0 && !allowEmpty && existsSync(OUT)) {
    warn("no ratings found; keeping existing snapshot.");
    return;
  }
  const sorted: Ratings = {};
  for (const key of Object.keys(ratings).sort()) sorted[key] = ratings[key];
  writeFileSync(OUT, JSON.stringify(sorted, null, 2) + "\n");
  console.log(`[fetch-ratings] wrote ${Object.keys(sorted).length} rating(s) to ${OUT}`);
}

async function graphql<T>(query: string, variables: Record<string, unknown>): Promise<T> {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "cat-agent-skills-ratings",
    },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) throw new Error(`GitHub GraphQL HTTP ${res.status}: ${await res.text()}`);
  const json = (await res.json()) as { data?: T; errors?: Array<{ message: string }> };
  if (json.errors?.length) throw new Error(json.errors.map((e) => e.message).join("; "));
  if (!json.data) throw new Error("GitHub GraphQL returned no data");
  return json.data;
}

type DiscussionsPage = {
  repository: {
    discussions: {
      pageInfo: { hasNextPage: boolean; endCursor: string | null };
      nodes: Array<{
        title: string;
        reactionGroups: Array<{
          content: string;
          reactors: { totalCount: number };
        }>;
      }>;
    };
  } | null;
};

const QUERY = `
  query ($owner: String!, $name: String!, $after: String) {
    repository(owner: $owner, name: $name) {
      discussions(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          title
          category { name }
          reactionGroups {
            content
            reactors { totalCount }
          }
        }
      }
    }
  }
`;

type ReactionGroup = { content: string; reactors: { totalCount: number } };

function thumbsUp(groups: ReactionGroup[] | undefined): number {
  const group = (groups ?? []).find((g) => g.content === "THUMBS_UP");
  return group?.reactors?.totalCount ?? 0;
}

async function main(): Promise<void> {
  if (!TOKEN) {
    warn("no GITHUB_TOKEN set; leaving ratings snapshot unchanged.");
    persist({}, { allowEmpty: false });
    return;
  }
  const [owner, name] = REPO.split("/");
  if (!owner || !name) {
    warn(`invalid GISCUS_REPO "${REPO}"; expected owner/repo.`);
    persist({}, { allowEmpty: false });
    return;
  }

  const ratings: Ratings = {};
  let after: string | null = null;
  try {
    do {
      const data: DiscussionsPage = await graphql<DiscussionsPage>(QUERY, { owner, name, after });
      const conn = data.repository?.discussions;
      if (!conn) break;
      for (const node of conn.nodes as any[]) {
        if (node.category?.name !== CATEGORY) continue;
        const slug = node.title.trim();
        // Only slug-shaped titles are skill discussions. This keeps the welcome
        // post and any real announcements (we share the Announcements category)
        // out of the ratings snapshot.
        if (!SLUG_RE.test(slug)) continue;
        ratings[slug] = (ratings[slug] ?? 0) + thumbsUp(node.reactionGroups);
      }
      after = conn.pageInfo.hasNextPage ? conn.pageInfo.endCursor : null;
    } while (after);
  } catch (err) {
    warn(`failed to fetch discussions: ${(err as Error).message}`);
    persist({}, { allowEmpty: false });
    return;
  }

  persist(ratings, { allowEmpty: true });
}

// Ensure a valid file exists even if something truly unexpected happens.
try {
  await main();
} catch (err) {
  warn(`unexpected error: ${(err as Error).message}`);
  if (!existsSync(OUT)) writeFileSync(OUT, "{}\n");
  else {
    try {
      JSON.parse(readFileSync(OUT, "utf8"));
    } catch {
      writeFileSync(OUT, "{}\n");
    }
  }
}
