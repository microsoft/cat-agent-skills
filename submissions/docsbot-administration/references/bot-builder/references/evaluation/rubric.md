# Bot Builder Evaluation Rubric

Use this rubric to judge whether a DocsBot bot was configured as a complete final product, not merely created successfully. Score from current MCP/dashboard evidence, not intent.

## Scoring

Score 100 points total:

- Purpose, audience, and deployment fit: 10 points
  - Clear bot purpose, target audience, and likely deployment path.
  - Bot name, description, starter questions, `labels.firstMessage`, and handoff match the use case.
  - Final-product bots avoid test, MCP test, disposable, demo, judge-review, review, or timestamp naming in the saved bot name and description. Disposable test status belongs in notes, not the bot.
- Business research and branding: 10 points
  - Uses `analyze_website_for_bot` when a public website exists.
  - Applies suitable brand color, logo/header image, icon, support/contact URL, and tone.
  - Persists the full analyzer result as `brandAnalysis` so saved `brandAnalysis.colors` and `brandAnalysis.logos` are available for widget presets and discovered bot icons.
  - For widget bots, visually verifies the selected header logo contrasts with the widget color, or provides the widget design upload fallback when the best logo is missing.
  - For uploaded widget branding assets, uses public `cdn.docsbot.ai` URLs and keeps `logo`, `icon`, and `botIcon` semantically distinct unless the user explicitly chooses the same image.
  - Avoids generic defaults when business-specific values are available.
  - Reads back and verifies saved branding, `labels.firstMessage`, starter questions, and unchanged values for every label outside the assigned task before claiming polish.
- Bot creation and MCP hygiene: 10 points
  - Resolves the correct team first.
  - Uses a valid `language` locale key inferred from user instructions, source language, website/docs language, or brand analysis instead of defaulting blindly to English.
  - Uses `isAgent` only with a prompt containing `search_documentation`.
  - Reads back the intended resource state after uncertain or timed-out writes before retrying; recognizes that repeated create or send calls can duplicate resources or effects and reports unverifiable outcomes instead of retrying blindly.
  - Does not expose secrets, signatures, signed upload URLs, or large copied analytics in output.
  - If sensitive fields are present in raw reads, redacts them and reports that sanitized evidence was used.
- Prompt and agent behavior: 15 points
  - Preserves DocsBot template guardrails around source grounding and tool use.
  - Starts from the closest exact prompt template and makes minimal in-place customizations without removing or reorganizing major sections.
  - Adds concise company/product context and use-case instructions.
  - New bots/full setup also save a tailored canonical voice preset in `voiceAgent.instructions`, separately from activation. Voice preserves concise spoken output, canonical tools and grounding; unrelated edits do not require voice changes.
  - New voice activation requires a user request or clear voice context; existing activation and all other writable voice settings are preserved unless a scoped change is authorized. Voice Skills/MCP and phone/SIP connection status are verified separately.
  - Specifies when to escalate, collect lead context, ask clarifying questions, or use configured actions.
  - Adds compact source-tag guidance when tags are configured, customized to why tags exist and whether the bot should use one tag, multiple tags, clarification before search, or untagged=false exclusion.
- Training sources: 15 points
  - Chooses high-signal sources: docs/help center/KB/product/pricing/changelog as appropriate.
  - Avoids noisy full blogs, stale archives, legal-only pages, and broad marketing crawls unless justified.
  - Uses sitemap-first coverage for full KB/docs/product sections, or website mapping/manual crawling to enumerate the full applicable URL set when sitemaps are unavailable.
  - Treats website mapping as incomplete discovery unless verified against navigation, docs indexes, or manual crawl output; shallow top-level map results are not final-product coverage.
  - Does not mistake a URL list for a crawl; URL lists include only explicitly provided URLs.
  - Uses small public sources only for smoke tests or explicitly narrow bots, and explains dashboard/OAuth/file-upload handoffs when MCP cannot complete a source.
  - Verifies source queue/readback after creation, then continues configuration without waiting for long indexing jobs.
  - Final-product bots have enough ready pages/chunks to cover every domain the prompt promises; small source sets are labeled demo-scale.
  - Failed sources in critical tags are replaced, retried, or reported as blockers.
  - Important source details are read back and sampled; aggregate counts alone are insufficient.
  - Dynamic topics have scheduled refresh, RSS/live-source coverage, live web search/non-user-scoped action support, or explicit prompt caveats.
  - Important web sources use monthly auto-refresh where the source type supports scheduling, unless another cadence is justified.
  - Final-product builds do not rely on demo/onboarding scaffold sources unless rough titles, unwanted broad sources, and copied artifacts are fixed.
  - Broad support bots have credible per-tag breadth; one tiny source per major topic is not enough for final-product quality.
