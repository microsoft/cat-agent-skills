# Risk and Compliance

Six Cowork skills that draft cited working papers for compliance, risk, and audit teams.

## What's included

- **reg-change-triage** — triages regulatory rule changes.
- **policy-gap-analysis** — maps policies to rules in a gap table.
- **exam-request-response** — tracks and drafts responses to exam requests.
- **enforcement-action-review** — enforcement action read-across.
- **vendor-risk-review** — vendor SOC 2 reviews.
- **kyc-research-pack** — KYC research records.

## Limitations

The skills never conclude compliance, rate risk, approve a vendor, or screen sanctions. Nothing is sent
or filed.

## How it was tested

This plugin went through both human and AI evaluation and has a passing score for overall quality
and build.

## Extending with connectors

Each skill uses a configured connector first, read-only for pre-fill and reconciliation. If none is
available, it falls back to public primary sources by direct route or browser, then supplied or
Microsoft 365 documents, and asks for an upload when a source cannot be reached.

| Skill | Connectors that improve it | Fallback without them |
|---|---|---|
| reg-change-triage | Reg-intelligence; GRC change register; policy/DMS; Planner or issue platform | Federal Register and eCFR, then uploaded or M365 policies |
| policy-gap-analysis | Policy repository, DMS, GRC; Regulations.gov (free API key) | eCFR and Federal Register, then the supplied policy |
| exam-request-response | DMS, audit, issue-management, GRC, Planner | SharePoint, OneDrive, Teams, and Outlook search, then uploads |
| enforcement-action-review | GRC control library, policy repository, DMS, legal matter system | SEC, FinCEN, OCC, FRB, and CFPB sites, then uploaded orders and M365 controls |
| vendor-risk-review | TPRM, GRC, DMS, contract system, screening provider | Supplied SOC reports and DDQs, plus labelled public research |
| kyc-research-pack | Screening or registry provider (World-Check, Dow Jones, LexisNexis) | Public registries, courts, regulator releases, and adverse media, then supplied onboarding files |

## Contributors

- Copilot Acceleration Team (CAT)
