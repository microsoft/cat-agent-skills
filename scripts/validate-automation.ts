/**
 * Validate a Scout automation `.json` against Scout's own import contract.
 *
 * A Scout automation is a `.json` file describing a scheduled (or conditional)
 * agent task: a `name`, a `schedule`, and an ordered list of prompt `steps`.
 * Scout imports these directly (via its GitHub-directory import: every root
 * `.json` in the pointed-at directory is treated as an automation), so this
 * validator is a FAITHFUL, standalone port of Scout's `AutomationImportSchema`
 * (electron/automations/schemas.ts in the Scout app repo). Anything that passes
 * here is guaranteed to import cleanly into Scout.
 *
 * It also returns a digest (schedule summary + steps) the importer uses to
 * synthesize the gallery detail page.
 *
 * Usage:
 *   tsx scripts/validate-automation.ts <file.json> [more.json ...]
 */
import { readFileSync } from "node:fs";
import { basename } from "node:path";
import { Cron } from "croner";
import { z } from "astro/zod";

// --- Pure calendar math, ported verbatim from Scout's common/monthly-schedule.ts.
//     Used by the `monthly` schedule superRefine to reject impossible combos
//     (e.g. "the 31st" scoped to February only).

/** Max day-of-month per 1-based month (Feb = 29 to admit leap-year Feb 29). */
const MAX_DAY_OF_MONTH: readonly number[] = [
  0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
];

type MonthlyOn =
  | { type: "dayOfMonth"; days: number[] }
  | { type: "weekday"; ordinal: number; weekday: number }
  | { type: "workday"; ordinal: number };

/** Whether a monthly selector can ever fire given its month scope. Nth-weekday
 *  and workday selectors always fire in some month, so they're always allowed. */
function monthlyCanFire(on: MonthlyOn, months: readonly number[]): boolean {
  if (on.type !== "dayOfMonth") return months.length > 0;
  return on.days.some(
    (d) => d === -1 || months.some((m) => m >= 1 && m <= 12 && d <= MAX_DAY_OF_MONTH[m]),
  );
}

// --- Schema (ported from Scout's electron/automations/schemas.ts) -------------

const AutomationStepSchema = z
  .object({ id: z.string().optional(), label: z.string(), prompt: z.string() })
  .strip();

const TimeOfDaySchema = z.object({
  hour: z.number().int().min(0).max(23),
  minute: z.number().int().min(0).max(59),
});

const DaysSchema = z.array(z.number().int().min(0).max(6));

const SingleScheduleSchema = z
  .object({
    kind: z.literal("single"),
    naturalLanguage: z.string(),
    days: DaysSchema,
    time: TimeOfDaySchema,
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
  })
  .passthrough();

const IntervalScheduleSchema = z
  .object({
    kind: z.literal("interval"),
    naturalLanguage: z.string(),
    days: DaysSchema,
    intervalMinutes: z
      .number()
      .int()
      .positive()
      .refine((minutes) => minutes <= 1440 && 1440 % minutes === 0, {
        message: "intervalMinutes must divide 1440 evenly",
      }),
    anchor: TimeOfDaySchema,
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
  })
  .passthrough();

const MultiScheduleSchema = z
  .object({
    kind: z.literal("multi"),
    naturalLanguage: z.string(),
    days: DaysSchema,
    times: z.array(TimeOfDaySchema).min(1),
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
  })
  .passthrough();

/** Ordinal for Nth/last-of-month selectors: 1..5, or -1 meaning "last". */
const OrdinalSchema = z.union([z.literal(-1), z.number().int().min(1).max(5)]);
/** Day-of-month value: 1..31, or -1 meaning "last day of the month". */
const DayOfMonthValueSchema = z.union([z.literal(-1), z.number().int().min(1).max(31)]);

const MonthlyOnSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("dayOfMonth"), days: z.array(DayOfMonthValueSchema).min(1) }),
  z.object({
    type: z.literal("weekday"),
    ordinal: OrdinalSchema,
    weekday: z.number().int().min(0).max(6),
  }),
  z.object({ type: z.literal("workday"), ordinal: OrdinalSchema }),
]);

