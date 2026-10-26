# Returns Rules (cited as returns-rules.md #<n>; engine constants mirror sections)
## 1. Eligibility
1.1 Window per category lives in config/return-windows.json; the clock runs from the order/receipt date to the request date.
1.2 Receipt or order lookup required above the receiptless limit (config); below it, ID-verified store credit only.
1.3 Condition rules: opened software/consumables non-returnable; worn/used items per category flag.
## 2. Determination discipline
2.1 The determination is eligible / ineligible / needs_evidence with the clause cited. A sympathetic story is context for a HUMAN exception, never an engine input.
2.2 needs_evidence lists exactly what is missing; the case is not decided until it arrives.
## 3. Fraud signals (surfaced, never adjudicated)
3.1 Serial mismatch: unit serial != serial sold on the order line.
3.2 Return frequency: > config threshold receiptless returns in 90 days.
3.3 High-value receiptless: value above config limit without receipt.
3.4 Wardrobing pattern: fashion category, worn flag, return on the window's last days.
Signals attach to the packet for asset-protection review; the plugin never accuses.
## 4. Confidence floor and human gate
4.1 Determination confidence < 0.75 -> hold_for_review.
4.2 Any fraud signal present -> recommendation is hold_for_review regardless of eligibility; a human decides.
## 5. Exceptions
5.1 Policy exceptions are a manager decision recorded as such - the plugin drafts the exception request; it never grants one.
