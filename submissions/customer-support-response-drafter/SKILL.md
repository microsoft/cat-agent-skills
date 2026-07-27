---
name: customer-support-response-drafter
description: >-
  Use this skill whenever a user needs a reply drafted to an inbound
  customer support email, ticket, or chat message, grounded in the
  organization's own product and policy knowledge sources, before sending
  or finalizing any customer-facing response.
---

Draft a reply grounded in what's actually known, matched to company tone,
and flag anything that needs a human before it goes out.

## Instructions

1. Read the inbound message for what's actually being asked, and separate a
   factual question, a complaint, a request for a refund or exception, and an
   emotional signal (frustration, urgency, a churn risk) if more than one is
   present. Each needs different handling in the same reply.

2. Search the organization's own product and policy knowledge sources (a
   help center, uploaded documentation, a connected knowledge base) for the
   factual parts of the reply. Answer product and policy questions only from
   what's retrieved, the same discipline as
   [`grounded-citation-guardrail`](../grounded-citation-guardrail). If
   something isn't covered, say so in the draft rather than guessing at an
   answer that sounds plausible.

3. Match the organization's actual support tone and format if it's known
   (from a style guide, prior examples, or a stored preference), rather than
   defaulting to a generic customer-service voice. Acknowledge the customer's
   actual situation before jumping to the resolution; a reply that answers
   the question but ignores that the customer is frustrated reads as tone-deaf.

4. Flag rather than draft a final answer for anything that needs a human
   decision: a refund or credit above a stated threshold, a request that
   falls outside documented policy, anything that reads as a legal threat or
   a safety issue, a customer who explicitly asks for a manager or a human,
   or a situation with real churn risk (a long-tenured or high-value customer
   expressing serious dissatisfaction). Draft what can be answered, and
   clearly mark the parts that need review before sending.

5. For a straightforward, fully covered question, produce a complete,
   ready-to-send draft. Don't add unnecessary hedging or escalate a simple
   question just to be cautious.

6. If the same issue is likely to recur (a bug, a confusing part of the
   product, a policy gap), note that separately from the reply itself. That
   observation is useful even though it isn't part of what goes to the
   customer.

## Guardrails

- Never promise a refund, credit, discount, or policy exception the retrieved
  policy doesn't actually support, or that exceeds a stated approval
  threshold, without flagging it for human approval first.
- Never state a product capability, timeline, or fact that isn't backed by
  the retrieved sources. "I don't have that confirmed, let me check" is
  better than a plausible-sounding guess in a customer-facing reply.
- Never send a reply that ignores an explicit request for a human or a
  manager.
- Don't apply a flat, cheerful tone to a genuinely serious complaint. Match
  the tone to the situation.

## Tone

Warm and specific in the drafted reply itself; direct and matter-of-fact when
talking to the user about what needs their review before sending.
