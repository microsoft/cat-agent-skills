---
name: Spend More Time With Friends & Family
description: "While you're out of office, watches a group chat and answers questions from your local knowledge docs (clearly marked AI-generated), logs anything it can't answer for later, and pings you on Teams if its setup is incomplete."
platforms: [Scout]
type: automation
tags: [scout, automation, teams, out-of-office, knowledge]
author: Adi Leibowitz
version: 1.0.0
createdAt: 2026-07-14
updatedAt: 2026-07-14
featured: true
bundle: bundles/spend-more-time-with-friends-and-family.json
---
While you're out of office, watches a group chat and answers questions from your local knowledge docs (clearly marked AI-generated), logs anything it can't answer for later, and pings you on Teams if its setup is incomplete.

> **Scout automation.** This is a Microsoft **Scout** automation (a `.json` of a schedule plus ordered prompt steps). It runs on Scout only.

## Trigger

Runs on a **schedule** — every 15 minutes.

## Steps

### 1. Main

```text
You are running the "spend more time with friends and family" automation. Work through these steps in order and stop early if instructed. All file paths are resolved at runtime relative to the Scout workspace so this automation is portable across machines and operating systems. Never hardcode an absolute path or a specific username.

STEP 0 — Resolve paths (portable, cross-OS).
- Determine the workspace root (WS): this is the automation's current working directory. Get it portably: on macOS/Linux run the shell command `pwd`; on Windows run `cd` (cmd) or `$PWD.Path` (PowerShell). Trim whitespace/newlines from the result. Use whichever shell the OS provides.
- Derive these paths by joining onto WS using the OS-native separator (the shell result for WS already uses the correct separator; just append subpaths with that same separator — forward slash `/` on macOS/Linux, backslash `\` on Windows). Let SEP be that separator:
  - BOT_DIR      = WS + SEP + "friends-family-bot"
  - CONFIG_PATH  = BOT_DIR + SEP + "config.json"
  - KNOWLEDGE_DIR = BOT_DIR + SEP + "knowledge"
  - UNANSWERED   = BOT_DIR + SEP + "unanswered.md"
- Use these resolved variables everywhere below. If you are ever unsure of the separator, prefer forward slashes — the filesystem tools accept them on all platforms.

DEFAULT_CONFIG (the template to write when bootstrapping a missing config file). Note the path values are LEFT BLANK/relative on purpose — fill knowledgeDocs and unansweredLog with the runtime-resolved KNOWLEDGE_DIR and UNANSWERED values when you write the file, so nothing personal is hardcoded:
{
  "chatId": "",
  "knowledgeDocs": [ "<KNOWLEDGE_DIR>" ],
  "unansweredLog": "<UNANSWERED>",
  "lastProcessedMessageId": "",
  "answerCaveat": "\ud83e\udd16 This is an AI-generated reply from Scout on behalf of the account owner (who is currently away). Please verify anything important.",
  "ownerRelayEmail": ""
}

STEP 1 — Load or bootstrap config.
- Try to read CONFIG_PATH as JSON.
- If the file does NOT exist (or BOT_DIR is missing): create BOT_DIR and KNOWLEDGE_DIR if needed, then WRITE DEFAULT_CONFIG to CONFIG_PATH with <KNOWLEDGE_DIR> and <UNANSWERED> replaced by the actual runtime-resolved paths. This self-creates a config the user can fill in. Treat the freshly written config as loaded and continue to validation.
- If the file exists but is unparseable/corrupt: do NOT overwrite it (avoid clobbering user edits). Treat as a fatal config error and go to STEP 1b, naming the parse problem.

STEP 1a — Validate.
- Required fields: `chatId` (non-empty), and `knowledgeDocs` (a non-empty array whose folders/files actually exist and contain at least one readable knowledge file other than README.md).
- Optional: `unansweredLog`, `lastProcessedMessageId`, `answerCaveat`, `ownerRelayEmail`.

STEP 1b — If any required field is missing/empty/invalid (including right after a fresh bootstrap, where they will be empty):
- Do NOT touch the monitored chat. Instead, complain to the owner over the Teams relay so they can fix it.
  - Check relay status with m_relay_status; if not connected, call m_relay_connect.
  - Determine where to send: if `ownerRelayEmail` is set, call workiq_create_chat_by_email with it; otherwise send to the Teams self-chat (workiq_create_chat_by_email with the current user's own email from workiq_get_my_profile).
  - Send a concise message naming exactly which fields are unset/invalid and the CONFIG_PATH to edit. If you just bootstrapped the file, say so, e.g.: "⚠️ 'spend more time with friends and family' created a blank config at CONFIG_PATH but chatId and knowledge docs are still empty. Fill them in to activate."
  - Then STOP the run. Register result "blocked: incomplete config (<fields>)". Do not proceed to later steps.

STEP 2 — Fetch new messages.
- Call workiq_list_chat_messages for `chatId` (newest first, limit ~30).
- Determine which messages are NEW: those posted after `lastProcessedMessageId`. If `lastProcessedMessageId` is empty, only consider messages from the last 60 minutes (do NOT backfill the whole history).
- Ignore messages sent by the owner themselves (compare against workiq_get_my_profile) and ignore system/event messages.

STEP 3 — Identify questions.
- From the NEW messages, pick those that are genuinely asking a question (ends with "?", or is clearly interrogative / a request for info). Skip greetings, reactions, and small talk.

STEP 4 — Answer from knowledge docs.
- Read the contents of every knowledge file referenced by `knowledgeDocs` (recurse into folders; skip README.md). Treat this as the ONLY source of truth.
- For each question, try to answer strictly from the knowledge docs. Do not invent facts not supported by the docs.
- If you have a supported answer: post a reply in the chat using workiq_reply_to_chat_message (reply to that specific message). Prepend/append the caveat from `answerCaveat` (or a sensible default if unset) so it's clear the reply is AI-generated by Scout on the owner's behalf.
- If the docs do NOT contain enough to answer: append a row to the `unansweredLog` markdown table with local timestamp, asker display name, the question text, and the message id / chat reference. Do NOT post a guess to the chat.

STEP 5 — Update state.
- Set `lastProcessedMessageId` in CONFIG_PATH to the id of the newest message you processed, and write the file back (preserve all other fields).

STEP 6 — Register a short result summary: how many new questions were found, how many answered in-chat, how many logged as unanswered. Only surface to Teams if something needs the owner's attention (e.g. unanswered questions logged), otherwise keep it quiet.
```

## Import into Scout

1. Download the automation (the `.json` on this page).
2. In **Scout › Automations**, choose **Import** and select the file (or paste its contents). Review the schedule and steps, then enable it.

You can also point Scout's **Import from GitHub** at a repository directory of automation `.json` files (a `skills/` subfolder is installed automatically). This automation's file is `submissions/spend-more-time-with-friends-and-family/` in this repo.

> Review the steps before enabling — automations act on your behalf on a schedule.
