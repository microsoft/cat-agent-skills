---
name: knowledge-source-router
description: >-
  Determines which region-specific knowledge source(s) to search based on the
  user's location. You MUST invoke this skill BEFORE calling the KnowledgeSearch
  tool, and pass the chosen source(s) as its `sources` parameter.
---

Pick the correct region-specific knowledge source(s) for a query based on the
**user's location**, so answers are grounded in content that is accurate for
where the user is. Always do this BEFORE calling the `KnowledgeSearch` tool, and
pass the chosen source(s) as the `sources` parameter of that call.

## When to use this skill
Apply this routing on every knowledge-grounded question. Policies, benefits, pricing,
legal/compliance, support hours, and product availability frequently differ by
country or region, so the agent must read from the source that matches the user's
location before answering.

## Available sources
| Source | Use when the user is located in... |
| --- | --- |
| `Global` | Any location, for content that is the same everywhere (fallback / default). |
| `Americas` | United States, Canada, Mexico, Central & South America. |
| `EMEA` | Europe, the Middle East, and Africa. |
| `APAC` | Asia, Australia, and the Pacific. |
