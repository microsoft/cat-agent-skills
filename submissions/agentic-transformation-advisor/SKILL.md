---
name: agentic-transformation-advisor
description: |
  Guides one organization, business function or industry through Microsoft's three public agent adoption frameworks on Microsoft Learn (transformation patterns, adoption maturity model, agentic Center of Excellence) and produces a leader-ready pack: pattern map, maturity radar, gap and scale-breaker analysis, roadmap, CoE blueprint and leader decisions, all cited to Learn. Use when the user asks for an "agent adoption strategy for <function>", "which transformation pattern fits", "assess our agentic AI maturity", "design an agent CoE", "find our scale-breaker" or an "agent adoption pack for sales, customer service, IT or HR". Do NOT use to score a single use case idea, analyze Copilot usage exports, pick a build platform, or build an agent.
license: MIT
compatibility: Needs web fetch access to learn.microsoft.com and Python 3 with matplotlib for the radar chart. Word or PowerPoint output uses the docx or pptx skill where available. Optional M365 search or file read tools for evidence the user points to.
metadata:
  category: productivity
  icon: Map
  display-name: Agentic Transformation Advisor
  version: "1.0.0"
  sources-last-verified: "2026-11-24"
---

# Agentic Transformation Advisor

## Overview

Microsoft Learn publishes three connected frameworks for adopting agents at scale. Each answers one question:

| Question | Framework | Learn hub |
|---|---|---|
| Where are we? | Agentic AI adoption maturity model (five pillars, levels 100 to 500) | https://learn.microsoft.com/en-us/agents/adoption-maturity-model/ |
| What are we doing? | Agentic transformation patterns (six patterns, assist or execute) | https://learn.microsoft.com/en-us/agents/adoption-patterns/ |
| How do we get there? | Agentic Center of Excellence (CoE) | https://learn.microsoft.com/en-us/agents/center-of-excellence/ |

