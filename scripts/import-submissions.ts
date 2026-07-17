/**
 * Import skill submissions into the site content.
 *
 * Every skill is contributed as a `submissions/<slug>/` folder holding a
 * `metadata.json` gallery sidecar plus EXACTLY ONE skill payload, in one of two
 * shapes:
 *
 *   submissions/<slug>/
 *   ├── metadata.json  (or metadata.yaml) Catalog metadata for THIS gallery:
 *   │                  `description` (the human catalog/gallery summary),
 *   │                  `platforms`, `tags`, `author`, `authorUrl`, `version`…
 *   │                  (`authorGithub`, the PR submitter's login, is stamped
 *   │                  automatically by CI — see PR_AUTHOR below — not authored.)
 *   │                  It is a SIDECAR — never packaged into the download bundle.
 *   └── EITHER an unpacked canonical Agent Skill:
 *   │     ├── SKILL.md     frontmatter `name` + `description` (the AGENT-facing
 *   │     │                description the model reads to decide when to invoke
 *   │     │                the skill), followed by the instructions body.
 *   │     ├── scripts/     optional executable code
 *   │     ├── references/  optional docs
 *   │     └── assets/      optional templates / data files
 *   │   OR a pre-packaged bundle:
 *         └── <name>.zip   a canonical Agent Skill (root SKILL.md + files).
 *
 * The two descriptions are deliberately separate:
 *   - SKILL.md frontmatter `description`  → `agentDescription` (what the agent reads)
 *   - metadata.json `description`         → `description`      (what the gallery shows)
 *
 * For every submission this script validates the merged metadata against the
 * shared schema (HARD FAIL on error), then generates the canonical
 * `src/content/skills/<slug>.md` (which authors never edit by hand). Any skill
 * that ships files beyond SKILL.md also gets a deterministic
 * `public/bundles/<slug>.zip`, with `bundle:` injected into the frontmatter.
 *
 * Bundling is VERBATIM — no file classification logic. An unpacked skill is
 * zipped exactly as authored (minus the metadata sidecar); a packed submission
 * is exploded, its root SKILL.md validated, then re-bundled deterministically
 * from the exploded contents (so the output can never contain metadata.json).
 *
 * Usage:
 *   tsx scripts/import-submissions.ts            # import everything
 *   tsx scripts/import-submissions.ts --check    # validate only, write nothing
 */
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { basename, join, posix, relative, sep } from "node:path";
import AdmZip from "adm-zip";
import matter from "gray-matter";
import { validateSkillData } from "./validate-skill.ts";
import {
  validateAutomationData,
  validateAutomationInstallerFiles,
  isAutomationInstaller,
  type AutomationDigest,
} from "./validate-automation.ts";
import {
  isPluginPackage,
  validatePluginFiles,
  type PluginConnector,
  type PluginSkill,
} from "./validate-plugin.ts";

const ROOT = join(import.meta.dirname, "..");
const SUBMISSIONS_DIR = join(ROOT, "submissions");
const CONTENT_DIR = join(ROOT, "src", "content", "skills");
const BUNDLES_DIR = join(ROOT, "public", "bundles");

// Instruction file match key. Compared against a lowercased basename, so it
// matches the canonical `SKILL.md` (and a legacy lowercase `skill.md`). The
// generated bundle always emits it as uppercase `SKILL.md`.
const INSTRUCTIONS_NAME = "skill.md";
const METADATA_NAMES = ["metadata.json", "metadata.yaml", "metadata.yml"];
// Canonical name emitted for the instruction file inside every download bundle.
const BUNDLE_INSTRUCTIONS_NAME = "SKILL.md";
// Fixed timestamp so generated bundle zips are byte-for-byte reproducible.
// adm-zip encodes the DOS time from the Date's *local* components, so this must
// be built from local components (not a UTC instant) to stay identical across
// timezones (e.g. a contributor's machine vs. CI running in UTC).
const FIXED_ZIP_DATE = new Date(2000, 0, 1, 0, 0, 0);
// Order in which frontmatter keys are emitted for generated content files.
const FIELD_ORDER = [
  "name",
  "description",
  "agentDescription",
  "platforms",
  "type",
  "tags",
  "author",
  "authorUrl",
  "authorGithub",
  "version",
  "createdAt",
  "updatedAt",
  "coverColor",
  "featured",
  "bundle",
];

