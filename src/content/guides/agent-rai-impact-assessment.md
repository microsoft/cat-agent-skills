# Agent RAI Impact Assessment

A skill for architects and reviewers assessing how an AI agent could affect people through its advice, data access, and actions. It turns a use case and design evidence into a draft Responsible AI impact assessment for accountable human review.

## What it produces

- A decision brief identifying the most material impacts and evidence gaps.
- A stakeholder view covering benefits, burdens, and affected non-users.
- An authority map showing what the agent can do and where controls are enforced.
- Concrete harm scenarios linked to current/proposed controls and residual uncertainty.
- Evaluation gates, mitigation ownership, recourse, and reassessment triggers.

It works in four modes: a one-page preliminary triage when little design exists, a full assessment, a critique of an existing assessment, and a change reassessment. For agents built in Copilot Studio, a bundled evidence map says which configuration, knowledge, tool, authentication, and analytics evidence to request for each review lens.

The skill distinguishes an identified hazard from an observed failure, and a proposed mitigation from a tested control. It does not assign an automatic compliance score or approve release.

## Example prompts

> Assess this procurement agent before a pilot. It drafts purchase requests and can submit them after buyer approval. Use the attached tool contracts, identity design, data flows, and evaluation results. Focus on who could be harmed, action authority, meaningful approval, and recovery after a tool timeout.

> Review this agent's RAI assessment. Identify unsupported conclusions, affected parties we missed, and mitigations that have no enforcement or test evidence. Keep observed failures separate from hypothetical scenarios.

> Reassess the attached agent after enabling cross-session memory and adding a tool that updates customer records. Show which previous conclusions change and which regression tests are required.

## Inputs and host capabilities

Start with the use case, affected people, knowledge/data sources, tool actions, identity/permissions, human involvement, and available evidence. Redacted diagrams, tool contracts, policy excerpts, and test results improve the assessment. No live tenant connection or credentials are needed.

The host must load `SKILL.md` and bundled Markdown references and accept supplied text or files. Web access is optional; without it, current external claims remain unverified. The skill generates text/Markdown and has no dependency on scripts, connectors, document-generation libraries, or a particular model vendor.

## Compatibility and attribution

This skill is published for Copilot Studio. It is plain Markdown with no scripts, connectors, or model-specific features, and it needs only `SKILL.md` together with the bundled `references/` folder. Results depend on the quality of the design evidence you supply.

The method draws on publicly available Microsoft Responsible AI resources: the 2022 Impact Assessment Guide and Template, the Responsible AI Standard v2 general requirements, and Microsoft Learn guidance for agents and Copilot Studio. The authority map, harm-chain prompts, approval-binding checks, evidence statuses, prioritization heuristic, consequence types, and Copilot Studio evidence map are original agent-focused extensions, not Microsoft-endorsed controls. Microsoft's internal approval roles are not binding on other organizations; use your own governance and treat any framework mapping as an interpretation. No Microsoft or NIST documents are redistributed in the package. This is a community contribution, not an official Microsoft assessment, certification, or legal determination.
