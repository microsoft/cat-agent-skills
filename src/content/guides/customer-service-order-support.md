# Customer Service & Order Support

For contact-centre and digital-care agents handling the small, repeatable set of intents that
carry most retail service traffic — where is my order, can I return this, is it in stock, what
does the policy say.

It classifies intent against the taxonomy, assembles customer, order, loyalty and delivery
context while detecting contradictions between sources, retrieves the approved answer, and
either drafts the resolution in channel and tone or builds a structured handoff packet.

The design bet is reliability over reach: a confident wrong answer costs more than an
escalation.

## How it works

1. Classifies intent against the taxonomy (deterministic).
2. Consolidates customer, order, loyalty and delivery context; flags contradictions.
3. Retrieves the approved answer with its citation.
4. Drafts the resolution in the customer's channel and tone.
5. Builds the structured escalation when confidence is below threshold.

## Example scenario

Delivered-not-received, with refund-now pressure and a chargeback threat.

- The intent resolves to **delivered-not-received**, which outranks a routine order-status
  read.
- The **carrier scan contradicts the customer's account** — the contradiction is recorded with
  its citation, and the interim reply never disputes the customer directly.
- The instant-resolution gate is **not met** on tier or value, so it routes to investigation
  with the clock attached, and goodwill is recorded as a **proposal for a human**.

A naive agent promises the instant refund.

## What you bring

Knowledge articles, CRM case history, OMS order status, loyalty records, delivery and carrier
status, product documentation, approved scripts and service policy.

## Boundaries

Resolution drafts and escalation packets. It does not issue goodwill credit, change payment
details or grant an unsupported policy exception.
