# Data sources - Microsoft 365 admin center exports

All five exports are CSV downloads from **Microsoft 365 admin center > Copilot**. The analysis script
recognises each file by its column headers (case, spaces and punctuation are ignored), so file names
do not matter. Invisible characters that the admin center adds around numbers (left-to-right marks,
non-breaking spaces) and thousands separators are stripped automatically.

| Export | Admin center path | Refresh | Key columns (as exported) |
|--------|-------------------|---------|---------------------------|
| **Consumption - Users** | Copilot > Cost management > Consumption > Users > Export | every 2 h; export is a snapshot | Display Name, User Principal Name, Monthly credit limit, Monthly credits used, User ID, Microsoft 365 Copilot license, Last activity date, Session Count, % Used |
| **Consumption - Groups** | Copilot > Cost management > Consumption > Groups > Export | every 2 h | Display Name, Total Users, Monthly credits used, Members that used credits, Avg credits per user per day, Group ID, Session Count, Last activity date |
| **Consumption - Agents and services** | Copilot > Cost management > Consumption > Agents and services > Export | every 2 h | Service Name, Active users, Monthly credits used, Prepaid credits used, Pay-as-you-go credits used, Last activity date |
| **Spending policies** | Copilot > Cost management > Configuration > Export | live | Spending policy, Applies to, Active users, Credits used, Current spending limit, Credit usage rate, Billing method, Policy status |
| **Cowork usage details** | Copilot > Cowork > Usage > user details > Export | ~48 h latency | UserPrincipalName, DisplayName, TotalTasks, ScheduledTasks, UserInitiatedTasks, ActiveDays, LastActivityDate |

Roles: AI administrator, License administrator, Global reader / Reports reader can view and export
consumption; Global or Billing administrator is needed to change billing methods (not required here).

## Directory enrichment (department, manager)

The consumption exports identify users by UPN only. The skill adds organisational context from
Microsoft Graph (read-only, `User.Read.All`):

```
GET /users?$filter=userPrincipalName in ('a@contoso.com', ... up to 15 ...)
    &$select=displayName,userPrincipalName,mail,department,jobTitle,usageLocation,officeLocation
    &$expand=manager($select=displayName,userPrincipalName)
```
Save each response (`{"value": [...]}`) as a `.json` file and pass the folder with `--org`
(or drop the files next to the exports). The script also accepts:

| Source | Columns used | Manager? |
|--------|--------------|----------|
| Graph user JSON (above) | department, jobTitle, usageLocation/country, officeLocation, manager.displayName, manager.userPrincipalName | Yes |
| Entra admin center > Users > Download users (CSV) | userPrincipalName, department, jobTitle, usageLocation | No |
| Hand-made org CSV | UserPrincipalName, Department, Manager, ManagerUpn, JobTitle, Country, CostCenter | Yes |

Matching is on UPN (case-insensitive) with a fallback to the Graph `mail` value, because admin
center exports sometimes carry the display e-mail. Guests, deleted users and users from another
tenant do not resolve and are reported under "(Unknown - not in directory)". Coverage is stated
in the report.

## How the figures relate (and why they do not add up)

- **Services** is the tenant total (Cowork, Cowork apps, Work IQ API). Prepaid = capacity packs;
  pay-as-you-go includes Copilot Credit pre-purchase plan (P3) credits.
- **Users** shows each user's credits under their **current** spending policy. If a user moved
  groups mid-period, earlier credits stay billed at policy level but drop out of the user row -
  so the user total is usually a little lower than the service total.
- **Groups** overlap: a user in three groups is counted in all three. Never add group rows together.
- **Policies** attribute credits to the policy that was active at the time of use, so policy
  totals can exceed the current user total.
- **% Used > 100** in the Users export means the limit was lowered or the user moved to a policy
  with a lower limit. Usage above a *per-user* soft limit completes the running task, is not billed
  (at Microsoft's discretion) and is not shown as consumed. Only the *policy-level* limit hard-stops.
- **Cowork usage** counts tasks, not credits, and includes activity from before metering started.
  Join on UPN (case-insensitive). Credits per task = credits / tasks for matched users only.

## Pricing assumptions used by the script
- Pay-as-you-go list rate: 0.01 per credit (`--rate`).
- Prepaid effective rate: 0.008 per credit (a 25,000-credit pack at 200 per month, `--prepaid-rate`).
- Pre-purchase plans (P3) are discounted by volume; pass the contracted rate if known.
- Costs are estimates. The invoice on the Azure subscription named in the billing method is the
  record of truth; MACC eligibility depends on that subscription's billing account.

## Related Microsoft Learn articles
- Understand usage-based billing and cost management for Copilot Credits
- Managing AI experiences enabled by usage-based billing (Cost management dashboard)
- Cowork usage report - Microsoft 365 admin center
- Microsoft Copilot Credits report (pay-as-you-go agents in Copilot Chat - a different meter)
- Copilot Studio billing rates and management (Power Platform admin center - out of scope here)

## Optional API paths (for automation, not used by the script)
- Microsoft Graph `GET /v1.0/copilot/reports/getMicrosoft365CopilotUsageUserDetail(period='D28',version='v2')`
  with `Reports.Read.All` - licensed-seat usage context (prompts, active days). No credit figures.
- Azure Cost Management exports / Usage Details API on the linked subscription - billed amounts
  for the Copilot Credit meters.
- Viva Insights Consumption Dashboard - trend over time by group / job function; reference only.
