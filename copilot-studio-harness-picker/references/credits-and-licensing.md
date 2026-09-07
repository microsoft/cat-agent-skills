# Copilot Credits and licensing

This reference is a planning snapshot checked on 2026-08-04. Licensing, pricing, feature inclusion, and consumption rates change. Verify the current Microsoft documentation, the customer's agreement, currency, geography, and tenant entitlements before a financial commitment.

## Contents

- Evidence rules
- GitHub Copilot harness planning ranges
- Standard and Copilot chat activity rates
- Inclusion and meter checkpoints
- List-price snapshot, including P3
- Estimation workflow and estimator usage
- Required estimate presentation

## Evidence rules

Never blend these categories:

- **Documented fact:** a Microsoft-published rate, range, inclusion, or licensing rule with a source and checked date.
- **Workload assumption:** a user-supplied or scenario value such as tasks per month, complexity mix, retries, pages, or growth.
- **Calculation:** arithmetic combining documented facts and assumptions.
- **Estimate:** the resulting planning range, not a quote or guarantee.
- **Exclusion:** a cost or activity not represented in the calculation.

Do not infer “free” from a Microsoft 365 license without verifying the user, channel, capability, and fair-use conditions.

A user question is not a universal billing unit. One interaction can produce classic or generative answers, activity-map agent actions, grounding, AI-tool tokens, and flow actions. Counts from different reports can also overlap. Define each input before summing it.

## GitHub Copilot harness planning ranges

The August 2026 Copilot Credits Guide provides planning ranges rather than a fixed per-task rate.

### AI-assisted creation

| Complexity | Indicative interaction | Documented planning range |
|---|---|---:|
| Light | 1–2 turns | 1–20 credits |
| Medium | 3–5 turns | 21–60 credits |
| Heavy | 6 or more turns | 61+ credits |

### Preview, evaluation, and runtime tasks

| Complexity | Indicative work | Documented planning range |
|---|---|---:|
| Light | Few sources, light reasoning, no more than one artifact | 100–300 credits |
| Medium | Many sources, structured reasoning, two or more artifacts | 300–500 credits |
| Heavy | Broad aggregation, deep reasoning, many artifacts | >500 credits |

Actual usage depends on models, tokens and context, tool calls, knowledge retrieval, runtime duration, artifacts, retries, and the path taken. Heavy ranges have no documented maximum. Never turn `61+` or `>500` into a closed range unless the user supplies a planning upper bound; label that bound as an assumption. Preserve the strict lower bound: `>500` is not the same as `500 or more`.

Challenge the supplied classification when the task description conflicts with the guide. A task using many sources, structured reasoning, and two or more artifacts is not a credible light case without observed evidence.

AI-assisted authoring, Preview, Evaluation, and production runtime can all consume credits. Manual editing and navigation in Build or Monitor do not by themselves consume credits. Include nonproduction activity in the plan.

GitHub Copilot harness runtime consumption is not zero-rated merely because the end user has a Microsoft 365 Copilot license. Verify any separate entitlement or offer rather than assuming one.

Treat these as overall planning ranges influenced by model, context, knowledge, MCP and other tools, runtime, and artifacts. Do not stack standard-harness feature rates on top unless current Microsoft guidance explicitly requires it.

## Standard and Copilot chat activity rates

The dated snapshot in `assets/credit-rates-2026-08.json` records these published activity rates:

| Activity | Credits |
|---|---:|
| Classic answer | 1 per answer |
| Generative answer | 2 per answer |
| Agent action | 5 per action |
| Tenant graph grounding | 10 per grounding |
| Copilot Studio agent flow actions | 13 per 100 actions |
| AI tools — basic | 0.1 per 1,000 tokens, characters, one image, or one page, as defined for the feature |
| AI tools — standard | 1.5 per defined unit |
| AI tools — premium | 10 per defined unit |
| Content processing | 8 per image or page |
| Voice with classic orchestration | 10 per minute |
| Voice with generative AI | 35 per minute |
| Voice with premium generative AI | 75 per minute |

Do not add every rate to every interaction. Identify the activities the design actually invokes. Confirm whether a feature meters by token, character, image, page, action, answer, or minute.

Agent actions are activity-map steps such as triggers, deep reasoning, and topic transitions. Copilot Studio agent-flow actions are actions inside agent flows. They can appear in the same interaction, but do not assume supplied counts are independent without telemetry.

Eligible authenticated business-to-employee use by Microsoft 365 Copilot licensed users in qualifying Microsoft surfaces can be included under Microsoft terms and fair-use limits. External, anonymous, custom-channel, nonqualifying, or separately metered capabilities may consume Copilot Credits. An agent flow can have different treatment depending on whether the agent called it or another trigger initiated it. Computer use and third-party or Azure services require separate validation.

Power Automate cloud flows use Power Automate licensing rather than the Copilot Studio agent-flow meter. Do not apply the 13-per-100 rate to a Power Automate cloud flow. First identify the flow type and trigger.

Copilot chat is an internal Microsoft 365 surface, but the exact included-versus-consumption treatment depends on user licensing and capability. Confirm it rather than copying a standard-harness assumption.

## Inclusion and meter checkpoints

