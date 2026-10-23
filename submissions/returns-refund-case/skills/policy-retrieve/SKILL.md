---
name: policy-retrieve
description: 'Retrieves the applicable return policy clauses and the configured windows/limits for a return case and attaches them verbatim as policy_context. Use after return-intake, or on "what does the return policy say for <category>", "what''s the return window for", "pull the policy clauses", "what does policy say about no receipt", "attach the policy to the case". Do NOT use to decide eligibility or red flags - use eligibility-check instead; not to start a case - use return-intake; not for the packet - use case-packet.'
license: Proprietary
metadata: {version: "1.0.3", author: Microsoft Retail & CPG Skills, category: research}
---
# Policy Retrieve
## Purpose
Bring the governing policy text and config values into the case with citations, so the Govern step can quote them.
## When to use
- After return-intake in every case.
- Ad hoc policy questions for a category ("what's the return window for electronics").
## When NOT to use
- Making the determination or surfacing fraud signals - eligibility-check.
- Structuring a new request - return-intake.
- Drafting the packet or customer wording - case-packet.
- Warranty or price-match questions: this plugin ships return rules only (references/returns-rules.md); say so and escalate to the policy owner.
## Inputs
Plugin assets ship inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md`, `demo-data/` - paths below are relative to this skill folder.
`case.json` + references/returns-rules.md + config/return-windows.json. Schema for the output block: `policy_context` in contracts/rtl.returns-refund-case.v1.json.
## Steps
1. Confirm the category exists in `config/return-windows.json.windows_days`; if not, escalate to the policy owner and record `needs_evidence` context.
2. Select clauses matching the case shape: window (#1.1), receipt/order lookup (#1.2), condition (#1.3), signal rules present in the facts (#3.1-3.4), determination discipline (#2.1, #2.2), human gate (#4.1, #4.2), exceptions (#5.1).
3. Write `policy_context` exactly per the contract: `clauses[{clause_id, text (verbatim), citation, applies_because}]`, `config_values[{key, value, unit, citation}]`, `not_found[]` for anything requested that the policy text does not contain, `source: skill:policy-retrieve/1.0.3`.
4. Validate the payload against the contract; write it back as the case payload.
## Example
```
User: "What does the return policy say for electronics with no receipt on a $249 item?"
-> read config/return-windows.json: windows_days.electronics = 15, receiptless_limit = 50.0
-> read references/returns-rules.md: #1.1 window clock, #1.2 receipt/order lookup, #3.3 high-value receiptless
-> policy_context.clauses = [RET-1.1, RET-1.2, RET-3.3 verbatim]; not_found = ["warranty"] if asked
Reply: table of clause id | verbatim text | applies because; then "Determination: not made here - eligibility-check."
```
## Output format
The case payload with a `policy_context` block added and nothing else changed. In chat: a short list of the clauses attached (id + one line) and the config values, then "Determination: not made here - eligibility-check".
## Grounding requirements
Clause text quoted verbatim with ids; config values cite config/return-windows.json. If a clause does not exist, it goes in `not_found` - it is never written.
## Guardrails
- Retrieval only; the determination belongs to eligibility-check. Never mark a case eligible/ineligible here.
- Never paraphrase, soften or "round" a window or limit; attach the configured value exactly.
- Never invent a clause or clause id for policy areas the shipped text does not cover.
## Escalation / uncertainty
If the policy file or config cannot be read, stop and report the missing source; never quote a clause from memory. If a category is missing from config, escalate to the policy owner.
Category missing from config, or a requested policy area absent from the text: escalate to the policy owner; the case becomes needs_evidence.
