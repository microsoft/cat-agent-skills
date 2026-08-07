# Classification rules

Read this during Step 3. Each bucket has a positive test, a negative test, and a worked example. A message enters a bucket only if the positive test matches and no negative test fires. When in doubt, leave in inbox - under-triaging is safe, over-triaging destroys trust.

## Bucket order

If a message matches signals for two buckets, prefer in this order:

1. `notifications`
2. `newsletters`
3. `past-events`
4. `duplicates`
5. `resolved`

Notifications wins over newsletters because a bug tracker digest that happens to include a `List-Unsubscribe` header is still a notification. Past-events wins over duplicates because the intent ("this is meeting logistics from a past event") is more specific. Duplicates wins over resolved because moving redundant older thread messages is a lower-risk action than declaring a whole thread resolved.

## newsletters

**Positive tests (any one is sufficient):**

- Message headers contain `List-Unsubscribe`.
- Sender domain matches a known bulk-mail platform:
  - `substack.com`, `substackcdn.com`
  - `mailchimp.com`, `mcsv.net`, `list-manage.com`
  - `marketo.com`, `mktdns.com`, `marketodesigner.com`
  - `sendgrid.net`, `sendgrid.com`
  - `mailerlite.com`, `mlsend.com`
  - `convertkit.com`, `ck.page`, `ck-server.com`
  - `hubspot.com`, `hs-sites.com`, `hsforms.com`
  - `campaign-monitor.com`, `createsend.com`
  - `constantcontact.com`, `ccsend.com`
  - `sparkpostmail.com`
  - `amazonses.com` (when sender local-part suggests marketing)
- Sender local part matches, case-insensitive: `newsletter|digest|weekly|marketing|hello|news|updates|team|team-updates|community`.

**Negative tests (any one blocks):**

- Sender is on the user's org allowlist.
- Sender is a colleague at the user's own domain (do not classify internal mail as newsletter even if a mailing platform stamps it).
- Message is unread AND received in the last 3 days (protection layer, but reinforced here).

**Worked example.**

- From `Morning Brew <newsletter@morningbrew.com>`, subject "Your Monday brief", `List-Unsubscribe: <https://morningbrew.com/unsubscribe/xyz>`. Bucket: `newsletters`.
- From `Sarah Chen <sarah@yourcompany.com>`, subject "FYI - team newsletter this week", no `List-Unsubscribe`. Bucket: none (internal colleague, plus no bulk headers).

## notifications

**Positive tests (any one is sufficient):**

- Sender local part starts with, case-insensitive: `noreply|no-reply|notifications|alerts|donotreply|do-not-reply|automated|system|robot|bot|jenkins|ci|deploy`.
- Sender domain matches a known automation platform:
  - `atlassian.net`, `jira.com`, `bitbucket.org`
  - `github.com`, `github-noreply.com` (except `notifications@github.com` for security alerts - see below)
  - `gitlab.com`, `gitlab-noreply.com`
  - `azuredevops.microsoft.com`, `visualstudio.com`
  - `servicenow.com`
  - `pagerduty.com`
  - `datadoghq.com`
  - `snyk.io`
  - `dependabot.com`
  - `circleci.com`, `travis-ci.com`, `github-actions.workflow`
  - `newrelic.com`
  - `sentry.io`
  - `hubspot.com` when subject matches `notification|assigned|reminder`
- Subject matches `\[(build|deploy|alert|incident|ticket|jira|ado|github|pr|mr)\]`.

**Negative tests (any one blocks):**

- Sender is `notifications@github.com` AND subject contains "security advisory" or "vulnerability". Route these to inbox - security alerts are for the user, not for triage.
- Sender is at the user's own domain (internal automation the user may still need to see).
- Message is flagged.

**Worked example.**

- From `Jira <noreply@yourcompany.atlassian.net>`, subject "[JIRA] JC-1204 has been assigned to you". Bucket: `notifications`.
- From `GitHub <notifications@github.com>`, subject "Security advisory: high-severity vulnerability in dependency X". Bucket: none (blocked by security-advisory negative test).

## past-events

**Positive tests (all required):**

