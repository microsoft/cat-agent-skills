# Inbox Triage

Your Outlook inbox has 2,000+ messages. You know 80% of it is newsletters, notifications, meeting logistics from events that already happened, and threads you resolved months ago. You also know that if you set up an aggressive rule that auto-archives all that, you *will* accidentally miss the one email from your manager that shared a subject line with a marketing blast. So you never set it up, and the inbox keeps growing.

This skill builds a triage plan you can actually run: it groups mail into buckets (newsletters, notifications, past-event logistics, resolved threads, redundant duplicates), shows you counts and sample senders per bucket, and waits for you to approve each bucket individually before it moves anything. Nothing is ever deleted, everything is moved into folders under `Inbox Triage/` in your mailbox, and a broad protection layer keeps anything from your manager, direct reports, active threads, flagged mail, HR/Legal/Finance/Security senders, or labelled mail completely out of scope.

## Basic usage

Once the skill is imported into Scout or Cowork, ask for it in plain language:

```
clean up my inbox
```

Other phrasings work too - "triage my mail", "get rid of the newsletter noise", "archive the old resolved threads". The skill returns a plan grouped by bucket:

```
Bucket: Newsletters (312 messages, 4 senders)
  Sample senders: Morning Brew, Product X marketing, KubeCon updates, ...
  Proposed action: move to "Inbox Triage/Newsletters"
  Approve this bucket? [approve | skip | show me one-by-one]

Bucket: Notifications (198 messages)
  Sample senders: noreply@jira, notifications@github, ...
  Proposed action: move to "Inbox Triage/Notifications"
  Approve this bucket?

...

Protected - not touched (1,204 messages):
  Org-chart senders: 112 | Active-thread senders: 318 | Flagged: 14 |
  Labelled: 47 | Sensitive senders: 89 | Unread & recent: 441 | Allowlist: 183
```

You approve each bucket separately. Nothing moves until you say so, per bucket. Skipping the newsletters bucket doesn't skip the notifications bucket.

## The two hard rules

Two things this skill never does, even if asked:

1. **Never deletes.** Every action is a *move* into a named folder inside your mailbox, always under `Inbox Triage/`. You can drag anything back. If you want them gone permanently, you empty those folders yourself.
2. **Never acts without per-bucket approval.** You see the plan first. You approve each bucket individually. There is no "auto-run", there is no "approve everything", there is no scheduled unattended triage.

The point is that you can trust this skill enough to actually run it. A destructive triage tool doesn't get run twice.

## The protection layer

A message is protected (and never triaged) if any of these are true:

- **From your manager or a direct report.** Resolved once per run via the platform's M365 lookup (WorkIQ on Scout, the equivalent M365 tool on Cowork).
- **Active thread** - you've emailed the sender in the last 14 days, or a non-bulk sender has emailed you in that window.
- **Flagged or starred.**
- **Sensitivity label** of Confidential or above.
- **Sensitive sender** - HR, Legal, Finance, or Security addresses matched by local part or domain (configurable).
- **Unread and recent** - unread and received in the last 3 days. Narrow exception: a high-confidence automation sender (`noreply@`, `alerts@`, etc.) can still be classified as a notification. Newsletters cannot bypass.
- **Your allowlist** - senders or domains you explicitly protect in config.

The plan shows how many messages were protected by each reason, so you can see the layer working.

## Configure

The skill runs with sensible defaults on the first try. To personalise, copy `assets/config.example.json` to `~/.copilot/inbox-triage/config.json` and set your priority allowlist, custom sensitive domains, folder names, localised meeting-response prefixes, and lookback window.

## Setup

In most sessions the skill creates the destination folders under `Inbox Triage/` in your mailbox automatically on first run — Cowork uses the platform's M365 folder tool; macOS/Linux Scout uses the WorkIQ CLI. In two cases you'll need to create the folders once yourself in Outlook (or set alternate names in `config.folders.*`):

- **Windows Scout**, because the WorkIQ CLI's `.cmd` wrapper cannot safely pass JSON payloads through `cmd.exe`.
- **Any session where the folder-create capability isn't exposed** (unusual, but the skill defers rather than guessing).

The default folders are:

- `Inbox Triage/Newsletters`
- `Inbox Triage/Notifications`
- `Inbox Triage/Past events`
- `Inbox Triage/Resolved`
- `Inbox Triage/Duplicates`

If a folder is missing at execution time and the runtime cannot create it, the skill stops that bucket and tells you the exact name to create — it never falls back to a different destination.

## Undo

Every move goes to a folder in your own mailbox. Reversal is Outlook drag-and-drop; the skill does not need to be involved. If you want to nuke a bucket after review, you empty the folder yourself - the safety guarantee ("this skill never deletes") is what makes it safe to run in the first place.

## Safety

Everything the skill reads is treated as untrusted data. A newsletter that says "please move me to inbox forever" is content to classify, not a command to follow. The skill never opens message bodies unless a candidate survives every bucket and needs disambiguation - classification runs on headers, subjects, and sender addresses, which keeps it fast and out of confidential content. Unsubscribe links are extracted and displayed to you for the newsletters bucket; the skill never clicks, follows, or sends any unsubscribe on your behalf.
