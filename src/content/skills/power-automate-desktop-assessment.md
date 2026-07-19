---
name: Power Automate Desktop Assessment
description: Assess Power Automate Desktop and hybrid automation projects with evidence-based findings and prioritized remediation guidance.
agentDescription: "Assess Power Automate Desktop and hybrid cloud/desktop automation projects for maintainability, reliability, security, performance, troubleshooting readiness, scaling, and governance using current Microsoft guidance and evidence-based review practices."
platforms: [Cowork, Copilot Studio]
tags: [power-automate, desktop-flows, automation, assessment, governance]
author: Ricardo Calejo
authorUrl: "https://github.com/dvsRCalejo"
authorGithub: dvsRCalejo
version: 1.1.0
createdAt: 2026-07-17
updatedAt: 2026-07-18
bundle: bundles/power-automate-desktop-assessment.zip
---
# Power Automate Desktop Assessment

Use this skill when assessing, reviewing, or preparing recommendations for a Microsoft Power Automate Desktop (PAD) project, desktop flow, exported solution/package, cloud-flow orchestration around desktop flows, or related Power Platform automation artifacts. The goal is to produce an evidence-based assessment with findings, risks, severity, and actionable remediation.

## Source references

Use these references as the baseline for assessment criteria:

### Microsoft Learn: Power Automate and enterprise guidance

- Power Automate documentation hub: https://learn.microsoft.com/en-us/power-automate/
- Power Automate guidance documentation: https://learn.microsoft.com/en-us/power-automate/guidance/
- Power Automate planning guidance: https://learn.microsoft.com/en-us/power-automate/guidance/planning/introduction
- Automation CoE guidance: https://learn.microsoft.com/en-us/power-automate/guidance/automation-coe/overview
- Automation Kit guidance: https://learn.microsoft.com/en-us/power-automate/guidance/automation-kit/overview/introduction
- Application lifecycle management for automation projects: https://learn.microsoft.com/en-us/power-automate/guidance/planning/application-lifecycle-management

### Microsoft Learn: cloud flow coding guidelines

- Cloud flow coding guidelines overview: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/
- Naming conventions: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-consistent-naming-conventions
- Solution-aware flows: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/understand-benefits-solution-aware-flows
- Scopes: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/create-scopes
- Child flows/reuse: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/create-reusable-code
- Parallel execution and concurrency: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/implement-parallel-execution
- Data operations: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-data-operations
- Trigger optimization: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/optimize-power-automate-triggers
- Work only with relevant data: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/work-with-relevant-data
- Avoid anti-patterns: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/avoid-anti-patterns
- Environment variables: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-environment-variables
- Robust error handling: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/error-handling
- Flow Checker: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/manage-flows-flow-checker
- Test cloud flows: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/test-cloud-flows
- Troubleshoot cloud flows: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/troubleshoot-cloud-flows
- Platform limits and throttling: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/understand-limits
- Secure inputs/outputs/triggers: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-secure-inputs-outputs-triggers
- Generic configuration: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/keep-flow-configuration-generic
- Flow ownership/access: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/understand-access-to-flows
- Dataverse/Purview auditing: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-auditing-dataverse
- Prevent data exfiltration: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/prevent-data-exfiltration
- Monitoring and alerting: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/monitoring-and-alerting

### Microsoft Learn: desktop flow coding guidelines

- Desktop flow coding guidelines overview: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/
- Build readable and maintainable flow scripts: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/build-readable-flow-scripts
- Optimize flow performance: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/optimize-flow-performance
- Secure your data: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/secure-your-data
- Optimize end-to-end process performance: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/optimize-end-to-end-performance
- Monitor and troubleshoot automation processes: https://learn.microsoft.com/en-us/power-automate/guidance/desktop-flow-coding-guidelines/monitor-automation

### Microsoft Learn: desktop execution, diagnostics, and troubleshooting

- Troubleshooter executable/app: https://learn.microsoft.com/en-us/power-automate/desktop-flows/troubleshooter
- Troubleshoot desktop flows runtime: https://learn.microsoft.com/en-us/power-automate/desktop-flows/troubleshoot
- Run desktop flows best practices: https://learn.microsoft.com/en-us/power-automate/desktop-flows/run-desktop-flows-best-practices
- Run desktop flows concurrently: https://learn.microsoft.com/en-us/power-automate/desktop-flows/run-desktop-flows-concurrently
- Run unattended desktop flows: https://learn.microsoft.com/en-us/power-automate/desktop-flows/run-unattended-desktop-flows
- Machine groups: https://learn.microsoft.com/en-us/power-automate/desktop-flows/manage-machine-groups
- Hosted RPA overview: https://learn.microsoft.com/en-us/power-automate/desktop-flows/hosted-rpa-overview
- Work queues: https://learn.microsoft.com/en-us/power-automate/desktop-flows/work-queues
- Desktop flow action logs configuration: https://learn.microsoft.com/en-us/power-automate/desktop-flows/configure-desktop-flow-logs
- Static analysis for desktop flows: https://learn.microsoft.com/en-us/power-automate/desktop-flows/static-analysis
- Cloud flow error troubleshooting: https://learn.microsoft.com/en-us/power-automate/troubleshoot-flow-errors
- Cloud flow error code reference: https://learn.microsoft.com/en-us/power-automate/error-reference
- Fix connection failures in cloud flows: https://learn.microsoft.com/en-us/power-automate/fix-connection-failures

