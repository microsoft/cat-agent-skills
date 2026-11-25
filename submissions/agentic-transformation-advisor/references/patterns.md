# Agentic transformation patterns (reference)

Last verified against Learn: 2026-11-24. Fetch the live pages at run time; they win over this file.

Primary sources:
- Agentic transformation patterns: https://learn.microsoft.com/en-us/agents/adoption-patterns/
- Choose the right transformation pattern: https://learn.microsoft.com/en-us/agents/adoption-patterns/choose-pattern
- Next steps action plan: https://learn.microsoft.com/en-us/agents/adoption-patterns/next-steps-action-plan

All text below is a paraphrase. Short quotes are marked and kept under 15 words.

## The shift from assist to execute

Learn frames the whole series around one shift: agents moving from assisting people to executing work (https://learn.microsoft.com/en-us/agents/adoption-patterns/).

- **Assist:** the person decides, acts and stays fully accountable. Lower risk; familiar governance fits.
- **Execute:** the agent acts across systems or runs a workflow while people oversee outcomes. Higher risk; needs a new operating model.

Once an agent executes, Learn lists four new demands:
1. Named ownership (who is accountable)
2. Defined risk response (what happens when it goes wrong)
3. Lifecycle management (who improves it over time)
4. Explicit authority (what is in and out of the agent's remit)

Learn's point: assistive-grade governance on an executing agent builds hidden risk, and heavy governance on a simple assistant slows adoption. Match governance to the work.

Patterns are design choices, not stages. Organizations do not graduate through them in order, and most run two or three at once, each with its own ownership and metrics (https://learn.microsoft.com/en-us/agents/adoption-patterns/choose-pattern).

## The six patterns

| Pattern | Purpose (paraphrased) | Who or what the agent serves | Assist or execute | Learn-named scale-breaker | Starting CoE structure | Deep-dive page |
|---|---|---|---|---|---|---|
| Employee AI enablement | Make every employee more capable | The individual employee | Assist | Organization and culture | Centralized | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-employee-ai-enablement |
| Business expert empowerment | Scale an expert's knowledge | Anyone who needs the expert's guidance | Assist | Technology and data (knowledge quality) | Federated | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-business-expert-empowerment |
| Workplace and IT services | Run internal services end to end | Employees using IT, HR and finance services | Execute | Business strategy (service design) | Centralized, then hybrid | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-workplace-it-services |
| Core business process transformation | Transform business-critical workflows | The business and its customers | Execute | Business strategy (process redesign) | Federated | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-core-business-process |
| External engagement | Serve customers and partners directly | People outside the organization | Execute | Governance and security | Centralized | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-external-engagement |
| AI-first capabilities | Create net-new capabilities | A new capability or market | Execute | Technology and data (orchestration) | Federated | https://learn.microsoft.com/en-us/agents/adoption-patterns/pattern-ai-first-capabilities |

Starting CoE structures come from https://learn.microsoft.com/en-us/agents/center-of-excellence/operating-models.

## Target maturity profiles

### Summary table (default for gap_calc.py)

Source: https://learn.microsoft.com/en-us/agents/adoption-patterns/choose-pattern

| Pattern | AI strategy and experience | Business strategy | Governance and security | Technology and data | Organization and culture |
|---|---|---|---|---|---|
| Employee AI enablement | 200 | 200-300 | 200 | 200-300 | 300 |
| Business expert empowerment | 200 | 200 | 300 | 300 | 300 |
| Workplace and IT services | 300-400 | 400 | 400 | 300 | 200-300 |
| Core business process transformation | 500 | 500 | 400 | 400 | 400 |
| External engagement | 300-400 | 400 | 500 | 400 | 200 |
| AI-first capabilities | 500 | 500 | 500 | 500 | 500 |

### Differences on the per-pattern deep-dive pages

The deep-dive pages (verified 2026-11-24) state a single target per pillar, and three patterns differ from the summary table:

| Pattern | Pillar | Summary table | Deep-dive page |
|---|---|---|---|
| Employee AI enablement | Business strategy | 200-300 | 200 |
| Employee AI enablement | Technology and data | 200-300 | 200 |
| Workplace and IT services | AI strategy and experience | 300-400 | 400 |
| Workplace and IT services | Organization and culture | 200-300 | 300 |
| External engagement | AI strategy and experience | 300-400 | 400 or higher |
| External engagement | Organization and culture | 200 | 400 or higher |

How to handle this:
- Default to the summary table and say so in the pack.
- Offer the deep-dive figures when the user wants the stricter view, and show both when the gap verdict changes. Set `target_source` to `deep-dive` in the shared input JSON, or pass `--target-source deep-dive` to both `gap_calc.py` and `radar_chart.py`, so the analysis and chart agree.
- Re-check both pages at run time; Learn may reconcile them.

## Start from intent, not technology

Learn maps three motivations to patterns (choose-pattern):

| Intent | Start with | Then |
|---|---|---|
| Enrich employee experiences | Employee AI enablement | Business expert empowerment to scale specialists |
| Reshape business processes | Workplace and IT services | Core business process transformation for mission-critical flows |
| Reinvent customer engagement | External engagement | |
| Do something you could not do before | AI-first capabilities | |

The same goal can land on different patterns. Learn's example: "improve customer service" could mean faster service staff (Employee AI enablement), internal service requests (Workplace and IT services) or a customer-facing agent (External engagement). Ask which one the leader means.

## How to choose (four steps from choose-pattern)

1. **Define the outcome and vision.** State the result as a measurable change, not a technology (for example lower cost to serve, faster cycle time, more expert capacity, new revenue), then the one to three year vision.
2. **Assess readiness** on the five pillars. Use what is true today. Note the weakest pillar; it limits everything.
3. **Align ambition with readiness** using three bands:
   - Meets or exceeds target: strong fit now, proceed.
   - One or two pillars short: clear scale-breaker; close it first or pilot while closing it.
   - Several pillars well short: ambition outruns readiness; pick a stepping-stone pattern.
4. **Sequence and revisit.** Start with high outcome value and the smallest gap. Reassess quarterly.

The biggest readiness jump is the assist-to-execute line. If the vision is an execute pattern but readiness is assistive, start on the assist side.

Learn guardrails for selection (paraphrased):
- Cap at two or three patterns.
- The weakest capability is the ceiling.
- Leadership decides, informed bottom-up.
- Every pattern needs a named outcome and owner. Learn: "No owner means it's a wish, not a choice."

## Per-pattern notes for the advisor

Paraphrased from each deep-dive page. Fetch the page for operating model tables, metrics and readiness checklists.

- **Employee AI enablement.** Agent recommends, person decides. Main risk is treating it as a technology rollout instead of a behavior change program. Metrics move from license counts to output quality, decision speed and time saved.
- **Business expert empowerment.** The agent is a scalable proxy for an expert; its credibility is the product. A named expert owns accuracy. Fix knowledge sources before scaling. Needs permission-aware grounding, escalation when the agent does not know, and measured accuracy.
- **Workplace and IT services.** The agent acts as a service (password reset, access, leave, expense checks) and escalates exceptions. Make-or-break role: the service owner who moves from processing tickets to governing a service. Design the service flow first, then build agents.
- **Core business process transformation.** Agents orchestrate business-critical work within set limits and route exceptions. Accountability stays in the business, not IT. Redesign the process before automating it. Needs depth in every pillar.
- **External engagement.** Agents cross the enterprise trust boundary and represent the brand. Identity isolation, AI disclosure and real-time monitoring become mandatory. Governance has to be designed in before the first external interaction.
- **AI-first capabilities.** Sense-decide-act loops that create value that did not exist before. No baseline to compare with, so success measures are invented with the capability. Needs a product owner, autonomy limits that expand with evidence, and responsible AI built into the architecture.

## Classification checklist

For each initiative, answer:
1. Who benefits: one employee, people needing an expert, employees using a service, the business and its customers, people outside, or a new market?
2. Does the agent act in a system of record, run a workflow or face customers? If yes, it is an execute pattern.
3. Does it cross the enterprise trust boundary? If yes, External engagement.
4. Could the organization do this at all before AI? If yes, it is not AI-first capabilities (Learn calls this "disguised productivity").
5. Does it fit two patterns? Flag it, and govern it at the riskier pattern's level or split scope.
