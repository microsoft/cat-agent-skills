---
name: attribute-normalize
description: Maps supplier product fields to the retailer taxonomy through the mapping table only, converts units with the calculation shown, and validates every GTIN check digit (GS1). Use after source-ingest, or when the user says "map these to our taxonomy", "are these GTINs valid", "validate these GTINs", "check the GS1 check digit", "normalise the supplier attributes" or "which supplier columns are unmapped". Do NOT use for ad-hoc unit conversions or non-product data - answer in chat instead; do NOT use for completeness or missing fields - use completeness-score instead; do NOT use for claim wording - use claim-check instead.
license: Proprietary
metadata: {version: "1.0.5", author: Microsoft Retail & CPG Skills, category: analysis, icon: ArrowSwap}
---
# Attribute Normalize

## Purpose
Deterministic hop: taxonomy mapping (#2.1), UOM conversions shown (#2.2) and GS1 check-digit validation (#1.1) via `scripts/attribute_normalize.py`. The engine decides; the model quotes.

## When to use
- After source-ingest in every batch (`batch.json` exists).
- The user asks whether GTINs are valid or how supplier columns map to the taxonomy.

## When NOT to Use
- Kitchen/recipe or generic unit conversions with no product record -> plain chat.
- "How complete is this SKU" / "what's missing" -> use completeness-score instead.
- "Can we say antibacterial" / claim safety -> use claim-check instead.
- Raw supplier sheet not yet structured -> use source-ingest instead.
- Adding or changing taxonomy attributes -> PIM steward decision, never this skill.

## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat (for example a `batch.json` from source-ingest, or the supplier item sheet itself).
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by enrichment batch ID (for example `ENR-0000-EXAMPLE`), supplier name, GTIN or file name when no location is given.
- Email attachments (for example the supplier's item sheet) found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write the working JSON files (`batch.json` when you have to build it, `normalized.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

The taxonomy mapping `config/taxonomy-map.json` is retailer configuration that ships with the plugin; it is not user data and is never edited here.

## Inputs
`batch.json` (entry hop) from source-ingest earlier in the session or supplied by the user, + `config/taxonomy-map.json`. If only the supplier item sheet is available, build `batch.json` from it first exactly as source-ingest does (one record per row: `row`, `gtin` verbatim as text, `supplier_fields` keyed by the supplier's own headers, whole numbers as numbers, other values as the exact text, blanks left out), in this shape:
```json
{"contract_version": "rtl.product-content-enrichment.v1", "batch_id": "ENR-0000-EXAMPLE", "supplier": "Example Supplier Co",
 "channel": "own-site", "skus": [{"gtin": "GTIN-EXAMPLE-1", "row": 2, "supplier_fields": {"Product Name": "Example Item", "Weight (lb)": "1.5"}}],
 "escalations": []}
```
For an ad-hoc GTIN list typed in the chat, build a minimal batch (gtin + row "?" ) and say the citations are provisional.

## Steps
1. Run the engine (tool: shell) with `batch.json` from the session working folder:
   ```bash
   python scripts/attribute_normalize.py --batch batch.json --taxonomy config/taxonomy-map.json --out normalized.json
   ```
2. Quote `normalized[]` verbatim per SKU: `gtin_valid`, mapped attributes with their mapping entry, `conversions[]` (from -> to, factor), `unmapped[]`.
3. An invalid GTIN blocks the record (#1.1). Report the expected vs supplied check digit; never "fix" it by guessing, even when a neighbouring digit would pass.
4. Unmapped supplier fields are listed for the PIM steward (#2.1) - never forced into the nearest slot, never added to the taxonomy by the model.
5. Hand `normalized.json` to completeness-score.

## Output format
A table per batch: `GTIN | GS1 valid | mapped attributes | conversions | unmapped`, then a bulleted escalations list, then "Next hop: completeness-score". Sections: Identity, Mapping, Conversions, Escalations.

## Grounding requirements
Every attribute cites the item sheet file name and row + mapping entry; every conversion shows the factor.

## Guardrails
- Never correct, pad or reconstruct a GTIN; an invalid check digit is a block and a steward escalation, whatever the launch deadline.
- Never invent a mapping or edit `config/taxonomy-map.json`; unmapped fields are listed, not guessed.
- Never convert a non-numeric value; the engine refuses and lists the field.
- Do not evaluate claims or completeness here; do not publish.
- If `batch.json` is missing or fails the contract assertion, stop and ask for the source-ingest output - do not fabricate a batch.
- Confirm the escalation list with the steward before the batch moves on.

## Escalation / uncertainty
Invalid GTINs and unmapped fields -> PIM steward with the engine's escalation lines quoted verbatim.
