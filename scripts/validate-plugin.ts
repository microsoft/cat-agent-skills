/**
 * Validate a Cowork plugin (an M365 app package) thoroughly.
 *
 * A plugin is a `.zip` whose ROOT holds a `manifest.json` (Unified M365 app
 * manifest), `color.png` / `outline.png` icons, and a `skills/` tree with one or
 * more Agent Skills. Unlike a single cross-platform skill, a plugin runs only on
 * Copilot Cowork.
 *
 * This module inspects the exploded zip files (never the filesystem) so the same
 * rules run at submission time and in CI. It returns the parsed manifest plus a
 * digest of the contained skills/connectors, which the importer uses to
 * synthesize the gallery detail page.
 *
 * Ref: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development
 */
import matter from "gray-matter";
import { posix } from "node:path";

/** A file inside the package, with a forward-slash relative path. */
export type PluginFile = { path: string; data: Buffer };

/** One Agent Skill contained in the plugin. */
export type PluginSkill = { folder: string; name: string; description: string };

/** One remote connector (MCP server) declared in the manifest. */
export type PluginConnector = {
  id?: string;
  displayName?: string;
  description?: string;
};

export type PluginValidation = {
  ok: boolean;
  problems: string[];
  /** The parsed manifest (present whenever it was valid JSON). */
  manifest?: Record<string, unknown>;
  /** Digest of each contained skill (empty for connector-only plugins). */
  skills: PluginSkill[];
  /** Digest of each declared connector. */
  connectors: PluginConnector[];
};

const MANIFEST_NAME = "manifest.json";
const SKILL_NAME = "skill.md"; // compared lowercased
const KEBAB = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const GUID = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
// Cowork's agentSkills/agentConnectors are a preview manifest feature, so the
// conversion script and real-world packages emit "devPreview"; the published
// docs reference the stable "1.28". Accept either.
const ACCEPTED_MANIFEST_VERSIONS = ["1.28", "devPreview"];
// Companion-file limits (per skill), from the Cowork plugin docs.
const MAX_COMPANION_FILES = 20;
const MAX_COMPANION_BYTES = 5 * 1024 * 1024;
const MAX_TOTAL_COMPANION_BYTES = 10 * 1024 * 1024;
const WIN_RESERVED = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/i;
// Alphanumeric, hyphen, underscore, dot, space, and "!" (plus "/" separators).
const SAFE_PATH = /^[A-Za-z0-9 _.!/-]+$/;

/** True when the package looks like a Cowork plugin (root manifest.json). */
export function isPluginPackage(files: PluginFile[]): boolean {
  return files.some((f) => f.path.toLowerCase() === MANIFEST_NAME);
}

