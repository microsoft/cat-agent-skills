# Admin MCP Operation Reference

Call the named Admin MCP tool directly. Use `search_tools` and `get_tool_schema` only when advertised metadata is needed. The exact schemas can change; this file records stable operation names and field guardrails verified against the DocsBot Admin MCP fixed tool map and local code.

## Entry Points

| Task | Named tool | Notes |
| --- | --- | --- |
| List accessible teams | `list_teams` | First call in most workflows. OAuth identifies a user, not a fixed team. |
| Get team details | `get_team` | Use after choosing `teamId`; responses are sanitized. |
| List bots | `list_bots` | Use to find existing bots and avoid duplicates. |
| Get bot settings | `get_bot` | Read before updating; preserves existing settings and action config. |
| Create bot | `create_bot` | Requires `name`; for agent bots include valid `agentPrompt`. |
| Update bot | `update_bot` | Use minimal bodies containing only intended settings. |
| Delete bot | `delete_bot` | Deletes the bot only. Confirm unless the user already explicitly authorized that exact deletion. |
| List research jobs | `list_research_jobs` | Use the bot's dedicated research route. |
| Get research job | `get_research_job` | Requires the bot and research job IDs. |
| Cancel and remove research job | `cancel_research_job` | Cancels the external task and soft-deletes the stored job. Confirm unless the user already explicitly authorized that exact action. |

## Bot Creation Guardrails

Observed live behavior on 2026-07-03:

- `language` must be the inferred DocsBot locale key for the bot's primary answer language, such as `en`, `es`, or `jp`; do not send natural-language names like `English` or browser locale strings like `en-US` unless the advertised schema explicitly supports them.
- Choose `language` before `create_bot` from user instructions, source/documentation language, website/help-center language, and brand analysis. If those signals conflict, ask before creating the bot instead of defaulting to English.
- Omit `model` during normal bot creation so the API uses the current DocsBot default. Set `model` only when the user explicitly requests a specific supported model or the workflow requires one and you have verified it is allowed by the team plan.
- Omit rate-limit and IP-recording fields during normal bot creation: do not send `rateLimitMessages`, `rateLimitSeconds`, `rateLimitIPAllowlist`, or `recordIP` as `null`, `false`, `0`, empty string, or empty array. The API treats defined values as writes; omitting the keys preserves the default/null state, matching onboarding-style creation.
- `isAgent: true` requires `agentPrompt` during create. The prompt must include the literal string `search_documentation`.
- Default create can enable `human_escalation` and `followup_rating`; inspect the created bot before replacing `tools`.
- Bot create/update responses can include inherited analytics plus bot signature material. Never quote secrets, signature keys, or large history payloads in user-facing output.
- Public bots force `tools.web_search.live` to `false` on update.
- `tools.customButtons[]` entries must include `enabled`, `name`, `functionKey`, `instructions`, `buttonText`, `icon`, and `url`; saved function keys do not include the internal `button_` prefix.
- `leadCollect.mode` must be `before_response` or `before_escalation`; field keys must be unique. Standard+ supports custom fields beyond `name` and `email`.
- `leadCollect.fields[].options` for select fields may be normalized on save; verify saved option labels before handoff and prefer simple option labels when exact spacing matters.

Good create skeleton:

```json
{
  "name": "Acme Support Bot",
  "description": "Answers product and support questions for Acme customers.",
  "privacy": "public",
  "language": "en",
  "region": "US",
  "isAgent": true,
  "agentPrompt": "<closest exact prompt asset with placeholders filled and minimal additions>"
}
```

Onboarding-style create shape intentionally does not include `rateLimitMessages`, `rateLimitSeconds`, `rateLimitIPAllowlist`, `recordIP`, `allowedDomains`, or similar safety/limit toggles. Configure those later only when the user explicitly asks or the deployment has a concrete requirement, and then verify the saved bot read.

For final-product builds, use `create_bot` plus explicit follow-up updates. Do not invoke adjacent demo-bot skills, public demo/pilot endpoints, or onboarding bot creation endpoints as the primary build path; those can create scaffolded source titles, broad auto-sources, copied demo analytics, or disposable naming. If an onboarding/demo endpoint is used only to inspect suggested branding or source ideas, clean up all scaffold artifacts before handoff: rename/delete rough sources, assign all tags, remove demo/test naming, and clearly identify any source still pending/indexing in the final handoff.

## Compact Field Map

Use this to map skill language to common `update_bot` and source fields. Inspect the advertised named tool schema before unusual writes.

