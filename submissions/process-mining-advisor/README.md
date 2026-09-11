# Process Mining Advisor

## Overview

Process Mining Advisor helps an agent reason from how work actually happened, not only from how a process was designed. It uses the official preview Power Automate Process Mining MCP tools when connected, and falls back to supplied event logs or exported/precomputed outputs when they are not.

The skill supports the complete lifecycle:

- **Pre-change:** assess event-log readiness, discover friction, establish a baseline, and prioritize interventions.
- **In-process design:** define the evidence, rules, controls, and freshness needed for conformance or next-action decisions.
- **Post-change:** compare performance, detect drift, and measure agents as actors in the end-to-end process.

## What works now

The skill deliberately separates four modes:

1. **MCP-connected preview:** use the nine documented Process Mining tools for process discovery, metadata, overall metrics, bottlenecks, variants, edges, cases, attribute values, and correlation.
2. **Results analysis:** interpret exports or precomputed results from Power Automate Process Mining or another approved engine.
3. **Event-log compute:** analyze raw event data only when the host platform provides an approved execution surface and required tools.
4. **Advisory:** frame a process, map sources, define the event log, design KPIs, and plan analysis.

The official MCP path requires the preview Process Mining connector, an active Process Mining license, at least one ingested process, Microsoft Entra ID authentication, and authorized process access. Advisory and results-analysis fallback modes do not require local Python or a mining library; event-log compute requires a separate approved execution surface. No scripts or runtime dependencies are bundled.

## Before you start

Bring whichever artifact is available:

- an active preview Process Mining connector and access to an ingested process;
- a process description and source schema;
- a sample or complete event log;
- a Power Automate Process Mining process map, variant table, statistics export, or conformance output;
- baseline and current KPI extracts;
- historical case/action/outcome evidence for next-action analysis.

The skill asks for the minimum missing artifact rather than demanding a complete data program up front.

Avoid sharing credentials or unnecessary personal data. Preserve source identifiers only where they are needed for controlled drill-through and lineage.

## How to use it

Ask in plain language:

- "Assess whether this audit history is ready for process mining."
- "Use the Process Mining tools to list my accessible processes and summarize the overall metrics for one process."
- "Find the top bottlenecks for this process after discovering valid department filter values."
- "Interpret these process map and variant exports and rank the main rework patterns."
- "Define a defensible cycle-time baseline before we automate this process."
- "Prioritize automation candidates using volume, delay, rework, exceptions, risk, and data confidence."
- "Compare the baseline and post-change KPI exports without overstating causality."
- "Design the event telemetry needed to measure our agent as a process actor."

The output identifies the operating mode, evidence used, limitations, findings, confidence, and the next smallest step.

## What you get

Depending on the evidence, the skill can produce:

- an event-log readiness report and source-to-event map;
- KPI and baseline definitions;
- evidence-backed variant, bottleneck, rework, and conformance findings;
- a scored automation-candidate backlog with controls;
- a next-action evidence assessment;
- a baseline/post-change comparison;
- a process-drift alert design;
- an agent-as-actor telemetry contract.

## Preview MCP scope

- The official Process Mining MCP server and connector are preview features, subject to change, and not meant for production use.
- The preview exposes nine documented read/analytics tools. This skill does not invent or wrap additional operations.
- Tool results remain subject to the authenticated user's environment and process permissions.
- Filtered and paged results must be labeled with their scope; partial retrieval is not a complete process result.

## What this does not do

- The current nine tools do not document transactional `check_conformance` or `next_best_action` operations.
- The current tool set does not include a dedicated continuous drift-monitoring operation; repeated timeframe comparisons are analytical, not a native monitor.
- A supplied export or materialized insight is precomputed evidence, not a live transactional guardrail.
- Copilot Studio does not gain local Python or pm4py execution from this skill.
- Event-log compute is optional and depends on the host environment's approved tools.
- The skill does not build or scaffold an MCP.
- Recommendations remain traceable to counts, filters, time windows, freshness, definitions, and source artifacts.

## Remaining product gap

The preview MCP supplies the governed analytics bridge that was previously missing. The remaining gap is production maturity and action-time process intelligence: transactional conformance checks before actions commit, next-best-action operations, and native continuous drift monitoring are not among the current nine documented tools.

Official preview documentation:

- [Process Mining MCP server reference](https://learn.microsoft.com/en-us/power-automate/process-mining-mcp-server-reference)
- [Create a Copilot Studio agent with process mining](https://learn.microsoft.com/en-us/power-automate/process-mining-mcp-create-cps-agent)
