# Connector Sources

Read this only when adding Truto-backed, cloud, WordPress, or similar connector sources that may require OAuth, private workspace selection, or dashboard-only file/folder picking.

Many cloud connectors are Truto-backed. MCP may expose the source type, existing integration records, or normalized source records, but it usually cannot complete the user OAuth flow or pick private files/folders for the user.

## Connector Handoff Flow

1. Use `search_tools` only if the connector tool name is unfamiliar, then inspect its advertised schema.
2. Read team/bot integrations when available to see whether the connector is already connected.
3. If no connection exists or item selection cannot be completed through MCP, give the user the dashboard deep link and the exact connector to add:
   `https://docsbot.ai/app/bots/{botId}/configure/sources`
4. Tell the user what to choose after OAuth: workspace/account, folders/files/spaces/projects, and whether to include child pages or attachments if the dashboard offers those options.
5. Explain the recommended scope from your research, for example "select the public product docs folder and the latest API reference folder; skip archived marketing drafts."
6. If the MCP catalog supports connector IDs such as `trutoIntegrationID` and `trutoFiles`, only use values returned by live reads or the user's completed dashboard selection. Do not invent IDs.
7. After the user connects/selects files, read sources again, verify status/counts/tags, and continue the normal readiness audit.

## Handoff Template

Keep dashboard-only handoff wording concrete and minimal:

```text
Connect Google Drive for this bot here:
https://docsbot.ai/app/bots/{botId}/configure/sources

Choose Google Drive, authorize the workspace, then select:
- Customer-facing product docs folder
- Current API reference folder
- Release notes folder

Skip archive, drafts, legal, and internal planning folders. After you connect it, I can verify source status and tune tags/prompt behavior.
```

## Verification

- Re-read the source list after the user connects or selects files.
- Verify source status, counts, tags, selected folders/files, and warnings.
- Do not invent connector IDs, file IDs, workspace IDs, or private paths.
- Treat connector secrets and OAuth state as out-of-band; never print tokens or secret values.
