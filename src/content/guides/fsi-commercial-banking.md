# Commercial Banking

Six Cowork skills for commercial banking credit and coverage teams.

## What's included

- **financial-statement-spread** — historical borrower-credit spread with Input, Normalized, and Ratios tabs.
- **credit-memo-narrative** — descriptive credit-memo sections.
- **credit-annual-review-packet** — annual credit-monitoring packets.
- **covenant-compliance-check** — governing-agreement-led covenant and borrowing-base reviews.
- **borrower-prospect-research** — borrower and prospect public-records research.
- **rm-call-prep-followup** — relationship call prep and call-note write-ups.

## Limitations

Runs on supplied documents, Microsoft 365, public registries, SEC EDGAR, and public web, with no paid
data dependency. Every figure carries its source and page. The skills never rate a credit, approve or
decline, set pricing, draft adverse-action reasons, or characterise creditworthiness.

## How it was tested

This plugin went through both human and AI evaluation and has a passing score for overall quality
and build.

## Extending with connectors

Each skill uses a configured connector first. If none is available, it falls back to supplied
documents and Microsoft 365, then public sources, and flags any remaining gap. Vendor names are
examples the skills recognize; any connector carrying the same data works.

| Skill | Connectors that improve it | Fallback without them |
|---|---|---|
| financial-statement-spread | Document extraction (Ocrolus, Hyperscience); peer benchmarks (RMA, Moody's Analytics, S&P Capital IQ); LOS/core (nCino, GL) | Uploaded statements and tax returns, then SEC EDGAR for public filers |
| credit-memo-narrative | LOS (nCino); CRM (Salesforce, DealCloud); company data (S&P Capital IQ, Moody's, D&B) | Term sheet, spread, and deal email from uploads/M365, then registries and EDGAR |
| credit-annual-review-packet | LOS/servicing (nCino); core/GL; business credit (D&B, Experian) | Prior review and current statements from uploads/M365, then public records |
| covenant-compliance-check | Covenant tracking or LOS (nCino); core/GL | Uploaded credit agreement and certificates, then EDGAR exhibits |
| borrower-prospect-research | Business credit (D&B, Experian, Equifax); company data (S&P Capital IQ, PitchBook); CRM (Salesforce, DealCloud) | Public registries and EDGAR via web or browser, then uploads/M365 |
| rm-call-prep-followup | CRM (Dynamics 365, Salesforce); core/treasury | Microsoft 365 mail, Teams, and meetings, then company site, registry, and EDGAR |

## Contributors

- Copilot Acceleration Team (CAT)