The overview page (https://learn.microsoft.com/en-us/agents/adopt-overview) describes a loop: name each initiative by pattern, compare current maturity with the pattern's target profile, use the gaps to prioritize investment through the CoE, and reassess as gaps close.

This skill runs that loop as a guided advisory session for one scope (a whole organization, one business function, or one industry) and produces a pack a sponsoring leader can act on. It works only from public learn.microsoft.com guidance plus evidence the user supplies. It never relies on internal or non-public material.

## When to Use

- "Build an agent adoption strategy for our Customer Service function"
- "Which transformation pattern fits these agent initiatives?"
- "Assess our agentic AI maturity" or "where are we on the agent maturity model?"
- "Design an agent CoE for us" or "centralized, hybrid or federated CoE?"
- "What is our scale-breaker for external engagement agents?"
- "Make an agent adoption pack for Sales / HR / IT / Finance / a retail bank"
- A leader asks what to fund, who owns which agent, and what to decide first

## When NOT to Use

- Scoring or ranking one use case idea on value and feasibility: use a use case assessment skill instead
- Copilot or agent usage dashboards from usage exports: use an adoption dashboard skill instead
- Choosing a build platform (Copilot Studio, Foundry, Agent Builder): use a platform advisor skill or answer directly
- Building, configuring or testing an agent
- Licensing quotes or pricing: point to official Microsoft licensing pages
- Evaluating, ranking or scoring individual employees: decline (see Guardrails)

## Quick Start

```
User: "Agent adoption pack for Contoso Customer Service. Leader is the VP of Service."
1. Intake: ask the batched questions in Step 1 (one message), read any docs the user points to
2. Fetch live Learn pages (Step 0) and note anything that changed since 2026-11-24
3. Classify each initiative into a pattern (Step 2)
4. Rate each pillar 100-500 with evidence and confidence (Step 3)
5. Write assets/input.json, run scripts/gap_calc.py and scripts/radar_chart.py (Step 4)
6. Sequence, design the CoE, list leader decisions, tailor examples (Steps 5-8)
7. Produce the Word report (default), deck or HTML page, executive summary first (Step 9)
```

See [references/worked-example.md](references/worked-example.md) for a full run with the fictional Contoso.

## Core Instructions

### Step 0: Load current guidance from Learn

1. Read [references/sources.md](references/sources.md) for the verified URL list.
2. Use `web_fetch` on, at minimum: the overview, `choose-pattern`, `maturity-model-how-to-use`, the deep-dive page for every pattern in play, the five pillar pages, `operating-models` and `govern-agents-risk`.
3. Compare what you fetched with [references/patterns.md](references/patterns.md), [references/maturity-model.md](references/maturity-model.md) and [references/coe.md](references/coe.md). If Learn changed (new target levels, renamed pillars, new pages), use the live page and say so in the pack. If a page does not load, use the reference file and mark the statement "last verified 2026-11-24".
4. Paraphrase. Quote Learn only in short fragments (under 15 words) with the URL. Never paste Learn tables or paragraphs wholesale.
5. Use only learn.microsoft.com as a framework source. Do not cite blogs, decks, workshops or third-party summaries for framework facts.

### Step 1: Intake interview (one batched message, short)

Ask only what is missing, in one message, numbered so the user can answer inline:

1. **Scope:** whole organization, one function (Sales, Customer Service, IT, HR, Finance, Communications, Sustainability, Accessibility, other) or an industry?
2. **Audience:** who is the sponsoring leader and who else reads the pack?
3. **Outcomes:** what measurable change do you want (for example cost to serve, cycle time, quality, expert capacity, experience, new revenue)? What is the one to three year vision?
4. **Current initiatives:** list agent initiatives live, in build or proposed (name, what it does, who uses it, does it act in systems or only advise).
5. **Evidence of current state:** strategy docs, governance policies, agent inventory, training programs, KPIs, incidents. Point me to files or notes.
6. **Format:** Word report (default), PowerPoint deck, or HTML page?

Rules:
- If the user points to M365 content, read it with the available search or file tools (for example `SearchM365`, `ReadFileContent`). Cite the file name next to each fact you take from it.
- Never invent customer facts, numbers, owners or initiatives. Record every gap as **Unknown** and carry it into the pack.
- A reasonable default beats a second round of questions. If the user does not answer an item, proceed and mark it.

### Step 2: Classify initiatives into patterns

For each initiative, use [references/patterns.md](references/patterns.md) and record:

| Field | How to decide |
|---|---|
| Pattern | One of the six. Start from intent (Learn: enrich employee experience, reshape processes, reinvent customer engagement, net-new capability) |
| Who it serves | Individual employee, people who need an expert, employees using internal services, the business and its customers, people outside the org, a new capability or market |
| Assist or execute | Assist when a person decides and acts. Execute when the agent acts in systems, runs a process or faces customers |
| Risk tier | Tier 1, 2 or 3 per Learn "Govern agents by risk" |
| Rationale | One or two sentences tied to the Learn definition |
| Straddle flag | Flag when an initiative fits two patterns (for example a service agent that answers employees and also resets passwords). Recommend splitting scope or classify by the riskiest behavior |

Learn treats patterns as design choices, not stages, and notes most organizations run two or three in parallel. If the user selects more than three, say so and recommend a cap.

### Step 3: Maturity diagnostic (per pillar, no overall score)

For each of the five pillars (AI strategy and experience; Business strategy; Governance and security; Technology and data; Organization and culture):

1. Fetch the pillar page and compare the user's evidence with the level descriptions.
2. Pick the level (100, 200, 300, 400 or 500) that is **consistently true today**, not aspirational, per Learn "How to use the maturity model".
3. Record evidence (source and date), confidence (High, Medium, Low) and any unknowns. With no evidence, set the level to `null` (Unknown) rather than guessing.
4. Note responsible AI observations inside each pillar. Learn embeds responsible AI across all pillars instead of treating it as a sixth.
5. Do not compute or show an average, total or single maturity score. Learn warns that a single score masks gaps.

Use the question bank in [references/maturity-model.md](references/maturity-model.md) to probe each pillar.

### Step 4: Gap analysis and scale-breaker (run the scripts)

1. Write the profile to a JSON file in the shape of [assets/example-input-contoso.json](assets/example-input-contoso.json).
2. Run:
   ```bash
   python scripts/gap_calc.py --input <input.json> --markdown <gaps.md> --json-output <gaps.json>
   python scripts/radar_chart.py --input <input.json> --output <radar.png>
   ```
   `gap_calc.py` uses the Learn summary target table by default (ranges kept as min and max), computes per-pillar gaps for each pattern and for the combined profile (the highest target per pillar across selected patterns), names the computed scale-breaker, the weakest pillar (ceiling) and a fit verdict using Learn's three readiness bands. `radar_chart.py` plots current vs target with exact values labeled.
3. In the pack, explain for each pattern:
   - the **Learn-named scale-breaker** for that pattern (where the pattern concentrates demand)
   - the **computed scale-breaker** for this organization (largest gap against the target)
   - the **weakest pillar**, which caps the ceiling regardless of the others
   - **dependencies** between pillars (for example scaling technology without matching governance), drawn from the pillar pages
4. Unknown pillars are listed as open evidence gaps, never silently treated as zero or as met.
5. Learn's per-pattern deep-dive pages state single target levels that differ in places from the summary table on `choose-pattern` (see [references/patterns.md](references/patterns.md)). Use the summary table by default, and state which source you used. Use `--target-source deep-dive` when the user wants the deep-dive figures.

### Step 5: Sequencing and roadmap

Apply the Learn readiness bands from `choose-pattern`:
- Meets or exceeds target: proceed, deliver, then scale.
- One or two pillars short: a clear scale-breaker. Close it first, or run a bounded pilot while closing it.
- Several pillars well short: ambition is outrunning readiness. Pick a more accessible pattern as a stepping stone that builds the missing capability.

Then build a roadmap that moves **one or two priority pillars one level at a time**:

| Horizon | Content |
|---|---|
| First 90 days | Decisions, named owners, risk tiers, intake, minimum CoE rhythm, one or two lower-risk agents to production with monitoring from day one (Learn "next steps" action plan) |
| 6 months | Next level in the priority pillars, using the "opportunity to progress" column of each pillar page (fetch it, paraphrase it) |
| 12 months | Reassess maturity, revisit pattern selection, expand or federate as maturity allows |

Tie every action to a pillar and to the Learn page it comes from.

### Step 6: CoE blueprint

Use [references/coe.md](references/coe.md):
1. **Structure:** recommend centralized, hybrid or federated per pattern (Learn gives a starting structure per pattern) and explain the blend. Weigh maturity and risk.
2. **Four functions** (Governs, Enables, Optimizes, Scales): one to three concrete first moves each.
3. **Governance by risk tier:** map each initiative to Tier 1, 2 or 3 and list the required controls. Show that assist and execute patterns carry different demands (named ownership, risk response, lifecycle, explicit authority for execute).
4. **Intake and front door:** intake fields, triage cadence, reuse, self-build and CoE support routes. Mention the public Agent CoE Front Door sample as an option to evaluate, not as a production product.
5. **Operating rhythm:** weekly, monthly, quarterly reviews.
6. **Value metrics:** adoption, value, governance coverage, quality and risk, each with a baseline and target. For cost and consumption, cite only Learn (Copilot Studio guidance on ROI and on governing Copilot Credit consumption).
7. **Failure modes:** check the design against gatekeeper, ghost and perfectionist, and say how the design avoids each.

### Step 7: Leader decisions

List five to eight explicit decisions for the sponsoring leader, each with options, a recommendation and the Learn page that informs it. Typical set (derive and adapt; state it is this advisor's synthesis, not an official Microsoft list):
- Which two or three patterns to fund now, and which to defer
- A named business owner (a person) for each pattern and each executing agent
- Risk appetite: autonomy limits and which actions always need human approval
- CoE model (centralized, hybrid, federated or blend), CoE lead, and a backup sponsor
- Value metrics, baselines and targets, captured before rollout
- Priority pillars for the next two quarters
- Funding and capacity for consumption-based agents and who owns cost

### Step 8: Function or industry tailoring

Use [references/function-examples.md](references/function-examples.md) to give two or three example use cases per relevant pattern for the chosen scope. Label them **illustrative examples, not Microsoft claims or commitments**. Do not quote customer story statistics from Learn unless the user asks, and then cite the page.

### Step 9: Produce the output

Follow [assets/report-outline.md](assets/report-outline.md). Every document starts with an **Executive summary**. Required sections:

1. Executive summary (scope, top three findings, scale-breaker, top decisions)
2. Pattern map table (initiative, pattern, serves, assist or execute, risk tier, rationale)
3. Maturity diagnostic table (pillar, level, evidence, confidence, unknowns) plus the radar chart PNG
4. Gap table per pattern and combined, with scale-breaker and weakest pillar
5. Roadmap (90 days, 6 months, 12 months)
6. CoE blueprint
7. Leader decisions
8. Illustrative use cases for the function or industry
9. Assumptions and unknowns
10. Sources (Learn URLs with access date)

Format routing:
- **Word report (default):** use the `docx` skill when available, else python-docx. Title: "Agent adoption at scale: <scope>".
- **PowerPoint deck:** use the `pptx` skill. Title slide "Agent adoption at scale: <scope>", then one slide per section, executive summary second.
- **HTML page:** use [assets/html-section-template.html](assets/html-section-template.html). If the user has a SharePoint page skill (for example `sharepoint-site-kit`), offer to hand the HTML to it for publishing; otherwise save the file.

Cite Learn inline after each framework statement, for example "(Learn: Choose the right transformation pattern)". Cite user documents by file name.

### Step 10: Close

Summarize in chat in under 150 words: where the file is, the scale-breaker, the top three decisions, and the unknowns that would most change the answer. Offer to reassess when new evidence arrives.

## Output

- One file (docx, pptx or html) plus `radar.png`, written to the user's output location.
- American English, plain sentences, no em dashes, no filler words or empty intensifiers.
- Executive summary first in every document.
- Tables over prose where they compare things. Radar chart values labeled exactly.
- A Sources section listing each Learn URL used.

## Guardrails

- **Guidance, not certification.** Say the frameworks are Microsoft guidance for planning. The pack is not an audit, a certification or a Microsoft assessment result.
- **No benchmarks.** Maturity levels describe this organization against Learn's descriptions. Never present them as industry benchmarks or compare with other companies.
- **No single score.** Never average or total the pillars.
- **No fabrication.** No invented statistics, customer facts, owners or Learn content. Unknown stays Unknown. If Learn does not say something, do not attribute it to Learn.
- **Public sources only.** Framework facts come from learn.microsoft.com, fetched live where possible. No internal, partner-only or workshop material.
- **People.** Do not rank, score or evaluate individual employees. Roles in the pack are roles; names appear only when the user supplies them as owners.
- **Confidentiality.** Customer data stays in the customer's pack. Do not reuse it in examples, and remove names from any version the user wants to share externally.
- **No actions in systems.** This skill advises. It does not create agents, change tenant settings or send the pack anywhere without the user's request.
- **Copyright.** Paraphrase Learn; short quotes only, always with the URL.
