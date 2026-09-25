# Classification rules

Read this during Step 3. Each bucket has a positive test, a negative test, and a worked example. A message enters a bucket only if the positive test matches and no negative test fires. When in doubt, leave in inbox - under-triaging is safe, over-triaging destroys trust.

## Bucket order

If a message matches signals for two buckets, prefer in this order:

1. `notifications`
2. `newsletters`
3. `pastEvents`
4. `duplicates`
5. `resolved`

Notifications wins over newsletters because a bug tracker digest that happens to include a `List-Unsubscribe` header is still a notification. Past-events wins over duplicates because the intent ("this is meeting logistics from a past event") is more specific. Duplicates wins over resolved because moving a redundant identical copy is a lower-risk action than declaring a whole thread resolved.

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

- Sender local part (case-insensitive) is one of these automation tokens, **bounded** so it is not merely a prefix of a real word: the local part either equals the token exactly, or the token is immediately followed by a separator (`-`, `_`, `.`, `+`) or a digit. Tokens: `noreply`, `no-reply`, `donotreply`, `do-not-reply`, `notifications`, `alerts`, `automated`, `system`, `robot`, `bot`, `jenkins`, `ci`, `deploy`. So `bot@`, `bot-ci@`, `system.alerts@`, `ci-01@` match, but `botany@`, `systematic@`, `cinema@` do **not** (the token boundary check is what prevents those false positives, which would otherwise be moved and also wrongly granted the unread-message exception below).
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

## pastEvents

Because Step 1 collects only subject, sender, and received time - it does **not** open calendar items or message bodies - this bucket is scoped to what those fields alone can prove. Meeting-response prefixes live in two separate config lists so localisation is unambiguous:

- **Retrospective receipts** (`config.meetingResponsePrefixes`, defaults `Accepted:`, `Declined:`, `Tentative:`, `Meeting Forward Notification:`): a record of a response that has *already happened*. These are logistics noise whether or not the meeting itself is still upcoming - an "Accepted:" receipt from two weeks ago adds nothing to the inbox - so they are eligible for `pastEvents`.
- **Forward-looking notices** (`config.meetingForwardLookingPrefixes`, defaults `Canceled:`, `Cancelled:`, `Updated invitation:`): these refer to the *meeting*, which may still be in the future or part of a live recurring series. That status cannot be verified without calendar access, so these are **left in the inbox** (never auto-bucketed) rather than guessed at.

Keeping the two lists separate is what makes localisation safe: add a localised `Accepted:` to `meetingResponsePrefixes` and a localised `Canceled:` to `meetingForwardLookingPrefixes`, and each stays in its correct group.

**Positive tests (all required):**

- Subject starts with one of the **retrospective-receipt** prefixes in `config.meetingResponsePrefixes`. A subject carrying one of these prefixes IS the calendar-response signal - a meeting-response receipt is normally sent **from the responding attendee's own address** (e.g. `Sarah Chen`), so do NOT additionally require the sender to be a calendar system; that would exclude the very receipts this bucket targets. A sender of `Microsoft Outlook`/`Exchange`/`Teams` is confirming evidence when present, not a gate. Add localised prefixes to `meetingResponsePrefixes` when the user's Outlook language is not English - the skill does not guess translations at run time.
- Received time is older than `pastEventMinAgeDays` (default 7 days).

**Negative tests (any one blocks):**

- Subject starts with a **forward-looking** prefix from `config.meetingForwardLookingPrefixes` - left in inbox because the meeting may be upcoming and that cannot be verified from the collected fields.
- Sender or attendees include the user's manager or a direct report (protection layer catches this too).

**Worked example.**

- Subject `Accepted: Weekly design sync`, received 3 weeks ago, sender `Sarah Chen` (an attendee's own address). Bucket: `pastEvents` (a receipt of a response already made, older than 7 days - eligible regardless of the meeting's future date, and regardless of the sender being a person rather than a calendar system).
- Subject `Updated invitation: Quarterly review`, received today, sender `Marcus Diaz`. Bucket: none (forward-looking prefix and recent - left in inbox).
- Subject `Canceled: Budget planning`, received 2 weeks ago. Bucket: none (forward-looking prefix; the series may still be active and that cannot be checked without calendar access).

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

A `duplicates` match is a genuine **redundant copy** of a message - the *same* message delivered to the inbox more than once (a classic cause: the user is both a direct recipient and on a distribution list that also delivers, so two identical copies land). Redundant copies share the same `internetMessageId` (the RFC 5322 Message-ID header). This is deliberately NOT "every older message in a thread": distinct replies on one `conversationId` are different messages, each with its own `internetMessageId`, and each may carry unique decisions or content - moving them would bury real conversation history.

**Positive tests (all required):**

- Two or more inbox messages share the same `internetMessageId`.
- The message under test is not the copy being kept (the newest copy by received time is kept; the rest are the duplicates).

**Negative tests (any one blocks):**

- Any copy carries an attachment another copy does not.
- Any copy carries a sensitivity label.
- Any copy is flagged.
- `internetMessageId` is missing/empty on the message (without it, redundancy cannot be proven - leave the message in the inbox).

The safe way to bucket duplicates is to keep one copy (the newest) in the inbox and move only the other identical copies.

**Worked example.**

- The same message (identical `internetMessageId`) appears 3 times in the inbox because the user is a direct recipient and also on two lists that deliver. Two copies move; the newest copy stays. A four-message *thread* (four different `internetMessageId`s on one `conversationId`) is NOT a duplicate set - none of those move under this bucket.

## What never gets triaged

Even matching every positive test, these mail types never enter a bucket:

- Any message with a Confidential-or-above sensitivity label.
- Any message from HR, Legal, Finance, or Security senders (matched via `protection.sensitiveDomains` or `protection.sensitiveLocalParts`).
- Any flagged/starred message.
- Any message from the user's manager or a direct report.
- Any message from a sender the user has emailed within `activeThreadWindowDays` (default 14).
- Any inbound message within the `activeThreadWindowDays` active-thread window whose sender is not a bulk-mail or automation source (a newsletter that arrives weekly is not an "active thread").
- Any unread message received in the last 3 days, with one narrow exception: a high-confidence automation sender (sender local part matches a **bounded** automation token as defined in the `notifications` rule above - `noreply`, `no-reply`, `donotreply`, `do-not-reply`, `notifications`, `alerts`, `automated`, `system`, `bot`, etc. - equal to the token or token-plus-separator/digit, so `botany@`/`systematic@` do not qualify) can still be classified as `notifications`. Newsletters cannot bypass this rule.

## Unsubscribe extraction

For each unique sender in the `newsletters` bucket, extract the `List-Unsubscribe` header value from one representative message. It commonly looks like one of:

- `<https://example.com/unsubscribe/abc123>` - keep the URL.
- `<mailto:unsubscribe@example.com>` - keep the address, tag as mailto.
- `<mailto:unsub@example.com>, <https://example.com/unsub>` - keep both, prefer https for display.

Show these in the plan. Never dereference them. The user decides which to visit.
