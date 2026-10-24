# Copilot Studio Agent Inventory Audit

The Power Platform admin center keeps an inventory of every Copilot Studio agent in your tenant. Download it, hand it to this skill, and get a governance report: which agents need attention and who owns them, then identity coverage, exposure, credential sharing, lifecycle, and ownership, each with the control that fixes it. The skill reads that inventory (admin center CSV, inventory API, `pac resource-query`, or Azure Resource Graph) and nothing else.

## What it produces

- A posture summary, then an **agents needing attention** table, so the first thing a reader sees is which agents to act on, who owns them, and whether that owner's account is disabled. Measures the export cannot support are shown as not evaluable, never as zero.
- Findings ranked by severity across 23 rules in five themes: exposure (no authentication, entire-tenant sharing, web search), credentials (maker-provided connections for tools or knowledge, one connection reused across agents, custom or watched connectors), identity (legacy app registrations, no identity recorded), lifecycle (old drafts, quarantined agents, unmanaged agents in Production, Default or Developer environments), and ownership (departing or missing owners, concentration), plus region and model checks.
- A remediation plan grouped by the control that fixes each rule, ownership first, and a **work by owner** table that gives each person their list.
- Environment, connector, and shared-connection tables, plus an identity migration list in the JSON.
- An **agent dossier** for one agent, and an **owner handover** for one person: their agents, the connections those agents share, the other agents that depend on them, and the actions to finish before the departure.

Nothing is inferred from agent names. A rule that cannot run because the export lacks a populated field is listed as not evaluated, with what would enable it, never as passed.

## Before you start

Export the inventory. Any of these works:

- **Power Platform admin center**: Manage > Inventory (or Manage > Copilot Studio), then **Download**. Quick, but the CSV lists connector names without operation detail, so the credential rules do not run.
- **Inventory API or `pac resource-query`** (the CLI command is in preview): query `PowerPlatformResources` for `microsoft.copilotstudio/agents` and `microsoft.powerplatform/environments` and save the JSON. This gives full connector detail and environment names. The API accepts delegated user tokens only.
- **Azure Resource Graph**: the same query from the Azure portal, `az graph query`, or PowerShell; save as JSON or CSV.

The skill's field catalog contains a ready-to-use query body and the equivalent KQL. Optionally add a user list (object ID, UPN, display name, account state) so owners appear by name and disabled accounts are flagged, and the approved regions and sensitive connector IDs your organization uses.

The bundled script `scripts/agent_inventory_audit.py` needs Python 3.8 or later and no packages. If your host cannot run Python, run the script locally and paste the Markdown report.

```bash
python3 scripts/agent_inventory_audit.py agents.json --users users.csv --md report.md --json report.json
python3 scripts/agent_inventory_audit.py inventory.csv --brief                                 # chat-sized: attention table, high and medium findings, one-line plan
python3 scripts/agent_inventory_audit.py agents.json --environments envs.json --environment "Contoso Production"
python3 scripts/agent_inventory_audit.py agents.json --agent "Public FAQ Bot"                  # one-agent dossier
python3 scripts/agent_inventory_audit.py agents.json --users users.csv --owner bob@contoso.com  # owner handover
python3 scripts/agent_inventory_audit.py agents.json --departing <object-id> --allowed-regions europe --watch-connectors shared_sql,shared_webcontents
```

## Example prompts

> Here is the inventory export for our tenant. We are onboarding to Agent 365 next month; what should we fix first?

> We are migrating legacy app-registration agents to Entra Agent IDs. From this export, list what is left, by environment and owner.

> Bob is leaving on Friday. From the inventory and this user list, which agents and shared connections depend on him?

> Audit the Contoso Production environment only and give me a remediation plan grouped by who has to act.

> Produce a dossier for the Public FAQ Bot before my review meeting with its owner.

## Good to know

- The inventory reflects each agent's **published** version. Draft changes are invisible until published, and classic chatbots (V1) are not included at all.
- Connector detail (who provides the connection, whether consent is required, how the orchestrator may use it) is Preview data and is capped at 200 resources of each type per agent; the report flags agents above the cap.
- Severity orders the work. It is this skill's heuristic, not a Microsoft rating and not a compliance verdict. Each finding says what to confirm in the live tenant before acting.
- The report's reference date is used for age calculations; it is not the time the export was taken. Sharing, quarantine, and account state change daily, so note when the export was made.
- The inventory API and `pac resource-query` return pages of up to 1,000 records. Pass every page file to the script together; a run on a truncated page is marked incomplete in the report header.
- Finding IDs (F1, F2, …) are numbered per run; a `--brief`, `--environment`, `--agent`, or `--owner` run renumbers them, so quote the run you attach and cross-reference by rule ID.
- The same bot ID can exist in several environments when a solution is deployed to each; the script audits each deployment separately and merges duplicates only within one environment. When one file names the environment (admin center CSV) and another gives its ID (API), pass `--environments` so the names resolve and the records merge.
- The departing-owner rule runs only when you pass `--departing` or a user list with an account-enabled or status column; owners missing from the list are reported as unknown, not as active.
- Owners appear as object IDs unless you supply a user list or the admin center CSV already carries names. `--departing` by UPN needs the user list to map UPNs to object IDs.
- Harness is derived from other fields when the export has no harness column; the report marks it.
- The custom-connector flag is a heuristic on the connector ID; your `--watch-connectors` list is the authoritative check.
- The report names people and the agents they own, and can include connection IDs and connector names. Review it before sharing outside the governance team.
- The script reads files and writes a report. It never calls the admin APIs and never changes an agent, a sharing setting, an owner, or an identity.

## Compatibility and attribution

This skill is published for Copilot Studio and Cowork. It consists of Markdown instructions plus one standard-library Python script. It reads the Power Platform inventory schema that Microsoft documents publicly and relies on no Microsoft tooling at runtime. It is a community contribution, not a Microsoft product, and does not replace Microsoft Agent 365, the Power Platform admin center's own governance features, or your organization's security review.