If live documentation is available, check current Microsoft guidance before finalizing recommendations. Prioritize Microsoft Learn over community sources. If documentation cannot be fetched, proceed with the criteria below and state that the assessment is based on the embedded baseline.

## Microsoft Learn discovery workflow

When this skill is used, start by searching current Microsoft guidance with the documentation or web retrieval tools available to the agent before relying on the embedded baseline.

1. Start with the official Microsoft Learn URLs listed in **Source references**.
2. Search Microsoft Learn to find:
   - the current version of each referenced article;
   - child/sub articles under the cloud flow coding guidelines and desktop flow coding guidelines sections;
   - related troubleshooting, limits, security, ALM, monitoring, and governance articles;
   - newer pages that supersede or redirect from the listed URLs.
3. Retrieve the relevant article content and extract assessment criteria, not generic documentation summaries.
4. Prefer official Microsoft Learn results over community content.
5. Record which Microsoft Learn articles were actually consulted in the assessment report appendix.
6. If documentation retrieval is unavailable, use the embedded baseline and explicitly mark the documentation confidence as limited.
7. Do not skip Microsoft Learn discovery because the baseline is already present. The baseline is a fallback and checklist, not a replacement for current Microsoft Learn research.

Suggested discovery queries:

- `Power Automate desktop flow coding guidelines build readable maintainable flow scripts`
- `Power Automate desktop flow optimize flow performance wait timeout loops unused components`
- `Power Automate secure desktop flows credentials sensitive variables DLP audit logs`
- `Power Automate optimize end-to-end process performance machine groups hosted machine groups work queues`
- `Power Automate monitor troubleshoot desktop automation action logs V2 Automation center`
- `Power Automate run desktop flows best practices timeout distribute load machine groups`
- `Power Automate cloud flow coding guidelines naming conventions concurrency trigger conditions anti-patterns limits`
- `Power Automate troubleshoot cloud flow errors 401 403 404 429 500`

## Assessment principles

- Be evidence-based: cite the file, flow, action, variable, selector, screenshot, exported artifact, run history, action log, or configuration record that supports each finding.
- Do not rubber-stamp. Flag real maintainability, reliability, security, correctness, performance, scaling, and governance issues directly.
- Separate required fixes from optional improvements.
- Prefer pragmatic remediation that fits low-code/RPA delivery, not over-engineered software patterns.
- Do not alter the user's automation unless explicitly asked. Assessment mode is read-only by default.
- Treat exported flows, credentials, environment variables, logs, selectors, screenshots, run history, connection references, and machine details as potentially sensitive.
- Clearly distinguish official Microsoft guidance from community or experience-based observations.

## Inputs to inspect

Depending on what the user provides, inspect as many of these as are available:

- PAD desktop flow exports, solution ZIPs, extracted folders, scripts, UI selector definitions, images, dependencies, connection references, environment variables, machine/runtime configuration notes, run history, action logs, error logs, documentation, test evidence, cloud flows that trigger desktop flows, DLP policies, machine group/hosted machine group configuration, work queue configuration, and operational dashboards.
- If a ZIP is provided, inspect its structure first, then extracted relevant metadata and flow definitions.
- If only screenshots or notes are available, perform a partial assessment and clearly mark missing evidence.

## Solution ZIP analysis patterns

When assessing an exported Power Platform solution ZIP, extract and summarize these artifacts before writing findings:

- `solution.xml`: solution unique name, version, managed/unmanaged status, publisher, and package metadata.
- `customizations.xml`: solution components, component counts, entity/process metadata, and signs of unmanaged/customized artifacts.
- `Workflows/*.json`: cloud flow definitions, triggers, actions, connection references, child-flow calls, desktop-flow calls, error handling, loops, scopes, variables, HTTP calls, waits, retry policies, and termination paths.
- `environmentvariabledefinitions/*/environmentvariabledefinition.xml`: schema name, display name, type, required flag, default value presence, and secret store flag.
- `desktopflowbinaries/*/data/*.json`: desktop flow manifest, engine version, module references, connector references, UI control repository, image repository, dependency file, screen/control counts, and use of UI/Web/File/System modules.

For workflow metrics, capture:

- number of workflows and total actions;
- top action types;
- connectors and connection references used;
- largest workflows by action count;
- `Foreach` count and maximum nested `Foreach` depth;
- scope count and `runAfter` non-success paths;
- retry policy count;
- `Terminate` actions;
- HTTP actions;
- wait/delay actions;
- child workflow / desktop flow references;
- potential sensitive keyword classes in definitions, without printing secret values.

Use these signals to drive findings:

- very large workflows or duplicated `OLD` / `TEST` workflows retained in the solution;
- nested loops or high loop counts that may create request, runtime, or throttling risk;
- workflows with little or no structured error handling (`Scope`, non-success `runAfter`, `Terminate`, retry policy);
- unmanaged solution packages intended for controlled environments;
- environment variables with no defaults and no required flag where deployment validation depends on external configuration;
- connection references for Outlook, OneDrive, Dataverse, filesystem, web content, or UI flows that need DLP/access review;
- desktop flow binaries with UI/Web automation modules that require selector robustness and runtime diagnostics review;
- generic names, misspellings, or artifacts named `OLD`, `TEST`, `Unknown`, or similar that indicate maintainability or ALM hygiene issues.

## Runtime contract for Cowork and Copilot Studio

The required workflow targets the common execution model of all declared platforms:

- Python 3.10+ in an isolated Linux-style runtime with a writable `/tmp` directory.
- Python standard library only for extraction, metrics, and the canonical report.
- Input and output through host-provided file or attachment capabilities, not a desktop filesystem or sync client.
- No PowerShell, Windows paths, desktop Office automation, process termination, Node.js, or host-specific skill-loader paths.

The skill includes four companion scripts under `scripts/`:

- `extract_solution.py` safely extracts a solution ZIP and rejects path traversal and oversized archives.
- `analyze_solution.py` generates static metrics without emitting configuration or secret values.
- `render_report.py` produces the canonical Markdown report.
- `run_assessment.py` runs the complete extraction, analysis, and report pipeline.

If a host exposes Python through an action or tool rather than directly to the agent, configure that action to use the same command-line contract and pass host-managed input/output files to it.

## Recommended assessment automation workflow

### 1. Stage the input

Use the host's file or attachment capability to materialize the supplied solution ZIP as a read-only temporary file, for example:

`/tmp/input/solution.zip`

Do not assume that a user-provided local path is visible inside the execution runtime.

### 2. Run the bundled Python workflow

From the skill package root, run:

```bash
python3 scripts/run_assessment.py \
  --zip /tmp/input/solution.zip \
  --work-dir /tmp/pad-assessment
```

The command creates a unique run directory and prints the exact paths. It produces:

- `/tmp/pad-assessment/run-<id>/output/assessment_metrics.json`
- `/tmp/pad-assessment/run-<id>/output/assessment_report.md`

The workflow:

- preserves the original ZIP;
- validates archive members before writing, extracts into a new staging directory, and rejects path traversal, excessive member counts, oversized files, and excessive total expansion;
- parses `solution.xml`;
- reads `environmentvariabledefinitions/*/environmentvariabledefinition.xml`;
- inspects `desktopflowbinaries/*/data/*.json`;
- walks all `Workflows/*.json` recursively;
- counts triggers, actions, action types, connectors, scopes, `Foreach`, maximum nested `Foreach` depth, non-success `runAfter` paths, retry policies, `Terminate`, HTTP-like actions, wait/delay actions, and desktop/child-flow references;
- records only sensitive keyword classes or presence indicators, never secret values;
- keeps source filenames for traceability and uses friendly names in the report.

Individual scripts can also be invoked directly:

```bash
python3 scripts/extract_solution.py \
  /tmp/input/solution.zip \
  /tmp/pad-assessment/solution_extract

python3 scripts/analyze_solution.py \
  --root /tmp/pad-assessment/solution_extract \
  --output /tmp/pad-assessment/output/assessment_metrics.json

python3 scripts/render_report.py \
  --metrics /tmp/pad-assessment/output/assessment_metrics.json \
  --output /tmp/pad-assessment/output/assessment_report.md
```

### 3. Complete the evidence-based review

Treat the generated report as a static-analysis draft. Verify its threshold-based findings against the extracted artifacts and add evidence from any supplied run history, action logs, selectors, machine configuration, DLP policies, test results, and operational documentation.

Do not infer runtime behavior from package structure alone. Lower confidence and list missing evidence when runtime artifacts are unavailable.

### 4. Create the executive dashboard

The portable default is a compact Markdown table using the metrics JSON. If the host provides a supported chart or image-generation capability, a PNG dashboard can also include:

- KPI cards: cloud flows, total actions, desktop artifacts, high-priority recommendations, nested-loop flows, and ALM hygiene signals;
- top workflows by action count;
- recommendation hotspots by topic;
- priority split;
- short interpretation notes.

Image generation is optional and must not block delivery of the Markdown report.

### 5. Generate the assessment report

Markdown is the canonical cross-platform output. The report should be in English by default and organized as:

1. Executive dashboard or summary metrics table.
2. Executive summary.
3. Priority recommendations grouped by artifact type:
   - Cloud Flows
   - Desktop Flow / PAD
   - Environment Variables
   - Solution-level artifacts
4. Complete recommendations grouped by artifact type.
5. Recommended next steps.

Report structure requirements:

