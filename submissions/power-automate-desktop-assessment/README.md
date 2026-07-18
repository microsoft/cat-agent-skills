# Power Automate Desktop Assessment

Review exported Power Automate solutions and hybrid cloud/desktop automation projects using an evidence-based assessment workflow grounded in current Microsoft guidance.

## What it covers

- Maintainability, architecture, and reuse
- Reliability, error handling, and troubleshooting readiness
- Security, credentials, DLP, and access control
- Performance, concurrency, machine strategy, and scaling
- Testing, ALM, governance, and operational support

The skill inventories solution artifacts, generates static metrics, and produces prioritized findings with evidence, impact, remediation, effort, and suggested ownership. It treats package analysis as one source of evidence and clearly identifies where run history, logs, selectors, machine configuration, or governance records are still required.

## Portable workflow

The bundled scripts run with Python 3.10+ and the standard library in the Linux-style execution environments used by Cowork and Copilot Studio. The default outputs are a Markdown assessment and a JSON metrics file. Richer formats are optional and used only when the host provides a supported document-generation capability.

The extraction workflow validates ZIP members before writing and rejects path traversal, excessive archive expansion, and unsafe output reuse. It does not print secret values or modify the supplied automation.

## Typical inputs

- Exported Power Platform solution ZIP
- Desktop-flow and cloud-flow definitions
- Run history and action logs
- Selector, machine, connection, DLP, and work queue configuration
- Test evidence and operational documentation

The resulting report includes an executive summary, strengths, prioritized risks, detailed recommendations, a remediation roadmap, open questions, and an inventory of reviewed artifacts and references.