const checkOnly = process.argv.includes("--check");

type ImportProblem = { source: string; problems: string[] };
/** A file inside a submission, with a forward-slash relative path. */
type SubFile = { path: string; data: Buffer };
/** A loaded submission (folder or packed zip), before parsing/validation. */
type Submission = {
  slug: string;
  label: string;
  /** "skill" (default), a Cowork "plugin", or a Scout "automation". */
  kind: "skill" | "plugin" | "automation";
  skillMd?: string;
  metaName?: string;
  metaText?: string;
  /** For an automation: the raw Scout automation `.json`, shipped verbatim. */
  automationJson?: string;
  automationJsonName?: string;
  /**
   * True when the automation payload is an installer `.zip` (an `INSTALL.md`
   * plus JSON config file(s)) rather than a bare importable `.json`. Its
   * `installerFiles` ship verbatim as the download and `installerInstall`
   * (the INSTALL.md contents) becomes the detail-page body.
   */
  installer?: boolean;
  installerInstall?: string;
  installerFiles?: SubFile[];
  /**
   * Every file that ships in the download bundle, at its authored path
   * (excluding the `metadata.*` sidecar and the root instruction file, which is
   * re-emitted as `SKILL.md`). Packaged verbatim — no reclassification.
   */
  bundleFiles: SubFile[];
  /**
   * For a plugin: the exploded M365 app-package files (manifest.json, icons,
   * skills/…), verbatim minus any metadata sidecar. Shipped as the download.
   */
  pluginFiles?: SubFile[];
  /** Problems detected while loading (e.g. ambiguous or missing payload). */
  loadProblems?: string[];
};

function quote(value: string): string {
  return /[:#\[\]{},'"]|^\s|\s$/.test(value) ? JSON.stringify(value) : value;
}

function formatScalar(value: unknown): string {
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  if (typeof value === "boolean" || typeof value === "number") return String(value);
  return quote(String(value));
}

/** Serialize a metadata object into a deterministic YAML frontmatter block. */
function serializeFrontmatter(meta: Record<string, unknown>): string {
  const keys = [
    ...FIELD_ORDER.filter((k) => k in meta),
    ...Object.keys(meta).filter((k) => !FIELD_ORDER.includes(k)),
  ];
  const lines = ["---"];
  for (const key of keys) {
    const value = meta[key];
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      lines.push(`${key}: [${value.map((v) => formatScalar(v)).join(", ")}]`);
    } else {
      lines.push(`${key}: ${formatScalar(value)}`);
    }
  }
  lines.push("---", "");
  return lines.join("\n");
}

/** Build a content markdown file from metadata + an instructions body. */
function buildContent(meta: Record<string, unknown>, body: string): string {
  return serializeFrontmatter(meta) + body.replace(/^\s+/, "");
}

/**
 * Resolve the skill author's GitHub handle (the PR submitter's login), used by
 * the "skillbot" to @-mention them on the first discussion comment. Set-once:
 *   1. Keep an explicit `authorGithub` already in the metadata.
 *   2. Otherwise preserve the value already stamped in the generated
 *      `src/content/skills/<slug>.md` (so a later, unrelated PR can never
 *      overwrite the original submitter).
 *   3. Otherwise fall back to `PR_AUTHOR` (set by CI on same-repo PRs) — this is
 *      a skill newly added in the current pull request.
 *   4. Otherwise leave it unset (e.g. local imports, fork PRs).
 * The result is mutated onto `meta` so every publish path stamps it uniformly.
 */
function resolveAuthorGithub(slug: string, meta: Record<string, unknown>): void {
  if (typeof meta.authorGithub === "string" && meta.authorGithub.trim()) {
    meta.authorGithub = meta.authorGithub.trim();
    return;
  }
  const existingPath = join(CONTENT_DIR, `${slug}.md`);
  if (existsSync(existingPath)) {
    try {
      const prior = matter(readFileSync(existingPath, "utf8")).data as {
        authorGithub?: unknown;
      };
      if (typeof prior.authorGithub === "string" && prior.authorGithub.trim()) {
        meta.authorGithub = prior.authorGithub.trim();
        return;
      }
    } catch {
      // Unparseable existing file: fall through to the PR-author fallback.
    }
  }
  const prAuthor = process.env.PR_AUTHOR?.trim();
  if (prAuthor) meta.authorGithub = prAuthor;
}