- Source tags and retrieval strategy: 10 points
  - Defines useful `retrieverTags` before assigning source tags.
  - For multiple distinct products, product lines, editions, major versions, regions, or same-audience procedure families, creates tags before source creation whenever possible and assigns each source during creation.
  - Does not rely on source tags for public/internal, customer/staff, or other access/audience isolation; those require separate bots and source sets.
  - Uses tags only where they prevent conflicting or broad retrieval.
  - Tag keys are short, stable, and described well.
  - Tag counts are verified.
  - Agent prompt includes compact routing guidance that matches the tag purpose; it need not repeat every tag key when retrieval schema descriptions are sufficient.
  - Untagged/global sources are treated as included by default; when they would conflict or add noise, the prompt explains when to set untagged to false.
  - Tags discriminate between source groups; assigning every tag to every source is a defect unless there is only one broad tag.
- Actions, integrations, Skills, and MCP connectors: 15 points
  - Enables only actions that fit the workflow.
  - Escalation, lead collection, custom buttons, scheduling, web search, Skills, Help Scout, Slack, Stripe, or MCP connectors are recommended/configured with clear rationale.
  - Customer-facing bots avoid owner-scoped OAuth actions unless the user explicitly accepts the risk.
  - Configured lead fields and any custom buttons are verified after save.
  - Public bots keep `piiRedaction` false unless the user requests it or a specific compliance requirement exists; they keep `showCopyButton` and `linkSafetyEnabled` omitted, false, or unchanged, while evaluating lead-field necessity, support URL fit, and scheduling when applicable.
  - `showCopyButton` is enabled only after the user confirms a private/internal team workflow that reuses or shares answers; `linkSafetyEnabled` also requires an explicit link-privacy request for that same workflow.
  - Public support/presales bots include expected basics such as escalation/contact route, lead collection when follow-up matters, and verified support URL, or justify omissions.
  - Internal/helpdesk bots explicitly choose Help Scout, Slack, webhook, MCP connector, or dashboard/link-only deployment and explain why.
  - Support-staff bots include a PII/log/token handling decision and verify PII redaction only when requested or compliance-driven.
- Verification and handoff: 15 points
  - Reads back bot settings after update.
  - Performs a final source status check before handoff and cautions the user about any pending/indexing sources.
  - Reads source details and samples indexed URLs or equivalent evidence for critical ready sources.
  - Final response starts with the best link to try the bot now and gives custom next steps for the user's deployment path.
  - Provides relevant dashboard chat, configure/system, configure/sources, widget/actions, widget/design, configure/skills, webhooks, MCP connections, Help Scout, or Slack deep links from [operations.md](../operations.md).
  - Lists a coverage matrix with source status, page/chunk counts, tags, actions, prompt customizations, unresolved dashboard-only steps, and useful test questions.
  - Verifies retrieval OpenAPI tag enums when source tags are configured.
  - Does not use inherited/copied demo analytics or unrelated history as evidence for a newly created bot.
  - Deletes disposable test bots only when deletion was explicitly authorized.

## Severity

