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

5. **Separate root cause from contributing factors**
   - Root cause: the fundamental origin that, if eliminated, prevents recurrence.
   - Contributing factor: made the problem more likely or more severe, but is not the origin.
   - Present both clearly; fixing only contributing factors will not fully resolve the issue.

6. **Output the diagnosis**
   - Root cause: one precise sentence.
   - Evidence: the "why" chain or diagram nodes that support it.
   - Contributing factors: bullet list with severity or likelihood.
   - Recommended actions: ordered by whether they address the root cause or only contributing factors.

## Guardrails

- Never skip the "why" chain. Symptoms are not causes.
- Do not propose fixes before the root cause is stated.
- Separate factual evidence from assumptions; label anything unverified.
- If evidence is missing, say so explicitly rather than inferring.
- Do not assign blame. Describe mechanisms and conditions, not people.
- Stop at actionable causes. Do not drift into speculation or philosophy.