const MonthlyScheduleSchema = z
  .object({
    kind: z.literal("monthly"),
    naturalLanguage: z.string(),
    days: DaysSchema,
    months: z.array(z.number().int().min(1).max(12)).min(1),
    on: MonthlyOnSchema,
    time: TimeOfDaySchema,
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
  })
  .passthrough();

const CronScheduleSchema = z
  .object({
    kind: z.literal("cron"),
    naturalLanguage: z.string(),
    cronExpression: z.string().min(1),
    days: DaysSchema,
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
  })
  .passthrough();

const AutomationScheduleSchema = z
  .discriminatedUnion("kind", [
    SingleScheduleSchema,
    IntervalScheduleSchema,
    MultiScheduleSchema,
    MonthlyScheduleSchema,
    CronScheduleSchema,
  ])
  .superRefine((schedule, ctx) => {
    if (schedule.kind === "monthly" && !monthlyCanFire(schedule.on as MonthlyOn, schedule.months)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "monthly selector can never fire in the given months",
        path: ["on"],
      });
    }
    if (schedule.kind === "cron") {
      let fires = false;
      try {
        fires = new Cron(schedule.cronExpression).nextRun() !== null;
      } catch {
        fires = false;
      }
      if (!fires) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "cronExpression is not a valid, fireable cron expression",
          path: ["cronExpression"],
        });
      }
    }
  });

// Reasoning/context enums (Scout's electron/schemas/session-schema.ts).
const ReasoningEffortSchema = z.string().min(1);
const ContextWindowTokensSchema = z.number().int().positive();

/**
 * The partial shape Scout accepts at IMPORT time (id/enabled/timestamps may be
 * absent). Mirrors Scout's `AutomationImportSchema`. `permissions` is kept loose
 * (a passthrough object) rather than re-porting Scout's full PermissionsConfig.
 */
export const automationImportSchema = z
  .object({
    name: z.string().min(1),
    steps: z.array(AutomationStepSchema),
    schedule: AutomationScheduleSchema,
    description: z.string().optional(),
    condition: z.string().optional(),
    conditionCheckInterval: z.number().optional(),
    model: z.string().optional(),
    reasoningEffort: ReasoningEffortSchema.optional(),
    contextWindowTokens: ContextWindowTokensSchema.optional(),
    permissions: z.object({}).passthrough().optional(),
    browserHeadless: z.boolean().optional(),
    teamsNotify: z.enum(["always", "auto", "never"]).optional(),
    triggerType: z.enum(["schedule", "condition"]).optional(),
  })
  .strip();

export type AutomationImport = z.infer<typeof automationImportSchema>;

/** Digest of a validated automation, used to synthesize the gallery page. */
export type AutomationDigest = {
  name: string;
  description?: string;
  triggerType: "schedule" | "condition";
  scheduleKind: string;
  scheduleSummary: string;
  steps: Array<{ label: string; prompt: string }>;
};

/** Result of validating a single automation source. */
export type AutomationValidationResult = {
  label: string;
  ok: boolean;
  problems: string[];
  digest?: AutomationDigest;
};

/** Validate an already-parsed automation object against the import schema. */
export function validateAutomationData(
  data: unknown,
  label: string,
): AutomationValidationResult {
  if (!data || typeof data !== "object") {
    return { label, ok: false, problems: ["automation JSON must be an object"] };
  }
  const result = automationImportSchema.safeParse(data);
  if (!result.success) {
    const problems = result.error.issues.map((issue) => {
      const field = issue.path.length ? issue.path.join(".") : "(root)";
      return `${field}: ${issue.message}`;
    });
    return { label, ok: false, problems };
  }
  const d = result.data;
  if (d.steps.length === 0) {
    return { label, ok: false, problems: ["steps: must contain at least one step"] };
  }
  const digest: AutomationDigest = {
    name: d.name,
    description: d.description,
    triggerType: d.triggerType ?? "schedule",
    scheduleKind: d.schedule.kind,
    scheduleSummary: d.schedule.naturalLanguage,
    steps: d.steps.map((s) => ({ label: s.label, prompt: s.prompt })),
  };
  return { label, ok: true, problems: [], digest };
}

/** Validate a raw JSON string for one automation. */
export function validateAutomationSource(
  source: string,
  label: string,
): AutomationValidationResult {
  let data: unknown;
  try {
    data = JSON.parse(source);
  } catch (err) {
    return { label, ok: false, problems: [`invalid JSON: ${(err as Error).message}`] };
  }
  return validateAutomationData(data, label);
}

