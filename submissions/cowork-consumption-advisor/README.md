# Cowork & Work IQ Consumption Advisor

**Command:** `/analyze-cowork-consumption` · **Platform:** Cowork

Copilot Cowork and the Work IQ API are billed in Copilot Credits. The Microsoft 365 admin center
shows what was consumed - but tab by tab, as snapshots, with no join between *who*, *which policy*,
*which group*, *how many tasks* and *what it cost*. This skill takes the five exports an admin
already has and turns them into one interactive report an executive can read in two minutes.

## Why
Copilot Cowork and the Work IQ API are billed in Copilot Credits through usage-based billing. The
Microsoft 365 admin center shows the numbers but only as snapshots, tab by tab, with no organisational
context. This skill reads the exports an admin already has, enriches consuming users with department,
job title, country and manager from Microsoft Graph, and produces one report an executive can read in
two minutes. Group, policy and user exports are independent aggregates (the admin center does not
export user-to-policy membership), so they are shown side by side rather than joined.

## What you get
- **Headline KPIs** - credits used, prepaid vs pay-as-you-go share, estimated cost, active users,
  credits per active user, credits per Cowork task, month-end or annualised forecast
- **Service breakdown** - Cowork, Cowork apps, Work IQ API; prepaid vs pay-as-you-go ring
- **Spending-limit analysis** - every policy with limit, usage rate, billing method; unlimited,
  near-limit and idle policies flagged
- **Departments and managers** - every consuming user is enriched from **Microsoft Graph**
  (department, job title, country, direct manager) so leadership sees spend by department and
  an accountability view per manager - credits, share, users, avg per user, credits per task,
  near-limit count, top user
- **Groups and users** - concentration (top 10 / top 20 %), limit tiers, over- and near-limit
  watchlist, dormant and unlicensed consumers, sortable and filterable tables
- **Evidence-backed recommendations** - each with the numbers behind it and a concrete action
- **Data-quality notes** - snapshot mismatches, overlapping groups, users over 100 % of a changed limit

Output: a self-contained `consumption-report.html` (no CDN, printable, safe to email), a
`consumption-summary.md` for chat or Teams, and `consumption-analysis.json` with every figure.

## Inputs
Exports from **Microsoft 365 admin center > Copilot** (CSV, any file name - detected by columns):

1. Cowork > Usage > **Cowork usage details**
2. Cost Management > Consumption > **Policies** (Configuration export)
3. Cost Management > Consumption > **Users**
4. Cost Management > Consumption > **Groups**
5. Cost Management > Consumption > **Agents and services**

Only Users *or* Agents and services is strictly required; every extra export unlocks a section.
Department and manager data is collected by the skill itself through Microsoft Graph
(`/users?$expand=manager`, read-only). An Entra user export or a simple org CSV works as a fallback.
Synthetic sample exports ship in `assets/sample-exports/` (five CSVs plus a Graph user JSON with
managers) so you can see the report before touching a tenant.

## How to use
Drop the exports into the conversation and say **"Build a consumption report from these files"**
(or `/analyze-cowork-consumption`). Optional: currency and contracted rate
(`--currency EUR --rate 0.0092`), `--anonymize` for wide distribution (pseudonymises every output),
`--period ytd` if you exported with a year-to-date filter (default is the current billing month).

Quick start outside Cowork:
```
python scripts/analyze_consumption.py --input <exports folder> --org <graph json folder> --out ./report
```

## Good to know
- **Reporting only.** It never changes spending policies, limits or billing methods.
- **Read-only Graph.** Directory enrichment uses `User.Read.All` GETs only; unresolved users are
  reported as unknown, never guessed.
- **Computed, not guessed.** All figures come from the bundled Python script (standard library only).
- **Invoice is truth.** Costs are list-rate estimates; the Azure subscription in the billing method
  carries the real bill.
- **Privacy aware.** `--anonymize` replaces names and UPNs with keyed pseudonyms (random per-run
  secret, so they cannot be reversed from a directory listing) and redacts input paths in every
  output; watchlists are spend-control, not performance ranking.

Complements the *Copilot Adoption Dashboard* skill (licence adoption from MAC usage reports) and
the Copilot ROI team's *Consumption Central* / *Chargeback* Power BI templates on Analytics Hub -
same exports, no Power BI required.