| Skill concept | Field(s) |
| --- | --- |
| Public/private bot | `privacy: "public"` or `"private"` |
| Agent mode | `isAgent: true`, `agentPrompt` containing `search_documentation` |
| Locale/language | `language` locale key inferred before creation, such as `en`, `es`, `jp`; verify advertised schema support for uncommon locales |
| Brand color/logo/header | `color`, `logo`, `icon`, `botIcon`, `headerAlignment`, `brandAnalysis` |
| First message/starter questions/labels | `labels.firstMessage` is the only label changed during standard production setup. Change `labels.floatingButton` or another `labels.*` field only when the user asks or the specific assigned task requires it; otherwise omit or preserve it. |
| Support/contact route | `supportLink`; helpdesk widget handoff uses embed `supportCallback` outside MCP |
| Response sharing/link privacy | `showCopyButton`, `linkSafetyEnabled`; omit or preserve by default. Enable only when the user explicitly confirms a private/internal team workflow that will reuse or share answer output; for `linkSafetyEnabled`, also require an explicit link-privacy request. |
| Public safety | `piiRedaction`, `recordIP`, `imageUploads`, `audioUploads`, `allowedDomains`; omit from initial create unless explicitly configuring |
| Retrieval tags | `retrieverTags: [{ key, description }]`, source `tags: ["key"]` |
| Source freshness | source `scheduleInterval` as `monthly`, `weekly`, `daily`, or `none` when supported |
| Lead form | `leadCollect`, `labels.leadCollectMessage` |
| Human escalation/follow-up rating | `tools.human_escalation`, `tools.followup_rating` |
| Scheduling tools | `tools.calendly`, `tools.calcom`, `tools.tidycal` with `{ enabled, instructions, url }` |
| Custom buttons | `tools.customButtons[]` with `{ enabled, name, functionKey, instructions, buttonText, icon, url }` |
| Web search | `tools.web_search` with `{ enabled, live, allowed_domains }` |
| Stripe customer billing | `tools.stripe` with `recent_billing`, `billing_portal`, `refund`, `cancellation` subkeys |
| External MCP servers | `mcpServers[]` with `serverLabel`, `serverUrl`, `serverDescription`, `enabled`, `tools`, optional auth/header fields |
| Help Scout prompt | `helpscoutPrompt` |
| Voice prompt (`voicePrompt` channel) | `voiceAgent.instructions`; never a top-level `voicePrompt` field. See [deployment/voice.md](deployment/voice.md) for preserving the complete writable voice object. |
| Advanced voice activation | `voiceAgent.enabled`; new/full setup prepares the prompt but activation requires a user request or clear voice context. Existing state is preserved unless a change is authorized. |

Preserve existing `tools`, `mcpServers`, `labels`, and `retrieverTags` entries when updating one part of the bot. Read the complete saved labels before a label update and change only `labels.firstMessage` plus labels specifically requested or required by the assigned task. If the API replaces the object, send the full saved labels object with only those scoped changes.

## Branding And Onboarding

| Task | Named tool | Notes |
| --- | --- | --- |
| Analyze website | `analyze_website_for_bot` | Takes `siteURL`; returns suggested bot config, brand colors/logos, screenshot, language, support/widget hints. Does not create a bot. |
| Draft prompt | `draft_bot_prompt` | Use `activeTab: "agent"` for agent prompts. Review before persisting with bot update. |
| Debug prompt | `debug_bot_prompt` | Use when current behavior is off; persist accepted edits with bot update. |
| Bot image upload URL | `create_bot_image_upload_url` | Signed upload URL plus public `cdnUrl` for widget `logo`, `icon`, or `botIcon` images. Upload bytes to `uploadUrl`, then save `cdnUrl` in bot settings. |
| Suggest source tag | `suggest_source_tags` | Drafts tag key/description; save accepted tags through bot update. |
| Draft custom button | `draft_custom_button` | Drafts metadata only; add `url` before saving in `tools.customButtons`. |

After `analyze_website_for_bot`, persist the returned analysis into bot create/update as `brandAnalysis: { domain, url, ...analysisResult }` along with selected `color`, `logo`, `widgetType`, and `supportLink`. Saved `brandAnalysis.colors` and `brandAnalysis.logos` power dashboard brand presets and discovered bot icons; omitting the field is a configuration defect. If the named tool schema or call rejects `brandAnalysis`, flag the Admin MCP/API mismatch and use dashboard/onboarding or propose a helper endpoint rather than dropping the field.

## Sources

