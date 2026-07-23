# Recommended Knowledge Metadata Schema

Use this schema to improve governance, filtering, retrieval, and lifecycle management.

## Minimum metadata

| Field | Purpose | Example |
|---|---|---|
| `title` | Human-readable content name | Laptop request policy |
| `owner` | Accountable business or content owner | IT Service Desk |
| `ownerEmail` | Contact for remediation | it-help@example.com |
| `lastReviewedDate` | Freshness signal | 2026-05-12 |
| `effectiveDate` | Policy start date | 2026-07-01 |
| `audience` | Intended users | Employees, managers |
| `category` | Retrieval and reporting grouping | IT access |
| `sourceSystem` | Original system of record | SharePoint |
| `sensitivity` | Data handling label or classification | Internal |

## Recommended metadata

| Field | Purpose | Example |
|---|---|---|
| `canonicalSource` | Marks authoritative copy | true |
| `region` | Region-specific filtering | US, EU, Global |
| `language` | Locale and localization | en-US |
| `productOrService` | Product/service scope | Copilot Studio |
| `reviewCadence` | Expected review cycle | Quarterly |
| `expirationDate` | Retirement or review trigger | 2026-12-31 |
| `relatedAction` | Action needed for live workflow | create_access_request |
| `relatedWorkflow` | Workflow used for guided flow | software_access_request |
| `version` | Content version | 2.1 |
| `status` | Lifecycle state | Draft, active, retired |

## Metadata quality checks

- Every production source should have an owner and review date.
- Policy content should have an effective date.
- Regional content should have a region or market field.
- Duplicate pages should identify a canonical source.
- Retired content should be removed, redirected, or clearly marked as retired.
- Restricted content should carry a sensitivity or classification value.