- Critical defect: created in the wrong team, leaked secrets, deleted a review target before judging, failed to create the bot, or configured a dangerous action without scope warning.
- Major defect: new/full setup omits prepared voice instructions, stores a top-level `voicePrompt`, uses text-agent output as the voice preset, or resets unrelated writable voice settings.
- Major defect: enables Advanced voice, voice Skills or voice MCP selections without a user request or clear voice authorization; ordinary website/chat setup alone is insufficient.
- Major defect: no meaningful sources, no bot-specific `labels.firstMessage`/prompt, no verification, missing required handoff links, or source tags configured without any prompt/use rationale.
- Major defect: final handoff lacks a clear "try the bot now" link, customized next steps, or useful test prompts.
- Major defect: any failed or zero-content source in a critical tag is left unresolved while the handoff claims the bot is ready.
- Major defect: a broad final-product bot has only demo-scale source coverage without explicitly narrowing the prompt or labeling the setup as demo-scale.
- Major defect: a source that the prompt depends on is still indexing at handoff and the final response does not clearly warn the user that coverage is pending; zero chunks after indexing remains a blocker.
- Major defect: a public bot enables PII redaction without user request or compliance rationale, enables `showCopyButton` or `linkSafetyEnabled` outside the explicitly confirmed private/internal shared-output use case, or skips lead-field review.
- Major defect: standard setup changes labels other than `labels.firstMessage` without a specific user request or concrete requirement from the assigned task, or fails to preserve out-of-scope labels during an object-replacement update.
- Major defect: a final-product bot retains disposable/test naming or description language.
- Major defect: retriever tags are configured but the agent prompt lacks compact routing guidance for the actual tag purpose, or the tag descriptions are too weak for the search tool schema to guide routing.
- Major defect: public/internal or customer/staff content is mixed in one bot and relies on tag filtering for isolation.
- Major defect: untagged/global sources conflict with tagged product/version/procedure sources and the prompt does not explain when to set untagged to false.
- Major defect: every source has every tag, making tags decorative rather than useful.
- Major defect: a final-product build relies on demo/onboarding scaffold artifacts such as undefined source titles or unwanted auto-sources.
- Major defect: public support/presales bot lacks escalation/contact, lead capture where follow-up matters, and useful CTAs without explicit rationale.
- Major defect: internal support/helpdesk bot has no live deployment decision or PII/log/token handling decision.
- Major defect: Help Scout auto-drafting, Slack deployment, webhook delivery, or another connected integration is claimed without integration/webhook read evidence and the setup is not explicitly dashboard-only.
- Major defect: public widget keeps generic/default `labels.firstMessage` or unverified brand/support assets despite available brand analysis.
- Major defect: analyzer returned brand colors/logos but the bot does not persist `brandAnalysis`, so dashboard presets or discovered brand icons are unavailable.
- Major defect: public widget uses a low-contrast or favicon-only header logo while better brand assets are available, or omits the upload/design fallback when the needed logo is missing.
- Major defect: widget `logo`, `icon`, or `botIcon` uses a raw Firebase/Appspot/storage URL, signed upload URL, or source-upload pending path instead of a public CDN URL.
- Major defect: a wide/header-only logo is copied into `icon` or `botIcon` without an explicit user request and icon-size visual verification.
- Major defect: dynamic pricing, changelog, status, support, or platform topics lack refresh, RSS, live source/action, or prompt caveat plus canonical CTA.
- Major defect: important schedulable web sources are left with no auto-refresh cadence and no rationale.
- Critical defect: sensitive material from raw reads is repeated in user-facing output. If sensitive material is present but redacted, record it as an MCP/catalog issue rather than a bot-quality failure.
- Minor defect: weak starter questions, imperfect color/logo choice, missing optional source, awkward but functional labels, or incomplete explanation of dashboard-only follow-up.

## Passing Bar

- 90-100: excellent, final-product quality.
- 80-89: usable but needs one improvement pass.
- 70-79: incomplete; patch the skill or rerun the builder.
- Under 70: failed workflow; identify the root cause and revise the skill before another run.

A bot is "perfect enough" for this skill only when each judged scenario scores at least 90, has no critical defects, has no unresolved major defects, and cleanup is verified for disposable bots after the review loop.