| Task | Named tool | Notes |
| --- | --- | --- |
| Add source | `create_source` | URL/file/website/sitemap/RSS/Q&A/cloud connector source creation. |
| List sources | `list_sources` | Supports pagination and tag filters. |
| Get source | `get_source` | Inspect status and normalized fields. |
| Count source status | `count_sources` | Useful after queuing ingest. |
| Count source tags | `count_source_tags` | Confirms tag assignment totals. |
| Map website URLs | `map_website_urls` | Discovers candidate URLs before website source creation; usually finds quickly accessible top-level/obvious links, not every URL. Prefer sitemaps for complete docs/KB/product coverage. Observed source create needs root `url` plus selected `urls`. |
| Bulk update source tags | `set_source_tags` | `sourceIds`, plus `set` or `add`/`remove`; max 100 source IDs. |
| Signed file upload URL | `create_source_upload_url` | MCP cannot upload bytes; upload with HTTP PUT, then create a single-file document source using returned `file`, or derive a shared pending batch prefix for multi-file `fileDir`. |
| Draft source title | `draft_source_title` | Optional helper for naming uploaded multi-file batches from filenames. |
| Rename source label | `update_source_title` | Dashboard label only for supported source types. |
| Retry failed ingest | `retry_failed_source` | Only for failed sources, not general editing. |
| Reingest source | `reingest_source` | Queues reingest where source type/status allows. |
| Schedule refresh | `set_source_refresh_schedule` | Sets `scheduleInterval`, including `none`. Important web sources should default to monthly refresh when scheduling is supported. |
| Download source archive | `get_source_download_url` | Signed download URL for source archive; use only when export/download is requested. |
| Download source file | `get_source_file_download_url` | Signed URL for one source file; do not print signed URLs unless user explicitly needs the download link. |
| Export Q&A source | `export_qa_source` | Exports Q&A source content. |
| Delete source | `delete_source` | Source must be ready/failed, not indexing. |

If a source cannot be renamed and has a scaffold title such as `undefined Website` or `undefined Sitemap`, replace it with an explicitly named source. If a broad scaffold sitemap is still indexing, do not build final-product scope around it; narrow the prompt or replace it with curated ready sources.

`create_source_upload_url` is for source files only. Do not use its returned signed URL, `file`, or `user/{userId}/team/{teamId}/bot/{botId}/...` path for widget `logo`, `icon`, or `botIcon` settings. Use `create_bot_image_upload_url` for widget branding image uploads; see [branding/widget.md](branding/widget.md).

Source tags are two-step:

1. Define bot vocabulary with `retrieverTags` on `update_bot`.
2. Assign keys on source create via `tags`, or later through `set_source_tags`.

Prefer defining tags before source creation when products, editions, major versions, regions, or same-audience procedure families differ. This lets each sitemap, website, URL-list, document, or connector source carry the correct `tags` value from creation instead of requiring repair later. Do not use tags for public/internal or customer/staff isolation; create separate bots and source sets instead.

## Integrations, Actions, MCP, Skills

| Task | Named tool | Notes |
| --- | --- | --- |
| List team integrations | `list_team_integrations` | Read before connect/configure. Use `type=helpscout` or `type=slack` when relevant. |
| Connect/reconnect Help Scout | Dashboard OAuth/configuration flow | The hosted named-tool catalog does not advertise a general integration credential write. |
| Configure Help Scout | `configure_helpscout_integration` | Assign tags/mailboxes to bots; set note/save/publish behavior. |
| Refresh Help Scout | `refresh_helpscout_metadata` | Poll/list after refresh. |
| Slack authorize URL | `get_slack_authorization_url` | User must complete OAuth outside Admin MCP. |
| Read Slack workspaces | `get_slack_integration` | Returns sanitized workspace routing and bot/channel mappings. |
| Update Slack routing | `update_slack_routing` | Sets `defaultBotId`, `channelBotMap`, and `adminsOnly` per workspace. |
| Disconnect Slack workspace | `disconnect_slack_workspace` | Requires `slackTeamId`; destructive integration change, confirm first outside disposable tests. |
| List Slack bot mapping | `list_slack_bots` | Use before selecting bot for Slack. |
| List bot webhooks | `list_webhooks` | Read configured outgoing subscriptions before create/update/test. |
| Create bot webhook | `create_webhook` | Supports `lead.created`, `conversation.escalated`, `conversation.rated`, and `deep_research.done`. |
| Get bot webhook | `get_webhook` | Verify a specific webhook by id. |
| Update bot webhook | `update_webhook` | Update label, status, target URL, events, or expiration. |
| Delete bot webhook | `delete_webhook` | Destructive; confirm before deleting non-test hooks. |
| Preview webhook payloads | `list_webhook_samples` | Returns sample payloads without delivery. |
| Test lead webhook | `send_test_lead_webhook` | Sends sample or selected lead payload. |
| Test escalation webhook | `send_test_escalation_webhook` | Sends `conversation.escalated` sample payload. |
| Test rating webhook | `send_test_rated_webhook` | Sends `conversation.rated` sample payload. |
| Test research webhook | `send_test_research_webhook` | Sends `deep_research.done` sample payload. |
| Start bot Stripe OAuth | Dashboard flow | The hosted named-tool catalog does not advertise this operation. |
| Discover external MCP tools | `discover_external_mcp_tools` | Use when the server is reachable or discovery supports the auth mode. If OAuth or private credentials are required, user must connect/authorize in dashboard. |
| Draft MCP metadata | `draft_mcp_server` | Draft safe server metadata and tool selection before saving in `mcpServers` with bot update. |
| List bot skills | `list_skill_drafts` | Includes missing bindings and enablement state. |
| Search library skills | `list_library_skills` | Search by vendor/task keywords. |
| Import library skill | `import_library_skill` | Creates a bot draft from a global library skill. |
| Read published skill settings | `get_skill_settings` | Secret values are never returned. |
| Configure published skill | `configure_published_skill` | Operational settings only: `enabledWidget`, declared env/secret bindings. |
| Read worker logs | `get_skill_runtime_logs` | Useful after enabling a skill. |