| Workload context | Planning treatment to verify |
|---|---|
| Standard-harness business-to-employee activity, authenticated as a Microsoft 365 Copilot licensed user | Core listed activities can be no charge under the Microsoft 365 Copilot USL, subject to identity, capability, surface, terms, and fair-use limits. |
| Copilot Studio agent flow invoked by the “When an agent calls the flow” trigger for that eligible licensed user | Can be no charge; another trigger consumes credits at the standard rate. |
| Power Automate cloud flow | Uses Power Automate licensing, not the Copilot Studio agent-flow credit meter. |
| External, anonymous, custom-channel, unlicensed, or nonqualifying standard-harness use | Plan Copilot Credit consumption at the applicable feature rates. |
| GitHub Copilot harness authoring, preview, evaluation, or runtime | Plan Copilot Credits using the GitHub Copilot harness ranges; do not assume a Microsoft 365 Copilot user license zero-rates it. |
| Copilot chat harness | Verify the exact custom-versus-Microsoft 365 agent type, consuming user license, invoked capabilities, and qualifying surface. |

Treat this table as a validation checklist, not a substitute for the current Product Terms or the customer's agreement.

## List-price snapshot

The August 2026 guide describes Copilot Credits as tenant-pooled capacity. The accompanying snapshot records:

- pay-as-you-go list price: USD $0.01 per credit;
- capacity pack: 25,000 credits per month for USD $200 list price, with annual billing and unused monthly capacity not rolling over.

The August 2026 Microsoft Copilot Studio Licensing Guide also lists a one-year, pay-upfront Copilot Credit Pre-Purchase Plan (P3). It uses an annual pool; unused credits expire at the end of the term, and usage beyond the pool can move to another P3 purchase or pay-as-you-go.

| P3 tier | Annual Copilot Credits | Published discount |
|---:|---:|---:|
| 1 | 300,000 | 5% |
| 2 | 1,500,000 | 6% |
| 3 | 3,000,000 | 7% |
| 4 | 15,000,000 | 8% |
| 5 | 30,000,000 | 10% |
| 6 | 75,000,000 | 12% |
| 7 | 150,000,000 | 14% |
| 8 | 225,000,000 | 17% |
| 9 | 300,000,000 | 20% |

P3 discounts do not simply stack with other discounts, and current Microsoft guidance describes purchase restrictions and default renewal behavior that must be checked before commitment. Do not recommend a P3 tier until a representative pilot establishes a stable annualized demand distribution. A tier can cost more than pay-as-you-go when the pool is oversized or expires unused.

Agreement pricing, annual pools, promotions, taxes, currency, geography, minimum commitments, and product terms can change the comparison. Report them separately from workload arithmetic.

## Estimation workflow

1. Define a month or another explicit period.
2. Split user populations and channels where licensing treatment differs.
3. Define the metered unit for every volume and reconcile possible overlap. Distinguish a Copilot Studio agent flow from a Power Automate cloud flow.
4. Estimate activity volumes from process evidence. Include retries, evaluation, growth, seasonality, and high-complexity cases.
5. Classify GitHub Copilot harness tasks as light, medium, or heavy from representative runs, not stakeholder optimism. Challenge inconsistent bands.
6. Use `scripts/estimate_credits.py` for gross credit arithmetic.
7. Apply verified licensing inclusions or tenant entitlements outside the script and show the adjustment.
8. Compare pay-as-you-go, monthly capacity packs, and annual P3 only on compatible periods and at applicable list or agreement prices. Mention expiry, nonrollover, upfront commitment, overage treatment, and discount interaction. Do not recommend commitment from a wide unvalidated range.
9. State exclusions and sensitivity. Do not present false precision.
10. Run a metered pilot, inspect the Copilot Studio Monitor or admin consumption data, and replace assumptions with observed distributions.

## Estimator usage

Run:

```bash
python scripts/estimate_credits.py --input workload.json --format markdown
```

Use `--input -` to read JSON from standard input and `--format json` for structured output.

Add `"p3_annualization_factor": 12` only when the input represents a repeatable monthly workload that can credibly be annualized; use `1` for an annual input. Omit it when demand is not stable. The estimator then shows a P3 sizing scenario but does not recommend a purchase.

### Standard or Copilot chat example

```json
{
  "harness": "standard",
  "period": "month",
  "p3_annualization_factor": 12,
  "activities": {
    "classic_answers": 10000,
    "generative_answers": 4000,
    "agent_actions": 1200,
    "agent_flow_actions": 5000,
    "content_processing_pages": 200
  }
}
```

Use `"harness": "copilot-chat"` for the same activity arithmetic. The script reports gross credits and does not decide which activity is included by a license.

`agent_flow_actions` means actions inside a Copilot Studio agent flow. Do not enter Power Automate cloud-flow actions in that field.

### GitHub Copilot harness example

```json
{
  "harness": "github-copilot",
  "period": "month",
  "authoring_sessions": {
    "light": 6,
    "medium": 3,
    "heavy": 1
  },
  "preview_evaluation_tasks": {
    "light": 40,
    "medium": 15,
    "heavy": 2
  },
  "runtime_tasks": {
    "light": 800,
    "medium": 150,
    "heavy": 25
  },
  "heavy_upper_bounds": {
    "authoring_credits_per_session": 120,
    "task_credits_per_task": 1200
  }
}
```

The heavy upper bounds in this example are assumptions, not Microsoft caps. Omit them when unsupported; the script will report an open-ended upper range.

For heavy runtime tasks, the script preserves Microsoft's strict `>500` lower bound. For example, ten heavy tasks are reported as more than 5,000 credits rather than as at least 5,000 credits.

## Required estimate presentation

Use this order:

1. **Documented facts and checked date**
2. **Workload and entitlement assumptions**
3. **Gross credit calculation**
4. **Verified inclusions or entitlements**
5. **Estimated billable range and compatible-period counterfactual list-price scenarios**
6. **Exclusions and sensitivity**
7. **Pilot telemetry and budget controls**

If a decision-critical volume is unknown, provide a formula or break-even input request instead of fabricating a total.
