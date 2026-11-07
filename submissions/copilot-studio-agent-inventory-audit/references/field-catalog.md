# Field catalog: Power Platform inventory records for agents

What each field in an agent inventory record means, where it comes from in each export shape, and what it cannot tell you. Field paths follow the Azure Resource Graph table `PowerPlatformResources`; the inventory API, `pac resource-query`, and the admin center read the same table. Status is the per-field tag in Microsoft's documentation as of October 2026; the agent inventory article itself is published as preview documentation, so fields marked GA can still change shape, and Preview fields can be null.

## Getting an export

| Source | How | Shape the script sees |
| --- | --- | --- |
| Power Platform admin center, **Manage > Inventory** (or **Manage > Copilot Studio**) | Filter if you like, then **Download**. The CSV holds the whole inventory, not just loaded rows. | CSV with the grid's display-name headers (Item name, Item type, Item ID, Owner, Environment, Created on, …). In practice the Connectors column holds names only, so credential rules do not run. |
| Power Platform inventory API | `POST {PowerPlatformAPI}/resourcequery/resources/query?api-version=2024-10-01` with a query body; delegated user token only (service principals and managed identities get 403). Page with `Options.Top`, `Skip`, `SkipToken`. | JSON object with `totalRecords`, `count`, `resultTruncated`, `skipToken`, and a `data` array of records with nested `properties`. |
| Power Platform CLI (preview command) | `pac resource-query query-resources` with the same request body. | Same JSON as the API. |
| Azure Resource Graph | Azure portal Resource Graph Explorer, `az graph query`, PowerShell, or REST against `PowerPlatformResources`. | A list of records, an object with `data`, a `columns`/`rows` table, or newline-delimited JSON. `properties` is often a JSON string. Portal CSV export keeps `properties` as one JSON column. |

A query body that returns agents and environments together, so the script can name environments:

```json
{
  "TableName": "PowerPlatformResources",
  "Clauses": [
    { "$type": "where", "FieldName": "type", "Operator": "in~",
      "Values": ["'microsoft.copilotstudio/agents'", "'microsoft.powerplatform/environments'"] }
  ],
  "Options": { "Top": 1000, "Skip": 0 }
}
```

A page holds at most `Top` records. When the response has `resultTruncated` set or returns a `skipToken`, repeat the call with `Options.SkipToken` until it does not, save each page as its own file, and pass all the files to the script together; it merges them by ID. A run on a truncated page alone reports the export as incomplete in the header and the warnings, and owner counts, shared-connection dependents, and handovers then cover only the records supplied. The script groups page files by their `totalRecords` value to judge each query; pages of two different queries that happen to report the same total are flagged as incomplete when their page chain does not add up, so keep each query's pages together and complete.

The equivalent KQL for Azure Resource Graph:

```kusto
PowerPlatformResources
| where type in~ ("microsoft.copilotstudio/agents", "microsoft.powerplatform/environments")
```

Roles that can read the inventory: Global administrator, Power Platform administrator, Dynamics 365 administrator, Global reader, AI administrator, AI reader. The AI roles see agents, agent flows, agentic apps, environments, and environment groups only. New or changed resources appear within about 15 to 20 minutes.

## Optional companion files

**User list** (`--users`): JSON or CSV with any of `id`, `objectId`, `userId` (object ID); `userPrincipalName`, `upn`, `mail`, `email`; `displayName`, `name`; and `accountEnabled` or `enabled` (boolean) or `status`, `state` (text: disabled, departed, left, terminated, inactive, offboarded, blocked, deleted mark the account as departing). Other common aliases are also recognized. A Microsoft Entra admin center user export fits. Owner keys in API and Resource Graph exports are object IDs, so the list needs the `id` column to resolve names; admin center CSVs may already carry owner display names, in which case the owner key is that name.

**Environment list** (`--environments`): the inventory's own environment records (type `microsoft.powerplatform/environments`) or a CSV with an environment ID column plus name, type, and managed flag. Environment records included in the main export are picked up automatically.

## Shared resource fields

