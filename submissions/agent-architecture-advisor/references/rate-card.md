# Rate Card

**rate-card-date: 2026-07**

---

## Read this before using any number below

These rates are a **modelling scaffold, not a price quote.** Microsoft pricing for
Copilot Studio Credits and Azure AI Foundry changes regularly, varies by agreement type,
region, and commitment level, and is frequently discounted in enterprise contracts.

Three rules, all non-negotiable:

1. **Every cost figure in a report carries the rate-card date and a verification note.**
2. **Every cost figure carries a sensitivity band** (default ±40%).
3. **Never present a cost projection as a decision-grade number.** It is a comparison
   tool — its value is in the *ratio* between options and the break-even point, not the
   absolute figure.

A confidently wrong cost number destroys trust in the entire report, including the parts
that were rigorously derived. The break-even *shape* survives rate changes; the absolute
number does not.

**Machine-readable companion:** `scripts/cost_model.py` loads its numbers from
`references/rate-card.json` (weights, token defaults, per-region Foundry rates). Update
that file to change the model's inputs; this document explains what the numbers mean.

**Verification sources:**
- Copilot Studio: Microsoft Power Platform pricing page and licensing guide
- Azure AI Foundry: Azure pricing calculator (model, Azure AI Search, storage)

---

## Regional cost and availability

**region-currency: 2026-08 — refresh with the rate card.**

Cost is not uniform across regions, and this materially affects the comparison:

- **Model inference and Azure AI Search prices vary by Azure region.** Model the region
  the agent will actually run in, not a default. A cheaper region can move the break-even
  point substantially.
- **Capability availability is regional.** A model tier, feature, or Foundry capability
  may not be deployed in a mandated data-residency region — the direct link to GOV-02 and
  CEIL-08. Never assume a capability priced in one region is available in another.
- **Copilot Studio Credit pricing** is comparatively uniform but still varies by agreement
  type and commitment; enterprise discounts are common.

When region is unknown, state the region assumed for every figure and flag that a
different deployment region changes both cost and availability. Where a required
capability has no in-region deployment, escalate to CEIL-08 rather than quoting an
out-of-region price.

---

## Copilot Studio — consumption model

Copilot Studio consumes **Credits** (also referred to as messages, depending on
licensing vintage). The critical modelling fact:

> **Different interaction types consume at different rates.** Generative answers and
> agent actions consume substantially more than classic deterministic responses.

This ratio — not the absolute rate — is what makes cost modelling useful, because it is
what the architecture actually controls. A well-designed agent moves deterministic
interactions out of generative handling, and the saving is proportional.

### Consumption weights

Relative multipliers used by `cost_model.py`. These express the *shape* of the model and
should be replaced with current rates when available.

| Interaction type | Relative weight | Notes |
|---|---|---|
| Classic topic response | 1.0 | Baseline — deterministic path, no generation |
| Generative answer (grounded) | 8–12 | Varies with retrieval scope and answer length |
| Generative orchestration turn | 10–15 | Includes tool-selection reasoning |
| Agent action / tool invocation | 5–8 | Per invocation |
| Escalation / handoff | 1.0 | Handoff itself is cheap; the turns preceding it are not |

**Modelling implication:** a conversation that misroutes and requires three additional
generative turns before escalating costs roughly 30–45× a clean classic response. This
is why CFG-01 (trigger collisions) is simultaneously the top quality finding and the top
cost finding, and why the two should be reported together rather than separately.

### Default assumptions

Override with user-supplied data whenever available; state which defaults were used.

| Parameter | Default | Notes |
|---|---|---|
| Turns per conversation | 4 | Typical support/FAQ pattern |
| Generative share of turns | derived from topic analysis | Do not guess if the artifact is available |
| Escalation rate (baseline) | 8% | Well-configured agent |
| Escalation rate (with collision findings) | 12–18% | Derived from collision severity |

---

## Azure AI Foundry — consumption model

Foundry cost has three components. Model inference usually dominates, but Azure AI Search
is frequently underestimated because it is a standing cost rather than a per-use one.

### 1. Model inference

Priced per input and output token, varying by model tier. Per-turn token estimate:

```
tokens_per_turn = system_prompt
                + retrieved_context      # usually the largest term
                + conversation_history
                + completion
```

Modelling defaults:

| Component | Default | Notes |
|---|---|---|
| System prompt | 500 tokens | Constant per turn |
| Retrieved context | 2,000 tokens | 3–5 chunks; scale with retrieval config |
| Conversation history | 1,500 tokens | At turn 4 of an average conversation |
| Completion | 400 tokens | Typical grounded answer |
| **Total per turn** | **~4,400 tokens** | Roughly 4:1 input:output |

**Retrieved context is the main cost lever.** Halving chunk count roughly halves per-turn
cost. This is the Foundry equivalent of COST-04 (over-grounding) and is worth flagging
in any Foundry target design.

Model tier selection is the second lever — a smaller model on a well-grounded task
frequently matches a larger one at a fraction of the cost. Recommend evaluating this
rather than defaulting to the largest available model.

### 2. Azure AI Search

Standing cost driven by tier, replica, and partition count — not by conversation volume.

**This is the term teams forget.** At low volume it can exceed model cost entirely, and
it does not scale down when usage is light. Always include it, and always call it out
separately in the cost section.

### 3. Supporting services

Storage, App Service or Container Apps hosting, Application Insights, and networking.
Individually small, collectively non-trivial. Model as a percentage uplift (default 15%)
rather than itemising, and say that is what you did.

---

## Break-even calculation

The single most useful output of the cost model.

```
break_even_conversations = 
    foundry_fixed_monthly / (credit_cost_per_conversation - foundry_variable_per_conversation)
```

Where `foundry_fixed_monthly` is dominated by Azure AI Search plus hosting.

**Interpretation:**

- Below break-even, Copilot Studio is cheaper — fixed costs dominate.
- Above break-even, Foundry is cheaper — marginal cost per conversation is lower.
- Within ±50% of break-even, **cost is not a decision factor.** Say so explicitly and
  decide on capability grounds instead.

That last case is common and worth stating plainly. Teams reach for cost as a tiebreaker
when the honest answer is that cost does not distinguish the options at their volume.

**Reporting rule:** a break-even crossing alone never justifies migration. Per COST-03,
present it as information unless a CEILING finding independently supports the
recommendation. Migration has operational costs the arithmetic above does not capture —
engineering time, parallel-run risk, retraining, and loss of maker accessibility.

---

## Worked example structure

Report cost like this, not as a single number:

```
Current (Copilot Studio)     ~X Credits/month    [±40%, rate card 2026-07]
  Top drivers:
    1. Generative answers on N topics    ~45% of consumption
    2. Retry burn from CFG-01 collisions ~20% of consumption
    3. Over-grounding on M topics        ~12% of consumption

Alternative (Foundry)         ~$Y/month          [±40%, rate card 2026-07]
  Fixed:    Azure AI Search + hosting     $A   (does not scale with volume)
  Variable: model inference               $B   (~4,400 tokens/turn)

Break-even: ~Z conversations/month
Current volume: V
Assessment: [V is N× break-even | V is below break-even | V is within the
             indifference band — cost should not drive this decision]

Verify current pricing before acting on these figures.
```

Note that the top-drivers breakdown is more actionable than the total. Two of the three
drivers in that example are fixable without changing platform — which is usually the
real finding.
