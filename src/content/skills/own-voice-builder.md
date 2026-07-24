---
name: Own Voice Builder
description: "Mines your sent emails to extract your real writing voice — languages, tone modes, structure, vocabulary, taboo phrases — and generates a personal voice skill that makes every email and Teams draft sound like you."
agentDescription: "Analyze the user's own sent emails to build a personal writing-voice profile and generate a reusable personal voice skill from it. Use this skill whenever the user asks to analyze their writing style, learn their tone of voice, create/build/update a personal voice skill or \"own voice\" profile, make drafts \"sound like me\", or makes an equivalent request in any other language. Also use it when the user complains that generated emails or Teams messages don't sound like them and no personal voice skill exists yet."
platforms: [Cowork, Scout]
tags: [writing, voice, email, teams, productivity, microsoft-365]
author: Marcel
authorUrl: "https://github.com/marcelhuszar"
authorGithub: marcelhuszar
version: 1.0.0
---
# Own Voice Builder

Follow the phases below to analyze the user's sent emails and generate (or update) a personal voice skill (default name: `<firstname>-voice`).

## Phase 0 — Setup questions (keep it short)

Ask the user, in one message, only what you cannot infer:

1. **Time window**: How far back to analyze (default: last 12 months).
2. **Exclusions**: Any recipients, domains, or topics to skip (e.g. HR, legal, personal contacts).
3. **Skill name**: Default `<firstname>-voice`; confirm the first name.

If the user already stated any of these in the conversation, do not re-ask. Check the user's existing memories/preferences for style rules (e.g. "no em-dashes", "never start with 'I hope this finds you well'") — these become **hard rules** in the generated skill, no exceptions.

## Phase 1 — Sample & analyze sent mail

**Sampling (do this in parallel where the harness allows):**

- Use the mail tool available in this harness (e.g. `m365_list_emails` with `folder="sent"`) to pull **100–150 sent emails**, stratified across the whole time window in 4–6 time buckets so the sample isn't biased toward recent weeks.
- Retrieve `subject`, `toRecipients`, `sentDateTime`, `bodyPreview`, and full `body` where needed.
- Classify each message: internal vs. external recipient (by domain), language, one-to-one vs. group, thread reply vs. fresh mail.
- Skip anything matching the user's exclusions. Skip auto-generated mail (calendar responses, forwards without added text, one-word replies) — they carry no style signal.

**Analyze the sample for:**

- **Language routing**: which languages the user writes in (one, several, or mixed within a mail) and what triggers each — recipient domain, thread language, specific people. Make no assumptions about which languages these are; detect them from the sample.
- **Register modes**: distinct tone modes (e.g. formal-external, warm-internal, terse-lowercase-quick-reply) and the contexts that trigger each.
- **Structural fingerprints**: greetings, openers, how they get to the point, closing patterns, sign-offs — per mode and per language.
- **Vocabulary**: recurring connectors, action verbs, hedges, signature phrases.
- **Punctuation & formatting habits**: em-dash usage, emoji frequency and which ones, exclamation marks, date formats, bullet style, paragraph length.
- **Behavioral patterns**: how they decline, propose meeting times, escalate, follow up, deliver bad news.
- **Evolution**: if the style changed over the window, weight recent months higher.
- **Taboo list**: words, phrases, and patterns that never appear in their mail — including typical AI-isms absent from it (English examples: "I hope this email finds you well", "delve", "leverage"; identify the equivalent stock phrases in each of the user's languages).

**Report:** Present the style report **inline in the chat as Markdown** — do not write the report to a workspace file. (Writing the generated skill file is allowed only in Phase 2’s fallback.)

## Phase 2 — Validate, then generate the personal skill

1. **Validation round**: Draft 2–3 short test messages in different modes (e.g. one formal external mail in each language, one casual internal Teams-style reply) using the extracted profile. Ask the user to rate them and correct the profile. Fold corrections in as rules.

2. **Create the skill** via `m_create_skill` (or the harness's skill-creation tool), named as confirmed in Phase 0:
   - **Description (frontmatter)** must contain explicit WHEN-triggers, in every language the user writes in, covering: composing, drafting, replying to, or forwarding emails; sending or replying to Teams/chat/channel messages; and the concrete tool names available in the harness (e.g. `m365_send_email`, `m365_reply_to_email`, `m365_create_draft`, `m365_forward_email`, `m365_send_chat_message`, `m365_reply_to_chat_message`, `m365_reply_to_channel_message`).
   - **Instructions** must contain:
     - Language routing rules based on recipient/thread
     - The modes with clear trigger contexts
     - A step-by-step structure template per mode (greeting → opener → body → close → sign-off)
     - Hard rules (what must NEVER happen), including all rules from the user's memories
     - Preferred vocabulary and connectors
     - Punctuation and formatting rules
     - An **anti-AI-fingerprint rule**: drafts must read as if the user typed them, never like AI output. Default-ban typical AI tells unless the sample proves the user genuinely uses them: em-dashes, "I hope this email finds you well", "delve", "leverage", "furthermore", perfectly parallel three-item structures, excessive bolding, over-hedging, and generic closers like "Let me know if you have any questions" — plus the equivalent stock phrases and tells in every language the user writes in. The safest heuristic: if a phrase or stylistic device does not appear in the user's own corpus, it does not belong in a draft.
     - A privacy rule for external recipients (no internal names, project codenames, or confidential details unless already in-thread)
     - Workflow: **always show the draft and wait for explicit confirmation before sending**
     - 3–4 concrete mini-examples per mode — **written fresh in the extracted style, never copied verbatim from real emails**

3. **Fallback**: If no skill-creation tool exists in this harness, output the complete generated `SKILL.md` as a downloadable file and tell the user how to upload it manually.

4. **Confirm**: Tell the user exactly which phrases and tool calls trigger the new skill, and that they can re-run this builder anytime to update the profile (if a voice skill with that name already exists, update it instead of creating a duplicate).

## Hard rules for this builder

- **Privacy**: Never copy verbatim sentences, names, recipients, or confidential content from real emails into the generated skill or the inline report. Extract *patterns*, not *content*. All examples must be synthetic.
- **User memories win**: Any existing user preference or memory about writing style is a hard rule in the generated skill, even if the mail sample contradicts it (the user may be trying to change a habit).
- **No sending**: This builder never sends anything. The generated skill must itself enforce draft-then-confirm.
- **Human, not AI**: The entire point of this skill is that the end result feels human. The generated skill must make "no AI-sounding text" a hard rule, and every test draft in the validation round must already comply. When in doubt between a polished-generic phrasing and the user's actual (possibly imperfect) habit, always pick the user's habit.
- **Honest signal only**: If the sample is too small or too homogeneous for a claim (e.g. only 3 external English mails), say so instead of inventing a mode.
