# Safety

The protection layer is the reason this skill is safe to run. Every rule below exists because a version of the skill without it would eventually move a message it should not have.

## Rule: Org chart

**What it does.** Any message where the sender or any To/Cc recipient is the user's manager or a direct report is protected.

**Why it exists.** Manager mail is disproportionately time-sensitive and disproportionately looks like other mail (a "reminder: submit expenses" from your manager reads like a notification from HR). Direct-report mail is often a request the user owes an answer to.

**How it can go wrong without it.** A manager who Cc's the user on a broad announcement gets classified as broadcast-notification and moved. The user misses it. Trust is gone.

**Scope note.** The skill uses `workiq_get_my_manager` and `workiq_get_my_direct_reports`, which return one hop only. Managers of managers are not resolved automatically because no single WorkIQ tool exposes that lookup reliably. If that extra layer of protection matters, add those addresses explicitly to `protection.allowlist`.

## Rule: Active thread

**What it does.** A sender is protected if the user has emailed that sender's address in the last 14 days (from the Sent-window listing). A sender is also protected if the sender has emailed the user in the last 14 days AND the sender does not match a bulk-mail or automation pattern (no `List-Unsubscribe` header, sender not on the bulk-mail/automation domain list).

**Why it exists.** Active conversations are conversations. A newsletter you unsubscribed from and forgot about is not active. A colleague you talked to last week about a project *is* active, even if this specific message reads like a broadcast. The asymmetry (user-sent recency counts for anyone, inbound recency counts only for non-bulk senders) matters: without it, weekly newsletters and daily automation notifications would be treated as active threads and never triaged.

**How it can go wrong without it.** You emailed a customer on Tuesday. They send a broadcast "quarterly update from our team" on Thursday. Without this rule, that update gets moved. The next time you talk, they mention it and you have no idea.

## Rule: Flag or star

**What it does.** Anything the user has flagged is protected, no matter what.

**Why it exists.** The user has already told the system this matters. Never second-guess a flag.

## Rule: Sensitivity label

**What it does.** Any message with a Confidential-or-above Microsoft Information Protection sensitivity label is protected. The bucketing pipeline never reads its body, only its headers, and the plan reports it only as a count under "labelled".

**Why it exists.** Sensitivity-labelled content has specific handling requirements the skill cannot honor for every possible label. The safe default is to not touch it and let the user handle it directly. This also means the skill never leaks labelled content into a triage plan the user might share.

## Rule: Sensitive sender

**What it does.** Any sender whose local part matches `protection.sensitiveLocalParts` (defaults: `hr`, `payroll`, `benefits`, `legal`, `compliance`, `finance`, `treasury`, `security`) or whose domain matches `protection.sensitiveDomains` is protected.

**Why it exists.** Mail from these functions is often compliance-critical (offer letter, retention notice, W-2 available, security incident). It can look automated (from `hr-notifications@`), which without this rule would put it in the notifications bucket. The wrong triage of one of these can have real consequences.

**Extending.** Add your organisation's HR/legal/finance/security domains to `protection.sensitiveDomains`, and any additional local-part patterns to `protection.sensitiveLocalParts`. When in doubt, add - the cost of over-protection is a slightly larger inbox, the cost of under-protection is missing something that matters.

## Rule: Unread and recent

**What it does.** Any unread message received in the last 3 days is protected. One narrow exception: a message whose sender local part matches a high-confidence automation pattern (`noreply|no-reply|donotreply|do-not-reply|notifications|alerts|automated|system|bot`) may still be classified as `notifications`. Newsletters (matched only by `List-Unsubscribe` or bulk-mail domain) never bypass this rule.

**Why it exists.** Fresh mail is fresh signal. The user has not made a call on it yet, and the point of triage is to reduce noise, not to make triage decisions on the user's behalf before they see anything. The `noreply@` exception is for the case where the whole point of the run was "get rid of the fresh notification noise" - which is a common trigger. Newsletters are excluded from the exception because a "MEGA SALE ENDS TONIGHT" blast is exactly the kind of item a user might scan on the day it arrives.

**Tuning.** `protection.unreadRecentProtectionDays` in config. Set higher (e.g. 7) if the user tends to be intermittent about reading mail; set lower (2) if the user reads mail hourly and wants tighter triage.

## Rule: Allowlist

**What it does.** Any sender address or domain in `protection.allowlist` is always protected.

**Why it exists.** There is always a long tail of important senders no heuristic catches. The user's spouse, their doctor, their accountant, a key customer contact, a mentor. The user should be able to add them once and never worry. Also the place to add a manager's manager if that extra layer of protection matters.

## What the protection layer does NOT protect against

The layer is broad, but not universal. It does not protect against:

- **User-caused approval mistakes.** If the user reads the plan and approves a bucket that contains something they should have kept, that message gets moved. The plan shows counts and sample senders to make this hard, but the user is the final authority.
- **Misclassification of new patterns.** A new bulk-mail platform the classifier does not recognise may end up not in the newsletters bucket. Under-triage is the safe direction here.
- **Bugs in the mail system.** If Outlook mis-labels a message's sensitivity, or a folder move corrupts thread state, this skill cannot detect it.

The layer catches the failures the user would notice; nothing catches everything.