/** Parse a metadata file (JSON or YAML) into a plain object. */
function parseMetadataFile(name: string, text: string): Record<string, unknown> {
  if (name.toLowerCase().endsWith(".json")) return JSON.parse(text);
  // Reuse gray-matter's YAML engine by wrapping the text as frontmatter.
  return matter(`---\n${text}\n---\n`).data;
}

/** Write a deterministic zip from the given files. */
function writeBundle(files: SubFile[], outPath: string): void {
  const out = new AdmZip();
  for (const file of [...files].sort((a, b) => a.path.localeCompare(b.path))) {
    out.addFile(file.path, file.data);
  }
  for (const entry of out.getEntries()) entry.header.time = FIXED_ZIP_DATE;
  out.writeZip(outPath);
}

/** Only write when content differs, so unchanged submissions create no diff. */
function writeIfChanged(path: string, content: string): void {
  if (existsSync(path) && readFileSync(path, "utf8") === content) return;
  writeFileSync(path, content, "utf8");
}

/** Recursively list every file under `dir`, with forward-slash relative paths. */
function listFiles(dir: string, baseDir = dir): SubFile[] {
  const out: SubFile[] = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...listFiles(full, baseDir));
    } else {
      out.push({ path: relative(baseDir, full).split(sep).join("/"), data: readFileSync(full) });
    }
  }
  return out;
}

/**
 * Split a payload's files into the root SKILL.md, the metadata sidecar, and the
 * verbatim bundle files. No reclassification: every file that is not the root
 * instruction file or a metadata sidecar ships in the bundle at its authored
 * path. `metadata.*` is only adopted as the catalog source if one was not
 * already provided alongside the payload (it is never bundled either way).
 */
function classifyPayload(sub: Submission, files: SubFile[]): void {
  // Prefer the shallowest SKILL.md / metadata.* if duplicated in subfolders.
  const byDepth = (a: SubFile, b: SubFile) =>
    a.path.split("/").length - b.path.split("/").length;
  const sorted = [...files].sort(byDepth);
  for (const file of sorted) {
    const base = posix.basename(file.path).toLowerCase();
    const isRoot = !file.path.includes("/");
    if (base === INSTRUCTIONS_NAME && isRoot && sub.skillMd === undefined) {
      sub.skillMd = file.data.toString("utf8");
    } else if (METADATA_NAMES.includes(base)) {
      // Sidecar — never bundled. Adopt as catalog source only if not already set.
      if (sub.metaText === undefined) {
        sub.metaName = base;
        sub.metaText = file.data.toString("utf8");
      }
    } else {
      sub.bundleFiles.push(file);
    }
  }
}

