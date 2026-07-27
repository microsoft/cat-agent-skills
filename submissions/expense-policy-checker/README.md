# Expense Policy Checker

A first pass over an expense claim before it goes to finance: missing
receipts, over-limit items, vague justifications, and anything that needs
pre-approval, checked against your organization's actual expense policy.

## How it's grounded

Same discipline as [`hr-policy-navigator`](../hr-policy-navigator): it never
brings its own assumptions about what a "reasonable" expense policy looks
like. It searches whatever policy source is configured (uploaded documents or
a connected knowledge base) and answers only from what's actually retrieved.
If nothing is configured, it says so rather than applying a generic guess.

## What it won't do

Approve or reject a claim. That decision, and the actual submission, stays
with a person or a dedicated approval workflow. This skill's job is to catch
the fixable issues (a missing receipt, a vague description, an over-limit
line) before the claim reaches that step.

## Pairs well with

[`hr-policy-navigator`](../hr-policy-navigator) for the same grounded-lookup
pattern applied to HR policy instead of finance, and
[`grounded-citation-guardrail`](../grounded-citation-guardrail) for the
underlying citation discipline both skills rely on.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
