# Tools

Read this before the first collection or execution call.

The skill runs on both Cowork and Scout. Tool names differ by platform - Scout typically exposes them as `workiq_*`, Cowork typically as `m365_*` (or platform-native names). Rather than hardcode names, the skill describes **capabilities** and binds them to whichever concrete tool the running session exposes.

## Capabilities the skill needs

Bind these capabilities to whichever concrete tools the running session exposes. The **collection + protection** capabilities (get profile, list emails, list mail folders, get manager, get direct reports) are required upfront - at the start of every run, inspect the tools available in the session and bind them. If any of those has no available tool binding, do not silently continue - report which capability is missing and stop. A triage skill that skips org-chart protection because a lookup tool was missing is much worse than one that says "profile lookup unavailable, aborting". The whole safety promise of the skill is the protection layer; a triage run without it is a foot-gun.

The **execution-only** capabilities (get email by ID, move email, create mail folder) are not required upfront: they are checked at Step 6. Move email and create mail folder have documented fallbacks (manual folder creation; already-moved handling). The **get-email-by-ID re-check** is required to move safely: bind it at Step 6 to a dedicated get-email tool or to an ID-filtered "list emails" contract that returns a single message's current `folderId` and protection fields. If neither is available in the session, the execution-time protection re-check cannot be performed, so **stop the affected bucket rather than move on stale state** (Step 6.5) - do not fall back to moving without the re-check. Do not stop the run at Step 1 because an execution-only capability is missing; surface it at execution.

| Capability | Purpose | Typical Scout name | Typical Cowork name |
|---|---|---|---|
| Get my profile | Display name, work address, user's own domain. Called once. | `workiq_get_my_profile` | `m365_get_my_profile` |
| List emails | Inbox listing over the lookback window; a **mailbox-wide** inbound listing over the active-thread window (all folders, so a filed reply still counts toward inbound active-thread protection); two Sent-folder listings (active-thread window with recipients incl. Bcc, and full lookback for `resolved` with the `from`/sender identity); at execution time, an **ID-filtered re-fetch** of a single approved message (by `id`, returning its current `folderId` and protection fields) when a dedicated "get email" tool is not present; and an **`internetMessageId`-filtered Inbox enumeration** used at execution time to re-establish the current membership of a duplicate group before moving it. The listing must return the protection- and duplicate-critical fields (`toRecipients`/`ccRecipients`, `flag.flagStatus`, sensitivity label, `isRead`, `folderId`, `internetMessageId`, sender, `hasAttachments`) - if it returns successfully but omits one, treat that field as an unavailable capability and stop rather than proceeding with a weakened protection layer. If mailbox-wide inbound search is not supported, stop the run because the inbound active-thread protection cannot be honored. | `workiq_list_emails` | `m365_list_emails` |
| Get email by ID | Execution only. Re-fetch one message's **current** state (its `folderId`, `flag.flagStatus`, `isRead`/received time, sensitivity label, sender/recipients) immediately before moving it, for the Step 6.5 protection re-check. If the session exposes no dedicated get-email tool, this capability may instead be satisfied by an ID-filtered "list emails" call (see above) that returns the same fields for a given message id. | `workiq_get_email` | `m365_get_email` |
| List mail folders | Resolve destination folder IDs by path at execution time. | `workiq_list_mail_folders` | `m365_list_mail_folders` |
| Get my manager | Org-chart protection rule. Once. | `workiq_get_my_manager` | `m365_get_my_manager` |
| Get my direct reports | Org-chart protection rule. Once. | `workiq_get_my_direct_reports` | `m365_get_my_direct_reports` |
| Move email | Execution only, after per-bucket approval. | `workiq_move_email` | `m365_move_email` |
| Create mail folder | Execution only, when the destination folder is missing. See "Folder creation" below. | (via WorkIQ CLI - see below) | Typically an `m365_create_mail_folder` tool or equivalent |

**Names in the table above are guidance, not guarantees.** Inspect the tools available in the current session and bind by capability. If the session exposes a differently-named tool that provides the capability, use it. If it exposes neither, treat the capability as missing.

## Folder creation

The "list mail folders" capability is read-only, so folder creation is handled separately:

- On **Cowork**, most builds expose a mail-folder create tool (typical name `m365_create_mail_folder`). Bind to whichever create tool is present.
- On **Scout (macOS/Linux)**, no MCP-level create tool is currently exposed, but the platform ships a CLI at `~/.scout/bin/workiq` that can call any Microsoft Graph endpoint. POSIX shells preserve argv cleanly, so the CLI works reliably:
  - Command (absolute path, resolve `~` via the runtime): `~/.scout/bin/workiq`
  - Arguments (each as a separate argv entry):
    1. `create`
    2. `-u` (short form of `--url`)
    3. `/me/mailFolders/{parent-id}/childFolders`
    4. `-b` (short form of `--body`)
    5. The JSON body as a single argv value, e.g. `{"displayName":"Inbox Triage"}`