/** Validate + generate one classified submission. */
function processSubmission(sub: Submission): ImportProblem | null {
  const { slug, label } = sub;
  if (sub.loadProblems?.length) {
    return { source: label, problems: sub.loadProblems };
  }
  if (sub.kind === "plugin") return processPlugin(sub);
  if (sub.kind === "automation") return processAutomation(sub);
  if (sub.skillMd === undefined) {
    return {
      source: label,
      problems: ["no root-level `SKILL.md` found in the submission payload"],
    };
  }
  if (sub.metaText === undefined) {
    return {
      source: label,
      problems: [
        `no metadata sidecar found next to the payload ` +
          `(expected ${METADATA_NAMES.join(" / ")})`,
      ],
    };
  }

  // SKILL.md → name + agent-facing description (its own frontmatter) + body.
  const parsed = matter(sub.skillMd);
  const skillFm = parsed.data as Record<string, unknown>;

  // metadata.* → catalog metadata for this gallery.
  let catalog: Record<string, unknown>;
  try {
    catalog = parseMetadataFile(sub.metaName!, sub.metaText);
  } catch (err) {
    return { source: label, problems: [`could not parse ${sub.metaName}: ${(err as Error).message}`] };
  }

  const problems: string[] = [];
  const slugName = skillFm.name as string | undefined;
  if (!slugName) {
    problems.push("`name` is required in SKILL.md frontmatter (must be a slug)");
  } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slugName)) {
    problems.push(
      `\`name\` in SKILL.md must be a slug (lowercase letters, numbers, and ` +
        `hyphens) \u2014 got "${slugName}"`,
    );
  } else if (slugName !== slug) {
    problems.push(
      `\`name\` in SKILL.md ("${slugName}") must match the submission ` +
        `folder name ("${slug}")`,
    );
  }
  const agentDescription = skillFm.description as string | undefined;
  if (!agentDescription) {
    problems.push("`description` (agent-facing) is required in SKILL.md frontmatter");
  }
  if (!catalog.name) {
    problems.push("`name` (display name) is required in the metadata file");
  }
  if (!catalog.description) {
    problems.push("`description` (catalog) is required in the metadata file");
  }
  if (problems.length) return { source: label, problems };

  // Merge into the canonical frontmatter. The gallery `name` is the human display
  // name from metadata; the slug (SKILL.md `name`) is the file id used for the
  // route and the downloadable SKILL.md. The agent description gets its own key.
  const { name: displayName, description: catalogDescription, ...catalogRest } = catalog;
  const meta: Record<string, unknown> = {
    name: displayName,
    description: catalogDescription,
    agentDescription,
    ...catalogRest,
  };

  const hasBundle = sub.bundleFiles.length > 0;
  if (hasBundle) meta.bundle = `bundles/${slug}.zip`;

  resolveAuthorGithub(slug, meta);

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, parsed.content));
    if (hasBundle) {
      mkdirSync(BUNDLES_DIR, { recursive: true });
      // The bundle is the canonical Agent Skill: a root-level SKILL.md (what
      // agent-skill uploaders require) plus every payload file verbatim.
      const bundleFiles: SubFile[] = [
        { path: BUNDLE_INSTRUCTIONS_NAME, data: Buffer.from(sub.skillMd, "utf8") },
        ...sub.bundleFiles,
      ];
      writeBundle(bundleFiles, join(BUNDLES_DIR, `${slug}.zip`));
    }
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md` +
        (hasBundle ? ` (+ public/bundles/${slug}.zip)` : ""),
    );
  }
  return null;
}

/**
 * Build the synthesized detail-page body for a Cowork plugin. There is no single
 * SKILL.md to show, so we render an overview, the contained skills/connectors,
 * and how to install the package on Cowork.
 */
function buildPluginBody(opts: {
  overview: string;
  skills: PluginSkill[];
  connectors: PluginConnector[];
}): string {
  const { overview, skills, connectors } = opts;
  const lines: string[] = [overview.trim(), ""];
  lines.push(
    "> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app " +
      "package (a `.zip` bundling the skills and connectors below). It installs " +
      "on Cowork only.",
    "",
  );
  if (skills.length) {
    lines.push("## Skills in this plugin", "");
    for (const s of skills) {
      const desc = s.description ? ` \u2014 ${s.description.trim()}` : "";
      lines.push(`- **${s.name}**${desc}`);
    }
    lines.push("");
  }
  if (connectors.length) {
    lines.push("## Connectors", "");
    for (const c of connectors) {
      const title = c.displayName ?? c.id ?? "connector";
      const idPart = c.id && c.displayName ? ` (\`${c.id}\`)` : "";
      const desc = c.description ? ` \u2014 ${c.description.trim()}` : "";
      lines.push(`- **${title}**${idPart}${desc}`);
    }
    lines.push("");
  }
  lines.push(
    "## Install",
    "",
    "1. Download the plugin package (the `.zip` on this page).",
    "2. Upload it to your tenant via **M365 admin center \u203a Manage apps \u203a " +
      "Upload custom app**, or sideload it for testing with the " +
      "[Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) " +
      "(`atk install --file-path <zip> --scope Personal`).",
    "3. Open **Cowork \u203a Sources & Skills \u203a Plugins** and enable it from the " +
      "**Discover** section.",
    "",
    "See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) " +
      "for details.",
  );
  return lines.join("\n") + "\n";
}

