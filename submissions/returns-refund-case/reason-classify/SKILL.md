---
name: reason-classify
description: 'Classifies the stated return reason against the reason-code taxonomy with the deterministic reason_classify engine, recording confidence and candidate codes. Use after return-intake in every case, or on "what reason code is this", "classify the return reason", "which reason code", "code this return", "why are they returning it". Do NOT use for sentiment or complaint triage; not for eligibility or red flags - use eligibility-check instead; not for policy text - use policy-retrieve.'
license: Proprietary
metadata: {version: "1.0.4", author: Microsoft Retail & CPG Skills, category: analysis, icon: TextBulletListLtr}
---
# Reason Classify
## Purpose
Deterministic taxonomy classification of the verbatim reason text - the {reason} hop.
## When to use
- After return-intake in every case; or when asked which reason code a stated reason maps to.
## When NOT to use
- Sentiment, complaint or ticket categorisation outside a return case.
- Eligibility, refund or fraud questions - eligibility-check.
- Retrieving policy - policy-retrieve. Drafting - case-packet.
## Where the data comes from
This plugin ships no sample data. The reason-code taxonomy (config/reason-taxonomy.json) is retailer configuration inside this skill folder. The case is the user's own content:
- `case.json` written earlier in the session by return-intake, or a case file the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by case ID or file name when no location is given.
- If the user only gives the customer's words (a note, email or chat line), build `case.json` with return-intake first so `reason_text` is verbatim.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or line. Write the working JSON file (`classified.json`) to the session working folder, never into the plugin. If the case or its reason text cannot be found, say which is missing and ask the user. Never invent it or fall back to example values.

## Inputs
Configuration ships inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md` - paths below are relative to this skill folder.
`case.json` (from return-intake in this session, or the user's case file - see *Where the data comes from*; it must carry `contract_version` and `return_request.reason_text`) + config/reason-taxonomy.json. Engine: scripts/reason_classify.py.
## Steps
1. Run `python scripts/reason_classify.py --case case.json --taxonomy config/reason-taxonomy.json --out classified.json` (case.json and classified.json live in the session working folder).
2. Quote `reason.category` and `reason.confidence` verbatim, with the `candidates` list when more than one category matched.
3. If confidence < 0.75 the engine appends an escalation: confirm the primary reason with the customer before the packet closes - never guess.
## Example
```
$ python scripts/reason_classify.py --case case.json --taxonomy config/reason-taxonomy.json --out classified.json
reason_classify: not_as_described (conf 0.7) -> classified.json
Reply: "Reason code: not_as_described (confidence 0.7). Matched: 'looks different'. Alternative: defective ('broken').
        Ambiguous - confirm the primary reason with the customer before the packet closes."
```
## Output format
`classified.json` - the case payload plus `reason: {category, confidence, candidates[], tie_break, source, citation}`. In chat: "Reason code: <category> (confidence <n>) - <matched keywords>; alternatives: <...>".
## Grounding requirements
Category cites the taxonomy file; matched keywords are listed so the pick is auditable.
## Guardrails
- Never fabricate a reason code or a confidence; both come only from the engine output.
- Taxonomy-only; never invent a new reason code (e.g. "suspected_fraud") - fraud is not a reason code.
- Never overwrite the engine's category or confidence to make a case "flow through".
- Never skip the customer confirmation on an ambiguous classification because the queue is long.
## Escalation / uncertainty
If the engine fails (contract mismatch, unreadable taxonomy) stop and report the error; never hand-pick a category. If `reason_text` is missing, send the case back to return-intake.
Confidence < 0.75 -> confirm with the customer before the packet closes; `unclassified` -> ask the customer to restate and, if still unmatched, escalate to the taxonomy owner.
