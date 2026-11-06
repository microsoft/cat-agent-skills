# Classification and evidence rules

Loaded on demand by `create-playbook` at Step 5. Apply these rules
exactly; they decide what the playbook is allowed to call a standard.

## The three classifications

| Label | Meaning | Test |
|---|---|---|
| `Candidate standard` | A materially consistent position supported by the corpus | At least three included precedents address the topic **and** a clear majority of them reach the same outcome |
| `Accepted alternative` | A distinct position that recurs, or is clearly contextual | Appears in the corpus but does not command the majority, or is explained by a stated context (sector, volume, jurisdiction, counterparty type) |
| `Counsel decision` | Evidence does not support a rule | Conflicting, sparse or context-dependent evidence, or fewer than three precedents on the topic |

## Small-sample rule — evidence strength, not just agreement

Require at least three included precedents addressing a topic, and a clear majority
among them, before classifying anything as `Candidate standard`. Where fewer than
three address it, classify it `Counsel decision` and label the evidence
`Single-instance evidence` or `Sparse evidence (n=2)`, **even when the sources
agree perfectly**. Perfect agreement across two documents is a coincidence the
corpus cannot distinguish from a rule.

## No averaging

Never resolve a split by averaging. A midpoint no counterparty has signed is not an
approved outcome. Present the competing outcomes with their precedent names and
locators, and put the choice to counsel.

## No inferred hierarchy

Do not call an alternative a `fallback position` unless the sources or the user
establish a negotiation hierarchy. Approved end states reveal where negotiations
landed, never which concession came first. Only fallbacks the user expressly
supplies belong in `Compromise Positions`, in the user's stated negotiation order.

## Drafts and negotiation markup

In a draft, only the user's own side's tracked changes and comments are evidence of
a position — a **requested** position. The other side's changes, and unmarked text
on the other side's paper, are not evidence of the user's position. Where it is
unclear which side made a change, do not count it, and say so in the coverage
summary.

Requested positions count towards the three-precedent test in the same way as
agreed positions. When a topic's positions are a mix, say so. When agreed and
requested positions conflict on a topic (for example, signed deals settled on a
lower cap than the user's markup asks for), classify the topic `Counsel decision`
and show both — this gap between what the user asks for and what deals settle on
is useful for counsel, and often points to a compromise position.

## Evidence strength labels used in chat

- `Single-instance evidence`
- `Sparse evidence (n=2)`
- `Majority (n of m)`
- `Split (n of m / n of m)`
- `Requested positions only (drafts)`
- `Agreed and requested positions conflict`
- `Not addressed in the corpus`

These labels, the source counts and the classifications live in the chat output
only. They must never appear in the `Instructions` or `Example Text` cells, which
are written for direct use during markup.

## Thin or inconsistent corpus

If the corpus is too incomplete or inconsistent to support a responsible
playbook, produce a partial table only where it remains useful, identify it as
partial in chat, and put the limitations and required counsel decisions prominently
in the coverage summary rather than presenting them as settled policy.
