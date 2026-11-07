# Service Rules (cited as service-rules.md #<n>; engine constants mirror sections)
## 1. Intent
1.1 Intent classifies against the configured taxonomy; below 0.75 confidence the run goes to handoff, not to a guessed answer.
1.2 Matching is word-boundary based after normalising case, curly apostrophes and whitespace; a keyword never matches inside another word.
## 2. Context integrity
2.1 A contradiction between records and the customer's account (carrier says delivered, customer says not received) selects the DNR path: carrier investigation per config before any refund/replacement, unless the config's instant-resolution gate is met (tier AND value limits). The check runs on every delivered carrier scan regardless of the classified intent: any intent that implies non-receipt (delivered_not_received, wismo, unclassified) is a contradiction.
2.2 The response never disputes the customer's account - it explains the process and the clock.
## 3. Money boundaries
3.1 Goodwill credit, payment-detail changes and unsupported policy exceptions are out of scope for the plugin at any tier - drafts may PROPOSE goodwill for a human to approve where config allows.
## 4. Grounding and handoff quality
4.1 A handoff packet carries: intent, full context, contradiction flags, what was already checked with citations, and the recommended next step. No bare transfers.
4.2 Records-only grounding: for answer_from_records paths, the OMS/carrier/loyalty extracts are approved grounding; no knowledge article is required. Every fact in the reply still cites its extract. An article is required only where the answer goes beyond the records (policy wording, product how-to, stock commitments); if none exists, the run is a handoff with "no approved answer" recorded.
