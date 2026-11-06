---
name: product-compare
description: 'Builds a side-by-side product comparison from the PIM extract with the deterministic product_compare engine - differences stated, missing shown as MISSING, never guessed. Use when the associate asks "what''s the difference between these two", "which should I recommend", "compare SKU A and SKU B", "side-by-side on these two models", "which one has the longer warranty". Do NOT use for a fresh floor question with no resolved payload - use question-intake instead; not for single-SKU promo or price questions - use promo-check or policy-retrieve; not to draft the final answer - use answer-draft; not for specs outside the PIM extract.'
license: Proprietary
metadata: {version: "1.0.9", author: Microsoft Retail & CPG Skills, category: analysis, icon: ArrowSwap}
---
# Product Compare
## Purpose
Attribute-level comparison from the PIM extract only (#3.1). One representation of "missing": absent or null both render as `MISSING`.
## When to use
- The question carries exactly two SKUs (`question.compare_skus`), after policy-retrieve has produced `resolved.json`.
## When NOT to use
- One SKU and a promo / price / return question - promo-check or policy-retrieve.
- Specs the PIM does not carry (brew time, wattage, dimensions) - they are reported as MISSING and escalated to the PIM steward, never looked up elsewhere.
- Writing the customer-facing answer - answer-draft.
## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by store ID, SKU/GTIN, product name, promo ID or file name when no location is given.
- Teams chat exports and email attachments (for example the associate's floor question) found the same way.
- The PIM (product information) export (CSV or Excel: GTIN, product name, list price, attribute, value) found by GTIN, product name or file name.
Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write working files (`resolved.json` copy with `compare_attributes`, `pim-extract.json`, `compared.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values (the values in the examples below are placeholders, not data).

## Inputs
- `resolved.json` from policy-retrieve in this session (or supplied by the user).
- The PIM export from the user's Microsoft 365 content (see *Where the data comes from*). Build `pim-extract.json` from it (step 2).
- Contract (ships in this skill folder): `contracts/rtl.store-associate-assist.v1.json` (`product_comparison`). Rules: `references/assist-rules.md`.
## Steps
1. Confirm `question.compare_skus` has exactly two GTINs; if not, ask which two (the engine reports the cause).
2. Add every attribute the user names to `compare_attributes` (REQUIRED, before the engine runs). List every product attribute, spec, feature or property named in the user's request, including any they ask you to "fill in", "look up" or "add" (for example "brew time", "wattage", "noise level", "weight"). Name each one: if the PIM export already has an attribute with that meaning, use the PIM name ("warranty" -> `warranty_months`, "how many cups" -> `capacity_cups`); otherwise use the user's words in lower snake_case ("brew time" -> `brew_time`, "wattage" -> `wattage`, "noise level" -> `noise_level`, "auto shut-off" -> `auto_shut_off`). Write a copy of `resolved.json` to the session working folder (never edit the user's file) with `question.compare_attributes` set to the existing list plus these names, without duplicates, and run the engine on that copy. Never leave out a named attribute because the PIM does not carry it: that is exactly the case the engine shows as MISSING. If the user names no attribute, keep `compare_attributes` as it is.
3. Build `pim-extract.json` in the session working folder from the PIM export, in exactly this shape (an object keyed by GTIN):
   `{"<GTIN>": {"name": "<product name>", "price": <list price as a number>, "attributes": {"<attribute>": <value>, ...}}}`
   Copy values verbatim: whole numbers as integers, decimals as numbers, true/false as booleans, other text as strings. An attribute row with a blank value is written as `null`; an attribute with no row for that GTIN is left out. Never fill a blank. Cite the export rows used.
4. Run the engine tool: `python scripts/product_compare.py --resolved resolved.json --pim pim-extract.json --out compared.json` (session paths; `resolved.json` is the step 2 copy).
5. Check the result before replying: every name from step 2 must appear as a row. If one is missing, add it to `compare_attributes` and run step 4 again. The row count is the PIM attributes of the two SKUs plus the named attributes the PIM does not carry.
6. Present `rows` verbatim as a table (attribute | SKU A | SKU B | differs). An attribute the PIM does not carry is shown as `MISSING` (never filled in, estimated or taken from memory, even when the user asks). List `missing_from_pim` under the table, then the note to the PIM steward, one line, for example: "brew_time, wattage are not in the PIM export for either SKU - shown as MISSING, not filled in; PIM steward asked to add them (#3.1)" (the engine also writes this to `escalations[]`).
7. Add a fit-to-need narrative that uses only attributes in the rows; never add a spec, price or claim that is not in the PIM export.
## Example
```
User: "Customer is torn between GTIN-EXAMPLE-1 and GTIN-EXAMPLE-2 - what's the difference, and what's the noise level?"
-> step 2: named attribute "noise level" -> compare_attributes ["noise_level"] (session copy of resolved.json) -> product_compare: 4 attributes, 3 differ, 1 missing from PIM
| attribute | Example Kettle A | Example Kettle B | differs |  ... | noise_level | MISSING | MISSING | no |
Reply: the table, "Missing from PIM: noise_level", "noise_level is not in the PIM export for either SKU - shown as MISSING, not filled in; PIM steward asked to add it (#3.1)", then a two-line fit-to-need note.
```
## Output format
`resolved.json` (session copy with `compare_attributes`), `pim-extract.json` and `compared.json` - the `{product_comparison}` hop, the full payload answer-draft reads - in the session working folder. In chat: a markdown table of the rows (one row per PIM attribute and per attribute the user named), a `Missing from PIM:` line, the PIM-steward note when anything is missing, the PIM export file and rows used, then <= 3 sentences of fit-to-need narrative grounded in the table.
## Grounding requirements
Every attribute cites the PIM extract (`product_comparison.citation`) and the user's PIM export file and rows; MISSING stays MISSING in the narrative.
## Guardrails
- No specs from memory or the internet; PIM only (#3.1). If asked to "fill in" a missing attribute, refuse, still add it to `compare_attributes` (step 2) so it shows as a MISSING row, and add the PIM-steward note.
- Never compare fewer attributes than the user named: a named attribute with no row is an error to fix (step 5), not an omission to explain.
- Never reserve inventory, hold units, change a price or promise availability (plugin boundary) - flag as an associate/manager action.
- Never recommend on an attribute the table does not contain.
## Escalation / uncertainty
SKU missing from PIM, or attributes missing from both SKUs: shown as MISSING + escalation to the PIM steward (the engine appends it to `escalations[]`). If the PIM export cannot be found or read, stop, say so and ask where it is.
