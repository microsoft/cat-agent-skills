# knowledge block - output template (knowledge-retrieve, rtl.customer-service-order-support.v1)

Attach exactly one `knowledge` object to the payload. Every fact carries a citation.

```json
{
  "knowledge": {
    "mode": "records_only | article",
    "status": "grounded | no_approved_answer | conflicting_sources",
    "intent": "<intent.category from assembled.json>",
    "resolution_path": "<context.resolution_path>",
    "sources_searched": ["<knowledge base / approved scripts / config / rules>"],
    "sources": [
      {"id": "<article id or SVC-DNR-2 or service-rules.md #n>", "clause": "<clause text or number>", "location": "<path or KB reference>"}
    ],
    "grounded_facts": [
      {"fact": "<one sentence the reply may state>", "citation": "<OMS / carrier / loyalty export file name, row n | article id #clause>"}
    ],
    "not_grounded": ["<anything the agent asked for that no approved source supports>"],
    "next_skill": "resolution-draft | handoff-packet",
    "citation": "service-rules.md #4.2"
  }
}
```

## Mode rules
- `records_only` - path is `answer_from_records`: grounded_facts come from the user's own OMS/carrier/loyalty export files only (status, last scan, ETA, tier for tone), each cited by file name and row. No article needed (#4.2).
- `article` - any other path or any statement beyond the records: sources must name a real article id or clause. None found -> `status = no_approved_answer`, `next_skill = handoff-packet`.

## Agent-facing summary (after the block)
| Fact | Citation |
|---|---|
| order ORD-0000-EXAMPLE shipped, ETA YYYY-MM-DD | <OMS export file name>, row n (context.order) |
| carrier in_transit, last scan YYYY-MM-DD <scan location> | <carrier export file name>, row n (context.carrier) |

- Next skill: resolution-draft
