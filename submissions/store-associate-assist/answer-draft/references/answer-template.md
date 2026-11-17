# Floor answer template (answer-draft, rtl.store-associate-assist.v1)
Fill every <slot> from the payload, the cited clause text or references/assist-rules.md; otherwise write `not in payload`. No other angle-bracket slots may remain. Never quote the associate's question text beyond the product name or SKU: no asides, hearsay or claims about what other staff or managers used to do.

## 1. Header
Store <store_context.store_id> / <store_context.department> - asked <question.asked_on> - status: <ANSWER | ESCALATION> - confidence <policy_resolution.confidence>

## 2. Determination
- <policy_resolution.determination> - "<policy_resolution.conditions[0]>" [policy clause <policy_resolution.applicable_clause>]
- Promo <promo_check.promo_id or pack id>: <eligible | NOT eligible | not checked> - <each promo_check.reasons[] line verbatim> [promo pack <id>]
- Promo check (REQUIRED whenever promo results are expected; copy the table verbatim from promo-check.md, never build it here):
| leg | result | reason |
|---|---|---|
| window | <pass or fail> | <reasons[] line naming the window, verbatim, or "inside <start>..<end> on <asked_on>" from promo-pack.json, or not in payload> |
| cluster | <pass or fail> | <reasons[] line naming the cluster, verbatim, or "<store_context.cluster> participates"> |
| SKU | <pass or fail> | <reasons[] line naming the SKU, verbatim, or "<question.sku> on the promo list"> |
Alternative: <"raincheck under PRC-3.3" only when policy_resolution.applicable_clause is PRC-3.3 | "none - applicable clause is not PRC-3.3">

[Section 3 is written ONLY when product_comparison.rows is non-empty. When rows is empty or product_comparison is absent, delete this whole section, the heading included, and write nothing about a comparison. Do not renumber: the next section stays "## 4.". Delete this bracketed line in every draft.]
## 3. Comparison
| attribute | <sku A> | <sku B> | differs |  ... rows verbatim ...  Missing from PIM: <product_comparison.missing_from_pim or none> [PIM extract <skus>]

## 4. What you can / cannot do
- CAN: <state the determination and the reasons above, cite the clause / promo line>
- CANNOT: <match or adjust a price, apply or extend a promo, authorise a refund, reserve inventory> - MANAGER ACTION [assist-rules.md #2.2]

## 5. Customer script (<= 3 sentences, plain words, no jargon, no promises beyond the payload)
"<script>"

## 6. Shift-lead escalation (when escalations[] is non-empty, confidence < 0.75, out of scope, or the customer is pressing for a manager action)
To: shift lead, <store id> - <one line per escalations[] entry, verbatim, or "customer pressing for a manager action" when that is the reason> - associate has NOT changed any price. [assist-rules.md #4.1 / #1.2]

DRAFT - checked: payload-only - engines: <provenance.engines>