/**
 * Validate + generate a Cowork plugin submission: a pre-built M365 app-package
 * `.zip` (root `manifest.json` + icons + `skills/`) plus a `metadata.*` sidecar.
 * The package ships verbatim as the download; the detail page is synthesized.
 */
function processPlugin(sub: Submission): ImportProblem | null {
  const { slug, label } = sub;
  if (sub.metaText === undefined) {
    return {
      source: label,
      problems: [
        `no metadata sidecar found next to the plugin package ` +
          `(expected ${METADATA_NAMES.join(" / ")})`,
      ],
    };
  }

  const pluginFiles = sub.pluginFiles ?? [];
  const pv = validatePluginFiles(pluginFiles, label);
  if (!pv.ok) return { source: label, problems: pv.problems };

  let catalog: Record<string, unknown>;
  try {
    catalog = parseMetadataFile(sub.metaName!, sub.metaText);
  } catch (err) {
    return { source: label, problems: [`could not parse ${sub.metaName}: ${(err as Error).message}`] };
  }

  // Catalog fields fall back to the manifest when the sidecar omits them.
  const manifest = pv.manifest ?? {};
  const mName = (manifest.name as Record<string, unknown> | undefined)?.short;
  const mDesc = manifest.description as Record<string, unknown> | undefined;
  const displayName = (catalog.name as string | undefined) ?? (mName as string | undefined);
  const catalogDescription =
    (catalog.description as string | undefined) ?? (mDesc?.short as string | undefined);

  const problems: string[] = [];
  if (!displayName) {
    problems.push("`name` is required in the metadata file (or manifest.name.short)");
  }
  if (!catalogDescription) {
    problems.push("`description` is required in the metadata file (or manifest.description.short)");
  }
  if (problems.length) return { source: label, problems };

  // A plugin is Cowork-only; drop any name/description/platforms/type from the
  // sidecar so they can't override the derived values.
  const {
    name: _n,
    description: _d,
    platforms: _p,
    type: _t,
    ...catalogRest
  } = catalog;
  const meta: Record<string, unknown> = {
    name: displayName,
    description: catalogDescription,
    platforms: ["Cowork"],
    type: "plugin",
    ...catalogRest,
    bundle: `bundles/${slug}.zip`,
  };

  resolveAuthorGithub(slug, meta);

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    const overview =
      (mDesc?.full as string | undefined) ??
      (mDesc?.short as string | undefined) ??
      catalogDescription!;
    const body = buildPluginBody({ overview, skills: pv.skills, connectors: pv.connectors });
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, body));
    mkdirSync(BUNDLES_DIR, { recursive: true });
    // Ship the M365 app package verbatim (deterministic order + fixed mtime).
    writeBundle(pluginFiles, join(BUNDLES_DIR, `${slug}.zip`));
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md ` +
        `(plugin, + public/bundles/${slug}.zip)`,
    );
  }
  return null;
}

// Day-of-week labels for rendering a schedule's `days` array (0 = Sunday).
const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/**
 * Build the synthesized detail-page body for a Scout automation. There is no
 * SKILL.md, so we render an overview, the trigger/schedule, the ordered prompt
 * steps, and how to import the `.json` into Scout.
 */
function buildAutomationBody(opts: {
  overview: string;
  digest: AutomationDigest;
  slug: string;
}): string {
  const { overview, digest, slug } = opts;
  const lines: string[] = [overview.trim(), ""];
  lines.push(
    "> **Scout automation.** This is a Microsoft **Scout** automation (a `.json` " +
      "of a schedule plus ordered prompt steps). It runs on Scout only.",
    "",
  );

  lines.push("## Trigger", "");
  if (digest.triggerType === "condition") {
    lines.push(`Runs on a **condition** — ${digest.scheduleSummary}.`, "");
  } else {
    lines.push(`Runs on a **schedule** — ${digest.scheduleSummary}.`, "");
  }

  lines.push("## Steps", "");
  digest.steps.forEach((step, i) => {
    const label = step.label?.trim() || `Step ${i + 1}`;
    lines.push(`### ${i + 1}. ${label}`, "");
    // Fence the prompt verbatim so its own Markdown/paths render literally.
    lines.push("```text", step.prompt.replace(/```/g, "``\u200b`"), "```", "");
  });

  lines.push(
    "## Import into Scout",
    "",
    "1. Download the automation (the `.json` on this page).",
    "2. In **Scout \u203a Automations**, choose **Import** and select the file " +
      "(or paste its contents). Review the schedule and steps, then enable it.",
    "",
    "You can also point Scout's **Import from GitHub** at a repository directory " +
      "of automation `.json` files (a `skills/` subfolder is installed " +
      "automatically). This automation's file is " +
      `\`submissions/${slug}/\` in this repo.`,
    "",
    "> Review the steps before enabling — automations act on your behalf on a " +
      "schedule.",
  );
  return lines.join("\n") + "\n";
}

