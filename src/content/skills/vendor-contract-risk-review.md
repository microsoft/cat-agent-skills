---
name: Vendor Contract Risk Review
description: "First-pass review of a vendor contract or SOW for the clauses that commonly cause problems (auto-renewal, liability caps, termination, IP ownership), flagged by risk level to prepare for legal review, not replace it."
agentDescription: "Use this skill whenever a user shares a vendor contract, SOW, or supplier agreement draft and wants a first-pass risk review before it goes to legal, before recommending any change to contract terms."
platforms: [Cowork, Copilot Studio]
tags: [contracts, legal, procurement, risk, vendor-management, review]
author: Tim Karlsson
authorUrl: "https://github.com/Timziito"
authorGithub: Timziito
version: 1.0.0
createdAt: 2026-07-27
updatedAt: 2026-07-27
---
Read the contract for the clauses that commonly cause problems later, flag
them clearly, and never present this as a substitute for legal review.

## Instructions

1. State the limit up front, in the first response: this is a first-pass
   flagging exercise to help the user prepare for legal review, not a legal
   opinion. It doesn't replace an actual lawyer or the organization's legal
   or procurement team.

2. Get the contract text (uploaded document or pasted text). If key sections
   are missing (no termination clause, no liability section at all), treat
   that absence itself as a finding, since a gap can matter as much as bad
   wording.

3. Read for the clauses that commonly cause disputes or unwelcome surprises:
   - **Auto-renewal**: does the contract renew automatically, and if so, how
     much notice is required to opt out, and by when?
   - **Termination**: can either party terminate for convenience, or only for
     cause? What notice period applies? Is there an early-termination fee?
   - **Liability caps**: is liability capped, and at what (fees paid, a fixed
     amount, uncapped)? Are there carve-outs (IP infringement, data breach,
     gross negligence) that remove the cap?
   - **Indemnification**: who indemnifies whom, and for what? Is it mutual or
     one-sided?
   - **Data and IP**: who owns data generated during the engagement? What
     happens to it on termination? Who owns work product or deliverables?
   - **SLA and remedies**: are there measurable service levels, and what
     happens if they're missed? Credits, termination right, or nothing
     stated?
   - **Pricing and escalation**: is pricing fixed for the term, or can it
     change? If it can escalate, is there a cap on the increase?
   - **Governing law and dispute resolution**: which jurisdiction, and is
     arbitration mandatory (which can limit the ability to litigate)?
   - **Assignment and subcontracting**: can the vendor assign the contract or
     subcontract the work without consent?

4. Report findings by risk level (high, medium, low) with the clause quoted
   or paraphrased, why it matters in plain terms, and what a more favorable
   version typically looks like, without drafting replacement legal language
   as if it were ready to use.

5. Distinguish "this is unusual or one-sided" from "this is definitely a
   problem." Some terms are standard for a given deal size or vendor
   relationship and aren't automatically red flags; say so when that's likely
   the case rather than flagging everything as equally risky.

6. Close with a short, prioritized list of what to raise with the vendor or
   legal team first, not a flat list of every clause found.

## Guardrails

- Never present findings as legal advice or a legal opinion. Every response
  should make clear this is preparation for a human legal or procurement
  review, not a substitute for it.
- Never draft final contract language for the user to send back to a vendor
  as if it were legally sound. Describe what a more favorable term typically
  looks like; leave actual drafting to legal counsel.
- Don't flag standard, unremarkable terms as high risk just to appear
  thorough. Over-flagging buries the findings that actually matter.
- If the contract involves a regulated area (data privacy, healthcare,
  financial services, government), say plainly that specialized legal review
  is needed beyond this general pass.

## Tone

Direct and risk-focused, like a procurement analyst doing triage before
handing off to counsel. Plain language over legal jargon wherever possible.
