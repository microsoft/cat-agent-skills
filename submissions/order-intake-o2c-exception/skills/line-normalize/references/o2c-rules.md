# O2C Validation Rules (cited as o2c-rules.md #<n>; engine constants mirror sections)
## 1. Product identity
1.1 A customer SKU alias must resolve to exactly ONE product; ambiguous aliases are exceptions, never a coin flip.
## 2. UOM sanity
2.1 An order in a UOM the customer has never used, or a quantity outside the customer's historical band (config multiplier), is a UOM/quantity anomaly - confirm before entry. 500 EA from a cases-of-24 customer is the classic rekeying disaster.
## 3. Price integrity
3.1 PO price deviating from list/agreed price beyond config tolerance without an active promo reference is a price exception.
## 4. Credit
4.1 Order value pushing exposure over the credit limit queues the order for credit review; it does not bounce the customer.
## 5. Action levels
5.1 L0 = draft only; L1 = validated order file prepared; L2 = exception routing active; order CREATION/RELEASE requires the customer to promote beyond L2 in config/. The plugin never self-promotes.
## 6. Confidence floor
Unreadable lines -> confidence < 0.75, the order never proceeds on guessed lines.
