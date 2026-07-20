# Worked examples

Short, illustrative walk-throughs. These show the reasoning pattern, not a script to copy word for word.

## Fast path: "Rewrite this paragraph professionally"

No classification step is shown to the user, no plan, no references loaded. The paragraph is rewritten and returned. That's the whole interaction.

## Structured path: "We need to onboard a new supplier"

Outcome: a working, low-risk onboarding of this supplier. Classification: process, with elements of task. Sizing: structured, moderate stakes (financial and compliance exposure, but a routine business activity).

The response works out generic supplier onboarding stages (due diligence, contract, systems setup, first order), flags that approval thresholds, required checks, and specific systems are organisation-specific and not yet known, and asks only for the blocking pieces (for example, whether a due-diligence or sanctions check is mandated here). It does not invent a company policy to fill the gap.

## Deep path: "Should we replace our CRM?"

Outcome: a sound, defensible recommendation on CRM replacement. Classification: decision, deep path (material spend, cross-functional impact, reversibility is moderate to low once implemented).

Lenses applied: economic (cost and ROI), technology (integration, migration risk), operating (process disruption), customer (impact on service during transition), implementation (who runs the migration). The sceptic lens is applied before finalising: what would make "replace" the wrong call (for example, if the real problem is poor adoption of the current system rather than the system itself). Output uses `assets/templates/decision-brief.md` or `assets/templates/recommendation-memo.md` depending on audience.

## Figure It Out: "Something is wrong with margins, figure it out"

Outcome: understand what's driving the margin issue and propose next steps. Classification: problem, with likely decision and communication follow-on. Sizing: deep, given the ambiguity and financial stakes.

Gathers what's already known (any figures, timeframes, or product lines mentioned), applies `problem-solving.md` to separate symptom from cause, identifies the blocking gap (which segment or period is driving it, if not already stated), and proceeds with a hypothesis tree rather than a single guessed cause. Produces a short diagnostic summary and a recommended next investigative step, rather than a definitive root cause the evidence doesn't support.

## Deep path with jurisdiction limits: "We're opening operations in Germany"

Classification: project, with legal/regulatory sensitivity. This response identifies the areas needing authoritative local expertise (employment law, tax, regulatory registration) rather than presenting generic knowledge as sufficient, and structures the rest (scope, milestones, stakeholders) around that constraint.

## Skill generation: "We've done this supplier review repeatedly, turn it into a Skill"

Runs `assets/templates/skill-candidate-assessment.md` first. If the process is genuinely repeatable, stable, and has clear inputs/outputs, proceeds through the pipeline in `skill-generator.md`, producing a full package (`SKILL.md`, relevant references, templates) rather than only a description of what such a Skill might contain.

## Boundary case: "Send the termination email and disable their access now"

This mixes drafting (safe) with executing consequential HR and access actions (not safe to do autonomously). The response distinguishes the two: it can prepare the email and describe the access change needed, but treats sending and disabling as requiring explicit human confirmation and the appropriate authority, per `governance-evidence-qa.md`.
