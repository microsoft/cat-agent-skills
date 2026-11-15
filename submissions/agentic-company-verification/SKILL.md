---
name: agentic-company-verification
description: Verify UK companies using the Companies House API. Use when the user asks whether a company exists, wants its registration (company) number, status (active/dissolved), incorporation date, SIC codes, registered office, directors/officers, persons with significant control, charges, insolvency or filing history. Triggers - "verify company", "does X Ltd exist", "Companies House", "company number", "who are the directors", "SIC code", "is company active", "create this company in Dynamics 365 Dataverse account table".
---

# Companies House company verification

Verify and report on UK companies using the official Companies House Public Data API
(https://developer.company-information.service.gov.uk/). Read-only; no data is changed.

## Tools used

Prefer the tools from the **Companies House Verification** custom connector
(`assets/companies-house-connector.swagger.json`), whose operation IDs map to the endpoints below.
If the connector is not available, call the REST API directly (see `references/api-reference.md`)
or run `scripts/ch_lookup.py`.

| Operation ID | Endpoint | Purpose |
| --- | --- | --- |
| `SearchCompanies` | `GET /search/companies?q=` | Find a company by name or number |
| `GetCompanyProfile` | `GET /company/{companyNumber}` | Status, dates, SIC codes, address |
| `ListOfficers` | `GET /company/{companyNumber}/officers` | Directors/secretaries |
| `ListPSCs` | `GET /company/{companyNumber}/persons-with-significant-control` | Beneficial owners |
| `ListCharges` | `GET /company/{companyNumber}/charges` | Mortgages/charges |
| `GetInsolvency` | `GET /company/{companyNumber}/insolvency` | Insolvency cases |
| `ListFilingHistory` | `GET /company/{companyNumber}/filing-history` | Recent filings |

## Workflow

1. **Identify the company.**
   - If the user gives an 8-character company number (e.g. `00445790`, `SC123456`, `OC301234`), skip to step 3. Pad purely numeric numbers with leading zeros to 8 characters.
   - Otherwise call `SearchCompanies` with the name (`items_per_page` = 5).
2. **Disambiguate.** If there is one clear exact (case-insensitive) name match, use it. If several plausible matches exist, list up to 5 (name, number, status, incorporation date, address) and ask the user to pick. If none, say the company was **not found** on Companies House and suggest checking spelling, trading vs registered name, or that it may be non-UK/unregistered. Never guess.
3. **Get the profile** with `GetCompanyProfile`. A 404 means no such company number: report "does not exist".
4. **Fetch extras only when asked** (or for a "full report"): officers, PSCs, charges, insolvency, filings.
5. **Answer** using the format below. Always state the source and retrieval time.

## What to report

Verification (default):
- Exists: Yes/No
- Company name, company number, type (`type`)
- Status (`company_status`, plus `company_status_detail` if present) – state clearly **Active**, Dissolved, Liquidation, Administration, etc.
- Incorporation date (`date_of_creation`); cessation date (`date_of_cessation`) if dissolved
- Registered office (`registered_office_address`)
- SIC codes (`sic_codes`)
- Accounts: next due / last made up to; confirmation statement next due; overdue flags
- Flags: `has_charges`, `has_insolvency_history`, `has_been_liquidated`, `undeliverable_registered_office_address`
- Previous company names, if any

Officers: name, role (`officer_role`), appointed on, resigned on, nationality, country of residence, occupation, month/year of birth only. Show **current** officers (no `resigned_on`) first; show resigned only if asked.

PSCs: name, kind, natures of control, notified on, ceased on.

## Saving to Dynamics 365 / Dataverse

When, after verifying a company, the user asks to create/save/add it as a record in Dynamics 365 Dataverse (the `account` table), follow `references/dataverse-account.md` exactly:
1. On the first run, create any missing Companies House columns on `account` (registration number, status, incorporation date, SIC codes, registered office, accounts/confirmation dates, flags, officers, etc.).
2. Add them to the Account main form on a new tab named **Companies House Information**, then publish.
3. Check for an existing account with the same company number; create or (with consent) update, mapping API values to the columns.
Only do this on explicit request, only for a company verified in this conversation, and never with invented values. Needs the agent to have Dataverse tools (with schema/form rights for the first run).

## Rules

- Report only data returned by the API; say "not provided" for missing fields. Do not infer or invent.
- Compare a user-supplied name/number with the returned record and flag mismatches (e.g. name changed, see `previous_company_names`).
- Flag as **caution / not fully verified** any company that is not `active`, has overdue accounts or confirmation statement, has insolvency history, or has an undeliverable registered office. State these as facts, not accusations.
- Only show officer/PSC personal data when requested; never show full date of birth (the API only returns month/year).
- The company number is the authoritative identifier; names are not unique.
- This is a public register check, not legal, credit or KYC/AML advice.
- Errors: `401` = invalid/missing API key (tell the admin to check the connection; never display the key), `404` = not found, `429` = rate limit (600 requests / 5 minutes) – wait and retry once, then report.
- Never echo the API key.

## Example response

> **Acme Widgets Ltd** (09876543) — ✅ Exists, **Active**
> Type: Private limited company · Incorporated: 12 March 2016
> Registered office: 1 High Street, London, EC1A 1AA
> SIC: 62012
> Accounts next due 30 Sep 2026 · Confirmation statement next due 25 Mar 2027 (not overdue)
> No charges or insolvency history.
> Source: Companies House API, retrieved 15 Nov 2026 10:00 UTC.
