---
name: Customer Sentiment Triage
description: "Classify inbound customer messages by sentiment and urgency, then route them to the right queue."
agentDescription: "Use this skill whenever an inbound customer message needs to be classified by sentiment and urgency and routed to the right queue, before drafting any reply."
platforms: [Copilot Studio, Cowork]
tags: [support, classification, customer, sample]
author: Support Excellence Team
version: 1.3.0
createdAt: 2026-01-28
updatedAt: 2026-04-09
---
Read inbound customer messages and decide how they should be handled.

## Instructions
1. Classify each message on two axes:
   - **Sentiment**: Positive, Neutral, Negative, or Critical.
   - **Urgency**: Low, Medium, High.
2. Choose a **route** based on the matrix:
   - Critical sentiment *or* High urgency → `escalation`.
   - Negative + Medium → `priority-support`.
   - Everything else → `standard-support`.
3. Extract the customer's core ask in one sentence.
4. Detect and flag any mention of churn, legal action, or security so a human is
   looped in immediately.
5. Output a compact JSON object: `{ sentiment, urgency, route, summary, flags }`.

## Guardrails
- Do not draft a customer-facing reply unless explicitly asked.
- Never downgrade urgency to clear a backlog.

## Tone
Calm and objective. The goal is accurate routing, not emotional mirroring.