- Subject starts with one of the prefixes in `config.meetingResponsePrefixes` (defaults: `Accepted:`, `Declined:`, `Tentative:`, `Canceled:`, `Cancelled:`, `Updated invitation:`, `Meeting Forward Notification:`). Add localised prefixes to this config value when the user's Outlook language is not English - the skill does not guess translations at run time.
- Received time is older than `pastEventMinAgeDays` (default 7 days).
- Sender is a calendar system (`Microsoft Outlook`, `Exchange`, `Teams`) or the mail is a calendar-response notification.

**Negative tests (any one blocks):**

- Subject references a meeting still in the future - check the meeting date in the message subject/body if visible in the header preview.
- Sender or attendees include the user's manager or a direct report (protection layer catches this too).
- The referenced meeting is a recurring series that is still occurring.

**Worked example.**

- Subject `Accepted: Weekly design sync`, received 3 weeks ago, sender `Sarah Chen`. Bucket: `past-events` (older than 7 days, calendar-response pattern).
- Subject `Updated invitation: Quarterly review`, received today, sender `Marcus Diaz`. Bucket: none (recent, still active).

## resolved

**Positive tests (all required):**

- Thread (`conversationId`) has at least 2 messages present across the Inbox and Sent listings from Step 1.
- The newest message across Inbox and Sent for that `conversationId` is FROM the user.
- That newest user-sent message is older than `resolvedThreadMinAgeDays` (default 60 days).
- No newer inbound reply exists in either listing.

**Negative tests (any one blocks):**

- Any protection reason applies (org chart, active thread, flag, label, sensitive sender, allowlist).
- Thread mentions a stated future deadline (search subject and last-message preview for date-like tokens).
- Thread is with someone at the user's own domain AND involves more than 3 messages (internal working threads deserve a higher bar).
- The full thread state cannot be confirmed from the collected listings - the newest-message check must succeed on real data, not a guess.

**Worked example.**

- From/to external contractor, thread of 5 messages, newest is a user-sent message from 4 months ago saying "sounds good, closing this out". Bucket: `resolved`.
- From/to a colleague, user sent last message 3 months ago, but colleague replied 2 months ago from a shared address that surfaced later in Inbox. Bucket: none (newest is inbound).

## duplicates

**Positive tests (all required):**

- Thread has 2+ messages present in inbox.
- Message is not the newest message in its thread.

**Negative tests (any one blocks):**

- Any older message contains an attachment the newer message does not.
- Any older message carries a sensitivity label.
- Any older message is flagged.

The safe way to bucket duplicates is to move the older ones only; the newest message in every thread stays in the inbox to preserve the thread anchor.

**Worked example.**

- Thread has 4 messages in inbox. Older 3 are moved; newest stays. If the older 3 include one with an attachment, that one stays too; only the truly redundant older messages move.

## What never gets triaged

Even matching every positive test, these mail types never enter a bucket:

- Any message with a Confidential-or-above sensitivity label.
- Any message from HR, Legal, Finance, or Security senders (matched via `protection.sensitiveDomains` or `protection.sensitiveLocalParts`).
- Any flagged/starred message.
- Any message from the user's manager or a direct report.
- Any message from a sender the user has emailed in the last 14 days.
- Any inbound message during the 14-day active-thread window whose sender is not a bulk-mail or automation source (a newsletter that arrives weekly is not an "active thread").
- Any unread message received in the last 3 days, with one narrow exception: a high-confidence automation sender (local part `noreply|no-reply|donotreply|do-not-reply|notifications|alerts|automated|system|bot`) can still be classified as `notifications`. Newsletters cannot bypass this rule.

## Unsubscribe extraction

For each unique sender in the `newsletters` bucket, extract the `List-Unsubscribe` header value from one representative message. It commonly looks like one of:

- `<https://example.com/unsubscribe/abc123>` - keep the URL.
- `<mailto:unsubscribe@example.com>` - keep the address, tag as mailto.
- `<mailto:unsub@example.com>, <https://example.com/unsub>` - keep both, prefer https for display.

Show these in the plan. Never dereference them. The user decides which to visit.
