# Report template

Choose the shape by channel first. If the host is Copilot Studio in Teams, or you cannot tell, use the chat shape: send the verdict and the five actions as the first message, then offer sections by name and send each on request; never a table wider than three columns. Use the full structure in Cowork documents, long-form replies, or when the user asks for a report. Cite finding IDs (F1, F2, …) and rule IDs (EX1, CR1, …) wherever a statement rests on one. Finding numbers are assigned per run and differ between reports; rule IDs are stable, so cross-reference by rule ID and cite the run you attach.

## What the script's report looks like

The script's Markdown report is the raw audit; the shapes below are what you build from it. A pasted full report has these parts, in this order:

```markdown
# Agent inventory audit

| Item | Value |
| Sources | agents.json (inventory API / pac resource-query, 312 records) |
| Agents audited | 287 of 300 agent records (13 outside the requested scope) |
| Export completeness | INCOMPLETE: … (only when an API page was truncated) |
| Rules evaluated on part of the scope | EX2 skipped 12 agents (12 from admin.csv; sharedWithViewers not in that file) (only when files from different routes are combined) |
| Reference date (--as-of) | 2026-10-16 (used for age calculations; not the export time) |
| Environment records in export | 12 |
| Environments joined | 287 of 287 environment IDs resolved to a name |
| Users joined | 1204 records; 41 of 41 distinct owners resolved |
| Field coverage | 29 of 30 fields present; absent: harness; present but empty: sharedWithEditors |
| Rules not evaluated | EX4 (sharedWithEditors): field present but empty in every record (re-export …); RG1: --allowed-regions not supplied (pass --allowed-regions to check) |
| Not visible to this audit | instructions, knowledge content, usage, … |
| Tool | agent_inventory_audit.py 1.2.0 |

## Warnings (only when there is something to say: an incomplete API page, unresolved environments, unparsed dates, consent values missing)
## Posture summary
| Measure | Count |
| Shared with the entire tenant | 6 |
| Web search enabled | n/a (not in export) |
## Agents needing attention
| Agent | Environment | Owner | High | Medium | Findings |
| Public FAQ Bot | Contoso (default) | Bob Builder (bob@contoso.com; account disabled) | 4 | 4 | F1 F3 F4 F8 F11 F12 F13 F17 · F21 |
## Findings
### High (9)
| # | Rule | Agent | Owner | Finding |
| F1 | CR1 | Public FAQ Bot | Bob Builder (bob@contoso.com) | One tool operation, shared_excelonlinebusiness.RunScriptProd, runs on a maker-provided connection … |
… and 4 more (F30, F31, F32, F33). Use --json for the full list or --max-rows to show more.
### Medium … ### Low … ### Info …
## Remediation plan
### Ownership (…)
- **OW1 Owner account disabled or departing** — High, 3 agents. Reassign ownership … Refs: F6, F7, F8.
### Agent identity (…) … (one group per control)
## Work by owner
| Owner | Agents owned | With findings | High | Medium | Agents to act on | Findings |
## Environments
## Connector footprint
### Maker-provided connections
## Inventory profile
### Identity coverage / Authentication / Harness and authoring tool / Channels / Orchestration and models
## Agent IDs
## Method and limits
```

Records minus agents audited are environment records, duplicates merged by ID, or records outside a `--environment` scope; the header names each. A table that ends with "… and N more" is truncated: those findings exist but are not in the paste. In the attention table, finding IDs before the dot are high or medium and after it low or info.