/** Validate an automation `.json` file on disk. */
export function validateAutomationFile(path: string): AutomationValidationResult {
  return validateAutomationSource(readFileSync(path, "utf8"), path);
}

// --- Automation installer (a `.zip` payload) ---------------------------------
//
// Besides a bare importable `.json`, an automation may be submitted as an
// installer `.zip`: an `INSTALL.md` (install procedure + the automation prompt)
// plus one or more JSON config files the automation consumes at runtime. Scout
// can't one-click import it — a human/agent follows INSTALL.md — so there is no
// schedule/steps digest. Validation here is intentionally MINIMAL (no config
// schema validation): the package must carry an INSTALL.md and at least one
// JSON file. This keeps arbitrary non-automation zips off this path without
// second-guessing the config contents.

/** A file inside the installer zip, with a forward-slash relative path. */
export type InstallerFile = { path: string; data: Buffer };

/** Names treated as the catalog metadata sidecar (never a config payload). */
const INSTALLER_METADATA_NAMES = ["metadata.json", "metadata.yaml", "metadata.yml"];
/** The required install-instructions file (compared lowercased). */
export const INSTALL_NAME = "install.md";

/** True when the exploded zip looks like an automation installer package. */
export function isAutomationInstaller(files: InstallerFile[]): boolean {
  const base = (f: InstallerFile) => f.path.split("/").pop()!.toLowerCase();
  // A packed skill owns the zip via its root SKILL.md; never steal it.
  if (files.some((f) => base(f) === "skill.md")) return false;
  const hasInstall = files.some((f) => base(f) === INSTALL_NAME);
  const hasConfigJson = files.some(
    (f) => base(f).endsWith(".json") && !INSTALLER_METADATA_NAMES.includes(base(f)),
  );
  return hasInstall && hasConfigJson;
}

export type InstallerValidation = {
  ok: boolean;
  problems: string[];
  /** The INSTALL.md contents (shallowest match), rendered as the detail page. */
  install?: string;
};

/**
 * Validate an automation installer's exploded zip files. Minimal by design:
 *   - an `INSTALL.md` must be present and non-empty;
 *   - at least one non-metadata `*.json` config file must be present.
 * The JSON config files are NOT parsed or schema-checked.
 */
export function validateAutomationInstallerFiles(
  files: InstallerFile[],
  label: string,
): InstallerValidation {
  const base = (f: InstallerFile) => f.path.split("/").pop()!.toLowerCase();
  const problems: string[] = [];

  // Prefer the shallowest INSTALL.md if the package nests under a folder.
  const installFiles = files
    .filter((f) => base(f) === INSTALL_NAME)
    .sort((a, b) => a.path.split("/").length - b.path.split("/").length);
  const install = installFiles[0]?.data.toString("utf8");
  if (install === undefined) {
    problems.push("no `INSTALL.md` found in the installer zip");
  } else if (install.trim().length === 0) {
    problems.push("`INSTALL.md` is empty");
  }

  const hasConfigJson = files.some(
    (f) => base(f).endsWith(".json") && !INSTALLER_METADATA_NAMES.includes(base(f)),
  );
  if (!hasConfigJson) {
    problems.push(
      "no JSON config file found in the installer zip (at least one `*.json` is required)",
    );
  }

  if (problems.length) return { ok: false, problems };
  return { ok: true, problems: [], install };
}

function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error("usage: tsx scripts/validate-automation.ts <file.json> [more.json ...]");
    process.exit(2);
  }

  let failures = 0;
  for (const file of files) {
    const result = validateAutomationFile(file);
    if (result.ok) {
      console.log(`\u2713 ${basename(file)} \u2014 automation OK`);
    } else {
      failures++;
      console.error(`\u2717 ${file} \u2014 invalid automation:`);
      for (const p of result.problems) console.error(`    \u2022 ${p}`);
    }
  }

  if (failures > 0) {
    console.error(
      `\n${failures} automation(s) failed validation. Fix the fields above and try again.`,
    );
    process.exit(1);
  }
  console.log(`\nAll ${files.length} automation(s) passed validation.`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
