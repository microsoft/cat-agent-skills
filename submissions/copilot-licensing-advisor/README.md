# Copilot Licensing Advisor

Answer a few questions about who needs what, and get back a license
recommendation and a costed table: Microsoft 365 Copilot, Copilot Studio, and
Power Platform, sized to the actual need instead of the biggest bundle.

## Why prices aren't in this skill

Licensing prices, SKU names, and message/Copilot Credit mechanics change
often enough that hardcoding them here would go stale fast. Instead, the skill
fetches current pricing and eligibility from official Microsoft sources at
the time you use it, and states the fetch date next to every number. What *is*
bundled in (`references/sku-rules.md`) is only the slow-moving structural
rules, like which base plan a Copilot add-on requires or which Copilot Studio
path fits which scenario: the kind of thing that doesn't change month to month.

## What it won't do

Quote a price it didn't just fetch, or recommend a bigger license than the
stated need requires. If a fetch fails, it says so and points you to the
official pricing page rather than estimating.

## Reference

[Microsoft 365 Copilot licensing](https://learn.microsoft.com/microsoft-365/copilot/microsoft-365-copilot-licensing)
· [Copilot Studio licensing](https://learn.microsoft.com/microsoft-copilot-studio/billing-licensing)
· [Power Platform pricing and billing](https://learn.microsoft.com/power-platform/admin/pricing-billing-skus)

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
