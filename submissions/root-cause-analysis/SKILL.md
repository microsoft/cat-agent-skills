---
name: root-cause-analysis
description: Use this skill whenever the user asks to diagnose why something failed, find the root cause of an incident, conduct a post-mortem, analyze a problem or defect, distinguish symptoms from causes, or apply 5 Whys or Fishbone analysis. Trigger on phrases like "why did this happen", "root cause", "post-mortem", "5 whys", "fishbone", "what caused this", "diagnose the failure", "why did it fail", "underlying cause". Do NOT trigger for general problem solving (use business-os), refining existing plans (use idea-refiner), or content quality audits (use content-quality-auditor).
---

# Root Cause Analysis

Guide the user through structured problem diagnosis to move from observed symptoms to the true underlying cause, using repeatable techniques that prevent guessing or stopping at surface-level fixes.

## Instructions

1. **Lock the problem statement**
   - State the exact symptom or failure in one sentence.
   - Capture when it occurred, where, and who or what was affected.
   - Do not allow vague wording like "it broke" or "performance is bad."

2. **Map the symptom chain**
   - List every observed symptom as a fact, not a hypothesis.
   - For each symptom, ask: "What could produce this?"
   - Keep asking "why" at least three levels deep before proposing any cause.

3. **Apply 5 Whys**
   - Start from the problem statement.
   - Ask "why" repeatedly, recording each answer.
   - Stop when you reach a cause that, if fixed, would prevent the symptom from recurring.
   - If you reach a cause that is a contributing factor rather than a fixable origin, keep going.
   - Load `references/rca-methods.md` if the problem is complex or the user asks for a specific technique.

 4. **Build a Fishbone diagram**
    - Categorize potential causes across: People, Process, Technology, Data, Environment, Management.
    - For each category, list specific contributing factors backed by evidence the user can confirm.
    - Do not invent facts; if a factor is uncertain, mark it as unverified.
    - Use `assets/fishbone-template.html` to structure the diagram. Open the template, replace the placeholder text in each category branch with the contributing factors identified above, and return the filled-in HTML so the user can save and open it.
    - Do NOT build a new diagram from scratch. Do NOT generate matplotlib, code-generated plots, or any output that is not based on the provided template. Editing and returning the provided HTML template is the correct output.
    - Classify every factor as **CONFIRMED**, **UNVERIFIED**, or **DISPROVEN** using the rules in the Evidence classification section below. In particular: only facts stated verbatim or by direct paraphrase in the user's input may be CONFIRMED. If a claim is built on the absence of information — for example, inferring a missing control because no one mentioned it — it must be UNVERIFIED, not CONFIRMED.

 5. **Separate root cause from contributing factors**
    - Root cause: the fundamental origin that, if eliminated, prevents recurrence.
    - Contributing factor: made the problem more likely or more severe, but is not the origin.
    - Present both clearly; fixing only contributing factors will not fully resolve the issue.

 6. **Output the diagnosis**
    - Root cause: one precise sentence.
    - Evidence: the "why" chain or diagram nodes that support it.
    - Contributing factors: bullet list with severity or likelihood.
    - Recommended actions: ordered by whether they address the root cause or only contributing factors.

## Evidence classification

Classify every factor in the fishbone as **CONFIRMED**, **UNVERIFIED**, or **DISPROVEN**.

- **CONFIRMED** — the fact is stated verbatim in the user's input, or is a direct paraphrase with no added detail.
- **UNVERIFIED** — the fact is an inference, an assumption, or any detail not explicitly provided by the user. This also includes claims built on the absence of information (for example, inferring a missing control from the fact that no one mentioned it).
- **DISPROVEN** — the user's input directly contradicts the claim.

**Rule:** Only facts present verbatim or by direct paraphrase in the user's input may be tagged CONFIRMED. Every added detail, inference, or absence of a piece of information that leads you to think the opposite is true, must be UNVERIFIED.

**Positive example (CONFIRMED):**
- User says: "The deploy failed because the config file was missing."
- Factor: "Config file was missing at deploy time." → **CONFIRMED** (verbatim)

**Negative example (UNVERIFIED):**
- User says: "The deploy failed and no one remembered checking the config."
- Factor: "The team did not have a checklist for config validation." → **UNVERIFIED** (inference from absence of information — the user never said a checklist existed or was missing)

## Guardrails

- Never skip the "why" chain. Symptoms are not causes.
- Do not propose fixes before the root cause is stated.
- Separate factual evidence from assumptions; label anything unverified.
- If evidence is missing, say so explicitly rather than inferring.
- Do not assign blame. Describe mechanisms and conditions, not people.
- Stop at actionable causes. Do not drift into speculation or philosophy.
