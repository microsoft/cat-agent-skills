# Scout tools

Read this before the first collection or execution call.

## Tools with confirmed names

| Tool | Use here |
|---|---|
| `workiq_get_my_profile` | Display name, work address, user's own domain. Call once. Needed to identify direct mail vs broadcast, and to filter the user's own address out of active-thread detection. Failure aborts the run. |
| `workiq_list_emails` | Inbox listing over the lookback window (Step 1). Two Sent-folder calls: one over the active-thread window for the protection layer, one over the full lookback window for the `resolved` bucket. |
| `workiq_list_mail_folders` | Called once per approved bucket at execution time to resolve the destination folder's ID by path. |
| `workiq_get_my_manager` | Once. For the org-chart protection rule. |
| `workiq_get_my_direct_reports` | Once. For the org-chart protection rule. |
| `workiq_move_email` | Execution only, after per-bucket approval (Step 6). |

## Tools to resolve at run time

**Mail-folder creation.** If a destination folder is missing at execution time, the skill creates it via the runtime's mail-folder create capability:

- On **Scout**, shell out to the WorkIQ CLI (`~/.scout/bin/workiq.cmd` on Windows, `~/.scout/bin/workiq` on macOS/Linux). Use `workiq create --path "/me/mailFolders/{parent-id}/childFolders" --json '{"displayName": "<Folder>"}'`. Discover the Inbox ID from `workiq_list_mail_folders` at run time. A "folder already exists" response is treated as success.
- On **Cowork**, bind to whichever M365 mail-folder create tool the session exposes. Names vary by build; inspect the tool list.

Do not hardcode any specific create-tool name here. Inspect what is available in the running session, bind if a create capability is present, and if neither the CLI nor an MCP tool is available (or the call fails with a non-idempotent error), fall through to instructing the user to create the folder in Outlook manually.

## Tools this skill deliberately does not use

| Tool | Why not |
|---|---|
| `workiq_delete_email` | Never. The skill's promise is that it never deletes. Even for duplicates or obviously past-event mail, the action is move, not delete. |
| `workiq_send_email`, `workiq_reply_to_email`, `workiq_forward_email` | Never. This is a read-and-move skill. It does not send outbound anything. |
| `workiq_mark_email` | Never. Read/unread is user state, not triage state. Moving a message does not change its read status. |
| Any calendar or chat tool | Never. Interactive skill; the output is the plan, delivered in the run. |

## What "unavailable" looks like

If any tool in the "Tools used" table above is unavailable in the current Scout session, do not silently continue. Report the missing tool and stop.

A triage skill that skips `workiq_get_my_manager` because it timed out and quietly runs without the org-chart protection is much worse than one that says "manager lookup failed, aborting". The whole safety promise of the skill is the protection layer; a triage run without it is a foot-gun.

Specific expected non-error responses:

- **Manager lookup returns no result** for a user without one (contractors, C-suite, sole proprietors). This is a normal response, not a failure. Treat as "no protection from this rule for a manager" and proceed. Report in the plan: "Manager: none returned - org-chart protection applied for direct reports only."
- **Direct reports lookup returns empty**. Same handling.
- **Sensitivity label field missing** on some messages. Treat as unlabelled and rely on other protection rules. Do not fabricate a label.
- **`workiq_list_emails` truncates.** If the tool signals truncation, stop and ask the user to run over a narrower window. Do not present a partial plan as though it covers the whole inbox.
- **`workiq_list_mail_folders` returns no match** for a configured destination folder. Attempt folder creation via the runtime's mail-folder create capability (Scout: `workiq` CLI; Cowork: M365 folder-create tool). If creation succeeds, continue. If neither the CLI nor an MCP tool is available, or the create call fails with a non-idempotent error, stop the bucket and instruct the user to create the exact folder name in Outlook. Never fall back to a different destination.

## Call discipline

**One inbox list, not one per message.** The Step 1 inbox listing must cover the whole lookback window in as few calls as the API allows (paginate if needed). Do not call `workiq_get_email` per message - bodies are not needed for classification and each call is a round trip.

**Cache the org chart for the run.** Manager and direct reports are resolved once at the start of Step 2. Do not call again per-message.

**Never re-list to answer a follow-up view.** The full set of candidates lives in one working set after Step 1. Every downstream operation - protection, classification, grouping, plan rendering - works from that set in memory. Do not re-list.

**Move in the smallest useful batches.** `workiq_move_email` may only move one at a time in some builds; if so, execute serially and report progress ("moved 50 of 312"). Do not parallelise moves across buckets; execute one approved bucket to completion before starting the next.
