# Copilot Adoption Dashboard

Turns the four Microsoft admin center Copilot activity exports into a branded,
single-file HTML adoption dashboard — KPIs, user segments, surface and agent
usage, the conversion pipeline, and recommended next steps.

## Before you start

Nothing to install — the skill runs on the Python that ships with Cowork and
uses only the standard library. No connected account, no special permissions,
no network access needed at build time.

What you do need is **four CSV exports** from the Microsoft 365 admin center
(**Reports → Usage → Microsoft 365 Copilot**, then *Export*). Pulling reports
there requires an admin role that can read Copilot usage data — typically Reports
Reader, Usage Summary Reports Reader, or a Global/Copilot admin. If you can open
the Copilot usage report in the admin center, you can export what this needs:

| # | Report | What it carries |
|---|---|---|
| 1 | **Copilot usage** | One row per licensed user — prompts, active days, per-app activity |
| 2 | **Agents — per user** | Agents used and responses received, per user |
| 3 | **Agents — per agent** | One row per agent — active users, responses sent |
| 4 | **Copilot Chat** | Chat activity, **including users with no paid licence** |

Bring all four for the full picture. Fewer is fine — the dashboard renders what
it can and marks the rest as pending rather than guessing.

Optional: a **logo** file (PNG, JPG, GIF or WebP). It gets embedded into the
HTML, so the finished dashboard stays a single portable file.

## How to use it

Run the command, or just ask in plain language:

```
/create-copilot-adoption-dashboard
```

> "Create a Copilot adoption dashboard for Contoso"
> "Turn these MAC exports into an adoption dashboard"
> "Build my Copilot usage dashboard — company is Fabrikam, logo attached"

The skill will explain the process, ask for your **company name** (required) and
**logo** (optional), and pick up the CSVs you've attached. It works out which
file is which by reading the column headers, so you don't need to name them in
any particular way.

It then computes the real numbers and hands back one HTML file —
`<Company>_Copilot_Adoption_Dashboard.html` — that opens in any browser:

- **Four KPI tiles** — licence activation, habitual-user rate, agent adoption, and conversion-ready leads.
- **Users by segment** — Champion, Habitual, Casual, Dormant, Never activated.
- **Top surfaces** — the ten apps where Copilot is actually being used.
- **Agent usage share** — the ten agents with the most reach.
- **Conversion funnel** — unlicensed Chat users ranked into Warm and Hot leads.
- **Recommended next steps** — the enablement plays that apply to *your* numbers.

Every tile and panel has an **i** button explaining what the metric means, how
it's calculated, and the target it's measured against. Hovering the donut or any
bar shows the underlying head-count, not just the percentage.

Before it delivers, it shows you a summary of the computed KPIs so you can sanity
-check them. You can also ask for a specific reporting window or report date, or
rerun with a corrected company name — just say so.

## Good to know

**The reporting window comes from your data.** The skill reads the *Report
Period* column (the admin center default is 28 days) and states that window on
the dashboard. If your exports disagree with each other, or the column is
missing, it tells you which window it used and why. Only override it if you
genuinely want a different period.

**Recommendations are earned, not generic.** Two kinds appear. *Triggered by your
KPI values* cards show up only when a number misses its framework target, and
each one quotes the number that triggered it. *Ongoing recommendations* — where
to focus training (your strongest surfaces and agents) and awareness (the quiet
ones) — always appear, because they're steady-state advice rather than a threshold
breach. If every KPI passes, you get "You're doing great — keep it up!" with the
ongoing cards beneath it.

**Missing a report is safe.** Leave one out and the related panel renders as
*pending* with a note naming what's needed. Nothing is ever estimated or filled
in with sample data — if the skill can't compute something, it says so.

**Zero-percent surfaces are shown on purpose.** An app sitting at 0% isn't a bug;
it's a licensed capability nobody is using, which is exactly where targeted
enablement pays off. Ask if you'd rather hide them.

**It's a single-period snapshot.** Growth, retention and dormancy trends need two
exports to compare, so they aren't reported. 

**Unusual column names are handled.** Headers are matched by keyword, not exact
text, so tenant-to-tenant differences are usually absorbed. If a column genuinely
can't be matched, the skill reports which one and can be pointed at the right
header — it will never quietly substitute a different number.

**Privacy.** The dashboard is aggregate only — segment counts, percentages and
totals. No individual user rows, names or rankings appear in the output, and the
skill won't evaluate individual people's usage. Due to this, you can use anonimized report exports as well.

**Sharing it.** The result is one self-contained file with the logo embedded and
no external dependencies, so it emails and archives cleanly. It's a point-in-time
snapshot, not a live report — rerun it with fresh exports each month.

**Adoption Analytics Framework.** Is custom. All KPIs used are custom developed and not using any public framework approach such as Microsoft Adoption toolkit or M365 Copilot Adoption Guide. Entire framework is within explained within references/adoption-framework.md.
