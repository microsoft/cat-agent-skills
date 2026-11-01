# Perfect-Store Rules (cited as execution-standards.md #<n>; engine constants mirror sections)
## 1. Scoring
1.1 Each criterion of the channel/cluster standard scores pass/fail from the audit answers - deterministic, no partial credit unless the standard defines it.
1.2 compliance_pct = passes / applicable criteria. It is a coverage number, not a value number.
## 2. Ranking (the point of this plugin)
2.1 gap_value = weekly scan units x price x facing-weight for the affected SKUs. Gaps rank by value at stake, never by count - two fails on hero SKUs outrank five on tail.
2.2 A gap on an SKU with an ACTIVE promotion carries a 2x promo multiplier - an empty promo display during the promo week is the most expensive kind of empty.
## 3. Evidence
3.1 Photos attach as evidence references; they are never scored by computer vision in this version (Wave 3 upgrade).
## 4. Order discipline
4.1 The suggested order lists must-stock OOS items at par quantities from the standard; the REP confirms and places it - the plugin never transmits an order.
## 5. Confidence floor
Missing scan extract or standard -> confidence < 0.75; ranking degrades to criterion order with an explicit note.
