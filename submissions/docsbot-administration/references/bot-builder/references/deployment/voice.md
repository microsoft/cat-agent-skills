# Voice Preparation And Deployment

Read this for new bot/full setup, voice instructions, Advanced voice activation, or phone/SIP deployment. An unrelated source, branding or administration edit does not require voice changes.

## Prepare Separately From Enabling

During new bot/full setup, prepare a business-specific voice prompt from the closest expanded canonical asset:

- [voice-support.md](../../assets/prompts/voice-support.md): runtime default, troubleshooting and customer support.
- [voice-receptionist.md](../../assets/prompts/voice-receptionist.md): greeting, common inquiries and routing.
- [voice-sales.md](../../assets/prompts/voice-sales.md): inbound qualification and grounded next steps.

These preserve the exact structure of `VOICE_INSTRUCTION_PRESETS` in `src/lib/voiceAgent.js`, including the expanded shared tool/knowledge and role/safety blocks. Replace `{business_name}`, `{product_info}`, and `{language}` with verified business context, concise product scope and the caller's default spoken language. Keep canonical tool names, skill-first priority, documentation grounding, short spoken turns, barge-in behavior and one-question clarification. Add only relevant tag routing and actually available action guidance. Do not reuse the verbose Markdown-oriented chat prompt.

The logical `voicePrompt` channel is persisted as `voiceAgent.instructions` through `create_bot` or `update_bot`. It is not a top-level `voicePrompt` property. `draft_bot_prompt` supports agent/default tabs and cannot draft voice; do not call it with a voice tab.

For a new bot, save prepared instructions with `voiceAgent.enabled: false` unless the user has requested voice or clear context authorizes a phone agent/voice assistant. Ordinary website support, chat, branding or sales-bot setup alone does not authorize Advanced voice. An explicit voice request already authorizes activation within that scope; do not ask for duplicate confirmation. For an existing bot, preserve its current enabled state unless the user requests a change. A prompt save and an activation change are separate decisions, even if an authorized payload includes both.

## Safe Voice Object Writes

A `voiceAgent` update is normalized as a complete configuration: omitted properties can reset to defaults. A minimal `{ instructions: ... }` patch is unsafe, and `{ enabled: false, instructions: ... }` alone is invalid because disabled configurations still require a valid model, voice and `maxCallDurationSeconds`.

1. Inspect `get_tool_schema` for the current `create_bot`/`update_bot` writable `voiceAgent` fields and enum/default values. Use the live schema and current runtime over hard-coded model choices.
2. For an existing bot, obtain a fresh `get_bot` immediately before constructing the write. Copy its complete current voice configuration, retaining only fields accepted by the write schema, recursively where necessary. Change `instructions` and only other settings authorized by the task. Preserve `enabled`, model, voice, greeting, limits, disclosure, transfer configuration/availability, lead collection, web-search settings and `mcpServerIds` as applicable.
3. Omit response-only fields such as `routingMode`, `phoneNumbers`, `sipAliases`, `directSipDestinations` and call/status metadata from the bot write. Existing route assignments are preserved by their dedicated APIs; do not clear or reassign them while saving a prompt.
4. For a new bot or absent voice configuration, start from current runtime defaults filtered to the write schema. `createDefaultVoiceAgent()` currently uses the first supported model/voice, a 900-second maximum, disabled transfer/lead collection/web search, no MCP selections and disabled disclosure. Do not universally pin a model ID; resolve the current valid options. Save the tailored instructions with `enabled: false` unless activation is authorized. Do not enable actions while filling required fields.
5. Read back with `get_bot`: verify exact instructions, enabled state and equality of all out-of-scope writable settings. If validation reports a stale selected MCP server or unsupported saved value, resolve within the authorized scope or report the specific blocker; do not silently drop the setting to make the write succeed.

Do not echo credentials, custom headers, signatures, phone/SIP connection secrets or raw call metadata into the handoff.

## Voice Actions And Connections

Enabling a text Skill or connecting a bot MCP server does not authorize using it in voice calls. `enabledVoice` on a Skill and `voiceAgent.mcpServerIds` select voice exposure; change them only within an explicit voice request or clear voice context covering those actions. Preserve existing selections during instruction edits. Verify connected server IDs and actual voice tool availability before promising an action. Add concise usage guidance only for actions available to this caller and surface.

Transfer targets, availability, lead collection and web search remain separate scoped settings. Do not infer permission for new customer-facing actions merely from preparing instructions. Preserve existing values; configure changes when the voice request authorizes them.

Phone-number/SIP assignment is separate from bot creation and prompt activation. Use the current advertised dedicated operations or dashboard to connect the requested route. Claim phone/SIP availability only from verified connection/routing evidence. Do not place calls just to verify saved settings unless a call test is authorized. Browser/widget live voice also needs the appropriate saved Advanced voice setting and browser microphone support; a prepared prompt alone does not establish a working widget call.

## Handoff And Checks

- Voice settings: `https://docsbot.ai/app/bots/{botId}/voice`
- Phone/SIP settings: `https://docsbot.ai/app/bots/{botId}/voice/phone`

Report prepared instructions, enabled/disabled Advanced voice, and connected/unconnected routes as distinct states. When preparation alone was authorized, “voice prompt prepared; Advanced voice disabled” is complete; activation is optional, not an unfinished required step. If voice deployment was requested, name any remaining connection or authorized test step and provide the relevant dashboard link.

For an authorized voice test, use a normal business question, unsupported pricing/policy question, short clarification exchange, caller interruption, and the configured escalation or qualification path. Check that answers are spoken briefly and only supported by available tool results; do not treat a text chat test as evidence of an actual call.
