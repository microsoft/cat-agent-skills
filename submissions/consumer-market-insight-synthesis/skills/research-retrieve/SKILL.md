---
name: research-retrieve
description: Retrieves and ranks prior research, panel extracts and campaign results relevant to the question. Use when the user says "what do we already know about <topic>", "find prior research on", "have we studied this before", or an insight request begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Insights & Category}
---
# Research Retrieve
## Purpose
Rank the repository against the question (market + topics + recency, #1.1) so decades of research get reused, not re-commissioned.
## When to use
Start of every insight run.
## Inputs
Question (market, topics, use_case DECLARED UP FRONT - internal vs external gates everything downstream, #4.2); research index. Emits the entry hop (schema in contracts/).
## Steps
1. Structure question.json: market, topics, recency floor, use_case, as_of_date.
2. Retrieval + ranking happen in trend_compare's first pass; this skill assembles the question and index.
## Output
question.json - the entry hop.
## Grounding requirements
Every study carries its repository identity; nothing cited that was not retrieved (#1.1).
## Constraints
- Scope #5.1: retrieval and citation - no analysis over large tabular files (known boundary), no forecasting.
## Escalation / uncertainty
Undeclared use_case: ask - the rights gate cannot run without it (#4.2).
