# Dataverse account table: Companies House columns, tab and upsert

Used only when the user asks to create/save the verified company in Dynamics 365 / Dataverse.
Use the agent's Dataverse tools (Dataverse MCP/connector). Never invent data: write only values returned by the Companies House API.

`{p}` = the publisher prefix of the solution the columns belong to (e.g. `cr123`). Discover it from an existing custom column on `account` or the target solution's publisher; ask the user once if it cannot be determined. Do not hard-code another prefix.

## Columns on `account` (create only those that are missing)

| Schema name | Display name | Type | Source |
| --- | --- | --- | --- |
| `{p}_companynumber` | Company Registration Number | Text (8) | `company_number` |
| `{p}_companystatus` | Company Status | Choice: Active, Dissolved, Liquidation, Administration, Receivership, Voluntary Arrangement, Converted/Closed, Insolvency Proceedings, Other | `company_status` |
| `{p}_companystatusdetail` | Company Status Detail | Text (200) | `company_status_detail` |
| `{p}_companytype` | Company Type | Text (100) | `type` |
| `{p}_incorporationdate` | Incorporation Date | Date only | `date_of_creation` |
| `{p}_dateofcessation` | Date of Cessation | Date only | `date_of_cessation` |
| `{p}_siccodes` | SIC Codes | Multiline text (500) | `sic_codes` joined by `; ` |
| `{p}_registeredoffice` | Registered Office | Multiline text (1000) | `registered_office_address` joined |
| `{p}_jurisdiction` | Jurisdiction | Text (100) | `jurisdiction` |
| `{p}_accountsnextdue` | Accounts Next Due | Date only | `accounts.next_due` |
| `{p}_accountsoverdue` | Accounts Overdue | Yes/No | `accounts.overdue` |
| `{p}_confstatementnextdue` | Confirmation Statement Next Due | Date only | `confirmation_statement.next_due` |
| `{p}_confstatementoverdue` | Confirmation Statement Overdue | Yes/No | `confirmation_statement.overdue` |
| `{p}_haschargesflag` | Has Charges | Yes/No | `has_charges` |
| `{p}_hasinsolvencyhistory` | Has Insolvency History | Yes/No | `has_insolvency_history` |
| `{p}_previouscompanynames` | Previous Company Names | Multiline text (1000) | `previous_company_names` |
| `{p}_currentofficers` | Current Officers | Multiline text (4000) | current officers: name, role, appointed on |
| `{p}_chprofileurl` | Companies House Profile | URL | `https://find-and-update.company-information.service.gov.uk/company/{number}` |
| `{p}_lastverifiedon` | Last Verified On | Date and time | retrieval time (UTC) |

Map the company name to the standard `name` column.

## First-run setup (idempotent)

1. Read `account` metadata. Compute which columns above are missing (match by schema name; if a column with the same purpose already exists under another name, reuse it and tell the user).
2. If any are missing, tell the user which columns will be created, then create them (add to the existing unmanaged solution the user names, otherwise ask which solution; never use the Default solution silently). Publish customisations.
3. Form: open the main **Account** form (type Main, the one the user's app uses; ask if several). If a tab named **Companies House Information** is absent, add it with one section **Company Details** and a second **Registered Office & Compliance**, placing all columns above (read-only for `{p}_lastverifiedon`). Save and publish the form. If a tab with that name exists, add only missing fields to it.
4. Read back the metadata/form to confirm, and report what was created vs. already present. Skip steps 1-3 on later runs once all columns and the tab exist.

If the tools cannot change schema or forms (permissions), stop, list the exact columns/tab needed, and ask an administrator or the user to create them. Do not claim success.

## Create or update the record

1. Require a verified company number from the Companies House API in this conversation. Fetch the profile, and current officers if not already retrieved. Refuse if the company was not found.
2. Search `account` for `{p}_companynumber eq '<number>'`. If found, show it and ask whether to update; update only the Companies House columns (and `name` if the user agrees). If not found, create it.
3. Confirm with the user before writing (name, number, status), unless they have already clearly said to create it.
4. Write the values per the mapping above (dates as `yyyy-MM-dd`; empty source = leave null). Set `{p}_lastverifiedon` to now (UTC).
5. Report the record name and its GUID/link, and which fields were set. Mention if the company is not Active.
