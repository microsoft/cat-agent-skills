# Asset Management

Six Cowork skills for institutional asset managers: RFP and DDQ teams, investment writers, research
analysts, product specialists, client service, and consultant relations.

## What's included

- **rfp-ddq-response-draft** — first-pass RFP and DDQ answers from your approved library, cited per answer.
- **investment-commentary-draft** — fund, portfolio, or strategy commentary from approved narrative and performance sources.
- **security-research-brief** — compares two issuer filings' risk factors, MD&A, and guidance.
- **peer-product-intelligence** — fund comparisons from public summary prospectuses.
- **institutional-client-review-prep** — mandate review prep with IPS/guidelines and relationship commitments.
- **consultant-database-refresh** — consultant questionnaire refresh with a redline.

## Limitations

Runs on Microsoft 365 content, supplied documents, SEC EDGAR, and public web, with no paid data
dependency. Current firm performance, AUM, attribution, and fees come verbatim from a system of record
or uploaded export. Outputs cite every claim and carry marketing-material labelling for compliance review.

## How it was tested

This plugin went through both human and AI evaluation and has a passing score for overall quality
and build.

## Extending with connectors

Each skill uses a configured connector first. If none is available, it falls back to uploads, the
firm's SharePoint library, then public sources, and flags any remaining gap. Vendor names are examples
the skills recognize; any connector carrying the same data works.

| Skill | Connectors that improve it | Fallback without them |
|---|---|---|
| rfp-ddq-response-draft | RFP platform (Loopio, Responsive, Qvidian); CRM (Salesforce, Dynamics); performance system | Uploaded prior responses and ADV, then the SharePoint answer library |
| investment-commentary-draft | Performance/attribution system; FactSet or Morningstar for market context | Uploaded performance export, SharePoint archive, then FRED, BLS, BEA, and Treasury |
| security-research-brief | Bloomberg, FactSet, or Refinitiv (consensus estimates); internal research library | Uploaded filings or transcripts, then SEC EDGAR and IR sites via browser |
| peer-product-intelligence | Morningstar Direct or eVestment (percentiles, ratings, flows, holdings); internal product master | Uploaded fact sheets, then public summary prospectuses (497K) |
| institutional-client-review-prep | CRM (Salesforce, Dynamics); performance/attribution system | Uploaded deck or IPS, then Microsoft 365 mail, Teams, and SharePoint |
| consultant-database-refresh | eVestment or consultant database (read-only); performance system; HR/org system | Uploaded questionnaire and prior submission, then SharePoint |

## Contributors

- Copilot Acceleration Team (CAT)