- The assessment body must be written in English unless the user explicitly requests another report language.
- Organize recommendations by artifact type, not raw file order.
- Use friendly artifact names in headings, followed by the artifact type, for example `Invoice Dispatcher [Cloud Flow]`.
- Do not use raw JSON filenames as recommendation titles. Keep raw names only in the **Technical source** field for traceability.
- Each recommendation must state what was observed, the target state, the remediation approach, the expected impact, and the priority.

For each recommendation, use professional headings:

- **Technical source**
- **Assessment area**
- **Observed condition**
- **Target state / best practice**
- **Recommended remediation**
- **Expected business/operational impact**
- **Priority**

### 6. Optional richer document formats

Only create DOCX, PDF, or another rich format when the user requests it and the current host exposes a supported document-generation capability.

- Use the host-native capability; do not require `docx-js`, Node.js, Microsoft Word, LibreOffice, a mounted OneDrive/SharePoint folder, or another platform's skill loader.
- Treat the Markdown report and metrics JSON as the source of truth.
- If the requested format is unavailable, deliver Markdown and state the limitation explicitly.
- Validate an optional rich document with the host's supported validator or preview capability before delivery. Never claim validation that did not run.

### 7. Publish outputs safely

Use explicit names:

- `*_Assessment.md`
- `*_Assessment_Metrics.json`
- an equivalent extension only when an optional richer format was requested and generated.

Return or persist outputs with the host's file/attachment API. Do not assume a mounted cloud-drive path. Avoid in-place overwrite; when a destination already exists, use a new versioned name. Never terminate user applications or sync processes.

## Common myths and verified facts

These are factually wrong claims that show up repeatedly in PAD assessments (and in partner-authored documents being reviewed). Always fact-check against current Microsoft Learn before accepting them as evidence — and call them out when they appear in the artifact under review.

| Myth (frequently asserted)                                                            | Verified fact                                                                                                                                                                                                                                                                                                                                                                                                 | Authoritative reference                                                                           |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| "Automation Center captures error screenshots automatically"                          | False. AC stores run history, status, recommendations, and queue health, but does **not** capture screenshots on error. The supported pattern is an explicit `Take screenshot` action wrapped by `On block error` or by exception-handling subflows.                                                                                                                                                          | Learn: _Troubleshoot failed unattended runs using screenshots_                                    |
| "Use the Azure Application Insights connector ('Send to App Insights') for telemetry" | The Azure Application Insights connector is **deprecated and read-only** (it only ran Analytics queries; it never wrote telemetry). For Power Automate: enable App Insights integration at the **environment level** in Power Platform admin centre to capture cloud flows automatically; for desktop flow custom traces, use an HTTP action against the Application Insights ingestion endpoint.             | Learn: _Set up Application Insights for an environment_; Connectors reference (deprecated marker) |
| "PAD has a 'Get files in folder' action under the System group"                       | The action lives under **Folder** group, not System.                                                                                                                                                                                                                                                                                                                                                          | Learn: _Folder actions reference_                                                                 |
| "PAD has a 'Generate random text or number' action"                                   | The native action is **`Create random text`** under the **Text** group.                                                                                                                                                                                                                                                                                                                                       | Learn: _Text actions reference_                                                                   |
| "PAD has a 'Convert custom object to datatable' action"                               | Does **not exist**. Variables actions provide `Convert JSON to custom object`, `Convert custom object to JSON`, and `Convert data table to text`. To produce a datatable from JSON, iterate the parsed custom object and use `Insert row into data table`, or perform the conversion in cloud-flow expressions.                                                                                               | Learn: _Variables actions_                                                                        |
| "Unattended fails because Entra tokens expire"                                        | Most reports of this symptom are actually the **`Connect with sign-in` option being interactive-only** — it cannot reconnect a machine after sign-out without a logged-in session. Move to a self-hosted Machine Group with a service principal as connection identity. The `Entra token expiry` framing leads to wrong remediation (forced re-login scripts) instead of the correct one (service principal). | Learn: _Set up machines for desktop flows_; _Run desktop flows from a cloud flow_                 |
| "Logs V1 with custom retention is fine"                                               | Logs V2 (Elastic Tables) supersedes V1. V2 provides **automatic data retention**, **near real-time updates**, and scales to GB of action logs per run. New environments default to V2; assessments should recommend V2 unless there is a hard incompatibility.                                                                                                                                                | Learn: _Desktop flow action logs configuration_                                                   |
| "Work Queues can be parallelised aggressively"                                        | Learn-documented limit: keep dequeueing concurrency moderate — **up to five parallel dequeue operations per work queue is recommended**. For sub-second processing, Work Queues are not suitable; Learn explicitly recommends **Azure Service Bus Queues** as alternative.                                                                                                                                    | Learn: _Work queues — Known limitations_                                                          |
| "Cloud flow timeout caps desktop flow at 24 h / 4 h / pick a number"                  | The `Run a flow built with Power Automate Desktop` action accepts an ISO 8601 timeout (e.g., `PT10M`, `PT1H`); Learn does **not** publish a maximum value for the action timeout. The only documented hard envelope is the cloud flow run duration limit (**30 days**).                                                                                                                                       | Learn: _Limits of automated, scheduled, and instant flows_                                        |
| "Custom assembly call counts and native action counts can be conflated"               | Distinguish carefully when counting Work Queue usage: **native** calls use the `WORKQUEUES` module, while **custom assembly** calls use a project-specific namespace and method. A mix is common; report them in two separate columns ("native hits" vs "assembly hits"), never a single total.                                                                                                               | Robin script convention; assembly source/manifest                                                 |