| Canonical name | Path (ARM/JSON) | Typical CSV header | Type | Status | Meaning and caveats |
| --- | --- | --- | --- | --- | --- |
| id | `name` (schema reference) or `properties.name` (agent inventory article) | Item ID | GUID | GA | The agent's ID in its Dataverse environment (the CDS bot ID). The script reads both paths. The top-level `id` of an ARM record is a resource path; the script keeps only its last segment. |
| displayName | `properties.displayName` | Item name | string | GA | Display name of the published version. |
| type | `type` | Item type | string | GA | `microsoft.copilotstudio/agents` for agents. Admin center CSVs may say `Agent`. |
| location | `location` | Location | string | GA | Geographic region of the resource, for example `unitedstates`. |
| createdAt | `properties.createdAt` | Created on | datetime | GA | Creation time. |
| createdBy | `properties.createdBy` | Created by | string (object ID) | GA | Creator. The admin center may show a name instead. |

## Agent fields

| Canonical name | Path | Type | Status | Meaning and caveats |
| --- | --- | --- | --- | --- |
| ownerId | `properties.ownerId` | string (object ID) | GA | Current owner. Empty means no owner recorded. |
| environmentId | `properties.environmentId` | string | GA | Environment that holds the agent. Join to environment records for name and type. |
| lastPublishedAt | `properties.lastPublishedAt` | datetime | GA | Last publish time. Empty means a draft that was never published. When the column is absent or a value cannot be parsed, the script treats the agent as published for exposure rules and says so under Warnings. |
| createdIn | `properties.createdIn` | string | GA | `Copilot Studio` or `Microsoft Copilot Agent Builder`. Agent Builder agents have no Entra identity and `isManaged` is null for them. |
| schemaName | `properties.schemaName` | string | GA | Dataverse schema name, for example `cr5e3_agentName`. |
| harness | `properties.harness` | string | GA (documented) | `Standard`, `GitHub Copilot`, or `Copilot Chat`. Microsoft's sample queries note the field may not yet be returned; when absent the script derives it exactly as those queries do: `isCLIAgent` true → GitHub Copilot; model or createdIn mention Microsoft 365 Copilot or Agent Builder → Copilot Chat; otherwise Standard. The report marks derived values. |
| isCLIAgent | `properties.isCLIAgent` | boolean | undocumented (sample queries only) | Used only for harness derivation. |
| isQuarantined | `properties.isQuarantined` | boolean | Preview | True when an admin quarantined or blocked the agent. Makers can still see and test it; it cannot be used in any other channel. Blocking applies only to published agents. |
| quarantinedAt | `properties.quarantinedAt` | datetime | Preview | Last quarantine time. |
| isManaged | `properties.isManaged` | boolean | Preview | True when the agent is part of a managed Dataverse solution. Null for Agent Builder agents. |
| botId | `properties.botId` | GUID | GA | The CDS bot ID, the same value as the agent ID. |
| entraAppId | `properties.entraAppId` | GUID | GA | Legacy app registration. Agents created before the Entra Agent ID rollout carry this until Microsoft or an admin migrates them. The rollout began in May 2026 and the environment-level opt-out ended in July 2026, so a remaining app registration is migration backlog, not a choice. |
| entraAgentId | `properties.entraAgentId` | GUID | GA | Microsoft Entra Agent ID: a service principal with the Agent subtype. Standard harness agents get one at creation; GitHub Copilot harness agents at first publish; Copilot Chat harness timing is not documented. Connector scopes are attached to it at publish, and Conditional Access can target those scopes, enforced today only when the agent runs in Teams. |
| entraAgentBlueprintId | `properties.entraAgentBlueprintId` | GUID | GA | Blueprint that created the identity. Copilot Studio's global blueprint ID is `25664c89-cea5-4ab6-b924-a54fd8a19ae0`. |
| orchestration | `properties.orchestration` | string | Preview | `Classic` (authored topics) or `Generative`. |
| model | `properties.model` | string | Preview | Primary model, for example `gpt-4o` or `gpt-4.1`. Microsoft's sample harness query treats `Microsoft 365 Copilot` here as the Copilot Chat harness. |
| authentication | `properties.authentication` | string | Preview | `None`, `Microsoft Entra`, or `Generic OAuth 2.0`. None means the agent does not sign users in and anyone with the link can chat. Microsoft documents the Teams and Microsoft 365 Copilot channel as requiring Authenticate with Microsoft and blocked otherwise, so None together with that channel is a configuration to verify, not evidence of channel-level protection. |
| channels | `properties.channels` | array | Preview | Display names of channels the agent is published to. Documented example: `["Teams","SharePoint"]`; other names seen in practice include `Microsoft 365 Copilot`, `Custom website`, `Demo website`, `Telephony`. |
| sharedWithViewers | `properties.sharedWithViewers` | object | Preview | `userCount`, `groupCount`, `entireTenant`. The entireTenant flag is set when the maker shared with the whole tenant, even if an admin has not approved a related store submission. |
| sharedWithEditors | `properties.sharedWithEditors` | object | Preview | `userCount`, `groupCount` of people who can edit, configure, share, and publish. |
| capabilitiesCounts | `properties.capabilitiesCounts` | object | Preview | Distinct counts per capability type, for example `distinctPowerPlatformConnectors` and `distinctPowerPlatformConnectorsOperations`. Compare against the 200-item cap below. |
| powerPlatformConnectors | `properties.powerPlatformConnectors` | array | Preview | Connectors the published agent uses, with per-operation detail (next table). The report calls that detail `connectorOperations` in Field coverage and Rules not evaluated. Admin center CSVs flatten it to connector names. |
| isWebSearchEnabledForKnowledge | `properties.IsWebSearchEnabledForKnowledge` | boolean | Preview | True when web search is a knowledge source. |

