# AI FinOps Admin Console

Create a point-in-time, offline HTML console for your tenant's AI spend and
consumption. It combines data from A365 Analytics (Viva Insights), Microsoft 365
Admin Center, and Power Platform Admin into charts and sortable tables across
11 areas, including spend, credits, users, agents, Cowork, and Power Platform.
Choose between 7 days, 30 days, quarter to date, and 90 days.

## Before you start

- Microsoft 365 Copilot Cowork and OneDrive for Business must be available.
- Enable and connect the A365 Analytics, Microsoft 365 Admin Center, and Power
  Platform Admin plugins in Cowork. Enable the skill and plugins for the task.
- Use an account with the appropriate admin permissions: Global Administrator
  or AI Administrator plus Billing Administrator or reader for billing and
  credits, and Power Platform Administrator for Power Platform inventory.
- Viva Insights requires an analyst or leader perspective; the Global partition
  is preferred. Data can lag about a week, and privacy thresholds hide small groups.
- Power Platform data requires a connected Power Platform for Admins V2
  connection. Cowork can request permission to create one and prompt you to sign in.

If a plugin or permission is unavailable, the skill can continue with the
remaining sources and reports unavailable sources in its summary.

## Install and run

Download and unzip the skill, then upload the unpacked
`cowork-ai-finops-analysis` folder to OneDrive for Business under
`Documents/Cowork/skills/`. Ensure `SKILL.md` is directly inside that folder,
alongside `scripts/` and `assets/`, without an extra nested folder. Alternatively,
attach the downloaded bundle in a Cowork chat and ask Cowork to install it as
`cowork-ai-finops-analysis`.

In a new Cowork task, check that the skill and plugins are enabled and ask:

> Build the AI FinOps console for my tenant.

The skill captures data in stages and produces
`ai-finops-admin-console-<tenant>-<date>.html`. A run may take 10–25 minutes,
depending on tenant size. If interrupted, ask Cowork to continue the same run.
Re-run it for a fresh snapshot.

## Data and limitations

The skill reads tenant data without changing tenant settings, policies, or
licenses. With your approval it may create a Power Platform connection. The HTML
contains tenant data, including names and costs; store and share it only with
authorized people. **Unavailable or failed reports can appear as zero or empty
values**, including AI spend and forecasts. Verify source availability and
values before relying on the console. Cloud-flow inventory can be incomplete
when the connector returns additional pages; the report warns when it detects this.
Credits and USD are different measures and must not be added
together; Admin Center and Viva Insights credits also have different definitions.
Some reports may not be available in every tenant.