When the artifact under review claims any of the left-column statements, treat it as a finding (Medium severity by default) and cite the corrected fact in the report.

## Assessment workflow

1. Understand context
   - Identify business process, trigger/orchestration model, attended vs unattended execution, target applications, expected volume, SLA, users, environments, failure impact, regulatory constraints, and support ownership.
   - Identify the project structure and main desktop flows/subflows/cloud flows.

2. Inventory the automation
   - List desktop flows, subflows, cloud orchestration flows, key actions, external systems, files/folders, applications automated, credentials/secrets touchpoints, connectors, connection references, environment variables, machine groups, work queues, and environment-specific assumptions.

3. Review using the assessment dimensions below
   - For every significant finding, capture evidence, impact, severity, and recommendation.
   - Use severity labels: Critical, High, Medium, Low, Observation.

4. Produce a report
   - Start with executive summary and overall health rating.
   - Include strengths, key risks, prioritized findings, remediation roadmap, and open questions.
   - Include quick wins separately from structural remediation.

5. Fact-check pass before finalize
   - Treat the report as a draft until an explicit fact-check pass is done. Do **not** ship v1 without it; bugs in numerical claims and action-name mismatches damage credibility with technical reviewers far more than a missing recommendation.
   - Audit chapter-by-chapter (or section-by-section). For each chapter, classify every assertable claim as verified / ambiguous / wrong, with a one-line reason and a Microsoft Learn citation for the non-trivial ones.
   - Categories of claims to check exhaustively:
     - **Native PAD action names** — exact group + action name as published in Learn (groups change: Folder != System; Text != Variables). Do not rely on memory.
     - **Connector names and status** — many connectors are deprecated, renamed, or read-only. Always verify status flags on the connector reference page.
     - **Numerical metrics** — counts, line numbers, callsite distributions must reconcile against the raw scripts and against the metrics JSON. Re-run greps if a number was edited.
     - **Throughput math** — verify it is internally consistent (items/day x seconds/item x machines should reconcile).
     - **Platform limits** — five parallel dequeue ops per queue, sub-second -> Service Bus, 30-day cloud flow envelope, etc. Cite Learn verbatim.
     - **Internal cross-references** — section X says "see section Y"; section Y must still exist and still say what X claims.
     - **Carry-over consistency** — when a fix is applied in one chapter, search the whole document for the obsolete wording; the same myth often appears in 3-5 places (executive summary, scorecard rationale, top-N priorities, glossary, roadmap card).
   - Present fact-check findings clearly and correct unsupported claims before finalizing the report.
   - Apply each correction consistently across all language and audience variants, then rebuild and revalidate every output.

## Assessment dimensions

### 1. Correctness and functional fit

Check whether the automation appears to implement the intended process correctly.

- Are business rules explicit and traceable?
- Are edge cases handled: empty inputs, missing files, duplicate records, invalid formats, application timeouts, unexpected UI states, locked records, partial completion, stale reads, polling-trigger backlogs, and target resource changes?
- Are there clear start/end states and idempotency considerations for reruns?
- Are manual handoffs and exception paths defined?
- Are assumptions about screen resolution, language, data formats, dates, paths, user profile, browser version, and machine state documented?
- If cloud flows orchestrate desktop flows, do trigger behavior and trigger conditions match the intended processing window and avoid unintended reruns?

### 2. Maintainability and readability

Assess whether another maker/developer can understand and safely change the flow.

- Flow, subflow, action, variable, UI element, image, and parameter names should be descriptive and consistent.
- For desktop variables, check whether camelCase, PascalCase, or underscores are used consistently, whether data type prefixes are used, and whether input/output variables have prefixes in both variable name and external name.
- For cloud flow components, check descriptive names, consistent camelCase/underscore style, and optional prefixes/tags such as `Trg_`, `Act_`, or `Var_` when this matches team standards.
- Avoid generic names such as `var`, `temp`, `data`, `result`, `NewVar`, `Button`, `Trigger1`, or unexplained abbreviations.
- Check whether naming conventions are documented in a style guide/wiki for the maker community.
- Related actions should be grouped logically. For desktop flows, look for `Region` / `End region` actions to group actions inside a subflow where useful.
- Long flows should be decomposed into meaningful subflows or reusable child desktop flows.
- Use comments at the beginning of `Main`, each subflow, and bug-fix sections to describe purpose, intended audience, related flows, and non-obvious design decisions.
- Avoid excessive nesting, duplicated action blocks, many skipped actions inside large switch branches, and hidden dependencies between distant actions.
- Dead, disabled, unused UI elements, and unused images should be justified or removed.

### 3. Architecture, design, and reuse

Assess whether the solution is structured for scale and supportability.