## Connector operation fields

Each entry of `powerPlatformConnectors` has a `connectorId` (for example `shared_sharepointonline`) and an `operations` array:

| Field | Values | Meaning |
| --- | --- | --- |
| operationId | string | The connector operation, for example `GetItems`. Connectors bound as data sources emit an empty operations array (documented for apps; expect the same for agents). |
| usedAs | `Tool`, `Topic Tool`, `Knowledge` | How the agent uses the operation. |
| isEnabled | boolean | Whether the operation is currently enabled. |
| whenCanBeUsed | `Anytime`, `ViaDirectReferenceOnly`, `Conditional` | Whether the orchestrator may call it freely, only from a topic that references it, or under maker-defined logic. |
| requiresEndUserConsent | boolean | Whether the user must consent before the operation runs. |
| connectionProvider | `User`, `Maker` | Who supplies credentials: the end user at runtime, or the maker at authoring time (Copilot Studio labels this agent author authentication or maker-provided credentials). A maker-provided connection means every user acts with the maker's permissions for that operation. |
| connectionIdSharedByMaker | GUID | The maker's connection, only when `connectionProvider` is Maker. The same ID across agents means one shared credential. |
| createdBy | object ID | Who configured the operation. |

Custom connector IDs are not documented by Microsoft; observed IDs look like `shared_my-20connector-5f0027f520b23e81c1-5f9888a90360086012` (`shared_`, an escaped display name, and a hex suffix). The script's custom-connector test is a heuristic on that shape; the `--watch-connectors` list or the tenant's `microsoft.powerplatformconnector/connectors` records are the authoritative check.

Connector scopes on the Entra Agent ID cover first-party and certified Power Platform connectors only. Custom connectors, MCP servers, and REST API tools do not add API permissions to the identity.

## Environment records

Type `microsoft.powerplatform/environments`: `name` is the environment ID, `properties.displayName` the name, `properties.environmentType` one of Production, Default, Sandbox, Trial, Developer, Dataverse for Teams, `properties.isManaged` whether it is a managed environment, `properties.environmentGroup` its group. The admin center's default inventory query joins `environmentName`, `environmentType`, `environmentRegion`, and `isManagedEnvironment` straight onto each resource row; the script reads those columns too.

## Limits of the inventory

- It describes the **published** version of each agent. Draft edits are invisible until published.
- Classic chatbots (V1, Power Virtual Agents) are not included.
- At most **200 resources of each type per agent** are listed; beyond that the list is a random subset. Use `capabilitiesCounts` to detect truncation.
- In GCC and GCC High only Standard-harness agents appear; GitHub Copilot harness, Copilot Chat harness, and Agent Builder agents do not. In DoD no agents or agent flows appear. Connector inventory is unavailable in GCC, GCC High, and DoD, and the inventory is not available at all in 21Vianet or air-gapped clouds.
- **Modified on** and **Last modified by** do not work for agents.
- Not in the inventory at all: topics, instructions, knowledge sources other than connectors and web search, DLP evaluation results, usage and conversation analytics, Copilot Credits consumption, Conditional Access policy state, sponsors or owners on the Entra identity, whether Agent 365 is enabled, and who actually uses the agent.
