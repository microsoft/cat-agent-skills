---
name: power-platform-health-check
description: Read-only health check of a Power Platform / Dataverse environment that inspects every component in one or more named solutions (tables, columns, forms, views, web resources, plug-ins and steps, cloud flows and workflows, apps, environment variables, connection references, dependencies). Use when the user supplies an environment and solution names and asks for a health check, smoke test, post-deployment verification, or component audit. Not for making changes.
---

# Skill: Power Platform Health Check

Verify that every component in the given solutions exists, is in a valid state, and has no missing dependencies. **Strictly read-only** - never create, update, delete, publish, or import anything.

## Inputs

| Input | Source |
|---|---|
| Environment URL | `POWERPLATFORM_ENV_URL` if set, otherwise the URL the user supplies. If neither exists, ask the user. |
| Solution unique names (one or more) | Supplied by the user. If the user gives display names, resolve them with the script's `--list-solutions` flag. Ask only if none were given. |
| Credentials | Service principal from `POWERPLATFORM_SP_APP_ID`, `POWERPLATFORM_SP_TENANT_ID`, `POWERPLATFORM_SP_CLIENT_SECRET`. Never print or persist the secret. If these are absent, obtain a Dataverse access token for the environment (for example `az account get-access-token --resource <env-url>`) and pass it via `DATAVERSE_ACCESS_TOKEN`. |

## Procedure

1. Confirm the connection targets the resolved environment URL.
2. Run the script (Python 3.8+, no third-party packages):

   ```powershell
   python scripts/health_check.py `
     --env-url $env:POWERPLATFORM_ENV_URL `
     --solutions SolutionA,SolutionB `
     --output docs/health_check_report.md
   ```

   Useful flags: `--list-solutions` (discover unique names), `--json` (machine-readable output), `--skip-dependencies`.
3. Read the report. For every **FAIL** or **WARN**, investigate with read-only Dataverse queries to confirm the finding and identify the cause.
4. Summarize to the user: solution and version, component counts, pass / warn / fail totals, then each finding with component name, ID, evidence, and a suggested remediation. Do not apply remediation unless the user asks.
5. If the user is tracking work in an issue, offer to add the results to it.

## Checks performed

| Component | Type code | Check |
|---|---|---|
| Solution | - | Exists, version, managed/unmanaged, component count |
| Table | 1 | Metadata present |
| Column | 2 | Metadata present |
| Option set | 9 | Global option set present |
| Relationship | 10 | Relationship metadata present |
| Cloud flow / workflow / action | 29 | Record exists; flows and modern processes must be **Activated**; flow `clientdata` non-empty |
| Web resource | 61 | Exists and has content |
| Plug-in assembly | 91 | Exists; isolation and source type reported |
| Plug-in step | 92 | Enabled |
| Form | 60 | Exists, non-empty `formxml`, active |
| View | 26 | Exists, `fetchxml` and `layoutxml` non-empty |
| Model-driven app | 80 | Exists and published |
| Canvas app | 300 | Exists |
| Environment variable definition / value | 380 / 381 | Definition exists; WARN if no default or current value |
| Connection reference | resolved dynamically | Exists; WARN if no connection bound |
| Other component types | resolved dynamically | Existence only ("inventoried, not deep-checked") |
| Dependencies | - | `RetrieveMissingDependencies` per solution; any result is a FAIL |

## Result levels

- **PASS** - present and valid.
- **WARN** - present but likely to misbehave (unbound connection reference, empty environment variable, disabled step, unpublished app).
- **FAIL** - missing, deactivated flow, empty required content, or missing dependency.

Script exit code: `0` pass/warn only, `1` any FAIL, `2` input or connection error.

## Rules

- Read-only: only HTTP GET is used (including the `RetrieveMissingDependencies` function).
- Report component names and IDs, never secrets or secret environment variable values.
- A passing report proves structure and state only; it does not replace functional testing. Say so in the summary.