- Clear separation between orchestration, business rules, UI automation, data access, logging, exception handling, and notification.
- Reusable subflows for repeated behavior within a desktop flow.
- Reusable child desktop flows for shared components across desktop flows, invoked via `Run desktop flow` where appropriate.
- Shared UI element collections should be used when the same application UI elements are reused across flows, so UI changes can be fixed centrally.
- Custom actions may be appropriate when repeated behavior needs a packaged reusable action.
- Avoid tight coupling to a single machine, user profile, screen layout, locale, hard-coded path, or unmanaged machine state.
- Use environment variables/configuration for environment-specific values where applicable.
- Prefer supported APIs, cloud connectors, or application/file-specific PAD actions over UI automation when reliable interfaces exist.
- For desktop action choice, prefer in this order: cloud connector actions, application/file-specific desktop actions, UI/browser automation, then image recognition/OCR/mouse/keyboard/clipboard. Consider scripting or HTTP actions for advanced cases when maintainable and governed.
- Consider ALM: solution packaging, source control/export process, version control, dev/test/prod separation, deployment notes, ownership, and rollback plan.

### 4. Error handling and resilience

Use Microsoft guidance patterns where applicable.

- Desktop flows should use action-level `On error` parameters, `On block error` for groups of actions, `Get last error` to capture diagnostic context, and `Stop flow` for graceful terminal failures.
- Cloud flows should use `Run after` settings and scopes to implement try/catch-style error paths, and `Terminate` where failure state must be explicit.
- Errors should be classified as recoverable vs terminal.
- Retry policies should be used for transient failures, with bounded retries and backoff where possible.
- Failures should surface meaningful messages and preserve diagnostic context.
- Logging should capture run ID/correlation ID, step, input reference, error details, last error, retry status, and outcome without leaking secrets.
- Termination paths should make failure state explicit and prevent unsafe continuation after critical errors.
- Avoid excessive custom logging/actions that materially degrade performance or increase action/request consumption.
- If run history shows errors, distinguish save errors, trigger issues, action errors, logic issues, runtime connectivity issues, queue errors, and environment/machine issues.

### 5. Security, privacy, and access control

Assess data protection, credentials, access, and exposure risk.

- No passwords, tokens, keys, secrets, or personal data hard-coded in flows, scripts, comments, logs, paths, screenshots, sample files, connection strings, or notifications.
- Prefer Power Automate credentials backed by Azure Key Vault or CyberArk for desktop-flow credentials.
- In desktop flows, prefer `Get credential` for sensitive values instead of passing secrets as input variables.
- Mark all sensitive input, output, and flow variables as sensitive. Do not copy sensitive values into non-sensitive variables, because sensitivity does not automatically propagate except for credential variable types.
- For desktop flow connections, use dedicated credentials and machine mapping where machines require separate accounts.
- Check whether MFA/certificate-based authentication requirements are met where relevant.
- Review access to desktop flows and related components: child desktop flows, work queues, credentials, UI element collections, custom actions, connection references, and connector actions.
- Apply least privilege to owner/co-owner/user roles and Dataverse security roles; verify whether broad Process table read access grants unintended co-owner visibility.
- Sensitive input/output files should be stored in approved locations with appropriate access controls and retention.
- Logs and notifications should not expose confidential records unnecessarily.
- Validate external data before using it in decisions, file paths, commands, scripts, browser input, UI automation, HTTP calls, or generated messages.
- Review use of scripts, command execution, clipboard, email sending, file deletion, and external network calls.
- Check DLP policies for desktop flow action groups, connector classification as Business/Non-business/Blocked, and individual connector action controls.
- Check whether Dataverse auditing and/or Microsoft Purview auditing is enabled for automation-related tables where needed.

### 6. Performance and runtime efficiency

Assess runtime efficiency and operational scalability.

- Avoid unnecessary UI interactions, repeated application launches, fixed sleeps, row-by-row processing, nested loops, and expensive selectors when batching or data actions are possible.
- Prefer explicit `Wait for...` actions with timeouts over generic `Wait` actions.
- Configure desktop flow timeout appropriately for expected duration.
- Check loops for upper bounds, exit conditions, and large dataset risks.
- For Excel/data-heavy flows, prefer Data table actions, Database actions, Power Fx functions, or maintainable scripting rather than looping through thousands of records in UI actions.
- Remove unused components, disabled actions, unused UI elements, and unused images to reduce size and save/load time.
- Identify high-volume paths, repeated file/network I/O, unbounded reads, action overages, and connector/API throttling risks.
- Capture expected and observed runtime where available.

### 7. Cloud-flow orchestration, concurrency, and API optimization

Use this dimension when cloud flows trigger or coordinate desktop flows, or when the assessment includes cloud flows.

