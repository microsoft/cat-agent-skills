# Output Templates

Both modes share one report skeleton. That is deliberate — a consistent structure makes
the dual-mode design feel intentional rather than assembled, and lets a reader who has
seen one report navigate the other immediately.

---

## Report structure

```markdown
# Agent Architecture Assessment

**Agent:** [name]
**Mode:** [Design | Review]
**Date:** [date]
**Assessment confidence:** [High | Medium | Low] — [what it rests on]
**Rate card:** [date from rate-card.md]

---

## 1. Verdict

**[OPTIMIZE | EXTEND | MIGRATE | REDESIGN]**

[One paragraph. Lead with the decision, then the single most important reason.
No preamble.]

[If OPTIMIZE, the mandatory sentence goes here:]
No platform ceiling was reached. The current platform is the correct one for these
requirements.

---

## 2. Requirement model

| Dimension | Value | Source |
|---|---|---|
| ... | ... | stated / inferred / assumed |

[Every `inferred` and `assumed` row is a caveat on everything downstream. Do not bury
them — a reader needs to know which conclusions rest on guesses.]

---

## 3. Findings register

| ID | Sev | Class | Finding | Evidence | Fix | Effort |
|---|---|---|---|---|---|---|
| F-01 | high | CONFIG | ... | [measurement or artifact element] | ... | low |

Sorted by severity. Class per `ceiling-rules.md`. Evidence names the specific artifact
element or measured value — never "analysis indicates."

---

## 4. Failure simulations

[3–5, severity-ranked. Only from detected findings. Only `medium` confidence or above.]

### SF-01 — [short name]
**From:** [finding ID]  **Confidence:** [high | medium]

```
User:  "..."
Agent: [response and why]
User:  "..."
Agent: [failure or escalation]
```

**Consequence chain**
→ [turn/cost impact]
→ [projected rate at stated volume]

**Root cause:** [CLASS — rule ID]
**Fix:** [action]  **Effort:** [low | medium | high]

---

## 5. Cost & capacity

**Current / projected:** ~[X] [unit]/month  [±40%, rate card [date]]

Top consumption drivers:
1. [driver] — ~[N]%
2. [driver] — ~[N]%
3. [driver] — ~[N]%

**Alternative:** ~[Y]/month  [±40%]
  Fixed: [amount] (does not scale with volume)
  Variable: [amount]

**Break-even:** ~[Z] conversations/month
**Current volume:** [V]
**Assessment:** [above / below / within the indifference band]

Verify current pricing before acting on these figures.

**Token optimization (advisory)** — top 3 techniques for this agent, highest-impact first:
1. [technique] — lever: [context/history/system/output] — expected: ~[band] — trade-off: [risk] — verify: [how]
2. [technique] — lever: [...] — expected: ~[band] — trade-off: [...] — verify: [...]
3. [technique] — lever: [...] — expected: ~[band] — trade-off: [...] — verify: [...]
[If a CEILING finding exists: "These reduce current cost; they do not remove the ceiling in §1."]
[Savings compound multiplicatively, not additively.]

---

## 6. Target architecture

[Diagram — ASCII is fine and often clearer than prose.]

**Components:** [what runs where, and why]

**Boundary contract** [required for EXTEND]:
| Element | Definition |
|---|---|
| Payload schema | ... |
| Latency budget | ... |
| Timeout behaviour | ... |
| Error semantics | ... |
| Fallback path | ... |
| Auth propagation | ... |

**What is lost** [required for MIGRATE]: [channel work, auth, governance inheritance,
maker accessibility, elapsed time]

---

## 7. Roadmap

**Phase 0 — Quick wins (≤1 week)**
- [ ] [action] — addresses [finding IDs]
Exit criteria: [measurable]

**Phase 1 — [name] ([duration])**
- [ ] [action]
Exit criteria: [measurable]  Rollback trigger: [condition]

**Phase 2 — [name] ([duration])**
- [ ] [action]
Exit criteria: [measurable]  Rollback trigger: [condition]

---

## 8. Decision record

### DR-01 — [decision]
**Decision:** [what]
**Driven by:** [finding IDs, requirement fields]
**Alternatives rejected:**
- *[alternative]* — [why not]
- *[alternative]* — [why not]

---

## 9. Open questions

| # | Question | Why it matters | What would resolve it |
|---|---|---|---|
| Q1 | ... | ... | ... |
```

---

## Mode-specific adjustments

### Mode A (Design)

- **Section 1** — the verdict is the recommended target platform, not a change verdict
- **Section 3** — findings are risks in the *proposed* design, not defects in a built one
- **Section 4** — becomes a **pre-mortem**: how this design fails if built as specified.
  This is what elevates Mode A above a questionnaire, so do not skip it.
- **Section 7** — becomes a build plan rather than a remediation plan

### Mode B (Review)

- **Section 2** — flag every inferred field; exports never contain scale or governance
- **Section 3** — the primary section; evidence must cite artifact elements
- **Section 9** — always populated. Exports are always partial.

### Mode B self-report (no artifact)

- Header confidence: **Low**
- Add immediately after the header:
  > This assessment is based on self-reported configuration rather than an agent export.
  > Findings are directional. An export would allow deterministic analysis of trigger
  > collisions, orchestration structure, and configuration completeness.
- Cap all finding confidence at `low`
- **Omit section 4 entirely** — simulations require `medium` confidence minimum

---

## Writing rules

**Lead with the verdict.** The reader wants the decision first. Reasoning follows.

**Evidence over assertion.** "Topics 3 and 7 share trigger phrases at 0.84 similarity"
beats "there may be routing ambiguity." Every finding should be checkable.

**Name the confidence.** A `high`-confidence finding and a `low`-confidence one must not
read identically. The reader's trust depends on being able to tell them apart.

**No padding.** Four well-evidenced findings beat twenty where sixteen are filler. If the
agent is well built, say so and keep the report short — a short report that says "this is
fine" is a valuable output, not a failure.

**Cost carries dates.** Always the rate-card date, always a sensitivity band, always a
verification note.

**Section 9 is not optional.** Stating the limits of the analysis is the strongest
credibility signal available and pre-empts the obvious objection.