The brief report (`--brief`) keeps a five-row header, one summary line, the attention table, high and medium findings as three-column tables (#, Agent, Finding with the rule ID in front), one line per low or info rule, a one-line-per-rule remediation plan, and a one-paragraph method note. The dossier (`--agent`) has a facts table, the connector operations table with a note naming any maker-provided connection and the other agents that use it, the findings, recommended actions split between administrators and the owner, and the checklist of what to confirm in Copilot Studio and the admin center. The owner handover (`--owner`) has the agents owned (with viewers and the highest finding besides ownership), shared connections and dependents, operations configured in other owners' agents, what is not visible, an ordered action table (Action, Who, Where), and the owner's agent IDs.

## Tenant posture

### 1. Verdict and the first five actions

One verdict line that states the scope, the counts that matter, and the gaps in evidence, then at most five actions ordered by severity (high, medium, low, info). Illustrative example; names and numbers are placeholders:

> **Verdict:** 287 agents across 14 environments, exported 15 October; 9 high findings on 6 agents, all in the Default environment and one Developer environment. Identity: 261 Entra Agent IDs, 19 legacy app registrations, 7 Agent Builder. Credential rules ran on API data; one agent exceeds the 200-item cap, so its connector list is partial.
>
> 1. **F1, F2, F6** Public FAQ Bot (owner's account disabled): tenant-wide, no user authentication on a custom website, runs an Excel script on a maker-provided connection. Microsoft 365 admin confirms the sharing today; Power Platform admin reassigns ownership; the new owner switches the tool to a user-provided connection or consent and enables authentication.
> 2. **F4, F5** Reassign the departing owner's three agents before the account closes.
> 3. **F11** Migrate 19 legacy app-registration agents so Conditional Access can see their connector scopes.
> 4. **F14** Expense Approver is unmanaged in Production; bring it into the Finance solution and pipeline.
> 5. **RG1** Supply the approved region list and rerun; two agents are in unitedstates.

### 2. Scope and evidence

Where the export came from (admin center CSV, API, Resource Graph), when it was taken, the reference date the script used, which environments, how many agents, which rules did not run and why, whether environments and users were joined, and whether a watch list or region list was supplied. State plainly what the inventory cannot show (instructions, knowledge content, usage, data policy results, Conditional Access state, Copilot Credits, whether Agent 365 is enabled).

### 3. Posture

The summary counts, restated in sentences or a three-column table: published versus draft, identity coverage, authentication, channels, tenant-wide shares, quarantined, harness mix. One sentence per number that changes what the reader should do; skip the rest. Counts name no agents; when one matters, ask for the JSON.

### 4. Findings by theme

One block per theme, by default in this order: exposure and credentials together (they compound), identity, ownership, lifecycle and ALM, region and model. The purpose may move one theme first (identity for an Agent 365 review, ownership for a handover). Within a theme, group by agent when one agent carries several findings, because the fix is one conversation with one owner. Start from the agents-needing-attention table. Each block:

> **Public FAQ Bot** (Contoso default, owner Bob Builder, account disabled). Shared with the entire tenant (F2) with no user authentication on a custom website channel (F1) and an Excel script tool on a maker-provided connection, callable in any conversation without consent (F6). *Consequence:* anyone who reaches the site can run the script with the maker's permissions. *Verify:* whether the site is live and whether the tenant-wide sharing was a store submission still awaiting approval. *Action:* Power Platform admin reassigns ownership; the new owner switches the tool to a user-provided connection or enables consent; Microsoft 365 admin reviews the sharing. *Refs:* F1, F2, F6.

Chat shape of the same block: one line "**Agent** (environment, owner): condition", then three short lines Consequence, Confirm, Action, then Refs.

Include every high and medium finding this way. Low and info findings can share one paragraph per rule with counts and an attachment reference. A credential finding on a never-published draft is a parked credential, not runtime exposure; say so and fold it into the LC1 block.

### 5. Environments and owners

Which environments carry the high and medium findings, which owners carry the most agents, and the quarantined and ownerless items. Three columns at most in chat.

### 6. Remediation plan

The script's plan regrouped by who acts: agent owners (connections, authentication, channels, drafts), Power Platform admins (ownership transfers, environment moves, quarantine decisions, identity migration), Microsoft 365 admins (sharing approvals, tenant settings), security (Conditional Access, connector policies, watch list). The script's work-by-owner table gives the owner side. Each line names the rule, the count, and the finding IDs. On agents with OW1 or OW2, the transfer comes first and owner actions are assigned to "the new owner".

### 7. Open questions

Numbered, each naming who answers it: intended anonymous agents, owners of shared connections, whether a watch list or region list exists, which departing accounts to include, when the export was taken, whether Agent 365 or environment groups already enforce some of this.

### 8. Not verifiable from the inventory

The limits list, tailored to what the findings touched, ending with one sentence that the audit lists what the inventory shows and what was evaluated, and establishes nothing about compliance.

## Environment review

Sections 1, 2, 4, 6, 7, and 8 restricted to the environment. Say that connections and owners shared with agents outside the environment are not visible in a scoped run. When a tenant-wide run exists, add one line after the verdict such as: "Contoso Production holds 22 of the tenant's 287 agents and 1 of its 9 high findings."

## Agent dossier

For one agent: the facts table from the script's dossier in prose or a two-column table, then every finding with consequence, verification, and action, then this fixed checklist of what to confirm in Copilot Studio and the admin center because the inventory cannot show it: Settings > Advanced > Metadata (identity), Settings > Security > Authentication, each tool's connection and consent settings, the knowledge sources and their connections, the Channels page, the Share panel, Analytics (usage and reactions), evaluation results, and data policy evaluation in the Power Platform admin center. Suitable as the brief for a review meeting with the owner.

## Owner handover

For one person: a facts line (how the person was identified: object ID, UPN, or display name; account state if a user list was supplied), then in this order: the agents they own with viewers and the highest finding besides ownership on each; the connections shared from those agents and every agent, including other owners' agents, that uses the same connection; operations they created in agents they do not own, when the JSON is available; what the inventory cannot show about them (editor seats, flows and apps outside these agents, whether the connections still authenticate, account state when no user list was supplied, members of shared viewer or editor groups); then an action table with columns Action, Who, Where, each action dated before the departure, transfers first.

## Remediation plan

Sections 1 and 6, with owners named where the user list resolved them, and a short list of the evidence gaps that would change priorities (missing connector detail, missing environment types, no user list, truncated tables, export age).

## Targeted question

One list, drawn from the findings or the JSON (the `identityMigration` list for legacy identities, agents with `published` false for drafts, `isQuarantined` for quarantined agents, empty `ownerId` for ownerless agents), grouped the way the user asked (by environment, by owner). Add one line of scope and evidence and name any rule not evaluated that bears on the list.

## Phrasing rules

- Lead with the condition, then the consequence, then the action. Never a bare rule name.
- Use display names; give the agent ID once per agent in an appendix or on first mention when names repeat. Give connection and app IDs in full once, then by their last segment.
- Say "maker-provided connection" and "user-provided connection", "end-user consent", and "no user authentication"; the script uses the same terms.
- Call severities "high finding", not "high risk". Say "the inventory shows" for facts and "confirm" for anything that needs the live tenant.
- Do not call an estate compliant, secure, or clean. Say what was evaluated and what was not.
- Keep object IDs out of the verdict and theme blocks unless no name is available.
