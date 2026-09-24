---
name: copilot-licensing-advisor
description: >-
  Use this skill whenever the user asks which Microsoft 365 Copilot, Copilot
  Studio, or Power Platform license or SKU they need, how many seats to buy,
  or what a rollout would cost, before quoting any price or recommending a
  specific SKU.
---

Interview the user about what they're trying to enable, recommend the license
mix that actually covers it, and cost it out, with current prices fetched at
the time of the conversation, never quoted from memory.

## Instructions

1. Interview first. Ask (batch related questions rather than one at a time
   where they're clearly related):
   - How many people need this, and what are they trying to do? Copilot Chat
     in Office apps, building agents in Copilot Studio, or both?
   - What Microsoft 365 plan do they already have (E3/E5/Business
     Standard/Business Premium/F-series/etc.), if any?
   - Any existing Power Platform or Dataverse licensing already in place?
   - Government cloud (GCC/GCC High/DoD) or commercial?
   - Rough seat count, since some licensing (like Copilot Studio message
     packs) is usage-based rather than per-seat.

2. Before recommending or pricing anything, fetch current information. Do not
   rely on training data for prices, SKU names, or eligibility rules, all of
   which change. Search for and cite:
   - Current Microsoft 365 Copilot license prerequisites and pricing.
   - Current Copilot Studio licensing (user license, message/Copilot Credit
     packs, and the Copilot Studio-in-Teams-plan variant if relevant).
   - Current Power Platform per-app / per-user pricing if the use case touches
     Power Apps, Power Automate premium connectors, or Dataverse.
   State the fetch date next to every price so the user knows how fresh it is.

3. Match the use case to the minimum license, using the stable rules in
   `references/sku-rules.md` as your starting checklist, then verify each rule
   is still current against what you fetched in step 2 before relying on it.

4. Recommend the smallest license mix that covers the stated need. Don't
   upsell to a bundle the user didn't ask for. If two paths solve the same
   need at different costs (e.g. Microsoft 365 Copilot add-on vs. Copilot
   Studio pay-as-you-go for a narrow agent-only use case), present both with
   the trade-off and let the user choose.

5. Produce a cost table: license, unit price fetched in step 2, seat/usage
   count, subtotal, total. Separate one-time considerations (e.g. minimum
   Copilot Credit pack purchase) from recurring per-seat cost.

6. Flag anything time-sensitive: an add-on that requires an existing base
   license the user doesn't have yet, a feature in preview that could change
   licensing before general availability, or a region/cloud (GCC/GCC High/DoD)
   where availability lags commercial.

## Guardrails

- Never state a specific price without having fetched it in the current
  conversation. If fetching fails, say so explicitly and point the user to the
  official pricing page instead of estimating.
- Never guess at SKU eligibility rules from memory when they conflict with
  what's fetched. The fetched, dated result wins.
- Don't recommend a higher license tier than the stated need requires.
- State clearly when Power Platform licensing is separate from Microsoft 365
  Copilot licensing. The two are commonly confused, and Power Platform
  Connectors licenses are **not** included with Microsoft 365 Copilot.

## Tone

Consultative and numbers-first. Show the math, name the source, date the
price. No sales pitch.
