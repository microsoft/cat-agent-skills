# Enrichment Rules (cited as enrichment-rules.md #<n>; engine constants mirror sections)
## 1. Identity
1.1 Every GTIN is validated with the GS1 check-digit algorithm. An invalid GTIN blocks the record - identity errors poison every downstream channel.
## 2. Normalisation
2.1 Attributes map through the taxonomy mapping table only; unmapped supplier fields are listed, never silently dropped or guessed into a slot.
2.2 UOM conversions are deterministic (g<->oz, ml<->fl oz) with the conversion shown.
## 3. Completeness
3.1 Channel requirements per category live in config/; completeness % counts required fields only. Missing fields are named per SKU.
## 4. Claims (Govern)
4.1 A marketing claim ships only if it matches the approved claim library FOR THAT GTIN (or its brand scope). Supplier romance copy is not approval.
4.2 Regulated terms (config list: e.g., organic, biodegradable, antibacterial, clinically proven, compostable) are BLOCKED unless the library carries the substantiation reference for that market.
4.3 A blocked claim never appears in draft copy - not even "softened".
## 5. Confidence floor
Unreadable source rows or ambiguous mapping -> confidence < 0.75, steward review.
