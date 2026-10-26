# Deduction Rules (cited as deduction-rules.md #<n>; engine constants mirror sections)
## 1. Matching
1.1 A claim matches when customer + period + type align with a signed term or calendared promotion. Unmatched claims are UNSUPPORTED, not assumed valid.
## 2. Validity (Govern)
2.1 valid: claimed amount <= entitled amount from the signed term (rate x actual volume).
2.2 partial: claimed > entitled -> disputable = claimed - entitled, calculation shown.
2.3 unsupported: no backup document or no matching term -> fully disputable pending backup.
2.4 Write-off is a business decision a human makes; the engine only quantifies. "Not worth chasing" is not a verdict.
## 3. Lift scoping (RGM foundation)
3.1 promo_lift runs ONLY when config/rgm-scoping.json declares account_pnl_present=true. Absent that foundation, lift is out of scope by design - deduction validity still runs. (Per RGM guidance: recommend and collaborate, not override.)
3.2 Baseline = fixed pre-period average, stated in the output; never re-fitted to flatter the promo.
## 4. Confidence floor
Illegible backup or ambiguous term version -> confidence < 0.75, analyst review before dispute.
