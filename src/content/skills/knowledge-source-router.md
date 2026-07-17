---
name: Knowledge Source Router
description: "Route Copilot Studio knowledge searches to the right region-specific source (Americas, EMEA, APAC, or Global) based on where the user is, so answers stay locally accurate."
agentDescription: "Determines which region-specific knowledge source(s) to search based on the user's location. You MUST invoke this skill BEFORE calling the KnowledgeSearch tool, and pass the chosen source(s) as its `sources` parameter."
platforms: [Copilot Studio]
tags: [knowledge, routing, localization, location, grounding]
author: Adi Leibowitz
authorUrl: "https://microsoft.github.io/mcscatblog/"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-06-23
updatedAt: 2026-06-23
featured: true
---
Pick the correct region-specific knowledge source(s) for a query based on the
**user's location**, so answers are grounded in content that is accurate for
where the user is. Always do this BEFORE calling the `KnowledgeSearch` tool, and
pass the chosen source(s) as the `sources` parameter of that call — on every
knowledge-grounded question. Policies, benefits, pricing, legal/compliance,
support hours, and product availability frequently differ by country or region,
so read from the source that matches the user's location before answering.

## Available sources
| Source | Use when the user is located in... |
| --- | --- |
| `Global` | Any location, for content that is the same everywhere (fallback / default). |
| `Americas` | United States, Canada, Mexico, Central & South America. |
| `EMEA` | Europe, the Middle East, and Africa. |
| `APAC` | Asia, Australia, and the Pacific. |
