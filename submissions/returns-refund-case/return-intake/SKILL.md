---
name: return-intake
description: 'Structures a customer return request - item, order/receipt, reason as stated, condition, serials, customer history - into the rtl.returns-refund-case.v1 contract as case.json. Use when the user says "customer wants to return", "process this return", "start a return case", "log this return", "new return at the desk", or a return case begins. Do NOT use for eligibility or refund decisions - use eligibility-check instead; not for policy text - use policy-retrieve; not for the write-up or customer response - use case-packet.'
license: Proprietary
metadata: {version: "1.0.4", author: Microsoft Retail & CPG Skills, category: productivity, icon: Form}
---
# Return Intake
## Purpose
Assemble the case facts: request, order record, SKU attributes, customer return history. Entry hop of every return case.
## When to use
- Start of every return case ("customer wants to return", "start a return case", "log this return").
## When NOT to use
- Deciding eligibility, refund or red flags - eligibility-check owns the determination.
- Fetching policy clauses or windows - policy-retrieve.
- Classifying the reason code - reason-classify.
- Drafting the packet, customer response or manager exception request - case-packet.
## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Facts the user types in the chat, and files the user names, links or attaches (a service-desk note, a customer email, an order/receipt lookup export, a customer return-history export).
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by case ID, order ID, unit serial or file name when no location is given.
- Email attachments or the customer's email itself, found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row (CSV exports carry a `row` column) or by line/section for notes and emails. Write the working JSON file (`case.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

## Inputs
Configuration ships inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md` - paths below are relative to this skill folder. Case facts come from the user's Microsoft 365 content (see *Where the data comes from*):
- The request as stated: the service-desk note, customer email or chat message (verbatim reason text, item, category, value, receipt presented, condition flags, unit serial, request date).
- The order/receipt lookup export: order ID, order date, category, unit price, sold serial.
- The customer return-history export: receiptless returns in the last 90 days.
Schema: contracts/rtl.returns-refund-case.v1.json.
## Steps
1. Find and read the sources above; list which were found and which are missing.
2. Mint `case_id` as `RET-<YYYY>-<5-digit sequence>` (contract convention); never encode the order id or customer identity in it. If the note, email or user already gives a case ID, use that one.
3. Capture `reason_text` verbatim - classification and the human exception path depend on the actual words.
4. Build `case.json` in the session working folder in exactly this shape (values below are neutral placeholders, not data):
```json
{ "contract_version": "rtl.returns-refund-case.v1", "case_id": "RET-2000-00001",
  "return_request": {"category": "<config/return-windows.json windows_days key>", "value": 0.0, "has_receipt": true,
    "opened": null, "worn": null, "requested_on": "YYYY-MM-DD", "reason_text": "<verbatim>", "unit_serial": null,
    "item": "<as described>", "citation": "<note or email file name, line>"},
  "order": {"order_id": "ORD-0000-EXAMPLE", "order_date": "YYYY-MM-DD", "sold_serial": null, "citation": "<export file name, row n>"},
  "customer_history": {"receiptless_returns_90d": 0, "citation": "<export file name, row n>"},
  "escalations": [] }
```
   Record `category`, `value`, `has_receipt`, `opened`, `worn`, `requested_on`, `unit_serial` as presented (a flag the sources do not state -> `null` or left out, never guessed). Attach `order` only when the lookup export has the order (with `order_date` and `sold_serial`), and `customer_history` only when the history export has the customer; each with a `citation`.
5. Validate against the contract (required keys, `contract_version` const, `case_id` pattern); write `case.json` to the session working folder.
## Example
```
User: "Customer wants to return a $120 bluetooth headset, no receipt; the desk found order ORD-0000-EXAMPLE."
-> ReadFileContent: order/receipt lookup export (ORD-0000-EXAMPLE, order date, sold serial SN-EXAMPLE-1) - cite file + row
-> ReadFileContent: customer return-history export (receiptless_returns_90d) - cite file + row
-> write case.json (session folder): case_id RET-2000-00001, reason_text verbatim, has_receipt false, unit_serial SN-EXAMPLE-2
Reply: "Case RET-2000-00001 recorded. Order and history attached (sources cited); receipt not presented. No determination made."
```
## Output format
`case.json` - the entry hop: `{contract_version, case_id, return_request{...}, order?{...}, customer_history?{...}, escalations: []}`. No `reason`, `eligibility` or `fraud_signals` keys. Tell the user which records were found and which are missing.
## Grounding requirements
Every fact cites its record (order id, POS receipt, history extract). The story is recorded; it is not evidence.
## Guardrails
- Never fabricate a fact to complete the record; write `null` or leave the block absent and cite what was searched.
- No eligibility or fraud opinions here - record the serial mismatch or the return count as facts only.
- Never fabricate an order id, date or history value; if the lookup finds nothing, leave the block absent and record it in `escalations`.
- Never skip the history pull because the customer is friendly - it is part of every case.
- Draft-first: nothing here approves, refunds or declines anything.
## Escalation / uncertainty
If the order lookup export or the history export cannot be found or returns nothing: record the block as absent, add an `escalations` entry naming the missing record, ask the user for it (for example the order number and purchase date from the receipt), and never fabricate a stand-in value.
No order found and no receipt: record it; the Govern step (eligibility-check) decides what that means. Ambiguous category: ask the user before writing.
