# Response Quality Diagnosis Handoff

Every completed analysis should end with a concise user-facing diagnosis the operator can act on. Do not end on tool output alone.

## Required Shape

Use this structure (adapt headings as needed):

1. **Verdict** — one or two sentences: what happened and the primary root cause.
2. **Evidence** — short bullets tied to log/search facts:
   - Question (and standalone form if different)
   - Outcome (`couldAnswer`, rating, escalation)
   - Whether logged sources contained the answer (quote a minimal snippet or say they did not)
   - What live semantic search returned now (rank / missing / only at high `top_k`)
3. **Root cause** — name the taxonomy class from [diagnosis.md](diagnosis.md).
4. **Prompt control** — say whether prompt instructions can improve the behavior and name the relevant prompt surface. If not, say why; do not manufacture a prompt fix.
5. **Recommended fixes** — ordered, concrete, bot-specific. Distinguish:
   - Already applied (with source/question IDs)
   - Ready to apply if the user approves
   - Dashboard-only / Skill Builder handoffs
6. **Next step** — when one or more fixes are ready to apply, explicitly ask the user if they want you to make those proposed changes now. Do not stop at a report-only summary when actionable remediations exist.
7. **Verify** — exact queries to retest with semantic search and/or Chat, and which page to open.
8. **Open items** — indexing pending, missing authorization, or unresolved clusters.

## Single-Incident Example Skeleton

```markdown
## Verdict
The bot escalated because retrieval never saw your refund window policy—the indexed help center page is failing, so no usable chunk reached the model.

## Evidence
- Question: "How many days do I have to request a refund?"
- couldAnswer: false; escalated: true
- Logged sources: marketing homepage snippets only; no refund policy text
- Live semantic search (`top_k` 6 and 16): no refund-policy hits; source "Help Center" status failed / 0 chunks

## Root cause
Missing knowledge (failed source)

## Recommended fixes
1. Reingest or replace the Help Center source (sourceId: …).
2. Revise this log into a Q&A pair for the 30-day refund window (creates/merges the bot Q&A source), then mark the question revised.
3. Retest with semantic search using the original question and a paraphrase after chunks > 0.

## Next step
Want me to apply these fixes now (reingest Help Center and revise this answer into Q&A)?

## Verify
Run Search for "refund window" and "How many days to request a refund?" Expect Help Center or Q&A chunks in the top results before retesting the full chat answer.
```

## Cluster Example Skeleton

```markdown
## Verdict
About half of last week's unanswered questions are the same gap: account-specific order status, which docs cannot answer.

## Top clusters
1. Order status / tracking — action/skill gap
2. Password reset URL outdated — missing/stale knowledge (semantic search misses current URL)
3. Partner pricing — correct refusal / needs human

## Highest-impact fixes
1. Enable or build an order-status action/skill.
2. Update the password-reset source or revise a representative question into Q&A.
3. Keep partner pricing on escalation; improve support link copy.

## Next step
Want me to apply the fixes I can make now (update the password-reset source / revise a representative Q&A), and outline the order-status action next?
```

## Style Rules

- Lead with the causal explanation, not a tour of DocsBot features.
- Explicitly flag hallucinated, contradicted, or unsupported claims. If the evidence cannot prove a claim false, call it unsupported rather than false.
- Cite question IDs and source IDs when recommending writes.
- Minimize customer PII; paraphrase emails/names unless the user needs the exact value.
- If several causes are plausible, rank them and say what semantic-search evidence would distinguish them.
- Link product docs only when they help the operator take the next step (response quality, prompts, widget `contextItems`).
- When dashboard navigation is available, navigate once to the most useful page for the next human action.
- After recommending actionable fixes or improvements, ask whether the user wants you to apply them. Do not leave the analysis as report-only when you can perform the remediation.
