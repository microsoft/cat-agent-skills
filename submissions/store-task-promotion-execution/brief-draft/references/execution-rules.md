# Execution Readiness Rules (cited as execution-rules.md #<n>; engine constants mirror sections)
## 1. Applicability
1.1 A pack requirement applies to a store only when the store's format AND cluster are in the requirement's applicability lists. Not-applicable is a status, not an omission.
## 2. Completeness
2.1 A requirement is ready only when every named asset/task for it is confirmed received or done at the store. completeness_pct counts applicable requirements only.
## 3. Price integrity
3.1 A promo price higher than or equal to the current shelf price is a PRICE CONFLICT - the top mispricing pattern; block the shelf change and escalate.
3.2 Two different prices for the same SKU across pack and price file is a PRICE CONFLICT.
## 4. Fixture / format conflicts
4.1 A requirement needing a fixture the store's format does not carry is a CONFLICT, not a missing item - the store cannot fix it locally.
## 5. Exception ranking
5.1 rank = weekly promo revenue at stake (velocity x promo price) x launch-proximity factor (2x inside 3 days) x price-conflict factor (1.5x, applied ONLY to PRICE CONFLICTS from #3.1/#3.2 - a mispricing costs margin on every unit, not just the display). Revenue impact, not count. Velocity is never estimated: no extract, no ranking.
## 6. Confidence floor
6.1 confidence = 0.95 when the store profile (store_id, format, cluster) AND the shelf-price extract are both present; a missing/incomplete profile caps it at 0.50, a missing/empty price extract caps it at 0.60. Below 0.75 readiness is BLOCKED (readiness.blocked = true) with an explicit escalation naming the missing input - never a crash, never a READY.