- Use trigger conditions and OData filters so flows run only when necessary.
- Understand polling vs webhook trigger behavior, especially backlog processing when a disabled polling-trigger flow is re-enabled.
- Use trigger concurrency control carefully; default is often safest, and concurrency control is irreversible on an existing flow.
- Use parallel branches only for independent tasks, especially tasks taking more than five seconds, and avoid overwhelming endpoints.
- Use `Apply to each` concurrency for independent items only; tune degree of parallelism instead of assuming 50 is best.
- Remember concurrency in nested `Apply to each` loops applies only at the highest level; inner loops remain sequential.
- Avoid large switch branches with many skipped actions; call child flows from branches when this improves maintainability.
- Process only relevant data: use trigger-level filters, Dataverse OData filters/select columns/row count, SharePoint filter query/top count/limit columns by view.
- Avoid nested `For each` loops. Use OData expansion, Select, filtering, batching, bulk operations, or dataflows where appropriate.
- Avoid using cloud flows as heavy ETL engines for large-scale transformations; consider Power Platform dataflows for ETL and cloud flows for orchestration.
- Estimate API request usage: triggers/actions, loops, retries, pagination, and failed actions count toward limits. Watch for 429 throttling.
- Review platform limits: API request limits, connector throttling, Dataverse service protection limits, flow concurrency limits, action burst limits, and flow design limits.

### 8. Execution scaling, workload distribution, and machine strategy

Assess whether the automation can run at the required volume and SLA.

- Desktop flows can queue for up to 12 hours while waiting for a machine; assess whether scheduling and capacity avoid timeout/failure risk.
- Spread load over time where possible if machine capacity is limited.
- Use machine groups for identical machine configurations and dynamic workload distribution.
- Use hosted machine groups when automatic scaling, Microsoft-managed maintenance, high availability, and reduced infrastructure overhead are appropriate.
- In cloud flows, consider parallel branches of `Run a flow built with Power Automate for desktop` only when desktop flow instances can safely run concurrently across machines/machine groups.
- Anticipate unattended parallel run volume and confirm licensing/capacity is adequate.
- For long-running desktop flows, verify the cloud action timeout is configured to cover expected run duration.
- Track CPU, memory, network, and app resource usage on machines that run flows.
- Consider Windows session reuse only when compliance and machine state requirements allow it.
- For attended scenarios, consider picture-in-picture when the user must keep working while automation runs.
- Use work queues to decouple complex processes, store work items, control prioritization/expiration/status, and support asynchronous scaling.

### 9. UI automation robustness

PAD-specific review focus.

- Selectors should be stable and resilient; avoid brittle coordinates, image-only matching, text that changes frequently, or unvalidated mouse/keyboard automation when better selectors or actions exist.
- UI element names should be clear and organized, preferably via shared UI element collections for reused assets.
- The flow should handle application startup, login/session state, pop-ups, loading states, focus issues, unexpected dialogs, browser extension state, virtual desktop quirks, and reconnects.
- Clipboard use should be minimized or guarded because it is shared mutable state.
- Keyboard/mouse actions should be deterministic and validated with post-action checks.
- Screenshots/image recognition and OCR should have documented thresholds, fallback behavior, and justification when used instead of more reliable actions.

### 10. Observability, diagnostics, and supportability

Assess whether operations teams can support the automation.

- Run history and business transaction status should be traceable.
- Configure desktop flow action logs to V2 where appropriate. Logs V2 use Elastic Tables, provide retention, can scale to high-volume logs, and support near real-time/progressive action logging.
- Use `Log message` with Info/Warning/Error severity to record progress and important details.
- Use `Display message` for attended user interaction/debugging where appropriate, knowing it is also logged.
- Use custom logging to Dataverse, SharePoint, or files only when justified and governed.
- Alerts should be actionable and routed to the right owner.
- Include enough context for triage: process instance, record/file identifier, failed step, error type, last error, retry status, machine/machine group, and run URL where available.
- Review Automation center reports: cloud flow activity, desktop flow activity, desktop flow runs, capacity utilization, recommendations, process map, execution logs, and performance metrics.
- Review tenant-level Power Platform admin center Monitor page where enterprise-wide health is relevant.
- For advanced reporting, consider Microsoft Fabric / OneLake integration for automation-centric analytics.
- There should be clear support documentation: prerequisites, recovery steps, restart/rerun process, known issues, escalation contacts, and ownership.

### 11. Troubleshooting readiness

Check whether the project and operating model can diagnose failures quickly.

- Know whether the local Power Automate for desktop Troubleshooter can be run via Help > Troubleshooter or `PAD.Troubleshooter.exe`.
- Troubleshooter diagnostic categories include connectivity, sign-in, Dataverse, UI/Web automation, picture-in-picture, installation issues, and connectivity for cloud runtime.
- Check whether generated troubleshooter CSV reports and exported logs are captured for incident analysis when needed.
- For desktop runtime connectivity, confirm `UIFlowService` can reach required services such as `*.dynamics.com`, `*.servicebus.windows.net`, `*.gateway.prod.island.powerapps.com`, and `*.api.powerplatform.com`.
- If connectivity works in an interactive user session but fails via service, review `NT SERVICE\UIFlowService` privileges, proxy rules, and service account configuration.
- For virtual desktop/RDP/Citrix issues, verify correct PAD version, agent for virtual desktops, reconnect steps, and plugin registration if applicable.
- Use verbose logging only to reproduce and capture issues, then turn it off because it can reduce performance and consume disk capacity.
- For cloud failures, classify using save errors, trigger issues, action errors, logic issues, and common error codes: 401 auth, 403 permission/DLP, 404 missing resource, 429 rate limit, 500 service/server issue.
- For expression errors, check missing branches, wrong data types, nulls, syntax, references to steps that did not execute, and use `coalesce()` or explicit empty checks where appropriate.

