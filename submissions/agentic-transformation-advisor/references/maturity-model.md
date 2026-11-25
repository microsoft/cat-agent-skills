# Agentic AI adoption maturity model (reference)

Last verified against Learn: 2026-11-24. Fetch the live pages at run time; they win over this file.

Primary sources:
- Introduction: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/
- How to use the model: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-how-to-use
- Pillar 1, AI strategy and experience: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-strategy
- Pillar 2, Business strategy: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-business-process
- Pillar 3, AI governance and security: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-security-governance
- Pillar 4, Technology and data: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-technology
- Pillar 5, Organization and culture: https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-readiness

All text below is a paraphrase.

## Levels

Learn bases the model on the Capability Maturity Model idea. Each pillar is rated on five levels:

| Level | Name | Paraphrase |
|---|---|---|
| 100 | Initial | Unplanned, experimental, depends on individuals |
| 200 | Repeatable | Early practices repeat, still informal and uneven |
| 300 | Defined | Documented, governed, standards and operating model in place; tied to business goals |
| 400 | Capable | Agents embedded in enterprise planning and operations; scaling across teams supported |
| 500 | Efficient | Agent-first enterprise; continuous improvement, strong leadership, culture and trust |

## Pillars

| Key used by scripts | Pillar | Focus (paraphrased) |
|---|---|---|
| `ai_strategy` | AI strategy and experience | Link agents to business objectives, leadership priorities and user experience |
| `business_strategy` | Business strategy | Redesign end-to-end processes for human-agent work and measure value |
| `governance_security` | AI governance and security | Guardrails, oversight, operations and lifecycle governance |
| `technology_data` | Technology and data | Platforms, architecture, integration and data access |
| `organization_culture` | Organization and culture | People, roles, incentives, enablement and ways of working |

Responsible AI is embedded across all five pillars. Report it inside each pillar, not as a sixth score.

## How to use the model (seven steps, paraphrased)

1. Assess each pillar independently, against observable reality. Be evidence-based, not aspirational; count what is consistently true. Uneven profiles are normal.
2. Do not collapse the pillars into one score; a single number hides the gaps that matter.
3. Plot a radar chart. The shape matters more than any average; recessed areas show where scale breaks.
4. Identify gaps using each pillar's "opportunity to progress" column: missing capabilities, hidden risks and dependencies between pillars.
5. Prioritize one or two pillars and move one level at a time.
6. Use the model as a shared language across business, IT, security and leadership.
7. Reassess regularly, using real usage, outcomes and incidents.

Learn calls the model a diagnostic, not a scorecard (https://learn.microsoft.com/en-us/agents/adoption-patterns/). The largest gap against a pattern's target is the scale-breaker, and the weakest pillar caps the ceiling.

## Evidence question bank (advisor's own prompts, not Learn text)

Use these to probe each pillar during intake. Map answers to the level descriptions on the live pillar page.

### AI strategy and experience
- Is there a written agent strategy tied to business goals? Who sponsors it at executive level?
- Are use cases prioritized by outcome, with success defined up front?
- Can employees find the right agent easily? Is the experience consistent across agents?
- Is responsible AI part of strategy and investment decisions?

### Business strategy
- Has any end-to-end process been mapped and redesigned for human-agent work, or only single steps?
- Are decision rights between agents and people written down?
- Are baselines captured before deployment and compared after?
- Is value reported at operational, strategic and transformational levels, or only anecdotally?

### Governance and security
- Are there agent-specific policies, risk tiers and release gates?
- Do agents have their own identities and least-privilege access? Is there a registry?
- Are dev, test and production separated? Is agent behavior logged and monitored?
- Is there a responsible AI review before release and an incident response plan?

### Technology and data
- Has the organization standardized on a small set of agent platforms by use case?
- Are connectors, data sources and integrations approved, inventoried and reused?
- Is there ALM (source control, deployment pipelines, rollback) for production agents?
- Are usage, quality and safety captured automatically?

### Organization and culture
- Is there a defined operating model with roles, intake and escalation?
- Are there structured training, a champions network and a community of practice?
- Do leaders visibly use agents? Are adoption and sentiment measured and acted on?
- Do employees know when to rely on agents and when to apply judgment?

## Opportunities to progress

Each pillar page has a table with "State" and "Opportunity to progress" for every level. At run time:
1. Fetch the pillar page for each priority pillar.
2. Read the "Opportunity to progress" cell for the organization's current level.
3. Paraphrase two to four actions into the roadmap, citing the page.

Two examples Learn gives on the how-to page (paraphrased): clearer intake, prioritization and ownership can lift organizational readiness from 200 to 300; consistent metrics and dashboards can lift value realization from 200 to 300.

## Confidence scale (advisor convention)

| Confidence | Meaning |
|---|---|
| High | Two or more independent documents or system evidence support the level |
| Medium | One document or consistent interview answers |
| Low | A single anecdote or the user's estimate |
| Unknown | No evidence; level set to `null` in the input JSON |