- On **Scout (Windows)**, the CLI is a `.cmd` batch wrapper (`~/.scout/bin/workiq.cmd`) that requires `cmd.exe`. `cmd.exe` cannot safely pass JSON with double quotes through argv, and the CLI does not accept the body via a file or stdin. **Do not attempt auto-create on Windows Scout** - treat the create capability as unavailable and use the manual-folder fallback. The failure modes of trying (folder created with wrong name because `displayName` was mangled) are silent and worse than simply asking the user to create the folder.

Discover `{parent-id}` from a prior `list mail folders` call. When creating `Inbox Triage` under Inbox, use Inbox's folder ID; when creating a bucket child under the `Inbox Triage` parent, use that parent's folder ID. Treat a Graph "folder already exists" or HTTP 409 response as success and re-resolve the folder ID from a fresh listing.

Regardless of platform, if folder creation truly fails for a reason other than already-exists (for example: Windows Scout where the `.cmd` wrapper cannot safely carry the JSON body, no WorkIQ CLI available on a non-Windows Scout host, no matching MCP tool on Cowork, permissions error, etc.), fall through to instructing the user to create the folder manually in Outlook. Never fall back to a different destination folder.

## Capabilities this skill deliberately does not use

| Capability | Why not |
|---|---|
| Delete email | Never. The skill's promise is that it never deletes. Even for duplicates or obviously past-event mail, the action is move, not delete. |
| Send email, reply, forward | Never. This is a read-and-move skill. It does not send outbound anything. |
| Mark read/unread | Never. Read/unread is user state, not triage state. Moving a message does not change its read status. |
| Calendar or chat | Never. Interactive skill; the output is the plan, delivered in the run. |

## What "unavailable" looks like

Specific expected non-error responses:

- **Manager lookup returns no result** for a user without one (contractors, C-suite, sole proprietors). This is a normal response, not a failure. Treat as "no protection from this rule for a manager" and proceed. Report in the plan: "Manager: none returned - org-chart protection applied for direct reports only."
- **Direct reports lookup returns empty**. Same handling.
- **Sensitivity label field missing** on some messages. **Treat as protected**, not as unlabelled - a missing label field is unknown, not confirmed absent, and the whole point of the sensitivity-label rule is that the skill never moves anything that might be labelled Confidential-or-above. Record the reason as "label unknown" in the protected count. Do not fabricate a label and do not rely on other protection rules to catch these.
- **List emails truncates.** If the tool signals truncation, stop and ask the user to run over a narrower window. Do not present a partial plan as though it covers the whole inbox.
- **List mail folders returns no match** for a configured destination folder. Attempt folder creation via the bound create capability (see above). If creation succeeds, continue. If the capability is unavailable, or the create call fails for a reason other than already-exists, stop the bucket and instruct the user to create the exact folder name in Outlook.

## Call discipline

**One inbox list, not one per message.** The Step 1 inbox listing must cover the whole lookback window in as few calls as the API allows (paginate if needed). Do not call any get-email-body tool per message - bodies are not needed for classification and each call is a round trip.

**Cache the org chart for the run.** Manager and direct reports are resolved once at the start of Step 2 and reused for planning and classification. Do not re-resolve per message during planning. **Exception:** the execution-time protection refresh in Step 6.5 may re-resolve the org chart under its short freshness bound, so a manager/direct-report change during a long approval or move run is caught before mail is moved - that refresh is required, not a per-message planning call.

**Never re-list to answer a follow-up view.** The full set of candidates lives in one working set after Step 1. Every downstream *classification and planning* operation - protection classification, grouping, plan rendering - works from that set in memory. Do not re-list to re-render or re-explore the plan. **Exception:** the execution-time protection refresh in Step 6.5 is required, not a follow-up view. Before moving mail, protection state must be current, so re-listing the Sent-window and inbound active-thread windows when the cached evidence has gone stale (and re-fetching the specific message being moved) is mandatory - never skip that refresh under this rule. The distinction: re-listing to *re-answer a question the working set already answers* is prohibited; re-listing to *obtain fresh protection evidence at execution time* is required.

**Move in the smallest useful batches.** The move capability may only move one at a time in some builds; if so, execute serially and report progress ("moved 50 of 312"). Do not parallelise moves across buckets; execute one approved bucket to completion before starting the next.
