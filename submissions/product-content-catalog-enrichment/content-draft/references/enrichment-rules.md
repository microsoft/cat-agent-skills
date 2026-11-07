# Enrichment Rules (cited as enrichment-rules.md #<n>; engine constants mirror sections)
## 1. Identity
1.1 Every GTIN is validated with the GS1 check-digit algorithm. An invalid GTIN blocks the record - identity errors poison every downstream channel. Downstream engines carry `record_blocked: true` on that record; nothing from it is drafted.
## 2. Normalisation
2.1 Attributes map through the taxonomy mapping table only; unmapped supplier fields are listed, never silently dropped or guessed into a slot.
2.2 UOM conversions are deterministic (oz/lb/kg -> g, fl oz/l -> ml) with the conversion shown per attribute (`conversions[]`: from, to, factor). A non-numeric value is refused and listed for the steward.
## 3. Completeness
3.1 Channel requirements per category live in config/; completeness % counts required fields only. Missing fields are named per SKU.
3.2 The customer completeness floor per channel lives in config/ (`completeness_floor_pct`). A batch average below the floor escalates to the steward before drafting.
## 4. Claims (Govern)
4.1 A marketing claim ships only if it matches the approved claim library FOR THAT GTIN (or its brand scope) and market. A library claim found in copy for a different GTIN or market is `unapproved`. Supplier romance copy is not approval.
4.2 Regulated terms (config list: e.g., organic, biodegradable, antibacterial, clinically proven, compostable) are BLOCKED unless the library carries the substantiation reference for that GTIN and market. A multi-word library claim that contains the regulated term (e.g. "antibacterial coating") substantiates it.
4.3 A blocked claim never appears in draft copy - not even "softened" ("fights germs" for a blocked "antibacterial" is still the claim).
4.4 Supplier romance terms (config `romance_terms`, e.g. eco-friendly, premium, sustainable) are `unapproved` unless the library approves them; they are dropped from copy and listed in the packet - they do not block the record.
## 5. Confidence floor
Unreadable source rows or ambiguous mapping -> confidence < 0.75, steward review.
