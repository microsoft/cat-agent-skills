# Agentic Transformation Advisor

Turn Microsoft's public guidance on adopting agents into a plan a leader can act on. The advisor walks one organization, business function or industry through three connected frameworks on Microsoft Learn and produces a pack with clear recommendations, all cited to Learn.

The advisor runs the adoption loop as a guided advisory session for one scope (a whole organization, one business function, or one industry) and produces a pack a sponsoring leader can act on.

| Question | Framework on Microsoft Learn |
|---|---|
| Where are we? | [Agentic AI adoption maturity model](https://learn.microsoft.com/en-us/agents/adoption-maturity-model/): five pillars, levels 100 to 500 |
| What are we doing? | [Agentic transformation patterns](https://learn.microsoft.com/en-us/agents/adoption-patterns/): six patterns, assist or execute |
| How do we get there? | [Agentic Center of Excellence](https://learn.microsoft.com/en-us/agents/center-of-excellence/) |

## What you get

- **Pattern map:** each of your agent initiatives classified into one of the six transformation patterns.
- **Maturity radar:** current and target levels for each of the five pillars, with no single overall score.
- **Gap and scale-breaker analysis:** where you fall short of each pattern's target profile, and the one pillar most likely to stop you scaling.
- **Roadmap:** 90-day, 6-month and 12-month steps, sequenced by the gaps.
- **CoE blueprint:** operating model, the Governs, Enables, Optimizes and Scales functions, and the failure modes to avoid.
- **Leader decisions:** the calls a sponsor needs to make first.

The pack comes as a Word document by default, a PowerPoint deck on request, or a SharePoint HTML page when used with the SharePoint Site Kit skill. Every pack starts with an executive summary and ends with a sources section.

## Example prompts

- "Build an agent adoption strategy for our Customer Service function."
- "Which transformation pattern fits these five agent initiatives?"
- "Assess our agentic AI maturity and find our scale-breaker."
- "Design an agent CoE for a 20,000-person retail bank. Centralized, hybrid or federated?"

## Quick start

Try: "Agent adoption pack for Contoso Customer Service. Leader is the VP of Service."

The advisor asks for scope, outcomes, initiatives and evidence, checks the current Learn guidance, then builds the pattern map, maturity diagnostic, gap analysis, roadmap and CoE blueprint. Choose a Word report (the default), a PowerPoint deck or an HTML page.

## What you need

- Web access to learn.microsoft.com, so the advisor can check the current guidance.
- Python 3 with matplotlib for the radar chart.
- **Word output:** the `docx` skill is optional. Without it, the Python environment must have `python-docx` installed for the fallback.
- **PowerPoint output:** the `pptx` skill is required. There is no standalone deck-generation fallback.
- Optional: search or file-read tools for evidence you point it to.

## Good to know

- **Public sources only.** Framework facts come from learn.microsoft.com. The advisor never uses internal or partner-only material.
- **Evidence from you.** Maturity ratings come from your answers and documents. Anything unknown stays marked Unknown.
- **Advice only.** It doesn't build agents, change tenant settings or send the pack anywhere.

