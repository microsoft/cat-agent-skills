---
name: qualification-memo
description: Drafts the supplier qualification memo for approval from the contract payload - outcome, conditions, risk detail, AVL position. Use when the user says "draft the qualification memo", "write it up for approval", or after avl-compare in a run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Supply Chain}
---
# Qualification Memo
## Purpose
Terminal artifact: the approval memo rendered from templates/memo-template.md, populated only from the contract payload.
## When to use
End of every qualification run.
## Inputs
compared.json (full payload).
## Steps
1. Validate against the contract; escalations lead the memo.
2. Fill the template: outcome, named conditions, three risk dimensions with notes and citations, AVL position, dossier index.
3. Mark DRAFT - sourcing leadership approves; nothing is awarded or added to the AVL by this plugin.
## Output
QUAL-<supplier>.md - terminal artifact.
## Grounding requirements
Every claim cites a dossier document, AVL row, or rule section.
## Constraints
- Draft-first; nothing in the memo that is not in the contract payload.
- A conditional outcome is never summarized as "approved".
## Escalation / uncertainty
Open conditions render as a checklist gating the award.