/** Read a PNG's pixel dimensions from its IHDR chunk (no external deps). */
function pngSize(buf: Buffer): { width: number; height: number } | null {
  // 8-byte signature, then IHDR: 4-byte length, "IHDR", width (BE), height (BE).
  if (buf.length < 24) return null;
  const isPng =
    buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47;
  if (!isPng) return null;
  if (buf.toString("ascii", 12, 16) !== "IHDR") return null;
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

/** Normalize a manifest folder reference (e.g. "./skills/x/") to "skills/x". */
function normalizeFolder(folder: string): string {
  return folder.replace(/^\.\//, "").replace(/\/+$/, "");
}

/**
 * Validate the exploded plugin files. `label` prefixes messages (e.g. the
 * submission folder). Always returns a result — never throws.
 */
export function validatePluginFiles(
  files: PluginFile[],
  label: string,
): PluginValidation {
  const problems: string[] = [];
  const skills: PluginSkill[] = [];
  const connectors: PluginConnector[] = [];
  const byPath = new Map(files.map((f) => [f.path, f]));
  const byLowerPath = new Map(files.map((f) => [f.path.toLowerCase(), f]));

  const manifestFile = byLowerPath.get(MANIFEST_NAME);
  if (!manifestFile) {
    problems.push("no root-level `manifest.json` found in the plugin package");
    return { ok: false, problems, skills, connectors };
  }

  let manifest: Record<string, unknown>;
  try {
    manifest = JSON.parse(manifestFile.data.toString("utf8"));
  } catch (err) {
    problems.push(`manifest.json is not valid JSON: ${(err as Error).message}`);
    return { ok: false, problems, skills, connectors };
  }

  // --- Top-level manifest fields ---------------------------------------------
  const manifestVersion = manifest.manifestVersion;
  if (!nonEmptyString(manifestVersion)) {
    problems.push(
      `manifest.manifestVersion is required (expected one of ${ACCEPTED_MANIFEST_VERSIONS.map((v) => `"${v}"`).join(" or ")})`,
    );
  } else if (!ACCEPTED_MANIFEST_VERSIONS.includes(manifestVersion)) {
    problems.push(
      `manifest.manifestVersion should be ${ACCEPTED_MANIFEST_VERSIONS.map((v) => `"${v}"`).join(" or ")} ` +
        `(got "${manifestVersion}")`,
    );
  }

  if (!nonEmptyString(manifest.id)) {
    problems.push("manifest.id is required");
  } else if (!GUID.test(manifest.id)) {
    problems.push(`manifest.id must be a GUID (got "${manifest.id}")`);
  }

  const name = manifest.name as Record<string, unknown> | undefined;
  if (!name || !nonEmptyString(name.short)) {
    problems.push("manifest.name.short is required");
  }
  const description = manifest.description as Record<string, unknown> | undefined;
  if (!description || !nonEmptyString(description.short)) {
    problems.push("manifest.description.short is required");
  }

  // --- Icons ------------------------------------------------------------------
  const icons = manifest.icons as Record<string, unknown> | undefined;
  const iconChecks: Array<[string, unknown, number, number]> = [
    ["color", icons?.color, 192, 192],
    ["outline", icons?.outline, 32, 32],
  ];
  for (const [key, ref, w, h] of iconChecks) {
    if (!nonEmptyString(ref)) {
      problems.push(`manifest.icons.${key} is required`);
      continue;
    }
    const iconPath = normalizeFolder(ref);
    const file = byPath.get(iconPath) ?? byLowerPath.get(iconPath.toLowerCase());
    if (!file) {
      problems.push(`manifest.icons.${key} points to "${ref}" but no such file is in the package`);
      continue;
    }
    const size = pngSize(file.data);
    if (!size) {
      problems.push(`icon "${ref}" is not a readable PNG`);
    } else if (size.width !== w || size.height !== h) {
      problems.push(
        `icon "${ref}" must be ${w}\u00d7${h}px (got ${size.width}\u00d7${size.height})`,
      );
    }
  }

  // --- Skills + connectors presence ------------------------------------------
  const agentSkills = manifest.agentSkills;
  const agentConnectors = manifest.agentConnectors;
  const hasSkills = Array.isArray(agentSkills) && agentSkills.length > 0;
  const hasConnectors = Array.isArray(agentConnectors) && agentConnectors.length > 0;
  if (!hasSkills && !hasConnectors) {
    problems.push(
      "manifest must declare at least one of `agentSkills` or `agentConnectors`",
    );
  }
  if (agentSkills !== undefined && !Array.isArray(agentSkills)) {
    problems.push("manifest.agentSkills must be an array when present");
  }

  // --- Each contained skill ---------------------------------------------------
  if (hasSkills) {
    for (const [i, entry] of (agentSkills as unknown[]).entries()) {
      const at = `manifest.agentSkills[${i}]`;
      const folderRef = (entry as Record<string, unknown>)?.folder;
      if (!nonEmptyString(folderRef)) {
        problems.push(`${at}.folder is required`);
        continue;
      }
      const folder = normalizeFolder(folderRef);
      const prefix = `${folder}/`;
      const inFolder = files.filter((f) => f.path === folder || f.path.startsWith(prefix));
      if (inFolder.length === 0) {
        problems.push(`${at}.folder "${folderRef}" does not exist in the package`);
        continue;
      }
      const skillMd = inFolder.find(
        (f) => f.path.toLowerCase() === `${folder.toLowerCase()}/${SKILL_NAME}`,
      );
      if (!skillMd) {
        problems.push(`skill folder "${folder}" has no SKILL.md`);
        continue;
      }

      const expectedName = posix.basename(folder);
      let fm: Record<string, unknown> = {};
      try {
        fm = matter(skillMd.data.toString("utf8")).data as Record<string, unknown>;
      } catch (err) {
        problems.push(`${folder}/SKILL.md has invalid frontmatter: ${(err as Error).message}`);
        continue;
      }
      const skillName = fm.name;
      if (!nonEmptyString(skillName)) {
        problems.push(`${folder}/SKILL.md frontmatter \`name\` is required`);
      } else if (!KEBAB.test(skillName)) {
        problems.push(
          `${folder}/SKILL.md \`name\` must be kebab-case (got "${skillName}")`,
        );
      } else if (skillName !== expectedName) {
        problems.push(
          `${folder}/SKILL.md \`name\` ("${skillName}") must match its folder ("${expectedName}")`,
        );
      }
      const skillDesc = fm.description;
      if (!nonEmptyString(skillDesc)) {
        problems.push(`${folder}/SKILL.md frontmatter \`description\` is required`);
      }

      // Companion files: everything under the folder except SKILL.md.
      const companions = inFolder.filter(
        (f) => f.path !== folder && f.path.toLowerCase() !== skillMd.path.toLowerCase(),
      );
      if (companions.length > MAX_COMPANION_FILES) {
        problems.push(
          `skill "${folder}" has ${companions.length} companion files ` +
            `(max ${MAX_COMPANION_FILES})`,
        );
      }
      let total = 0;
      for (const c of companions) {
        total += c.data.length;
        const rel = c.path.slice(prefix.length);
        const base = posix.basename(c.path);
        if (c.data.length > MAX_COMPANION_BYTES) {
          problems.push(`companion "${c.path}" exceeds 5 MB`);
        }
        if (rel.includes("..")) {
          problems.push(`companion "${c.path}" must not contain ".." path segments`);
        }
        if (c.path.includes("\\")) {
          problems.push(`companion "${c.path}" must not contain backslashes`);
        }
        if (base.startsWith(".")) {
          problems.push(`companion "${c.path}" must not be a hidden file`);
        }
        if (!SAFE_PATH.test(c.path)) {
          problems.push(`companion "${c.path}" uses unsafe characters`);
        }
        if (WIN_RESERVED.test(posix.basename(base, posix.extname(base)))) {
          problems.push(`companion "${c.path}" uses a Windows reserved name`);
        }
      }
      if (total > MAX_TOTAL_COMPANION_BYTES) {
        problems.push(`skill "${folder}" companions exceed 10 MB total`);
      }

      skills.push({
        folder,
        name: nonEmptyString(skillName) ? skillName : expectedName,
        description: nonEmptyString(skillDesc) ? skillDesc : "",
      });
    }
  }

  // --- Connectors (light digest; MCP wiring is validated by Cowork itself) ----
  if (hasConnectors) {
    for (const entry of agentConnectors as Record<string, unknown>[]) {
      connectors.push({
        id: typeof entry?.id === "string" ? entry.id : undefined,
        displayName:
          typeof entry?.displayName === "string" ? entry.displayName : undefined,
        description:
          typeof entry?.description === "string" ? entry.description : undefined,
      });
    }
  }

  return { ok: problems.length === 0, problems, manifest, skills, connectors };
}