Admin MCP may expose broader skill authoring operations, but for normal bot setup prefer library import plus published skill settings. Do not create or edit arbitrary skill source files unless the user explicitly asks to build a new DocsBot Skill.

## Verification, Tuning, And Access

Use `get_tool_schema` if filters or payloads are unclear:

| Task | Named tool | Notes |
| --- | --- | --- |
| Retrieval OpenAPI | `get_bot_retrieval_openapi` | Verify search schema and source-tag enums for external retrieval handoff. |
| Test semantic retrieval | `search_bot_knowledge` | Search bot knowledge with optional tags; catalog marks this write-like, so use only when verification is authorized. |
| List question logs | `list_questions` | Use for behavior tuning; do not treat inherited demo logs as evidence. |
| Search question logs | `search_question_logs` | Semantic search over historical questions. |
| Update saved answer | `mark_question_revised` | Writes curated Q&A/answer feedback; confirm before changing real bot history. |
| List conversations | `list_conversations` | Use for escalation/lead/chat behavior diagnostics. |
| Get conversation | `get_conversation` | Full transcript details. |
| List leads | `list_leads` | Verify lead capture after tests. |
| Export leads | `export_leads` | Returns signed CSV URL; use only when requested. |
| Delete lead | `delete_lead` | Destructive privacy cleanup. Confirm unless disposable test data. |
| Bot stats/reports | `get_bot_stats`, `get_monthly_report` | Diagnostics only; avoid inherited demo analytics as quality proof. |
| Team members | `list_team_members` | Resolve members/invites before access changes. |
| Invite member | `invite_team_member` | Invite or bot-scoped access; write action, confirm first. |
| Update team member | `change_team_member_role` | Role change; write action, confirm first. |
| Bot member override | `set_bot_member_role` | Per-bot role override; verify with bot/member reads. |

DocsBot account subscription and commerce mutations are outside this plugin. Read account usage only through an advertised read tool.

## Useful Deep Links

Use these in handoff once `botId` is known:

- Dashboard chat: `https://docsbot.ai/app/bots/{botId}/chat`
- Bot system settings: `https://docsbot.ai/app/bots/{botId}/configure/system`
- Agent instructions: `https://docsbot.ai/app/bots/{botId}/configure/instructions`
- Sources: `https://docsbot.ai/app/bots/{botId}/configure/sources`
- Widget actions: `https://docsbot.ai/app/bots/{botId}/widget/actions`
- Widget design: `https://docsbot.ai/app/bots/{botId}/widget/design`
- Skills: `https://docsbot.ai/app/bots/{botId}/configure/skills`
- Webhooks: `https://docsbot.ai/app/bots/{botId}/configure/webhooks`
- MCP connections: `https://docsbot.ai/app/bots/{botId}/configure/mcp-connections`
- Help Scout integration: `https://docsbot.ai/app/api#helpscout-integration`
- Slack integration: `https://docsbot.ai/app/api#slack-settings`
- Public share/demo pattern: inspect current dashboard routes or bot response before promising a share URL; do not invent a URL if unsure.