/**
 * Build the synthesized detail-page body for an automation installer. There is
 * no schedule/steps digest, so the submitted `INSTALL.md` is rendered verbatim
 * as the body. The "how to install" guidance lives next to the download button
 * on the detail page, so we don't repeat it as a callout here.
 */
function buildInstallerBody(install: string, _slug: string): string {
  return `${install.trim()}\n`;
}

/**
 * Validate + generate an automation installer submission: a `.zip` holding an
 * `INSTALL.md` plus one or more JSON config files, alongside a `metadata.*`
 * sidecar. The `.zip` ships verbatim as the download; the detail page renders
 * the `INSTALL.md`. Validation is minimal (INSTALL.md + >=1 JSON present); the
 * config files are never schema-checked.
 */
function processAutomationInstaller(sub: Submission): ImportProblem | null {
  const { slug, label } = sub;
  const files = sub.installerFiles ?? [];

  const iv = validateAutomationInstallerFiles(files, label);
  if (!iv.ok || iv.install === undefined) return { source: label, problems: iv.problems };

  if (sub.metaText === undefined) {
    return {
      source: label,
      problems: [
        `no metadata sidecar found next to the installer ` +
          `(expected ${METADATA_NAMES.join(" / ")})`,
      ],
    };
  }

  let catalog: Record<string, unknown>;
  try {
    catalog = parseMetadataFile(sub.metaName!, sub.metaText);
  } catch (err) {
    return { source: label, problems: [`could not parse ${sub.metaName}: ${(err as Error).message}`] };
  }

  const problems: string[] = [];
  if (!catalog.name) {
    problems.push("`name` (display name) is required in the metadata file");
  }
  if (!catalog.description) {
    problems.push("`description` (catalog) is required in the metadata file");
  }
  if (problems.length) return { source: label, problems };

  // An installer is a Scout automation; drop any name/description/platforms/type
  // from the sidecar so they can't override the derived values.
  const {
    name: displayName,
    description: catalogDescription,
    platforms: _p,
    type: _t,
    ...catalogRest
  } = catalog;
  const meta: Record<string, unknown> = {
    name: displayName,
    description: catalogDescription,
    platforms: ["Scout"],
    type: "automation",
    ...catalogRest,
    // A `.zip` bundle (vs a `.json`) is what marks this automation as an installer.
    bundle: `bundles/${slug}.zip`,
  };

  resolveAuthorGithub(slug, meta);

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    const body = buildInstallerBody(iv.install, slug);
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, body));
    mkdirSync(BUNDLES_DIR, { recursive: true });
    // Ship the installer package verbatim (deterministic order + fixed mtime).
    writeBundle(files, join(BUNDLES_DIR, `${slug}.zip`));
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md ` +
        `(automation installer, + public/bundles/${slug}.zip)`,
    );
  }
  return null;
}

/**
 * Validate + generate a Scout automation submission: a raw Scout automation
 * `.json` plus a `metadata.*` sidecar. The `.json` ships verbatim as the
 * download (re-importable into Scout); the detail page is synthesized.
 */
function processAutomation(sub: Submission): ImportProblem | null {
  const { slug, label } = sub;
  if (sub.installer) return processAutomationInstaller(sub);
  if (sub.automationJson === undefined) {
    return { source: label, problems: ["no automation `.json` payload found"] };
  }
  if (sub.metaText === undefined) {
    return {
      source: label,
      problems: [
        `no metadata sidecar found next to the automation ` +
          `(expected ${METADATA_NAMES.join(" / ")})`,
      ],
    };
  }

  // Validate the automation against Scout's import contract.
  const av = validateAutomationData(
    (() => {
      try {
        return JSON.parse(sub.automationJson!);
      } catch {
        return null;
      }
    })(),
    label,
  );
  if (!av.ok || !av.digest) {
    const problems = av.problems.length
      ? av.problems
      : [`${sub.automationJsonName ?? "automation.json"} is not valid JSON`];
    return { source: label, problems };
  }
  const digest = av.digest;

  let catalog: Record<string, unknown>;
  try {
    catalog = parseMetadataFile(sub.metaName!, sub.metaText);
  } catch (err) {
    return { source: label, problems: [`could not parse ${sub.metaName}: ${(err as Error).message}`] };
  }

  // Catalog name/description fall back to the automation's own fields.
  const displayName = (catalog.name as string | undefined) ?? digest.name;
  const catalogDescription =
    (catalog.description as string | undefined) ?? digest.description;

  const problems: string[] = [];
  if (!displayName) {
    problems.push("`name` is required in the metadata file (or the automation's `name`)");
  }
  if (!catalogDescription) {
    problems.push(
      "`description` is required in the metadata file (or the automation's `description`)",
    );
  }
  if (problems.length) return { source: label, problems };

  // An automation is Scout-only; drop any name/description/platforms/type from
  // the sidecar so they can't override the derived values.
  const {
    name: _n,
    description: _d,
    platforms: _p,
    type: _t,
    ...catalogRest
  } = catalog;
  const meta: Record<string, unknown> = {
    name: displayName,
    description: catalogDescription,
    platforms: ["Scout"],
    type: "automation",
    ...catalogRest,
    bundle: `bundles/${slug}.json`,
  };

  resolveAuthorGithub(slug, meta);

  const result = validateSkillData(meta, label);
  if (!result.ok) return { source: label, problems: result.problems };

  if (!checkOnly) {
    const body = buildAutomationBody({
      overview: catalogDescription!,
      digest,
      slug,
    });
    mkdirSync(CONTENT_DIR, { recursive: true });
    writeIfChanged(join(CONTENT_DIR, `${slug}.md`), buildContent(meta, body));
    mkdirSync(BUNDLES_DIR, { recursive: true });
    // Ship the automation `.json` verbatim so the gallery download equals the
    // exact file Scout imports.
    writeIfChanged(join(BUNDLES_DIR, `${slug}.json`), sub.automationJson);
    console.log(
      `\u2713 ${label} \u2192 src/content/skills/${slug}.md ` +
        `(automation, + public/bundles/${slug}.json)`,
    );
  }
  return null;
}

/**
 * Load a `submissions/<slug>/` folder: a `metadata.json` sidecar plus exactly
 * one skill payload — either an unpacked canonical skill (root `SKILL.md` +
 * optional dirs) or a single pre-packaged `<name>.zip`.
 */
function loadSubmission(dir: string): Submission {
  const slug = basename(dir);
  const label = `submissions/${slug}/`;
  const sub: Submission = { slug, label, kind: "skill", bundleFiles: [] };
  const problems: string[] = [];

  const topFiles = readdirSync(dir).filter((n) => statSync(join(dir, n)).isFile());
  const zips = topFiles.filter((n) => n.toLowerCase().endsWith(".zip"));
  const hasRootSkill = topFiles.some((n) => n.toLowerCase() === INSTRUCTIONS_NAME);

  // Metadata sidecar (top-level, next to the payload — never inside the bundle).
  const metaFile = topFiles.find((n) => METADATA_NAMES.includes(n.toLowerCase()));
  if (metaFile) {
    sub.metaName = metaFile.toLowerCase();
    sub.metaText = readFileSync(join(dir, metaFile), "utf8");
  }

  if (zips.length > 0 && hasRootSkill) {
    problems.push(
      "submission has BOTH an unpacked SKILL.md and a .zip payload \u2014 " +
        "provide exactly one",
    );
  } else if (zips.length > 1) {
    problems.push(
      `submission has ${zips.length} .zip files \u2014 provide exactly one ` +
        "packed payload",
    );
  } else if (zips.length === 1) {
    // Packed payload: explode the zip. A root-level `manifest.json` marks a
    // Cowork plugin (an M365 app package); otherwise it's a canonical Agent
    // Skill (root `SKILL.md`), re-bundled from its exploded contents.
    const files = new AdmZip(join(dir, zips[0]))
      .getEntries()
      .filter((e) => !e.isDirectory)
      .map((e) => ({ path: e.entryName.split("\\").join("/"), data: e.getData() }));
    if (isPluginPackage(files)) {
      sub.kind = "plugin";
      // Ship the package verbatim, minus any stray metadata sidecar.
      sub.pluginFiles = files.filter(
        (f) => !METADATA_NAMES.includes(basename(f.path).toLowerCase()),
      );
    } else if (isAutomationInstaller(files)) {
      // An automation installer: an `INSTALL.md` + JSON config file(s). Shipped
      // verbatim as the download; the INSTALL.md becomes the detail-page body.
      sub.kind = "automation";
      sub.installer = true;
      sub.installerFiles = files.filter(
        (f) => !METADATA_NAMES.includes(basename(f.path).toLowerCase()),
      );
    } else {
      classifyPayload(sub, files);
    }
  } else if (hasRootSkill) {
    // Unpacked: bundle the folder contents verbatim (minus the metadata sidecar).
    classifyPayload(sub, listFiles(dir));
  } else {
    // A Scout automation payload: a single top-level `.json` that is NOT the
    // metadata sidecar (all root `.json` files are automations by Scout's
    // GitHub-import convention). The sidecar carries the catalog metadata.
    const automationJsons = topFiles.filter(
      (n) =>
        n.toLowerCase().endsWith(".json") && !METADATA_NAMES.includes(n.toLowerCase()),
    );
    if (automationJsons.length === 1) {
      sub.kind = "automation";
      sub.automationJsonName = automationJsons[0];
      sub.automationJson = readFileSync(join(dir, automationJsons[0]), "utf8");
    } else if (automationJsons.length > 1) {
      problems.push(
        `submission has ${automationJsons.length} automation .json files \u2014 ` +
          "provide exactly one (plus the `metadata.*` sidecar)",
      );
    } else {
      problems.push(
        "submission has no payload \u2014 add a root `SKILL.md` (with optional " +
          "`scripts/`, `references/`, `assets/`), a single `<name>.zip`, or a " +
          "single Scout automation `<name>.json`",
      );
    }
  }

  if (problems.length) sub.loadProblems = problems;
  return sub;
}

function main() {
  if (!existsSync(SUBMISSIONS_DIR)) {
    console.log("No submissions/ directory \u2014 nothing to import.");
    return;
  }

  const submissions: Submission[] = [];
  for (const name of readdirSync(SUBMISSIONS_DIR)) {
    if (name.startsWith(".") || name.startsWith("_")) continue; // _template, etc.
    const full = join(SUBMISSIONS_DIR, name);
    // Submissions are folders. A skill is packaged as a `<name>.zip` *inside* its
    // submission folder, not as a top-level zip in submissions/.
    if (statSync(full).isDirectory()) {
      submissions.push(loadSubmission(full));
    }
  }

  if (submissions.length === 0) {
    console.log("No submissions found in submissions/.");
    return;
  }

  const problems: ImportProblem[] = [];
  for (const sub of submissions) {
    const p = processSubmission(sub);
    if (p) problems.push(p);
  }

  if (problems.length > 0) {
    console.error(`\n\u2717 ${problems.length} submission(s) failed validation:\n`);
    for (const p of problems) {
      console.error(`  ${p.source}:`);
      for (const msg of p.problems) console.error(`    \u2022 ${msg}`);
    }
    console.error(
      "\nEach submission is a `submissions/<slug>/` folder with a `metadata.*` " +
        "sidecar (catalog `description`, `platforms`, `tags`) plus exactly one " +
        "payload: an unpacked `SKILL.md` (frontmatter `name` + agent-facing " +
        "`description`, then instructions), a single `<name>.zip`, or a single " +
        "Scout automation `<name>.json`. Fix the items above and retry.",
    );
    process.exit(1);
  }

  console.log(
    checkOnly
      ? `\nAll ${submissions.length} submission(s) passed validation (check-only, nothing written).`
      : `\nImported ${submissions.length} submission(s).`,
  );
}

main();
