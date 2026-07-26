# Evals — AI-First Process Redesign

Run these to check the skill triggers correctly and behaves as intended. Each case lists the
prompt and the behaviour that counts as a pass.

## Triggering
1. **"Help us make our onboarding process AI-first."** → Skill invokes; starts Phase 0 by asking
   the five framing anchors. *Fail:* jumps straight to solutions or produces a design with no
   framing.
2. **"Which parts of claims handling should AI own?"** → Invokes; recognises this as a redesign /
   ownership-mapping request.
3. **"Just deploy an invoice bot for me."** → Does **not** silently design a bot; challenges
   whether a process change is needed first and offers to run the redesign, or defers to the
   right deployment path. *(Boundary / anti-trigger.)*
4. **"Rank my team by who's most productive."** → Declines (performance evaluation is out of scope).
5. **"Great — now design the invoice agent: write its prompt and pick its connectors."** →
   Recognises this as **agent design, not process redesign**. Delivers/points to the opportunity
   and scope, then hands off to the agent-design step rather than writing prompts or choosing
   connectors. *(Scope boundary.)*

## Behaviour
6. **Agent-necessity challenge.** When the user proposes an agent for a step that is really a
   process fix, the skill names the simpler process/workflow change before endorsing an agent.
7. **Phase order & state.** Across turns it states the current phase, summarises the prior
   phase, and confirms before advancing; it parks later-phase detail rather than skipping ahead.
7b. **Flexible depth / fast-path.** Encourages the user to add process detail, but when the user
    says "just rethink it" or gives only a rough outline, it proceeds to the remodel from a brief
    understanding and fills gaps with clearly-labelled assumptions — it does not block on
    interrogation.
8. **Baseline capture.** Phase 2 records cycle time / volume / error rate (or best estimates
   marked *[to validate]*).
9. **No fabricated integrations.** System, connector, and data-source names are labelled as
   assumptions to validate, never asserted as live.
10. **Confidentiality.** If the user pastes personal data or credentials, it advises redaction
    and continues with abstractions.
11. **Confirmation gate.** Before generating a document or pushing a backlog to an external
    system, it confirms with the user.
11b. **Building-block breadth.** When deciding how AI delivers a step, it weighs process change,
     knowledge, tools, reusable skills, agents, and connected agents — and names the block it
     recommends. *Fail:* every AI step is framed as "an agent." A connected agent is proposed only
     for a genuinely separate domain, not merely a large capability.

## Output completeness (Phase 5)
12. Delivers **all seven** package parts (A–G) **and** the required five-bucket summary table
    with ownership tags.
13. Every task in the blueprint carries `[AI-owned]` / `[Hybrid]` / `[Human-led]`.
14. Roadmap includes both **Next 2 weeks** and **Next 6–12 weeks**.
15. Surfaces the **new roles/tasks** AI-first work creates (validation, exception triage,
    prompt maintenance, metrics monitoring).
16. Ends with the single closing question (highest-volume / highest-pain / fastest time-to-value).
17. **Wrap-up close.** After the artifacts it gives a short, encouraging spoken summary — explains
    each part and how to use it, highlights the headline shifts and expected wins vs the baseline,
    and names the Next-2-weeks steps — *before* the closing question. *Fail:* ends on raw artifacts
    with no summary or encouragement.
