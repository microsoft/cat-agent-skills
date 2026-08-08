# Customer Support Response Drafter

Turns an inbound support email, ticket, or chat message into a ready-to-send
reply, grounded in your organization's actual product and policy knowledge,
with anything needing a human decision (a refund above threshold, a churn-risk
customer, an explicit request for a manager) clearly flagged instead of
drafted as final.

## How it's different from it-support-ticket-agent

[`it-support-ticket-agent`](../it-support-ticket-agent) is for *internal* IT
issues: an employee's own hardware, software, or access problem, logged as a
ticket. This skill is for *external* customer support: replying to someone
outside the organization who has a product question, a complaint, or a
request. Different audience, different job.

## How it's grounded

Same discipline as [`grounded-citation-guardrail`](../grounded-citation-guardrail)
and [`hr-policy-navigator`](../hr-policy-navigator): it answers product and
policy questions only from what's actually retrieved from your organization's
own knowledge sources, and says so plainly when something isn't covered
instead of guessing at a plausible-sounding answer.

## What it won't do

Promise a refund, credit, or exception the retrieved policy doesn't support,
send a flat cheerful reply to a genuinely serious complaint, or draft a final
answer over an explicit request to speak to a human.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
