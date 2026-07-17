# Scout automation template

> **Heads up:** this README is contributor guidance for the template. If you keep
> a `README.md` in your own submission it **becomes the main content** on the
> gallery detail page — so replace this text with a human-facing overview of your
> automation, or delete the file to fall back to the auto-generated page.

Copy this folder to `submissions/<your-slug>/` to submit a **Scout automation** —
a scheduled/triggered `.json` (a schedule plus an ordered list of prompt steps)
that runs **only** in Scout.

See [`../spend-more-time-with-friends-and-family/`](../spend-more-time-with-friends-and-family)
for a complete working example.

## What to put here

```
submissions/<your-slug>/
├── metadata.json       # catalog sidecar (this file's sibling) — tweak or delete
│                       #  name/description; they fall back to the automation
└── <your-automation>.json   # the Scout automation export (add this yourself)
```

The submission is auto-detected as an **automation** because the single
non-sidecar top-level file is a `.json` (not a `.zip`, not a `SKILL.md`). Do
**not** set `platforms` in `metadata.json` — the importer forces `["Scout"]`.
The exact `.json` you submit is the file offered for download and re-imported
verbatim into Scout, so ship it as you want it distributed (strip any personal
paths or secrets first).

## Required `.json` shape

The automation is validated against Scout's own import schema
(`scripts/validate-automation.ts` is a faithful port). At minimum:

- `name` — non-empty string.
- `steps` — array of `{ "label": string, "prompt": string }` (an optional `id`
  is allowed but Scout regenerates ids on import).
- `schedule` — **required**, an object discriminated on `kind`:
  - `single` — fires once per matching day at a time.
  - `interval` — every N minutes (`intervalMinutes` must divide 1440 evenly).
  - `multi` — several fixed times per day.
  - `monthly` — a day/weekday/workday selector across chosen months (must be
    able to actually fire — e.g. not Feb 31).
  - `cron` — a `cronExpression` (must be a valid, fireable cron string).

Optional: `description`, `triggerType` (`"schedule"` | `"condition"`),
`condition`, `conditionCheckInterval`, `model`, `reasoningEffort`,
`contextWindowTokens`, `permissions`, `browserHeadless`, `teamsNotify`
(`always` | `auto` | `never`). Unknown top-level keys are stripped.

The [`automation.json`](./automation.json) in this folder is a minimal valid
example (a `single` daily schedule with one step).

## Validate locally

```bash
npm run check:submissions    # thorough validation, writes nothing
npm run import:submissions    # generate the automation page + published .json
npm run build
```