### 12. Testing and verification

Assess test quality and release readiness.

- Evidence of unit-like subflow testing, end-to-end testing, negative/error-path testing, regression testing, and operational smoke tests.
- Test data should cover happy path, empty inputs, invalid inputs, boundary cases, duplicate records, unavailable apps, permission failures, throttling/rate limits, machine unavailable, application update/UI change, and rerun/idempotency scenarios.
- Tests should verify business outcomes, not just that the flow ran.
- Include deployment validation and smoke tests for each environment.
- Review whether Flow Checker, Power CAT Toolkit, static analysis for desktop flows, or equivalent tooling was used where applicable.

### 13. Governance, CoE, and compliance

Assess alignment with Power Platform governance.

- Ownership, service account model, environment strategy, DLP policy alignment, connector usage, licensing, machine group usage, and monitoring responsibilities should be clear.
- Confirm solution packaging and ALM practices for enterprise maintainability.
- Assess whether the automation fits the organization's CoE operating model, environment strategy, maker support model, monitoring/reporting model, and adoption maturity.
- Consider Automation Kit / Automation Center for enterprise-scale monitoring, exception rules, DLP impact analysis, desktop flow audit logs, scheduler, and historical voluminous data monitoring.
- Check whether the business impact, ROI, risk, and process mining insights are captured for continuous improvement.

## Finding format

Use this format for each finding:

```markdown
### [Severity] Short finding title

**Evidence:** File/flow/action/subflow/log/run/configuration reference and what was observed.
**Impact:** Why it matters for correctness, maintenance, reliability, security, performance, scaling, or governance.
**Recommendation:** Specific remediation steps.
**Effort:** Low/Medium/High.
**Owner:** Maker/Developer/Admin/Business owner/Operations/CoE, if inferable.
```

Severity guidance:

- Critical: likely data loss, security exposure, unsafe execution, material compliance breach, or automation cannot reliably run.
- High: significant production reliability, maintainability, supportability, scalability, or compliance risk.
- Medium: meaningful issue that should be fixed in the next planned iteration.
- Low: minor improvement or localized maintainability issue.
- Observation: informational context, good practice, positive finding, or future consideration.

## Report template

```markdown
# Power Automate Desktop Assessment

## Executive summary

**Overall health:** Red/Amber/Green
**Assessment confidence:** High/Medium/Low
**Scope reviewed:** ...
**Key conclusion:** ...

## Strengths

- ...

## Top risks

| Priority | Severity | Area        | Finding | Recommended action |
| -------- | -------- | ----------- | ------- | ------------------ |
| 1        | High     | Reliability | ...     | ...                |

## Detailed findings

[Use finding format]

## Remediation roadmap

### Quick wins (0-2 weeks)

- ...

### Stabilization (2-6 weeks)

- ...

### Structural improvements (6+ weeks)

- ...

## Open questions and missing evidence

- ...

## Appendix: Inventory

- Desktop flows/subflows/cloud flows reviewed
- External systems and dependencies
- Machine/machine group/hosted machine group/work queue configuration reviewed
- Sensitive-data touchpoints
- Test/log/run history evidence reviewed
- Relevant Microsoft Learn references used
```

## Assessment checklist

Use this checklist internally and include it when useful:

- [ ] Project inventory completed
- [ ] Business process and run model understood
- [ ] Cloud orchestration reviewed, if present
- [ ] Naming and readability reviewed
- [ ] Comments, regions, subflows, and reusable components reviewed
- [ ] UI selector robustness reviewed
- [ ] Error handling and retry behavior reviewed
- [ ] Logging/monitoring/action logs reviewed
- [ ] Troubleshooter/diagnostics readiness reviewed
- [ ] Security, sensitive variables, credentials, access, and DLP reviewed
- [ ] Performance/scalability/concurrency reviewed
- [ ] Machine groups/hosted machines/work queues reviewed, if applicable
- [ ] Platform limits/throttling/API request usage reviewed
- [ ] ALM/governance/CoE reviewed
- [ ] Testing evidence reviewed
- [ ] Findings prioritized with severity and effort

## Output style

- Write formal assessment reports in English by default, even when the conversation is in another language, unless the user explicitly requests a different report language. Short chat explanations can still match the user's language.
- Be detailed yet specific. Avoid generic best-practice filler.
- When evidence is missing, say so clearly and lower confidence rather than guessing.
- When using non-official/community sources, identify them as supplementary rather than authoritative.
- If the user asks for an assessment report file, create the requested format only after confirming the intended deliverable type unless it is obvious from the request.
